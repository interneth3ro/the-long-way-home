extends CanvasLayer

@export var player: Node2D
@export var display_enabled: bool = true

@onready var _coordinates: Label = $HUD/Coordinates


func _ready() -> void:
	_refresh_coordinates()


func _process(_delta: float) -> void:
	_refresh_coordinates()


func _refresh_coordinates() -> void:
	visible = display_enabled and is_instance_valid(player)
	if not visible:
		return
	var world_position := player.global_position
	_coordinates.text = "X: %+d   Y: %+d" % [roundi(world_position.x), roundi(world_position.y)]
