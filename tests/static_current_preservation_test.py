"""Read-only identity and adversarial scope checks; never invokes Godot."""
import importlib
import json
import unittest
from unittest.mock import patch

import current_preservation as scope


def mutate(raw):
    return bytes([raw[0] ^ 1]) + raw[1:]


class CurrentPreservationStaticTest(unittest.TestCase):
    def test_approved_artwork_rejects_mutation(self):
        for path, digest in scope.ARTWORK_SHA256.items():
            raw = (scope.ROOT/path).read_bytes()
            scope.verify_fingerprint(path, raw, digest)
            with self.subTest(path=path), self.assertRaises(AssertionError):
                scope.verify_fingerprint(path, mutate(raw), digest)

    def test_historical_stage_manifests_are_unchanged(self):
        for path, revision in (
            ('docs/experiments/production_terrain_stage.json', '4c5bccc1877472a3551df756b673ef5e059dccf6'),
            ('docs/experiments/illustrated_terrain_presenter_stage.json', '63318e464898b8ecf4596216f9577cd64e72dbcc'),
        ):
            expected = scope.git_blob(revision, path).replace(b'\r\n', b'\n')
            actual = (scope.ROOT/path).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(actual, expected, path)

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
