"""Stage 2B-1 offline geometry proofs, exhaustive audit and preservation guards."""
from dataclasses import replace
from fractions import Fraction as F
import hashlib
import json
import random
import subprocess
import unittest

import terrain_stage2b_compatibility_reference as oracle
import terrain_stage2_reference as classification
from static_ground_rejection_test import authored_geometry, material_at, rejection_bounds
from static_terrain_stage2_coverage_test import rational_cover, rational_hash


ROOT = classification.ROOT
ADDITIONS = {
    "docs/experiments/terrain_stage2b_compatibility.md",
    "tests/terrain_stage2b_compatibility_reference.py",
    "tests/static_terrain_stage2b_compatibility_test.py",
}
AMENDMENT = "tests/static_terrain_stage2_coverage_test.py"
SQUARE = ((0, 0), (10, 0), (10, 10), (0, 10))


class CompatibilityTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = classification.load_geometry()
        cls.reports = {a.seed: a for a in oracle.audit(cls.geometry)}

    def test_exact_segment_projection_endpoints_and_degeneracy(self):
        for point, a, b, expected in (
            ((5, 3), (0, 0), (10, 0), 9),
            ((-3, -4), (0, 0), (10, 0), 25),
            ((13, 4), (0, 0), (10, 0), 25),
            ((-3, -4), (0, 0), (0, 0), 25),
            ((1, 0), (0, 0), (1, 1), F(1, 2)),
        ):
            self.assertEqual(oracle.squared_segment_distance(point, a, b), expected)
            self.assertEqual(oracle.squared_segment_distance(point, b, a), expected)

    def test_filled_polygon_interior_vertices_concavity_and_signed_coordinates(self):
        for point, expected in (((5, 5), 0), ((10, 5), 0), ((0, 0), 0), ((-3, -4), 25)):
            self.assertEqual(oracle.squared_polygon_distance(point, SQUARE), expected)
            self.assertEqual(oracle.squared_polygon_distance(point, SQUARE[::-1]), expected)
        concave = ((-10, -10), (10, -10), (10, 0), (0, 0), (0, 10), (-10, 10))
        self.assertEqual(oracle.squared_polygon_distance((3, 4), concave), 9)
        self.assertEqual(oracle.squared_polygon_distance((-3, 4), concave), 0)

    def test_integer_square_root_enclosures_are_proofs(self):
        for squared in (0, 25, F(1, 2), F(861184, 13), F(2803712, 41), F(1, 10**30)):
            lo, hi = oracle.sqrt_bounds(squared)
            self.assertLessEqual(lo * lo, squared)
            self.assertGreaterEqual(hi * hi, squared)
            self.assertLessEqual(hi - lo, F(1, oracle.SCALE))
        self.assertEqual(oracle.sqrt_bounds(25), (5, 5))

    def test_strict_gameplay_rectangle_and_conditional_circle_conflict(self):
        geometry = classification.Geometry(SQUARE, (), ())
        for point, relation, predicate, bounds in (
            ((57, 5), "inside", True, (0, 0)),
            ((58, 5), "boundary", False, (0, 0)),
            ((59, 5), "outside", False, (1, 1)),
        ):
            distance = oracle.clearance(point, geometry)
            self.assertEqual((distance.relation, distance.model_predicate), (relation, predicate))
            self.assertEqual((distance.lower, distance.upper), bounds)
        # Hypothetical independent Green ID. This is not a production failure.
        circle = classification.Geometry((), (), (("synthetic", (192, 32)),))
        distance = oracle.clearance(classification.center((0, 0)), circle)
        self.assertEqual((distance.relation, distance.model_predicate), ("boundary", False))
        self.assertEqual(oracle.outcome(3, distance), oracle.CONFLICT)
        self.assertEqual(oracle.outcome(0, distance), oracle.EARTH)
        self.assertEqual(oracle.clearance((33, 32), circle).relation, "inside")
        self.assertEqual(oracle.clearance((31, 32), circle).lower, 1)

    def test_feather_computed_positive_and_endpoint_uncertainty(self):
        geometry = classification.Geometry((), (("square", SQUARE, 256),), ())
        for point, reason in (((57, 5), "authored:square"), ((58, 5), "skirt:square"),
                              ((265, 5), "skirt:square"), ((266, 5), None)):
            self.assertEqual(oracle.clearance(point, geometry).model_reason, reason)
        boundary = oracle.clearance((266, 5), geometry)
        self.assertEqual(boundary.relation, "boundary")
        self.assertEqual(oracle.outcome(1, boundary), oracle.UNRESOLVED)
        # Smoothstep cancellation can produce zero strictly INSIDE ideal reach.
        point = (266 - 1e-8, 5)
        self.assertEqual(classification.overlay_weight(point, SQUARE, 256), 0)
        distance = oracle.clearance(point, geometry)
        self.assertEqual(distance.relation, "inside")
        self.assertTrue(any("disagrees" in s for s in distance.uncertainty))
        for material in (0, 1, 4):
            self.assertEqual(oracle.outcome(material, distance), oracle.UNRESOLVED)

    def test_overlap_resolves_only_covered_endpoints(self):
        geometry = classification.Geometry((), (("square", SQUARE, 256),), (("cover", (266, 5)),))
        distance = oracle.clearance((266, 5), geometry)
        self.assertEqual(distance.relation, "inside")
        self.assertEqual(distance.uncertainty, ())
        self.assertTrue(distance.covered_endpoints)
        self.assertEqual(oracle.outcome(0, distance), oracle.EARTH)
        self.assertEqual(oracle.outcome(4, distance), oracle.CONFLICT)
        isolated = replace(geometry, anchors=())
        self.assertEqual(oracle.outcome(0, oracle.clearance((266, 5), isolated)), oracle.UNRESOLVED)

    def test_margin_uses_both_bounds_and_never_changes_id(self):
        circle = classification.Geometry((), (), (("circle", (192, 32)),))
        distance = oracle.clearance((31, 32), circle)  # exact clearance 1
        self.assertEqual(oracle.outcome(2, distance, F(1, 2)), oracle.COMPATIBLE)
        self.assertEqual(oracle.outcome(2, distance, 2), oracle.INSUFFICIENT)
        self.assertEqual(oracle.outcome(2, distance, 1), oracle.UNRESOLVED)
        near = oracle.clearance((32 - 1e-8, 32), circle)
        self.assertEqual(oracle.outcome(2, near), oracle.UNRESOLVED)
        for bad in (-1,):
            with self.assertRaises(ValueError):
                oracle.outcome(2, distance, bad)
        with self.assertRaises(ValueError):
            oracle.outcome(5, distance)
        for seed in (26026, -42):
            a = oracle.anchor((9, -9), seed, self.geometry, 2)
            self.assertEqual(a.outcome, oracle.INSUFFICIENT)
            self.assertEqual(a.original_id, classification.classify((9, -9), seed, self.geometry))

    def test_source_derived_envelope_and_all_outside_center_bound(self):
        bounds, cells, outside_lower = oracle.envelope(self.geometry)
        self.assertEqual(bounds, (-1280, -1280, 1280, 1280))
        self.assertEqual(cells, (-21, -21, 20, 20))
        self.assertEqual(outside_lower, 96 - oracle.NUMERIC_BAND)
        self.assertEqual(rejection_bounds(*authored_geometry()), (-1281, -1281, 1281, 1281))
        # Any outside index has x or y <= -22 or >= 21, hence that axis's
        # center <= -1376 or >= 1376. Axis separation from AABB is >= 96.
        self.assertEqual(classification.center((-22, 21)), (-1376, 1376))
        self.assertEqual(classification.world_to_cell((-0.001, -64.001)), (-1, -2))
        self.assertEqual(classification.chunk_and_local((-1, -33)), ((-1, -2), (31, 31)))
        # Model scope is enforced rather than silently claiming distant parity.
        self.assertTrue(oracle.clearance((100000, 0), self.geometry).uncertainty)

    def test_exhaustive_geometry_including_all_noise_independent_hazards(self):
        records = self.reports[26026].anchors
        self.assertEqual(len(records), 42**2)
        self.assertEqual(sum(a.clearance.relation == "inside" for a in records), 1441)
        self.assertEqual(sum(a.clearance.relation == "outside" for a in records), 323)
        self.assertFalse(any(a.clearance.relation == "boundary" for a in records))
        self.assertFalse(any(a.clearance.uncertainty for a in records))
        internal = {a.cell for a in records if a.clearance.covered_endpoints}
        self.assertEqual(internal, {(-14, -18), (-10, -16), (-6, -13), (-2, -10)})
        # Hand-derived perpendicular distance to Clearing's (192,-512)-(768,-128).
        closest = min((a for a in records if a.clearance.relation == "outside"),
                      key=lambda a: a.clearance.lower)
        self.assertEqual(closest.cell, (9, -9))
        lo, hi = oracle.sqrt_bounds(F(861184, 13))
        self.assertEqual((closest.clearance.lower, closest.clearance.upper), (lo - 256, hi - 256))
        self.assertGreater(closest.clearance.lower - oracle.NUMERIC_BAND, F(138, 100))
        for report in self.reports.values():
            self.assertEqual(report.outcome, oracle.COMPATIBLE)
            for a in report.anchors:
                if a.clearance.relation == "inside":
                    self.assertEqual(a.original_id, 0)

    def test_exhaustive_original_ids_independent_model_and_rational_noise(self):
        original = authored_geometry()
        for seed, report in self.reports.items():
            for a in report.anchors:
                self.assertEqual(a.original_id, material_at(a.world_center, seed, original), (seed, a.cell))
                self.assertEqual(a.binary_anchor, int(a.original_id > 0))
                if not a.clearance.model_predicate:
                    cover = rational_cover(a.cell, seed)
                    self.assertGreater(abs(cover - F(16, 25)), F(1, 10**10))
                    expected = 0 if cover < F(16, 25) else 1 + 4 * rational_hash(*a.cell, seed, 10) // classification.MODULUS
                    self.assertEqual(a.original_id, expected, (seed, a.cell))

    def test_per_seed_findings_and_previously_unclassified_probe(self):
        # Counts are audit regression observations, NOT new classification goldens.
        expected = {26026: (188, (9, -9), 3, 1), 0: (215, (-18, -8), 4, 0),
                    -42: (142, (9, -9), 4, 4), -1: (114, (-16, 8), 3, 0),
                    2147483647: (215, (-18, -8), 4, 0),
                    2147483648: (42, (-18, -6), 1, 0),
                    -2147483648: (114, (-16, 8), 3, 0)}
        for seed, (count, cell, material, probe_id) in expected.items():
            green = [a for a in self.reports[seed].anchors if a.binary_anchor]
            self.assertEqual(len(green), count)
            minimum = min(green, key=lambda a: a.clearance.lower)
            self.assertEqual((minimum.cell, minimum.original_id), (cell, material))
            probe = next(a for a in self.reports[seed].anchors if a.cell == (16, 1))
            self.assertEqual((probe.world_center, probe.original_id), ((1056, 96), probe_id))
            # Hand cross product: (64*224 - 576*288)^2 / (64^2 + 576^2).
            lo, hi = oracle.sqrt_bounds(F(2803712, 41))
            self.assertEqual((probe.clearance.lower, probe.clearance.upper), (lo - 256, hi - 256))

    def test_frozen_stage2a_vectors_are_reused_without_rebaselining(self):
        vectors = json.loads((ROOT / "tests/fixtures/terrain_stage2_classification_vectors.json").read_text())
        self.assertEqual(len(vectors["records"]), 14)
        self.assertEqual(vectors["geometry_sha256"], classification.geometry_identity(self.geometry))
        for v in vectors["records"]:
            self.assertEqual(classification.classify(v["cell"], v["seed"], self.geometry), v["material"])

    def test_seed_aliases_and_full_query_order_reload_determinism(self):
        base = self.reports[26026]
        cells = [a.cell for a in base.anchors]
        shuffled = cells[:]
        random.Random(134).shuffle(shuffled)
        for order in (cells[::-1], shuffled):
            reloaded = oracle.audit(classification.load_geometry(), (26026,), query_order=order)[0]
            self.assertEqual(base, reloaded)
        for a, b in ((0, 2147483647), (-1, -2147483648)):
            self.assertEqual(tuple(replace(r, seed=b) for r in self.reports[a].anchors), self.reports[b].anchors)
        for cell in ((9, -9), (16, 1), (-21, 20), (0, 0)):
            for seed in (0, -42, 26026):
                a = oracle.anchor(cell, seed, self.geometry)
                for alias in (seed + classification.MODULUS, seed - classification.MODULUS):
                    self.assertEqual(replace(a, seed=alias), oracle.anchor(cell, alias, self.geometry))
        with self.assertRaises(ValueError):
            oracle.audit(self.geometry, (0,), query_order=cells[:-1])
        with self.assertRaises(ValueError):
            oracle.audit(self.geometry, (0,), query_order=cells[:-1] + cells[:1])

    def test_audit_margin_and_unresolved_aggregation(self):
        # Small independent geometry keeps these exhaustive decision checks small.
        geometry = classification.Geometry((), (), (("circle", (192, 32)),))
        self.assertEqual(oracle.audit(geometry, (0,))[0].outcome, oracle.CONFLICT)
        # Shift the separate margin fixture off canonical circle equalities.
        geometry = classification.Geometry((), (), (("circle", (192, 33)),))
        for margin, expected in ((0, oracle.COMPATIBLE), (100, oracle.INSUFFICIENT)):
            report = oracle.audit(geometry, (0,), margin=margin)[0]
            self.assertEqual(report.outcome, expected)
        feather = classification.Geometry((), (("square", ((0, 0), (32, 0), (32, 32), (0, 32)), 256),), ())
        self.assertEqual(oracle.audit(feather, (0,))[0].outcome, oracle.UNRESOLVED)

    def test_stage2b_exact_scope_and_unchanged_sources(self):
        # Historical PR #135 inventory; current-tree scope belongs to Stage 2B-2.
        stage2b_merge = "1f4ac408c31b99be4ab7158960dab06adec93871"
        changes = subprocess.check_output(["git", "diff", "--name-status", oracle.BASE, stage2b_merge, "--"], cwd=ROOT, text=True)
        inventory = dict((path, status) for status, path in (line.split("\t", 1) for line in changes.splitlines()))
        receipt = json.loads((ROOT / "artifacts/logs/terrain-preservation-2026-11-03.json").read_text())
        protected = set(receipt["protected_sidecars"])
        self.assertEqual(len(protected), 15)
        self.assertEqual(inventory, {**dict.fromkeys(ADDITIONS, "A"), AMENDMENT: "M"})
        for path, entry in receipt["protected_sidecars"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), entry["sha256"])
        vectors = json.loads((ROOT / "tests/fixtures/terrain_stage2_classification_vectors.json").read_text())
        for path, expected in vectors["source_sha256_lf"].items():
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes().replace(b"\r\n", b"\n")).hexdigest(), expected)
        # Every previously tracked file besides the authorized amendment is
        # protected by the exact inventory, including frozen goldens and C1.

    def test_stage2a_amendment_is_only_historical_inventory_fix(self):
        old = '''        # Compare against fixed baseline, not a moving main. All existing tracked
        # files (assets, runner, tests, gameplay, scenes, receipts) must be intact.
        changes = subprocess.check_output(["git", "diff", "--name-status", reference.BASE, "--"], cwd=ROOT, text=True)
'''
        new = '''        # Historical Stage 2A inventory is immutable, not a ban on later additions.
        # Keep the working-source preservation checks below against the same base.
        stage2a_merge = "1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744"
        changes = subprocess.check_output(
            ["git", "diff", "--name-status", reference.BASE, stage2a_merge, "--"], cwd=ROOT, text=True)
        self.assertEqual({line.split("\\t", 1)[1] for line in changes.splitlines()}, NEW_FILES)
'''
        baseline = subprocess.check_output(["git", "show", f"{oracle.BASE}:{AMENDMENT}"], cwd=ROOT, text=True)
        current = (ROOT / AMENDMENT).read_text()
        self.assertEqual(current.count(new), 1)
        self.assertEqual(current.replace(new, old), baseline)


if __name__ == "__main__":
    unittest.main()
