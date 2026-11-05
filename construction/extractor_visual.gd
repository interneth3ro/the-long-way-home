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
# Provisional presentation choices, independent of ore-production timing.
const STROKE_PX := [8.0, 8.0, 6.0, 6.0]
const HALF_STROKE_SECONDS := 0.8
var _turns: int = -1
var _producing: bool = false
var _motion: Tween


func configure(quarter_turns: int) -> void:
	var direction := posmod(quarter_turns, 4)
	if direction == _turns:
		return
	_stop_motion()
	_turns = direction
	for index in range(_layers.size()):
		_layers[index].texture = TEXTURES[direction][index]
		_layers[index].position = OFFSETS[direction][index]
	_start_motion()


func set_producing(producing: bool) -> void:
	if _producing == producing:
		return
	_producing = producing
	_stop_motion()
	_start_motion()


func _start_motion() -> void:
	if not _producing or not is_inside_tree() or _turns < 0 or _motion != null:
		return
	var raised: Vector2 = OFFSETS[_turns][1]
	_motion = create_tween().set_loops()
	_motion.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_motion.tween_property($Barrel, "position", raised + Vector2(0, STROKE_PX[_turns]), HALF_STROKE_SECONDS)
	_motion.tween_property($Barrel, "position", raised, HALF_STROKE_SECONDS)


func _stop_motion() -> void:
	if _motion != null:
		_motion.kill()
		_motion = null
	if _turns >= 0:
		$Barrel.position = OFFSETS[_turns][1]


func _exit_tree() -> void:
	_producing = false
	_stop_motion()
