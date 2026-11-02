"""Reproduce the approved isolated treatment in memory, preserving saved evidence."""
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
SELECTION = ROOT/'docs/experiments/ground_art_approved_treatment.json'


class GroundApprovalTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.selection = json.loads(SELECTION.read_text())
        recipe = ROOT/cls.selection['recipe']['path']
        if hashlib.sha256(recipe.read_bytes().replace(b'\r\n',b'\n')).hexdigest() != cls.selection['recipe']['sha256_lf']:
            raise AssertionError('Approved comparison recipe changed')
        spec = importlib.util.spec_from_file_location('approved_ground_recipe',recipe)
        cls.recipe = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(cls.recipe)
        cls.context = cls.recipe.load_context()

    def test_owner_selection_and_preserved_alternatives(self):
        self.assertEqual(self.selection['status'],'owner-approved isolated artwork prototype')
        self.assertEqual(self.selection['accepted_date'],'2026-11-02')
        self.assertEqual(self.selection['selected']['label'],'CANDIDATE A')
        self.assertEqual(self.selection['selected']['feather_range'],[.15,.85])
        self.assertEqual([(e['label'],e['feather_range']) for e in self.selection['preserved_treatments']],
                         [('CURRENT',[.20,.80]),('CANDIDATE B',[.10,.90])])
        self.assertEqual(self.recipe.TREATMENTS,
                         (('CURRENT',.20,.80),('CANDIDATE A',.15,.85),('CANDIDATE B',.10,.90)))

    def test_approved_input_and_evidence_hashes(self):
        ref = self.selection['comparison_manifest']
        raw = (ROOT/ref['path']).read_bytes()
        self.assertEqual(hashlib.sha256(raw.replace(b'\r\n',b'\n')).hexdigest(),ref['sha256_lf'])
        comparison = json.loads(raw)
        self.assertEqual(self.selection['refined_source_sha256'],comparison['source_sha256'])
        for name,expected in self.selection['refined_source_sha256'].items():
            self.assertEqual(hashlib.sha256((self.recipe.INPUT/'sources'/name).read_bytes()).hexdigest(),expected)

    def test_selected_range_reproduces_all_saved_candidate_a_pixels(self):
        tiles,masks,report = self.recipe.render(self.context,*self.selection['selected']['feather_range'])
        comparison = json.loads((ROOT/self.selection['comparison_manifest']['path']).read_text())
        selected = next(t for t in comparison['treatments'] if t['label'] == self.selection['selected']['label'])
        self.assertEqual(selected['range'],self.selection['selected']['feather_range'])
        self.assertEqual(report,selected['validation'])
        self.assertEqual(len(tiles),45)
        for entry in selected['tile_pixel_sha256']:
            self.assertEqual(hashlib.sha256(tiles[tuple(entry['signature']),entry['variant']]).hexdigest(),entry['sha256'])
        self.assertEqual(report['anchors'],369)
        self.assertEqual(report['compatible_ordered_edge_pairs'],836)
        self.assertEqual(report['assembled_adjacencies'],900)
        self.assertEqual(report['maximum_shared_edge_channel_difference'],0)

    def test_historical_prototype_and_comparison_files_match_accepted_revision(self):
        revision = self.selection['accepted_artwork_revision']
        paths = subprocess.check_output(['git','ls-tree','-r','--name-only',revision,'--',
                                        'assets/experiments/native_terrain_47_96/ground_refinement_v1',
                                        'assets/experiments/native_terrain_47_96/ground_softness_comparison_v1'],cwd=ROOT).decode().splitlines()
        self.assertEqual(len(paths),20)
        for name in paths:
            old = subprocess.check_output(['git','show',revision+':'+name],cwd=ROOT)
            current = (ROOT/name).read_bytes()
            if not name.endswith('.png'):
                old,current = old.replace(b'\r\n',b'\n'),current.replace(b'\r\n',b'\n')
            self.assertEqual(current,old,name)


if __name__ == '__main__':
    unittest.main()
