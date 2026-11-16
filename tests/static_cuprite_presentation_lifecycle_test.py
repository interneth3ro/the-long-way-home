"""Focused source contracts only; no Godot or project code executes."""
from pathlib import Path
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRESENTER = (ROOT / "scenes/world/resource_presenter_v2.gd").read_text()
EXTERIOR = (ROOT / "scenes/world/planet_exterior.gd").read_text()
BEHAVIOR = (ROOT / "tests/cuprite_presentation_lifecycle_test.gd").read_text()


def body(source, name):
    return re.search(r"^func " + name + r"\(.*?(?=^func |\Z)", source, re.M | re.S)[0]


class CupritePresentationLifecycleTests(unittest.TestCase):
    def _assert_terminal_completion_contract(self, source):
        step = body(source, "step")
        prefix = ('func step(token: int) -> Dictionary:\n'
                  '\tif token != _token or not _active:\n'
                  '\t\treturn {"ok": true, "stale": true}\n'
                  '\tif is_complete(token):\n'
                  '\t\treturn {"ok": true, "done": true}\n')
        self.assertTrue(step.startswith(prefix))
        complete = body(source, "is_complete")
        for guard in ('token != _token or not _active or not _complete',
                      'context.ok and context.token == _world_token and context.world_seed == _seed',
                      '_source.is_ready() and _source.identity_policy() == _policy'):
            self.assertIn(guard, complete)

    def test_completed_step_is_terminal_after_validated_completion(self):
        self._assert_terminal_completion_contract(PRESENTER)
        import subprocess
        reviewed = '2f9adac517eb469c9641133391afd782d3e067c8'
        path = 'scenes/world/resource_presenter_v2.gd'
        before = subprocess.check_output(['git', 'show', reviewed + ':' + path], cwd=ROOT).decode('utf-8')
        terminal = '\tif is_complete(token):\n\t\treturn {"ok": true, "done": true}\n'
        self.assertEqual(PRESENTER.count(terminal), 1)
        self.assertEqual(PRESENTER.replace(terminal, '', 1), before)
        for path in ('scenes/world/planet_exterior.gd', 'scenes/main/scene_transition_controller.gd',
                     'scenes/interaction/ferrite_inspection.gd', 'scenes/world/planet_world_state.gd',
                     'scenes/main/playthrough_state.gd', 'tools/run-behavioral-tests.ps1',
                     'tools/run-local-tests.ps1', 'tests/behavioral/test_runner.gd'):
            with self.subTest(path=path):
                before = subprocess.check_output(['git', 'show', reviewed + ':' + path], cwd=ROOT)
                self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'), before.replace(b'\r\n', b'\n'))

    def test_terminal_guard_rejects_removed_unchecked_or_state_mutating_shortcuts(self):
        terminal = '\tif is_complete(token):\n\t\treturn {"ok": true, "done": true}\n'
        for replacement in ('', terminal.replace('is_complete(token)', '_complete'),
                            terminal.replace('"done": true', '"done": false'),
                            terminal.replace('\t\treturn', '\t\t_index = 0\n\t\treturn')):
            with self.subTest(replacement=replacement):
                with self.assertRaises(AssertionError):
                    self._assert_terminal_completion_contract(PRESENTER.replace(terminal, replacement, 1))
        with self.assertRaises(AssertionError):
            self._assert_terminal_completion_contract(PRESENTER.replace('context.token == _world_token', 'true'))

    def test_authored_completion_regressions_cover_service_and_reveal(self):
        for label in ('repeated completed step remains done',
                      'terminal completion does not replay registrations or mutate published state',
                      'unchanged coverage service preserves completed readiness',
                      'same-area new request invalidates completed work',
                      'changed coverage starts genuinely incomplete request',
                      'completed presentation still fails closed after ',
                      'detached activity guard precedes terminal completion',
                      'cancelled activity cannot return completed work',
                      'disposed presenter cannot return completed work'):
            self.assertIn(label, BEHAVIOR)
        gameplay = (ROOT / 'tests/cuprite_gameplay_test.gd').read_text()
        self.assertIn('completed arrival receipt stays valid across normal reveal interval', gameplay)
        self.assertIn('await reveal._fade_to(0.0)', gameplay)
        self.assertIn('exterior.process_mode = Node.PROCESS_MODE_INHERIT', gameplay)
        self.assertIn('process_frame.connect(sample_readiness)', gameplay)
        self.assertIn('not readiness_samples.has(false)', gameplay)
        self.assertNotIn('create_timer', gameplay)

    def test_temporary_detachment_retires_token_but_preserves_completed_live_state(self):
        initial = body(EXTERIOR, "prepare_initial_neighborhood")
        self.assertIn("_initialize_world(state)", initial)
        self.assertIn("_service_resources()", initial)
        controller = (ROOT / "scenes/main/scene_transition_controller.gd").read_text()
        prepare = body(controller, "prepare_initial_exterior")
        self.assertLess(prepare.index("await exterior.prepare_initial_neighborhood(state)"),
                        prepare.index("world_host.remove_child(exterior)"))
        exit_tree = body(PRESENTER, "_exit_tree")
        for fragment in ("context.token == _world_token", "context.world_seed == _seed",
                         "var completed := _complete", "cancel(true)", "_complete = completed"):
            self.assertIn(fragment, exit_tree)
        self.assertLess(exit_tree.index("cancel(true)"), exit_tree.index("_complete = completed"))
        cancel = body(PRESENTER, "cancel")
        self.assertLess(cancel.index("_token += 1"), cancel.index("if keep_visuals:"))
        self.assertIn("if keep_visuals:\n\t\treturn", cancel)

    def test_same_world_reuse_precedes_destructive_configuration(self):
        configure = body(PRESENTER, "configure_world")
        self.assertLess(configure.index("if matches_world(world, definitions):"), configure.index("dispose()"))
        self.assertIn('_active = _complete\n\t\treturn {"ok": true, "reused": true}', configure)
        initialize = body(EXTERIOR, "_initialize_world")
        self.assertIn("_resource_token = _resource_presenter.snapshot().token", initialize)
        self.assertIn('configured.get("reused", false)', initialize)
        self.assertIn("if not _resources_done:\n\t\t_resource_chunks.clear()", initialize)
        self.assertNotIn("_resources_done = true", initialize)

    def test_context_and_catalog_compatibility_are_checked(self):
        match = body(PRESENTER, "matches_world")
        for fragment in ("_world != world", "definitions.size() != _catalogs.size()",
                         "context.token != _world_token", "context.world_seed != _seed",
                         "seen.has(resource_id)", "_references.get(resource_id) != definition.presentation_catalog",
                         "Catalog.read_catalog(definition.presentation_catalog, resource_id) != _catalogs[resource_id]"):
            self.assertIn(fragment, match)

    def test_explicit_and_interrupted_cancellation_cannot_reuse_completion(self):
        cancel = body(PRESENTER, "cancel")
        self.assertIn("_complete = false", cancel)
        for fragment in ("_pages.clear()", "_members.clear()", "_active = false"):
            self.assertIn(fragment, cancel)
        cancellation = body(EXTERIOR, "cancel_arrival_preparation")
        for fragment in ("_arrival_generation += 1", "_resource_presenter.cancel()",
                         "_resource_chunks.clear()", "_resources_done = false"):
            self.assertIn(fragment, cancellation)
        step = body(PRESENTER, "step")
        self.assertLess(step.index("token != _token or not _active"), step.index("_world.query_resource_descriptors_v2"))
        self.assertIn('_complete = true\n\treturn {"ok": true, "done": true}', step)

    def test_loaded_coverage_changes_still_request_and_retire_visuals(self):
        self.assertIn("loaded == _resource_chunks", body(EXTERIOR, "_initialize_world"))
        service = body(EXTERIOR, "_service_resources")
        for fragment in ("if loaded != _resource_chunks:", "set_loaded_chunks(loaded)",
                         "request(area)", "_resources_done = false"):
            self.assertIn(fragment, service)
        loaded = body(PRESENTER, "set_loaded_chunks")
        self.assertIn("if not _is_loaded(_registrations[identity]):", loaded)
        self.assertIn("sprite.free()", loaded)
        self.assertIn("if not _sprites.has(identity):", body(PRESENTER, "step"))

    def test_readiness_requires_current_completion_and_fresh_arrival(self):
        for name in ("arrival_is_ready", "_initial_completed"):
            self.assertIn("_resource_presenter.is_complete(_resource_token)", body(EXTERIOR, name))
        ready = body(EXTERIOR, "arrival_is_ready")
        for fragment in ('result.get("generation", -1) == _arrival_generation',
                         "_required_ground_is_current()", "is_complete(_resource_token)",
                         "and _resources_done", "not _arrival_cancelled"):
            self.assertIn(fragment, ready)
        complete = body(PRESENTER, "is_complete")
        self.assertIn("token != _token or not _active or not _complete", complete)
        self.assertIn("context.token == _world_token", complete)

    def test_failure_replacement_and_actual_retirement_have_disposal(self):
        self.assertIn("dispose()", body(PRESENTER, "_failure"))
        self.assertIn("dispose()", body(PRESENTER, "configure_world"))
        self.assertIn("if what == NOTIFICATION_PREDELETE:", body(PRESENTER, "_notification"))
        self.assertIn("dispose()", body(PRESENTER, "_notification"))
        dispose = body(PRESENTER, "dispose")
        for fragment in ("cancel()", "_world = null", "_world_token = null",
                         "_loaded_chunks.clear()", "_textures.clear()", "_catalogs.clear()"):
            self.assertIn(fragment, dispose)

    def test_mixed_resource_lifecycle_retains_all_three_presentations(self):
        for fragment in ('&"ferrite"', '&"cuprite"', '&"carbite"', '[FERRITE, CUPRITE, CARBITE]',
                         'presenter.snapshot().sprites == 3', 'presenter._sprites == sprites',
                         'presenter._textures == textures', 'replacement.members = world.members.duplicate(true)',
                         'for retained_sprite: WeakRef in retained_sprites:'):
            self.assertIn(fragment, BEHAVIOR)

    def test_behavioral_fixture_covers_lifecycle_without_runner_expansion(self):
        for label in ("initial presentation completes", "reattachment performs no repeated queries",
                      "registrations sprite and texture retained", "cancelled work restarts safely",
                      "interrupted preparation cannot become ready on reattachment",
                      "streaming reload restores visible sprite", "world replacement clears unrelated caches",
                      "retired generation context cannot be reused", "explicit disposal clears all reusable state",
                      "actual retirement frees retained child sprites"):
            self.assertIn(label, BEHAVIOR)
        for runner in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("cuprite_presentation_lifecycle_test", runner.read_text())


if __name__ == "__main__":
    unittest.main()
