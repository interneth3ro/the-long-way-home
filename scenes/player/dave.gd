extends CharacterBody2D

const MOVEMENT_SPEED: float = 240.0
const WALK_ANIMATIONS = [&"walk_south", &"walk_north", &"walk_west", &"walk_east"]
const IDLE_ANIMATIONS = [&"idle_south", &"idle_north", &"idle_west", &"idle_east"]

enum Facing { SOUTH, NORTH, WEST, EAST }

var last_facing: Facing = Facing.SOUTH

@onready var animation_player: AnimationPlayer = $Visual/AnimationPlayer


func _ready() -> void:
	_update_walk_animation(Vector2.ZERO)


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * MOVEMENT_SPEED
	move_and_slide()
	_update_walk_animation(direction)


func _update_walk_animation(direction: Vector2) -> void:
	var walking := direction != Vector2.ZERO
	if walking:
		# Dominant axis selects presentation only; exact ties face horizontally.
		if absf(direction.x) >= absf(direction.y):
			last_facing = Facing.WEST if direction.x < 0.0 else Facing.EAST
		else:
			last_facing = Facing.NORTH if direction.y < 0.0 else Facing.SOUTH

	var animation_name: StringName = WALK_ANIMATIONS[last_facing] if walking else IDLE_ANIMATIONS[last_facing]
	if animation_player.current_animation != animation_name or not animation_player.is_playing():
		animation_player.play(animation_name)
		# Apply sheet, frame and anchor together before the next rendered frame.
		animation_player.advance(0.0)
