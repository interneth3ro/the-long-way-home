"""Text/geometry checks only. Never invokes Godot or imports gameplay code."""

from pathlib import Path
import hashlib
import math
import re
import subprocess
import unittest

import static_automatic_transitions_test as geometry


ROOT = Path(__file__).resolve().parents[1]
# Fixed verified post-P6 / pre-P8 project baseline for the sole startup allowance.
P8_BASE = "e14703e64aef961f18feba8a616acec00c4f069e"
PAIRS = [
    ("ship_interior_v2", "interior", "Maintenance", "FromMaintenance"),
    ("maintenance_bay_v2", "maintenance", "Interior", "FromInterior"),
]


def read(path):
    return (ROOT / path).read_text()


def base(path):
    return subprocess.check_output(
        ["git", "show", f"origin/main:{path}"], cwd=ROOT, text=True)


class V2ConnectionStaticTest(unittest.TestCase):
    def test_references_counts_and_uids(self):
        scenes = [f"scenes/world/{room}.tscn" for room, *_ in PAIRS]
        scenes += [f"scenes/dev/v2_connection_{name}.tscn" for _, name, *_ in PAIRS]
        scenes += ["scenes/dev/v2_two_room_connection.tscn"]
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
        for name in ["v2_connection_world", "v2_two_room_connection"]:
            uid = read(f"scenes/dev/{name}.gd.uid").strip()
            self.assertRegex(uid, r"^uid://[a-z0-9]+$")
            matches = [p for p in ROOT.glob("**/*.gd.uid") if ".godot" not in p.parts
                       and p.read_text().strip() == uid]
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
        for index, (room, name, door, _) in enumerate(PAIRS):
            other_room, other_name, _, other_spawn = PAIRS[1 - index]
            text = read(f"scenes/dev/v2_connection_{name}.tscn")
            nodes = geometry.nodes(text)
            self.assertIn(f'path="res://scenes/world/{room}.tscn"', text)
            root = nodes["ConnectedInteriorV2" if index == 0 else "ConnectedMaintenanceV2"]
            self.assertIn('instance=ExtResource("1_room")', root[0])
            self.assertIn("scale = Vector2(1.25, 1.25)", root[1])
            self.assertIn("scale = Vector2(0.8, 0.8)", nodes["GroundObjects"][1])
            self.assertAlmostEqual(1.25 * 0.8, 1.0)
            self.assertIn("process_mode = 0", nodes["Doorways"][1])
            self.assertIn(f'destination_scene = "res://scenes/dev/v2_connection_{other_name}.tscn"',
                          nodes[f"Doorways/{door}"][1])
            self.assertIn(f'destination_spawn = &"{other_spawn}"', nodes[f"Doorways/{door}"][1])
            self.assertIn(f"Spawns/{other_spawn}", geometry.nodes(read(f"scenes/world/{other_room}.tscn")))
            self.assertNotIn("scene_file_path =", text)
            self.assertIn(f"arrival_facing = {3 if index == 0 else 2}", text)
        interior = read("scenes/dev/v2_connection_interior.tscn")
        self.assertIn("disabled = true", geometry.nodes(interior)["CollisionContent/MaintenanceDoorBarrier/Shape"][1])
        self.assertNotIn("ExteriorDoorBarrier", interior)
        self.assertNotIn("PreviewOnlyRightDoorBarrier", read("scenes/dev/v2_connection_maintenance.tscn"))

    def test_fixed_arrivals_and_start_outside_thresholds(self):
        for room, name, door, spawn in PAIRS:
            text = read(f"scenes/world/{room}.tscn")
            nodes, shapes = geometry.nodes(text), geometry.resources(text)
            origin = geometry.vectors(nodes[f"Doorways/{door}"][1])[0]
            shape_id = re.search(r'SubResource\("([^"]+)"\)', nodes[f"Doorways/{door}/Shape"][1])[1]
            size = geometry.vectors(shapes[shape_id][1])[0]
            ground = geometry.vectors(nodes[f"Spawns/{spawn}"][1])[0]
            self.assertLessEqual(size[0] * 1.25, 20)
            positions = [ground]
            if name == "interior":
                positions.append((-510, -31.5))
            for p in positions:
                center = (p[0], p[1] - 8)
                distance = math.hypot(max(abs(center[0] - origin[0]) - size[0]/2, 0),
                                      max(abs(center[1] - origin[1]) - size[1]/2, 0))
                self.assertGreater(distance, 8)
            # Top/bottom edges leave 10 native pixels to opening corners.
            low, high = (-102, 23) if name == "interior" else (-47, 113)
            self.assertEqual(origin[1] - size[1]/2 - low, 10)
            self.assertEqual(high - origin[1] - size[1]/2, 10)
            # Sample feet centers from arrival across the trigger to the opening.
            end_x = -568 if name == "interior" else 622
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
        host = read("scenes/dev/v2_two_room_connection.tscn")
        nodes = geometry.nodes(host)
        self.assertEqual([p for p in nodes if p.startswith("Worlds/")], ["Worlds/InteriorV2"])
        self.assertEqual(geometry.vectors(nodes["Dave"][1])[0], (-637.5, -39.375))
        self.assertNotIn("scale =", nodes["Dave"][1])
        for file in ["scenes/main/scene_transition_controller.gd", "scenes/main/playthrough_state.gd",
                     "scenes/interaction/automatic_doorway.gd", "scenes/player/dave.tscn",
                     "scenes/player/dave.gd", "scenes/main/main.tscn"]:
            self.assertEqual(read(file), base(file))
        actual = (ROOT / "project.godot").read_bytes().replace(b"\r\n", b"\n")
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
        startup = read("scenes/dev/v2_two_room_connection.gd")
        self.assertIn("DaveController.Facing.WEST", startup)
        adapter = read("scenes/dev/v2_connection_world.gd")
        self.assertIn("func prepare_for_arrival", adapter)
        self.assertIn("IDLE_ANIMATIONS[arrival_facing]", adapter)
        self.assertNotIn("request_transition", startup + adapter)

    def test_art_production_and_old_previews_preserved(self):
        # Compare baseline previews only; later isolated previews may add files.
        baseline = subprocess.check_output(
            ["git", "ls-tree", "-r", "--name-only", "origin/main", "scenes/dev"],
            cwd=ROOT, text=True).splitlines()
        for relative in baseline:
            if not Path(relative).name.startswith("v2_"):
                self.assertEqual(read(relative), base(relative))
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
