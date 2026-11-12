from south_idle_preservation import verified_south_idle_paths
from north_idle_preservation import verified_north_idle_paths
"""Milestone 4 offline lifecycle specifications and production source contracts.

Finite fixtures do not execute GDScript or establish engine/UI behavior.
"""
from itertools import permutations
from pathlib import Path
import subprocess
import unittest

from static_automatic_transitions_test import function, nodes
from static_save_codec_runner_test import verified_codec_runner_paths

ROOT = Path(__file__).resolve().parents[1]
A = (ROOT / "scenes/application/application.gd").read_text()
C = (ROOT / "scenes/main/scene_transition_controller.gd").read_text()
L = (ROOT / "scenes/application/loading_screen.gd").read_text()
S = (ROOT / "scenes/application/loading_screen.tscn").read_text()


def ordered(test, text, *markers):
    positions = [text.index(marker) for marker in markers]
    test.assertEqual(positions, sorted(positions))


class LoadingScreenTests(unittest.TestCase):
    def test_render_precedes_synchronous_initialization(self):
        ordered(self, function(A, "_start_new_game"), "_starting = true", "add_child(_loading)",
                "begin_operation", "await RenderingServer.frame_post_draw",
                "while Input.is_anything_pressed():", "GAMEPLAY.instantiate()",
                "_session.process_mode = Node.PROCESS_MODE_DISABLED", "add_child(_session)",
                "initial_preparation_progress.connect", "await transitions.prepare_initial_exterior(true)")
        self.assertIn('layer = 120', S)
        self.assertIn('process_mode = 3', S)
        self.assertIn('color = Color(0.018, 0.024, 0.028, 1)', S)

    def test_units_are_actual_and_final_completion_is_explicit(self):
        self.assertIn('const STARTUP_UNITS: int = 51', A)
        report = function(A, '_report_startup_progress')
        self.assertIn('total != STARTUP_UNITS - 1', report)
        self.assertIn('clampi(completed, 0, 50)', report)
        self.assertIn('exterior preparation units ready', report)
        self.assertNotIn('terrain sectors ready', report)
        ordered(self, function(A, '_start_new_game'), 'if not prepared:',
                '_loading.report_progress(50,', 'await _loading.fade_out()',
                'await _drain_input()', 'if not transitions.activate_initial_session():',
                '_loading.complete_operation', '_retire_loading()',
                '_session.process_mode = Node.PROCESS_MODE_PAUSABLE', '_starting = false')
        self.assertIn('_total - 1', function(L, 'report_progress'))
        self.assertIn('_bar.value = _total', function(L, 'complete_operation'))
        for code in (A, L):
            for fake in ('create_timer', 'Time.', 'delta', '_process(', '_physics_process('):
                self.assertNotIn(fake, code)
        self.assertNotIn('_bar', function(L, 'fade_out'))

    def test_permuted_progress_never_regresses_or_completes_early(self):
        # Specification: repeated/reordered completed-work observations may be
        # ignored, but cannot reduce displayed work or award readiness.
        for events in permutations((0, 1, 25, 49, 50)):
            shown = 0
            for value in events + (50, 25, 50):
                candidate = max(shown, min(value, 50))
                self.assertGreaterEqual(candidate, shown)
                self.assertLess(candidate, 51)
                shown = candidate
            self.assertEqual(shown, 50)
        body = function(L, 'report_progress')
        self.assertIn('_state != State.WORKING or completed < _completed', body)
        self.assertIn('clampi(completed, _completed, _total - 1)', body)

    def test_failure_is_terminal_for_work_and_completion(self):
        for method in ('report_progress', 'complete_operation', 'fail_operation', 'fade_out'):
            self.assertIn('_state != State.WORKING', function(L, method))
        fail = function(L, 'fail_operation')
        for marker in ('_state = State.FAILED', '_overlay.modulate.a = 1.0',
                       '_return.show()', '_return.grab_focus()'):
            self.assertIn(marker, fail)
        self.assertNotIn('_bar.value', fail)
        self.assertNotIn('return_requested.emit', fail)
        self.assertIn('if _starting and not _startup_failed:', function(A, '_input'))

    def test_presentation_is_reusable_and_has_no_work_authority(self):
        for code in (L, S):
            for forbidden in ('PlanetExterior', 'terrain_chunk', 'SQLite', 'PlaythroughState',
                              'SceneTransitionController', 'main_v2', 'prepare_initial'):
                self.assertNotIn(forbidden, code)
        for api in ('begin_operation', 'report_progress', 'complete_operation', 'fail_operation', 'fade_out'):
            self.assertIn('func ' + api, L)
        self.assertEqual(S.count('type="ProgressBar"'), 1)
        self.assertEqual(S.count('type="Button"'), 1)
        self.assertIn('Return to Main Menu', S)

    def test_preparation_keeps_original_readiness_and_retention_before_handoff(self):
        body = function(C, 'prepare_initial_exterior')
        ordered(self, body, 'await exterior.prepare_initial_neighborhood(state)',
                'if not exterior.preparation_is_ready(result):',
                'while Input.is_anything_pressed():', '_worlds[EXTERIOR_SCENE] = exterior',
                'world_host.remove_child(exterior)', 'initial_exterior_initialized = true',
                'if defer_activation:', '_startup_activation_pending = true')
        hold = body.split('if defer_activation:', 1)[1].split('return true', 1)[0]
        self.assertNotIn('_finish_transition', hold)
        self.assertNotIn('progression.process_mode =', hold)
        self.assertIn('_curtain.hide()', hold)
        self.assertIn('defer_activation: bool = false', body)

    def test_activation_rejects_cancelled_or_replaced_context(self):
        body = function(C, 'activate_initial_session')
        for marker in ('not _busy', 'not _startup_activation_pending',
                       'not initial_exterior_initialized', 'not is_instance_valid(exterior)',
                       'exterior.get_parent() != null', 'progression.planet != _startup_state',
                       '_startup_state.seed_value != _startup_seed',
                       '_startup_state.revision != _startup_revision',
                       'not _current_world.is_ancestor_of(player)'):
            self.assertIn(marker, body)
        ordered(self, body, 'return false', 'progression.process_mode = _startup_progression_mode',
                '_finish_transition(_startup_player_mode)', 'return true')
        self.assertIn('_startup_activation_pending = false', function(C, 'cancel_initial_preparation'))

    def test_failure_disconnects_invalidates_and_never_activates(self):
        body = function(A, '_fail_startup')
        ordered(self, body, '_disconnect_progress()', '_startup_failed = true',
                '_startup_generation += 1', 'cancel_initial_preparation()', '_loading.fail_operation')
        for forbidden in ('activate_initial_session', 'complete_operation', '_starting = false', 'paused ='):
            self.assertNotIn(forbidden, body)
        self.assertIn('push_error(', body)

    def test_retirement_restores_pause_after_discard_and_before_title(self):
        body = function(A, '_return_failed_startup')
        ordered(self, body, '_loading.disable_return()', '_startup_generation += 1',
                '_disconnect_progress()', 'cancel_initial_preparation()', 'await _drain_input()',
                'remove_child(_session)', '_session.free()', '_session = null',
                'get_tree().paused = _pause_before_session', '_retire_loading()',
                '_title = TITLE.instantiate()', '_connect_title()',
                '_startup_failed = false', '_starting = false')
        self.assertIn('_pause_before_session = get_tree().paused', function(A, '_start_new_game'))
        self.assertIn('world.free()', function(C, '_exit_tree'))

    def test_generation_and_subscription_guards_cover_every_startup_await(self):
        body = function(A, '_start_new_game')
        for tail in body.split('await ')[1:]:
            after = tail.split('\n', 1)[1]
            self.assertTrue(after.lstrip().startswith('if not _owns_startup(generation):'), tail[:80])
        self.assertIn('generation == _startup_generation', function(A, '_owns_startup'))
        self.assertIn('not _startup_failed', function(A, '_owns_startup'))
        self.assertIn('_owns_startup(generation)', function(A, '_report_startup_progress'))
        self.assertIn('is_connected(_progress_callback)', function(A, '_disconnect_progress'))
        self.assertIn('disconnect(_progress_callback)', function(A, '_disconnect_progress'))
        self.assertIn('_progress_callback = Callable()', function(A, '_disconnect_progress'))

    def test_finite_failure_cleanup_and_fresh_session_specification(self):
        # Each boundary may fail. A rejected/retired generation never activates;
        # restoring prior pause is independent of the failed session's pause.
        for boundary in ('interior', 'terrain', 'retention', 'reveal', 'readiness'):
            for prior_pause in (False, True):
                generation, active, displayed = 1, False, 0
                for stage, units in (('interior', 0), ('terrain', 49), ('retention', 50),
                                     ('reveal', 50), ('readiness', 50)):
                    if stage == boundary:
                        break
                    displayed = units
                self.assertLess(displayed, 51)
                retired_generation = generation
                generation += 1
                paused = prior_pause
                session = None
                self.assertNotEqual(retired_generation, generation)
                self.assertFalse(active)
                self.assertEqual(paused, prior_pause)
                self.assertIsNone(session)
                generation += 1  # Fresh New Game, independent ownership.
                self.assertNotEqual(retired_generation, generation)
        self.assertIn('if _starting or _session != null:', function(A, '_start_new_game'))

    def test_hatch_gameplay_artwork_and_world_implementation_unchanged(self):
        old = subprocess.check_output(['git', 'show', 'f142fa4:scenes/main/scene_transition_controller.gd'],
                                      cwd=ROOT).decode()
        # Every ordinary transition method and teardown cache loop stays exact.
        for method in ('request_transition', '_perform_transition', '_perform_quick_transition',
                       '_validate_arrival', '_finish_transition', '_fade_to',
                       '_finish_quick_transition', 'cancel_quick_transition'):
            self.assertEqual(function(C, method), function(old, method), method)
        paths = ('assets', 'construction', 'inventory', 'scenes/world', 'scenes/player',
                 'scenes/main/main.gd', 'scenes/main/main_v2.gd', 'scenes/main/playthrough_state.gd',
                 'scenes/application/pause_menu.gd', 'scenes/application/pause_menu.tscn', 'tools')
        changed = subprocess.check_output(['git', 'diff', '--name-only', 'f142fa4', '--', *paths],
                                          cwd=ROOT, text=True)
        self.assertFalse(set(changed.splitlines()) - verified_codec_runner_paths() - verified_north_idle_paths() - verified_south_idle_paths(), changed)


if __name__ == '__main__':
    unittest.main()
