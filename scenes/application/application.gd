extends Node

# MainV2 continues to own every gameplay system and its PlaythroughState.
const GAMEPLAY: PackedScene = preload("res://scenes/main/main_v2.tscn")

var _starting: bool = false
var _session: Node = null

@onready var _title: TitleScreen = $TitleScreen


func _ready() -> void:
	_title.new_game_requested.connect(_start_new_game)
	_title.exit_requested.connect(_quit)


func _input(_event: InputEvent) -> void:
	if _starting:
		get_viewport().set_input_as_handled()


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
	add_child(_session)
	# add_child completes MainV2's existing synchronous ready/spawn setup.
	# Preserve any startup failure pause set by Main itself.
	_starting = false
	set_process_input(false)
	# The shell owns the session child; normal tree teardown frees it and its state.


func _quit() -> void:
	if not _starting:
		get_tree().quit()
