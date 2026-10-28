"""P3 source/scene/geometry inspection only; never executes GDScript or Godot."""

from collections import deque
import math
import re
import unittest

import static_automatic_transitions_test as geometry
from static_v2_production_host_test import ROOT, MAINTENANCE, read, merged_nodes


MACHINES = {"Extractor": (-442, -156), "Smelter": (435, -159),
            "Fabricator": (-451, 295)}
SCRIPT = "scenes/world/stationary_machine_presentation.gd"


class StationaryMachinesStaticTest(unittest.TestCase):
    def setUp(self):
        self.text = read(MAINTENANCE)
        self.nodes = geometry.nodes(self.text)
        self.shapes = geometry.resources(self.text)
        self.script = read(SCRIPT)

    def test_room_native_anchors_and_shared_sorting_context(self):
        for node in ["ProductionMaintenanceBayV2", "GroundObjects", "StationaryMachines"]:
            self.assertIn("y_sort_enabled = true", self.nodes[node][1])
        self.assertIn("z_index = -1", self.nodes["Background"][1])
        self.assertNotIn("scale =", self.nodes["StationaryMachines"][1])
        for name, position in MACHINES.items():
            path = "StationaryMachines/" + name
            self.assertEqual(geometry.vectors(self.nodes[path][1])[0], position)
            self.assertNotIn("scale =", self.nodes[path][1])
            # Unsorted assembly preserves scene-local shadow-before-sprite order.
            self.assertNotIn("y_sort_enabled", self.nodes[path][1])
            visual = self.nodes[path + "/Visual"]
            self.assertEqual(visual[1].strip(), "")
            self.assertIn(f'path="res://scenes/visuals/{name.lower()}_stationary.tscn"', self.text)
            scene = read(f"scenes/visuals/{name.lower()}_stationary.tscn")
            self.assertIn("resource_local_to_scene = true", scene)
            self.assertIn("shader_parameter/outline_width = 20.0", scene)
            self.assertIn("shader_parameter/outline_enabled = false", scene)
            self.assertLess(scene.index('name="ContactShadow"'), scene.index('name="Machine"'))

    def test_dormant_contract_and_world_space_front_approaches(self):
        for name, (x, y) in MACHINES.items():
            path = "StationaryMachines/" + name
            target = self.nodes[path + "/Interaction"][1]
            self.assertIn("interaction_enabled = false", target)
            self.assertIn("max_interaction_distance = 45.0", target)
            for forbidden in ["interaction_prompt", "conversation =", "inspection_response"]:
                self.assertNotIn(forbidden, target)
            self.assertIn('path="res://scenes/interaction/world_interactable.gd"', self.text)
            bx, by = geometry.vectors(self.nodes[path + "/Body/Shape"][1])[0]
            width, height = geometry.vectors(self.shapes[name + "Base"][1])[0]
            tx, ty = geometry.vectors(target)[0]
            tw, th = geometry.vectors(self.shapes["InteractionTarget"][1])[0]
            self.assertGreater(ty - th/2, by + height/2)
            self.assertLessEqual(abs(tx - bx), width/2)
            # Feet/detector center at front+20 local has 25 world units clearance.
            feet = (x, y + by + height/2 + 20)
            point = (x + tx, y + ty)
            self.assertLess(math.dist(feet, point) * 1.25, 45)
            self.assertGreater(feet[1], point[1] + th/2)
        contract = read("scenes/interaction/world_interactable.gd")
        self.assertIn("interaction_enabled and", geometry.function(contract, "can_interact"))
        self.assertIn("$Interaction.interaction_enabled = false", self.script)

    def test_presentation_uses_authority_and_all_lifecycle_events_without_writes(self):
        progression = read("scenes/main/playthrough_state.gd")
        ready = geometry.function(self.script, "_ready")
        events = re.findall(r'&"(\w+_completed)"', ready)
        self.assertEqual(len(events), 9)
        for event in events:
            self.assertIn("signal " + event, progression)
        self.assertIn("_progression.connect(event, refresh_presentation)", ready)
        self.assertIn("objective_state_changed.connect(_on_objective_state_changed)", ready)
        self.assertIn("refresh_presentation.call_deferred()", geometry.function(self.script, "_enter_tree"))
        refresh = geometry.function(self.script, "refresh_presentation")
        self.assertIn("if not is_inside_tree():", refresh)
        self.assertIn("$Visual.visible = not recovered", refresh)
        self.assertIn('"outline_enabled", not recovered and _is_highlighted()', refresh)
        for path in ["Body", "Interaction"]:
            self.assertIn(f'${path}/Shape.set_deferred("disabled", recovered)', refresh)
        self.assertNotIn("StaticCollision", self.script)
        self.assertNotRegex(self.script, r"func _(?:process|physics_process|input|unhandled_input)\(")
        self.assertNotRegex(self.script, r"\.(?:recover_\w+|add_item|activate_objective|complete_objective)\(")
        self.assertNotRegex(self.script, r"_progression\.\w+\s*=(?!=)")
        recovered = geometry.function(self.script, "_is_recovered")
        for name in MACHINES:
            self.assertIn(f'"{name.lower()}": return _progression.{name.lower()}_recovered', recovered)
        # Every property checked in highlight precedence exists in Main's tracker,
        # in the same order; no new objective IDs or mutable stage are introduced.
        highlight = geometry.function(self.script, "_is_highlighted")
        fields = re.findall(r"_progression\.(\w+)", highlight)
        tracker = geometry.function(read("scenes/main/main.gd"), "_refresh_objective_tracker")
        expected = re.findall(r"\$PlaythroughState\.(\w+)", tracker)
        self.assertEqual(fields, expected)
        self.assertIn('_objectives.get_active_objective()', highlight)
        self.assertIn('active.objective_id != &"restore_computer"', highlight)

    def test_clear_floor_connects_entry_and_all_machine_front_approaches(self):
        # Conservative grid flood fill with 9 native units clearance (Dave radius
        # is 8 native units), including unchanged permanent geometry and new bases.
        permanent = geometry.resources(read("scenes/world/maintenance_bay_v2.tscn"))
        obstacles = []
        for header, body in permanent.values():
            if 'type="SegmentShape2D"' in header:
                obstacles.append(geometry.vectors(body))
            elif 'type="ConvexPolygonShape2D"' in header:
                raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                obstacles.append(list(zip(raw[::2], raw[1::2])))
        for name, (x, y) in MACHINES.items():
            cx, cy = geometry.vectors(self.nodes[f"StationaryMachines/{name}/Body/Shape"][1])[0]
            w, h = geometry.vectors(self.shapes[name + "Base"][1])[0]
            obstacles.append([(x+cx-w/2, y+cy-h/2), (x+cx+w/2, y+cy-h/2),
                              (x+cx+w/2, y+cy+h/2), (x+cx-w/2, y+cy+h/2)])

        def clear(point):
            for polygon in obstacles:
                if len(polygon) > 2 and geometry.point_in_polygon(point, polygon):
                    return False
                if min(geometry.segment_distance(point, a, b)
                       for a, b in zip(polygon, polygon[1:] + polygon[:1])) <= 9:
                    return False
            return True

        floor = {(x, y) for x in range(-640, 624, 8) for y in range(-296, 376, 8)
                 if clear((x, y))}
        entry = geometry.vectors(merged_nodes(MAINTENANCE)["Spawns/FromInterior"][1])[0]
        start = min(floor, key=lambda p: math.dist(p, (entry[0], entry[1]-8)))
        visited, queue = {start}, deque([start])
        while queue:
            x, y = queue.popleft()
            for neighbor in [(x+8,y), (x-8,y), (x,y+8), (x,y-8)]:
                if neighbor in floor and neighbor not in visited:
                    visited.add(neighbor)
                    queue.append(neighbor)
        for name, (x, y) in MACHINES.items():
            for point in [(x, y+30), (x-98, y+30), (x+98, y+30), (x, y-70)]:
                self.assertTrue(clear(point), (name, point))
                nearest = min(floor, key=lambda p: math.dist(p, point))
                self.assertLess(math.dist(nearest, point), 8)
                self.assertTrue(nearest in visited, (name, point, "unreachable"))


if __name__ == "__main__":
    unittest.main()
