extends CharacterBody2D
## Position is Dave's ground contact point; Visual can be replaced independently.

@export var movement_speed: float = 220.0


func _physics_process(_delta: float) -> void:
	var direction := Input.get_vector("move_left", "move_right", "move_up", "move_down")
	velocity = direction * movement_speed
	move_and_slide()
