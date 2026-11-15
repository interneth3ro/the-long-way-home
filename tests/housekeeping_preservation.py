"""Immutable Stage 2A evidence and retained metadata; no source admission."""

from functools import lru_cache
import hashlib
import importlib.util
import io
import itertools
import marshal

import json

from pathlib import Path, PurePosixPath
import re
import stat
import struct
import types

import subprocess

ROOT = Path(__file__).resolve().parents[1]

RECORD = 'docs/experiments/repository_housekeeping_stage2a.json'

RECORD_SHA256 = '18341364e959fb7f512357bbce24d2033a26660422beb2dffbf8dfc01b7bfa20'
COMPLETION = 'docs/experiments/repository_housekeeping_stage2a_cleanup.json'
COMPLETION_SHA256 = '0c8904624fa55105536488975c008fe51f102987511b2afe1acc7e4ed31cddb8'
BASELINE = '0701430b7fa29f845bffebf0475e0bb683f9ef42'
RETENTION = 'e09d643cb4ebb84e4650e57a1e7c521ac0d7c1ea'
CLEANUP = 'b0578e77d198ac08ea2f4325d6d87fa4a3069549'
MERGE = '79112574779a52a9d62094348ee00eeedafdb22f'
DELETION_GROUPS = {
    'D1': (30, 642069), 'D2': (8, 8029), 'D3': (6, 5792),
    'D4': (1961, 24211475), 'D5': (22, 8135870),
    'D6': (2, 1980), 'D8': (174, 176317),
}

@lru_cache(maxsize=1)
def _parse(raw):
    if hashlib.sha256(raw).hexdigest() != RECORD_SHA256:
        raise AssertionError('Unreviewed Stage 2A disposition')
    return json.loads(raw)

def record():
    return _parse((ROOT / RECORD).read_bytes().replace(b'\r\n', b'\n'))


def git(*arguments):
    """Read objects/index only. Missing required evidence fails, without fallback."""
    try:
        return subprocess.check_output(['git', *arguments], cwd=ROOT, stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as error:
        raise AssertionError('Missing or unreadable housekeeping Git evidence') from error


def safe_relative(path):
    assert isinstance(path, str), 'Unsafe housekeeping path'
    relative = PurePosixPath(path)
    assert (re.fullmatch(r'[A-Za-z0-9_./ ()-]+', path)
            and not relative.is_absolute() and '..' not in relative.parts
            and str(relative) == path
            and all(not part.endswith((' ', '.')) for part in relative.parts)), 'Unsafe housekeeping path'
    return relative


def verify_records(disposition_raw, completion_raw):
    data = _parse(disposition_raw.replace(b'\r\n', b'\n'))
    completion_raw = completion_raw.replace(b'\r\n', b'\n')
    assert hashlib.sha256(completion_raw).hexdigest() == COMPLETION_SHA256, 'Changed cleanup attestation'
    completion = json.loads(completion_raw)
    assert data['baseline'] == completion['baseline'] == BASELINE
    assert completion['retention_commit'] == RETENTION
    assert completion['approved_disposition'] == RECORD
    assert completion['approved_disposition_sha256'] == RECORD_SHA256
    sections = ('retained', 'deferred_publication', 'deferred_archives', 'deletions')
    for left, right in itertools.combinations(sections, 2):
        assert not set(data[left]) & set(data[right]), 'Overlapping housekeeping scope'
    for section in sections:
        for path, entry in data[section].items():
            safe_relative(path)
            assert re.fullmatch(r'[0-9a-f]{64}', entry['sha256'])
            assert isinstance(entry['bytes'], int) and entry['bytes'] >= 0
    totals = {}
    for path, entry in data['deletions'].items():
        group = entry['group']
        assert group in DELETION_GROUPS, 'Unclassified deletion'
        count, size = totals.get(group, (0, 0))
        totals[group] = (count+1, size+entry['bytes'])
        if group == 'D1':
            assert re.fullmatch(r'tests/__pycache__/[A-Za-z_]\w*\.cpython-314\.pyc', path)
    assert totals == DELETION_GROUPS
    for group, (count, size) in totals.items():
        assert completion['removed_groups'][group] == {'files': count, 'bytes': size}
    assert len(data['deletions']) == completion['disposable_files_removed'] == 2203
    assert sum(e['bytes'] for e in data['deletions'].values()) == \
        completion['disposable_file_payload_bytes_removed'] == 33181532
    assert (len(data['retained']), len(data['deferred_publication']),
            len(data['deferred_archives'])) == (278, 4, 1)
    return data


def verify_history():
    """Verify immutable attestations, not a fictional tracked-file deletion diff.

    These targets were local/untracked. Git preserves the approved inventory and
    completion statement, not their original bytes or individual unlink events.
    """
    raw = (ROOT/RECORD).read_bytes().replace(b'\r\n', b'\n')
    completed = (ROOT/COMPLETION).read_bytes().replace(b'\r\n', b'\n')
    data = verify_records(raw, completed)
    assert git('show', RETENTION+':'+RECORD) == raw
    assert git('show', CLEANUP+':'+COMPLETION) == completed
    assert git('rev-parse', RETENTION+'^').decode().strip() == BASELINE
    assert git('rev-parse', CLEANUP+'^').decode().strip() == RETENTION
    assert git('rev-list', '--parents', '-n', '1', MERGE).decode().split() == [MERGE, BASELINE, CLEANUP]
    for revision in (BASELINE, RETENTION, CLEANUP, MERGE):
        tree = set(git('ls-tree', '-r', '--name-only', revision).decode().splitlines())
        assert not tree & data['deletions'].keys(), 'Historical deletion targets unexpectedly tracked'
    ignore = git('show', RETENTION+':.gitignore')
    assert b'# Regenerable Python bytecode.\n__pycache__/\n*.pyc' in ignore
    return data


def plain_location(path):
    """Check lexical components with lstat before reading through any parent."""
    relative = safe_relative(path)
    location = ROOT
    for component in ('', *relative.parts):
        if component:
            location = location/component
        try:
            info = location.lstat()
        except FileNotFoundError:
            break
        assert not stat.S_ISLNK(info.st_mode), 'Linked housekeeping path'
        assert not getattr(info, 'st_file_attributes', 0) & getattr(stat, 'FILE_ATTRIBUTE_REPARSE_POINT', 0), \
            'Reparse housekeeping path'
    return ROOT.joinpath(*relative.parts)


def verify_cache(raw, source_path, source_raw, source_mtime, historical_sources):
    """Compare code objects without importing, executing or writing any cache.

    A stale timestamp/checked-hash cache may match committed ancestral source.
    Code masquerading as current, and unchecked-hash stale code, must reject.
    """
    assert len(raw) >= 16 and raw[:4] == importlib.util.MAGIC_NUMBER, 'Unknown cache format'
    flags = struct.unpack('<I', raw[4:8])[0]
    assert flags in (0, 1, 3), 'Invalid cache flags'
    try:
        payload = io.BytesIO(raw[16:])
        code = marshal.load(payload)
    except (EOFError, ValueError, TypeError) as error:
        raise AssertionError('Malformed Python cache') from error
    assert isinstance(code, types.CodeType) and payload.tell() == len(raw)-16, 'Invalid cache payload'
    pending = [code]
    while pending:
        item = pending.pop()
        assert Path(item.co_filename).resolve() == source_path.resolve(), 'Unrelated cache source'
        pending.extend(c for c in item.co_consts if isinstance(c, types.CodeType))
    current = compile(source_raw, code.co_filename, 'exec', dont_inherit=True, optimize=0)
    if code == current:
        return 'current'
    current_header = (raw[8:16] == importlib.util.source_hash(source_raw) if flags & 1 else
                      struct.unpack('<II', raw[8:16]) ==
                      (int(source_mtime) & 0xffffffff, len(source_raw) & 0xffffffff))
    assert not current_header and flags != 1, 'Cache disguises different code as current'
    for historical in historical_sources:
        if code == compile(historical, code.co_filename, 'exec', dont_inherit=True, optimize=0):
            return 'stale'
    raise AssertionError('Cache does not match current or committed ancestral source')


def historical_sources(path):
    # log HEAD limits candidates to committed ancestry of this exact source path.
    for revision in git('log', '--format=%H', 'HEAD', '--', path).decode().splitlines():
        if git('ls-tree', '--name-only', revision, '--', path).strip():
            yield git('show', revision+':'+path)


def verify_deletion_path(path, entry, tracked):
    assert path not in tracked, 'Tracked/staged deletion target reintroduced'
    assert record()['deletions'].get(path) == entry, 'Unlisted deletion-path exception'
    location = plain_location(path)
    try:
        info = location.lstat()
    except FileNotFoundError:
        return 'absent'
    assert entry['group'] == 'D1', 'Non-cache deletion target reintroduced'
    assert re.fullmatch(r'tests/__pycache__/[A-Za-z_]\w*\.cpython-314\.pyc', path)
    assert stat.S_ISREG(info.st_mode), 'Cache is not an ordinary file'
    assert git('check-ignore', '--', path).decode().strip() == path, 'Cache is not ignored'
    source_relative = 'tests/'+location.name.split('.cpython-')[0]+'.py'
    assert source_relative in tracked, 'Cache has no tracked source'
    source = plain_location(source_relative)
    assert stat.S_ISREG(source.lstat().st_mode), 'Cache source is not an ordinary file'
    return verify_cache(location.read_bytes(), source, source.read_bytes(), source.stat().st_mtime,
                        historical_sources(source_relative))


def verify_deletion_paths(data):
    # HEAD catches a tracked path staged for deletion; ls-files catches staged adds.
    tracked = set(git('ls-files').decode().splitlines())
    tracked.update(git('ls-tree', '-r', '--name-only', 'HEAD').decode().splitlines())
    return {path: verify_deletion_path(path, entry, tracked)
            for path, entry in data['deletions'].items()}

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
