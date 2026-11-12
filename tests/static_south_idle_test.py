"""South-idle PNG and live scene contracts; no Godot or gameplay execution."""
import hashlib
import json
import re
import unittest

from current_preservation import git_blob
from south_idle_preservation import BASE, verified_south_idle_paths, without_south_idle
from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_exterior_hatch_visual_test import png


ART = 'assets/characters/dave/dave_idle_south_v1'
SHEET_SHA256 = 'ab994380e1775aea1d4cb8fc1256f5f039f15663c4c270422a8a8399f1f777e4'


class SouthIdleStaticTest(unittest.TestCase):
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
        master = [source[y*sw*4:(y*sw+181)*4] for y in range(181)]
        for frame, pose in enumerate([0, 0, 1, 2, 2, 1]):
            for y in range(181):
                with self.subTest(frame=frame, row=y):
                    source_y = y
                    if y < 88 and pose == 1:
                        source_y += 1
                    elif pose == 2:
                        source_y += 2 if y < 83 else (1 if y < 88 else 0)
                    actual = pixels[(y*width+frame*181)*4:(y*width+(frame+1)*181)*4]
                    self.assertEqual(actual, master[source_y])
                    if y >= 88:
                        self.assertEqual(actual, master[y])

    def test_metadata_and_lossless_import(self):
        data = json.loads(read(ART + '.json'))
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 181})
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'idle_south', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'idle_south_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'], {'x': i*181, 'y': 0, 'w': 181, 'h': 181})
            self.assertEqual(frame['duration'], 500)
            self.assertFalse(frame['trimmed'])
            self.assertFalse(frame['rotated'])
        self.assertEqual(data['proof']['sheet_sha256'], SHEET_SHA256)
        self.assertEqual(data['proof']['source_frame'], 0)
        self.assertEqual(data['proof']['source_anchor'], [94, 174])
        self.assertEqual(data['proof']['fixed_region'], {'x': 0, 'y': 88, 'w': 181, 'h': 93})
        settings = read(ART + '.png.import')
        for expected in ['compress/mode=0', 'mipmaps/generate=false',
                         'process/size_limit=0', f'source_file="res://{ART}.png"']:
            self.assertIn(expected, settings)
        cache_hash = hashlib.md5(f'res://{ART}.png'.encode()).hexdigest()
        self.assertEqual(settings.count(f'dave_idle_south_v1.png-{cache_hash}.ctex'), 2)

    def test_south_timing_and_frame_addressing(self):
        clip = self.clips['idle_south']
        self.assertIn('length = 3.0\n', clip)
        self.assertIn('loop_mode = 1\n', clip)
        self.assertIn('step = 0.5\n', clip)
        frame_track = clip.split('tracks/1/type')[0]
        self.assertIn('NodePath("SouthIdleSprite2D:frame")', frame_track)
        self.assertIn('"values": [0, 1, 2, 3, 4, 5]', frame_track)
        self.assertIn('"times": PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)', frame_track)
        self.assertIn('"update": 1', frame_track)

    def test_all_animation_transitions_select_exactly_one_sprite(self):
        expected = {'RESET', 'idle_north', 'idle_south', 'idle_east', 'idle_west',
                    'walk_north', 'walk_south', 'walk_east', 'walk_west'}
        self.assertEqual(set(self.clips), expected)
        for name, clip in self.clips.items():
            with self.subTest(animation=name):
                tracks = dict(re.findall(r'tracks/(\d+)/type = "value"\n(.*?)(?=tracks/\d+/type|\Z)',
                                         clip, re.S))
                self.assertEqual(set(tracks), {'0', '1', '2', '3', '4'})
                visibility = []
                for index, sprite in [('2', 'Sprite2D'), ('3', 'NorthIdleSprite2D'),
                                      ('4', 'SouthIdleSprite2D')]:
                    track = tracks[index]
                    self.assertIn(f'NodePath("{sprite}:visible")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    visibility.append(json.loads(re.search(r'"values": (\[[^\]]+\])', track)[1])[0])
                self.assertEqual(visibility, [name not in ('idle_north', 'idle_south'),
                                              name == 'idle_north', name == 'idle_south'])
        controller = read('scenes/player/dave.gd')
        self.assertIn('animation_player.play(animation_name)', controller)
        self.assertIn('animation_player.advance(0.0)', controller)

    def test_sprite_scale_anchor_and_default_visibility(self):
        scene_nodes = nodes(self.scene)
        sprite = scene_nodes['Visual/SouthIdleSprite2D'][1]
        for value in ['visible = false', 'texture_filter = 1', 'hframes = 6',
                      'texture = ExtResource("8_south_idle")', 'centered = false',
                      'offset = Vector2(-94, -174)',
                      'scale = Vector2(0.71424418545, 0.71424418545)']:
            self.assertIn(value, sprite)
        self.assertNotRegex(sprite, r'(?m)^(vframes|position|rotation|skew|flip_h) =')
        self.assertIn(f'path="res://{ART}.png" id="8_south_idle"', self.scene)
        for path in re.findall(r'path="res://([^"]+)"', self.scene):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_only_approved_scene_delta_and_existing_art_preserved(self):
        old_scene = git_blob(BASE, 'scenes/player/dave.tscn').replace(b'\r\n', b'\n')
        self.assertEqual(without_south_idle('scenes/player/dave.tscn', self.scene.encode()), old_scene)
        self.assertEqual(verified_south_idle_paths(),
                         {ART + '.png', ART + '.json', ART + '.png.import', 'scenes/player/dave.tscn'})
        for path in ['scenes/player/dave.gd', 'scenes/player/follow_camera.gd',
                     'assets/characters/dave/dave_idle_walk_4dir.png',
                     'assets/characters/dave/dave_idle_walk_4dir.json',
                     'assets/characters/dave/dave_idle_walk_4dir.png.import',
                     'assets/characters/dave/dave_idle_north_v1.png',
                     'assets/characters/dave/dave_idle_north_v1.json',
                     'assets/characters/dave/dave_idle_north_v1.png.import']:
            actual = (ROOT / path).read_bytes()
            original = git_blob(BASE, path)
            if not path.endswith('.png'):
                actual, original = actual.replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n')
            self.assertEqual(actual, original, path)


if __name__ == '__main__':
    unittest.main()
