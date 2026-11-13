"""Static live-window geometry/budget checks; no Godot or project code runs."""
from pathlib import Path
import math
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
PRESENTER = (ROOT / "scenes/world/resource_presenter_v2.gd").read_text()
EXTERIOR = (ROOT / "scenes/world/planet_exterior.gd").read_text()
GENERATOR = (ROOT / "scenes/world/ordinary_resource_generator.gd").read_text()


def number(source, name):
    return float(re.search(r"const " + name + r": \w+ = ([\d.]+)", source)[1])


class LiveResourceWindowTests(unittest.TestCase):
    def test_real_chunk_dimensions_and_supported_windows(self):
        coordinates = (ROOT / "scenes/world/world_coordinates.gd").read_text()
        chunk = number(coordinates, "TERRAIN_SIZE") * number(coordinates, "CHUNK_TILES")
        initial = 2 * number(EXTERIOR, "INITIAL_RADIUS") + 1
        loading = int(re.search(r"@export_range\(1, (\d+), 1\) var loading_radius", EXTERIOR)[1])
        retention = int(re.search(r"@export_range\(1, (\d+), 1\) var retention_margin", EXTERIOR)[1])
        self.assertEqual(chunk, 2048)
        self.assertEqual(initial * chunk, 14336)
        self.assertGreater(initial * chunk, number(PRESENTER, "MAX_AREA_AXIS"))
        self.assertEqual((2 * (loading + retention) + 1) * chunk,
                         number(PRESENTER, "MAX_LIVE_AREA_AXIS"))
        self.assertLessEqual(initial * chunk, number(PRESENTER, "MAX_LIVE_AREA_AXIS"))

    def test_signed_windows_fit_page_and_accumulation_budgets(self):
        page = number(PRESENTER, "LIVE_PAGE_SIZE")
        reach = 512  # catalog's maximum supported artwork reach
        halo = (number(GENERATOR, "MAX_OFFSET") + number(GENERATOR, "ANCHOR_SIZE")
                + number(GENERATOR, "VISUAL_MARGIN"))
        for loading in range(1, 5):
            for retention in range(1, 3):
                radius = max(3, loading + retention)
                for center in range(-12, 13):
                    start, end = (center - radius) * 2048, (center + radius + 1) * 2048
                    first, last = math.floor(start / page), math.floor(end / page)
                    pages = last - first + 1
                    owners = (math.floor(((last + 1) * page + reach + halo) / page)
                              - math.floor((first * page - reach - halo) / page) + 1)
                    self.assertLessEqual(pages ** 2, number(PRESENTER, "MAX_LIVE_PAGES"))
                    self.assertLessEqual(owners ** 2 * 4 * 3 + 7,
                                         number(PRESENTER, "MAX_LIVE_DESCRIPTORS"))

    def test_each_page_keeps_original_query_bounds(self):
        page = number(PRESENTER, "LIVE_PAGE_SIZE")
        halo = (number(GENERATOR, "MAX_OFFSET") + number(GENERATOR, "ANCHOR_SIZE")
                + number(GENERATOR, "VISUAL_MARGIN"))
        owners = math.floor((page + 512 + halo) / page) - math.floor((-512 - halo) / page) + 1
        self.assertLessEqual(owners ** 2, number(GENERATOR, "MAX_QUERY_REGIONS"))
        self.assertLessEqual(owners ** 2 * 4 * 3 + 7, number(PRESENTER, "MAX_DESCRIPTORS"))
        self.assertIn("_world.query_resource_descriptors_v2(page.grow(_reach), _world_token)", PRESENTER)
        self.assertIn("queried.deposits.size() > MAX_DESCRIPTORS", PRESENTER)

    def test_limits_are_selected_by_adapter_and_still_fail_closed(self):
        self.assertIn("MAX_LIVE_AREA_AXIS if _world != null else MAX_AREA_AXIS", PRESENTER)
        self.assertIn("area.size.x > area_limit or area.size.y > area_limit", PRESENTER)
        self.assertIn("area.end.is_finite()", PRESENTER)
        self.assertIn("> MAX_LIVE_PAGES:", PRESENTER)
        self.assertIn("MAX_LIVE_DESCRIPTORS if _world != null else MAX_DESCRIPTORS", PRESENTER)
        self.assertEqual(number(PRESENTER, "MAX_AREA_AXIS"), 6144)
        self.assertEqual(number(PRESENTER, "MAX_OWNERS"), 64)
        self.assertEqual(number(PRESENTER, "MAX_DESCRIPTORS"), 775)
        self.assertEqual(number(PRESENTER, "TEXTURE_LIMIT"), 8)

    def test_generation_and_terrain_inputs_are_unchanged(self):
        for path in ("scenes/world/ordinary_resource_generator.gd",
                     "scenes/world/starting_resource_generator.gd",
                     "scenes/world/planet_exterior.gd", "scenes/world/world_coordinates.gd",
                     "scenes/world/resource_presentation_catalog.gd", "tools/run-local-tests.ps1"):
            with self.subTest(path=path):
                old = subprocess.check_output(["git", "show", "e7aeef97c194fdbdf9ccf8b1c7b3493417ebe39a:" + path],
                                              cwd=ROOT, text=True)
                self.assertEqual((ROOT / path).read_text(), old)


if __name__ == "__main__":
    unittest.main()
