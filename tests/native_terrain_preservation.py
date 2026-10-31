"""Exact PR #98 projections for older static guards; no execution permissions."""
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
REVIEWED_HEAD = '56e2990fb8866b36f87d49d746e0cf7b9f9062e2'
BASE_ATTRIBUTES_SHA256 = 'acb53bcce3ee93874e9fa9a6bb9c26b9f98ce459e4db49071bcf7b667061804e'
MAPPING_ATTRIBUTES_SHA256 = 'cf52b95e79821eb811cfdaff290b5c9bd93da571fbb776b8b809757b64b99e0d'
MAPPING_ATTRIBUTES = (
    'docs/experiments/native_terrain_47_96/tlwh_47_pattern_mapping.csv -text whitespace=cr-at-eol\n'
    'docs/experiments/native_terrain_47_96/tlwh_47_pattern_mapping.md -text\n'
)
TERRAIN_INPUT_SHA256 = {
    'assets/experiments/native_terrain_47_96/experimental_47_patterns.png':
        'ecc7c6fbdfd1a141753420be800b5443b73eb7d91a068626d634433e3611a1f3',
    'assets/experiments/native_terrain_47_96/experimental_match_corners_and_sides.tres':
        'b9eedbd2c94843381a977c921aacdedc55ffcf8aeba241ef0862d56d6c98dc50',
    'scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn':
        '3c251d7066a7d3f66d62f6d1f4018ca6edf431eec139e8177076df6725a052b3',
}
# Filled from the precise diagnostic corrections after their implementation.
# Older whole-tree guards still compare their reviewed pre-correction bytes.
TEST_UPDATE_SHA256 = {'tests/static_musing_ui_test.py': '59ee7b549f1a756ffea216ad8eb0433ce157b92f2b4cd5f7cd48d75fa11663d8', 'tests/static_v2_production_host_test.py': '64655f154435b7cec2e652dd5f2c0e20c0ea181be1ac108e5fd6a70612943d5e'}


def historical_mapping_attributes(text):
    digest = hashlib.sha256(text.encode('utf-8')).hexdigest()
    if digest == BASE_ATTRIBUTES_SHA256:
        return text
    if digest != MAPPING_ATTRIBUTES_SHA256 or text.count(MAPPING_ATTRIBUTES) != 1:
        raise AssertionError('Unreviewed mapping/font attribute bytes')
    historical = text.replace(MAPPING_ATTRIBUTES, '', 1)
    assert hashlib.sha256(historical.encode('utf-8')).hexdigest() == BASE_ATTRIBUTES_SHA256
    return historical


def verify_terrain_input(path, raw):
    if path not in TERRAIN_INPUT_SHA256:
        raise AssertionError(f'Unapproved experimental path: {path}')
    if not path.endswith('.png'):
        raw = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(raw).hexdigest() != TERRAIN_INPUT_SHA256[path]:
        raise AssertionError(f'Modified experimental input: {path}')


def historical_test_bytes(path, raw):
    """Restore only two fully pinned test corrections, never owner resources."""
    if path not in TEST_UPDATE_SHA256:
        return raw
    raw = raw.replace(b'\r\n', b'\n')
    before = subprocess.check_output(['git', 'show', f'{REVIEWED_HEAD}:{path}'], cwd=ROOT).replace(b'\r\n', b'\n')
    if raw == before:
        return raw
    if hashlib.sha256(raw).hexdigest() != TEST_UPDATE_SHA256[path]:
        raise AssertionError(f'Unreviewed preservation test correction: {path}')
    return before
