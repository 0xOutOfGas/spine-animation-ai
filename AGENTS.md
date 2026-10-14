# Codex Spine fork

- Keep the upstream license, authorship and history. Record adaptation changes in commits and `CHANGELOG.md`.
- `SKILL.template.md` is the short instruction source; `python build_skill.py` updates `SKILL.md`. Scripts are executed in place, not embedded into instructions.
- ChatGPT Image is the native generation/editing path. Python helpers consume existing local files; they must not call Gemini, Anthropic or an image API, or require model API keys.
- Core dependencies are Pillow and NumPy. Keep OpenCV optional outside the positioning helper. Use workspace environments rather than system package replacement.
- Turret root and base are stationary. Animation must not key `aim`; runtime code controls it after animation application. Recoil is local to the barrel axis and muzzles inherit it. Keep Simulation authoritative for shots and damage.
- Run meaningful tests for changed scripts and validate real engine loading when claiming engine compatibility. A geometry preview is not a Spine runtime.
- Preserve existing game art and working trees. Do not publish unrelated private project files in this public fork.
