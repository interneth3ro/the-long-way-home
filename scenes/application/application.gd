extends Node

# MainV2 continues to own every gameplay system and its PlaythroughState.
const GAMEPLAY: PackedScene = preload("res://scenes/main/main_v2.tscn")
const LOADING: PackedScene = preload("res://scenes/application/loading_screen.tscn")
const STARTUP_UNITS: int = 51
const TITLE: PackedScene = preload("res://scenes/application/title_screen.tscn")

var _loading: LoadingScreen
var _startup_generation: int = 0
var _startup_failed: bool = false
var _progress_callback: Callable
var _starting: bool = false
var _session: Node = null
var _pause_open: bool = false
var _pause_before_menu: bool = false
var _pause_before_session: bool = false

@onready var _title: TitleScreen = $TitleScreen
@onready var _pause: PauseMenu = $PauseMenu


func _ready() -> void:
	_connect_title()
	_pause.resume_requested.connect(_resume)
	_pause.main_menu_requested.connect(_return_to_title)
	_pause.exit_requested.connect(_quit)


func _connect_title() -> void:
	_title.new_game_requested.connect(_start_new_game)
	_title.exit_requested.connect(_quit)


func _input(_event: InputEvent) -> void:
	if _starting and not _startup_failed:
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	# Descendant gameplay handlers and GUI get first refusal of Escape.
	if _starting or _session == null or _pause_open or event.is_echo():
		return
	if event.is_action_pressed("ui_cancel"):
		# Do not interrupt arrival transitions or their disabled player state.
		if _session.get_node("SceneTransitions").is_transitioning():
			return
		get_viewport().set_input_as_handled()
		_pause_before_menu = get_tree().paused
		_pause_open = true
		get_tree().paused = true
		_pause.open()


func _start_new_game() -> void:
	if _starting or _session != null:
		return
	_starting = true
	_title.disable_menu()
	_startup_generation += 1
	var generation := _startup_generation
	_startup_failed = false
	_pause_before_session = get_tree().paused
	_loading = LOADING.instantiate() as LoadingScreen
	add_child(_loading)
	_loading.begin_operation("NEW GAME", STARTUP_UNITS, "Preparing ship interior...")
	_loading.return_requested.connect(_return_failed_startup)
	get_viewport().set_input_as_handled()
	# Render the opaque overlay before synchronous instantiate/_ready work.
	await RenderingServer.frame_post_draw
	if not _owns_startup(generation):
		return
	# Keep gameplay out of the tree until held keys/buttons have been released.
	# The extra frame also drains just-pressed state used by polling controllers.
	await get_tree().process_frame
	if not _owns_startup(generation):
		return
	while Input.is_anything_pressed():
		if not _owns_startup(generation):
			return
		await get_tree().process_frame
		if not _owns_startup(generation):
			return
	await get_tree().process_frame
	if not _owns_startup(generation):
		return
	remove_child(_title)
	_title.queue_free()
	_title = null
	_session = GAMEPLAY.instantiate()
	# The shell always processes; gameplay must not inherit that mode.
	_session.process_mode = Node.PROCESS_MODE_DISABLED
	add_child(_session)
	# MainV2 completes interior setup synchronously. Exterior work has its own
	# explicit completion contract; a global pause never authorizes activation.
	if not _session.get_node("PlaythroughState").planet.is_resource_generation_ready():
		_fail_startup("Ship initialization failed. Return to Main Menu to start a new session.")
		return
	var transitions := _session.get_node("SceneTransitions") as SceneTransitionController
	_progress_callback = _report_startup_progress.bind(generation)
	transitions.initial_preparation_progress.connect(_progress_callback)
	_loading.report_progress(0, "Preparing surrounding terrain...", "0 of 50 exterior preparation units ready")
	var prepared := await transitions.prepare_initial_exterior(true)
	if not _owns_startup(generation):
		return
	_disconnect_progress()
	if not prepared:
		_fail_startup("Surrounding terrain could not be prepared. Return to Main Menu to start a new session.")
		return
	_loading.report_progress(50, "Revealing ship interior...", "50 of 51 initialization units ready")
	await _loading.fade_out()
	if not _owns_startup(generation):
		return
	# Drain polling input again: keys may have been pressed during the reveal.
	await _drain_input()
	if not _owns_startup(generation):
		return
	if not transitions.activate_initial_session():
		_fail_startup("Startup readiness changed. Return to Main Menu to start a new session.")
		return
	_loading.complete_operation("Ship interior ready")
	_retire_loading()
	_session.process_mode = Node.PROCESS_MODE_PAUSABLE
	_starting = false


func _owns_startup(generation: int) -> bool:
	return is_inside_tree() and _starting and not _startup_failed \
		and generation == _startup_generation and is_instance_valid(_loading)


func _report_startup_progress(completed: int, total: int, generation: int) -> void:
	if not _owns_startup(generation) or total != STARTUP_UNITS - 1:
		return
	# The upstream 50 units combine chunk publications and resource presentation;
	# they cannot truthfully be labelled a terrain-only count.
	_loading.report_progress(clampi(completed, 0, 50), "Preparing surrounding terrain...",
		"%d of 50 exterior preparation units ready" % clampi(completed, 0, 50))


func _disconnect_progress() -> void:
	if is_instance_valid(_session) and _progress_callback.is_valid():
		var transitions := _session.get_node("SceneTransitions") as SceneTransitionController
		if transitions.initial_preparation_progress.is_connected(_progress_callback):
			transitions.initial_preparation_progress.disconnect(_progress_callback)
	_progress_callback = Callable()


func _fail_startup(message: String) -> void:
	_disconnect_progress()
	_startup_failed = true
	_startup_generation += 1
	if is_instance_valid(_session):
		_session.get_node("SceneTransitions").cancel_initial_preparation()
	_loading.fail_operation(message)
	push_error("New Game initialization failed: " + message)


func _retire_loading() -> void:
	if is_instance_valid(_loading):
		remove_child(_loading)
		_loading.queue_free()
	_loading = null


func _return_failed_startup() -> void:
	if not _starting or not _startup_failed:
		return
	_loading.disable_return()
	_startup_generation += 1
	_disconnect_progress()
	if is_instance_valid(_session):
		_session.get_node("SceneTransitions").cancel_initial_preparation()
	await _drain_input()
	# Synchronous retirement frees staged children and controller-owned caches.
	if is_instance_valid(_session):
		remove_child(_session)
		_session.free()
	_session = null
	get_tree().paused = _pause_before_session
	_retire_loading()
	if not is_instance_valid(_title):
		_title = TITLE.instantiate()
		add_child(_title)
		_connect_title()
	_startup_failed = false
	_starting = false


func _drain_input() -> void:
	await get_tree().process_frame
	while Input.is_anything_pressed():
		await get_tree().process_frame
	await get_tree().process_frame


func _resume() -> void:
	if _starting or not _pause_open:
		return
	_starting = true
	_pause.disable_menu()
	# Stay paused until activation and held gameplay input have drained.
	await _drain_input()
	_pause.close()
	_pause_open = false
	get_tree().paused = _pause_before_menu
	_starting = false


func _return_to_title() -> void:
	if _starting or not _pause_open:
		return
	_starting = true
	_pause.disable_menu()
	await _drain_input()
	_pause.close()
	_pause_open = false
	# Free synchronously before another New Game; exit callbacks retain their owners.
	remove_child(_session)
	_session.free()
	_session = null
	# Discard pauses belonging to the retired session, including startup failure.
	get_tree().paused = _pause_before_session
	_title = TITLE.instantiate()
	add_child(_title)
	_connect_title()
	_starting = false


func _quit() -> void:
	if not _starting:
		get_tree().quit()
