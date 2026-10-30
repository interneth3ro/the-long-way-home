"""Nonexecuting presentation integration; no Godot or gameplay execution."""
import hashlib
import re
import subprocess
import unittest
from static_automatic_transitions_test import ROOT, read
from static_extractor_inspection_test import functions
from static_v2_production_host_test import FABRICATOR_BASE, without_fabricator_changes


# Proposed chooser presentation bytes; owner approval required before Native use.
# Pin the complete candidate, then retain the original immutable comparison.
CHOOSER_SHA256 = {
    "scenes/ui/fabricator_inspection.gd": "71d64127565cc739cc94085455a80988ef7206c64a2966d0a5efe0edfb2318a4",
    "scenes/ui/fabricator_inspection.tscn": "89fb92c1968ce7699031069f02f650fe0cbbb70a300a402792496596d9dd3335",
    "scenes/ui/recipe_card_content.gd": "dfca9e010019397c4ad579cb9a4072d01808215f1430dda4f7a1c0ae14b33140",
    "scenes/ui/recipe_card_content.gd.uid": "97619be08f17930fbf4e87d683b8f0f46d7a5c8272ed7f1af44c87b4707b88cd",
    "assets/ui/recipe_chooser.tres": "0be69e2cf39d05b123874b1ddd829b3ddb76c2497f3e8e07fff49ee69e994be9",
}


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
                actual = without_fabricator_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                expected = expected.replace(b"\r\n", b"\n")
            self.assertEqual(actual, expected, path)

    def test_shared_gauge_correction_preserves_state_and_machine_layouts(self):
        base = "32958a6142f0314440df9bb8eeb9a9d53e438a4c"
        gauge = read("scenes/ui/cycle_gauge.gd")
        before = subprocess.check_output(["git", "show", f"{base}:scenes/ui/cycle_gauge.gd"],
                                         cwd=ROOT).decode().replace("\r\n", "\n")
        self.assertEqual(gauge.split("func _draw()", 1)[0], before.split("func _draw()", 1)[0])
        for path in ("scenes/ui/fabricator_inspection.gd", "scenes/ui/fabricator_inspection.tscn",
                     "scenes/ui/extractor_inspection.gd", "scenes/ui/extractor_inspection.tscn",
                     "scenes/ui/smelter_inspection.gd", "scenes/ui/smelter_inspection.tscn",
                     "scenes/ui/machine_ui.gd", "scenes/ui/machine_ui.tscn"):
            approved = subprocess.check_output(["git", "show", f"{base}:{path}"], cwd=ROOT)
            actual = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
            if path in CHOOSER_SHA256:
                self.assertEqual(hashlib.sha256(actual).hexdigest(), CHOOSER_SHA256[path], path)
                actual = approved.replace(b"\r\n", b"\n")
            self.assertEqual(actual, approved.replace(b"\r\n", b"\n"), path)

    def test_chooser_candidate_and_gameplay_boundary(self):
        for path, digest in CHOOSER_SHA256.items():
            self.assertEqual(hashlib.sha256(read(path).encode()).hexdigest(), digest, path)
        base = "52792154be2bb3f1b1bb7cd3ef6eb9fdb6204b35"
        # Entire controller stays frozen, including selection, pause and layout.
        controller = subprocess.check_output(["git", "show", f"{base}:scenes/ui/machine_ui.gd"], cwd=ROOT)
        self.assertEqual(read("scenes/ui/machine_ui.gd"), controller.decode().replace("\r\n", "\n"))
        before = functions(subprocess.check_output(["git", "show", f"{base}:scenes/ui/fabricator_inspection.gd"], cwd=ROOT).decode().replace("\r\n", "\n"))
        after = functions(read("scenes/ui/fabricator_inspection.gd"))
        for name in ("_ready", "set_compact", "_build_ingredients"):
            self.assertEqual(before[name], after[name])
        self.assertEqual(before["refresh"].split("\tvar accent :=", 1)[1],
                         after["refresh"].split("\tvar accent :=", 1)[1])
        scene_before = subprocess.check_output(["git", "show", f"{base}:scenes/ui/fabricator_inspection.tscn"], cwd=ROOT).decode().replace("\r\n", "\n")
        scene_after = read("scenes/ui/fabricator_inspection.tscn")
        # Both normal inspection columns remain byte-identical.
        start = '[node name="Columns"'
        end = '[node name="Chooser"'
        self.assertEqual(scene_before.split(start, 1)[1].split(end, 1)[0],
                         scene_after.split(start, 1)[1].split(end, 1)[0])

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
