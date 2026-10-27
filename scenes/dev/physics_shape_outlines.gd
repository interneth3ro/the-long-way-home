extends Node2D

# Development-only presentation. Shape resources remain the sole geometry source.
@export var environment: Node2D
@export var player: CharacterBody2D

const WALL_COLOR := Color(0.2, 1.0, 0.8, 1.0)
const PLAYER_COLOR := Color(1.0, 0.85, 0.2, 1.0)


func _process(_delta: float) -> void:
	if is_visible_in_tree():
		queue_redraw()


func _draw() -> void:
	_draw_shapes(environment, WALL_COLOR)
	# Show the unchanged feet circle too, excluding the interaction detector.
	_draw_shape(player.get_node("CollisionShape2D") as CollisionShape2D, PLAYER_COLOR)


func _draw_shapes(root: Node, color: Color) -> void:
	for child in root.get_children():
		if child is CollisionShape2D:
			_draw_shape(child, color)
		else:
			_draw_shapes(child, color)


func _draw_shape(collider: CollisionShape2D, color: Color) -> void:
	if collider.disabled or collider.shape == null:
		return
	var body := collider.get_parent() as CollisionObject2D
	if body == null or body.collision_layer == 0:
		return
	var points := PackedVector2Array()
	var shape := collider.shape
	var closed := false
	if shape is SegmentShape2D:
		points = PackedVector2Array([shape.a, shape.b])
	elif shape is ConvexPolygonShape2D:
		points = shape.points
		closed = true
	elif shape is CircleShape2D:
		for index in range(64):
			points.append(Vector2.from_angle(TAU * float(index) / 64.0) * shape.radius)
		closed = true
	else:
		# New physics types must explicitly add a resource-derived outline here.
		push_error("Unsupported preview collision shape: " + shape.get_class())
		return
	if points.size() < 2:
		return
	# Shape-local -> global -> overlay-local includes all ancestor transforms.
	var shape_to_overlay := global_transform.affine_inverse() * collider.global_transform
	points = shape_to_overlay * points
	if closed:
		points.append(points[0])
	draw_polyline(points, color, 1.5, true)
