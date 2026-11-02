"""Nonexecuting presentation integration; no Godot or gameplay execution."""
import re
import unittest
from static_automatic_transitions_test import read


class FabricatorInspectionStaticTest(unittest.TestCase):
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
