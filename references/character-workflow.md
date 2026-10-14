# Characters and existing rigs

Inspect supplied parts and the assembled reference first. If existing skeleton/atlas data is supplied, preserve the established hierarchy, slots, skin names, source scale and runtime version while making the requested changes. New hidden surfaces or reskins use [ChatGPT Image](chatgpt-image.md).

For matching parts to a reference, the optional OpenCV helper uses SIFT/RANSAC and alpha-aware template matching:

```sh
python "$SKILL_DIR/scripts/position_parts.py" --reference reference.png --parts parts/ --output layout.json --debug debug/
```

Inspect `debug/comparison.png` and low-confidence/occluded parts. **layout.json is a positioning report, not a skeleton configuration.** Codex must use the measured layout, joint pivots and visual draw order to author bones, parent-relative positions and attachment offsets. It cannot be passed directly to the skeleton builder.

For region-only humanoid rigs, `build_spine_json.py` accepts `bones`, `slots`, `attachments`, preset names and custom animations. Presets depend on the documented humanoid bone names; inspect the result rather than assuming a matching name means a correct joint. Use `skeleton.spine_version` to declare the runtime. Presets use normalized authoring easing internally and are converted to 4.x wire format.

Custom animations are **already Spine wire format by default** and are preserved verbatim. Set `custom_animation_format: "shorthand"` only for this helper's legacy normalized easing/`angle` authoring format. This prevents applying the normalized curve conversion a second time to a valid exported animation.

```sh
python "$SKILL_DIR/scripts/build_spine_json.py" --config rig.json --output output/hero.spine-json
python "$SKILL_DIR/scripts/make_atlas.py" --parts parts/ --output output/ --name hero
python "$SKILL_DIR/scripts/generate_spine_player.py" --skeleton output/hero.spine-json --atlas output/hero.atlas --output output/hero-preview.html
```

The official player preview embeds assets but requires the indicated runtime's CDN files. It is not an offline artifact. Use the actual Godot/Spine runtime for format validation and [the JSON reference](spine-json-spec.md) for 4.x curves. For a stationary turret, use the dedicated turret builder rather than humanoid animation presets.
