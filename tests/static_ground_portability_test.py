"""Exact two-path checkout contracts; corruption is supplied in memory only."""
import unittest
from unittest.mock import patch

import ground_art_preservation as guard


class GroundPortabilityTest(unittest.TestCase):
    def test_original_git_identities_and_both_exact_checkout_forms(self):
        for path, (revision, identity) in guard.PORTABLE.items():
            original = guard.git_bytes(revision, path)
            self.assertEqual(guard.blob_id(original), identity)
            self.assertEqual(guard.historical_checkout(path), original)
            for checkout in (original, original.replace(b'\n', b'\r\n')):
                self.assertEqual(guard.historical_checkout(path, checkout), original)

    def test_mixed_endings_and_changed_content_are_rejected(self):
        for path, (revision, _) in guard.PORTABLE.items():
            original = guard.git_bytes(revision, path)
            # The audit has many lines; the one-line attributes file also must
            # reject extra mixed-ending content rather than normalizing it away.
            mixed = original.replace(b'\n', b'\r\n', 1)
            if mixed == original.replace(b'\n', b'\r\n'):
                mixed += b'\n'
            for damaged in (mixed, original+b'ALTERED', original[1:], b'X'+original[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    guard.historical_checkout(path, damaged)

    def test_changed_historical_head_and_index_git_identities_are_rejected(self):
        original_reader = guard.git_bytes
        for path, (revision, _) in guard.PORTABLE.items():
            for target in (revision, 'HEAD', ''):
                def changed(ref, name):
                    raw = original_reader(ref, name)
                    return raw+b'ALTERED' if (ref, name) == (target, path) else raw
                with self.subTest(path=path, ref=target), patch.object(guard, 'git_bytes', side_effect=changed):
                    with self.assertRaises(AssertionError):
                        guard.historical_checkout(path)

    def test_unknown_portability_path_is_rejected(self):
        for path in guard.PORTABLE:
            with self.assertRaises(AssertionError):
                guard.historical_checkout(path+'.other', b'unchanged\n')


if __name__ == '__main__':
    unittest.main()
