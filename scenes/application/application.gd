extends Node

# MainV2 continues to own every gameplay system and its PlaythroughState.
const GAMEPLAY: PackedScene = preload("res://scenes/main/main_v2.tscn")
const TITLE: PackedScene = preload("res://scenes/application/title_screen.tscn")

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
	if _starting:
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
	get_viewport().set_input_as_handled()
	# Keep gameplay out of the tree until held keys/buttons have been released.
	# The extra frame also drains just-pressed state used by polling controllers.
	await get_tree().process_frame
	while Input.is_anything_pressed():
		await get_tree().process_frame
	await get_tree().process_frame
	remove_child(_title)
	_title.queue_free()
	_title = null
	_session = GAMEPLAY.instantiate()
	# The shell always processes; gameplay must not inherit that mode.
	_session.process_mode = Node.PROCESS_MODE_PAUSABLE
	_pause_before_session = get_tree().paused
	add_child(_session)
	# add_child completes MainV2's existing synchronous ready/spawn setup.
	# Preserve any startup failure pause set by Main itself.
	_starting = false
	# The shell owns the session child; normal tree teardown frees it and its state.


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
