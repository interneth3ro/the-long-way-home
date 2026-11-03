"""3A offline spatial/lifecycle specifications and source contracts.

No Godot, GDScript, ResourceLoader or Geometry2D execution. Mask-cell clipping
is an independent expected-coverage oracle, not a runtime polygon clipper test.
"""
from copy import deepcopy
import math
import unittest

from static_automatic_transitions_test import ROOT, function
from static_ferrite_region_test import Oracle, VARIANTS, CELL, REGION, intersects
from static_ferrite_catalog_test import catalog
from static_ferrite_initialization_test import DATA, validate


PRESENTER = (ROOT/'scenes/world/ferrite_deposit_presenter.gd').read_text()
EXTERIOR = (ROOT/'scenes/world/planet_exterior.gd').read_text()
STATE = (ROOT/'scenes/world/planet_world_state.gd').read_text()
CHUNK, PAGE = 2048, 8192


def retained(center, radius):
    x, y = center
    return ((x-radius)*CHUNK, (y-radius)*CHUNK,
            (x+radius+1)*CHUNK, (y+radius+1)*CHUNK)


def pages(area):
    left, top, right, bottom = area
    return [(x, y, min(x+PAGE, right), min(y+PAGE, bottom))
            for y in range(top, bottom, PAGE) for x in range(left, right, PAGE)]


def nearby(oracle, area):
    return {d.deposit_id: d for page in pages(area) for d in oracle.query(page)}


def clipped_cells(variant, origin, box):
    """Exact cell rectangles intersected with a chunk; empty cells never fill."""
    rows = (ROOT/variant['mask_path']).read_text().splitlines()
    return clip_rows(rows, origin, box)


def clip_rows(rows, origin, box):
    result = {}
    for y, row in enumerate(rows):
        for x, token in enumerate(row):
            if token != '#':
                continue
            left, top = (origin[0]+x)*CELL, (origin[1]+y)*CELL
            clip = (max(left, box[0]), max(top, box[1]),
                    min(left+CELL, box[2]), min(top+CELL, box[3]))
            if clip[0] < clip[2] and clip[1] < clip[3]:
                result[x,y] = clip
    return result


def components(cells):
    remaining, count = set(cells), 0
    while remaining:
        stack = [remaining.pop()]
        count += 1
        while stack:
            x, y = stack.pop()
            for neighbor in ((x-1,y),(x+1,y),(x,y-1),(x,y+1)):
                if neighbor in remaining:
                    remaining.remove(neighbor)
                    stack.append(neighbor)
    return count


class FerritePresentationStaticTest(unittest.TestCase):
    def test_pages_cover_maximum_retention_and_respect_owner_budget(self):
        # All alignment residues of chunk origins modulo the 3072-unit regions.
        for center in ((-4,-4),(-1,0),(0,0),(1,1),(2,2)):
            for radius in range(2,7):
                area = retained(center,radius)
                chunks = pages(area)
                self.assertLessEqual(len(chunks),16)
                self.assertEqual(sum((p[2]-p[0])*(p[3]-p[1]) for p in chunks),
                                 (area[2]-area[0])*(area[3]-area[1]))
                for p in chunks:
                    first = (math.floor((p[0]-832)/REGION),math.floor((p[1]-832)/REGION))
                    last = (math.floor((p[2]+64)/REGION),math.floor((p[3]+64)/REGION))
                    self.assertLessEqual((last[0]-first[0]+1)*(last[1]-first[1]+1),64)
        self.assertIn('4 * WorldCoordinates.CHUNK_SIZE',PRESENTER)

    def test_paged_queries_match_single_query_and_deduplicate_page_edges(self):
        oracle = Oracle()
        for center in ((0,0),(-3,-3),(4,-4)):
            area = retained(center,3)
            self.assertEqual(nearby(oracle,area),{d.deposit_id:d for d in oracle.query(area)})
        self.assertIn('nearby[descriptor.deposit_id] = descriptor',PRESENTER)
        self.assertIn('if not _sprites.has(identity):',PRESENTER)

    def test_repeated_arrival_revisions_eviction_and_bounded_retirement(self):
        oracle, nodes, created = Oracle(), {}, 0
        original = nearby(oracle,retained((0,0),3))
        for center in [(0,0)]*3+[(20,-20),(-20,20),(0,0),(0,0)]:
            wanted = nearby(oracle,retained(center,3))
            previous = nodes.copy()
            for identity in wanted:
                if identity not in nodes:
                    nodes[identity] = object()
                    created += 1
            nodes = {identity:node for identity,node in nodes.items() if identity in wanted}
            for identity in nodes.keys() & previous.keys():
                self.assertIs(nodes[identity],previous[identity])
            self.assertEqual(set(nodes),set(wanted))
            self.assertLessEqual(len(nodes),64*6)
        self.assertEqual(nearby(oracle,retained((0,0),3)),original)
        self.assertGreater(created,0)
        for text in ('area.intersects(_envelopes[identity], true)','remove_child(sprite)',
                     'sprite.queue_free()', '_sprites.erase(identity)'):
            self.assertIn(text,PRESENTER)

    def test_all_variants_register_complete_envelopes_at_signed_boundaries(self):
        for v in VARIANTS:
            for origin in ((-49,-33),(-1,-1),(31,47),(48,32)):
                start = tuple(c*CELL-r*.5 for c,r in zip(origin,v['logical_origin_source_pixels']))
                end = tuple(s+n*.5 for s,n in zip(start,v['image_size_pixels']))
                self.assertEqual(start,(origin[0]*CELL-32,origin[1]*CELL-32))
                self.assertEqual(end,((origin[0]+v['width_cells'])*CELL+32,
                                      (origin[1]+v['height_cells'])*CELL+32))
        for text in ('sprite.centered = false','sprite.scale = Vector2.ONE * registration.scale',
                     'variant.logical_origin_source_pixels','descriptor.origin_cell',
                     'texture.get_size() * scale_value) != descriptor.illustrated_envelope'):
            self.assertIn(text,PRESENTER)

    def test_padding_only_intersection_retains_until_whole_image_leaves(self):
        v = VARIANTS[0]
        width, height = v['width_cells']*CELL, v['height_cells']*CELL
        for x,y in ((0,0),(-CHUNK,-CHUNK),(REGION,REGION)):
            envelope = (x-32,y-32,x+width+32,y+height+32)
            for area in ((x-64,y-64,x-1,y-1),(x+width+1,y,x+width+32,y+height)):
                self.assertTrue(intersects(envelope,area))
                self.assertFalse(intersects((x,y,x+width,y+height),area))
            self.assertFalse(intersects(envelope,(x+width+33,y,x+width+64,y+height)))
        query = function((ROOT/'scenes/world/ferrite_region_generator.gd').read_text(),'query')
        self.assertIn('area.intersects(descriptor.illustrated_envelope, true)',query)

    def test_cross_boundary_owner_can_leave_while_artwork_remains(self):
        oracle = Oracle()
        crossed = []
        for page in pages(retained((0,0),6)):
            for d in oracle.query(page):
                box = d.illustrated_envelope
                for axis in (0,1):
                    edge = (d.owner_region[axis]+1)*REGION
                    if box[axis+2] > edge:
                        point = list(d.origin_cell)
                        point = [p*CELL for p in point]
                        point[axis] = edge+1
                        area = (*point,point[0]+1,point[1]+1)
                        self.assertIn(d.deposit_id,nearby(oracle,area))
                        crossed.append(d)
        self.assertTrue(crossed)

    def test_exact_mask_clips_across_four_chunks_preserve_concave_notches(self):
        empty_count = 0
        for v in VARIANTS:
            rows = (ROOT/v['mask_path']).read_text().splitlines()
            for boundary in (-CHUNK,0,CHUNK,REGION):
                origin = (boundary//CELL-2,boundary//CELL-2)
                polygon = [(x+origin[0]*CELL,y+origin[1]*CELL)
                           for x,y in v['logical_polygon_world_units']]
                clips = {}
                left = math.floor(origin[0]*CELL/CHUNK)
                top = math.floor(origin[1]*CELL/CHUNK)
                for cy in range(top,top+2):
                    for cx in range(left,left+2):
                        for cell,rect in clipped_cells(v,origin,(cx*CHUNK,cy*CHUNK,(cx+1)*CHUNK,(cy+1)*CHUNK)).items():
                            self.assertNotIn(cell,clips)
                            clips[cell] = rect
                self.assertEqual(len(clips),v['occupied_cells'])
                self.assertEqual(sum((r[2]-r[0])*(r[3]-r[1]) for r in clips.values()),
                                 v['occupied_cells']*CELL*CELL)
                for y,row in enumerate(rows):
                    for x,token in enumerate(row):
                        expected = token == '#'
                        self.assertEqual((x,y) in clips,expected)
                        point = ((origin[0]+x+.5)*CELL,(origin[1]+y+.5)*CELL)
                        self.assertEqual(catalog.contains(point,polygon),expected)
                        empty_count += not expected
        self.assertGreater(empty_count,0)

    def test_multi_piece_clipping_contract_uses_every_polygon(self):
        # Synthetic U tests the multi-piece contract without adding a catalog variant.
        # Its connecting base lies below the chunk; both upper arms must survive.
        rows = ['##..##','##..##','##..##','######','######']
        _, polygon = catalog.geometry(rows)
        cells = clip_rows(rows,(0,30),(0,0,CHUNK,CHUNK))
        self.assertEqual(components(cells),2)
        self.assertEqual(len(cells),8)
        self.assertFalse(catalog.contains((3*CELL,1*CELL),polygon))
        highlight = function(EXTERIOR,'_refresh_highlights')
        self.assertIn('for polygon in Geometry2D.intersect_polygons(deposit.footprint, boundary):',highlight)
        self.assertNotIn('[0]',highlight)
        self.assertNotIn('convex_hull',highlight)

    def test_highlight_spatial_filter_identity_color_cleanup_and_chunk_scope(self):
        highlight = function(EXTERIOR,'_refresh_highlights')
        for text in ('_ferrite_presenter.highlight_deposits(_state, _ferrite_token)',
                     'compatible_resources.has(deposit.resource_type)',
                     'if not _chunks.has(coordinate):','highlight.color = deposit.construction_highlight',
                     '_construction_definition == null','world_to_chunk(bounds.position)',
                     'world_to_chunk(bounds.end)'):
            self.assertIn(text,highlight)
        self.assertNotIn('_state.get_deposits()',highlight)
        self.assertNotIn('for coordinate in _chunks:',highlight)
        self.assertLess(highlight.index('_clear_highlights()'),highlight.index('_construction_definition == null'))
        clear = function(EXTERIOR,'_clear_highlights')
        self.assertIn('_highlights.remove_child(child)',clear)
        self.assertIn('child.queue_free()',clear)

    def test_neighborhood_change_gate_layers_and_no_per_frame_rebuild(self):
        update = function(EXTERIOR,'_update_neighborhood')
        self.assertLess(update.index('center == _center and _state.revision == _revision'),
                        update.index('_ferrite_presenter.request'))
        self.assertEqual(EXTERIOR.count('_ferrite_presenter.request('),1)
        self.assertNotIn('_process(',PRESENTER)
        self.assertNotIn('refresh(',function(EXTERIOR,'_process'))
        for text in ('_ferrite_presenter.z_index = -5','_highlights.z_index = -4'):
            self.assertIn(text,EXTERIOR)
        for forbidden in ('Image.', 'ImageTexture', 'modulate', 'rotation', 'flip_h', 'flip_v', 'material ='):
            self.assertNotIn(forbidden,PRESENTER)

    def test_texture_failures_block_and_cache_is_catalog_bounded(self):
        for text in ('ResourceLoader.exists(path, "Texture2D")', 'texture == null',
                     'texture.get_size() != expected','_textures[variant.id] = texture',
                     'state.is_resource_generation_ready()', 'Correct the input/package and restart'):
            self.assertIn(text,PRESENTER)
        self.assertLess(PRESENTER.index('_textures.get(variant.id)'),PRESENTER.index('load(path)'))
        step = function(PRESENTER,'step')
        self.assertLess(step.index('_registration(state, _nearby[identity])'),
                        step.index('Sprite2D.new()'))
        self.assertIn('get_tree().paused = true',function(EXTERIOR,'_update_neighborhood'))
        for bad in (None, '', 'wrong.png', '../outside.png',VARIANTS[1]['png_path']):
            data = deepcopy(DATA)
            data['variants'][0]['png_path'] = bad
            self.assertEqual(validate(data),'png_path')

    def test_authored_sprite_separate_and_simulation_ignores_presentation(self):
        # Scene/intro inputs stay unchanged; legacy preservation regressions pin geometry.
        scene = (ROOT/'scenes/world/planet_exterior.tscn').read_text()
        self.assertIn('position = Vector2(96, 96)',scene)
        self.assertIn('faceted_ferrite_10x6.png',scene)
        self.assertNotIn('crash_site_ferrite',PRESENTER)
        for name in ('get_deposit','deposit_at','machine_status','advance_production'):
            method = function(STATE,name)
            self.assertNotIn('presenter',method)
            self.assertNotIn('_chunks',method)
        d = next(iter(nearby(Oracle(),retained((0,0),3)).values()))
        expected = Oracle.polygon(d)
        # Evict its owner descriptors and reconstruct without any artwork nodes.
        oracle = Oracle()
        for x in range(40):
            oracle.region((x,40))
        reconstructed = next(r for r in oracle.region(d.owner_region) if r.deposit_id == d.deposit_id)
        self.assertEqual(Oracle.polygon(reconstructed),expected)
        getter = function((ROOT/'scenes/world/ferrite_region_generator.gd').read_text(),'variant_metadata')
        self.assertIn('duplicate(true)',getter)
        self.assertNotIn('load(',getter)


if __name__ == '__main__':
    unittest.main()
