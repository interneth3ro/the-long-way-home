"""Approved east/west walking pixels and live scene contracts; no Godot execution."""
import hashlib
import json
import re
import subprocess
import unittest

from current_preservation import git_blob, normalized
from east_walk_alignment_preservation import ART, BASE, verified_east_walk_alignment_paths, without_east_walk_alignment
from static_automatic_transitions_test import ROOT, blocks, nodes, read
from static_east_idle_test import tracks
from static_exterior_hatch_visual_test import png


SHEET_SHA256 = '6d00dfb65a183512afb1fb383dfed7a9e023b55aa5279dd65e70519e27bc0353'
SOURCE = 'assets/characters/dave/dave_idle_walk_4dir.png'
SHIFTS = [-4, 0, 4, -4, 0, 4]


class EastWalkAlignmentStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.scene = read('scenes/player/dave.tscn')
        cls.clips = {re.search(r'id="Animation_([^"]+)"', h)[1]: b
                     for h, b in blocks(cls.scene, 'sub_resource') if h.startswith('type="Animation"')}
        cls.sheet = png((ROOT / (ART + '.png')).read_bytes())
        cls.source = png((ROOT / SOURCE).read_bytes())

    def test_approved_sheet_identity_and_cell_size(self):
        self.assertEqual(hashlib.sha256((ROOT / (ART + '.png')).read_bytes()).hexdigest(), SHEET_SHA256)
        self.assertEqual(self.sheet[:2], (1086, 181))
        self.assertEqual(self.source[:2], (1086, 1448))
        self.assertEqual(hashlib.sha256((ROOT / SOURCE).read_bytes()).hexdigest(),
                         '6ca7d1eb6d341847216c4eccf9c6b39958b451823cda21b3150cfeeeaf0c2766')

    def test_each_frame_is_lossless_horizontal_translation(self):
        width, _, source = self.source
        pixels = self.sheet[2]
        self.assertEqual(sum(SHIFTS), 0)
        for frame, dx in enumerate(SHIFTS):
            with self.subTest(frame=frame):
                for y in range(181):
                    old_start = ((905 + y) * width + frame * 181) * 4
                    old = source[old_start:old_start + 181 * 4]
                    start = (y * width + frame * 181) * 4
                    actual = pixels[start:start + 181 * 4]
                    if dx < 0:
                        self.assertFalse(any(old[: -dx * 4]))
                        expected = old[-dx * 4:] + bytes(-dx * 4)
                    elif dx > 0:
                        self.assertFalse(any(old[(181 - dx) * 4:]))
                        expected = bytes(dx * 4) + old[:(181 - dx) * 4]
                    else:
                        expected = old
                    self.assertEqual(actual, expected, (frame, y))

    def test_metadata_and_lossless_import(self):
        data = json.loads(read(ART + '.json'))
        self.assertEqual(data['meta']['image'], 'dave_walk_east_aligned_v1.png')
        self.assertEqual(data['meta']['size'], {'w': 1086, 'h': 181})
        self.assertEqual(data['meta']['frameTags'], [{'name': 'walk_east', 'from': 0, 'to': 5, 'direction': 'forward'}])
        self.assertEqual(list(data['frames']), [f'walk_east_{i:02}' for i in range(6)])
        for i, frame in enumerate(data['frames'].values()):
            self.assertEqual(frame['frame'], {'x': i * 181, 'y': 0, 'w': 181, 'h': 181})
            self.assertEqual(frame['sourceSize'], {'w': 181, 'h': 181})
            self.assertEqual(frame['duration'], 100)
            self.assertFalse(frame['trimmed'])
            self.assertFalse(frame['rotated'])
        proof = data['proof']
        self.assertEqual(proof['source'], SOURCE)
        self.assertEqual(proof['sheet_sha256'], SHEET_SHA256)
        self.assertEqual(proof['source_frames'], list(range(30, 36)))
        self.assertEqual(proof['integer_shifts_x'], SHIFTS)
        self.assertEqual(proof['integer_shifts_y'], [0] * 6)
        self.assertEqual(proof['anchor'], [94, 174])
        self.assertEqual(proof['loop_ms'], 600)
        settings = read(ART + '.png.import')
        for expected in ['compress/mode=0', 'mipmaps/generate=false', 'process/size_limit=0',
                         f'source_file="res://{ART}.png"']:
            self.assertIn(expected, settings)
        cache_hash = hashlib.md5(f'res://{ART}.png'.encode()).hexdigest()
        self.assertEqual(settings.count(f'dave_walk_east_aligned_v1.png-{cache_hash}.ctex'), 2)
        uid = re.search(r'^uid="([^"]+)"', settings, re.M)[1]
        other_settings = [p for p in (ROOT / 'assets/characters/dave').rglob('*.import')
                          if p != ROOT / (ART + '.png.import')]
        self.assertFalse(any(f'uid="{uid}"' in p.read_text() for p in other_settings))

    def test_east_and_west_share_frame_order_and_timing(self):
        for direction in ('east', 'west'):
            clip = self.clips['walk_' + direction]
            for value in ['length = 0.6\n', 'loop_mode = 1\n', 'step = 0.1\n']:
                self.assertIn(value, clip)
            frame = tracks(clip)['0']
            for value in ['NodePath("EastWalkSprite2D:frame")', '"values": [0, 1, 2, 3, 4, 5]',
                          '"times": PackedFloat32Array(0.0, 0.1, 0.2, 0.3, 0.4, 0.5)', '"update": 1']:
                self.assertIn(value, frame)
        self.assertEqual(self.scene.count('NodePath("EastWalkSprite2D:frame")'), 2)

    def test_all_live_clips_select_one_sprite_and_reset_flips(self):
        expected = {'RESET', 'idle_north', 'idle_south', 'idle_east', 'idle_west',
                    'walk_north', 'walk_south', 'walk_east', 'walk_west'}
        self.assertEqual(set(self.clips), expected)
        for name, clip in self.clips.items():
            with self.subTest(animation=name):
                actual = tracks(clip)
                self.assertEqual(set(actual), {str(i) for i in range(10)})
                visibility = []
                for index, sprite, visible in [
                    (2, 'Sprite2D', name in ('RESET', 'walk_south')),
                    (3, 'NorthIdleSprite2D', name == 'idle_north'),
                    (4, 'SouthIdleSprite2D', name == 'idle_south'),
                    (5, 'EastIdleSprite2D', name in ('idle_east', 'idle_west')),
                    (7, 'NorthWalkSprite2D', name == 'walk_north'),
                    (8, 'EastWalkSprite2D', name in ('walk_east', 'walk_west')),
                ]:
                    track = actual[str(index)]
                    self.assertIn(f'NodePath("{sprite}:visible")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    value = json.loads(re.search(r'"values": (\[[^\]]+\])', track)[1])
                    self.assertEqual(value, [visible])
                    visibility += value
                self.assertEqual(sum(visibility), 1)
                for index, sprite, flipped in [(1, 'Sprite2D', False),
                                               (6, 'EastIdleSprite2D', name == 'idle_west'),
                                               (9, 'EastWalkSprite2D', name == 'walk_west')]:
                    track = actual[str(index)]
                    self.assertIn(f'NodePath("{sprite}:flip_h")', track)
                    self.assertIn('"times": PackedFloat32Array(0.0)', track)
                    self.assertIn('"update": 1', track)
                    self.assertIn(f'"values": [{str(flipped).lower()}]', track)
        self.assertIn('animation_player.advance(0.0)', read('scenes/player/dave.gd'))

    def test_shared_scale_anchor_and_scene_references(self):
        scene_nodes = nodes(self.scene)
        sprite = scene_nodes['Visual/EastWalkSprite2D'][1]
        for value in ['visible = false', 'texture_filter = 1', 'hframes = 6',
                      'texture = ExtResource("11_east_walk")', 'centered = false',
                      'offset = Vector2(-94, -174)', 'scale = Vector2(0.71424418545, 0.71424418545)']:
            self.assertIn(value, sprite)
        self.assertNotRegex(sprite, r'(?m)^(vframes|position|rotation|skew|flip_h) =')
        for path in re.findall(r'path="res://([^"]+)"', self.scene):
            self.assertTrue((ROOT / path).is_file(), path)
        external = re.findall(r'^\[ext_resource .* id="([^"]+)"\]$', self.scene, re.M)
        internal = re.findall(r'^\[sub_resource .* id="([^"]+)"\]$', self.scene, re.M)
        self.assertEqual(len(external), len(set(external)))
        self.assertEqual(len(internal), len(set(internal)))
        self.assertEqual(int(re.search(r'load_steps=(\d+)', self.scene)[1]), len(external) + len(internal) + 1)
        self.assertLessEqual(set(re.findall(r'ExtResource\("([^"]+)"\)', self.scene)), set(external))
        self.assertLessEqual(set(re.findall(r'SubResource\("([^"]+)"\)', self.scene)), set(internal))
        for target in re.findall(r'NodePath\("([^":]+):[^"]+"\)', self.scene):
            self.assertIn('Visual/' + target, scene_nodes)

    def test_only_approved_scene_delta_and_existing_art_preserved(self):
        scene = 'scenes/player/dave.tscn'
        self.assertEqual(without_east_walk_alignment(scene, self.scene.encode()),
                         git_blob(BASE, scene).replace(b'\r\n', b'\n'))
        self.assertEqual(verified_east_walk_alignment_paths(), {ART + '.png', ART + '.json', ART + '.png.import', scene})
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--',
                                        'assets/characters/dave'], cwd=ROOT, text=True).splitlines()
        paths += ['scenes/player/dave.gd', 'scenes/player/follow_camera.gd', 'project.godot',
                  'tools/run-local-tests.ps1', 'AGENTS.md', 'docs/LOCAL_TESTING.md']
        for path in paths:
            self.assertEqual(normalized(path, (ROOT / path).read_bytes()), normalized(path, git_blob(BASE, path)), path)

    def test_projection_rejects_changed_tracks_and_keeps_unrelated_edits_visible(self):
        scene = 'scenes/player/dave.tscn'
        changed = self.scene.replace('NodePath("EastWalkSprite2D:flip_h")', 'NodePath("EastWalkSprite2D:flip_v")', 1)
        with self.assertRaises(AssertionError):
            without_east_walk_alignment(scene, changed.encode())
        changed = self.scene.replace('radius = 10.0', 'radius = 11.0', 1)
        restored = without_east_walk_alignment(scene, changed.encode())
        self.assertNotEqual(restored, git_blob(BASE, scene).replace(b'\r\n', b'\n'))
        self.assertIn(b'radius = 11.0', restored)


if __name__ == '__main__':
    unittest.main()
