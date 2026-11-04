"""Source contracts and finite authority models; no GDScript or Godot execution.

Models specify admission, not pixels, engine parsing, scheduling or performance.
Existing presenter/transition suites exercise their other source-bound contracts.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import subprocess
import unittest

from static_illustrated_exterior_test import body, window

ROOT = Path(__file__).resolve().parents[1]
BASE = '6a4a24b0f5d2b251150153aebd26801318f78ec9'
E = (ROOT/'scenes/world/planet_exterior.gd').read_text()
P = (ROOT/'scenes/world/illustrated_terrain_presenter.gd').read_text()


@dataclass(frozen=True)
class Ground:
    state: int = 1
    seed: int = 26026
    revision: int = 0
    generator: int = 2
    presenter: int = 3
    layer: int = 4
    chunk: int = 5
    token: int = 1


class Authority:
    """Independent oracle: retained pixels never confer authority by themselves."""
    def __init__(self):
        self.context = Ground()
        self.high = 0
        self.active = {}
        self.pixels = {}
        self.receipts = {}
        self.attached = True
        self.flushed = True
        self.arrival = 1
        self.cancelled = False

    def begin(self, c, token):
        if token <= self.high:
            return False
        self.high = token
        self.active[c] = (token, False)
        self.receipts.pop(c, None)
        return True

    def publish(self, c, token, valid=True):
        if self.active.get(c) != (token, False) or not valid:
            return False
        self.pixels[c] = token
        self.active[c] = (token, True)
        self.receipts[c] = replace(self.context, token=token)
        return True

    def retire(self, c, token):
        if c not in self.active or self.active[c][0] != token:
            return False
        del self.active[c]
        self.receipts.pop(c, None)
        self.pixels.pop(c, None)
        return True

    def ready(self, arrival, center=(0, 0), radius=2):
        return (arrival == self.arrival and not self.cancelled and self.attached
                and self.flushed and all(
                    c in self.receipts and self.active.get(c) == (self.receipts[c].token, True)
                    and self.receipts[c] == replace(self.context, token=self.receipts[c].token)
                    for c in window(center, radius)))


def filled():
    a = Authority()
    for token, c in enumerate(sorted(window((0, 0), 2)), 1):
        assert a.begin(c, token) and a.publish(c, token)
    return a


class GroundPublicationTest(unittest.TestCase):
    def test_publication_validity_is_guarded_before_layer_access(self):
        evidence = body(P, 'publication')
        current = body(P, '_current')
        guard = body(P, '_guard')
        self.assertLess(evidence.index('not _current(coordinate, generation_token, false).ok'),
                        evidence.index('_terrain.is_inside_tree()'))
        self.assertIn('if _lookup == null or not is_instance_valid(_terrain):\n'
                      '\t\treturn _result(false, &"uninitialized"', guard)
        self.assertIn('var guard := _guard(coordinate, token)\n'
                      '\tif not guard.ok:\n\t\treturn guard', current)
        self.assertLess(current.index('if not guard.ok:'), current.index('_matches('))
        # No suspension or external callback can invalidate the layer between
        # the shared guard and the first layer query. Detach keeps nodes alive.
        for method in (evidence, current, guard):
            for forbidden in ('await ', '.call(', '.emit(', 'call_deferred('):
                self.assertNotIn(forbidden, method)
        self.assertEqual(P.count('_terrain = layer'), 1)

    def test_unchanged_neighborhood_fails_closed_without_receipt_retry(self):
        neighborhood = body(E, '_update_neighborhood')
        early = ('if center == _center and _state.revision == _revision \\\n'
                 '\t\t\tand _ferrite_presenter.matches_context(_state):\n\t\treturn')
        self.assertIn(early, neighborhood)
        self.assertLess(neighborhood.index(early), neighborhood.index('_pending.clear()'))
        self.assertLess(neighborhood.index('_pending.clear()'),
                        neighborhood.index('or not _ground_is_current(coordinate)'))
        process = body(E, '_process')
        self.assertLess(process.index('_update_neighborhood()'), process.index('_generate_budget()'))
        for invalid in ('absent', 'mismatched'):
            a = filled()
            if invalid == 'absent':
                a.receipts.pop((0, 0))
            else:
                a.receipts[(0, 0)] = replace(a.receipts[(0, 0)], presenter=-1)
            # Drained queue and an unchanged neighborhood cannot repair or
            # authorize this state. Missing evidence is not a retry request.
            self.assertIn((0, 0), a.pixels)
            self.assertFalse(a.ready(1), invalid)
        arrival = body(E, 'prepare_for_arrival')
        rejection = arrival[arrival.index('if not _required_ground_is_current():'):]
        self.assertLess(rejection.index('_stop_terrain('), rejection.index('if not arrival_is_ready('))
        self.assertIn('return {"ok": false, "cancelled": false}', rejection)
        # Supported cancellation/reattachment invalidates the early-return
        # predicate, so retained work is reconsidered on the next preparation.
        ferrite = (ROOT/'scenes/world/ferrite_deposit_presenter.gd').read_text()
        self.assertIn('_active and _state == state', body(ferrite, 'matches_context'))
        self.assertIn('_active = false', body(ferrite, 'cancel'))
        self.assertIn('cancel()', body(ferrite, '_exit_tree'))
        self.assertIn('_ferrite_presenter.cancel()', body(E, 'cancel_arrival_preparation'))
        # Receipt removal occurs only during synchronous replacement or
        # successful retirement; failures stop before any later admission.
        self.assertEqual(E.count('_ground_receipts.erase(coordinate)'), 3)
        self.assertNotIn('await ', body(E, '_generate_budget'))
        self.assertIn('_stop_terrain(result)', body(E, '_present_illustrated_chunk'))

    def test_legacy_is_an_explicit_exception_to_illustrated_receipts(self):
        current = body(E, '_ground_is_current')
        self.assertIn('if _effective_renderer == TerrainRenderer.LEGACY:\n\t\treturn true', current)
        self.assertLess(current.index('return true'), current.index('_ground_receipts.has(coordinate)'))
        for name in ('_present_illustrated_chunk', '_retire_illustrated_chunk'):
            method = body(E, name)
            self.assertLess(method.index('return true'), method.index('_terrain_presenter.'))
        budget = body(E, '_generate_budget')
        self.assertIn('if _effective_renderer != TerrainRenderer.LEGACY:\n'
                      '\t\tfor coordinate in committed:\n\t\t\t_ground_receipts[coordinate] =', budget)
        self.assertIn('enum TerrainRenderer { LEGACY, ILLUSTRATED, CONTINUOUS }', E)

    def test_complete_required_square_and_partial_missing_queue_drained(self):
        a = filled()
        self.assertEqual(len(a.receipts), 25)
        self.assertTrue(a.ready(1))
        self.assertFalse(a.ready(1, center=(1, 0)))
        for c in list(a.receipts):
            receipt = a.receipts.pop(c)
            self.assertFalse(a.ready(1), c)  # independent of any scheduling queue
            a.receipts[c] = receipt
        self.assertFalse(Authority().ready(1))
        required = body(E, '_required_ground_is_current')
        for marker in ('not is_inside_tree()', '_tint_dirty',
                       'range(-loading_radius, loading_radius + 1)',
                       '_ground_is_current(_center + Vector2i(x, y))'):
            self.assertIn(marker, required)
        self.assertNotIn('retention_margin', required)
        ready = body(E, 'arrival_is_ready')
        for marker in ('_required_ground_is_current()', 'result.get("ground_center") == _center',
                       'result.get("ground_radius") == loading_radius', '_pending.is_empty()',
                       'required_ready(_ferrite_token)', 'matches_context(_state)'):
            self.assertIn(marker, ready)

    def test_tokens_replacement_failure_retained_old_and_retirement(self):
        a = filled()
        c = (0, 0)
        old = a.pixels[c]
        self.assertTrue(a.begin(c, 26))
        self.assertFalse(a.ready(1))  # registered/prepared is not published
        self.assertFalse(a.publish(c, old))
        self.assertFalse(a.retire(c, old))
        self.assertFalse(a.publish(c, 26, valid=False))
        self.assertEqual(a.pixels[c], old)
        self.assertFalse(a.ready(1))
        self.assertFalse(a.begin(c, 25))
        self.assertFalse(a.begin(c, 26))
        self.assertTrue(a.begin(c, 27) and a.publish(c, 27))
        self.assertFalse(a.publish(c, 27))
        self.assertTrue(a.ready(1))
        self.assertTrue(a.retire(c, 27))
        self.assertFalse(a.ready(1))
        self.assertFalse(a.publish(c, 27))
        present = body(E, '_present_illustrated_chunk')
        self.assertLess(present.index('_ground_receipts.erase(coordinate)'),
                        present.index('begin_generation(coordinate, token)'))
        retire = body(E, '_retire_illustrated_chunk')
        self.assertLess(retire.index('retire_chunk('), retire.index('if result.ok:'))
        self.assertLess(retire.index('if result.ok:'), retire.index('_ground_receipts.erase(coordinate)'))
        self.assertIn('or not _ground_is_current(coordinate)', body(E, '_update_neighborhood'))

    def test_every_identity_dimension_rejects_other_context(self):
        for field in Ground.__dataclass_fields__:
            a = filled()
            c = (0, 0)
            receipt = a.receipts[c]
            a.receipts[c] = replace(receipt, **{field: getattr(receipt, field)+1})
            self.assertFalse(a.ready(1), field)
        current = body(E, '_ground_is_current')
        for marker in ('_ground_state != _state', '_ground_seed != _state.seed_value',
                       'not is_instance_valid(_generator)', 'not is_instance_valid(_terrain_presenter)',
                       'is_ancestor_of(_terrain_presenter)', '_ground_receipts.has(coordinate)',
                       '_terrain_tokens.has(coordinate)', '_chunks.has(coordinate)',
                       'chunk.is_inside_tree()', 'chunk.get_parent() == self',
                       'chunk.state_revision == _state.revision', 'receipt.get("state") == _state',
                       'receipt.get("seed") == _state.seed_value', 'receipt.get("revision") == _state.revision',
                       'receipt.get("generator") == _generator.get_instance_id()',
                       'receipt.get("chunk") == chunk.get_instance_id()',
                       'not receipt.get("publication", {}).is_empty()',
                       'receipt.publication == _ground_publication(coordinate, _terrain_tokens[coordinate])'):
            self.assertIn(marker, current)
        arrival = body(E, 'prepare_for_arrival')
        neighborhood = body(E, '_update_neighborhood')
        self.assertIn('if _ground_state != _state or _ground_seed != _state.seed_value:', neighborhood)
        self.assertLess(neighborhood.index('&"ground_context"'), neighborhood.index('var center :='))
        self.assertIn('&"ground_publication"', arrival)

    def test_revision_replacement_requires_all_current_but_keeps_pixels(self):
        a = filled()
        a.context = replace(a.context, revision=1)
        self.assertFalse(a.ready(1))
        for token, c in enumerate(sorted(a.receipts), 26):
            self.assertTrue(a.begin(c, token))
            self.assertIn(c, a.pixels)
            self.assertFalse(a.ready(1))
            self.assertTrue(a.publish(c, token))
        self.assertTrue(a.ready(1))

    def test_detachment_cancellation_and_fresh_retained_admission(self):
        a = filled()
        a.attached = False
        a.arrival += 1  # exterior _exit_tree invalidates old transition receipts
        self.assertFalse(a.ready(1))
        self.assertFalse(a.ready(2))
        a.attached = True
        a.arrival += 1  # prepare_for_arrival rechecks retained evidence
        self.assertFalse(a.ready(1))
        self.assertTrue(a.ready(3))
        a.arrival += 1
        a.cancelled = True
        self.assertFalse(a.ready(3))
        self.assertFalse(a.ready(4))
        a.cancelled = False
        a.arrival += 1
        self.assertTrue(a.ready(5))
        for name in ('prepare_for_arrival', 'cancel_arrival_preparation', '_exit_tree'):
            self.assertIn('_arrival_generation += 1', body(E, name))
        ready = body(E, 'arrival_is_ready')
        self.assertIn('result.get("generation", -1) == _arrival_generation', ready)
        self.assertIn('not _arrival_cancelled', ready)
        self.assertIn('is_ancestor_of(_player)', ready)

    def test_commit_after_tint_and_attachment_and_live_presenter_evidence(self):
        a = filled()
        a.flushed = False
        self.assertFalse(a.ready(1))
        budget = body(E, '_generate_budget')
        order = ['chunk.configure(', '_present_illustrated_chunk(coordinate)', 'chunk.write_tint(',
                 '_sync_tint_borders(', 'remove_child(previous)', 'add_child(chunk)',
                 '_chunks[coordinate] = chunk', '\n\t_flush_terrain_tint()',
                 '_ground_receipts[coordinate] =']
        self.assertEqual([budget.index(s) for s in order], sorted(budget.index(s) for s in order))
        self.assertNotIn('await ', budget)
        evidence = body(P, 'publication')
        for marker in ('_current(coordinate, generation_token, false).ok',
                       'not _active[coordinate].presented', 'not is_inside_tree()',
                       'not _terrain.is_inside_tree()', '_terrain.get_parent() != self',
                       'not _terrain.is_visible_in_tree()', 'return {}',
                       '"chunk": coordinate', '"token": generation_token',
                       '"presenter": get_instance_id()', '"layer": _terrain.get_instance_id()'):
            self.assertIn(marker, evidence)
        self.assertNotIn('set_cell', evidence)
        self.assertNotIn('await ', evidence)

    def test_protected_systems_wiring_and_existing_presenter_mutation_unchanged(self):
        # Exact current-vs-planning-baseline comparison, without changing any
        # historical receipt or expanding an engine runner's inventory.
        for path in ('scenes/world/world_coordinates.gd', 'scenes/world/terrain_chunk.gd',
                     'scenes/world/planet_generator.gd', 'scenes/world/planet_world_state.gd',
                     'scenes/world/ferrite_deposit_presenter.gd', 'scenes/world/planet_exterior.tscn',
                     'scenes/world/illustrated_terrain_tint.gdshader',
                     'scenes/main/scene_transition_controller.gd', 'scenes/main/playthrough_state.gd',
                     'project.godot', 'tools/run-local-tests.ps1'):
            expected = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
            # These gameplay files now include Computer restoration. Keep this
            # terrain-era comparison historical; current preservation is checked
            # explicitly by static_computer_restoration_test.py.
            actual = (subprocess.check_output(['git', 'show', '993ffc14c1fad1032227801870cd3a3fce50f7a5:'+path], cwd=ROOT)
                      if path in ('scenes/main/scene_transition_controller.gd', 'scenes/main/playthrough_state.gd') else
                      subprocess.check_output(['git', 'show', 'cd91c9086ef24e71ddb6a43a2076c4be5a69485e:'+path], cwd=ROOT)
                      if path == 'tools/run-local-tests.ps1' else (ROOT/path).read_bytes())
            self.assertEqual(actual.replace(b'\r\n', b'\n'),
                             expected.replace(b'\r\n', b'\n'), path)
        old = subprocess.check_output(['git', 'show', f'{BASE}:scenes/world/illustrated_terrain_presenter.gd'],
                                      cwd=ROOT, text=True)
        for method in ('begin_generation', 'present_chunk', 'retire_chunk', '_prepare',
                       '_validate_assignments', '_guard', '_current', '_matches'):
            # Ignore the new query's introductory comment following retire_chunk.
            self.assertEqual(body(P, method).split('# Read-only evidence')[0].rstrip(),
                             body(old, method).rstrip(), method)
        self.assertIn('terrain_renderer: TerrainRenderer = TerrainRenderer.CONTINUOUS', E)


if __name__ == '__main__':
    unittest.main()
