"""Default-selection and exact production-diff contracts; no Godot execution."""
import json
from pathlib import Path
import subprocess
import unittest

from static_illustrated_exterior_test import body

ROOT = Path(__file__).resolve().parents[1]
BASE = 'e5db8040d38bfd6b1ddb584d636af01052806b7c'
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
    def test_exact_scope_preserves_all_other_tracked_inputs(self):
        inventory = {p: s for s, p in (line.split('\t') for line in
                     git('diff', '--name-status', BASE, '--').splitlines())}
        untracked = set(git('ls-files', '--others', '--exclude-standard').splitlines())
        receipt = json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
        self.assertEqual(untracked - ADDED, set(receipt['protected_sidecars']))
        inventory.update(dict.fromkeys(untracked & ADDED, 'A'))
        self.assertEqual(inventory, {**dict.fromkeys(ADDED, 'A'), **dict.fromkeys(MODIFIED, 'M')})

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
