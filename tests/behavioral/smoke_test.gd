extends RefCounted
## Actual production grid conversion, including negative and exact boundaries.
const Coordinates = preload("res://scenes/world/world_coordinates.gd")


func run() -> Dictionary:
	var cases := [
		{"point": Vector2(-0.01, -32.01), "expected": Vector2i(-1, -2)},
		{"point": Vector2(-32, -64), "expected": Vector2i(-1, -2)},
		{"point": Vector2(31.99, 32), "expected": Vector2i(0, 1)},
		{"point": Vector2(32, 64), "expected": Vector2i(1, 2)},
	]
	var failures: Array[String] = []
	for vector in cases:
		var actual: Vector2i = Coordinates.world_to_construction(vector.point)
		if actual != vector.expected:
			failures.append("world_to_construction(%s): expected %s; got %s" % [vector.point, vector.expected, actual])
	return {"checks": cases.size(), "failures": failures}
