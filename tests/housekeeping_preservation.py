"""Exact owner-authorized Stage 2A disposition; no historical pin changes."""
from functools import lru_cache
import hashlib
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/experiments/repository_housekeeping_stage2a.json'
RECORD_SHA256 = '18341364e959fb7f512357bbce24d2033a26660422beb2dffbf8dfc01b7bfa20'


@lru_cache(maxsize=1)
def _parse(raw):
    if hashlib.sha256(raw).hexdigest() != RECORD_SHA256:
        raise AssertionError('Unreviewed Stage 2A disposition')
    return json.loads(raw)


def record():
    return _parse((ROOT / RECORD).read_bytes().replace(b'\r\n', b'\n'))

# Exact forward-looking Stage 2C policy deltas; original Stage 2A pins stay intact.
STAGE2C_BASE = '79112574779a52a9d62094348ee00eeedafdb22f'
STAGE2C_INPUT_SHA256 = {'AGENTS.md': '7918ea7188d5841e348a1e64f736507b42343829b95561ee00d195a60f42f2c9', '.gitignore': 'f7a802083849f1364fe3b1576eacfd04c88c836829cba8755402bddadbe46016', 'README.md': '4509e0ff64d9e70bba9b4a3abe9beb463723fcb57255bb9656b543a238ba11bf'}


# Forward-looking Stage 2D policy projection; all historical pins stay intact.
# Only these two exact complete files may reach the unchanged older guards.
STAGE2D_BASE = 'd5f54506efeab1567dc850aa45ffa84bf194162b'
STAGE2D_INPUT_SHA256 = {
    '.gitignore': 'd774efbacb5f1b485e4889594c3da78cad52974a9da4343cf55ea7e49aa9a283',
    'README.md': '653061674a9401cdb3e0aa9558cbd09e0ec6573e32b6e36b6fc9f393efa14bca',
}


def stage2d_predecessor(path, raw):
    expected = STAGE2D_INPUT_SHA256.get(path)
    if expected and hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() == expected:
        return subprocess.check_output(['git', 'show', STAGE2D_BASE + ':' + path], cwd=ROOT)
    return raw  # Unknown bytes still reach, and must pass, the older exact guards.


def stage2c_predecessor(path, raw):
    raw = stage2d_predecessor(path, raw)
    if path not in STAGE2C_INPUT_SHA256:
        return raw
    normalized = raw.replace(b"\r\n", b"\n")
    before = subprocess.check_output(["git", "show", STAGE2C_BASE + ":" + path], cwd=ROOT)
    if normalized == before.replace(b"\r\n", b"\n"):
        return before
    if hashlib.sha256(normalized).hexdigest() == STAGE2C_INPUT_SHA256[path]:
        return before
    # Keep the older exact fixtures available to their original historical guards.
    original = subprocess.check_output(["git", "show", record()["baseline"] + ":" + path], cwd=ROOT)
    if normalized == original.replace(b"\r\n", b"\n"):
        return raw
    raise AssertionError("Changed Stage 2A input: " + path)


def verify(path, raw, entry):
    raw = stage2c_predecessor(path, raw)
    # Stage 2A retained metadata pins identify committed Git blobs. On Windows,
    # autocrlf can change their checkout representation without changing content.
    # Keep this exception inside the exact immutable receipt, not every text file.
    if (path.endswith(('.import', '.uid'))
            and record()['retained'].get(path) == entry):
        attributes = subprocess.check_output(
            ['git', 'check-attr', '-z', 'filter', 'working-tree-encoding', '--', path], cwd=ROOT)
        values = attributes.split(b'\0')[2::3]
        if values != [b'unspecified', b'unspecified']:
            raise AssertionError('Unexpected retained metadata conversion: ' + path)
        canonical = subprocess.check_output(['git', 'show', ':' + path], cwd=ROOT)
        checkout = subprocess.check_output(
            ['git', 'cat-file', '--filters', '--path=' + path, ':' + path], cwd=ROOT)
        if raw not in (canonical, checkout):
            raise AssertionError('Changed Stage 2A input: ' + path)
        raw = canonical
    if entry.get('normalize_lf'):
        raw = raw.replace(b'\r\n', b'\n')
    if hashlib.sha256(raw).hexdigest() != entry['sha256'] or len(raw) != entry['bytes']:
        raise AssertionError('Changed Stage 2A input: ' + path)


def historical_input(path, raw):
    disposition = record()
    entry = disposition['existing_changes'].get(path)
    if entry is None:
        return raw
    before = subprocess.check_output(
        ['git', 'show', disposition['baseline'] + ':' + path], cwd=ROOT)
    if raw.replace(b'\r\n', b'\n') == before.replace(b'\r\n', b'\n'):
        return before
    verify(path, raw, entry)
    return before


def without_approved_paths(paths):
    disposition = record()
    approved = (disposition['retained'] | disposition['existing_changes']
                | disposition['import_policy'] | disposition['formatting_policy'])
    remaining = []
    for path in paths:
        if path in approved:
            verify(path, (ROOT / path).read_bytes(), approved[path])
        else:
            remaining.append(path)
    return remaining
