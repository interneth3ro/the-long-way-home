"""Static broad-phase proof and source-bound arithmetic oracle; no Godot execution."""
import hashlib
import math
import re
import subprocess
import unittest

from static_weathered_earth_test import ROOT, GREEN_ORIGINAL, original_green_bytes, noise, coordinate_random
from static_low_green_ground_test import inside, edge_distance
from native_terrain_preservation import historical_mapping_attributes, historical_test_bytes


def authored_geometry():
    scene = (ROOT/'scenes/world/planet_exterior.tscn').read_text()
    head = scene.split('[node name="FerriteGround"')[0]
    overlays = []
    for raw in re.findall(r'polygon = PackedVector2Array\(([^)]+)\)', head):
        values = [float(v) for v in raw.split(',')]
        overlays.append((list(zip(values[::2], values[1::2])), 256.0))
    source = (ROOT/'scenes/world/planet_exterior.gd').read_text().split('var _player:')[0]
    protected = [(float(x),float(y)) for x,y in re.findall(r'Vector2\((-?\d+), (-?\d+)\)', source)]
    anchors = [(float(x),float(y)) for x,y in re.findall(
        r'\[node name="[^"]+" type="StaticBody2D"[^\]]*\]\s*.*?^position = Vector2\((-?\d+), (-?\d+)\)',
        scene, re.S | re.M)]
    return protected, overlays, anchors


def influence(point, polygon, feather):
    # Same 1-smoothstep expression as immutable PR #95, not a box classifier.
    if inside(point, polygon):
        return 1.0
    t = max(0.0, min(1.0, edge_distance(point, polygon)/feather))
    return 1.0 - t*t*(3.0-2.0*t)


def original_protection(point, protected, overlays, anchors, count=None):
    if count is not None:
        count['precise_calls'] += 1
    if inside(point, protected) or edge_distance(point, protected) < 48.0:
        return True
    if any(math.dist(point, a) < 160.0 for a in anchors):
        return True
    # Preserve original short-circuit order and both overlay loops.
    for polygon, feather in overlays:
        if influence(point, polygon, 48.0) > 0.0:
            return True
    for polygon, feather in overlays:
        if influence(point, polygon, feather) > 0.0:
            return True
    return False


def polygon_bounds(polygon, pad):
    if not polygon:
        polygon = [(0.0,0.0)]
    return (min(x for x,y in polygon)-pad, min(y for x,y in polygon)-pad,
            max(x for x,y in polygon)+pad, max(y for x,y in polygon)+pad)


def rejection_bounds(protected, overlays, anchors):
    regions = [polygon_bounds(protected, 49.0)]
    regions += [polygon_bounds([anchor], 161.0) for anchor in anchors]
    regions += [polygon_bounds(polygon, max(48.0,feather)+1.0) for polygon,feather in overlays]
    return (min(b[0] for b in regions), min(b[1] for b in regions),
            max(b[2] for b in regions), max(b[3] for b in regions))


def has_point(bounds, point):
    left, top, right, bottom = bounds
    return left <= point[0] < right and top <= point[1] < bottom


def material_at(point, seed, geometry, optimized=False, bounds=None, count=None):
    # Source construction uses tile-center world positions. Arbitrary positions
    # below additionally probe polygon/feather corners and rejection-box edges.
    if not optimized or has_point(bounds, point):
        if original_protection(point, *geometry, count):
            return 0
    cover = noise(point[0]/768.0, point[1]/768.0, seed, 8) + noise(point[0]/192.0, point[1]/192.0, seed, 9)*0.18
    if cover < 0.64:
        return 0
    tile = (math.floor(point[0]/64), math.floor(point[1]/64))
    return 1 + min(3, int(coordinate_random(*tile, seed, 10)*4.0))


class GroundRejectionStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.geometry = authored_geometry()
        cls.bounds = rejection_bounds(*cls.geometry)

    def assert_equivalent(self, points, seeds=(26026,1,-42,2147483646)):
        for point in points:
            # Stronger than matching IDs: every precise-positive point is inside
            # the rejecting box, irrespective of seed/noise/selected variant.
            if original_protection(point, *self.geometry):
                self.assertTrue(has_point(self.bounds,point), point)
            for seed in seeds:
                self.assertEqual(material_at(point,seed,self.geometry),
                    material_at(point,seed,self.geometry,True,self.bounds),(point,seed))

    def test_original_oracle_and_exact_source_preservation(self):
        path='scenes/world/planet_generator.gd'
        current=(ROOT/path).read_bytes().replace(b'\r\n',b'\n')
        original=original_green_bytes(path,current)
        self.assertEqual(hashlib.sha256(original).hexdigest(),
            '332971078f58fba3b9a108e8236689130c82071c09292f3644d8d188f59066fa')
        source=current.decode()
        # Only cached bounds initialization/helper and this one material guard
        # may differ. All precise predicates and the noise/variant tail stay exact.
        restored=source.replace('var _ground_protection_bounds: Rect2\n','')
        begin=restored.index('\t# Geometry is fixed')
        end=restored.index('# Integer arithmetic',begin)
        restored=restored[:begin]+'\n\n'+restored[end:]
        guard='\tif _ground_protection_bounds.has_point(point):\n'
        begin=restored.index(guard)
        end=restored.index('\t# Broad clusters',begin)
        body=restored[begin+len(guard):end]
        self.assertTrue(all(line.startswith('\t\t') for line in body.splitlines()))
        restored=restored[:begin]+''.join(line[1:] for line in body.splitlines(keepends=True))+restored[end:]
        self.assertEqual(restored,original.decode())
        for required in ('_polygon_bounds(_protected).grow(DETAIL_CLEARANCE + 1.0)',
            'Rect2(anchor, Vector2.ZERO).grow(161.0)',
            'maxf(DETAIL_CLEARANCE, float(overlay.feather)) + 1.0',
            '_polygon_bounds(overlay.polygon).grow(reach)',
            'bounds = Rect2(polygon[0], Vector2.ZERO)', 'bounds = bounds.expand(vertex)'):
            self.assertIn(required,source)
        self.assertEqual(source.count('_ground_protection_bounds.has_point(point)'),1)
        self.assertEqual(source.count('_ground_protection_bounds ='),3)

    def test_grid_chunk_edges_seeds_and_visit_order(self):
        tiles={(x,y) for y in range(-24,25) for x in range(-24,25)}
        for edge in (-65,-64,-33,-32,-1,0,31,32,63,64):
            tiles.update((edge,y) for y in (-65,-32,-1,0,31,32,64))
            tiles.update((x,edge) for x in (-65,-32,-1,0,31,32,64))
        tiles.update((x,y) for x in (-10000,-1024,1024,10000) for y in (-10000,-1024,1024,10000))
        self.assert_equivalent([((x+.5)*64,(y+.5)*64) for x,y in sorted(tiles)])
        for seed in (26026,-42):
            expected={t:material_at(((t[0]+.5)*64,(t[1]+.5)*64),seed,self.geometry) for t in tiles}
            actual={}
            for x,y in sorted(tiles,reverse=True):
                cx,cy,lx,ly=x//32,y//32,x%32,y%32
                point=((cx*32+lx+.5)*64,(cy*32+ly+.5)*64)
                actual[x,y]=material_at(point,seed,self.geometry,True,self.bounds)
            self.assertEqual(actual,expected)
            self.assertEqual(actual,{t:material_at(((t[0]+.5)*64,(t[1]+.5)*64),seed,self.geometry,True,self.bounds) for t in tiles})

    def test_polygon_edges_corners_and_feather_limits(self):
        protected,overlays,anchors=self.geometry
        self.assertEqual([len(p) for p,f in overlays],[8,5,7,7])
        self.assertEqual(len(protected),6)
        self.assertEqual(len(anchors),4)
        points=[]
        for polygon, reach in [(protected,48.0),*overlays]:
            for a,b in zip(polygon,polygon[1:]+polygon[:1]):
                dx,dy=b[0]-a[0],b[1]-a[1];length=math.hypot(dx,dy)
                nx,ny=-dy/length,dx/length
                for d in (0.0,0.001,-0.001,reach-0.001,reach,reach+0.001):
                    for sign in (-1,1):
                        points.append(((a[0]+b[0])/2+nx*d*sign,(a[1]+b[1])/2+ny*d*sign))
                for x in (-reach-0.001,-reach,0,reach,reach+0.001):
                    for y in (-reach-0.001,0,reach+0.001):
                        points.append((a[0]+x,a[1]+y))
        for x,y in anchors:
            points.extend((x+d,y) for d in (-160.001,-160,-159.999,0,159.999,160,160.001))
        self.assert_equivalent(points)

    def test_inclusive_rejection_extents_and_ferrite(self):
        left,top,right,bottom=self.bounds
        # Rect2 excludes its right/bottom edge; the extra unit must preserve
        # every potentially influenced point before that exclusion matters.
        points=[(x,y) for x in (left-.001,left,left+.001,right-.001,right,right+.001)
                for y in (top-.001,top,top+.001,bottom-.001,bottom,bottom+.001)]
        points += [(304,280),(124,256),(452,256),(288,372),(0,0),(-384,-64)]
        self.assert_equivalent(points)
        self.assertEqual(material_at((304,280),26026,self.geometry,True,self.bounds),0)
        # Nondefault overlay reach and a distant object must enlarge the union.
        synthetic=([(-10,-10),(10,-10),(10,10),(-10,10)],
                   [([(100,100),(200,100),(200,200),(100,200)],400.0)],[(5000,-6000)])
        box=rejection_bounds(*synthetic)
        for point in ((599.99,150),(600,150),(5000+159.999,-6000),(5000+160,-6000)):
            self.assertEqual(material_at(point,1,synthetic),material_at(point,1,synthetic,True,box))

    def test_distant_operation_counts_and_unchanged_systems(self):
        count={'precise_calls':0}
        for y in range(32):
            for x in range(32):
                material_at(((x+1000+.5)*64,(y+1000+.5)*64),26026,self.geometry,True,self.bounds,count)
        self.assertEqual(count['precise_calls'],0)
        protected,overlays,anchors=self.geometry
        self.assertEqual((len(protected)+2*sum(len(p) for p,f in overlays))*1024,61440)
        # Ensure every already tracked file outside the exact correction scope
        # remains byte-identical to original PR #95 (normalizing text newlines).
        # Owner-requested final acceptance notes; no runtime preservation exemption.
        allowed={'scenes/world/planet_generator.gd','tests/static_weathered_earth_test.py',
                 'tests/static_low_green_ground_test.py','tests/static_machine_icons_test.py','README.md',
                 'docs/GAME_VISION.md'}
        files=subprocess.check_output(['git','ls-tree','-r','--name-only',GREEN_ORIGINAL],cwd=ROOT,text=True).splitlines()
        proc=subprocess.Popen(['git','cat-file','--batch'],cwd=ROOT,stdin=subprocess.PIPE,stdout=subprocess.PIPE)
        try:
            for path in files:
                if path in allowed:
                    continue
                proc.stdin.write(f'{GREEN_ORIGINAL}:{path}\n'.encode());proc.stdin.flush()
                header=proc.stdout.readline().split();expected=proc.stdout.read(int(header[2]))
                self.assertEqual(proc.stdout.read(1),b'\n')
                actual=(ROOT/path).read_bytes()
                if not path.endswith(('.png','.ttf')):
                    actual=actual.replace(b'\r\n',b'\n');expected=expected.replace(b'\r\n',b'\n')
                if path == '.gitattributes':
                    actual=historical_mapping_attributes(actual.decode('utf-8')).encode('utf-8')
                actual=historical_test_bytes(path,actual)
                self.assertEqual(actual,expected,path)
        finally:
            proc.stdin.close();self.assertEqual(proc.wait(timeout=10),0);proc.stdout.close()


if __name__=='__main__':
    unittest.main()
