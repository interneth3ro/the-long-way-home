"""Read scene text only; no Godot, project imports or runtime simulation."""

from pathlib import Path
import math
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]


def resource(text, identifier):
    pattern = rf'\[sub_resource [^\n]*id="{identifier}"\]\n(.*?)(?=\n\[)'
    return re.search(pattern, text, re.S)[1]


def vector_values(text):
    return [tuple(map(float, pair.split(",")))
            for pair in re.findall(r"Vector2\(([^)]+)\)", text)]


def cross(a, b, c):
    return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])


def edges(polygon):
    return list(zip(polygon, polygon[1:] + polygon[:1]))


def distance(point, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    if dx == 0 and dy == 0:
        return math.dist(point, a)
    t = max(0, min(1, ((point[0] - a[0]) * dx
                      + (point[1] - a[1]) * dy) / (dx * dx + dy * dy)))
    return math.hypot(point[0] - a[0] - t * dx, point[1] - a[1] - t * dy)


def source_point(point):
    return point[0] + 768, point[1] + 512


class PortConsoleGeometryTest(unittest.TestCase):
    def setUp(self):
        self.scene = (ROOT / "scenes/world/ship_interior_v2.tscn").read_text()
        raw = resource(self.scene, "Footprint_PortConsole")
        numbers = list(map(float, re.search(
            r"PackedVector2Array\(([^)]+)\)", raw)[1].split(",")))
        self.polygon = [source_point(p) for p in zip(numbers[::2], numbers[1::2])]
        production = (ROOT / "scenes/world/production_ship_interior_v2.tscn").read_text()
        scale = vector_values(production.split('[node name="ProductionShipInteriorV2"')[1])[0]
        self.assertEqual(scale, (1.25, 1.25))
        dave = (ROOT / "scenes/player/dave.tscn").read_text()
        radius = float(re.search(r"radius = ([\d.]+)", resource(
            dave, "CircleShape2D_feet"))[1])
        self.assertEqual(radius, 10)
        self.radius = radius / scale[0]

    def test_convex_and_confined_to_console_and_wall_mount(self):
        p = self.polygon
        self.assertTrue(all(cross(p[i], p[(i + 1) % len(p)],
                                  p[(i + 2) % len(p)]) > 0 for i in range(len(p))))
        self.assertTrue(all(240 <= x <= 345 and 307.5 <= y <= 435 for x, y in p))

    def test_reported_upper_surface_and_rear_pocket_are_blocked(self):
        # Image-space witnesses from approved art and the owner's Test 2 capture.
        # (290,338) approximates the yellow feet-circle center, not sprite head.
        for point in [(290, 338), (265, 350), (315, 335), (330, 355),
                      (250, 340), (275, 330)]:
            with self.subTest(point=point):
                self.assertTrue(all(cross(a, b, point) >= 0
                                    for a, b in edges(self.polygon)))

    def test_rear_edges_join_existing_wall_without_a_passage(self):
        wall = [source_point(p) for p in vector_values(
            resource(self.scene, "Segment_Wall01"))]
        side = [source_point(p) for p in vector_values(
            resource(self.scene, "Segment_Wall23"))]
        a, b = self.polygon[:2]
        # A full rear edge lies on Wall01; a side edge also lies on Wall23.
        # Contact is continuous, rather than a gap merely too small for Dave.
        self.assertLess(distance(a, *wall), 1e-8)
        self.assertLess(distance(b, *wall), 1e-8)
        self.assertGreater(math.dist(a, b), 2 * self.radius)
        self.assertLess(distance(self.polygon[-1], *side), 1e-8)
        self.assertLess(distance(a, *side), 1e-8)

    def test_floor_approaches_remain_clear_for_feet_circle(self):
        # Entire east approach and south approach, not just endpoints.
        for a, b in [((370, 490), (370, 340)), ((300, 490), (300, 455))]:
            for step in range(151):
                t = step / 150
                point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                self.assertFalse(all(cross(c, d, point) >= 0
                                     for c, d in edges(self.polygon)))
                self.assertGreater(min(distance(point, c, d)
                                       for c, d in edges(self.polygon)), self.radius)


class PortContainerGeometryTest(unittest.TestCase):
    def setUp(self):
        self.scene = (ROOT / "scenes/world/ship_interior_v2.tscn").read_text()
        match = re.search(
            r'\[node name="PortContainer" type="StaticBody2D" parent="CollisionContent"\]'
            r'\n(.*?)(?=\n\[)', self.scene, re.S)
        self.assertIsNotNone(match, "Container must have its own physics body")
        self.body = match[1]
        self.center = source_point(vector_values(self.body)[0])
        self.radius = float(re.search(r"radius = ([\d.]+)", resource(
            self.scene, "Footprint_PortContainer"))[1])
        self.raw_shape = resource(self.scene, "Footprint_PortContainer")
        # Permit the old circle to reach coverage/attachment assertions in the
        # negative control; an explicit resource-type assertion rejects it too.
        height = re.search(r"height = ([\d.]+)", self.raw_shape)
        self.height = float(height[1]) if height else 2 * self.radius
        offset = self.height / 2 - self.radius
        self.axis = [(self.center[0], self.center[1] - offset),
                     (self.center[0], self.center[1] + offset)]
        self.polygons = []
        self.walls = []
        for kind, raw in re.findall(
                r'\[sub_resource type="([^"]+)"[^\n]*\]\n(.*?)(?=\n\[)',
                self.scene, re.S):
            if kind == "ConvexPolygonShape2D":
                values = list(map(float, re.search(
                    r"PackedVector2Array\(([^)]+)\)", raw)[1].split(",")))
                self.polygons.append([source_point(p)
                                      for p in zip(values[::2], values[1::2])])
            elif kind == "SegmentShape2D":
                self.walls.append([source_point(p) for p in vector_values(raw)])

    def test_independent_capsule_covers_full_obstruction(self):
        # Background: lid near y=282-303, base down to y=337, wall at y=285.
        self.assertIn('type="CapsuleShape2D" id="Footprint_PortContainer"', self.scene)
        self.assertEqual(self.center, (381, 309))
        self.assertEqual((self.radius, self.height), (18, 58))
        self.assertNotIn("rotation", self.body)
        self.assertIn("collision_layer = 1", self.body)
        self.assertIn("collision_mask = 1", self.body)
        self.assertIn(
            '[node name="Shape" type="CollisionShape2D" parent="CollisionContent/PortContainer"]\n'
            'shape = SubResource("Footprint_PortContainer")', self.scene)
        for witness in [(381, 320), (367, 320), (395, 320), (381, 334),
                        (381, 283), (366, 293), (396, 293), (381, 290)]:
            self.assertLess(distance(witness, *self.axis), self.radius)

    def test_rear_cap_overlaps_existing_wall_continuously(self):
        wall = [source_point(p) for p in vector_values(
            resource(self.scene, "Segment_Wall02"))]
        self.assertEqual(wall, [(350, 285), (465, 285)])
        self.assertLess(self.axis[0][1] - self.radius, wall[0][1])
        # A continuous wall chord inside the capsule blocks diagonal passage,
        # not merely a gap smaller than the player's collision diameter.
        for x in range(370, 393):
            self.assertLess(distance((x, 285), *self.axis), self.radius)

    def test_accessible_routes_clear_all_obstacles_for_daves_feet(self):
        production = (ROOT / "scenes/world/production_ship_interior_v2.tscn").read_text()
        scale = vector_values(production.split('[node name="ProductionShipInteriorV2"')[1])[0]
        self.assertEqual(scale, (1.25, 1.25))
        dave = (ROOT / "scenes/player/dave.tscn").read_text()
        radius = float(re.search(r"radius = ([\d.]+)", resource(
            dave, "CircleShape2D_feet"))[1])
        self.assertEqual(radius, 10)
        feet_radius = radius / scale[0]
        # Feet-circle centers: west, front and east routes; rear is now blocked.
        route = [(354, 307), (354, 360), (420, 360), (420, 307)]
        blockers = self.walls + [edge for p in self.polygons for edge in edges(p)]
        for a, b in zip(route, route[1:]):
            for step in range(201):
                t = step / 200
                point = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
                self.assertGreater(distance(point, *self.axis), self.radius + feet_radius)
                self.assertGreater(min(distance(point, c, d)
                                       for c, d in blockers), feet_radius)
                for polygon in self.polygons:
                    self.assertFalse(all(cross(c, d, point) >= 0
                                         for c, d in edges(polygon)))


if __name__ == "__main__":
    unittest.main()
