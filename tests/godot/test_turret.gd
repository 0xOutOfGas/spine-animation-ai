extends SceneTree
var failures := 0
var checks := 0

func _init() -> void:
	call_deferred("_run")

func check(value: bool, reason: String) -> void:
	checks += 1
	if not value:
		failures += 1
		push_error(reason)

func _run() -> void:
	if not ClassDB.class_exists("SpineSprite"):
		push_error("Spine runtime is not installed in this isolated project")
		quit(1)
		return
	var manifest: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://turret/toy-turret.manifest.json"))
	var data = ClassDB.instantiate("SpineSkeletonDataResource")
	data.set("atlas_res", load("res://turret/toy-turret.atlas"))
	data.set("skeleton_file_res", load("res://turret/toy-turret.spine-json"))
	var sprite = ClassDB.instantiate("SpineSprite")
	sprite.set("skeleton_data_res", data)
	sprite.set("update_mode", 2) # Manual: the test controls each pose/update step.
	sprite.scale = Vector2.ONE * float(manifest.godot_display_scale)
	var helper = Node2D.new()
	helper.set_script(load("res://stationary_turret.gd"))
	helper.set("spine_sprite", sprite)
	helper.position = Vector2(220, 160)
	helper.rotation = 0.31
	helper.scale = Vector2.ONE * 0.9
	helper.add_child(sprite)
	root.add_child(helper)
	var skeleton = sprite.call("get_skeleton")
	if skeleton == null:
		push_error("Generated JSON failed to create a native skeleton")
		quit(1)
		return
	var state = sprite.call("get_animation_state")
	var recoil_bone = skeleton.call("find_bone", "recoil")
	var aim_bone = skeleton.call("find_bone", "aim")
	var base_bone = skeleton.call("find_bone", "base")
	check(recoil_bone != null and aim_bone != null and base_bone != null, "Required bones are missing")
	sprite.call("update_skeleton", 0.0)
	var fixed_base: Transform2D = sprite.call("get_global_bone_transform", "base")
	var setup: Array = manifest.muzzles[0].setup_px
	var pivot: Array = manifest.pivot_px
	var muzzle := Vector2(float(setup[0])-float(pivot[0]), float(setup[1])-float(pivot[1]))
	var peak := float(manifest.fire.peak_time)
	var duration := float(manifest.fire.duration)
	var recoil_px := float(manifest.fire.recoil_source_px)
	for degrees in range(-360, 361, 15):
		var theta := deg_to_rad(float(degrees))
		var local_target := Vector2.from_angle(theta) * 100.0
		helper.call("aim_at", sprite.to_global(local_target))
		check(helper.call("present_shot", "yaw-" + str(degrees)), "Shot was rejected")
		sprite.call("update_skeleton", peak)
		var pose = aim_bone.call("get_pose")
		var actual := deg_to_rad(float(pose.call("get_rotation")))
		check(absf(wrapf(actual + theta, -PI, PI)) < 0.0001, "Aim overwritten by animation at %s" % degrees)
		check(is_equal_approx(float(base_bone.call("get_pose").call("get_rotation")), 0.0), "Base rotated")
		var base_now: Transform2D = sprite.call("get_global_bone_transform", "base")
		check(base_now.is_equal_approx(fixed_base), "Base moved under rotation or recoil")
		var muzzle_now: Transform2D = helper.call("visual_muzzle_transform")
		var expected: Vector2 = sprite.to_global((muzzle-Vector2(recoil_px,0)).rotated(theta))
		check(muzzle_now.origin.distance_to(expected) < 0.001, "Visual muzzle transform wrong at %s: %s vs %s" % [degrees,muzzle_now.origin,expected])
		sprite.call("update_skeleton", duration+0.05)
		check(absf(float(recoil_bone.call("get_pose").call("get_x"))) < 0.0001, "Recoil failed to restore")
		var rest: Transform2D = helper.call("visual_muzzle_transform")
		check(rest.origin.distance_to(sprite.to_global(muzzle.rotated(theta))) < 0.001, "Rest muzzle drift")
	check(helper.call("present_shot", "dedup"), "Fresh event rejected")
	sprite.call("update_skeleton", peak*0.5)
	check(not helper.call("present_shot", "dedup"), "Duplicate visual shot accepted")
	sprite.call("update_skeleton", peak*0.5)
	check(absf(float(recoil_bone.call("get_pose").call("get_x"))+recoil_px) < 0.001, "Duplicate reset recoil clock")
	for index in range(30):
		helper.call("present_shot", "rapid-"+str(index))
		sprite.call("update_skeleton", 1.0/120.0)
	sprite.call("update_skeleton", duration+0.2)
	check(absf(float(recoil_bone.call("get_pose").call("get_x"))) < 0.001, "Rapid shots left residual recoil")
	sprite.set("update_mode", 0) # Process, to verify actual scene processing pause.
	helper.call("present_shot", "pause")
	# Retain a looping track for this clock check so it cannot be disposed by a
	# queued idle transition during variable-duration scene frames.
	var track = state.call("set_animation", "fire", true, 0)
	await process_frame
	await process_frame
	helper.call("set_presentation_paused", true)
	var held := float(track.call("get_track_time"))
	for index in range(6):
		await process_frame
	check(is_equal_approx(float(track.call("get_track_time")),held), "Paused sprite advanced")
	helper.call("set_presentation_paused", false)
	for index in range(6):
		await process_frame
	check(float(track.call("get_track_time")) > held, "Unpaused sprite did not advance")
	helper.call("reset_session")
	check(helper.call("present_shot", "dedup"), "New session retained old event deduplication")
	print(JSON.stringify({"result":"PASS" if failures==0 else "FAIL", "checks":checks, "failures":failures,
		"yaw_samples":49,"rapid_shots":30,"engine":Engine.get_version_info().string,"spine_data":manifest.spine_version}))
	helper.queue_free()
	await process_frame
	quit(0 if failures==0 else 1)
