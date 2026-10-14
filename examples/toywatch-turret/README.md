# ChatGPT Image turret sample

Independent generic artwork for exercising the Codex workflow, not an update to existing Toywatch art. [generation.json](generation.json) records the native tool, final edit prompt, source hash and crop/resample operations; [regions.json](regions.json) contains measured source-sheet rectangles. White and faint alpha inside these named crops are preserved. The original selected sheet is retained as `parts-sheet.png`.

The measured 256px canonical canvas uses a fixed (128,128) socket, a right-pointing barrel, three visible parts and one visual muzzle. Display scale is 64/256 at a 72px cell; head envelope is 0.332065 cell, recoil is 0.01 cell and fire lasts 0.18s. The exported clips are idle and fire.

Run `python scripts/build_turret.py --config examples/toywatch-turret/rig.config.json --output output/turret-v1` from the fork root, then open `preview.html` in the new output. [export/](export/) is the checked sample package. It includes a portable config and untrimmed images as well as runtime assets. [Native and visual verification](../../docs/validation.md) records the exact checks and remaining limits.
