"""Fixed ground-art pins and adversarial inputs; no protected file writes."""
from pathlib import Path
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

    def test_every_modified_admitted_file_is_rejected(self):
        for path in guard.record()['admitted']:
            raw = guard.read_working(path)
            for changed in (raw+b'ALTERED', b'X'+raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    guard.verify_admitted(path, changed)


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


    def test_owner_pinned_candidate_atlas_hashes_are_unchanged(self):
        prefix = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/'
        for name, expected in {
            'baseline_94.png': '36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0',
            'interiors_bc.png': 'd8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694',
        }.items():
            self.assertEqual(guard.sha256(guard.read_working(prefix+name)), expected)


if __name__ == '__main__':
    unittest.main()
