class_name ResourceGenerationCrashSite
extends RefCounted
## Inert authored snapshot, not a live-scene adapter. Static tests guard provenance.

const Protection = preload("res://scenes/world/crash_site_protection.gd")
const SHIP_REFERENCE := Vector2(-384, -192)
const CONSTRUCTION_CLEARANCE: int = 96


static func protected_bounds() -> Array[Rect2]:
	var gameplay := Rect2(Protection.GAMEPLAY[0], Vector2.ZERO)
	for vertex: Vector2 in Protection.GAMEPLAY:
		gameplay = gameplay.expand(vertex)
	return [gameplay.grow(CONSTRUCTION_CLEARANCE),
		# Union AABB of the three grounded hull collision polygons, world space.
		Rect2(-951, -631, 1183, 532).grow(CONSTRUCTION_CLEARANCE),
		# Authored rocks: include painted silhouettes and collision circles.
		Rect2(-816, 288, 96, 96).grow(CONSTRUCTION_CLEARANCE),
		Rect2(656, -480, 96, 96).grow(CONSTRUCTION_CLEARANCE),
		# Fixed authored clearing, scar, north ridge and south shelf AABBs.
		Rect2(-832, -704, 1664, 1472).grow(48),
		Rect2(-1024, -864, 832, 736).grow(48),
		Rect2(-1024, -1024, 2048, 256).grow(48),
		Rect2(-1024, 768, 2048, 256).grow(48)]
