"""East/west idle PNG and live scene contracts; no Godot or gameplay execution."""
import hashlib
import json
import re
import unittest

from current_preservation import git_blob
from east_idle_preservation import BASE, verified_east_idle_paths, without_east_idle
from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_exterior_hatch_visual_test import png


ART = 'assets/characters/dave/dave_idle_east_v1'
SHEET_SHA256 = '4598bf309fa81774e8c5ff77d811566258f4d8f36e9a1ff70be32bced850d2f1'


def tracks(clip):
    return dict(re.findall(r'tracks/(\d+)/type = "value"\n(.*?)(?=tracks/\d+/type|\Z)', clip, re.S))


class EastIdleStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = read('scenes/player/dave.tscn')
        cls.clips = {re.search(r'id="Animation_([^"]+)"', h)[1]: b
                     for h, b in blocks(cls.scene, 'sub_resource')
                     if h.startswith('type="Animation"')}

    def test_approved_sheet_pixels_and_grounding(self):
        raw = (ROOT / (ART + '.png')).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SHEET_SHA256)
        width, height, pixels = png(raw)
        self.assertEqual((width, height), (1086, 181))
        sw, sh, source = png((ROOT / 'assets/characters/dave/dave_idle_walk_4dir.png').read_bytes())
        self.assertEqual((sw, sh), (1086, 1448))
        master = [source[((724+y)*sw)*4:((724+y)*sw+181)*4] for y in range(181)]
        for frame, pose in enumerate([0, 0, 1, 2, 2, 1]):
            for y in range(181):
                with self.subTest(frame=frame, row=y):
                    source_y = y
                    if y < 96 and pose == 1:
                        source_y += 1
                    elif pose == 2:
                        source_y += 2 if y < 91 else (1 if y < 96 else 0)
                    actual = pixels[(y*width+frame*181)*4:(y*width+(frame+1)*181)*4]
                    self.assertEqual(actual, master[source_y])
                    if y >= 96:
                        self.assertEqual(actual, master[y])

    def test_metadata_and_lossless_import(self):
        data = json.loads(read(ART + '.json'))
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 181})
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'idle_east', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'idle_east_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'], {'x': i*181, 'y': 0, 'w': 181, 'h': 181})
            self.assertEqual(frame['duration'], 500)
            self.assertFalse(frame['trimmed'])
            self.assertFalse(frame['rotated'])
        self.assertEqual(data['proof']['sheet_sha256'], SHEET_SHA256)
        self.assertEqual(data['proof']['source_frame'], 24)
        self.assertEqual(data['proof']['source_anchor'], [94, 174])
        self.assertEqual(data['proof']['fixed_region'], {'x': 0, 'y': 96, 'w': 181, 'h': 85})
        settings = read(ART + '.png.import')
        for expected in ['compress/mode=0', 'mipmaps/generate=false',
                         'process/size_limit=0', f'source_file="res://{ART}.png"']:
            self.assertIn(expected, settings)
        cache_hash = hashlib.md5(f'res://{ART}.png'.encode()).hexdigest()
        self.assertEqual(settings.count(f'dave_idle_east_v1.png-{cache_hash}.ctex'), 2)

    def test_east_and_west_share_frames_and_timing(self):
        for name in ('idle_east', 'idle_west'):
            clip = self.clips[name]
            self.assertIn('length = 3.0\n', clip)
            self.assertIn('loop_mode = 1\n', clip)
            self.assertIn('step = 0.5\n', clip)
            frame_track = tracks(clip)['0']
            self.assertIn('NodePath("EastIdleSprite2D:frame")', frame_track)
            self.assertIn('"values": [0, 1, 2, 3, 4, 5]', frame_track)
            self.assertIn('"times": PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)', frame_track)
            self.assertIn('"update": 1', frame_track)
        self.assertEqual(tracks(self.clips['idle_east'])['0'], tracks(self.clips['idle_west'])['0'])

    def test_all_clips_explicitly_select_one_visible_sprite(self):
        expected = {'RESET', 'idle_north', 'idle_south', 'idle_east', 'idle_west',
                    'walk_north', 'walk_south', 'walk_east', 'walk_west'}
        self.assertEqual(set(self.clips), expected)
        for name, clip in self.clips.items():
            with self.subTest(animation=name):
                actual = tracks(clip)
                self.assertEqual(set(actual), {str(i) for i in range(7)})
                visibility = []
                for index, sprite in [('2', 'Sprite2D'), ('3', 'NorthIdleSprite2D'),
                                      ('4', 'SouthIdleSprite2D'), ('5', 'EastIdleSprite2D')]:
                    track = actual[index]
                    self.assertIn(f'NodePath("{sprite}:visible")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    visibility.append(json.loads(re.search(r'"values": (\[[^\]]+\])', track)[1])[0])
                self.assertEqual(visibility, [name == 'RESET' or name.startswith('walk_'),
                                              name == 'idle_north', name == 'idle_south',
                                              name in ('idle_east', 'idle_west')])
                self.assertEqual(sum(visibility), 1)

    def test_west_idle_flip_and_all_other_flip_resets(self):
        for name, clip in self.clips.items():
            with self.subTest(animation=name):
                actual = tracks(clip)
                for index, sprite, mirrored in [('1', 'Sprite2D', name == 'walk_west'),
                                                 ('6', 'EastIdleSprite2D', name == 'idle_west')]:
                    track = actual[index]
                    self.assertIn(f'NodePath("{sprite}:flip_h")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    self.assertIn(f'"values": [{str(mirrored).lower()}]', track)
        # Explicit flags on every target clip remove dependency on the previous
        # direction, including west walk -> idle -> east/north/south and RESET.
        controller = read('scenes/player/dave.gd')
        self.assertIn('animation_player.play(animation_name)', controller)
        self.assertIn('animation_player.advance(0.0)', controller)

    def test_shared_sprite_scale_anchor_and_scene_references(self):
        sprite = nodes(self.scene)['Visual/EastIdleSprite2D'][1]
        for value in ['visible = false', 'texture_filter = 1', 'hframes = 6',
                      'texture = ExtResource("9_east_idle")', 'centered = false',
                      'offset = Vector2(-94, -174)',
                      'scale = Vector2(0.71424418545, 0.71424418545)']:
            self.assertIn(value, sprite)
        self.assertNotRegex(sprite, r'(?m)^(vframes|position|rotation|skew|flip_h) =')
        self.assertIn(f'path="res://{ART}.png" id="9_east_idle"', self.scene)
        for path in re.findall(r'path="res://([^"]+)"', self.scene):
            self.assertTrue((ROOT / path).is_file(), path)
        external = re.findall(r'^\[ext_resource .* id="([^"]+)"\]$', self.scene, re.M)
        internal = re.findall(r'^\[sub_resource .* id="([^"]+)"\]$', self.scene, re.M)
        self.assertEqual(len(external), len(set(external)))
        self.assertEqual(len(internal), len(set(internal)))
        self.assertEqual(int(re.search(r'load_steps=(\d+)', self.scene)[1]), len(external)+len(internal)+1)
        self.assertLessEqual(set(re.findall(r'ExtResource\("([^"]+)"\)', self.scene)), set(external))
        self.assertLessEqual(set(re.findall(r'SubResource\("([^"]+)"\)', self.scene)), set(internal))

    def test_only_approved_scene_delta_and_existing_art_preserved(self):
        old_scene = git_blob(BASE, 'scenes/player/dave.tscn').replace(b'\r\n', b'\n')
        self.assertEqual(without_east_idle('scenes/player/dave.tscn', self.scene.encode()), old_scene)
        self.assertEqual(verified_east_idle_paths(),
                         {ART + '.png', ART + '.json', ART + '.png.import', 'scenes/player/dave.tscn'})
        paths = ['scenes/player/dave.gd', 'scenes/player/follow_camera.gd']
        for name in ('dave_idle_walk_4dir', 'dave_idle_north_v1', 'dave_idle_south_v1'):
            paths.extend(f'assets/characters/dave/{name}{suffix}' for suffix in ('.png', '.json', '.png.import'))
        for path in paths:
            actual = (ROOT / path).read_bytes()
            original = git_blob(BASE, path)
            if not path.endswith('.png'):
                actual, original = actual.replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n')
            self.assertEqual(actual, original, path)


if __name__ == '__main__':
    unittest.main()
