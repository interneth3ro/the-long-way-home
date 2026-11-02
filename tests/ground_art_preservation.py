"""Saved ground artwork/receipt integrity and exact historical text checkout forms."""
import hashlib

import json

from pathlib import Path

import subprocess

ROOT = Path(__file__).resolve().parents[1]

RECORD = 'docs/experiments/ground_art_validation_admission.json'

RECORD_SHA256_LF = '3f156da362bae9faf24b272034a175801c0c299154fdddc45857ef30b3d0b991'

START = '5d4f502928ea964e9d8b8b71ded87c0888b5aaaf'

VALIDATION_PATHS = frozenset({
    'tests/current_preservation.py', 'tests/static_ground_refinement_test.py',
    'tests/static_ground_softness_test.py', 'tests/static_stage2e_preservation_test.py',
    'tests/static_housekeeping_test.py',
})

PORTABLE = {
    'assets/experiments/native_terrain_47_96/ground_softness_comparison_v1/.gitattributes':
        ('b7358186fda7d5636fd1e7799348d31cd0bef2f1', '4bb99cf85ca1ac6e6c408c78d23cfa5d77b906cb'),
    'docs/experiments/repository_housekeeping_stage2e_audit.md':
        ('1a88d641b1c5bfa0929ec5f200f40c48865f95ea', '979a7cbf5dcdc4a257d73dfdb43447fa31f81bed'),
}

def require(condition, message):
    if not condition:
        raise AssertionError(message)

def sha256(raw):
    return hashlib.sha256(raw).hexdigest()

def blob_id(raw):
    return hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\0'+raw).hexdigest()

def read_working(path):
    try:
        return (ROOT/path).read_bytes()
    except OSError as error:
        raise AssertionError('Missing preserved file: '+path) from error

def git_bytes(ref, path):
    return subprocess.check_output(['git', 'show', ref+':'+path], cwd=ROOT)

def exact_checkout(raw, lf, path):
    require(b'\r' not in lf, 'Expected LF Git bytes: '+path)
    require(raw in (lf, lf.replace(b'\n', b'\r\n')), 'Changed content or mixed checkout endings: '+path)
    return lf

def historical_checkout(path, raw=None):
    """Preserve Git identity and permit only its two exact text checkout forms."""
    require(path in PORTABLE, 'Unapproved portability path: '+path)
    revision, expected_blob = PORTABLE[path]
    original = git_bytes(revision, path)
    require(blob_id(original) == expected_blob, 'Changed historical Git identity: '+path)
    require(git_bytes('HEAD', path) == original, 'Changed HEAD identity: '+path)
    require(git_bytes('', path) == original, 'Changed index identity: '+path)
    return exact_checkout(read_working(path) if raw is None else raw, original, path)

def record():
    raw = read_working(RECORD)
    lf = raw.replace(b'\r\n', b'\n')
    exact_checkout(raw, lf, RECORD)
    require(sha256(lf) == RECORD_SHA256_LF, 'Changed ground-art admission record')
    data = json.loads(lf)
    require(len(data['admitted']) == 37 and set(data['validation_amendments']) == VALIDATION_PATHS,
            'Changed exact ground-art admission inventory')
    return data

def verify_identity(path, raw, entry):
    # The existing candidate README has a reviewed mixed-ending saved form.
    # Preserve those exact bytes as well as its Git checkout representation;
    # this is an individually pinned identity, not mixed-ending normalization.
    if 'saved_sha256' in entry and sha256(raw) == entry['saved_sha256']:
        return
    if entry['format'] == 'binary':
        canonical = raw
    else:
        canonical = raw.replace(b'\r\n', b'\n')
        exact_checkout(raw, canonical, path)
    require(sha256(canonical) == entry['sha256'], 'Changed reviewed ground-art input: '+path)

def verify_admitted(path, raw=None):
    pins = record()['admitted']
    require(path in pins, 'Unapproved ground-art path: '+path)
    entry = pins[path]
    if 'source_blob' in entry:
        original = git_bytes(START, path)
        require(blob_id(original) == entry['source_blob'], 'Changed admitted historical Git identity: '+path)
        verify_identity(path, original, entry)
    verify_identity(path, read_working(path) if raw is None else raw, entry)
