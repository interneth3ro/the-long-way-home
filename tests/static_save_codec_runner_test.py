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


def verify_codec_documentation(doc):
    """Historical PASS is not present execution permission. Inspect named sections."""
    def section(title):
        matches = re.findall(rf'^## {re.escape(title)}\n(.*?)(?=^## |\Z)', doc, re.M | re.S)
        assert len(matches) == 1, f'Missing or duplicate documentation section: {title}'
        return matches[0]

    def require(text, statement):
        assert statement in ' '.join(text.split()), f'Missing authorization/history contract: {statement}'

    historical = section('Historical M5-42 validation and restoration')
    rows = re.findall(r'^\| ([^|]+?) \| ([^|]+?) \|$', historical, re.M)
    expected = {
        'Preflight': 'PASS',
        'Static validation': '515 tests; 513 passed, two optional skips',
        'Static duration': '320.473 seconds',
        'Isolated cold import': 'PASS',
        'Godot codec runtime': '261 checks, zero failures',
        'Independent file reopening': 'PASS',
        'One-time authorization': 'CONSUMED',
    }
    for phase, result in expected.items():
        assert [value for key, value in rows if key == phase] == [result], phase
    require(historical, 'Completion: `SAVE_FILE_CODEC: PASS checks=261 failures=0`.')
    require(historical, 'This validates the standalone synthetic codec scope, not gameplay save/load or performance.')
    require(doc.split('\n## ', 1)[0],
            'The merged runner returns `PREPARED`; the only historical codec runtime grant is consumed.')
    require(historical, '**Current authorization: none for codec execution.** The grant is consumed; '
            'fresh explicit owner approval and a newly reviewed activation are required '
            'before any future import or codec runtime attempt.')
    require(historical, "M5-43 restored `return 'PREPARED'` in")
    for revision in ('8ae6e6fb040a10c7384d01f62b7b60751326c531',
                     'd544160b92bd488cd29374e505051b1cbb9e64a2'):
        require(historical, f'[`{revision}`](https://github.com/interneth3ro/the-long-way-home/commit/{revision})')
    require(historical, '`5f02aec5194413a4bc917b84edb1f151bce67394`.')
    require(historical, '`codex/m5-codec-one-time-activation`; they were not rewritten into the merged PRs.')
    require(historical, 'Preserve the consumption record, stage and retained runtime evidence. '
            'Do not delete, reset or reuse them.')
    for evidence in (
        r'D:\GameDev\Godot\TLWH-NativeStages\codec-grant-5f02aec5194413a4bc917b84edb1f151bce67394.consumed.json',
        r'D:\GameDev\Godot\TLWH-NativeStages\tlwh-codec-1994fd3302d64e2784d698ddbcadb1c6',
    ):
        require(historical, '`' + evidence + '`')

    gate = section('Entry points and inactive gate')
    require(gate, 'Default invocation and `-Mode Run` both return exit 1 and explicit '
            '`AUTHORIZATION_DENIED` **before source preflight, any process, stage, profile or evidence creation**')
    require(gate, 'Preparing, passing static tests, pushing or merging these PRs **does not authorize execution**.')
    workflow = section('Proposed fixed workflow after separate activation')
    require(workflow, '**Static bound: 600 seconds.**')
    require(workflow, 'Only after clean import may the codec phase run. Any failure stops the sequence; '
            'there are no automatic retries and at most one attempt at each command.')
    require(workflow, '| Cold import | `--headless --editor --path <fresh-stage> --quit` | 60 seconds |')
    require(workflow, '| Codec, only after clean import | `--headless --path <fresh-stage> --script '
            'res://tests/save_file_codec_test.gd` | 30 seconds |')
    require(workflow, '`D:\\GameDev\\Godot\\Standard\\Godot_v4.7.2-stable_win64.exe`')
    require(workflow, '`AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.')
    limits = section('Results, limits and evidence')
    require(limits, 'Every process has a **1,048,576-byte combined stdout/stderr limit**.')
    require(limits, 'Retained diagnostics are at most **4,096 UTF-8 bytes**, without splitting code points.')
    require(limits, 'Uncertain termination is always failure; no later engine phase is allowed.')
    require(limits, 'Codec success additionally requires exactly one completion record across both '
            'streams, as the last nonempty stdout line, matching exactly:')
    require(limits, 'SAVE_FILE_CODEC: PASS checks=<positive decimal integer> failures=0')
    procedure = section('M5-40 one-time activation procedure — not authorized now')
    require(procedure, 'Four approvals are distinct: preparation approval permits this inactive code; '
            'source activation approval permits only the reviewed transition commit; actual '
            'Godot execution approval names one invocation and scope; merge approval permits '
            'only merging a specific PR. None implies another. Do not schedule or retry runs.')
    require(procedure, '| Restored | The source returns `PREPARED` again; restoration and denial '
            'are independently verified. Tombstone and evidence remain preserved. |')
    require(procedure, 'The owner must separately authorize the exact invocation '
            '`pwsh -NoProfile -File tools/run-save-codec-tests.ps1 -Mode Run` at reviewed A.')


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
        verify_codec_documentation(doc)

    def test_documentation_rejects_incorrect_history_or_current_permission(self):
        doc = (ROOT / 'docs/SAVE_CODEC_RUNNER.md').read_text(encoding='utf-8')
        changes = (
            ('| Godot codec runtime | 261 checks, zero failures |', '| Godot codec runtime | NOT RUN |'),
            ('| One-time authorization | CONSUMED |', '| One-time authorization | AVAILABLE |'),
            ('Current authorization: none for codec execution.', 'Current authorization: execution granted.'),
            ('M5-43 restored `return \'PREPARED\'` in', 'M5-43 restored `return \'AUTHORIZED_FOREVER\'` in'),
            ('fresh explicit owner approval and a newly reviewed activation are required',
             'historical approval can be reused'),
            ('d544160b92bd488cd29374e505051b1cbb9e64a2', '0' * 40),
            ('codec-grant-5f02aec5194413a4bc917b84edb1f151bce67394.consumed.json', 'missing.json'),
            ('1,048,576-byte combined stdout/stderr limit', 'unbounded stdout/stderr'),
            ('4,096 UTF-8 bytes', 'unbounded UTF-8 bytes'),
            ('--script res://tests/save_file_codec_test.gd', '--script res://unreviewed.gd'),
            ('| 60 seconds |', '| 600 seconds |'),
            ('| 30 seconds |', '| 300 seconds |'),
            ('**Static bound: 600 seconds.**', '**Static bound: unlimited.**'),
            ('None implies another. Do not schedule or retry runs.', 'All approvals imply execution.'),
            ('Uncertain termination is always failure;', 'Uncertain termination is accepted;'),
        )
        for before, after in changes:
            self.assertIn(before, doc)
            with self.subTest(changed=before), self.assertRaises(AssertionError):
                verify_codec_documentation(doc.replace(before, after))
        duplicate = doc + '\n## Historical M5-42 validation and restoration\nUnapproved history\n'
        with self.assertRaises(AssertionError):
            verify_codec_documentation(duplicate)


if __name__ == '__main__':
    unittest.main()
