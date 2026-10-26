extends Sprite2D
## Development-only art comparison; independent of repair and narrative state.

const DAMAGED_TEXTURE: Texture2D = preload("res://assets/environment/computer/computer_damaged_pilot.png")
const REPAIRED_TEXTURE: Texture2D = preload("res://assets/environment/computer/computer_repaired_pilot.png")


func _ready() -> void:
	texture = DAMAGED_TEXTURE
	set_process_input(OS.is_debug_build())


func _input(event: InputEvent) -> void:
	if not event is InputEventKey:
		return
	if not event.pressed or event.echo or event.get_modifiers_mask() != 0:
		return

	match event.physical_keycode:
		KEY_F6:
			texture = DAMAGED_TEXTURE
		KEY_F7:
			texture = REPAIRED_TEXTURE
