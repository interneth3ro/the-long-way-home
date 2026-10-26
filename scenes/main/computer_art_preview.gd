@tool
extends Sprite2D
## Development-only art comparison; independent of repair and narrative state.

const DAMAGED_TEXTURE: Texture2D = preload("res://assets/environment/computer/computer_damaged_pilot.png")
const REPAIRED_TEXTURE: Texture2D = preload("res://assets/environment/computer/computer_repaired_pilot.png")

@export var preview_repaired: bool = false:
	set(value):
		preview_repaired = value
		_update_preview_texture()


func _ready() -> void:
	_update_preview_texture()


func _update_preview_texture() -> void:
	texture = REPAIRED_TEXTURE if preview_repaired else DAMAGED_TEXTURE
