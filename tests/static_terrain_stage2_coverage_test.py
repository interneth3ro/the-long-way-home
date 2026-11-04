"""Stage 2A: independent math, model comparisons, metamorphic and source guards.

Never imports GDScript, invokes Godot, regenerates artwork or writes fixtures.
"""
from fractions import Fraction
import hashlib
import json
import math
import random
import subprocess
import unittest

import terrain_stage2_reference as reference
from static_ground_rejection_test import authored_geometry, material_at, original_protection
from static_low_green_ground_test import inside
from static_weathered_earth_test import coordinate_random, noise


ROOT = reference.ROOT
FIXTURE = ROOT / "tests/fixtures/terrain_stage2_classification_vectors.json"
NEW_FILES = {
    "docs/experiments/terrain_stage2_coverage.md",
    "tests/terrain_stage2_reference.py",
    "tests/static_terrain_stage2_coverage_test.py",
    "tests/fixtures/terrain_stage2_classification_vectors.json",
}


def rational_hash(x, y, seed, channel):
    """Independent integer calculation; returns numerator, not a float sample."""
    modulus = 2147483647
    a = (48271 * (seed % modulus) + 69621 * (x % modulus)) % modulus
    b = (48271 * a + 907 * (y % modulus)) % modulus
    c = (48271 * b + 104729 * channel) % modulus
    return ((c ^ (c // 8192)) * 48271) % modulus


def rational_cover(cell, seed):
    """Exact real-arithmetic oracle for cell-center noise, without geometry.

    Fractions avoid the new model's binary64 evaluation and weighted-sum order.
    Decimal source constants 0.18/0.64 are interpreted as 9/50 and 16/25 here.
    This independent arithmetic check is deliberately not an engine emulator.
    """
    def sample(scale, channel):
        x, y = (Fraction(2 * c + 1, 2 * scale) for c in cell)
        ix, iy = math.floor(x), math.floor(y)
        u, v = x - ix, y - iy
        u, v = u * u * (3 - 2 * u), v * v * (3 - 2 * v)
        a, b = rational_hash(ix, iy, seed, channel), rational_hash(ix + 1, iy, seed, channel)
        c, d = rational_hash(ix, iy + 1, seed, channel), rational_hash(ix + 1, iy + 1, seed, channel)
        return ((a + u * (b - a)) + v * ((c + u * (d - c)) - (a + u * (b - a)))) / 2147483647
    return sample(12, 8) + Fraction(9, 50) * sample(3, 9)


class Stage2ClassificationTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = reference.load_geometry()
        cls.original = authored_geometry()
        cls.vectors = json.loads(FIXTURE.read_text())

    def test_independent_goldens_exact_ids_and_provenance(self):
        self.assertEqual(self.vectors["classification_rule"], reference.RULE)
        self.assertEqual(self.vectors["geometry_sha256"], reference.geometry_identity(self.geometry))
        self.assertEqual(len(self.vectors["records"]), 14)
        self.assertEqual({v["material"] for v in self.vectors["records"]}, set(range(5)))
        for vector in self.vectors["records"]:
            cell, seed = tuple(vector["cell"]), vector["seed"]
            self.assertEqual(list(reference.center(cell)), vector["world_center"])
            self.assertEqual(vector["binary"], int(vector["material"] > 0))
            self.assertTrue(vector["rationale"] and vector["provenance"])
            if "exact_cover" in vector:
                cover = rational_cover(cell, seed)
                numerator = rational_hash(*cell, seed, 10)
                self.assertEqual(str(cover), vector["exact_cover"])
                self.assertEqual(numerator, vector["subtype_hash_numerator"])
                expected = 0 if cover < Fraction(16, 25) else 1 + (4 * numerator) // 2147483647
                self.assertEqual(expected, vector["material"])
                self.assertGreater(abs(float(cover) - 0.64), 1e-4)
                self.assertIsNone(reference.exclusion_reason(reference.center(cell), self.geometry))
            else:
                polygon = (self.original[1][2][0] if vector["rationale"].startswith("NorthRidge")
                           else self.original[0])
                self.assertTrue(inside(reference.center(cell), polygon))
                self.assertTrue(original_protection(reference.center(cell), *self.original))
                self.assertEqual(vector["material"], 0)
            self.assertEqual(reference.classify(cell, seed, self.geometry), vector["material"])

    def test_independent_simple_geometry_and_exact_boundaries(self):
        square = ((0.0, 0.0), (10.0, 0.0), (10.0, 10.0), (0.0, 10.0))
        gameplay = reference.Geometry(square, (), ())
        for point in ((5, 5), (0, 0), (10, 5), (57.999, 5)):
            self.assertEqual(reference.exclusion_reason(point, gameplay), "gameplay")
        for point in ((58, 5), (58.001, 5)):
            self.assertIsNone(reference.exclusion_reason(point, gameplay))
        # 3-4-5 projection at a corner is independent of ray-crossing policy.
        self.assertEqual(reference.edge_distance((-3, -4), square), 5)
        anchor = reference.Geometry((), (), (("test", (1000, 1000)),))
        self.assertEqual(reference.exclusion_reason((1159.999, 1000), anchor), "anchor:test")
        self.assertIsNone(reference.exclusion_reason((1160, 1000), anchor))
        self.assertIsNone(reference.exclusion_reason((1160.001, 1000), anchor))
        overlay = reference.Geometry((), (("test", square, 256.0),), ())
        self.assertEqual(reference.exclusion_reason((57.999, 5), overlay), "authored:test")
        self.assertEqual(reference.exclusion_reason((58, 5), overlay), "skirt:test")
        self.assertEqual(reference.exclusion_reason((265.999, 5), overlay), "skirt:test")
        self.assertIsNone(reference.exclusion_reason((266, 5), overlay))
        self.assertIsNone(reference.exclusion_reason((266.001, 5), overlay))

    def test_independent_threshold_and_subtype_intervals(self):
        below, above = math.nextafter(0.64, -math.inf), math.nextafter(0.64, math.inf)
        self.assertEqual(reference.ground_id(below, 0.9), 0)
        for cover in (0.64, above):
            for value, expected in ((0, 1), (0.25, 2), (0.5, 3), (0.75, 4)):
                self.assertEqual(reference.ground_id(cover, value), expected)
        self.assertEqual(reference.coordinate_random((0, 0), 0, 0), 0)
        self.assertEqual(reference.noise((0, 0), 0, 0), 0)

    def test_independent_half_open_floor_and_chunk_ownership(self):
        for boundary in (-512, -4, -1, 0, 1, 4, 512):
            world = boundary * 2048
            for offset, expected in ((-0.001, boundary - 1), (0, boundary), (0.001, boundary)):
                cell = reference.world_to_cell((world + offset, world + offset))
                chunk, local = reference.chunk_and_local(cell)
                self.assertEqual(chunk, (expected, expected))
                self.assertTrue(all(0 <= value < 32 for value in local))
                self.assertEqual(tuple(c * 32 + v for c, v in zip(chunk, local)), cell)
        self.assertEqual(reference.world_to_cell((-0.001, 0)), (-1, 0))
        self.assertEqual(reference.world_to_cell((-0.001, 0), 32), (-1, 0))
        self.assertEqual(reference.chunk_and_local((-1, -33)), ((-1, -2), (31, 31)))

    def test_model_equivalence_bounded_production_samples(self):
        cells = {(cx * 32 + x, cy * 32 + y)
                 for cx in range(-4, 5) for cy in range(-4, 5)
                 for x in (-1, 0, 15, 31, 32) for y in (-1, 0, 15, 31, 32)}
        cells.update((x, y) for x in range(-24, 25, 3) for y in range(-24, 25, 3))
        cells.update((c * 32 + d, e * 32 + f) for c in (-512, 512) for e in (-512, 512)
                     for d in (-1, 0, 31, 32) for f in (-1, 0, 31, 32))
        for seed in (0, 26026, -42, -1, 2147483647, 2147483648, -2147483648):
            for cell in sorted(cells):
                expected = material_at(reference.center(cell), seed, self.original)
                self.assertEqual(reference.classify(cell, seed, self.geometry), expected, (seed, cell))

    def test_model_geometry_extraction_is_current_and_ordered(self):
        self.assertEqual(self.geometry.gameplay, tuple(self.original[0]))
        self.assertEqual([p for _, p, _ in self.geometry.overlays], [tuple(p) for p, _ in self.original[1]])
        self.assertEqual([p for _, p in self.geometry.anchors], self.original[2])
        self.assertEqual([n for n, _, _ in self.geometry.overlays],
                         ["Clearing", "ImpactScar", "NorthRidge", "SouthShelf"])
        self.assertEqual([n for n, _ in self.geometry.anchors], ["CrashedShip", "Hatch", "WestRock", "EastRock"])
        self.assertEqual([f for _, _, f in self.geometry.overlays], [256.0] * 4)

    def test_model_real_geometry_edge_vertex_and_clearance_probes(self):
        points = []
        for polygon, reach in [(self.geometry.gameplay, 48),
                               *((p, f) for _, p, f in self.geometry.overlays)]:
            for a, b in zip(polygon, polygon[1:] + polygon[:1]):
                dx, dy = b[0] - a[0], b[1] - a[1]
                length = math.hypot(dx, dy)
                for distance in (0, 0.001, 47.999, 48, 48.001, reach - 0.001, reach, reach + 0.001):
                    for sign in (-1, 1):
                        points.append(((a[0] + b[0]) / 2 - sign * dy * distance / length,
                                       (a[1] + b[1]) / 2 + sign * dx * distance / length))
                points.extend(((a[0] + d, a[1] + e) for d in (-0.001, 0, 0.001) for e in (-0.001, 0, 0.001)))
        for _, (x, y) in self.geometry.anchors:
            points.extend((x + d, y) for d in (-160.001, -160, -159.999, 0, 159.999, 160, 160.001))
        for point in points:
            self.assertEqual(reference.exclusion_reason(point, self.geometry) is not None,
                             original_protection(point, *self.original), point)

    def test_model_hash_noise_crosscheck(self):
        for seed in (0, 26026, -42, -(2**63), 2**63 - 1):
            for cell in ((-16385, 16384), (-33, -1), (0, 0), (31, 32), (16384, -16385)):
                for channel in (8, 9, 10):
                    self.assertEqual(reference.coordinate_random(cell, seed, channel), coordinate_random(*cell, seed, channel))
                    point = (cell[0] / 12, cell[1] / 12)
                    self.assertAlmostEqual(reference.noise(point, seed, channel), noise(*point, seed, channel), places=14)

    def test_metamorphic_seed_alias_order_and_reload(self):
        cells = [(x, y) for x in (-129, -33, -1, 0, 31, 128, 16384) for y in (-16385, -32, 0, 32, 129)]
        expected = {cell: reference.classify(cell, -42, self.geometry) for cell in cells}
        shuffled = list(cells)
        random.Random(133).shuffle(shuffled)
        for order in (cells[::-1], shuffled):
            self.assertEqual(expected, {c: reference.classify(c, -42, reference.load_geometry()) for c in order})
        for seed in (0, 26026, -42):
            for cell in cells:
                self.assertEqual(reference.classify(cell, seed, self.geometry),
                                 reference.classify(cell, seed + reference.MODULUS, self.geometry))
                self.assertEqual(reference.classify(cell, seed, self.geometry),
                                 reference.classify(cell, seed - reference.MODULUS, self.geometry))

    def test_source_guards_reviewed_provenance_and_protected_files(self):
        for path, digest in self.vectors["source_sha256_lf"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), digest)
        # Historical Stage 2A inventory is immutable, not a ban on later additions.
        # Keep the working-source preservation checks below against the same base.
        stage2a_merge = "1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744"
        changes = subprocess.check_output(
            ["git", "diff", "--name-status", reference.BASE, stage2a_merge, "--"], cwd=ROOT, text=True)
        self.assertEqual({line.split("\t", 1)[1] for line in changes.splitlines()}, NEW_FILES)
        for line in changes.splitlines():
            status, path = line.split("\t", 1)
            self.assertEqual(status, "A", line)
            self.assertIn(path, NEW_FILES)
        for path in ("scenes/world/planet_generator.gd", "scenes/world/world_coordinates.gd",
                     "scenes/world/planet_world_state.gd", "scenes/world/terrain_chunk.gd",
                     "scenes/world/planet_exterior.gd", "scenes/world/planet_exterior.tscn",
                     "scenes/world/illustrated_terrain_presenter.gd", "scenes/world/terrain_resolver.gd",
                     "scenes/world/terrain_assignment_lookup.gd", "scenes/world/ferrite_region_generator.gd",
                     "scenes/main/scene_transition_controller.gd", "project.godot", "tools/run-local-tests.ps1"):
            baseline = subprocess.check_output(["git", "show", f"{reference.BASE}:{path}"], cwd=ROOT)
            actual = (subprocess.check_output(["git", "show", "cd91c9086ef24e71ddb6a43a2076c4be5a69485e:"+path], cwd=ROOT)
                      if path == "tools/run-local-tests.ps1" else
                      subprocess.check_output(["git", "show", "de09eeee2c07036ac50471bde12a716e173e3366:"+path], cwd=ROOT)
                      if path == "scenes/world/planet_exterior.gd" else (ROOT/path).read_bytes())
            self.assertEqual(actual.replace(b"\r\n", b"\n"), baseline.replace(b"\r\n", b"\n"), path)

    def test_source_guards_state_tint_detail_and_publication_separation(self):
        generator = (ROOT / "scenes/world/planet_generator.gd").read_text()
        material = generator.split("func sample_ground_material(", 1)[1]
        for forbidden in ("state", "revision", "terrain_color", "removed_detail"):
            self.assertNotIn(forbidden, material)
        self.assertIn("if cover < 0.64:", material)
        self.assertIn("_noise(point / 768.0, 8) + _noise(point / 192.0, 9) * 0.18", material)
        color = generator.split("func sample_color(", 1)[1].split("func _overlay_weight", 1)[0]
        self.assertLess(color.index("state.terrain_color"), color.index("for overlay in _overlays"))
        self.assertIn("state.is_detail_removed(tile)", generator)
        state = (ROOT / "scenes/world/planet_world_state.gd").read_text()
        for method in ("set_terrain_color", "remove_detail"):
            self.assertIn("revision += 1", state.split("func " + method, 1)[1].split("\nfunc ", 1)[0])
        chunk = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        self.assertLess(chunk.index("generator.sample_color"), chunk.index("_colors[index] = _earth_tint(color)"))
        exterior = (ROOT / "scenes/world/planet_exterior.gd").read_text()
        self.assertIn("TerrainRenderer.ILLUSTRATED", exterior)
        self.assertIn('Callable(_generator, "sample_ground_material")', exterior)
        self.assertIn("func _ground_is_current", exterior)
        self.assertIn("func _required_ground_is_current", exterior)
        resolver = (ROOT / "scenes/world/terrain_resolver.gd").read_text()
        self.assertIn("const RULE_VERSION: int = 1", resolver)
        self.assertIn("return int(material > 0)", resolver)


if __name__ == "__main__":
    unittest.main()
