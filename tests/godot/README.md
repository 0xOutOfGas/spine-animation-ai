# Native runtime check

Run `python tests/godot/run.py --godot "$GODOT" --runtime-bin "$SPINE_BIN" --evidence /path/to/new-evidence` from this fork with an existing licensed Spine 4.3 GDExtension. This creates an isolated temporary project and records native output and hashes. It does not ship or install a runtime.

The sample uses Spine 4.3.26 JSON and the test exercises the 4.3 pose API. The helper also has a 4.2 pose-method path, but this test does not verify a 4.2 runtime. Tests run only after the bounded headless editor/import stage succeeds; the runtime stage must emit a structured PASS with zero failures, so a script parse error cannot be mistaken for success.

The checked target was Godot 4.7.2 on macOS arm64. The import stage uses editor frames before exit because immediate cold `--import` shutdown crashed on that target. See [recorded evidence](../../docs/validation.md).
