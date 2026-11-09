class_name FabricatorVisual
extends Node2D

# Accepted front resting composite and three static side/rear crops.
# Offsets already subtract each view's ground anchor; never translate twice.
const TEXTURES := [
	preload("res://assets/machines/fabricator/fabricator_0_resting.png"),
	preload("res://assets/machines/fabricator/fabricator_90_body.png"),
	preload("res://assets/machines/fabricator/fabricator_180_body.png"),
	preload("res://assets/machines/fabricator/fabricator_270_body.png"),
]
const OFFSETS := [
	Vector2(-627, -1080),
	Vector2(-659, -1044),
	Vector2(-586, -1001),
	Vector2(-672, -971),
]
const SCALES := [8.0 / 65.0, 32.0 / 305.0, 32.0 / 265.0, 16.0 / 155.0]

# Decision 62: elapsed seconds and source-pixel XYZ at every phase boundary.
# Each five-second pattern owns its outgoing, raised-tool handoff.
const PATTERNS := [
	[ # Material Pass
		[0.00, Vector3(-65, -20, -6)],
		[0.18, Vector3(-65, -20, 20)],
		[1.98, Vector3(65, -20, 20)],
		[2.16, Vector3(65, -20, -6)],
		[2.86, Vector3(45, 18, -6)],
		[3.04, Vector3(45, 18, 20)],
		[4.19, Vector3(-35, 18, 20)],
		[4.37, Vector3(-35, 18, -6)],
		[5.00, Vector3(-40, -8, -6)],
	],
	[ # Precision Work
		[0.00, Vector3(-40, -8, -6)],
		[0.16, Vector3(-40, -8, 10)],
		[1.06, Vector3(-28, -8, 10)],
		[1.22, Vector3(-28, -8, -6)],
		[1.62, Vector3(0, 12, -6)],
		[1.72, Vector3(0, 12, -6)],
		[1.88, Vector3(0, 12, 10)],
		[2.78, Vector3(12, 12, 10)],
		[2.94, Vector3(12, 12, -6)],
		[3.34, Vector3(40, -8, -6)],
		[3.50, Vector3(40, -8, 10)],
		[4.40, Vector3(28, -8, 10)],
		[4.56, Vector3(28, -8, -6)],
		[5.00, Vector3(55, 26, -6)],
	],
	[ # Finishing Pass
		[0.00, Vector3(55, 26, -6)],
		[0.18, Vector3(55, 26, 20)],
		[3.18, Vector3(-55, 26, 20)],
		[3.36, Vector3(-55, 26, -6)],
		[3.76, Vector3(-55, 26, -6)],
		[5.00, Vector3(-65, -20, -6)],
	],
]
enum PresentationState { REST, INITIALIZING, FABRICATING, SHUTTING_DOWN }

@onready var _body: Sprite2D = $Body
@onready var _front_assembly: Node2D = $FrontAssembly
@onready var _gantry_y: Node2D = $FrontAssembly/GantryY
@onready var _carriage_x: Node2D = $FrontAssembly/GantryY/CarriageX
@onready var _tool_z: Node2D = $FrontAssembly/GantryY/CarriageX/ToolZ
var _turns: int = 0
var _applied_turns: int = -1
var _machine_id: int = 0
var _enabled: bool = false
var _production_intent: bool = false
var _initialized: bool = false
var _state: PresentationState = PresentationState.REST
var _pattern_cursor: int = 0
var _motion: Tween
var _generation: int = 0


func _ready() -> void:
	if not visibility_changed.is_connected(_on_visibility_changed):
		visibility_changed.connect(_on_visibility_changed)
	configure(_turns)
	_refresh_view()
	_refresh_motion()


func configure(quarter_turns: int) -> void:
	_turns = posmod(quarter_turns, 4)
	# Retain pre-ready configuration; repeated calls leave the current pose alone.
	if not is_node_ready() or _applied_turns == _turns:
		return
	_reset_motion()
	_body.texture = TEXTURES[_turns]
	_body.position = OFFSETS[_turns]
	scale = Vector2.ONE * SCALES[_turns]
	_applied_turns = _turns
	_refresh_view()
	_refresh_motion()


# Assigned by the adapter before tree entry, never stored in simulation records.
func set_presentation_identity(machine_id: int) -> void:
	if _machine_id == machine_id:
		return
	_machine_id = machine_id
	_reset_motion()
	_refresh_motion()


func _starting_pattern() -> int:
	return posmod(_machine_id - 1, 3) if _machine_id > 0 else 0


# Only effective production intent matters: nonproducing-to-nonproducing changes
# cannot restart shutdown. The shared adapter still updates its status dot at once.
func set_operating_status(status: PlanetWorldState.OperatingStatus, enabled: bool = true) -> void:
	var producing := status == PlanetWorldState.OperatingStatus.PRODUCING
	if _production_intent == producing and _enabled == enabled:
		return
	var enabled_changed := _enabled != enabled
	_production_intent = producing
	_enabled = enabled
	if enabled_changed:
		_reset_motion()
	_refresh_view()
	_refresh_motion()


func _refresh_view() -> void:
	if not is_node_ready():
		return
	# Deployed front stays layered even while idle or shutting down; ghosts use Body.
	var layered := _enabled and _turns == 0
	_body.visible = not layered
	_front_assembly.visible = layered


func _can_animate() -> bool:
	return is_node_ready() and is_inside_tree() and is_visible_in_tree() and _enabled and _turns == 0


func _refresh_motion() -> void:
	if not is_node_ready() or not is_inside_tree():
		return
	if not _can_animate():
		_reset_motion()
		return
	if not _initialized:
		_initialized = true
		_pattern_cursor = _starting_pattern()
	if _production_intent:
		if _state in [PresentationState.REST, PresentationState.SHUTTING_DOWN]:
			_start_initializing()
	elif _state in [PresentationState.INITIALIZING, PresentationState.FABRICATING]:
		# Initialization reserves an attempt; the outgoing handoff still belongs
		# to that attempt until its five-second completion. Abandon it exactly once.
		_pattern_cursor = (_pattern_cursor + 1) % 3
		_start_shutdown()


func _displayed_pose() -> Vector3:
	return Vector3(_carriage_x.position.x, _gantry_y.position.y, _tool_z.position.y)


func _set_pose(pose: Vector3) -> void:
	# Only these identity groups move. Sprite offsets and root registration stay fixed.
	var gantry := Vector2(0, pose.y)
	var carriage := Vector2(pose.x, 0)
	var tool := Vector2(0, pose.z)
	if _gantry_y.position != gantry:
		_gantry_y.position = gantry
	if _carriage_x.position != carriage:
		_carriage_x.position = carriage
	if _tool_z.position != tool:
		_tool_z.position = tool


func _cancel_motion() -> void:
	_generation += 1
	if _motion != null:
		_motion.kill()
		_motion = null


func _begin_motion(state: PresentationState) -> void:
	_cancel_motion()
	_state = state
	_motion = create_tween()
	_motion.set_trans(Tween.TRANS_LINEAR).set_ease(Tween.EASE_IN)


func _append_phase(start: Vector3, target: Vector3, seconds: float) -> void:
	if seconds <= 0.0:
		return # The tool is already raised; no zero-duration tweener or pose reset.
	if start == target:
		_motion.tween_interval(seconds)
	else:
		_motion.tween_method(_interpolate_pose.bind(start, target, _generation), 0.0, 1.0, seconds)


func _carriage_fraction(u: float) -> float:
	const A := 0.12
	const B := 0.18
	const V := 20.0 / 17.0
	if u < A:
		return V * u * u / (2.0 * A)
	if u <= 1.0 - B:
		return V * (u - A / 2.0)
	return 1.0 - V * (1.0 - u) * (1.0 - u) / (2.0 * B)


func _interpolate_pose(u: float, start: Vector3, target: Vector3, generation: int) -> void:
	if generation != _generation or not _can_animate():
		return
	if u >= 1.0:
		_set_pose(target) # Exact endpoints, including raised-tool and home coordinates.
		return
	var x := _carriage_fraction(u)
	var y := (1.0 - cos(PI * u)) / 2.0
	var z := 4.0 * u * u * u if u < 0.5 else 1.0 - pow(-2.0 * u + 2.0, 3.0) / 2.0
	_set_pose(Vector3(lerpf(start.x, target.x, x), lerpf(start.y, target.y, y), lerpf(start.z, target.z, z)))


func _start_initializing() -> void:
	var pose := _displayed_pose()
	var raised := Vector3(pose.x, pose.y, -6)
	var entry: Vector3 = PATTERNS[_pattern_cursor][0][1]
	_begin_motion(PresentationState.INITIALIZING)
	_append_phase(pose, raised, 0.15 * (pose.z + 6.0) / 26.0)
	_append_phase(raised, entry, 0.45)
	_motion.finished.connect(_finish_initializing.bind(_generation), CONNECT_ONE_SHOT)


func _completion_valid(generation: int, state: PresentationState, producing: bool) -> bool:
	return generation == _generation and _state == state and _initialized \
			and _can_animate() and _production_intent == producing


func _finish_initializing(generation: int) -> void:
	if not _completion_valid(generation, PresentationState.INITIALIZING, true):
		return
	_motion = null
	_start_pattern()


func _start_pattern() -> void:
	_begin_motion(PresentationState.FABRICATING)
	var frames: Array = PATTERNS[_pattern_cursor]
	for index in range(1, frames.size()):
		_append_phase(frames[index - 1][1], frames[index][1], frames[index][0] - frames[index - 1][0])
	_motion.finished.connect(_finish_pattern.bind(_generation), CONNECT_ONE_SHOT)


func _finish_pattern(generation: int) -> void:
	if not _completion_valid(generation, PresentationState.FABRICATING, true):
		return
	_motion = null
	_pattern_cursor = (_pattern_cursor + 1) % 3
	_start_pattern()


func _start_shutdown() -> void:
	var pose := _displayed_pose()
	var raised := Vector3(pose.x, pose.y, -6)
	var home := Vector3(0, 0, -6)
	_begin_motion(PresentationState.SHUTTING_DOWN)
	_append_phase(pose, raised, 0.18 * (pose.z + 6.0) / 26.0)
	_append_phase(raised, home, 0.70)
	_append_phase(home, Vector3.ZERO, 0.12)
	_motion.finished.connect(_finish_shutdown.bind(_generation), CONNECT_ONE_SHOT)


func _finish_shutdown(generation: int) -> void:
	if not _completion_valid(generation, PresentationState.SHUTTING_DOWN, false):
		return
	_motion = null
	_set_pose(Vector3.ZERO)
	_state = PresentationState.REST


func _reset_motion() -> void:
	_cancel_motion()
	_state = PresentationState.REST
	_initialized = false
	_pattern_cursor = _starting_pattern()
	if is_node_ready():
		_set_pose(Vector3.ZERO)


func _on_visibility_changed() -> void:
	# CanvasItem propagates effective ancestor visibility changes to this signal.
	_refresh_motion()


func _exit_tree() -> void:
	_reset_motion()
	_production_intent = false
	_applied_turns = -1
	# Parent MachineVisual resupplies the latest authoritative status on re-entry.
	request_ready()
