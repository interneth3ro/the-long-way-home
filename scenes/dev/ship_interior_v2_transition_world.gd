extends Node2D


func prepare_for_arrival(player: CharacterBody2D, _planet: PlanetWorldState) -> void:
	# Development-only presentation via the existing arrival hook. Apply before
	# fade-in, without changing production Dave or adding facing to the contract.
	var from_maintenance := player.global_position.is_equal_approx($Spawns/FromMaintenance.global_position)
	player.set("last_facing", 3 if from_maintenance else 1)
	var animation := player.get_node("Visual/AnimationPlayer") as AnimationPlayer
	animation.play(&"idle_east" if from_maintenance else &"idle_north")
	animation.advance(0.0)
