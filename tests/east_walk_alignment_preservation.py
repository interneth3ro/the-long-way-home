"""Reverse only the approved east/west walking delta for historical checks.

static_east_walk_alignment_test checks the live six-sprite scene. Historical
hash pins remain unchanged; unrelated scene edits remain detectable.
"""
import hashlib
import re

from current_preservation import ROOT, git_blob


BASE = '8fc1ddca8cc4e0cd91a09fc386269d618a0c3663'
ART = 'assets/characters/dave/dave_walk_east_aligned_v1'


def without_east_walk_alignment(path, raw):
    if path != 'scenes/player/dave.tscn':
        return raw
    text = raw.decode('utf-8').replace('\r\n', '\n')

    def replace_once(before, after):
        nonlocal text
        assert text.count(before) == 1, 'Unexpected east-walk alignment scene structure'
        text = text.replace(before, after, 1)

    replace_once('[gd_scene load_steps=24 format=3]', '[gd_scene load_steps=23 format=3]')
    replace_once(f'[ext_resource type="Texture2D" path="res://{ART}.png" id="11_east_walk"]\n', '')
    replace_once('''[node name="EastWalkSprite2D" type="Sprite2D" parent="Visual"]
visible = false
texture_filter = 1
scale = Vector2(0.71424418545, 0.71424418545)
texture = ExtResource("11_east_walk")
centered = false
offset = Vector2(-94, -174)
hframes = 6

''', '')

    def restore_clip(match):
        header, body = match[1], match[2]
        horizontal = any(f'id="Animation_walk_{direction}"' in header for direction in ('east', 'west'))
        west = 'id="Animation_walk_west"' in header
        for index, prop, value in [(8, 'visible', horizontal), (9, 'flip_h', west)]:
            track = (f'tracks/{index}/type = "value"\n'
                     f'tracks/{index}/path = NodePath("EastWalkSprite2D:{prop}")\n'
                     f'tracks/{index}/interp = 1\ntracks/{index}/keys = {{\n'
                     '"times": PackedFloat32Array(0.0),\n'
                     '"transitions": PackedFloat32Array(1),\n"update": 1,\n'
                     f'"values": [{str(value).lower()}]\n}}\n')
            assert body.count(track) == 1, 'Missing or changed east-walk visibility/flip track'
            body = body.replace(track, '', 1)
        if horizontal:
            for before, after in [
                ('NodePath("EastWalkSprite2D:frame")', 'NodePath("Sprite2D:frame")'),
                ('"values": [0, 1, 2, 3, 4, 5]', '"values": [30, 31, 32, 33, 34, 35]'),
            ]:
                assert body.count(before) == 1, 'Unexpected east-walk frame track'
                body = body.replace(before, after, 1)
            for index, value in [(1, west), (2, True)]:
                prefix, tail = body.split(f'tracks/{index}/type = "value"\n')
                track, tail = tail.split(f'tracks/{index + 1}/type = "value"\n')
                assert track.count('"values": [false]') == 1
                track = track.replace('"values": [false]', f'"values": [{str(value).lower()}]', 1)
                body = prefix + f'tracks/{index}/type = "value"\n' + track + f'tracks/{index + 1}/type = "value"\n' + tail
        return header + body

    text, count = re.subn(r'(\[sub_resource type="Animation"[^\n]+\]\n)'
                          r'(.*?)(?=\[sub_resource)', restore_clip, text, flags=re.S)
    assert count == 9, 'Expected RESET and eight directional clips'
    assert 'EastWalkSprite2D' not in text
    return text.encode('utf-8')


def verified_east_walk_alignment_paths():
    """Admit four exact production paths only after checking their contents."""
    hashes = {
        ART + '.png': '6d00dfb65a183512afb1fb383dfed7a9e023b55aa5279dd65e70519e27bc0353',
        ART + '.json': '95475aba99babe52f0eb0e8a28640ffb6a90b2a21f4ed01e4b52ad30f622ed3f',
        ART + '.png.import': '56f95c3994c7377a75f1b2b15b39285d542de38a5f832e1b706bdb0eaa39b5c0',
    }
    for path, digest in hashes.items():
        raw = (ROOT / path).read_bytes()
        if not path.endswith('.png'):
            raw = raw.replace(b'\r\n', b'\n')
        assert hashlib.sha256(raw).hexdigest() == digest, path
    scene = 'scenes/player/dave.tscn'
    original = git_blob(BASE, scene).replace(b'\r\n', b'\n')
    assert without_east_walk_alignment(scene, (ROOT / scene).read_bytes()) == original
    return set(hashes) | {scene}
