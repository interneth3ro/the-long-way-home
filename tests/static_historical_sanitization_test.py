"""Historical derivative integrity checks; never execute evidence or Godot."""
import ast
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

import housekeeping_preservation as housekeeping

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/experiments/repository_housekeeping_stage2c.json'
RECORD_SHA256 = '4c3675f8a27cbf776a2068f393fa299bc16de809a5e075b8944074096726afa9'
ABSOLUTE_PATH = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]:[\\/]')
SECRET = re.compile(
    r'-----BEGIN .*PRIVATE KEY-----|\b(?:gh[pousr]_[A-Za-z0-9]{20,}'
    r'|github_pat_[A-Za-z0-9_]{20,}|(?:AKIA|ASIA)[A-Z0-9]{16})'
    r'|bearer\s+[A-Za-z0-9_.-]{15,}', re.I)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def record():
    raw = (ROOT / RECORD).read_bytes().replace(b'\r\n', b'\n')
    if digest(raw) != RECORD_SHA256:
        raise AssertionError('Changed Stage 2C disposition')
    return json.loads(raw)


class HistoricalSanitizationTest(unittest.TestCase):
    def test_retained_metadata_checks_exact_git_bytes_and_checkout_conversion(self):
        path = 'assets/audio/exterior_hatch/hatch_close.wav.import'
        entry = housekeeping.record()['retained'][path]
        canonical = subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT)
        self.assertEqual(digest(canonical), entry['sha256'])
        checkout = canonical.replace(b'\n', b'\r\n')
        git_bytes = {'canonical': canonical, 'checkout': checkout}

        def git_output(args, cwd):
            self.assertEqual(cwd, ROOT)
            if args[1] == 'check-attr':
                return (path.encode() + b'\0filter\0unspecified\0'
                        + path.encode() + b'\0working-tree-encoding\0unspecified\0')
            if args == ['git', 'show', ':' + path]:
                return git_bytes['canonical']
            self.assertEqual(args, ['git', 'cat-file', '--filters', '--path=' + path, ':' + path])
            return git_bytes['checkout']

        with patch.object(housekeeping.subprocess, 'check_output', side_effect=git_output):
            housekeeping.verify(path, checkout, entry)
            housekeeping.verify(path, canonical, entry)
            for changed in (checkout + b'CHANGED', checkout[1:],
                            checkout.replace(b'\r\n', b'\r\r\n')):
                with self.assertRaises(AssertionError):
                    housekeeping.verify(path, changed, entry)
            # Even a matching checkout cannot rescue a changed canonical blob.
            git_bytes['canonical'] = canonical + b'CHANGED'
            git_bytes['checkout'] = checkout + b'CHANGED'
            with self.assertRaises(AssertionError):
                housekeeping.verify(path, git_bytes['checkout'], entry)
            # Unlisted metadata still protects raw working bytes exactly.
            with patch.object(housekeeping, 'record', return_value={'retained': {}}):
                with self.assertRaises(AssertionError):
                    housekeeping.verify(path, checkout, entry)

    def test_derivatives_preserve_source_structure_and_publication_scope(self):
        data = record()
        self.assertEqual(len(data['artifacts']), 4)
        for entry in data['artifacts']:
            path = entry['derivative']
            raw = (ROOT / path).read_bytes()
            self.assertEqual(len(raw), entry['derivative_bytes'])
            self.assertEqual(digest(raw), entry['derivative_sha256'])
            text = raw.decode('utf-8')
            self.assertIsNone(ABSOLUTE_PATH.search(text))
            self.assertIsNone(SECRET.search(text))
            self.assertIn('historical', text.splitlines()[0])
            ignored = subprocess.run(['git', 'check-ignore', '--no-index', '-q', path], cwd=ROOT)
            self.assertEqual(ignored.returncode, 1)
            if path.endswith('.py'):
                tree = ast.parse(text)
                self.assertEqual(digest(ast.dump(tree, include_attributes=False).encode()),
                                 entry['normalized_ast_sha256'])
                package = next(node for node in tree.body if isinstance(node, ast.Assign)
                               and any(isinstance(t, ast.Name) and t.id == 'PACKAGE'
                                       for t in node.targets))
                self.assertEqual(package.value.args[0].value, '<HISTORICAL_REFERENCE_PACKAGE_ZIP>')
                original = ROOT / entry['original']
                if original.exists():
                    old = ast.parse(original.read_text())
                    old_package = next(node for node in old.body if isinstance(node, ast.Assign)
                                       and any(isinstance(t, ast.Name) and t.id == 'PACKAGE'
                                               for t in node.targets))
                    old_package.value.args[0].value = package.value.args[0].value
                    self.assertEqual(ast.dump(old), ast.dump(tree))
            else:
                expected = entry['historical_plan']
                start = text.rfind('{', 0, text.index('"Purpose"'))
                plan = json.JSONDecoder().raw_decode(text[start:])[0]
                self.assertEqual(plan['Revision'], expected['revision'])
                self.assertEqual(len(plan['Controls']), expected['control_count'])
                self.assertEqual(len(plan['Inputs']), expected['input_count'])
                self.assertEqual(plan['Authorization'], 'INACTIVE')
                self.assertEqual(plan['Routine'], 'INACTIVE')
                self.assertIn(expected['godot_resource_script'], text)
                self.assertEqual(text.splitlines()[-1], expected['summary'])
                self.assertIn('Ran 43 tests', text)
        self.assertIsNone(ABSOLUTE_PATH.search(json.dumps(data)))
        self.assertIsNone(SECRET.search(json.dumps(data)))

    def test_original_identities_and_historical_dependencies_stay_immutable(self):
        data = record()
        original_data = housekeeping.record()
        originals = original_data['deferred_publication'] | original_data['deferred_archives']
        for entry in data['artifacts'] + [data['archive']]:
            self.assertEqual(entry['sha256'], originals[entry['original']]['sha256'])
            self.assertEqual(entry['bytes'], originals[entry['original']]['bytes'])
        for path, expected in data['historical_dependency_sha256'].items():
            before = subprocess.check_output(['git', 'show', data['baseline'] + ':' + path], cwd=ROOT)
            self.assertEqual(digest(before), expected)
            # Permit only checkout line-ending conversion, never content changes.
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'),
                             before.replace(b'\r\n', b'\n'))


    def test_completion_receipt_records_only_the_authorized_deletions(self):
        data = record()
        path = ROOT / data['completion_record']
        if not path.exists():
            return  # Preservation commit intentionally precedes deletion and receipt.
        completed = json.loads(path.read_text())
        expected = {e['original']: e for e in data['artifacts'] + [data['archive']]}
        self.assertEqual({e['path'] for e in completed['deleted']}, set(expected))
        self.assertEqual(completed['deleted_files'], 5)
        self.assertEqual(completed['deleted_payload_bytes'], sum(e['bytes'] for e in expected.values()))
        for entry in completed['deleted']:
            self.assertEqual(entry['sha256'], expected[entry['path']]['sha256'])
            self.assertEqual(entry['bytes'], expected[entry['path']]['bytes'])
            self.assertFalse((ROOT / entry['path']).exists())
        commit = completed['preservation_commit']
        for entry in data['artifacts']:
            blob = subprocess.check_output(['git', 'show', commit + ':' + entry['derivative']], cwd=ROOT)
            self.assertEqual(digest(blob), entry['derivative_sha256'])


if __name__ == '__main__':
    unittest.main()
