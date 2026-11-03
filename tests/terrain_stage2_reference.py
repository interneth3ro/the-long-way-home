"""Offline classification model, not GDScript execution or numeric parity proof.

No rendering, coverage reconstruction, state mutation, assets or output writers.
Geometry is read from current scene text; tests pin the reviewed source separately.
"""
from dataclasses import dataclass
import hashlib
import json
import math
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
BASE = "06666cc108d431294aba25d1ba0bd652d448c18b"
RULE = "production-ground@" + BASE
MODULUS = 2147483647


@dataclass(frozen=True)
class Geometry:
    gameplay: tuple
    overlays: tuple  # ordered (name, polygon, feather) records; colors excluded
    anchors: tuple   # ordered (name, point) direct StaticBody2D children


def _pairs(raw):
    values = tuple(float(value.strip()) for value in raw.split(","))
    if len(values) % 2:
        raise ValueError("Incomplete coordinate pair")
    return tuple(zip(values[::2], values[1::2]))


def load_geometry():
    """Read only the explicit current authoring format; no scene instantiation."""
    scene = (ROOT / "scenes/world/planet_exterior.tscn").read_text()
    overlays, anchors = [], []
    for header, body in re.findall(r"\[node ([^\n]+)\]\n(.*?)(?=\n\[|\Z)", scene, re.S):
        attributes = dict(re.findall(r'(\w+)="([^"]*)"', header))
        if attributes.get("parent") == "AuthoredCrashSite":
            if attributes.get("type") != "Polygon2D":
                raise ValueError("Unreviewed authored overlay type")
            raw = re.search(r"^polygon = PackedVector2Array\(([^)]+)\)", body, re.M)
            if raw is None:
                raise ValueError("Missing authored polygon")
            overlays.append((attributes["name"], _pairs(raw[1]), 256.0))
        if attributes.get("parent") == "GroundObjects" and attributes.get("type") == "StaticBody2D":
            raw = re.search(r"^position = Vector2\(([^)]+)\)", body, re.M)
            anchors.append((attributes["name"], _pairs(raw[1])[0] if raw else (0.0, 0.0)))
    source = (ROOT / "scenes/world/crash_site_protection.gd").read_text()
    gameplay = tuple((float(x), float(y)) for x, y in re.findall(
        r"Vector2\((-?\d+),\s*(-?\d+)\)", source))
    if (len(gameplay), len(overlays), len(anchors)) != (6, 4, 4):
        raise ValueError("Unreviewed production geometry inventory")
    return Geometry(gameplay, tuple(overlays), tuple(anchors))


def geometry_identity(geometry):
    payload = [geometry.gameplay, geometry.overlays, geometry.anchors]
    return hashlib.sha256(json.dumps(payload, separators=(",", ":")).encode()).hexdigest()


def center(cell):
    return tuple(64 * coordinate + 32 for coordinate in cell)


def world_to_cell(point, size=64):
    return tuple(math.floor(coordinate / size) for coordinate in point)


def chunk_and_local(cell):
    return tuple(value // 32 for value in cell), tuple(value % 32 for value in cell)


def coordinate_random(cell, seed, channel):
    """Modulo recurrence over integers; only the final ratio uses Python float."""
    value = seed % MODULUS
    additions = (cell[0] % MODULUS * 69621, cell[1] % MODULUS * 907, channel * 104729)
    for addition in additions:
        value = (48271 * value + addition) % MODULUS
    return (((value ^ (value >> 13)) * 48271) % MODULUS) / MODULUS


def noise(point, seed, channel):
    cell = tuple(math.floor(value) for value in point)
    weights = tuple((value - origin) ** 2 * (3 - 2 * (value - origin))
                    for value, origin in zip(point, cell))
    # Weighted sum derived from four lattice corner contributions, independently
    # of production's sequential lerpf expression. Python binary64 throughout.
    return sum(coordinate_random((cell[0] + dx, cell[1] + dy), seed, channel)
               * (weights[0] if dx else 1 - weights[0])
               * (weights[1] if dy else 1 - weights[1])
               for dy in (0, 1) for dx in (0, 1))


def edge_distance(point, polygon):
    distances = []
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        direction = (b[0] - a[0], b[1] - a[1])
        length_squared = sum(value * value for value in direction)
        projection = sum((p - start) * delta for p, start, delta in zip(point, a, direction))
        t = min(1.0, max(0.0, projection / length_squared)) if length_squared else 0.0
        distances.append(math.dist(point, tuple(start + t * delta for start, delta in zip(a, direction))))
    return min(distances, default=math.inf)


def polygon_contains(point, polygon):
    # The reference includes the boundary. Final classification there is already
    # protected by positive clearance/feather, irrespective of engine tie policy.
    if edge_distance(point, polygon) == 0:
        return True
    crossings = 0
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > point[1]) != (b[1] > point[1]):
            crossing_x = a[0] + (point[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            crossings += crossing_x > point[0]
    return bool(crossings % 2)


def overlay_weight(point, polygon, feather):
    if polygon_contains(point, polygon):
        return 1.0
    t = min(1.0, max(0.0, edge_distance(point, polygon) / feather))
    return 1.0 - t * t * (3.0 - 2.0 * t)


def exclusion_reason(point, geometry):
    if polygon_contains(point, geometry.gameplay) or edge_distance(point, geometry.gameplay) < 48.0:
        return "gameplay"
    for name, anchor in geometry.anchors:
        if math.dist(point, anchor) < 160.0:
            return "anchor:" + name
    for name, polygon, _ in geometry.overlays:
        if overlay_weight(point, polygon, 48.0) > 0.0:
            return "authored:" + name
    for name, polygon, feather in geometry.overlays:
        if overlay_weight(point, polygon, feather) > 0.0:
            return "skirt:" + name
    return None


def ground_id(cover, subtype_random):
    return 0 if cover < 0.64 else 1 + min(3, int(subtype_random * 4.0))


def classify(cell, seed, geometry):
    """Cell classification only. No material classification at arbitrary points."""
    point = center(cell)
    if exclusion_reason(point, geometry) is not None:
        return 0
    cover = noise(tuple(value / 768 for value in point), seed, 8)
    cover += 0.18 * noise(tuple(value / 192 for value in point), seed, 9)
    return ground_id(cover, coordinate_random(cell, seed, 10))
