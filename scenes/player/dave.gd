extends CharacterBody2D

const MOVEMENT_SPEED: float = 240.0


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * MOVEMENT_SPEED
	move_and_slide()
