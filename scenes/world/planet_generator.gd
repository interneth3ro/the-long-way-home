class_name PlanetGenerator
extends RefCounted

const ROCK := Color(0.30, 0.34, 0.34)
const SOIL := Color(0.35, 0.32, 0.26)
const WEATHERED := Color(0.27, 0.30, 0.29)
const SCRUB := Color(0.26, 0.33, 0.27)
const DETAIL_CLEARANCE: float = 48.0

var _seed: int
var _overlays: Array[Dictionary] = []
var _protected: PackedVector2Array
var _authored_objects: PackedVector2Array


func _init(world_seed: int, overlays: Array[Dictionary], protected: PackedVector2Array,
		authored_objects: PackedVector2Array) -> void:
	_seed = world_seed
	_overlays = overlays
	_protected = protected
	_authored_objects = authored_objects


# Integer arithmetic stays below int64 overflow, including negative coordinates.
# Each sample has its own coordinate-derived value; there is no mutable RNG.
func coordinate_random(tile: Vector2i, channel: int = 0) -> float:
	var value := posmod(_seed, 2147483647)
	value = posmod(value * 48271 + posmod(tile.x, 2147483647) * 69621, 2147483647)
	value = posmod(value * 48271 + posmod(tile.y, 2147483647) * 907, 2147483647)
	value = posmod(value * 48271 + channel * 104729, 2147483647)
	value = posmod((value ^ (value >> 13)) * 48271, 2147483647)
	return float(value) / 2147483647.0


func _noise(point: Vector2, channel: int) -> float:
	var cell := Vector2i(floori(point.x), floori(point.y))
	var blend := point - Vector2(cell)
	blend = blend * blend * (Vector2(3.0, 3.0) - 2.0 * blend)
	var north := lerpf(coordinate_random(cell, channel),
		coordinate_random(cell + Vector2i.RIGHT, channel), blend.x)
	var south := lerpf(coordinate_random(cell + Vector2i.DOWN, channel),
		coordinate_random(cell + Vector2i.ONE, channel), blend.x)
	return lerpf(north, south, blend.y)


# Presentation-only treatment weights at absolute terrain-grid vertices.
# Channels 8-10 leave existing terrain/detail randomness untouched. Broad fields
# cross chunk boundaries without depending on neighbors being loaded.
func weathered_earth_weights(vertex: Vector2i) -> Vector3:
	var point := Vector2(vertex) * WorldCoordinates.TERRAIN_SIZE / 1024.0
	return Vector3(
		smoothstep(0.35, 0.75, _noise(point, 8)) * 0.65,
		smoothstep(0.40, 0.80, _noise(point, 9)) * 0.65,
		smoothstep(0.50, 0.85, _noise(point, 10)) * 0.55)


# World-space samples are shared across chunk edges. Authored polygons, retained
# in the scene as editable data, take precedence over baseline and modifications.
func sample_color(tile: Vector2i, state: PlanetWorldState) -> Color:
	var point := (Vector2(tile) + Vector2(0.5, 0.5)) * WorldCoordinates.TERRAIN_SIZE
	var geology := _noise(point / 768.0, 1)
	var cover := _noise(point / 512.0, 2)
	var color := WEATHERED.lerp(ROCK, smoothstep(0.35, 0.75, geology))
	color = color.lerp(SOIL, smoothstep(0.50, 0.80, 1.0 - geology))
	color = color.lerp(SCRUB, smoothstep(0.50, 0.85, cover) * 0.75)
	color = state.terrain_color(tile, color)
	# Recovery is irregular, seed-independent, and continuous in world space.
	for overlay in _overlays:
		var polygon: PackedVector2Array = overlay.polygon
		var weight := _overlay_weight(point, polygon, float(overlay.feather))
		color = color.lerp(overlay.color, weight)
	return color


func _overlay_weight(point: Vector2, polygon: PackedVector2Array, feather: float) -> float:
	if Geometry2D.is_point_in_polygon(point, polygon):
		return 1.0
	return 1.0 - smoothstep(0.0, feather, _edge_distance(point, polygon))


func _edge_distance(point: Vector2, polygon: PackedVector2Array) -> float:
	var distance := INF
	for index in range(polygon.size()):
		var closest := Geometry2D.get_closest_point_to_segment(
			point, polygon[index], polygon[(index + 1) % polygon.size()])
		distance = minf(distance, point.distance_to(closest))
	return distance


func is_protected(point: Vector2) -> bool:
	# Separate gameplay polygon reserves hatch, approach, factory and Ferrite space.
	if Geometry2D.is_point_in_polygon(point, _protected) \
			or _edge_distance(point, _protected) < DETAIL_CLEARANCE:
		return true
	# Existing rock visuals extend north of their ground anchors. The ship's
	# larger footprint is already contained in the gameplay/clearing polygons.
	for anchor in _authored_objects:
		if point.distance_to(anchor) < 160.0:
			return true
	# Preserve actual authored geology with clearance, independently of its skirt.
	for overlay in _overlays:
		if _overlay_weight(point, overlay.polygon, DETAIL_CLEARANCE) > 0.0:
			return true
	return false


# Empty or {position: Vector2, kind: int}; purely decorative, no collision.
func sample_detail(tile: Vector2i, state: PlanetWorldState) -> Dictionary:
	if state.is_detail_removed(tile) or coordinate_random(tile, 3) > 0.065:
		return {}
	var jitter := Vector2(coordinate_random(tile, 4), coordinate_random(tile, 5))
	var point := (Vector2(tile) + Vector2(0.2, 0.2) + jitter * 0.6) * WorldCoordinates.TERRAIN_SIZE
	if is_protected(point):
		return {}
	# Vegetation/details return sparsely through the recovery feather, rather
	# than starting abruptly at its edge. Interior protection always wins.
	var recovery_weight: float = 0.0
	for overlay in _overlays:
		recovery_weight = maxf(recovery_weight,
			_overlay_weight(point, overlay.polygon, float(overlay.feather)))
	if coordinate_random(tile, 7) < recovery_weight * 0.9:
		return {}
	var kind := mini(2, int(coordinate_random(tile, 6) * 3.0))
	return {"position": point, "kind": kind}
