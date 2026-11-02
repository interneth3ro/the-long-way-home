"""Read-only identity and adversarial scope checks; never invokes Godot."""
import hashlib
import importlib
import json
from pathlib import Path
import unittest
from unittest.mock import patch

import current_preservation as scope


# Each original failed method must still reject corruption of its protected
# input. Subtest failures are collected by TestResult, never suppressed in the
# production discovery run. The intentionally failing instances here are inert
# controlled doubles, not edits to owner/source files.
GUARDS = {
    'scenes/main/scene_transition_controller.gd': [
        'static_conversation_ui_test.ConversationUIStaticTest.test_gameplay_ownership_and_narrative_unchanged',
        'static_ground_rejection_test.GroundRejectionStaticTest.test_distant_operation_counts_and_unchanged_systems',
        'static_illustrated_exterior_test.IllustratedExteriorStaticTest.test_ordered_masks_feather_state_and_gameplay_remain_exact',
        'static_illustrated_terrain_test.IllustratedTerrainStaticTest.test_references_diagnostic_visibility_and_production_preservation',
        'static_musing_ui_test.MusingUIStaticTest.test_narrative_progression_and_adjacent_ui_preserved',
        'static_v2_connection_test.V2ConnectionStaticTest.test_single_host_and_unchanged_cache_lock_and_rearm_contract',
        'static_v2_production_host_test.V2ProductionHostStaticTest.test_protected_existing_code_art_and_sidecars_unchanged',
    ],
    'scenes/world/planet_exterior.tscn': [
        'static_illustrated_exterior_test.IllustratedExteriorStaticTest.test_exact_candidate_amendments_reject_tampering_and_expansion',
        'static_illustrated_terrain_presenter_test.PresenterStaticTest.test_exact_inputs_and_test_amendments_reject_tampering',
        'static_illustrated_terrain_presenter_test.PresenterStaticTest.test_unchanged_production_assets_controls_and_historical_inventory',
        'static_low_green_ground_test.LowGreenStaticTest.test_authored_clearing_masks_and_authority_preserved',
        'static_machine_icons_test.MachineIconsStaticTest.test_protected_assets_gameplay_and_execution_controls_match_pr91',
        'static_production_terrain_test.ProductionTerrainStaticTest.test_production_assets_policy_and_pr99_unchanged',
        'static_terrain_resolver_test.TerrainResolverStaticTest.test_production_and_approved_assets_preserved',
        'static_v2_connection_test.V2ConnectionStaticTest.test_art_and_shared_production_preserved',
        'static_weathered_earth_test.WeatheredEarthStaticTest.test_unchanged_gameplay_lifecycle_and_generator_methods',
        'static_illustrated_exterior_test.IllustratedExteriorStaticTest.test_scene_draw_order_and_resource_references',
    ],
    'assets/environment/exterior/crashed_exploration_ship_approved.png': [
        'static_native_terrain_47_test.Native47StaticTest.test_lab_references_and_production_isolation',
    ],
}


def mutate(raw):
    return bytes([raw[0] ^ 1]) + raw[1:]


class CurrentPreservationStaticTest(unittest.TestCase):
    def test_current_identities_and_projections_are_bound_to_accepted_commits(self):
        self.assertEqual(len(scope.CURRENT_INPUT_SHA256), 5)
        self.assertEqual(len(scope.PREDECESSORS), 4)
        for path, digest in scope.CURRENT_INPUT_SHA256.items():
            raw = (scope.ROOT/path).read_bytes()
            accepted = scope.git_blob(scope.ACCEPTED_IMPLEMENTATION, path)
            self.assertEqual(scope.normalized(path, raw), scope.normalized(path, accepted), path)
            scope.verify_current_input(path, raw)
            self.assertEqual(hashlib.sha256(scope.normalized(path, accepted)).hexdigest(), digest)
            before = scope.git_blob(scope.PREDECESSORS[path], path) if path in scope.PREDECESSORS else raw
            self.assertEqual(scope.historical_bytes(path, raw), before)
            for bad in (mutate(raw), raw + b'UNREVIEWED', raw[1:], raw + raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    scope.historical_bytes(path, bad)
            with self.assertRaises(AssertionError):
                scope.verify_current_input(path + '.other', raw)
            if path in scope.PREDECESSORS:
                self.assertEqual(scope.historical_bytes(path, before), before)
                with self.assertRaises(AssertionError):
                    scope.verify_current_input(path, before)

    def test_complete_maintained_test_receipts_reject_unrelated_edits(self):
        self.assertEqual(len(scope.MAINTAINED_TEST_SHA256), 15)
        for path, digest in scope.MAINTAINED_TEST_SHA256.items():
            raw = (scope.ROOT/path).read_bytes()
            before = scope.git_blob(scope.MAINTENANCE_BASE, path)
            scope.verify_fingerprint(path, raw, digest)
            self.assertNotEqual(scope.normalized(path, raw), scope.normalized(path, before))
            self.assertEqual(scope.historical_bytes(path, raw), before)
            for bad in (mutate(raw), raw + b'UNRELATED', raw + raw, raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    scope.historical_bytes(path, bad)
        for path, digest in scope.ACCEPTED_TEST_SHA256.items():
            raw = (scope.ROOT/path).read_bytes()
            accepted = scope.git_blob(scope.ACCEPTED_IMPLEMENTATION, path)
            self.assertEqual(scope.normalized(path, raw), scope.normalized(path, accepted))
            scope.verify_fingerprint(path, raw, digest)
            self.assertEqual(scope.historical_bytes(path, raw), scope.git_blob(scope.PREDECESSORS[path], path))
            with self.assertRaises(AssertionError):
                scope.historical_bytes(path, mutate(raw))
        for path in scope.native.TEST_UPDATE_SHA256:
            original = scope.git_blob(scope.native.REVIEWED_HEAD, path)
            self.assertEqual(scope.historical_test_bytes(path, original), original)
            with self.assertRaises(AssertionError):
                scope.historical_test_bytes(path, mutate(original))

    def test_historical_helpers_manifests_and_execution_policy_are_unchanged(self):
        for path in (
            'tests/exterior_activation_preservation.py', 'tests/production_terrain_preservation.py',
            'tests/native_terrain_preservation.py', 'tests/illustrated_exterior_native_validation.gd',
            'tests/fabricator_recipe_switching_test.gd', 'tools/run-local-tests.ps1',
            'docs/experiments/illustrated_exterior_stage.json',
            'docs/experiments/illustrated_terrain_presenter_stage.json',
            'docs/experiments/production_terrain_stage.json', 'docs/LOCAL_TESTING.md',
            'AGENTS.md', '.gitattributes',
        ):
            actual = scope.normalized(path, (scope.ROOT/path).read_bytes())
            expected = scope.normalized(path, scope.git_blob(scope.MAINTENANCE_BASE, path))
            self.assertEqual(actual, expected, path)

    def test_unrelated_owner_inputs_get_no_projection_or_inventory_exemption(self):
        for path in ('assets/ui/b1_theme.tres', 'construction/recipes/ferrite_plate.tres',
                     'dialogue/computer_opening.tres', 'tools/run-local-tests.ps1'):
            raw = (scope.ROOT/path).read_bytes() + b'OWNER'
            self.assertEqual(scope.historical_bytes(path, raw), raw)
            self.assertEqual(scope.without_current_paths([path]), [path])
            with self.assertRaises(AssertionError):
                scope.verify_current_input(path, raw)

    def test_all_sealed_inputs_and_original_manifest_reject_tampering(self):
        path = 'docs/experiments/illustrated_exterior_stage.json'
        raw = (scope.ROOT/path).read_bytes()
        self.assertEqual(scope.normalized(path, raw), scope.normalized(path, scope.git_blob(scope.SEALED_REVIEW_HEAD, path)))
        proposal = json.loads(raw)
        self.assertEqual(len(proposal['inputs']), 83)
        for path, record in proposal['inputs'].items():
            original = scope.sealed_input(path, record)
            for bad in (mutate(original), original + b'EXTRA', original[1:]):
                with self.subTest(path=path), patch.object(scope, 'git_blob', return_value=bad):
                    with self.assertRaises(AssertionError):
                        scope.sealed_input(path, record)
            with self.assertRaises(AssertionError):
                scope.sealed_input(path, record | {'sha256': '0' * 64})
            with self.assertRaises(AssertionError):
                scope.sealed_input(path, record | {'bytes': record['bytes'] + 1})

    def test_every_original_working_guard_rejects_protected_input_corruption(self):
        original_bytes, original_text = Path.read_bytes, Path.read_text
        self.assertEqual(sum(map(len, GUARDS.values())), 18)
        for protected, identifiers in GUARDS.items():
            target = scope.ROOT/protected
            for identifier in identifiers:
                module, cls, method = identifier.split('.')
                case_class = getattr(importlib.import_module(module), cls)
                case = case_class(method)
                # Establish geometry/source fixtures before injecting corruption.
                case_class.setUpClass()

                def read_bytes(path):
                    raw = original_bytes(path)
                    return mutate(raw) if path == target else raw

                def read_text(path, *args, **kwargs):
                    text = original_text(path, *args, **kwargs)
                    return text + '\n# UNREVIEWED\n' if path == target else text

                with self.subTest(test=identifier), patch.object(Path, 'read_bytes', read_bytes), patch.object(Path, 'read_text', read_text):
                    result = unittest.TestResult()
                    case.run(result)
                    self.assertFalse(result.errors, result.errors)
                    self.assertTrue(result.failures, identifier + ' accepted corruption')

    def test_original_sealed_guard_rejects_corrupted_historical_controller(self):
        module = importlib.import_module('static_illustrated_exterior_test')
        original = scope.git_blob

        def read_blob(ref, path):
            raw = original(ref, path)
            return mutate(raw) if path == 'scenes/main/scene_transition_controller.gd' else raw

        case = module.IllustratedExteriorStaticTest('test_proposed_native_package_is_closed_bounded_and_non_playable')
        with patch.object(scope, 'git_blob', read_blob):
            result = unittest.TestResult()
            case.run(result)
        self.assertFalse(result.errors, result.errors)
        self.assertTrue(result.failures, 'Historical package accepted corruption')


if __name__ == '__main__':
    unittest.main()
