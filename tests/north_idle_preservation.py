"""Reverse only the approved north-idle presentation for historical comparisons.

Existing historical hashes stay unchanged. The live integration is checked by
static_north_idle_test; this projection keeps unrelated source edits detectable.
"""
import hashlib
import re

from current_preservation import ROOT, git_blob
from south_idle_preservation import without_south_idle


def without_north_idle(path, raw):
    if path != 'scenes/player/dave.tscn':
        return raw
    text = raw.decode('utf-8').replace('\r\n', '\n')

    def replace_once(before, after):
        nonlocal text
        assert text.count(before) == 1, 'Unexpected north-idle scene structure'
        text = text.replace(before, after, 1)

    replace_once('[gd_scene load_steps=20 format=3]', '[gd_scene load_steps=19 format=3]')
    replace_once('[ext_resource type="Texture2D" path="res://assets/characters/dave/'
                 'dave_idle_north_v1.png" id="7_north_idle"]\n', '')
    replace_once('''[node name="NorthIdleSprite2D" type="Sprite2D" parent="Visual"]
visible = false
texture_filter = 1
scale = Vector2(0.71424418545, 0.71424418545)
texture = ExtResource("7_north_idle")
centered = false
offset = Vector2(-94, -174)
hframes = 6

''', '')

    def restore_clip(match):
        header, body = match[1], match[2]
        north = 'id="Animation_idle_north"' in header
        for index, node, visible in [(2, 'Sprite2D', not north),
                                     (3, 'NorthIdleSprite2D', north)]:
            track = (f'tracks/{index}/type = "value"\n'
                     f'tracks/{index}/path = NodePath("{node}:visible")\n'
                     f'tracks/{index}/interp = 1\ntracks/{index}/keys = {{\n'
                     '"times": PackedFloat32Array(0.0),\n'
                     '"transitions": PackedFloat32Array(1),\n"update": 1,\n'
                     f'"values": [{str(visible).lower()}]\n}}\n')
            assert body.count(track) == 1, 'Missing or changed sprite visibility selection'
            body = body.replace(track, '', 1)
        if north:
            replacements = [
                ('length = 3.0\n', 'length = 1.2\n'),
                ('step = 0.5\n', 'step = 0.2\n'),
                ('NodePath("NorthIdleSprite2D:frame")', 'NodePath("Sprite2D:frame")'),
                ('PackedFloat32Array(0.0, 0.5, 1.0, 1.5, 2.0, 2.5)',
                 'PackedFloat32Array(0.0, 0.2, 0.4, 0.6, 0.8, 1.0)'),
                ('"values": [0, 1, 2, 3, 4, 5]', '"values": [36, 37, 38, 39, 40, 41]'),
            ]
            for before, after in replacements:
                assert body.count(before) == 1, 'Unexpected north-idle frame/timing track'
                body = body.replace(before, after, 1)
        return header + body

    text, count = re.subn(r'(\[sub_resource type="Animation"[^\n]+\]\n)'
                          r'(.*?)(?=\[sub_resource)', restore_clip, text, flags=re.S)
    assert count == 9, 'Expected RESET and eight directional clips'
    assert 'NorthIdleSprite2D' not in text
    return text.encode('utf-8')


def verified_north_idle_paths():
    """Admit four exact production paths only after checking their contents."""
    art = 'assets/characters/dave/dave_idle_north_v1'
    hashes = {
        art + '.png': '74983d4f94314f25065ddf53e421e170fd6909aa09b5c1c03b52a302bcab619a',
        art + '.json': '34bcf0c0225dc2a3d50abcba5d670c8be5cdc2319518f9e7f483810004354943',
        art + '.png.import': 'b3081a3bd42c60251d1c3941344ece4865ef4a19006737b69b57603bf24787b9',
    }
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if not path.endswith('.png'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == digest, path
    scene = 'scenes/player/dave.tscn'
    original = git_blob('8edb00937beb8842ae9a50a30394045d033841aa', scene)
    assert without_north_idle(scene, without_south_idle(scene, (ROOT / scene).read_bytes())) == original.replace(b'\r\n', b'\n')
    return set(hashes) | {scene}
