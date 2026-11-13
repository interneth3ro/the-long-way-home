"""Milestone 8 nonexecuting checks; no Godot or project code is invoked."""
from pathlib import Path
import hashlib
import re
import struct
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "5c70fba96fc05053d9ce7c059a0d6fcd0811c3cb"

def read(path):
    return (ROOT / path).read_text(encoding="utf-8")

def body(source, name):
    return re.search(r"^(?:static )?func " + name + r"\(.*?(?=^(?:static )?func |\Z)", source, re.M | re.S)[0]

WORLD = read("scenes/world/planet_world_state.gd")
PRESENTER = read("scenes/world/resource_presenter_v2.gd")
EXTERIOR = read("scenes/world/planet_exterior.gd")

class CupriteGameplayStaticTests(unittest.TestCase):
    def test_approved_icon_bytes_and_transparency(self):
        png = (ROOT / "assets/items/cuprite_ore.png").read_bytes()
        self.assertEqual(hashlib.sha256(png).hexdigest(), "5bf845d4d3620e935ccfe0037e4c0d6ecf98c1b54cfae1f6e7445b5bda9ac129")
        self.assertEqual(struct.unpack(">II", png[16:24]), (256, 256))
        self.assertEqual(png[25], 6)  # original RGBA PNG
        self.assertIn('&"cuprite_ore": preload("res://assets/items/cuprite_ore.png")', read("scenes/ui/item_presentation.gd"))

    def test_item_and_import_conventions(self):
        self.assertEqual(read("inventory/cuprite_ore.tres"), read("inventory/ferrite_ore.tres").replace("ferrite_ore", "cuprite_ore").replace("Ferrite Ore", "Cuprite Ore"))
        old = read("assets/items/ferrite_ore.png.import").split("[params]", 1)[1]
        self.assertEqual(read("assets/items/cuprite_ore.png.import").split("[params]", 1)[1], old)
        self.assertIn('process/premult_alpha=false', old)
        metadata = read('assets/items/cuprite_ore.png.import')
        uid = re.search(r'uid="uid://([a-y0-8]{1,13})"', metadata)[1]
        value = 0
        for char in uid:
            value = value * 34 + "abcdefghijklmnopqrstuvwxy012345678".index(char)
        self.assertTrue(0 < value <= 0x7fffffffffffffff)
        self.assertEqual(sum(('uid://'+uid) in p.read_text() for p in (ROOT/'assets').rglob('*.import')), 1)

    def test_committed_authority_and_supported_mapping(self):
        resolver = body(WORLD, "extractor_output_item")
        for fragment in ('_machines.get(snapshot.get("id", 0), {})', 'machine != snapshot',
                         'extractor_occupant_v2(machine.v2_deposit_id) != machine.id',
                         'resource_descriptor_v2_by_id(machine.v2_deposit_id, context.token)',
                         'ExtractorAnchorRules.member_rejection(member, definition,',
                         'match member.resource_type:', '"cuprite": return preload("res://inventory/cuprite_ore.tres")',
                         '"ferrite": return preload("res://inventory/ferrite_ore.tres")'):
            self.assertIn(fragment, resolver)
        self.assertNotIn('v2_resource_type', resolver)
        self.assertNotIn('"carbite":', resolver)
        self.assertIn('return null', resolver.split('match member.resource_type:')[1].split('var point :=')[0])

    def test_status_and_shared_timing(self):
        status = body(WORLD, "machine_status")
        self.assertIn('extractor_output_item(machine) == null', status)
        self.assertIn('machine.output > definition.output_capacity - definition.output_per_cycle', status)
        for fragment in ('output_per_cycle = 1', 'cycle_seconds = 1.0', 'output_capacity = 20'):
            self.assertIn(fragment, read("inventory/extractor.tres"))
        original = subprocess.check_output(["git", "show", BASE + ":scenes/world/planet_world_state.gd"], cwd=ROOT, text=True)
        self.assertEqual(body(WORLD, "advance_production"), body(original, "advance_production"))
        self.assertEqual(body(WORLD, "_advance_recipe"), body(original, "_advance_recipe"))

    def test_collection_recovery_reuse_transactions(self):
        self.assertIn('return extractor_output_item(machine)', body(WORLD, "stored_output_item"))
        collect = body(WORLD, "collect_output")
        recovery = body(WORLD, "recover_machine")
        self.assertLess(collect.index('inventory.add_item(stored_output_item(machine)'), collect.index('machine.output = 0'))
        self.assertLess(recovery.index('stored_output_item(machine)'), recovery.index('inventory.add_items(recovered, false)'))
        self.assertLess(recovery.index('inventory.add_items(recovered, false)'), recovery.index('_machines.erase(machine_id)'))
        for name in ('collect_output', 'recover_machine'):
            self.assertIn('_machine_transaction = true', body(WORLD, name))

    def test_inspection_receives_resolved_product(self):
        view = read("scenes/ui/extractor_inspection.gd")
        self.assertIn('product: ItemDefinition = null', view)
        self.assertIn('definition.has_production() and product != null', view)
        self.assertIn('ItemPresentation.set_material_icon(_material_icon, product, machine.output)', view)
        self.assertNotIn('definition.output_item', view)
        self.assertIn('progression.planet.stored_output_item(machine)', read("scenes/ui/machine_ui.gd"))

    def test_refresh_declares_and_reuses_resolved_output(self):
        refresh = body(read("scenes/ui/machine_ui.gd"), "_refresh")
        declaration = 'var output_item := progression.planet.stored_output_item(machine)'
        heading = 'output_heading += " — %s" % output_item.display_name'
        inspection = ('_extractor_view.refresh(machine, progression.planet.machine_status(machine), '
                      '_in_range(machine),\n\t\t\toutput_item)')
        self.assertEqual(refresh.count('stored_output_item(machine)'), 1)
        self.assertIn(declaration, refresh)
        self.assertIn('if machine.output > 0 and output_item != null:', refresh)
        self.assertIn(heading, refresh)
        self.assertIn(inspection, refresh)
        self.assertLess(refresh.index(declaration), refresh.index(heading))
        self.assertLess(refresh.index(declaration), refresh.index(inspection))
        self.assertNotIn('definition.output_item', refresh)
        # Dedicated Smelter/Fabricator routes still return before this fixed-output path.
        for route in ('_refresh_fabricator_shell(machine, definition)',
                      '_refresh_smelter(machine, definition)',
                      '_refresh_fabricator(machine, definition)'):
            self.assertLess(refresh.index(route), refresh.index(declaration))

    def test_world_adapter_uses_bounded_queries(self):
        self.assertIn('world.resource_generation_v2_context()', body(PRESENTER, 'configure_world'))
        step = body(PRESENTER, 'step')
        self.assertIn('_world.query_resource_descriptors_v2(page.grow(_reach), _world_token)', step)
        self.assertIn('context.token != _world_token', step)
        self.assertIn('queried.deposits.size() > MAX_DESCRIPTORS', step)
        self.assertIn('page budget exceeded', PRESENTER)
        self.assertNotIn('_resource_v2._source', PRESENTER + EXTERIOR)
        self.assertNotIn('Generator.new(', PRESENTER)

    def test_shared_sprite_path_and_frozen_catalog_validation(self):
        self.assertEqual(PRESENTER.count('Sprite2D.new()'), 1)
        for fragment in ('sprite.position = registration.position', 'sprite.scale = Vector2.ONE * registration.scale',
                         'if not _sprites.has(identity):', 'FileAccess.get_sha256(registration.artwork) != registration.sha256',
                         '_textures.size() >= TEXTURE_LIMIT'):
            self.assertIn(fragment, PRESENTER)

    def test_loaded_terrain_lifecycle_and_preparation(self):
        service = body(EXTERIOR, '_service_resources')
        self.assertIn('for coordinate in _chunks:', service)
        self.assertIn('_resource_presenter.set_loaded_chunks(loaded)', service)
        self.assertIn('_resource_presenter.request(area)', service)
        self.assertIn('_resource_presenter.step(_resource_token)', service)
        self.assertIn('_is_loaded(registration)', body(PRESENTER, 'step'))
        retire = body(PRESENTER, 'set_loaded_chunks')
        for fragment in ('remove_child(sprite)', 'sprite.free()', '_sprites.erase(identity)'):
            self.assertIn(fragment, retire)
        self.assertIn('not _resources_done', body(EXTERIOR, 'prepare_for_arrival'))
        self.assertIn('not _resources_done', body(EXTERIOR, 'prepare_initial_neighborhood'))
        self.assertIn('and _resources_done', body(EXTERIOR, 'arrival_is_ready'))
        self.assertIn('_resource_presenter.cancel()', body(EXTERIOR, 'cancel_arrival_preparation'))

    def test_generation_construction_and_world_art_unchanged(self):
        paths = ['construction/construction_controller.gd', 'construction/extractor_anchor_rules.gd',
                 'construction/placement_rules.gd', 'scenes/world/resource_generation_v2_integration.gd',
                 'scenes/world/resource_presentation_catalog.gd', 'inventory/extractor.tres',
                 'scenes/world/ordinary_resource_generator.gd', 'scenes/world/starting_resource_generator.gd',
                 'scenes/world/resource_generation_descriptors.gd', 'scenes/world/resource_presentations/v2/cuprite.json',
                 'assets/environment/exterior/cuprite/cuprite_prototype_v1.png', 'tools/run-local-tests.ps1']
        for path in paths:
            with self.subTest(path=path):
                original = subprocess.check_output(['git', 'show', BASE + ':' + path], cwd=ROOT)
                current = (ROOT / path).read_bytes()
                if not path.endswith('.png'):
                    current, original = current.replace(b'\r\n', b'\n'), original.replace(b'\r\n', b'\n')
                self.assertEqual(hashlib.sha256(current).digest(), hashlib.sha256(original).digest())

    def test_legacy_and_other_production_methods_preserved(self):
        original = subprocess.check_output(['git', 'show', BASE + ':scenes/world/planet_world_state.gd'], cwd=ROOT, text=True)
        for name in ('extractor_target_v2', 'extractor_anchor_rejection_v2', '_deploy_machine_transaction',
                     'deposit_at', 'query_deposit_descriptors', 'transfer_input', 'collect_output', 'recover_machine',
                     '_recipe_status', '_advance_recipe', 'change_recipe'):
            with self.subTest(method=name):
                self.assertEqual(body(WORLD, name), body(original, name))

    def test_behavioral_coverage_is_authored_and_not_dispatched(self):
        fixture = read('tests/cuprite_gameplay_test.gd')
        for fragment in ('successful Cuprite production', 'full-output status', 'production resume after collection',
                         'correct Cuprite item identity', 'recovery returns stored Cuprite', 'inventory rejection without item loss',
                         'legacy Ferrite production', 'legacy Ferrite recovery', 'unsupported resource inactivity',
                         'presentation positioning', 'streaming unload', 'no duplicate sprites', 'duplicate claim',
                         'failed removal', 'failed placement', 'unavailable authority'):
            self.assertIn(fragment, fixture)
        for path in (ROOT / 'tools').glob('*.ps1'):
            self.assertNotIn('cuprite_gameplay_test', path.read_text())

if __name__ == '__main__':
    unittest.main()
