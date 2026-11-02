"""Immutable artwork and sealed historical input checks; no current-source projection."""
from functools import lru_cache

import hashlib

from pathlib import Path

import subprocess

ROOT = Path(__file__).resolve().parents[1]

SEALED_REVIEW_HEAD = '4a364481e5eba90bba0d88b2518a8fce004dc979'

def normalized(path, raw):
    return raw if path.endswith(('.png', '.wav')) else raw.replace(b'\r\n', b'\n')

@lru_cache(maxsize=None)
def git_blob(ref, path):
    # Read committed objects only; never check out, stage or execute them.
    return subprocess.check_output(['git', 'show', f'{ref}:{path}'], cwd=ROOT)

def verify_fingerprint(path, raw, digest, size=None):
    raw = normalized(path, raw)
    if hashlib.sha256(raw).hexdigest() != digest or (size is not None and len(raw) != size):
        raise AssertionError('Changed preserved input: ' + path)

def sealed_input(path, record):
    raw = git_blob(SEALED_REVIEW_HEAD, path)
    verify_fingerprint(path, raw, record['sha256'], record['bytes'])
    return normalized(path, raw)

ARTWORK_SHA256 = {'assets/audio/exterior_hatch/hatch_open.wav': '20fe5cda88b672702f869921ad93a4c55f0906851b39142244a712ad13f13ea2',
 'assets/audio/exterior_hatch/hatch_close.wav': '17dee920be23e8d96848124ee8a3fbab4e9b3bca6895d929df840e35ae450b6f',
 'assets/environment/exterior/hatch_v2/door_leaf_opaque_v2.png': '7cccb9390beff971abd9e0f1c74455a35cf5b4cd05844f37887542ccea067e10',
 'assets/environment/exterior/hatch_v2/recess_backing_black_light.png': '80aa066edd98fae9eb5392ee79bb061bd82c80d48dc41e854e7c31141a3872c6',
 'assets/environment/exterior/crashed_exploration_ship_approved.png': '80ae633c36242c1effdcebea38dc05cfef8eb586ca9ef3103f6b02be91564e5b',
 'assets/environment/exterior/crashed_ship_contact_shadow_prototype.png': '1cd8111595e11d8beb527f538188f38f8517f1d3365633c013b9a137ca601777'}
