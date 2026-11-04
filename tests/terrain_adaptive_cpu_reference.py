"""One offline adaptive box-cover candidate. Never an engine/GPU enclosure.

Exact rational closed offset geometry, with the previous 1/10000 guard.
Uncertain leaves are BLOCKED, never sampled/interpolated into permission.
"""
from fractions import Fraction as F
import math
import time

import terrain_stage2_reference as ids
import terrain_stage2b_compatibility_reference as geometry
import terrain_stage2b2_reconstruction_reference as baseline

IDENTITY = "5846d34ec602ba20d3a4f84c63c123b4cfd41104d4a943986df600174520b590"
GUARD = F(1, 10000)
LIMIT = 32768
HALO = 32800


def box_squared(p, box):
    return sum(max(box[i]-p[i], 0, p[i]-box[i+2])**2 for i in (0, 1))


def point(p, halo=False):
    if (len(p) != 2 or any(isinstance(v, bool) or not isinstance(v, (int, float, F))
                          or not math.isfinite(v) for v in p)):
        raise ValueError("Finite two-dimensional input required")
    p = tuple(map(F, p))
    if any(not (-HALO <= v <= HALO if halo else -LIMIT <= v < LIMIT) for v in p):
        raise ValueError("Outside owned study domain / explicit center halo")
    return p


class Cover:
    """Shared seed-independent cover; all coordinates and certificates rational.

    Center-to-box L1 radius equals its side, bounds Euclidean displacement.
    Distance to a closed filled primitive is 1-Lipschitz. An OUT leaf therefore
    cannot meet the guarded union. IN leaves and unresolved leaves cover it.
    Refine unresolved 8-unit leaves only if they touch an eligible lattice center.
    """
    def __init__(self, authored, seconds=60):
        if ids.geometry_identity(authored) != IDENTITY:
            raise ValueError("Unreviewed authored geometry")
        self.authored = authored
        self.primitives = geometry.primitives(authored)
        self.boxes = []
        self.leaves = []
        self.nodes = 0
        self.deadline = time.monotonic()+seconds
        self._build((-2048, -2048, 2048, 2048), 0)
        self.buckets = {}
        for index, box in enumerate(self.boxes):
            # g reaches its 16 cap by distance sqrt(512) < 24. Every box
            # that can lower a query is indexed into that query's 64-unit bin.
            for y in range(math.floor((box[1]-24)/64), math.floor((box[3]+24)/64)+1):
                for x in range(math.floor((box[0]-24)/64), math.floor((box[2]+24)/64)+1):
                    self.buckets.setdefault((x, y), []).append(index)

    def interval(self, box):
        side = box[2]-box[0]
        p = ((box[0]+box[2])/2, (box[1]+box[3])/2)
        lower, upper = [], []
        for primitive in self.primitives:
            # Cheap exact AABB rejection before polygon distance.
            bounds = tuple(min(q[i] for q in primitive.points) for i in (0, 1)) + tuple(
                max(q[i] for q in primitive.points) for i in (0, 1))
            radius = primitive.radius+GUARD
            if box_squared(p, bounds) > (radius+side)**2:
                lower.append(F(1)); upper.append(F(1))
                continue
            lo, hi = geometry.sqrt_bounds(geometry.primitive_distance_squared(p, primitive))
            lower.append(lo-radius-side)
            upper.append(hi-radius+side)
        return min(lower), min(upper)

    def eligible_center_touches(self, box):
        for y in range(math.ceil((box[1]-32)/64), math.floor((box[3]-32)/64)+1):
            for x in range(math.ceil((box[0]-32)/64), math.floor((box[2]-32)/64)+1):
                p = ids.center((x, y))
                # Seed-independent: even a presently Earth center is reserved
                # if it lies outside K_guard. Original IDs remain separate.
                if all(geometry.primitive_distance_squared(p, primitive) >
                       (primitive.radius+GUARD)**2 for primitive in self.primitives):
                    return True
        return False

    def _build(self, box, depth):
        self.nodes += 1
        if self.nodes > 20000 or time.monotonic() > self.deadline:
            raise RuntimeError("Preparation budget exceeded; stop, no automatic retry")
        box = tuple(map(F, box))
        lo, hi = self.interval(box)
        state = "outside" if lo > 0 else "inside" if hi <= 0 else "uncertain"
        if state == "uncertain" and (box[2]-box[0] > 8 or self.eligible_center_touches(box)):
            if depth >= 18:
                raise RuntimeError("Cannot preserve lattice center within depth budget")
            mx, my = (box[0]+box[2])/2, (box[1]+box[3])/2
            for child in ((box[0], box[1], mx, my), (mx, box[1], box[2], my),
                          (box[0], my, mx, box[3]), (mx, my, box[2], box[3])):
                self._build(child, depth+1)
            return
        self.leaves.append((box, state))
        if state != "outside":
            self.boxes.append(box)

    def distance_surrogate(self, p):
        """Continuous exact squared box distance /32, capped at 16."""
        nearby = self.buckets.get(tuple(math.floor(v/64) for v in p), ())
        return min((min(F(16), box_squared(p, self.boxes[i])/32) for i in nearby), default=F(16))

    def payload(self):
        """Canonical dyadic box list. Index is derived, not free storage."""
        return [[str(v) for v in box] for box in self.boxes]


class Field:
    def __init__(self, cover, seed):
        if type(seed) is not int or not -(2**63) <= seed < 2**63:
            raise ValueError("Signed int64 seed required")
        self.cover, self.seed = cover, seed
        self.centers = {}

    def center_record(self, cell):
        if len(cell) != 2 or any(type(v) is not int for v in cell):
            raise ValueError("Integer absolute cell required")
        cell = tuple(cell)
        p = point(ids.center(cell), halo=True)
        if cell not in self.centers:
            material = ids.classify(cell, self.seed, self.cover.authored)
            g = self.cover.distance_surrogate(p)
            if material and g <= 0:
                raise RuntimeError("BLOCKED: cover consumes original Green center")
            self.centers[cell] = material, min(F(16), g/2) if material else F(16)
        return self.centers[cell]

    def values(self, p):
        p = point(p)
        q = tuple(math.floor((v-32)/64) for v in p)
        u, v = (baseline.smooth((p[i]-64*q[i]-32)/64) for i in (0, 1))
        raw, scale = F(0), F(0)
        for dy in (0, 1):
            for dx in (0, 1):
                material, s = self.center_record((q[0]+dx, q[1]+dy))
                w = (u if dx else 1-u)*(v if dy else 1-v)
                raw += int(material > 0)*w
                scale += s*w
        a = baseline.smooth(baseline.clamp((raw-F(5, 32))/F(11, 16)))
        protection = baseline.smooth(baseline.clamp(self.cover.distance_surrogate(p)/scale))
        return a, a*protection
