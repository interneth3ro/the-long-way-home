"""Read-only Stage 2 PNG/resource/preservation checks. Never executes Godot or the baker."""
import csv
import hashlib
import json
from pathlib import Path
import re
import unittest

from static_illustrated_terrain_test import png_rgb, ROOT, BITS
from baked_terrain_preservation import (
    INPUT_SHA256, APPROVED_BASELINE_PIXELS, APPROVED_INTERIOR_PIXELS, verify_input,
)

ASSET = 'assets/experiments/native_terrain_47_96/baked_v2/'
SCENE = 'scenes/experiments/native_terrain_47_96/illustrated_baked_v2.tscn'


class BakedTerrainStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        with (ROOT / 'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv').open(newline='') as stream:
            cls.rows = list(csv.DictReader(stream))
        cls.mapping = json.loads((ROOT / ASSET / 'mapping.json').read_text())
        cls.resource = (ROOT / ASSET / 'baked_terrain.tres').read_text()
        width,height,cls.atlas_rows = png_rgb((ROOT / ASSET / 'baseline_94.png').read_bytes())
        assert (width,height) == (1536,1024)
        width,height,cls.interior_rows = png_rgb((ROOT / ASSET / 'interiors_bc.png').read_bytes())
        assert (width,height) == (256,256)
        cls.baseline = {tuple(e['atlas']): cls.cell(cls.atlas_rows,*e['atlas']) for e in cls.mapping['baseline']}
        cls.interiors = {(e['signature'][0], 'ABC'.index(e['variant'])):
                         cls.cell(cls.interior_rows,*e['atlas']) for e in cls.mapping['interiors']}

    @staticmethod
    def cell(rows,x,y):
        return b''.join(row[x*384:(x+1)*384] for row in rows[y*128:(y+1)*128])

    def test_original_inventory_and_all_752_baseline_assignments(self):
        expected = {(int(r['atlas_x']),int(r['atlas_y'])):
                    (int(r['tlwh_center']),*(int(r['tlwh_'+b]) for b in BITS)) for r in self.rows}
        actual = {}
        sources = re.findall(r'\[sub_resource type="TileSetAtlasSource" id="([^"]+)"\]\n(.*?)(?=\n\[)',self.resource,re.S)
        self.assertEqual([s[0] for s in sources],['Baseline','Interiors'])
        for source,body in sources:
            records = {}
            for x,y in re.findall(r'^(\d+):(\d+)/0 = 0$',body,re.M):
                prefix = f'{x}:{y}/0/'
                props = dict(re.findall(r'^'+prefix+r'([^\n=]+) = ([^\n]+)$',body,re.M))
                self.assertEqual(set(props), {'terrain_set','terrain',*('terrains_peering_bit/'+b for b in BITS)})
                self.assertEqual(props['terrain_set'],'0')
                sig = (int(props['terrain']),*(int(props['terrains_peering_bit/'+b]) for b in BITS))
                coord = (int(x),int(y))
                self.assertNotIn(coord,records)
                records[coord] = sig
            if source == 'Baseline':
                actual = records
                self.assertEqual(body.count('/terrains_peering_bit/'),752)
            else:
                self.assertEqual(records,{(0,0):(0,)*9,(1,0):(0,)*9,(0,1):(1,)*9,(1,1):(1,)*9})
        self.assertEqual(actual,expected)
        self.assertEqual(len(set(actual.values())),94)
        self.assertEqual({tuple(e['atlas']):tuple(e['signature']) for e in self.mapping['baseline']},expected)
        self.assertEqual(self.resource.count('/terrains_peering_bit/'),784)  # 752 + four exact solid alternatives
        self.assertIn('tile_size = Vector2i(128, 128)',self.resource)
        self.assertEqual(self.resource.count('texture_region_size = Vector2i(128, 128)'),2)
        self.assertEqual(re.findall(r'^sources/\d+ = .*$',self.resource,re.M),
                         ['sources/0 = SubResource("Baseline")','sources/1 = SubResource("Interiors")'])
        for coord in ((10,1),(10,5)):
            self.assertNotIn(coord,actual)
            self.assertEqual(self.cell(self.atlas_rows,*coord),bytes(128*128*3))

    def test_approved_stage1_pixels_and_exact_three_interior_variants(self):
        self.assertEqual(len(APPROVED_BASELINE_PIXELS),20)
        for coord,digest in APPROVED_BASELINE_PIXELS.items():
            self.assertEqual(hashlib.sha256(self.baseline[coord]).hexdigest(),digest,coord)
        self.assertEqual(set(self.interiors),{(c,v) for c in (0,1) for v in (1,2)})
        for key,digest in APPROVED_INTERIOR_PIXELS.items():
            self.assertEqual(hashlib.sha256(self.interiors[key]).hexdigest(),digest,key)
        for entry in self.mapping['baseline']:
            self.assertEqual(hashlib.sha256(self.baseline[tuple(entry['atlas'])]).hexdigest(),entry['pixel_sha256'])
        for c in (0,1):
            original = self.baseline[(9,2+4*c)]
            self.assertEqual(len({original,self.interiors[c,1],self.interiors[c,2]}),3)

    def test_all_raster_center_and_peer_anchors_match_metadata(self):
        originals = []
        for name in ('earth_solid.png','green_solid.png'):
            _,_,rows = png_rgb((ROOT / 'assets/experiments/native_terrain_47_96/illustrated_v1/originals' / name).read_bytes())
            originals.append(b''.join(rows))
        for entry in self.mapping['baseline']:
            pixels = self.baseline[tuple(entry['atlas'])]
            for x,y,k in ((64,64,0),(0,0,1),(64,0,2),(127,0,3),(0,64,4),(127,64,5),(0,127,6),(64,127,7),(127,127,8)):
                offset = (y*128+x)*3
                self.assertEqual(pixels[offset:offset+3], originals[entry['signature'][k]][offset:offset+3],entry['atlas'])
            self.assertNotIn((255,0,255),[tuple(pixels[i:i+3]) for i in range(0,len(pixels),3)])

    def test_every_compatible_saved_tile_edge_including_variants(self):
        entries = [(tuple(e['signature']),self.baseline[tuple(e['atlas'])]) for e in self.mapping['baseline']]
        entries += [((c,)*9,pixels) for (c,v),pixels in self.interiors.items()]
        def edge(pixels,side):
            if side=='top':return pixels[:384]
            if side=='bottom':return pixels[-384:]
            x = 0 if side=='left' else 127
            return b''.join(pixels[(y*128+x)*3:(y*128+x)*3+3] for y in range(128))
        comparisons = 0
        for a,ap in entries:
            for b,bp in entries:
                for side,opposite,ia,ib in (('right','left',(3,5,8),(1,4,6)),('bottom','top',(6,7,8),(1,2,3))):
                    if tuple(a[i] for i in ia)==tuple(b[i] for i in ib):
                        self.assertEqual(edge(ap,side),edge(bp,opposite),(a,b,side))
                        comparisons += 1
        self.assertGreater(comparisons,1000)

    def test_shader_free_acceptance_path_and_resource_references(self):
        scene = (ROOT / SCENE).read_text()
        for text in (scene,self.resource):
            for path in re.findall(r'path="res://([^"]+)"',text):
                self.assertTrue((ROOT/path).is_file(),path)
                self.assertNotIn('illustrated_v1/',path)
                self.assertNotIn('diagnostic',path)
            for forbidden in ('ShaderMaterial','.gdshader','/material =','script =','tile_map_data'):
                self.assertNotIn(forbidden,text)
        self.assertEqual(scene.count('type="TileMapLayer"'),1)
        self.assertIn('texture_filter = 1',scene)
        self.assertNotIn('MAGENTA',scene)

    def test_exact_new_paths_tamper_rejection_and_preserved_owner_bytes(self):
        self.assertEqual(len(INPUT_SHA256),6)
        for path in INPUT_SHA256:
            raw = (ROOT/path).read_bytes()
            verify_input(path,raw)
            for bad in (raw+b'CHANGED',raw[1:],raw+raw):
                with self.assertRaises(AssertionError):verify_input(path,bad)
        protected = json.loads((ROOT/'assets/experiments/native_terrain_47_96/illustrated_v1/mapping.json').read_text())['protected_working_sha256']
        for path,digest in protected.items():
            raw = (ROOT/path).read_bytes()
            self.assertEqual(hashlib.sha256(raw).hexdigest(),digest,path)
            with self.assertRaises(AssertionError):verify_input(path,raw)


if __name__ == '__main__':
    unittest.main()
