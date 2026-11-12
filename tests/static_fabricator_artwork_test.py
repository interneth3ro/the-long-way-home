from east_idle_preservation import verified_east_idle_paths
from south_idle_preservation import verified_south_idle_paths
from north_idle_preservation import verified_north_idle_paths
from initial_exterior_preservation import verified_initial_paths
from static_save_codec_runner_test import verified_codec_runner_paths
"""Frozen PNGs, scene/source contracts and offline geometry; never runs Godot.

Set TLWH_FABRICATOR_FROZEN_ROOTS to a JSON array of the four external package
directories (0/90/180/270) to also recheck their complete frozen inventories.
No external package code is executed, and no files are written.
"""
from application_shell_preservation import verified_application_paths
from fractions import Fraction
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import unittest

from current_preservation import ROOT, git_blob
from extractor_artwork_offline import BODY_PATHS, decode_png, verify_active_artifacts
from smelter_artwork_offline import (BODY_PATHS as SMELTER_BODIES,
                                     verify_active_artifacts as verify_smelter_artifacts)
from static_automatic_transitions_test import function, nodes, vectors
from static_fabricator_animation_test import LAYER_PATHS, without_presentation_identity

BASE = "4b37fc97ff2bbdb24e1fee600245c2329055982d"
MANIFESTS = [
    "c2f8441a7706169d62b96d9c4d3b6b0821765b65939f6fb9f0ef42cbf3d2d0df",
    "32266dfdba5687571ab31b28aa305d6e24c7886ca1b6f79330df656df92db433",
    "6a68b6ea0a2dad155259eb0f019c726b3403b3e238c1599af325b77ba62e6280",
    "a4c405caaeca6331d2cacceb345b775fc29ccc64437af767d1cc9fe1c30f553d",
]
PNG_HASHES = [
    "8230ff568218379c754d409fdf1bf568d90d00c71ccc677feee435e11999dd7e",
    "789a5600cc396b11b18579aa7ac7dd50d3abfe458733c8c980f4a91a74c30c0d",
    "cb17fff5627c03ee5034a37ecac420d1ae4f8192ce5d8759feb4069f0256eca3",
    "1344c9c217e197da11c7e74b4a626714f2424f5b6ea95b9b82a10860d33f64f0",
]
NAMES = ["fabricator_0_resting.png", "fabricator_90_body.png",
         "fabricator_180_body.png", "fabricator_270_body.png"]
PATHS = ["assets/machines/fabricator/" + name for name in NAMES]
SIZES = [(1254, 1254), (1316, 1075), (1171, 1022), (1339, 993)]
CANVASES = [(1254, 1254), (1536, 1536), (1280, 1280), (1536, 1536)]
ANCHORS = [(627, 1080), (768, 1370), (640, 1123), (768, 1255)]
CROPS = [(0, 0, 1254, 1254), (109, 326, 1316, 1075),
         (54, 122, 1171, 1022), (96, 284, 1339, 993)]
RATIOS = [(8, 65), (32, 305), (32, 265), (16, 155)]
OFFSETS = [(-627, -1080), (-659, -1044), (-586, -1001), (-672, -971)]
ARTWORK_PATHS = PATHS + [p + ".import" for p in PATHS] + [
    "construction/fabricator_visual.gd", "construction/fabricator_visual.gd.uid",
    "construction/fabricator_visual.tscn", "construction/machine_visual.gd"]
ANIMATION_PATHS = LAYER_PATHS + [p + ".import" for p in LAYER_PATHS] + ["construction/deployed_machine.gd"]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def inventory():
    return json.loads(read("docs/experiments/fabricator_static_artwork.json"))


def configured():
    script = read("construction/fabricator_visual.gd")
    textures = re.findall(r'preload\("res://([^"\n]+\.png)"\)', script)
    offsets = [tuple(map(int, p)) for p in re.findall(
        r'Vector2\((-?\d+), (-?\d+)\)', script.split("const OFFSETS := [", 1)[1].split("]", 1)[0])]
    ratios = [Fraction(a) / Fraction(b) for a, b in re.findall(
        r'([\d.]+) / ([\d.]+)', script.split("const SCALES := [", 1)[1].split("]", 1)[0])]
    return textures, offsets, ratios


class FabricatorArtworkStaticTest(unittest.TestCase):
    def test_four_accepted_pngs_dimensions_rgba_and_exact_inventory(self):
        data = inventory()
        self.assertEqual(data["baseline"], BASE)
        self.assertEqual([r["direction"] for r in data["directions"]], [0, 90, 180, 270])
        self.assertEqual([r["manifest_sha256"] for r in data["directions"]], MANIFESTS)
        self.assertEqual([r["sha256"] for r in data["directions"]], PNG_HASHES)
        for i, record in enumerate(data["directions"]):
            with self.subTest(direction=i * 90):
                self.assertEqual(record["path"], PATHS[i])
                self.assertEqual(record["package_path"], ("payload/previews/" if i == 0
                                 else "accepted_prototype/runtime/") + NAMES[i])
                raw = (ROOT / PATHS[i]).read_bytes()
                self.assertEqual(sha(raw), PNG_HASHES[i])
                self.assertEqual(len(raw), record["bytes"])
                w, h, rgba = decode_png(raw)  # CRC, RGBA8, zlib and scanline validation.
                self.assertEqual((w, h), SIZES[i])
                self.assertEqual([w, h], record["size_px"])
                self.assertEqual(sha(rgba), record["rgba_sha256"])
                self.assertIn(0, rgba[3::4])
                self.assertIn(255, rgba[3::4])
        self.assertEqual({p.name for p in (ROOT / "assets/machines/fabricator").iterdir()},
                         set(NAMES + [name + ".import" for name in NAMES] +
                             [Path(p).name for p in LAYER_PATHS] + [Path(p).name + ".import" for p in LAYER_PATHS]))

    def test_import_paths_settings_and_unique_canonical_uids(self):
        new_uids = []
        for path in PATHS:
            metadata = read(path + ".import")
            settings = dict(re.findall(r'^([^\n=]+)=(.*)$', metadata, re.M))
            for key, expected in {
                "importer": '"texture"', "type": '"CompressedTexture2D"',
                "compress/mode": "0", "compress/channel_pack": "0",
                "mipmaps/generate": "true", "process/size_limit": "0",
                "process/premult_alpha": "false", "process/fix_alpha_border": "true",
                "process/channel_remap/red": "0", "process/channel_remap/green": "1",
                "process/channel_remap/blue": "2", "process/channel_remap/alpha": "3",
                "source_file": f'"res://{path}"',
            }.items():
                self.assertEqual(settings[key], expected, (path, key))
            cache = "res://.godot/imported/" + Path(path).name + "-" + hashlib.md5(
                ("res://" + path).encode()).hexdigest() + ".ctex"
            self.assertEqual(settings["path"], f'"{cache}"')
            self.assertEqual(settings["dest_files"], f'["{cache}"]')
            new_uids.append(settings["uid"].strip('"'))
        new_uids.append(read("construction/fabricator_visual.gd.uid").strip())
        self.assertEqual(len(set(new_uids)), 5)
        alphabet = "abcdefghijklmnopqrstuvwxy012345678"
        for uid in new_uids:
            self.assertRegex(uid, r'^uid://[b-y0-8][a-y0-8]*$')
            value = 0
            for char in uid[6:]:
                value = value * 34 + alphabet.index(char)
            self.assertTrue(0 < value < 2**63)
        # Compare with tracked resource identities; engine caches are not inputs.
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for path in paths:
            if path.endswith((".uid", ".import")) and path not in ARTWORK_PATHS:
                self.assertFalse(set(new_uids) & set(re.findall(r'uid://[a-y0-8]+', read(path))), path)

    def test_exact_directional_registration_and_independent_world_mapping(self):
        textures, offsets, ratios = configured()
        self.assertEqual(textures, PATHS)
        self.assertEqual(offsets, OFFSETS)
        self.assertEqual(ratios, [Fraction(*ratio) for ratio in RATIOS])
        data = inventory()
        self.assertEqual(data["footprint_cells"], [4, 4])
        self.assertEqual(data["footprint_world"], [128, 128])
        self.assertEqual(data["art_root_position"], [64, 128])
        for i, record in enumerate(data["directions"]):
            for key, expected in [("canvas", CANVASES[i]), ("ground_anchor", ANCHORS[i]),
                                  ("crop", CROPS[i]), ("offset", OFFSETS[i]), ("scale_ratio", RATIOS[i])]:
                self.assertEqual(record[key], list(expected))
            ax, ay = ANCHORS[i]
            cx, cy, w, h = CROPS[i]
            self.assertEqual((cx - ax, cy - ay), offsets[i])
            self.assertTrue(0 <= cx < cx + w <= CANVASES[i][0])
            self.assertTrue(0 <= cy < cy + h <= CANVASES[i][1])
            scale = ratios[i]
            # Use source/crop coordinates independently: anchor and base-span endpoints.
            for px, py, expected in [(ax, ay, (64, 128)),
                                     (ax - 64 / scale, ay, (0, 128)),
                                     (ax + 64 / scale, ay, (128, 128))]:
                world = (64 + scale * (px - cx + offsets[i][0]),
                         128 + scale * (py - cy + offsets[i][1]))
                self.assertEqual(world, expected)

    def test_normalization_idempotence_and_configuration_before_ready(self):
        script = read("construction/fabricator_visual.gd")
        configure = function(script, "configure")
        self.assertIn("_turns = posmod(quarter_turns, 4)", configure)
        guard = "if not is_node_ready() or _applied_turns == _turns:\n\t\treturn"
        self.assertIn(guard, configure)
        self.assertLess(configure.index("_turns = posmod"), configure.index(guard))
        self.assertLess(configure.index(guard), configure.index("_body.texture ="))
        self.assertIn("configure(_turns)", function(script, "_ready"))
        self.assertIn("var _turns: int = 0", script)
        self.assertIn("var _applied_turns: int = -1", script)
        for assignment in ("_body.texture = TEXTURES[_turns]", "_body.position = OFFSETS[_turns]",
                           "scale = Vector2.ONE * SCALES[_turns]", "_applied_turns = _turns"):
            self.assertIn(assignment, configure)
        self.assertLess(configure.index("_applied_turns = _turns"), configure.index("_refresh_view()"))
        textures, _, _ = configured()
        for supplied, direction in [(-9, 3), (-4, 0), (-1, 3), (0, 0), (1, 1),
                                    (2, 2), (3, 3), (4, 0), (9, 1), (1002, 2)]:
            self.assertEqual(textures[supplied % 4], PATHS[direction])

    def test_static_body_registration_preserved_alongside_front_assembly(self):
        scene = read("construction/fabricator_visual.tscn")
        entries = nodes(scene)
        self.assertEqual(list(entries)[:3], ["FabricatorVisual", "Body", "FrontAssembly"])
        self.assertIn('type="Node2D"', entries["FabricatorVisual"][0])
        self.assertIn('type="Sprite2D" parent="."', entries["Body"][0])
        self.assertEqual(vectors(entries["FabricatorVisual"][1]), [(64, 128)])
        self.assertIn("texture_filter = 4", entries["FabricatorVisual"][1])
        self.assertEqual(entries["Body"][1].strip(), "centered = false")
        script = read("construction/fabricator_visual.gd")
        self.assertEqual(script.count("scale ="), 1)
        self.assertEqual(script.count("_body.position ="), 1)
        self.assertNotRegex(script + scene,
                            r"rotation|flip_[hv]|translate\(|AnimationPlayer|Timer|Light2D|material|shader|"
                            r"z_index|y_sort_enabled|clip_children|func _(?:physics_)?process|"
                            r"FileAccess|JSON|ImageTexture|recipe|inventory|set_producing")
        # Decision 62's separate animation suite pins every added node/transform.
        self.assertIn("var layered := _enabled and _turns == 0", function(script, "_refresh_view"))

    def test_shared_adapter_ghost_and_deployed_selection(self):
        visual = read("construction/machine_visual.gd")
        refresh = function(visual, "_refresh_presentation")
        self.assertIn('preload("res://construction/fabricator_visual.tscn")', visual)
        self.assertIn('definition.item_id in [&"extractor", &"smelter", &"fabricator"]', refresh)
        self.assertIn("modulate = Color.WHITE if illustrated or not is_ghost else Color(1, 1, 1, 0.5)", refresh)
        branch = refresh.split('if definition != null and definition.item_id == &"fabricator":', 1)[1]
        for contract in ("if _fabricator == null:", "if is_ghost:", "CanvasGroup.new()",
                         "group.self_modulate = Color(1, 1, 1, 0.5)", "_fabricator_art_container = group",
                         "else:\n\t\t\t\t_fabricator_art_container = Node2D.new()",
                         "add_child(_fabricator_art_container)",
                         "_fabricator = FABRICATOR_SCENE.instantiate() as FabricatorVisual",
                         "_fabricator_art_container.add_child(_fabricator)",
                         "_fabricator_art_container.show()", "_fabricator.configure(turns)",
                         "elif _fabricator_art_container != null:\n\t\t_fabricator.set_operating_status(status, false)\n\t\t_fabricator_art_container.hide()"):
            self.assertIn(contract, branch)
        self.assertEqual(branch.count("instantiate()"), 1)
        self.assertLess(branch.index("_fabricator.configure(turns)"), branch.index("_refresh_fabricator_status()"))
        self.assertNotIn("func _draw_fabricator(", visual)
        self.assertIn('&"fabricator"', function(visual, "_draw").split("return", 1)[0])

    def test_status_overlay_is_unscaled_last_sibling_with_existing_semantics(self):
        visual = read("construction/machine_visual.gd")
        refresh = function(visual, "_refresh_fabricator_status")
        for contract in ('definition.item_id == &"fabricator" and show_status and not is_ghost',
                         "if _fabricator_status == null:", "_fabricator_status = Node2D.new()",
                         "_fabricator_status.draw.connect(_draw_fabricator_status)",
                         "add_child(_fabricator_status)",
                         "Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE",
                         "_fabricator_status.position = definition.rotated_point(size - Vector2(13, 13), turns)",
                         "_fabricator_status.show()", "_fabricator_status.queue_redraw()",
                         "_fabricator_status.hide()"):
            self.assertIn(contract, refresh)
        self.assertNotRegex(refresh, r"\.scale|z_index|CanvasGroup|art_container\.add_child")
        self.assertIn("_fabricator_status.draw_circle(Vector2.ZERO, 3.5, _status_color())",
                      function(visual, "_draw_fabricator_status"))
        old = git_blob(BASE, "construction/machine_visual.gd").decode().replace("\r\n", "\n")
        self.assertEqual(function(visual, "_status_color"), function(old, "_status_color"))
        self.assertEqual([(115, 115), (128 - 115, 115), (128 - 115, 128 - 115), (115, 128 - 115)],
                         [(115, 115), (13, 115), (13, 13), (115, 13)])

    def test_existing_adapter_branches_contract_and_sorting_preserved(self):
        visual = read("construction/machine_visual.gd")
        old = git_blob(BASE, "construction/machine_visual.gd").decode().replace("\r\n", "\n")
        declarations = visual.split("func _ready()", 1)[0]
        for addition in ['const FABRICATOR_SCENE := preload("res://construction/fabricator_visual.tscn")\n',
                         'var _fabricator: FabricatorVisual\n', 'var _fabricator_art_container: Node2D\n',
                         'var _fabricator_status: Node2D\n', 'var presentation_machine_id: int = 0\n']:
            self.assertEqual(declarations.count(addition), 1)
            declarations = declarations.replace(addition, "")
        self.assertEqual(declarations, old.split("func _ready()", 1)[0])
        for method in ("_ready", "_exit_tree", "_refresh_smelter_status", "_draw_smelter_status", "_status_color"):
            self.assertEqual(function(visual, method).strip(), function(old, method).strip())
        start = 'if definition != null and definition.item_id == &"extractor":'
        current_branch = function(visual, "_refresh_presentation").split(start, 1)[1].split(
            '\tif definition != null and definition.item_id == &"fabricator":', 1)[0]
        old_branch = function(old, "_refresh_presentation").split(start, 1)[1].split('\t_refresh_smelter_status()', 1)[0]
        self.assertEqual(current_branch, old_branch)
        self.assertIn("position = Vector2(footprint.get_center().x, footprint.end.y)", read("construction/deployed_machine.gd"))
        self.assertIn("visual.position = Vector2(-footprint.size.x / 2.0, -footprint.size.y)", read("construction/deployed_machine.gd"))
        self.assertIn("y_sort_enabled = true", nodes(read("scenes/world/planet_exterior.tscn"))["GroundObjects"][1])

    def test_gameplay_existing_artwork_and_execution_controls_preserved(self):
        # An exact path boundary covers all production, inventory/recipes, recovery,
        # objectives, old presenters/assets and engine safety controls, not a glob exemption.
        changed = subprocess.check_output([
            "git", "diff", "--name-only", BASE, "--", "inventory", "construction", "scenes", "assets",
            "objectives", "dialogue", "project.godot", "tools", "AGENTS.md", "docs/LOCAL_TESTING.md",
        ], cwd=ROOT, text=True).splitlines()
        # Decision 2A leaves every other machine asset and import protected.
        verify_active_artifacts()
        verify_smelter_artifacts()
        self.assertFalse(set(changed) - set(ARTWORK_PATHS + ANIMATION_PATHS)
                     - set(BODY_PATHS) - set(SMELTER_BODIES) - verified_application_paths() - verified_initial_paths()
                     - verified_codec_runner_paths() - verified_north_idle_paths() - verified_south_idle_paths() - verified_east_idle_paths(), changed)
        path = "construction/deployed_machine.gd"
        self.assertEqual(without_presentation_identity(read(path)),
                         git_blob(BASE, path).decode().replace("\r\n", "\n"))
        self.assertIn("footprint_cells = Vector2i(4, 4)", read("inventory/fabricator.tres"))

    @unittest.skipUnless(os.environ.get("TLWH_FABRICATOR_FROZEN_ROOTS"),
                         "External package roots not supplied; repository PNG checks still run")
    def test_external_frozen_packages_and_direct_png_byte_equality(self):
        roots = json.loads(os.environ["TLWH_FABRICATOR_FROZEN_ROOTS"])
        self.assertEqual(len(roots), 4)
        for root_text, record in zip(roots, inventory()["directions"]):
            root = Path(root_text).resolve(strict=True)
            self.assertEqual(root.name, record["package"])
            self.assertEqual(sha((root / record["manifest"]).read_bytes()), record["manifest_sha256"])
            self.assertEqual(sha((root / record["receipt"]).read_bytes()), record["receipt_sha256"])
            self.assertEqual((root / record["package_path"]).read_bytes(), (ROOT / record["path"]).read_bytes())
            snapshot = {}
            for path in sorted(root.rglob("*")):
                self.assertFalse(path.is_symlink() or path.is_junction(), str(path))
                if path.is_file():
                    raw = path.read_bytes()
                    snapshot[path.relative_to(root).as_posix()] = [len(raw), sha(raw)]
            self.assertEqual(len(snapshot), record["frozen_file_count"])
            self.assertEqual(sha(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()),
                             record["frozen_inventory_sha256"])
            checksum_base = root / "freeze" if record["direction"] == 0 else root
            for line in (root / "freeze/SHA256SUMS.txt").read_text().splitlines():
                digest, relative = line.split("  ", 1)
                path = (checksum_base / relative).resolve(strict=True)
                self.assertTrue(path.is_relative_to(root))
                self.assertEqual(sha(path.read_bytes()), digest, relative)


if __name__ == "__main__":
    unittest.main()
