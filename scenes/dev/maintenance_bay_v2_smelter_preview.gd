extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only visual simulation; placement and material values are locked.

@onready var _smelter: Node2D = $PreviewRoom/Smelter
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Smelter/Machine.material

var _outline_enabled: bool = false


func _ready() -> void:
	super._ready()
	_update_smelter_readout()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	# Leave editor/OS modifier shortcuts alone.
	if event.ctrl_pressed or event.alt_pressed or event.meta_pressed:
		return
	match event.keycode:
		KEY_O:
			_outline_enabled = not _outline_enabled
			_outline_material.set_shader_parameter("outline_enabled", _outline_enabled)
		KEY_V:
			_smelter.visible = not _smelter.visible
		KEY_C, KEY_H:
			super._unhandled_key_input(event)
			_update_smelter_readout()
			return
		_:
			return
	_update_smelter_readout()
	get_viewport().set_input_as_handled()


func _update_smelter_readout() -> void:
	_readout.text = ("DEVELOPMENT ONLY | Smelter visual simulation | World 1.25x\n"
		+ "O: outline | V: installed/removed\n"
		+ "C: collision outlines | H: HUD | WASD/arrows: move | Wheel: zoom\n"
		+ "Outline: %s | Smelter: %s | Collision outlines: %s\n" % [
			"ON" if _outline_enabled else "OFF",
			"INSTALLED" if _smelter.visible else "REMOVED (simulation)",
			"ON" if _outlines.visible else "OFF"]
		+ "Visual only: walk-through machine; no recovery or production.")
