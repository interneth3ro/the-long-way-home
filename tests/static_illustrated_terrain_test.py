"""Nonexecuting illustrated-lab resource, pixel and preservation checks."""
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
BASE = '44d83bc46aebe5409d0c2e7ca0e388531ae1e3c3'
ASSET = 'assets/experiments/native_terrain_47_96/illustrated_v1/'
SCENE = 'scenes/experiments/native_terrain_47_96/illustrated_v1.tscn'
BITS = ('top_left_corner', 'top_side', 'top_right_corner', 'left_side',
        'right_side', 'bottom_left_corner', 'bottom_side', 'bottom_right_corner')


def png_rgb(raw):
    """Decode the supplied noninterlaced RGB PNGs, including every chunk CRC."""
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, packed, kinds = 8, bytearray(), []
    while pos < len(raw):
        size = struct.unpack_from('>I', raw, pos)[0]
        kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+size]
        assert zlib.crc32(kind + data) == struct.unpack_from('>I', raw, pos+8+size)[0]
        if kind == b'IHDR':
            width, height, *mode = struct.unpack('>IIBBBBB', data)
            assert mode == [8, 2, 0, 0, 0]
        if kind == b'IDAT':
            packed.extend(data)
        kinds.append(kind)
        pos += size + 12
    assert pos == len(raw) and kinds[0] == b'IHDR' and kinds[-1] == b'IEND'
    data = zlib.decompress(packed)
    stride = width * 3
    assert len(data) == height * (stride + 1)
    previous, rows = bytearray(stride), []
    for y in range(height):
        offset = y * (stride + 1)
        filtering = data[offset]
        assert filtering in range(5)
        row = bytearray(data[offset+1:offset+1+stride])
        for x in range(stride):
            a = row[x-3] if x >= 3 else 0
            b = previous[x]
            c = previous[x-3] if x >= 3 else 0
            p = a + b - c
            distances = (abs(p-a), abs(p-b), abs(p-c))
            paeth = (a, b, c)[distances.index(min(distances))]
            row[x] = (row[x] + (0, a, b, (a+b)//2, paeth)[filtering]) % 256
        rows.append(bytes(row))
        previous = row
    return width, height, rows


class IllustratedTerrainStaticTest(unittest.TestCase):
    def setUp(self):
        self.manifest = json.loads((ROOT / ASSET / 'mapping.json').read_text())
        self.resource = (ROOT / ASSET / 'illustrated_terrain.tres').read_text()

    def test_original_artwork_integrity_and_reference_only_corners(self):
        originals = self.manifest['original_sha256']
        self.assertEqual(len(originals), 15)  # 14 source tiles and original README
        for name, digest in originals.items():
            raw = (ROOT / ASSET / 'originals' / name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            if name.endswith('.png'):
                self.assertEqual(png_rgb(raw)[:2], (128, 128))
        used = {t['art'] for t in self.manifest['illustrated']}
        for name in ('outer_green_corner.png', 'outer_earth_corner.png',
                     'inner_green_corner.png', 'inner_earth_corner.png'):
            self.assertNotIn(name, used)
        for name in ('earth_solid.png', 'green_solid.png'):
            _, _, rows = png_rgb((ROOT / ASSET / 'originals' / name).read_bytes())
            self.assertEqual(rows[0], rows[-1], name + ': top/bottom')
            self.assertTrue(all(row[:3] == row[-3:] for row in rows), name + ': left/right')

    def test_complete_original_signatures_without_duplicate_or_approximate_mapping(self):
        with (ROOT / 'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv').open(newline='') as f:
            rows = list(csv.DictReader(f))
        expected = {(int(r['atlas_x']), int(r['atlas_y'])):
                    (int(r['tlwh_center']), *(int(r['tlwh_' + b]) for b in BITS)) for r in rows}
        actual = {}
        sources = re.findall(r'\[sub_resource type="TileSetAtlasSource" id="([^"]+)"\]\n(.*?)(?=\n\[)', self.resource, re.S)
        self.assertEqual(len(sources), 11)
        illustrated = {tuple(t['original_atlas']): t for t in self.manifest['illustrated']}
        self.assertEqual(len(illustrated), 10)
        for source, body in sources:
            tile_headers = re.findall(r'^(\d+):(\d+)/0 = 0$', body, re.M)
            for x, y in tile_headers:
                prefix = f'{x}:{y}/0/'
                props = dict(re.findall(r'^' + prefix + r'([^\n=]+) = ([^\n]+)$', body, re.M))
                signature = (int(props['terrain']), *(int(props['terrains_peering_bit/' + b]) for b in BITS))
                if source == 'Diagnostic':
                    coord = (int(x), int(y))
                    self.assertNotIn(coord, illustrated)
                else:
                    entry = next(t for t in illustrated.values() if t['source'] == int(source[3:]))
                    coord = tuple(entry['original_atlas'])
                    self.assertEqual(signature, tuple(entry['signature']))
                self.assertNotIn(coord, actual)
                actual[coord] = signature
        self.assertEqual(actual, expected)
        self.assertEqual(len(set(actual.values())), 94)
        self.assertEqual(self.resource.count('/terrains_peering_bit/'), 752)
        self.assertIn('tile_size = Vector2i(128, 128)', self.resource)
        self.assertEqual(self.resource.count('texture_region_size = Vector2i(128, 128)'), 11)

    def test_complementary_boundaries_and_material_parameters(self):
        entries = self.manifest['illustrated']
        signatures = {tuple(t['signature']) for t in entries}
        for center in (0, 1):
            self.assertIn((center,) * 9, signatures)
            for indices in ((0, 1, 2), (5, 6, 7), (0, 3, 5), (2, 4, 7)):
                peers = [center] * 8
                for i in indices:
                    peers[i] = 1 - center
                self.assertIn((center, *peers), signatures)
        for entry in entries:
            if entry['source'] <= 2:
                continue
            block = re.search(r'\[sub_resource type="ShaderMaterial" id="Mat' + str(entry['source']) + r'"\]\n(.*?)(?=\n\[)', self.resource, re.S)[1]
            s = entry['signature']
            for name, indices in (('top', (1, 2, 3)), ('bottom', (6, 7, 8)),
                                  ('left', (1, 4, 6)), ('right', (3, 5, 8))):
                value = ', '.join(str(s[i]) for i in indices)
                self.assertIn(f'shader_parameter/{name} = Vector3({value})', block)
            self.assertIn('shader_parameter/mirror = Vector2' + str(tuple(entry['mirror'])), block)
        shader = (ROOT / ASSET / 'edge_compatibility.gdshader').read_text()
        self.assertIn('smoothstep(0.0, 8.0, distance_to_edge)', shader)
        self.assertIn('mix(original, compatible, correction)', shader)
        self.assertEqual(self.resource.count('use_texture_padding = false'), 10)

    def test_shared_edge_contract_for_every_illustrated_neighbor_pair(self):
        signatures = [tuple(t['signature']) for t in self.manifest['illustrated']]
        # Border samples follow the three native peers in spatial order. Solid
        # textures are independently checked for opposite-edge pixel equality.
        # This proves the data/mathematical boundary contract, not GPU rendering.
        edges = {'top': (1, 2, 3), 'bottom': (6, 7, 8),
                 'left': (1, 4, 6), 'right': (3, 5, 8)}
        cross_terrain = set()
        for direction, opposite in (('right', 'left'), ('bottom', 'top')):
            for a in signatures:
                for b in signatures:
                    ea = tuple(a[i] for i in edges[direction])
                    eb = tuple(b[i] for i in edges[opposite])
                    if ea != eb:
                        continue
                    if a[0] != b[0]:
                        cross_terrain.add((direction, a[0], ea))
                    for pixel in range(128):
                        t = pixel / 127
                        segment = 0 if t <= .5 else 1
                        u = t * 2 - segment
                        weight = u * u * (3 - 2*u)
                        va = ea[segment]*(1-weight) + ea[segment+1]*weight
                        vb = eb[segment]*(1-weight) + eb[segment+1]*weight
                        self.assertEqual(va, vb)
        self.assertEqual(cross_terrain, {(direction, c, (p, p, p))
                         for direction in ('right', 'bottom') for c in (0, 1) for p in (0, 1)})

    def test_exact_new_input_guards_reject_tampering_and_protected_paths(self):
        from illustrated_terrain_preservation import INPUT_SHA256, verify_input
        self.assertEqual(len(INPUT_SHA256), 21)
        for path in INPUT_SHA256:
            raw = (ROOT / path).read_bytes()
            verify_input(path, raw)
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.assertRaises(AssertionError):
                    verify_input(path, bad)
        for path, digest in self.manifest['protected_working_sha256'].items():
            raw = (ROOT / path).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest, path)
            with self.assertRaises(AssertionError):
                verify_input(path, raw)

    def test_references_diagnostic_visibility_and_production_preservation(self):
        scene = (ROOT / SCENE).read_text()
        for text in (scene, self.resource):
            for path in re.findall(r'path="res://([^"]+)"', text):
                self.assertTrue((ROOT / path).is_file(), path)
        self.assertNotIn('script =', scene)
        self.assertNotIn('tile_map_data', scene)
        self.assertIn('84 MAGENTA-MARKED DIAGNOSTIC', scene)
        svg = (ROOT / ASSET / 'unsupported_diagnostic.svg').read_text()
        self.assertEqual(svg.count('fill="#ff00ff"'), 84)
        # All baseline source/assets and protected owner working bytes must remain
        # unchanged. Only one narrowly amended historical guard may differ.
        files = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE], cwd=ROOT, text=True).splitlines()
        for path in files:
            if path.startswith(('assets/', 'scenes/', 'construction/', 'dialogue/', 'inventory/',
                                'objectives/', 'shaders/', 'tools/')) or path in ('project.godot', 'AGENTS.md', 'docs/LOCAL_TESTING.md'):
                old = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
                now = (ROOT / path).read_bytes()
                if not path.endswith(('.png', '.ttf')):
                    old, now = old.replace(b'\r\n', b'\n'), now.replace(b'\r\n', b'\n')
                self.assertEqual(old, now, path)


if __name__ == '__main__':
    unittest.main()
