from south_idle_preservation import verified_south_idle_paths
from north_idle_preservation import verified_north_idle_paths
from initial_exterior_preservation import verified_initial_paths
from static_save_codec_runner_test import verified_codec_runner_paths
"""Offline pause ownership, input routing and preservation contracts; no Godot execution."""
import subprocess
import unittest

from static_automatic_transitions_test import ROOT, function, nodes
from static_v2_production_host_test import read


class PauseMenuTests(unittest.TestCase):
    def test_pause_ui_and_session_have_separate_process_modes(self):
        shell = read("scenes/application/application.gd")
        self.assertIn("process_mode = 3", nodes(read("scenes/application/application.tscn"))["Application"][1])
        start = function(shell, "_start_new_game")
        self.assertLess(start.index("_session.process_mode = Node.PROCESS_MODE_DISABLED"),
                        start.index("add_child(_session)"))
        self.assertNotIn("paused =", start)
        pause = function(shell, "_unhandled_input")
        order = ['event.is_action_pressed("ui_cancel")', 'is_transitioning()',
                 '_pause_before_menu = get_tree().paused', 'get_tree().paused = true', '_pause.open()']
        positions = [pause.index(part) for part in order]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("ui_cancel", function(shell, "_input"))
        ui = nodes(read("scenes/application/pause_menu.tscn"))
        self.assertIn("process_mode = 3", ui["PauseMenu"][1])
        self.assertIn("layer = 110", ui["PauseMenu"][1])

    def test_resume_and_retirement_drain_input_before_restoring_pause(self):
        code = read("scenes/application/application.gd")
        drain = function(code, "_drain_input")
        self.assertIn("while Input.is_anything_pressed():", drain)
        self.assertTrue(drain.rstrip().endswith("await get_tree().process_frame"))
        for method, restored in (("_resume", "_pause_before_menu"),
                                 ("_return_to_title", "_pause_before_session")):
            body = function(code, method)
            order = ["_starting = true", "_pause.disable_menu()", "await _drain_input()",
                     "_pause.close()", f"get_tree().paused = {restored}", "_starting = false"]
            positions = [body.index(part) for part in order]
            self.assertEqual(positions, sorted(positions))
        retire = function(code, "_return_to_title")
        order = ["remove_child(_session)", "_session.free()", "_session = null",
                 "_title = TITLE.instantiate()", "add_child(_title)", "_connect_title()"]
        positions = [retire.index(part) for part in order]
        self.assertEqual(positions, sorted(positions))

    def test_menu_order_disabled_options_and_title_style(self):
        scene = read("scenes/application/pause_menu.tscn")
        ui = nodes(scene)
        prefix = "Overlay/Center/Menu/"
        options = ("Resume", "SaveGame", "LoadGame", "Settings", "MainMenu", "ExitGame")
        self.assertEqual([key.removeprefix(prefix) for key in ui
                          if key.startswith(prefix) and key != prefix + "Heading"], list(options))
        for name in ("SaveGame", "LoadGame", "Settings"):
            self.assertIn("disabled = true", ui[prefix + name][1])
            self.assertIn("focus_mode = 0", ui[prefix + name][1])
        for name, previous, following in (("Resume", "ExitGame", "MainMenu"),
                                          ("MainMenu", "Resume", "ExitGame"),
                                          ("ExitGame", "MainMenu", "Resume")):
            self.assertIn(f'focus_next = NodePath("../{following}")', ui[prefix + name][1])
            self.assertIn(f'focus_previous = NodePath("../{previous}")', ui[prefix + name][1])
        self.assertIn('text = "PAUSED"', ui[prefix + "Heading"][1])
        self.assertIn('type="CenterContainer"', scene)
        self.assertIn("Color(0.02, 0.03, 0.04, 0.78)", ui["Overlay"][1])
        title = read("scenes/application/title_screen.tscn")
        # Exact typography and all button states match the existing title.
        for text in (title, scene):
            self.assertIn("IBMPlexSans-Regular.ttf", text)
            self.assertIn("IBMPlexSans-Medium.ttf", text)
        theme = lambda text: text[text.index('[sub_resource type="StyleBoxEmpty"'):text.index('[node name=')]
        self.assertEqual(theme(scene), theme(title))

    def test_confirmation_paths_and_escape_cannot_confirm(self):
        code = read("scenes/application/pause_menu.gd")
        ready = function(code, "_ready")
        for button, destination in (("MainMenu", "main_menu"), ("ExitGame", "exit")):
            self.assertIn(f'get_node("{button}").pressed.connect(_ask.bind(&"{destination}"))', ready)
        ask = function(code, "_ask")
        self.assertIn('"Return to Main Menu?"', ask)
        self.assertIn('"Exit Game?"', ask)
        self.assertIn('get_node("Actions/Cancel").grab_focus()', ask)
        handler = function(code, "_input")
        self.assertIn('_destination != &""', handler)
        self.assertIn("_cancel()", handler)
        self.assertIn("resume_requested.emit()", handler)
        self.assertNotIn("_confirm()", handler)
        cancel = function(code, "_cancel")
        self.assertNotIn("requested.emit", cancel)
        self.assertIn("_menu.show()", cancel)
        confirm = function(code, "_confirm")
        self.assertIn("main_menu_requested.emit()", confirm)
        self.assertIn("exit_requested.emit()", confirm)
        scene = read("scenes/application/pause_menu.tscn")
        self.assertIn('text = "Any progress since your last save will be lost."', scene)
        self.assertNotIn("PackedScene", scene)

    def test_gameplay_and_assets_match_merged_shell_baseline(self):
        protected = ["construction", "inventory", "scenes/main", "scenes/player", "scenes/ui",
                     "scenes/world", "assets", "dialogue", "objectives", "project.godot", "tools",
                     "AGENTS.md", "docs/LOCAL_TESTING.md", "docs/experiments"]
        changed = subprocess.check_output(["git", "diff", "--name-only",
            "f92e8111b2fdcb0d88b4ebe336ca25c2f849c4d1", "--", *protected], cwd=ROOT, text=True)
        self.assertFalse(set(changed.splitlines()) - verified_initial_paths() - verified_codec_runner_paths() - verified_north_idle_paths() - verified_south_idle_paths(), changed)


if __name__ == "__main__":
    unittest.main()
