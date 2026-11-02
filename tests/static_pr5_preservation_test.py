"""Bounded data-only historical preservation checks; never execute archived code."""
import ast
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import struct
import subprocess
import unittest
import zipfile
import zlib

import housekeeping_preservation as housekeeping

ROOT = Path(__file__).resolve().parents[1]
RECORD = 'docs/experiments/repository_housekeeping_stage2d.json'
RECORD_SHA256 = '8b97ca029ef33a2c5380b1d6b643fb7211336dd8712409c28d680ec095f0166b'
ABSOLUTE = re.compile(r'(?<![A-Za-z0-9_])[A-Za-z]:[\\/]|/(?:home|Users)/|\\\\[A-Za-z0-9]')
SECRET = re.compile(r'-----BEGIN .*PRIVATE KEY|\b(?:gh[pousr]_[A-Za-z0-9]{20,}'
                    r'|github_pat_[A-Za-z0-9_]{20,}|(?:AKIA|ASIA)[A-Z0-9]{16})'
                    r'|bearer\s+[A-Za-z0-9_.-]{15,}', re.I)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def record():
    raw = (ROOT / RECORD).read_bytes().replace(b'\r\n', b'\n')
    if digest(raw) != RECORD_SHA256:
        raise AssertionError('Changed Stage 2D disposition')
    return json.loads(raw)


def verify_file(entry, raw):
    if len(raw) != entry['bytes'] or digest(raw) != entry['sha256']:
        raise AssertionError('Changed historical input: ' + entry.get('path', entry.get('name', '')))


def decode_bundle(raw):
    """Resolve this small pack in memory, without Git object writes or imports."""
    assert len(raw) == 25718
    header, pack = raw.split(b'\n\n', 1)
    assert header == (b'# v2 git bundle\n3b5fecc77c88e7a9da69edcf850951cd04824748 '
                      b'refs/heads/codex/walkable-ship-foundation')
    assert pack[:4] == b'PACK' and hashlib.sha1(pack[:-20]).digest() == pack[-20:]
    version, count = struct.unpack('>II', pack[4:12])
    assert version == 2 and count == 70
    pos, total = 12, 0
    entries, by_id = {}, {}
    names = {1: 'commit', 2: 'tree', 3: 'blob', 4: 'tag'}
    for _ in range(count):
        offset = pos
        value = pack[pos]
        pos += 1
        kind, size, shift = (value >> 4) & 7, value & 15, 4
        while value & 128:
            value = pack[pos]
            pos += 1
            size |= (value & 127) << shift
            shift += 7
            assert shift <= 32
        assert size <= 1048576
        base = None
        if kind == 6:
            value = pack[pos]
            pos += 1
            distance = value & 127
            while value & 128:
                value = pack[pos]
                pos += 1
                distance = ((distance + 1) << 7) + (value & 127)
            base = offset - distance
            assert base in entries
        elif kind == 7:
            base = pack[pos:pos + 20].hex()
            pos += 20
        else:
            assert kind in names
        inflater = zlib.decompressobj()
        data = inflater.decompress(pack[pos:-20], size + 1)
        assert inflater.eof and len(data) == size
        pos += len(pack[pos:-20]) - len(inflater.unused_data)
        total += len(data)
        assert total <= 2097152
        entries[offset] = [kind, base, data, None]
    assert pos == len(pack) - 20

    def varint(data, pos):
        result, shift = 0, 0
        while True:
            value = data[pos]
            pos += 1
            result |= (value & 127) << shift
            shift += 7
            assert shift <= 32
            if not value & 128:
                return result, pos

    def resolve(offset, seen=()):
        assert offset not in seen and len(seen) < 32
        entry = entries[offset]
        if entry[3] is not None:
            return entry[3]
        kind, base, data, _ = entry
        if kind in (6, 7):
            if kind == 7:
                assert base in by_id  # Ref deltas must have an already resolved base.
                base = by_id[base]
            kind, source = resolve(base, seen + (offset,))
            size, pos = varint(data, 0)
            assert size == len(source)
            size, pos = varint(data, pos)
            assert size <= 1048576
            output = bytearray()
            while pos < len(data):
                command = data[pos]
                pos += 1
                if command & 128:
                    start, length = 0, 0
                    for bit in range(4):
                        if command & (1 << bit):
                            start |= data[pos] << (8 * bit)
                            pos += 1
                    for bit in range(3):
                        if command & (1 << (bit + 4)):
                            length |= data[pos] << (8 * bit)
                            pos += 1
                    length = length or 65536
                    assert start + length <= len(source)
                    output.extend(source[start:start + length])
                else:
                    assert command and pos + command <= len(data)
                    output.extend(data[pos:pos + command])
                    pos += command
                assert len(output) <= size
            assert len(output) == size
            data = bytes(output)
        oid = hashlib.sha1(names[kind].encode() + b' ' + str(len(data)).encode()
                           + b'\0' + data).hexdigest()
        # Delta resolution inherits the base's numeric Git type code. Convert to
        # public type names only after all recursive resolution is complete.
        entry[3] = (kind, data)
        by_id[oid] = offset
        return entry[3]

    # Resolve non-deltas first for ref-delta bases, then the remaining entries.
    for offset, entry in entries.items():
        if entry[0] in names:
            resolve(offset)
    for offset in entries:
        resolve(offset)
    assert len(by_id) == 70
    return {oid: (names[entries[offset][3][0]], entries[offset][3][1])
            for oid, offset in by_id.items()}


class PR5PreservationTest(unittest.TestCase):
    def test_delta_resolution_preserves_object_ids_and_self_contained_graph(self):
        data = record()
        raw = (ROOT / data['bundle']['path']).read_bytes()
        verify_file(data['bundle'], raw)
        objects = decode_bundle(raw)
        pending = [data['bundle']['tip']]
        reached = set()
        while pending:
            oid = pending.pop()
            if oid in reached:
                continue
            self.assertIn(oid, objects, 'Bundle requires an external object')
            kind, content = objects[oid]
            self.assertIn(kind, ('commit', 'tree', 'blob'))
            canonical = kind.encode() + b' ' + str(len(content)).encode() + b'\0' + content
            self.assertEqual(hashlib.sha1(canonical).hexdigest(), oid)
            reached.add(oid)
            if kind == 'commit':
                headers = content.split(b'\n\n', 1)[0].splitlines()
                trees = [line[5:].decode('ascii') for line in headers if line.startswith(b'tree ')]
                self.assertEqual(len(trees), 1)
                pending.extend(trees)
                pending.extend(line[7:].decode('ascii') for line in headers if line.startswith(b'parent '))
            elif kind == 'tree':
                pos = 0
                while pos < len(content):
                    end = content.index(b'\0', pos)
                    mode, name = content[pos:end].split(b' ', 1)
                    self.assertIn(mode, (b'40000', b'100644', b'100755', b'120000'))
                    self.assertTrue(name)
                    self.assertLessEqual(end + 21, len(content))
                    child = content[end + 1:end + 21].hex()
                    self.assertIn(child, objects)
                    self.assertEqual(objects[child][0], 'tree' if mode == b'40000' else 'blob')
                    pending.append(child)
                    pos = end + 21
        self.assertEqual(len(reached), 70)
        self.assertEqual(reached, set(objects), 'Bundle contains unreachable objects')

    def test_bundle_is_exact_complete_and_privacy_reviewed(self):
        data = record()
        raw = (ROOT / data['bundle']['path']).read_bytes()
        verify_file(data['bundle'], raw)
        objects = decode_bundle(raw)
        self.assertEqual(dict(Counter(kind for kind, _ in objects.values())),
                         data['bundle']['objects'])
        self.assertEqual(digest(('\n'.join(sorted(objects)) + '\n').encode()),
                         data['bundle']['object_list_sha256'])
        self.assertIn(data['bundle']['tip'], objects)
        for kind, content in objects.values():
            if kind == 'blob':
                text = content.decode('utf-8-sig')
                self.assertIsNone(ABSOLUTE.search(text))
                self.assertIsNone(SECRET.search(text))
        for changed in (raw + b'x', raw[:-1], raw[:200] + bytes([raw[200] ^ 1]) + raw[201:]):
            with self.assertRaises(AssertionError):
                decode_bundle(changed)

    def test_outputs_are_exact_safe_and_outside_active_tooling(self):
        data = record()
        self.assertEqual(len(data['outputs']), 9)
        for entry in data['outputs']:
            raw = (ROOT / entry['path']).read_bytes()
            verify_file(entry, raw)
            for bad in (raw + b'x', raw[1:]):
                with self.assertRaises(AssertionError):
                    verify_file(entry, bad)
            self.assertTrue(entry['path'].startswith('artifacts/evidence/pr5-abandoned-history/'))
            self.assertFalse(entry['path'].endswith(('.gd', '.py', '.godot')))
            if not entry['path'].endswith('.png'):
                text = raw.decode('utf-8-sig')
                self.assertIsNone(ABSOLUTE.search(text), entry['path'])
                self.assertIsNone(SECRET.search(text), entry['path'])
        self.assertTrue((ROOT / 'artifacts/.gdignore').exists())
        for directory in ('tools', 'scenes', 'tests'):
            for path in (ROOT / directory).rglob('*'):
                if path.suffix in ('.py', '.ps1', '.gd', '.tscn') and path != Path(__file__):
                    self.assertNotIn('pr5-abandoned-history', path.read_text(encoding='utf-8'))
        self.assertIsNone(ABSOLUTE.search(json.dumps(data)))
        self.assertIsNone(SECRET.search(json.dumps(data)))

    def test_original_zip_equivalence_and_explicit_exclusions(self):
        data = record()
        entries = data['zip']['entries']
        self.assertEqual(len(entries), 16)
        manifest_entry = next(e for e in entries if e['name'] == 'manifest.json')
        manifest = json.loads((ROOT / manifest_entry['preserved']['path']).read_text())
        self.assertEqual({e['archive_path']: (e['size'], e['sha256'].lower()) for e in manifest['files']},
                         {e['name']: (e['bytes'], e['sha256']) for e in entries if e['name'] != 'manifest.json'})
        path = ROOT / data['zip']['path']
        if not path.exists():
            return  # Fresh clones retain immutable identities and verified output pins.
        verify_file(data['zip'], path.read_bytes())
        with zipfile.ZipFile(path) as archive:
            self.assertEqual(set(archive.namelist()), {e['name'] for e in entries})
            for entry in entries:
                self.assertLessEqual(entry['bytes'], 36000)
                original = archive.read(entry['name'])
                verify_file(entry, original)
                if entry['disposition'].startswith('exact original'):
                    self.assertEqual(original, (ROOT / entry['preserved']['path']).read_bytes())
            self.assertEqual(archive.read('artifacts/tmp/perf_manual_initial.png'),
                             archive.read('artifacts/tmp/perf_manual_final.png'))
            source = archive.read('artifacts/tmp/performance_run_20261025.py')
            literals = re.findall(rb'(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\r\n\"\x27]+', source)
            self.assertEqual(len(literals), 2)
            for old, role in zip(literals, [b'<HISTORICAL_GODOT_EXECUTABLE>', b'<HISTORICAL_GPU_QUERY_EXECUTABLE>']):
                source = source.replace(old, role)
            runner = next(e for e in entries if e['name'].endswith('.py'))
            preserved = (ROOT / runner['preserved']['path']).read_bytes()
            self.assertEqual(source, preserved)
            self.assertEqual(digest(ast.dump(ast.parse(preserved), include_attributes=False).encode()),
                             runner['normalized_ast_sha256'])
            original_manifest = json.loads(archive.read('manifest.json'))
            original_manifest['history_bundle']['path'] = manifest['history_bundle']['path']
            for entry, sanitized in zip(original_manifest['files'], manifest['files']):
                entry['original_path'] = sanitized['original_path']
            self.assertEqual(original_manifest, {k: v for k, v in manifest.items() if k != '_stage2d'})
            source = archive.read('.godot/editor/project_metadata.cfg')
            source, count = re.subn(rb'(?<![A-Za-z0-9_])[A-Za-z]:[\\/][^\r\n\"]+',
                                    b'<HISTORICAL_GODOT_EXECUTABLE>', source)
            self.assertEqual(count, 1)
            metadata = next(e for e in entries if e['name'].endswith('project_metadata.cfg'))
            self.assertEqual(source, (ROOT / metadata['preserved']['path']).read_bytes())

    def test_historical_pins_and_policy_corruption_guards(self):
        data = record()
        for path, expected in data['historical_dependency_sha256'].items():
            raw = (ROOT / path).read_bytes()
            self.assertIn(expected, (digest(raw), digest(raw.replace(b'\r\n', b'\n'))))
            self.assertEqual(digest(subprocess.check_output(['git', 'show', data['baseline'] + ':' + path], cwd=ROOT)), expected)
        for path in housekeeping.STAGE2D_INPUT_SHA256:
            raw = (ROOT / path).read_bytes()
            before = housekeeping.stage2d_predecessor(path, raw)
            self.assertEqual(before, subprocess.check_output(['git', 'show', data['baseline'] + ':' + path], cwd=ROOT))
            for bad in (raw + b'UNAPPROVED', raw[1:], raw + raw):
                with self.assertRaises(AssertionError):
                    housekeeping.stage2c_predecessor(path, bad)
        self.assertEqual(housekeeping.stage2d_predecessor('unrelated', b'unchanged'), b'unchanged')

    def test_completion_requires_committed_preservation_before_exact_deletion(self):
        data = record()
        path = ROOT / data['deletion']['completion_record']
        if not path.exists():
            return  # Preservation commit deliberately precedes deletion and receipt.
        completed = json.loads(path.read_text())
        self.assertEqual(completed['deleted'], [data['zip'] | {'absent': True}])
        self.assertFalse((ROOT / data['zip']['path']).exists())
        self.assertEqual(completed['deleted_file_payload_bytes'], 70428)
        for entry in data['outputs'] + [data['bundle']]:
            raw = subprocess.check_output(['git', 'show', completed['preservation_commit'] + ':' + entry['path']], cwd=ROOT)
            verify_file(entry, raw)


if __name__ == '__main__':
    unittest.main()
