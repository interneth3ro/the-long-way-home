"""Nonexecuting machine artwork, layout and interaction preservation checks."""
import hashlib
import math
import struct
import subprocess
import unittest
import zlib

from static_automatic_transitions_test import ROOT, read
from static_extractor_inspection_test import functions
from static_weathered_earth_test import INPUT_SHA256, verify_input
from static_low_green_ground_test import ASSETS as GREEN_ASSETS
from static_v2_production_host_test import (
    MACHINE_ICONS_BASE, MACHINE_ICONS_SHA256, without_machine_icon_changes,
    MACHINE_LAYOUT_BASE, MACHINE_LAYOUT_SHA256, without_machine_layout_changes,
)

ART = {
    "extractor": ("3e4db4d251dbc0914dd4c9d68d2f771a52691176c147c68e89caf958047697ea", (23, 23, 232, 232)),
    "smelter": ("461f5eecd9c0096bee40d5cbc20b53e9eb525e79ead538c422d82b72468b3e60", (23, 39, 232, 216)),
    "fabricator": ("623ba4f0e119eec180d9a4c1245ec9e119c185861a16c771ab66a5304b9a31fd", (23, 46, 232, 208)),
}


def baseline(path):
    return subprocess.check_output(["git", "show", f"{MACHINE_ICONS_BASE}:{path}"], cwd=ROOT).decode().replace("\r\n", "\n")


def node(scene, name):
    return scene.split(f'[node name="{name}"', 1)[1].split('[node ', 1)[0]


def rgba_pixels(raw):
    """Verify PNG CRCs and unfilter the supplied noninterlaced RGBA scanlines."""
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    pos, compressed, ended = 8, bytearray(), False
    while pos < len(raw):
        length = struct.unpack_from(">I", raw, pos)[0]
        kind, data = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + length]
        assert zlib.crc32(kind + data) == struct.unpack_from(">I", raw, pos + 8 + length)[0]
        if kind == b"IHDR":
            assert struct.unpack(">IIBBBBB", data) == (256, 256, 8, 6, 0, 0, 0)
        if kind == b"IDAT":
            compressed.extend(data)
        if kind == b"IEND":
            assert length == 0
            ended = True
        pos += 12 + length
    assert pos == len(raw) and ended
    scan = zlib.decompress(compressed)
    assert len(scan) == 256 * 1025
    previous, pixels = bytearray(1024), bytearray()
    for y in range(256):
        kind = scan[y * 1025]
        assert kind in range(5)
        row = bytearray(scan[y * 1025 + 1:(y + 1) * 1025])
        for i in range(1024):
            a, b, c = row[i - 4] if i >= 4 else 0, previous[i], previous[i - 4] if i >= 4 else 0
            if kind == 0:
                predictor = 0
            elif kind == 1:
                predictor = a
            elif kind == 2:
                predictor = b
            elif kind == 3:
                predictor = (a + b) // 2
            else:
                p = a + b - c
                distances = (abs(p - a), abs(p - b), abs(p - c))
                predictor = (a, b, c)[distances.index(min(distances))]
            row[i] = (row[i] + predictor) % 256
        pixels.extend(row)
        previous = row
    return pixels


class MachineIconsStaticTest(unittest.TestCase):
    def test_exact_candidate_pins_retain_history_and_reject_tampering(self):
        for path in MACHINE_ICONS_SHA256:
            text = read(path)
            self.assertEqual(without_machine_icon_changes(path, text), baseline(path))
            for changed in (text.replace("\n", "\nCHANGED\n", 1), text + text, text + "UNRELATED\n"):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    without_machine_icon_changes(path, changed)
        self.assertEqual(without_machine_icon_changes("unrelated.gd", "sentinel"), "sentinel")

    def test_supplied_png_bytes_crc_alpha_bounds_and_shared_mapping(self):
        helper = read("scenes/ui/item_presentation.gd")
        for item, (digest, expected_bounds) in ART.items():
            raw = (ROOT / f"assets/items/{item}.png").read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            pixels = rgba_pixels(raw)
            alpha = pixels[3::4]
            self.assertIn(0, alpha)
            self.assertIn(255, alpha)
            points = [(i % 256, i // 256) for i, a in enumerate(alpha) if a]
            bounds = (min(x for x, y in points), min(y for x, y in points),
                      max(x for x, y in points), max(y for x, y in points))
            self.assertEqual(bounds, expected_bounds)
            self.assertTrue(all(0 < edge < 255 for edge in bounds))
            self.assertIn(f'&"{item}": preload("res://assets/items/{item}.png")', helper)
        # All helper behavior outside the mapping is byte-preserved.
        self.assertEqual(helper.split("static func", 1)[1], baseline("scenes/ui/item_presentation.gd").split("static func", 1)[1])

    def test_lossless_imports_and_aspect_filtering(self):
        for item in ART:
            path = f"res://assets/items/{item}.png"
            metadata = read(f"assets/items/{item}.png.import")
            self.assertIn(f'source_file="{path}"', metadata)
            cache = f"res://.godot/imported/{item}.png-{hashlib.md5(path.encode()).hexdigest()}.ctex"
            self.assertEqual(metadata.count(cache), 2)
            uid = metadata.split('uid="', 1)[1].split('"', 1)[0]
            self.assertRegex(uid, r"^uid://[a-y0-8]{1,13}$")
            alphabet = "abcdefghijklmnopqrstuvwxy012345678"
            value = 0
            for character in uid[6:]:
                value = value * 34 + alphabet.index(character)
            self.assertTrue(0 < value <= 0x7fffffffffffffff)
            expected = read("assets/items/ferrite_ore.png.import")
            old_uid = expected.split('uid="', 1)[1].split('"', 1)[0]
            old_cache = "res://.godot/imported/ferrite_ore.png-e72a2a5c55de84c2790e8907dc818856.ctex"
            expected = expected.replace(old_uid, uid).replace(old_cache, cache).replace("res://assets/items/ferrite_ore.png", path)
            self.assertEqual(metadata, expected)
            for setting in ("compress/mode=0", "mipmaps/generate=true", "process/fix_alpha_border=true", "process/premult_alpha=false"):
                self.assertIn(setting, metadata)
        for path in ("scenes/ui/inventory_ui.gd", "scenes/ui/hotbar_ui.gd"):
            text = read(path)
            self.assertIn("TextureRect.EXPAND_IGNORE_SIZE", text)
            self.assertIn("TextureRect.STRETCH_KEEP_ASPECT_CENTERED", text)
            self.assertIn("CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS", text)

    def test_capacity_order_overflow_and_all_action_methods_are_unchanged(self):
        for path, allowed in (("scenes/ui/inventory_ui.gd", {"_ready", "_create_slots", "_fit_panel"}),
                              ("scenes/ui/hotbar_ui.gd", {"_ready"})):
            before, after = functions(baseline(path)), functions(read(path))
            self.assertEqual(set(after) - set(before), {"_fit_panel"} if "inventory" in path else set())
            for method in set(before) - allowed:
                self.assertEqual(after[method], before[method], (path, method))
            for fallback in ('get(item.item_id, "?")' if "inventory" in path else 'get(definition.item_id, "?")',):
                self.assertIn(fallback, read(path))
        inventory = read("scenes/ui/inventory_ui.gd")
        self.assertIn("const MATERIAL_SLOTS := 24", inventory)
        self.assertIn("const EQUIPMENT_SLOTS := 8", inventory)
        self.assertIn("_create_slots(_equipment, EQUIPMENT_SLOTS, EQUIPMENT_SLOT_SIZE)", inventory)
        self.assertIn("const SLOT_SIZE := Vector2(50, 50)", inventory)
        self.assertIn("const EQUIPMENT_SLOT_SIZE := Vector2(70, 70)", inventory)
        hotbar = read("scenes/ui/hotbar_ui.gd")
        self.assertIn("for index in PlaythroughState.HOTBAR_SIZE:", hotbar)
        self.assertIn("slot.custom_minimum_size = Vector2(60, 60)", hotbar)
        # Only artwork/geometry differs within construction of the slots.
        self.assertIn('slot.pressed.connect(_activate.bind(index))', hotbar)
        self.assertIn('slot.gui_input.connect(_slot_input.bind(index, slot))', hotbar)

    def test_grid_bounds_and_source_alpha_clearance_above_quantity_bands(self):
        inventory = read("scenes/ui/inventory_ui.gd")
        scene = read("scenes/ui/inventory_ui.tscn")
        self.assertIn("columns = 8", node(scene, "Materials"))
        self.assertIn("columns = 6", node(scene, "Equipment"))
        self.assertIn("size_flags_horizontal = 0", node(scene, "Equipment"))
        self.assertIn("offset_right = 496.0", node(scene, "Panel"))
        self.assertEqual(6 * 70 + 5 * 4 + 32, 496 - 24)
        self.assertLessEqual(8 * 50 + 7 * 4, 6 * 70 + 5 * 4)
        self.assertEqual(math.ceil(8 / 6), 2)
        self.assertIn("var icon_half := 28 if equipment else 17", inventory)
        self.assertIn("var icon_top := 0 if equipment else 3", inventory)
        self.assertIn("icon.offset_bottom = icon_top + icon_half * 2", inventory)
        self.assertIn("quantity.offset_top = -16", inventory)
        self.assertLess(inventory.index("slot.add_child(icon)"), inventory.index("icon.set_anchors_and_offsets_preset"))
        for digest, bounds in ART.values():
            self.assertLess((bounds[3] + 1) * 56 / 256, 70 - 16)
            self.assertLess((bounds[3] + 1) * 46 / 256, 44)
        # Ferrite geometry stays at its approved 34-unit canvas and y=3 inset.
        for bottom in (227, 221, 210, 228):
            self.assertLess(3 + (bottom + 1) * 34 / 256, 50 - 16)
        hotbar = read("scenes/ui/hotbar_ui.gd")
        self.assertIn("icon.position = Vector2(7, 0)", hotbar)
        self.assertIn("icon.size = Vector2(46, 46)", hotbar)
        self.assertIn('Vector2(0, 64), 13)', hotbar)
        self.assertIn('key.size.x = 60', hotbar)
        self.assertIn('key.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER', hotbar)
        self.assertIn('key.theme_type_variation = &"B1MutedLabel"', hotbar)
        self.assertIn('Vector2(4, 44), 12)', hotbar)
        self.assertIn("quantity.size.x = 52", hotbar)
        self.assertIn("backing.content_margin_top = 4.0", hotbar)

    def test_supported_window_scale_bounds_and_adjacent_hud_clearance(self):
        scene = read("scenes/ui/hotbar_ui.tscn")
        backing = node(scene, "Backing")
        for line in ("offset_left = -331.0", "offset_right = 331.0", "offset_top = -101.0", "offset_bottom = -33.0"):
            self.assertIn(line, backing)
        self.assertEqual(10 * 60 + 9 * 6 + 8, 662)
        self.assertEqual(4 + 60 + 4, 101 - 33)
        # External key hints start four units below each 60-unit button, outside
        # the backing. A 17-unit key line ends 16 units above the viewport edge.
        self.assertGreater(64, 60)
        self.assertEqual(-101 + 4 + 64 + math.ceil(13 * 1.3), -16)
        self.assertEqual(-101 + 4 + 64, -33)
        # 12pt quantities fit the 16-unit bottom band.
        self.assertLessEqual(math.ceil(12 * 1.3), 16)
        # Inventory upper bound: real Plex hhea ratio 1.3, rounded line heights;
        # 24 material slots (3 rows), eight equipment slots (2 rows), full overflow;
        # title line includes its existing four-unit StyleBoxEmpty bottom margin.
        font = (ROOT / "assets/fonts/ibm-plex-sans/IBMPlexSans-Regular.ttf").read_bytes()
        tables = {}
        for i in range(struct.unpack_from(">H", font, 4)[0]):
            tag, _, offset, _ = struct.unpack_from(">4sIII", font, 12 + i * 16)
            tables[tag] = offset
        em = struct.unpack_from(">H", font, tables[b"head"] + 18)[0]
        ascent, descent, gap = struct.unpack_from(">hhh", font, tables[b"hhea"] + 4)
        self.assertEqual((ascent - descent + gap) / em, 1.3)
        theme = read("assets/ui/b1_theme.tres")
        self.assertIn('[sub_resource type="StyleBoxEmpty" id="TitleSpacing"]\ncontent_margin_bottom = 4.0', theme)
        panel_height = 28 + 3 * 19 + 158 + 4 + 144 + 64 + 7 * 4 + 28
        self.assertEqual(panel_height, 511)
        inventory = read("scenes/ui/inventory_ui.gd")
        self.assertIn("_panel.minimum_size_changed.connect(_fit_panel, CONNECT_DEFERRED)", inventory)
        self.assertIn("$HUD.scale_changed.connect(_fit_panel)", inventory)
        self.assertIn("minf(100.0, maxf(12.0, $HUD.size.y - _panel.size.y - 117.0))", inventory)
        for width, height in ((1024, 576), (1280, 720), (1920, 1080)):
            for preference in (.75, .85, 1.0):
                scale = preference * math.sqrt(min(width / 1280, height / 720))
                logical_width, logical_height = width / scale, height / scale
                self.assertLess(662 + 32, logical_width)
                self.assertLess(496 + 16, logical_width)
                panel_y = min(100, max(12, logical_height - panel_height - 117))
                self.assertLessEqual(panel_y + panel_height + 117, logical_height)
        # Existing conversation/musing reservations stay intact, above backing.
        self.assertIn("104", read("scenes/ui/dialogue_ui.gd"))
        self.assertIn("112", read("scenes/ui/musing_ui.gd"))
        self.assertLess(101, 104)
        self.assertLess(101, 112)

    def test_layout_refinement_pins_preserve_initial_pr_and_approved_rendering(self):
        for path in MACHINE_LAYOUT_SHA256:
            text = read(path)
            original = subprocess.check_output(["git", "show", f"{MACHINE_LAYOUT_BASE}:{path}"], cwd=ROOT).decode().replace("\r\n", "\n")
            self.assertEqual(without_machine_layout_changes(path, text), original)
            for changed in (text.replace("\n", "\nCHANGED\n", 1), text + text, text + "UNRELATED\n"):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    without_machine_layout_changes(path, changed)
            if path.endswith(".gd"):
                before, after = functions(original), functions(text)
                self.assertEqual(before.keys(), after.keys())
                changed_methods = {"_ready", "_fit_panel"} if "inventory" in path else {"_ready"}
                for method in before.keys() - changed_methods:
                    self.assertEqual(after[method], before[method], (path, method))
                if "hotbar" in path:
                    # Only padding and key hints change; icons, quantities,
                    # symbols and button callbacks keep the approved rendering.
                    for first, last in (("\t\tvar icon :=", "\t\t# External hints"),
                                        ("\t\tvar symbol :=", "\tprogression.hotbar_changed")):
                        current = text.split(first, 1)[1].split(last, 1)[0]
                        original_last = '\t\t_add_label(slot, "Key"' if "icon" in first else last
                        previous = original.split(first, 1)[1].split(original_last, 1)[0]
                        self.assertEqual(current, previous)
        self.assertEqual(without_machine_layout_changes("unrelated.gd", "sentinel"), "sentinel")
        # Every approved icon, import and canonical mapping is unchanged by
        # this owner refinement, including owner-local sidecar bytes.
        for item in (*ART, "ferrite_ore", "ferrite_ingot", "ferrite_plate", "ferrite_rod"):
            for suffix in (".png", ".png.import"):
                path = f"assets/items/{item}{suffix}"
                original = subprocess.check_output(["git", "show", f"{MACHINE_LAYOUT_BASE}:{path}"], cwd=ROOT)
                actual = (ROOT / path).read_bytes()
                if suffix.endswith(".import"):
                    original, actual = original.replace(b"\r\n", b"\n"), actual.replace(b"\r\n", b"\n")
                self.assertEqual(actual, original, path)
        self.assertEqual(read("scenes/ui/item_presentation.gd"), subprocess.check_output(
            ["git", "show", f"{MACHINE_LAYOUT_BASE}:scenes/ui/item_presentation.gd"], cwd=ROOT).decode().replace("\r\n", "\n"))

    def test_inventory_shrinks_to_content_without_resize_feedback_or_fixed_height(self):
        text = read("scenes/ui/inventory_ui.gd")
        fitting = functions(text)["_fit_panel"]
        self.assertLess(fitting.index("_panel.reset_size()"), fitting.index("_panel.position.y"))
        self.assertNotIn("_panel.resized.connect", text)
        self.assertIn("minimum_size_changed.connect(_fit_panel, CONNECT_DEFERRED)", text)
        self.assertIn("_fit_panel.call_deferred()", text)
        self.assertNotIn("_panel.size =", fitting)
        scene = read("scenes/ui/inventory_ui.tscn")
        panel = node(scene, "Panel")
        self.assertNotIn("anchor_bottom = 1", panel)
        self.assertNotIn("custom_minimum_size", panel)
        self.assertIn("custom_minimum_size = Vector2(0, 64)", node(scene, "Overflow"))
        self.assertIn("visible = false", node(scene, "Overflow"))
        # Content-driven normal height omits the hidden overflow's 64-unit
        # strip and its one four-unit separation. It can grow then shrink back.
        full_height = 511
        normal_height = full_height - 64 - 4
        self.assertEqual(normal_height, 443)
        self.assertLess(normal_height, full_height)
        for height in (normal_height, full_height, normal_height):
            for width, window_height in ((1024, 576), (1280, 720), (1920, 1080)):
                for preference in (.75, .85, 1.0):
                    logical_height = window_height / (preference * math.sqrt(min(width / 1280, window_height / 720)))
                    y = min(100, max(12, logical_height - height - 117))
                    self.assertLessEqual(y + height + 117, logical_height)

    def test_protected_assets_gameplay_and_execution_controls_match_pr91(self):
        changed = subprocess.check_output([
            "git", "diff", "--name-only", MACHINE_ICONS_BASE, "--", "assets", "scenes",
            "inventory", "construction", "dialogue", "world", "objectives", "project.godot",
            "AGENTS.md", "tools", "docs/LOCAL_TESTING.md", "tests/fabricator_recipe_switching_test.gd",
        ], cwd=ROOT, text=True).splitlines()
        # Exact Weathered Earth candidates only; no path-wide exemption and no
        # Native permission expansion. Review this amendment before Native use.
        for path in set(changed) & set(INPUT_SHA256):
            verify_input(path, (ROOT / path).read_bytes())
        # Original PR #95 introduced these four PNGs. Pin each candidate's
        # bytes before permitting its exact path through this historical guard.
        green_assets = {
            f"assets/environment/exterior/low_green_ground_cover_provisional/{name}.png": digest
            for name, digest in GREEN_ASSETS.items()
        }
        for path in set(changed) & set(green_assets):
            self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), green_assets[path], path)
        allowed = set(MACHINE_ICONS_SHA256) | set(INPUT_SHA256) | set(green_assets) | {
            f"assets/items/{item}.png{suffix}" for item in ART for suffix in ("", ".import")
        }
        self.assertFalse(set(changed) - allowed, set(changed) - allowed)


if __name__ == "__main__":
    unittest.main()
