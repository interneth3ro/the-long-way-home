extends "res://scenes/main/main.gd"

# Opt-in composition only. Main retains all gameplay authority and signal setup.
const INITIAL_WORLD: PackedScene = preload("res://scenes/world/production_ship_interior_v2.tscn")
const EXTERIOR_SCENE: String = "res://scenes/world/planet_exterior.tscn"


func _enter_tree() -> void:
	# Replace the inherited opening before any child enters the tree or readies.
	var worlds := get_node("Worlds")
	var legacy_opening := worlds.get_child(0)
	worlds.remove_child(legacy_opening)
	legacy_opening.free()
	worlds.add_child(INITIAL_WORLD.instantiate())
	worlds.child_entered_tree.connect(_configure_exterior_return)


func _ready() -> void:
	# Parent @onready captures DialogueUI while Dave is still Main/Dave.
	# All exported controller/UI player references resolve before initialize reparents.
	super._ready()
	var transitions := $SceneTransitions as SceneTransitionController
	var world := transitions.get_current_world()
	var spawn := world.get_node("Spawns/Initial") as Marker2D
	transitions.player.global_position = spawn.global_position
	world.call("prepare_for_arrival", transitions.player, $PlaythroughState.planet)
	var camera := transitions.player.get_node("Camera2D") as Camera2D
	camera.reset_smoothing()
	camera.force_update_scroll()


func _configure_exterior_return(world: Node) -> void:
	if world.scene_file_path != EXTERIOR_SCENE:
		return
	# Configure the real exterior instance on each attach, before arrival/unlock.
	# Its source path, simulation and legacy authored defaults remain untouched.
	var hatch := world.get_node("GroundObjects/Hatch")
	hatch.set("destination_scene", INITIAL_WORLD.resource_path)
	hatch.set("destination_spawn", &"FromPlanet")
