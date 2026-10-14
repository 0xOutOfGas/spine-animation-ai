#!/usr/bin/env python3
"""Embed Spine assets in an HTML player preview (runtime CDN still needs internet)."""
import argparse
import base64
import html
import json
import re
from pathlib import Path


def find_atlas_images(atlas_path):
    atlas_path = Path(atlas_path).resolve()
    lines = atlas_path.read_text(encoding="utf-8").splitlines()
    images = []
    for index,line in enumerate(lines):
        line = line.strip()
        if index+1 < len(lines) and line and ":" not in line and lines[index+1].strip().startswith("size:"):
            path = (atlas_path.parent/line).resolve()
            if not path.is_relative_to(atlas_path.parent):
                raise ValueError("Atlas page leaves its source directory")
            if not path.is_file():
                raise ValueError(f"Missing atlas page: {line}")
            images.append((line,str(path)))
    if not images:
        raise ValueError("No atlas pages found")
    return images


def generate_html(skeleton_path, atlas_path, atlas_images, animation=None, skin=None,
                  bg_color="#1a1a2eff", show_controls=True, title="Spine Animation Preview", runtime_version=None):
    skeleton_path,atlas_path = Path(skeleton_path),Path(atlas_path)
    is_json = skeleton_path.suffix.lower() in (".json",".spine-json")
    inferred = None
    if is_json:
        data = json.loads(skeleton_path.read_text(encoding="utf-8"))
        inferred = ".".join(data["skeleton"]["spine"].split(".")[:2])
    runtime_version = runtime_version or (inferred+".*" if inferred else None)
    if not runtime_version or not re.fullmatch(r"4\.[23]\.(?:\d+|\*)",runtime_version):
        raise ValueError("Declare a 4.2.x or 4.3.x player version (required for binary exports)")
    if inferred and not runtime_version.startswith(inferred+"."):
        raise ValueError("Player major/minor version must match skeleton data")
    # Alias Godot's extension to .json so player type inference works reliably.
    skeleton_name = skeleton_path.stem+".json" if is_json else skeleton_path.name
    raw = {}
    for key,path,mime in [(skeleton_name,skeleton_path,"application/json" if is_json else "application/octet-stream"),
                          (atlas_path.name,atlas_path,"application/octet-stream")]+[
                              (name,Path(path),"image/png" if Path(path).suffix.lower()==".png" else "image/jpeg")
                              for name,path in atlas_images]:
        raw[key] = f"data:{mime};base64,"+base64.b64encode(Path(path).read_bytes()).decode("ascii")
    config = {"skeleton":skeleton_name,"atlas":atlas_path.name,"backgroundColor":bg_color,
              "showControls":show_controls,"premultipliedAlpha":False,"rawDataURIs":raw}
    if animation:
        config["animation"] = animation
    if skin:
        config["skin"] = skin
    encoded = json.dumps(config,ensure_ascii=False).replace("</","<\\/")
    cdn = f"https://unpkg.com/@esotericsoftware/spine-player@{runtime_version}/dist/"
    return f'''<!doctype html><html lang="en"><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{html.escape(title)}</title><script src="{cdn}iife/spine-player.js"></script><link rel="stylesheet" href="{cdn}spine-player.css">
<style>body{{background:#141d29;color:#eee;font:16px system-ui;margin:24px}}#player{{width:95vw;height:78vh}}p{{font-size:13px;color:#a1bdc8}}</style>
<h1>{html.escape(title)}</h1><p>Assets embedded; player {html.escape(runtime_version)} loads from a CDN. Engine compatibility must be checked separately.</p>
<div id="status">Loading runtime…</div><div id="player"></div><script>
const config={encoded};config.success=()=>document.querySelector('#status').textContent='Loaded';
config.error=(player,reason)=>document.querySelector('#status').textContent='Error: '+reason;
new spine.SpinePlayer('player',config);</script></html>'''


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--skeleton",type=Path,required=True)
    parser.add_argument("--atlas",type=Path,required=True)
    parser.add_argument("--atlas-image",type=Path)
    parser.add_argument("--output",type=Path,default=Path("preview.html"))
    parser.add_argument("--animation")
    parser.add_argument("--skin")
    parser.add_argument("--background",default="#1a1a2eff")
    parser.add_argument("--title",default="Spine Animation Preview")
    parser.add_argument("--runtime-version",help="Player version; JSON defaults to its declared major/minor")
    parser.add_argument("--no-controls",action="store_true")
    parser.add_argument("--overwrite",action="store_true")
    args=parser.parse_args()
    try:
        images=find_atlas_images(args.atlas)
        if args.atlas_image:
            if len(images)!=1:
                raise ValueError("--atlas-image can override only a one-page atlas")
            images=[(images[0][0],str(args.atlas_image))]
        if args.output.exists() and not args.overwrite:
            raise ValueError("Output exists; choose a versioned path or --overwrite")
        page=generate_html(args.skeleton,args.atlas,images,args.animation,args.skin,args.background,
                           not args.no_controls,args.title,args.runtime_version)
        args.output.parent.mkdir(parents=True,exist_ok=True)
        args.output.write_text(page,encoding="utf-8")
    except (ValueError,OSError,KeyError,TypeError) as exc:
        parser.exit(2,f"ERROR: {exc}\n")
    print(f"Saved {args.output}; internet required for player CDN")


if __name__=="__main__":
    main()
