"""Scene/text/geometry checks only. Never imports gameplay or invokes Godot.

Control-flow assertions are regression tripwires, not runtime validation of
physics registration, async cancellation, input delivery or engine parsing.
"""

from pathlib import Path
import hashlib
import json
import math
import re
import unittest


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "scenes/world/production_ship_interior_v2.tscn"
MAINTENANCE = "scenes/world/production_maintenance_bay_v2.tscn"
EXTERIOR = "scenes/world/planet_exterior.tscn"
WORLDS = [PRIMARY, MAINTENANCE, EXTERIOR]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def blocks(text, kind):
    return [(match[1], match[2]) for match in re.finditer(
        rf'^\[{kind} ([^\n]+)\]\n(.*?)(?=^\[|\Z)', text, re.M | re.S)]


def nodes(text):
    result = {}
    for header, body in blocks(text, "node"):
        name = re.search(r'name="([^"]+)"', header)[1]
        parent = re.search(r'parent="([^"]+)"', header)
        path = name if not parent else ("" if parent[1] == "." else parent[1] + "/") + name
        result[path] = (header, body)
    return result


def vectors(text):
    return [tuple(map(float, value.split(",")))
            for value in re.findall(r'Vector2\(([^)]+)\)', text)]


def resources(text):
    return {re.search(r'id="([^"]+)"', h)[1]: (h, b)
            for h, b in blocks(text, "sub_resource")}


def inherited_scene(path):
    text = read(path)
    root = next(iter(nodes(text).values()))[0]
    instance = re.search(r'instance=ExtResource\("([^"]+)"\)', root)
    if not instance:
        return None
    header = next(h for h, _ in blocks(text, "ext_resource")
                  if f'id="{instance[1]}"' in h)
    return re.search(r'path="res://([^"]+)"', header)[1]


def merged_nodes(path):
    # Scene-text overlay only, not a Godot inheritance/instance evaluator.
    local = nodes(read(path))
    inherited = inherited_scene(path)
    result = merged_nodes(inherited) if inherited else {}
    for key, (header, body) in local.items():
        previous_header, previous_body = result.get(key, ("", ""))
        if previous_header and 'type=' not in header and 'instance=' not in header:
            header = previous_header
        result[key] = (header, previous_body + body)
    return result


def merged_resources(path):
    inherited = inherited_scene(path)
    result = merged_resources(inherited) if inherited else {}
    result.update(resources(read(path)))
    return result


def segment_distance(p, a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    t = max(0, min(1, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx*dx + dy*dy)))
    return math.dist(p, (a[0] + t*dx, a[1] + t*dy))


def point_in_polygon(p, polygon):
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > p[1]) != (b[1] > p[1]):
            x = a[0] + (p[1] - a[1]) * (b[0] - a[0]) / (b[1] - a[1])
            if p[0] < x:
                inside = not inside
    return inside


def function(text, name):
    return re.search(rf'^func {name}\(.*?(?=^func |\Z)', text, re.S | re.M)[0]


class AutomaticTransitionsStaticTest(unittest.TestCase):
    def setUp(self):
        self.controller = (ROOT / "scenes/main/scene_transition_controller.gd").read_text()
        self.door = (ROOT / "scenes/interaction/automatic_doorway.gd").read_text()
        self.interior = read(PRIMARY)

    def test_resource_references_and_load_steps(self):
        paths = WORLDS + ["scenes/main/main_v2.tscn", "scenes/main/main.tscn",
                          "scenes/interaction/automatic_doorway.tscn"]
        for path in paths:
            text = read(path)
            external = blocks(text, "ext_resource")
            internal = blocks(text, "sub_resource")
            self.assertEqual(int(re.search(r'load_steps=(\d+)', text)[1]), 1 + len(external) + len(internal))
            for header, _ in external:
                target = re.search(r'path="res://([^"]+)"', header)[1]
                self.assertTrue((ROOT / target).is_file(), target)
            for kind, declared in [("ExtResource", external), ("SubResource", internal)]:
                ids = {re.search(r'\bid="([^"]+)"', h)[1] for h, _ in declared}
                self.assertTrue(set(re.findall(rf'{kind}\("([^"]+)"\)', text)) <= ids)

    def test_reciprocal_graph_and_destination_contracts(self):
        routes = [(PRIMARY, "Maintenance", MAINTENANCE, "FromInterior"),
                  (MAINTENANCE, "Interior", PRIMARY, "FromMaintenance"),
                  (PRIMARY, "Exterior", EXTERIOR, "FromShip")]
        for source, door, destination, spawn in routes:
            body = merged_nodes(source)["Doorways/" + door][1]
            self.assertIn(f'destination_scene = "res://{destination}"', body)
            self.assertIn(f'destination_spawn = &"{spawn}"', body)
            target = merged_nodes(destination)
            self.assertIn('type="Marker2D"', target["Spawns/" + spawn][0])
            self.assertIn('type="Node2D"', target["GroundObjects"][0])
            self.assertNotIn('scene_file_path =', read(source))
        # Exterior's authored return is deliberately legacy; the V2 host overrides
        # that actual instance on every attach, without changing its cache identity.
        configure = function(read("scenes/main/main_v2.gd"), "_configure_exterior_return")
        self.assertIn('world.scene_file_path != EXTERIOR_SCENE', configure)
        self.assertIn('hatch.set("destination_scene", INITIAL_WORLD.resource_path)', configure)
        self.assertIn('hatch.set("destination_spawn", &"FromPlanet")', configure)

    def test_host_uses_real_controller_and_unscaled_persistent_dave(self):
        host = read("scenes/main/main.tscn")
        self.assertIn('path="res://scenes/main/scene_transition_controller.gd"', host)
        self.assertIn('path="res://scenes/main/playthrough_state.gd"', host)
        self.assertIn('path="res://scenes/player/dave.tscn"', host)
        startup = function(read("scenes/main/main_v2.gd"), "_enter_tree")
        self.assertLess(startup.index('worlds.remove_child'), startup.index('worlds.add_child'))
        self.assertIn('INITIAL_WORLD.instantiate()', startup)
        self.assertNotIn("scale =", nodes(host)["Dave"][1])
        self.assertIn('scale = Vector2(1.25, 1.25)', self.interior)
        self.assertIn('scale = Vector2(0.8, 0.8)', nodes(self.interior)["GroundObjects"][1])
        # A disabled Dave must suppress all inheriting input/physics descendants.
        dave = (ROOT / "scenes/player/dave.tscn").read_text()
        self.assertNotIn("process_mode =", dave)
        self.assertIn('player.reparent(_current_world.get_node("GroundObjects"))', self.controller)
        self.assertIn('_worlds[_current_world.scene_file_path] = _current_world', self.controller)

    def test_all_approved_art_hashes(self):
        folder = ROOT / "assets/environment/ship_interior_v2"
        manifest = json.loads((folder / "manifest.json").read_text())
        for name, metadata in manifest["files"].items():
            self.assertEqual(hashlib.sha256((folder / Path(name).name).read_bytes()).hexdigest(), metadata["sha256"])

    def test_safe_spawns_outside_every_threshold(self):
        for name in [PRIMARY, MAINTENANCE]:
            scene_nodes = merged_nodes(name)
            shapes = merged_resources(name)
            spawns = [vectors(body)[0] for path, (_, body) in scene_nodes.items() if path.startswith("Spawns/")]
            doors = [(path, vectors(body)[0]) for path, (_, body) in scene_nodes.items()
                     if path.startswith("Doorways/") and "destination_scene" in body]
            for spawn in spawns:
                # Uniform 1.25x room: Dave's radius/offset 10 world = 8 native.
                center = (spawn[0], spawn[1] - 8)
                for path, position in doors:
                    shape_id = re.search(r'SubResource\("([^"]+)"\)', scene_nodes[path + "/Shape"][1])[1]
                    size = vectors(shapes[shape_id][1])[0]
                    distance = math.hypot(max(abs(center[0] - position[0]) - size[0]/2, 0),
                                          max(abs(center[1] - position[1]) - size[1]/2, 0))
                    self.assertGreater(distance, 8, (name, spawn, path))

    def test_v2_safe_spawn_and_threshold_approach_clearance(self):
        text = (ROOT / "scenes/world/ship_interior_v2.tscn").read_text()
        shapes = resources(text)
        perimeter = []
        obstacles = []
        for path, (_, body) in nodes(text).items():
            if not path.startswith("CollisionContent/") or not path.endswith("/Shape"):
                continue
            shape_id = re.search(r'SubResource\("([^"]+)"\)', body)[1]
            header, resource = shapes[shape_id]
            if 'type="SegmentShape2D"' in header:
                perimeter.append(vectors(resource))
            elif 'type="ConvexPolygonShape2D"' in header:
                numbers = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', resource)[1].split(",")))
                obstacles.append(list(zip(numbers[::2], numbers[1::2])))
        polygon = [a for a, _ in perimeter]
        capsule_header, capsule = shapes["Footprint_PortContainer"]
        self.assertIn('type="CapsuleShape2D"', capsule_header)
        radius = float(re.search(r'radius = ([\d.]+)', capsule)[1])
        height = float(re.search(r'height = ([\d.]+)', capsule)[1])
        capsule_origin = vectors(nodes(text)["CollisionContent/PortContainer"][1])[0]
        capsule_segment = [(capsule_origin[0], capsule_origin[1] + sign*(height/2-radius)) for sign in (-1, 1)]
        # Ground-origin routes include both authored inward spawns and reachable
        # threshold centers. Sample every <= 1 world unit; not movement simulation.
        routes = [[(-110, 28.75), (-600, -45), (-684, -45)],
                  [(-110, 28.75), (-16, 340), (-16, 412)]]
        for route in routes:
            for a, b in zip(route, route[1:]):
                count = math.ceil(math.dist(a, b))
                for i in range(count + 1):
                    p = ((a[0] + (b[0]-a[0])*i/count)/1.25,
                         (a[1] + (b[1]-a[1])*i/count - 10)/1.25)
                    self.assertTrue(point_in_polygon(p, polygon), p)
                    self.assertGreater(min(segment_distance(p, *edge) for edge in perimeter), 8, p)
                    for obstacle in obstacles:
                        self.assertFalse(point_in_polygon(p, obstacle), p)
                        self.assertGreater(min(segment_distance(p, x, y) for x, y in zip(obstacle, obstacle[1:] + obstacle[:1])), 8, p)
                    self.assertGreater(segment_distance(p, *capsule_segment), radius + 8, p)

    def test_real_exterior_arrival_and_first_reveal_contract(self):
        # Synthetic rooms' four-wall/color checks certified only old fixtures.
        # Protect the real destination and reveal preparation order instead.
        exterior = merged_nodes(EXTERIOR)
        self.assertEqual(vectors(exterior["Spawns/FromShip"][1])[0], (-384, -64))
        self.assertIn('destination_spawn = &"FromPlanet"', exterior["GroundObjects/Hatch"][1])
        transition = function(self.controller, "_perform_transition")
        self.assertLess(transition.index('await _fade_to(1.0)'), transition.index('load(destination_scene)'))
        self.assertLess(transition.index('await destination.call("prepare_for_arrival"'),
                        transition.index('progression.first_exterior_reveal_completed = true'))
        self.assertIn('and not progression.first_exterior_reveal_completed', transition)

    def test_entry_rearm_and_cached_world_synchronization_guards(self):
        self.assertIn('get_overlapping_bodies().has(controller.player)', self.door)
        self.assertIn('_reset_entry()', function(self.door, "_enter_tree"))
        self.assertIn('not world.is_ancestor_of(self)', self.door)
        self.assertIn('controller.is_transitioning()', self.door)
        self.assertIn('_registration_frames -= 1', self.door)
        self.assertIn('if not overlapping:\n\t\t_state = EntryState.ARMED', self.door)
        self.assertEqual(self.door.count('controller.request_transition('), 1)
        self.assertNotIn('Input.', self.door)
        self.assertNotIn('create_timer', self.door)
        self.assertNotIn('res://scenes/dev/', self.door)

    def test_duplicate_and_held_input_lock_order(self):
        request = function(self.controller, "request_transition")
        self.assertLess(request.index('if _busy or source_scene !='), request.index('_busy = true'))
        for lock in ['clear_for_transition()', 'player.velocity = Vector2.ZERO',
                     'player.process_mode = Node.PROCESS_MODE_DISABLED']:
            self.assertLess(request.index(lock), request.index('transition_started.emit()'))
        finish = function(self.controller, "_finish_quick_transition")
        self.assertLess(finish.index('await _fade_to(0.0'), finish.index('_finish_transition('))
        self.assertIn('clear_for_transition()', finish)
        self.assertNotIn('Input.action_release', self.controller)

    def test_fade_mode_isolation_and_failure_before_source_detach(self):
        self.assertIn('enum Presentation { IMMEDIATE, FIRST_EXTERIOR_REVEAL, QUICK_FADE }', self.controller)
        self.assertIn('const FADE_SECONDS: float = 0.65', self.controller)
        self.assertIn('var quick_fade_seconds: float = 0.15', self.controller)
        quick = function(self.controller, "_perform_quick_transition")
        self.assertNotIn('first_exterior_reveal_completed', quick)
        detach = quick.index('world_host.remove_child(source)')
        for validation in ['ResourceLoader.exists', 'destination.scene_file_path != destination_scene',
                           'spawn == null or ground_objects == null']:
            self.assertLess(quick.index(validation), detach)
        self.assertLess(quick.index('await _fade_to(1.0'), detach)
        self.assertIn('await _finish_quick_transition()\n\t\treturn', quick)
        self.assertIn('_worlds[destination_scene] = destination', quick)

    def test_cancellation_rollback_and_unlock_paths(self):
        quick = function(self.controller, "_perform_quick_transition")
        self.assertIn('player.global_position = source_position', quick)
        self.assertIn('world_host.add_child(source)', quick)
        self.assertIn('if _quick_active and not _quick_committed:', self.controller)
        self.assertLess(quick.index('world_host.add_child(source)'), quick.index('_quick_committed = true'))
        finish = function(self.controller, "_finish_transition")
        self.assertIn('_curtain.color.a = 0.0', finish)
        self.assertIn('player.process_mode = previous_process_mode', finish)
        self.assertIn('_busy = false', finish)


if __name__ == "__main__":
    unittest.main()
