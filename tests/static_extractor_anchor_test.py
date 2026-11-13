"""Nonexecuting source guards and independent math; never runs Godot/GDScript."""
from pathlib import Path
import math
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = '5e88e774f13d80befe63c5fb24c0cace24e35f3f'
RULE_PATH = 'construction/extractor_anchor_rules.gd'
HARNESS_PATH = 'scenes/experiments/resource_generation_v2/extractor_anchor_inspection.gd'
RULES = (ROOT / RULE_PATH).read_text()
HARNESS = (ROOT / HARNESS_PATH).read_text()
ASSERTIONS = (ROOT / 'tests/extractor_anchor_test.gd').read_text()


def body(source, name):
    return re.search(r'^(?:static )?func ' + name + r'\(.*?(?=^(?:static )?func |\Z)',
                     source, re.M | re.S)[0]


def code(source):
    return '\n'.join(line.split('#')[0] for line in source.splitlines())


class ExtractorAnchorStaticTests(unittest.TestCase):
    def test_fixed_geometry_and_negative_cell_conversion(self):
        self.assertIn('ANCHOR_CELLS := Vector2i(4, 4)', RULES)
        self.assertIn('CELL: int = 32', RULES)
        self.assertIn('Vector2(anchor.position) * CELL, Vector2(anchor.size) * CELL', RULES)
        coordinates = (ROOT / 'scenes/world/world_coordinates.gd').read_text()
        self.assertIn('floori(point.x / CONSTRUCTION_SIZE)', coordinates)
        for x, y in [(0, 0), (-2, -2), (-49, 47), (47, -49), (8192, -8192)]:
            rectangle = (x * 32, y * 32, 4 * 32, 4 * 32)
            self.assertEqual(rectangle[2:], (128, 128))
            self.assertEqual((math.floor(rectangle[0]/32), math.floor(rectangle[1]/32)), (x, y))
        self.assertEqual(math.floor(-.01/32), -1)
        self.assertEqual(math.floor(-1536.01/1536), -2)

    def test_independent_snap_vectors_and_tie_order(self):
        # Independent oracle only; this does not translate/execute project code.
        def choose(point, members):
            candidates = []
            for identity, (x, y) in members:
                dx = max(x - point[0], 0, point[0] - x - 128)
                dy = max(y - point[1], 0, point[1] - y - 128)
                distance = dx*dx + dy*dy
                if distance <= 32*32:
                    candidates.append((distance, identity))
            return min(candidates)[1] if candidates else None
        members = [('resource:b', (128, -64)), ('resource:a', (-64, -64))]
        for order in [members, list(reversed(members))]:
            self.assertEqual(choose((96, 0), order), 'resource:a')
            self.assertEqual(choose((-96, 0), order), 'resource:a')
            for cursor in [(-96.01, 0), (-96, -96), (10000, 0)]:
                self.assertIsNone(choose(cursor, order))
        self.assertIn('SNAP_TOLERANCE: float = 32.0', RULES)
        self.assertIn('cursor.distance_squared_to(cursor.clamp(', RULES)
        self.assertIn('distance == best_distance', RULES)
        self.assertIn('member.deposit_id < best.deposit_id', RULES)

    def test_bounded_existing_generator_query_without_second_owner_algorithm(self):
        target = body(RULES, 'target')
        self.assertIn('source.query(Rect2(', target)
        self.assertIn('select(cursor, result.deposits) if result.ok else {}', target)
        self.assertIn('deposits.size() > 775', RULES)
        for forbidden in ('owner_at(', 'region(', 'query_owners(', '_candidate(', 'visual_bounds('):
            self.assertNotIn(forbidden, code(RULES))
        self.assertNotIn('turns', body(RULES, 'target'))
        self.assertNotIn('turns', body(RULES, 'select'))

    def test_confirmation_resolves_identity_without_retargeting(self):
        reject = body(RULES, 'rejection')
        for check in ('ticket.get("source") != source', 'source.descriptor_by_id(ticket.deposit_id)',
                      'ticket.get("policy") != source.identity_policy()',
                      'ticket.get("anchor_cells") != member.anchor_cells',
                      'definition.compatible_resources.has(StringName(member.resource_type))',
                      'definition.item_id != &"extractor"', 'cell != anchor.position',
                      'definition.footprint_cells != ANCHOR_CELLS',
                      'definition.footprint(cell, turns) != bounds(anchor)', 'occupant != 0',
                      'gameplay_eligible: bool = false'):
            self.assertIn(check, reject)
        self.assertNotIn('select(', reject)
        self.assertNotIn('target(', body(HARNESS, 'confirm'))
        self.assertIn('ticket.get("epoch") != _epoch', HARNESS)
        self.assertIn('ticket.get("seed") != seed_value', HARNESS)
        self.assertIn('_epoch += 1', body(HARNESS, 'configure'))

    def test_seed_consistency_and_fixture_contract(self):
        configure = body(HARNESS, 'configure')
        self.assertLess(configure.index('source._seed != seed_value'), configure.index('_source = source'))
        preview = body(HARNESS, 'preview')
        self.assertLess(preview.index('_source._seed != seed_value'), preview.index('Rules.target('))
        reject = body(HARNESS, 'inspect_rejection')
        self.assertLess(reject.index('_source._seed != seed_value'), reject.index('Rules.rejection('))
        self.assertNotIn('Inspection.new()', body(ASSERTIONS, '_geometry'))
        self.assertNotIn('Inspection.new()', body(ASSERTIONS, '_transactions'))
        for label in ('mismatched generator seed rejected at configure',
                      'world seed mismatch blocks fresh preview', 'world seed mismatch blocks confirmation',
                      'generator seed mismatch blocks fresh preview', 'generator seed mismatch blocks confirmation',
                      'seed failures preserve inventory registry and occupancy',
                      'fixture foundation descriptor validity', 'fixture canonical resource identities'):
            self.assertIn(label, ASSERTIONS)
        fixture = body(ASSERTIONS, '_fixture')
        self.assertIn('Descriptors.location_error(made.location)', fixture)
        self.assertIn('Rect2i(-2, -2, 4, 4), Rect2i(4, -2, 4, 4)', fixture)
        self.assertIn('Vector2i(-1, -1)', fixture)
        self.assertEqual((math.floor(-2/48), math.floor(-2/48)), (-1, -1))
        self.assertEqual((math.floor(4/48), math.floor(-2/48)), (0, -1))

    def test_single_machine_registry_and_constant_occupancy_lookup(self):
        self.assertIn('extends "res://scenes/world/planet_world_state.gd"', HARNESS)
        self.assertNotRegex(HARNESS, r'var _machines\b|var _next_machine_id\b|var _machine_transaction\b')
        occupant = body(HARNESS, 'occupant')
        self.assertIn('_claims.get(deposit_id, 0)', occupant)
        self.assertIn('_machines.has(machine_id)', occupant)
        self.assertNotIn('for ', code(occupant))
        self.assertIn('"v2_deposit_id": ticket.deposit_id', HARNESS)
        self.assertNotIn('func claim', HARNESS)
        self.assertIn('not _machines.is_empty()', body(HARNESS, 'configure'))

    def test_transaction_order_and_reentrancy_guard(self):
        confirm = body(HARNESS, 'confirm')
        operations = ['if _machine_transaction', 'inspect_rejection(', '_machine_transaction = true',
                      'inventory.remove_item(definition, 1, false)', '_machines[machine_id] =',
                      '_claims[ticket.deposit_id] = machine_id', '_next_machine_id += 1',
                      'inventory.changed.emit()', 'machines_changed.emit()']
        positions = [confirm.index(value) for value in operations]
        self.assertEqual(positions, sorted(positions))
        self.assertLess(confirm.rindex('_machine_transaction = false'), confirm.index('return machine_id'))
        failure = confirm.split('if not inventory.remove_item', 1)[1].split('var machine_id', 1)[0]
        self.assertIn('return 0', failure)
        self.assertNotIn('_claims[', failure)
        for forbidden in ('await ', 'call_deferred', 'machine_deployed.emit', 'deploy_machine_instance('):
            self.assertNotIn(forbidden, code(confirm))

    def test_preview_and_confirmation_share_fail_closed_validation(self):
        self.assertIn('inspect_rejection(', body(HARNESS, 'preview'))
        self.assertIn('inspect_rejection(', body(HARNESS, 'confirm'))
        reject = body(HARNESS, 'inspect_rejection')
        for check in ('Rules.rejection(', 'footprint.intersects(other.footprint(',
                      'PlacementRules.distance_to_footprint(', 'context.player_point.is_finite()',
                      'context.range < 0', 'context.get("obstacle_clear") != true',
                      'context.get("player_clear") != true', 'inventory.get_items().has(definition)',
                      'inventory.get_quantity(definition.item_id) < 1'):
            self.assertIn(check, reject)
        self.assertIn('current["inventory"] = inventory', body(HARNESS, 'confirm'))
        for reason in ('No valid target', 'Unavailable anchor', 'Occupied anchor', 'Incompatible resource',
                       'Overlaps a deployed machine', 'Blocked by a solid obstacle'):
            self.assertIn(reason, RULES + HARNESS)

    def test_recovery_uses_existing_transaction_before_index_retirement(self):
        recover = body(HARNESS, 'recover_machine')
        self.assertIn('super.recover_machine(machine_id, inventory, player_point, recovery_range)', recover)
        self.assertLess(recover.index('super.recover_machine('), recover.index('_claims.erase(identity)'))
        self.assertNotIn('inventory.add_', recover)
        self.assertNotIn('_machines.erase', recover)
        self.assertIn('player_point.is_finite()', recover)

    def test_inert_harness_has_no_production_or_gameplay_callers(self):
        self.assertIn('return 0', body(HARNESS, 'deploy_machine_instance'))
        self.assertEqual(code(body(HARNESS, 'advance_production')).strip(),
                         'func advance_production(_delta: float) -> void:\n\tpass')
        for root in ['scenes', 'construction', 'inventory']:
            for path in (ROOT / root).rglob('*'):
                if path.suffix not in ('.gd', '.tscn', '.tres') or path == ROOT / HARNESS_PATH:
                    continue
                self.assertNotIn('extractor_anchor_inspection', path.read_text(encoding='utf-8'), str(path))
        for source in [RULES, HARNESS]:
            for forbidden in ('ResourceDeposit', 'ResourcePresenter', 'Sprite2D', 'Texture2D',
                              'FileAccess', 'DirAccess', 'load_threaded', 'randf(', 'randi('):
                self.assertNotIn(forbidden, code(source))

    def test_authored_assertions_cover_required_behavior_without_runner_dispatch(self):
        for label in ('exact 4x4 geometry and world conversion', 'negative coordinates floor',
                      'stable tie breaking', 'query-order independence', 'snap tolerance outside',
                      'rotation without anchor displacement', 'incompatible resource',
                      'exact footprint alignment', 'occupied-anchor rejection',
                      'duplicate claim and repeated confirmation rejected',
                      'recovery releases occupancy before callbacks',
                      'failed placement without inventory consumption or claim',
                      'reentrant confirmation rejected', 'world seed invalidation',
                      'source and policy invalidation', 'no inactive gameplay activation',
                      'all seven reservations unchanged', 'cross-region deposit coverage',
                      'failed recovery preserves claim', 'normal deployment entry stays disabled'):
            self.assertIn(label, ASSERTIONS)
        for path in (ROOT / 'tools').glob('*.ps1'):
            self.assertNotIn('extractor_anchor_test', path.read_text())

    def test_all_preexisting_gameplay_generation_artwork_and_controls_unchanged(self):
        # Compare tracked baseline bytes, including every historical static guard.
        # Additions are independently scoped below; no historical guard is repinned.
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
        protected = [path for path in files if path.startswith((
            'construction/', 'inventory/', 'scenes/', 'assets/', 'tools/', 'persistence/', 'tests/'))
            or path in ('AGENTS.md', 'project.godot')]
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE], cwd=ROOT, text=True)
        self.assertEqual(set(changed.splitlines()) & set(protected), set())

    def test_references_resolve_and_new_scope_is_exact(self):
        for source in (RULES, HARNESS, ASSERTIONS):
            for ref in re.findall(r'(?:preload\(|extends )"res://([^"\n]+)"', source):
                self.assertTrue((ROOT / ref).is_file(), ref)
        allowed = {RULE_PATH, HARNESS_PATH, 'tests/extractor_anchor_test.gd',
                   'tests/static_extractor_anchor_test.py', 'docs/RESOURCE_GENERATION_V2_PLACEMENT.md'}
        added = subprocess.check_output(['git', 'diff', '--name-only', '--diff-filter=A', BASE], cwd=ROOT, text=True)
        self.assertLessEqual(set(added.splitlines()), allowed)


if __name__ == '__main__':
    unittest.main()
