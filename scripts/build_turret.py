#!/usr/bin/env python3
"""Build a stationary 360-degree turret, Spine data, atlas and geometry preview.

The configuration contains measured pixel geometry, not AI-generated coordinates.
Root/base stay fixed; aim is external; only recoil is animated. Outputs never
replace an existing directory. See references/toywatch-turrets.md for the schema.
"""
import argparse
import json
import math
import re
import shutil
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image
from asset_io import asset_name, finite, pair, sha256, write_json
from make_atlas import write_atlas
from turret_preview import generate_preview


def pixel_to_spine(point, pivot):
    return point[0]-pivot[0], pivot[1]-point[1]


def recoil_at(time, duration, peak_time, recover_time, depth):
    if time < 0 or time >= duration:
        return 0.0
    if time <= peak_time:
        return depth*time/peak_time
    if time < recover_time:
        return depth*(recover_time-time)/(recover_time-peak_time)
    return 0.0


def radius_px(image, position, pivot, offset=(0.0, 0.0)):
    """All alpha>0 texel corners, no opacity cutoff or assumed transparent bounds."""
    y, x = np.nonzero(np.asarray(image.getchannel("A")) > 0)
    if not len(x):
        raise ValueError("A part is completely transparent")
    max_sq = 0.0
    for dx, dy in ((0,0), (1,0), (0,1), (1,1)):
        xx = x+dx+position[0]-pivot[0]+offset[0]
        yy = y+dy+position[1]-pivot[1]+offset[1]
        max_sq = max(max_sq, float(np.max(xx*xx+yy*yy)))
    return math.sqrt(max_sq)


def validate_skeleton(skeleton):
    names = {b["name"] for b in skeleton["bones"]}
    if len(names) != len(skeleton["bones"]):
        raise ValueError("Duplicate bone names")
    if set(skeleton["animations"]) != {"idle", "fire"}:
        raise ValueError("Turrets require exactly idle and fire clips")
    for clip in skeleton["animations"].values():
        if set(clip.get("bones", {})) != {"recoil"}:
            raise ValueError("Turret clips may animate only the recoil bone; aim is procedural")
        frames = clip["bones"]["recoil"]["translate"]
        if frames[0].get("x",0) or frames[0].get("y",0) or frames[-1].get("x",0) or frames[-1].get("y",0):
            raise ValueError("Clips must start and finish at rest")
        times = [f.get("time",0) for f in frames]
        if any(b <= a for a,b in zip(times,times[1:])):
            raise ValueError("Keyframe times must increase")
    for bone in skeleton["bones"]:
        if bone["name"].startswith("muzzle_") and bone.get("parent") != "recoil":
            raise ValueError("Muzzle bones must inherit recoil")


def build(config, config_dir):
    name = asset_name(config["name"])
    version = config["spine_version"]
    if not isinstance(version,str) or not re.fullmatch(r"4\.[23](?:\.\d+)?", version):
        raise ValueError("Declare the installed Spine runtime version (supported subset: 4.2 or 4.3)")
    canvas = pair(config["canvas_size_px"], "canvas_size_px")
    if min(canvas) <= 0 or canvas[0] != canvas[1] or any(v != int(v) for v in canvas):
        raise ValueError("Turret canvas must be a positive square in integer pixels")
    pivot = pair(config["pivot_px"], "pivot_px")
    if any(p < 0 or p > canvas[i] for i,p in enumerate(pivot)):
        raise ValueError("pivot_px must be inside the canonical canvas")
    forward = pair(config.get("forward_px", [1,0]), "forward_px")
    length = math.hypot(*forward)
    if length == 0:
        raise ValueError("forward_px must be nonzero")
    forward = tuple(v/length for v in forward)
    display = finite(config.get("display_size_px", 64), "display_size_px")
    cell = finite(config.get("cell_size_px", 72), "cell_size_px")
    if min(display, cell) <= 0:
        raise ValueError("Display and cell sizes must be positive")
    scale = display/canvas[0]
    profile = config.get("profile", "toywatch_turret")
    if profile not in ("toywatch_turret", "stationary_turret"):
        raise ValueError("Unknown turret profile")
    max_radius = finite(config.get("head_max_radius_cell", .45), "head_max_radius_cell")
    recoil = config.get("fire", {})
    recoil_cell = finite(recoil.get("recoil_cell", .01), "recoil_cell")
    if max_radius <= 0 or recoil_cell < 0:
        raise ValueError("Envelope must be positive and recoil nonnegative")
    if profile == "toywatch_turret" and (max_radius > .45 or recoil_cell > .01):
        raise ValueError("Toywatch head budget is 0.45cell and recoil budget is 0.01cell; exceptions need an explicit project profile")
    depth = recoil_cell*cell/scale
    duration = finite(recoil.get("duration", .18), "fire.duration")
    peak = finite(recoil.get("peak_time", .03), "fire.peak_time")
    recover = finite(recoil.get("recover_time", duration), "fire.recover_time")
    if not 0 < peak < recover <= duration:
        raise ValueError("Require 0 < peak_time < recover_time <= duration")
    # Spine is Y-up. Pixel forward/recoil and the browser preview are Y-down.
    recoil_spine = [-forward[0]*depth, forward[1]*depth]
    frames = [{"time":0.0,"x":0.0,"y":0.0},
              {"time":peak,"x":recoil_spine[0],"y":recoil_spine[1]},
              {"time":recover,"x":0.0,"y":0.0}]
    if recover < duration:
        frames.append({"time":duration,"x":0.0,"y":0.0})
    skeleton = {"skeleton": {"spine":version,"x":-pivot[0],"y":pivot[1]-canvas[1],
                              "width":canvas[0],"height":canvas[1],"images":"./images/"},
                "bones": [{"name":"root"}, {"name":"base","parent":"root"},
                          {"name":"aim","parent":"root"}, {"name":"recoil","parent":"aim"}],
                "slots": [], "skins": [{"name":"default","attachments":{}}],
                "animations": {"idle":{"bones":{"recoil":{"translate":[{"time":0.0,"x":0.0,"y":0.0},{"time":1.0,"x":0.0,"y":0.0}]}}},
                               "fire":{"bones":{"recoil":{"translate":frames}}}}}
    images, parts, source_files = {}, [], {}
    head_radius, fixed_radius = 0.0, 0.0
    if not isinstance(config.get("parts"),list) or not config["parts"]:
        raise ValueError("parts must be a nonempty ordered list")
    for part in config["parts"]:
        part_name = asset_name(part["name"])
        if part_name in images:
            raise ValueError(f"Duplicate part {part_name}")
        role = part["role"]
        if role not in ("base", "aim", "recoil"):
            raise ValueError(f"{part_name}: role must be base, aim or recoil")
        path = Path(part["file"])
        path = path if path.is_absolute() else Path(config_dir)/path
        image = Image.open(path).convert("RGBA")
        pos = pair(part.get("position_px", [0,0]), "position_px")
        if min(pos) < 0 or pos[0]+image.width > canvas[0] or pos[1]+image.height > canvas[1]:
            raise ValueError(f"{part_name}: positioned image exceeds canonical canvas")
        center = (pos[0]+image.width/2, pos[1]+image.height/2)
        sx, sy = pixel_to_spine(center, pivot)
        skeleton["slots"].append({"name":part_name,"bone":role,"attachment":part_name})
        skeleton["skins"][0]["attachments"][part_name] = {part_name:{"x":sx,"y":sy,"width":image.width,"height":image.height}}
        radius = radius_px(image, pos, pivot)
        if role == "recoil":
            # The squared distance is convex in linear recoil depth: endpoints
            # bound every time and every aim angle without sampled omissions.
            radius = max(radius, radius_px(image,pos,pivot,(-forward[0]*depth,-forward[1]*depth)))
        if role == "base":
            fixed_radius = max(fixed_radius, radius)
        else:
            head_radius = max(head_radius, radius)
        images[part_name], source_files[part_name] = image, path
        parts.append({"name":part_name,"role":role,"position_px":list(pos),"size_px":list(image.size),
                      "sha256":sha256(path),"radius_cell":radius*scale/cell})
    if not any(p["role"] == "recoil" for p in parts):
        raise ValueError("At least one visible recoil part is required")
    envelope = head_radius*scale/cell
    if envelope > max_radius + 1e-12:
        raise ValueError(f"Rotating head alpha envelope {envelope:.6f}cell exceeds {max_radius:.6f}cell; adjust measured display size or artwork")
    muzzles, muzzle_names = [], set()
    if not isinstance(config.get("muzzles"),list) or not config["muzzles"]:
        raise ValueError("At least one measured muzzle is required")
    for index, muzzle in enumerate(config["muzzles"]):
        muzzle_name = asset_name(muzzle.get("name",str(index)))
        if muzzle_name in muzzle_names:
            raise ValueError("Duplicate muzzle name")
        muzzle_names.add(muzzle_name)
        point = pair(muzzle["position_px"], "muzzle.position_px")
        if any(p < 0 or p > canvas[i] for i,p in enumerate(point)):
            raise ValueError("Muzzle point lies outside canonical canvas")
        sx,sy = pixel_to_spine(point,pivot)
        bone = "muzzle_"+muzzle_name
        skeleton["bones"].append({"name":bone,"parent":"recoil","x":sx,"y":sy})
        muzzles.append({"bone":bone,"setup_px":list(point),"setup_spine":[sx,sy]})
    manifest = {"schema":1,"name":name,"profile":profile,"spine_version":version,
                "canvas_size_px":list(canvas),"pivot_px":list(pivot),"forward_px":list(forward),
                "godot_display_scale":scale,"cell_size_px":cell,"display_size_px":display,
                "head_envelope_cell":envelope,"head_max_radius_cell":max_radius,
                "fixed_base_radius_cell":fixed_radius*scale/cell,
                "fire":{"duration":duration,"peak_time":peak,"recover_time":recover,
                        "recoil_cell":recoil_cell,"recoil_source_px":depth},
                "clips":{"idle":{"loop":True},"fire":{"loop":False}},
                "parts":parts,"muzzles":muzzles,"verification":{"geometry":"passed","engine":"not-run"}}
    validate_skeleton(skeleton)
    return skeleton, images, manifest, source_files


def export(config_path, output):
    config_path, output = Path(config_path), Path(output)
    if output.exists():
        raise ValueError(f"Output exists: {output}; choose a versioned directory")
    config = json.loads(config_path.read_text(encoding="utf-8"))
    skeleton, images, manifest, sources = build(config, config_path.parent)
    output.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix=".turret-",dir=output.parent))
    try:
        name = manifest["name"]
        (staging/"images").mkdir()
        portable = dict(config)
        portable["parts"] = []
        for spec in config["parts"]:
            entry = dict(spec)
            entry["file"] = f"images/{spec['name']}.png"
            portable["parts"].append(entry)
            shutil.copyfile(sources[spec["name"]],staging/entry["file"])
        write_atlas(images,staging,name)
        write_json(staging/(name+".spine-json"),skeleton)
        write_json(staging/"rig.config.json",portable)
        manifest["source_config_sha256"] = sha256(config_path)
        manifest["outputs"] = {name+s:sha256(staging/(name+s)) for s in (".png",".atlas",".spine-json")}
        write_json(staging/(name+".manifest.json"),manifest)
        (staging/"preview.html").write_text(generate_preview(manifest,images),encoding="utf-8")
        staging.rename(output)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config",type=Path,required=True)
    parser.add_argument("--output",type=Path,required=True)
    args = parser.parse_args()
    try:
        result = export(args.config,args.output)
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,f"ERROR: {exc}\n")
    print(json.dumps({"output":str(args.output),"head_envelope_cell":result["head_envelope_cell"],
                      "clips":list(result["clips"]),"muzzles":len(result["muzzles"])}))


if __name__ == "__main__":
    main()
