"""Exact PR #104 candidates projected to immutable PR #103 for older guards.

No directory exemptions, historical rebaseline or native execution permissions.
"""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
ACTIVATION_BASE = '63318e464898b8ecf4596216f9577cd64e72dbcc'
ACTIVATION_INPUT_SHA256 = {
    'scenes/world/planet_exterior.gd': 'd48dbefa96cf319b538432b8ed46f8653b0b674374119ee16ee204405df2f6f9',
    'scenes/world/terrain_chunk.gd': '531632bba6a5f2463dffa21a818d9c468409f4c1edb6a275528a2c04d3ca388e',
    'scenes/world/planet_exterior.tscn': 'bb682c92f4feb70295204159a20e87c6cab55fe473114703156c17ab0fdcb3fb',
    'scenes/world/illustrated_terrain_tint.gdshader': '3d9f68df53176c56006773c3921571c871b4c0f452e1899fa79c6ff9f8d09e62',
}
ACTIVATION_TEST_SHA256 = {
    'tests/static_weathered_earth_test.py': '7d1995fbeaf84f6f84e3f2140284fd9f8e44a0cb1e621c113173c6df09173b84',
    'tests/static_low_green_ground_test.py': 'e1816be70000804f10324d7867e29cf9eef65f4c587a64c0be8088097b85e499',
    'tests/static_illustrated_terrain_presenter_test.py': '54aae0a6913f43e809e08f73cd7d49a357bcc75e9e6e0d5104cc2a74bc8545d7',
    'tests/static_native_terrain_47_test.py': 'd6774732c78859c855a9aa45803278f86140a9b85400eeaabce694812c248643',
}


def verify_activation_input(path, raw):
    if path not in ACTIVATION_INPUT_SHA256:
        raise AssertionError('Unapproved exterior activation path: ' + path)
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != ACTIVATION_INPUT_SHA256[path]:
        raise AssertionError('Modified exterior activation input: ' + path)


def historical_activation_bytes(path, raw):
    pins = ACTIVATION_INPUT_SHA256 | ACTIVATION_TEST_SHA256
    if path not in pins:
        return raw
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != pins[path]:
        raise AssertionError('Unreviewed PR #104 bytes: ' + path)
    # A new production shader has no historical representation; never project it.
    if path == 'scenes/world/illustrated_terrain_tint.gdshader':
        return raw
    return subprocess.check_output(['git', 'show', f'{ACTIVATION_BASE}:{path}'], cwd=ROOT)
