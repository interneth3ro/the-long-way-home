extends Node2D

# Presentation-only image coordinates, never gameplay spawns or walkability data.
const DaveController = preload("res://scenes/player/dave.gd")
const IMAGE_CENTER := Vector2(768, 512)
const SCALE_OPTIONS: Array[float] = [1.0, 1.25, 1.5]
const COMPARISON_POINTS: Array[Vector2] = [
	Vector2(1270, 565), # Clear floor inside the right entrance
	Vector2(790, 700), # In front of the central repair platform
	Vector2(505, 385), # Beside the upper-left Extractor foundation
	Vector2(1010, 385), # Beside the upper-right Smelter foundation
	Vector2(520, 810), # Beside the lower-left Fabricator foundation
	Vector2(900, 335), # Below the closed reserved top door
]

@onready var _environment: Node2D = $MaintenanceBayV2
@onready var _dave: DaveController = $Dave
@onready var _camera: Camera2D = $Dave/Camera2D
@onready var _readout: Label = $PreviewHUD/Readout

var _scale_index: int = 1


func _ready() -> void:
	# PR #47 isolation: only this instance loses collision and interactions.
	_dave.get_node("InteractionDetector").process_mode = Node.PROCESS_MODE_DISABLED
	_dave.get_node("CollisionShape2D").set("disabled", true)
	_dave.get_node("InteractionUI").hide()
	_dave.get_node("DialogueUI").hide()
	_dave.last_facing = DaveController.Facing.WEST
	_place_at(0)
	_update_readout()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_1:
			_set_scale(0)
		KEY_2:
			_set_scale(1)
		KEY_3:
			_set_scale(2)
		KEY_4:
			_place_at(0)
		KEY_5:
			_place_at(1)
		KEY_6:
			_place_at(2)
		KEY_7:
			_place_at(3)
		KEY_8:
			_place_at(4)
		KEY_9:
			_place_at(5)
		KEY_H:
			_readout.visible = not _readout.visible
		_:
			return
	get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	_update_readout()


func _set_scale(index: int) -> void:
	# Keep Dave at the same image-space point without scaling him or camera zoom.
	var image_position := _dave.position / _environment.scale.x
	_scale_index = index
	_environment.scale = Vector2.ONE * SCALE_OPTIONS[index]
	_dave.position = image_position * _environment.scale.x
	_dave.velocity = Vector2.ZERO
	_camera.reset_smoothing()
	_camera.force_update_scroll()


func _place_at(index: int) -> void:
	_dave.position = (COMPARISON_POINTS[index] - IMAGE_CENTER) * _environment.scale.x
	_dave.velocity = Vector2.ZERO
	_camera.reset_smoothing()
	_camera.force_update_scroll()


func _update_readout() -> void:
	_readout.text = (
		"DEVELOPMENT ONLY | World %.2fx | Camera %.2fx | Walk through artwork: expected\n"
		+ "1 / 2 / 3: world 1.0 / 1.25 / 1.5x | WASD / arrows: move | Wheel: zoom | H: HUD\n"
		+ "4: entry | 5: repair platform | 6: Extractor | 7: Smelter | 8: Fabricator | 9: top door\n"
		+ "Empty foundations only | No collision, interactions or travel | Scale pending owner review"
	) % [SCALE_OPTIONS[_scale_index], _camera.zoom.x]
