"""Nonexecuting musing presentation/preservation checks; no gameplay execution."""
import hashlib
import re
import struct
import unittest

from static_automatic_transitions_test import ROOT, read


class MusingUIStaticTest(unittest.TestCase):
    def test_border_refinement_preserves_layout_and_inset_frame_geometry(self):
        path = "scenes/ui/musing_ui.tscn"
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


    def test_italic_staging_scope_metadata_and_historical_controls(self):
        sidecar = "assets/fonts/ibm-plex-sans/IBMPlexSans-Italic.ttf.import"
        data = (ROOT / sidecar).read_bytes()
        self.assertEqual(hashlib.sha256(data).hexdigest(),
                         "59dcbab3fc80589bdb874f68bfb1cd93e6d979fd96ff56787094500a56d62c20")
        self.assertNotIn(b"\r", data)
        self.assertIn(b'source_file="res://assets/fonts/ibm-plex-sans/IBMPlexSans-Italic.ttf"', data)
        regular = (ROOT / "assets/fonts/ibm-plex-sans/IBMPlexSans-Regular.ttf.import").read_bytes()
        self.assertEqual(data.split(b"[params]", 1)[1], regular.split(b"[params]", 1)[1])
        self.assertIn(sidecar + " text eol=lf", read(".gitattributes"))

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
