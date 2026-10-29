"""Text/geometry checks only. Never invokes Godot or imports gameplay code."""

import hashlib
import math
import re
import subprocess
import unittest

import static_automatic_transitions_test as geometry
from static_automatic_transitions_test import ROOT, PRIMARY, MAINTENANCE, read, merged_nodes
from static_v2_production_host_test import P8_BASE, tracked_non_dev_files, without_approved_b1_changes


PAIRS = [
    ("ship_interior_v2", PRIMARY, "Maintenance", "FromMaintenance"),
    ("maintenance_bay_v2", MAINTENANCE, "Interior", "FromInterior"),
]


def base(path):
    # These contracts did not change in P8; compare with verified post-P6 blobs,
    # never moving origin/main (which could compare a merged change to itself).
    return subprocess.check_output(
        ["git", "show", f"{P8_BASE}:{path}"], cwd=ROOT, text=True, encoding="utf-8")


class V2ConnectionStaticTest(unittest.TestCase):
    def test_references_counts_and_uids(self):
        scenes = [f"scenes/world/{room}.tscn" for room, *_ in PAIRS]
        scenes += [PRIMARY, MAINTENANCE, "scenes/main/main_v2.tscn"]
        for path in scenes:
            text = read(path)
            ext = geometry.blocks(text, "ext_resource")
            sub = geometry.blocks(text, "sub_resource")
            self.assertEqual(int(re.search(r"load_steps=(\d+)", text)[1]), 1 + len(ext) + len(sub))
            for header, _ in ext:
                self.assertTrue((ROOT / re.search(r'path="res://([^"]+)"', header)[1]).is_file())
            for kind, declarations in [("ExtResource", ext), ("SubResource", sub)]:
                ids = [re.search(r'id="([^"]+)"', h)[1] for h, _ in declarations]
                self.assertEqual(len(ids), len(set(ids)))
                self.assertTrue(set(re.findall(rf'{kind}\("([^"]+)"\)', text)) <= set(ids))
        for script in ["scenes/world/v2_room_arrival.gd", "scenes/main/main_v2.gd"]:
            uid = read(script + ".uid").strip()
            self.assertRegex(uid, r"^uid://[a-z0-9]+$")
            matches = [p for p in tracked_non_dev_files("*.gd.uid") if read(p).strip() == uid]
            self.assertEqual(len(matches), 1)

    def test_room_ownership_and_preview_isolation(self):
        for room, _, door, spawn in PAIRS:
            text = read(f"scenes/world/{room}.tscn")
            nodes = geometry.nodes(text)
            self.assertIn(f"Spawns/{spawn}", nodes)
            self.assertIn(f"Doorways/{door}/Shape", nodes)
            self.assertIn("process_mode = 4", nodes["Doorways"][1])
            self.assertNotIn("destination_scene =", text)
            self.assertNotIn("res://scenes/dev/", text)
            self.assertNotIn("GroundObjects", text)
            self.assertNotIn('name="Dave"', text)
            # Every existing shape and node remains byte-for-byte equivalent.
            original = base(f"scenes/world/{room}.tscn")
            for key, value in geometry.resources(original).items():
                self.assertEqual(geometry.resources(text)[key], value)
            for key, value in geometry.nodes(original).items():
                self.assertEqual(nodes[key][0], value[0])
                self.assertEqual(nodes[key][1].strip(), value[1].strip())
        door = read("scenes/interaction/automatic_doorway.gd")
        self.assertIn("if controller == null:\n\t\treturn", door)

    def test_reciprocal_routes_and_inherited_world_identity(self):
        for index, (room, path, door, _) in enumerate(PAIRS):
            other_room, other_path, _, other_spawn = PAIRS[1 - index]
            text = read(path)
            nodes = geometry.nodes(text)
            self.assertIn(f'path="res://scenes/world/{room}.tscn"', text)
            root = nodes["ProductionShipInteriorV2" if index == 0 else "ProductionMaintenanceBayV2"]
            self.assertIn('instance=ExtResource("1_room")', root[0])
            self.assertIn("scale = Vector2(1.25, 1.25)", root[1])
            self.assertIn("scale = Vector2(0.8, 0.8)", nodes["GroundObjects"][1])
            self.assertAlmostEqual(1.25 * 0.8, 1.0)
            self.assertIn("process_mode = 0", nodes["Doorways"][1])
            self.assertIn(f'destination_scene = "res://{other_path}"',
                          nodes[f"Doorways/{door}"][1])
            self.assertIn(f'destination_spawn = &"{other_spawn}"', nodes[f"Doorways/{door}"][1])
            self.assertIn(f"Spawns/{other_spawn}", geometry.nodes(read(f"scenes/world/{other_room}.tscn")))
            self.assertNotIn("scene_file_path =", text)
            self.assertIn(f"metadata/facing = {3 if index == 0 else 2}",
                          nodes[f"Spawns/{'FromMaintenance' if index == 0 else 'FromInterior'}"][1])
        interior = read(PRIMARY)
        self.assertIn("disabled = true", geometry.nodes(interior)["CollisionContent/MaintenanceDoorBarrier/Shape"][1])
        self.assertNotIn("CollisionContent/ExteriorDoorBarrier", interior)
        self.assertNotIn("PreviewOnlyRightDoorBarrier", read(MAINTENANCE))

    def test_fixed_arrivals_and_start_outside_thresholds(self):
        for room, path, door, spawn in PAIRS:
            text = read(f"scenes/world/{room}.tscn")
            nodes, shapes = geometry.nodes(text), geometry.resources(text)
            origin = geometry.vectors(nodes[f"Doorways/{door}"][1])[0]
            shape_id = re.search(r'SubResource\("([^"]+)"\)', nodes[f"Doorways/{door}/Shape"][1])[1]
            size = geometry.vectors(shapes[shape_id][1])[0]
            ground = geometry.vectors(nodes[f"Spawns/{spawn}"][1])[0]
            self.assertLessEqual(size[0] * 1.25, 20)
            positions = [ground]
            if path == PRIMARY:
                positions.append(geometry.vectors(merged_nodes(PRIMARY)["Spawns/Initial"][1])[0])
            for p in positions:
                center = (p[0], p[1] - 8)
                distance = math.hypot(max(abs(center[0] - origin[0]) - size[0]/2, 0),
                                      max(abs(center[1] - origin[1]) - size[1]/2, 0))
                self.assertGreater(distance, 8)
            # Top/bottom edges leave 10 native pixels to opening corners.
            low, high = (-102, 23) if path == PRIMARY else (-47, 113)
            self.assertEqual(origin[1] - size[1]/2 - low, 10)
            self.assertEqual(high - origin[1] - size[1]/2, 10)
            # Sample feet centers from arrival across the trigger to the opening.
            end_x = -568 if path == PRIMARY else 622
            count = math.ceil(abs(end_x - ground[0]))
            for i in range(count + 1):
                p = (ground[0] + (end_x - ground[0]) * i / count, ground[1] - 8)
                for key, (header, body) in shapes.items():
                    if key == "Segment_MaintenanceDoorBarrier":
                        continue  # Disabled only in connected Primary instance.
                    if 'type="SegmentShape2D"' in header:
                        self.assertGreater(geometry.segment_distance(p, *geometry.vectors(body)), 8)
                    elif 'type="ConvexPolygonShape2D"' in header:
                        raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                        polygon = list(zip(raw[::2], raw[1::2]))
                        self.assertFalse(geometry.point_in_polygon(p, polygon))
                        self.assertGreater(min(geometry.segment_distance(p, a, b)
                                               for a, b in zip(polygon, polygon[1:] + polygon[:1])), 8)
                    elif 'type="CapsuleShape2D"' in header:
                        radius = float(re.search(r'radius = ([\d.]+)', body)[1])
                        height = float(re.search(r'height = ([\d.]+)', body)[1])
                        x, y = geometry.vectors(nodes["CollisionContent/PortContainer"][1])[0]
                        self.assertGreater(geometry.segment_distance(p, (x, y-height/2+radius),
                                                                     (x, y+height/2-radius)), 8+radius)

    def test_single_host_and_unchanged_cache_lock_and_rearm_contract(self):
        host = read("scenes/main/main.tscn")
        nodes = geometry.nodes(host)
        self.assertEqual([p for p in nodes if p.startswith("Worlds/")], ["Worlds/ShipInterior"])
        self.assertIn('instance=ExtResource("3_dave")', nodes["Dave"][0])
        self.assertNotIn("scale =", nodes["Dave"][1])
        for file in ["scenes/main/scene_transition_controller.gd", "scenes/main/playthrough_state.gd",
                     "scenes/interaction/automatic_doorway.gd", "scenes/player/dave.tscn",
                     "scenes/player/dave.gd", "scenes/main/main.tscn"]:
            self.assertEqual(without_approved_b1_changes(file, read(file)), base(file))
        actual = without_approved_b1_changes("project.godot", read("project.godot")).encode("utf-8")
        expected = subprocess.check_output(
            ["git", "show", f"{P8_BASE}:project.godot"], cwd=ROOT).replace(b"\r\n", b"\n")
        approved = b'run/main_scene="res://scenes/main/main_v2.tscn"'
        baseline = b'run/main_scene="res://scenes/main/main.tscn"'
        pattern = rb"^[ \t]*run/main_scene[ \t]*=.*$"
        self.assertEqual(re.findall(pattern, actual, re.M), [approved])
        self.assertEqual(re.findall(pattern, expected, re.M), [baseline])
        self.assertEqual(actual.replace(approved, baseline, 1), expected)
        for role in ["player", "world_host", "progression"]:
            self.assertIn(f"{role} = NodePath", nodes["SceneTransitions"][1])
        for script in ["scene_transition_controller.gd", "playthrough_state.gd"]:
            self.assertEqual(host.count(f"/main/{script}"), 1)
        startup = read("scenes/main/main_v2.gd")
        self.assertIn('preload("res://' + PRIMARY + '")', startup)
        self.assertIn('world.get_node("Spawns/Initial")', startup)
        self.assertIn('metadata/facing = 1', merged_nodes(PRIMARY)["Spawns/Initial"][1])
        adapter = read("scenes/world/v2_room_arrival.gd")
        self.assertIn("func prepare_for_arrival", adapter)
        self.assertIn('nearest.get_meta(&"facing")', adapter)
        self.assertIn("IDLE_ANIMATIONS[facing]", adapter)
        self.assertNotIn("request_transition", startup + adapter)

    def test_art_and_shared_production_preserved(self):
        # Old preview preservation is replaced by the exact retirement allowance
        # in the production-host suite. Keep immutable shared-world/art coverage.
        art = ROOT / "assets/environment/maintenance_bay_v2/maintenance_bay_v2_machine_free_background.png"
        self.assertEqual(hashlib.sha256(art.read_bytes()).hexdigest(),
                         "968d4deca9e8df72bd5abb205a018d11a866b902de0ac0c1440750caa5ef99e1")
        # Production worlds cannot acquire a reference to the new harness.
        for name in ["ship_interior", "maintenance_bay", "planet_exterior"]:
            for path in (ROOT / "scenes/world").glob(name + ".*"):
                relative = path.relative_to(ROOT).as_posix()
                self.assertEqual(read(relative), base(relative))


if __name__ == "__main__":
    unittest.main()
