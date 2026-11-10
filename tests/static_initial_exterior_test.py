"""Milestone 3 finite fixtures + source contracts. Never executes Godot/GDScript.

The model specifies readiness/ownership, not engine scheduling, parsing, rendering
or performance. Source wiring binds the specification to actual production hooks.
"""
from dataclasses import dataclass, replace
from pathlib import Path
import re
import subprocess
import unittest

from static_automatic_transitions_test import function
from initial_exterior_preservation import without_initial_preparation

ROOT = Path(__file__).resolve().parents[1]
BASE = "5ab32bd"
E = (ROOT / "scenes/world/planet_exterior.gd").read_text()
C = (ROOT / "scenes/main/scene_transition_controller.gd").read_text()
A = (ROOT / "scenes/application/application.gd").read_text()


def square(center, radius):
    return {(center[0] + x, center[1] + y)
            for y in range(-radius, radius + 1) for x in range(-radius, radius + 1)}


def authored_center():
    scene = (ROOT / "scenes/world/planet_exterior.tscn").read_text()
    point = re.search(r'\[node name="FromShip"[^\n]*\]\nposition = Vector2\((-?\d+), (-?\d+)\)', scene)
    chunk = (ROOT / "scenes/world/world_coordinates.gd").read_text()
    size = int(re.search(r'const TERRAIN_SIZE: int = (\d+)', chunk)[1])
    size *= int(re.search(r'const CHUNK_TILES: int = (\d+)', chunk)[1])
    return tuple(int(v) // size for v in point.groups())


@dataclass(frozen=True)
class Context:
    state: int = 10
    seed: int = 26026
    revision: int = 0
    generation: int = 1
    resources: bool = True
    attached: bool = True
    cancelled: bool = False
    failure: bool = False
    tint_flushed: bool = True
    pending: bool = False
    player_attached: bool = False


def ready(context, receipt, publications):
    return (context.attached and not context.cancelled and not context.failure
            and context.tint_flushed and context.resources and not context.pending
            and all(getattr(context, k) == receipt[k] for k in
                    ("state", "seed", "revision", "generation"))
            and all(publications.get(c) == receipt for c in square(authored_center(), 3)))


class InitialExteriorTests(unittest.TestCase):
    def test_exact_authored_signed_square_and_extra_24(self):
        center = authored_center()
        self.assertEqual(center, (-1, -1))
        required = square(center, 3)
        self.assertEqual(len(required), 49)
        self.assertEqual(len(required - square(center, 2)), 24)
        self.assertEqual({x for x, y in required}, set(range(-4, 3)))
        self.assertEqual({y for x, y in required}, set(range(-4, 3)))
        prep = function(E, "prepare_initial_neighborhood")
        for marker in ('get_node("Spawns/FromShip")', 'to_local(spawn.global_position)',
                       'WorldCoordinates.world_to_chunk', 'range(-INITIAL_RADIUS, INITIAL_RADIUS + 1)',
                       'not _pending.has(coordinate)', '_pending.append(coordinate)'):
            self.assertIn(marker, prep)
        self.assertIn('const INITIAL_RADIUS: int = 3', E)
        self.assertIn('const INITIAL_CHUNK_COUNT: int = 49', E)
        for marker in ('loading_radius: int = 2', 'retention_margin: int = 1'):
            self.assertIn(marker, E)
        self.assertNotIn('loading_radius =', prep)

    def test_player_independent_preparation_preserves_arrival_safety(self):
        prep = function(E, "prepare_initial_neighborhood")
        self.assertIn('_player = null', prep)
        self.assertNotIn('is_ancestor_of', prep)
        self.assertNotIn('player.reparent', prep)
        self.assertNotIn('_player', function(E, 'preparation_is_ready'))
        arrival = function(E, 'arrival_is_ready')
        for marker in ('is_ancestor_of(_player)', 'result.get("player") == _player',
                       '_required_ground_is_current()', 'WorldCoordinates.world_to_chunk'):
            self.assertIn(marker, arrival)
        self.assertIn('_initialize_world(state)', function(E, 'prepare_for_arrival'))
        self.assertIn('_initialize_world(state)', prep)

    def test_every_publication_and_resource_completion_is_required(self):
        context = Context()
        receipt = {k: getattr(context, k) for k in ('state', 'seed', 'revision', 'generation')}
        publications = dict.fromkeys(square(authored_center(), 3), receipt)
        self.assertTrue(ready(context, receipt, publications))  # No player.
        for coordinate in publications:
            partial = publications.copy()
            partial.pop(coordinate)
            self.assertFalse(ready(context, receipt, partial), coordinate)
            partial[coordinate] = receipt | {'revision': -1}
            self.assertFalse(ready(context, receipt, partial), coordinate)
        for field, value in (('resources', False), ('attached', False), ('cancelled', True),
                             ('failure', True), ('tint_flushed', False), ('pending', True),
                             ('state', 11), ('seed', 1), ('revision', 1), ('generation', 2)):
            self.assertFalse(ready(replace(context, **{field: value}), receipt, publications), field)
        live = function(E, '_initial_completed')
        for marker in ('_chunks.has(coordinate)', 'is_instance_valid(_chunks[coordinate])',
                       'get_parent() == self', 'is_inside_tree()', 'state_revision == _state.revision',
                       '_ground_is_current(coordinate)', 'not _tint_dirty',
                       'matches_context(_state)', 'required_ready(_ferrite_token)'):
            self.assertIn(marker, live)
        self.assertIn('_initial_completed(_center) == INITIAL_CHUNK_COUNT + 1',
                      function(E, 'preparation_is_ready'))

    def test_readiness_context_and_cancellation_guards(self):
        check = function(E, 'preparation_is_ready')
        for marker in ('result is Dictionary', 'result.get("ok", false)',
                       'result.get("generation", -1) == _arrival_generation',
                       'result.get("state") == _state', 'result.get("seed") == _state.seed_value',
                       'result.get("revision") == _state.revision', 'not _arrival_cancelled',
                       'not _preparing', '_terrain_failure.is_empty()', '_pending.is_empty()',
                       '_continuous_job.is_empty()', '_ground_state == _state',
                       'result.get("ferrite_token", -1) == _ferrite_token'):
            self.assertIn(marker, check)
        prep = function(E, 'prepare_initial_neighborhood')
        self.assertLess(prep.index('if generation != _arrival_generation:'), prep.index('_preparing = false'))
        self.assertIn('_stop_terrain({"ok": false, "code": &"initial_publication"', prep)
        for method in ('cancel_arrival_preparation', '_exit_tree'):
            self.assertIn('_arrival_generation += 1', function(E, method))
        cancel = function(C, 'cancel_initial_preparation')
        self.assertIn('_initial_generation += 1', cancel)
        self.assertIn('_initial_world.cancel_arrival_preparation()', cancel)
        self.assertNotIn('_finish_transition', cancel)
        self.assertIn('_initial_generation += 1', function(C, '_exit_tree'))
        self.assertNotIn('cancel_initial_preparation()', function(C, '_exit_tree'))
        owns = function(C, '_owns_initial_preparation')
        for marker in ('generation == _initial_generation', '_initial_world == exterior',
                       'progression.planet == state', 'state.seed_value == seed_value',
                       'state.revision == revision', 'exterior.is_inside_tree()'):
            self.assertIn(marker, owns)

    def test_retention_first_exit_and_exploration_identity_fixture(self):
        center = authored_center()
        chunks = {c: object() for c in square(center, 3)}
        retained = chunks.copy()
        # Detachment invalidates arrival authority but preserves these instances.
        def stream(at):
            for c in list(chunks):
                if c not in square(at, 3):
                    del chunks[c]
            requested = square(at, 2) - chunks.keys()
            for c in requested:
                chunks[c] = object()
            return requested
        self.assertEqual(stream(center), set())
        self.assertTrue(all(chunks[c] is retained[c] for c in retained))
        self.assertTrue(stream((center[0] + 2, center[1])))
        self.assertLessEqual(set(chunks), square((center[0] + 2, center[1]), 3))
        prep = function(C, 'prepare_initial_exterior')
        ordered = ['player.process_mode = Node.PROCESS_MODE_DISABLED',
                   'progression.process_mode = Node.PROCESS_MODE_DISABLED', '_curtain.color.a = 1.0',
                   'world_host.add_child(exterior)', 'await exterior.prepare_initial_neighborhood(state)',
                   'if not exterior.preparation_is_ready(result):', 'while Input.is_anything_pressed():',
                   '_worlds[EXTERIOR_SCENE] = exterior', 'world_host.remove_child(exterior)',
                   '_owns_initial_preparation(generation, exterior, state, seed_value, revision, false)',
                   'initial_exterior_initialized = true', '_finish_transition(previous_player_mode)']
        self.assertEqual([prep.index(m) for m in ordered], sorted(prep.index(m) for m in ordered))
        self.assertNotIn('get_tree().paused', prep)
        self.assertLess(prep.index('exterior.process_mode = Node.PROCESS_MODE_DISABLED'),
                        prep.index('world_host.add_child(exterior)'))
        self.assertLess(prep.index('world_host.remove_child(exterior)'),
                        prep.index('exterior.process_mode = Node.PROCESS_MODE_INHERIT'))
        for method in ('_perform_transition', '_perform_quick_transition'):
            self.assertIn('_worlds.get(destination_scene)', function(C, method))
        exit_tree = function(E, '_exit_tree')
        for marker in ('_chunks.clear', '_ground_receipts.clear', '_terrain_tokens.clear'):
            self.assertNotIn(marker, exit_tree)
        shell = function(A, '_start_new_game')
        self.assertLess(shell.index('add_child(_session)'), shell.index('await transitions.prepare_initial_exterior(true)'))
        self.assertLess(shell.index('prepare_initial_exterior(true)'), shell.index('_starting = false'))

    def test_existing_gameplay_and_publication_methods_are_exactly_preserved(self):
        for path in ('scenes/world/planet_exterior.gd', 'scenes/main/scene_transition_controller.gd'):
            old = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT).replace(b'\r\n', b'\n')
            raw = (ROOT / path).read_bytes()
            self.assertEqual(without_initial_preparation(path, raw), old)
            for marker in (b'_sync_machines()', b'player.reparent(ground_objects)'):
                if marker in raw:
                    self.assertNotEqual(without_initial_preparation(path, raw.replace(marker, marker + b' # unexpected', 1)), old)
        for path in ('scenes/world/terrain_chunk.gd', 'scenes/world/planet_generator.gd',
                     'scenes/world/planet_world_state.gd', 'scenes/world/ferrite_deposit_presenter.gd',
                     'scenes/world/continuous_terrain_presenter.gd', 'scenes/main/playthrough_state.gd',
                     'tools/run-local-tests.ps1', 'scenes/world/planet_exterior.tscn'):
            self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'),
                             subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT).replace(b'\r\n', b'\n'), path)

    def test_real_progress_and_existing_cooperative_work_paths(self):
        prep = function(E, 'prepare_initial_neighborhood')
        for marker in ('_service_ferrite(true)', '_generate_budget()', '_flush_highlights()',
                       'preparation_progress.emit(_initial_completed(center), INITIAL_CHUNK_COUNT + 1)',
                       'await get_tree().process_frame'):
            self.assertIn(marker, prep)
        self.assertNotIn('Time.', prep)
        self.assertNotIn('create_timer', prep)
        self.assertIn('initial_preparation_progress.emit(completed, total)', function(C, '_report_initial_progress'))
        # Cache visits revalidate resource ownership, using existing sprites/textures.
        ferrite = (ROOT / 'scenes/world/ferrite_deposit_presenter.gd').read_text()
        self.assertIn('return not _sprites.has(identity)', function(ferrite, 'step'))


if __name__ == '__main__':
    unittest.main()
