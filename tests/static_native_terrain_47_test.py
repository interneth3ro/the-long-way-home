"""Read-only configuration/PNG checks; never runs Godot or project code."""
import csv
import hashlib
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSET = 'assets/experiments/native_terrain_47_96/'
DOC = 'docs/experiments/native_terrain_47_96/'
SCENE = 'scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn'
BASE = '48cd9150d7aa2e029c7328229e7865cf00e83723'
BITS = ('top_left_corner', 'top_side', 'top_right_corner', 'left_side',
        'right_side', 'bottom_left_corner', 'bottom_side', 'bottom_right_corner')


class Native47StaticTest(unittest.TestCase):
    def setUp(self):
        with (ROOT / DOC / 'tlwh_47_pattern_mapping.csv').open(newline='') as f:
            self.rows = list(csv.DictReader(f))
        self.resource = (ROOT / ASSET / 'experimental_match_corners_and_sides.tres').read_text()

    def test_supplied_mapping_integrity_and_agreement(self):
        attrs = (ROOT / '.gitattributes').read_text()
        for extension in ('csv', 'md'):
            self.assertIn(DOC + f'tlwh_47_pattern_mapping.{extension} -text', attrs)
        for name, digest in (
            ('csv', 'c18738b5118b2e792cbbe9f9fcc14788d5db302dc4c828baca5895668d70bb11'),
            ('md', '6e059dfe02476dfd06610fb8550b1dffa8c10a84c1ec5d922fd18895f5bb3e5d'),
        ):
            self.assertEqual(hashlib.sha256((ROOT / DOC / f'tlwh_47_pattern_mapping.{name}').read_bytes()).hexdigest(), digest)
        self.assertEqual(len(self.rows), 47)
        self.assertEqual([int(r['pattern']) for r in self.rows], list(range(1, 48)))
        self.assertEqual(len({tuple(r['tlwh_' + b] for b in BITS) for r in self.rows}), 47)
        coords = {(int(r['reference_atlas_x']), int(r['reference_atlas_y'])) for r in self.rows}
        self.assertEqual(coords, {(x, y) for y in range(4, 8) for x in range(12)} - {(10, 5)})
        for row in self.rows:
            self.assertEqual(row['tlwh_center_green'], '1')
            self.assertTrue(all(row['tlwh_' + b] in ('0', '1') for b in BITS))
        md = (ROOT / DOC / 'tlwh_47_pattern_mapping.md').read_text(encoding='utf-8')
        table = re.findall(r'^\| (\d+) \| \((\d+),(\d+)\) \| (.*?) \|$', md, re.M)
        self.assertEqual([[a, b, c, *[v.strip() for v in tail.split('|')]] for a, b, c, tail in table],
                         [list(row.values()) for row in self.rows])
        self.assertIn('Grass (1) → TLWH Earth (0)', md)
        self.assertIn('Dirt (2) → TLWH Green (1)', md)

    def test_resource_exact_inventory_assignments_and_references(self):
        text = self.resource
        self.assertEqual(text.count('type="TileSetAtlasSource"'), 1)
        self.assertIn('texture_region_size = Vector2i(16, 16)', text)
        self.assertIn('tile_size = Vector2i(16, 16)', text)
        self.assertEqual(re.findall(r'^terrain_set_\d+/mode = (\d+)$', text, re.M), ['0'])
        self.assertEqual(re.findall(r'^terrain_set_0/terrain_\d+/name = "([^"]+)"$', text, re.M),
                         ['Weathered Earth', 'Low Green Cover'])
        actual = {}
        for line in text.splitlines():
            if re.match(r'^\d+:\d+/0', line):
                key, value = line.split(' = ')
                self.assertNotIn(key, actual)
                actual[key] = int(value)
        expected = {}
        for row in self.rows:
            prefix = f"{row['reference_atlas_x']}:{row['reference_atlas_y']}/0"
            expected.update({prefix: 0, prefix + '/terrain_set': 0, prefix + '/terrain': 1})
            expected.update({prefix + '/terrains_peering_bit/' + b: int(row['tlwh_' + b]) for b in BITS})
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 47 * 11)
        self.assertEqual(re.findall(r'^sources/\d+ = .*$', text, re.M), ['sources/0 = SubResource("TileSetAtlasSource_47")'])
        self.assertEqual(re.findall(r'path="res://([^"]+)"', text), [ASSET + 'experimental_47_patterns.png'])
        for forbidden in ('physics_layer', 'navigation_layer', 'custom_data', 'script ='):
            self.assertNotIn(forbidden, text)

    def test_png_crc_dimensions_inventory_and_every_visual_sector(self):
        raw = (ROOT / ASSET / 'experimental_47_patterns.png').read_bytes()
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        pos, compressed, kinds = 8, bytearray(), []
        while pos < len(raw):
            size = struct.unpack_from('>I', raw, pos)[0]
            kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+size]
            self.assertEqual(zlib.crc32(kind + data), struct.unpack_from('>I', raw, pos+8+size)[0])
            if kind == b'IHDR':
                self.assertEqual(struct.unpack('>IIBBBBB', data), (192, 128, 8, 6, 0, 0, 0))
            elif kind == b'IDAT':
                compressed.extend(data)
            kinds.append(kind)
            pos += size + 12
        self.assertEqual(pos, len(raw))
        self.assertEqual(kinds, [b'IHDR', b'tEXt', b'IDAT', b'IEND'])
        self.assertIn(b'EXPERIMENTAL Issue 96', raw)
        scan = zlib.decompress(compressed)
        self.assertEqual(len(scan), 128 * 769)
        for y in range(128):
            self.assertEqual(scan[y*769], 0)
        by_coord = {(int(r['reference_atlas_x']), int(r['reference_atlas_y'])): r for r in self.rows}
        sectors = (('top_left_corner', 'top_side', 'top_right_corner'),
                   ('left_side', 'center_green', 'right_side'),
                   ('bottom_left_corner', 'bottom_side', 'bottom_right_corner'))
        palette = {0: bytes((156, 100, 62, 255)), 1: bytes((74, 170, 82, 255))}
        occupied = set()
        for y in range(128):
            for x in range(192):
                coord = (x // 16, y // 16)
                offset = y*769 + 1 + x*4
                pixel = scan[offset:offset+4]
                if coord not in by_coord:
                    self.assertEqual(pixel, bytes(4))
                    continue
                occupied.add(coord)
                sx = 0 if x % 16 < 4 else (2 if x % 16 >= 12 else 1)
                sy = 0 if y % 16 < 4 else (2 if y % 16 >= 12 else 1)
                self.assertEqual(pixel, palette[int(by_coord[coord]['tlwh_' + sectors[sy][sx]])])
        self.assertEqual(len(occupied), 47)

    def test_known_missing_centers_and_extreme_patterns(self):
        by_number = {int(r['pattern']): r for r in self.rows}
        self.assertTrue(all(by_number[33]['tlwh_' + b] == '1' for b in BITS))
        self.assertTrue(all(by_number[36]['tlwh_' + b] == '0' for b in BITS))
        self.assertEqual(by_number[36]['tlwh_center_green'], '1')
        self.assertFalse(any(r['tlwh_center_green'] == '0' for r in self.rows))
        report = (ROOT / 'docs/NATIVE_TERRAIN_47_PROTOTYPE.md').read_text()
        self.assertIn('no Earth-centered configurations', report)
        self.assertIn('NOT RUN', report)

    def test_lab_references_and_production_isolation(self):
        scene = (ROOT / SCENE).read_text()
        self.assertEqual(re.findall(r'path="res://([^"]+)"', scene),
                         [ASSET + 'experimental_match_corners_and_sides.tres', ASSET + 'experimental_47_patterns.png'])
        self.assertEqual(scene.count('type="TileMapLayer"'), 1)
        self.assertNotIn('script =', scene)
        self.assertNotIn('tile_map_data', scene)
        self.assertIn('texture_filter = 1', scene)
        for text in (scene, self.resource):
            for ref in re.findall(r'path="res://([^"]+)"', text):
                self.assertTrue((ROOT / ref).is_file(), ref)
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
        for path in paths:
            if path == 'project.godot' or path.startswith(('assets/', 'scenes/', 'construction/', 'inventory/', 'dialogue/', 'objectives/', 'shaders/', 'tools/')) or path in ('AGENTS.md', 'docs/LOCAL_TESTING.md'):
                baseline = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)
                self.assertEqual((ROOT / path).read_bytes().replace(b'\r\n', b'\n'), baseline.replace(b'\r\n', b'\n'), path)
        for path in paths:
            if path.endswith(('.gd', '.tscn', '.tres', '.godot')):
                self.assertNotIn('native_terrain_47_96', (ROOT / path).read_text(encoding='utf-8'), path)


if __name__ == '__main__':
    unittest.main()
