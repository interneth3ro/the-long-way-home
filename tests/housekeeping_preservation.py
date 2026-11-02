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


def verify(path, raw, entry):
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
