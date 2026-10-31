"""Read-only configuration/PNG checks; never runs Godot or project code."""
import csv
import hashlib
import json
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
            self.original_rows = list(csv.DictReader(f))
        with (ROOT / DOC / 'tlwh_94_pattern_mapping.csv').open(newline='') as f:
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
        original = self.original_rows
        self.assertEqual(len(original), 47)
        self.assertEqual([int(r['pattern']) for r in original], list(range(1, 48)))
        self.assertEqual(len({tuple(r['tlwh_' + b] for b in BITS) for r in original}), 47)
        coords = {(int(r['reference_atlas_x']), int(r['reference_atlas_y'])) for r in original}
        self.assertEqual(coords, {(x, y) for y in range(4, 8) for x in range(12)} - {(10, 5)})
        for row in original:
            self.assertEqual(row['tlwh_center_green'], '1')
            self.assertTrue(all(row['tlwh_' + b] in ('0', '1') for b in BITS))
        md = (ROOT / DOC / 'tlwh_47_pattern_mapping.md').read_text(encoding='utf-8')
        table = re.findall(r'^\| (\d+) \| \((\d+),(\d+)\) \| (.*?) \|$', md, re.M)
        self.assertEqual([[a, b, c, *[v.strip() for v in tail.split('|')]] for a, b, c, tail in table],
                         [list(row.values()) for row in original])
        self.assertIn('Grass (1) → TLWH Earth (0)', md)
        self.assertIn('Dirt (2) → TLWH Green (1)', md)

    def test_extracted_reference_and_both_family_remaps(self):
        raw = (ROOT / DOC / 'reference_corners_and_sides.json').read_bytes().replace(b'\r\n', b'\n')
        self.assertEqual(hashlib.sha256(raw).hexdigest(), 'e0c6497b08f35a6138f98b4b70b70fa1ee5de086639c7d52310416b4cc5bd6b2')
        source = json.loads(raw)
        self.assertEqual(source['archive_sha256'], '9b9e26b25138d4c4b8fa83430204d2e5b571795cda48673f199d822e9d4a1971')
        self.assertEqual(source['scene_sha256'], '1f67cf862a16c90eb2ffb6076cc2980d453e33b24b19b35e8e7806acc0e94582')
        self.assertEqual(source['atlas_subresource'], 'TileSetAtlasSource_matpb')
        self.assertEqual(source['terrain_set_mode'], 0)
        tiles = source['tiles']
        self.assertEqual(len(tiles), 95)
        self.assertEqual([sum(t['center'] == c for t in tiles) for c in (0, 1, 2)], [1, 47, 47])
        lookup = {(t['atlas_x'], t['atlas_y']): t for t in tiles}
        self.assertEqual(len(lookup), 95)
        self.assertEqual(lookup[10, 1], dict(atlas_x=10, atlas_y=1, center=0, peers=dict.fromkeys(BITS, 0)))
        self.assertEqual(len(self.rows), 94)
        coords = set()
        for family, ref_center, center, remap, y0 in (
            ('earth', 1, 0, {1: 0, 0: 1}, 0), ('green', 2, 1, {2: 1, 1: 0}, 4),
        ):
            rows = [r for r in self.rows if r['family'] == family]
            self.assertEqual(len(rows), 47)
            self.assertEqual([int(r['pattern']) for r in rows], list(range(1, 48)))
            self.assertEqual(len({tuple(r['tlwh_' + b] for b in BITS) for r in rows}), 47)
            family_coords = {(int(r['atlas_x']), int(r['atlas_y'])) for r in rows}
            self.assertEqual(family_coords, {(x, y) for x in range(12) for y in range(y0, y0+4)} - {(10, y0+1)})
            self.assertFalse(coords & family_coords)
            coords |= family_coords
            for row in rows:
                coord = (int(row['reference_atlas_x']), int(row['reference_atlas_y']))
                self.assertEqual(coord, (int(row['atlas_x']), int(row['atlas_y'])))
                ref = lookup[coord]
                self.assertEqual(int(row['reference_center']), ref['center'])
                self.assertEqual(ref['center'], ref_center)
                self.assertEqual(int(row['tlwh_center']), center)
                for bit in BITS:
                    self.assertEqual(int(row['reference_' + bit]), ref['peers'][bit])
                    self.assertEqual(int(row['tlwh_' + bit]), remap[ref['peers'][bit]])
        green = [r for r in self.rows if r['family'] == 'green']
        for old, new in zip(self.original_rows, green):
            self.assertEqual(old['tlwh_center_green'], new['tlwh_center'])
            for key in ('pattern', 'reference_atlas_x', 'reference_atlas_y', *('tlwh_' + b for b in BITS)):
                self.assertEqual(old[key], new[key])

    def test_resource_exact_inventory_assignments_and_references(self):
        text = self.resource
        self.assertEqual(text.count('type="TileSetAtlasSource"'), 1)
        # Owner editor serialization omits these properties at their 16px defaults.
        for prop in ('texture_region_size', 'tile_size'):
            value = re.findall(r'^' + prop + r' = (.*)$', text, re.M)
            self.assertIn(value, ([], ['Vector2i(16, 16)']))
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
            prefix = f"{row['atlas_x']}:{row['atlas_y']}/0"
            expected.update({prefix: 0, prefix + '/terrain_set': 0, prefix + '/terrain': int(row['tlwh_center'])})
            expected.update({prefix + '/terrains_peering_bit/' + b: int(row['tlwh_' + b]) for b in BITS})
        self.assertEqual(actual, expected)
        self.assertEqual(len(actual), 94 * 11)
        self.assertEqual(sum('/terrains_peering_bit/' in key for key in actual), 752)
        self.assertEqual([sum(v == c for k, v in actual.items() if k.endswith('/terrain')) for c in (0, 1)], [47, 47])
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
        by_coord = {(int(r['atlas_x']), int(r['atlas_y'])): r for r in self.rows}
        sectors = (('top_left_corner', 'top_side', 'top_right_corner'),
                   ('left_side', 'center', 'right_side'),
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
        self.assertEqual(len(occupied), 94)

    def test_center_plus_peer_uniqueness_and_shared_peer_extremes(self):
        signatures = {(int(r['tlwh_center']), *(int(r['tlwh_' + b]) for b in BITS)) for r in self.rows}
        self.assertEqual(len(signatures), 94)
        families = [{tuple(int(r['tlwh_' + b]) for b in BITS) for r in self.rows if r['family'] == family}
                    for family in ('earth', 'green')]
        self.assertEqual(families[0] & families[1], {(0,) * 8, (1,) * 8})
        for center in (0, 1):
            for peer in (0, 1):
                self.assertIn((center, *((peer,) * 8)), signatures)
        report = (ROOT / 'docs/NATIVE_TERRAIN_47_PROTOTYPE.md').read_text()
        self.assertIn('94', report)
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
        # Check committed and proposed PR inputs. Owner playtesting edits are
        # intentionally preserved in the working tree; legacy suite checks still
        # inspect those working bytes and may fail independently of this PR.
        for args in (['git', 'diff', BASE, 'HEAD', '--name-only'],
                     ['git', 'diff', BASE, '--cached', '--name-only']):
            changed = subprocess.check_output(args, cwd=ROOT, text=True).splitlines()
            for path in changed:
                protected = path == 'project.godot' or path.startswith(('assets/', 'scenes/', 'construction/', 'inventory/', 'dialogue/', 'objectives/', 'shaders/', 'tools/')) or path in ('AGENTS.md', 'docs/LOCAL_TESTING.md')
                if protected:
                    if path == 'tools/bake-illustrated-terrain.py':
                        # Exact offline authoring recipe only; no engine/runner scope.
                        from baked_terrain_preservation import verify_input
                        verify_input(path, (ROOT / path).read_bytes())
                        continue
                    self.assertTrue(path.startswith((ASSET, 'scenes/experiments/native_terrain_47_96/')), path)
        for path in paths:
            if path.endswith(('.gd', '.tscn', '.tres', '.godot')):
                self.assertNotIn('native_terrain_47_96', (ROOT / path).read_text(encoding='utf-8'), path)


if __name__ == '__main__':
    unittest.main()
