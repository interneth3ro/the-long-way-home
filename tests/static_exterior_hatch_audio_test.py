"""Offline WAV and source contracts; never imports Godot or runs gameplay."""
import importlib.util
import io
import math
from pathlib import Path
import re
import struct
import unittest
from unittest.mock import patch
import wave

import current_preservation as preservation
from static_automatic_transitions_test import function

ROOT = Path(__file__).resolve().parents[1]
VISUAL = 'scenes/interaction/exterior_hatch_visual.gd'
SCENE = 'scenes/interaction/exterior_hatch_visual.tscn'
PLAYER = 'scenes/interaction/exterior_hatch_audio.gd'
GENERATOR = 'tools/generate-hatch-audio.py'
ART = 'assets/audio/exterior_hatch/'


def read(path):
    return (ROOT/path).read_text(encoding='utf-8')


class ExteriorHatchAudioStaticTest(unittest.TestCase):
    def test_pcm_format_duration_headroom_and_smooth_boundaries(self):
        for name, duration in (('open', 0.6), ('close', 0.7)):
            raw = (ROOT/ART/f'hatch_{name}.wav').read_bytes()
            self.assertEqual(raw[:4], b'RIFF')
            self.assertEqual(struct.unpack_from('<I', raw, 4)[0], len(raw)-8)
            self.assertEqual(raw[8:16], b'WAVEfmt ')
            self.assertEqual(struct.unpack_from('<H', raw, 20)[0], 1)  # PCM
            with wave.open(io.BytesIO(raw), 'rb') as wav:
                self.assertEqual((wav.getnchannels(), wav.getsampwidth(), wav.getframerate()), (1, 2, 24000))
                self.assertEqual(wav.getcomptype(), 'NONE')
                self.assertEqual(wav.getnframes(), round(24000*duration))
                frames = wav.readframes(wav.getnframes())
            samples = struct.unpack(f'<{len(frames)//2}h', frames)
            self.assertEqual(len(raw), 44+len(frames))
            self.assertEqual((samples[0], samples[-1]), (0, 0))
            self.assertLess(max(map(abs, samples)), 16384)
            self.assertGreater(max(map(abs, samples)), 2000)
            self.assertLess(abs(sum(samples)/len(samples)), 20)  # DC
            self.assertLess(max(abs(b-a) for a, b in zip(samples, samples[1:])), 2200)
            rms = math.sqrt(sum(s*s for s in samples)/len(samples))
            self.assertLess(rms/32768, 0.12)

    def test_deterministic_offline_generator_matches_both_assets(self):
        spec = importlib.util.spec_from_file_location('hatch_synthesis', ROOT/GENERATOR)
        generator = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(generator)
        for name in ('open', 'close'):
            self.assertEqual(generator.wav_bytes(name), (ROOT/ART/f'hatch_{name}.wav').read_bytes())
            self.assertEqual(generator.wav_bytes(name), generator.wav_bytes(name))
        source = read(GENERATOR)
        self.assertIn('path.open("xb")', source)
        for forbidden in ('import numpy', 'import scipy', 'import requests', 'import random'):
            self.assertNotIn(forbidden, source)

    def test_resource_closure_single_local_voice_and_no_autoplay(self):
        scene, player = read(SCENE), read(PLAYER)
        self.assertEqual(scene.count('type="AudioStreamPlayer"'), 1)
        self.assertIn('max_polyphony = 1', scene)
        self.assertNotIn('autoplay', scene)
        self.assertIn('class_name ExteriorHatchAudio\nextends AudioStreamPlayer', player)
        for name in ('open', 'close'):
            self.assertIn(f'preload("res://{ART}hatch_{name}.wav")', player)
        for path in re.findall(r'(?:path=|preload\()"res://([^"]+)"', scene+player):
            self.assertTrue((ROOT/path).is_file(), path)

    def test_animation_changes_are_only_audio_hooks(self):
        visual = read(VISUAL)
        restored = visual.replace('@onready var _audio: ExteriorHatchAudio = $MechanicalAudio\n', '', 1)
        restored = restored.replace('\t_audio.reset_audio()\n', '', 1)
        hook = '\tif delta > 0.0 and openness != target:\n\t\t_audio.update_motion(_target_open, openness)\n'
        self.assertEqual(visual.count(hook), 1)
        restored = restored.replace(hook, '', 1)
        self.assertEqual(restored, preservation.git_blob(preservation.AUDIO_BASE, VISUAL).decode().replace('\r\n', '\n'))
        tick = function(visual, '_advance_animation')
        self.assertLess(tick.index('_audio.update_motion'), tick.index('openness = move_toward'))
        self.assertIn('OPEN_SECONDS if _target_open else CLOSE_SECONDS', tick)
        self.assertIn('_audio.reset_audio()', function(visual, 'prepare_for_arrival'))
        scene = read(SCENE).replace('load_steps=7', 'load_steps=6', 1)
        scene = scene.replace('[ext_resource type="Script" path="res://'+PLAYER+'" id="4_audio"]\n', '', 1)
        scene = scene.replace('\n[node name="MechanicalAudio" type="AudioStreamPlayer" parent="."]\nmax_polyphony = 1\nscript = ExtResource("4_audio")\n', '', 1)
        self.assertEqual(scene, preservation.git_blob(preservation.AUDIO_BASE, SCENE).decode().replace('\r\n', '\n'))

    def test_direction_guard_reversal_fades_and_remaining_travel_seek(self):
        code = read(PLAYER)
        update = function(code, 'update_motion')
        self.assertIn('if direction == _direction:\n\t\treturn', update)
        self.assertLess(update.index('if direction == _direction'), update.index('_ramp.kill()'))
        self.assertLess(update.index('_direction = direction'), update.index('if _switching:'))
        self.assertIn('_switching = true', update)
        self.assertIn('tween_property(self, "volume_linear", 0.0, RAMP_SECONDS)', update)
        self.assertLess(update.index('tween_property'), update.index('tween_callback(_play_direction)'))
        start = function(code, '_play_direction')
        self.assertLess(start.index('stop()'), start.index('stream ='))
        self.assertLess(start.index('stream ='), start.index('\tplay('))
        self.assertIn('OPEN_SOUND if _direction > 0 else CLOSE_SOUND', start)
        self.assertIn('_openness if _direction > 0 else 1.0 - _openness', start)
        self.assertLess(start.index('volume_linear = 0.0'), start.index('\tplay('))
        self.assertIn('clampf(fraction, 0.0, 1.0) * stream.get_length()', start)
        self.assertEqual(code.count('\tplay('), 1)
        self.assertNotIn('AudioStreamPlayer.new', code)
        self.assertIn('const RAMP_SECONDS: float = 0.012', code)

    def test_transition_detach_and_silent_cached_arrival_cleanup(self):
        code = read(PLAYER)
        self.assertIn('transitions.transition_started.connect(_silence)', function(code, '_ready'))
        silence = function(code, '_silence')
        self.assertLess(silence.index('if not is_inside_tree():'), silence.index('create_tween()'))
        self.assertIn('_ramp.kill()', silence)
        self.assertIn('_direction = 0', silence)
        self.assertIn('_switching = false', silence)
        self.assertLess(silence.index('tween_property'), silence.index('tween_callback(stop)'))
        self.assertIn('reset_audio()', function(code, '_exit_tree'))
        reset = function(code, 'reset_audio')
        for contract in ('_ramp.kill()', 'stop()', '_direction = 0', '_switching = false', 'volume_linear = 0.0'):
            self.assertIn(contract, reset)
        self.assertNotIn('process_mode', code)

    def test_protected_boarding_collision_transition_and_player_bytes_unchanged(self):
        for path in ('scenes/interaction/exterior_boarding.gd', 'scenes/world/planet_exterior.tscn',
                     'scenes/world/planet_exterior.gd', 'scenes/main/scene_transition_controller.gd',
                     'scenes/player/dave.gd', 'scenes/player/follow_camera.gd',
                     'scenes/interaction/scene_hatch.gd', 'scenes/world/production_ship_interior_v2.tscn',
                     'project.godot'):
            self.assertEqual(preservation.normalized(path, (ROOT/path).read_bytes()),
                             preservation.normalized(path, preservation.git_blob(preservation.AUDIO_BASE, path)), path)

    def test_exact_audio_scope_and_projections_reject_tampering(self):
        self.assertEqual(set(preservation.AUDIO_INPUT_SHA256), {
            VISUAL, SCENE, PLAYER, GENERATOR, ART+'hatch_open.wav', ART+'hatch_close.wav'})
        for path, digest in (preservation.AUDIO_INPUT_SHA256 | preservation.AUDIO_TEST_SHA256).items():
            raw = (ROOT/path).read_bytes()
            preservation.verify_fingerprint(path, raw, digest)
            projected = preservation.audio_predecessor(path, raw)
            if path in preservation.AUDIO_EXISTING_PATHS:
                self.assertEqual(preservation.normalized(path, projected),
                                 preservation.normalized(path, preservation.git_blob(preservation.AUDIO_BASE, path)))
            for bad in (raw+b'UNREVIEWED', raw[1:], raw+raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    preservation.audio_predecessor(path, bad)
                with patch.object(Path, 'read_bytes', return_value=bad):
                    if path in preservation.AUDIO_INPUT_SHA256:
                        with self.assertRaises(AssertionError):
                            preservation.without_current_paths([path])
        self.assertEqual(preservation.without_current_paths(list(preservation.AUDIO_INPUT_SHA256)), [])
        self.assertEqual(preservation.without_current_paths([ART+'unrelated.wav']), [ART+'unrelated.wav'])
        raw = b'RIFF\r\nWAVE'
        self.assertEqual(preservation.normalized(ART+'hatch_open.wav', raw), raw)


if __name__ == '__main__':
    unittest.main()
