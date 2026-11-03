"""C1-only offline data/geometry checks. Never invokes Godot or GDScript."""
import importlib.util
import json
import math
from pathlib import Path
import re
import subprocess
import unittest

ROOT=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('c1_reference',ROOT/'tools/terrain-c1-author.py')
c1=importlib.util.module_from_spec(spec)
spec.loader.exec_module(c1)


class TerrainC1(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.cached={coordinate:c1.fields(coordinate) for coordinate in c1.COORDS}

    def test_saved_field_and_phase_pixels(self):
        for coordinate,(field,phase) in self.cached.items():
            for kind,image in (('field',field),('phase',phase)):
                path=c1.ASSETS/f'fields/{coordinate[0]}_{coordinate[1]}_{kind}.png'
                self.assertEqual(c1.png.decode_png(path.read_bytes()),image)

    def test_all_shared_gutters(self):
        comparisons=0
        for a,(field,phase) in self.cached.items():
            for b,(other,other_phase) in self.cached.items():
                if a>=b:
                    continue
                for j in range(c1.WIDTH):
                    for i in range(c1.WIDTH):
                        x=a[0]*128+i-c1.GUTTER-b[0]*128+c1.GUTTER
                        y=a[1]*128+j-c1.GUTTER-b[1]*128+c1.GUTTER
                        if 0<=x<c1.WIDTH and 0<=y<c1.WIDTH:
                            p=field[2][(j*c1.WIDTH+i)*3:(j*c1.WIDTH+i+1)*3]
                            q=other[2][(y*c1.WIDTH+x)*3:(y*c1.WIDTH+x+1)*3]
                            self.assertEqual(p,q); comparisons+=1
                for j in range(7):
                    for i in range(7):
                        x=a[0]*4+i-b[0]*4; y=a[1]*4+j-b[1]*4
                        if 0<=x<7 and 0<=y<7:
                            self.assertEqual(phase[2][(j*7+i)*3:(j*7+i+1)*3],other_phase[2][(y*7+x)*3:(y*7+x+1)*3])
        self.assertGreater(comparisons,4500)

    def test_reconstructed_crossings_and_origin(self):
        comparisons=0
        for a,(image,_) in self.cached.items():
            for b,(other,_) in self.cached.items():
                for y in (-2048.,-64.,-8.,0.,8.,64.,2048.):
                    for x in (-2048.,-64.,-8.,0.,8.,64.,2048.):
                        if all(-64<=v-coordinate*2048<=2112 for v,coordinate in zip((x,y),a)) and all(-64<=v-coordinate*2048<=2112 for v,coordinate in zip((x,y),b)):
                            p=c1.reconstruct(image,a,(x,y)); q=c1.reconstruct(other,b,(x,y))
                            for u,v in zip(p,q): self.assertAlmostEqual(u,v,places=14)
                            comparisons+=1
        self.assertGreater(comparisons,100)
        self.assertEqual(c1.select_chunk((-1,-1)),(-1,-1))
        self.assertEqual(c1.select_chunk((0,0)),(0,0))

    def test_strict_exclusions_after_bilinear_reconstruction(self):
        checked=0
        for y in range(-1600,1601,43):
            for x in range(-1600,1601,43):
                point=(x+.37,y+.61)
                if c1.strict_distance(point)<=0:
                    coordinate=c1.select_chunk(point)
                    coverage=c1.reconstruct(self.cached[coordinate][0],coordinate,point)[0]
                    self.assertEqual(coverage,0.)
                    # Every bilinear footprint vertex is within sqrt(2)*STEP.
                    for yy in (math.floor(point[1]/16)*16,math.floor(point[1]/16)*16+16):
                        for xx in (math.floor(point[0]/16)*16,math.floor(point[0]/16)*16+16):
                            self.assertEqual(c1.field_node(xx,yy)[0],0)
                    checked+=1
        self.assertGreater(checked,1000)

    def test_reverse_regeneration_and_retirement_reconstruction(self):
        forward={coordinate:c1.sha(c1.png.encode_png(*data[0])+c1.png.encode_png(*data[1])) for coordinate,data in self.cached.items()}
        reverse={coordinate:c1.sha(c1.png.encode_png(*c1.fields(coordinate)[0])+c1.png.encode_png(*c1.fields(coordinate)[1])) for coordinate in reversed(c1.COORDS)}
        self.assertEqual(forward,reverse)
        coordinate=(-1,0)
        regenerated=c1.fields(coordinate)
        self.assertEqual(regenerated,self.cached[coordinate])
        self.assertNotEqual(c1.phase_node(-1,0),c1.phase_node(-1,0,c1.SEED+1))
        self.assertNotEqual(c1.phase_node(-1,0),c1.phase_node(1,0))

    def test_sampling_windows_shared_at_lattice_and_chunk_edges(self):
        # Verify each chunk's stored metadata selects canonical integer identities.
        for coordinate,(_,phase) in self.cached.items():
            for j in range(7):
                for i in range(7):
                    self.assertEqual(phase[2][(j*7+i)*3:(j*7+i+1)*3],c1.phase_node(coordinate[0]*4+i-1,coordinate[1]*4+j-1))
        for local in (0.,.001,511.999,512.,1024.,2047.999,2048.):
            lattice=math.floor(local/512)
            for vertex in (lattice,lattice+1):
                for phase in (0.,1.):
                    uv=.35+.3*phase+(local-vertex*512)/2048
                    self.assertGreaterEqual(uv,.10-1e-9)
                    self.assertLessEqual(uv,.90+1e-9)

    def test_isolation_and_data_identity(self):
        # Audit the immutable original C1 scope, not unrelated future main changes.
        # Live resource, identity, dependency and production checks below still apply.
        paths=subprocess.check_output(['git','diff','--name-only','fa410ed9b329ffd28a927e142d2362971d54584a','a4edb49720ebfa9be654353abb093c76740554e7'],cwd=ROOT,text=True).splitlines()
        allowed=('assets/experiments/terrain_c1/','scenes/experiments/terrain_c1/','docs/experiments/terrain_c1.md','tools/terrain-c1-author.py','tests/static_terrain_c1_test.py')
        self.assertTrue(all(path.startswith(allowed) for path in paths),paths)
        harness=(ROOT/'scenes/experiments/terrain_c1/harness.gd').read_text()
        self.assertNotIn('set_terrain_color(',harness)
        self.assertNotIn('set_setting(',harness)
        self.assertNotIn('OS.execute',harness)
        self.assertIn('generation != _epoch',harness)
        self.assertIn('_active.get(coordinate, -1) != token',harness)
        self.assertIn('_receipt_epoch == _epoch',harness)
        shader=(ROOT/'scenes/experiments/terrain_c1/continuous.gdshader').read_text()
        self.assertNotIn('sin(',shader)
        self.assertNotIn('MODEL_MATRIX',shader)
        self.assertIn('local_point = VERTEX',shader)
        for relative in re.findall(r'res://([^"\n]+)',harness+(ROOT/'scenes/experiments/terrain_c1/terrain_c1.tscn').read_text()):
            if relative.endswith('/'):
                self.assertTrue((ROOT/relative).is_dir(),relative)
            elif '+' not in relative:
                self.assertTrue((ROOT/relative).exists(),relative)
        fixture=json.loads((c1.ASSETS/'fixture.json').read_text())
        self.assertEqual(fixture['seed'],26026)
        self.assertEqual(fixture['supported_chunks'],[list(c) for c in c1.COORDS])
        self.assertEqual(fixture['rule'],'c1_fields_v1')

    def test_source_override_precedence_stays_production_owned(self):
        generator=(ROOT/'scenes/world/planet_generator.gd').read_text()
        method=generator.split('func sample_color(',1)[1].split('\n\n\nfunc ',1)[0]
        self.assertLess(method.index('state.terrain_color'),method.index('for overlay in _overlays'))
        harness=(ROOT/'scenes/experiments/terrain_c1/harness.gd').read_text()
        self.assertIn('chunk.configure(coordinate, _generator, _state, false)',harness)
        self.assertIn('chunk.write_tint(tint, Vector2i.ZERO)',harness)


if __name__=='__main__': unittest.main()
