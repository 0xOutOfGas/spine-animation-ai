# Quickstart for Codex

Install the global `spine-animation-codex` skill as described in [README.md](../README.md). Keep any project-local skill used by another agent intact. The skill reads local scripts in place and uses the native ChatGPT Image tool; no model key or alternate agent home path is required.

1. Supply separated transparent parts plus a reference, a complete image to decompose, or an existing Spine export. State the asset's purpose and desired actions. For Toywatch turrets, start with a static idle and short fire recoil.
2. Codex inspects the images. For artwork generation, missing hidden surfaces or reskins, use [the ChatGPT Image workflow](../references/chatgpt-image.md). Save the selected source, prompt and hashes.
3. Crop named measured regions with `scripts/split_character.py`; use automatic components only as a draft. Preserve alpha. Author measured geometry after reviewing the pixels.
4. Run `scripts/build_turret.py` for a fixed-base 360-degree turret, or the character helpers after constructing a real rig configuration from the positioning report.
5. Inspect the output at game scale and through an angle/recoil sweep. Verify it in the installed engine runtime before integrating presentation events.

Core dependencies: Python 3.10+, Pillow, NumPy (`requirements.txt`). OpenCV (`requirements-positioning.txt`) is optional. Use the available bundled runtime or a workspace venv. `--help` on each helper documents exact inputs. Outputs use fresh versioned directories/files by default.

A minimal reproducible sample:

```sh
python scripts/build_turret.py --config examples/toywatch-turret/rig.config.json --output output/turret-v1
python -m unittest discover -s tests -v
python build_skill.py --check
```

[Turret configuration](../references/toywatch-turrets.md) · [Godot integration](../references/godot.md) · [Validation scope](validation.md)
