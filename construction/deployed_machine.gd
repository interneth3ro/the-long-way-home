class_name DeployedMachine
extends StaticBody2D

var machine_id: int
var display_name: String
var interaction_point: Vector2
var _state: PlanetWorldState
var _visual: MachineVisual

# Presentation/physical collision only; identity and ownership stay in planet state.
func configure(machine: Dictionary, state: PlanetWorldState) -> void:
	machine_id = machine.id
	_state = state
	var definition: MachineDefinition = machine.definition
	display_name = definition.display_name
	var footprint := definition.footprint(machine.cell, machine.turns)
	position = Vector2(footprint.get_center().x, footprint.end.y)
	interaction_point = Vector2(0, -footprint.size.y / 2.0)
	collision_layer = 1
	collision_mask = 1
	var shape := RectangleShape2D.new()
	shape.size = footprint.size
	var collision := CollisionShape2D.new()
	collision.shape = shape
	collision.position = Vector2(0, -footprint.size.y / 2.0)
	add_child(collision)
	var visual := MachineVisual.new()
	visual.definition = definition
	visual.turns = machine.turns
	visual.position = Vector2(-footprint.size.x / 2.0, -footprint.size.y)
	visual.show_status = true
	visual.status = _state.machine_status(machine)
	add_child(visual)
	_visual = visual


func _process(_delta: float) -> void:
	var status := _state.machine_status(_state.get_machine(machine_id))
	if status == _visual.status:
		return
	_visual.status = status
	_visual.queue_redraw()
