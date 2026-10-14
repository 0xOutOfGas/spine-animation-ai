# Spine Animation for Codex

A Codex adaptation of [GenielabsOpenSource/spine-animation-ai](https://github.com/GenielabsOpenSource/spine-animation-ai), based on upstream commit `702b71689cac826efee942ee4564fef9560d6ef8`.

Codex handles asset analysis, measured rig design and iteration. ChatGPT Image creates or revises the artwork through the native image tool. Local Python helpers crop existing pixels, create Spine data, pack atlases and produce previews. No image-service API key is required by this workflow.

The adapted skill is named **`spine-animation-codex`**. Install it globally for Codex. A project's existing `spine-animation` skill can remain available for another agent without replacing its files.

## Install

Clone the adaptation branch into your user skills directory:

```sh
git clone --branch codex/codex-toywatch https://github.com/0xOutOfGas/spine-animation-ai.git ~/.codex/skills/spine-animation-codex
```

If that destination exists, preserve it and inspect the current version before updating. The skill is available on the next Codex turn. Invoke it as `$spine-animation-codex` or request a Spine rig, turret recoil or Godot animation workflow. See [SKILL.md](SKILL.md).

## Stationary turret example

The minimal turret has `root → base` and `root → aim → recoil → muzzle_*`. `idle` is a static loop; `fire` is a short, non-looping return-to-rest recoil. Aim is applied by runtime code after animation posing. There are no locomotion clips or baked turns. A top-down asset can be aimed through 360 degrees while its base and gameplay socket stay fixed.

```sh
python scripts/build_turret.py --config examples/toywatch-turret/rig.config.json --output output/turret-v1
```

Outputs: `.spine-json`, `.atlas`, `.png`, portable source images/config, hashes, an alpha-envelope report and an offline geometry `preview.html`. Open the preview to sweep angles, fire and inspect the same asset at the 72px cell scale. This preview does not load the Spine runtime; use [the Godot reference](references/godot.md) for engine verification.

[Toywatch turret geometry and configuration](references/toywatch-turrets.md) documents pivots, forward vectors, muzzles, recoil and draw order. It uses the project's current presentation budgets: head radius ≤0.45 cell and recoil ≤0.01 cell. Check the current game rules before reusing those defaults; model behavior never comes from animation events.

## Characters, artwork and reskins

- [Character workflow](references/character-workflow.md): reference matching, measured joints, existing-rig refinement and humanoid presets.
- [ChatGPT Image workflow](references/chatgpt-image.md): generation, targeted edits, transparent parts, and reskin invariants.
- [JSON format reference](references/spine-json-spec.md): 4.x timelines and coordinate conventions.
- [Quickstart](docs/getting-started.md): local commands and dependencies.

Python 3.10+, Pillow and NumPy are sufficient for the named-region and turret pipelines. OpenCV is optional for automatic components and SIFT matching. Prefer the available Codex bundled runtime or a workspace virtual environment:

```sh
python -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
# Only for SIFT or automatic component drafts:
.venv/bin/python -m pip install -r requirements-positioning.txt
```

Paths shown are shell examples; the skill resolves its own loaded location and runs scripts in place on the user's operating system. It does not extract scripts into a service-specific home directory or replace system packages.

## Maintenance and evidence

Edit `SKILL.template.md`, run `python build_skill.py`, then `python build_skill.py --check`. The entrypoint stays short; supporting scripts are not embedded into the prompt. Run `python -m unittest discover -s tests -v` for helper behavior. The CI workflow checks the entrypoint and these tests without making commits or deploying a site.

Changes and scope are recorded in [CHANGELOG.md](CHANGELOG.md), commits and [validation evidence](docs/validation.md). Upstream examples remain as historical demonstrations. The separate upstream web reskin application was retired from this adaptation; Codex performs image edits through its native tool and keeps the local deterministic pipeline.

## License and credits

The upstream **PolyForm Noncommercial 1.0.0** [LICENSE](LICENSE) is preserved. Commercial use of this code requires permission from the original licensor. Spine runtime/editor licensing is separate; see [Spine's licensing terms](https://esotericsoftware.com/spine-editor-license). This fork does not change either license.

Original rigging, atlas and animation helpers: Genielabs contributors. Codex adaptation: ChatGPT Image workflow, local processing, stationary turret builder, preview and Godot integration recipe. Spine is by Esoteric Software; OpenCV, Pillow and NumPy support the local asset pipeline.
