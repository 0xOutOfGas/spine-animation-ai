# Codex adaptation verification · 2026-10-14

Source base: upstream `702b71689cac826efee942ee4564fef9560d6ef8`; implementation identity is the adaptation branch's Git commit. [The runtime report](evidence/godot-20261014-final/report.json) records exact hashes of the helper, test, builder, skeleton, atlas, texture and native runtime used. Recorded hashes refer to the files actually checked, not an earlier PASS.

## Results and scope

- Skill creator `quick_validate.py`: PASS; concise Codex entrypoint with `spine-animation-codex` name. `build_skill.py --check`: PASS. Python syntax and Git whitespace checks: PASS.
- [Python helper tests](evidence/python-20261014.log): 13 PASS. They cover named/automatic alpha crops (including faint and white pixels), exact atlas pixels, deterministic packing, rest pose, aim ownership, diagonal recoil at all yaw samples, continuous recoil envelope bounds, Toywatch budget rejection, safe failed output, portable reproduction and 4.x custom curve preservation/player version selection.
- SIFT CLI check: one 112×96 textured part placed in a 400×320 reference at (150,100); recovered (150,100), scale 1, 23/23 inliers, score 1. Debug generation also completed. [Positioning report](evidence/sift-20261014.json).
- [Actual Godot runtime log](evidence/godot-20261014-final/runtime.log): 351 PASS, 0 failures, 49 yaw samples (-360° through 360° at 15° increments), 30 rapid shots. Checked native JSON/atlas loading, procedural aim after AnimationState application, stationary base, transformed world muzzle, peak recoil, return to rest, duplicate event handling, pause/resume and session reset. Engine: Godot `4.7.2.stable.official.ed1daf0bf`; skeleton: Spine `4.3.26`, existing Spine 4.3 GDExtension on macOS arm64. The licensed runtime is not distributed in this fork.
- [Browser geometry preview](evidence/preview-20261014/preview.jpg): visually inspected fixed base, assembled parts, 12 angles at rest/peak, native 72px cell scale and enlarged view. Browser controls enabled full sweep and repeat fire; the UI showed changing angles and `fire`/`idle`. Canvas geometry output is separate from the native engine check.
- Native ChatGPT Image was exercised for the sample. First generation showed a perspective muzzle; a targeted image edit changed the receiver/barrel to overhead silhouettes. [Generation record](../examples/toywatch-turret/generation.json) preserves the final prompt, source hash, measured crop rectangles and deterministic resampling. Head alpha-corner envelope: `0.3320650060001453 cell`, within the `0.45 cell` limit; recoil: `0.01 cell`.

## Failures and repairs

The first sandboxed Godot import could not write its ordinary user data/editor settings and crashed. It was rerun with the required filesystem access. A fresh immediate `--editor --import` also imported the assets then crashed during shutdown in this installed engine/runtime combination; [that failed attempt](evidence/godot-20261014/import.log) and its [FAIL report](evidence/godot-20261014/report.json) are retained.

The reproducible runner now starts the editor with `--quit-after 120`, allowing importer/editor frames to drain before exit, then runs the bounded native test. The final fresh isolated project returned 0 for both stages with no script/engine errors. This verifies the revised command; it does not claim that Godot's immediate cold `--import` shutdown issue was repaired in the engine.

Initial test-harness iterations also caught an inferred GDScript type error and use of the obsolete `get_current` track API; the final test uses a retained track returned by `set_animation`. Real native tests identified these instead of treating a parser exit code of zero as PASS. The runner requires a structured native PASS and rejects error output.

## Reproduce

Use a Python environment with `requirements-positioning.txt`. PyYAML is additionally needed by the separately installed system skill-creator validator. Verified Python runtime: 3.12.14; Pillow 12.3.0, NumPy 2.3.5, optional OpenCV 5.0.0; validator PyYAML 6.0.3.

```sh
python build_skill.py --check
python -m unittest discover -s tests -v
python tests/godot/run.py --godot "$GODOT" --runtime-bin "$SPINE_BIN" --evidence /path/to/new-evidence
```

`GODOT` is the actual editor executable. `SPINE_BIN` is an existing licensed compatible GDExtension `bin/` directory. The runner copies only this host's runtime into a temporary isolated project, not into the user's game; Godot still uses its normal local user-data/editor-settings directories. Fresh evidence destinations prevent accidental replacement of older results. Logs and SHA-256 identities are saved.

Not checked: Spine 4.2 native playback, other host platforms, a packaged game, Toywatch combat regression, actual game event wiring, or GPU/manual game rendering and sound. The example is independent demonstration artwork. No Toywatch gameplay source, project-local agent skill or existing game assets were changed by this adaptation.
