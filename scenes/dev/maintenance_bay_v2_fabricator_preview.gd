extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only, session-only position tuning; retire after V2 migration audit.
# Outline width/color are fixed in the reusable scene, never adjusted here.
@onready var _fabricator: Node2D = $PreviewRoom/Fabricator
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Fabricator/Machine.material

var _initial_position: Vector2
var _outline_enabled: bool = false


func _ready() -> void:
	super._ready()
	_initial_position = _fabricator.position
	_update_fabricator_readout()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	# Leave editor/OS shortcuts alone; Shift is reserved for coarse position steps.
	if event.ctrl_pressed or event.alt_pressed or event.meta_pressed:
		return
	if event.shift_pressed and event.keycode not in [KEY_I, KEY_K, KEY_J, KEY_L]:
		return
	var step: float = 5.0 if event.shift_pressed else 1.0
	match event.keycode:
		KEY_I:
			_fabricator.position.y -= step
		KEY_K:
			_fabricator.position.y += step
		KEY_J:
			_fabricator.position.x -= step
		KEY_L:
			_fabricator.position.x += step
		KEY_R:
			# Reset position only; retain simulated removal and requested outline.
			_fabricator.position = _initial_position
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
	var current := _fabricator.position
	var delta := current - _initial_position
	_readout.text = ("DEVELOPMENT ONLY | Fabricator visual simulation | World 1.25x\n"
		+ "I/K: up/down | J/L: left/right | Step: 1 room pixel; Shift: 5 | R: reset position only\n"
		+ "O: outline | V: installed/removed | C: collision outlines | H: HUD\n"
		+ "WASD/arrows: move | Wheel: zoom | Session-only tuning\n"
		+ "Room-local: X=%.2f; Y=%.2f | Initial: X=%.2f; Y=%.2f | Delta: X=%.2f; Y=%.2f\n" % [
			current.x, current.y, _initial_position.x, _initial_position.y, delta.x, delta.y]
		+ "Outline: %s | Fabricator: %s | Collision outlines: %s\n" % [
			"ON" if _outline_enabled else "OFF",
			"INSTALLED" if _fabricator.visible else "REMOVED (simulation)",
			"ON" if _outlines.visible else "OFF"]
		+ "Fixed outline: width=20.0 source texels; opacity=1.00\n"
		+ "COPY THESE VALUES: X=%.2f; Y=%.2f\n" % [current.x, current.y]
		+ "Visual only: walk-through machine; no recovery or production.")
