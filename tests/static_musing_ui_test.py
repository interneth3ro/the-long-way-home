"""Nonexecuting musing presentation/preservation checks; no gameplay execution."""
import hashlib
import re
import struct
import subprocess
import unittest

from static_automatic_transitions_test import ROOT, read
from static_v2_production_host_test import MUSING_BASE, MUSING_SHA256, without_musing_changes


class MusingUIStaticTest(unittest.TestCase):
    def test_exact_allowance_retains_history_and_rejects_tampering(self):
        for path in MUSING_SHA256:
            original = read(path)
            historical = subprocess.check_output(
                ["git", "show", f"{MUSING_BASE}:{path}"], cwd=ROOT
            ).decode().replace("\r\n", "\n")
            self.assertEqual(without_musing_changes(path, original), historical)
            for changed in (original.replace("\n", "\nCHANGED\n", 1),
                            original + original, original + "UNRELATED\n"):
                with self.subTest(path=path):
                    with self.assertRaises(AssertionError):
                        without_musing_changes(path, changed)
        self.assertEqual(without_musing_changes("unrelated.gd", "sentinel"), "sentinel")

    def test_narrative_progression_and_adjacent_ui_preserved(self):
        paths = [
            "scenes/main/main.gd", "scenes/main/main.tscn", "scenes/main/main_v2.gd",
            "scenes/main/playthrough_state.gd", "scenes/main/scene_transition_controller.gd",
            "scenes/player/interaction_detector.gd", "scenes/ui/dialogue_ui.gd",
            "scenes/ui/dialogue_ui.tscn", "scenes/ui/inventory_ui.gd",
            "scenes/ui/hotbar_ui.gd", "scenes/ui/machine_ui.gd",
            "scenes/ui/objective_tracker.gd", "scenes/ui/ui_scale_root.gd",
            "assets/ui/b1_theme.tres", "project.godot", "tools/run-local-tests.ps1",
            "tests/fabricator_recipe_switching_test.gd", "docs/LOCAL_TESTING.md",
            "dialogue/musing_definition.gd", "dialogue/computer_opening.tres",
            "dialogue/ferrite_discovery.tres", "dialogue/extractor_recovery.tres",
            "dialogue/ferrite_acquisition.tres", "dialogue/ferrite_ingot_acquisition.tres",
        ]
        for path in paths:
            with self.subTest(path=path):
                historical = subprocess.check_output(
                    ["git", "show", f"{MUSING_BASE}:{path}"], cwd=ROOT
                ).decode().replace("\r\n", "\n")
                self.assertEqual(read(path), historical)

    def test_scene_paths_passivity_and_real_italic_face(self):
        scene, script = read("scenes/ui/musing_ui.tscn"), read("scenes/ui/musing_ui.gd")
        nodes = {}
        for block in re.split(r'(?=\[node )', scene)[1:]:
            name, parent = re.search(r'name="([^"]+)".*?(?:parent="([^"]+)")?\]', block.splitlines()[0]).groups()
            # Parse parent separately because the optional regexp may skip it.
            match = re.search(r'parent="([^"]+)"', block.splitlines()[0])
            parent = match.group(1) if match else None
            path = name if not parent or parent == "." else parent + "/" + name
            nodes[path] = block
            if name != "MusingUI":
                self.assertIn("mouse_filter = 2", block)
        for path in re.findall(r'\$([A-Za-z][A-Za-z0-9_/]*)', script):
            self.assertIn(path, nodes)
        self.assertNotRegex(script, r'func _(?:unhandled_)?(?:key_)?input\(')
        self.assertNotIn('type="Button"', scene)
        self.assertIn('theme_override_fonts/font = ExtResource("3_italic")', nodes["HUD/Panel/Content/Scroll/Text"])
        self.assertIn('theme_override_fonts/font = ExtResource("4_medium")', nodes["HUD/Panel/Content/Identity/Speaker"])
        font = (ROOT / "assets/fonts/ibm-plex-sans/IBMPlexSans-Italic.ttf").read_bytes()
        self.assertEqual(hashlib.sha256(font).hexdigest(),
                         "a9c6ef9942c49e49d11e11a6dacc0b3a087978757e9b22a06b8ac22a6400fb15")
        # TrueType head.macStyle bit 1 identifies the actual italic face.
        tables = {}
        for offset in range(12, 12 + struct.unpack_from(">H", font, 4)[0] * 16, 16):
            tag, _, start, length = struct.unpack_from(">4sIII", font, offset)
            tables[tag] = font[start:start + length]
        self.assertTrue(struct.unpack_from(">H", tables[b"head"], 44)[0] & 2)


if __name__ == "__main__":
    unittest.main()
