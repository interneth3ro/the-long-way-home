"""Stage 2E publication and corruption guards; no cleanup or engine execution."""
import hashlib
import json
import subprocess
import unittest

import housekeeping_preservation as housekeeping

ROOT = housekeeping.ROOT
RECORD = 'docs/experiments/repository_housekeeping_stage2e.json'
PAYLOAD = 'artifacts/evidence/pr98-validation-commit-791c48b1.payload'


def blob(ref, path):
    return subprocess.check_output(['git', 'show', ref + ':' + path], cwd=ROOT)


class Stage2EPreservationTest(unittest.TestCase):
    def test_exact_policy_amendment_preserves_historical_comparisons(self):
        self.assertEqual(set(housekeeping.STAGE2E_INPUT_SHA256), {'.gitignore', 'README.md'})
        for path in housekeeping.STAGE2E_INPUT_SHA256:
            raw = (ROOT / path).read_bytes()
            before = blob(housekeeping.STAGE2E_BASE, path)
            self.assertEqual(housekeeping.stage2e_predecessor(path, raw), before)
            # Both older comparison entrypoints must still return their own
            # exact historical bytes, including the direct Stage 2D assertion.
            self.assertEqual(housekeeping.stage2d_predecessor(path, raw),
                             blob(housekeeping.STAGE2D_BASE, path))
            self.assertEqual(housekeeping.stage2c_predecessor(path, raw),
                             blob(housekeeping.STAGE2C_BASE, path))
            for bad in (raw + b'UNAPPROVED', raw[1:], raw + raw,
                        bytes([raw[0] ^ 1]) + raw[1:]):
                self.assertEqual(housekeeping.stage2e_predecessor(path, bad), bad)
                with self.assertRaises(AssertionError):
                    housekeeping.stage2c_predecessor(path, bad)
            self.assertEqual(housekeeping.stage2e_predecessor(path + '.other', raw), raw)
        raw = (ROOT / '.gitignore').read_bytes().replace(b'\r\n', b'\n')
        before = blob(housekeeping.STAGE2E_BASE, '.gitignore')
        self.assertEqual(raw, before + b'\n# Owner-approved Stage 2E inert validation commit payload only.\n'
                         b'!/artifacts/evidence/pr98-validation-commit-791c48b1.payload\n')

    def test_publication_exception_is_exact_and_neighbors_remain_ignored(self):
        def ignored(path):
            result = subprocess.run(['git', 'check-ignore', '--no-index', '-q', '--', path], cwd=ROOT)
            self.assertIn(result.returncode, (0, 1))
            return result.returncode == 0
        self.assertFalse(ignored(PAYLOAD))
        for path in (PAYLOAD + '.other', PAYLOAD.replace('791c48b1', 'other'),
                     'artifacts/evidence/unapproved.payload', 'artifacts/tmp/unapproved.payload'):
            self.assertTrue(ignored(path), path)

    def test_validation_payload_and_reviewed_audit_remain_exact(self):
        data = json.loads((ROOT / RECORD).read_bytes())
        raw = (ROOT / PAYLOAD).read_bytes()
        self.assertEqual(len(raw), 327)
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'e3b833c248c6c629b36778febe7d286a03641cac32edaa99e53bb4c8113c64d6')
        self.assertEqual(hashlib.sha1(b'commit 327\0' + raw).hexdigest(),
                         '791c48b1c4001d9b2b52f6ecd73535417514af6b')
        self.assertEqual(blob('', PAYLOAD), raw)  # Proposed index bytes.
        self.assertEqual(data['validation_commit']['path'], PAYLOAD)
        audit = data['audit']
        self.assertEqual((ROOT / audit['path']).read_bytes(), blob(audit['source_commit'], audit['path']))


if __name__ == '__main__':
    unittest.main()
