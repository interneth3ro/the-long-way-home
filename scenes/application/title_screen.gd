class_name TitleScreen
extends Control

signal new_game_requested
signal exit_requested

@onready var _menu: VBoxContainer = $Menu


func _ready() -> void:
	$Menu/NewGame.grab_focus()


func disable_menu() -> void:
	for button: Button in _menu.get_children():
		button.release_focus()
		button.disabled = true


func _on_new_game_pressed() -> void:
	new_game_requested.emit()


func _on_exit_pressed() -> void:
	exit_requested.emit()
