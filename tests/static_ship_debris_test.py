"""PNG, scene and geometry inspection only; never launches Godot/project code."""
import hashlib
import json
import math
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'assets/environment/exterior/debris_v1'
SCENE = ROOT / 'scenes/world/localized_ship_debris.tscn'
BASE = '029e1d54958d6259940cf44e4b5f56fb53bc0133'


def png(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, packed, kinds = 8, bytearray(), []
    while pos < len(raw):
        size = struct.unpack_from('>I', raw, pos)[0]
        kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+size]
        assert zlib.crc32(kind + data) == struct.unpack_from('>I', raw, pos+8+size)[0]
        if kind == b'IHDR':
            w, h, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', data)
            assert (depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0)
        if kind == b'IDAT':
            packed.extend(data)
        kinds.append(kind)
        pos += size + 12
    assert pos == len(raw) and kinds[0] == b'IHDR' and kinds[-1] == b'IEND'
    scan, stride = zlib.decompress(packed), w * 4
    assert len(scan) == h * (stride + 1)
    previous, rows = bytearray(stride), []
    for y in range(h):
        mode = scan[y*(stride+1)]
        assert mode in range(5)
        row = bytearray(scan[y*(stride+1)+1:(y+1)*(stride+1)])
        for i in range(stride):
            a, b, c = row[i-4] if i >= 4 else 0, previous[i], previous[i-4] if i >= 4 else 0
            p = a + b - c
            distances = (abs(p-a), abs(p-b), abs(p-c))
            predictor = (a, b, c)[distances.index(min(distances))]
            row[i] = (row[i] + (0, a, b, (a+b)//2, predictor)[mode]) % 256
        rows.append(bytes(row))
        previous = row
    return w, h, rows


def numbers(text):
    return tuple(map(float, text.split(',')))


def section(text, prefix):
    return text.split(prefix, 1)[1].split('\n[', 1)[0]


def transform(point, position, angle):
    x, y = point
    c, s = math.cos(angle), math.sin(angle)
    return position[0]+c*x-s*y, position[1]+s*x+c*y


def separated(a, b, margin=0):
    for poly in (a, b):
        for p, q in zip(poly, poly[1:]+poly[:1]):
            dx, dy = q[0]-p[0], q[1]-p[1]
            length = math.hypot(dx, dy)
            axis = -dy/length, dx/length
            aa = [x*axis[0]+y*axis[1] for x, y in a]
            bb = [x*axis[0]+y*axis[1] for x, y in b]
            if max(aa)+margin < min(bb) or max(bb)+margin < min(aa):
                return True
    return False


class ShipDebrisStaticTest(unittest.TestCase):
    def test_package_png_integrity_regions_and_alpha_bounds(self):
        manifest = json.loads((ART/'atlas_manifest.json').read_text(encoding='utf-8'))
        atlas_raw = (ART/'tlwh_debris_atlas_v1.png').read_bytes()
        self.assertEqual(hashlib.sha256(atlas_raw).hexdigest(), manifest['atlas_sha256'])
        self.assertEqual(manifest['atlas_sha256'], '846773a82ee2e128ead678e37e79e7c3ffb4fbe0b1644f68d7eecad0970fcd29')
        w, h, atlas = png(atlas_raw)
        self.assertEqual([w, h], manifest['atlas_size'])
        self.assertEqual([w, h], [1920, 1280])
        self.assertEqual(manifest['cell_size'], [640, 640])
        text = SCENE.read_text(encoding='utf-8')
        for i, region in enumerate(manifest['regions']):
            raw = (ART/(region['name']+'.png')).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), region['sha256'])
            sw, sh, rows = png(raw)
            self.assertEqual((sw, sh), (640, 640))
            x, y, rw, rh = region['rect']
            self.assertEqual((rw, rh), (640, 640))
            self.assertEqual(rows, [row[x*4:(x+rw)*4] for row in atlas[y:y+rh]])
            points = [(x, y) for y, row in enumerate(rows) for x, a in enumerate(row[3::4]) if a]
            left, top = min(p[0] for p in points), min(p[1] for p in points)
            bounds = [left, top, max(p[0] for p in points)+1-left, max(p[1] for p in points)+1-top]
            self.assertEqual(bounds, region['visible_bounds_in_cell'])
            self.assertEqual(min(a for row in rows for a in row[3::4]), 0)
            self.assertGreaterEqual(max(a for row in rows for a in row[3::4]), 128)
            # Sample each fitted footprint against actual source alpha; the tiny
            # fragment cluster deliberately combines gaps between shards.
            shape = section(text, f'[sub_resource type="ConvexPolygonShape2D" id="DebrisFootprint{i}"]')
            values = numbers(re.search(r'PackedVector2Array\(([^)]+)\)', shape)[1])
            poly = list(zip(values[::2], values[1::2]))
            name = re.findall(r'\[node name="([^"]+)" type="StaticBody2D"', text)[i]
            sprite = section(text, f'[node name="Sprite2D" type="Sprite2D" parent="{name}"]')
            self.assertIn(f'texture = SubResource("DebrisRegion{i}")', sprite)
            collision = section(text, f'[node name="CollisionShape2D" type="CollisionShape2D" parent="{name}"]')
            self.assertIn(f'shape = SubResource("DebrisFootprint{i}")', collision)
            scale = numbers(re.search(r'scale = Vector2\(([^)]+)\)', sprite)[1])[0]
            bx, by, bw, bh = bounds
            solid = count = 0
            for py in range(math.floor(min(values[1::2])), math.ceil(max(values[1::2]))):
                for px in range(math.floor(min(values[::2])), math.ceil(max(values[::2]))):
                    crosses = [(b[0]-a[0])*(py-a[1])-(b[1]-a[1])*(px-a[0]) for a, b in zip(poly, poly[1:]+poly[:1])]
                    if not (all(c >= 0 for c in crosses) or all(c <= 0 for c in crosses)):
                        continue
                    sx, sy = int(px/scale+bx+bw/2), int(py/scale+by+bh)
                    count += 1
                    solid += rows[sy][sx*4+3] >= 128
            self.assertGreater(solid/count, 0.5 if i == 5 else 0.7, name)
            resource = section(text, f'[sub_resource type="AtlasTexture" id="DebrisRegion{i}"]')
            self.assertIn('region = Rect2('+', '.join(map(str, region['rect']))+')', resource)

    def test_static_prop_contracts_transforms_and_clearances(self):
        text = SCENE.read_text(encoding='utf-8')
        self.assertEqual(text.count('[ext_resource'), 1)
        self.assertNotRegex(text, r'Script|Area2D|RigidBody2D|interaction|salvage|shader|animation')
        self.assertIn('y_sort_enabled = true', text)
        self.assertEqual(int(re.search(r'load_steps=(\d+)', text)[1]), text.count('[ext_resource')+text.count('[sub_resource')+1)
        manifest = json.loads((ART/'atlas_manifest.json').read_text(encoding='utf-8'))
        bodies = re.findall(r'\[node name="([^"]+)" type="StaticBody2D" parent="\."\]', text)
        self.assertEqual(len(bodies), 6)
        limits = [(70, 100), (65, 90), (60, 90), (65, 95), (40, 65), (35, 55)]
        footprints = []
        for i, (name, region, (lo, hi)) in enumerate(zip(bodies, manifest['regions'], limits)):
            body = section(text, f'[node name="{name}" type="StaticBody2D" parent="."]')
            self.assertIn('collision_layer = 5', body)
            self.assertIn('collision_mask = 0', body)
            position = numbers(re.search(r'position = Vector2\(([^)]+)\)', body)[1])
            angle = float(re.search(r'rotation = ([^\n]+)', body)[1])
            sprite = section(text, f'[node name="Sprite2D" type="Sprite2D" parent="{name}"]')
            sx, sy = numbers(re.search(r'scale = Vector2\(([^)]+)\)', sprite)[1])
            offset = numbers(re.search(r'position = Vector2\(([^)]+)\)', sprite)[1])
            self.assertEqual(sx, sy)
            x, y, w, h = region['visible_bounds_in_cell']
            self.assertTrue(lo <= max(w, h)*sx <= hi)
            self.assertAlmostEqual(offset[0]+(x+w/2)*sx, 0)
            self.assertAlmostEqual(offset[1]+(y+h)*sy, 0)
            shape = section(text, f'[sub_resource type="ConvexPolygonShape2D" id="DebrisFootprint{i}"]')
            values = numbers(re.search(r'PackedVector2Array\(([^)]+)\)', shape)[1])
            poly = list(zip(values[::2], values[1::2]))
            crosses = []
            for a, b, c in zip(poly, poly[1:]+poly[:1], poly[2:]+poly[:2]):
                crosses.append((b[0]-a[0])*(c[1]-b[1])-(b[1]-a[1])*(c[0]-b[0]))
            self.assertTrue(all(v > 0 for v in crosses) or all(v < 0 for v in crosses))
            self.assertTrue(all(-w*sx/2 < px < w*sx/2 and -h*sy < py < 0 for px, py in poly))
            world = [transform(p, position, angle) for p in poly]
            footprints.append(world)
            # Unchanged hatch approach/spawn corridor, Ferrite ground and starter construction space.
            for rect in [(-448, -200, -320, 40), (124, 140, 452, 372), (-256, 0, 128, 384)]:
                l, t, r, b = rect
                self.assertTrue(separated(world, [(l,t), (r,t), (r,b), (l,b)], 32), name)
            print(f'{name}: origin={position}, scale={sx}, angle={math.degrees(angle):.1f}, visible={w*sx:.2f}x{h*sy:.2f}')
        for i, a in enumerate(footprints):
            for b in footprints[i+1:]:
                self.assertTrue(separated(a, b, 20))
        exterior = (ROOT/'scenes/world/planet_exterior.tscn').read_text(encoding='utf-8')
        for shape in ('ShipNoseFootprint', 'ShipFuselageFootprint', 'ShipRearFootprint'):
            resource = section(exterior, f'[sub_resource type="ConvexPolygonShape2D" id="{shape}"]')
            values = numbers(re.search(r'PackedVector2Array\(([^)]+)\)', resource)[1])
            hull = [(x-384, y-192) for x, y in zip(values[::2], values[1::2])]
            for debris in footprints:
                self.assertTrue(separated(hull, debris, 16), shape)
        rules = (ROOT/'construction/placement_rules.gd').read_text(encoding='utf-8')
        self.assertIn('const BLOCKING_LAYER: int = 4', rules)
        self.assertIn('query.collision_mask = BLOCKING_LAYER', rules)
        self.assertIn('space.intersect_shape(query, 1)', rules)

    def test_existing_exterior_and_approved_art_are_preserved(self):
        path = 'scenes/world/planet_exterior.tscn'
        before = subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT).decode()
        current = (ROOT/path).read_text(encoding='utf-8')
        current = current.replace('load_steps=14', 'load_steps=13', 1)
        current = current.replace('[ext_resource type="PackedScene" path="res://scenes/world/localized_ship_debris.tscn" id="7_debris"]\n\n', '', 1)
        current = current.replace('[node name="LocalizedDebris" parent="GroundObjects" instance=ExtResource("7_debris")]\n\n', '', 1)
        self.assertEqual(current, before.replace('\r\n', '\n'))
        for filename, digest in {
            'crashed_exploration_ship_approved.png': '80ae633c36242c1effdcebea38dc05cfef8eb586ca9ef3103f6b02be91564e5b',
            'crashed_ship_contact_shadow_prototype.png': '1cd8111595e11d8beb527f538188f38f8517f1d3365633c013b9a137ca601777',
        }.items():
            self.assertEqual(hashlib.sha256((ART.parent/filename).read_bytes()).hexdigest(), digest)


if __name__ == '__main__':
    unittest.main()
