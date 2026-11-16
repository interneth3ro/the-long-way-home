"""Ferrite artwork and isolated preview contracts; file inspection, never Godot."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

from extractor_artwork_offline import decode_png

ROOT = Path(__file__).resolve().parents[1]
BASE = "b21cd0490c1ece3c5905843fd593ad8f8d38b034"
ART = "assets/environment/exterior/ferrite/ferrite_v2_production_candidate_v1.png"
HASH = "bd0f7696d64f8f96dca3cbfa0baecb7bba7da96876242eabc5056916574825a0"
CATALOG = "scenes/world/resource_presentations/v2/ferrite.json"
PREVIEW = "scenes/experiments/resource_generation_v2/"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def original(path):
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).decode().replace("\r\n", "\n")


class FerriteV2PreviewStaticTests(unittest.TestCase):
    def test_approved_rgba_pixels_and_soft_transparency(self):
        png = (ROOT / ART).read_bytes()
        self.assertEqual(hashlib.sha256(png).hexdigest(), HASH)
        width, height, rgba = decode_png(png)  # CRC, RGBA8 and full decoding.
        self.assertEqual((width, height), (1536, 1024))
        alpha = rgba[3::4]
        self.assertEqual((min(alpha), max(alpha), len(set(alpha))), (0, 254, 255))
        self.assertEqual(alpha.count(0), 963188)
        self.assertEqual(sum(0 < a < 255 for a in alpha), 609676)
        self.assertEqual((alpha[0], alpha[width - 1], alpha[-width], alpha[-1]), (0, 0, 1, 0))

    def test_catalog_and_preview_only_definition(self):
        self.assertEqual(json.loads(read(CATALOG)), {
            "version": 1, "resource_id": "ferrite", "variants": [{
                "id": "production_candidate_v1", "artwork": "res://" + ART,
                "sha256": HASH, "size": [1536, 1024], "scale": 0.225, "offset": [0, 16]}]})
        live = "scenes/world/resource_definitions/v2/ferrite.tres"
        self.assertEqual(read(live), original(live) + f'presentation_catalog = "res://{CATALOG}"\n')
        self.assertIn("presentation_catalog", read(live))
        self.assertEqual(read(PREVIEW + "ferrite_preview.tres"),
                         read(live))
        # Existing catalog admission: positive scale, bounded image and overhang.
        self.assertLessEqual(1536, 2048)
        self.assertLessEqual(1024, 2048)
        self.assertLessEqual(max(1536 * 0.225 / 2, 1024 * 0.225 / 2 + 16), 512)

    def test_authored_import_identity_and_unchanged_alpha_settings(self):
        metadata = read(ART + ".import")
        reference = read("assets/environment/exterior/carbite/carbite_deposit_candidate_v1.png.import")
        self.assertEqual(metadata.split("[params]", 1)[1], reference.split("[params]", 1)[1])
        imported = "res://.godot/imported/" + Path(ART).name + "-" + hashlib.md5(("res://" + ART).encode()).hexdigest() + ".ctex"
        for fragment in (f'source_file="res://{ART}"', f'path="{imported}"', f'dest_files=["{imported}"]'):
            self.assertIn(fragment, metadata)
        for uid, pattern in ((re.search(r'uid="([^"]+)"', metadata)[1], "*.import"),
                             (read(PREVIEW + "ferrite_inspection.gd.uid").strip(), "*.uid")):
            encoded = uid.removeprefix("uid://")
            self.assertRegex(encoded, r"^[a-y0-8]{1,13}$")
            value = 0
            for character in encoded:
                value = value * 34 + "abcdefghijklmnopqrstuvwxy012345678".index(character)
            self.assertTrue(0 < value < 2**63)
            self.assertEqual(sum(uid in p.read_text() for folder in ("assets", "scenes", "tests")
                                 for p in (ROOT / folder).rglob(pattern)), 1)

    def test_preview_reuses_shared_rendering_and_is_inaccessible_from_gameplay(self):
        script = read(PREVIEW + "ferrite_inspection.gd")
        scene = read(PREVIEW + "ferrite_inspection.tscn")
        for fragment in ('not OS.has_feature("editor")', 'get_tree().current_scene != self',
                         'not development_inspection_enabled', 'ResourcePresenterV2.new()',
                         '_presenter.configure(_generator, WORLD_SEED, definitions)',
                         '[FERRITE, CARBITE, CUPRITE]', 'Generator.new(WORLD_SEED, definitions, Context.protected_bounds(), Context.SHIP_REFERENCE)',
                         'counts != Generator.REQUIRED', 'Vector2(128, 128)',
                         'ContinuousTerrainPresenter.new()', '_terrain.z_index = -11',
                         'Callable(_ground, "sample_ground_material")', '_camera.set_exterior_zoom(true)',
                         '_presenter.step(_token)', '_terrain.step(', '_presenter.dispose()',
                         'KEY_TAB', 'KEY_A'):
            self.assertIn(fragment, script)
        self.assertIn('development_inspection_enabled = true', scene)
        self.assertIn('res://scenes/player/follow_camera.gd', scene)
        for forbidden in ('Sprite2D.new()', 'configure_world(', 'PlanetWorldState.new(',
                          'PlaythroughState', 'ResourceDeposit', 'FileAccess', 'while '):
            self.assertNotIn(forbidden, script)
        # Every explicit resource reference resolves without importing or loading.
        for path in (PREVIEW + "ferrite_inspection.gd", PREVIEW + "ferrite_inspection.tscn", PREVIEW + "ferrite_preview.tres"):
            for reference in re.findall(r'"res://([^"\n]+)"', read(path)):
                self.assertTrue((ROOT / reference).is_file(), reference)
        for folder in ("scenes", "construction", "inventory", "objectives", "dialogue", "tools"):
            for path in (ROOT / folder).rglob("*"):
                if path.suffix not in (".gd", ".tscn", ".tres", ".ps1") or path.parent == ROOT / PREVIEW:
                    continue
                self.assertNotIn(PREVIEW + "ferrite_inspection", path.read_text(), str(path))
                self.assertNotIn("ferrite_preview.tres", path.read_text(), str(path))

    def test_live_authority_generation_and_presenter_limits_preserved(self):
        paths = [
            "project.godot", "inventory/extractor.tres",
            "scenes/world/introductory_ferrite.tres", "scenes/world/ferrite_region_generator.gd",
            "scenes/world/resource_presenter_v2.gd", "scenes/world/resource_presentation_catalog.gd",
            "scenes/world/world_resource_definition.gd", "scenes/world/ordinary_resource_generator.gd",
            "scenes/world/starting_resource_generator.gd", "scenes/world/resource_generation_descriptors.gd",
            "scenes/world/resource_generation_crash_site.gd", "scenes/world/resource_generation_v2_integration.gd",
            "construction/extractor_anchor_rules.gd",
            "construction/construction_controller.gd", "scenes/world/continuous_terrain_presenter.gd",
            "scenes/world/continuous_terrain.gdshader", "scenes/world/planet_generator.gd",
            "tools/run-local-tests.ps1", "tools/run-behavioral-tests.ps1",
            "tests/behavioral/test_runner.gd",
        ]
        paths += [f"scenes/world/resource_definitions/v2/{name}.tres" for name in ("cuprite", "carbite")]
        paths += [f"scenes/world/resource_presentations/v2/{name}.json" for name in ("cuprite", "carbite")]
        for path in paths:
            with self.subTest(path=path):
                current = read(path)
                if path == "scenes/world/resource_presenter_v2.gd":
                    current = current.split('\n\n# Read-only live presentation availability.', 1)[0]
                    current = current.replace('\tif is_complete(token):\n\t\treturn {"ok": true, "done": true}\n', '', 1)
                self.assertEqual(current, original(path))
        presenter = read("scenes/world/resource_presenter_v2.gd")
        self.assertIn("sprite.texture_filter = CanvasItem.TEXTURE_FILTER_LINEAR", presenter)
        self.assertIn("sprite.z_index = -5", presenter)
