class_name SmelterVisual
extends Node2D

# Four independently illustrated views. Slots stay body/interior/heat/foreground.
# Offsets already subtract each direction's ground anchor; never subtract twice.
const TEXTURES := [
	[
		preload("res://assets/machines/smelter/smelter_0_body.png"),
		preload("res://assets/machines/smelter/smelter_0_interior.png"),
		preload("res://assets/machines/smelter/smelter_0_illumination.png"),
		preload("res://assets/machines/smelter/smelter_0_foreground.png"),
	],
	[
		preload("res://assets/machines/smelter/smelter_90_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_90_illumination.png"),
		null,
	],
	[
		preload("res://assets/machines/smelter/smelter_180_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_180_illumination.png"),
		null,
	],
	[
		preload("res://assets/machines/smelter/smelter_270_body.png"),
		null,
		preload("res://assets/machines/smelter/smelter_270_illumination.png"),
		null,
	],
]
const OFFSETS := [
	[Vector2(-571, -999), Vector2(-8, -439), Vector2(-400, -987), Vector2(-72, -460)],
	[Vector2(-467, -1144), Vector2.ZERO, Vector2(-72, -1130), Vector2.ZERO],
	[Vector2(-596, -1039), Vector2.ZERO, Vector2(256, -1021), Vector2.ZERO],
	[Vector2(-463, -1100), Vector2.ZERO, Vector2(-101, -897), Vector2.ZERO],
]

@onready var _layers: Array[Sprite2D] = [$Body, $Interior, $Illumination, $Foreground]
const HEAT_LOW := 0.82
const HEAT_HIGH := 1.0
const WARMUP_SECONDS := 0.5
const HALF_PULSE_SECONDS := 1.8
const COOLDOWN_SECONDS := 1.0
var _turns: int = -1
var _status: PlanetWorldState.OperatingStatus = PlanetWorldState.OperatingStatus.INACTIVE
var _initialized: bool = false
var _thermal: Tween
var _generation: int = 0


func configure(quarter_turns: int) -> void:
	var direction := posmod(quarter_turns, 4)
	if direction == _turns:
		return
	_turns = direction
	for index in range(_layers.size()):
		_layers[index].texture = TEXTURES[direction][index]
		_layers[index].position = OFFSETS[direction][index]
		# Direction changes retain the heat sprite's opacity, visibility and tween.
		if index != 2:
			_layers[index].visible = TEXTURES[direction][index] != null


# The adapter supplies status; this presenter never reads simulation records.
func set_operating_status(status: PlanetWorldState.OperatingStatus, enabled: bool = true) -> void:
	if not enabled:
		reset_thermal()
		return
	if not is_node_ready() or not is_inside_tree() or _turns < 0:
		return
	if _initialized and _status == status:
		return
	var initialize := not _initialized
	_cancel_thermal()
	_status = status
	_initialized = true
	if initialize:
		# Fresh attachment/re-entry has no reliable offscreen thermal history.
		_set_heat(HEAT_LOW if status == PlanetWorldState.OperatingStatus.PRODUCING else 0.0)
		if status == PlanetWorldState.OperatingStatus.PRODUCING:
			_start_pulse(_generation)
		return
	match status:
		PlanetWorldState.OperatingStatus.PRODUCING:
			$Illumination.show()
			var heat: float = $Illumination.self_modulate.a
			if heat >= HEAT_LOW:
				# Reverse a hot cooldown upward without jumping back to the low.
				var seconds := minf(WARMUP_SECONDS, HALF_PULSE_SECONDS * (HEAT_HIGH - heat) / (HEAT_HIGH - HEAT_LOW))
				_transition_to(HEAT_HIGH, seconds, _start_pulse.bind(_generation, true))
			else:
				var seconds := WARMUP_SECONDS * (HEAT_LOW - heat) / HEAT_LOW
				_transition_to(HEAT_LOW, seconds, _start_pulse.bind(_generation))
		PlanetWorldState.OperatingStatus.INPUT_EMPTY, PlanetWorldState.OperatingStatus.OUTPUT_FULL:
			if $Illumination.self_modulate.a > 0.0:
				_transition_to(0.0, COOLDOWN_SECONDS, _finish_cooldown.bind(_generation))
			else:
				_set_heat(0.0)
		_:
			_set_heat(0.0)


func _transition_to(target: float, seconds: float, completion: Callable) -> void:
	if seconds <= 0.0:
		_set_heat(target)
		completion.call()
		return
	_thermal = create_tween()
	_thermal.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_thermal.tween_property($Illumination, "self_modulate:a", target, seconds)
	# A finished signal runs after this tween completes, before its replacement.
	_thermal.finished.connect(completion, CONNECT_ONE_SHOT)


func _start_pulse(generation: int, from_high: bool = false) -> void:
	if generation != _generation or not _initialized or not is_inside_tree() \
			or _status != PlanetWorldState.OperatingStatus.PRODUCING:
		return
	_thermal = create_tween().set_loops()
	_thermal.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)
	_thermal.tween_property($Illumination, "self_modulate:a", HEAT_LOW if from_high else HEAT_HIGH, HALF_PULSE_SECONDS)
	_thermal.tween_property($Illumination, "self_modulate:a", HEAT_HIGH if from_high else HEAT_LOW, HALF_PULSE_SECONDS)


func _finish_cooldown(generation: int) -> void:
	if generation != _generation or not _initialized or not is_inside_tree() \
			or _status not in [PlanetWorldState.OperatingStatus.INPUT_EMPTY, PlanetWorldState.OperatingStatus.OUTPUT_FULL]:
		return
	_thermal = null
	_set_heat(0.0)


func _cancel_thermal() -> void:
	_generation += 1
	if _thermal != null:
		_thermal.kill()
		_thermal = null


func _set_heat(heat: float) -> void:
	$Illumination.self_modulate.a = clampf(heat, 0.0, 1.0)
	$Illumination.visible = heat > 0.0


# Hard-cold disable for ghosts, hidden subtrees, recovery and detached worlds.
func reset_thermal() -> void:
	_cancel_thermal()
	_initialized = false
	_status = PlanetWorldState.OperatingStatus.INACTIVE
	_set_heat(0.0)


func _exit_tree() -> void:
	reset_thermal()
