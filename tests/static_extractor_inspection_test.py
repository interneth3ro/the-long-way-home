"""Nonexecuting pilot integration checks; not Godot parsing or visual validation."""

import re
import subprocess
import unittest

from static_automatic_transitions_test import ROOT, read


BASE = "17c67d8c4bbab3a799686c30f341b1f602231640"


def baseline(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def functions(text):
    return dict(re.findall(r"^func (\w+)(.*?)(?=^func |\Z)", text, re.M | re.S))


class ExtractorInspectionStaticTest(unittest.TestCase):
    def test_existing_machine_actions_range_and_recipe_lifecycle_preserved(self):
        path = "scenes/ui/machine_ui.gd"
        before, after = functions(baseline(path)), functions(read(path))
        presentation_edits = {"_ready", "_show_machine", "close", "_exit_tree", "_refresh"}
        for name in before.keys() - presentation_edits:
            with self.subTest(function=name):
                self.assertEqual(before[name], after[name])
        # Strip the Extractor-only display update and compare the complete
        # Smelter/Fabricator dispatch and fixed-machine refresh with main.
        anchor = '\t_title.text = definition.display_name\n'
        extractor_update = ('\tif extractor:\n'
                            '\t\t_extractor_view.refresh(machine, progression.planet.machine_status(machine), _in_range(machine))\n'
                            '\t\t_layout_extractor()\n')
        self.assertEqual(after["_refresh"].count(extractor_update), 1)
        self.assertEqual(before["_refresh"].split(anchor, 1)[1],
                         after["_refresh"].split(anchor, 1)[1].replace(extractor_update, "", 1))

    def test_legacy_scene_content_and_connections_preserved(self):
        path = "scenes/ui/machine_ui.tscn"
        text = read(path).replace("load_steps=6", "load_steps=5", 1)
        text = text.replace('[ext_resource type="PackedScene" path="res://scenes/ui/extractor_inspection.tscn" id="4_extractor"]\n', "", 1)
        text = text.replace('[node name="ExtractorInspection" parent="HUD/Panel" instance=ExtResource("4_extractor")]\nvisible = false\nlayout_mode = 2\n\n', "", 1)
        self.assertEqual(text, baseline(path))

    def test_tracker_override_does_not_mutate_player_preference(self):
        path = "scenes/ui/objective_tracker.gd"
        before, after = functions(baseline(path)), functions(read(path))
        for name in before.keys() - {"_refresh_visibility"}:
            self.assertEqual(before[name], after[name])
        override = after["set_machine_inspection_open"]
        self.assertNotRegex(override, r"_(?:presentation|expanded)\s*=")
        self.assertTrue(after["_refresh_visibility"].endswith(before["_refresh_visibility"].split("\n", 1)[1]))
        self.assertIn('from="MachineUI" to="ObjectiveTracker" method="set_machine_inspection_open"',
                      read("scenes/main/main.tscn"))
        machine = functions(read("scenes/ui/machine_ui.gd"))
        self.assertIn("inspection_visibility_changed.emit(true)", machine["_show_machine"])
        for name in ("close", "_exit_tree"):
            self.assertIn("inspection_visibility_changed.emit(false)", machine[name])


if __name__ == "__main__":
    unittest.main()
