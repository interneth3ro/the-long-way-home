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

    def test_refinement_preserves_initial_presentation_except_scoped_values(self):
        initial_commit = "f9f8968a9f153dc96ff1431b12eedddb5fba4b1b"
        candidates = {
            "scenes/ui/musing_ui.gd": (
                "bd8284da6e4155a404e425d279e099ab8532afc0284a094ad2ef60f2eb60d143",
                "const MAX_WIDTH := 360.0", "const MAX_WIDTH := 540.0"),
            "scenes/ui/musing_ui.tscn": (
                "f1d8df0de4aa78d52aec1d9f74def8a9094cb24491f2443a08e1726cd5b971d4",
                "theme_override_font_sizes/font_size = 18",
                "theme_override_font_sizes/font_size = 16"),
        }
        def before_border_refinement(path):
            current = read(path)
            if path.endswith(".tscn"):
                current = current.replace("border_color = Color(0.29, 0.40, 0.43, 0.5)",
                                          "border_color = Color(0.29, 0.40, 0.43, 0.8)", 1)
            return current

        for path, (digest, old, new) in candidates.items():
            with self.subTest(path=path):
                initial = subprocess.check_output(
                    ["git", "show", f"{initial_commit}:{path}"], cwd=ROOT
                ).decode().replace("\r\n", "\n")
                self.assertEqual(hashlib.sha256(initial.encode()).hexdigest(), digest)
                self.assertEqual(initial.count(old), 1)
                self.assertEqual(before_border_refinement(path), initial.replace(old, new, 1))

        # Retain the first refinement as well: this follow-up changes one value.
        previous_commit = "97fe4a5"
        for path in candidates:
            previous = subprocess.check_output(
                ["git", "show", f"{previous_commit}:{path}"], cwd=ROOT
            ).decode().replace("\r\n", "\n")
            if path.endswith(".gd"):
                self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),
                                 "cec8d2db14c9d6076ab27813b4d9780bc0376f3b606d94686010f3a0509803a6")
                previous = previous.replace("const MAX_WIDTH := 440.0", "const MAX_WIDTH := 540.0", 1)
            self.assertEqual(before_border_refinement(path), previous)

    def test_border_refinement_preserves_layout_and_inset_frame_geometry(self):
        path = "scenes/ui/musing_ui.tscn"
        previous = subprocess.check_output(
            ["git", "show", f"e2c203e:{path}"], cwd=ROOT
        ).decode().replace("\r\n", "\n")
        self.assertEqual(hashlib.sha256(previous.encode()).hexdigest(),
                         "04a4c060faccd3a4b8eba7daa4c04c150c3962ec29676a7d1efbe51de7eae839")
        old = "border_color = Color(0.29, 0.40, 0.43, 0.8)"
        new = "border_color = Color(0.29, 0.40, 0.43, 0.5)"
        self.assertEqual(previous.count(old), 1)
        self.assertEqual(read(path), previous.replace(old, new, 1))
        style = read(path).split('[sub_resource type="StyleBoxFlat" id="MusingStyle"]', 1)[1].split("[node", 1)[0]
        for side in ("left", "top", "right", "bottom"):
            self.assertIn(f"border_width_{side} = 1\n", style)
        for corner in ("top_left", "top_right", "bottom_left", "bottom_right"):
            self.assertIn(f"corner_radius_{corner} = 2\n", style)
        # Default zero expansion/shadow keeps the StyleBox inside its panel rect.
        self.assertNotIn("expand_margin_", style)
        self.assertNotIn("shadow_", style)
        panel = read(path).split('[node name="Panel"', 1)[1].split('[node name="Content"', 1)[0]
        self.assertIn('theme_override_styles/panel = SubResource("MusingStyle")', panel)
        self.assertNotIn("clip_contents = true", read(path))

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
