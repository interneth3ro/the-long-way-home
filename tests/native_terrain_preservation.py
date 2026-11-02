"""Immutable original native terrain experiment identities; no checkout admission."""
import hashlib

from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


TERRAIN_INPUT_SHA256 = {
    'assets/experiments/native_terrain_47_96/experimental_47_patterns.png':
        'ecc7c6fbdfd1a141753420be800b5443b73eb7d91a068626d634433e3611a1f3',
    'assets/experiments/native_terrain_47_96/experimental_match_corners_and_sides.tres':
        'b9eedbd2c94843381a977c921aacdedc55ffcf8aeba241ef0862d56d6c98dc50',
    'scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn':
        '3c251d7066a7d3f66d62f6d1f4018ca6edf431eec139e8177076df6725a052b3',
}

def verify_terrain_input(path, raw):
    if path not in TERRAIN_INPUT_SHA256:
        raise AssertionError(f'Unapproved experimental path: {path}')
    if not path.endswith('.png'):
        raw = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(raw).hexdigest() != TERRAIN_INPUT_SHA256[path]:
        raise AssertionError(f'Modified experimental input: {path}')
