"""Focused offline subset checks. No Godot, gameplay scripts or disk generation."""
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('ground_refinement', ROOT/'tools/ground-art-refinement.py')
study = importlib.util.module_from_spec(spec)
spec.loader.exec_module(study)
ANCHORS = ((64,64,0),(0,0,1),(64,0,2),(127,0,3),(0,64,4),
           (127,64,5),(0,127,6),(64,127,7),(127,127,8))
RELATIONSHIPS = (('right','left',(3,5,8),(1,4,6)),
                 ('bottom','top',(6,7,8),(1,2,3)))


class GroundRefinementTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.bake = study.load_baker()
        cls.path = study.OUTPUT
        cls.manifest = json.loads((cls.path/'manifest.json').read_text())
        cls.images = {}
        for name in cls.manifest['output_sha256']:
            if name.endswith('.png'):
                cls.images[name] = cls.bake.decode_png((cls.path/name).read_bytes())
        cls.sources = [cls.images['sources/'+name+'_refined.png'][2] for name in ('earth','green')]
        cls.tiles = {}
        for entry in cls.manifest['baseline']:
            cls.tiles[tuple(entry['signature']), 'A'] = study.crop(cls.images['baseline_subset.png'][2], 1536, *entry['atlas'])
        for entry in cls.manifest['interiors']:
            cls.tiles[tuple(entry['signature']), entry['variant']] = study.crop(cls.images['interiors_bc.png'][2], 256, *entry['atlas'])

    def test_dimensions_rgb_and_every_saved_output_digest(self):
        self.assertEqual(self.images['baseline_subset.png'][:2], (1536,1024))
        self.assertEqual(self.images['interiors_bc.png'][:2], (256,256))
        for name in ('earth','green'):
            self.assertEqual(self.images['sources/'+name+'_refined.png'][:2], (128,128))
        for name, expected in self.manifest['output_sha256'].items():
            self.assertEqual(hashlib.sha256((self.path/name).read_bytes()).hexdigest(), expected, name)
        self.assertEqual(set(p.relative_to(self.path).as_posix() for p in self.path.rglob('*') if p.is_file()),
                         {*self.manifest['output_sha256'], 'manifest.json', 'README.md', '.gitattributes'})

    def test_subset_matches_immutable_csv_and_production_mapping(self):
        with (ROOT/'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv').open(newline='') as stream:
            rows = list(csv.DictReader(stream))
        expected = {(int(r['atlas_x']),int(r['atlas_y'])):
                    (int(r['tlwh_center']),*(int(r['tlwh_'+bit]) for bit in self.bake.BITS)) for r in rows}
        production = json.loads((study.BASE/'baked_v2/mapping.json').read_text())
        by_coord = {tuple(e['atlas']): tuple(e['signature']) for e in production['baseline']}
        self.assertEqual(expected, by_coord)
        entries = self.manifest['baseline']
        self.assertEqual(len(entries), self.manifest['baseline_count'])
        self.assertEqual(len({tuple(e['signature']) for e in entries}), len(entries))
        self.assertLess(len(entries),94)
        for entry in entries:
            self.assertEqual(tuple(entry['signature']), expected[tuple(entry['atlas'])])
            self.assertEqual(entry['variant'],'A')
        self.assertTrue(set(map(tuple,self.manifest['representative_order'])).issubset({tuple(e['atlas']) for e in entries}))
        self.assertEqual([(e['atlas'],e['signature'],e['variant']) for e in self.manifest['interiors']],
                         [([v-1,c],[c]*9,'ABC'[v]) for c in (0,1) for v in (1,2)])

    def test_all_compatible_subset_edges_and_variant_edges(self):
        comparisons = 0
        for (a,av), ap in self.tiles.items():
            for (b,bv), bp in self.tiles.items():
                for side, opposite, ia, ib in RELATIONSHIPS:
                    if tuple(a[i] for i in ia) == tuple(b[i] for i in ib):
                        self.assertEqual(study.edge(ap,side), study.edge(bp,opposite), (a,av,b,bv,side))
                        comparisons += 1
        self.assertGreater(comparisons, 100)
        print('Subset ordered compatible right/bottom edge pairs:', comparisons)
        for source in self.sources:
            self.assertEqual(study.edge(source,'top'),study.edge(source,'bottom'))
            self.assertEqual(study.edge(source,'left'),study.edge(source,'right'))
        for c in (0,1):
            sig = (c,)*9
            self.assertEqual(len({self.tiles[sig,v] for v in 'ABC'}),3)
            for side in ('top','right','bottom','left'):
                self.assertEqual(len({study.edge(self.tiles[sig,v],side) for v in 'ABC'}),1)

    def test_every_signature_anchor_and_no_configured_placeholders(self):
        for (sig, variant), pixels in self.tiles.items():
            self.assertEqual(len(pixels),128*128*3)
            self.assertNotEqual(len(set(pixels)),1)
            for i in range(0,len(pixels),3):
                self.assertNotIn(pixels[i:i+3], (b'\x00\x00\x00',b'\xff\x00\xff'))
            if variant == 'A':
                for x,y,k in ANCHORS:
                    offset = (y*128+x)*3
                    self.assertEqual(pixels[offset:offset+3],self.sources[sig[k]][offset:offset+3],(sig,k))

    def test_feather_narrows_without_moving_midpoint_or_binary_anchors(self):
        before = after = 0
        for sig, variant in self.tiles:
            if variant != 'A':
                continue
            old = self.bake.mask(sig)
            new = [self.bake.smooth((v-.20)/.60) for v in old]
            self.assertEqual([v >= .5 for v in old], [v >= .5 for v in new])
            for x,y,k in ANCHORS:
                self.assertEqual(new[y*128+x],sig[k])
            before += sum(0 < v < 1 for v in old)
            after += sum(0 < v < 1 for v in new)
        self.assertLess(after,before)
        self.assertGreater(after,0)
        self.assertEqual(self.manifest['feather_nonpure_texels'],dict(original=before,refined=after))

    def test_color_balance_and_faint_nonzero_texture(self):
        for c, source in enumerate(self.sources):
            original = self.bake.sources[c]
            for channel in range(3):
                def statistics(pixels):
                    values = [self.bake.to_linear(pixels[(y*128+x)*3+channel]) for y in range(127) for x in range(127)]
                    mean = sum(values)/len(values)
                    return mean, (sum((v-mean)**2 for v in values)/len(values))**.5
                old_mean, old_sd = statistics(original)
                new_mean, new_sd = statistics(source)
                self.assertLess(abs(new_mean-old_mean), .003)
                self.assertGreater(new_sd,0)
                self.assertLess(new_sd,old_sd*.20)

    def test_identical_historical_layout_and_every_preview_adjacency(self):
        historical = json.loads((ROOT/'artifacts/evidence/pr100-stage2-baked-v2/previews.json').read_text())
        for name in ('green_patch_varied','earth_patch_varied','meandering_boundary_varied'):
            old = next(p for p in historical['previews'] if p['name']==name)
            self.assertEqual(self.manifest['layouts'][name],old['cells'])
        for name, layout in self.manifest['layouts'].items():
            for y,row in enumerate(layout):
                for x,entry in enumerate(row):
                    sig = tuple(entry['signature'])
                    key = sig, entry['variant']
                    self.assertIn(key,self.tiles)
                    if sig != (sig[0],)*9:
                        self.assertEqual(entry['variant'],'A')
                    for dx,dy,side,opp,ia,ib in ((1,0,*RELATIONSHIPS[0]),(0,1,*RELATIONSHIPS[1])):
                        if y+dy<len(layout) and x+dx<len(row):
                            neighbor = layout[y+dy][x+dx]
                            ns = tuple(neighbor['signature'])
                            self.assertEqual(tuple(sig[i] for i in ia),tuple(ns[i] for i in ib),(name,x,y))
                            self.assertEqual(study.edge(self.tiles[key],side),study.edge(self.tiles[ns,neighbor['variant']],opp))

    def test_production_sources_baker_and_historical_layout_identity(self):
        study.checked_inputs()
        raw = (ROOT/'artifacts/evidence/pr100-stage2-baked-v2/previews.json').read_bytes()
        self.assertEqual(hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),self.manifest['historical_preview_sha256'])
        # New isolated files only: every pre-existing tracked path must still
        # match the verified starting revision, including preserved guard code.
        changed = subprocess.check_output(['git','diff',self.manifest['base_revision'],'--name-only','--diff-filter=MDRT'],cwd=ROOT).decode().splitlines()
        self.assertEqual(changed,[])

    def test_byte_identical_regeneration_in_memory(self):
        for name, raw in study.build().items():
            self.assertEqual((self.path/name).read_bytes(),raw,name)


if __name__ == '__main__':
    unittest.main()
