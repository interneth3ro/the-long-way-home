"""Milestone 7 nonexecuting integration contracts; no engine/project code runs."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "fc3b0947be5e3cb217e4de12f95ec23d550a5003"

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def body(source, name):
    return re.search(r"^(?:static )?func " + name + r"\(.*?(?=^(?:static )?func |\Z)", source, re.M | re.S)[0]

WORLD = read("scenes/world/planet_world_state.gd")
CONTROL = read("construction/construction_controller.gd")
RULES = read("construction/placement_rules.gd")
ANCHOR = read("construction/extractor_anchor_rules.gd")

class LiveExtractorStaticTests(unittest.TestCase):
    def test_authoritative_target_query_and_error_distinction(self):
        target = body(WORLD, "extractor_target_v2")
        for fragment in ("resource_generation_v2_context()", "query_resource_descriptors_v2(",
                         "if not context.ok:", "if not result.ok:", '"Unavailable v2 context"',
                         '"Unavailable v2 query"', "ExtractorAnchorRules.select(cursor, result.deposits)"):
            self.assertIn(fragment, target)
        self.assertNotIn("_resource_v2._source", WORLD)

    def test_legacy_routing_precedes_v2_and_uses_extraction_geometry(self):
        target = body(WORLD, "extractor_target_v2")
        self.assertLess(target.index('deposit_at(point, &"ferrite")'), target.index("resource_generation_v2_context()"))
        self.assertIn("definition.rotated_point(definition.extraction_point, turns)", target)
        self.assertIn('if _definition.item_id == &"extractor" and _world is PlanetExterior:', CONTROL)

    def test_ticket_identity_and_exact_resolution(self):
        for key in ('"token": context.token', '"deposit_id": member.deposit_id',
                    '"resource_type": member.resource_type', '"anchor_cells": member.anchor_cells'):
            self.assertIn(key, WORLD)
        validate = body(WORLD, "extractor_anchor_rejection_v2")
        self.assertIn("resource_descriptor_v2_by_id(ticket.deposit_id, ticket.token)", validate)
        self.assertIn('ticket.get("anchor_cells") != member.anchor_cells', validate)
        self.assertIn('ticket.get("resource_type") != member.resource_type', validate)
        self.assertNotIn("select(", validate)

    def test_shared_selection_and_geometry(self):
        self.assertIn("const SNAP_TOLERANCE: float = 32.0", ANCHOR)
        self.assertIn("member.deposit_id < best.deposit_id", ANCHOR)
        geometry = body(ANCHOR, "member_rejection")
        for fragment in ("definition.compatible_resources.has", "anchor.size != ANCHOR_CELLS",
                         "definition.footprint_cells != ANCHOR_CELLS", "cell != anchor.position",
                         "definition.footprint(cell, turns) != bounds(anchor)", '"Occupied anchor"'):
            self.assertIn(fragment, geometry)
        self.assertIn("member_rejection(member, definition, cell, turns, occupant)", body(ANCHOR, "rejection"))
        self.assertIn("ExtractorAnchorRules.member_rejection(", WORLD)

    def test_click_freezes_preview_and_commit_never_selects(self):
        click = body(CONTROL, "_unhandled_input")
        for fragment in ("_requested_cell = _cell", "_requested_anchor_ticket = _anchor_ticket.duplicate(true)",
                         "_requested_reason = _reason"):
            self.assertIn(fragment, click)
        self.assertNotIn("extractor_target_v2", click)
        commit = body(CONTROL, "_physics_process")
        self.assertIn("deploy_extractor_v2(", commit)
        self.assertIn("_requested_anchor_ticket, _definition, _requested_cell, _requested_turns", commit)
        self.assertIn("if not _requested_reason.is_empty():", commit)

    def test_preview_and_highlight_share_snapped_cell(self):
        physics = body(CONTROL, "_physics_process")
        self.assertIn("_cell = selected.cell", physics)
        self.assertIn("_definition.footprint(_cell, _turns).position", physics)
        self.assertIn("_definition.footprint(_cell, _turns)", body(CONTROL, "_draw"))
        self.assertNotIn("artwork", body(CONTROL, "_draw"))

    def test_common_environment_checks_are_retained(self):
        for fragment in ('is_in_group(&"construction_world")', "inventory.get_items().has(definition)",
                         "distance_to_footprint", "state.get_machines()", "space.intersect_shape(query, 1)",
                         "query.collision_mask = player.collision_layer", "result.collider == player"):
            self.assertIn(fragment, RULES)
        self.assertIn("state.extractor_anchor_rejection_v2(v2_ticket, definition, cell, turns)", RULES)
        self.assertIn("elif not definition.compatible_resources.is_empty():", RULES)

    def test_one_transaction_order_and_guard(self):
        transaction = body(WORLD, "_deploy_machine_transaction")
        ordered = ["_machine_transaction = true", "PlacementRules.rejection(",
                   "inventory.remove_item(definition, 1, false)", "var machine_id := _next_machine_id",
                   "_extractor_claims_v2[v2_ticket.deposit_id] = machine_id", "_machines[machine_id] = machine",
                   "_next_machine_id += 1", "inventory.changed.emit()", "machines_changed.emit()",
                   "machine_deployed.emit(definition)"]
        positions = [transaction.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(WORLD.count("inventory.remove_item(definition, 1, false)"), 1)
        mutation = transaction.split("var machine_id :=", 1)[1].split("inventory.changed.emit()", 1)[0]
        self.assertNotIn("await ", mutation)
        self.assertNotIn("emit(", mutation)
        self.assertIn("_deploy_machine_transaction(", body(WORLD, "deploy_machine_instance"))
        self.assertIn("_deploy_machine_transaction(", body(WORLD, "deploy_extractor_v2"))

    def test_recovery_claim_release_after_inventory_before_notifications(self):
        recovery = body(WORLD, "recover_machine")
        ordered = ["inventory.add_items(recovered, false)", "_machines.erase(machine_id)",
                   '_extractor_claims_v2.erase(machine.get("v2_deposit_id", ""))', "inventory.changed.emit()"]
        positions = [recovery.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("select(", recovery)
        self.assertIn("return false", recovery.split("inventory.add_items", 1)[1].split("_machines.erase", 1)[0])

    def test_v2_production_is_inactive_without_gates(self):
        self.assertIn('machine.has("v2_deposit_id")', body(WORLD, "machine_status").split("var definition:")[0])
        for token in ("feature_flag", "developer_mode", "gameplay_eligible"):
            self.assertNotIn(token, CONTROL + WORLD)
        definition = read("inventory/extractor.tres")
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite", &"cuprite"])', definition)
        self.assertIn('path="res://inventory/ferrite_ore.tres"', definition)
        self.assertNotIn("cuprite_ore", WORLD + definition)

    def test_v2_inspection_does_not_advertise_ferrite_production(self):
        view = read("scenes/ui/extractor_inspection.gd")
        self.assertIn('definition.has_production() and not machine.has("v2_deposit_id")', view)
        self.assertIn("var product := definition.output_item if configured else null", view)
        self.assertIn("_details.visible = configured", view)
        self.assertIn("_unavailable.visible = not configured", view)

    def test_legacy_queries_and_production_loop_unchanged(self):
        original = subprocess.check_output(["git", "show", BASE + ":scenes/world/planet_world_state.gd"], cwd=ROOT, text=True)
        for name in ("deposit_at", "get_deposit", "get_deposits_in_area", "query_deposit_descriptors",
                     "advance_production", "transfer_input", "collect_output"):
            self.assertEqual(body(WORLD, name), body(original, name), name)

    def test_unexecuted_behavior_and_preserved_inputs(self):
        behavior = read("tests/live_extractor_v2_test.gd")
        for label in ("stable tie", "occupied feedback", "incompatible feedback", "failed removal",
                      "successful deployment", "duplicate claim", "failed placement", "failed recovery",
                      "successful recovery", "stale context", "legacy Ferrite", "no Cuprite production"):
            self.assertIn(label, behavior)
        for path in ("scenes/world/planet_exterior.gd", "scenes/world/resource_generation_v2_integration.gd",
                     "scenes/experiments/resource_generation_v2/extractor_anchor_inspection.gd",
                     "tools/run-local-tests.ps1", "tests/fixtures/metadata_smoke/inputs.json"):
            original = subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT)
            self.assertEqual(read(path), original.decode("utf-8").replace("\r\n", "\n"), path)
        for path in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("live_extractor_v2_test", path.read_text())

if __name__ == "__main__":
    unittest.main()
