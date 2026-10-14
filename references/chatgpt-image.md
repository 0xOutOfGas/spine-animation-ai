# ChatGPT Image artwork and reskins

Use the built-in `image_gen` tool for image generation and creative edits. Read the available `imagegen` skill for its current tool parameters. Use `transparent_background: true` for parts. The native tool does not need `OPENAI_API_KEY`; do not invent a Python client for it or switch to an external provider.

For a local reference/edit target, inspect it with `view_image` first. Supply its actual local path with `referenced_image_paths`, or use the smallest set of recent conversation images when there is no path. Do not combine those mechanisms. Keep the tool's source output; copy the selected result into a named workspace destination before referencing it in the project. The tool determines its initial save location; it has no assumed destination argument.

Use ChatGPT's vision to inspect the result at source resolution and at the game display scale. Record what is measured rather than trusting dimensions in the prompt. If a single assembled image has hidden joints, use an image edit to complete the hidden material; a crop cannot reconstruct it.

## Stationary turret art

Request an orthographic view directly overhead. Base, rotating receiver and recoiling barrel need complete independent silhouettes. Keep the source forward direction explicit, normally screen-right. A stationary base should use symmetric or overhead lighting; perspective, a visible vertical muzzle bore or a directional ground shadow can make a rotated sprite look like it is rolling. Inspect the whole 360-degree contact sheet.

Example prompt:

> Produce three isolated transparent components of the same cheerful toy cannon: fixed round pedestal, overhead rotating receiver without the barrel, and a separate right-pointing overhead barrel. Keep the same palette and scale. Use complete hidden surfaces under overlaps. Strictly orthographic directly above; no side faces, perspective ellipses, text, ground shadow or additional assembled cannon. The barrel's muzzle is a thin terminal edge from above. Leave generous gaps.

Separate calls per part are useful when a sheet merges parts or mis-scales them. Use a common reference and repeat visual invariants for each edit. Do not repeatedly regenerate the whole design to correct one joint.

## Reskin

Keep part identity, canvas size, pivots, silhouettes and overlap material stable. Edit the relevant source part using ChatGPT Image, compare old/new alpha boundaries, then repack the atlas without changing the measured rig. If the silhouette changes, explicitly review the pivot, muzzle and envelope rather than assuming the old geometry still fits. Avoid recoloring a flattened assembly and cutting arbitrary boxes through overlapping parts.

## Local crop manifest

`scripts/split_character.py` operates on an existing transparent sheet. It performs no generation or background-removal request. Named rectangles preserve disconnected details and all source alpha, including white artwork:

```json
{"parts":[{"name":"base","rect":[20,20,200,200],"pivot_px":[100,100]},
          {"name":"barrel","rect":[300,80,180,70],"pivot_px":[20,35]}]}
```

Rectangles are measured sheet-local `[x,y,width,height]`; optional pivots are crop-local. Run:

```sh
python "$SKILL_DIR/scripts/split_character.py" parts-sheet.png --regions regions.json --output-dir parts-v1
```

`--auto` is an OpenCV connected-alpha draft, useful only for clean isolated components. It cannot identify semantic parts and may separate decorative islands. Name and group parts after viewing the output; prefer named rectangles if that would preserve a complete part. An opaque input is rejected so white interior paint is never silently erased.

Save `generation.json` containing the final prompt, the native tool name, reference roles, selected source filename/hash and deterministic crop/resample operations. Do not store API keys or private absolute paths in a public fork.
