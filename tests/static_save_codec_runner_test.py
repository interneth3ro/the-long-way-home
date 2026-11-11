"""Preparation-only runner contracts. Never import project code or launch Godot."""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = 'c048787628843719f693ae0116458242d41b0ead'
RUNNER = (ROOT / 'tools/run-save-codec-tests.ps1').read_text(encoding='utf-8')


def verify_codec_runner_text(text):
    """Exact single-path historical exception, never an execution permission."""
    normalized, count = re.subn(
        r"(?m)^    return '(?:PREPARED|AUTHORIZED_ONCE:[0-9a-f]{40})'$",
        "    return 'PREPARED'", text)
    pins = {
        # Reviewed PR #173 runner, and the M5-40 prepared amendment respectively.
        '7c5d8426c75df2573dcd9d40fe3be10ec9b800900d620b21aa877720f5af3ad3',
        'f506b5ac5fbb06fa0b17453634ba57d6e04702a5d650dffae7d4038d380ee740',
    }
    if count > 1 or hashlib.sha256(normalized.encode('utf-8')).hexdigest() not in pins:
        raise AssertionError('Dedicated codec runner differs from exact reviewed/prepared preservation pins')
    return {'tools/run-save-codec-tests.ps1'}


def verified_codec_runner_paths():
    raw = (ROOT / 'tools/run-save-codec-tests.ps1').read_bytes().replace(b'\r\n', b'\n')
    return verify_codec_runner_text(raw.decode('utf-8'))


def function(name):
    return re.search(rf'^function {name}\b.*?(?=^function |^if \(\$MyInvocation|\Z)',
                     RUNNER, re.M | re.S)[0]


class SaveCodecRunnerStaticTests(unittest.TestCase):
    def test_historical_runner_exception_is_hash_pinned_and_rejects_other_changes(self):
        self.assertEqual(verified_codec_runner_paths(), {'tools/run-save-codec-tests.ps1'})
        old = subprocess.check_output(['git', 'show',
            'a2206096be202c8b3b0341e96039fb0f5bb815a0:tools/run-save-codec-tests.ps1'], cwd=ROOT).decode('utf-8')
        self.assertEqual(verify_codec_runner_text(old), {'tools/run-save-codec-tests.ps1'})
        active = re.sub(r"(?m)^    return 'PREPARED'$", "    return 'AUTHORIZED_ONCE:" + 'b' * 40 + "'", RUNNER)
        self.assertEqual(verify_codec_runner_text(active), {'tools/run-save-codec-tests.ps1'})
        for changed in (RUNNER + '\n# unreviewed', RUNNER.replace('1048576', '2097152'),
                        RUNNER.replace('res://tests/save_file_codec_test.gd', 'res://other.gd'),
                        RUNNER.replace("return 'PREPARED'", "return 'AUTHORIZED_FOREVER'")):
            with self.assertRaises(AssertionError):
                verify_codec_runner_text(changed)

    def test_source_transition_is_literal_and_only_owned_consumed_context_can_continue(self):
        transition = function('Get-CodecGrantTransition')
        self.assertRegex(transition, r"\Afunction Get-CodecGrantTransition \{\n    return '(?:PREPARED|AUTHORIZED_ONCE:[0-9a-f]{40})'\n\}\n\n\Z")
        for forbidden in ('param(', '$env:', 'Test-Path', 'Get-Content'):
            self.assertNotIn(forbidden, transition)
        begin = function('Start-CodecInvocation')
        self.assertLess(begin.index('Get-CodecGrantedRevision'), begin.index('Test-Path'))
        self.assertIn('[IO.FileMode]::CreateNew', begin)
        self.assertIn('[IO.FileShare]::None', begin)
        self.assertIn('$stream.Flush($true)', begin)
        self.assertLess(begin.index('$stream.Flush($true)'), begin.index('$script:CodecGrantContext ='))
        gate = function('Assert-CodecAuthorization')
        for proof in ('Get-CodecGrantedRevision', 'Get-CodecGrantBinding', 'Stream.CanRead',
                      'Stream.CanWrite', 'RecordSha256', 'NextStep'):
            self.assertIn(proof, gate)
        for name in ('Invoke-CodecAuthorizedRun', 'New-CodecStage', 'Invoke-CodecEnginePhase'):
            executable = function(name).split('{', 1)[1].lstrip()
            self.assertTrue(executable.startswith('Assert-CodecAuthorization'), name)
        self.assertLess(function('Invoke-SaveCodecTests').index('Start-CodecInvocation'),
                        function('Invoke-SaveCodecTests').index('Invoke-CodecAuthorizedRun'))
        self.assertIn('finally { Close-CodecInvocation }', function('Invoke-SaveCodecTests'))
        self.assertIn("$codecInvocationMode = $Mode\n. ", RUNNER)
        self.assertIn("[string]$Mode = 'Run'", RUNNER)

    def test_activation_binds_exact_parent_tree_and_normalized_one_line(self):
        binding = function('Get-CodecGrantBinding')
        for marker in ("'rev-list', '--parents'", '$parents.Count -ne 2',
                       "'diff', '--name-only'", "'show'", '$current.Replace($activeLine, $inactiveLine) -cne $prepared'):
            self.assertIn(marker, binding)
        self.assertIn('Get-CodecSnapshot $source', binding)
        self.assertIn('codec-grant-$ReviewedRevision.consumed.json', function('Get-CodecConsumptionPath'))
        for name in ('Start-CodecInvocation', 'Close-CodecInvocation'):
            for forbidden in ('Remove-Item', 'Delete(', 'Set-Content', 'WriteAllText'):
                self.assertNotIn(forbidden, function(name))

    def test_reviewed_workflow_bodies_change_only_at_authorization_checkpoints(self):
        baseline = subprocess.check_output(['git', 'show',
            'a2206096be202c8b3b0341e96039fb0f5bb815a0:tools/run-save-codec-tests.ps1'], cwd=ROOT).decode('utf-8')
        names = re.findall(r'^function ([\w-]+)', baseline, re.M)
        for name in names:
            if name in ('Assert-CodecAuthorization', 'Invoke-SaveCodecTests'):
                continue
            before = re.search(rf'^function {name}\b.*?(?=^function |^if \(\$MyInvocation|\Z)',
                               baseline, re.M | re.S)[0]
            after = function(name)
            after = after.replace('Assert-CodecAuthorization -Step Stage', 'Assert-CodecAuthorization')
            after = after.replace('Assert-CodecAuthorization -Step Dispatch', 'Assert-CodecAuthorization')
            after = after.replace('Assert-CodecAuthorization -Step $Phase', 'Assert-CodecAuthorization')
            after = after.replace('            Complete-CodecAuthorizationPhase $command.Phase\n', '')
            self.assertEqual(before, after, name)

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
