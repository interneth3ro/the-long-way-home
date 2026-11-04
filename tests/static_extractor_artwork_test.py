"""Frozen static art contracts; no engine execution or graphical acceptance."""
import hashlib
import json
import re
import struct
import unittest

from current_preservation import git_blob
from extractor_artwork_offline import ROOT, INVENTORY, configured_layers
from static_automatic_transitions_test import function, nodes

BASE = "0a0003444be0ba4b67e7ab6c8fa678abbf740b34"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class ExtractorArtworkStaticTest(unittest.TestCase):
    def test_all_twelve_frozen_textures_sizes_offsets_and_imports(self):
        records = json.loads(INVENTORY.read_text())["directions"]
        configured = configured_layers()
        self.assertEqual([r["direction"] for r in records], [0, 90, 180, 270])
        for d, record in enumerate(records):
            self.assertEqual(record["master"]["size_px"], [1254, 1254])
            self.assertEqual(record["master"]["anchor_px"], [632, 1139])
            self.assertEqual(record["scale"], 0.11387900355871886)
            self.assertEqual([a["role"] for a in record["assets"]], ["body", "barrel", "foreground"])
            for i, asset in enumerate(record["assets"]):
                path, offset = configured[d * 3 + i]
                data = (ROOT / path).read_bytes()
                self.assertEqual(hashlib.sha256(data).hexdigest(), asset["sha256"])
                self.assertEqual(struct.unpack(">IIBB", data[16:26]), (*asset["exported_size_px"], 8, 6))
                self.assertEqual(list(offset), asset["anchor_relative_offset_px"])
                self.assertEqual([offset[0] + 632, offset[1] + 1139], asset["crop_rect_px"][:2])
                self.assertEqual(asset["crop_rect_px"][2:], asset["exported_size_px"])
                self.assertEqual(asset["draw_order"], i)
                self.assertEqual(asset["orientation_degrees_clockwise"], record["direction"])
                metadata = read(path + ".import")
                for setting in ["compress/mode=0", "mipmaps/generate=true", "process/size_limit=0",
                                f'source_file="res://{path}"']:
                    self.assertIn(setting, metadata)

    def test_anchor_scale_and_local_layer_sorting(self):
        scene = read("construction/extractor_visual.tscn")
        entries = nodes(scene)
        self.assertEqual(list(entries), ["ExtractorVisual", "Body", "Barrel", "Foreground"])
        self.assertIn("position = Vector2(64, 128)", scene)
        self.assertIn("scale = Vector2(0.11387900355871886, 0.11387900355871886)", scene)
        self.assertIn("texture_filter = 4", scene)  # LINEAR_WITH_MIPMAPS, local only.
        self.assertEqual(scene.count("centered = false"), 3)
        self.assertNotRegex(scene, r"z_index|y_sort_enabled|rotation|flip_[hv]|material")
        for point in [(632, 1139), (70, 15), (1194, 1139)]:
            world = (64 + (point[0] - 632) * (128 / 1124), 128 + (point[1] - 1139) * (128 / 1124))
            expected = {(632, 1139): (64, 128), (70, 15): (0, 0), (1194, 1139): (128, 128)}[point]
            for actual, value in zip(world, expected):
                self.assertAlmostEqual(actual, value)

    def test_direction_identity_and_no_dynamic_art(self):
        records = json.loads(INVENTORY.read_text())["directions"]
        for record, edge, halves in zip(records, ["right", "bottom", "left", "top"],
                                       [("upper", "lower"), ("right", "left"), ("lower", "upper"), ("left", "right")]):
            self.assertEqual([(p["id"], p["edge"], p["half"]) for p in record["output_ports"]],
                             [(1, edge, halves[0]), (2, edge, halves[1])])
        script = read("construction/extractor_visual.gd")
        self.assertIn("posmod(quarter_turns, 4)", script)
        self.assertIn("if direction == _turns:", script)
        self.assertNotRegex(script, r"func _(?:physics_)?process|Tween|AnimationPlayer|ImageTexture|JSON|FileAccess|status|rotation|flip_[hv]")

    def test_shared_adapter_and_composite_ghost(self):
        visual = read("construction/machine_visual.gd")
        refresh = function(visual, "_refresh_presentation")
        self.assertIn('definition.item_id == &"extractor"', refresh)
        self.assertIn("if is_ghost:", refresh)
        self.assertEqual(refresh.count("CanvasGroup.new()"), 1)
        self.assertIn("group.self_modulate = Color(1, 1, 1, 0.5)", refresh)
        self.assertIn("modulate = Color.WHITE if illustrated or not is_ghost", refresh)
        self.assertIn("_art_container.hide()", refresh)
        self.assertIn("_extractor.configure(turns)", refresh)
        self.assertNotIn("func _process", visual)
        self.assertIn('if definition == null or definition.item_id == &"extractor":', function(visual, "_draw"))
        for script in ["construction/deployed_machine.gd", "construction/construction_controller.gd"]:
            self.assertIn("MachineVisual.new()", read(script))
        controller = read("construction/construction_controller.gd")
        self.assertIn("_ghost.is_ghost = true", controller)
        original = git_blob(BASE, "construction/construction_controller.gd").decode().replace("\r\n", "\n")
        self.assertEqual(controller.replace("_ghost.is_ghost = true", "_ghost.modulate = Color(1, 1, 1, 0.5)"), original)

    def test_simulation_placement_other_machines_and_stationary_preserved(self):
        for path in ["inventory/extractor.tres", "inventory/smelter.tres", "inventory/fabricator.tres",
                     "construction/machine_definition.gd", "construction/placement_rules.gd",
                     "construction/deployed_machine.gd", "scenes/world/planet_world_state.gd",
                     "scenes/world/world_coordinates.gd", "scenes/world/planet_exterior.gd",
                     "scenes/world/planet_exterior.tscn", "scenes/player/dave.tscn",
                     "scenes/player/interaction_detector.gd", "scenes/ui/machine_ui.gd",
                     "scenes/visuals/extractor_stationary.tscn", "scenes/world/stationary_machine_presentation.gd",
                     "project.godot", "assets/environment/maintenance_bay_v2/machines/extractor_stationary.png",
                     "assets/environment/maintenance_bay_v2/machines/extractor_stationary.png.import"]:
            with self.subTest(path=path):
                data, original = (ROOT / path).read_bytes(), git_blob(BASE, path)
                if not path.endswith(".png"):
                    data, original = data.replace(b"\r\n", b"\n"), original.replace(b"\r\n", b"\n")
                self.assertEqual(data, original)
        old = git_blob(BASE, "construction/machine_visual.gd").decode().replace("\r\n", "\n")
        for method in ["_draw_smelter", "_draw_fabricator"]:
            self.assertEqual(function(read("construction/machine_visual.gd"), method).strip(), function(old, method).strip())
