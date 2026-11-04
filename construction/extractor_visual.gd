class_name ExtractorVisual
extends Node2D

# Frozen package crops in body / raised barrel / foreground order.
# Offsets already subtract master anchor (632,1139); never subtract it again.
const TEXTURES := [
	[
		preload("res://assets/machines/extractor/extractor_0_body.png"),
		preload("res://assets/machines/extractor/extractor_0_barrel.png"),
		preload("res://assets/machines/extractor/extractor_0_foreground.png"),
	],
	[
		preload("res://assets/machines/extractor/extractor_90_body.png"),
		preload("res://assets/machines/extractor/extractor_90_barrel.png"),
		preload("res://assets/machines/extractor/extractor_90_foreground.png"),
	],
	[
		preload("res://assets/machines/extractor/extractor_180_body.png"),
		preload("res://assets/machines/extractor/extractor_180_barrel.png"),
		preload("res://assets/machines/extractor/extractor_180_foreground.png"),
	],
	[
		preload("res://assets/machines/extractor/extractor_270_body.png"),
		preload("res://assets/machines/extractor/extractor_270_barrel.png"),
		preload("res://assets/machines/extractor/extractor_270_foreground.png"),
	],
]
const OFFSETS := [
	[Vector2(-566, -1102), Vector2(-312, -865), Vector2(-336, -873)],
	[Vector2(-483, -1124), Vector2(-44, -874), Vector2(-356, -883)],
	[Vector2(-563, -1118), Vector2(131, -886), Vector2(109, -898)],
	[Vector2(-525, -1124), Vector2(-98, -871), Vector2(-196, -903)],
]

@onready var _layers: Array[Sprite2D] = [$Body, $Barrel, $Foreground]
var _turns: int = -1


func configure(quarter_turns: int) -> void:
	var direction := posmod(quarter_turns, 4)
	if direction == _turns:
		return
	_turns = direction
	for index in range(_layers.size()):
		_layers[index].texture = TEXTURES[direction][index]
		_layers[index].position = OFFSETS[direction][index]
