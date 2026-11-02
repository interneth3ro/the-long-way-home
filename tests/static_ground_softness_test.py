"""Offline transition study validation; never launches Godot or writes files."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from ground_art_preservation import historical_checkout

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('softness_study',ROOT/'tools/ground-transition-softness.py')
softness = importlib.util.module_from_spec(spec)
spec.loader.exec_module(softness)


class GroundSoftnessTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.context = softness.load_context()
        cls.models = [softness.render(cls.context,lo,hi) for _,lo,hi in softness.TREATMENTS]
        cls.manifest = json.loads((softness.OUTPUT/'manifest.json').read_text())

    def test_exact_regeneration_and_saved_output_hashes(self):
        for name,raw in softness.build().items():
            saved = (softness.OUTPUT/name).read_bytes()
            if name == '.gitattributes':
                saved = historical_checkout((softness.OUTPUT/name).relative_to(ROOT).as_posix(), saved)
            self.assertEqual(saved,raw,name)
        for name,expected in self.manifest['output_sha256'].items():
            saved = (softness.OUTPUT/name).read_bytes()
            if name == '.gitattributes':
                saved = historical_checkout((softness.OUTPUT/name).relative_to(ROOT).as_posix(), saved)
            self.assertEqual(hashlib.sha256(saved).hexdigest(),expected,name)
        self.assertEqual({p.name for p in softness.OUTPUT.iterdir()},
                         {*self.manifest['output_sha256'],'manifest.json','README.md'})

    def test_all_three_treatments_compatible_edges_anchors_and_saved_hashes(self):
        self.assertEqual([(e['label'],e['range']) for e in self.manifest['treatments']],
                         [(label,[lo,hi]) for label,lo,hi in softness.TREATMENTS])
        for record,(tiles,masks,report) in zip(self.manifest['treatments'],self.models):
            self.assertEqual(record['validation'],report)
            self.assertEqual(report['compatible_ordered_edge_pairs'],836)
            self.assertEqual(report['configured_records'],45)
            self.assertEqual(report['baseline_signatures'],41)
            self.assertEqual(report['anchors'],41*9)
            self.assertEqual(report['maximum_shared_edge_channel_difference'],0)
            self.assertEqual(softness.validate_tiles(self.context,tiles,masks),report)
            for entry in record['tile_pixel_sha256']:
                key = tuple(entry['signature']),entry['variant']
                self.assertEqual(hashlib.sha256(tiles[key]).hexdigest(),entry['sha256'])

    def test_current_is_exact_saved_baseline_and_interiors_never_change(self):
        study,bake,manifest,sources,baseline = self.context
        self.assertEqual(self.models[0][0],baseline)
        for tiles,_,_ in self.models:
            for key,pixels in baseline.items():
                sig,variant = key
                if sig == (sig[0],)*9:
                    self.assertEqual(tiles[key],pixels)
        for name,expected in self.manifest['source_sha256'].items():
            raw = (softness.INPUT/'sources'/name).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),expected)
            relative = (softness.INPUT/'sources'/name).relative_to(ROOT).as_posix()
            self.assertEqual(raw,subprocess.check_output(['git','show',softness.BASE_REVISION+':'+relative],cwd=ROOT))

    def test_centerlines_anchors_and_increasing_softness(self):
        counts = [report['partially_blended_texels'] for _,_,report in self.models]
        self.assertLess(counts[0],counts[1])
        self.assertLess(counts[1],counts[2])
        for sig in self.models[0][1]:
            masks = [model[1][sig] for model in self.models]
            classification = [v >= .5 for v in masks[0]]
            for mask in masks:
                self.assertEqual([v >= .5 for v in mask],classification)
                for x,y,k in softness.ANCHORS:
                    self.assertEqual(mask[y*128+x],sig[k])

    def test_exact_layouts_and_atlas_coordinates(self):
        study,bake,baseline,_,_ = self.context
        self.assertEqual(self.manifest['baseline'],
                         [dict(atlas=e['atlas'],signature=e['signature']) for e in baseline['baseline']])
        self.assertEqual(self.manifest['interiors'],baseline['interiors'])
        for name in softness.LAYOUTS:
            raw = json.dumps(baseline['layouts'][name],sort_keys=True,separators=(',',':')).encode()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),self.manifest['layout_sha256'][name])
        for name,width,height in (('meandering_boundary_varied',12,8),('mixed_24x16',24,16)):
            raw = (softness.OUTPUT/(name+'_comparison.png')).read_bytes()
            image = bake.decode_png(raw)
            self.assertEqual(image[:2],(max(width*64,1024)*3+64,height*64+768+168))
            x,y = (2,1) if name == 'meandering_boundary_varied' else (12,4)
            detail = [entry['signature'] for row in baseline['layouts'][name][y:y+6] for entry in row[x:x+8]]
            self.assertEqual({sig[0] for sig in detail},{0,1})
            self.assertTrue(any(sig != [sig[0]]*9 for sig in detail))

    def test_validation_rejects_anchor_and_nonanchor_edge_damage(self):
        sig = (0,)*9
        for tiles,masks,_ in self.models:
            for x,y in ((64,64),(127,12)):
                damaged = dict(tiles)
                pixels = bytearray(damaged[sig,'A'])
                pixels[(y*128+x)*3] ^= 1
                damaged[sig,'A'] = bytes(pixels)
                with self.assertRaises(ValueError):
                    softness.validate_tiles(self.context,damaged,masks)


if __name__ == '__main__':
    unittest.main()
