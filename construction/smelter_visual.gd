class_name SmelterVisual
extends Node2D

# Four independently illustrated views. Slots stay body/interior/heat/foreground.
# Offsets already subtract each direction's ground anchor; never subtract twice.
const TEXTURES := [
	[
		preload("res://assets/machines/smelter/smelter_0_body.png"),
		preload("res://assets/machines/smelter/smelter_0_interior.png"),
		preload("res://assets/machines/smelter/smelter_0_illumination.png"),
		preload("res://assets/machines/smelter/smelter_0_foreground.png"),
	],
	[
		preload("res://assets/machines/smelter/smelter_90_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_90_illumination.png"),
		null,
	],
	[
		preload("res://assets/machines/smelter/smelter_180_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_180_illumination.png"),
		null,
	],
	[
		preload("res://assets/machines/smelter/smelter_270_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_270_illumination.png"),
		null,
	],
]
const OFFSETS := [
	[Vector2(-571, -999), Vector2(-8, -439), Vector2(-400, -987), Vector2(-72, -460)],
	[Vector2(-467, -1144), Vector2.ZERO, Vector2(-72, -1130), Vector2.ZERO],
	[Vector2(-596, -1039), Vector2.ZERO, Vector2(256, -1021), Vector2.ZERO],
	[Vector2(-463, -1100), Vector2.ZERO, Vector2(-101, -897), Vector2.ZERO],
]

@onready var _layers: Array[Sprite2D] = [$Body, $Interior, $Illumination, $Foreground]
var _turns: int = -1


func configure(quarter_turns: int) -> void:
	var direction := posmod(quarter_turns, 4)
	if direction == _turns:
		return
	_turns = direction
	for index in range(_layers.size()):
		_layers[index].texture = TEXTURES[direction][index]
		_layers[index].position = OFFSETS[direction][index]
		# Static idle in every operating state; heat remains a frozen hidden slot.
		_layers[index].visible = TEXTURES[direction][index] != null and index != 2
