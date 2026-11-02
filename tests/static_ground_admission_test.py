"""Fixed ground-art pins and adversarial inputs; no protected file writes."""
from pathlib import Path
import copy
import unittest
from unittest.mock import patch

import ground_art_preservation as guard


class GroundAdmissionTest(unittest.TestCase):
    def test_exact_record_and_all_thirty_seven_working_identities(self):
        record = guard.record()
        self.assertEqual(len(record['admitted']), 37)
        self.assertEqual(sum('source_blob' in e for e in record['admitted'].values()), 22)
        self.assertEqual(set(record['validation_amendments']), {
            'tests/current_preservation.py', 'tests/static_ground_refinement_test.py',
            'tests/static_ground_softness_test.py', 'tests/static_stage2e_preservation_test.py',
            'tests/static_housekeeping_test.py'})
        for path in record['admitted']:
            guard.verify_admitted(path)
        self.assertEqual(guard.without_ground_art_paths(list(record['admitted'])), [])

    def test_every_modified_admitted_file_is_rejected(self):
        for path in guard.record()['admitted']:
            raw = guard.read_working(path)
            for changed in (raw+b'ALTERED', b'X'+raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    guard.verify_admitted(path, changed)

    def test_unknown_path_is_not_admitted_or_hidden(self):
        unknown = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/unknown.png'
        with self.assertRaises(AssertionError):
            guard.verify_admitted(unknown, b'unknown')
        self.assertEqual(guard.without_ground_art_paths([unknown]), [unknown])
        self.assertEqual(guard.without_validation_changes([unknown]), [unknown])

    def test_missing_admitted_file_is_rejected_without_deleting_anything(self):
        path = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/baseline_94.png'
        original_reader = Path.read_bytes
        def missing(instance):
            if instance == guard.ROOT/path:
                raise FileNotFoundError(path)
            return original_reader(instance)
        with patch.object(Path, 'read_bytes', missing), self.assertRaisesRegex(AssertionError, 'Missing preserved file'):
            guard.verify_admitted(path)

    def test_admission_record_cannot_supply_its_own_replacement_hashes(self):
        original_reader = guard.read_working
        def changed(path):
            raw = original_reader(path)
            return raw+b' ' if path == guard.RECORD else raw
        with patch.object(guard, 'read_working', side_effect=changed), self.assertRaisesRegex(AssertionError, 'admission record'):
            guard.record()

    def test_changed_admitted_historical_git_identity_is_rejected(self):
        path = 'tools/ground-art-refinement.py'
        original_reader = guard.git_bytes
        def changed(ref, name):
            raw = original_reader(ref, name)
            return raw+b'ALTERED' if name == path else raw
        with patch.object(guard, 'git_bytes', side_effect=changed), self.assertRaisesRegex(AssertionError, 'Git identity'):
            guard.verify_admitted(path)

    def test_five_validation_amendments_are_verified_before_projection(self):
        paths = list(guard.record()['validation_amendments'])
        self.assertEqual(guard.without_validation_changes(paths), [])
        original_reader = guard.read_working
        for target in paths:
            def changed(path):
                raw = original_reader(path)
                return raw+b'ALTERED' if path == target else raw
            with self.subTest(path=target), patch.object(guard, 'read_working', side_effect=changed):
                with self.assertRaises(AssertionError):
                    guard.without_validation_changes([target])

    def test_owner_pinned_candidate_atlas_hashes_are_unchanged(self):
        prefix = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/'
        for name, expected in {
            'baseline_94.png': '36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0',
            'interiors_bc.png': 'd8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694',
        }.items():
            self.assertEqual(guard.sha256(guard.read_working(prefix+name)), expected)

    def test_all_amendments_are_checked_before_filtering_a_partial_or_empty_list(self):
        paths = list(guard.VALIDATION_PATHS)
        reader = guard.read_working
        for target in paths:
            def changed(path):
                raw = reader(path)
                return raw+b'ALTERED' if path == target else raw
            for requested in ([], [p for p in paths if p != target]):
                with self.subTest(target=target, requested=requested), patch.object(guard, 'read_working', side_effect=changed):
                    with self.assertRaises(AssertionError):
                        guard.without_validation_changes(requested)

    def test_missing_amendment_is_rejected_before_any_filtering(self):
        original_reader = Path.read_bytes
        for target in guard.VALIDATION_PATHS:
            def missing(instance):
                if instance == guard.ROOT/target:
                    raise FileNotFoundError(target)
                return original_reader(instance)
            with self.subTest(path=target), patch.object(Path, 'read_bytes', missing):
                with self.assertRaisesRegex(AssertionError, 'Missing preserved file'):
                    guard.without_validation_changes([])

    def test_incorrect_amendment_hash_is_rejected(self):
        data = guard.record()
        for target in guard.VALIDATION_PATHS:
            damaged = copy.deepcopy(data)
            damaged['validation_amendments'][target]['sha256'] = '0'*64
            with self.subTest(path=target), patch.object(guard, 'record', return_value=damaged):
                with self.assertRaisesRegex(AssertionError, 'Changed reviewed ground-art input'):
                    guard.without_validation_changes([])

    def test_directory_cannot_replace_an_exact_amendment(self):
        damaged = copy.deepcopy(guard.record())
        entry = damaged['validation_amendments'].pop('tests/current_preservation.py')
        damaged['validation_amendments']['tests/'] = entry
        with patch.object(guard, 'record', return_value=damaged):
            with self.assertRaisesRegex(AssertionError, 'exact validation amendment inventory'):
                guard.without_validation_changes(['tests/'])
        self.assertEqual(guard.without_validation_changes(['tests/']), ['tests/'])

    def test_original_stage2a_still_rejects_an_altered_resource(self):
        import current_preservation as current
        import housekeeping_preservation as historical
        path = 'artifacts/evidence/pr100-stage2-baked-v2/earth_patch_varied.png'
        # Verify the real historical path first; supply corruption only through
        # a read double. The source file, index and historical receipt are inert.
        original_reader = Path.read_bytes
        self.assertIn(path, historical.record()['retained'])
        current.without_current_paths([path])
        def changed(instance):
            raw = original_reader(instance)
            return raw+b'ALTERED' if instance == guard.ROOT/path else raw
        with patch.object(Path, 'read_bytes', changed):
            with self.assertRaisesRegex(AssertionError, 'Changed Stage 2A input'):
                current.without_current_paths([path])

    def test_unknown_changed_file_reaches_the_original_inventory_assertion(self):
        import current_preservation as current
        unknown = 'tools/unrecognized-ground-change.py'
        self.assertEqual(current.without_current_paths([unknown]), [unknown])

    def test_stage2a_predecessor_retains_the_original_receipt_and_assertions(self):
        import housekeeping_preservation as historical
        path = 'tests/current_preservation.py'
        original = guard.stage2a_helper_predecessor(path, guard.read_working(path))
        self.assertEqual(original, guard.git_bytes(guard.START, path))
        historical.verify(path, original, historical.record()['existing_changes'][path])
        self.assertNotEqual(original, historical.historical_input(path, original))

    def test_stage2a_replacement_rejects_altered_unknown_and_missing_identities(self):
        path = 'tests/current_preservation.py'
        raw = guard.read_working(path)
        with self.assertRaises(AssertionError):
            guard.stage2a_helper_predecessor(path, raw+b'ALTERED')
        with self.assertRaises(AssertionError):
            guard.stage2a_helper_predecessor(path+'.other', raw)
        for absent in ('entry', 'source_blob'):
            damaged = copy.deepcopy(guard.record())
            if absent == 'entry':
                damaged['validation_amendments'].pop(path)
            else:
                damaged['validation_amendments'][path].pop('source_blob')
            with patch.object(guard, 'record', return_value=damaged), self.assertRaises(AssertionError):
                guard.stage2a_helper_predecessor(path, raw)

    def test_stage2a_changed_original_helper_identity_is_rejected(self):
        path = 'tests/current_preservation.py'
        raw = guard.read_working(path)
        with patch.object(guard, 'git_bytes', return_value=b'ALTERED HISTORICAL HELPER'):
            with self.assertRaisesRegex(AssertionError, 'predecessor identity'):
                guard.stage2a_helper_predecessor(path, raw)


if __name__ == '__main__':
    unittest.main()
