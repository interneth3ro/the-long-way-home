"""Nonexecuting source, PNG integrity and arithmetic models; never runs Godot."""
import hashlib
import math
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zlib
from production_terrain_preservation import historical_presenter_bytes

from static_weathered_earth_test import (ROOT, GREEN_BASE, GREEN_SHA256,
    coordinate_random, noise, weathered_bytes, original_green_bytes)

ART = ROOT / 'assets/environment/exterior/low_green_ground_cover_provisional'
ASSETS = {
    'a_balanced_cover': '85043ba1079be6fa1577312bcd2d0884b66efa5f0b7592bd7ccaeb96baae978d',
    'b_moss_dominant': '38048cb8d8ca542df4a7f247b4a0c917e306d7b9c949a3d08ed3b3ef26f31ad3',
    'c_exposed_earth': 'f5f81c6fcf6a906d96f6e8b7dfe9bdfad65deb83d327bcb2368f30c30032db5a',
    'd_fine_grass': 'dd50462374578046c3f6822f4e8f02d85f6d7e571dfee9a06fe43e0c7c090009',
}


def decode_png(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, compressed, kinds = 8, bytearray(), []
    while pos < len(raw):
        length = struct.unpack_from('>I', raw, pos)[0]
        kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+length]
        assert zlib.crc32(kind + data) == struct.unpack_from('>I', raw, pos+8+length)[0]
        if kind == b'IHDR':
            assert struct.unpack('>IIBBBBB', data) == (128, 128, 8, 2, 0, 0, 0)
        if kind == b'IDAT':
            compressed.extend(data)
        kinds.append(kind)
        pos += length + 12
    assert pos == len(raw) and kinds[0] == b'IHDR' and kinds[-1] == b'IEND'
    scan = zlib.decompress(compressed)
    assert len(scan) == 128 * 385
    previous, rows = bytearray(384), []
    for y in range(128):
        mode, row = scan[y*385], bytearray(scan[y*385+1:(y+1)*385])
        assert 0 <= mode <= 4
        for i in range(384):
            a, b, c = (row[i-3] if i >= 3 else 0), previous[i], (previous[i-3] if i >= 3 else 0)
            p = a + b - c
            distances = [abs(p-a), abs(p-b), abs(p-c)]
            paeth = (a, b, c)[distances.index(min(distances))]
            row[i] = (row[i] + (0, a, b, (a+b)//2, paeth)[mode]) % 256
        rows.append(bytes(row))
        previous = row
    return rows


def edge_distance(point, polygon):
    result = math.inf
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        dx, dy = b[0]-a[0], b[1]-a[1]
        t = max(0, min(1, ((point[0]-a[0])*dx+(point[1]-a[1])*dy)/(dx*dx+dy*dy)))
        result = min(result, math.hypot(point[0]-a[0]-t*dx, point[1]-a[1]-t*dy))
    return result


def inside(point, polygon):
    x, y = point
    hit = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            hit = not hit
    return hit


def material(x, y, seed, protected=(), overlays=(), anchors=()):
    point = ((x+0.5)*64, (y+0.5)*64)
    if protected and (inside(point, protected) or edge_distance(point, protected) < 48):
        return 0
    if any(math.dist(point, a) < 160 for a in anchors):
        return 0
    if any(inside(point, p) or edge_distance(point, p) < 256 for p in overlays):
        return 0
    cover = noise((x+0.5)/12, (y+0.5)/12, seed, 8) + noise((x+0.5)/3, (y+0.5)/3, seed, 9)*0.18
    return 0 if cover < 0.64 else 1 + min(3, int(coordinate_random(x,y,seed,10)*4))


class LowGreenStaticTest(unittest.TestCase):
    def test_exact_assets_metadata_integrity_shared_edges_palette(self):
        family = []
        for name, digest in ASSETS.items():
            raw = (ART / (name+'.png')).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            rows = decode_png(raw)
            family.append(rows)
            means = [sum(row[c::3][i] for row in rows for i in range(128))/16384 for c in range(3)]
            self.assertTrue(40 < means[2] < means[0] < 180)
            self.assertTrue(means[1] > means[2])
        for a in family:
            for b in family:
                self.assertEqual(a[0], b[-1])
                self.assertEqual([r[:3] for r in a], [r[-3:] for r in b])
        self.assertEqual(len({b''.join(r) for r in family}), 4)

    def test_single_pass_resources_precomputed_bounded_work(self):
        chunk = (ROOT/'scenes/world/terrain_chunk.gd').read_text()
        generator = (ROOT/'scenes/world/planet_generator.gd').read_text()
        drawing = chunk.split('func _draw() -> void:')[1].split('# Low ground details')[0]
        self.assertEqual(drawing.count('draw_polygon('), 1)
        self.assertIn('GROUND_TEXTURES[ground_material]', drawing)
        self.assertNotIn('generator.', drawing)
        self.assertEqual(chunk.count('preload('), 5)
        for name in ASSETS:
            self.assertIn(f'/{name}.png")', chunk)
        for path in re.findall(r'preload\("res://([^\"]+)"\)', chunk):
            self.assertTrue((ROOT/path).is_file())
        self.assertIn('_ground_materials.resize(WorldCoordinates.CHUNK_TILES * WorldCoordinates.CHUNK_TILES)', chunk)
        self.assertEqual(chunk.count('generator.sample_ground_material(tile)'), 1)
        self.assertIn('coordinate * WorldCoordinates.CHUNK_TILES + Vector2i(x, y)', chunk)
        method = generator.split('func sample_ground_material')[1]
        self.assertEqual(method.count('_noise('), 2)
        self.assertIn('_noise(point / 768.0, 8) + _noise(point / 192.0, 9) * 0.18', method)
        self.assertIn('if cover < 0.64:', method)
        self.assertIn('1 + mini(3, int(coordinate_random(tile, 10) * 4.0))', method)
        for forbidden in ('Sprite2D', 'add_child', 'Image.new', 'ImageTexture', 'func _process', 'Shader'):
            self.assertNotIn(forbidden, chunk)
        self.assertNotIn('state.', method)
        self.assertIn('if is_protected(point):', method)
        self.assertIn('_overlay_weight(point, overlay.polygon, float(overlay.feather)) > 0.0', method)
        self.assertEqual(32*32, 1024)  # One byte and one polygon per cell.
        self.assertEqual(34*34*2 + 32*32*2, 4360)  # Maximum noise calls, not timings.

    def test_cluster_selection_boundaries_regeneration_visit_order(self):
        for seed in (26026, 1, -42):
            tiles = [(x,y) for y in range(-48,48) for x in range(-48,48)]
            expected = {tile: material(*tile,seed) for tile in tiles}
            chunks = {}
            for x,y in reversed(tiles):
                cx,cy = x//32,y//32
                lx,ly = x%32,y%32
                chunks[x,y] = material(cx*32+lx,cy*32+ly,seed)
            self.assertEqual(expected, chunks)
            self.assertEqual(set(expected.values()), set(range(5)))
            green = [t for t,v in expected.items() if v]
            self.assertTrue(0.1 < len(green)/len(tiles) < 0.7)
            # Clusters, rather than independent/checkerboard material choice.
            pairs = [(t,(t[0]+1,t[1])) for t in green if (t[0]+1,t[1]) in expected]
            self.assertGreater(sum(bool(expected[b]) for a,b in pairs)/len(pairs), 0.7)
            for x,y in ((-33,-32),(-1,0),(31,32),(32,-1)):
                self.assertEqual(material(x,y,seed), expected[x,y])
        self.assertNotEqual([material(x,30,1) for x in range(50)], [material(x,30,2) for x in range(50)])

    def test_authored_clearing_masks_and_authority_preserved(self):
        scene = (ROOT/'scenes/world/planet_exterior.tscn').read_text()
        overlays = []
        for values in re.findall(r'polygon = PackedVector2Array\(([^)]+)\)', scene.split('[node name="FerriteGround"')[0]):
            numbers = [float(v) for v in values.split(',')]
            overlays.append(list(zip(numbers[::2],numbers[1::2])))
        source = (ROOT/'scenes/world/planet_exterior.gd').read_text()
        protected = [(float(x),float(y)) for x,y in re.findall(r'Vector2\((-?\d+), (-?\d+)\)', source.split('var _player:')[0])]
        self.assertEqual(len(overlays), 4)
        self.assertEqual(len(protected), 6)
        for y in range(-22,22):
            for x in range(-22,22):
                point = ((x+.5)*64,(y+.5)*64)
                if inside(point,protected) or any(inside(point,p) or edge_distance(point,p)<256 for p in overlays):
                    self.assertEqual(material(x,y,26026,protected,overlays), 0)
        self.assertEqual(material(100,100,26026,anchors=[(6432,6432)]),0)
        generator = (ROOT/'scenes/world/planet_generator.gd').read_bytes().replace(b'\r\n',b'\n')
        original = weathered_bytes('scenes/world/planet_generator.gd',generator)
        self.assertEqual(original_green_bytes('scenes/world/planet_generator.gd', generator).split(b'\n\n# Presentation only:')[0], original)
        path = 'scenes/world/terrain_chunk.gd'
        chunk = historical_presenter_bytes(path, (ROOT/path).read_bytes()).decode().replace('\r\n', '\n')
        before = weathered_bytes(path, (ROOT/path).read_bytes()).decode()
        # All legacy tint/halo/detail code stays exact, beyond the reviewed
        # texture table, cached byte array, configure assignment and texture lookup.
        restored = re.sub(r'const GROUND_TEXTURES:.*?\]\n', '', chunk, flags=re.S)
        restored = re.sub(r'^.*_ground_materials.*\n', '', restored, flags=re.M)
        restored = restored.replace('GROUND_TEXTURES[ground_material]', 'BASE_SOIL')
        self.assertEqual(restored, before)
        for path in ('scenes/world/planet_exterior.gd','scenes/world/planet_exterior.tscn',
                     'scenes/world/planet_world_state.gd','scenes/world/world_coordinates.gd',
                     'scenes/world/introductory_ferrite.tres','construction/construction_controller.gd'):
            baseline = subprocess.check_output(['git','show',f'{GREEN_BASE}:{path}'],cwd=ROOT)
            self.assertEqual(historical_presenter_bytes(path, (ROOT/path).read_bytes()).replace(b'\r\n',b'\n'),baseline.replace(b'\r\n',b'\n'))

    def test_exact_source_adapter_rejects_tampering(self):
        for path in GREEN_SHA256:
            raw = (ROOT/path).read_bytes()
            weathered_bytes(path,raw)
            for changed in (raw+b'\n# unrelated',raw+raw,raw.replace(b'func ',b'func changed_',1)):
                with self.assertRaises(AssertionError):
                    weathered_bytes(path,changed)


if __name__ == '__main__':
    unittest.main()
