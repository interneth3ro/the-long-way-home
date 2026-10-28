extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only visual simulation; no objectives, inventory or recovery state.
@onready var _extractor: Node2D = $PreviewRoom/Extractor
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Extractor/Machine.material

var _outline_enabled: bool = false


func _ready() -> void:
	super._ready()
	_update_extractor_readout()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	match event.keycode:
		KEY_O:
			_outline_enabled = not _outline_enabled
			_outline_material.set_shader_parameter("outline_enabled", _outline_enabled)
		KEY_V:
			_extractor.visible = not _extractor.visible
		_:
			super._unhandled_key_input(event)
			_update_extractor_readout()
			return
	_update_extractor_readout()
	get_viewport().set_input_as_handled()


func _update_extractor_readout() -> void:
	_readout.text = ("DEVELOPMENT ONLY | Extractor visual simulation | World 1.25x\n"
		+ "WASD/arrows: move | Wheel: zoom | O: objective outline | V: installed/removed\n"
		+ "C: collision outlines | H: HUD | No recovery or progression\n"
		+ "Extractor: %s | Objective outline: %s | Outlines: %s" % [
			"INSTALLED" if _extractor.visible else "REMOVED (visual only)",
			"ON" if _outline_enabled else "OFF",
			"ON" if _outlines.visible else "OFF"])
