"""Production activation contracts and independent finite models; no Godot.

These checks inspect GDScript/shader text and immutable historical inputs. They
do not parse with the engine, execute project code or establish runtime behavior.
"""
import hashlib
import itertools
import math
from pathlib import Path
import re
import subprocess
import unittest
from current_preservation import SEALED_REVIEW_HEAD, git_blob, sealed_input


ROOT = Path(__file__).resolve().parents[1]
EXTERIOR = 'scenes/world/planet_exterior.gd'
CHUNK = 'scenes/world/terrain_chunk.gd'
SCENE = 'scenes/world/planet_exterior.tscn'
SHADER = 'scenes/world/illustrated_terrain_tint.gdshader'
SOURCE = (ROOT/EXTERIOR).read_text(encoding='utf-8')
GROUND = (ROOT/CHUNK).read_text(encoding='utf-8')
TINT = (ROOT/SHADER).read_text(encoding='utf-8')


def body(source, name):
    return re.search(r'^(?:static )?func ' + name + r'\(.*?(?=^(?:static )?func |\Z)', source, re.M | re.S)[0].rstrip()


def window(center, radius):
    return {(center[0]+x, center[1]+y) for x in range(-radius, radius+1) for y in range(-radius, radius+1)}


def slot(chunk, count):
    return tuple(c % count * 33 for c in chunk)


def vertices(chunk):
    return {(chunk[0]*32+x, chunk[1]*32+y) for x in range(33) for y in range(33)}


class IllustratedExteriorStaticTest(unittest.TestCase):
    def test_proposed_native_package_is_closed_bounded_and_non_playable(self):
        import json
        proposal = json.loads((ROOT/'docs/experiments/illustrated_exterior_stage.json').read_text())
        inputs = proposal['inputs']
        self.assertEqual(len(inputs), 83)
        self.assertEqual(proposal['source_commit'], 'seal.review_head')
        classes = {}
        # Historical closure must use the same committed universe as its seal,
        # not current global classes or working resource bytes.
        for path in subprocess.check_output(['git','ls-tree','-r','--name-only',SEALED_REVIEW_HEAD],cwd=ROOT,text=True).splitlines():
            if not path.endswith('.gd'):
                continue
            match = re.search(r'^class_name (\w+)', git_blob(SEALED_REVIEW_HEAD, path).decode('utf-8'), re.M)
            if match:
                classes[match[1]] = path
        for path,record in inputs.items():
            raw = sealed_input(path, record)
            self.assertEqual((len(raw),hashlib.sha256(raw).hexdigest()), (record['bytes'],record['sha256']), path)
            if path.endswith(('.gd','.tscn','.tres','.gdshader')):
                text = raw.decode('utf-8')
                for dependency in re.findall(r'(?:path="|(?:load|preload)\(")res://([A-Za-z0-9_./-]+)',text):
                    self.assertIn(dependency,inputs,(path,dependency))
                if path.endswith('.gd'):
                    for name,dependency in classes.items():
                        if re.search(r'\b'+name+r'\b',text):
                            self.assertIn(dependency,inputs,(path,name))
        self.assertEqual({p for p in inputs if p.endswith('.tscn')}, {SCENE})
        self.assertNotIn('project.godot',inputs)
        self.assertFalse(any(p.endswith('.exe') or p.startswith(('.godot/','tools/')) for p in inputs))
        self.assertEqual([p['timeout_seconds'] for p in proposal['phases']], [60,30])
        self.assertEqual([p['name'] for p in proposal['phases']], ['Import','Assertions'])
        self.assertEqual(len(set(proposal['allowed_generated_paths'])),41)
        self.assertEqual(proposal['process_policy']['combined_output_limit_bytes'],1048576)
        harness = git_blob(SEALED_REVIEW_HEAD, 'tests/illustrated_exterior_native_validation.gd').decode('utf-8')
        for marker in ('initial 25 chunks','Ground-only suppression','Stale retirement rejected',
                       'Absolute negative-coordinate assignment','Shared tint dimensions',
                       'Revision borders agree','Failure stops further processing',
                       'Legacy avoids illustrated initialization','Illustrated exterior validation failures: %d'):
            self.assertIn(marker,harness)
        self.assertIsNone(re.search(r'^\s*while ',harness,re.M))
        code = '\n'.join(line.split('#',1)[0] for line in harness.splitlines())
        for forbidden in ('Input.', 'DisplayServer', 'benchmark', 'main_v2.tscn'):
            self.assertNotIn(forbidden,code)

    def test_default_selection_is_locked_once_and_legacy_does_no_illustrated_work(self):
        self.assertIn('terrain_renderer: TerrainRenderer = TerrainRenderer.CONTINUOUS', SOURCE)
        configure = body(SOURCE, '_configure_terrain_renderer')
        order = ['if not _renderer_configured:', '_renderer_configured = true',
                 '_effective_renderer = terrain_renderer', 'if _effective_renderer == TerrainRenderer.ILLUSTRATED:',
                 '_terrain_presenter.initialize()', 'Image.create(', 'ShaderMaterial.new()', 'load(']
        self.assertEqual([configure.index(x) for x in order], sorted(configure.index(x) for x in order))
        self.assertEqual(SOURCE.count('_effective_renderer = terrain_renderer'), 1)
        self.assertNotIn('preload(', SOURCE)
        self.assertIn('if _effective_renderer != TerrainRenderer.ILLUSTRATED:\n\t\treturn true', body(SOURCE, '_present_illustrated_chunk'))
        self.assertIn('if _effective_renderer == TerrainRenderer.LEGACY:\n\t\treturn true', body(SOURCE, '_retire_illustrated_chunk'))
        budget = body(SOURCE, '_generate_budget')
        self.assertIn('chunk.configure(coordinate, _generator, _state, _effective_renderer == TerrainRenderer.LEGACY)', budget)
        self.assertIn('if _effective_renderer != TerrainRenderer.LEGACY:\n\t\t\tchunk.write_tint(', budget)
        self.assertNotIn('initialize(', budget)

    def test_ground_only_gate_preserves_exact_draw_commands_and_details(self):
        drawing = body(GROUND, '_draw')
        self.assertIn('if _draw_legacy_ground:', drawing)
        self.assertIn('draw_legacy_ground: bool = true', body(GROUND, 'configure'))
        self.assertEqual(GROUND.count('draw_polygon('), 1)
        self.assertIn('\t\t\tif _draw_legacy_ground:\n\t\t\t\t_ground_materials[', GROUND)

    def test_tint_sampling_halo_and_detail_generation_are_exact(self):
        writer = body(GROUND, 'write_tint')
        self.assertIn('_colors[y * VERTEX_WIDTH + x]', writer)
        self.assertNotIn('sample_', writer)
        self.assertIn('WorldCoordinates.CHUNK_TILES + 2', GROUND)

    def test_lifecycle_order_uses_existing_tokens_and_preserves_failed_replacement(self):
        budget = body(SOURCE, '_generate_budget')
        order = ['_pending.pop_front()', 'chunk.configure(', '_present_illustrated_chunk(coordinate)',
                 'chunk.write_tint(', '_sync_tint_borders(coordinate)', 'remove_child(previous)',
                 'add_child(chunk)', '_chunks[coordinate] = chunk', '\n\t_flush_terrain_tint()']
        self.assertEqual([budget.index(x) for x in order], sorted(budget.index(x) for x in order))
        present = body(SOURCE, '_present_illustrated_chunk')
        order = ['_terrain_generation += 1', 'var token := _terrain_generation',
                 'begin_generation(coordinate, token)', '_terrain_tokens[coordinate] = token',
                 'present_chunk(coordinate, token,']
        self.assertEqual([present.index(x) for x in order], sorted(present.index(x) for x in order))
        self.assertIn('Callable(_generator, "sample_ground_material"), _state.seed_value, TerrainResolver.RULE_VERSION', present)
        retire = body(SOURCE, '_retire_illustrated_chunk')
        self.assertLess(retire.index('retire_chunk(coordinate, _terrain_tokens[coordinate])'), retire.index('_terrain_tokens.erase'))
        self.assertLess(retire.index('if result.ok:'), retire.index('_tint_image.fill_rect('))
        neighborhood = body(SOURCE, '_update_neighborhood')
        self.assertLess(neighborhood.index('_retire_illustrated_chunk(coordinate)'), neighborhood.index('remove_child(chunk)'))
        # Native token validation/32x32 ownership is inherited byte-for-byte.

    def test_failure_is_retained_reported_and_bounded_without_retry(self):
        budget = body(SOURCE, '_generate_budget')
        self.assertIn('_pending.push_front(coordinate)\n\t\t\tbreak', budget)
        for name in ('_generate_budget', '_update_neighborhood', '_configure_terrain_renderer'):
            self.assertIn('if not _terrain_failure.is_empty():\n\t\treturn', body(SOURCE, name))
        self.assertIn('not _terrain_failure.is_empty()', body(SOURCE, '_process'))
        arrival = body(SOURCE, 'prepare_for_arrival')
        self.assertIn('not _pending.is_empty() or not _ferrite_presenter.required_ready(_ferrite_token)', arrival)
        self.assertIn('and _terrain_failure.is_empty() and arrival == _arrival_generation:', arrival)
        self.assertIn('if _terrain_failure.is_empty():', body(SOURCE, '_stop_terrain'))
        self.assertIn('_terrain_failure.duplicate(true)', body(SOURCE, 'terrain_failure'))
        for name in ('_present_illustrated_chunk', '_retire_illustrated_chunk'):
            self.assertIn('_stop_terrain(result)', body(SOURCE, name))
        # Failure on second request preserves first success, old replacement,
        # failed request and remaining queue. Later frames attempt nothing.
        queue, shown, stopped, attempts = [(-1,0), (0,0), (1,0)], {(0,0): 'old'}, False, 0
        for frame in range(20):
            if stopped:
                continue
            for _ in range(min(2, len(queue))):
                c = queue.pop(0)
                attempts += 1
                if c == (0,0):
                    queue.insert(0, c)
                    stopped = True
                    break
                shown[c] = 'new'
        self.assertEqual(attempts, 2)
        self.assertEqual(queue, [(0,0), (1,0)])
        self.assertEqual(shown, {(0,0): 'old', (-1,0): 'new'})

    def test_initial_25_revision_retention_movement_and_reload_model(self):
        for text in ('loading_radius: int = 2', 'retention_margin: int = 1', 'chunks_per_frame: int = 2',
                     'range(mini(budget, _pending.size()))', '_pending.clear()',
                     '_chunks[coordinate].state_revision != _revision', '_distance(coordinate, center) > retained_radius'):
            self.assertIn(text, SOURCE)
        chunks = {}
        def update(center, revision):
            for c in list(chunks):
                if max(abs(c[i]-center[i]) for i in (0,1)) > 3:
                    del chunks[c]
            pending = {c for c, r in chunks.items() if r != revision} | (window(center, 2)-chunks.keys())
            count = len(pending)
            while pending:
                batch = sorted(pending)[:2]
                self.assertLessEqual(len(batch), 2)
                for c in batch:
                    chunks[c] = revision
                    pending.remove(c)
            self.assertTrue(set(chunks) <= window(center, 3))
            return count
        self.assertEqual(update((0,0), 0), 25)
        self.assertEqual(update((0,0), 0), 0)  # retained arrival
        self.assertEqual(update((1,0), 0), 5)
        self.assertEqual(update((1,0), 1), 30)  # includes outer retained column
        self.assertEqual(update((-20,-20), 1), 25)
        self.assertEqual(update((0,0), 1), 25)
        self.assertEqual(len(chunks), 25)

    def test_bounded_tint_slots_negative_coordinates_and_retirement_isolation(self):
        self.assertIn('_tint_slots = 2 * (loading_radius + retention_margin) + 1', SOURCE)
        self.assertIn('posmod(coordinate.x, _tint_slots), posmod(coordinate.y, _tint_slots)', body(SOURCE, '_tint_slot'))
        for radius in range(2,7):
            count = 2*radius+1
            for center in ((0,0), (-1,-1), (-32,31), (100,-200)):
                owned = window(center, radius)
                slots = {c: slot(c, count) for c in owned}
                self.assertEqual(len(set(slots.values())), len(owned))
                # All old chunks sharing an incoming slot have retired first.
                incoming = window((center[0]+1, center[1]-1), radius)
                retained = owned & incoming
                for c in incoming-owned:
                    self.assertNotIn(slot(c,count), {slots[n] for n in retained})
                for x,y in slots.values():
                    self.assertTrue(0 <= x <= count*33-33 and 0 <= y <= count*33-33)
        self.assertEqual(7*33, 231)
        self.assertEqual(231*231*16, 853776)  # fixed default upload, not a timing
        self.assertIn('Rect2i(_tint_slot(coordinate),\n\t\t\tVector2i.ONE * TerrainChunk.VERTEX_WIDTH)', SOURCE)

    def test_fragment_uv_stays_in_own_slot_and_matches_cpu_for_negatives(self):
        for equation in ('floor(cell_point / 32.0)', 'cell_point - chunk * 32.0',
                         'mod(chunk, vec2(slot_count)) * 33.0 + vertex',
                         '(texel + vec2(0.5)) / (slot_count * 33.0)', 'COLOR *= texture(tint_field, field_uv)'):
            self.assertIn(equation, TINT)
        self.assertIn('filter_linear, repeat_disable', TINT)
        self.assertNotIn('source_color', TINT)
        for chunk in itertools.product(range(-8,9), repeat=2):
            for local in ((0,0), (.001,31.999), (31.999,.001), (16.5,16.5)):
                point = tuple(chunk[i]*32+local[i] for i in (0,1))
                shader_chunk = tuple(math.floor(v/32) for v in point)
                self.assertEqual(shader_chunk, chunk)
                texel = tuple((shader_chunk[i] % 7)*33 + point[i]-shader_chunk[i]*32 for i in (0,1))
                for i in (0,1):
                    self.assertTrue(slot(chunk,7)[i] <= texel[i] <= slot(chunk,7)[i]+32)
                    uv = (texel[i]+.5)/231
                    self.assertAlmostEqual(uv*231-.5, texel[i])
        self.assertIn('exterior_x * world_point.x + exterior_y * world_point.y + exterior_origin', TINT)
        self.assertIn('var inverse := global_transform.affine_inverse()', SOURCE)

    def test_shared_vertex_halo_override_and_pending_revision_continuity_model(self):
        from static_weathered_earth_test import earth_tint
        def tint(v, edited=False):
            # Asymmetric field plus a stored override on a four-chunk seam.
            samples = [(0.55,0.30,0.18,1) if edited and (v[0]+x,v[1]+y)==(-1,-1)
                       else (.3+(v[0]+x)*.0001,.31+(v[1]+y)*.0002,.26,1)
                       for x,y in ((-1,-1),(0,-1),(-1,0),(0,0))]
            return earth_tint(tuple(sum(c[i] for c in samples)/4 for i in range(4)))
        chunks = [(-1,-1),(0,-1),(-1,0),(0,0)]
        fields = {c:{v:tint(v) for v in vertices(c)} for c in chunks}
        old_border = fields[(0,0)][(0,0)]
        # A successful revision replacement refreshes only its shared borders,
        # even when the three neighbors remain on their older revision.
        fields[(-1,-1)] = {v:tint(v,True) for v in vertices((-1,-1))}
        for c in chunks[1:]:
            shared = fields[c].keys() & fields[(-1,-1)].keys()
            for v in shared:
                fields[c][v] = fields[(-1,-1)][v]
        self.assertNotEqual(fields[(0,0)][(0,0)], old_border)
        for a,b in itertools.combinations(chunks,2):
            for v in fields[a].keys() & fields[b].keys():
                self.assertEqual(fields[a][v], fields[b][v])
        borders = body(SOURCE, '_sync_tint_borders')
        for required in ('range(-1, 2)', 'not _chunks.has(neighbor)', 'bounds.intersection(',
                         '_tint_image.blit_rect(_tint_image, source,', '_tint_slot(neighbor) + shared.position - neighbor_origin'):
            self.assertIn(required, borders)
        self.assertNotIn('sample_', borders)

    def test_shared_upload_is_bounded_and_has_no_extra_frame_loop(self):
        self.assertEqual(SOURCE.count('Image.create('), 1)
        self.assertEqual(SOURCE.count('ShaderMaterial.new()'), 1)
        self.assertEqual(SOURCE.count('_tint_texture.update('), 1)
        self.assertIn('Image.FORMAT_RGBAF', SOURCE)
        self.assertIn('if _tint_dirty:\n\t\t_tint_texture.update(_tint_image)\n\t\t_tint_dirty = false', SOURCE)
        budget = body(SOURCE, '_generate_budget')
        self.assertIn('if _pending.is_empty():\n\t\t_flush_terrain_tint()\n\t\treturn', budget)
        self.assertLess(budget.index('if _pending.is_empty():'), budget.index('_highlights_dirty = true'))
        self.assertIn('\n\t_flush_terrain_tint()', budget)
        self.assertEqual(SOURCE.count('func _process('), 1)
        self.assertNotIn('func _physics_process', SOURCE)
        self.assertNotIn('await ', budget)
        self.assertNotIn('_terrain_generation = 0', body(SOURCE, '_configure_terrain_renderer'))

    def test_ordered_masks_feather_state_and_gameplay_remain_exact(self):
        arrival = body(SOURCE, 'prepare_for_arrival')
        generator = (ROOT/'scenes/world/planet_generator.gd').read_text(encoding='utf-8')
        sample = body(generator,'sample_color')
        self.assertLess(sample.index('_noise('), sample.index('state.terrain_color('))
        self.assertLess(sample.index('state.terrain_color('), sample.index('for overlay in _overlays:'))
        self.assertIn('_initialize_world(state)', arrival)
        self.assertIn('"feather": 256.0', body(SOURCE, '_initialize_world'))
        self.assertIn('1.0 - smoothstep(0.0, feather, _edge_distance(point, polygon))', generator)

    def test_scene_draw_order_and_resource_references(self):
        scene = (ROOT/SCENE).read_text(encoding='utf-8')
        # Verify today's complete accepted scene first, then retain the original
        # PR #104-vs-#103 Z-only comparison. Current Z/resource checks stay below.
        self.assertIn('chunk.z_index = -10', SOURCE)
        self.assertIn('_highlights.z_index = -4', SOURCE)
        self.assertIn('[node name="FerriteGround" type="Node2D" parent="."]\nz_index = -5', scene)
        self.assertEqual(scene.count('type="TileMapLayer"'), 1)
        for path in re.findall(r'(?:path="|load\(")res://([^"]+)', scene + SOURCE):
            self.assertTrue((ROOT/path).is_file(), path)
        self.assertNotIn('tile_set =', scene)


if __name__ == '__main__':
    unittest.main()
