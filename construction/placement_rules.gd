class_name PlacementRules
extends RefCounted

# Layer 3 is an explicit object property, independent of vegetation/art category.
const BLOCKING_LAYER: int = 4


static func distance_to_footprint(point: Vector2, footprint: Rect2) -> float:
	return point.distance_to(point.clamp(footprint.position, footprint.end))


# The preview and commit both call this, in the physics callback. World queries
# use planet-local coordinates; physical solids use the planet's global transform.
static func rejection(state: PlanetWorldState, definition: MachineDefinition,
		cell: Vector2i, turns: int, player: CharacterBody2D,
		world: Node2D, construction_range: float, inventory: InventoryState) -> String:
	if definition == null or not definition.is_valid():
		return "Invalid machine definition"
	if world == null or not world.is_in_group(&"construction_world"):
		return "Requires planetary ground"
	if inventory == null or not inventory.get_items().has(definition) \
			or inventory.get_quantity(definition.item_id) < 1:
		return "No packaged machine in inventory"
	var footprint := definition.footprint(cell, turns)
	if distance_to_footprint(world.to_local(player.global_position), footprint) > construction_range:
		return "Out of construction range"
	if not definition.compatible_resources.is_empty():
		var point := footprint.position + definition.rotated_point(definition.extraction_point, turns)
		var compatible := false
		for resource_type in definition.compatible_resources:
			if state.deposit_at(point, resource_type) != null:
				compatible = true
				break
		if not compatible:
			return "Requires compatible mineral-bearing ground"
	for machine in state.get_machines():
		var other: MachineDefinition = machine.definition
		if footprint.intersects(other.footprint(machine.cell, machine.turns)):
			return "Overlaps a deployed machine"
	var shape := RectangleShape2D.new()
	# A tiny inset permits exact edge contact, including physics contact tolerance.
	shape.size = footprint.size - Vector2.ONE * 0.02
	var query := PhysicsShapeQueryParameters2D.new()
	query.shape = shape
	query.transform = world.global_transform * Transform2D(0.0, footprint.get_center())
	query.collision_mask = BLOCKING_LAYER
	var space := world.get_world_2d().direct_space_state
	if not space.intersect_shape(query, 1).is_empty():
		return "Blocked by a solid obstacle"
	# Dave is not an environmental construction blocker, but must not be trapped.
	query.collision_mask = player.collision_layer
	for result in space.intersect_shape(query):
		if result.collider == player:
			return "Dave is in the footprint"
	return ""
