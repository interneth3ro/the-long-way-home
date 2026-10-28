extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only, session-local tuning; retirement-audit candidate after approval.
# Keep the shared shader's accepted 0..20 source-texel range unchanged.
const MIN_WIDTH: float = 0.0
const MAX_WIDTH: float = 20.0

@onready var _smelter: Node2D = $PreviewRoom/Smelter
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Smelter/Machine.material

var _initial_position: Vector2
var _initial_width: float
var _initial_color: Color
var _outline_width: float
var _outline_color: Color
var _outline_enabled: bool = false


func _ready() -> void:
	super._ready()
	# The reusable scene marks its material local to each instantiated scene.
	_initial_position = _smelter.position
	_initial_width = _outline_material.get_shader_parameter("outline_width")
	_initial_color = _outline_material.get_shader_parameter("outline_color")
	_reset_tuning()
	_apply_tuning()


func _unhandled_key_input(event: InputEvent) -> void:
	if not event is InputEventKey or not event.pressed or event.echo:
		return
	# Leave editor/OS modifier shortcuts alone; Shift only changes movement step.
	if event.ctrl_pressed or event.alt_pressed or event.meta_pressed:
		return
	var step: float = 5.0 if event.shift_pressed else 1.0
	match event.keycode:
		KEY_I:
			_smelter.position.y -= step
		KEY_K:
			_smelter.position.y += step
		KEY_J:
			_smelter.position.x -= step
		KEY_L:
			_smelter.position.x += step
		KEY_U:
			_outline_width = clampf(_outline_width - 1.0, MIN_WIDTH, MAX_WIDTH)
		KEY_P:
			_outline_width = clampf(_outline_width + 1.0, MIN_WIDTH, MAX_WIDTH)
		KEY_BRACKETLEFT:
			_outline_color.a = clampf(_outline_color.a - 0.05, 0.0, 1.0)
		KEY_BRACKETRIGHT:
			_outline_color.a = clampf(_outline_color.a + 0.05, 0.0, 1.0)
		KEY_O:
			_outline_enabled = not _outline_enabled
		KEY_V:
			_smelter.visible = not _smelter.visible
		KEY_R:
			_reset_tuning()
		KEY_C, KEY_H:
			super._unhandled_key_input(event)
			_update_smelter_readout()
			return
		_:
			return
	_apply_tuning()
	get_viewport().set_input_as_handled()


func _reset_tuning() -> void:
	_smelter.position = _initial_position
	_outline_width = _initial_width
	_outline_color = _initial_color
	_outline_enabled = false
	_smelter.show()
	_outlines.hide()
	_readout.show()


func _apply_tuning() -> void:
	_outline_material.set_shader_parameter("outline_enabled", _outline_enabled)
	_outline_material.set_shader_parameter("outline_width", _outline_width)
	_outline_material.set_shader_parameter("outline_color", _outline_color)
	_update_smelter_readout()


func _update_smelter_readout() -> void:
	var delta_position := _smelter.position - _initial_position
	_readout.text = ("DEVELOPMENT ONLY | Smelter visual simulation | World 1.25x\n"
		+ "I/K: up/down | J/L: left/right (1 room px; Shift: 5)\n"
		+ "U/P: width -/+1 texel [0..20] | [/]: opacity -/+0.05\n"
		+ "O: outline | V: installed/removed | R: reset all tuning\n"
		+ "C: collision outlines | H: HUD | WASD/arrows: move | Wheel: zoom\n"
		+ "X=%.2f; Y=%.2f | width=%.1f texels; opacity=%.2f\n" % [
			_smelter.position.x, _smelter.position.y, _outline_width, _outline_color.a]
		+ "Outline: %s | Smelter: %s | Collision outlines: %s\n" % [
			"ON" if _outline_enabled else "OFF",
			"INSTALLED" if _smelter.visible else "REMOVED (simulation)",
			"ON" if _outlines.visible else "OFF"]
		+ "Defaults: X=%.2f; Y=%.2f; width=%.1f; opacity=%.2f; OFF/installed\n" % [
			_initial_position.x, _initial_position.y, _initial_width, _initial_color.a]
		+ "Delta: X=%+.2f; Y=%+.2f; width=%+.1f; opacity=%+.2f\n" % [
			delta_position.x, delta_position.y,
			_outline_width - _initial_width, _outline_color.a - _initial_color.a]
		+ "COPY THESE VALUES: X=%.2f; Y=%.2f; width=%.1f; opacity=%.2f\n" % [
			_smelter.position.x, _smelter.position.y, _outline_width, _outline_color.a]
		+ "Visual only: walk-through machine; no recovery, production or saved tuning.")
