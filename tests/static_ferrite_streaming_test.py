"""3B non-engine specifications + source contracts; no GDScript/runtime execution.

The accepted generation oracle supplies real catalog descriptors. Scheduling is
an independent Python specification, not proof of Godot parsing or frame times.
"""
from collections import Counter
import math
import unittest

from static_automatic_transitions_test import ROOT, function
from static_ferrite_region_test import Oracle, VARIANTS, REGION, intersects, grow
from static_ferrite_presentation_test import retained, pages, nearby

PRESENTER = (ROOT/'scenes/world/ferrite_deposit_presenter.gd').read_text()
EXTERIOR = (ROOT/'scenes/world/planet_exterior.gd').read_text()
GENERATOR = (ROOT/'scenes/world/ferrite_region_generator.gd').read_text()
STATE = (ROOT/'scenes/world/planet_world_state.gd').read_text()
TRANSITION = (ROOT/'scenes/main/scene_transition_controller.gd').read_text()


def owners(area):
    """Union of the ORIGINAL page halos, including inclusive signed edges."""
    result = set()
    for p in pages(area):
        first = [math.floor((p[i]-832)/REGION) for i in (0, 1)]
        last = [math.floor((p[i+2]+64)/REGION) for i in (0, 1)]
        result.update((x, y) for y in range(first[1], last[1]+1)
                      for x in range(first[0], last[0]+1))
    center = [math.floor((area[i]+area[i+2])/2/REGION) for i in (0, 1)]
    return sorted(result, key=lambda p: (max(abs(p[i]-center[i]) for i in (0, 1)), p[1], p[0]))


class Schedule:
    """Observable work contract: required owners, validation, sprites, lookahead."""
    def __init__(self, seed=26026):
        self.oracle = Oracle(seed)
        self.regions, self.sprites, self.textures = {}, {}, set()
        self.visits, self.events = Counter(), []
        self.token, self.active, self.revision = 0, False, 0

    def cancel(self):
        self.token += 1
        self.active = False
        self.work = []

    def request(self, area, revision=0):
        self.cancel()
        if revision != self.revision:
            self.regions.clear()
        self.revision, self.area = revision, area
        self.required, self.future = owners(area), owners(grow(area, 2048))
        self.regions = {o: d for o, d in self.regions.items() if o in self.future}
        self.sprites = {k: d for k, d in self.sprites.items() if intersects(area, d.illustrated_envelope)}
        self.work = [('region', o) for o in self.required if o not in self.regions]
        self.work += [('collect', None)]
        self.active, self.ready = True, False
        return self.token

    def collect(self, region_set, area):
        return {d.deposit_id: d for o in region_set for d in self.regions[o]
                if intersects(area, d.illustrated_envelope)}

    def step(self, token, required_only=False):
        if not self.active or token != self.token or not self.work:
            return
        if required_only and self.ready:
            return
        kind, value = self.work.pop(0)
        self.events.append((kind, value))
        if kind in ('region', 'prefetch_region'):
            self.visits[value] += 1
            self.regions[value] = self.oracle.region(value)
        elif kind == 'collect':
            self.nearby = self.collect(self.required, self.area)
            ids = sorted(k for k in self.nearby if k not in self.sprites)
            self.work = [('validate', k) for k in ids] + [('sprite', k) for k in ids] + [('ready', None)]
        elif kind == 'validate':
            self.textures.add(self.nearby[value].variant_id)
        elif kind == 'sprite':
            self.sprites.setdefault(value, self.nearby[value])
        elif kind == 'ready':
            self.ready = True
            self.work = [('prefetch_region', o) for o in self.future if o not in self.regions]
            self.work += [('prefetch_collect', None)]
        elif kind == 'prefetch_collect':
            data = self.collect(self.future, grow(self.area, 2048))
            self.work = [('prefetch_texture', d.variant_id) for _, d in sorted(data.items())]
        elif kind == 'prefetch_texture':
            self.textures.add(value)

    def drain(self, token, required_only=False):
        for _ in range(2000):
            if not self.work or (required_only and self.ready):
                return
            self.step(token, required_only)
        raise AssertionError('bounded work failed to drain')


class FerriteStreamingStaticTest(unittest.TestCase):
    def test_query_membership_matches_prior_pages_at_signed_boundaries(self):
        for seed in (26026, -7):
            for center, radius in (((-1,-1),3), ((0,0),3), ((3,-3),2), ((-4,4),6)):
                area = retained(center, radius)
                oracle = Oracle(seed)
                actual = {d.deposit_id: d for o in owners(area) for d in oracle.region(o)
                          if intersects(area, d.illustrated_envelope)}
                self.assertEqual(actual, nearby(Oracle(seed), area))
        query = function(GENERATOR, 'query_owners')
        for text in ('query_is_bounded(area)', 'area.position - Vector2.ONE * reach',
                     'area.end + Vector2.ONE * CELL', 'result.append(Vector2i(x, y))'):
            self.assertIn(text, query)

    def test_owner_planning_bounds_all_allowed_sizes_and_alignment_residues(self):
        for radius in range(2, 7):
            for x in range(-3, 3):
                for y in range(-3, 3):
                    area = retained((x,y), radius)
                    self.assertLessEqual(len(owners(grow(area, 2048))), 144)
        self.assertEqual(len(owners(retained((-1,-1),3))), 36)
        self.assertIn('MAX_SNAPSHOT_REGIONS: int = 144', PRESENTER)
        self.assertIn('_lookahead = area.grow(WorldCoordinates.CHUNK_SIZE)', PRESENTER)
        self.assertIn('unique[owner] = true', function(PRESENTER, '_owners'))
        self.assertNotIn('get_deposit_region', function(PRESENTER, '_owners'))
        self.assertIn('CACHE_LIMIT: int = 32', GENERATOR)

    def test_required_precedes_lookahead_and_only_needed_textures_at_arrival(self):
        model = Schedule()
        token = model.request(retained((-1,-1),3))
        model.drain(token, required_only=True)
        expected = nearby(Oracle(), model.area)
        self.assertEqual(model.sprites, expected)
        self.assertEqual(model.textures, {d.variant_id for d in expected.values()})
        self.assertFalse(any(k.startswith('prefetch') for k,_ in model.events))
        self.assertEqual(sum(model.visits.values()), 36)
        self.assertTrue(all(n == 1 for n in model.visits.values()))
        step = function(PRESENTER, 'step')
        self.assertLess(step.index('if required_only:'), step.index('_future_pending.pop_front()'))
        self.assertLess(step.index('Sprite2D.new()'), step.index('if required_only:'))
        self.assertNotIn('Sprite2D.new()', step[step.index('if required_only:'):])
        self.assertNotIn('for variant', PRESENTER)

    def test_stationary_queue_drains_and_speculative_sprites_never_appear(self):
        model = Schedule()
        token = model.request(retained((-1,-1),3))
        model.drain(token)
        self.assertFalse(model.work)
        self.assertEqual(model.sprites, nearby(Oracle(), model.area))
        expected_future = nearby(Oracle(), grow(model.area, 2048))
        self.assertEqual(model.textures, {d.variant_id for d in expected_future.values()})
        self.assertTrue(all(n == 1 for n in model.visits.values()))
        process = function(EXTERIOR, '_process')
        self.assertLess(process.index('_update_neighborhood()'), process.index('_service_ferrite()'))
        self.assertNotIn('_service_ferrite', function(EXTERIOR, '_update_neighborhood'))
        self.assertEqual(function(EXTERIOR, '_service_ferrite').count('.step('), 1)

    def test_cached_return_reuses_completed_registrations_without_per_id_work(self):
        model = Schedule()
        token = model.request(retained((-1,-1),3))
        model.drain(token)
        model.cancel()
        token = model.request(model.area)
        model.events.clear()
        model.drain(token, required_only=True)
        self.assertEqual([kind for kind,_ in model.events],['collect','ready'])
        step = function(PRESENTER,'step')
        self.assertIn('_pending_ids = _required_ids.filter',step)
        self.assertIn('return not _sprites.has(identity)',step)

    def test_reversals_reuse_stable_sprites_and_keep_memory_bounded(self):
        model = Schedule()
        initial = None
        for center in ((-1,-1),(0,-1),(1,0),(0,-1),(-1,-1),(50,-50),(-1,-1)):
            token = model.request(retained(center,3))
            before = model.sprites.copy()
            model.drain(token)
            self.assertEqual(model.sprites, nearby(Oracle(), model.area))
            for k in before.keys() & model.sprites.keys():
                self.assertIs(before[k], model.sprites[k])
            self.assertLessEqual(len(model.regions),144)
            self.assertLessEqual(len(model.sprites),144*6)
            self.assertLessEqual(len(model.textures),10)
            if initial is None:
                initial = model.sprites.copy()
        self.assertEqual(initial,model.sprites)
        request = function(PRESENTER, 'request')
        self.assertIn('_regions.erase(owner)',request)
        self.assertIn('area.intersects(_envelopes[identity], true)',request)

    def test_cancel_and_superseding_request_reject_every_old_phase(self):
        for phase in ('region','collect','validate','sprite','ready','prefetch_region','prefetch_texture'):
            model = Schedule()
            old = model.request(retained((-1,-1),3))
            while model.work and model.work[0][0] != phase:
                model.step(old)
            self.assertTrue(model.work, phase)
            model.cancel()
            before = (dict(model.sprites), set(model.textures), dict(model.regions))
            model.step(old)
            self.assertEqual(before,(model.sprites,model.textures,model.regions))
            current = model.request(retained((8,-8),3))
            model.step(old)
            self.assertFalse(model.ready)
            model.drain(current)
            self.assertEqual(model.sprites,nearby(Oracle(),model.area))
        step = function(PRESENTER,'step')
        self.assertLess(step.index('token != _token'),step.index('get_deposit_region'))
        self.assertIn('not matches_context(state)',step)
        self.assertIn('not is_inside_tree()',step)
        self.assertIn('cancel()',function(PRESENTER,'_exit_tree'))
        cancel = function(TRANSITION,'cancel_quick_transition')
        self.assertIn('_arrival_world.call("cancel_arrival_preparation")',cancel)
        self.assertIn('_arrival_generation += 1',function(EXTERIOR,'_exit_tree'))
        rollback = function(TRANSITION,'_perform_quick_transition')
        rearm = 'await source.call("prepare_for_arrival", player, progression.planet)'
        self.assertIn(rearm,rollback)
        self.assertLess(rollback.index(rearm),rollback.index('_quick_committed = true'))

    def test_state_seed_and_revision_invalidation_and_arrival_token(self):
        context = function(PRESENTER,'matches_context')
        for text in ('_active','_state == state','_seed == state.seed_value','_revision == state.revision'):
            self.assertIn(text,context)
        request = function(PRESENTER,'request')
        for text in ('_state != state','_seed != state.seed_value','_revision != state.revision',
                     '_regions.clear()','_footprints.clear()','_variants.clear()','_textures.clear()',
                     '_clear_sprites()'):
            self.assertIn(text,request)
        arrival = function(EXTERIOR,'prepare_for_arrival')
        for text in ('required_ready(_ferrite_token)','arrival == _arrival_generation',
                     '_service_ferrite(true)','await get_tree().process_frame'):
            self.assertIn(text,arrival)
        model = Schedule()
        token = model.request(retained((-1,-1),3))
        model.drain(token)
        token = model.request(model.area, revision=1)
        self.assertEqual(model.regions,{})
        model.drain(token)
        self.assertEqual(model.sprites,nearby(Oracle(),model.area))

    def test_geometry_deduplicated_before_reconstruction_and_reused(self):
        highlight = function(PRESENTER,'highlight_deposits')
        self.assertIn('if not _footprints.has(identity):',highlight)
        self.assertIn('state.deposit_resource(_nearby[identity])',highlight)
        self.assertNotIn('query_',highlight)
        self.assertNotIn('get_deposits_in_area',EXTERIOR)
        self.assertIn('_footprints.erase(identity)',function(PRESENTER,'step'))
        registration = function(PRESENTER,'_registration')
        self.assertIn('if not _variants.has(variant_id):',registration)
        self.assertIn('duplicate(true)',function(GENERATOR,'variant_metadata'))
        # No mutable generator catalog escapes through the new planning API.
        self.assertNotIn('_by_id',function(GENERATOR,'query_owners'))

    def test_highlight_coalescing_immediate_clear_and_exact_clipping(self):
        for name in ('_update_neighborhood','_generate_budget'):
            self.assertIn('_highlights_dirty = true',function(EXTERIOR,name))
            self.assertNotIn('_refresh_highlights()',function(EXTERIOR,name))
        setter = function(EXTERIOR,'set_construction_definition')
        self.assertIn('_clear_highlights()',setter)
        self.assertNotIn('_refresh_highlights()',setter)
        self.assertEqual(function(EXTERIOR,'_process').count('_flush_highlights()'),1)
        flush = function(EXTERIOR,'_flush_highlights')
        self.assertIn('_highlights_dirty = false',flush)
        highlight = function(EXTERIOR,'_refresh_highlights')
        self.assertLess(highlight.index('_construction_definition == null'),highlight.index('highlight_deposits'))
        self.assertIn('for polygon in Geometry2D.intersect_polygons(deposit.footprint, boundary):',highlight)

    def test_all_variants_resolve_without_catalog_or_simulation_changes(self):
        self.assertEqual(len(VARIANTS),10)
        for v in VARIANTS:
            self.assertTrue((ROOT/v['png_path']).is_file())
            self.assertEqual(v['display_scale'],.5)
            self.assertEqual(v['logical_origin_source_pixels'],[64,64])
        for name in ('deposit_at','get_deposit','machine_status','advance_production'):
            self.assertNotIn('presenter',function(STATE,name))
            self.assertNotIn('required_ready',function(STATE,name))
        self.assertIn('planet.advance_production(delta)',(ROOT/'scenes/main/playthrough_state.gd').read_text())


if __name__ == '__main__':
    unittest.main()
