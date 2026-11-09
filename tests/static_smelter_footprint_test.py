"""Smelter resource/source contracts and offline geometry examples; no Godot execution."""
import math
import re
import unittest

from current_preservation import ROOT, git_blob, normalized
from static_automatic_transitions_test import function
from static_fabricator_animation_test import without_presentation_identity

BASE = "461950a2c379ae3039b30d682b530180de645f72"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class SmelterFootprintStaticTest(unittest.TestCase):
    def test_resource_changes_only_explicit_footprint(self):
        path = "inventory/smelter.tres"
        current = read(path)
        self.assertEqual(current.count("footprint_cells = Vector2i(4, 4)"), 1)
        self.assertEqual(current.replace("footprint_cells = Vector2i(4, 4)",
                                         "footprint_cells = Vector2i(2, 2)"),
                         git_blob(BASE, path).decode().replace("\r\n", "\n"))
        for field in ['input_item = ExtResource("2_input")', 'input_per_cycle = 1',
                      'input_capacity = 20', 'output_item = ExtResource("3_output")',
                      'output_per_cycle = 1', 'output_capacity = 20', 'cycle_seconds = 2.0',
                      'compatible_resources = Array[StringName]([])']:
            self.assertIn(field, current)
        definition = read("construction/machine_definition.gd")
        self.assertIn("footprint_cells: Vector2i = Vector2i(2, 2)", definition)
        self.assertIn("extraction_point: Vector2 = Vector2(32, 32)", definition)
        self.assertNotIn("extraction_point =", current)

    def test_geometry_rotations_occupancy_adjacency_and_snapping(self):
        cells = tuple(map(int, re.search(r"footprint_cells = Vector2i\((\d+), (\d+)\)",
                                        read("inventory/smelter.tres")).groups()))
        coordinates = read("scenes/world/world_coordinates.gd")
        grid = int(re.search(r"CONSTRUCTION_SIZE: int = (\d+)", coordinates)[1])
        self.assertEqual((grid, cells), (32, (4, 4)))
        footprint = function(read("construction/machine_definition.gd"), "footprint")
        for contract in ["var cells := footprint_cells", "posmod(quarter_turns, 2) == 1",
                         "cells = Vector2i(cells.y, cells.x)",
                         "Rect2(Vector2(cell) * WorldCoordinates.CONSTRUCTION_SIZE",
                         "Vector2(cells) * WorldCoordinates.CONSTRUCTION_SIZE"]:
            self.assertIn(contract, footprint)
        # Independent cell-set oracle, bound above to the resource/grid and source.
        for turns in range(4):
            width, height = cells if turns % 2 == 0 else cells[::-1]
            self.assertEqual((width * grid, height * grid), (128, 128))
            for cx, cy in [(0, 0), (-3, -5), (7, 9)]:
                occupied = {(cx + x, cy + y) for x in range(width) for y in range(height)}
                self.assertEqual(len(occupied), 16)
                for dx, dy in [(4, 0), (-4, 0), (0, 4), (0, -4)]:
                    self.assertFalse(occupied & {(x + dx, y + dy) for x, y in occupied})
                for dx, dy in [(3, 0), (-3, 0), (0, 3), (0, -3), (0, 0)]:
                    self.assertTrue(occupied & {(x + dx, y + dy) for x, y in occupied})
        for axis in ("x", "y"):
            self.assertIn(f"floori(point.{axis} / CONSTRUCTION_SIZE)", coordinates)
        for world, expected in [(-128.01, -5), (-128, -4), (-32.01, -2), (-32, -1),
                                (-0.01, -1), (0, 0), (31.99, 0), (32, 1), (128, 4)]:
            self.assertEqual(math.floor(world / grid), expected)

    def test_preview_commit_obstacles_and_dave_use_shared_footprint(self):
        rules = read("construction/placement_rules.gd")
        for contract in ["var footprint := definition.footprint(cell, turns)",
                         "footprint.intersects(other.footprint(machine.cell, machine.turns))",
                         "shape.size = footprint.size - Vector2.ONE * 0.02",
                         "Transform2D(0.0, footprint.get_center())",
                         "query.collision_mask = BLOCKING_LAYER", "space.intersect_shape(query, 1)",
                         "Blocked by a solid obstacle", "query.collision_mask = player.collision_layer",
                         "result.collider == player", "Dave is in the footprint"]:
            self.assertIn(contract, rules)
        controller = read("construction/construction_controller.gd")
        for contract in ["PlacementRules.rejection(", "WorldCoordinates.world_to_construction(point)",
                         "_turns = posmod(_turns + 1, 4)", "_ghost.turns = _turns",
                         "_definition.footprint(_cell, _turns).position", "draw_rect(footprint,"]:
            self.assertIn(contract, controller)
        commit = function(read("scenes/world/planet_world_state.gd"), "deploy_machine_instance")
        self.assertIn("PlacementRules.rejection(", commit)
        self.assertIn('"turns": posmod(turns, 4)', commit)

    def test_collision_center_anchor_and_accepted_reach(self):
        deployed = function(read("construction/deployed_machine.gd"), "configure")
        for contract in ["definition.footprint(machine.cell, machine.turns)",
                         "position = Vector2(footprint.get_center().x, footprint.end.y)",
                         "interaction_point = Vector2(0, -footprint.size.y / 2.0)",
                         "shape.size = footprint.size",
                         "collision.position = Vector2(0, -footprint.size.y / 2.0)"]:
            self.assertIn(contract, deployed)
        size = (128, 128)
        anchor = (size[0] / 2, size[1])
        center = (anchor[0], anchor[1] - size[1] / 2)
        self.assertEqual((center, anchor), ((64, 64), (64, 128)))
        detector = read("scenes/player/interaction_detector.gd")
        reach = float(re.search(r"machine_interaction_range: float = ([\d.]+)", detector)[1])
        self.assertEqual(reach, 96)
        self.assertIn("machine.to_global(machine.interaction_point)", detector)
        self.assertIn("machine_interaction_range * machine_interaction_range", detector)
        ui = read("scenes/ui/machine_ui.gd")
        in_range = function(ui, "_in_range")
        self.assertIn("definition.footprint(machine.cell, machine.turns).get_center()", in_range)
        self.assertIn("<= _detector.machine_interaction_range", in_range)
        for method in ("_transfer", "_collect"):
            self.assertIn("not _in_range(machine)", function(ui, method))
        # Representative Dave feet centers 10 units off a side/corner.
        for point in [(-10, 64), (138, 64), (64, -10), (64, 138)]:
            self.assertLess(math.dist(point, center), reach)
        self.assertGreater(math.dist((-10, -10), center), reach)
        controller = read("construction/construction_controller.gd")
        self.assertIn("recovery_range: float = 160.0", controller)
        self.assertIn("PlacementRules.distance_to_footprint(_world.to_local(player.global_position)", controller)
        self.assertIn("target_definition.footprint(_target.cell, _target.turns)) > recovery_range", controller)
        self.assertIn("point.distance_to(point.clamp(footprint.position, footprint.end))",
                      read("construction/placement_rules.gd"))

    def test_shared_gameplay_presentation_and_stationary_preserved(self):
        # Current pre-feature baseline; no broad exemption for other machines/adapters.
        for path in ["inventory/extractor.tres", "inventory/fabricator.tres",
                     "construction/machine_definition.gd", "construction/placement_rules.gd",
                     "construction/construction_controller.gd", "construction/deployed_machine.gd",
                     # Shared adapter gets the separately authorized static art;
                     # preserve its interfaces below, all gameplay here.
                     "construction/extractor_visual.gd",
                     "construction/extractor_visual.tscn", "scenes/world/world_coordinates.gd",
                     "scenes/world/planet_world_state.gd", "scenes/world/planet_exterior.gd",
                     "scenes/world/planet_exterior.tscn", "scenes/player/dave.gd",
                     "scenes/player/dave.tscn", "scenes/player/interaction_detector.gd",
                     "scenes/ui/machine_ui.gd", "scenes/ui/smelter_inspection.gd",
                     "scenes/ui/smelter_inspection.tscn", "scenes/visuals/smelter_stationary.tscn",
                     "scenes/interaction/v2_smelter_recovery.gd",
                     "scenes/world/stationary_machine_presentation.gd", "scenes/interaction/smelter_rack.gd",
                     "assets/environment/maintenance_bay_v2/machines/smelter_stationary.png",
                     "scenes/main/playthrough_state.gd", "project.godot"]:
            with self.subTest(path=path):
                # Authorized Fabricator 4x4 amendment: restore only this exact
                # field for comparison against the unchanged historical baseline.
                current = normalized(path, (ROOT / path).read_bytes())
                if path == "construction/deployed_machine.gd":
                    current = without_presentation_identity(current.decode()).encode()
                if path == "inventory/fabricator.tres":
                    self.assertEqual(current.count(b"footprint_cells = Vector2i(4, 4)"), 1)
                    current = current.replace(b"footprint_cells = Vector2i(4, 4)",
                                              b"footprint_cells = Vector2i(2, 2)")
                self.assertEqual(current,
                                 normalized(path, git_blob(BASE, path)))
        path = "construction/machine_visual.gd"
        current, original = read(path), git_blob(BASE, path).decode().replace("\r\n", "\n")
        declarations = current.split("func _ready()", 1)[0]
        for addition in ['const SMELTER_SCENE := preload("res://construction/smelter_visual.tscn")\n',
                         'var _smelter: SmelterVisual\n', 'var _smelter_art_container: Node2D\n',
                         'var _smelter_status: Node2D\n',
                         'const FABRICATOR_SCENE := preload("res://construction/fabricator_visual.tscn")\n',
                         'var _fabricator: FabricatorVisual\n', 'var _fabricator_art_container: Node2D\n',
                         'var _fabricator_status: Node2D\n', 'var presentation_machine_id: int = 0\n']:
            self.assertEqual(declarations.count(addition), 1)
            declarations = declarations.replace(addition, "")
        self.assertEqual(declarations, original.split("func _ready()", 1)[0])
        for method in ("_ready", "_exit_tree"):
            self.assertEqual(function(current, method).strip(), function(original, method).strip())
        self.assertNotIn("func _draw_fabricator(", current)
        self.assertIn("_fabricator.configure(turns)", current)
