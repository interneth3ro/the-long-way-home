"""Bounded offline proof/reference. No engine or image side effects on import."""
from fractions import Fraction as F
import hashlib
import math
import sys

import terrain_stage2_reference as classification
import terrain_stage2b_compatibility_reference as compatibility

BASE = "1f4ac408c31b99be4ab7158960dab06adec93871"
CEILING = 2**21
EPSILON = F(1, 10000)
CAP = F(16)
RULE = "stage2b2-paired-v1"
TIE_RULE = "midpoint-tie-v1"
MIDPOINTS = {"N": (32, 0), "E": (64, 32), "S": (32, 64), "W": (0, 32)}
SEGMENTS = {0: (), 1: ("NW",), 2: ("NE",), 3: ("WE",), 4: ("ES",),
            6: ("NS",), 7: ("SW",), 8: ("SW",), 9: ("NS",),
            11: ("ES",), 12: ("WE",), 13: ("NE",), 14: ("NW",), 15: ()}


def tie_digest(seed, square):
    # ASCII subset of UTF-8; no spaces, plus signs, or terminal newline.
    payload = f"{TIE_RULE}|{seed % classification.MODULUS}|{square[0]}|{square[1]}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def contour_segments(pattern, tie):
    if pattern not in range(16) or tie not in (0, 1):
        raise ValueError("Invalid pattern/tie")
    names = (("NE", "SW") if tie == 0 else ("NW", "ES")) if pattern in (5, 10) else SEGMENTS[pattern]
    return tuple((MIDPOINTS[name[0]], MIDPOINTS[name[1]]) for name in names)


def source_bounds(rect, gutter=0, radius=None):
    """Inclusive centers for A; inclusive squares for B, including closed edges."""
    x0, y0, x1, y1 = map(F, rect)
    if x1 < x0 or y1 < y0 or gutter < 0 or (radius is not None and radius < 0):
        raise ValueError("Invalid extent")
    lo, hi = (x0-gutter, y0-gutter), (x1+gutter, y1+gutter)
    for p in (lo, hi):
        checked_point(p)
    if radius is None:
        bounds = (math.floor((lo[0]-32)/64), math.floor((lo[1]-32)/64),
                  math.floor((hi[0]-32)/64)+1, math.floor((hi[1]-32)/64)+1)
        last = bounds[2:]
    else:
        bounds = (math.ceil((lo[0]-radius-96)/64), math.ceil((lo[1]-radius-96)/64),
                  math.floor((hi[0]+radius-32)/64), math.floor((hi[1]+radius-32)/64))
        last = (bounds[2]+1, bounds[3]+1)
    checked_point(classification.center(bounds[:2]))
    checked_point(classification.center(last))
    return bounds


class Reconstruction:
    def __init__(self, material, seed, protection=None):
        self.material = material
        self.seed = seed
        self.protection = protection
        self.squares = {}

    def square(self, q):
        q = tuple(q)
        if q not in self.squares:
            cells = ((q[0], q[1]), (q[0]+1, q[1]), (q[0]+1, q[1]+1), (q[0], q[1]+1))
            for cell in cells:
                checked_point(classification.center(cell))
            ids = tuple(self.material(cell) for cell in cells)
            if any(m not in range(5) for m in ids):
                raise ValueError("Original material must be 0..4")
            pattern = sum((1 << i) for i, material in enumerate(ids) if material > 0)
            tie = int(tie_digest(self.seed, q)[-1], 16) & 1
            self.squares[q] = (ids, pattern, contour_segments(pattern, tie))
        return self.squares[q]

    def values(self, point):
        """Control A, sharpened A (a=5/32), B (w=16), shared protection."""
        p = checked_point(point)
        q = tuple((v-32)//64 for v in p)
        local = tuple(p[i]-(64*q[i]+32) for i in (0, 1))
        ids, pattern, segments = self.square(q)
        u, v = (smooth(value/64) for value in local)
        b = tuple(int(m > 0) for m in ids)
        f = (b[0]*(1-u)+b[1]*u)*(1-v) + (b[3]*(1-u)+b[2]*u)*v
        sharpened = smooth(clamp((f-F(5, 32))/F(11, 16)))
        # Crossing from the left edge. Half-open y convention agrees between
        # adjacent squares; points on contour have distance zero regardless.
        green = bool(pattern & (1 if local[1] < 32 else 8))
        for a, z in segments:
            if (a[1] > local[1]) != (z[1] > local[1]):
                cross = a[0] + (local[1]-a[1])*F(z[0]-a[0], z[1]-a[1])
                if 0 <= cross <= local[0]:
                    green = not green
        bounds = source_bounds((*p, *p), radius=16)
        squared = F(16**2)
        for y in range(bounds[1], bounds[3]+1):
            for x in range(bounds[0], bounds[2]+1):
                origin = classification.center((x, y))
                for a, z in self.square((x, y))[2]:
                    a = tuple(origin[i]+a[i] for i in (0, 1))
                    z = tuple(origin[i]+z[i] for i in (0, 1))
                    squared = min(squared, compatibility.squared_segment_distance(p, a, z))
        distance = math.sqrt(float(squared))
        contour = smooth(clamp(0.5 + (distance if green else -distance)/32))
        protection = self.protection.value(p) if self.protection else 1.0
        return (float(f), float(sharpened), contour, protection)


def smooth(t):
    return t * t * (3 - 2 * t)


def clamp(t, lo=0, hi=1):
    return max(lo, min(hi, t))


def checked_point(point):
    if len(point) != 2 or any(not math.isfinite(v) or abs(v) > CEILING for v in point):
        raise ValueError("Query outside finite offline arithmetic ceiling")
    return tuple(F(v) for v in point)


def runtime_contract():
    """Verify supported interpreter metadata, not a binary/source attestation."""
    return (sys.implementation.name == "cpython"
            and sys.version_info[:3] == (3, 14, 7)
            and sys.float_info.radix == 2 and sys.float_info.mant_dig == 53
            and sys.float_info.rounds == 1)


def geometry_contract(geometry):
    records = compatibility.primitives(geometry)
    return (all(p.radius in (48, 160, 256) for p in records)
            and all(F(v).denominator == 1 and abs(v) <= 1024
                    for p in records for q in p.points for v in q))


class Protection:
    """Exact rational shared protection; cache contains only immutable center data."""
    def __init__(self, seed, geometry):
        if not runtime_contract() or not geometry_contract(geometry):
            raise ValueError("Unresolved numerical case: unsupported runtime/geometry")
        self.seed = seed
        self.geometry = geometry
        self.primitives = compatibility.primitives(geometry)
        self.bounds, self.cells, _ = compatibility.envelope(geometry)
        if self.bounds != (-1280, -1280, 1280, 1280):
            raise ValueError("Unreviewed protection envelope")
        self.cutoff = tuple(v + (-1 if i < 2 else 1) * (EPSILON + CAP)
                            for i, v in enumerate(self.bounds))
        self.centers = {}

    def center_record(self, cell):
        cell = tuple(cell)
        if cell in self.centers:
            return self.centers[cell]
        point = classification.center(cell)
        checked_point(point)
        material = classification.classify(cell, self.seed, self.geometry)
        lower = None
        if material:
            x0, y0, x1, y1 = self.cells
            if not (x0 <= cell[0] <= x1 and y0 <= cell[1] <= y1):
                lower = F(96) - EPSILON
            else:
                lower = min(compatibility.sqrt_bounds(
                    compatibility.primitive_distance_squared(point, primitive))[0]
                    - primitive.radius - EPSILON for primitive in self.primitives)
            if lower <= 0:
                raise ValueError("Insufficient margin: enclosure consumes certified Green clearance")
        scale = min(CAP, lower / 2) if material else CAP
        record = (material, int(material > 0), lower, scale)
        self.centers[cell] = record
        return record

    def value(self, point):
        p = checked_point(point)
        x0, y0, x1, y1 = self.cutoff
        if p[0] <= x0 or p[1] <= y0 or p[0] >= x1 or p[1] >= y1:
            return 1.0
        g = CAP
        for primitive in self.primitives:
            radius = primitive.radius + EPSILON
            squared = compatibility.primitive_distance_squared(p, primitive)
            g = min(g, clamp((squared - radius**2) / (2 * radius + CAP), 0, CAP))
            if g == 0:
                return 0.0
        q = tuple((v - 32) // 64 for v in p)
        u, v = (smooth((p[i] - (64 * q[i] + 32)) / 64) for i in (0, 1))
        scale = sum(self.center_record((q[0] + dx, q[1] + dy))[3]
                    * (u if dx else 1 - u) * (v if dy else 1 - v)
                    for dy in (0, 1) for dx in (0, 1))
        return float(smooth(clamp(g / scale)))
