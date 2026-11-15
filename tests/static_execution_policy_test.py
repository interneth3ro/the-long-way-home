"""Current restrictive execution contracts; inspect text, never invoke a runner.

The later LOCAL_TESTING approval note conflicts with operative AGENTS restrictions.
These tests preserve the restrictive boundary; a green test grants no permission.
"""
from pathlib import Path
import re
import subprocess
import unittest


ROOT = Path(__file__).resolve().parents[1]
REVIEWED = '4d6c7351e6c3873a2f2f02a4dd59a12569eb2a34'
ENGINE = r'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe'
ENGINE_SHA256 = 'AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424'
CONTROLS = (
    'tools/run-local-tests.ps1', 'tools/run-save-codec-tests.ps1',
    'tools/run-behavioral-tests.ps1', 'tests/behavioral/test_runner.gd',
    'tests/behavioral/smoke_test.gd', 'tests/fabricator_recipe_switching_test.gd',
    'tests/metadata_smoke_test.gd', 'tests/fixtures/metadata_smoke/inputs.json',
)


def function(source, name):
    match = re.search(r'^function '+re.escape(name)+r'\b.*?(?=^function |^if \(\$MyInvocation|\Z)',
                      source, re.M | re.S)
    assert match, 'Missing runner function: '+name
    return match[0]


def require(source, phrase):
    text = ' '.join(source.replace('**', '').replace('`', '').split())
    assert phrase in text, 'Missing restrictive contract: '+phrase


def verify_metadata_denial(runner):
    gate = function(runner, 'Assert-NativeExecutionAuthorization')
    statements = '\n'.join(line for line in gate.splitlines() if not line.lstrip().startswith('#'))
    assert "if ($Metadata) { throw 'MetadataSmoke requires separate explicit owner execution authorization; draft recipe inactive.' }" in statements
    assert not re.search(r'\breturn\b', statements), 'Metadata gate can return before denial'
    entry = function(runner, 'Invoke-LocalTests')
    authorization = "if ($RequestedMode -in @('Native', 'MetadataSmoke')) { Assert-NativeExecutionAuthorization @options }"
    assert entry.count(authorization) == 1
    # The gate must be the first statement inside try, before even prerequisites.
    assert entry.split('try {', 1)[1].lstrip().startswith(authorization)
    prefix = entry[:entry.index(authorization)]
    assert not any(call in prefix for call in ('New-InputStage', 'Invoke-BoundedProcess',
                                               'Invoke-RestrictedNativeDispatch'))


def verify_operative_policy(agents, native, codec, behavioral, dispatcher, codec_document):
    for phrase in (
        ENGINE, ENGINE_SHA256,
        'Only its fixed import and recipe-switching phases are authorized.',
        'standing authorization does not permit automatic retries or unattended runs.',
        'No executable, script, scene or argument overrides are permitted.',
        'MetadataSmoke is inactive and rejects dispatch before any process or stage.',
        'all three grants are consumed.',
        'No metadata import, execution, real-stage creation, or numerical certification is authorized',
        'authorization covers only the original world_coordinates group and its four unchanged assertions.',
        'The expanded two-group manifest is not authorized to execute',
        'Only ordinary project-profile log creation/rotation is an allowed write effect.',
        'Cache changes (including .godot/), UID/import sidecars, source, artwork, saves/settings, '
        'historical evidence, unrelated owner files and protected .godot/validation-profile/ remain excluded.',
        'Executable, manifest, assertions, command, limits or filesystem-scope changes require renewed review and authorization.',
        'Never run Godot in the source checkout or reuse a previous stage.',
        'Stop on engine/script/parse errors, assertion failure, missing/malformed completion, abnormal exit/crash, '
        'timeout, overflow, uncertain termination or changed source/stage/executable identity.',
        'Obtain explicit owner authorization before launching the Godot editor or game graphically',
        'Never reproduce a reported system lockup without explicit owner authorization.',
    ):
        require(agents, phrase)
    identity = function(native, 'Get-StandardGodotIdentity')
    assert "Path = '"+ENGINE+"'" in identity
    assert "Sha256 = '"+ENGINE_SHA256+"'" in identity
    verify_metadata_denial(native)
    commands = function(native, 'New-NativeCommandPlan')
    assert "@('--headless', '--editor', '--path', $directory, '--quit')" in commands
    assert "@('--headless', '--path', $directory, '--script', ('res://' + $test))" in commands
    assert "@('Import', 'Native')" in commands
    assert "if ($phase -eq 'Import') { 60 } else { 30 }" in commands
    assert 'MaxBytes = 1048576' in commands
    assert "'tests/fabricator_recipe_switching_test.gd'" in commands
    assert "return 'PREPARED'" in function(codec, 'Get-CodecGrantTransition')
    require(codec_document, 'The merged runner returns PREPARED; the only historical codec runtime grant is consumed.')
    require(codec_document, 'Current authorization: none for codec execution.')
    require(codec_document, 'fresh explicit owner approval and a newly reviewed activation are required')
    for marker in ('-Seconds 30 -MaxBytes 1048576 -ExcerptBytes 4096',
                   "'res://tests/behavioral/test_runner.gd'", 'Assert-PinnedEngine'):
        assert marker in behavioral
    groups = re.findall(r'\{"name": "([^"]+)", "script": preload\("res://([^"]+)"\)\}', dispatcher)
    assert groups == [('world_coordinates', 'tests/behavioral/smoke_test.gd'),
                      ('resource_generation_v2', 'tests/behavioral/resource_generation_v2_test.gd')]
    # This exact proposed manifest is preserved, not authorized by its bare-return gate.
    assert 'DO NOT RUN without separate approval' in dispatcher


class ExecutionPolicyStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sources = {p: (ROOT/p).read_text(encoding='utf-8') for p in CONTROLS}
        cls.agents = (ROOT/'AGENTS.md').read_text(encoding='utf-8')
        cls.codec_document = (ROOT/'docs/SAVE_CODEC_RUNNER.md').read_text(encoding='utf-8')

    def _verify(self, agents=None, sources=None):
        sources = self.sources if sources is None else sources
        verify_operative_policy(self.agents if agents is None else agents,
                                sources[CONTROLS[0]], sources[CONTROLS[1]],
                                sources[CONTROLS[2]], sources[CONTROLS[3]], self.codec_document)

    def test_current_restrictive_policy_and_fixed_commands(self):
        self._verify()

    def test_reviewed_runners_manifests_and_assertions_have_no_scope_drift(self):
        for path in CONTROLS:
            expected = subprocess.check_output(['git', 'show', REVIEWED+':'+path], cwd=ROOT).decode('utf-8')
            self.assertEqual(self.sources[path], expected.replace('\r\n', '\n'), path)

    def test_metadata_denial_precedes_all_staging_and_dispatch(self):
        verify_metadata_denial(self.sources[CONTROLS[0]])
        source = self.sources[CONTROLS[0]]
        for changed in (
            source.replace("if ($Metadata) { throw 'MetadataSmoke requires separate explicit owner execution authorization; draft recipe inactive.' }", 'return'),
            source.replace("if ($RequestedMode -in @('Native', 'MetadataSmoke')) { Assert-NativeExecutionAuthorization @options }", 'New-InputStage'),
        ):
            with self.assertRaises(AssertionError):
                verify_metadata_denial(changed)

    def test_policy_and_command_mutations_are_rejected(self):
        for old in ('four unchanged assertions', 'not authorized to execute',
                    'saves/settings', 'UID/import sidecars', 'automatic retries or unattended runs'):
            self.assertIn(old, self.agents)
            with self.subTest(policy=old), self.assertRaises(AssertionError):
                self._verify(agents=self.agents.replace(old, 'unreviewed scope'))
        changes = (
            (CONTROLS[0], ENGINE_SHA256, '0'*64),
            (CONTROLS[0], ENGINE, 'unreviewed.exe'),
            (CONTROLS[0], "{ 60 } else { 30 }", '{ 600 } else { 300 }'),
            (CONTROLS[0], 'MaxBytes = 1048576', 'MaxBytes = 2097152'),
            (CONTROLS[1], "return 'PREPARED'", "return 'AUTHORIZED_FOREVER'"),
            (CONTROLS[2], '-Seconds 30 -MaxBytes 1048576 -ExcerptBytes 4096', '-Seconds 300'),
            (CONTROLS[3], 'resource_generation_v2', 'unreviewed_group'),
        )
        for path, old, new in changes:
            self.assertIn(old, self.sources[path])
            changed = self.sources | {path: self.sources[path].replace(old, new)}
            with self.subTest(control=path, change=old), self.assertRaises(AssertionError):
                self._verify(sources=changed)


if __name__ == '__main__':
    unittest.main()
