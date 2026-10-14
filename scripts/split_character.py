#!/usr/bin/env python3
"""Crop a ChatGPT Image parts sheet locally; this helper never generates images.

Prefer --regions for semantic parts. --auto drafts connected alpha components
and requires OpenCV; disconnected details should be grouped by named rectangles.
"""
import argparse
import json
from pathlib import Path

import numpy as np
from PIL import Image
from asset_io import asset_name, sha256, write_json


def split_sheet(source, output, regions=None, auto=False, min_area=64, padding=2):
    source, output = Path(source), Path(output)
    if output.exists():
        raise ValueError(f"Output already exists: {output}; choose a versioned directory")
    if padding < 0 or min_area < 1:
        raise ValueError("padding must be nonnegative and min-area must be positive")
    image = Image.open(source).convert("RGBA")
    alpha = np.asarray(image.getchannel("A"))
    if not (alpha < 255).any():
        raise ValueError("Input has no transparent background. Request alpha from ChatGPT Image first")
    masks = {}
    if auto:
        try:
            import cv2
        except ImportError as exc:
            raise ValueError("--auto needs OpenCV; use --regions or install requirements-positioning.txt") from exc
        count, labels, stats, _ = cv2.connectedComponentsWithStats((alpha > 0).astype(np.uint8), connectivity=8)
        accepted = [(i, s) for i, s in enumerate(stats[1:], 1) if s[4] >= min_area]
        accepted.sort(key=lambda item: (int(item[1][1]), int(item[1][0])))
        regions = {"parts": []}
        for index, (label, stat) in enumerate(accepted):
            x, y, w, h = map(int, stat[:4])
            left, top = max(0, x-padding), max(0, y-padding)
            right, bottom = min(image.width, x+w+padding), min(image.height, y+h+padding)
            name = f"part_{index:02d}"
            regions["parts"].append({"name": name, "rect": [left, top, right-left, bottom-top]})
            masks[name] = labels[top:bottom, left:right] == label
    if not isinstance(regions, dict) or not isinstance(regions.get("parts"), list) or not regions["parts"]:
        raise ValueError("A nonempty parts list is required")
    items, used = [], set()
    for spec in regions["parts"]:
        name = asset_name(spec["name"])
        if name in used:
            raise ValueError(f"Duplicate part: {name}")
        used.add(name)
        rect = spec.get("rect")
        if not isinstance(rect, list) or len(rect) != 4 or any(type(v) is not int for v in rect):
            raise ValueError(f"{name}: rect must be four integer pixels")
        x, y, w, h = rect
        if min(x, y) < 0 or min(w, h) <= 0 or x+w > image.width or y+h > image.height:
            raise ValueError(f"{name}: rect is outside the image")
        crop = image.crop((x, y, x+w, y+h))
        if name in masks:
            pixels = np.array(crop)
            pixels[~masks[name]] = 0
            crop = Image.fromarray(pixels)
        if crop.getchannel("A").getbbox() is None:
            raise ValueError(f"{name}: crop is empty")
        pivot = spec.get("pivot_px")
        if pivot is not None and (len(pivot) != 2 or not all(isinstance(v, (int, float)) and np.isfinite(v) for v in pivot)):
            raise ValueError(f"{name}: invalid crop-local pivot_px")
        items.append((crop, {"name": name, "file": name+".png", "rect_px": rect,
                             "pivot_px": pivot, "alpha_bbox_px": list(crop.getchannel("A").getbbox())}))
    output.mkdir(parents=True)
    manifest = {"schema": 1, "source_sha256": sha256(source), "source_size_px": list(image.size),
                "mode": "auto-draft" if auto else "named-regions", "parts": []}
    for crop, entry in items:
        path = output / entry["file"]
        crop.save(path)
        entry["sha256"] = sha256(path)
        manifest["parts"].append(entry)
    write_json(output / "parts.manifest.json", manifest)
    return manifest


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_image", type=Path, help="Existing transparent parts sheet")
    parser.add_argument("--output-dir", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--regions", type=Path, help="JSON with named parts and crop rectangles")
    mode.add_argument("--auto", action="store_true", help="Draft unnamed alpha components")
    parser.add_argument("--min-area", type=int, default=64)
    parser.add_argument("--padding", type=int, default=2)
    args = parser.parse_args()
    try:
        regions = json.loads(args.regions.read_text(encoding="utf-8")) if args.regions else None
        result = split_sheet(args.input_image, args.output_dir, regions, args.auto, args.min_area, args.padding)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    print(json.dumps({"output": str(args.output_dir), "parts": len(result["parts"]), "mode": result["mode"]}))


if __name__ == "__main__":
    main()
