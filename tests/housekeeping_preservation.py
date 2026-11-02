"""Immutable Stage 2A evidence and retained metadata; no source admission."""

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

def verify(path, raw, entry):
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
