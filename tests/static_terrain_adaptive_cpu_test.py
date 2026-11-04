"""Offline candidate checks only; no Godot/GPU numerical certification."""
from fractions import Fraction as F
import json
import math
import hashlib
import subprocess
import unittest

import terrain_adaptive_cpu_reference as candidate
import terrain_stage2_reference as ids
import terrain_stage2b_compatibility_reference as geometry


class AdaptiveTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.authored = ids.load_geometry()
        cls.cover = candidate.Cover(cls.authored)

    def test_deterministic_representation(self):
        other = candidate.Cover(self.authored)
        self.assertEqual(self.cover.payload(), other.payload())
        self.assertEqual(self.cover.leaves, other.leaves)

    def test_exact_change_scope_and_preservation(self):
        root = ids.ROOT
        added = {'tests/terrain_adaptive_cpu_reference.py',
                 'tests/static_terrain_adaptive_cpu_test.py',
                 'tools/terrain-adaptive-cpu-diagnostics.py',
                 'docs/experiments/terrain_adaptive_cpu_prototype.md'}
        modified = {'tests/static_metadata_smoke_test.py',
                    'docs/experiments/terrain_stage3_architecture_decisions.md'}
        delta = subprocess.check_output(['git','diff','--name-status',
                  'ee937c98aa5e5bcb087f99c5b0eb8c8960ecf4f0','--'],cwd=root,text=True)
        inventory = {p:s for s,p in (line.split('\t',1) for line in delta.splitlines())}
        untracked = set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=root,text=True).splitlines())
        receipt = json.loads((root/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
        self.assertEqual(untracked-added,set(receipt['protected_sidecars']))
        inventory.update({p:'A' for p in untracked & added})
        self.assertEqual(inventory,{**dict.fromkeys(added,'A'),**dict.fromkeys(modified,'M')})
        for p,e in receipt['protected_sidecars'].items():
            self.assertEqual(hashlib.sha256((root/p).read_bytes()).hexdigest(),e['sha256'])

    def test_all_unexcluded_local_centers_have_positive_box_clearance(self):
        # Exclusion is seed-independent. Exhaust this finite center envelope;
        # outside it the primitive AABBs and the root partition prove separation.
        for y in range(-33,33):
            for x in range(-33,33):
                p = ids.center((x,y))
                if ids.exclusion_reason(p,self.authored) is None:
                    self.assertGreater(self.cover.distance_surrogate(p),0)

    def test_partition_and_independent_outside_certificate(self):
        area = sum((b[2]-b[0])*(b[3]-b[1]) for b, _ in self.cover.leaves)
        self.assertEqual(area, 4096**2)
        # Independently check every OUT certificate without the AABB fast path.
        for box, state in self.cover.leaves:
            if state != 'outside':
                self.assertIn(box, self.cover.boxes)
                continue
            p = ((box[0]+box[2])/2, (box[1]+box[3])/2)
            r = box[2]-box[0]
            for primitive in self.cover.primitives:
                self.assertGreater(geometry.primitive_distance_squared(p, primitive),
                                   (primitive.radius+candidate.GUARD+r)**2)

    def test_protected_vertices_edges_disks_feathers(self):
        points = set()
        for primitive in self.cover.primitives:
            for a, b in zip(primitive.points, primitive.points[1:]+primitive.points[:1]):
                for t in (F(0), F(1, 2), F(1)):
                    p = tuple(a[i]+t*(b[i]-a[i]) for i in (0, 1))
                    points.add(p)
                    for direction in ((1,0),(-1,0),(0,1),(0,-1)):
                        for delta in (-candidate.GUARD, 0, candidate.GUARD):
                            points.add(tuple(F(p[i])+direction[i]*(primitive.radius+delta) for i in (0,1)))
        field = candidate.Field(self.cover, 26026)
        protected = 0
        for p in points:
            exact = any(geometry.primitive_distance_squared(p, primitive) <=
                        (primitive.radius+candidate.GUARD)**2 for primitive in self.cover.primitives)
            if exact:
                protected += 1
                self.assertEqual(field.values(p)[1], 0)
                self.assertEqual(self.cover.distance_surrogate(p), 0)
        self.assertGreater(protected, 100)

    def test_original_ids_and_green_endpoints_seven_seeds(self):
        for seed in geometry.SEEDS:
            field = candidate.Field(self.cover, seed)
            for y in range(-21, 21):
                for x in range(-21, 21):
                    cell = (x, y)
                    material, scale = field.center_record(cell)
                    self.assertEqual(material, ids.classify(cell, seed, self.authored))
                    if material:
                        self.assertGreater(scale, 0)
                        self.assertEqual(field.values(ids.center(cell)), (1, 1))
        field = candidate.Field(self.cover, 26026)
        self.assertGreater(field.center_record((9, -9))[0], 0)
        self.assertEqual(field.values((608, -544)), (1, 1))

    def test_negative_seams_boundaries_and_halos(self):
        a, b = (candidate.Field(self.cover, -42) for _ in range(2))
        for p in ((-2048, -32), (0, 0), (2048, -2048), (-32768, -32768),
                  (F(32768)-F(1, 8), 0), (-64, F(-1, 8)), (608, -544)):
            self.assertEqual(a.values(p), b.values(p))
        for p in ((-32800, -32800), (32800, 32800)):
            cell = tuple((v-32)//64 for v in p)
            self.assertEqual(a.center_record(cell), b.center_record(cell))
        # Indexed distance agrees with an independent full list query at seams.
        for p in ((0,0), (608,-544), (600,-544), (-1280,-1280), (-64,-64), (1280,32)):
            expected = min(F(16), min(candidate.box_squared(p, box)/32 for box in self.cover.boxes))
            self.assertEqual(self.cover.distance_surrogate(p), expected)

    def test_unknown_inputs_fail(self):
        for seed in (True, 1.0, 2**63, -2**63-1):
            with self.assertRaises(ValueError):
                candidate.Field(self.cover, seed)
        field = candidate.Field(self.cover, 0)
        for p in ((math.inf, 0), (math.nan, 0), (32768, 0), (-32769, 0), (True, 0), (0,)):
            with self.assertRaises(ValueError):
                field.values(p)
        with self.assertRaises(ValueError):
            field.center_record((0.5, 0))
        with self.assertRaises(ValueError):
            candidate.Cover(ids.Geometry((), (), ()))

    def test_serialization_is_exact(self):
        payload = json.loads(json.dumps(self.cover.payload()))
        self.assertEqual([tuple(map(F, row)) for row in payload], self.cover.boxes)


if __name__ == '__main__':
    unittest.main()
