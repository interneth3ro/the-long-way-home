"""Default-selection and exact production-diff contracts; no Godot execution."""
import hashlib
import json
import re
from pathlib import Path
import subprocess
import unittest

from static_illustrated_exterior_test import body

ROOT = Path(__file__).resolve().parents[1]
BASE = 'e5db8040d38bfd6b1ddb584d636af01052806b7c'
MERGED = '27d14a3773f9f3cb047957ed7e648661e74c77fa'
UID_SHA256 = {
    'scenes/experiments/terrain_stage3b/continuous.gdshader.uid':
        '1950da4e6f05abd23939f5acedfc59ce040ee76a62243e35cc5430f939a096c7',
    'scenes/experiments/terrain_stage3b/lab.gd.uid':
        'cc6e7f490bf329c47bb7000808ea8874c01b513f36721ac890b593ec93f786c8',
    'scenes/world/continuous_terrain.gdshader.uid':
        '4eb706153729ce2e89faa4591074220bed63f337f836cc1d8c28683e9dc13a17',
    'scenes/world/continuous_terrain_metadata.gd.uid':
        'c2943c83c21a28d729fd4894eed779b774ab3ad33a9111b59d644fc21f9d2bcb',
    'scenes/world/continuous_terrain_presenter.gd.uid':
        '5bd1b11db76a5a53450ffabdc9c8307cf848dbaae50fc5a8d4822249ef36a075',
}
ADDED = {'tests/static_terrain_stage3d_test.py',
         'docs/experiments/terrain_stage3d_default.md'}
MODIFIED = {'scenes/world/planet_exterior.gd',
            'tests/static_terrain_stage3c_test.py', 'tests/static_ground_publication_test.py',
            'tests/static_illustrated_exterior_test.py',
            'README.md', 'docs/ILLUSTRATED_EXTERIOR.md',
            'docs/experiments/terrain_stage3_architecture_decisions.md'}


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True)


class Stage3DTest(unittest.TestCase):
    def test_historical_pr145_exact_scope(self):
        # Immutable PR #145 inventory, independent of later development/F5 metadata.
        inventory = {p: s for s, p in (line.split('\t') for line in
                     git('diff', '--name-status', BASE, MERGED, '--').splitlines())}
        self.assertEqual(inventory, {**dict.fromkeys(ADDED, 'A'), **dict.fromkeys(MODIFIED, 'M')})

    def test_current_reviewed_metadata_is_tracked_and_byte_preserved(self):
        raw_receipt = (ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw_receipt).hexdigest(),
                         '8eb39435fef15561e7024bdc0cc340a309acacbcf58e870f1e0eff0ea3a521a7')
        receipt = json.loads(raw_receipt)
        self.assertEqual(len(receipt['protected_sidecars']), 15)
        expected = {p: e['sha256'] for p, e in receipt['protected_sidecars'].items()}
        expected.update(UID_SHA256)
        self.assertEqual(len(expected), 20)
        tracked = set(git('ls-files').splitlines())
        self.assertLessEqual(set(expected), tracked)
        for path, digest in expected.items():
            with self.subTest(path=path):
                raw = (ROOT/path).read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
                indexed = subprocess.check_output(['git', 'show', ':'+path], cwd=ROOT)
                self.assertEqual(indexed, raw)
                attrs = git('check-attr', '-z', 'text', 'filter', 'working-tree-encoding',
                            '--', path).split('\0')[2::3]
                self.assertEqual(attrs, ['unset', 'unspecified', 'unspecified'])
                checkout = subprocess.check_output(
                    ['git', 'cat-file', '--filters', '--path='+path, ':'+path], cwd=ROOT)
                self.assertEqual(checkout, raw)
        # Reviewed identities must not alias another tracked resource.
        owners = {}
        for path in sorted(tracked):
            if path.endswith(('.import', '.uid')):
                for uid in set(re.findall(rb'uid://[a-z0-9]+', (ROOT/path).read_bytes())):
                    owners.setdefault(uid, set()).add(path)
        for path in expected:
            uids = re.findall(rb'uid://[a-z0-9]+', (ROOT/path).read_bytes())
            self.assertEqual(len(uids), 1, path)
            self.assertEqual(owners[uids[0]], {path})

    def test_only_script_default_changes_and_scene_inherits_it(self):
        path = 'scenes/world/planet_exterior.gd'
        before = git('show', BASE+':'+path)
        old = '@export var terrain_renderer: TerrainRenderer = TerrainRenderer.ILLUSTRATED'
        self.assertEqual(before.count(old), 1)
        current = (ROOT/path).read_text()
        self.assertEqual(current, before.replace(old, old.replace('= TerrainRenderer.ILLUSTRATED',
                                                                 '= TerrainRenderer.CONTINUOUS')))
        path = 'scenes/world/planet_exterior.tscn'
        before = git('show', BASE+':'+path)
        marker = 'script = ExtResource("2_world")\n'
        self.assertEqual(before.count(marker), 1)
        scene = (ROOT/path).read_text()
        self.assertEqual(scene, before)
        self.assertNotIn('terrain_renderer =', scene)
        # The enum keeps serialized rollback value 1; selection remains locked
        # once per fresh instance, with no automatic failure fallback.
        self.assertIn('enum TerrainRenderer { LEGACY, ILLUSTRATED, CONTINUOUS }', current)
        configure = body(current, '_configure_terrain_renderer')
        self.assertIn('if not _renderer_configured:', configure)
        self.assertIn('_effective_renderer = terrain_renderer', configure)
        self.assertIn('if _effective_renderer == TerrainRenderer.ILLUSTRATED:', configure)
        self.assertIn('_terrain_presenter.initialize()', configure)
        self.assertNotIn('_effective_renderer =', body(current, '_stop_terrain'))


if __name__ == '__main__':
    unittest.main()
