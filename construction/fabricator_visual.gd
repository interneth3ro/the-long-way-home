class_name FabricatorVisual
extends Node2D

# Accepted front resting composite and three static side/rear crops.
# Offsets already subtract each view's ground anchor; never translate twice.
const TEXTURES := [
	preload("res://assets/machines/fabricator/fabricator_0_resting.png"),
	preload("res://assets/machines/fabricator/fabricator_90_body.png"),
	preload("res://assets/machines/fabricator/fabricator_180_body.png"),
	preload("res://assets/machines/fabricator/fabricator_270_body.png"),
]
const OFFSETS := [
	Vector2(-627, -1080),
	Vector2(-659, -1044),
	Vector2(-586, -1001),
	Vector2(-672, -971),
]
const SCALES := [8.0 / 65.0, 32.0 / 305.0, 32.0 / 265.0, 16.0 / 155.0]

@onready var _body: Sprite2D = $Body
var _turns: int = 0
var _applied_turns: int = -1


func _ready() -> void:
	configure(_turns)


func configure(quarter_turns: int) -> void:
	_turns = posmod(quarter_turns, 4)
	# Retain pre-ready configuration; repeated calls leave the static view alone.
	if not is_node_ready() or _applied_turns == _turns:
		return
	_body.texture = TEXTURES[_turns]
	_body.position = OFFSETS[_turns]
	scale = Vector2.ONE * SCALES[_turns]
	_applied_turns = _turns
