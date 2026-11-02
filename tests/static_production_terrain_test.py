"""Source-bound Python models and text inspection only; never execute Godot."""
import itertools
import json
import math
from pathlib import Path
import re
import subprocess
import unittest

from current_preservation import (FIXTURE_INPUT_SHA256, verify_fixture_input,
    PRESENTER_INPUT_SHA256, historical_presenter_bytes, historical_source, without_presenter_paths)
from static_terrain_resolver_test import signature, bucket, variant, inventory, OFFSETS
from static_weathered_earth_test import earth_tint

ROOT = Path(__file__).resolve().parents[1]
BASE = '74f4ecb3f5a831bbeed4436ec2324441c60b8c77'
DIRECTORY = 'scenes/experiments/production_terrain/'
SOURCE = historical_source(DIRECTORY + 'fixture.gd')
SCENE = historical_source(DIRECTORY + 'fixture.tscn')
SHADER = (ROOT / DIRECTORY / 'tint.gdshader').read_text()
CHUNKS = ((-1, -1), (0, -1), (-1, 0), (0, 0))
REGIONS = json.loads(re.search(r'const REGIONS := (\[.*?\])\n\n', SOURCE, re.S)[1])
ASSET = ROOT / 'assets/experiments/native_terrain_47_96/baked_v2'
TILES = inventory((ASSET / 'baked_terrain.tres').read_text(), json.loads((ASSET / 'mapping.json').read_text()))


def body(name):
    return SOURCE.split('func ' + name + '(', 1)[1].split('\n\n\n', 1)[0]


def historical_stage_input(path, raw, digest):
    """Check immutable #102 inventory; never authorize current staging bytes."""
    import hashlib
    import production_terrain_preservation as preservation
    old = subprocess.check_output(['git', 'show', f'{preservation.PRESENTER_BASE}:{path}'], cwd=ROOT)
    if Path(path).suffix in ('.gd', '.tscn', '.tres', '.gdshader', '.json'):
        projected = historical_presenter_bytes(path, raw).replace(b'\r\n', b'\n')
        old = old.replace(b'\r\n', b'\n')
        assert projected == old, path
        assert digest in {hashlib.sha256(old).hexdigest(),
                          hashlib.sha256(old.replace(b'\n', b'\r\n')).hexdigest()}, path
    else:
        assert hashlib.sha256(raw).hexdigest() == digest, path


def material(x, y):
    # Evaluate only the fixture's restricted coordinate predicate; rectangle
    # inclusion below is an independent half-open integer geometry oracle.
    predicate = re.search(r'if (.+):', body('sample_material'))[1]
    assert re.fullmatch(r'[a-z0-9 .<>=+(),_-]+', predicate)
    predicate = predicate.replace('cell.x', 'x').replace('cell.y', 'y')
    result = int(eval(predicate, {'__builtins__': {}}, {'x': x, 'y': y, 'posmod': lambda a, b: a % b}))
    for rx, ry, width, height, terrain in REGIONS:
        if rx <= x < rx + width and ry <= y < ry + height:
            result = terrain
    return result


def chunk(coordinate):
    cx, cy = coordinate
    halo = {(x, y): material(x, y) for x in range(cx*32-1, cx*32+33)
            for y in range(cy*32-1, cy*32+33)}
    result = {}
    for x in range(cx*32, cx*32+32):
        for y in range(cy*32, cy*32+32):
            sig = signature([halo[x+dx, y+dy] for dx, dy in OFFSETS])
            v = variant(bucket((x, y), 19)) if len(set(sig)) == 1 else 'A'
            result[x, y] = sig, v, TILES[sig, v]
    return result


class ProductionTerrainStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.chunks = {c: chunk(c) for c in CHUNKS}
        cls.cells = {p: a for cells in cls.chunks.values() for p, a in cells.items()}

    def test_real_resolver_metadata_lookup_and_halo_contract(self):
        self.assertIn('TerrainAssignmentLookup.new()', SOURCE)
        self.assertIn('if not _lookup.initialize():', SOURCE)
        self.assertIn('TerrainResolver.resolve(cell, samples, _lookup, PRESENTATION_SEED, RULE_VERSION)', SOURCE)
        self.assertIn('RULE_VERSION: int = TerrainResolver.RULE_VERSION', SOURCE)
        self.assertIn('PRESENTATION_SEED: int = 19', SOURCE)
        self.assertIn('halo[cell] = sample_material(cell)', SOURCE)
        self.assertIn('range(-1, WorldCoordinates.CHUNK_TILES + 1)', body('_generate'))
        self.assertIn('samples.append(halo[cell + offset])', SOURCE)
        offsets = re.search(r'const OFFSETS := (.*?)\nconst FIELD_MIN', SOURCE, re.S)[1]
        self.assertEqual(tuple((int(x), int(y)) for x, y in re.findall(r'Vector2i\((-?\d+), (-?\d+)\)', offsets)), OFFSETS)
        actual_chunks = re.search(r'const CHUNKS := (.*?)\nconst OFFSETS', SOURCE, re.S)[1]
        self.assertEqual(tuple((int(x), int(y)) for x, y in re.findall(r'Vector2i\((-?\d+), (-?\d+)\)', actual_chunks)), CHUNKS)
        for text in (SOURCE, SCENE):
            for forbidden in ('set_cells_terrain_connect', 'update_internals', 'set_cells_terrain_path',
                              'RandomNumberGenerator', 'randf(', 'randi(', 'tile_map_data', 'mapping.json'):
                self.assertNotIn(forbidden, text)

    def test_scale_origins_centers_construction_and_floor(self):
        self.assertEqual(SCENE.count('type="TileMapLayer"'), 1)
        layer = SCENE.split('[node name="Terrain"', 1)[1].split('[node ', 1)[0]
        self.assertIn('scale = Vector2(0.5, 0.5)', layer)
        self.assertNotIn('position =', layer)
        self.assertIn('show_behind_parent = true', layer)
        self.assertIn('tile_size = Vector2i(128, 128)', (ASSET / 'baked_terrain.tres').read_text())
        self.assertIn('path="res://assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres"', SCENE)
        coords = (ROOT / 'scenes/world/world_coordinates.gd').read_text()
        for contract in ('TERRAIN_SIZE: int = 64', 'CONSTRUCTION_SIZE: int = 32', 'CHUNK_TILES: int = 32',
                         'floori(point.x / TERRAIN_SIZE)', 'floori(float(tile.x) / CHUNK_TILES)'):
            self.assertIn(contract, coords)
        for cell in itertools.product((-33, -32, -1, 0, 31, 32), repeat=2):
            origin = tuple(v * 128 * .5 for v in cell)
            center = tuple(v + 32 for v in origin)
            self.assertEqual(tuple(math.floor(v/64) for v in center), cell)
            self.assertEqual(tuple(math.floor((v-.001)/64) for v in origin), tuple(v-1 for v in cell))
            self.assertEqual(tuple(math.floor(v/32) for v in origin), tuple(v*2 for v in cell))
        self.assertEqual(math.floor(-1 / 32), -1)

    def test_representative_features_and_real_assignments(self):
        self.assertEqual(len(self.cells), 4096)
        for point, expected in {(-28, -28): 1, (0, -30): 0, (-18, -18): 0,
                                (-2, -26): 1, (0, -9): 1, (0, 0): 1,
                                (14, 12): 1, (15, 12): 0}.items():
            self.assertEqual(material(*point), expected)
        signatures = {a[0] for a in self.cells.values()}
        self.assertIn((0,)*9, signatures)
        self.assertIn((1,)*9, signatures)
        self.assertGreater(len(signatures), 15)
        for sig, v, address in self.cells.values():
            self.assertEqual(TILES[sig, v], address)
        self.assertEqual({v for sig, v, _ in self.cells.values() if sig == (1,)*9}, {'A', 'B', 'C'})
        self.assertEqual({v for sig, v, _ in self.cells.values() if sig == (0,)*9}, {'A', 'B', 'C'})
        self.assertTrue(all(v == 'A' for sig, v, _ in self.cells.values() if len(set(sig)) > 1))

    def test_every_chunk_order_retirement_replacement_and_reload(self):
        # Model the source's exact owned-cell mutation contract. Order exhausts
        # all 24 permutations; no neighboring loaded cells are sampled.
        for order in itertools.permutations(CHUNKS):
            loaded, cells = {}, {}
            for coordinate in order:
                loaded[coordinate] = self.chunks[coordinate]
                cells.update(loaded[coordinate])
            self.assertEqual(cells, self.cells)
            for coordinate in CHUNKS:
                old = loaded.pop(coordinate)
                for point in old:
                    del cells[point]
                self.assertEqual(len(cells), 3072)
                self.assertFalse(set(old) & set(cells))
                regenerated = chunk(coordinate)
                self.assertEqual(old, regenerated)
                loaded[coordinate] = regenerated
                cells.update(regenerated)
                self.assertEqual(cells, self.cells)
        load = body('_load_chunk')
        self.assertLess(load.index('_generate(coordinate)'), load.index('_unload_chunk(coordinate)'))
        self.assertIn('_loaded[coordinate] != assignments', load)
        self.assertIn('coordinate not in CHUNKS', load)
        self.assertIn('terrain.set_cell(cell, assignment.source_id, assignment.atlas_coords, assignment.alternative_id)', load)
        retire = body('_unload_chunk')
        self.assertIn('for cell in _loaded[coordinate]:\n\t\tterrain.erase_cell(cell)', retire)
        self.assertLess(retire.index('terrain.erase_cell'), retire.index('_loaded.erase'))
        self.assertIn('if not _load_chunk(coordinate):\n\t\t\treturn', body('_reload'))

    def test_continuity_on_all_edges_including_chunk_seams(self):
        seam_transitions = 0
        for (x, y), (sig, _, _) in self.cells.items():
            if (x+1, y) in self.cells:
                other = self.cells[x+1, y][0]
                self.assertEqual(tuple(sig[i] for i in (3, 5, 8)), tuple(other[i] for i in (1, 4, 6)))
                seam_transitions += int(x == -1 and len(set(sig)) > 1)
            if (x, y+1) in self.cells:
                self.assertEqual(sig[6:9], self.cells[x, y+1][0][1:4])
                seam_transitions += int(y == -1 and len(set(sig)) > 1)
        self.assertGreater(seam_transitions, 0)

    def test_tint_grid_mapping_four_contributors_and_shared_boundaries(self):
        self.assertIn('FIELD_MIN := Vector2i(-32, -32)', SOURCE)
        self.assertIn('FIELD_WIDTH: int = 65', SOURCE)
        for contract in ('range(-1, FIELD_WIDTH)', 'generator.sample_color(cell, state)',
                         'samples[vertex - Vector2i.ONE] + samples[vertex - Vector2i.DOWN]',
                         '+ samples[vertex - Vector2i.RIGHT] + samples[vertex]) / 4.0',
                         'image.set_pixel(x, y, TerrainChunk._earth_tint(average))',
                         'Image.FORMAT_RGBAF'):
            self.assertIn(contract, body('_set_shading'))
        self.assertIn('(MODEL_MATRIX * vec4(VERTEX, 0.0, 1.0)).xy', SHADER)
        self.assertIn('(world_point - field_origin) / terrain_size', SHADER)
        self.assertIn('(field_vertex + vec2(0.5)) / field_size', SHADER)
        self.assertIn('textureLod(tint_field, field_uv, 0.0)', SHADER)
        self.assertIn('COLOR *= terrain_tint;', SHADER)
        self.assertNotIn('source_color,', SHADER)
        def contributors(vertex):
            x, y = vertex
            return {(x-1, y-1), (x, y-1), (x-1, y), (x, y)}
        for x, y in itertools.product(range(-32, 33), repeat=2):
            u, v = ((x+32+.5)/65, (y+32+.5)/65)
            self.assertAlmostEqual(u*65-.5, x+32)
            self.assertAlmostEqual(v*65-.5, y+32)
            self.assertTrue(all(-33 <= a <= 32 and -33 <= b <= 32 for a, b in contributors((x, y))))
        shared = {}
        for cx, cy in CHUNKS:
            for dx, dy in itertools.product(range(33), repeat=2):
                vertex = cx*32+dx, cy*32+dy
                # Nonconstant, asymmetric synthetic color catches transposition
                # and off-by-one contributor errors without production execution.
                samples = [(.3+a*.001, .3+b*.002, .25, 1) for a, b in sorted(contributors(vertex))]
                tint = earth_tint(tuple(sum(s[c] for s in samples)/4 for c in range(4)))
                if vertex in shared:
                    self.assertEqual(shared[vertex], tint)
                shared[vertex] = tint
        self.assertEqual(len(shared), 65*65)

    def test_shading_order_shared_material_and_upload_bounds(self):
        generator = (ROOT / 'scenes/world/planet_generator.gd').read_text()
        sample = generator.split('func sample_color(', 1)[1].split('func _overlay_weight', 1)[0]
        self.assertLess(sample.index('_noise('), sample.index('state.terrain_color('))
        self.assertLess(sample.index('state.terrain_color('), sample.index('for overlay in _overlays:'))
        self.assertIn('color = color.lerp(overlay.color, weight)', sample)
        shade = body('_set_shading')
        self.assertIn('PlanetGenerator.new(COLOR_SAMPLE_SEED, overlays,', shade)
        self.assertIn('state.set_terrain_color(', shade)
        self.assertIn('if mode != 0 and mode != _shading_mode:', shade)
        self.assertNotIn('_load_chunk', shade)
        self.assertNotIn('set_cell', shade)
        self.assertNotIn('ShaderMaterial.new', SOURCE)
        self.assertEqual(SCENE.count('type="ShaderMaterial"'), 1)
        self.assertNotIn('draw_polygon', SOURCE)
        self.assertNotIn('TerrainChunk.new', SOURCE)
        self.assertNotIn('func _process', SOURCE)
        self.assertIn('draw_rect(bounds, Color(1.0, 0.7, 0.2), false, 4.0)', SOURCE)
        self.assertLess(shade.index('samples[vertex'), shade.index('TerrainChunk._earth_tint(average)'))

    def test_production_assets_policy_and_pr99_unchanged(self):
        protected = ['assets', 'scenes', 'shaders', 'tools', 'inventory', 'construction',
                     'dialogue', 'objectives', 'project.godot', 'AGENTS.md', 'docs/LOCAL_TESTING.md']
        existing = subprocess.check_output(['git', 'ls-tree', '-r', '--name-only', BASE, '--', *protected], cwd=ROOT, text=True).splitlines()
        changed = subprocess.check_output(['git', 'diff', '--name-only', BASE, '--', *protected], cwd=ROOT, text=True).splitlines()
        self.assertFalse(set(existing) & set(without_presenter_paths(changed)))
        self.assertEqual(subprocess.check_output(['git', 'rev-parse', 'refs/heads/codex/preserve-editor-resource-serialization'], cwd=ROOT, text=True).strip(),
                         '326591e1a1438944d79b0be4c52992b3eb86af0f')
        for path in existing:
            if path.endswith(('.gd', '.tscn', '.tres', '.godot')):
                self.assertNotIn('production_terrain', historical_source(path))

    def test_exact_new_path_pins_reject_tampering_and_expansion(self):
        self.assertEqual(set(FIXTURE_INPUT_SHA256), {DIRECTORY + name for name in
                         ('fixture.gd', 'fixture.tscn', 'tint.gdshader', 'engine_validation.gd')})
        for path in FIXTURE_INPUT_SHA256:
            raw = (ROOT/path).read_bytes()
            verify_fixture_input(path, raw)
            for bad in (raw + b'CHANGED', raw[1:], raw + raw):
                with self.assertRaises(AssertionError):
                    verify_fixture_input(path, bad)
            with self.assertRaises(AssertionError):
                verify_fixture_input(path + '.other', raw)
        with self.assertRaises(AssertionError):
            verify_fixture_input('scenes/world/terrain_chunk.gd', b'')

    def test_scene_resources_and_separate_engine_validation_plan(self):
        for path in re.findall(r'path="res://([^"]+)"', SCENE):
            self.assertTrue((ROOT/path).is_file(), path)
        proposed = historical_source(DIRECTORY + 'engine_validation.gd')
        for contract in ('extends SceneTree', 'get_cell_source_id(cell) == -1', 'map_to_local(cell)',
                         'snapshot == fixture._loaded', 'fixture._set_shading(2)',
                         'Production terrain fixture failures: %d'):
            self.assertIn(contract, proposed)
        self.assertNotIn('engine_validation.gd', SOURCE + SCENE)
        self.assertNotIn('Input.', SOURCE)

    def test_proposed_stage_inventory_hashes_and_dependency_closure(self):
        import hashlib
        manifest = json.loads((ROOT/'docs/experiments/production_terrain_stage.json').read_text())
        tracked = subprocess.check_output(['git', 'ls-files'], cwd=ROOT, text=True).splitlines()
        classes = {}
        for path in tracked:
            if path.endswith('.gd'):
                match = re.search(r'^class_name (\w+)', (ROOT/path).read_text(encoding='utf-8'), re.M)
                if match:
                    classes[match[1]] = path
        for path, digest in manifest.items():
            self.assertFalse(path.startswith('.'))
            self.assertNotIn('..', Path(path).parts)
            self.assertTrue(path in tracked or path in FIXTURE_INPUT_SHA256)
            raw = (ROOT/path).read_bytes()
            historical_stage_input(path, raw, digest)
            if Path(path).suffix not in ('.gd', '.tscn', '.tres', '.gdshader', '.json'):
                continue  # Import sidecar cache destinations are outputs, not inputs.
            text = historical_source(path)
            for reference in re.findall(r'res://([A-Za-z0-9_./-]+)', text):
                self.assertIn(reference, manifest, (path, reference))
            if path.endswith('.gd'):
                for name, reference in classes.items():
                    if re.search(r'\b'+name+r'\b', text):
                        self.assertIn(reference, manifest, (path, name))
        self.assertFalse(any(p.endswith('.tscn') and p not in FIXTURE_INPUT_SHA256 for p in manifest))
        self.assertNotIn('project.godot', manifest)


if __name__ == '__main__':
    unittest.main()
