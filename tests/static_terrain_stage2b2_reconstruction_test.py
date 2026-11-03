"""Independent bounded enclosure/protection checks; no diagnostics or engine."""
from fractions import Fraction as F
import json
import math
import hashlib
import random
import subprocess
import unittest

import terrain_stage2_reference as classification
import terrain_stage2b_compatibility_reference as compatibility
import terrain_stage2b2_reconstruction_reference as reference

ROOT = classification.ROOT
ADDITIONS = {'docs/experiments/terrain_stage2b2_reconstruction.md',
             'tests/terrain_stage2b2_reconstruction_reference.py',
             'tests/static_terrain_stage2b2_reconstruction_test.py',
             'tests/fixtures/terrain_stage2b2_cases.json', 'tools/terrain-stage2b2-diagnostics.py'}
AMENDMENT = 'tests/static_terrain_stage2b_compatibility_test.py'
# Stage 3A-1 adds only isolated preparation, its tests and two approved records.
# Keep every historical inventory, mathematical and preservation assertion.
ADDITIONS |= {'scenes/world/continuous_terrain_metadata.gd',
              'tests/static_terrain_stage3a1_metadata_test.py',
              'docs/experiments/terrain_stage3_architecture_decisions.md',
              'docs/experiments/terrain_stage3a1_metadata.md'}


class ReconstructionTest(unittest.TestCase):
    def test_table_complement_and_center_distance_bound(self):
        expected = {0:(),1:('NW',),2:('NE',),3:('WE',),4:('ES',),6:('NS',),
                    7:('SW',),8:('SW',),9:('NS',),11:('ES',),12:('WE',),
                    13:('NE',),14:('NW',),15:()}
        # Independently enumerate which edges have unlike endpoint labels.
        edges = [('N',0,1),('E',1,2),('S',2,3),('W',3,0)]
        for pattern in range(16):
            for tie in (0,1):
                names = (('NE','SW') if tie==0 else ('NW','ES')) if pattern in (5,10) else expected[pattern]
                segments = reference.contour_segments(pattern,tie)
                self.assertEqual(segments,tuple((reference.MIDPOINTS[n[0]],reference.MIDPOINTS[n[1]]) for n in names))
                self.assertEqual(segments,reference.contour_segments(15-pattern,tie))
                required={name for name,a,b in edges if bool(pattern&(1<<a))!=bool(pattern&(1<<b))}
                self.assertEqual({n for pair in names for n in pair},required)
                for a,b in segments:
                    for corner in ((0,0),(64,0),(64,64),(0,64)):
                        self.assertGreaterEqual(compatibility.squared_segment_distance(corner,a,b),512)
        # Hand minimum: line x+y=32 from (32,0) to (0,32).
        self.assertEqual(compatibility.squared_segment_distance((0,0),(32,0),(0,32)),512)

    def test_independent_utf8_tie_vectors(self):
        for seed,q,digest in ((0,(0,0),'be5143de23aeb411493ed3d2f9decf49527d238aee794b7e065f74c7c74594c8'),
            (26026,(-1,0),'61237022e86c73a367a5795a133b91ac50bdf8c53380ee5c510ac0367d08714b'),
            (-42,(9,-9),'ff7eb31c1aca79d3941f944b2590879adc1de33073a60aefb05b7dda5fbaf7cb')):
            self.assertEqual(reference.tie_digest(seed,q),digest)
            self.assertEqual(reference.tie_digest(seed+classification.MODULUS,q),digest)

    def test_all_patterns_both_ties_anchors_ranges_saddles_and_complement(self):
        for pattern in range(16):
            for seed,q in ((0,(0,0)),(26026,(-1,0))):
                def material(cell):
                    x,y=(cell[i]-q[i] for i in (0,1))
                    index=((0,1),(3,2))[y%2][x%2]
                    return int(bool(pattern&(1<<index)))
                model=reference.Reconstruction(material,seed)
                inverse=reference.Reconstruction(lambda c:1-material(c),seed)
                origin=classification.center(q)
                for x,y in ((0,0),(64,0),(64,64),(0,64),(32,32),(8,16),(48,8),(56,48),(8,56)):
                    p=(origin[0]+x,origin[1]+y)
                    values=model.values(p)[:3]
                    opposite=inverse.values(p)[:3]
                    for a,b in zip(values,opposite):
                        self.assertGreaterEqual(a,0); self.assertLessEqual(a,1)
                        self.assertAlmostEqual(a+b,1,places=14)
                    if x in (0,64) and y in (0,64):
                        self.assertEqual(values,(material((q[0]+x//64,q[1]+y//64)),)*3)
                    if (x,y)==(32,32) and pattern in (5,10):
                        self.assertEqual(values[:2],(.5,.5))
                        # Both midpoint ties route around the square center.
                        self.assertIn(values[2],(0.0,1.0))

    def test_straight_widths_constants_and_neighbor_contours(self):
        model=reference.Reconstruction(lambda c:int(c[0]>=1),0)
        for x,expected in ((48,0),(64,.5),(80,1)):
            values=model.values((x,48))
            self.assertEqual(values[1],expected)
            self.assertEqual(values[2],expected)
        for bit in (0,1):
            model=reference.Reconstruction(lambda c:bit,0)
            self.assertEqual(model.values((-2048,73))[:3],(bit,bit,bit))
        # A point in a constant square can be close to a neighboring contour:
        # canonical x=32 is Green, x=-32 Earth, boundary x=0. At x=36 it is
        # already saturated; local support must still include neighboring squares.
        calls=set()
        model=reference.Reconstruction(lambda c:(calls.add(c) or int(c[0]>=0)),0)
        model.values((33,48))
        self.assertTrue(any(c[0]<0 for c in calls))

    def test_seams_gutters_order_reload_aliases_and_locality(self):
        points=[(x+d,y+d) for x,y in ((-2048,-2048),(-2048,0),(0,0),(2048,2048),
                                     (-2**20,-2**20),(2**20,2**20)) for d in (-1,0,1)]
        def material(c): return int((c[0]+2*c[1])%3!=0)
        forward=reference.Reconstruction(material,-42)
        expected={p:forward.values(p) for p in points}
        random.Random(135).shuffle(points)
        backward=reference.Reconstruction(material,-42+classification.MODULUS)
        for p in points:
            self.assertEqual(backward.values(p),expected[p])
            self.assertEqual(reference.Reconstruction(material,-42).values(p),expected[p])
        self.assertEqual(reference.source_bounds((0,0,2048,2048)),(-1,-1,32,32))
        for p in points:
            calls=set()
            model=reference.Reconstruction(lambda c:(calls.add(c) or material(c)),0)
            model.values(p)
            bounds=reference.source_bounds((*p,*p),radius=16)
            self.assertTrue(all(bounds[0]<=x<=bounds[2]+1 and bounds[1]<=y<=bounds[3]+1 for x,y in calls))
        model=reference.Reconstruction(material,0)
        for y in (-32,0,32,64,96):
            left=model.values((32-1e-7,y))
            right=model.values((32+1e-7,y))
            for a,b in zip(left,right): self.assertAlmostEqual(a,b,places=6)

    def test_manifest_bounds_and_scope_preservation(self):
        manifest=json.loads((ROOT/'tests/fixtures/terrain_stage2b2_cases.json').read_text())
        self.assertEqual(manifest['geometry_sha256'],classification.geometry_identity(classification.load_geometry()))
        self.assertEqual({c['pattern'] for c in manifest['cases'] if c['kind']=='pattern'},set(range(16)))
        self.assertEqual({c['seed'] for c in manifest['cases'] if c['kind']=='production'},set(compatibility.SEEDS))
        self.assertEqual(len({c['group'] for c in manifest['cases']}),7)
        for c in manifest['cases']:
            self.assertEqual(tuple(c['source_centers_a']),reference.source_bounds(c['rect'],c['gutter']))
            self.assertEqual(tuple(c['source_squares_b']),reference.source_bounds(c['rect'],c['gutter'],16))
        changes=subprocess.check_output(['git','diff','--name-status',reference.BASE,'cd91c9086ef24e71ddb6a43a2076c4be5a69485e','--'],cwd=ROOT,text=True)
        inventory={p:s for s,p in (line.split('\t',1) for line in changes.splitlines())}
        receipt=json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
        self.assertEqual(inventory,{**dict.fromkeys(ADDITIONS,'A'),AMENDMENT:'M'})
        for path,entry in receipt['protected_sidecars'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),entry['sha256'])

    def test_exact_historical_amendment(self):
        baseline=subprocess.check_output(['git','show',reference.BASE+':'+AMENDMENT],cwd=ROOT,text=True)
        old='        changes = subprocess.check_output(["git", "diff", "--name-status", oracle.BASE, "--"], cwd=ROOT, text=True)\n'
        new='        # Historical PR #135 inventory; current-tree scope belongs to Stage 2B-2.\n        stage2b_merge = "1f4ac408c31b99be4ab7158960dab06adec93871"\n        changes = subprocess.check_output(["git", "diff", "--name-status", oracle.BASE, stage2b_merge, "--"], cwd=ROOT, text=True)\n'
        self.assertEqual(baseline.count(old),1)
        expected=baseline.replace(old,new)
        for line in ('        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())\n',
                     '        self.assertEqual(untracked - ADDITIONS, protected)\n',
                     '        inventory.update({path: "A" for path in untracked & ADDITIONS})\n'):
            self.assertEqual(expected.count(line),1)
            expected=expected.replace(line,'')
        historical=subprocess.check_output(['git','show','cd91c9086ef24e71ddb6a43a2076c4be5a69485e:'+AMENDMENT],cwd=ROOT,text=True)
        self.assertEqual(historical,expected)


class ProtectionProofTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = classification.load_geometry()

    def test_runtime_and_geometry_assumptions(self):
        self.assertTrue(reference.runtime_contract())
        self.assertTrue(reference.geometry_contract(self.geometry))
        for primitive in compatibility.primitives(self.geometry):
            for a, b in zip(primitive.points, primitive.points[1:] + primitive.points[:1]):
                if a[1] != b[1]:
                    self.assertGreaterEqual(abs(a[1] - b[1]), 1)

    def test_uniform_error_budget_rational_inequalities(self):
        # sqrt(2)<3/2: upper bound, not a sampled floating norm comparison.
        segment_norm = F(3, 2) * (F(1, 2**40) + F(1, 2**32)) + F(1, 2**31)
        crossing = F(1, 2**28)
        self.assertLess(segment_norm, F(1, 10**8))
        self.assertLess(crossing, F(1, 10**8))
        self.assertLess(F(1, 10**8), reference.EPSILON)
        self.assertEqual(1.0 - 1.0 * 1.0 * (3.0 - 2.0 * 1.0), 0.0)
        for reach in (48.0, 160.0, 256.0):
            for distance in (reach, math.nextafter(reach, math.inf), 2.0**21):
                self.assertGreaterEqual(distance / reach, 1.0)

    def test_squared_surrogate_independent_algebra(self):
        for radius in (F(48), F(160), F(256)):
            radius += reference.EPSILON
            for d in (F(0), F(1, 10**8), F(1, 2), F(138, 100), F(8), F(16), F(32)):
                value = min(F(16), d * (2 * radius + d) / (2 * radius + 16))
                self.assertLessEqual(value, d)
                self.assertGreaterEqual(value, min(F(16), F(6, 7) * d))
                self.assertGreaterEqual(value, min(F(16), d / 2))

    def test_new_clearance_and_exact_anchor_preservation(self):
        lo, _ = compatibility.sqrt_bounds(F(861184, 13))
        for seed in compatibility.SEEDS:
            protection = reference.Protection(seed, self.geometry)
            for cell in ((9, -9), (16, 1), (-18, -8), (-16, 8), (-18, -6), (0, 0),
                         (40, 40), (-16385, 16384), (16384, -16385)):
                material, binary, lower, scale = protection.center_record(cell)
                self.assertEqual(material, classification.classify(cell, seed, self.geometry))
                if binary:
                    self.assertGreater(lower, 0)
                    self.assertEqual(protection.value(classification.center(cell)), 1.0)
                    self.assertGreater(scale, 0)
            if seed in (26026, -42):
                self.assertEqual(protection.center_record((9, -9))[2], lo - 256 - reference.EPSILON)

    def test_strict_geometry_endpoints_overlaps_and_cutoff(self):
        protection = reference.Protection(26026, self.geometry)
        # NorthRidge's exposed horizontal outer boundary and nearby points.
        for p in ((0, -1280), (0, -1280 + F(1, 10**8)), (0, -1280 - F(1, 10**8)),
                  (32, 32), (-384, -192), (-832, -1120)):
            self.assertEqual(protection.value(p), 0.0)
        self.assertEqual(protection.cutoff, (-1296-reference.EPSILON, -1296-reference.EPSILON,
                                            1296+reference.EPSILON, 1296+reference.EPSILON))
        for p in ((-2048, 0), (2048, 2048), (2**20, -2**20), (0, -1296-reference.EPSILON)):
            self.assertEqual(protection.value(p), 1.0)
        for p in ((math.inf, 0), (math.nan, 0), (2**21+1, 0)):
            with self.assertRaises(ValueError):
                protection.value(p)

    def test_original_fourteen_vectors(self):
        vectors = json.loads((classification.ROOT / 'tests/fixtures/terrain_stage2_classification_vectors.json').read_text())
        self.assertEqual(len(vectors['records']), 14)
        for record in vectors['records']:
            self.assertEqual(classification.classify(record['cell'], record['seed'], self.geometry), record['material'])

    def test_every_audited_green_anchor_and_separate_outcomes(self):
        for seed in compatibility.SEEDS:
            protection=reference.Protection(seed,self.geometry)
            for x in range(-21,21):
                for y in range(-21,21):
                    record=protection.center_record((x,y))
                    if record[1]:
                        self.assertGreater(record[2],0)
                        self.assertEqual(protection.value(classification.center((x,y))),1.0)
        self.assertEqual(len({compatibility.CONFLICT,compatibility.INSUFFICIENT,
                              compatibility.UNRESOLVED,compatibility.COMPATIBLE}),4)


if __name__ == '__main__':
    unittest.main()
