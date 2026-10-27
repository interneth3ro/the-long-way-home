class_name DeployedMachine
extends StaticBody2D

# Presentation/physical collision only; identity and ownership stay in planet state.
func configure(machine: Dictionary) -> void:
	var definition: MachineDefinition = machine.definition
	var footprint := definition.footprint(machine.cell, machine.turns)
	position = Vector2(footprint.get_center().x, footprint.end.y)
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
	add_child(visual)
