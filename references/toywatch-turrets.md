# Toywatch stationary turrets

Read the current game's `AGENTS.md`, `game/project.godot`, `docs/m0.md` and `docs/art.md` before integrating assets. The values below are a presentation profile observed in the project on 2026-10-14, not permission to change its rules. The skill's generic `stationary_turret` profile permits explicitly authored display budgets; Toywatch exceptions such as stationary Tank geometry need their own documented profile instead of silently raising every turret's limit.

## Rig and animation ownership

```text
root (gameplay socket, never animated)
├── base (stationary artwork)
└── aim (procedural yaw, never animated)
    └── recoil (local slide opposite the barrel's forward vector)
        └── muzzle_* (visual effect socket, inherits aim and recoil)
```

Map visible parts to `base`, `aim` or `recoil`. The ordered `parts` list is the constant back-to-front draw order. A truly overhead receiver remains valid through 360 degrees. Fixed front/back supports that occlude a turning barrel need a different art decomposition; do not reuse a side-view cradle with a ±35° pitch limit as a top-down yaw rig.

Default clips are **idle** (static, loop) and **fire** (non-looping, 0.18s). Add build/hit/destroy/charge only if the actual game requires them, through a deliberate rig extension; omit walk/run/jump and baked directional turns. A new shot restarts fire and returns to idle without queuing an ever-growing list of shots. Rapid shots must still preserve aim and restore the rest pose.

Target angle comes from the game's current target in the turret's local coordinate system. Apply it after AnimationState poses the skeleton and before world transforms update. Use the shortest wrapped angle if smoothing; position and collision remain at the fixed socket. Never mirror the head to aim behind it.

Simulation owns firing, damage, attack count and logical projectile decisions. Animation clips/events cannot fire weapons. A stable shot event identity starts the visual recoil once. Visual muzzle coordinates may move during recoil; retain the game's established logical projectile origin and damage contract. Multiple muzzle sockets support alternating barrels, not extra damage events.

## Measured configuration

```json
{
  "name":"toy-turret", "profile":"toywatch_turret", "spine_version":"4.3.26",
  "canvas_size_px":[256,256], "pivot_px":[128,128], "forward_px":[1,0],
  "display_size_px":64, "cell_size_px":72, "head_max_radius_cell":0.45,
  "parts":[
    {"name":"base","role":"base","file":"parts/base.png","position_px":[68,68]},
    {"name":"receiver","role":"aim","file":"parts/receiver.png","position_px":[78,78]},
    {"name":"barrel","role":"recoil","file":"parts/barrel.png","position_px":[111,108]}
  ],
  "muzzles":[{"name":"main","position_px":[221,128]}],
  "fire":{"duration":0.18,"peak_time":0.03,"recover_time":0.18,"recoil_cell":0.01}
}
```

Declare the installed runtime's version; do not relabel incompatible exports. Current builder supports the shared 4.2/4.3 region/translate subset. Canvas is a positive square. `position_px` is each source image's top-left in that canonical canvas. `pivot_px` is the fixed socket in canvas pixels. `forward_px` is normalized by the builder and denotes the art's rest firing direction in Y-down pixels. All placements/muzzles must fit within the canonical canvas. Sources can be full-canvas transparent layers or cropped sprites with measured offsets.

The example dimensions assume base 120×120, receiver 100×100 and barrel 112×40. Replace them and their positions with actual measurements, including the muzzle at the barrel's exit. The builder never infers them from the prompt.

Pixel → Spine: `(x-pivot.x, pivot.y-y)`. Aim and recoil originate at that pivot. All attachment offsets use the full untrimmed part center; image dimensions are not scaled twice. Godot sprite scale is `display_size_px / canvas_width`, applied once. A screen yaw becomes its negative in the Spine Y-up pose. Forward can be diagonal; it need not be hardcoded right.

Toywatch profile enforces rotating head radius ≤0.45 cell and recoil ≤0.01 cell. The report scans every alpha>0 texel's four corners in rest and maximum recoil. Rigid yaw preserves radius; squared radius along linear recoil is convex, so these two endpoints bound the entire animation and all aim angles. Fixed base is reported independently. Faint edge pixels count. Adjust the art or measured display size if the profile rejects it; do not hide pixels with a threshold.

```sh
python "$SKILL_DIR/scripts/build_turret.py" --config rig.config.json --output output/turret-v1
```

The output directory must be new. It contains portable `rig.config.json` and `images/`, runtime `.spine-json`, `.atlas`/`.png`, a manifest with hashes and geometry evidence, and a standalone Canvas geometry preview. Regenerating the portable config reproduces the core artifacts.

## Acceptance

Inspect idle and peak recoil at 0/30/…/330 degrees and the actual 72px grid scale. Check the base crosshair, upper pivot, barrel overlap and every muzzle. In the installed Godot runtime, sweep full yaw while applying both clips; the aim angle must survive pose application. Check repeated shots, return to rest, pause/unpause and zoom/camera transforms. Verify visual anchors after world transforms change. Loading is an engine check; it does not establish the appearance or game's combat regression. See [godot.md](godot.md).
