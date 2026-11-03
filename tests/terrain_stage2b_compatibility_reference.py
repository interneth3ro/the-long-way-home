"""Read-only, bounded compatibility audit; no engine, field or output writer.

Exact rational geometry is separate from the frozen Stage 2A binary64 classifier.
Certificates concern the documented geometry/model envelope, never Godot parity.
"""
from dataclasses import dataclass
from fractions import Fraction as F
import math
from math import ceil, floor, isqrt

import terrain_stage2_reference as classification


BASE = "1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744"
SEEDS = (26026, 0, -42, -1, 2147483647, 2147483648, -2147483648)
SCALE = 10**12  # rational sqrt enclosure width <= 1e-12 world units
NUMERIC_BAND = F(1, 10000)  # deliberately wider binary64 endpoint guard
COMPATIBLE = "compatible within model/envelope"
CONFLICT = "conflict"
INSUFFICIENT = "insufficient margin"
UNRESOLVED = "unresolved numeric case"
EARTH = "Earth (no Green constraint)"


@dataclass(frozen=True)
class Primitive:
    name: str
    kind: str  # circle, polygon, feather
    points: tuple
    radius: F


@dataclass(frozen=True)
class Clearance:
    nearest: tuple
    relation: str  # inside, boundary, outside the ideal closed union
    lower: F
    upper: F
    model_predicate: bool
    model_reason: str | None
    uncertainty: tuple
    covered_endpoints: tuple  # observations resolved by strict union interior


@dataclass(frozen=True)
class Anchor:
    seed: int
    cell: tuple
    world_center: tuple
    original_id: int
    binary_anchor: int
    clearance: Clearance
    margin: F | None
    outcome: str


@dataclass(frozen=True)
class Audit:
    seed: int
    bounds: tuple
    cells: tuple  # inclusive min-x, min-y, max-x, max-y
    outside_lower: F
    anchors: tuple
    margin: F | None
    outcome: str


def squared_segment_distance(point, a, b):
    """Clamped projection; rational dot products, including degenerate segments."""
    point, a, b = (tuple(map(F, v)) for v in (point, a, b))
    d = tuple(y - x for x, y in zip(a, b))
    v = tuple(x - y for x, y in zip(point, a))
    length = sum(x * x for x in d)
    t = max(F(0), min(F(1), sum(x * y for x, y in zip(v, d)) / length)) if length else F(0)
    return sum((x - t * y)**2 for x, y in zip(v, d))


def squared_polygon_distance(point, polygon):
    """Distance to filled polygon, with exact boundary and ray-crossing tests."""
    point = tuple(map(F, point))
    polygon = tuple(tuple(map(F, p)) for p in polygon)
    if len(polygon) < 3:
        raise ValueError("A filled polygon needs at least three vertices")
    edges = tuple(zip(polygon, polygon[1:] + polygon[:1]))
    distance = min(squared_segment_distance(point, a, b) for a, b in edges)
    if distance == 0:
        return F(0)
    x, y = point
    crossings = sum((a[1] > y) != (b[1] > y)
                    and a[0] + (y - a[1]) * (b[0] - a[0]) / (b[1] - a[1]) > x
                    for a, b in edges)
    return F(0) if crossings % 2 else distance


def sqrt_bounds(squared):
    """Integer sqrt gives a proof enclosure, without floating sqrt/tolerance."""
    squared = F(squared)
    if squared < 0:
        raise ValueError("Negative squared distance")
    n = isqrt(squared.numerator * SCALE**2 // squared.denominator)
    lower = F(n, SCALE)
    return lower, lower if lower * lower == squared else F(n + 1, SCALE)


def primitives(geometry):
    records = []
    if geometry.gameplay:
        records.append(Primitive("gameplay", "polygon", geometry.gameplay, F(48)))
    records.extend(Primitive("anchor:" + name, "circle", (point,), F(160))
                   for name, point in geometry.anchors)
    records.extend(Primitive("authored:" + name, "feather", polygon, F(48))
                   for name, polygon, _ in geometry.overlays)
    records.extend(Primitive("skirt:" + name, "feather", polygon, F(feather))
                   for name, polygon, feather in geometry.overlays)
    if not records or any(p.radius <= 0 for p in records):
        raise ValueError("Expected nonempty geometry with positive reaches")
    return tuple(records)


def primitive_distance_squared(point, primitive):
    if primitive.kind == "circle":
        return sum((F(x) - F(y))**2 for x, y in zip(point, primitive.points[0]))
    return squared_polygon_distance(point, primitive.points)


def clearance(point, geometry):
    """Distance to ideal closure plus explicit computed-predicate disagreements.

    A positive certificate is reduced by NUMERIC_BAND. Feather boundaries or
    disagreements never become conflicts by assuming the ideal offset is exact
    production truth. Strict-circle exact boundaries remain proof cases.
    """
    rows, uncertain, robust_interior = [], [], []
    for primitive in primitives(geometry):
        squared = primitive_distance_squared(point, primitive)
        lo, hi = sqrt_bounds(squared)
        radius = primitive.radius
        relation = "inside" if squared < radius**2 else "boundary" if squared == radius**2 else "outside"
        lower, upper = max(F(0), lo - radius), max(F(0), hi - radius)
        if primitive.kind == "feather":
            predicate = classification.overlay_weight(point, primitive.points, float(radius)) > 0
        elif primitive.kind == "circle":
            # The existing model is authoritative for the reported predicate.
            predicate = math.dist(point, primitive.points[0]) < float(radius)
        else:
            predicate = (classification.polygon_contains(point, primitive.points)
                         or classification.edge_distance(point, primitive.points) < float(radius))
        if predicate != (relation == "inside"):
            uncertain.append(primitive.name + ": computed predicate disagrees with ideal open offset")
        if lo - radius <= NUMERIC_BAND and hi - radius >= -NUMERIC_BAND:
            # Exact non-feather boundary is independently decidable in this model.
            if primitive.kind == "feather" or relation != "boundary":
                uncertain.append(primitive.name + ": numeric endpoint band")
        if hi + NUMERIC_BAND < radius and predicate:
            robust_interior.append(primitive.name)
        rows.append((primitive.name, lower, upper, relation))
    lower, upper = min(r[1] for r in rows), min(r[2] for r in rows)
    nearest = tuple(sorted(r[0] for r in rows if r[1] <= upper))
    relation = ("inside" if any(r[3] == "inside" for r in rows) else
                "boundary" if any(r[3] == "boundary" for r in rows) else "outside")
    reason = classification.exclusion_reason(point, geometry)
    if (reason is not None) != (relation == "inside"):
        uncertain.append("union: computed predicate disagrees with ideal open union")
    covered = ()
    if robust_interior and reason is not None:
        # A neighborhood is already excluded by another primitive. An internal
        # endpoint cannot change membership or distance to closure of the union.
        covered, uncertain = tuple(sorted(uncertain)), []
    records = primitives(geometry)
    if (any(abs(F(v)) > 2048 for v in point)
            or any(abs(F(v)) > 2048 for p in records for q in p.points for v in q)
            or any(p.radius > 256 for p in records)
            or any(0 < sum((F(x) - F(y))**2 for x, y in zip(a, b)) < 1
                   for p in records if p.kind != "circle"
                   for a, b in zip(p.points, p.points[1:] + p.points[:1]))):
        uncertain.append("outside reviewed binary64 geometry envelope")
    # Retain exact geometric bounds. The decision below applies the separate band.
    return Clearance(nearest, relation, lower, upper, reason is not None, reason,
                     tuple(sorted(uncertain)), covered)


def outcome(original_id, distance, margin=None):
    """original_id is independently supplied; never repaired from geometry."""
    if original_id not in range(5):
        raise ValueError("Expected original material ID 0..4")
    margin = None if margin is None else F(margin)
    if margin is not None and margin < 0:
        raise ValueError("Margin must be nonnegative")
    if distance.uncertainty:
        return UNRESOLVED
    if not original_id:
        return EARTH
    if distance.relation in ("inside", "boundary"):
        return CONFLICT
    certified_lower = max(F(0), distance.lower - NUMERIC_BAND)
    if not certified_lower:
        return UNRESOLVED
    if margin is not None:
        # Insufficiency requires an upper bound, not merely failure of the lower.
        if distance.upper + NUMERIC_BAND < margin:
            return INSUFFICIENT
        if certified_lower < margin:
            return UNRESOLVED
    return COMPATIBLE


def anchor(cell, seed, geometry, margin=None, distance=None):
    point = classification.center(cell)
    original_id = classification.classify(cell, seed, geometry)
    distance = clearance(point, geometry) if distance is None else distance
    margin = None if margin is None else F(margin)
    return Anchor(seed, tuple(cell), point, original_id, int(original_id > 0),
                  distance, margin, outcome(original_id, distance, margin))


def envelope(geometry):
    """Offset union AABB, first outside ring, then a bound for all other centers."""
    boxes = [(min(F(p[0]) for p in r.points) - r.radius,
              min(F(p[1]) for p in r.points) - r.radius,
              max(F(p[0]) for p in r.points) + r.radius,
              max(F(p[1]) for p in r.points) + r.radius) for r in primitives(geometry)]
    bounds = (min(b[0] for b in boxes), min(b[1] for b in boxes),
              max(b[2] for b in boxes), max(b[3] for b in boxes))
    x0, y0 = (ceil((v - 32) / 64) - 1 for v in bounds[:2])
    x1, y1 = (floor((v - 32) / 64) + 1 for v in bounds[2:])
    outside_lower = min(bounds[0] - (64 * (x0 - 1) + 32),
                        bounds[1] - (64 * (y0 - 1) + 32),
                        64 * (x1 + 1) + 32 - bounds[2],
                        64 * (y1 + 1) + 32 - bounds[3]) - NUMERIC_BAND
    return bounds, (x0, y0, x1, y1), outside_lower


def audit(geometry, seeds=SEEDS, margin=None, query_order=None):
    """Exhaust every center, even Earth; canonicalize order, reject missing cells.

    Outside-envelope margin larger than the proved lower bound is unresolved:
    the audit does not silently extrapolate or infer distant noise classifications.
    """
    bounds, cells, outside_lower = envelope(geometry)
    x0, y0, x1, y1 = cells
    required = {(x, y) for x in range(x0, x1 + 1) for y in range(y0, y1 + 1)}
    order = sorted(required) if query_order is None else list(query_order)
    if len(order) != len(required) or set(order) != required:
        raise ValueError("Audit requires each envelope center exactly once")
    distances = {cell: clearance(classification.center(cell), geometry) for cell in order}
    margin = None if margin is None else F(margin)
    reports = []
    for seed in sorted(set(seeds)):
        records = tuple(anchor(c, seed, geometry, margin, distances[c]) for c in sorted(required))
        outcomes = {a.outcome for a in records}
        result = next((value for value in (CONFLICT, UNRESOLVED, INSUFFICIENT) if value in outcomes), COMPATIBLE)
        if result == COMPATIBLE and margin is not None and margin > outside_lower:
            result = UNRESOLVED
        reports.append(Audit(seed, bounds, cells, outside_lower, records, margin, result))
    return tuple(reports)
