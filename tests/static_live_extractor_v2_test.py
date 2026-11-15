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
    def _assert_transaction_contract(self, source):
        transaction = body(source, "_deploy_machine_transaction")
        self.assertIn('if not is_resource_generation_ready() or _machine_transaction or inventory == null:\n\t\treturn 0', transaction)
        self.assertIn('PlacementRules.rejection(self, definition, cell, turns, player, world,\n\t\t\tconstruction_range, inventory, v2_ticket).is_empty():\n\t\t_machine_transaction = false\n\t\treturn 0', transaction)
        self.assertIn('if not inventory.remove_item(definition, 1, false):\n\t\t_machine_transaction = false\n\t\treturn 0\n\tvar machine_id := _next_machine_id', transaction)
        ordered = ['not is_resource_generation_ready()', '_machine_transaction = true',
                   'PlacementRules.rejection(', 'inventory.remove_item(definition, 1, false)',
                   'var machine_id := _next_machine_id',
                   '_extractor_claims_v2[v2_ticket.deposit_id] = machine_id',
                   '_machines[machine_id] = machine', '_next_machine_id += 1',
                   'inventory.changed.emit()', 'machines_changed.emit()',
                   'machine_deployed.emit(definition)']
        for fragment in ordered:
            self.assertIn(fragment, transaction)
        positions = [transaction.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertTrue(transaction.rstrip().endswith('_machine_transaction = false\n\treturn machine_id'))
        # The only releases are the two rejected paths and the final success return.
        self.assertEqual(transaction.count('_machine_transaction = false'), 3)
        self.assertEqual(source.count('inventory.remove_item(definition, 1, false)'), 1)
        publication = transaction.split('if not inventory.remove_item', 1)[1].split('inventory.changed.emit()', 1)[0]
        self.assertNotRegex(publication, r'\bawait\b|\b(?:call_deferred|set_deferred|call|callv|emit|emit_signal|connect)\s*\(')
        for name, ticket in (('deploy_machine_instance', '{}'), ('deploy_extractor_v2', 'ticket')):
            self.assertIn('return _deploy_machine_transaction(definition, cell, turns, inventory, player, world, construction_range, ' + ticket + ')',
                          body(source, name))
        self.assertIn('if ticket.is_empty():\n\t\treturn 0', body(source, 'deploy_extractor_v2'))

    def _assert_output_contract(self, source):
        resolver = body(source, 'extractor_output_item')
        for fragment in ('_machines.get(snapshot.get("id", 0), {})',
                         'if machine.is_empty() or machine != snapshot:\n\t\treturn null',
                         'if definition.item_id != &"extractor":\n\t\treturn null'):
            self.assertIn(fragment, resolver)
        v2, legacy = resolver.split('\tif machine.has("v2_deposit_id"):', 1)[1].split('\n\tvar point :=', 1)
        for fragment in ('var context := resource_generation_v2_context()',
                         'if not context.ok or extractor_occupant_v2(machine.v2_deposit_id) != machine.id:\n\t\t\treturn null',
                         'var resolved := resource_descriptor_v2_by_id(machine.v2_deposit_id, context.token)',
                         'if not resolved.ok or not resolved.descriptor.has("anchor_cells"):\n\t\t\treturn null',
                         'if not ExtractorAnchorRules.member_rejection(member, definition,\n\t\t\t\tmachine.cell, machine.turns, 0).is_empty():\n\t\t\treturn null'):
            self.assertIn(fragment, v2)
        self.assertIn('match member.resource_type:', v2)
        authority, mapping = v2.split('match member.resource_type:', 1)
        self.assertNotIn('preload(', authority)
        self.assertEqual(mapping.strip(), '"cuprite": return preload("res://inventory/cuprite_ore.tres")\n\t\t\t"ferrite": return preload("res://inventory/ferrite_ore.tres")\n\t\treturn null')
        self.assertNotIn('definition.output_item', resolver)
        self.assertNotIn('v2_resource_type', resolver)
        self.assertIn('return preload("res://inventory/ferrite_ore.tres") if deposit_at(point, &"ferrite") != null else null', legacy)
        status = body(source, 'machine_status')
        self.assertIn('extractor_output_item(machine) == null):\n\t\treturn OperatingStatus.INACTIVE', status)
        self.assertIn('return extractor_output_item(machine)', body(source, 'stored_output_item'))

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
        self._assert_transaction_contract(WORLD)

    def test_transaction_guards_reject_source_mutations(self):
        validation = 'if not PlacementRules.rejection(self, definition, cell, turns, player, world,\n\t\t\tconstruction_range, inventory, v2_ticket).is_empty():\n\t\t_machine_transaction = false\n\t\treturn 0\n\t'
        mutations = {
            'removed validation': WORLD.replace(validation, '', 1),
            'validation after consumption': WORLD.replace(validation, '', 1).replace('var machine_id := _next_machine_id', validation + 'var machine_id := _next_machine_id', 1),
            'failed removal falls through': WORLD.replace('if not inventory.remove_item(definition, 1, false):\n\t\t_machine_transaction = false\n\t\treturn 0', 'if not inventory.remove_item(definition, 1, false):\n\t\t_machine_transaction = false', 1),
            'missing rejection release': WORLD.replace('v2_ticket).is_empty():\n\t\t_machine_transaction = false', 'v2_ticket).is_empty():', 1),
            'missing inventory failure release': WORLD.replace('if not inventory.remove_item(definition, 1, false):\n\t\t_machine_transaction = false', 'if not inventory.remove_item(definition, 1, false):', 1),
            'missing reentrancy exclusion': WORLD.replace('or _machine_transaction or inventory == null', 'or inventory == null', 1),
            'missing readiness': WORLD.replace('not is_resource_generation_ready() or _machine_transaction', '_machine_transaction', 1),
            'missing success release': WORLD.replace('machine_deployed.emit(definition)\n\t_machine_transaction = false', 'machine_deployed.emit(definition)', 1),
            'release before notifications': WORLD.replace('inventory.changed.emit()\n\tmachines_changed.emit()', '_machine_transaction = false\n\tinventory.changed.emit()\n\tmachines_changed.emit()', 1),
            'mutation before failed removal return': WORLD.replace('if not inventory.remove_item(definition, 1, false):\n\t\t_machine_transaction = false', 'if not inventory.remove_item(definition, 1, false):\n\t\t_next_machine_id += 1\n\t\t_machine_transaction = false', 1),
            'deferred publication': WORLD.replace('var machine_id := _next_machine_id', 'call_deferred("publish")\n\tvar machine_id := _next_machine_id', 1),
            'await before publication': WORLD.replace('var machine_id := _next_machine_id', 'await signal_ready\n\tvar machine_id := _next_machine_id', 1),
            'incorrect ticket forwarding': WORLD.replace('construction_range, ticket)', 'construction_range, {})', 1),
        }
        for label, mutant in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(mutant, WORLD)
                with self.assertRaises(AssertionError):
                    self._assert_transaction_contract(mutant)

    def test_recovery_claim_release_after_inventory_before_notifications(self):
        recovery = body(WORLD, "recover_machine")
        ordered = ["inventory.add_items(recovered, false)", "_machines.erase(machine_id)",
                   '_extractor_claims_v2.erase(machine.get("v2_deposit_id", ""))', "inventory.changed.emit()"]
        positions = [recovery.index(fragment) for fragment in ordered]
        self.assertEqual(positions, sorted(positions))
        self.assertNotIn("select(", recovery)
        self.assertIn("return false", recovery.split("inventory.add_items", 1)[1].split("_machines.erase", 1)[0])

    def test_supported_production_requires_authoritative_output_without_dev_gates(self):
        self._assert_output_contract(WORLD)
        for token in ("feature_flag", "developer_mode", "gameplay_eligible"):
            self.assertNotIn(token, CONTROL + WORLD)
        definition = read("inventory/extractor.tres")
        self.assertIn('compatible_resources = Array[StringName]([&"ferrite", &"cuprite"])', definition)
        self.assertIn('path="res://inventory/ferrite_ore.tres"', definition)

    def test_output_authority_rejects_source_mutations(self):
        resolver = body(WORLD, 'extractor_output_item')
        fallback = 'return preload("res://inventory/ferrite_ore.tres")'
        mutations = {
            'unavailable context fallback': resolver.replace('machine.id:\n\t\t\treturn null', 'machine.id:\n\t\t\t' + fallback, 1),
            'stale descriptor fallback': resolver.replace('has("anchor_cells"):\n\t\t\treturn null', 'has("anchor_cells"):\n\t\t\t' + fallback, 1),
            'unsupported resource fallback': resolver.replace('\n\t\treturn null\n\tvar point', '\n\t\t' + fallback + '\n\tvar point', 1),
            'caller label authority': resolver.replace('match member.resource_type:', 'match machine.v2_resource_type:', 1),
        }
        for label, replacement in mutations.items():
            with self.subTest(mutation=label):
                self.assertNotEqual(replacement, resolver)
                with self.assertRaises(AssertionError):
                    self._assert_output_contract(WORLD.replace(resolver, replacement))

    def test_inspection_requires_resolved_product_and_disables_unavailable_collection(self):
        view = read("scenes/ui/extractor_inspection.gd")
        self.assertIn('product: ItemDefinition = null', view)
        self.assertIn('var configured := definition.has_production() and product != null', view)
        self.assertNotIn('definition.output_item', view)
        self.assertIn('_collect.disabled = not configured or machine.output <= 0 or not in_range', view)
        self.assertIn('"No production configured."', view)
        refresh = body(read('scenes/ui/machine_ui.gd'), '_refresh')
        self.assertIn('var output_item := progression.planet.stored_output_item(machine)', refresh)
        self.assertIn('_in_range(machine),\n\t\t\toutput_item)', refresh)
        self.assertIn("_details.visible = configured", view)
        self.assertIn("_unavailable.visible = not configured", view)

    def test_legacy_queries_and_production_loop_unchanged(self):
        original = subprocess.check_output(["git", "show", BASE + ":scenes/world/planet_world_state.gd"], cwd=ROOT, text=True)
        for name in ("deposit_at", "get_deposit", "get_deposits_in_area", "query_deposit_descriptors",
                     "advance_production", "transfer_input", "collect_output"):
            self.assertEqual(body(WORLD, name), body(original, name), name)

if __name__ == "__main__":
    unittest.main()
