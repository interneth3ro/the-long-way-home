from east_idle_preservation import verified_east_idle_paths
from south_idle_preservation import verified_south_idle_paths
from north_idle_preservation import verified_north_idle_paths
from initial_exterior_preservation import verified_initial_paths
from static_save_codec_runner_test import verified_codec_runner_paths
"""Fabricator source contracts and independent geometry models; no Godot execution."""
from application_shell_preservation import verified_application_paths
import math
import re
import subprocess
import unittest

from current_preservation import ROOT, git_blob
from extractor_artwork_offline import BODY_PATHS, verify_active_artifacts
from smelter_artwork_offline import (BODY_PATHS as SMELTER_BODIES,
                                     verify_active_artifacts as verify_smelter_artifacts)
from static_automatic_transitions_test import function
from static_fabricator_animation_test import LAYER_PATHS, without_presentation_identity

BASE = "249dd92411db6d70d1f08da809305c7f6c720385"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


class FabricatorFootprintStaticTest(unittest.TestCase):
    def test_only_authorized_resource_line_changes(self):
        path = "inventory/fabricator.tres"
        original = git_blob(BASE, path).decode().replace("\r\n", "\n")
        self.assertEqual(original.count("footprint_cells = Vector2i(2, 2)"), 1)
        expected = original.replace("footprint_cells = Vector2i(2, 2)",
                                    "footprint_cells = Vector2i(4, 4)")
        self.assertEqual(read(path), expected)
        self.assertNotIn("extraction_point =", read(path))
        self.assertNotIn("compatible_resources =", read(path))

    def test_geometry_rotations_occupancy_adjacency_and_snapping(self):
        cells = tuple(map(int, re.search(r"footprint_cells = Vector2i\((\d+), (\d+)\)",
                                        read("inventory/fabricator.tres")).groups()))
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

    def test_protected_gameplay_art_and_execution_controls_unchanged(self):
        # Footprint milestone permits one data line. Decision 36 additionally
        # permits these exact presentation paths; the separate codec runner is
        # accepted only after complete source-hash verification below.
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", "inventory", "construction",
             "scenes", "assets", "project.godot", "tools", "AGENTS.md",
             "docs/LOCAL_TESTING.md"], cwd=ROOT, text=True).splitlines()
        artwork = {"construction/machine_visual.gd", "construction/fabricator_visual.gd",
                   "construction/fabricator_visual.gd.uid", "construction/fabricator_visual.tscn"}
        for name in ("fabricator_0_resting.png", "fabricator_90_body.png",
                     "fabricator_180_body.png", "fabricator_270_body.png"):
            artwork.update(("assets/machines/fabricator/" + name,
                            "assets/machines/fabricator/" + name + ".import"))
        # Decision 62 adds exactly five runtime layers and one identity assignment.
        artwork.update(LAYER_PATHS + [p + ".import" for p in LAYER_PATHS])
        # Decision 2A: exact active identities protect only four Extractor bodies.
        verify_active_artifacts()
        artwork.update(BODY_PATHS)
        verify_smelter_artifacts()
        artwork.update(SMELTER_BODIES)
        artwork.update(verified_application_paths())
        artwork.update(verified_initial_paths())
        artwork.update(verified_codec_runner_paths())
        artwork.update(verified_north_idle_paths())
        artwork.update(verified_south_idle_paths())
        artwork.update(verified_east_idle_paths())
        self.assertEqual(set(changed) - artwork, {"inventory/fabricator.tres", "construction/deployed_machine.gd"})
        path = "construction/deployed_machine.gd"
        self.assertEqual(without_presentation_identity(read(path)),
                         git_blob(BASE, path).decode().replace("\r\n", "\n"))
        stationary = read("scenes/world/production_maintenance_bay_v2.tscn")
        self.assertIn("max_interaction_distance = 45.0", stationary)

    def test_state_transfer_collection_and_recovery_distance_contracts(self):
        state = read("scenes/world/planet_world_state.gd")
        for method in ("transfer_input", "collect_output"):
            self.assertIn(
                "player_point.distance_to(definition.footprint(machine.cell, machine.turns).get_center()) > interaction_range",
                function(state, method))
        self.assertIn("PlacementRules.distance_to_footprint(player_point,",
                      function(state, "recover_machine"))
        self.assertIn("definition.footprint(machine.cell, machine.turns)) > recovery_range",
                      function(state, "recover_machine"))
        center = (64, 64)
        for point, accepted in [((-32, 64), True), ((-32.01, 64), False),
                                ((-10, -10), False), ((64, -10), True)]:
            self.assertEqual(math.dist(point, center) <= 96, accepted)
        for point, accepted in [((-160, 64), True), ((-160.01, 64), False),
                                ((288, 64), True), ((64, 288.01), False),
                                ((-96, -128), True), ((-96.01, -128), False)]:
            nearest = tuple(min(128, max(0, axis)) for axis in point)
            self.assertEqual(math.dist(point, nearest) <= 160, accepted)
        self.assertGreater(math.dist((-160, 64), center), 160)
        self.assertIn("construction_range: float = 160.0",
                      read("construction/construction_controller.gd"))

    def test_initial_configuration_and_illustrated_ghost_remain_definition_driven(self):
        ui = read("scenes/ui/machine_ui.gd")
        placed = function(ui, "_open_placed_machine")
        self.assertIn("_show_machine(machine_id, machine, true)", placed)
        self.assertNotIn("_in_range", placed)
        for method in ("open_machine", "_change_recipe", "_transfer", "_collect"):
            self.assertIn("not _in_range(machine)", function(ui, method))
        visual = read("construction/machine_visual.gd")
        status = function(visual, "_refresh_fabricator_status")
        for contract in ["Vector2(definition.footprint_cells) * WorldCoordinates.CONSTRUCTION_SIZE",
                         "definition.rotated_point(size - Vector2(13, 13), turns)"]:
            self.assertIn(contract, status)
        self.assertIn("_fabricator.configure(turns)", function(visual, "_refresh_presentation"))
        self.assertIn("draw_circle(Vector2.ZERO, 3.5, _status_color())",
                      function(visual, "_draw_fabricator_status"))
        self.assertNotIn("func _draw_fabricator(", visual)
        controller = read("construction/construction_controller.gd")
        self.assertIn("_ghost.definition = definition", controller)
        fixture = read("tests/fabricator_deployment_test.gd")
        self.assertIn("Recovery/redeployment retains expanded geometry", fixture)
        self.assertIn("Chooser targets placed instance beyond ordinary range", fixture)
        self.assertIn("Placement exception cannot transfer", fixture)


if __name__ == "__main__":
    unittest.main()
