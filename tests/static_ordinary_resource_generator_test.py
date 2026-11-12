"""Static wiring/preservation and independent policy geometry checks only.

These tests do NOT execute, parse or translate the GDScript generator. Hash
vectors and geometry proofs describe policy obligations; runtime assertions
live in ordinary_resource_generator_test.gd and are not authorized to run.
"""
from itertools import product
from pathlib import Path
import hashlib
import math
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "70a031dc3c9a628d1209440a614d923034cd150f"
PATH = "scenes/world/ordinary_resource_generator.gd"
SOURCE = (ROOT / PATH).read_text(encoding="utf-8")
ASSERTIONS = (ROOT / "tests/ordinary_resource_generator_test.gd").read_text(encoding="utf-8")


def number(name):
    return int(re.search(rf"const {name}: int = (\d+)\b", SOURCE)[1])


def sample(seed, owner, slot, channel):
    key = f"ordinary-v2-1:{seed}:{owner[0]}:{owner[1]}:{slot}:{channel}"
    return int(hashlib.sha256(key.encode("ascii")).hexdigest()[:7], 16)


class OrdinaryResourceStaticTests(unittest.TestCase):
    def test_locked_units_and_signed_boundaries(self):
        self.assertEqual(number("REGION_SIZE"), 1536)
        self.assertEqual(number("REGION_CONSTRUCTION_CELLS") * number("CELL"), 1536)
        self.assertEqual(1536 // 64, 24)
        for point, expected in [((0, 0), (0, 0)), ((-1, -1536), (-1, -1)),
                                ((1536, 3072), (1, 2)), ((-1537, 1535), (-2, 0))]:
            self.assertEqual(tuple(math.floor(v / 1536) for v in point), expected)
        self.assertIn("floori(point.x / REGION_SIZE)", SOURCE)
        self.assertIn("floori(point.y / REGION_SIZE)", SOURCE)

    def test_all_template_offsets_fit_declared_reach_and_spacing(self):
        # Exhaustive unrotated template space; rotations/reflections preserve
        # Euclidean distances and swap absolute coordinate components.
        for px, py, tx, ty in product(range(10, 15), range(-2, 3), range(2, 7), range(12, 15)):
            points = [(0, 0), (px, py), (tx, ty)]
            for index, a in enumerate(points):
                self.assertLessEqual(max(abs(v) for v in a) * 32, number("MAX_OFFSET"))
                for b in points[:index]:
                    dx, dy = abs(a[0] - b[0]) * 32, abs(a[1] - b[1]) * 32
                    self.assertGreaterEqual(math.hypot(dx, dy), number("WITHIN_MIN"))
                    self.assertLessEqual(math.hypot(dx, dy), number("WITHIN_MAX"))
                    # 128 anchor + 2*64 margin + 32 terrain gap, inclusive.
                    self.assertGreater(max(dx, dy), 128 + 2 * 64 + 32)

    def test_conflict_halo_proof(self):
        reach = 2 * number("MAX_OFFSET") + number("ANCHOR_SIZE") + 2 * number("VISUAL_MARGIN") + number("BETWEEN_GAP")
        halo, region = number("NEIGHBOR_HALO"), number("REGION_SIZE")
        # Any excluded owner differs on an axis by >= halo+1, whose nearest
        # possible base origins are separated by > halo * region.
        self.assertGreaterEqual(halo * region, reach)
        self.assertLess((halo - 1) * region, reach)
        self.assertIn("2 * MAX_OFFSET + ANCHOR_SIZE + 2 * VISUAL_MARGIN + BETWEEN_GAP", SOURCE)

    def test_symmetric_query_reach_covers_crossing_members(self):
        reach = number("MAX_OFFSET") + number("ANCHOR_SIZE") + number("VISUAL_MARGIN")
        self.assertEqual(reach, 640)
        for base in (-1536, -32, 0, 1504, 1536):
            owner = math.floor(base / 1536)
            for offset in (-448, 0, 448):
                for point in (base + offset - 64, base + offset + 128 + 64):
                    first, last = math.floor((point - reach) / 1536), math.floor((point + reach) / 1536)
                    self.assertLessEqual(first, owner)
                    self.assertGreaterEqual(last, owner)
        self.assertIn("area.position - Vector2.ONE * QUERY_REACH", SOURCE)
        self.assertIn("area.end + Vector2.ONE * QUERY_REACH", SOURCE)

    def test_stable_channels_and_group_target(self):
        self.assertIn('key.sha256_text().left(7).hex_to_int()', SOURCE)
        self.assertIn('[POLICY, _seed, owner.x, owner.y, slot, channel]', SOURCE)
        self.assertIn('return 1 if roll < 60 else (2 if roll < 90 else 3)', SOURCE)
        self.assertEqual(sample(42, (-1, 2), 3, "group"), 121821107)
        counts = [0, 0, 0]
        for seed, x, y, slot in product((0, 42, -79), range(-8, 9), range(-8, 9), range(4)):
            roll = sample(seed, (x, y), slot, "group") % 100
            counts[0 if roll < 60 else 1 if roll < 90 else 2] += 1
        total = sum(counts)
        for count, target in zip(counts, (.6, .3, .1)):
            self.assertLess(abs(count / total - target), .035)

    def test_atomic_raw_neighbor_resolution(self):
        self.assertIn('not made.ok or not _eligible(made.location)', SOURCE)
        self.assertIn('_precedes(other, candidate) and _conflicts(candidate.location, other.location)', SOURCE)
        self.assertIn('accepted.append(candidate.location)', SOURCE)
        self.assertNotIn('accepted.append(member)', SOURCE)
        candidate = SOURCE.split('func _candidate(', 1)[1].split('static func _precedes', 1)[0]
        self.assertNotIn('region(', candidate)
        self.assertNotIn('_cache', candidate)
        self.assertIn('return a.location.location_id < b.location.location_id', SOURCE)

    def test_geology_uses_existing_numeric_terrain_and_rejects_unsupported_vocabularies(self):
        self.assertIn('Definition.definitions_error(definitions, [&"terrain_geology"])', SOURCE)
        self.assertIn('_terrain._noise(point / 768.0, 1)', SOURCE)
        terrain = (ROOT / 'scenes/world/planet_generator.gd').read_text()
        self.assertIn('var geology := _noise(point / 768.0, 1)', terrain)
        self.assertNotIn('sample_ground_material(', SOURCE)
        self.assertNotIn('sample_color(', SOURCE)
        self.assertIn('not is_finite(total)', SOURCE)

    def test_unregistered_native_definitions_have_provisional_relative_weights(self):
        weights = {}
        for resource in ('ferrite', 'carbite', 'cuprite'):
            data = (ROOT / f'scenes/world/resource_definitions/v2/{resource}.tres').read_text()
            self.assertIn('script_class="WorldResourceDefinition"', data)
            self.assertIn(f'resource_id = &"{resource}"', data)
            self.assertIn('"terrain_geology"', data)
            weights[resource] = float(re.search(r'abundance_weight = ([\d.]+)', data)[1])
        self.assertEqual(weights, {'ferrite': 1.2, 'carbite': 1.0, 'cuprite': 1.0})
        for file in (ROOT / 'scenes').rglob('*'):
            if file.suffix in ('.gd', '.tscn', '.tres') and file.name != 'ordinary_resource_generator.gd':
                self.assertNotIn('ordinary_resource_generator.gd', file.read_text(encoding='utf-8'))
                self.assertNotIn('resource_definitions/v2/', file.read_text(encoding='utf-8'))

    def test_queries_reject_before_work_and_copy_cache_values(self):
        query = SOURCE.split('func query_owners(', 1)[1].split('func query(', 1)[0]
        for check in ('area.is_finite()', 'area.end.is_finite()', 'area.size.x < 0.0',
                      'MAX_QUERY_REGIONS', 'MAX_REGION_COORDINATE - 1'):
            self.assertIn(check, query)
        self.assertLess(query.index('if count > MAX_QUERY_REGIONS'), query.index('for y in range'))
        self.assertIn('not seen.has(member.deposit_id)', SOURCE)
        self.assertIn('_cache[owner].duplicate(true)', SOURCE)
        self.assertIn('accepted.duplicate(true)', SOURCE)
        self.assertIn('_cache.erase(_cache.keys()[0])', SOURCE)
        self.assertEqual(number('MAX_QUERY_REGIONS') * number('CANDIDATE_SLOTS') * 3, 768)

    def test_identity_is_canonical_and_foundation_owned(self):
        self.assertIn('Descriptors.create_location(POLICY, _seed, owner, slot,', SOURCE)
        self.assertIn('str(parts[index].to_int()) != parts[index]', SOURCE)
        self.assertIn('parts[3].to_int() < -MAX_REGION_COORDINATE', SOURCE)
        self.assertNotIn('absi(parts[', SOURCE)  # int64 minimum must not wrap via abs.
        self.assertIn('location.location_id == identity', SOURCE)
        self.assertIn('member.deposit_id == identity', SOURCE)

    def test_no_mutable_gameplay_or_artwork_inputs(self):
        code = '\n'.join(line.split('#')[0] for line in SOURCE.splitlines())
        for forbidden in ('RandomNumberGenerator', 'randf(', 'randi(', 'String.hash(',
                          'FileAccess', 'DirAccess', 'Texture2D', 'Node2D', 'get_tree(',
                          'PlanetWorldState.new(', 'FerriteRegionGenerator', 'get_machines(',
                          'depletion', 'quantity', 'distance_to_ship'):
            self.assertNotIn(forbidden, code)
        self.assertIn('definition.duplicate(true)', code)
        self.assertIn('_protected.append(bounds)', code)

    def test_behavioral_obligations_are_authored_only(self):
        for label in ('same seed reverse query order and cache eviction',
                      'foundation schema compatible complete membership',
                      'cross-region query deduplication', 'cross-region ownership retained',
                      'accepted single pair triple coverage',
                      'unavailable environment fails closed', 'stable tie breaking',
                      'authored protection rejects complete group',
                      'raw group never silently trimmed',
                      'rejected queries do no generation',
                      'returned descriptors cannot mutate cache'):
            self.assertIn(label, ASSERTIONS)
        for runner in (ROOT / 'tools').glob('*.ps1'):
            self.assertNotIn('ordinary_resource_generator_test', runner.read_text(encoding='utf-8'))

    def test_preserved_foundation_gameplay_assets_and_controls(self):
        paths = ['assets', 'construction', 'inventory', 'persistence', 'tools', 'AGENTS.md',
                 'scenes/world/world_resource_definition.gd', 'scenes/world/resource_generation_descriptors.gd',
                 'scenes/world/planet_generator.gd', 'scenes/world/planet_world_state.gd',
                 'scenes/world/planet_exterior.gd', 'scenes/world/planet_exterior.tscn',
                 'scenes/world/ferrite_region_generator.gd', 'scenes/world/ferrite_deposit_presenter.gd',
                 'scenes/world/resource_deposit.gd', 'scenes/world/cuprite_visual_prototype.tscn',
                 'tests/static_resource_generation_v2_test.py', 'tests/resource_generation_v2_contract_test.gd']
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--', *paths], cwd=ROOT, text=True)
        self.assertEqual(changed, '')


if __name__ == '__main__':
    unittest.main()
