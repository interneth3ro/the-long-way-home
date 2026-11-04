"""Offline Ferrite geometry/registration contracts; no Godot or project execution."""
import hashlib
import math
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
        self.assertIn('footprint_cells = Vector2i(4, 4)',definition)
        self.assertIn('extraction_point = Vector2(64, 64)',definition)
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite"])',definition)
        # Source-bound independent membership examples. All rotations leave center fixed.
        for turns in range(4):
            center = [(64,64), (128-64,64), (128-64,128-64), (64,128-64)][turns]
            self.assertEqual(center, (64,64))
            for cell, expected in [((3,3),True),((21,3),True),((3,13),True),((21,13),True),
                                   ((1,3),False),((23,3),False),((3,1),False),((3,15),False)]:
                point = (cell[0]*32+center[0],cell[1]*32+center[1])
                self.assertEqual(inside(point,self.points),expected,(turns,cell))
        # Closed polygon specification: centers on edges/corners qualify even
        # when half the machine extends off mineral ground. Engine verification
        # of Geometry2D's boundary behavior remains an owner acceptance check.
        for point in self.points + [(128,320),(768,320),(448,128),(448,512)]:
            self.assertEqual(edge_distance(point,self.points),0)
        for point in [(127.99,320),(768.01,320),(448,127.99),(448,512.01)]:
            self.assertFalse(inside(point,self.points))
        # Two 128-wide footprints touching at x=256 share the same deposit.
        for x in (128,256):
            self.assertTrue(inside((x+64,192),self.points))
        self.assertEqual(128+128,256)
        rules = read('construction/placement_rules.gd')
        self.assertIn('definition.rotated_point(definition.extraction_point, turns)', rules)
        self.assertIn('state.deposit_at(point, resource_type)', rules)
        self.assertIn('footprint.intersects(other.footprint(machine.cell, machine.turns))',rules)
        self.assertIn('Blocked by a solid obstacle',rules)
        self.assertIn('Out of construction range',rules)

    def test_extractor_occupancy_grid_and_shared_geometry_contract(self):
        definition = read('inventory/extractor.tres')
        cells = tuple(map(int, re.search(
            r'^footprint_cells = Vector2i\((\d+), (\d+)\)$', definition, re.M).group(1, 2)))
        point = tuple(map(int, re.search(
            r'^extraction_point = Vector2\((\d+), (\d+)\)$', definition, re.M).group(1, 2)))
        coordinates = read('scenes/world/world_coordinates.gd')
        grid = int(re.search(r'CONSTRUCTION_SIZE: int = (\d+)', coordinates)[1])
        size = tuple(v * grid for v in cells)
        self.assertEqual((grid, cells, size, point), (32, (4,4), (128,128), (64,64)))
        # Independent occupancy oracle: a one-cell incursion overlaps, while
        # four-cell separation touches exactly. Includes negative grid origins.
        for cell in [(0,0), (-3,-5), (7,9)]:
            occupied = {(cell[0]+x, cell[1]+y)
                        for x in range(cells[0]) for y in range(cells[1])}
            self.assertEqual(len(occupied), 16)
            adjacent = {(x+4,y) for x,y in occupied}
            overlapping = {(x+3,y) for x,y in occupied}
            self.assertFalse(occupied & adjacent)
            self.assertEqual(len(occupied & overlapping), 4)
            origin = tuple(v * grid for v in cell)
            center = tuple(origin[i]+point[i] for i in range(2))
            anchor = (origin[0]+size[0]/2, origin[1]+size[1])
            self.assertEqual(center, (origin[0]+64, origin[1]+64))
            self.assertEqual(anchor, (origin[0]+64, origin[1]+128))
        self.assertIn('floori(point.x / CONSTRUCTION_SIZE)', coordinates)
        self.assertIn('floori(point.y / CONSTRUCTION_SIZE)', coordinates)
        for world, expected in [(-32.01,-2), (-32,-1), (-0.01,-1), (0,0),
                                (31.99,0), (32,1), (127.99,3), (128,4)]:
            self.assertEqual(math.floor(world/grid), expected)
        rules = read('construction/placement_rules.gd')
        for contract in ['var footprint := definition.footprint(cell, turns)',
                         'shape.size = footprint.size - Vector2.ONE * 0.02',
                         'Transform2D(0.0, footprint.get_center())',
                         'query.collision_mask = BLOCKING_LAYER',
                         'query.collision_mask = player.collision_layer',
                         'Dave is in the footprint']:
            self.assertIn(contract, rules)
        commit = function(read('scenes/world/planet_world_state.gd'), 'deploy_machine_instance')
        self.assertIn('PlacementRules.rejection(self, definition, cell, turns', commit)
        status = function(read('scenes/world/planet_world_state.gd'), 'machine_status')
        self.assertIn('definition.rotated_point(definition.extraction_point, machine.turns)', status)
        self.assertIn('deposit_at(point, resource_type)', status)

    def test_footprint_change_preserves_other_definitions_and_gameplay(self):
        base = '10b3ae89011efbd73118b9b86cf481b73df2c91c'
        original = git_blob(base, 'inventory/extractor.tres').decode().replace('\r\n', '\n')
        restored = read('inventory/extractor.tres').replace(
            'footprint_cells = Vector2i(4, 4)', 'footprint_cells = Vector2i(2, 2)').replace(
            'extraction_point = Vector2(64, 64)', 'extraction_point = Vector2(32, 32)')
        self.assertEqual(restored, original)  # All production/item fields preserved.
        for path in ['inventory/smelter.tres', 'inventory/fabricator.tres',
                     'scenes/world/world_coordinates.gd', 'construction/machine_definition.gd',
                     'construction/placement_rules.gd', 'construction/deployed_machine.gd',
                     'construction/construction_controller.gd', 'scenes/world/planet_world_state.gd',
                     'scenes/player/interaction_detector.gd', 'scenes/ui/machine_ui.gd']:
            with self.subTest(path=path):
                current = read(path)
                if path == 'construction/construction_controller.gd':
                    # PR A moves ghost opacity to the completed Extractor composite.
                    # Every other byte of placement/recovery remains protected.
                    current = current.replace('_ghost.is_ghost = true',
                                              '_ghost.modulate = Color(1, 1, 1, 0.5)')
                self.assertEqual(current, git_blob(base, path).decode().replace('\r\n', '\n'))
        for machine in ['smelter', 'fabricator']:
            self.assertIn('footprint_cells = Vector2i(2, 2)', read(f'inventory/{machine}.tres'))

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
