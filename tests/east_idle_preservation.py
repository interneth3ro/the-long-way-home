"""Reverse only the approved east/west idle delta for historical comparisons.

The east contract is checked by static_east_idle_test; the live five-sprite
scene is checked by static_north_walk_size_test.
Historical hash pins remain unchanged and unrelated scene edits stay detectable.
"""
import hashlib
import re

from north_walk_size_preservation import without_north_walk_size
from current_preservation import ROOT, git_blob


BASE = 'a650743373e98020c2f1ebea692309e458c3d344'


def without_east_idle(path, raw):
    if path != 'scenes/player/dave.tscn':
        return raw
    text = raw.decode('utf-8').replace('\r\n', '\n')

    def replace_once(before, after):
        nonlocal text
        assert text.count(before) == 1, 'Unexpected east-idle scene structure'
        text = text.replace(before, after, 1)

    replace_once('[gd_scene load_steps=22 format=3]', '[gd_scene load_steps=21 format=3]')
    replace_once('[ext_resource type="Texture2D" path="res://assets/characters/dave/'
                 'dave_idle_east_v1.png" id="9_east_idle"]\n', '')
    replace_once('''[node name="EastIdleSprite2D" type="Sprite2D" parent="Visual"]
visible = false
texture_filter = 1
scale = Vector2(0.71424418545, 0.71424418545)
texture = ExtResource("9_east_idle")
centered = false
offset = Vector2(-94, -174)
hframes = 6

''', '')

    def restore_clip(match):
        header, body = match[1], match[2]
        name = re.search(r'id="Animation_([^"]+)"', header)[1]
        side_idle = name in ('idle_east', 'idle_west')
        for index, prop, value in [(5, 'visible', side_idle),
                                    (6, 'flip_h', name == 'idle_west')]:
            track = (f'tracks/{index}/type = "value"\n'
                     f'tracks/{index}/path = NodePath("EastIdleSprite2D:{prop}")\n'
                     f'tracks/{index}/interp = 1\ntracks/{index}/keys = {{\n'
                     '"times": PackedFloat32Array(0.0),\n'
                     '"transitions": PackedFloat32Array(1),\n"update": 1,\n'
                     f'"values": [{str(value).lower()}]\n}}\n')
            assert body.count(track) == 1, 'Missing or changed side-idle selection/mirroring'
            body = body.replace(track, '', 1)
        if side_idle:
            first = 24 if name == 'idle_east' else 12
            replacements = [
                ('length = 3.0\n', 'length = 1.2\n'),
                ('step = 0.5\n', 'step = 0.2\n'),
                ('NodePath("EastIdleSprite2D:frame")', 'NodePath("Sprite2D:frame")'),
                ('PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)',
                 'PackedFloat32Array(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)'),
                ('"values": [0, 1, 2, 3, 4, 5]', '"values": ' + str(list(range(first, first+6)))),
            ]
            for before, after in replacements:
                assert body.count(before) == 1, 'Unexpected east/west-idle frame/timing track'
                body = body.replace(before, after, 1)
            prefix, tail = body.split('tracks/2/type = "value"\n')
            main_track, tail = tail.split('tracks/3/type = "value"\n')
            assert main_track.count('"values": [false]') == 1
            main_track = main_track.replace('"values": [false]', '"values": [true]', 1)
            body = prefix + 'tracks/2/type = "value"\n' + main_track + 'tracks/3/type = "value"\n' + tail
        return header + body

    text, count = re.subn(r'(\[sub_resource type="Animation"[^\n]+\]\n)'
                          r'(.*?)(?=\[sub_resource)', restore_clip, text, flags=re.S)
    assert count == 9, 'Expected RESET and eight directional clips'
    assert 'EastIdleSprite2D' not in text
    return text.encode('utf-8')


def verified_east_idle_paths():
    """Admit four exact production paths only after checking their contents."""
    art = 'assets/characters/dave/dave_idle_east_v1'
    hashes = {
        art + '.png': '4598bf309fa81774e8c5ff77d811566258f4d8f36e9a1ff70be32bced850d2f1',
        art + '.json': '0e7ba9fbacea7b3455371a7449657e42f60c0a98487ebc74fa06d0e244e8bfa5',
        art + '.png.import': '5890984b6c8f8c3a0ad32d741321b8549fadb57c0941520aae5d872ca2f4526c',
    }
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if not path.endswith('.png'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == digest, path
    scene = 'scenes/player/dave.tscn'
    original = git_blob(BASE, scene).replace(b'\r\n', b'\n')
    assert without_east_idle(scene, without_north_walk_size(scene, (ROOT / scene).read_bytes())) == original
    return set(hashes) | {scene}
