"""Offline startup contracts; does not execute GDScript or establish UI behavior."""
import unittest
import subprocess
from unittest.mock import patch

import application_shell_preservation as preservation
import static_automatic_transitions_test as geometry
from static_v2_production_host_test import read


class ApplicationShellTests(unittest.TestCase):
    def test_loading_screen_uid_exception_is_exact_and_matches_approved_commit(self):
        path = "scenes/application/loading_screen.gd.uid"
        approved = subprocess.check_output([
            "git", "show", "0b8d14544ada1693aaf25f91d286c1e589f8fe3c:" + path
        ], cwd=preservation.ROOT)
        self.assertEqual(preservation.LOADING_SCREEN_UID, path)
        self.assertEqual(preservation.verify_loading_screen_uid(approved), {path})
        self.assertEqual(preservation.verify_loading_screen_uid(approved.replace(b"\n", b"\r\n")), {path})
        allowed = preservation.verified_application_paths()
        self.assertEqual(allowed - preservation.APPLICATION_FILES - {"project.godot"}, {path})
        self.assertNotIn("scenes/application/unapproved.gd.uid", allowed)
        self.assertNotIn("scenes/world/unapproved.gd.uid", allowed)
        for bad in (b"", approved[:-1], approved + b"extra\n",
                    approved.replace(b"cqbd6damin78b", b"different"), b"\xef\xbb\xbf" + approved):
            with self.subTest(uid=bad), self.assertRaises(AssertionError):
                preservation.verify_loading_screen_uid(bad)
        real_read = preservation.Path.read_bytes

        def changed_uid(file):
            return b"uid://different\n" if file == preservation.ROOT / path else real_read(file)

        with patch.object(preservation.Path, "read_bytes", changed_uid), self.assertRaises(AssertionError):
            preservation.verified_application_paths()

    def test_uid_amendment_keeps_historical_preservation_consumers_closed(self):
        names = (
            'static_fabricator_animation_test.FabricatorAnimationStaticTest.'
            'test_all_other_production_artwork_gameplay_and_execution_controls_preserved',
            'static_fabricator_artwork_test.FabricatorArtworkStaticTest.'
            'test_gameplay_existing_artwork_and_execution_controls_preserved',
            'static_fabricator_footprint_test.FabricatorFootprintStaticTest.'
            'test_protected_gameplay_art_and_execution_controls_unchanged',
        )
        real_output = subprocess.check_output
        for unexpected in ('scenes/application/unapproved.gd.uid', 'scenes/world/planet_world_state.gd',
                           'assets/machines/unapproved.png', 'tools/unapproved.ps1'):
            def changed_paths(args, *a, **kw):
                actual = real_output(args, *a, **kw)
                if list(args[:3]) == ['git', 'diff', '--name-only']:
                    return actual.rstrip('\n') + '\n' + unexpected + '\n'
                return actual

            for name in names:
                with self.subTest(path=unexpected, consumer=name):
                    result = unittest.TestResult()
                    case = unittest.TestLoader().loadTestsFromName(name)
                    with patch('subprocess.check_output', side_effect=changed_paths):
                        case.run(result)
                    self.assertEqual(result.testsRun, 1)
                    self.assertFalse(result.errors, result.errors)
                    self.assertEqual(len(result.failures), 1, 'Unexpected path was accepted')
                    self.assertIn(unexpected, result.failures[0][1])

    def test_historical_projection_rejects_unrelated_configuration_changes(self):
        raw = (preservation.ROOT / "project.godot").read_bytes()
        preservation.verified_application_paths()
        for bad in (raw + b'\n[autoload]\n', raw.replace(b'viewport_width=1280', b'viewport_width=640')):
            with self.subTest(bad=bad[-40:]), patch.object(preservation.Path, "read_bytes", return_value=bad):
                with self.assertRaises(AssertionError):
                    preservation.verified_application_paths()
        with self.assertRaises(AssertionError):
            preservation.without_application_startup(raw + raw)

    def test_startup_has_no_live_gameplay_until_activation_and_release(self):
        scene = read("scenes/application/application.tscn")
        self.assertNotIn("main_v2.tscn", scene)
        self.assertNotIn("[autoload]", read("project.godot"))
        code = read("scenes/application/application.gd")
        start = geometry.function(code, "_start_new_game")
        ordered = ["if _starting or _session != null:", "_starting = true",
                   "_title.disable_menu()", "while Input.is_anything_pressed():",
                   "remove_child(_title)", "_session = GAMEPLAY.instantiate()",
                   "add_child(_session)", "_starting = false"]
        indices = [start.index(text) for text in ordered]
        self.assertEqual(indices, sorted(indices))
        self.assertLess(start.index("await get_tree().process_frame"), start.index("remove_child"))
        self.assertIn("set_input_as_handled()", geometry.function(code, "_input"))
        self.assertNotIn("paused = false", code)
        self.assertIn("get_tree().quit()", geometry.function(code, "_quit"))

    def test_menu_placeholders_focus_and_independent_background(self):
        scene = read("scenes/application/title_screen.tscn")
        nodes = geometry.nodes(scene)
        for name in ("LoadGame", "Settings"):
            self.assertIn("disabled = true", nodes[f"Menu/{name}"][1])
            self.assertIn("focus_mode = 0", nodes[f"Menu/{name}"][1])
            self.assertNotIn(f'from="Menu/{name}"', scene)
        for name, target in (("NewGame", "Exit"), ("Exit", "NewGame")):
            for direction in ("top", "bottom"):
                self.assertIn(f'focus_neighbor_{direction} = NodePath("../{target}")',
                              nodes[f"Menu/{name}"][1])
        self.assertIn("THE LONG WAY HOME", nodes["Title"][1])
        background = read("scenes/application/title_background.tscn")
        self.assertIn("crashed_exploration_ship_approved.png", background)
        for forbidden in ("Script", "planet_exterior", "main_v2", "Button"):
            self.assertNotIn(forbidden, background)


if __name__ == "__main__":
    unittest.main()
