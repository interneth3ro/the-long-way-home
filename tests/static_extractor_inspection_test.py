"""Nonexecuting pilot integration checks; not Godot parsing or visual validation."""

import re
import unittest

from static_automatic_transitions_test import read


def functions(text):
    return dict(re.findall(r"^func (\w+)(.*?)(?=^func |\Z)", text, re.M | re.S))


class ExtractorInspectionStaticTest(unittest.TestCase):
    def test_smelter_header_keeps_merged_extractor_geometry_and_frame_inset(self):
        extractor = read("scenes/ui/extractor_inspection.tscn")
        smelter = read("scenes/ui/smelter_inspection.tscn")
        start = '[sub_resource type="StyleBoxEmpty" id="HeaderTitleSpacing"]'
        end = '[node name="Columns"'
        approved = extractor.split(start, 1)[1].split(end, 1)[0]
        candidate = smelter.split(start, 1)[1].split(end, 1)[0]
        self.assertEqual(approved.replace("ExtractorInspection", "SmelterInspection")
                         .replace('text = "EXTRACTOR"', 'text = "SMELTER"'), candidate)
        machine = functions(read("scenes/ui/machine_ui.gd"))
        self.assertIn("_set_panel_padding(true)", machine["_layout_smelter"])
        # The existing inset helper is already compared byte-for-byte to main;
        # it applies content margins and compensating frame offsets together.
        self.assertIn("Vector4(24, 12, 24, 24)", machine["_set_panel_padding"])

    def test_tracker_override_does_not_mutate_player_preference(self):
        path = "scenes/ui/objective_tracker.gd"
        after = functions(read(path))
        override = after["set_machine_inspection_open"]
        self.assertNotRegex(override, r"_(?:presentation|expanded)\s*=")
        self.assertIn('from="MachineUI" to="ObjectiveTracker" method="set_machine_inspection_open"',
                      read("scenes/main/main.tscn"))
        machine = functions(read("scenes/ui/machine_ui.gd"))
        self.assertIn("inspection_visibility_changed.emit(true)", machine["_show_machine"])
        for name in ("close", "_exit_tree"):
            self.assertIn("inspection_visibility_changed.emit(false)", machine[name])


if __name__ == "__main__":
    unittest.main()
