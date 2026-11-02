"""Static texture decoding, sampling models and exact preservation; no Godot."""
import math
from pathlib import Path
import runpy
import struct
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
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


def earth_tint(color):
    """Arithmetic model only; the source contract below binds these equations."""
    r, g, b, a = color
    mean = (r + g + b) / 3
    green_bias = max(0, g - (r + b) * 0.5)
    brightness = min(0.99, max(0.84, 0.94 + (mean - 0.30) * 0.4 - green_bias))
    warmth = min(0.015, max(-0.015, (r - b) * 0.15))
    return (brightness + warmth, brightness, brightness - warmth, a)


class WeatheredEarthStaticTest(unittest.TestCase):
    def test_uv_array_uses_shared_runtime_initializer(self):
        source = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        self.assertIn("static var _texture_uvs := PackedVector2Array(", source)
        self.assertNotIn("const TEXTURE_UVS", source)
        self.assertEqual(source.count("_texture_uvs :="), 1)
        self.assertEqual(source.count("draw_polygon(vertices, colors, _texture_uvs,"), 1)


    def test_warm_tint_bounds_and_authored_variation(self):
        source = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        for equation in (
            "var mean := (color.r + color.g + color.b) / 3.0",
            "var green_bias := maxf(0.0, color.g - (color.r + color.b) * 0.5)",
            "var brightness := clampf(0.94 + (mean - 0.30) * 0.4 - green_bias, 0.84, 0.99)",
            "var warmth := clampf((color.r - color.b) * 0.15, -0.015, 0.015)",
            "return Color(brightness + warmth, brightness, brightness - warmth, color.a)",
            "_colors[index] = _earth_tint(color)",
        ):
            self.assertIn(equation, source)
        self.assertNotIn("255.0 /", source)
        # Sweep includes extreme stored RGB edits. Hue must remain warm even
        # when the legacy input is neutral gray, pure green or pure blue.
        for r in (0, 0.25, 0.5, 0.75, 1):
            for g in (0, 0.25, 0.5, 0.75, 1):
                for b in (0, 0.25, 0.5, 0.75, 1):
                    tint = earth_tint((r, g, b, 0.7))
                    output = [v * t / 255 for v, t in zip((156, 141, 121), tint)]
                    self.assertTrue(output[0] > output[1] > output[2])
                    self.assertTrue(all(0.825 - 1e-12 <= t <= 1.005 for t in tint[:3]))
                    self.assertEqual(tint[3], 0.7)
        weathered = earth_tint((0.27, 0.30, 0.29, 1))
        clearing = earth_tint((0.32, 0.34, 0.29, 1))
        scar = earth_tint((0.21, 0.22, 0.22, 1))
        self.assertLess(scar[1], clearing[1])
        self.assertLess(clearing[1], weathered[1])
        # Continuous arithmetic, including near the green-bias branch.
        a = earth_tint((0.30, 0.30 - 1e-7, 0.30, 1))
        b = earth_tint((0.30, 0.30 + 1e-7, 0.30, 1))
        self.assertLess(max(abs(x - y) for x, y in zip(a, b)), 1e-6)

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
        chunk = (ROOT / "scenes/world/terrain_chunk.gd").read_text()
        self.assertIn("generator.sample_color(origin + Vector2i(x - 1, y - 1), state)", chunk)
        self.assertIn("samples[(y + 1) * SAMPLE_WIDTH + x + 1]) / 4.0", chunk)
        # Build each full chunk independently, using a synthetic deterministic
        # legacy field plus a stored edit at a boundary. No GDScript execution.
        def colors(cx, cy, seed):
            samples = {}
            for y in range(34):
                for x in range(34):
                    tx, ty = cx * 32 + x - 1, cy * 32 + y - 1
                    a = noise((tx + 0.5) / 12, (ty + 0.5) / 12, seed, 1)
                    b = noise((tx + 0.5) / 8, (ty + 0.5) / 8, seed, 2)
                    samples[x, y] = ((0.8, 0.2, 0.1, 1) if (tx, ty) == (-1, -1)
                                     else (0.25 + a * 0.1, 0.28 + b * 0.06, 0.24 + a * 0.08, 1))
            return {(x, y): earth_tint(tuple(sum(samples[x + dx, y + dy][c]
                    for dx, dy in ((0, 0), (1, 0), (0, 1), (1, 1))) / 4 for c in range(4)))
                    for y in range(33) for x in range(33)}

        for seed in (26026, 1, -42):
            for cx, cy in ((0, 0), (-1, -1), (-2, 1), (3, -4)):
                center = colors(cx, cy, seed)
                east = colors(cx + 1, cy, seed)
                south = colors(cx, cy + 1, seed)
                for offset in range(33):
                    self.assertEqual(center[32, offset], east[0, offset])
                    self.assertEqual(center[offset, 32], south[offset, 0])
                self.assertEqual(center, colors(cx, cy, seed))  # Regeneration.
        self.assertNotEqual(colors(-1, -1, 26026), colors(-1, -1, 7))


if __name__ == "__main__":
    unittest.main()
