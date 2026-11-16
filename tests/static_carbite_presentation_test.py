"""Carbite production presentation and inventory contracts. File inspection only; never invokes Godot."""
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "a8d2cba42c101d703d1e925b216881bac33f641d"
ART = "assets/environment/exterior/carbite/carbite_deposit_candidate_v1.png"
CATALOG = "scenes/world/resource_presentations/v2/carbite.json"
DEFINITION = "scenes/world/resource_definitions/v2/carbite.tres"
HASH = "f2c72ef73cd9dbdb9fc15faf3d3cd4aeeb15d135f9944c39c59970ad93948022"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def original(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)


class CarbitePresentationStaticTests(unittest.TestCase):
    def test_approved_png_and_catalog_registration(self):
        png = (ROOT / ART).read_bytes()
        self.assertEqual(png[:8], b"\x89PNG\r\n\x1a\n")
        self.assertEqual(hashlib.sha256(png).hexdigest(), HASH)
        self.assertEqual(struct.unpack(">II", png[16:24]), (1536, 1024))
        self.assertEqual(tuple(png[24:26]), (8, 6))  # RGBA, original alpha pinned by hash.
        catalog = json.loads(read(CATALOG))
        self.assertEqual(catalog, {
            "version": 1, "resource_id": "carbite", "variants": [{
                "id": "candidate_v1", "artwork": "res://" + ART, "sha256": HASH,
                "size": [1536, 1024], "scale": 0.225, "offset": [0, 16]}]})
        before = original(DEFINITION).decode().replace("\r\n", "\n")
        self.assertEqual(read(DEFINITION), before + f'presentation_catalog = "res://{CATALOG}"\n')

    def test_import_matches_cuprite_without_engine_generation(self):
        metadata = read(ART + ".import")
        cuprite = read("assets/environment/exterior/cuprite/cuprite_prototype_v1.png.import")
        self.assertEqual(metadata.split("[params]", 1)[1], cuprite.split("[params]", 1)[1])
        self.assertIn(f'source_file="res://{ART}"', metadata)
        imported = "res://.godot/imported/" + Path(ART).name + "-" + hashlib.md5(("res://" + ART).encode()).hexdigest() + ".ctex"
        self.assertIn(f'path="{imported}"', metadata)
        self.assertIn(f'dest_files=["{imported}"]', metadata)
        uid = re.search(r'uid="([^"]+)"', metadata)[1]
        encoded = uid.removeprefix("uid://")
        self.assertRegex(encoded, r"^[a-y0-8]{1,13}$")
        value = 0
        for character in encoded:
            value = value * 34 + "abcdefghijklmnopqrstuvwxy012345678".index(character)
        self.assertTrue(0 < value < 2**63)
        self.assertEqual(sum(uid in p.read_text() for p in (ROOT / "assets").rglob("*.import")), 1)

    def test_exterior_adds_only_carbite_to_shared_configuration(self):
        setup = read("scenes/world/planet_exterior.gd")
        for resource in ("ferrite", "cuprite", "carbite"):
            self.assertIn(f'resource_definitions/v2/{resource}.tres', setup)
        presenter = read("scenes/world/resource_presenter_v2.gd")
        self.assertIn("sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR", presenter)
        self.assertIn("sprite.z_index = -5", presenter)

    def test_generation_and_existing_presentation_contracts_preserved(self):
        paths = (
            "scenes/world/ordinary_resource_generator.gd",
            "scenes/world/starting_resource_generator.gd",
            "scenes/world/resource_generation_descriptors.gd",
            "scenes/world/resource_generation_v2_integration.gd",
            "scenes/world/resource_generation_crash_site.gd",
            "scenes/world/resource_definitions/v2/cuprite.tres",
            "scenes/world/resource_presenter_v2.gd",
            "scenes/world/resource_presentation_catalog.gd",
            "scenes/world/ferrite_region_generator.gd",
            "scenes/world/resource_presentations/v2/cuprite.json",
            "assets/environment/exterior/cuprite/cuprite_prototype_v1.png",
        )
        for path in paths:
            with self.subTest(path=path):
                current, before = (ROOT / path).read_bytes(), original(path)
                if not path.endswith(".png"):
                    current, before = current.replace(b"\r\n", b"\n"), before.replace(b"\r\n", b"\n")
                if path == "scenes/world/resource_presenter_v2.gd":
                    current = current.split(b'\n\n# Read-only live presentation availability.', 1)[0]
                self.assertEqual(current, before)

    def test_shared_gameplay_extension_preserves_authority_and_transactions(self):
        from static_live_extractor_v2_test import LiveExtractorStaticTests, body
        world = read("scenes/world/planet_world_state.gd")
        contracts = LiveExtractorStaticTests()
        contracts._assert_output_contract(world)
        contracts._assert_transaction_contract(world)
        before = original("scenes/world/planet_world_state.gd").decode().replace("\r\n", "\n")
        for method in ("collect_output", "stored_output_item", "extractor_anchor_rejection_v2"):
            self.assertEqual(body(world, method), body(before, method), method)
        extractor = read("inventory/extractor.tres")
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite", &"cuprite", &"carbite"])', extractor)
        for fragment in ('path="res://inventory/ferrite_ore.tres"', 'output_item = ExtResource("2_ore")',
                         'footprint_cells = Vector2i(4, 4)', 'extraction_point = Vector2(64, 64)',
                         'output_per_cycle = 1', 'cycle_seconds = 1.0', 'output_capacity = 20'):
            self.assertIn(fragment, extractor)
        icon_pattern = r'&"([^"\n]+)": preload\("([^"\n]+)"\)'
        icons = dict(re.findall(icon_pattern, read("scenes/ui/item_presentation.gd")))
        old_icons = dict(re.findall(icon_pattern, original("scenes/ui/item_presentation.gd").decode()))
        self.assertEqual(icons, dict(old_icons, carbite_ore="res://assets/items/carbite_ore.png"))
        for path in ("construction/extractor_anchor_rules.gd",
                     "construction/construction_controller.gd"):
            self.assertEqual(read(path), original(path).decode().replace("\r\n", "\n"))

    def test_approved_inventory_icon_and_item_conventions(self):
        from extractor_artwork_offline import decode_png
        icon = "assets/items/carbite_ore.png"
        png = (ROOT / icon).read_bytes()
        self.assertEqual(hashlib.sha256(png).hexdigest(),
                         "002eb84e1ccfc9bf63b54ee97e9ec4af6e176c25c430cd65158e58e8266ac17b")
        width, height, rgba = decode_png(png)
        self.assertEqual((width, height), (256, 256))
        self.assertEqual((min(rgba[3::4]), max(rgba[3::4])), (0, 255))
        self.assertEqual(read("inventory/carbite_ore.tres"),
                         read("inventory/cuprite_ore.tres").replace("cuprite", "carbite").replace("Cuprite", "Carbite"))
        metadata = read(icon + ".import")
        self.assertEqual(metadata.split("[params]", 1)[1],
                         read("assets/items/cuprite_ore.png.import").split("[params]", 1)[1])
        imported = "res://.godot/imported/carbite_ore.png-" + hashlib.md5(("res://" + icon).encode()).hexdigest() + ".ctex"
        self.assertIn(f'source_file="res://{icon}"', metadata)
        self.assertIn(f'path="{imported}"', metadata)
        self.assertIn(f'dest_files=["{imported}"]', metadata)
        uid = re.search(r'uid="uid://([a-y0-8]{1,13})"', metadata)[1]
        value = 0
        for character in uid:
            value = value * 34 + "abcdefghijklmnopqrstuvwxy012345678".index(character)
        self.assertTrue(0 < value < 2**63)
        self.assertEqual(sum(("uid://" + uid) in p.read_text() for p in (ROOT / "assets").rglob("*.import")), 1)

    def test_shared_behavioral_coverage_is_authored_only(self):
        fixture = read("tests/cuprite_gameplay_test.gd")
        for fragment in ('for resource_type in ["ferrite", "cuprite", "carbite"]',
                         'ordinary resource resolves through world authority',
                         'foreign context rejected', 'stale context rejected',
                         'forged deposit identity rejected', 'missing descriptor pauses production',
                         'missing anchor pauses production', 'missing claim pauses production',
                         'canonical ore and icon identity', 'inspection populated-buffer identity',
                         'incompatible feedback', 'unsupported resource inactivity'):
            self.assertIn(fragment, fixture)
        for path in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("cuprite_gameplay_test", path.read_text())
