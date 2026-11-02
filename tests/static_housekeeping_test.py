"""Disposition identity and corruption checks; never runs cleanup or Godot."""
from pathlib import Path
import unittest
from unittest.mock import patch

import housekeeping_preservation as housekeeping
from ground_art_preservation import stage2a_helper_predecessor


class HousekeepingStaticTest(unittest.TestCase):
    def test_retained_inputs_and_exact_scope_reject_mutation(self):
        data = housekeeping.record()
        self.assertEqual(len(data['retained']), 278)
        for path, entry in data['retained'].items():
            raw = (housekeeping.ROOT / path).read_bytes()
            housekeeping.verify(path, raw, entry)
            for bad in (raw + b'UNREVIEWED', raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    housekeeping.verify(path, bad, entry)
            with patch.object(Path, 'read_bytes', return_value=raw + b'UNREVIEWED'):
                with self.assertRaises(AssertionError):
                    housekeeping.without_approved_paths([path])
        self.assertEqual(housekeeping.without_approved_paths(['unapproved.png']), ['unapproved.png'])

    def test_existing_changes_preserve_old_bytes_and_reject_other_changes(self):
        data = housekeeping.record()
        for path, entry in data['existing_changes'].items():
            raw = (housekeeping.ROOT / path).read_bytes()
            if path == 'tests/current_preservation.py':
                # Verify complete amended and original identities, then retain
                # every original Stage 2A assertion and immutable receipt below.
                raw = stage2a_helper_predecessor(path, raw)
            housekeeping.verify(path, raw, entry)
            before = housekeeping.historical_input(path, raw)
            self.assertNotEqual(raw.replace(b'\r\n', b'\n'), before.replace(b'\r\n', b'\n'))
            for bad in (raw + b'UNREVIEWED', raw[1:], raw + raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    housekeeping.historical_input(path, bad)

    def test_formatting_exceptions_are_exact_and_hash_guarded(self):
        data = housekeeping.record()
        for path, entry in data['formatting_policy'].items():
            housekeeping.verify(path, (housekeeping.ROOT / path).read_bytes(), entry)
        rules = (housekeeping.ROOT / 'artifacts/.gitattributes').read_text().splitlines()
        for line in rules:
            if not line or line.startswith('#') or line == '* -text':
                continue
            path, rule = line.split()
            self.assertFalse(any(c in path for c in '*?[]'))
            relative = 'artifacts/' + path
            self.assertIn(relative, data['retained'])
            self.assertIn(rule, ('whitespace=cr-at-eol', 'whitespace=cr-at-eol,-blank-at-eol'))
            if rule.endswith(',-blank-at-eol'):
                self.assertEqual(relative, 'artifacts/evidence/pr98-static-review-1212f80a46314248825c2498e5439cb1.md')
            raw = (housekeeping.ROOT / relative).read_bytes()
            housekeeping.verify(relative, raw, data['retained'][relative])
            with self.assertRaises(AssertionError):
                housekeeping.verify(relative, raw + b'new whitespace \n', data['retained'][relative])

    def test_disposition_integrity_and_deferred_files_are_preserved(self):
        data = housekeeping.record()
        self.assertEqual(len(data['deferred_publication']), 4)
        self.assertEqual(len(data['deferred_archives']), 1)
        self.assertEqual(len(data['deletions']), 2203)
        protected = data['deferred_publication'] | data['deferred_archives']
        self.assertFalse(set(protected) & set(data['deletions']))
        self.assertFalse(set(protected) & set(data['retained']))
        for path, entry in (protected | data['deletions']).items():
            # Local-only material is optional on fresh clones; existing files are immutable.
            location = housekeeping.ROOT / path
            if location.exists():
                housekeeping.verify(path, location.read_bytes(), entry)
        with patch.object(Path, 'read_bytes', return_value=b'{}'):
            with self.assertRaises(AssertionError):
                housekeeping.record()

    def test_csv_keep_policy_and_artifacts_are_outside_gameplay(self):
        data = housekeeping.record()
        for path, entry in data['import_policy'].items():
            raw = (housekeeping.ROOT / path).read_bytes()
            housekeeping.verify(path, raw, entry)
            self.assertEqual(raw.replace(b'\r\n', b'\n'), b'[remap]\n\nimporter="keep"\n')
        self.assertTrue((housekeeping.ROOT / 'artifacts/.gdignore').is_file())
        for path in (housekeeping.ROOT / 'scenes').rglob('*.gd'):
            self.assertNotIn('res://artifacts/', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
