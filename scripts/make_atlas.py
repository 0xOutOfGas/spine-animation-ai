#!/usr/bin/env python3
"""Pack untrimmed RGBA parts into a deterministic Spine atlas with edge padding."""
import argparse
import math
from pathlib import Path

from PIL import Image
from asset_io import asset_name


def next_pow2(value):
    return 1 << max(0, int(value-1).bit_length())


def pack(images, padding=2):
    if not images or padding < 1:
        raise ValueError("At least one image and positive padding are required")
    ordered = sorted(images.items(), key=lambda item: (-item[1].height, item[0]))
    area = sum((im.width+2*padding)*(im.height+2*padding) for im in images.values())
    width = next_pow2(max(max(im.width+2*padding for im in images.values()), math.ceil(math.sqrt(area))))
    x, y, row_height = padding, padding, 0
    placements = {}
    for name, im in ordered:
        asset_name(name)
        if x + im.width + padding > width:
            x, y, row_height = padding, y+row_height+2*padding, 0
        placements[name] = (x, y, im.width, im.height)
        x += im.width+2*padding
        row_height = max(row_height, im.height)
    height = next_pow2(y+row_height+padding)
    if max(width, height) > 8192:
        raise ValueError("Atlas exceeds 8192px; reduce source sizes or split the asset")
    return width, height, placements


def write_atlas(images, output, name, padding=2):
    name, output = asset_name(name), Path(output)
    if any((output / (name+suffix)).exists() for suffix in (".png", ".atlas")):
        raise ValueError("Atlas destination exists; choose a new version")
    images = {k: im.convert("RGBA") for k, im in images.items()}
    width, height, placements = pack(images, padding)
    atlas = Image.new("RGBA", (width, height))
    for region, (x, y, w, h) in placements.items():
        im = images[region]
        # Extend border texels without changing region coordinates or source alpha.
        for dx, dy, crop in ((-padding, 0, (0, 0, 1, h)), (w, 0, (w-1, 0, w, h)),
                             (0, -padding, (0, 0, w, 1)), (0, h, (0, h-1, w, h))):
            strip = im.crop(crop)
            strip = strip.resize((padding, h) if dx else (w, padding), Image.Resampling.NEAREST)
            atlas.paste(strip, (x+dx, y+dy))
        for sx, sy, dx, dy in ((0,0,-padding,-padding), (w-1,0,w,-padding),
                               (0,h-1,-padding,h), (w-1,h-1,w,h)):
            atlas.paste(Image.new("RGBA", (padding, padding), im.getpixel((sx,sy))), (x+dx,y+dy))
        atlas.paste(im, (x, y))
    output.mkdir(parents=True, exist_ok=True)
    atlas.save(output / (name+".png"))
    lines = [name+".png", f"size: {width},{height}", "format: RGBA8888",
             "filter: Linear,Linear", "repeat: none", "pma: false"]
    for region, (x, y, w, h) in placements.items():
        lines.extend([region, "  rotate: false", f"  xy: {x}, {y}", f"  size: {w}, {h}",
                      f"  orig: {w}, {h}", "  offset: 0, 0", "  index: -1"])
    (output / (name+".atlas")).write_text("\n".join(lines)+"\n", encoding="utf-8")
    return placements


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--parts", type=Path, required=True)
    parser.add_argument("--output", type=Path, default=Path("."))
    parser.add_argument("--name", default="skeleton")
    parser.add_argument("--padding", type=int, default=2)
    args = parser.parse_args()
    try:
        images = {p.stem: Image.open(p).convert("RGBA") for p in sorted(args.parts.glob("*.png"))}
        placements = write_atlas(images, args.output, args.name, args.padding)
    except (OSError, ValueError) as exc:
        parser.exit(2, f"ERROR: {exc}\n")
    print(f"Packed {len(placements)} regions into {args.output / (args.name+'.atlas')}")


if __name__ == "__main__":
    main()
