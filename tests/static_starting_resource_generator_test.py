"""Nonexecuting source/provenance checks and independent mathematical obligations.

No Godot/project code is executed. These are not runtime determinism assertions.
"""
from pathlib import Path
import hashlib
import math
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = '499a86cfb35428b70fb24644fe80b3312d8abdef'
SOURCE = (ROOT / 'scenes/world/starting_resource_generator.gd').read_text()
CONTEXT = (ROOT / 'scenes/world/resource_generation_crash_site.gd').read_text()
DIAGNOSTICS = (ROOT / 'scenes/world/resource_migration_diagnostics.gd').read_text()
ORDINARY = (ROOT / 'scenes/world/ordinary_resource_generator.gd').read_text()
ASSERTIONS = (ROOT / 'tests/starting_resource_generator_test.gd').read_text()


class StartingResourceStaticTests(unittest.TestCase):
    def test_independent_numerical_layout_examples(self):
        # Mathematical policy examples, NOT execution/translation of GDScript.
        # This catches an infeasible budget or contradictory geometry before an
        # owner-authorized runtime test can establish engine reconstruction.
        directions = [(1000, 0), (924, 383), (707, 707), (383, 924), (0, 1000),
                      (-383, 924), (-707, 707), (-924, 383), (-1000, 0),
                      (-924, -383), (-707, -707), (-383, -924), (0, -1000),
                      (383, -924), (707, -707), (924, -383)]
        protection = [(-992, -640, 928, 832), (-1047, -727, 328, -3),
                      (-912, 192, -624, 480), (560, -576, 848, -288),
                      (-880, -752, 880, 816), (-1072, -912, -144, -80),
                      (-1072, -1072, 1072, -720), (-1072, 720, 1072, 1072)]

        def intersects(a, b):
            return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]

        results = []
        for seed in (26026, 0, 1, 42, -79, 7341, -9223372036854775807, 9223372036854775807):
            def sample(attempt, slot, channel):
                key = f'starting-v2-2:{seed}:{attempt}:{slot}:{channel}'
                return int(hashlib.sha256(key.encode()).hexdigest()[:7], 16)

            found = None
            for attempt in range(4096):
                groups, slot = [], 4
                for count, thresholds in zip((3, 2, 2), ((25, 90), (10, 65), (45, 90))):
                    remaining = count
                    while remaining:
                        members = 1 + sample(attempt, slot, 'group') % remaining
                        remaining -= members
                        roll = sample(attempt, slot, 'band') % 100
                        band = 0 if roll < thresholds[0] else 1 if roll < thresholds[1] else 2
                        lo, hi = ((14, 22), (26, 46), (50, 68))[band]
                        radius = lo + sample(attempt, slot, 'radius') % (hi - lo + 1)
                        dx, dy = directions[sample(attempt, slot, 'direction') % 16]
                        origin = (round(-12 + dx * radius / 1000) - 2,
                                  round(-6 + dy * radius / 1000) - 2)
                        group = []
                        for x, y in ((0, 0), (12, -2), (4, 12))[:members]:
                            for _ in range(sample(attempt, slot, 'rotation') % 4):
                                x, y = -y, x
                            group.append(((origin[0] + x) * 32, (origin[1] + y) * 32))
                        groups.append(group)
                        slot += 1
                valid = True
                for i, group in enumerate(groups):
                    for x, y in group:
                        envelope = (x - 64, y - 64, x + 192, y + 192)
                        if not 384 <= math.hypot(x + 64 + 384, y + 64 + 192) <= 2304:
                            valid = False
                        if any(intersects(envelope, p) for p in protection):
                            valid = False
                        expanded = (x - 512, y - 512, x + 640, y + 640)
                        for earlier in groups[:i]:
                            if any(intersects(expanded, (a - 64, b - 64, a + 192, b + 192)) for a, b in earlier):
                                valid = False
                if valid:
                    found = (attempt, groups)
                    break
            self.assertIsNotNone(found, f'numerical example exhausts budget: {seed}')
            self.assertEqual(sum(map(len, found[1])), 7)
            results.append(found[1])
        self.assertGreater(len({str(result) for result in results}), 1)

    def test_complete_bounded_search_and_failure_publication(self):
        self.assertIn('const ARRANGEMENT_BUDGET: int = 4096', SOURCE)
        self.assertIn('const REQUIRED := {"ferrite": 3, "carbite": 2, "cuprite": 2}', SOURCE)
        self.assertIn('for attempt in range(ARRANGEMENT_BUDGET)', SOURCE)
        self.assertLess(SOURCE.index('var arrangement := _arrangement(attempt)'),
                        SOURCE.index('if _arrangement_valid(arrangement)'))
        self.assertIn('_reservations = arrangement', SOURCE)
        self.assertIn('complete seven-deposit starting arrangement exhausted', SOURCE)
        self.assertIn('return counts == REQUIRED', SOURCE)
        self.assertIn('remaining -= members', SOURCE)
        self.assertNotIn('while true', SOURCE)

    def test_shared_validation_and_owner_identity(self):
        for fragment in ('Descriptors.create_location(STARTING_POLICY',
                         'Descriptors.configured_location_error', 'not _eligible(location)',
                         '_conflicts(location, locations[previous])',
                         'owner_at(Vector2(origin) * CELL)', 'const START_SLOT: int = 4',
                         'location.location_slot >= START_SLOT + 7'):
            self.assertIn(fragment, SOURCE)
        # Ordinary slots [0,4), reserved slots [4,11): disjoint even in one owner.
        self.assertFalse(set(range(4)) & set(range(4, 11)))
        self.assertIn('return super.descriptor_by_id(identity)', SOURCE)
        self.assertIn('location.duplicate(true)', SOURCE)

    def test_distance_preferences_overlap_and_transition_is_presence_only(self):
        self.assertIn('[[25, 90], [10, 65], [45, 90]]', SOURCE)
        # Every resource has positive mass in all three radial bands.
        for a, b in ((25, 90), (10, 65), (45, 90)):
            self.assertTrue(0 < a < b < 100)
        self.assertIn('get_center().distance_to(_ship)', SOURCE)
        self.assertIn('distance < MIN_DISTANCE or distance > MAX_DISTANCE', SOURCE)
        weights = []
        for distance in (0, 1536, 1920, 2304, 2688, 3072, 100000):
            t = max(0, min(1, (distance - 1536) / 1536))
            weights.append(t * t * (3 - 2 * t))
        self.assertEqual(weights, sorted(weights))
        self.assertEqual(weights[:2], [0, 0])
        self.assertEqual(weights[3], .5)
        self.assertEqual(weights[-2:], [1, 1])
        self.assertIn('smoothstep(float(INNER_RADIUS)', SOURCE)
        candidate = SOURCE.split('func _candidate(', 1)[1].split('func region(', 1)[0]
        self.assertIn('super._candidate(owner, slot)', candidate)
        self.assertIn('not _ordinary_allowed(raw.location, owner, slot)', candidate)
        self.assertNotIn('region(', candidate)
        region = SOURCE.split('func region(', 1)[1].split('func descriptor_by_id', 1)[0]
        self.assertNotIn('transition', region)
        self.assertNotIn('_ordinary_allowed', region)

    def test_raw_competition_and_old_policy_preserved(self):
        old = subprocess.check_output(['git', 'show', f'{BASE}:scenes/world/ordinary_resource_generator.gd'],
                                      cwd=ROOT, text=True)
        expected = old.replace('func descriptor_by_id(identity: String) -> Dictionary:',
                              'func identity_policy() -> String:\n\treturn POLICY\n\n\n'
                              'func descriptor_by_id(identity: String) -> Dictionary:')
        expected = expected.replace('if parts[1] != POLICY:', 'if parts[1] != identity_policy():')
        self.assertEqual(ORDINARY, expected)
        self.assertIn('_precedes(other, candidate) and _conflicts(candidate.location, other.location)', ORDINARY)
        self.assertIn('_conflicts(location, reservation)', SOURCE)
        self.assertIn('raw.priority', SOURCE)
        self.assertIn('"starting-v2-1"', SOURCE)

    def test_query_reach_covers_reserved_templates(self):
        # Reserved offsets <=384 vs ordinary maximum 448. Inherited symmetric
        # 640-unit query reach therefore covers even cross-owner members.
        for x, y in ((0, 0), (12, -2), (4, 12)):
            self.assertLessEqual(max(abs(x), abs(y)) * 32, 448)
        self.assertIn('Vector2i(12, -2), Vector2i(4, 12)', SOURCE)
        self.assertIn('not seen.has(member.deposit_id)', ORDINARY)
        self.assertIn('var owned := region(owner)', ORDINARY)

    def test_authored_ship_snapshot_provenance_and_clearance(self):
        scene = (ROOT / 'scenes/world/planet_exterior.tscn').read_text()
        ship = re.search(r'\[node name="CrashedShip".*?position = Vector2\(([^)]+)\)', scene, re.S)[1]
        self.assertEqual(ship, '-384, -192')
        self.assertIn('SHIP_REFERENCE := Vector2(-384, -192)', CONTEXT)
        points = []
        for name in ('ShipNoseFootprint', 'ShipFuselageFootprint', 'ShipRearFootprint'):
            raw = re.search(r'id="' + name + r'"\]\npoints = PackedVector2Array\(([^)]+)\)', scene)[1]
            values = list(map(int, raw.split(',')))
            points.extend((x - 384, y - 192) for x, y in zip(values[::2], values[1::2]))
        x0, y0 = min(x for x, y in points), min(y for x, y in points)
        x1, y1 = max(x for x, y in points), max(y for x, y in points)
        self.assertEqual((x0, y0, x1 - x0, y1 - y0), (-951, -631, 1183, 532))
        self.assertIn('Rect2(-951, -631, 1183, 532).grow(CONSTRUCTION_CLEARANCE)', CONTEXT)
        self.assertIn('Protection.GAMEPLAY', CONTEXT)
        self.assertIn('CONSTRUCTION_CLEARANCE: int = 96', CONTEXT)
        # Hatch collision and approach lie inside shared gameplay AABB.
        self.assertIn('position = Vector2(-384, -176)', scene)
        for name, expected in [('Clearing', (-832, -704, 1664, 1472)),
                               ('ImpactScar', (-1024, -864, 832, 736)),
                               ('NorthRidge', (-1024, -1024, 2048, 256)),
                               ('SouthShelf', (-1024, 768, 2048, 256))]:
            raw = re.search(r'\[node name="' + name + r'"[^\n]*\]\npolygon = PackedVector2Array\(([^)]+)\)', scene)[1]
            values = list(map(int, raw.split(',')))
            xs, ys = values[::2], values[1::2]
            self.assertEqual((min(xs), min(ys), max(xs)-min(xs), max(ys)-min(ys)), expected)
            self.assertIn('Rect2(%d, %d, %d, %d).grow(48)' % expected, CONTEXT)
        for name, position in [('WestRock', '-768, 384'), ('EastRock', '704, -384')]:
            self.assertIn(f'position = Vector2({position})', scene)
        # Protection source is byte-preserved by the preservation test below.

    def test_diagnostics_are_bounded_deterministic_and_read_only(self):
        for fragment in ('MAX_LEGACY: int = 128', 'MAX_LOCATIONS: int = 128',
                         'MAX_REPORTS: int = 256', 'legacy.duplicate(true)',
                         'locations.duplicate(true)', 'ordered_legacy.sort_custom',
                         'ordered_locations.sort_custom', 'potential_gameplay_overlap',
                         'visual_proximity', 'potential_authored_overlap',
                         'v2_authored_clearance', '"complete": false',
                         '"owner_review_required": true', '"first_bounds"', '"second_bounds"'):
            self.assertIn(fragment, DIAGNOSTICS)
        code = '\n'.join(line.split('#')[0] for line in DIAGNOSTICS.splitlines())
        for forbidden in ('FileAccess', 'FerriteRegionGenerator.new', 'ResourceLoader',
                          '.erase(', 'set_deferred', 'relocate'):
            self.assertNotIn(forbidden, code)
        self.assertNotRegex(code, r'(?<![\w])(?:legacy|locations)\.sort')

    def test_behavioral_obligations_authored_and_not_dispatched(self):
        for label in ('exact seven counts', 'same seed complete reconstruction',
                      'seed position and grouping variation', 'explicit bounded exhaustion',
                      'whole arrangement rejection', 'stable reserved identity',
                      'cross-region deduplication', 'reverse query order and cache eviction',
                      'inactive reservation blocks ordinary triple',
                      'removed raw competitor cannot suppress survivor',
                      'transition endpoints and midpoint', 'legacy snapshots unchanged',
                      'potential blocking overlap requires owner review'):
            self.assertIn(label, ASSERTIONS)
        for runner in (ROOT / 'tools').glob('*.ps1'):
            self.assertNotIn('starting_resource_generator_test', runner.read_text())

    def test_no_live_integration_or_mutable_generation_inputs(self):
        code = '\n'.join(line.split('#')[0] for line in SOURCE.splitlines())
        for forbidden in ('FileAccess', 'get_tree(', 'get_node(', 'Texture2D',
                          'get_machines(', 'RandomNumberGenerator', 'randf(', 'randi(',
                          'FerriteRegionGenerator', 'active_types', 'depletion', 'quantity'):
            self.assertNotIn(forbidden, code)
        for file in (ROOT / 'scenes').rglob('*'):
            if file.suffix in ('.gd', '.tres', '.tscn') and file.name != 'starting_resource_generator.gd':
                self.assertNotIn('starting_resource_generator.gd', file.read_text(encoding='utf-8'))

    def test_preserved_gameplay_assets_foundation_and_safety_controls(self):
        paths = ['assets', 'construction', 'inventory', 'persistence', 'tools', 'AGENTS.md',
                 'project.godot', 'scenes/world/planet_generator.gd',
                 'scenes/world/planet_world_state.gd', 'scenes/world/planet_exterior.gd',
                 'scenes/world/planet_exterior.tscn', 'scenes/world/ferrite_region_generator.gd',
                 'scenes/world/ferrite_deposit_presenter.gd', 'scenes/world/crash_site_protection.gd',
                 'scenes/world/introductory_ferrite.tres', 'scenes/world/resource_definitions',
                 'scenes/world/resource_generation_descriptors.gd', 'scenes/world/world_resource_definition.gd',
                 'tests/static_resource_generation_v2_test.py', 'tests/resource_generation_v2_contract_test.gd']
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--', *paths], cwd=ROOT, text=True)
        self.assertEqual(changed, '')


if __name__ == '__main__':
    unittest.main()
