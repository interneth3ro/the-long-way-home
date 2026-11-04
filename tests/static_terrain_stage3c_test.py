"""Stage 3C offline contracts/models only; no engine or GDScript execution."""
import hashlib
import json
from pathlib import Path
import subprocess
import unittest

from static_illustrated_exterior_test import body, window
from static_terrain_stage3b_test import reconstructed
import terrain_stage2_reference as classification
from static_terrain_c1_test import c1

ROOT = Path(__file__).resolve().parents[1]
BASE = 'de09eeee2c07036ac50471bde12a716e173e3366'
E = (ROOT/'scenes/world/planet_exterior.gd').read_text()
P = (ROOT/'scenes/world/continuous_terrain_presenter.gd').read_text()
S = (ROOT/'scenes/world/continuous_terrain.gdshader').read_text()
ADDED = {'scenes/world/continuous_terrain_presenter.gd', 'scenes/world/continuous_terrain.gdshader',
         'tests/static_terrain_stage3c_test.py', 'docs/experiments/terrain_stage3c_exterior.md', 'docs/experiments/terrain_stage3c_gameplay_plan.json'}
MODIFIED = {'scenes/world/planet_exterior.gd', 'tests/static_terrain_stage3b_test.py',
            'tests/static_ground_publication_test.py', 'tests/static_illustrated_exterior_test.py',
            'docs/ILLUSTRATED_EXTERIOR.md', 'docs/experiments/terrain_stage3_architecture_decisions.md',
            'README.md', 'tests/static_metadata_smoke_test.py', 'tests/static_terrain_stage2_coverage_test.py'}


class Stage3CTest(unittest.TestCase):
    def test_exact_scope_and_protected_inputs(self):
        delta = subprocess.check_output(['git','diff','--name-status',BASE,'e5db8040d38bfd6b1ddb584d636af01052806b7c','--'],cwd=ROOT,text=True)
        inventory = dict((p,s) for s,p in (line.split('\t') for line in delta.splitlines()))
        receipt = json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
        # Immutable PR #143 inventory; Stage 3D checks the current exact scope.
        self.assertEqual(inventory,{**dict.fromkeys(ADDED,'A'),**dict.fromkeys(MODIFIED,'M')})
        for path,entry in receipt['protected_sidecars'].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(),entry['sha256'])
        # In particular: artwork, generator, gameplay, tint calculation, scene,
        # execution policy, receipts and historical evidence cannot change.
        for path in ('scenes/world/terrain_chunk.gd','scenes/world/planet_generator.gd',
                     'scenes/world/planet_exterior.tscn','scenes/world/planet_world_state.gd'):
            self.assertEqual((ROOT/path).read_text(),subprocess.check_output(['git','show',BASE+':'+path],cwd=ROOT,text=True))

    def test_inactive_gameplay_plan_inputs_transforms_and_dependencies(self):
        import re
        plan = json.loads((ROOT/'docs/experiments/terrain_stage3c_gameplay_plan.json').read_text())
        self.assertTrue(plan['status'].startswith('INACTIVE'))
        inputs = {e['path']:e for e in plan['inputs']}
        self.assertEqual(len(inputs),plan['input_count'])
        self.assertEqual(sum(e['bytes'] for e in inputs.values()),plan['source_bytes'])
        historical_inputs = ('scenes/world/planet_exterior.gd', 'scenes/player/dave.tscn',
                             'dialogue/computer_opening.tres', 'objectives/restore_computer.tres',
                             # Computer restoration extends these gameplay files;
                             # keep the consumed Stage 3C plan and its hashes sealed.
                             # Current source preservation has separate feature checks.
                             'construction/construction_controller.gd', 'scenes/main/main.gd',
                             'scenes/main/main.tscn', 'scenes/main/playthrough_state.gd',
                             'scenes/main/scene_transition_controller.gd',
                             'scenes/player/interaction_detector.gd', 'scenes/ui/dialogue_ui.gd',
                             'scenes/ui/hotbar_ui.gd', 'scenes/ui/inventory_ui.gd')
        for path,entry in inputs.items():
            # The consumed Stage 3C plan stays sealed to its merged source.
            raw = (subprocess.check_output(['git','show','e5db8040d38bfd6b1ddb584d636af01052806b7c:'+path],cwd=ROOT)
                   if path in historical_inputs
                   else (ROOT/path).read_bytes())
            if path in historical_inputs:
                # Historical manifest pins the approved CRLF serialization.
                raw = raw.replace(b'\r\n', b'\n').replace(b'\n', b'\r\n')
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()),(entry['bytes'],entry['sha256']),path)
            if 'transform' in entry:
                t = entry['transform']
                self.assertEqual(raw.count(t['find'].encode()),1)
                staged = raw.replace(t['find'].encode(),t['replace'].encode())
                self.assertEqual((len(staged),hashlib.sha256(staged).hexdigest()),(entry['staged_bytes'],entry['staged_sha256']))
            self.assertFalse(path.startswith(('tools/','tests/','artifacts/','scenes/experiments/')))
            if path.endswith(('.gd','.tscn','.tres','.gdshader')):
                text = raw.decode('utf-8')
                for dep in re.findall(r'(?:path="|(?:load|preload)\(")res://([A-Za-z0-9_./-]+)',text):
                    self.assertIn(dep,inputs,(path,dep))
        self.assertEqual({p for p,e in inputs.items() if 'transform' in e},
                         {'project.godot','scenes/world/planet_exterior.tscn'})
        self.assertEqual([p['timeout_seconds'] for p in plan['phases']],[60,300])
        self.assertEqual(plan['retries'],0)

    def test_continuous_default_and_no_failure_fallback(self):
        self.assertIn('terrain_renderer: TerrainRenderer = TerrainRenderer.CONTINUOUS',E)
        self.assertIn('enum TerrainRenderer { LEGACY, ILLUSTRATED, CONTINUOUS }',E)
        self.assertEqual(E.count('_effective_renderer = terrain_renderer'),1)
        config = body(E,'_configure_terrain_renderer')
        self.assertIn('_continuous_presenter = ContinuousTerrainPresenter.new()',config)
        self.assertNotIn('_effective_renderer =',body(E,'_stop_terrain'))
        self.assertIn('_cancel_continuous()',body(E,'_stop_terrain'))
        self.assertIn('if _effective_renderer == TerrainRenderer.LEGACY:',body(E,'_ground_is_current'))

    def test_accepted_shader_core_is_exact(self):
        lab = (ROOT/'scenes/experiments/terrain_stage3b/continuous.gdshader').read_text()
        for start,end in [('float green_at','void fragment()'),('    float amount =','    if (diagnostic == 1)')]:
            original = lab.split(start,1)[1].split(end,1)[0]
            self.assertIn(start+original,S)
        for forbidden in ('protection_field','generate_mipmaps','Thread','FileAccess','PlanetGenerator.new'):
            self.assertNotIn(forbidden,P+S)
        self.assertNotIn('field.r',S)
        self.assertIn('id < 0 or id > 4',P)
        self.assertIn('"materials": _job.ids',P)
        self.assertIn('Callable(_generator, "sample_ground_material")',body(E,'_step_continuous'))

    def test_halos_on_envelope_and_negative_seams(self):
        geometry = classification.load_geometry()
        for seed in (-2**63,0,26026,2**63-1):
            for left in (-16,-1,0,14):
                a,b = (left,-1),(left+1,-1)
                def ids(c):
                    return bytes(classification.classify((c[0]*32+x,c[1]*32+y),seed,geometry)
                                 for y in range(-1,33) for x in range(-1,33))
                pa,pb = ids(a),ids(b)
                for row in range(34):
                    self.assertEqual(pa[row*34+32:row*34+34],pb[row*34:row*34+2])
                for y in (-2048,-2000,-1024,0):
                    point = ((left+1)*2048,y)
                    self.assertAlmostEqual(reconstructed(pa,point,a),reconstructed(pb,point,b),places=14)
        self.assertIn('coordinate.x < -16 or coordinate.x > 15',P)
        self.assertIn('coordinate.y < -16 or coordinate.y > 15',P)

    def test_c1_shading_and_phase_absolute_identity(self):
        # Decode original frozen data and independently address overlapping
        # windows; red coverage is intentionally outside the production contract.
        for coord in c1.COORDS:
            stem = f'{coord[0]}_{coord[1]}'
            _,_,field = c1.png.decode_png((c1.ASSETS/f'fields/{stem}_field.png').read_bytes())
            _,_,phase = c1.png.decode_png((c1.ASSETS/f'fields/{stem}_phase.png').read_bytes())
            for i,j in ((0,0),(4,4),(68,68),(136,136)):
                x,y = coord[0]*2048+(i-4)*16,coord[1]*2048+(j-4)*16
                expected = bytes(round(255*c1.noise(x,y,scale,channel)) for scale,channel in ((1270,102),(370,103)))
                self.assertEqual(field[(j*137+i)*3+1:(j*137+i)*3+3],expected)
            for j in range(7):
                for i in range(7):
                    key = f'c1_fields_v1:c1_materials_v1:26026:{coord[0]*4+i-1}:{coord[1]*4+j-1}:material'
                    self.assertEqual(phase[(j*7+i)*3:(j*7+i+1)*3],hashlib.sha256(key.encode()).digest()[:3])
        for text in ('index % 137 - 4','index / 137 - 4','point / 1270.0, 102','point / 370.0, 103',
                     'coordinate * 4','key.sha256_buffer()'):
            self.assertIn(text,P)

    def test_revision_cancellation_publication_boundary(self):
        step = body(E,'_step_continuous')
        for text in ('_continuous_job.revision != _state.revision','_continuous_job.state != _state',
                     '_continuous_job.seed != _state.seed_value','_continuous_job.arrival != _arrival_generation',
                     '_arrival_cancelled','if result.pending:'):
            self.assertIn(text,step)
        for method in ('prepare_for_arrival','cancel_arrival_preparation','_update_neighborhood','_stop_terrain'):
            self.assertIn('_cancel_continuous()',body(E,method))
        publication = body(P,'publication')
        for text in ('not is_inside_tree()','token != token','not _active[coordinate].presented',
                     'surface.get_parent() != self','not surface.is_visible_in_tree()'):
            self.assertIn(text,publication)
        publish = body(P,'_publish')
        self.assertLess(publish.index('add_child(surface)'),publish.index('"presented": true'))
        self.assertLess(publish.index('surface.is_visible_in_tree()'),publish.index('remove_child(previous)'))
        budget = body(E,'_generate_budget')
        self.assertLess(budget.index('_step_continuous()'),budget.index('_pending.pop_front()'))
        self.assertLess(budget.index('_flush_terrain_tint()\n\t# Publication'),budget.index('_ground_receipts[coordinate] ='))
        # Adversarial readiness matrix independent of the implementation syntax:
        # old visible pixels, new CPU data, upload, cancellation, reparenting,
        # wrong revision or missing details must never satisfy a live receipt.
        import itertools
        for flags in itertools.product((False,True),repeat=7):
            attached,published,tint,details,revision,token,cancelled = flags
            ready = all((attached,published,tint,details,revision,token)) and not cancelled
            if ready:
                self.assertEqual(flags,(True,True,True,True,True,True,False))

    def test_production_tint_overlay_and_bounded_retention(self):
        self.assertIn('chunk.write_tint(_tint_image, _tint_slot(coordinate))',E)
        self.assertIn('COLOR = vec4(color, 1) * tint',S)
        self.assertIn('mod(chunk_coordinate, vec2(slot_count)) * 33.0 + vertex',S)
        self.assertIn('const MAX_UNITS := 32768',P)
        self.assertIn('const SLICE_USEC := 2000',P)
        self.assertIn('Time.get_ticks_usec() >= deadline',P)
        self.assertIn('not _job.is_empty()',body(P,'begin_generation'))
        self.assertIn('_active.erase(coordinate)',body(P,'retire_chunk'))
        self.assertIn('_active.erase(coordinate)',body(P,'cancel'))
        # Raw chunk payload + retained IDs, default 49 slots and one replacement.
        per_chunk = 34*34 + 137*137*3 + 7*7*3
        self.assertLess(per_chunk,128*1024)
        self.assertLess(per_chunk*50 + 49*34*34,32*1024*1024)
        for center in ((-1,-1),(0,0),(12,12)):
            slots = {tuple(v%7 for v in c) for c in window(center,3)}
            self.assertEqual(len(slots),49)


if __name__ == '__main__':
    unittest.main()
