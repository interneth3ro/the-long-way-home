extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only visual simulation; placement and material values are locked.
# Preview scene/script remain candidates for the later V2 retirement audit.
@onready var _fabricator: Node2D = $PreviewRoom/Fabricator
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Fabricator/Machine.material

var _outline_enabled: bool = false


func _ready() -> void:
	super._ready()
	_update_fabricator_readout()


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
			_fabricator.visible = not _fabricator.visible
		KEY_C, KEY_H:
			super._unhandled_key_input(event)
			_update_fabricator_readout()
			return
		_:
			return
	_update_fabricator_readout()
	get_viewport().set_input_as_handled()


func _update_fabricator_readout() -> void:
	_readout.text = ("DEVELOPMENT ONLY | Fabricator visual simulation | World 1.25x\n"
		+ "O: outline | V: installed/removed | C: collision outlines | H: HUD\n"
		+ "WASD/arrows: move | Wheel: zoom\n"
		+ "Outline: %s | Fabricator: %s | Collision outlines: %s\n" % [
			"ON" if _outline_enabled else "OFF",
			"INSTALLED" if _fabricator.visible else "REMOVED (simulation)",
			"ON" if _outlines.visible else "OFF"]
		+ "Fixed outline: width=20.0 source texels; opacity=1.00\n"
		+ "Visual only: walk-through machine; no recovery or production.")
