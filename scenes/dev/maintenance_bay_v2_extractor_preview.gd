extends "res://scenes/dev/maintenance_bay_v2_collision_preview.gd"

# Development-only visual simulation; no objectives, inventory or recovery state.
@onready var _extractor: Node2D = $PreviewRoom/Extractor
@onready var _outline_material: ShaderMaterial = $PreviewRoom/Extractor/Machine.material

var _outline_enabled: bool = false
var _baseline_position: Vector2
var _baseline_width: float
var _baseline_color: Color
var _tuning_y: float
var _tuning_width: float
var _tuning_color: Color


func _ready() -> void:
	super._ready()
	# Private runtime copy: never change another instance or serialize tuning.
	_outline_material = _outline_material.duplicate() as ShaderMaterial
	$PreviewRoom/Extractor/Machine.material = _outline_material
	_baseline_position = _extractor.position
	_baseline_width = float(_outline_material.get_shader_parameter("outline_width"))
	_baseline_color = _outline_material.get_shader_parameter("outline_color")
	_reset_tuning()
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
		KEY_I:
			_tuning_y -= 5.0 if event.shift_pressed else 1.0
		KEY_K:
			_tuning_y += 5.0 if event.shift_pressed else 1.0
		KEY_U:
			_tuning_width = clampf(_tuning_width - 1.0, 0.0, 20.0)
		KEY_P:
			_tuning_width = clampf(_tuning_width + 1.0, 0.0, 20.0)
		KEY_J:
			_tuning_color.a = clampf(snappedf(_tuning_color.a - 0.05, 0.05), 0.0, 1.0)
		KEY_L:
			_tuning_color.a = clampf(snappedf(_tuning_color.a + 0.05, 0.05), 0.0, 1.0)
		KEY_R:
			_reset_tuning()
		KEY_C, KEY_H:
			# Inherited controls own handling; rebuild with current tuning afterward.
			super._unhandled_key_input(event)
			_update_extractor_readout()
			return
		_:
			return
	_apply_tuning()
	_update_extractor_readout()
	get_viewport().set_input_as_handled()


func _reset_tuning() -> void:
	_tuning_y = _baseline_position.y
	_tuning_width = _baseline_width
	_tuning_color = _baseline_color
	_apply_tuning()


func _apply_tuning() -> void:
	_extractor.position = Vector2(_baseline_position.x, _tuning_y)
	_outline_material.set_shader_parameter("outline_width", _tuning_width)
	_outline_material.set_shader_parameter("outline_color", _tuning_color)


func _update_extractor_readout() -> void:
	_readout.text = ("EXTRACTOR TUNING (DEV ONLY) | World 1.25x | Not saved\n"
		+ "I/K: up/down 1 room unit | Shift+I/K: 5 | U/P: width -/+1 | J/L: opacity -/+0.05\n"
		+ "O: outline | V: installed/removed | C: collision | H: HUD | R: reset tuning only\n"
		+ "WASD/arrows: move | Wheel: zoom | No recovery or progression\n"
		+ "Position X: %.2f | Position Y: %.2f (room-local) | Y delta from baseline: %+.2f\n" % [
			_extractor.position.x, _tuning_y, _tuning_y - _baseline_position.y]
		+ "Outline width: %.0f source texels [0-20] | Outline opacity: %.2f [0-1]\n" % [
			_tuning_width, _tuning_color.a]
		+ "Baseline: Y = %.2f; width = %.0f; opacity = %.2f\n" % [
			_baseline_position.y, _baseline_width, _baseline_color.a]
		+ "COPY THESE VALUES: Y = %.2f; width = %.0f; opacity = %.2f\n" % [
			_tuning_y, _tuning_width, _tuning_color.a]
		+ "Outline: %s | Extractor: %s | Outlines: %s" % [
			"ON" if _outline_enabled else "OFF",
			"INSTALLED" if _extractor.visible else "REMOVED (visual simulation)",
			"ON" if _outlines.visible else "OFF"])
