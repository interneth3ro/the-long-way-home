"""Nonexecuting presentation integration; no Godot or gameplay execution."""
import re
import subprocess
import unittest
from static_automatic_transitions_test import ROOT, read
from static_extractor_inspection_test import functions
from static_v2_production_host_test import FABRICATOR_BASE


class FabricatorInspectionStaticTest(unittest.TestCase):
    def test_protected_methods_and_other_presentations_preserved(self):
        path = "scenes/ui/machine_ui.gd"
        before = functions(subprocess.check_output(["git", "show", f"{FABRICATOR_BASE}:{path}"],
                                                  cwd=ROOT).decode().replace("\r\n", "\n"))
        after = functions(read(path))
        for name in before.keys() - {"_ready", "_refresh"}:
            with self.subTest(function=name):
                self.assertEqual(before[name].rstrip(), after[name].rstrip())
        dispatch = "\tif _refresh_fabricator_shell(machine, definition):\n\t\treturn\n"
        self.assertEqual(after["_refresh"].count(dispatch), 1)
        self.assertEqual(before["_refresh"], after["_refresh"].replace(dispatch, "", 1))
        for path in ("scenes/ui/extractor_inspection.gd", "scenes/ui/extractor_inspection.tscn",
                     "scenes/ui/smelter_inspection.gd", "scenes/ui/smelter_inspection.tscn",
                     "scenes/ui/cycle_gauge.gd", "scenes/ui/ui_scale_root.gd",
                     "scenes/ui/objective_tracker.gd", "assets/ui/machine_actions.tres",
                     "tests/fabricator_recipe_switching_test.gd", "tools/run-local-tests.ps1",
                     "assets/environment/maintenance_bay_v2/machines/fabricator_stationary.png"):
            expected = subprocess.check_output(["git", "show", f"{FABRICATOR_BASE}:{path}"], cwd=ROOT)
            actual = (ROOT / path).read_bytes()
            if not path.endswith(".png"):
                actual = actual.replace(b"\r\n", b"\n")
                expected = expected.replace(b"\r\n", b"\n")
            self.assertEqual(actual, expected, path)

    def test_scene_paths_and_shared_components(self):
        scene = read("scenes/ui/fabricator_inspection.tscn")
        script = read("scenes/ui/fabricator_inspection.gd")
        paths = set()
        for name, parent in re.findall(r'\[node name="([^"]+)" type="[^"]+"(?: parent="([^"]+)")?', scene):
            paths.add(name if not parent else name if parent == "." else parent + "/" + name)
        for path in re.findall(r'\$([A-Za-z][A-Za-z0-9_/]*)', script):
            self.assertIn(path, paths)
        self.assertIn('path="res://scenes/ui/cycle_gauge.gd"', scene)
        self.assertIn('texture_filter = 4', scene)
        self.assertIn('expand_mode = 1', scene)
        self.assertIn('stretch_mode = 5', scene)
        self.assertIn('mipmaps/generate=true', read("assets/environment/maintenance_bay_v2/machines/fabricator_stationary.png.import"))
        # Header geometry stays identical to the final merged Smelter.
        start = '[sub_resource type="StyleBoxEmpty" id="HeaderTitleSpacing"]'
        end = '[node name="Columns"'
        smelter = read("scenes/ui/smelter_inspection.tscn").split(start, 1)[1].split(end, 1)[0]
        self.assertEqual(scene.split(start, 1)[1].split(end, 1)[0],
                         smelter.replace("SmelterInspection", "FabricatorInspection")
                         .replace('text = "SMELTER"', 'text = "FABRICATOR"'))


if __name__ == "__main__":
    unittest.main()
