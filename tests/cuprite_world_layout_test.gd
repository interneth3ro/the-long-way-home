extends SceneTree
## Authored only. No runner dispatch and no engine execution authorized.

const Generator = preload("res://scenes/world/starting_resource_generator.gd")
const Context = preload("res://scenes/world/resource_generation_crash_site.gd")
const FERRITE = preload("res://scenes/world/resource_definitions/v2/ferrite.tres")
const CARBITE = preload("res://scenes/world/resource_definitions/v2/carbite.tres")
const CUPRITE = preload("res://scenes/world/resource_definitions/v2/cuprite.tres")
var _failures: int = 0


func _check(condition: bool, label: String) -> void:
	if not condition:
		_failures += 1
		push_error(label)


func _initialize() -> void:
	_check(Generator.BAND_THRESHOLDS == [[25, 90], [10, 65], [45, 90]], "exact revised preferences")
	for seed_value in [26026, 0, 1, 42, -79, 7341, -9223372036854775807, 9223372036854775807]:
		var definitions: Array[WorldResourceDefinition] = [FERRITE, CARBITE, CUPRITE]
		var generator := Generator.new(seed_value, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)
		_check(generator.is_ready(), "complete revised layout prepares")
		if not generator.is_ready():
			continue
		_check(generator.identity_policy() == "starting-v2-2", "revised starting policy")
		_check(not Generator.new(seed_value, definitions, Context.protected_bounds(),
			Context.SHIP_REFERENCE, "starting-v2-1").is_ready(), "old policy rejected")
		var layout: Dictionary = generator.reservations()
		var repeat := Generator.new(seed_value, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)
		_check(layout == repeat.reservations(), "same-seed deterministic layout")
		_check(generator._arrangement_valid(layout.locations), "spacing and protection remain active")
		var counts := {"ferrite": 0, "carbite": 0, "cuprite": 0}
		for location: Dictionary in layout.locations:
			_check(location.generation_policy == "starting-v2-2", "current descriptor policy")
			for member: Dictionary in location.deposits:
				counts[member.resource_type] += 1
				_check(member.anchor_cells.size == Vector2i(4, 4), "anchor geometry")
				_check(generator.descriptor_by_id(member.deposit_id).descriptor == member,
					"stable exact deposit identity")
				var retired_id: String = member.deposit_id.replace("starting-v2-2", "starting-v2-1")
				_check(not generator.descriptor_by_id(retired_id).ok, "old identity rejected without alias")
				if member.resource_type == "cuprite":
					var distance: float = Generator.anchor_bounds(member).get_center().distance_to(Context.SHIP_REFERENCE)
					_check(distance >= Generator.MIN_DISTANCE and distance <= Generator.MAX_DISTANCE,
						"Cuprite permitted distance")
					print("Cuprite anchor-center distance: seed=%d id=%s distance=%.3f" % [
						seed_value, member.deposit_id, distance])
		_check(counts == {"ferrite": 3, "carbite": 2, "cuprite": 2}, "complete starting counts")
	quit(0 if _failures == 0 else 1)
