---
name: spine-animation-codex
description: Create or refine Spine 2D rigs and animations in Codex, using ChatGPT Image for artwork and local scripts for export. Use for character animation, stationary turret recoil and 360-degree aiming, or Spine assets intended for Godot.
---

# Spine animation in Codex

Use Codex vision and reasoning to identify parts, pivots, hierarchy and timing; use the built-in ChatGPT Image tool for creating or revising artwork; execute the bundled scripts for reproducible data and texture processing. Read only the references needed for the requested asset.

## Choose the workflow

- **Stationary turrets, especially Toywatch:** read [references/toywatch-turrets.md](references/toywatch-turrets.md). Start with `idle` and `fire`, a fixed root/base, an externally controlled aim bone and local barrel recoil. Use `scripts/build_turret.py`.
- **Characters or an existing Spine export:** read [references/character-workflow.md](references/character-workflow.md) and [references/spine-json-spec.md](references/spine-json-spec.md). Preserve the existing rig and animation names when refining it. Use `scripts/position_parts.py`, `scripts/build_spine_json.py` and `scripts/make_atlas.py` as appropriate.
- **New artwork, missing hidden surfaces or a reskin:** read [references/chatgpt-image.md](references/chatgpt-image.md). Produce or edit the parts with the built-in `image_gen` tool, inspect the actual output, then crop measured regions with `scripts/split_character.py`. Generation and creative edits happen through the tool; the Python script processes existing pixels locally.

## Local execution

Resolve `SKILL_DIR` from the location of this loaded `SKILL.md`; run its scripts in place. Do not extract embedded scripts or assume an operating system, home directory or global install location. Write outputs in the user's workspace at a named versioned destination. Keep intermediate files outside formal assets.

Inspect the existing project instructions and source state before editing. Select an available Python with Pillow and NumPy; OpenCV is optional and only needed for automatic connected components or SIFT positioning. In Codex Desktop, `load_workspace_dependencies` can locate the bundled runtime. If dependencies are missing, use a workspace virtual environment and `python -m pip install -r "$SKILL_DIR/requirements.txt"`; install `requirements-positioning.txt` only for positioning. Avoid system-wide package changes.

The built-in image tool needs no API key. This skill's scripts make no model or image-service requests. Use the installed `imagegen` skill when available; if the native image tool is unavailable, explain that limitation. An API fallback requires the user's explicit choice.

## Work from measured assets

Inspect each source or generated image with `view_image`, including alpha edges and the intended game display size. Prompted part names, positions and dimensions are intentions, not measured data. Use a named region manifest for sheets with disconnected details; automatic component splitting is a draft that needs semantic naming and visual review. Do not estimate exact pivots or muzzles from the prompt.

Keep a generation record: final prompt, tool, reference roles, selected source file and SHA-256. Record measured canvas, part placement, pivot, forward vector, draw order and muzzle points in the rig configuration. When correcting a placement, preserve the source and record the original value and applied delta.

Keep skeleton format and runtime versions explicit. Use `.spine-json` for current Godot importers. A successful HTML preview does not prove engine compatibility. For integration, read [references/godot.md](references/godot.md) and check the target project's installed runtime. Spine runtime/editor licensing and the upstream PolyForm Noncommercial license remain applicable.

## Deliver and check

Deliver skeleton data, atlas and texture together with the source configuration and hashes. Run changed scripts and inspect the generated artifacts. For turrets, check a full angle sweep and recoil at 72px/cell: socket/base stay fixed, aim survives animation application, recoil follows the barrel, muzzle positions follow the visual attachment, and all clips restore their rest pose. The builder emits a geometry preview and an alpha-envelope report; verify the assets in the actual runtime before describing them as game-ready.

Animations and their events control presentation. The game simulation remains the source of attack timing, damage and projectile decisions. Preserve pause behavior and use stable event identities to avoid duplicate presentation shots. Report the exact source identity, commands, checks and any engine or visual checks not performed.
