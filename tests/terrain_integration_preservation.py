"""Exact forward artwork substitution; immutable historical pins remain authoritative.

No engine execution, directory exemptions, import metadata or historical writes.
"""
from functools import lru_cache
import hashlib
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
BASE = 'da3d2d53b90f6a311d47bf1ab43f2a45437577b5'
OLD = 'assets/experiments/native_terrain_47_96/baked_v2/'
OFFLINE = 'assets/experiments/native_terrain_47_96/ground_refinement_full_v1/'
ACTIVE = 'assets/environment/exterior/ground_refined_v1/'
LOOKUP = 'scenes/world/terrain_assignment_lookup.gd'
ATLAS_SHA256 = {
    'baseline_94.png': '36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0',
    'interiors_bc.png': 'd8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694',
}
# Complete validation/documentation amendments, independent of old receipts.
AMENDMENTS = {
    'tests/current_preservation.py':
        'bcf7ef6eefd7e358c537e0a7c3f7c39c2d6c98d8215d211de2f8a27d38aa0d80',
    'tests/ground_art_preservation.py':
        '68f12f0d49c792d579e6c59e964475a204483b4ef163d6b20829c9edc256bb2c',
    'tests/static_terrain_resolver_test.py':
        '0a0d56e93b6b91698df00e3d0d9d08918433ece7c0e9182d8b0bf9ef872cc9a0',
    'tests/static_ground_full_atlas_test.py':
        '5fbe11db2dd032efb17929caad60292a54094c7f320e0612010e32d01c6a78b7',
    'docs/GROUND_REFINEMENT_FULL_ATLAS.md':
        '8915523353ab9f1cd401b5f916cb1954615aec9641f79363dd085a26e3098380',
    'docs/TERRAIN_RESOLVER.md':
        '1e392bbdbdd91cb771faab5469ca2679e664a2882c7a03e8ff6b2d14bc7bc504',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def lf(raw):
    return raw.replace(b'\r\n', b'\n')


@lru_cache(maxsize=None)
def original(path):
    return subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)


def read(path):
    try:
        return (ROOT/path).read_bytes()
    except OSError as error:
        raise AssertionError('Missing integration input: ' + path) from error


def expected_lookup():
    before = original(LOOKUP)
    old = (OLD + 'baked_terrain.tres').encode()
    assert before.count(old) == 1
    return before.replace(old, (ACTIVE + 'terrain.tres').encode())


def expected_tileset():
    raw = original(OLD + 'baked_terrain.tres')
    for name in ATLAS_SHA256:
        assert raw.count((OLD + name).encode()) == 1
        raw = raw.replace((OLD + name).encode(), (ACTIVE + name).encode())
    return raw


def verify_resource(path, raw):
    if path == LOOKUP:
        assert lf(raw) == expected_lookup(), 'Unauthorized lookup edit'
    elif path == ACTIVE + 'terrain.tres':
        assert lf(raw) == expected_tileset(), 'Unexpected TileSet difference'
    elif path in {ACTIVE + name for name in ATLAS_SHA256}:
        name = path.removeprefix(ACTIVE)
        assert digest(raw) == ATLAS_SHA256[name], 'Wrong approved atlas bytes'
        assert raw == original(OFFLINE + name) == read(OFFLINE + name), 'Changed offline atlas'
    else:
        raise AssertionError('Unapproved integration path: ' + path)


def predecessor(path, raw):
    """Accept original fixtures or exact forward changes; reject any other delta."""
    if path != LOOKUP and path not in AMENDMENTS:
        return raw
    before = original(path)
    if lf(raw) == before:
        return before
    if path == LOOKUP:
        verify_resource(path, raw)
    else:
        assert digest(lf(raw)) == AMENDMENTS[path], 'Changed integration amendment: ' + path
    return before


def verify_all():
    for path in (LOOKUP, ACTIVE + 'terrain.tres', *(ACTIVE + n for n in ATLAS_SHA256)):
        verify_resource(path, read(path))
    for path, expected in AMENDMENTS.items():
        assert digest(lf(read(path))) == expected, 'Changed integration amendment: ' + path
    # Original production resources and candidate import isolation are immutable.
    for path in (OLD + 'baked_terrain.tres', OLD + 'mapping.json',
                 *(OLD + n for n in ATLAS_SHA256), OFFLINE + '.gdignore'):
        raw = read(path)
        assert (raw if path.endswith('.png') else lf(raw)) == original(path), path


def without_integration_changes(paths):
    verify_all()  # Verify all siblings even for empty or partial path lists.
    exact = {LOOKUP, ACTIVE + 'terrain.tres', *(ACTIVE + n for n in ATLAS_SHA256), *AMENDMENTS}
    return [path for path in paths if path not in exact]


def historical_input_hashes(current):
    """Project verified working bytes to the sealed full-atlas input inventory."""
    verify_all()
    result = dict(current)
    for path, value in current.items():
        raw = read(path)
        assert digest(raw) == value, 'Changed working input during validation: ' + path
        before = predecessor(path, raw)
        if before != raw and (path == LOOKUP or path in AMENDMENTS):
            # The sealed manifest recorded this checkout's CRLF source form.
            old = original(path)
            result[path] = digest(old.replace(b'\n', b'\r\n') if b'\r\n' in raw else old)
    return result
