"""Offline PNG composition, geometry and source-contract checks; no Godot."""
import hashlib
import math
from pathlib import Path
import re
import struct
import subprocess
import unittest
from unittest.mock import patch
import zlib

import current_preservation as preservation

ROOT = Path(__file__).resolve().parents[1]
ART = 'assets/environment/exterior/hatch_v2/'
SCENE = 'scenes/world/planet_exterior.tscn'
VISUAL = 'scenes/interaction/exterior_hatch_visual.tscn'
SCRIPT = 'scenes/interaction/exterior_hatch_visual.gd'
BASE = '14876d26e4199922a5bd09cf436997792d7a5b6a'


def text(path):
    return (ROOT/path).read_text(encoding='utf-8')


def baseline(path):
    return subprocess.check_output(['git', 'show', f'{BASE}:{path}'], cwd=ROOT)


def png(raw):
    """CRC-check and decode ordinary 8-bit RGBA, without image dependencies."""
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, compressed, ended = 8, bytearray(), False
    while pos < len(raw):
        size = struct.unpack_from('>I', raw, pos)[0]
        kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+size]
        assert zlib.crc32(kind+data) == struct.unpack_from('>I', raw, pos+8+size)[0]
        if kind == b'IHDR':
            width, height, *mode = struct.unpack('>IIBBBBB', data)
            assert mode == [8, 6, 0, 0, 0]
        if kind == b'IDAT':
            compressed.extend(data)
        if kind == b'IEND':
            assert size == 0
            ended = True
        pos += size+12
    assert pos == len(raw) and ended
    scan = zlib.decompress(compressed)
    stride = width*4
    assert len(scan) == height*(stride+1)
    previous, pixels = bytearray(stride), bytearray()
    for y in range(height):
        offset = y*(stride+1)
        filtering = scan[offset]
        assert filtering in range(5)
        row = bytearray(scan[offset+1:offset+1+stride])
        for x in range(stride):
            a = row[x-4] if x >= 4 else 0
            b, c = previous[x], previous[x-4] if x >= 4 else 0
            p = a+b-c
            distances = (abs(p-a), abs(p-b), abs(p-c))
            paeth = (a, b, c)[distances.index(min(distances))]
            row[x] = (row[x]+(0, a, b, (a+b)//2, paeth)[filtering]) % 256
        pixels.extend(row)
        previous = row
    return width, height, pixels


def node(scene, name):
    return scene.split(f'[node name="{name}"', 1)[1].split('[node ', 1)[0]


class ExteriorHatchVisualStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        ship = (ROOT/'assets/environment/exterior/crashed_exploration_ship_approved.png').read_bytes()
        assert hashlib.sha256(ship).hexdigest() == '80ae633c36242c1effdcebea38dc05cfef8eb586ca9ef3103f6b02be91564e5b'
        w, h, pixels = png(ship)
        assert (w, h) == (1774, 887)
        cls.crop = b''.join(pixels[(y*w+725)*4:(y*w+1000)*4] for y in range(535, 810))
        cls.leaf = png((ROOT/(ART+'door_leaf_opaque_v2.png')).read_bytes())[2]
        cls.recess = png((ROOT/(ART+'recess_backing_black_light.png')).read_bytes())[2]

    def test_approved_bytes_dimensions_and_binary_aperture(self):
        expected = {
            'door_leaf_opaque_v2.png': '7cccb9390beff971abd9e0f1c74455a35cf5b4cd05844f37887542ccea067e10',
            'recess_backing_black_light.png': '80aa066edd98fae9eb5392ee79bb061bd82c80d48dc41e854e7c31141a3872c6',
        }
        for name, digest in expected.items():
            raw = (ROOT/(ART+name)).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(), digest)
            self.assertEqual(png(raw)[:2], (275, 275))
        self.assertEqual(self.leaf[3::4], self.recess[3::4])
        self.assertEqual(set(self.recess[3::4]), {0, 255})
        self.assertEqual(sum(a > 0 for a in self.recess[3::4]), 11021)
        shadow = ROOT/'assets/environment/exterior/crashed_ship_contact_shadow_prototype.png'
        self.assertEqual(hashlib.sha256(shadow.read_bytes()).hexdigest(),
                         '1cd8111595e11d8beb527f538188f38f8517f1d3365633c013b9a137ca601777')

    def test_actual_closed_stack_rgb_and_accepted_alpha_tolerance(self):
        # Both overlay alphas are binary: source-over is exact replacement at
        # 255 and unchanged destination at zero. No partitioning shortcut.
        composite = bytearray(self.crop)
        for layer in (self.recess, self.leaf):
            for i in range(0, len(layer), 4):
                if layer[i+3] == 255:
                    composite[i:i+4] = layer[i:i+4]
        rgba, rgb, maximum, absolute = 0, 0, [0]*4, 0
        for i in range(0, len(composite), 4):
            rgba += composite[i:i+4] != self.crop[i:i+4]
            rgb += composite[i:i+3] != self.crop[i:i+3]
            for channel in range(4):
                delta = abs(composite[i+channel]-self.crop[i+channel])
                maximum[channel] = max(maximum[channel], delta)
                if channel < 3:
                    absolute += delta
        self.assertEqual((rgba, rgb, maximum, absolute), (11021, 0, [0, 0, 0, 3], 0))
        # Reproduce the explicitly accepted example-background tolerance.
        displayed_max = 0
        for i in range(0, len(composite), 4):
            for c, background in enumerate((64, 72, 56)):
                def over(image):
                    return (image[i+c]*image[i+3]+background*(255-image[i+3])+127)//255
                displayed_max = max(displayed_max, abs(over(composite)-over(self.crop)))
        self.assertEqual(displayed_max, 2)

    def test_fixed_aperture_clips_every_diagnostic_step_and_clears_at_endpoint(self):
        visible_counts = []
        mask = self.recess[3::4]
        for t in (0, .25, .5, .75, 1):
            dx, dy = math.floor(10*t+.5), -math.floor(140*t+.5)
            composite = bytearray(self.crop)
            visible = 0
            for i in range(275*275):
                if not mask[i]:
                    continue
                composite[i*4:i*4+4] = self.recess[i*4:i*4+4]
                sx, sy = i % 275-dx, i//275-dy
                if 0 <= sx < 275 and 0 <= sy < 275 and mask[sy*275+sx]:
                    j = (sy*275+sx)*4
                    composite[i*4:i*4+4] = self.leaf[j:j+4]
                    visible += 1
            self.assertTrue(all(composite[i*4:i*4+4] == self.crop[i*4:i*4+4]
                                for i in range(275*275) if not mask[i]))
            visible_counts.append(visible)
        self.assertEqual(visible_counts, [11021, 7337, 3689, 219, 0])

    def test_registration_layer_order_and_native_clipping_contract(self):
        scene, exterior = text(VISUAL), text(SCENE)
        self.assertIn('parent="GroundObjects/CrashedShip" instance=', exterior)
        self.assertIn('position = Vector2(-87.5, -134.5)', node(scene, 'Artwork'))
        self.assertIn('scale = Vector2(0.70, 0.70)', node(scene, 'Artwork'))
        self.assertIn('clip_children = 2', node(scene, 'Recess'))
        self.assertIn('parent="Artwork/Recess"', node(scene, 'Door'))
        self.assertEqual(scene.count('centered = false'), 2)
        self.assertNotIn('stationary_surround', scene)
        self.assertNotIn('Shader', scene)
        self.assertNotIn('CanvasGroup', scene)
        self.assertNotIn('y_sort_enabled', scene)
        self.assertEqual((-384-87.5, -192-134.5), (-471.5, -326.5))
        self.assertEqual((-471.5+125*.7, -326.5+215*.7), (-384, -176))
        for path in re.findall(r'path="res://([^"]+)"', scene+exterior):
            self.assertTrue((ROOT/path).is_file(), path)

    def test_world_unit_zones_include_doorway_footprint_and_arrival(self):
        scene = text(VISUAL)
        def dimensions(name):
            match = re.search(r'id="'+name+r'"\]\nsize = Vector2\((\d+), (\d+)\)', scene)
            return tuple(map(int, match.groups()))
        approach, hold = dimensions('ApproachZone'), dimensions('HoldOpenZone')
        self.assertEqual(approach, (128, 112))
        self.assertEqual(hold, (176, 160))
        self.assertNotIn('scale =', node(scene, 'HatchVisual'))
        for name in ('Approach', 'HoldOpen'):
            area = node(scene, name)
            for prop in ('position = Vector2(0, 71)', 'collision_layer = 0',
                         'collision_mask = 1', 'monitorable = false'):
                self.assertIn(prop, area)
        # Same center and 24 units of hysteresis margin on each side.
        self.assertEqual(tuple((h-a)/2 for a, h in zip(approach, hold)), (24, 24))
        center = (-384, -192+71)
        self.assertEqual(center, (-384, -176+55))
        left, right = center[0]-hold[0]/2, center[0]+hold[0]/2
        top, bottom = center[1]-hold[1]/2, center[1]+hold[1]/2
        self.assertEqual((left, right, top, bottom), (-472, -296, -201, -41))
        # Hold zone still contains the unchanged hatch plus a radius-10 buffer.
        self.assertLessEqual(left, -416-10)
        self.assertGreaterEqual(right, -352+10)
        self.assertLessEqual(top, -188-10)
        self.assertGreaterEqual(bottom, -164+10)
        # Dave's arrival circle center (-384,-74) is inside approach and hold.
        self.assertTrue(center[0]-approach[0]/2 < -384 < center[0]+approach[0]/2)
        self.assertTrue(center[1]-approach[1]/2 < -74 < center[1]+approach[1]/2)

    def test_animation_source_preserves_partial_position_and_delay(self):
        source = text(SCRIPT)
        for constant, value in (('OPEN_SECONDS', '0.6'), ('CLOSE_SECONDS', '0.7'), ('CLOSE_DELAY', '1.0')):
            self.assertIn(f'const {constant}: float = {value}', source)
        self.assertIn('const DOOR_TRAVEL := Vector2(10, -140)', source)
        self.assertIn('openness = move_toward(openness, target, delta / duration)', source)
        self.assertIn('_door.position = DOOR_TRAVEL * openness', source)
        self.assertIn('OPEN_SECONDS if _target_open else CLOSE_SECONDS', source)
        self.assertIn('if approaching or (holding and (_target_open or openness > 0.0)):', source)
        self.assertIn('CLOSE_DELAY - _outside_seconds', source)
        self.assertIn('_advance_animation(delta - grace)', source)
        self.assertEqual(source.count('get_first_node_in_group'), 1)
        self.assertIn('_registration_frames = 2', source)
        self.assertIn('_transitions.is_transitioning()', source)
        self.assertNotIn('body_entered', source)
        for forbidden in ('request_transition', 'interaction_enabled', '.disabled',
                          'create_tween', 'Input.', 'Audio', 'load(', 'queue_free'):
            self.assertNotIn(forbidden, source)
        # Independent timing/distance expectations for reversal from 40% open.
        self.assertAlmostEqual((1-.4)*.6, .36)
        self.assertAlmostEqual(.4*.7, .28)
        self.assertAlmostEqual(1.0-.99, .01)

    def test_exterior_delta_is_only_visual_attachment_and_e_contract_is_unchanged(self):
        scene = text(SCENE)
        restored = scene.replace('load_steps=14', 'load_steps=13', 1)
        restored = restored.replace('[ext_resource type="PackedScene" path="res://'+VISUAL+'" id="7_hatch_visual"]\n\n', '', 1)
        restored = restored.replace('[node name="HatchVisual" parent="GroundObjects/CrashedShip" instance=ExtResource("7_hatch_visual")]\n\n', '', 1)
        self.assertEqual(restored, baseline(SCENE).decode().replace('\r\n', '\n'))
        for path in ('scenes/interaction/scene_hatch.gd', 'scenes/main/main_v2.gd',
                     'scenes/main/scene_transition_controller.gd', 'scenes/player/dave.gd',
                     'scenes/player/interaction_detector.gd', 'project.godot',
                     'scenes/world/planet_exterior.gd', 'scenes/interaction/automatic_doorway.gd',
                     'scenes/world/production_ship_interior_v2.tscn'):
            self.assertEqual((ROOT/path).read_bytes().replace(b'\r\n', b'\n'),
                             baseline(path).replace(b'\r\n', b'\n'), path)
        # Owner's initial 8/8 acceptance remains preserved at its commit.
        # This refinement may change only the two sizes, centers and comment.
        accepted = '3c315a707f1131367d58d3f1a61f5b70776596b8'
        refined = text(VISUAL)
        refined = refined.replace('id="ApproachZone"]\nsize = Vector2(128, 112)',
                                  'id="ApproachZone"]\nsize = Vector2(176, 160)')
        refined = refined.replace('id="HoldOpenZone"]\nsize = Vector2(176, 160)',
                                  'id="HoldOpenZone"]\nsize = Vector2(224, 208)')
        refined = refined.replace('position = Vector2(0, 71)', 'position = Vector2(0, 96)')
        refined = refined.replace('; + (0,55).', '; + (0,80).')
        for path, actual in ((VISUAL, refined), (SCRIPT, text(SCRIPT))):
            original = subprocess.check_output(['git', 'show', f'{accepted}:{path}'], cwd=ROOT)
            self.assertEqual(actual, original.decode().replace('\r\n', '\n'), path)

    def test_new_exact_receipts_reject_tampering_and_expansion(self):
        self.assertEqual(set(preservation.HATCH_INPUT_SHA256),
                         {SCENE, SCRIPT, VISUAL, ART+'door_leaf_opaque_v2.png', ART+'recess_backing_black_light.png'})
        for path, digest in preservation.HATCH_INPUT_SHA256.items():
            raw = (ROOT/path).read_bytes()
            preservation.verify_fingerprint(path, raw, digest)
            for bad in (raw+b'EXTRA', raw[1:], raw+raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    preservation.verify_fingerprint(path, bad, digest)
                with patch.object(Path, 'read_bytes', return_value=bad), self.assertRaises(AssertionError):
                    preservation.without_current_paths([path])
        self.assertEqual(preservation.without_current_paths(list(preservation.HATCH_INPUT_SHA256)), [])
        self.assertEqual(preservation.without_current_paths([ART+'unrelated.png']), [ART+'unrelated.png'])


if __name__ == '__main__':
    unittest.main()
