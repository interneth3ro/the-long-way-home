"""Read-only scene/route/geometry checks; no Godot or gameplay code execution."""

from pathlib import Path
import hashlib
import math
import re
import subprocess
import unittest

import static_automatic_transitions_test as geometry


ROOT = Path(__file__).resolve().parents[1]
PRIMARY = "scenes/world/production_ship_interior_v2.tscn"
MAINTENANCE = "scenes/world/production_maintenance_bay_v2.tscn"
EXTERIOR = "scenes/world/planet_exterior.tscn"


def read(path):
    if path == MAINTENANCE:
        return (ROOT / path).read_text(encoding="utf-8")
    return (ROOT / path).read_text()


def merged_nodes(path):
    text = read(path)
    nodes = geometry.nodes(text)
    root = next(iter(nodes.values()))[0]
    instance = re.search(r'instance=ExtResource\("([^"]+)"\)', root)
    if not instance:
        return nodes
    header = next(h for h, _ in geometry.blocks(text, "ext_resource")
                  if f'id="{instance[1]}"' in h)
    base = merged_nodes(re.search(r'path="res://([^"]+)"', header)[1])
    for key, (header, body) in nodes.items():
        base[key] = (header, base.get(key, ("", ""))[1] + body)
    return base


class V2ProductionHostStaticTest(unittest.TestCase):
    def test_resource_graph_has_no_dev_dependency_and_valid_declarations(self):
        pending = ["scenes/main/main_v2.tscn"]
        visited = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            self.assertNotIn("scenes/dev/", path)
            self.assertTrue((ROOT / path).is_file(), path)
            if not path.endswith((".tscn", ".tres", ".gd", ".gdshader")):
                continue
            text = read(path)
            references = re.findall(r'res://([^"\n]+)', text)
            pending.extend(references)
            if path.endswith(".tscn"):
                ext = geometry.blocks(text, "ext_resource")
                sub = geometry.blocks(text, "sub_resource")
                self.assertEqual(int(re.search(r"load_steps=(\d+)", text)[1]),
                                 1 + len(ext) + len(sub), path)
                for kind, entries in [("ExtResource", ext), ("SubResource", sub)]:
                    ids = [re.search(r'\bid="([^"]+)"', h)[1] for h, _ in entries]
                    self.assertEqual(len(ids), len(set(ids)), path)
                    self.assertTrue(set(re.findall(rf'{kind}\("([^"]+)"\)', text)) <= set(ids), path)
        for script in ["scenes/main/main_v2.gd", "scenes/world/v2_room_arrival.gd",
                       "scenes/world/stationary_machine_presentation.gd",
                       "scenes/interaction/v2_extractor_recovery.gd",
                       "scenes/interaction/v2_smelter_recovery.gd"]:
            uid = read(script + ".uid").strip()
            self.assertRegex(uid, r"^uid://[a-z0-9]+$")
            self.assertEqual(sum(p.read_text().strip() == uid
                                 for p in ROOT.glob("**/*.gd.uid")
                                 if ".godot" not in p.parts), 1)

    def test_routes_resolve_to_real_wrapper_identity_and_markers(self):
        expected = [(PRIMARY, "Maintenance", MAINTENANCE, "FromInterior"),
                    (MAINTENANCE, "Interior", PRIMARY, "FromMaintenance"),
                    (PRIMARY, "Exterior", EXTERIOR, "FromShip")]
        for source, door, destination, spawn in expected:
            nodes = merged_nodes(source)
            body = nodes[f"Doorways/{door}"][1]
            self.assertIn(f'destination_scene = "res://{destination}"', body)
            self.assertIn(f'destination_spawn = &"{spawn}"', body)
            self.assertIn(f"Spawns/{spawn}", merged_nodes(destination))
            self.assertIn("GroundObjects", merged_nodes(destination))
            self.assertNotIn("scene_file_path =", read(source))
            if door == "Exterior":
                self.assertIn("presentation = 1", body)
            else:
                self.assertNotIn("presentation =", body)  # Existing QUICK_FADE default.
        host = read("scenes/main/main_v2.gd")
        self.assertIn(f'preload("res://{PRIMARY}")', host)
        self.assertIn(f'EXTERIOR_SCENE: String = "res://{EXTERIOR}"', host)
        self.assertIn('worlds.child_entered_tree.connect(_configure_exterior_return)', host)
        configure = geometry.function(host, "_configure_exterior_return")
        self.assertIn('world.scene_file_path != EXTERIOR_SCENE', configure)
        self.assertIn('world.get_node("GroundObjects/Hatch")', configure)
        self.assertIn('hatch.set("destination_scene", INITIAL_WORLD.resource_path)', configure)
        self.assertIn('hatch.set("destination_spawn", &"FromPlanet")', configure)
        legacy_hatch = merged_nodes(EXTERIOR)["GroundObjects/Hatch"][1]
        self.assertIn('source_scene = "res://scenes/world/planet_exterior.tscn"', legacy_hatch)
        self.assertIn('destination_scene = "res://scenes/world/ship_interior.tscn"', legacy_hatch)
        self.assertIn('destination_spawn = &"FromPlanet"', legacy_hatch)

    def test_one_main_owner_and_initialization_order(self):
        host_scene = read("scenes/main/main_v2.tscn")
        self.assertIn('path="res://scenes/main/main.tscn"', host_scene)
        self.assertEqual(len(geometry.nodes(host_scene)), 2)
        self.assertIn("display_enabled = false", host_scene)
        host = read("scenes/main/main_v2.gd")
        self.assertTrue(host.startswith('extends "res://scenes/main/main.gd"'))
        for script in [host, read("scenes/world/v2_room_arrival.gd")]:
            self.assertNotRegex(script, r"func _(?:unhandled_)?(?:key_)?input\(")
            self.assertNotIn("Input.", script)
        startup = geometry.function(host, "_enter_tree")
        self.assertLess(startup.index("worlds.remove_child"), startup.index("worlds.add_child"))
        self.assertNotIn("initialize()", startup)
        ready = geometry.function(host, "_ready")
        self.assertLess(ready.index("super._ready()"), ready.index("transitions.player.global_position"))
        self.assertNotIn("$Dave", ready.replace("# Parent @onready captures DialogueUI while Dave is still Main/Dave.", ""))
        parent = read("scenes/main/main.gd")
        self.assertIn('@onready var _dialogue: DialogueUI = $Dave/DialogueUI', parent)
        self.assertLess(parent.index("$SceneTransitions.initialize()"),
                        parent.index("_dialogue.conversation_completed.connect"))
        for path in [PRIMARY, MAINTENANCE]:
            text = read(path)
            self.assertIn("scale = Vector2(1.25, 1.25)", text)
            self.assertIn("scale = Vector2(0.8, 0.8)", geometry.nodes(text)["GroundObjects"][1])
            self.assertNotIn('name="Dave"', text)
            for forbidden in ["rack", "request_transition"]:
                self.assertNotIn(forbidden, text.lower())
            if path == MAINTENANCE:
                self.assertNotIn("computer_opening", text)

    def test_computer_reuses_legacy_contract_without_progression_authority(self):
        text = read(PRIMARY)
        nodes = geometry.nodes(text)
        header, body = nodes["ComputerInteraction"]
        self.assertIn('type="Area2D" parent="."', header)
        self.assertIn('collision_layer = 1', body)
        self.assertIn('collision_mask = 0', body)
        self.assertIn('monitoring = false', body)
        self.assertIn('interaction_point = Vector2(0, 0)', body)
        self.assertNotIn('interaction_enabled = false', body)
        legacy = geometry.nodes(read("scenes/world/ship_interior.tscn"))["GroundObjects/WestObstacle"][1]
        for property_name in ["interaction_prompt", "inspection_response"]:
            value = re.search(rf'^{property_name} = .*$', legacy, re.M)[0]
            self.assertIn(value, body)
        for property_name, path in [("script", "scenes/interaction/world_interactable.gd"),
                                    ("conversation", "dialogue/computer_opening.tres")]:
            resource_id = re.search(rf'{property_name} = ExtResource\("([^"]+)"\)', body)[1]
            self.assertTrue(any(f'id="{resource_id}"' in h and f'path="res://{path}"' in h
                                for h, _ in geometry.blocks(text, "ext_resource")))
        self.assertNotIn('[connection ', text)
        self.assertIn('conversation_id = &"computer_opening"', read("dialogue/computer_opening.tres"))
        main = read("scenes/main/main.gd")
        self.assertEqual(main.count('_dialogue.conversation_completed.connect(_on_conversation_completed)'), 1)
        completed = geometry.function(main, "_on_conversation_completed")
        self.assertIn('conversation_id == &"computer_opening"', completed)
        self.assertIn('_objectives.activate_objective(&"restore_computer")', completed)
        dialogue = read("scenes/ui/dialogue_ui.gd")
        self.assertNotIn('conversation_completed.emit', geometry.function(dialogue, "dismiss"))
        self.assertIn('conversation_dismissed.emit', geometry.function(dialogue, "dismiss"))
        self.assertIn('_objectives.activate_objective(&"restore_computer")',
                      geometry.function(main, "_on_ferrite_discovered"))

    def test_computer_front_approach_range_and_solid_clearance(self):
        nodes = geometry.nodes(read(PRIMARY))
        target = geometry.vectors(nodes["ComputerInteraction"][1])[0]
        size = geometry.vectors(geometry.resources(read(PRIMARY))["ComputerInteraction"][1])[0]
        self.assertEqual(target, (0, -214))  # Owner-accepted provisional placement.
        native = read("scenes/world/ship_interior_v2.tscn")
        shapes = geometry.resources(native)
        base = shapes["Footprint_ComputerBase"][1]
        raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', base)[1].split(',')))
        front = max(raw[1::2])
        self.assertGreater(target[1] - size[1]/2, front)
        # Dave detector/feet center is 10 world units above ground. Sample the
        # straight walk from Initial toward Computer without crossing its base.
        for ground_y in range(80, -198, -1):
            center = (0, ground_y - 8)
            for key, (header, body) in shapes.items():
                if key == "Segment_MaintenanceDoorBarrier":
                    continue
                if 'type="SegmentShape2D"' in header:
                    self.assertGreater(geometry.segment_distance(center, *geometry.vectors(body)), 8)
                elif 'type="ConvexPolygonShape2D"' in header:
                    raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                    polygon = list(zip(raw[::2], raw[1::2]))
                    self.assertFalse(geometry.point_in_polygon(center, polygon))
                    self.assertGreater(min(geometry.segment_distance(center, a, b)
                                           for a, b in zip(polygon, polygon[1:] + polygon[:1])), 8)
                    # For the in-range front approach the ray is vertical at x=0.
                    # No polygon intersects this x except Computer, behind target.
                    if min(raw[::2]) <= 0 <= max(raw[::2]):
                        self.assertLessEqual(max(raw[1::2]), front)
                elif 'type="CapsuleShape2D"' in header:
                    self.assertGreater(abs(center[0] - (-387)), 18 + 8)
            if ground_y <= -111:
                self.assertLessEqual(math.dist(center, target) * 1.25, 120)
                self.assertGreater(center[1], target[1])
        dave = read("scenes/player/dave.tscn")
        self.assertIn('radius = 120.0', geometry.resources(dave)["CircleShape2D_interaction"][1])
        self.assertIn('collision_mask = 1', geometry.nodes(dave)["InteractionDetector"][1])
        detector = read("scenes/player/interaction_detector.gd")
        self.assertIn('query.collide_with_areas = true', detector)
        self.assertIn('hit.get("collider") == collider', detector)

    def test_computer_only_world_distance_cap_and_default_preservation(self):
        contract = read("scenes/interaction/world_interactable.gd")
        self.assertIn('@export var max_interaction_distance: float = 0.0', contract)
        body = geometry.nodes(read(PRIMARY))["ComputerInteraction"][1]
        self.assertIn('max_interaction_distance = 45.0', body)
        # P3 adds dormant per-machine caps; legacy Computer still uses defaults.
        scenes = subprocess.check_output(['git', 'ls-files', 'scenes/*.tscn'],
                                         cwd=ROOT, text=True).splitlines()
        overrides = [(path, node) for path in scenes
                     for node, (_, properties) in geometry.nodes(read(path)).items()
                     if re.search(r'^max_interaction_distance =', properties, re.M)]
        self.assertEqual(set(overrides), {(PRIMARY, "ComputerInteraction")} | {
            (MAINTENANCE, f"StationaryMachines/{name}/Interaction")
            for name in ["Extractor", "Smelter", "Fabricator"]})
        refresh = geometry.function(read("scenes/player/interaction_detector.gd"), "_refresh_target")
        cap = ('if body != null and body.max_interaction_distance > 0.0:\n'
               '\t\t\tlimit = minf(limit, body.max_interaction_distance * body.max_interaction_distance)')
        self.assertIn(cap, refresh)
        self.assertIn('body.to_global(body.interaction_point)', refresh)
        self.assertIn('global_position.distance_squared_to(point)', refresh)
        self.assertIn('if distance > limit or distance >= nearest_distance:\n\t\t\tcontinue', refresh)
        self.assertLess(refresh.index(cap), refresh.index('if distance > limit'))
        self.assertLess(refresh.index('if distance > limit'), refresh.index('nearest_distance = distance'))
        # 45 world units = 36 native units at 1.25x, not 45 native units.
        point = (0, -214 * 1.25)
        for dx, dy, eligible in [(0, 45, True), (0, 45.01, False),
                                 (-27, 36, True), (27, 36, True), (27, 36.01, False)]:
            center = (point[0] + dx, point[1] + dy)
            self.assertEqual(math.dist(center, point) ** 2 <= 45.0 ** 2, eligible)

    def test_prompt_and_queued_e_share_fresh_selection_and_line_of_sight(self):
        detector = read("scenes/player/interaction_detector.gd")
        physics = geometry.function(detector, "_physics_process")
        self.assertLess(physics.index('_refresh_target()'), physics.index('if _interaction_requested:'))
        self.assertLess(physics.index('_refresh_target()'), physics.index('dialogue_ui.show_conversation'))
        input_handler = geometry.function(detector, "_unhandled_input")
        self.assertIn('_interaction_requested = true', input_handler)
        self.assertNotIn('show_conversation', input_handler)
        refresh = geometry.function(detector, "_refresh_target")
        self.assertLess(refresh.index('_target = null'), refresh.index('for result in'))
        self.assertIn('PhysicsRayQueryParameters2D.create(global_position, point, collision_mask)', refresh)
        self.assertIn('query.collide_with_areas = true', refresh)
        self.assertIn('if hit.get("collider") == collider:', refresh)
        self.assertIn('prompt = _target.interaction_prompt', refresh)
        self.assertIn('interaction_ui.set_prompt(prompt)', refresh)

    def test_spawn_and_exterior_approach_clearance(self):
        native = read("scenes/world/ship_interior_v2.tscn")
        nodes = merged_nodes(PRIMARY)
        shapes = geometry.resources(native)
        # Same radius-10 world feet circle as production Dave: native radius 8,
        # center 8 above the ground origin at the 1.25x room scale.
        positions = [geometry.vectors(nodes[f"Spawns/{name}"][1])[0]
                     for name in ["Initial", "FromPlanet", "FromMaintenance"]]
        positions += [(-13, y) for y in range(281, 340)]
        for x, y in positions:
            center = (x, y - 8)
            for key, (header, body) in shapes.items():
                if key == "Segment_MaintenanceDoorBarrier":
                    continue
                if 'type="SegmentShape2D"' in header:
                    self.assertGreater(geometry.segment_distance(center, *geometry.vectors(body)), 8, (center, key))
                elif 'type="ConvexPolygonShape2D"' in header:
                    raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                    polygon = list(zip(raw[::2], raw[1::2]))
                    self.assertFalse(geometry.point_in_polygon(center, polygon), (center, key))
                    self.assertGreater(min(geometry.segment_distance(center, a, b)
                                           for a, b in zip(polygon, polygon[1:] + polygon[:1])), 8, (center, key))
                elif 'type="CapsuleShape2D"' in header:
                    radius = float(re.search(r'radius = ([\d.]+)', body)[1])
                    height = float(re.search(r'height = ([\d.]+)', body)[1])
                    px, py = geometry.vectors(nodes["CollisionContent/PortContainer"][1])[0]
                    self.assertGreater(geometry.segment_distance(center, (px, py-height/2+radius),
                                                                 (px, py+height/2-radius)), 8+radius)
        # Both Primary arrivals and start are outside both thresholds.
        for x, y in positions[:3]:
            for door, origin, size in [("Maintenance", (-552, -39.5), (16, 105)),
                                       ("Exterior", (-13, 323), (170, 16))]:
                distance = math.hypot(max(abs(x-origin[0])-size[0]/2, 0),
                                      max(abs(y-8-origin[1])-size[1]/2, 0))
                self.assertGreater(distance, 8, (x, y, door))
        for path, name, facing in [(PRIMARY, "Initial", 1), (PRIMARY, "FromPlanet", 1),
                                   (PRIMARY, "FromMaintenance", 3), (MAINTENANCE, "FromInterior", 2)]:
            self.assertIn(f"metadata/facing = {facing}", merged_nodes(path)[f"Spawns/{name}"][1])

    def test_protected_existing_code_art_and_sidecars_unchanged(self):
        # Existing production/dev code, project settings, assets and sidecars are
        # all protected in this additive slice. Compare SHA-256 of working bytes
        # with baseline blobs (normalize text CRLF only, never binary assets).
        files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", "origin/main",
                                         "assets", "scenes", "construction", "dialogue",
                                         "inventory", "objectives", "world", "project.godot"],
                                        cwd=ROOT, text=True).splitlines()
        proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            for path in files:
                proc.stdin.write(f"origin/main:{path}\n".encode())
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                expected = proc.stdout.read(int(header[2]))
                self.assertEqual(proc.stdout.read(1), b"\n")
                actual = (ROOT / path).read_bytes()
                if path == MAINTENANCE:
                    # Compare to the actual baseline, reversing only the P5
                    # Smelter binding if that baseline still has a dormant target.
                    # P4 Extractor nodes/resources are protected byte-for-byte.
                    actual_text = actual.decode().replace("\r\n", "\n")
                    expected_text = expected.decode().replace("\r\n", "\n")
                    declaration = ('[ext_resource type="Script" '
                                   'path="res://scenes/interaction/v2_smelter_recovery.gd" '
                                   'id="9_smelter_recovery"]\n\n')
                    if declaration not in expected_text:
                        self.assertEqual(actual_text.count(declaration), 1)
                        actual_text = actual_text.replace(declaration, "").replace(
                            'load_steps=14', 'load_steps=13').replace(
                            'script = ExtResource("9_smelter_recovery")\n'
                            'interaction_prompt = "E — Recover Smelter"',
                            'script = ExtResource("7_interaction")\ninteraction_enabled = false')
                    actual, expected = actual_text.encode(), expected_text.encode()
                if path == "scenes/world/stationary_machine_presentation.gd":
                    actual = actual.replace(b"\r\n", b"\n")
                    expected = expected.replace(b"\r\n", b"\n")
                    if b'if machine_id != "extractor":' in expected:
                        actual = actual.replace(
                            b'# V2 recovery adapters own eligibility; Fabricator remains dormant.\n'
                            b'\tif machine_id == "fabricator":',
                            b'# The V2 Extractor adapter owns eligibility; later machines remain dormant.\n'
                            b'\tif machine_id != "extractor":')
                if not path.endswith(".png"):
                    expected = expected.replace(b"\r\n", b"\n")
                    actual = actual.replace(b"\r\n", b"\n")
                self.assertEqual(hashlib.sha256(actual).digest(), hashlib.sha256(expected).digest(), path)
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.wait()


if __name__ == "__main__":
    unittest.main()
