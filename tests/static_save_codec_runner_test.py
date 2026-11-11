"""Preparation-only runner contracts. Never import project code or launch Godot."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'c048787628843719f693ae0116458242d41b0ead'
RUNNER = (ROOT / 'tools/run-save-codec-tests.ps1').read_text(encoding='utf-8')


def function(name):
    return re.search(rf'^function {name}\b.*?(?=^function |^if \(\$MyInvocation|\Z)',
                     RUNNER, re.M | re.S)[0]


class SaveCodecRunnerStaticTests(unittest.TestCase):
    def test_gate_is_unconditional_and_has_no_input(self):
        gate = function('Assert-CodecAuthorization')
        self.assertIn("throw 'AUTHORIZATION_DENIED", gate)
        for forbidden in ('param(', '$env:', 'Test-Path', 'if (', 'return', 'Get-Content'):
            self.assertNotIn(forbidden, gate)
        for name in ('Invoke-CodecAuthorizedRun', 'New-CodecStage', 'Invoke-CodecEnginePhase'):
            executable = function(name).split('{', 1)[1].lstrip()
            self.assertTrue(executable.startswith('Assert-CodecAuthorization'), name)
        self.assertLess(function('Invoke-SaveCodecTests').index('Assert-CodecAuthorization'),
                        function('Invoke-SaveCodecTests').index('Invoke-CodecAuthorizedRun'))
        self.assertIn("$codecInvocationMode = $Mode\n. ", RUNNER)
        self.assertIn("[string]$Mode = 'Run'", RUNNER)

    def test_exact_reviewed_input_hashes_and_minimal_template(self):
        inventory = re.findall(r"Source = '([^']+)'; Path = '([^']+)'; Sha256 = '([0-9A-F]{64})'", RUNNER)
        self.assertEqual(len(inventory), 3)
        self.assertEqual([item[1] for item in inventory],
                         ['project.godot', 'persistence/save_file_codec.gd', 'tests/save_file_codec_test.gd'])
        for source, _, pin in inventory:
            raw = (ROOT / source).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(hashlib.sha256(raw).hexdigest().upper(), pin, source)
        template = (ROOT / inventory[0][0]).read_text(encoding='utf-8')
        self.assertIn('config/custom_user_dir_name="TLWH-codec-__STAGE_ID__"', template)
        for forbidden in ('[autoload]', 'run/main_scene', 'res://', '[display]', '[input]'):
            self.assertNotIn(forbidden, template)

    def test_existing_permissions_runner_and_codec_bytes_unchanged(self):
        for path in ('AGENTS.md', 'tools/run-local-tests.ps1', 'tests/local_runner_fixture_test.ps1',
                     'persistence/save_file_codec.gd', 'tests/save_file_codec_test.gd'):
            before = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
            after = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(before, after, path)

    def test_fixed_budget_sequence_and_rechecks(self):
        static = function('Invoke-CodecStatic')
        self.assertIn('-Seconds 600', static)
        self.assertIn("'static_*test.py'", static)
        self.assertIn('Actual Python static suite did not PASS.', static)
        phase = function('Invoke-CodecEnginePhase')
        markers = ['Assert-CodecAuthorization', 'Assert-CodecSnapshot', 'Assert-CodecStage',
                   'Assert-PinnedEngine', 'Invoke-BoundedProcess']
        positions = [phase.index(marker) for marker in markers]
        self.assertEqual(positions, sorted(positions))
        plan = function('Get-CodecCommandPlan')
        self.assertIn('@(\'Import\', \'Codec\')', plan)
        self.assertIn("'res://tests/save_file_codec_test.gd'", plan)
        self.assertNotIn('Invoke-BoundedProcess', plan)
        self.assertNotIn('New-Item', plan)
        sequence = function('Invoke-CodecAuthorizedRun')
        self.assertEqual(sequence.count('Invoke-CodecEnginePhase '), 1)
        self.assertIn("throw 'Codec engine phase failed; no retry.'", sequence)
        self.assertLess(sequence.index('Invoke-CodecStatic'), sequence.index('New-CodecStage'))

    def test_documentation_keeps_activation_separate(self):
        doc = (ROOT / 'docs/SAVE_CODEC_RUNNER.md').read_text(encoding='utf-8')
        for term in ('NOT RUN — OWNER AUTHORIZATION REQUIRED', '600 seconds', '335', '1,048,576',
                     '4,096', 'c048787', 'codex/m5-sav-codec', 'does not authorize execution'):
            self.assertIn(term, doc)


if __name__ == '__main__':
    unittest.main()
