"""Offline full-atlas inventory, saved raster, deterministic and preservation checks."""
from terrain_integration_preservation import historical_input_hashes
from unittest.mock import patch
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest
from ground_art_preservation import without_validation_changes

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('full_ground',ROOT/'tools/ground-refinement-full-atlas.py')
full = importlib.util.module_from_spec(spec)
spec.loader.exec_module(full)


class FullGroundAtlasTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.soft,cls.context,cls.approval,cls.mapping = full.load_context()
        cls.study,cls.bake,cls.prototype,cls.sources,cls.original = cls.context
        cls.manifest = json.loads((full.OUTPUT/'manifest.json').read_text())
        cls.files = {name:(full.OUTPUT/name).read_bytes() for name in cls.manifest['output_sha256']}
        cls.tiles = full.saved_tiles(cls.study,cls.bake,cls.mapping,cls.files)
        cls.masks = {tuple(e['signature']):[cls.bake.smooth((v-.15)/.70) for v in cls.bake.mask(tuple(e['signature']))]
                     for e in cls.mapping['baseline']}

    def test_exact_inventory_coordinates_variants_and_unconfigured_slots(self):
        m = self.manifest
        self.assertEqual((m['baseline_count'],m['unique_signatures'],m['configured_records']),(94,94,98))
        self.assertEqual(m['families'],dict(earth=47,green=47))
        self.assertEqual(len(self.tiles),98)
        for kind in ('baseline','interiors'):
            fields = ('atlas','signature','family','pattern') if kind == 'baseline' else ('atlas','signature','variant')
            self.assertEqual([{k:e[k] for k in fields} for e in m[kind]],
                             [{k:e[k] for k in fields} for e in self.mapping[kind]])
            self.assertEqual({e['alternative_id'] for e in m[kind]},{0})
            for e in m[kind]:
                self.assertEqual(full.digest(self.tiles[tuple(e['signature']),e['variant']]),e['pixel_sha256'])
        self.assertEqual(m['unused_baseline_slots'],[[10,1],[10,5]])
        atlas = self.bake.decode_png(self.files['baseline_94.png'])
        for x,y in m['unused_baseline_slots']:
            self.assertEqual(self.study.crop(atlas[2],1536,x,y),bytes(128*128*3))

    def test_all_saved_edges_anchors_contours_placeholders_and_corner_relationships(self):
        report = self.soft.validate_tiles(self.context,self.tiles,self.masks)
        self.assertEqual(report['anchors'],846)
        self.assertEqual(report['compatible_ordered_edge_pairs'],2788)
        self.assertEqual(report['maximum_shared_edge_channel_difference'],0)
        self.assertEqual(report,{k:v for k,v in self.manifest['validation'].items()
                                 if k != 'ordered_edge_pairs_by_direction'})
        counts = {}
        for label,(side,opp,ia,ib) in zip(('horizontal','vertical'),self.soft.RELATIONSHIPS):
            count = 0
            for (a,av),ap in self.tiles.items():
                for (b,bv),bp in self.tiles.items():
                    if tuple(a[i] for i in ia) == tuple(b[i] for i in ib):
                        self.assertEqual(self.study.edge(ap,side),self.study.edge(bp,opp))
                        count += 1
            counts[label] = count
        self.assertEqual(counts,self.manifest['validation']['ordered_edge_pairs_by_direction'])
        # Diagonal compatibility is equality of the touching corner signature.
        for (a,av),ap in self.tiles.items():
            for (b,bv),bp in self.tiles.items():
                if a[8] == b[1]:
                    self.assertEqual(ap[-3:],bp[:3])
                if a[6] == b[3]:
                    self.assertEqual(ap[-384:-381],bp[381:384])

    def test_every_preview_uses_identical_saved_layout_and_atlas_pixels(self):
        for name,layout in self.manifest['layouts'].items():
            if name in self.prototype['layouts']:
                self.assertEqual(layout,self.prototype['layouts'][name])
            expected = self.study.pair(name.replace('_',' '),
                                      full.preview_image(self.soft,self.study,layout,self.original,name),
                                      full.preview_image(self.soft,self.study,layout,self.tiles,name))
            self.assertEqual(self.files['previews/'+name+'.png'],self.bake.encode_png(*expected))
            for y,row in enumerate(layout):
                for x,e in enumerate(row):
                    a = tuple(e['signature'])
                    for dx,dy,side,opp,ia,ib in ((1,0,*self.soft.RELATIONSHIPS[0]),(0,1,*self.soft.RELATIONSHIPS[1])):
                        if x+dx < len(row) and y+dy < len(layout):
                            # A 24-pixel gutter separates the two material samples.
                            if name == 'abc_repetition' and dy == 1 and y == 1:
                                continue
                            neighbor = layout[y+dy][x+dx]; b = tuple(neighbor['signature'])
                            self.assertEqual(tuple(a[i] for i in ia),tuple(b[i] for i in ib))
                            self.assertEqual(self.study.edge(self.tiles[a,e['variant']],side),
                                             self.study.edge(self.tiles[b,neighbor['variant']],opp))

    def test_approved_subset_and_bc_bytes_unchanged(self):
        accepted = json.loads((ROOT/self.approval['comparison_manifest']['path']).read_text())
        selected = next(t for t in accepted['treatments'] if t['label'] == 'CANDIDATE A')
        for e in selected['tile_pixel_sha256']:
            self.assertEqual(full.digest(self.tiles[tuple(e['signature']),e['variant']]),e['sha256'])
        self.assertEqual(self.files['interiors_bc.png'],(self.soft.INPUT/'interiors_bc.png').read_bytes())
        for c in (0,1):
            self.assertEqual(self.tiles[(c,)*9,'A'],self.sources[c])
            self.assertEqual(len({self.tiles[(c,)*9,v] for v in 'ABC'}),3)

    def test_reject_missing_records_anchor_edge_and_contour_damage(self):
        damaged = dict(self.tiles); damaged.pop(next(iter(damaged)))
        with self.assertRaises(ValueError):
            self.soft.validate_tiles(self.context,damaged,self.masks)
        for x,y in ((64,64),(127,12)):
            damaged = dict(self.tiles); pixels = bytearray(damaged[(0,)*9,'A'])
            pixels[(y*128+x)*3] ^= 1; damaged[(0,)*9,'A'] = bytes(pixels)
            with self.assertRaises(ValueError):
                self.soft.validate_tiles(self.context,damaged,self.masks)
        masks = copy.deepcopy(self.masks); masks[(0,)*9][129] = 1
        with self.assertRaises(ValueError):
            self.soft.validate_tiles(self.context,self.tiles,masks)

    def test_readonly_exact_regeneration_and_output_inventory(self):
        # Verify current inputs, then reproduce the immutable historical receipt.
        reader = full.protected_inputs
        with patch.object(full, 'protected_inputs', side_effect=lambda: historical_input_hashes(reader())):
            outputs = full.build()
        for name,raw in outputs.items():
            self.assertEqual((full.OUTPUT/name).read_bytes(),raw,name)
        for name,raw in self.files.items():
            self.assertEqual(full.digest(raw),self.manifest['output_sha256'][name])
        self.assertEqual({p.relative_to(full.OUTPUT).as_posix() for p in full.OUTPUT.rglob('*') if p.is_file()},
                         {*self.files,'manifest.json','README.md'})

    def test_preservation_and_no_production_references(self):
        self.assertEqual(historical_input_hashes(full.protected_inputs()),self.manifest['protected_working_input_sha256'])
        changed = subprocess.check_output(['git','diff',full.START,'--name-only','--diff-filter=MDRT'],cwd=ROOT).decode().splitlines()
        changed = without_validation_changes(changed)
        self.assertEqual(changed,[],'Existing tracked files must remain unchanged')
        for prefix in ('scenes','assets','project.godot'):
            paths = subprocess.check_output(['git','ls-tree','-r','--name-only',full.START,'--',prefix],cwd=ROOT).decode().splitlines()
            for name in paths:
                if name.endswith(('.tscn','.tres','.gd','.gdshader','.godot')):
                    self.assertNotIn(b'ground_refinement_full_v1',(ROOT/name).read_bytes(),name)


if __name__ == '__main__':
    unittest.main()
