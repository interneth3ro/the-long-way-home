extends SceneTree
## Run with: godot --headless --path . --script tests/ship_foundation_test.gd

var failures: int = 0


func _initialize() -> void:
	call_deferred("run")


func check(condition: bool, description: String) -> void:
	if condition:
		print("PASS: ", description)
	else:
		push_error(description)
		failures += 1


func step_frames(count: int) -> void:
	for frame in count:
		await physics_frame
		await process_frame


func travel(player: CharacterBody2D, start: Vector2, actions: Array, frames: int) -> Vector2:
	player.position = start
	for action in actions:
		Input.action_press(action)
	await step_frames(frames)
	for action in actions:
		Input.action_release(action)
	var end := player.position
	await step_frames(2)
	return end


func run() -> void:
	var scene := load("res://scenes/main/main.tscn").instantiate() as Node2D
	root.add_child(scene)
	var player := scene.get_node("Actors/Dave") as CharacterBody2D
	var camera := player.get_node("Camera2D") as Camera2D
	await step_frames(3)
	var spawn := player.position
	check(not player.test_move(player.global_transform, Vector2.ZERO), "spawn is clear")
	var cardinal := await travel(player, spawn, ["move_right"], 30)
	var diagonal := await travel(player, spawn, ["move_right", "move_up"], 30)
	check(absf(cardinal.distance_to(spawn) - 110.0) < 5.0, "physics movement is 220 units/second")
	check(absf(diagonal.distance_to(spawn) - cardinal.distance_to(spawn)) < 1.0, "diagonal distance matches cardinal distance")
	for action in ["move_left", "move_right", "move_up", "move_down"]:
		var end := await travel(player, spawn, [action], 10)
		check(end.distance_to(spawn) > 30.0, "movement action: " + action)
	var wall_end := await travel(player, Vector2(400, 300), ["move_right"], 60)
	check(wall_end.x < 489.0 and wall_end.x > 480.0, "bulkhead blocks Dave's feet")
	var slide_end := await travel(player, Vector2(480, 280), ["move_right", "move_down"], 20)
	check(slide_end.x < 489.0 and slide_end.y > 315.0, "Dave slides along bulkheads")
	var obstacle_end := await travel(player, Vector2(800, 590), ["move_down"], 60)
	check(obstacle_end.y < 641.0 and obstacle_end.y > 630.0, "table collision stops Dave")
	for start in [Vector2(450, 464), Vector2(1018, 464)]:
		var end := await travel(player, start, ["move_right"], 45)
		check(end.x > start.x + 150.0, "open doorway is traversable")
	# Exercise the four outer hull walls from unobstructed approach points.
	for trial in [[Vector2(60, 464), "move_left", 0], [Vector2(1540, 464), "move_right", 1], [Vector2(800, 70), "move_up", 2], [Vector2(800, 930), "move_down", 3]]:
		var end := await travel(player, trial[0], [trial[1]], 30)
		check(end.x >= 35.0 and end.x <= 1565.0 and end.y >= 33.0 and end.y <= 967.0, "outer hull collision " + str(trial[2]))
	player.position = spawn
	await step_frames(2)
	check(camera.global_position.is_equal_approx(player.global_position), "camera follows Dave's ground position")
	camera.call("apply_zoom", -10.0)
	check(is_equal_approx(camera.zoom.x, 0.85), "minimum zoom clamps")
	camera.call("apply_zoom", 10.0)
	check(is_equal_approx(camera.zoom.x, 1.4), "maximum zoom clamps")
	Input.action_press("zoom_out")
	await step_frames(15)
	Input.action_release("zoom_out")
	check(camera.zoom.x < 1.4 and camera.zoom.x >= 0.85, "zoom input changes zoom")
	for level in [0.85, 1.4]:
		camera.call("apply_zoom", level)
		for corner in [Vector2(36, 34), Vector2(1564, 34), Vector2(36, 966), Vector2(1564, 966)]:
			player.position = corner
			await step_frames(2)
			camera.force_update_scroll()
			var center := camera.get_screen_center_position()
			var half := root.get_visible_rect().size / camera.zoom / 2.0
			check(center.x - half.x >= -0.1 and center.y - half.y >= -0.1 and center.x + half.x <= 1600.1 and center.y + half.y <= 1000.1, "camera view stays within room at " + str(corner) + " zoom " + str(level))
	var visual := player.get_node("Visual")
	player.remove_child(visual)
	visual.free()
	var replacement := Node2D.new()
	replacement.name = "Visual"
	player.add_child(replacement)
	var after_swap := await travel(player, spawn, ["move_right"], 10)
	check(after_swap.x > spawn.x + 30.0, "movement works after replacing Visual")
	scene.queue_free()
	await process_frame
	print("Ship foundation checks complete; failures: ", failures)
	quit(0 if failures == 0 else 1)
