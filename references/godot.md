# Godot integration

The skill produces assets; it does not silently install a runtime or change the game's engine. Inspect the actual `project.godot`, existing GDExtension and skeleton format version. Godot and Spine runtime versions are separate. Use the official [spine-godot documentation](https://esotericsoftware.com/spine-godot) to select a compatible runtime, subject to the [Spine runtime/editor license](https://esotericsoftware.com/spine-editor-license).

Current Godot importers use `.spine-json` for JSON data, `.skel` for binary, `.atlas` plus its PNG. Keep the files and relative texture page names together. The turret builder emits JSON, not binary or a `.spine` editor project. A `.skel` export requires the actual Spine editor/export tools.

Create a SpineSkeletonDataResource using the imported skeleton and atlas, then bind it to a SpineSprite. Keep its parent at the gameplay socket, sprite rotation zero and uniform display scale from the manifest. Resource import/caching differs from raw disk loading; the official `13-load-from-disk` example shows the latter. [assets/godot/stationary_turret.gd](../assets/godot/stationary_turret.gd) is an integration helper for the generated subset.

## Aim ordering and muzzle transforms

Connect `before_world_transforms_change`. In that callback the AnimationState pose has already been applied, so set the `aim` bone rotation there. The 4.3 wrapper exposes the mutable pose via `bone.get_pose().set_rotation`; 4.2 exposes `bone.set_rotation`. The helper inspects the method and supports both instead of assuming one wrapper API. Do not write aim from a generic `_process` callback before Spine poses the frame, and do not key aim in fire/idle clips.

Convert the target via the sprite's `to_local(global_target)` so camera zoom, parent scale and transforms are accounted for. Screen forward is Y-down; the Spine angle is its negative. A near-zero target vector retains the previous aim. Reacquire bone wrappers from the current sprite after a resource reload.

Use `get_global_bone_transform("muzzle_main")` after `world_transforms_changed` for visual effects. This includes aim, recoil and the Godot canvas transform. Do not hand-roll a second Y inversion or derive a nozzle from axis-aligned sprite bounds. This coordinate is a presentation attachment; maintain Simulation's established logical shot origin and event timing.

## Event and pause behavior

`present_shot(stable_event_id)` starts the non-looping fire clip and queues idle. New shots replace the current track rather than accumulating unbounded fire clips. The helper deduplicates a bounded recent-event window; reset it on a new replay/session. It never emits damage or projectile commands.

The game's presentation clock controls when aim and shot events are delivered. Freeze the Spine sprite's processing with the game pause, then restore its previous process mode on resume. The helper supplies `set_presentation_paused`; integration still must wire the actual game's pause and session lifecycle.

Check native loading, full yaw+recoil, rest pose, repeated shots, pause and transformed muzzle attachment coordinates. State exactly which version/platform was verified. The offline Canvas preview checks geometry and visual assembly but does not constitute a Spine or Godot compatibility check.
