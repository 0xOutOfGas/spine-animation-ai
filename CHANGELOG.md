# Adaptation changes

## Codex adaptation · 2026-10-14

Base: GenielabsOpenSource/spine-animation-ai at `702b71689cac826efee942ee4564fef9560d6ef8`. The upstream license and Git history are retained.

- Name the global skill `spine-animation-codex` to distinguish it from project-local skills used by other agents.
- Replace the large embedded-script entrypoint with a short Codex router and on-demand references. Resolve the loaded skill path and use workspace environments.
- Use built-in ChatGPT Image for generation, targeted edits and reskins. Replace the image-service splitting helper with deterministic transparent-sheet cropping and source hashes.
- Retire the separate upstream reskin web app and its external image/model provider stack from the adaptation branch. Upstream history retains the original implementation.
- Add a measured stationary turret builder with only idle/fire, fixed root/base, procedural aim, local directional recoil, inherited muzzles, exact alpha-corner envelopes and versioned portable export bundles.
- Add an offline geometry preview, a Godot integration helper and verification of real runtime behavior.
- Make atlas packing deterministic, preserve full region sizes and add extruded edge padding. Preserve wire-format custom character animations; fix conversion of one-key rotation timelines.
- Update official-player previews for Godot JSON extensions and explicit runtime selection. CI validates without making generated commits or deploying a site.

See [validation evidence](docs/validation.md). Implementation and follow-up repairs are recorded in the adaptation branch's Git commits.
