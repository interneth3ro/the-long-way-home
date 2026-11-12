"""North-idle PNG and scene contracts; no Godot or gameplay execution."""
import hashlib
import json
import re
import unittest

from current_preservation import git_blob
from north_idle_preservation import without_north_idle
from north_walk_size_preservation import without_north_walk_size
from east_idle_preservation import without_east_idle
from south_idle_preservation import without_south_idle
from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_exterior_hatch_visual_test import png


ART = 'assets/characters/dave/dave_idle_north_v1'
BASE = '8edb00937beb8842ae9a50a30394045d033841aa'
SHEET_SHA256 = '74983d4f94314f25065ddf53e421e170fd6909aa09b5c1c03b52a302bcab619a'


class NorthIdleStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Retain the original north contract; north-walk size tests check the live scene.
        cls.scene = without_south_idle('scenes/player/dave.tscn',
                                       without_east_idle('scenes/player/dave.tscn',
                                                         without_north_walk_size('scenes/player/dave.tscn', read('scenes/player/dave.tscn').encode()))).decode()
        cls.clips = {re.search(r'id="Animation_([^"]+)"', h)[1]: b
                     for h, b in blocks(cls.scene, 'sub_resource')
                     if h.startswith('type="Animation"')}

    def test_accepted_sheet_pixels_and_grounding(self):
        raw = (ROOT / (ART + '.png')).read_bytes()
        self.assertEqual(hashlib.sha256(raw).hexdigest(), SHEET_SHA256)
        width, height, pixels = png(raw)
        self.assertEqual((width, height), (1086, 181))
        sw, sh, source = png((ROOT / 'assets/characters/dave/dave_idle_walk_4dir.png').read_bytes())
        self.assertEqual((sw, sh), (1086, 1448))
        master = [source[((1086+y)*sw)*4:((1086+y)*sw+181)*4] for y in range(181)]
        for frame, pose in enumerate([0, 0, 1, 2, 2, 1]):
            for y in range(181):
                with self.subTest(frame=frame, row=y):
                    source_y = y
                    if y < 91 and pose == 1:
                        source_y += 1
                    elif pose == 2:
                        source_y += 2 if y < 86 else (1 if y < 91 else 0)
                    actual = pixels[(y*width+frame*181)*4:(y*width+(frame+1)*181)*4]
                    self.assertEqual(actual, master[source_y])
                    if y >= 91:
                        self.assertEqual(actual, master[y])

    def test_metadata_and_lossless_import(self):
        data = json.loads(read(ART + '.json'))
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 181})
        self.assertEqual(data['meta']['frameTags'],
                         [{'name': 'idle_north', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'idle_north_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'], {'x': i*181, 'y': 0, 'w': 181, 'h': 181})
            self.assertEqual(frame['duration'], 500)
            self.assertFalse(frame['trimmed'])
            self.assertFalse(frame['rotated'])
        self.assertEqual(data['proof']['sheet_sha256'], SHEET_SHA256)
        self.assertEqual(data['proof']['source_anchor'], [94, 174])
        settings = read(ART + '.png.import')
        for expected in ['compress/mode=0', 'mipmaps/generate=false',
                         'process/size_limit=0', f'source_file="res://{ART}.png"']:
            self.assertIn(expected, settings)

    def test_north_timing_and_frame_addressing(self):
        clip = self.clips['idle_north']
        self.assertIn('length = 3.0\n', clip)
        self.assertIn('loop_mode = 1\n', clip)
        self.assertIn('step = 0.5\n', clip)
        frame_track = clip.split('tracks/1/type')[0]
        self.assertIn('NodePath("NorthIdleSprite2D:frame")', frame_track)
        self.assertIn('"values": [0, 1, 2, 3, 4, 5]', frame_track)
        self.assertIn('"times": PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)', frame_track)
        self.assertIn('"update": 1', frame_track)

    def test_all_animation_transitions_select_exactly_one_sprite(self):
        expected = {'RESET', 'idle_north', 'idle_south', 'idle_east', 'idle_west',
                    'walk_north', 'walk_south', 'walk_east', 'walk_west'}
        self.assertEqual(set(self.clips), expected)
        for name, clip in self.clips.items():
            tracks = dict(re.findall(r'tracks/(\d+)/type = "value"\n(.*?)(?=tracks/\d+/type|\Z)',
                                     clip, re.S))
            self.assertEqual(set(tracks), {'0', '1', '2', '3'})
            visibility = []
            for index, sprite in [('2', 'Sprite2D'), ('3', 'NorthIdleSprite2D')]:
                track = tracks[index]
                self.assertIn(f'NodePath("{sprite}:visible")', track)
                self.assertIn('"times": PackedFloat32Array(0.0)', track)
                self.assertIn('"update": 1', track)
                visibility.append(json.loads(re.search(r'"values": (\[[^\]]+\])', track)[1])[0])
            self.assertEqual(visibility, [name != 'idle_north', name == 'idle_north'])
        # Existing controller applies the clip switch before the next rendered frame.
        controller = read('scenes/player/dave.gd')
        self.assertIn('animation_player.play(animation_name)', controller)
        self.assertIn('animation_player.advance(0.0)', controller)

    def test_sprite_scale_anchor_and_default_visibility(self):
        scene_nodes = nodes(self.scene)
        sprite = scene_nodes['Visual/NorthIdleSprite2D'][1]
        for value in ['visible = false', 'texture_filter = 1', 'hframes = 6',
                      'texture = ExtResource("7_north_idle")', 'centered = false',
                      'offset = Vector2(-94, -174)',
                      'scale = Vector2(0.71424418545, 0.71424418545)']:
            self.assertIn(value, sprite)
        self.assertNotRegex(sprite, r'(?m)^(vframes|position|rotation|skew|flip_h) =')
        self.assertIn(f'path="res://{ART}.png" id="7_north_idle"', self.scene)
        for path in re.findall(r'path="res://([^"]+)"', self.scene):
            self.assertTrue((ROOT / path).is_file(), path)

    def test_only_approved_scene_delta_and_no_other_art_changes(self):
        old_scene = git_blob(BASE, 'scenes/player/dave.tscn').replace(b'\r\n', b'\n')
        self.assertEqual(without_north_idle('scenes/player/dave.tscn', self.scene.encode()), old_scene)
        for path in ['scenes/player/dave.gd', 'scenes/player/follow_camera.gd',
                     'assets/characters/dave/dave_idle_walk_4dir.png',
                     'assets/characters/dave/dave_idle_walk_4dir.json']:
            actual = (ROOT / path).read_bytes()
            original = git_blob(BASE, path)
            if not path.endswith('.png'):
                actual, original = actual.replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n')
            self.assertEqual(actual, original, path)


if __name__ == '__main__':
    unittest.main()
