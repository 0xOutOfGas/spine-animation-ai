extends Node2D
## Presentation helper for a generated base/aim/recoil turret. Simulation owns shots.
## Assign a SpineSprite whose skeleton_data_res is already imported.
@export var spine_sprite: Node2D
@export var rest_forward := Vector2.RIGHT
var _screen_angle := 0.0
var _recent_ids: Dictionary = {}
var _id_order: Array[String] = []
var _paused := false
var _saved_process_mode: int = Node.PROCESS_MODE_INHERIT

func _ready() -> void:
	assert(spine_sprite != null)
	assert(spine_sprite.has_signal("before_world_transforms_change"))
	spine_sprite.connect("before_world_transforms_change", _apply_aim)
	var state = spine_sprite.call("get_animation_state")
	state.call("set_animation", "idle", true, 0)

func aim_at(global_target: Vector2) -> void:
	var direction := spine_sprite.to_local(global_target)
	if direction.length_squared() > 0.000001:
		_screen_angle = wrapf(direction.angle() - rest_forward.angle(), -PI, PI)

func _apply_aim(_sprite = null) -> void:
	# Reacquire wrappers: resource reloads invalidate previously retained bones.
	var skeleton = spine_sprite.call("get_skeleton")
	if skeleton == null:
		return
	var bone = skeleton.call("find_bone", "aim")
	if bone == null:
		return
	var degrees := -rad_to_deg(_screen_angle)
	if bone.has_method("get_pose"):
		bone.call("get_pose").call("set_rotation", degrees) # Spine 4.3
	else:
		bone.call("set_rotation", degrees) # Spine 4.2

func present_shot(stable_event_id: String) -> bool:
	if _paused or stable_event_id.is_empty() or _recent_ids.has(stable_event_id):
		return false
	_recent_ids[stable_event_id] = true
	_id_order.append(stable_event_id)
	if _id_order.size() > 128:
		_recent_ids.erase(_id_order.pop_front())
	var state = spine_sprite.call("get_animation_state")
	state.call("set_animation", "fire", false, 0)
	state.call("add_animation", "idle", true, 0, 0.0)
	return true

func visual_muzzle_transform(muzzle_name: String = "main") -> Transform2D:
	# Call after world_transforms_changed. This is a visual attachment, not damage logic.
	return spine_sprite.call("get_global_bone_transform", "muzzle_" + muzzle_name)

func set_presentation_paused(value: bool) -> void:
	if _paused == value:
		return
	_paused = value
	if value:
		_saved_process_mode = spine_sprite.process_mode
		spine_sprite.process_mode = Node.PROCESS_MODE_DISABLED
	else:
		spine_sprite.process_mode = _saved_process_mode

func reset_session() -> void:
	_recent_ids.clear()
	_id_order.clear()
