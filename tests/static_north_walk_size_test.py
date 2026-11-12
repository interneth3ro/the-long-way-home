"""North-walk size artwork and live scene contracts; no Godot execution."""
import hashlib
import json
import re
import unittest

from current_preservation import git_blob
from north_walk_size_preservation import BASE, verified_north_walk_size_paths, without_north_walk_size
from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_exterior_hatch_visual_test import png
from static_east_idle_test import tracks


ART = 'assets/characters/dave/dave_walk_north_size_v1'
SHEET_SHA256 = '07f995bd09eda3c31e9784270bee35d0b93862fab492c7e59f19ba7f277e47b4'
BOUNDS = [[43, 9, 145, 175], [43, 9, 147, 165], [43, 9, 145, 166],
          [42, 10, 147, 175], [43, 10, 147, 166], [43, 10, 146, 167]]


class NorthWalkSizeStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = read('scenes/player/dave.tscn')
        cls.clips = {re.search(r'id="Animation_([^"]+)"', h)[1]: b
                     for h, b in blocks(cls.scene, 'sub_resource')
                     if h.startswith('type="Animation"')}

    def test_approved_sheet_pixels_size_and_bounds(self):
        raw = (ROOT / (ART + '.png')).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SHEET_SHA256)
        width, height, pixels = png(raw)
        self.assertEqual((width, height), (1086, 181))
        for frame, expected in enumerate(BOUNDS):
            points = [(x, y) for y in range(181) for x in range(181)
                      if pixels[(y*width+frame*181+x)*4+3] >= 128]
            xs, ys = zip(*points)
            bounds = [min(xs), min(ys), max(xs)+1, max(ys)+1]
            self.assertEqual(bounds, expected)
            self.assertLessEqual(abs(bounds[2]-bounds[0]-103), 2)
            self.assertGreater(bounds[0], 0)
            self.assertGreater(bounds[1], 0)
            self.assertLess(bounds[2], 181)
            self.assertLess(bounds[3], 181)

    def test_source_provenance_and_unchanged_vertical_transform(self):
        proof = json.loads(read(ART + '.json'))['proof']
        self.assertEqual(proof['source_sha256'],
                         'f65cc6062cba1531b356a4dbc7a5103227f236eb308cb992d0319e2394207e34')
        self.assertEqual(hashlib.sha256((ROOT / proof['source']).read_bytes()).hexdigest(),
                         proof['source_sha256'])
        self.assertEqual(proof['source_grid'], [3, 2])
        self.assertEqual(proof['source_cell'], [512, 512])
        self.assertEqual(proof['source_anchor'], [256, 430])
        self.assertEqual(proof['resize'], [240, 210])
        self.assertEqual(proof['crop_exclusive'], [26, 2, 207, 183])
        self.assertEqual(proof['baseline_resize'], [210, 210])
        self.assertEqual(proof['baseline_crop_exclusive'], [11, 2, 192, 183])
        for prefix in ('', 'baseline_'):
            resize, crop = proof[prefix+'resize'], proof[prefix+'crop_exclusive']
            anchor = [proof['source_anchor'][i]*resize[i]/512-crop[i] for i in (0, 1)]
            self.assertEqual(anchor, [94, 174.3671875])
            self.assertEqual(anchor, proof['output_anchor'])
        self.assertEqual(proof['horizontal_factor_relative_to_current'], 240/210)
        self.assertEqual(proof['vertical_factor_relative_to_current'], 1)
        self.assertEqual(proof['frame_order'], list(range(6)))
        self.assertEqual(proof['loop_ms'], 600)
        self.assertEqual(proof['candidate_bounds_alpha_128'], BOUNDS)

    def test_metadata_and_lossless_import(self):
        data = json.loads(read(ART + '.json'))
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 181})
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'walk_north', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'walk_north_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'], {'x': i*181, 'y': 0, 'w': 181, 'h': 181})
            self.assertEqual(frame['duration'], 100)
            self.assertFalse(frame['trimmed'])
            self.assertFalse(frame['rotated'])
        self.assertEqual(data['proof']['sheet_sha256'], SHEET_SHA256)
        settings = read(ART + '.png.import')
        for expected in ['compress/mode=0', 'mipmaps/generate=false',
                         'process/size_limit=0', f'source_file="res://{ART}.png"']:
            self.assertIn(expected, settings)
        cache_hash = hashlib.md5(f'res://{ART}.png'.encode()).hexdigest()
        self.assertEqual(settings.count(f'dave_walk_north_size_v1.png-{cache_hash}.ctex'), 2)

    def test_north_walk_keeps_frame_order_and_timing(self):
        clip = self.clips['walk_north']
        for value in ['length = 0.6\n', 'loop_mode = 1\n', 'step = 0.1\n']:
            self.assertIn(value, clip)
        frame = tracks(clip)['0']
        self.assertIn('NodePath("NorthWalkSprite2D:frame")', frame)
        self.assertIn('"values": [0, 1, 2, 3, 4, 5]', frame)
        self.assertIn('"times": PackedFloat32Array(0.0, 0.1, 0.2, 0.3, 0.4, 0.5)', frame)
        self.assertIn('"update": 1', frame)
        self.assertEqual(self.scene.count('NodePath("NorthWalkSprite2D:frame")'), 1)

    def test_all_live_clips_select_one_sprite_and_reset_mirroring(self):
        expected = {'RESET', 'idle_north', 'idle_south', 'idle_east', 'idle_west',
                    'walk_north', 'walk_south', 'walk_east', 'walk_west'}
        self.assertEqual(set(self.clips), expected)
        for name, clip in self.clips.items():
            with self.subTest(animation=name):
                actual = tracks(clip)
                self.assertEqual(set(actual), {str(i) for i in range(8)})
                visibility = []
                for index, sprite in [('2', 'Sprite2D'), ('3', 'NorthIdleSprite2D'),
                                      ('4', 'SouthIdleSprite2D'), ('5', 'EastIdleSprite2D'),
                                      ('7', 'NorthWalkSprite2D')]:
                    track = actual[index]
                    self.assertIn(f'NodePath("{sprite}:visible")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    visibility.append(json.loads(re.search(r'"values": (\[[^\]]+\])', track)[1])[0])
                self.assertEqual(visibility, [name in ('RESET', 'walk_south', 'walk_east', 'walk_west'),
                                              name == 'idle_north', name == 'idle_south',
                                              name in ('idle_east', 'idle_west'), name == 'walk_north'])
                self.assertEqual(sum(visibility), 1)
                for index, sprite, mirrored in [('1', 'Sprite2D', name == 'walk_west'),
                                                 ('6', 'EastIdleSprite2D', name == 'idle_west')]:
                    track = actual[index]
                    self.assertIn(f'NodePath("{sprite}:flip_h")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    self.assertIn(f'"values": [{str(mirrored).lower()}]', track)
        self.assertNotIn('NorthWalkSprite2D:flip_h', self.scene)
        controller = read('scenes/player/dave.gd')
        self.assertIn('animation_player.play(animation_name)', controller)
        self.assertIn('animation_player.advance(0.0)', controller)

    def test_shared_scale_anchor_and_scene_references(self):
        scene_nodes = nodes(self.scene)
        sprite = scene_nodes['Visual/NorthWalkSprite2D'][1]
        for value in ['visible = false', 'texture_filter = 1', 'hframes = 6',
                      'texture = ExtResource("10_north_walk")', 'centered = false',
                      'offset = Vector2(-94, -174)',
                      'scale = Vector2(0.71424418545, 0.71424418545)']:
            self.assertIn(value, sprite)
        self.assertNotRegex(sprite, r'(?m)^(vframes|position|rotation|skew|flip_h) =')
        for path in re.findall(r'path="res://([^"]+)"', self.scene):
            self.assertTrue((ROOT / path).is_file(), path)
        external = re.findall(r'^\[ext_resource .* id="([^"]+)"\]$', self.scene, re.M)
        internal = re.findall(r'^\[sub_resource .* id="([^"]+)"\]$', self.scene, re.M)
        self.assertEqual(len(external), len(set(external)))
        self.assertEqual(len(internal), len(set(internal)))
        self.assertEqual(int(re.search(r'load_steps=(\d+)', self.scene)[1]), len(external)+len(internal)+1)
        self.assertLessEqual(set(re.findall(r'ExtResource\("([^"]+)"\)', self.scene)), set(external))
        self.assertLessEqual(set(re.findall(r'SubResource\("([^"]+)"\)', self.scene)), set(internal))
        for target in re.findall(r'NodePath\("([^":]+):[^"]+"\)', self.scene):
            self.assertIn('Visual/' + target, scene_nodes)

    def test_only_approved_scene_delta_and_existing_art_preserved(self):
        scene = 'scenes/player/dave.tscn'
        original = git_blob(BASE, scene).replace(b'\r\n', b'\n')
        self.assertEqual(without_north_walk_size(scene, self.scene.encode()), original)
        self.assertEqual(verified_north_walk_size_paths(),
                         {ART + '.png', ART + '.json', ART + '.png.import', scene})
        paths = ['scenes/player/dave.gd', 'scenes/player/follow_camera.gd']
        for name in ('dave_idle_walk_4dir', 'dave_idle_north_v1', 'dave_idle_south_v1', 'dave_idle_east_v1'):
            paths.extend(f'assets/characters/dave/{name}{suffix}' for suffix in ('.png', '.json', '.png.import'))
        paths.extend('assets/characters/dave/source_art/north_walk_v2/' + name
                     for name in ('dave_walk_north_v2_refined.png', 'dave_walk_north_v2.json'))
        for path in paths:
            actual, original = (ROOT / path).read_bytes(), git_blob(BASE, path)
            if not path.endswith('.png'):
                actual, original = actual.replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n')
            self.assertEqual(actual, original, path)


if __name__ == '__main__':
    unittest.main()
