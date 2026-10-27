extends Node2D

# Development presentation only. These image-space comparison points are not
# gameplay spawns, walkability promises or transition destinations.
const IMAGE_CENTER := Vector2(768, 512)
const SCALE_OPTIONS: Array[float] = [1.0, 1.25, 1.5]
const COMPARISON_POINTS: Array[Vector2] = [
	Vector2(768, 335), # Computer
	Vector2(285, 520), # Maintenance doorway
	Vector2(855, 645), # Wreckage
	Vector2(760, 800), # Exterior hatch
	Vector2(680, 535), # Open center
]

@onready var _visuals: Node2D = $ShipInteriorV2/VisualContent
@onready var _dave: CharacterBody2D = $Dave
@onready var _camera: Camera2D = $Dave/Camera2D
@onready var _readout: Label = $PreviewHUD/Readout

var _scale_index: int = 0


func _ready() -> void:
	# Keep Dave's movement, artwork and camera unchanged; disable only this
	# instance's interaction queries and body shape in the isolated harness.
	_dave.get_node("InteractionDetector").process_mode = Node.PROCESS_MODE_DISABLED
	_dave.get_node("CollisionShape2D").set("disabled", true)
	_dave.get_node("InteractionUI").hide()
	_dave.get_node("DialogueUI").hide()
	_place_at(4)
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
		KEY_H:
			_readout.visible = not _readout.visible
		_:
			return
	get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	_update_readout()


func _set_scale(index: int) -> void:
	# Preserve Dave's image-space location while scaling every room layer through
	# one common parent. Dave's own size and the camera zoom stay unchanged.
	var image_position := _dave.position / _visuals.scale.x
	_scale_index = index
	_visuals.scale = Vector2.ONE * SCALE_OPTIONS[index]
	_dave.position = image_position * _visuals.scale.x
	_dave.velocity = Vector2.ZERO
	_camera.reset_smoothing()
	_camera.force_update_scroll()


func _place_at(index: int) -> void:
	_dave.position = (COMPARISON_POINTS[index] - IMAGE_CENTER) * _visuals.scale.x
	_dave.velocity = Vector2.ZERO
	_camera.reset_smoothing()
	_camera.force_update_scroll()


func _update_readout() -> void:
	_readout.text = (
		"DEVELOPMENT ONLY | World %.2fx | Camera %.2fx | No collision / interactions\n"
		+ "1 / 2 / 3: world 1.0 / 1.25 / 1.5x | WASD / arrows: move | Wheel: camera zoom\n"
		+ "4: Computer | 5: maintenance | 6: wreckage | 7: hatch | 8: center | H: hide HUD"
	) % [SCALE_OPTIONS[_scale_index], _camera.zoom.x]
