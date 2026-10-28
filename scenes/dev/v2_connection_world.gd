extends Node2D

# Presentation adapter for the existing arrival hook; geometry stays room-owned.
const DaveController = preload("res://scenes/player/dave.gd")
@export var arrival_facing: DaveController.Facing = DaveController.Facing.WEST


func prepare_for_arrival(player: CharacterBody2D, _planet: PlanetWorldState) -> void:
	player.set("last_facing", arrival_facing)
	var animation := player.get_node("Visual/AnimationPlayer") as AnimationPlayer
	animation.play(DaveController.IDLE_ANIMATIONS[arrival_facing])
	animation.advance(0.0)
