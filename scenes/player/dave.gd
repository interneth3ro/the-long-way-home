extends CharacterBody2D

const MOVEMENT_SPEED: float = 240.0

@onready var static_sprite: Sprite2D = $Visual/Sprite2D
@onready var walking_sprite: Sprite2D = $Visual/WalkSouthSprite
@onready var north_walking_sprite: Sprite2D = $Visual/WalkNorthSprite
@onready var animation_player: AnimationPlayer = $Visual/AnimationPlayer


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * MOVEMENT_SPEED
	move_and_slide()
	_update_walk_animation(direction)


func _update_walk_animation(direction: Vector2) -> void:
	# Only straight north/south input animates; idle and diagonals use static art.
	var walking_south := direction.y > 0.0 and is_zero_approx(direction.x)
	var walking_north := direction.y < 0.0 and is_zero_approx(direction.x)
	if walking_south or walking_north:
		var animation_name: StringName = &"walk_north" if walking_north else &"walk_south"
		if not animation_player.is_playing() or animation_player.current_animation != animation_name:
			animation_player.play(animation_name)
			animation_player.advance(0.0)
	else:
		animation_player.stop()
	static_sprite.visible = not (walking_south or walking_north)
	walking_sprite.visible = walking_south
	north_walking_sprite.visible = walking_north
