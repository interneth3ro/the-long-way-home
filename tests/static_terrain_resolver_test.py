"""Source-bound arithmetic and metadata proofs; no GDScript/Godot execution.

Only the resolver's restricted integer expressions are evaluated by Python.
Engine parsing, native API behavior and runtime integration remain unverified.
"""
import collections
import hashlib
import itertools
import json
from pathlib import Path
import re
import subprocess
import unittest
from current_preservation import without_presenter_paths, PRESENTER_INPUT_SHA256, verify_presenter_input

ROOT = Path(__file__).resolve().parents[1]
SOURCE = (ROOT / 'scenes/world/terrain_resolver.gd').read_text()
LOOKUP = (ROOT / 'scenes/world/terrain_assignment_lookup.gd').read_text()
ASSET = ROOT / 'assets/experiments/native_terrain_47_96/baked_v2'
BASE = '9f157795b3ee7737ed55787a2a4355a126af5d1e'
RESOLVER_INPUT_SHA256 = {
    'scenes/world/terrain_resolver.gd': '75db40185fbb86f394035ef442a44dd18b911ce9bc3e4ab1489f443e1b210117',
    'scenes/world/terrain_assignment_lookup.gd': '582560a0d625e6531124b90a10ffcea4b2b4d1bca8944a2c673b8b3a30cb9567',
}
BITS = ('top_left_corner', 'top_side', 'top_right_corner', 'left_side',
        'right_side', 'bottom_left_corner', 'bottom_side', 'bottom_right_corner')
OFFSETS = ((0, 0), (-1, -1), (0, -1), (1, -1), (-1, 0),
           (1, 0), (-1, 1), (0, 1), (1, 1))


def verify_resolver_input(path, raw):
    if path not in RESOLVER_INPUT_SHA256:
        raise AssertionError('Unapproved resolver input: ' + path)
    if hashlib.sha256(raw.replace(b'\r\n', b'\n')).hexdigest() != RESOLVER_INPUT_SHA256[path]:
        raise AssertionError('Modified resolver input: ' + path)


def signature(materials):
    # Bind the proof to the actual production return expression, not a second
    # hand-maintained implementation. Reject anything outside integer products.
    expression = re.search(r'return PackedInt32Array\(\[(g\[0\],.*?)\]\)', SOURCE, re.S)[1]
    assert re.fullmatch(r'[g\[\]0-8,*\s]+', expression)
    assert 'return int(material > 0)' in SOURCE
    assert 'material < 0 or material > 4' in SOURCE
    if len(materials) != 9 or any(m not in range(5) for m in materials):
        raise ValueError('invalid material samples')
    g = [int(m > 0) for m in materials]
    return tuple(eval('[' + expression + ']', {'__builtins__': {}}, {'g': g}))


def bucket(cell, seed=0):
    body = SOURCE.split('static func variation_bucket(', 1)[1].split('\n\n\n', 1)[0]
    expressions = re.findall(r'^\t(?:var value :=|value =) (.*)$', body, re.M)
    assert len(expressions) == 5
    env = {'posmod': lambda a, b: a % b, 'presentation_seed': seed,
           'HASH_MODULUS': int(re.search(r'HASH_MODULUS: int = (\d+)', SOURCE)[1]),
           'PRESENTATION_CHANNEL': int(re.search(r'PRESENTATION_CHANNEL: int = (\d+)', SOURCE)[1])}
    for expression in expressions:
        expression = expression.replace('cell.x', str(cell[0])).replace('cell.y', str(cell[1]))
        assert re.fullmatch(r'[A-Za-z_0-9 (),*+^><-]+', expression)
        env['value'] = eval(expression, {'__builtins__': {}}, env)
    assert '\treturn value % 100' in body
    return env['value'] % 100


def variant(value):
    body = SOURCE.split('static func variant_for_bucket', 1)[1].split('\n\n\n', 1)[0]
    thresholds = re.findall(r'if bucket < (\d+):\n\t\treturn "([ABC])"', body)
    assert len(thresholds) == 2 and '\treturn "C"' in body
    assert 'bucket < 0 or bucket >= 100' in body
    if not 0 <= value < 100:
        raise ValueError('invalid bucket')
    return next((name for limit, name in thresholds if value < int(limit)), 'C')


def inventory(resource, manifest):
    """Independent text-reader verifies all native records against the manifest."""
    records = {}
    sources = dict(re.findall(r'\[sub_resource type="TileSetAtlasSource" id="([^"]+)"\]\n(.*?)(?=\n\[)', resource, re.S))
    bindings = dict((name, int(index)) for index, name in
                    re.findall(r'^sources/(\d+) = SubResource\("([^"]+)"\)', resource, re.M))
    assert bindings == {'Baseline': 0, 'Interiors': 1}
    for name, body in sources.items():
        for x, y, alt in re.findall(r'^(\d+):(\d+)/(\d+) = 0$', body, re.M):
            assert alt == '0'
            prefix = re.escape(f'{x}:{y}/{alt}/')
            props = dict(re.findall('^' + prefix + r'([^\n=]+) = ([^\n]+)$', body, re.M))
            assert props['terrain_set'] == '0'
            sig = (int(props['terrain']), *(int(props['terrains_peering_bit/' + b]) for b in BITS))
            records[bindings[name], (int(x), int(y)), int(alt)] = sig
    assert len(records) == 98
    result = {}
    seen = set()
    for group, sid in (('baseline', 0), ('interiors', 1)):
        assert len(manifest[group]) == (94 if sid == 0 else 4)
        for entry in manifest[group]:
            assert all(v in (0, 1) for v in entry['signature'])
            assert len(entry['signature']) == 9
            assert all(isinstance(v, (int, float)) and int(v) == v and 0 <= v <= 2147483647
                       for v in entry['atlas'])
            address = sid, tuple(entry['atlas']), 0
            sig = tuple(entry['signature'])
            assert address not in seen and records[address] == sig
            seen.add(address)
            key = sig, entry.get('variant', 'A')
            assert key not in result
            result[key] = address
    assert seen == set(records)
    return result


class TerrainResolverStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.resource = (ASSET / 'baked_terrain.tres').read_text()
        cls.manifest = json.loads((ASSET / 'mapping.json').read_text())
        cls.tiles = inventory(cls.resource, cls.manifest)

    def test_classification_and_all_green_neighborhoods(self):
        reached = set()
        for neighbors in itertools.product((0, 1), repeat=8):
            sig = signature((1, *neighbors))
            reached.add(sig)
            self.assertIn((sig, 'A'), self.tiles)
            for green in range(1, 5):
                self.assertEqual(signature([green] + [green if n else 0 for n in neighbors]), sig)
        self.assertEqual(len(reached), 47)
        self.assertEqual({sig for sig, v in self.tiles if sig[0] == 1 and v == 'A'}, reached)
        for invalid in (-1, 5):
            with self.assertRaises(ValueError):
                signature([invalid] * 9)

    def test_earth_and_native_order(self):
        for n in itertools.product((0, 1), repeat=8):
            self.assertEqual(signature((0, *n)), (0,) * 9)
        self.assertIn(((0,) * 9, 'A'), self.tiles)
        # Independent geometric oracle: every vertex uses precisely its four
        # incident centers, every side its two. Exercises every binary 3x3 grid.
        for samples in itertools.product((0, 1), repeat=9):
            grid = dict(zip(OFFSETS, samples))
            expected = [samples[0]]
            for dx, dy in OFFSETS[1:]:
                incident = itertools.product((0, dx) if dx else (0,), (0, dy) if dy else (0,))
                expected.append(int(all(grid[p] for p in incident)))
            self.assertEqual(signature(samples), tuple(expected))
        names = re.findall(r'TileSet.CELL_NEIGHBOR_([A-Z_]+)', LOOKUP)
        self.assertEqual([n.lower() for n in names], list(BITS))

    def test_exhaustive_shared_edges_and_corners(self):
        # Adjacent 3x3 halos have a 4x3 union: all 4096 binary worlds,
        # both axes, full three-peer boundary (including both endpoints).
        for bits in itertools.product((0, 1), repeat=12):
            world = dict(zip(itertools.product(range(-1, 3), range(-1, 2)), bits))
            def at(x, y):
                return signature([world[x + dx, y + dy] for dx, dy in OFFSETS])
            a, b = at(0, 0), at(1, 0)
            self.assertEqual(tuple(a[i] for i in (3, 5, 8)), tuple(b[i] for i in (1, 4, 6)))
            transposed = {(y, x): v for (x, y), v in world.items()}
            a = signature([transposed[dx, dy] for dx, dy in OFFSETS])
            b = signature([transposed[dx, 1 + dy] for dx, dy in OFFSETS])
            self.assertEqual(tuple(a[i] for i in (6, 7, 8)), tuple(b[i] for i in (1, 2, 3)))

    def test_chunk_order_negative_halos_and_regeneration(self):
        # Coordinate-only synthetic material field; no production sampler run.
        def material(x, y):
            return ((x * 17 + y * 31) ^ (x // 3)) % 5
        def chunk(cx, cy, seed):
            halo = {(x, y): material(x, y) for x in range(cx*32-1, cx*32+33)
                    for y in range(cy*32-1, cy*32+33)}
            result = {}
            for x in range(cx*32, cx*32+32):
                for y in range(cy*32, cy*32+32):
                    sig = signature([halo[x+dx, y+dy] for dx, dy in OFFSETS])
                    v = variant(bucket((x, y), seed)) if len(set(sig)) == 1 else 'A'
                    result[x, y] = (sig, self.tiles[sig, v])
            return result
        coords = [(-1, -1), (0, -1), (-1, 0), (0, 0), (1, 0)]
        forward = {c: chunk(*c, 19) for c in coords}
        reverse = {c: chunk(*c, 19) for c in reversed(coords)}
        self.assertEqual(forward, reverse)
        for c in coords:
            self.assertEqual(forward[c], chunk(*c, 19))  # discarded/rebuilt, no retained neighbors
        merged = {p: value for cells in forward.values() for p, value in cells.items()}
        for (x, y), (a, _) in merged.items():
            if (x+1, y) in merged:
                b = merged[x+1, y][0]
                self.assertEqual((a[3], a[5], a[8]), (b[1], b[4], b[6]))
            if (x, y+1) in merged:
                b = merged[x, y+1][0]
                self.assertEqual(a[6:9], b[1:4])

    def test_variant_thresholds_seeds_and_representative_distribution(self):
        self.assertEqual(collections.Counter(variant(i) for i in range(100)), {'A': 60, 'B': 25, 'C': 15})
        self.assertEqual([variant(i) for i in (0, 59, 60, 84, 85, 99)], ['A', 'A', 'B', 'B', 'C', 'C'])
        for c in (0, 1):
            self.assertEqual({v for sig, v in self.tiles if sig == (c,)*9}, {'A', 'B', 'C'})
        counts = collections.Counter(variant(bucket((x, y), 0)) for x in range(-50, 50) for y in range(-50, 50))
        for v, fraction in (('A', .60), ('B', .25), ('C', .15)):
            self.assertLess(abs(counts[v]/10000 - fraction), .025)
        changed = 0
        for cell in ((-33, -1), (-1, 0), (0, 0), (31, 32), (900, -800)):
            self.assertEqual(bucket(cell, -97), bucket(cell, -97))
            changed += variant(bucket(cell, 0)) != variant(bucket(cell, 1))
            for center in (0, 1):
                sig = signature([center]*9)
                for seed in (0, 1):
                    self.assertEqual(sig, (center,)*9)
                    self.assertIn((sig, variant(bucket(cell, seed))), self.tiles)
        self.assertGreater(changed, 0)
        self.assertEqual([bucket(c, s) for c, s in [((0, 0), 0), ((-33, -1), -97), ((31, 32), 19)]],
                         [20, 34, 51])

    def test_failure_guards_and_lookup_metadata_binding(self):
        for guard in ('rule_version != RULE_VERSION', 'materials.size() != 9',
                      'if terrain < 0:', 'return PackedInt32Array()', 'if resolved.is_empty() or lookup == null:'):
            self.assertIn(guard, SOURCE)
        for guard in ('record.signature != sig or record.alternative_id != 0',
                      'not _assignments.has(key)', '_assignments.clear()',
                      'Duplicate signature/variant', 'Duplicate or missing native assignment',
                      'source.get_tile_data(atlas, alternative)', 'data.get_terrain_peering_bit(peer)',
                      'return _assignments[key].duplicate(true)'):
            self.assertIn(guard, LOOKUP)
        with self.assertRaises(AssertionError):
            inventory(self.resource.replace('0:0/0/terrain = 0', '0:0/0/terrain = 1', 1), self.manifest)
        for mutation in ('missing', 'duplicate', 'signature', 'overflow_signature', 'overflow_coordinate'):
            bad = json.loads(json.dumps(self.manifest))
            if mutation == 'missing': bad['baseline'].pop()
            if mutation == 'duplicate': bad['baseline'][1] = bad['baseline'][0]
            if mutation == 'signature': bad['baseline'][0]['signature'][1] ^= 1
            if mutation == 'overflow_signature': bad['baseline'][0]['signature'][0] = 4294967296
            if mutation == 'overflow_coordinate': bad['baseline'][0]['atlas'][0] = 4294967296
            with self.assertRaises(AssertionError): inventory(self.resource, bad)
        self.assertNotIn(((1, 1, 0, 0, 0, 0, 0, 0, 0), 'A'), self.tiles)
        self.assertIn('for terrain in raw_sig:', LOOKUP)
        self.assertIn('coordinate < 0 or coordinate > 2147483647', LOOKUP)
        self.assertIn('if solid:\n\t\tvariant = variant_for_bucket(variation_bucket(cell, presentation_seed))', SOURCE)
        self.assertIn('return lookup.assignment(resolved, variant)', SOURCE)
        for text in (SOURCE, LOOKUP):
            for forbidden in ('randf(', 'randi(', 'randomize(', 'RandomNumberGenerator',
                              'set_cells_terrain_connect', 'get_cell_', 'PlanetGenerator.new'):
                self.assertNotIn(forbidden, text)

    def test_production_and_approved_assets_preserved(self):
        # Entire pre-existing simulation/presentation/resource/artwork trees.
        paths = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--',
                                         'assets', 'scenes', 'shaders', 'inventory', 'construction',
                                         'dialogue', 'objectives', 'project.godot', 'tools'], cwd=ROOT).decode().splitlines()
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--'], cwd=ROOT).decode().splitlines()
        self.assertFalse(set(paths) & set(without_presenter_paths(changed)), 'Pre-existing production/asset/tool files changed')
        for path in ROOT.glob('scenes/**/*.gd'):
            if path.name not in ('terrain_resolver.gd', 'terrain_assignment_lookup.gd'):
                from current_preservation import FIXTURE_INPUT_SHA256, verify_fixture_input
                relative = path.relative_to(ROOT).as_posix()
                if relative in PRESENTER_INPUT_SHA256:
                    verify_presenter_input(relative, path.read_bytes())
                    continue
                if relative in FIXTURE_INPUT_SHA256:
                    verify_fixture_input(relative, path.read_bytes())
                    continue
                self.assertNotIn('TerrainResolver', path.read_text())
                self.assertNotIn('TerrainAssignmentLookup', path.read_text())

    def test_exact_new_script_exception_rejects_tampering_and_other_paths(self):
        self.assertEqual(len(RESOLVER_INPUT_SHA256), 2)
        for path in RESOLVER_INPUT_SHA256:
            raw = (ROOT/path).read_bytes()
            verify_resolver_input(path, raw)
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.assertRaises(AssertionError): verify_resolver_input(path, bad)
            with self.assertRaises(AssertionError): verify_resolver_input(path + '.other', raw)
        for path in ('scenes/world/planet_generator.gd', 'scenes/world/terrain_chunk.gd',
                     'tools/run-local-tests.ps1', 'assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres'):
            with self.assertRaises(AssertionError): verify_resolver_input(path, (ROOT/path).read_bytes())


if __name__ == '__main__':
    unittest.main()
