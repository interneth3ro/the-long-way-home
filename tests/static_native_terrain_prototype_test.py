"""Nonexecuting Issue 96 fixture checks. Does not import project code or Godot."""
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'assets/experiments/native_terrain_96'
SCENE = ROOT / 'scenes/experiments/native_terrain_96/terrain_painting_lab.tscn'
BASE = '48cd915'
CORNERS = ('top_left_corner', 'top_right_corner',
           'bottom_left_corner', 'bottom_right_corner')


def tile_properties():
    text = (ASSET / 'experimental_match_corners.tres').read_text()
    tiles = {}
    for x, y, prop, value in re.findall(
            r'^(\d+):(\d+)/0(?:/([^=]+?))? = (\d+)$', text, re.M):
        key = (int(x), int(y))
        props = tiles.setdefault(key, {})
        assert prop not in props, 'duplicate tile property'
        props[prop] = int(value)
    return text, tiles


class NativeTerrainPrototypeStaticTest(unittest.TestCase):
    def test_png_integrity_palette_and_every_corner_pixel(self):
        raw = (ASSET / 'experimental_corner_masks_16.png').read_bytes()
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        pos, compressed, kinds, title = 8, bytearray(), [], b''
        while pos < len(raw):
            size = struct.unpack_from('>I', raw, pos)[0]
            kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+size]
            self.assertEqual(zlib.crc32(kind+data),
                             struct.unpack_from('>I', raw, pos+8+size)[0])
            kinds.append(kind)
            if kind == b'IHDR':
                self.assertEqual(struct.unpack('>IIBBBBB', data),
                                 (128, 128, 8, 2, 0, 0, 0))
            if kind == b'tEXt':
                title += data
            if kind == b'IDAT':
                compressed.extend(data)
            pos += size+12
        self.assertEqual(pos, len(raw))
        self.assertEqual(kinds, [b'IHDR', b'tEXt', b'IDAT', b'IEND'])
        self.assertIn(b'EXPERIMENTAL', title)
        scan = zlib.decompress(compressed)
        self.assertEqual(len(scan), 128*385)
        colors = (bytes((139, 94, 60)), bytes((101, 124, 79)))
        for y in range(128):
            self.assertEqual(scan[y*385], 0)
            for x in range(128):
                # Independent quadrant lookup: TL, TR, BL, BR.
                mask = (y//32)*4+x//32
                corner = (y % 32 >= 16)*2+(x % 32 >= 16)
                start = y*385+1+x*3
                self.assertEqual(scan[start:start+3],
                                 colors[(mask >> corner) & 1])

    def test_resource_topology_and_exact_assignments(self):
        text, tiles = tile_properties()
        self.assertEqual(text.count('[sub_resource '), 1)
        self.assertEqual(text.count('[ext_resource '), 1)
        self.assertIn('type="TileSetAtlasSource"', text)
        self.assertIn('texture_region_size = Vector2i(32, 32)', text)
        self.assertIn('tile_size = Vector2i(32, 32)', text)
        self.assertIn('terrain_set_0/mode = 1', text)
        self.assertEqual(re.findall(r'terrain_set_(\d+)/mode', text), ['0'])
        self.assertEqual(re.findall(r'terrain_set_0/terrain_(\d+)/name = "(\w+)"', text),
                         [('0', 'Earth'), ('1', 'Green')])
        self.assertEqual(re.findall(r'^sources/(\d+) = ', text, re.M), ['0'])
        self.assertEqual(set(tiles), {(x, y) for x in range(4) for y in range(4)})
        for (x, y), props in tiles.items():
            mask = y*4+x
            expected = {'': 0, 'terrain_set': 0,
                        'terrain': int(bin(mask).count('1') >= 3)}
            expected.update({f'terrains_peering_bit/{name}': (mask >> bit) & 1
                             for bit, name in enumerate(CORNERS)})
            self.assertEqual(props, expected)
        self.assertNotRegex(text, r'\d+:\d+/[1-9]')  # no hidden alternatives

    def test_corner_coverage_does_not_imply_center_completeness(self):
        _, tiles = tile_properties()
        actual = {(p['terrain'], tuple(p['terrains_peering_bit/'+c] for c in CORNERS))
                  for p in tiles.values()}
        full = {(center, tuple((m >> i) & 1 for i in range(4)))
                for center in range(2) for m in range(16)}
        self.assertEqual(len(actual), 16)
        self.assertEqual(len(full-actual), 16)
        # Center islands absent despite complete four-corner coverage.
        self.assertNotIn((1, (0, 0, 0, 0)), actual)
        self.assertNotIn((0, (1, 1, 1, 1)), actual)

    def test_lab_is_editor_only_and_references_resolve(self):
        text = SCENE.read_text()
        self.assertEqual(text.count('type="TileMapLayer"'), 1)
        self.assertIn('tile_set = ExtResource("1_tiles")', text)
        self.assertIn('texture_filter = 1', text)
        self.assertNotIn('script =', text)
        self.assertNotIn('tile_map_data', text)
        self.assertNotIn('instance=', text)
        for source in (text, (ASSET/'experimental_match_corners.tres').read_text()):
            for path in re.findall(r'path="res://([^"]+)"', source):
                self.assertTrue((ROOT/path).is_file(), path)
                self.assertIn('/experiments/native_terrain_96/', '/'+path)

    def test_production_and_existing_owner_assets_preserved(self):
        # Compare all pre-existing tracked inputs, including runner/policy and art.
        # Only the documentation entry point may change in this experiment.
        names = subprocess.check_output(
            ['git', 'diff', '--name-only', BASE, '--'], cwd=ROOT, text=True).splitlines()
        allowed = {'README.md', 'docs/NATIVE_TERRAIN_PROTOTYPE.md',
                   'tests/static_native_terrain_prototype_test.py',
                   'scenes/experiments/native_terrain_96/terrain_painting_lab.tscn',
                   'assets/experiments/native_terrain_96/experimental_corner_masks_16.png',
                   'assets/experiments/native_terrain_96/experimental_match_corners.tres'}
        self.assertFalse(set(names)-allowed, set(names)-allowed)
        self.assertNotIn('native_terrain_96', (ROOT/'project.godot').read_text())


if __name__ == '__main__':
    unittest.main()
