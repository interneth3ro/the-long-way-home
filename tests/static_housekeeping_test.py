"""Disposition identity and corruption checks; never runs cleanup or Godot."""
from pathlib import Path
import copy
import importlib.util
import json
import marshal
import stat
import struct
import subprocess
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

import housekeeping_preservation as housekeeping


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
        data = housekeeping.verify_history()
        self.assertEqual(len(data['deferred_publication']), 4)
        self.assertEqual(len(data['deferred_archives']), 1)
        self.assertEqual(len(data['deletions']), 2203)
        protected = data['deferred_publication'] | data['deferred_archives']
        self.assertFalse(set(protected) & set(data['deletions']))
        self.assertFalse(set(protected) & set(data['retained']))
        for path, entry in protected.items():
            # Protected historical material never receives the D1 cache allowance.
            location = housekeeping.ROOT / path
            if location.exists():
                housekeeping.verify(path, location.read_bytes(), entry)
        housekeeping.verify_deletion_paths(data)
        with patch.object(Path, 'read_bytes', return_value=b'{}'):
            with self.assertRaises(AssertionError):
                housekeeping.record()

    def test_historical_records_reject_identity_scope_and_completion_mutations(self):
        raw = (housekeeping.ROOT/housekeeping.RECORD).read_bytes()
        completed = (housekeeping.ROOT/housekeeping.COMPLETION).read_bytes()
        data = json.loads(raw)
        path = next(iter(data['deletions']))
        mutations = []
        for field, value in (('sha256', '0'*64), ('bytes', 0), ('group', 'D1')):
            changed = copy.deepcopy(data)
            changed['deletions'][path][field] = value
            mutations.append(changed)
        changed = copy.deepcopy(data)
        changed['deletions']['../unreviewed'] = changed['deletions'].pop(path)
        mutations.append(changed)
        changed = copy.deepcopy(data)
        changed['deletions'].pop(path)
        mutations.append(changed)
        for number, changed in enumerate(mutations):
            with self.subTest(mutation=number), self.assertRaises(AssertionError):
                housekeeping.verify_records(json.dumps(changed).encode(), completed)
        for bad in (b'', b'{}', completed + b'changed'):
            with self.subTest(completion=bad[:20]), self.assertRaises(AssertionError):
                housekeeping.verify_records(raw, bad)

    def test_missing_git_evidence_and_broken_ancestry_reject_without_fallback(self):
        with patch.object(housekeeping.subprocess, 'check_output',
                          side_effect=subprocess.CalledProcessError(128, ['git'])), \
                self.assertRaises(AssertionError):
            housekeeping.verify_history()
        original = housekeeping.git

        def broken_parent(*args):
            return b'0'*40+b'\n' if args == ('rev-parse', housekeeping.CLEANUP+'^') else original(*args)

        with patch.object(housekeeping, 'git', side_effect=broken_parent), self.assertRaises(AssertionError):
            housekeeping.verify_history()
        read_bytes = Path.read_bytes

        def missing_completion(path):
            if path == housekeeping.ROOT/housekeeping.COMPLETION:
                raise FileNotFoundError('Missing cleanup record')
            return read_bytes(path)

        with patch.object(Path, 'read_bytes', missing_completion), self.assertRaises(FileNotFoundError):
            housekeeping.verify_history()

    def test_deferred_evidence_has_no_cache_exception(self):
        for section in ('deferred_publication', 'deferred_archives'):
            for path, entry in housekeeping.record()[section].items():
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    housekeeping.verify(path, b'corrupted protected evidence', entry)

    def test_deletion_reintroduction_is_narrow_and_untracked_only(self):
        data = housekeeping.record()
        cache = 'tests/__pycache__/current_preservation.cpython-314.pyc'
        for path, entry in data['deletions'].items():
            # Reject tracking even an absent path, or valid D1 bytes.
            with self.subTest(tracked=path), self.assertRaises(AssertionError):
                housekeeping.verify_deletion_path(path, entry, {path})
        # Exercise both Git inputs independently. Make every local target absent
        # so a failure cannot accidentally come from an unrelated cache check.
        first = next(iter(data['deletions']))
        absent = Mock()
        absent.lstat.side_effect = FileNotFoundError
        for origin in ('index', 'HEAD'):
            def tracking(*args):
                selected = (args[0] == 'ls-files') if origin == 'index' else (args[0] == 'ls-tree')
                return (first+'\n').encode() if selected else b''
            with self.subTest(origin=origin), patch.object(housekeeping, 'git', side_effect=tracking), \
                    patch.object(housekeeping, 'plain_location', return_value=absent), \
                    self.assertRaises(AssertionError):
                housekeeping.verify_deletion_paths(data)
        present = Mock()
        present.lstat.return_value = SimpleNamespace(st_mode=stat.S_IFREG)
        for group in housekeeping.DELETION_GROUPS.keys()-{'D1'}:
            path, entry = next((p, e) for p, e in data['deletions'].items() if e['group'] == group)
            with self.subTest(group=group), patch.object(housekeeping, 'plain_location', return_value=present), \
                    self.assertRaises(AssertionError):
                housekeeping.verify_deletion_path(path, entry, set())
        with self.assertRaises(AssertionError):
            housekeeping.verify_deletion_path('tests/__pycache__/unreviewed.cpython-314.pyc',
                                             data['deletions'][cache], set())
        # Existing D1 caches still require a tracked source and an ignore rule.
        with patch.object(housekeeping, 'git', return_value=b''), self.assertRaises(AssertionError):
            housekeeping.verify_deletion_path(cache, data['deletions'][cache], set())
        with patch.object(housekeeping, 'git', return_value=(cache+'\n').encode()), \
                self.assertRaises(AssertionError):
            housekeeping.verify_deletion_path(cache, data['deletions'][cache], set())

    def test_paths_reject_traversal_links_and_reparse_points(self):
        for path in ('../outside', '/outside', 'C:/outside', 'tests//cache', 'tests/./cache', 'tests\\cache'):
            with self.subTest(path=path), self.assertRaises(AssertionError):
                housekeeping.safe_relative(path)
        for info in (SimpleNamespace(st_mode=stat.S_IFLNK, st_file_attributes=0),
                     SimpleNamespace(st_mode=stat.S_IFDIR, st_file_attributes=stat.FILE_ATTRIBUTE_REPARSE_POINT)):
            with patch.object(Path, 'lstat', return_value=info), self.assertRaises(AssertionError):
                housekeeping.plain_location('tests/__pycache__/current_preservation.cpython-314.pyc')

    def test_cache_content_matches_current_or_ancestral_source_without_execution(self):
        path = housekeeping.ROOT/'tests/current_preservation.py'
        current, old = b'VALUE = 2\n', b'VALUE = 1\n'

        def cache(source, timestamp, filename=path):
            # Synthetic bytes exist only in memory, never as a cache file.
            code = compile(source, str(filename), 'exec', dont_inherit=True, optimize=0)
            return importlib.util.MAGIC_NUMBER + struct.pack('<III', 0, timestamp, len(source)) + marshal.dumps(code)

        fresh, stale = cache(current, 2), cache(old, 1)
        self.assertEqual(housekeeping.verify_cache(fresh, path, current, 2, []), 'current')
        self.assertEqual(housekeeping.verify_cache(stale, path, current, 2, [old]), 'stale')
        malformed = (
            fresh[:15], b'BAD!'+fresh[4:], fresh[:4]+struct.pack('<I', 4)+fresh[8:],
            fresh[:16]+b'invalid marshal', fresh+b'extra payload', fresh[:16]+marshal.dumps(42),
            cache(b'raise RuntimeError("MUST NEVER EXECUTE")\n', 1),
            cache(current, 1, housekeeping.ROOT/'unrelated.py'),
            fresh[:16]+stale[16:],  # Forged current header around old code.
        )
        for number, raw in enumerate(malformed):
            with self.subTest(mutation=number), self.assertRaises(AssertionError):
                housekeeping.verify_cache(raw, path, current, 2, [old])
        with self.assertRaises(AssertionError):
            housekeeping.verify_cache(stale, path, current, 2, [])

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
