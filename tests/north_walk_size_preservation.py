"""Reverse only the approved north-walk size delta for historical comparisons.

The north contract is checked by static_north_walk_size_test; the live scene
is checked by static_east_walk_alignment_test.
Historical hash pins remain unchanged and unrelated edits stay detectable.
"""
import hashlib
import re

from current_preservation import ROOT, git_blob
from east_walk_alignment_preservation import without_east_walk_alignment


BASE = 'e8bbdd3bcd04e32e363057f13a0940ce2416c087'


def without_north_walk_size(path, raw):
    if path != 'scenes/player/dave.tscn':
        return raw
    raw = without_east_walk_alignment(path, raw)
    text = raw.decode('utf-8').replace('\r\n', '\n')

    def replace_once(before, after):
        nonlocal text
        assert text.count(before) == 1, 'Unexpected north-walk size scene structure'
        text = text.replace(before, after, 1)

    replace_once('[gd_scene load_steps=23 format=3]', '[gd_scene load_steps=22 format=3]')
    replace_once('[ext_resource type="Texture2D" path="res://assets/characters/dave/'
                 'dave_walk_north_size_v1.png" id="10_north_walk"]\n', '')
    replace_once('''[node name="NorthWalkSprite2D" type="Sprite2D" parent="Visual"]
visible = false
texture_filter = 1
scale = Vector2(0.71424418545, 0.71424418545)
texture = ExtResource("10_north_walk")
centered = false
offset = Vector2(-94, -174)
hframes = 6

''', '')

    def restore_clip(match):
        header, body = match[1], match[2]
        north = 'id="Animation_walk_north"' in header
        track = ('tracks/7/type = "value"\n'
                 'tracks/7/path = NodePath("NorthWalkSprite2D:visible")\n'
                 'tracks/7/interp = 1\ntracks/7/keys = {\n'
                 '"times": PackedFloat32Array(0.0),\n'
                 '"transitions": PackedFloat32Array(1),\n"update": 1,\n'
                 f'"values": [{str(north).lower()}]\n}}\n')
        assert body.count(track) == 1, 'Missing or changed north-walk sprite selection'
        body = body.replace(track, '', 1)
        if north:
            for before, after in [
                ('NodePath("NorthWalkSprite2D:frame")', 'NodePath("Sprite2D:frame")'),
                ('"values": [0, 1, 2, 3, 4, 5]', '"values": [42, 43, 44, 45, 46, 47]'),
            ]:
                assert body.count(before) == 1, 'Unexpected north-walk frame track'
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
    assert 'NorthWalkSprite2D' not in text
    return text.encode('utf-8')


def verified_north_walk_size_paths():
    """Admit four exact production paths only after checking their contents."""
    art = 'assets/characters/dave/dave_walk_north_size_v1'
    hashes = {
        art + '.png': '07f995bd09eda3c31e9784270bee35d0b93862fab492c7e59f19ba7f277e47b4',
        art + '.json': '71069c69e0b66ae9ae922640ff4592d3d659c62b9bddfb3f8f0bb36377c5e4e7',
        art + '.png.import': '8057866c6288141effd852340abb0e03bc8fe5c869d7d281fc13edd9036f965d',
    }
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if not path.endswith('.png'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == digest, path
    scene = 'scenes/player/dave.tscn'
    original = git_blob(BASE, scene).replace(b'\r\n', b'\n')
    assert without_north_walk_size(scene, (ROOT / scene).read_bytes()) == original
    return set(hashes) | {scene}
