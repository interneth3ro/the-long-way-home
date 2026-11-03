"""Offline Ferrite geometry/registration contracts; no Godot or project execution."""
import hashlib
import re
import struct
import unittest

from static_automatic_transitions_test import ROOT, nodes, vectors, function
from static_low_green_ground_test import inside, edge_distance
from static_ground_rejection_test import authored_geometry
from current_preservation import git_blob


ART = 'assets/environment/exterior/ferrite/faceted_ferrite_10x6.png'


def read(path):
    return (ROOT/path).read_text(encoding='utf-8')


def polygon(text):
    values = list(map(float, re.search(r'footprint = PackedVector2Array\(([^)]+)\)', text)[1].split(',')))
    return list(zip(values[::2], values[1::2]))


class FerriteIntegrationStaticTest(unittest.TestCase):
    def setUp(self):
        self.deposit = read('scenes/world/introductory_ferrite.tres')
        self.points = polygon(self.deposit)
        self.scene = read('scenes/world/planet_exterior.tscn')
        self.nodes = nodes(self.scene)

    def test_exact_grid_rectangle_and_identity(self):
        self.assertEqual(self.points, [(128,128),(768,128),(768,512),(128,512)])
        self.assertEqual((768-128,512-128), (10*64,6*64))
        self.assertTrue(all(v % 64 == 0 for p in self.points for v in p))
        self.assertIn('deposit_id = &"crash_site_ferrite"', self.deposit)
        self.assertIn('resource_type = &"ferrite"', self.deposit)
        self.assertIn('construction_highlight = Color(0.63, 0.76, 0.88, 0.18)', self.deposit)

    def test_approved_rgba_bytes_and_importable_resource(self):
        raw = (ROOT/ART).read_bytes()
        self.assertEqual(raw, (ROOT/'assets/experiments/ferrite_artwork_v1/previews/large_10x6.png').read_bytes())
        self.assertEqual(hashlib.sha256(raw).hexdigest(), '82442d7e11eaf4483202ff22b22060efa4c2f638e66f30694d8b527dd1961c75')
        self.assertEqual(raw[:8], b'\x89PNG\r\n\x1a\n')
        self.assertEqual(struct.unpack('>IIBB',raw[16:26]), (1408,896,8,6))
        for parent in (ROOT/ART).parents:
            self.assertFalse((parent/'.gdignore').exists(), parent)
            if parent == ROOT:
                break
        self.assertIn(f'path="res://{ART}" id="8_ferrite_art"', self.scene)
        self.assertTrue((ROOT/'assets/experiments/ferrite_artwork_v1/.gdignore').is_file())

    def test_canvas_margin_scale_layers_and_placeholder_removal(self):
        header, sprite = self.nodes['FerriteGround/FacetedFerrite']
        self.assertIn('type="Sprite2D"', header)
        self.assertEqual(vectors(sprite), [(96,96),(0.5,0.5)])
        self.assertIn('centered = false', sprite)
        self.assertIn('texture = ExtResource("8_ferrite_art")', sprite)
        self.assertEqual((96+64*0.5,96+64*0.5), self.points[0])
        self.assertEqual((96+(64+1280)*0.5,96+(64+768)*0.5), self.points[2])
        self.assertIn('z_index = -5',self.nodes['FerriteGround'][1])
        self.assertEqual([p for p in self.nodes if p.startswith('FerriteGround/')], ['FerriteGround/FacetedFerrite'])
        for path in ('FerriteGround','FerriteGround/FacetedFerrite','PlanetExterior'):
            for forbidden in ('material =','modulate ='):
                self.assertNotIn(forbidden,self.nodes[path][1])

    def test_protected_apron_and_unchanged_inspection_access(self):
        protected, _, _ = authored_geometry()
        # Convex protected polygon: all apron corners inside implies full coverage.
        for point in [(64,64),(832,64),(832,576),(64,576)]:
            # The apron touches the polygon's east edge; sample infinitesimally inside.
            self.assertTrue(inside((point[0]-0.001,point[1]),protected), point)
        self.assertEqual(vectors(self.nodes['GroundObjects/FerriteInspection'][1]), [(304,280)])
        self.assertTrue(inside((304,280),self.points))
        self.assertIn('radius = 24.0', self.scene)
        inspection = read('scenes/interaction/ferrite_inspection.gd')
        self.assertIn('deposit_id: StringName = &"crash_site_ferrite"',inspection)
        self.assertIn('_progression.discover_ferrite(deposit_id)',inspection)
        self.assertEqual(vectors(self.nodes['Spawns/FromShip'][1]), [(-384,-64)])
        # Entire direct approach is south of hull/hatch and away from rock circles.
        for t in range(101):
            p = (-384+688*t/100, -64+344*t/100)
            for rock in ((-768,336),(704,-432)):
                self.assertGreater(sum((a-b)**2 for a,b in zip(p,rock)), (48+10)**2)
            self.assertGreaterEqual(p[1],-64)

    def test_extraction_points_near_all_edges_rotations_and_adjacent_machines(self):
        definition = read('inventory/extractor.tres')
        self.assertIn('footprint_cells = Vector2i(2, 2)',definition)
        self.assertIn('extraction_point = Vector2(32, 32)',definition)
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite"])',definition)
        # Source-bound independent membership examples. All rotations leave center fixed.
        for turns in range(4):
            center = [(32,32), (64-32,32), (64-32,64-32), (32,64-32)][turns]
            for cell, expected in [((4,4),True),((22,4),True),((4,14),True),((22,14),True),
                                   ((2,4),False),((24,4),False),((4,2),False),((4,16),False)]:
                point = (cell[0]*32+center[0],cell[1]*32+center[1])
                self.assertEqual(inside(point,self.points),expected,(turns,cell))
        # Closed polygon specification: centers on edges/corners qualify even
        # when half the machine extends off mineral ground. Engine verification
        # of Geometry2D's boundary behavior remains an owner acceptance check.
        for point in self.points + [(128,320),(768,320),(448,128),(448,512)]:
            self.assertEqual(edge_distance(point,self.points),0)
        for point in [(127.99,320),(768.01,320),(448,127.99),(448,512.01)]:
            self.assertFalse(inside(point,self.points))
        # Two 64-wide footprints touching at x=192 share the same deposit.
        for x in (128,192):
            self.assertTrue(inside((x+32,160),self.points))
        self.assertEqual(128+64,192)
        rules = read('construction/placement_rules.gd')
        self.assertIn('definition.rotated_point(definition.extraction_point, turns)', rules)
        self.assertIn('state.deposit_at(point, resource_type)', rules)
        self.assertIn('footprint.intersects(other.footprint(machine.cell, machine.turns))',rules)
        self.assertIn('Blocked by a solid obstacle',rules)
        self.assertIn('Out of construction range',rules)

    def test_other_exterior_nodes_and_resource_fields_are_unchanged(self):
        base = '87ca9733749e55e138361bab8ba0fb2ff08d0c7f'
        original = nodes(git_blob(base,'scenes/world/planet_exterior.tscn').decode('utf-8'))
        without_ferrite = lambda entries: {p:(h,re.sub(r'^;.*\n', '',b,flags=re.M).rstrip()) for p,(h,b) in entries.items() if not p.startswith('FerriteGround/')}
        self.assertEqual(without_ferrite(self.nodes),without_ferrite(original))
        old_deposit = git_blob(base,'scenes/world/introductory_ferrite.tres').decode('utf-8')
        without_footprint = lambda text: re.sub(r'^footprint = .*\n?', '',text.replace('\r\n','\n'),flags=re.M)
        self.assertEqual(without_footprint(self.deposit),without_footprint(old_deposit))

    def test_lookup_and_highlights_consume_resource_polygon(self):
        state = read('scenes/world/planet_world_state.gd')
        self.assertIn('preload("res://scenes/world/introductory_ferrite.tres")',state)
        self.assertIn('deposit.contains_point(world_point)',function(state,'deposit_at'))
        self.assertIn('Geometry2D.is_point_in_polygon(world_point, footprint)',read('scenes/world/resource_deposit.gd'))
        highlight = function(read('scenes/world/planet_exterior.gd'),'_refresh_highlights')
        self.assertIn('compatible_resources.has(deposit.resource_type)',highlight)
        self.assertIn('Geometry2D.intersect_polygons(deposit.footprint, boundary)',highlight)
        self.assertIn('highlight.color = deposit.construction_highlight',highlight)


if __name__ == '__main__':
    unittest.main()
