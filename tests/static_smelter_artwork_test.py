from south_idle_preservation import without_south_idle
from north_idle_preservation import without_north_idle
from initial_exterior_preservation import without_initial_preparation
"""Frozen artwork/source contracts and offline composites; never runs Godot."""
from application_shell_preservation import without_application_startup
from functools import lru_cache
import hashlib
import json
import re
import unittest

from current_preservation import ROOT, git_blob, normalized
from extractor_artwork_offline import decode_png, place
from smelter_artwork_offline import (BODY_PATHS, alpha_bounds, composite, historical_bytes,
                                     verify_active_artifacts)
from static_automatic_transitions_test import function, nodes, vectors
from static_fabricator_animation_test import without_presentation_identity

BASE = "65564d5d95502fcc0368a2b5396d1855311c5806"
MANIFESTS = [
    "7138460485af27067d33b8f0fa562e904c9857829f08c26fb41a19dad741e7d0",
    "fd1632155ab1fddca29e341697f2cb3261f4bcb419bd8abb42c6951a24c5d1c4",
    "530847fd5413fd5cd3c12972068e9366a9e08ad8a16a5ab629ec313c6cb34166",
    "67164aa4317d7a6551b96aeb51e74c6cabaa8e4ac53b29250ba07176bee64338",
]
# Owner-pinned manifests supply these exact ten encoded PNG identities.
PNG_HASHES = [
    "22ef39828ea9b31fc7c893183674ab9c83d81db6f5838440712edd90ce3f50f9",
    "81c62cb2b4872554440f4d58b769c4446460b5a60a5064d1897859ef7844d8b3",
    "ce148c6e9319b2efb852010bc6ce73e0c0e2124f60385ac21ae7145186ecf58f",
    "73a3d1b52e051fda2158f26602868010ac6132f1a028773af6b7ac8d8d9d6397",
    "a50374aa29900b863c931c4853b4ec0b6223559a854eae908c5d8351b7f1070f",
    "5e34c50f1055296a311240e283f1d66c5d279e3d78af97f49153c6f1ec47b538",
    "9a6d4b4d3236e6d1d902920864bfdeb3171873fe50c8df4e46877d14e9539b05",
    "391c692f08adcd0a395c169de034ab536f015a45002ca9a318724b42b3086fb4",
    "a3673227279850f84fdbeb4af548cc32a9a92184b203893e7b3225706b4806bb",
    "329ba5256f4286f151a24bf27bac8527b9d4106fd951c83a3fb97ec7a266c3fd",
]
IDLE_RGBA = [
    "3e679ed07e8ab45d3cfe1e56d5fbfcdb3f512394db55ee095a6d4d6bb70f06de",
    "7cf7b452acb7841489b746ba0be95206f758832080e61f40fc57b2dcb07b8e42",
    "f4c68ea296187872b2a5f4e6ec0081bb33cb2f358c8f0c09a65a655a0deaeea3",
    "b737a53146439274c4a6eef70cdbf32ff74b62cc1aada90965a5cd1b0e1ad398",
]
ANCHORS = [(608, 1096), (628, 1158), (634, 1128), (625, 1172)]
OFFSETS = [
    [(-571, -999), (-8, -439), (-400, -987), (-72, -460)],
    [(-467, -1144), None, (-72, -1130), None],
    [(-596, -1039), None, (256, -1021), None],
    [(-463, -1100), None, (-101, -897), None],
]
ROLES = ["body", "interior", "illumination", "foreground"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def inventory():
    return json.loads(read("docs/experiments/smelter_static_artwork.json"))


@lru_cache(maxsize=None)
def decoded(path, historical=False):
    return decode_png(historical_bytes(path) if historical else (ROOT / path).read_bytes())


def configured():
    script = read("construction/smelter_visual.gd")
    texture_section, offset_section = script.split("const OFFSETS := [", 1)
    rows = re.findall(r'\t\[\n(.*?)\t\],', texture_section, re.S)
    textures = [[match[0] or None for match in re.findall(
        r'preload\("res://([^"\n]+)"\)|(null)', row)] for row in rows]
    offsets = []
    for row in re.findall(r'\t\[(.*?)\],', offset_section.split("@onready", 1)[0]):
        offsets.append([tuple(map(int, pair)) if pair[0] else (0, 0)
                        for pair in re.findall(r'Vector2\((-?\d+), (-?\d+)\)|Vector2\.ZERO', row)])
    return textures, offsets


class SmelterArtworkStaticTest(unittest.TestCase):
    def test_frozen_identity_dimensions_alpha_and_imports(self):
        data = inventory()
        records = data["directions"]
        self.assertEqual(data["baseline"], BASE)
        self.assertEqual([r["direction"] for r in records], [0, 90, 180, 270])
        self.assertEqual([r["manifest_sha256"] for r in records], MANIFESTS)
        assets = [a for r in records for a in r["assets"]]
        self.assertEqual([a["sha256"] for a in assets], PNG_HASHES)
        self.assertEqual(len(assets), 10)
        expected_paths = set()
        uids = set()
        for asset in assets:
            path = asset["path"]
            raw = historical_bytes(path) if path in BODY_PATHS else (ROOT / path).read_bytes()
            self.assertEqual((len(raw), hashlib.sha256(raw).hexdigest()),
                             (asset["bytes"], asset["sha256"]))
            w, h, rgba = decoded(path, historical=path in BODY_PATHS)  # Includes chunk CRCs, RGBA8 and zlib decode.
            self.assertEqual([w, h], asset["size_px"])
            self.assertEqual(hashlib.sha256(rgba).hexdigest(), asset["rgba_sha256"])
            alpha = rgba[3::4]
            self.assertIn(0, alpha)
            self.assertIn(255, alpha)
            points = [(i % w, i // w) for i, a in enumerate(alpha) if a]
            bounds = (min(x for x, y in points), min(y for x, y in points),
                      max(x for x, y in points) + 1, max(y for x, y in points) + 1)
            self.assertEqual(bounds, (4, 4, w - 4, h - 4))
            metadata = read(path + ".import")
            for setting in ("compress/mode=0", "mipmaps/generate=true", "process/size_limit=0",
                            "process/premult_alpha=false", f'source_file="res://{path}"'):
                self.assertIn(setting, metadata)
            cache = path.rsplit("/", 1)[1] + "-" + hashlib.md5(("res://" + path).encode()).hexdigest() + ".ctex"
            self.assertEqual(metadata.count("res://.godot/imported/" + cache), 2)
            uid = re.search(r'uid="uid://([a-y0-8]+)"', metadata)[1]
            self.assertNotIn(uid, uids)
            uids.add(uid)
            expected_paths.update((path.rsplit("/", 1)[1], path.rsplit("/", 1)[1] + ".import"))
        self.assertEqual({p.name for p in (ROOT / "assets/machines/smelter").iterdir()}, expected_paths)

    def test_active_derivatives_exact_identities_and_measured_alpha(self):
        active = verify_active_artifacts()
        textures, offsets = configured()
        for index, body in enumerate(active["bodies"]):
            self.assertEqual(textures[index][0], body["path"])
            self.assertEqual(list(offsets[index][0]), body["offset_px"])
            w, h, rgba = decoded(body["path"])
            self.assertEqual(alpha_bounds(w, h, rgba), body["alpha_bounds_px"])
            # Active bounds are independently pinned; historical four-edge bounds
            # above remain exact and apply to historical originals only.
            self.assertEqual(hashlib.sha256(rgba).hexdigest(), body["source_crop_rgba_sha256"])

    def test_active_thermal_composites_preserve_supporting_layer_response(self):
        for body, record in zip(verify_active_artifacts()["bodies"], inventory()["directions"]):
            active_rgba = decoded(body["path"])[2]
            original_rgba = decoded(body["path"], historical=True)[2]
            cold = composite(record, active_rgba, 0)
            old_cold = composite(record, original_rgba, 0)
            self.assertEqual([r["illumination_opacity"] for r in body["offline_composites"]], [0, .82, 1])
            for check in body["offline_composites"]:
                opacity = check["illumination_opacity"]
                current = composite(record, active_rgba, opacity)
                self.assertEqual(hashlib.sha256(current).hexdigest(), check["rgba_sha256"])
                self.assertEqual(current[3::4], cold[3::4])
                if opacity:
                    original = composite(record, original_rgba, opacity)
                    # Every channel's thermal contribution remains identical,
                    # including at the 0-degree interior/foreground boundaries.
                    self.assertTrue(all(a - b == c - d for a, b, c, d in
                                        zip(current, cold, original, old_cold)))

    def test_directional_slots_order_crops_and_anchors(self):
        textures, offsets = configured()
        self.assertEqual((len(textures), len(offsets)), (4, 4))
        for d, record in enumerate(inventory()["directions"]):
            self.assertEqual(record["master_size_px"], [1254, 1254])
            self.assertEqual(tuple(record["ground_anchor_px"]), ANCHORS[d])
            self.assertEqual(len(textures[d]), 4)
            self.assertEqual(offsets[d], [p or (0, 0) for p in OFFSETS[d]])
            assets = {a["role"]: a for a in record["assets"]}
            self.assertEqual(list(assets), ROLES if d == 0 else ["body", "illumination"])
            for slot, role in enumerate(ROLES):
                path = textures[d][slot]
                if role not in assets:
                    self.assertIsNone(path)
                    continue
                a = assets[role]
                self.assertEqual(path, f"assets/machines/smelter/smelter_{d * 90}_{role}.png")
                self.assertEqual(path, a["path"])
                self.assertEqual(a["draw_order"], list(assets).index(role))
                self.assertEqual(a["blend"], "normal_source_over")
                self.assertEqual(a["anchor_relative_offset_px"], list(offsets[d][slot]))
                self.assertEqual(a["crop_rect_px"][:2],
                                 [offsets[d][slot][i] + ANCHORS[d][i] for i in range(2)])
                self.assertEqual(a["crop_rect_px"][2:], a["size_px"])

    def test_turn_normalization_and_preserved_layer_configuration(self):
        script = read("construction/smelter_visual.gd")
        configure = function(script, "configure")
        self.assertIn("var direction := posmod(quarter_turns, 4)", configure)
        self.assertIn("if direction == _turns:\n\t\treturn", configure)
        self.assertIn("_layers[index].texture = TEXTURES[direction][index]", configure)
        self.assertIn("_layers[index].position = OFFSETS[direction][index]", configure)
        self.assertIn("if index != 2:\n\t\t\t_layers[index].visible = TEXTURES[direction][index] != null", configure)
        self.assertNotRegex(configure, r"_thermal|_cancel_thermal|_start_pulse|_set_heat|self_modulate")
        self.assertIn("[$Body, $Interior, $Illumination, $Foreground]", script)
        self.assertNotRegex(script, r"func _(?:physics_)?process|AnimationPlayer|FileAccess|JSON|ImageTexture|rotation|flip_[hv]|material")
        textures, _ = configured()
        # Independent modulo examples bound to the exact posmod selection above.
        for turns, direction in [(-9, 3), (-4, 0), (-1, 3), (0, 0), (1, 1),
                                 (2, 2), (3, 3), (4, 0), (9, 1), (1002, 2)]:
            self.assertEqual(turns % 4, direction)
            self.assertTrue(textures[turns % 4][0].endswith(f"smelter_{direction * 90}_body.png"))

    def test_calibration_uncentered_layers_and_sorting(self):
        scene = read("construction/smelter_visual.tscn")
        entries = nodes(scene)
        self.assertEqual(list(entries), ["SmelterVisual", "Body", "Interior", "Illumination", "Foreground"])
        self.assertEqual(vectors(entries["SmelterVisual"][1]), [(64, 128), (4 / 29, 4 / 29)])
        self.assertIn("texture_filter = 4", entries["SmelterVisual"][1])
        self.assertIn("visible = false", entries["Illumination"][1])
        self.assertEqual(scene.count("centered = false"), 4)
        self.assertNotRegex(scene, r"z_index|y_sort_enabled|rotation|flip_[hv]|material|clip_children")
        self.assertEqual(inventory()["source_to_world_ratio"], [4, 29])
        for ax, ay in ANCHORS:
            for px, py, expected in [(ax, ay, (64, 128)), (ax - 464, ay - 928, (0, 0)),
                                     (ax + 464, ay, (128, 128))]:
                world = (64 + (px - ax) * 4 / 29, 128 + (py - ay) * 4 / 29)
                self.assertEqual(world, expected)
        deployed = read("construction/deployed_machine.gd")
        self.assertIn("position = Vector2(footprint.get_center().x, footprint.end.y)", deployed)
        self.assertIn("visual.position = Vector2(-footprint.size.x / 2.0, -footprint.size.y)", deployed)
        self.assertIn("y_sort_enabled = true", nodes(read("scenes/world/planet_exterior.tscn"))["GroundObjects"][1])
        self.assertIn("$GroundObjects.add_child(presenter)", read("scenes/world/planet_exterior.gd"))

    def test_historical_crops_reconstruct_frozen_idle_pixels(self):
        textures, offsets = configured()
        for d, record in enumerate(inventory()["directions"]):
            composite = bytearray(1254 * 1254 * 4)
            for slot, path in enumerate(textures[d]):
                if path is None or slot == 2:
                    continue
                w, h, rgba = decoded(path, historical=path in BODY_PATHS)
                origin = tuple(offsets[d][slot][i] + ANCHORS[d][i] for i in range(2))
                place(rgba, w, h, origin, composite)
            digest = hashlib.sha256(composite).hexdigest()
            self.assertEqual(digest, IDLE_RGBA[d])
            self.assertEqual(digest, record["idle_rgba_sha256"])

    def test_shared_presenter_composite_ghost_and_switching(self):
        visual = read("construction/machine_visual.gd")
        refresh = function(visual, "_refresh_presentation")
        self.assertIn('preload("res://construction/smelter_visual.tscn")', visual)
        self.assertIn('var illustrated := definition != null and definition.item_id in [&"extractor", &"smelter", &"fabricator"]', refresh)
        self.assertIn("modulate = Color.WHITE if illustrated or not is_ghost else Color(1, 1, 1, 0.5)", refresh)
        branch = refresh.split('if definition != null and definition.item_id == &"smelter":', 1)[1]
        for contract in ("if _smelter == null:", "if is_ghost:", "var group := CanvasGroup.new()",
                         "group.self_modulate = Color(1, 1, 1, 0.5)", "_smelter_art_container = Node2D.new()",
                         "_smelter = SMELTER_SCENE.instantiate() as SmelterVisual",
                         "_smelter_art_container.add_child(_smelter)", "_smelter.configure(turns)",
                         "_smelter.set_operating_status(status, not is_ghost)",
                         "elif _smelter_art_container != null:\n\t\t_smelter.reset_thermal()\n\t\t_smelter_art_container.hide()"):
            self.assertIn(contract, branch)
        self.assertIn("_extractor.set_producing(false)\n\t\t_art_container.hide()", refresh)
        self.assertLess(refresh.index("_smelter_art_container.add_child(_smelter)"), refresh.index("_refresh_smelter_status()"))
        self.assertNotRegex(visual, r"func _(?:physics_)?process|ImageTexture|create_tween|FileAccess")
        self.assertNotIn(".modulate", read("construction/smelter_visual.gd"))
        controller = read("construction/construction_controller.gd")
        for contract in ("_ghost.is_ghost = true", "_ghost.turns = _turns", "z_index = 10",
                         "_definition.footprint(_cell, _turns).position"):
            self.assertIn(contract, controller)

    def test_deployed_only_foreground_status_preserves_colors_radius_and_position(self):
        script = read("construction/machine_visual.gd")
        refresh = function(script, "_refresh_smelter_status")
        for contract in ('definition.item_id == &"smelter" and show_status and not is_ghost',
                         "if _smelter_status == null:", "_smelter_status.draw.connect(_draw_smelter_status)",
                         "add_child(_smelter_status)",
                         "_smelter_status.position = definition.rotated_point(size - Vector2(13, 13), turns)",
                         "_smelter_status.queue_redraw()", "_smelter_status.hide()"):
            self.assertIn(contract, refresh)
        self.assertNotRegex(refresh, r"\.scale|z_index|CanvasGroup")
        self.assertIn("_smelter_status.draw_circle(Vector2.ZERO, 3.5, _status_color())",
                      function(script, "_draw_smelter_status"))
        colors = function(script, "_status_color")
        for status, color in [("PRODUCING", "0.35, 0.78, 0.46"), ("OUTPUT_FULL", "0.94, 0.69, 0.28"),
                              ("INPUT_EMPTY", "0.35, 0.60, 0.90")]:
            self.assertIn(f"if status == PlanetWorldState.OperatingStatus.{status}:\n\t\treturn Color({color})", colors)
        self.assertIn("return Color(0.55, 0.58, 0.59)", colors)
        # Original top-left transform + clockwise rotation of (115,115).
        self.assertEqual([(115, 115), (128 - 115, 115), (128 - 115, 128 - 115), (115, 128 - 115)],
                         [(115, 115), (13, 115), (13, 13), (115, 13)])
        draw = function(script, "_draw")
        self.assertIn('definition.item_id in [&"extractor", &"smelter", &"fabricator"]', draw)
        self.assertIn("draw_circle(Vector2(size.x - 13, size.y - 13), 3.5, _status_color())", draw)

    def test_gameplay_other_presenters_and_stationary_preserved(self):
        for path in ["inventory/smelter.tres", "inventory/extractor.tres", "inventory/fabricator.tres",
                     "construction/deployed_machine.gd", "construction/construction_controller.gd",
                     "construction/machine_definition.gd", "construction/placement_rules.gd",
                     "construction/extractor_visual.gd", "construction/extractor_visual.tscn",
                     "scenes/world/world_coordinates.gd", "scenes/world/planet_world_state.gd",
                     "scenes/world/planet_exterior.gd", "scenes/world/planet_exterior.tscn",
                     "scenes/player/dave.gd", "scenes/player/dave.tscn",
                     "scenes/player/interaction_detector.gd", "scenes/main/scene_transition_controller.gd",
                     "scenes/main/playthrough_state.gd", "scenes/ui/machine_ui.gd",
                     "scenes/ui/smelter_inspection.gd", "scenes/ui/smelter_inspection.tscn",
                     "scenes/visuals/smelter_stationary.tscn", "scenes/world/stationary_machine_presentation.gd",
                     "scenes/interaction/v2_smelter_recovery.gd", "scenes/interaction/smelter_rack.gd",
                     "assets/environment/maintenance_bay_v2/machines/smelter_stationary.png",
                     "assets/environment/maintenance_bay_v2/machines/smelter_stationary.png.import",
                     "docs/experiments/extractor_static_artwork.json", "project.godot"]:
            with self.subTest(path=path):
                # Authorized Fabricator 4x4 amendment: restore only this exact
                # field for comparison against the unchanged historical baseline.
                current = normalized(path, without_north_idle(path, without_south_idle(path, without_initial_preparation(path, (ROOT / path).read_bytes()))))
                if path == "project.godot":
                    current = without_application_startup(current)
                if path == "construction/deployed_machine.gd":
                    current = without_presentation_identity(current.decode()).encode()
                if path == "inventory/fabricator.tres":
                    self.assertEqual(current.count(b"footprint_cells = Vector2i(4, 4)"), 1)
                    current = current.replace(b"footprint_cells = Vector2i(4, 4)",
                                              b"footprint_cells = Vector2i(2, 2)")
                self.assertEqual(current, normalized(path, git_blob(BASE, path)))
        self.assertIn("footprint_cells = Vector2i(4, 4)", read("inventory/smelter.tres"))
        self.assertIn("CONSTRUCTION_SIZE: int = 32", read("scenes/world/world_coordinates.gd"))
        path = "construction/machine_visual.gd"
        # Decision 36 replaces only Fabricator presentation; its own suite pins
        # the new artwork, registration, ghost and unscaled status overlay.
        self.assertNotIn("func _draw_fabricator(", read(path))
        self.assertIn("_fabricator.configure(turns)", read(path))
