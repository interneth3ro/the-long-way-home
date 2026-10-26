class_name WorldCoordinates
extends RefCounted

const TERRAIN_SIZE: int = 64
const CONSTRUCTION_SIZE: int = 32
const CHUNK_TILES: int = 32
const CHUNK_SIZE: int = TERRAIN_SIZE * CHUNK_TILES


static func world_to_terrain(point: Vector2) -> Vector2i:
	return Vector2i(floori(point.x / TERRAIN_SIZE), floori(point.y / TERRAIN_SIZE))


static func world_to_construction(point: Vector2) -> Vector2i:
	return Vector2i(floori(point.x / CONSTRUCTION_SIZE), floori(point.y / CONSTRUCTION_SIZE))


static func terrain_to_chunk(tile: Vector2i) -> Vector2i:
	return Vector2i(floori(float(tile.x) / CHUNK_TILES), floori(float(tile.y) / CHUNK_TILES))


static func terrain_to_local(tile: Vector2i) -> Vector2i:
	return tile - terrain_to_chunk(tile) * CHUNK_TILES


static func world_to_chunk(point: Vector2) -> Vector2i:
	return terrain_to_chunk(world_to_terrain(point))
