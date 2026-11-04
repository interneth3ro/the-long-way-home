"""Offline model and text contracts only; does not execute GDScript or Godot."""
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import subprocess
import unittest

import terrain_stage2_reference as classification
import terrain_stage2b2_reconstruction_reference as reconstruction

ROOT = Path(__file__).resolve().parents[1]
BASE = 'ee937c98aa5e5bcb087f99c5b0eb8c8960ecf4f0'
LAB = 'scenes/experiments/terrain_stage3b/'
ADDED = {LAB+'lab.gd', LAB+'lab.tscn', LAB+'continuous.gdshader',
         'tests/static_terrain_stage3b_test.py', 'docs/experiments/terrain_stage3b_visible_lab.md'}
MODIFIED = {'tests/static_metadata_smoke_test.py',
            'docs/experiments/terrain_stage3_architecture_decisions.md'}


def read(path):
    return (ROOT/path).read_text()


def reconstructed(ids, point, chunk):
    """Independent local texture layout and scalar Candidate A specification."""
    q = tuple((point[i]-2048*chunk[i]-32)/64 for i in (0, 1))
    cell = tuple(math.floor(v) for v in q)
    weights = tuple((v-math.floor(v))**2*(3-2*(v-math.floor(v))) for v in q)
    def bit(x, y):
        if not (-1 <= x <= 32 and -1 <= y <= 32):
            raise ValueError('outside halo')
        return int(ids[(y+1)*34+x+1] > 0)
    u, v = weights
    value = ((1-u)*bit(*cell)+u*bit(cell[0]+1, cell[1]))*(1-v)
    value += ((1-u)*bit(cell[0], cell[1]+1)+u*bit(cell[0]+1, cell[1]+1))*v
    t = max(0, min(1, (value-5/32)/(11/16)))
    return t*t*(3-2*t)


class Stage3BTest(unittest.TestCase):
    def test_four_center_patterns_and_center_endpoints(self):
        for pattern in range(16):
            def material(c):
                index = ((0, 1), (3, 2))[c[1] % 2][c[0] % 2]
                return (1+index) if pattern & (1 << index) else 0
            ids = bytes(material((x,y)) for y in range(-1,33) for x in range(-1,33))
            model = reconstruction.Reconstruction(material, -42)
            for x in (0, 8, 16, 32, 48, 56, 64):
                for y in (0, 8, 16, 32, 48, 56, 64):
                    p = (32+x,32+y)
                    self.assertAlmostEqual(reconstructed(ids,p,(0,0)),model.values(p)[1],places=14)
                    if x in (0,64) and y in (0,64):
                        self.assertEqual(reconstructed(ids,p,(0,0)),int(material((x//64,y//64))>0))

    def test_signed_seed_original_ids_and_negative_seam(self):
        geometry = classification.load_geometry()
        chunks = ((-1,-1),(0,-1),(-1,0),(0,0))
        points = ((0,0),(0,-1700),(-.125,-1700),(.125,-1700),(-2048,-2048),(2048,2048))
        for seed in (-2**63,-42,0,26026,2**63-1):
            payloads = {c: bytes(classification.classify((32*c[0]+x,32*c[1]+y),seed,geometry)
                                for y in range(-1,33) for x in range(-1,33)) for c in chunks}
            oracle = reconstruction.Reconstruction(lambda c:classification.classify(c,seed,geometry),seed)
            for p in points:
                results = [reconstructed(data,p,c) for c,data in payloads.items()
                           if all(2048*c[i] <= p[i] <= 2048*(c[i]+1) for i in (0,1))]
                self.assertTrue(results)
                for result in results:
                    self.assertAlmostEqual(result,oracle.values(p)[1],places=13)
            # Identical two-column halo: no coordinate wrap at the negative seam.
            a,b = payloads[(-1,-1)],payloads[(0,-1)]
            for row in range(34):
                self.assertEqual(a[row*34+32:row*34+34],b[row*34:row*34+2])

    def test_shader_numerical_fetch_and_no_removed_mask(self):
        shader = read(LAB+'continuous.gdshader')
        self.assertIn('texelFetch(material_ids, cell + ivec2(1), 0)',shader)
        self.assertIn('ivec2 cell = ivec2(floor(q))',shader)
        self.assertIn('(p - vec2(32.0)) / 64.0',shader)
        self.assertIn('smoothstep(5.0 / 32.0, 27.0 / 32.0, value)',shader)
        for name in ('material_ids','phase_field'):
            line = next(s for s in shader.splitlines() if 'uniform sampler2D '+name in s)
            self.assertIn('filter_nearest',line)
            self.assertNotIn('source_color',line)
            self.assertNotIn('mipmap',line)
        self.assertIn('texelFetch(phase_field, ivec2(lattice) + ivec2(1), 0)',shader)
        self.assertNotIn('field.r',shader)
        self.assertNotIn('protection_field',shader)
        self.assertNotIn('Geometry2D',shader)
        self.assertIn('local_point = VERTEX',shader)

    def test_fixed_runtime_bounds_failure_and_dependencies(self):
        source = read(LAB+'lab.gd')
        self.assertIn('Metadata.prepare(SEED, coordinate, _overlays, _protected, _anchors)',source)
        self.assertIn('Image.create_from_data(34, 34, false, Image.FORMAT_R8, ids)',source)
        self.assertIn('coordinate not in COORDS or _metadata.has(coordinate)',source)
        self.assertIn('ids.size() != 34 * 34',source)
        self.assertIn('id > 4',source)
        self.assertIn('_metadata[coordinate] = prepared',source)
        self.assertIn('_metadata.size() == COORDS.size()',source)
        fail = source.split('func _fail(',1)[1]
        for text in ('_ready_for_view = false','surface.hide()','$CanvasLayer/Curtain.show()','set_process(false)'):
            self.assertIn(text,fail)
        for forbidden in ('PlanetWorldState.new','TerrainChunk.new','OS.execute','generate_mipmaps','set_terrain_color','change_scene','Thread'):
            self.assertNotIn(forbidden,source)
        self.assertEqual({p.name for p in (ROOT/LAB).iterdir()}, {'lab.gd','lab.tscn','continuous.gdshader'})
        # The chosen natural and negative seam views actually include both classes.
        geometry = classification.load_geometry()
        for cx,cy in ((-1100,750),(0,-1700)):
            found = {classification.classify((x,y),26026,geometry)>0
                     for y in range(math.floor((cy-360)/64),math.floor((cy+360)/64))
                     for x in range(math.floor((cx-640)/64),math.floor((cx+640)/64))}
            self.assertEqual(found,{False,True})

    def test_frozen_inputs_preservation_and_exact_scope(self):
        receipt = json.loads(read('artifacts/logs/terrain-preservation-2026-11-03.json'))
        delta = subprocess.check_output(['git','diff','--name-status',BASE,'--'],cwd=ROOT,text=True)
        inventory = {p:s for s,p in (line.split('\t',1) for line in delta.splitlines())}
        untracked = set(subprocess.check_output(['git','ls-files','--others','--exclude-standard'],cwd=ROOT,text=True).splitlines())
        self.assertEqual(untracked-ADDED,set(receipt['protected_sidecars']))
        inventory.update({p:'A' for p in untracked & ADDED})
        self.assertEqual(inventory,{**dict.fromkeys(ADDED,'A'),**dict.fromkeys(MODIFIED,'M')})
        for p,entry in receipt['protected_sidecars'].items():
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),entry['sha256'])
        for family in ('earth','green'):
            p='assets/experiments/terrain_c1/sources/'+family+'.png'
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),receipt['commits']['c1']['sha256'][p])

    def test_proposed_stage_inventory_and_phase_identity(self):
        inputs = json.loads(read('tests/fixtures/metadata_smoke/inputs.json'))
        excluded = {'tests/metadata_smoke_test.gd','tests/metadata_smoke_test.gd.uid',
                    'tests/fixtures/metadata_smoke/geometry.json',
                    'tests/fixtures/terrain_stage2_classification_vectors.json'}
        inputs = [p for p in inputs if p not in excluded]
        inputs += [LAB+'lab.gd',LAB+'lab.tscn',LAB+'continuous.gdshader',
                   'assets/experiments/terrain_c1/fixture.json']
        images = ['assets/experiments/terrain_c1/sources/'+f+'.png' for f in ('earth','green')]
        images += ['assets/experiments/terrain_c1/fields/'+c+'_'+kind+'.png'
                   for c in ('-1_-1','-1_0','0_-1','0_0') for kind in ('field','phase')]
        inputs += images + [p+'.import' for p in images]
        self.assertEqual(len(inputs),52)
        self.assertEqual(len(set(inputs)),52)
        self.assertTrue(all((ROOT/p).is_file() for p in inputs))
        receipt = json.loads(read('artifacts/logs/terrain-preservation-2026-11-03.json'))
        for p in images+['assets/experiments/terrain_c1/fixture.json']:
            self.assertEqual(hashlib.sha256((ROOT/p).read_bytes()).hexdigest(),receipt['commits']['c1']['sha256'][p])
        for p in images:
            self.assertEqual(hashlib.sha256((ROOT/(p+'.import')).read_bytes()).hexdigest(),receipt['metadata'][p+'.import']['sha256'])
        # Decode frozen bytes with the existing offline PNG reader; compare every
        # stored phase to its specified absolute-coordinate identity.
        spec = importlib.util.spec_from_file_location('stage3b_png',ROOT/'tools/bake-illustrated-terrain.py')
        png = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(png)
        maps = {}
        for cx,cy in ((-1,-1),(0,-1),(-1,0),(0,0)):
            path = ROOT/f'assets/experiments/terrain_c1/fields/{cx}_{cy}_phase.png'
            width,height,pixels = png.decode_png(path.read_bytes())
            self.assertEqual((width,height),(7,7))
            maps[(cx,cy)] = {}
            for j in range(7):
                for i in range(7):
                    x,y = cx*4+i-1,cy*4+j-1
                    phase = pixels[(j*7+i)*3:(j*7+i+1)*3]
                    expected = hashlib.sha256(f'c1_fields_v1:c1_materials_v1:26026:{x}:{y}:material'.encode()).digest()[:3]
                    self.assertEqual(phase,expected)
                    maps[(cx,cy)][(x,y)] = phase
        for a in maps.values():
            for b in maps.values():
                for point in a.keys() & b.keys():
                    self.assertEqual(a[point],b[point])

    def test_exact_historical_guard_amendment(self):
        path='tests/static_metadata_smoke_test.py'
        before=subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True)
        expected=before.replace('        delta = subprocess.check_output(["git", "diff", "--name-status", BASE, "--"], cwd=ROOT, text=True)',
            '        # PR #139 historical inventory; Stage 3B checks its own exact scope.\n        merged = "'+BASE+'"\n        delta = subprocess.check_output(["git", "diff", "--name-status", BASE, merged, "--"], cwd=ROOT, text=True)')
        for line in ('        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())\n',
                     '        self.assertEqual(untracked-ADDED, set(receipt["protected_sidecars"]))\n',
                     '        inventory.update({path: "A" for path in untracked & ADDED})\n'):
            self.assertEqual(expected.count(line),1)
            expected=expected.replace(line,'')
        self.assertEqual(read(path),expected)


if __name__ == '__main__':
    unittest.main()
