"""Source contracts only. No Godot, gameplay or performance execution."""
import re
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REVIEWED = '6d17aabd7b9f9c2b30ccc4359108abc892d3127b'


def read(path):
    return (ROOT / path).read_text(encoding='utf-8')


def functions(source):
    return dict(re.findall(r'^func (\w+)(\(.*?)(?=^func |\Z)', source, re.M | re.S))


class ConstructionHighlightTests(unittest.TestCase):
    def test_projection_is_bounded_copied_published_and_context_checked(self):
        source = read('scenes/world/resource_presenter_v2.gd')
        f = functions(source)
        for guard in ('is_inside_tree()', 'not _exiting', '_world != null', 'is_complete(token)'):
            self.assertIn(guard, f['highlight_view_is_current'])
        page = f['highlight_page']
        for text in ('not highlight_view_is_current(token)', 'offset < 0', 'offset > _highlight_ids.size()',
                     'mini(offset + 16, _highlight_ids.size())', 'range(offset, end)',
                     'is_deposit_presented(identity, _world, _world_token)',
                     'registration.logical_bounds', '_loaded_chunks.has(Vector2i(x, y))'):
            self.assertIn(text, page)
        for forbidden in ('query_resource', '.region(', '_texture(', 'load(', 'ticket', 'duplicate('):
            self.assertNotIn(forbidden, page)
        self.assertIn('entries.append({"deposit_id": identity', page)
        self.assertNotIn('entries.append(registration)', page)

    def test_existing_presenter_behavior_and_budgets_preserved(self):
        path = 'scenes/world/resource_presenter_v2.gd'
        before = subprocess.check_output(['git', 'show', REVIEWED + ':' + path], cwd=ROOT).decode()
        current = read(path).split('\n\n# Visual feedback only.', 1)[0]
        for addition in ('var _highlight_ids: Array = [] # Completed visual index survives supported detachment.\n',
                         '\t_highlight_ids = _ids.duplicate()\n', '\t\t_highlight_ids.clear()\n'):
            self.assertEqual(current.count(addition), 1)
            current = current.replace(addition, '', 1)
        self.assertEqual(current, before)

    def test_selection_changes_visibility_without_rebuilding(self):
        f = functions(read('scenes/world/planet_exterior.gd'))
        self.assertNotIn('_clear_highlights', f['set_construction_definition'])
        self.assertIn('_update_highlight_visibility()', f['set_construction_definition'])
        for name in ('set_construction_definition', '_update_highlight_visibility', '_clear_highlights'):
            for forbidden in ('Polygon2D.new', '.free()', 'query_resource', '.region('):
                self.assertNotIn(forbidden, f[name])
        refresh = f['_refresh_highlights']
        for text in ('highlight_page(_resource_token, _highlight_cursor)',
                     'if not _highlight_nodes.has(identity)', '_highlight_nodes[identity] = highlight',
                     'range(HIGHLIGHT_BUDGET)', '_highlight_seen.has(identity)'):
            self.assertIn(text, refresh)
        for forbidden in ('query_resource', '.region(', 'for coordinate', '_state.'):
            self.assertNotIn(forbidden, refresh)
        self.assertEqual(refresh.count('range(HIGHLIGHT_BUDGET)'), 2)
        self.assertLess(refresh.index('highlight.free()'), refresh.index('Polygon2D.new()'))
        self.assertIn('if not _highlight_ready:', f['_flush_highlights'])
        self.assertIn('_highlight_token != _resource_token', f['_flush_highlights'])
        self.assertIn('_clear_highlights()', f['_stop_terrain'])

    def test_unrelated_exterior_and_all_authority_remain_identical(self):
        path = 'scenes/world/planet_exterior.gd'
        before = subprocess.check_output(['git', 'show', REVIEWED + ':' + path], cwd=ROOT).decode()
        current = read(path)
        allowed = {'set_construction_definition', '_clear_highlights', '_flush_highlights',
                   '_refresh_highlights', '_initialize_world', '_stop_terrain'}
        old, new = functions(before), functions(current)
        self.assertEqual(set(new) - set(old), {'_update_highlight_visibility'})
        for name in old.keys() - allowed:
            self.assertEqual(old[name], new[name], name)
        for name, addition in (('_initialize_world', '\t\t_highlights.hide()\n'),
                               ('_stop_terrain', '\t\t_clear_highlights()\n')):
            self.assertEqual(new[name].replace(addition, '', 1), old[name])
        for path in ('construction/construction_controller.gd', 'construction/placement_rules.gd',
                     'scenes/world/planet_world_state.gd', 'scenes/world/ordinary_resource_generator.gd',
                     'scenes/world/starting_resource_generator.gd', 'scenes/world/resource_presentation_catalog.gd'):
            previous = subprocess.check_output(['git', 'show', REVIEWED + ':' + path], cwd=ROOT).decode()
            self.assertEqual(read(path), previous, path)

    def test_behavioral_regressions_authored_without_dispatch_changes(self):
        behavior = read('tests/cuprite_presentation_lifecycle_test.gd')
        for label in ('highlight selection performs no generation', 'reselection retains highlight node identity',
                      'three resource highlights and crossing anchor', 'highlight projection returns independent data',
                      'streaming retires highlight nodes', 'highlight reconciliation budget',
                      'retired context rejects highlight projection', 'detachment rejects highlight projection'):
            self.assertIn(label, behavior)
        for path in ('tools/run-behavioral-tests.ps1', 'tests/behavioral/test_runner.gd'):
            before = subprocess.check_output(['git', 'show', REVIEWED + ':' + path], cwd=ROOT).decode()
            self.assertEqual(read(path), before)
