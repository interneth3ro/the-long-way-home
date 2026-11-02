"""Approved terrain artwork and resource integrity; no source-history admission."""
import hashlib
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
OLD = 'assets/experiments/native_terrain_47_96/baked_v2/'
OFFLINE = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/'
ACTIVE = 'assets/environment/exterior/ground_refined_v1/'
LOOKUP = 'scenes/world/terrain_assignment_lookup.gd'
ATLAS_SHA256 = {
    'baseline_94.png': '36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0',
    'interiors_bc.png': 'd8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def lf(raw):
    return raw.replace(b'\r\n', b'\n')


def read(path):
    try:
        return (ROOT/path).read_bytes()
    except OSError as error:
        raise AssertionError('Missing approved terrain input: ' + path) from error


def expected_tileset():
    raw = lf(read(OLD + 'baked_terrain.tres'))
    for name in ATLAS_SHA256:
        raw = raw.replace((OLD + name).encode(), (ACTIVE + name).encode())
    return raw


def verify_lookup(raw, tileset_path='res://' + ACTIVE + 'terrain.tres'):
    paths = re.findall(rb'^const TILESET_PATH := "([^"]+)"$', lf(raw), re.M)
    assert paths == [tileset_path.encode()], 'Wrong active TileSet path'


def verify_resource(path, raw):
    if path == LOOKUP:
        verify_lookup(raw)
    elif path == ACTIVE + 'terrain.tres':
        assert lf(raw) == expected_tileset(), 'Unexpected TileSet structure or texture path'
    elif path in {ACTIVE + name for name in ATLAS_SHA256}:
        name = path.removeprefix(ACTIVE)
        assert digest(raw) == ATLAS_SHA256[name], 'Wrong approved atlas bytes'
        assert raw == read(OFFLINE + name), 'Changed offline atlas'
    else:
        raise AssertionError('Unknown active terrain resource: ' + path)


def verify_all():
    for path in (LOOKUP, ACTIVE + 'terrain.tres', *(ACTIVE + n for n in ATLAS_SHA256)):
        verify_resource(path, read(path))
