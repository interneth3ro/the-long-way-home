"""Reverse only the approved south-idle delta for historical comparisons.

The original south contract is checked by static_south_idle_test; the live scene
is checked by static_north_walk_size_test. Historical hashes remain unchanged and
unrelated scene edits remain detectable.
"""
import hashlib
import re

from current_preservation import ROOT, git_blob
from north_walk_size_preservation import without_north_walk_size
from east_idle_preservation import without_east_idle


BASE = '3806e6e99030ea3db866c1ebe7254d5b64ae232d'


def without_south_idle(path, raw):
    if path != 'scenes/player/dave.tscn':
        return raw
    text = raw.decode('utf-8').replace('\r\n', '\n')

    def replace_once(before, after):
        nonlocal text
        assert text.count(before) == 1, 'Unexpected south-idle scene structure'
        text = text.replace(before, after, 1)

    replace_once('[gd_scene load_steps=21 format=3]', '[gd_scene load_steps=20 format=3]')
    replace_once('[ext_resource type="Texture2D" path="res://assets/characters/dave/'
                 'dave_idle_south_v1.png" id="8_south_idle"]\n', '')
    replace_once('''[node name="SouthIdleSprite2D" type="Sprite2D" parent="Visual"]
visible = false
texture_filter = 1
scale = Vector2(0.71424418545, 0.71424418545)
texture = ExtResource("8_south_idle")
centered = false
offset = Vector2(-94, -174)
hframes = 6

''', '')

    def restore_clip(match):
        header, body = match[1], match[2]
        south = 'id="Animation_idle_south"' in header
        track = ('tracks/4/type = "value"\n'
                 'tracks/4/path = NodePath("SouthIdleSprite2D:visible")\n'
                 'tracks/4/interp = 1\ntracks/4/keys = {\n'
                 '"times": PackedFloat32Array(0.0),\n'
                 '"transitions": PackedFloat32Array(1),\n"update": 1,\n'
                 f'"values": [{str(south).lower()}]\n}}\n')
        assert body.count(track) == 1, 'Missing or changed south sprite visibility selection'
        body = body.replace(track, '', 1)
        if south:
            replacements = [
                ('length = 3.0\n', 'length = 1.2\n'),
                ('step = 0.5\n', 'step = 0.2\n'),
                ('NodePath("SouthIdleSprite2D:frame")', 'NodePath("Sprite2D:frame")'),
                ('PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)',
                 'PackedFloat32Array(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)'),
            ]
            for before, after in replacements:
                assert body.count(before) == 1, 'Unexpected south-idle frame/timing track'
                body = body.replace(before, after, 1)
            # Only south idle stops displaying the original atlas sprite.
            prefix, tail = body.split('tracks/2/type = "value"\n')
            main_track, tail = tail.split('tracks/3/type = "value"\n')
            assert main_track.count('"values": [false]') == 1
            main_track = main_track.replace('"values": [false]', '"values": [true]', 1)
            body = prefix + 'tracks/2/type = "value"\n' + main_track + 'tracks/3/type = "value"\n' + tail
        return header + body

    text, count = re.subn(r'(\[sub_resource type="Animation"[^\n]+\]\n)'
                          r'(.*?)(?=\[sub_resource)', restore_clip, text, flags=re.S)
    assert count == 9, 'Expected RESET and eight directional clips'
    assert 'SouthIdleSprite2D' not in text
    return text.encode('utf-8')


def verified_south_idle_paths():
    """Admit four exact production paths only after checking their contents."""
    art = 'assets/characters/dave/dave_idle_south_v1'
    hashes = {
        art + '.png': 'ab994380e1775aea1d4cb8fc1256f5f039f15663c4c270422a8a8399f1f777e4',
        art + '.json': '660b709bc715f72aef1f1ebe451ef7c2cdf30758aeddf3858998f02be2789ce3',
        art + '.png.import': '2f5e6bb8d8ddbda84e104eb595de68f770bbe669f4834e60ef65d862f4651f8d',
    }
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if not path.endswith('.png'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == digest, path
    scene = 'scenes/player/dave.tscn'
    original = git_blob(BASE, scene).replace(b'\r\n', b'\n')
    assert without_south_idle(scene, without_east_idle(scene, without_north_walk_size(scene, (ROOT / scene).read_bytes()))) == original
    return set(hashes) | {scene}
