"""Carbite visual preview contracts. File inspection only; never invokes Godot."""
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
        path = "scenes/world/planet_exterior.gd"
        before = original(path).decode().replace("\r\n", "\n")
        old = '[preload("res://scenes/world/resource_definitions/v2/cuprite.tres")])'
        new = '[preload("res://scenes/world/resource_definitions/v2/cuprite.tres"),\n\t\tpreload("res://scenes/world/resource_definitions/v2/carbite.tres")])'
        self.assertEqual(before.count(old), 1)
        self.assertEqual(read(path), before.replace(old, new))
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
            "scenes/world/resource_definitions/v2/ferrite.tres",
            "scenes/world/resource_definitions/v2/cuprite.tres",
            "scenes/world/resource_presenter_v2.gd",
            "scenes/world/resource_presentation_catalog.gd",
            "scenes/world/ferrite_deposit_presenter.gd",
            "scenes/world/ferrite_region_generator.gd",
            "scenes/world/planet_exterior.tscn",
            "scenes/world/resource_presentations/v2/cuprite.json",
            "assets/environment/exterior/cuprite/cuprite_prototype_v1.png",
        )
        for path in paths:
            with self.subTest(path=path):
                current, before = (ROOT / path).read_bytes(), original(path)
                if not path.endswith(".png"):
                    current, before = current.replace(b"\r\n", b"\n"), before.replace(b"\r\n", b"\n")
                self.assertEqual(current, before)

    def test_carbite_stays_incompatible_and_has_no_inventory_output(self):
        extractor = read("inventory/extractor.tres")
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite", &"cuprite"])', extractor)
        world = read("scenes/world/planet_world_state.gd")
        resolver = world.split("func extractor_output_item(", 1)[1].split("\nfunc ", 1)[0]
        self.assertNotIn('"carbite":', resolver)
        self.assertIn('"cuprite": return preload("res://inventory/cuprite_ore.tres")', resolver)
        self.assertIn('"ferrite": return preload("res://inventory/ferrite_ore.tres")', resolver)
        self.assertNotIn("carbite", read("scenes/ui/item_presentation.gd"))
        self.assertFalse((ROOT / "inventory/carbite_ore.tres").exists())
        for path in ("inventory/extractor.tres", "scenes/world/planet_world_state.gd",
                     "construction/extractor_anchor_rules.gd", "construction/placement_rules.gd",
                     "construction/construction_controller.gd", "scenes/ui/item_presentation.gd"):
            with self.subTest(path=path):
                self.assertEqual(read(path), original(path).decode().replace("\r\n", "\n"))
