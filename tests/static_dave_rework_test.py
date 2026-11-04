"""Offline Dave atlas, animation and nonvisual preservation contracts; no Godot."""
import hashlib
import json
import re
import unittest

from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_exterior_hatch_visual_test import png


ART = 'assets/characters/dave/dave_idle_walk_4dir'
ROWS = ['idle_south', 'walk_south', 'idle_west', 'walk_west',
        'idle_east', 'walk_east', 'idle_north', 'walk_north']


class DaveReworkStaticTest(unittest.TestCase):
    def test_supplied_metadata_and_all_frame_rectangles(self):
        raw = (ROOT / (ART + '.json')).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         '216603c6a8163643ecfcbf69ff9e4fdeb1f999dab00740a63d1b4d7b6cea1cec')
        data = json.loads(raw)
        self.assertEqual(data['meta']['image'], 'dave_idle_walk_4dir.png')
        self.assertEqual(data['meta']['format'], 'RGBA8888')
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 1448})
        self.assertEqual(list(data['frames']),
                         [f'{name}_{c:02}' for name in ROWS for c in range(6)])
        for r, name in enumerate(ROWS):
            self.assertEqual(data['meta']['frameTags'][r],
                             {'name': name, 'from': 6*r, 'to': 6*r+5, 'direction': 'forward'})
            for c in range(6):
                frame = data['frames'][f'{name}_{c:02}']
                self.assertEqual(frame['frame'], {'x': c*181, 'y': r*181, 'w': 181, 'h': 181})
                self.assertEqual(frame['spriteSourceSize'], {'x': 0, 'y': 0, 'w': 181, 'h': 181})
                self.assertEqual(frame['sourceSize'], {'w': 181, 'h': 181})
                self.assertFalse(frame['rotated'])
                self.assertFalse(frame['trimmed'])
                self.assertEqual(frame['duration'], 200 if name.startswith('idle') else 100)
        self.assertEqual(len(data['meta']['frameTags']), 8)

    def test_cleaned_png_integrity_visible_margins_and_import(self):
        raw = (ROOT / (ART + '.png')).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(),
                         'd008e4b4467fec2d83da65dd116d50ac275b0337827e63ee636197350d1bbf0d')
        w, h, pixels = png(raw)  # CRCs, RGBA8888 and every scanline.
        self.assertEqual((w, h), (1086, 1448))
        self.assertEqual((min(pixels[3::4]), max(pixels[3::4])), (0, 255))
        heights = []
        for r in range(8):
            for c in range(6):
                visible = [(x, y) for y in range(181) for x in range(181)
                           if pixels[((r*181+y)*w+c*181+x)*4+3] >= 128]
                self.assertTrue(visible)
                self.assertTrue(all(0 < x < 180 and 0 < y < 180 for x, y in visible))
                heights.append(max(y for x, y in visible)-min(y for x, y in visible)+1)
        self.assertEqual((min(heights), max(heights)), (163, 172))
        # Faint source edge residue is retained; do not claim zero-alpha gutters.
        self.assertLessEqual(max(pixels[(y*w+x)*4+3] for y in range(h) for x in range(w)
                                 if x % 181 in (0, 180) or y % 181 in (0, 180)), 26)
        settings = read(ART + '.png.import')
        for value in ['compress/mode=0', 'mipmaps/generate=false', 'process/size_limit=0',
                      f'source_file="res://{ART}.png"']:
            self.assertIn(value, settings)

    def test_animation_grid_order_timing_and_shared_anchor(self):
        scene = read('scenes/player/dave.tscn')
        animations = {re.search(r'id="([^"]+)"', header)[1]: body
                      for header, body in blocks(scene, 'sub_resource')
                      if header.startswith('type="Animation"')}
        self.assertEqual(set(animations), {'Animation_' + name for name in ROWS + ['RESET']})
        for r, name in enumerate(ROWS):
            clip = animations['Animation_' + name]
            dt = .2 if name.startswith('idle') else .1
            self.assertIn(f'length = {round(6*dt, 1)}\n', clip)
            self.assertIn('loop_mode = 1', clip)
            self.assertEqual(re.findall(r'NodePath\("([^"]+)"\)', clip), ['Sprite2D:frame'])
            self.assertIn('"update": 1', clip)
            self.assertEqual(json.loads(re.search(r'"values": (\[[^\]]+\])', clip)[1]),
                             list(range(6*r, 6*r+6)))
            times = re.search(r'"times": PackedFloat32Array\(([^)]+)\)', clip)[1]
            self.assertEqual([float(t) for t in times.split(',')],
                             [round(i*dt, 1) for i in range(6)])
        self.assertIn('"values": [0]', animations['Animation_RESET'])
        sprite = nodes(scene)['Visual/Sprite2D'][1]
        for value in ['hframes = 6', 'vframes = 8', 'centered = false', 'texture_filter = 1',
                      'offset = Vector2(-94, -174)', 'scale = Vector2(0.529069767, 0.529069767)',
                      'texture = ExtResource("6_atlas")']:
            self.assertIn(value, sprite)
        self.assertIn(f'path="res://{ART}.png" id="6_atlas"', scene)
        for path in re.findall(r'path="res://([^"]+)"', scene):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_controller_and_all_other_nodes_preserved(self):
        # Normalize Git's platform line endings for this source preservation pin.
        self.assertEqual(hashlib.sha256(read('scenes/player/dave.gd').encode()).hexdigest(),
                         '77ff1b20a69e1eab4b74cc350c01dcbbff0285caa6a46d93e21f3737c7e54f1f')
        scene = read('scenes/player/dave.tscn')
        tail = scene[scene.index('[node name="Dave"'):]
        tail = re.sub(r'\[node name="Sprite2D"[^\n]*\]\n.*?(?=\[node)', '', tail, flags=re.S)
        self.assertEqual(hashlib.sha256(tail.encode()).hexdigest(),
                         '5eefd0600144a73d9dc60e3c1158bc7af9c9789cd20407040a7ec052047d012c')
        for shape, radius in [('feet', 10), ('interaction', 120)]:
            self.assertIn(f'[sub_resource type="CircleShape2D" id="CircleShape2D_{shape}"]\n'
                          f'radius = {radius}.0', scene)


if __name__ == '__main__':
    unittest.main()
