"""Offline startup contracts; does not execute GDScript or establish UI behavior."""
import unittest
from unittest.mock import patch

import application_shell_preservation as preservation
import static_automatic_transitions_test as geometry
from static_v2_production_host_test import read


class ApplicationShellTests(unittest.TestCase):
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
        self.assertIn("await get_tree().process_frame\n\tremove_child", start)
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
