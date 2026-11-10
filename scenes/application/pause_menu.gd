class_name PauseMenu
extends CanvasLayer

signal resume_requested
signal main_menu_requested
signal exit_requested

var _destination: StringName = &""
var _busy: bool = false

@onready var _root: Control = $Overlay
@onready var _menu: VBoxContainer = $Overlay/Center/Menu
@onready var _confirmation: VBoxContainer = $Overlay/Center/Confirmation


func _ready() -> void:
	_menu.get_node("Resume").pressed.connect(func() -> void: resume_requested.emit())
	_menu.get_node("MainMenu").pressed.connect(_ask.bind(&"main_menu"))
	_menu.get_node("ExitGame").pressed.connect(_ask.bind(&"exit"))
	_confirmation.get_node("Actions/Confirm").pressed.connect(_confirm)
	_confirmation.get_node("Actions/Cancel").pressed.connect(_cancel)


func open() -> void:
	_busy = false
	_destination = &""
	_confirmation.hide()
	_menu.show()
	_root.show()
	_menu.get_node("Resume").grab_focus()


func close() -> void:
	_root.hide()
	get_viewport().gui_release_focus()


func disable_menu() -> void:
	_busy = true
	get_viewport().gui_release_focus()


func _input(event: InputEvent) -> void:
	if not _root.visible:
		return
	if _busy:
		get_viewport().set_input_as_handled()
	elif event.is_action_pressed("ui_cancel"):
		get_viewport().set_input_as_handled()
		if not event.is_echo():
			if _destination != &"":
				_cancel()
			else:
				resume_requested.emit()


func _unhandled_input(_event: InputEvent) -> void:
	if _root.visible:
		# GUI navigation/activation runs first; paused gameplay receives nothing.
		get_viewport().set_input_as_handled()


func _ask(destination: StringName) -> void:
	if _busy:
		return
	_destination = destination
	_confirmation.get_node("Heading").text = "Return to Main Menu?" if destination == &"main_menu" else "Exit Game?"
	_menu.hide()
	_confirmation.show()
	_confirmation.get_node("Actions/Cancel").grab_focus()


func _cancel() -> void:
	if _busy:
		return
	var button := "MainMenu" if _destination == &"main_menu" else "ExitGame"
	_destination = &""
	_confirmation.hide()
	_menu.show()
	_menu.get_node(button).grab_focus()


func _confirm() -> void:
	if _busy:
		return
	if _destination == &"main_menu":
		main_menu_requested.emit()
	elif _destination == &"exit":
		exit_requested.emit()
