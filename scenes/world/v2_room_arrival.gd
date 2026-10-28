extends Node2D

const DaveController = preload("res://scenes/player/dave.gd")


# Controller has already placed Dave at a marker. Facing is presentation only.
func prepare_for_arrival(player: CharacterBody2D, _planet: PlanetWorldState) -> void:
	var nearest: Marker2D
	var distance: float = INF
	for child in $Spawns.get_children():
		var marker := child as Marker2D
		if marker != null:
			var candidate := player.global_position.distance_squared_to(marker.global_position)
			if candidate < distance:
				nearest = marker
				distance = candidate
	var facing: int = nearest.get_meta(&"facing")
	player.set("last_facing", facing)
	var animation := player.get_node("Visual/AnimationPlayer") as AnimationPlayer
	animation.play(DaveController.IDLE_ANIMATIONS[facing])
	animation.advance(0.0)
