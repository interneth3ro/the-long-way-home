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
                         '6ca7d1eb6d341847216c4eccf9c6b39958b451823cda21b3150cfeeeaf0c2766')
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
        self.assertEqual((min(heights), max(heights)), (155, 172))
        # Faint source edge residue is retained; do not claim zero-alpha gutters.
        self.assertLessEqual(max(pixels[(y*w+x)*4+3] for y in range(h) for x in range(w)
                                 if x % 181 in (0, 180) or y % 181 in (0, 180)), 26)
        settings = read(ART + '.png.import')
        self.assertEqual(hashlib.sha256(settings.encode()).hexdigest(),
                         'a3e623b632c0a9a09821c2907b6f2d1830a9c29ec3e8d0fe5a018e75a29a4357')
        for value in ['compress/mode=0', 'mipmaps/generate=false', 'process/size_limit=0',
                      f'source_file="res://{ART}.png"']:
            self.assertIn(value, settings)

    def test_north_v2_sources_and_accepted_cells_preserved(self):
        source = ROOT / 'assets/characters/dave/source_art/north_walk_v2'
        self.assertTrue((source / '.gdignore').is_file())
        for name, digest in [
            ('dave_walk_north_v2_refined.png',
             'f65cc6062cba1531b356a4dbc7a5103227f236eb308cb992d0319e2394207e34'),
            ('dave_walk_north_v2.json',
             '11363224ca798ebdf436ebf88e61fdf2a993ca89fa98d5e4537da23d93e82bb0'),
        ]:
            self.assertEqual(hashlib.sha256((source / name).read_bytes()).hexdigest(), digest)
        data = json.loads((source / 'dave_walk_north_v2.json').read_bytes())
        self.assertEqual(data['meta']['image'], 'dave_walk_north_v2_refined.png')
        self.assertEqual(png((source / data['meta']['image']).read_bytes())[:2], (1536, 1024))
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'walk_north', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'walk_north_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'],
                             {'x': i % 3 * 512, 'y': i // 3 * 512, 'w': 512, 'h': 512})
            self.assertEqual(frame['duration'], 100)
            self.assertFalse(frame['rotated'])
            self.assertFalse(frame['trimmed'])
        w, h, pixels = png((ROOT / (ART + '.png')).read_bytes())
        # East row preservation is covered separately; accepted north cells stay exact.
        expected = [
            '3d64652e5b70d73657ccd113055331d25e75d8088954395f8ace145087cbaf81',
            'b96e6b6a910b311e8a7f74c525b0d106b30716bada2d9ccaaa67249475be09e4',
            '9749cb8e165fcc6925369a66efb15396e0cd795107f5b20fef824b660f70c561',
            '3636552493ed1ba0c61ddf276c7e4928031e42a9f612780629972ccea0f52d88',
            'bd40c44bb4f5a3874e0030fb858d1220c587c5c43ca5347f62976f5953515a26',
            'd1cd4771fcf5e773318ccade2fed1c31fe3bdb816a1748dc6575fad635fb5f41',
        ]
        for i, digest in enumerate(expected):
            cell = b''.join(pixels[(y*w+i*181)*4:(y*w+(i+1)*181)*4]
                            for y in range(1267, h))
            self.assertEqual(hashlib.sha256(cell).hexdigest(), digest)

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
            self.assertEqual(re.findall(r'NodePath\("([^"]+)"\)', clip),
                             ['Sprite2D:frame', 'Sprite2D:flip_h'])
            self.assertIn('"update": 1', clip)
            self.assertEqual(json.loads(re.search(r'"values": (\[[^\]]+\])', clip)[1]),
                             list(range(30, 36)) if name == 'walk_west'
                             else list(range(6*r, 6*r+6)))
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

    def test_east_v2_source_identity_grid_and_timing(self):
        source = ROOT / 'assets/characters/dave/source_art/east_walk_v2'
        self.assertTrue((source / '.gdignore').is_file())
        for name, digest in [
            ('dave_walk_east_v2.png',
             '2d59b08aacda305e468e0673f224b9dc1219f9b8a538d0f8928755e38b8b9c9a'),
            ('dave_walk_east_v2.json',
             'b89d3c75a08aacf7c61ac73b7cbfc6994b99539b61f9242f10d25c05cfcd621c'),
        ]:
            self.assertEqual(hashlib.sha256((source / name).read_bytes()).hexdigest(), digest)
        data = json.loads((source / 'dave_walk_east_v2.json').read_bytes())
        self.assertEqual(data['meta']['image'], 'dave_walk_east_v2.png')
        self.assertEqual(data['meta']['format'], 'RGBA8888')
        self.assertEqual(data['meta']['size'], {'w': 1536, 'h': 1024})
        self.assertEqual(png((source / data['meta']['image']).read_bytes())[:2], (1536, 1024))
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'walk_east', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'walk_east_{i:02}' for i in range(6)])
        self.assertIn('horizontal sprite flip', data['draft']['west_usage'])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'],
                             {'x': i % 3 * 512, 'y': i // 3 * 512, 'w': 512, 'h': 512})
            self.assertEqual(frame['sourceSize'], {'w': 512, 'h': 512})
            self.assertEqual(frame['spriteSourceSize'], {'x': 0, 'y': 0, 'w': 512, 'h': 512})
            self.assertEqual(frame['duration'], 100)
            self.assertFalse(frame['rotated'])
            self.assertFalse(frame['trimmed'])

    def test_east_v2_replacements_and_all_42_untouched_cells(self):
        w, h, pixels = png((ROOT / (ART + '.png')).read_bytes())
        # Every RGBA byte outside cells 30-35 equals the merged PR #150 baseline.
        untouched = pixels[:w*905*4] + pixels[w*1086*4:]
        self.assertEqual(hashlib.sha256(untouched).hexdigest(),
                         'c19045abab51692e598219c0d7fce1c24b5bfe0df31e4770e54635124cd25c52')
        expected = [
            'c18162ea76730c7506f1273e7ec17fc4c6d852071fedfb82a49d04249efd4337',
            'eb55d1424df25fa23f80fe8b9ceac1171e312caeaa99ed068aac504c6369b66e',
            'f2a18acc3421e6701600187e98e98e5e941efe4cf291328ad8e44f2e9f165ded',
            'f70e5143ad73d4e4431ad07bba3d813fad6a9cd2a4baaac24a67c6c16a7ec0ad',
            'e41a9ddf8a49c6907bd26e90c3aa4691f5ff2959edc8476a144b73fc9478b03c',
            'a129de1ab30219486d4a46ee7c56b7476979e5672943e93160665f837d13001d',
        ]
        for i, digest in enumerate(expected):
            cell = b''.join(pixels[(y*w+i*181)*4:(y*w+(i+1)*181)*4]
                            for y in range(905, 1086))
            self.assertEqual(hashlib.sha256(cell).hexdigest(), digest)
            self.assertEqual(min(cell[3::4]), 0)
            visible = [(x, y) for y in range(181) for x in range(181)
                       if cell[(y*181+x)*4+3] >= 128]
            self.assertTrue(all(0 < x < 180 and 0 < y < 180 for x, y in visible))
            self.assertIn(max(y for x, y in visible), (172, 173))
            # Mirror preserves vertical grounding and clear horizontal margins.
            self.assertTrue(all(0 < 180-x < 180 for x, y in visible))
            self.assertLessEqual(max(cell[(y*181+x)*4+3] for y in range(181)
                                     for x in range(181)
                                     if x in (0, 180) or y in (0, 180)), 4)

    def test_explicit_flip_states_and_only_intended_scene_edits(self):
        scene = read('scenes/player/dave.tscn')
        animations = [(header, body) for header, body in blocks(scene, 'sub_resource')
                      if header.startswith('type="Animation"')]
        for header, body in animations:
            flip = body.split('tracks/1/type = "value"\n')[1]
            self.assertEqual(re.findall(r'NodePath\("([^"]+)"\)', flip), ['Sprite2D:flip_h'])
            self.assertIn('"times": PackedFloat32Array(0.0)', flip)
            self.assertIn('"update": 1', flip)
            self.assertIn('"values": [true]' if 'id="Animation_walk_west"' in header
                          else '"values": [false]', flip)
            self.assertNotIn('tracks/2/', body)
        # Undo only the nine flip tracks and the west frame remap; everything
        # else, including complete node properties and north timing, stays exact.
        restored = re.sub(r'tracks/1/type = "value"\n.*?\n}\n', '', scene, flags=re.S)
        west_start = restored.index('[sub_resource type="Animation" id="Animation_walk_west"]')
        west_end = restored.index('[sub_resource', west_start + 1)
        west = restored[west_start:west_end].replace(
            '"values": [30, 31, 32, 33, 34, 35]', '"values": [18, 19, 20, 21, 22, 23]')
        restored = restored[:west_start] + west + restored[west_end:]
        self.assertEqual(hashlib.sha256(restored.encode()).hexdigest(),
                         '8959a23140d2086f900129987b74d7dc3806b6b118eca7cdd9ebb7b283eaf2af')

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
