"""Static GDScript contract + independent offline layout/math; NOT engine parity.

No execution/translation of GDScript, asset generation, or runtime certification.
"""
import hashlib
import json
import math
from pathlib import Path
import subprocess
import unittest

import terrain_stage2_reference as reference
import terrain_stage2b2_reconstruction_reference as reconstruction

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'scenes/world/continuous_terrain_metadata.gd').read_text()
BASE = 'b4abb3ac8d78d5833b232061642297434ec5abc6'


def cells(chunk):
    """Independent specification: flatten the absolute inclusive rectangle."""
    return [(x, y) for y in range(32*chunk[1]-1, 32*chunk[1]+33)
            for x in range(32*chunk[0]-1, 32*chunk[0]+33)]


class MetadataContractTest(unittest.TestCase):
    def test_authoritative_call_and_unchanged_original_sources(self):
        vectors = json.loads((ROOT/'tests/fixtures/terrain_stage2_classification_vectors.json').read_text())
        for path, digest in vectors['source_sha256_lf'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes().replace(b'\r\n', b'\n')).hexdigest(), digest)
        self.assertIn('Generator = preload("res://scenes/world/planet_generator.gd")', SOURCE)
        self.assertIn('Generator.new(seed, copied_overlays, protected.duplicate(), anchors.duplicate())', SOURCE)
        self.assertEqual(SOURCE.count('generator.sample_ground_material(cell)'), 1)
        for forbidden in ('posmod(', '_noise(', 'Geometry2D.', 'Shader', 'Thread', 'sample_color('):
            self.assertNotIn(forbidden, SOURCE)
        self.assertIn('"seed": seed', SOURCE)
        self.assertIn('"runtime_certified": false', SOURCE)

    def test_layout_source_contract(self):
        for fragment in ('const HALO_WIDTH := 34', 'materials.resize(HALO_WIDTH * HALO_WIDTH)',
                         'chunk * WorldCoordinates.CHUNK_TILES', 'for y in range(-1, 33):',
                         'for x in range(-1, 33):', 'origin + Vector2i(x, y)',
                         'materials[(y + 1) * HALO_WIDTH + x + 1] = material',
                         'material < 0 or material > 4', '"geometry":', 'overlay.duplicate(true)'):
            self.assertIn(fragment, SOURCE)

    def test_rejection_source_contract_not_executed_branches(self):
        for fragment in ('typeof(seed) != TYPE_INT', 'typeof(chunk) != TYPE_VECTOR2I',
                         'chunk.x < MIN_CHUNK or chunk.x > MAX_CHUNK',
                         'chunk.y < MIN_CHUNK or chunk.y > MAX_CHUNK',
                         'const MIN_CHUNK := -16', 'const MAX_CHUNK := 15',
                         'TERRAIN_SIZE != 64', 'CHUNK_TILES != 32',
                         '_valid_points(protected, 3)', '_valid_points(anchors, 0)',
                         'typeof(overlays) != TYPE_ARRAY', 'typeof(overlay) != TYPE_DICTIONARY',
                         '_valid_points(overlay.get("polygon"), 3)',
                         'typeof(feather) != TYPE_FLOAT and typeof(feather) != TYPE_INT',
                         'not is_finite(float(feather)) or float(feather) <= 0.0',
                         'typeof(points) != TYPE_PACKED_VECTOR2_ARRAY',
                         'points.size() < minimum', 'not point.is_finite()'):
            self.assertIn(fragment, SOURCE)
        errors = [line for line in SOURCE.splitlines() if '"error":' in line]
        self.assertEqual(len(errors), 11)
        self.assertTrue(all('return {"ok": false,' in line for line in errors))
        self.assertLess(SOURCE.index('"unsupported_chunk"'), SOURCE.index('Generator.new'))

    def test_all_supported_chunk_layouts_and_boundary_support(self):
        for cy in range(-16, 16):
            for cx in range(-16, 16):
                chunk = (cx, cy)
                layout = cells(chunk)
                self.assertEqual(len(set(layout)), 1156)
                self.assertEqual(layout[0], (cx*32-1, cy*32-1))
                self.assertEqual(layout[-1], (cx*32+32, cy*32+32))
                bounds = reconstruction.source_bounds((cx*2048, cy*2048, (cx+1)*2048, (cy+1)*2048))
                self.assertEqual((*layout[0], *layout[-1]), bounds)
        self.assertEqual(reference.center(cells((-16, -16))[0]), (-32800, -32800))
        self.assertEqual(reference.center(cells((15, 15))[-1]), (32800, 32800))

    def test_neighbor_overlap_is_absolute_identity(self):
        for chunk in ((-16,-16), (-1,-1), (0,0), (14,14)):
            left = set(cells(chunk))
            for delta, count in (((1,0),68), ((0,1),68), ((1,1),4)):
                right = set(cells(tuple(a+b for a,b in zip(chunk, delta))))
                self.assertEqual(len(left & right), count)
        # Reuse original offline goldens as payloads; never relabel as engine output.
        vectors = json.loads((ROOT/'tests/fixtures/terrain_stage2_classification_vectors.json').read_text())
        geometry = reference.load_geometry()
        for v in vectors['records']:
            cell = tuple(v['cell'])
            chunk, local = reference.chunk_and_local(cell)
            self.assertEqual(cells(chunk)[(local[1]+1)*34+local[0]+1], cell)
            self.assertEqual(reference.classify(cell, v['seed'], geometry), v['material'])
        self.assertEqual({v['material'] for v in vectors['records']}, set(range(5)))

    def test_signed_seed_model_and_order_identity(self):
        geometry = reference.load_geometry()
        sample = [(-513,-513), (-512,511), (512,512), (-1,0), (44,40)]
        for seed in (-2**63, -42, -1, 0, 26026, 2**63-1):
            expected = {c: reference.classify(c, seed, geometry) for c in sample}
            for c in reversed(sample):
                self.assertEqual(reference.classify(c, seed, geometry), expected[c])
                self.assertEqual(reference.classify(c, seed % reference.MODULUS, geometry), expected[c])

    def test_floor_ownership_and_unsupported_owner_examples(self):
        for boundary in (-32768, -2048, 0, 2048, 32768):
            for offset in (-0.25, 0, 0.25):
                p = boundary + offset
                cell = reference.world_to_cell((p,p))
                chunk, local = reference.chunk_and_local(cell)
                self.assertEqual(chunk, (math.floor(p/2048),)*2)
                self.assertTrue(all(0 <= n < 32 for n in local))
        for p, owned in ((-32768.25,False), (-32768,True), (32767.75,True), (32768,False)):
            self.assertEqual(-16 <= math.floor(p/2048) <= 15, owned)

    def test_guard_amendment_exact_scope(self):
        path = 'tests/static_terrain_stage2b2_reconstruction_test.py'
        before = subprocess.check_output(['git','show',BASE+':'+path], cwd=ROOT, text=True)
        # Validate the immutable merged 3A-1 amendment; 3A-2 checks its own exact delta.
        after = subprocess.check_output(['git', 'show', 'cd91c9086ef24e71ddb6a43a2076c4be5a69485e:'+path], cwd=ROOT, text=True)
        added = after[after.index('# Stage 3A-1'):after.index('\n\n\nclass ReconstructionTest')]
        self.assertEqual(after.replace(added+'\n',''), before)
        self.assertEqual(added.count("'scenes/"), 1)
        self.assertEqual(added.count("'tests/"), 1)
        self.assertEqual(added.count("'docs/"), 2)


if __name__ == '__main__':
    unittest.main()
