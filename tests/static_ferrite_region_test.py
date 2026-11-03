"""Offline specification oracle and source contracts, NOT GDScript execution.

Properties exercise real catalog geometry and authoritative crash-site inputs.
Godot parsing, Geometry2D clipping/boundaries and runtime remain unverified.
"""
from collections import Counter, OrderedDict
from dataclasses import dataclass, asdict
from fractions import Fraction
import hashlib
import json
import math
import random
import re
import unittest

from static_ferrite_catalog_test import catalog
from static_ground_rejection_test import authored_geometry
from static_automatic_transitions_test import ROOT, function


SOURCE = (ROOT/'scenes/world/ferrite_region_generator.gd').read_text()
DATA = json.loads((ROOT/catalog.ASSET/'catalog.json').read_text())
VARIANTS = sorted(DATA['variants'], key=lambda v: v['id'])
BY_ID = {v['id']: v for v in VARIANTS}


def constant(name):
    return int(re.search(rf'const {name}: (?:int|float) = (\d+)', SOURCE)[1])


CELLS = constant('REGION_CELLS')
CELL = DATA['terrain_cell_world_units']
REGION = CELLS*CELL
GAP = constant('VISIBLE_GAP')
HALO = constant('NEIGHBOR_HALO')
LIMIT = constant('CACHE_LIMIT')
WEIGHTS = dict(re.findall(r'"(\w+)": (\d+)', re.search(r'const SHAPE_WEIGHTS := (.*)', SOURCE)[1]))
WEIGHTS = {k: int(v) for k,v in WEIGHTS.items()}


def bounds(polygon, pad=0):
    xs, ys = zip(*polygon)
    return min(xs)-pad, min(ys)-pad, max(xs)+pad, max(ys)+pad


def grow(box, pad):
    return box[0]-pad, box[1]-pad, box[2]+pad, box[3]+pad


def intersects(a, b):
    return a[0] <= b[2] and a[2] >= b[0] and a[1] <= b[3] and a[3] >= b[1]


@dataclass(frozen=True)
class Descriptor:
    deposit_id: str
    world_seed: int
    owner_region: tuple
    slot: int
    variant_id: str
    origin_cell: tuple
    catalog_version: str
    generation_version: str
    size_policy_version: str
    illustrated_envelope: tuple
    priority: int


class Oracle:
    def __init__(self, seed=26026):
        self.seed = seed
        self.cache = OrderedDict()
        self.evaluations = 0
        protected, _, _ = authored_geometry()
        intro = (ROOT/'scenes/world/introductory_ferrite.tres').read_text()
        values = [int(v) for v in re.search(r'footprint = PackedVector2Array\(([^)]+)', intro)[1].split(',')]
        self.reserved = [bounds(protected, GAP),
                         bounds(list(zip(values[::2],values[1::2])), 32+GAP)]

    def sample(self, owner, slot, channel):
        key = f'v1:{self.seed}:{owner[0]}:{owner[1]}:{slot}:{channel}'
        return int(hashlib.sha256(key.encode()).hexdigest()[:7], 16)

    def size(self, owner, slot):
        roll = self.sample(owner, slot, 'size_v1') % 100
        return 'small' if roll < 10 else 'medium' if roll < 60 else 'large'

    def variant(self, owner, slot):
        choices = [v for v in VARIANTS if v['size_class'] == self.size(owner, slot)]
        families = {v['shape_family'] for v in choices}
        roll = self.sample(owner, slot, 'shape') % sum(w for f,w in WEIGHTS.items() if f in families)
        for family, weight in WEIGHTS.items():
            if family not in families:
                continue
            roll -= weight
            if roll < 0:
                choices = [v for v in choices if v['shape_family'] == family]
                return choices[self.sample(owner, slot, 'variant') % len(choices)]
        raise AssertionError('unreachable')

    def candidate(self, owner, slot):
        self.evaluations += 1
        rich = self.sample(owner, -1, 'richness') % 100 < constant('RICH_PERCENT')
        if slot >= (constant('CANDIDATE_SLOTS') if rich else constant('ORDINARY_SLOTS')):
            return None
        variant = self.variant(owner, slot)
        origin = tuple(o*CELLS+self.sample(owner,slot,'position_'+axis) % CELLS
                       for o,axis in zip(owner,('x','y')))
        p = tuple(v*CELL for v in origin)
        registration = tuple(v*variant['display_scale'] for v in variant['logical_origin_source_pixels'])
        image = tuple(v*variant['display_scale'] for v in variant['image_size_pixels'])
        box = (p[0]-registration[0], p[1]-registration[1],
               p[0]-registration[0]+image[0], p[1]-registration[1]+image[1])
        if any(intersects(box,reserved) for reserved in self.reserved):
            return None
        return Descriptor(f'ferrite:v1:{self.seed}:{owner[0]}:{owner[1]}:{slot}',
                          self.seed, owner, slot, variant['id'], origin,
                          DATA['catalog_version'], 'v1', 'size_v1', box,
                          self.sample(owner,slot,'priority'))

    def region(self, owner):
        if owner in self.cache:
            return self.cache[owner]
        neighbors = [self.candidate((owner[0]+x,owner[1]+y),slot)
                     for y in range(-HALO,HALO+1) for x in range(-HALO,HALO+1)
                     for slot in range(constant('CANDIDATE_SLOTS'))]
        neighbors = [d for d in neighbors if d]
        result = tuple(d for d in neighbors if d.owner_region == owner and not any(
            (other.priority,other.deposit_id) < (d.priority,d.deposit_id)
            and intersects(grow(d.illustrated_envelope,GAP),other.illustrated_envelope)
            for other in neighbors))
        if len(self.cache) >= LIMIT:
            self.cache.popitem(last=False)
        self.cache[owner] = result
        return result

    def query(self, box):
        reach = (constant('MAX_REACH_CELLS')+1)*CELL
        first = (math.floor((box[0]-reach)/REGION),math.floor((box[1]-reach)/REGION))
        last = (math.floor((box[2]+CELL)/REGION),math.floor((box[3]+CELL)/REGION))
        if (last[0]-first[0]+1)*(last[1]-first[1]+1) > constant('MAX_QUERY_REGIONS'):
            return ()
        return tuple(d for y in range(first[1],last[1]+1) for x in range(first[0],last[0]+1)
                     for d in self.region((x,y)) if intersects(box,d.illustrated_envelope))

    @staticmethod
    def polygon(d):
        return [(x+d.origin_cell[0]*CELL,y+d.origin_cell[1]*CELL)
                for x,y in BY_ID[d.variant_id]['logical_polygon_world_units']]


class FerriteRegionStaticTest(unittest.TestCase):
    def test_source_binds_offline_policy_and_has_no_presentation_dependencies(self):
        # Explicit arithmetic/channel/order contracts bind the oracle to GDScript.
        for expression in (
            '"%s:%d:%d:%d:%d:%s" % [GENERATION_VERSION, _seed, owner.x, owner.y, slot, channel]',
            'key.sha256_text().left(7).hex_to_int()',
            '"small" if roll < 10 else ("medium" if roll < 60 else "large")',
            '_sample(owner, -1, "richness") % 100 < RICH_PERCENT',
            '_sample(owner, slot, "position_x") % REGION_CELLS',
            '_sample(owner, slot, "position_y") % REGION_CELLS',
            '_sample(owner, slot, "shape") % total',
            '_sample(owner, slot, "variant") % choices.size()',
            '_sample(owner, slot, "priority")',
            'return a.deposit_id < b.deposit_id',
            'envelope.intersects(reserved, true)',
            'VISIBLE_GAP).intersects(other.illustrated_envelope, true)',
            'result.make_read_only()', 'accepted.make_read_only()',
            '_cache.erase(_cache.keys()[0])',
            'floori(point.x / REGION_SIZE)', 'floori(point.y / REGION_SIZE)',
            'area.position - Vector2.ONE * reach', 'area.end + Vector2.ONE * CELL',
            'Vector2(vertex[0], vertex[1]) + Vector2(descriptor.origin_cell) * CELL',
        ):
            self.assertIn(expression, SOURCE)
        for forbidden in ('randf(', 'randi(', 'RandomNumberGenerator', 'TerrainChunk',
                          'Sprite2D', 'Texture2D', 'Image.', 'PlanetExterior', '_process('):
            self.assertNotIn(forbidden, SOURCE)
        region = function(SOURCE,'region')
        self.assertEqual(region.count('region('), 1)  # no acceptance recursion
        self.assertIn('if _precedes(other, candidate)', region)
        self.assertIn('catalog.catalog_version == CATALOG_VERSION', SOURCE)
        self.assertIn('MAX_REACH_CELLS', function(SOURCE,'_init'))

    def test_stable_vectors_seed_and_slot_identity(self):
        o = Oracle(-42)
        # Independently known SHA-256 digest prefix, including signed inputs.
        self.assertEqual(o.sample((-2,3),4,'size_v1'),
                         int(hashlib.sha256(b'v1:-42:-2:3:4:size_v1').hexdigest()[:7],16))
        self.assertEqual(o.region((-2,3)), Oracle(-42).region((-2,3)))
        self.assertNotEqual(o.region((-2,3)), Oracle(42).region((-2,3)))
        for d in o.region((-2,3)):
            self.assertEqual(d.deposit_id, f'ferrite:v1:-42:-2:3:{d.slot}')
            self.assertEqual(d.generation_version,'v1')
            self.assertEqual(d.catalog_version,DATA['catalog_version'])

    def test_query_order_eviction_and_no_duplicates(self):
        owners = [(x,y) for y in range(-4,5) for x in range(-4,5)]
        a, b = Oracle(), Oracle()
        expected = {p: a.region(p) for p in owners}
        shuffled = owners.copy()
        random.Random(91).shuffle(shuffled)
        for p in shuffled:
            self.assertEqual(b.region(p),expected[p])
            self.assertLessEqual(len(b.cache),LIMIT)
        self.assertNotIn(owners[0],a.cache)
        self.assertEqual(a.region(owners[0]),expected[owners[0]])
        serialize = lambda ds: json.dumps([asdict(d) for d in ds],sort_keys=True)
        for p in reversed(owners):
            self.assertEqual(serialize(a.region(p)),serialize(expected[p]))
        ids = [d.deposit_id for values in expected.values() for d in values]
        self.assertEqual(len(ids),len(set(ids)))

    def test_all_variant_masks_translated_and_concave_empty_cells(self):
        concave_empty = 0
        for v in VARIANTS:
            mask = (ROOT/v['mask_path']).read_text().splitlines()
            for origin in ((-48,-49),(-1,31),(47,47),(32,32)):
                d = Descriptor('test',1,(0,0),0,v['id'],origin,DATA['catalog_version'],
                               'v1','size_v1',(0,0,0,0),0)
                polygon = Oracle.polygon(d)
                for y in range(-1,v['height_cells']+1):
                    for x in range(-1,v['width_cells']+1):
                        expected = 0 <= y < len(mask) and 0 <= x < len(mask[0]) and mask[y][x] == '#'
                        p = ((origin[0]+x+.5)*CELL,(origin[1]+y+.5)*CELL)
                        self.assertEqual(catalog.contains(p,polygon),expected)
                        if 0 <= y < len(mask) and 0 <= x < len(mask[0]) and not expected:
                            concave_empty += 1
        self.assertGreater(concave_empty,0)

    def test_full_clearance_and_cross_region_spacing(self):
        o = Oracle()
        deposits = [d for y in range(-5,6) for x in range(-5,6) for d in o.region((x,y))]
        self.assertGreater(len(deposits),100)  # fixture coverage, not a density target
        for i,d in enumerate(deposits):
            for reserved in o.reserved:
                self.assertFalse(intersects(d.illustrated_envelope,reserved))
            self.assertTrue(all(d.illustrated_envelope[0] <= x <= d.illustrated_envelope[2]
                                and d.illustrated_envelope[1] <= y <= d.illustrated_envelope[3]
                                for x,y in o.polygon(d)))
            for other in deposits[i+1:]:
                self.assertFalse(intersects(grow(d.illustrated_envelope,GAP),other.illustrated_envelope))

    def test_signed_chunk_region_edges_corners_and_query_completeness(self):
        o = Oracle()
        owners = [(x,y) for y in range(-3,4) for x in range(-3,4)]
        deposits = [d for p in owners for d in o.region(p)]
        crossed = Counter()
        for d in deposits:
            poly = o.polygon(d)
            box = bounds(poly)
            for size,kind in ((REGION,'region'),(2048,'chunk')):
                if math.floor(box[0]/size) != math.floor((box[2]-.01)/size):
                    crossed[kind] += 1
            if box[2] > (d.owner_region[0]+1)*REGION and box[3] > (d.owner_region[1]+1)*REGION:
                crossed['corner'] += 1
            # Every occupied center resolves to the one canonical identity.
            mask = (ROOT/BY_ID[d.variant_id]['mask_path']).read_text().splitlines()
            x,y = next((x,y) for y,row in enumerate(mask) for x,c in enumerate(row) if c == '#')
            p = ((d.origin_cell[0]+x+.5)*CELL,(d.origin_cell[1]+y+.5)*CELL)
            matches = [v.deposit_id for v in o.query((*p,*p)) if catalog.contains(p,o.polygon(v))]
            self.assertEqual(matches,[d.deposit_id])
        self.assertTrue(all(crossed[k] > 0 for k in ('region','chunk','corner')),crossed)
        # Exhaustive nearby owners independently establish query completeness.
        for x,y in ((0,0),(-REGION,-REGION),(REGION,0),(-2048,2048)):
            query = (x-1,y-1,x+1,y+1)
            expected = {d.deposit_id for d in deposits if intersects(query,d.illustrated_envelope)}
            self.assertEqual({d.deposit_id for d in o.query(query)},expected)

    def test_bounded_work_and_halo_proof(self):
        o = Oracle()
        o.region((10,-10))
        self.assertEqual(o.evaluations, (2*HALO+1)**2*constant('CANDIDATE_SLOTS'))
        self.assertEqual(o.evaluations,54)
        before = o.evaluations
        o.region((10,-10))
        self.assertEqual(o.evaluations,before)
        self.assertLess((constant('MAX_REGION_COORDINATE')+1)*CELLS+CELLS-1,2**31)
        self.assertIn('not area.end.is_finite()',function(SOURCE,'query_is_bounded'))
        self.assertIn('area.size.x > REGION_SIZE * MAX_QUERY_REGIONS',function(SOURCE,'query_is_bounded'))
        self.assertIn('absi(owner.x) > MAX_REGION_COORDINATE',function(SOURCE,'region'))
        # The largest padded envelope plus gap cannot reach an owner two away.
        max_width = max(v['image_size_pixels'][0]*v['display_scale'] for v in VARIANTS)
        self.assertLess(max_width+GAP,REGION*HALO)
        self.assertEqual(o.query((-100*REGION,-100*REGION,100*REGION,100*REGION)),())
        self.assertEqual(o.evaluations,before)

    def test_selection_policy_available_family_renormalization(self):
        sizes = {'small':Fraction(1,10),'medium':Fraction(1,2),'large':Fraction(2,5)}
        aggregate = Counter()
        for size,p in sizes.items():
            families = {v['shape_family'] for v in VARIANTS if v['size_class'] == size}
            total = sum(WEIGHTS[f] for f in families)
            for family in families:
                aggregate[family] += p*Fraction(WEIGHTS[family],total)
        self.assertEqual(dict(aggregate),{f:Fraction(w,100) for f,w in WEIGHTS.items()})
        o = Oracle()
        selected = {o.variant((x,7),slot)['id'] for x in range(-100,100) for slot in range(6)}
        self.assertEqual(selected,set(BY_ID))
        self.assertNotIn('distance',function(SOURCE,'_size_class').split('\n',1)[1])

    def test_legacy_contracts_and_persistent_lookup_wiring(self):
        state = (ROOT/'scenes/world/planet_world_state.gd').read_text()
        # Existing point-only compatibility and persistent production contracts.
        status = function(state,'machine_status')
        self.assertIn('definition.rotated_point(definition.extraction_point, machine.turns)',status)
        self.assertIn('deposit_at(point, resource_type)',status)
        self.assertIn('definition.output_per_cycle',function(state,'advance_production'))
        self.assertIn('PlacementRules.rejection',function(state,'deploy_machine_instance'))
        self.assertIn('return _deposits.duplicate()',function(state,'get_deposits'))
        self.assertIn('_ferrite.descriptor_by_id(deposit_id)',function(state,'get_deposit'))
        self.assertIn('_ferrite.query(Rect2(world_point, Vector2.ZERO))',function(state,'deposit_at'))
        self.assertIn('deposit.contains_point(world_point)',function(state,'deposit_at'))
        self.assertIn('parts[2].to_int() != _seed',function(SOURCE,'descriptor_by_id'))
        self.assertIn('descriptor.deposit_id == String(deposit_id)',function(SOURCE,'descriptor_by_id'))
        self.assertIn('var deposit := ResourceDeposit.new()',function(SOURCE,'resource'))
        self.assertIn('_ferrite = FerriteRegionGenerator.new(world_seed)',state)
        intro = (ROOT/'scenes/world/introductory_ferrite.tres').read_text()
        self.assertIn('footprint = PackedVector2Array(128, 128, 768, 128, 768, 512, 128, 512)',intro)
        self.assertIn('deposit_id = &"crash_site_ferrite"',intro)
        self.assertIn('ferrite', (ROOT/'inventory/extractor.tres').read_text())


if __name__ == '__main__':
    unittest.main()
