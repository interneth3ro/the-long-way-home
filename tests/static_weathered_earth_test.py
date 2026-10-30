"""Static texture decoding, sampling models and exact preservation; no Godot."""
import hashlib
import math
from pathlib import Path
import runpy
import struct
import subprocess
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
BASE = "c3b0460a6b52437b1961b5d0936f6ec279371d55"
# Exact candidate allowance; owner review required before any future Native use.
# Restore the unchanged main bytes for older preservation checks, never exempt a file.
TERRAIN_SHA256 = {
    "scenes/world/planet_generator.gd": "c926e53c8ea29274c0a925a3f1f1b3271ff5b54f2e3da1f72115e4913cd34651",
    "scenes/world/terrain_chunk.gd": "617d5b184fc4fcb3cb0c5560b64e5830f489e042b0996fda356c230744d8eac1",
}
INPUT_SHA256 = {
    **TERRAIN_SHA256,
    "tools/generate-weathered-earth.py": "543268b77f3aa57a1b60db1868097c38992aad87aa960288a0f7029fb65cbf2b",
    "assets/environment/exterior/weathered_earth_provisional/a_base_soil.png": "1333e2fe5126193a8f283a2f4517f00dc6480f4ac579e91e4b88fb98c20d5042",
    "assets/environment/exterior/weathered_earth_provisional/b_compacted_soil.png": "49b569da91c1caf3f7f62c7d3e70e206aeaeeaa38b4bb63d428ed66e97a2bf3f",
    "assets/environment/exterior/weathered_earth_provisional/c_dusty_patches.png": "dcb4e176f29f778abe6e1d193a578d3e8f971252da68317c4e5f6b848c1c2b51",
    "assets/environment/exterior/weathered_earth_provisional/d_subtle_gravel.png": "4db46c882bde7ee6377fe0648d9a6ca44c9ab5b163ba0a9c6c5758f9282c08c7",
}


def verify_input(path, actual):
    normalized = actual if path.endswith(".png") else actual.replace(b"\r\n", b"\n")
    assert hashlib.sha256(normalized).hexdigest() == INPUT_SHA256[path], path


def preserved_terrain_bytes(path, actual):
    normalized = actual.replace(b"\r\n", b"\n")
    assert hashlib.sha256(normalized).hexdigest() == TERRAIN_SHA256[path], path
    return subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).replace(b"\r\n", b"\n")


def pixels(raw):
    assert raw[:8] == b"\x89PNG\r\n\x1a\n"
    pos, data, kinds = 8, bytearray(), []
    while pos < len(raw):
        length = struct.unpack_from(">I", raw, pos)[0]
        kind, payload = raw[pos + 4:pos + 8], raw[pos + 8:pos + 8 + length]
        assert zlib.crc32(kind + payload) == struct.unpack_from(">I", raw, pos + 8 + length)[0]
        if kind == b"IHDR":
            assert struct.unpack(">IIBBBBB", payload) == (128, 128, 8, 2, 0, 0, 0)
        if kind == b"IDAT":
            data.extend(payload)
        kinds.append(kind)
        pos += length + 12
    assert pos == len(raw) and kinds == [b"IHDR", b"IDAT", b"IEND"]
    scan = zlib.decompress(data)
    assert len(scan) == 128 * 385
    assert all(scan[y * 385] == 0 for y in range(128))
    return [scan[y * 385 + 1:(y + 1) * 385] for y in range(128)]


def coordinate_random(x, y, seed, channel):
    number = seed % 2147483647
    number = (number * 48271 + (x % 2147483647) * 69621) % 2147483647
    number = (number * 48271 + (y % 2147483647) * 907) % 2147483647
    number = (number * 48271 + channel * 104729) % 2147483647
    return ((number ^ (number >> 13)) * 48271 % 2147483647) / 2147483647.0


def noise(x, y, seed, channel):
    ix, iy = math.floor(x), math.floor(y)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = coordinate_random(ix, iy, seed, channel), coordinate_random(ix + 1, iy, seed, channel)
    c, d = coordinate_random(ix, iy + 1, seed, channel), coordinate_random(ix + 1, iy + 1, seed, channel)
    return (a + (b - a) * fx) * (1 - fy) + (c + (d - c) * fx) * fy


class WeatheredEarthStaticTest(unittest.TestCase):
    def test_uv_array_uses_shared_runtime_initializer(self):
        source = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        self.assertIn("static var _texture_uvs := PackedVector2Array(", source)
        self.assertNotIn("const TEXTURE_UVS", source)
        self.assertEqual(source.count("_texture_uvs :="), 1)
        self.assertEqual(source.count("draw_polygon(vertices, colors, _texture_uvs,"), 2)

    def test_provisional_textures_reproduce_and_decode(self):
        recipe = runpy.run_path(str(ROOT / "tools/generate-weathered-earth.py"))
        family = []
        for treatment, name in enumerate(recipe["NAMES"]):
            raw = (recipe["OUTPUT"] / (name + ".png")).read_bytes()
            self.assertEqual(raw, recipe["png_bytes"](treatment))
            family.append(pixels(raw))
        self.assertEqual(len({tuple(rows) for rows in family}), 4)
        # Verify all 16 ordered adjacencies, not just four isolated repetitions.
        for left in family:
            for right in family:
                for y in range(128):
                    self.assertEqual(left[y][-3:], right[y][:3])
                self.assertEqual(left[-1], right[0])
        # Shared border strips soften treatment changes near mixed-tile edges.
        for other in family[1:]:
            for y in range(128):
                self.assertEqual(family[0][y][:24], other[y][:24])
                self.assertEqual(family[0][y][-24:], other[y][-24:])

    def test_absolute_sampling_and_negative_boundary_model(self):
        source = (ROOT / "scenes/world/planet_generator.gd").read_text()
        self.assertIn("Vector2(vertex) * WorldCoordinates.TERRAIN_SIZE / 1024.0", source)
        self.assertIn("_noise(point, 8)", source)
        self.assertIn("_noise(point, 9)", source)
        self.assertIn("_noise(point, 10)", source)
        chunk = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        self.assertIn("generator.weathered_earth_weights(origin + Vector2i(x, y))", chunk)
        self.assertIn("generator.sample_color(origin + Vector2i(x - 1, y - 1), state)", chunk)
        for seed in (26026, 1, -42):
            for cx, cy in ((0, 0), (-1, -1), (-2, 1), (3, -4)):
                for offset in range(33):
                    # Both chunks compute identical boundary vertices and the
                    # identical four-sample tint halo, even across world zero.
                    left = (cx * 32 + 32, cy * 32 + offset)
                    right = ((cx + 1) * 32, cy * 32 + offset)
                    self.assertEqual(left, right)
                    for channel in (8, 9, 10):
                        a = noise(left[0] / 16, left[1] / 16, seed, channel)
                        b = noise(right[0] / 16, right[1] / 16, seed, channel)
                        self.assertEqual(a, b)
                        self.assertTrue(0 <= a <= 1)
                    halo = lambda p: {(p[0] + x, p[1] + y) for x in (-1, 0) for y in (-1, 0)}
                    self.assertEqual(halo(left), halo(right))
        # Absolute sampling is independent of generation order or chunk residency.
        points = [(x, y) for x in (-65, -33, -32, -1, 0, 31, 32, 64) for y in (-33, 0, 32)]
        sample = lambda p: noise(p[0] / 16, p[1] / 16, 26026, 8)
        self.assertEqual(dict((p, sample(p)) for p in points), dict((p, sample(p)) for p in reversed(points)))
        self.assertTrue(any(sample(p) != noise(p[0] / 16, p[1] / 16, 7, 8) for p in points))

    def test_unchanged_gameplay_lifecycle_and_generator_methods(self):
        paths = ["scenes/world/planet_exterior.gd", "scenes/world/planet_exterior.tscn",
                 "scenes/world/world_coordinates.gd", "scenes/world/planet_world_state.gd",
                 "scenes/world/introductory_ferrite.tres", "scenes/main/playthrough_state.gd",
                 "construction/placement_rules.gd", "construction/machine_definition.gd",
                 "construction/construction_controller.gd", "construction/deployed_machine.gd"]
        for path in paths:
            expected = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT)
            self.assertEqual((ROOT / path).read_bytes().replace(b"\r\n", b"\n"), expected.replace(b"\r\n", b"\n"), path)
        path = "scenes/world/planet_generator.gd"
        actual = (ROOT / path).read_text()
        baseline = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT, text=True)
        start = actual.index("# Presentation-only treatment weights")
        end = actual.index("# World-space samples", start)
        self.assertEqual(actual[:start] + actual[end:], baseline)
        chunk = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        before = subprocess.check_output(["git", "show", f"{BASE}:scenes/world/terrain_chunk.gd"], cwd=ROOT, text=True)
        self.assertEqual(chunk.split("# Low ground details", 1)[1], before.split("# Low ground details", 1)[1])
        self.assertEqual(chunk.count("preload("), 4)
        for forbidden in ("Sprite2D", "TileMapLayer", "Image.new", "ImageTexture", "func _process", "add_child"):
            self.assertNotIn(forbidden, chunk)

    def test_exact_preservation_allowance_rejects_unrelated_edits(self):
        for path in INPUT_SHA256:
            actual = (ROOT / path).read_bytes()
            verify_input(path, actual)
            with self.assertRaises(AssertionError):
                verify_input(path, actual + b"UNRELATED")
        for path in TERRAIN_SHA256:
            actual = (ROOT / path).read_bytes()
            expected = subprocess.check_output(["git", "show", f"{BASE}:{path}"], cwd=ROOT).replace(b"\r\n", b"\n")
            self.assertEqual(preserved_terrain_bytes(path, actual), expected)
            for mutation in (actual + b"\n# Unrelated", actual + actual, actual.replace(b"func ", b"func changed_", 1)):
                with self.assertRaises(AssertionError):
                    preserved_terrain_bytes(path, mutation)


if __name__ == "__main__":
    unittest.main()
