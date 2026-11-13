"""Nonexecuting Milestone 6 source, isolation and preservation checks.
No Godot or project code executes; behavioral assertions remain unexecuted.
"""
from pathlib import Path
import hashlib
import re
import unittest

ROOT = Path(__file__).resolve().parents[1]
COMPONENT_PATH = "scenes/world/resource_generation_v2_integration.gd"
WORLD_PATH = "scenes/world/planet_world_state.gd"
SOURCE = (ROOT / COMPONENT_PATH).read_text()
WORLD = (ROOT / WORLD_PATH).read_text()
BEHAVIOR = (ROOT / "tests/resource_generation_v2_integration_test.gd").read_text()


def body(source, name):
    return re.search(r"^(?:static )?func " + name + r"\(.*?(?=^(?:static )?func |\Z)",
                     source, re.M | re.S)[0]


def code(source):
    return "\n".join(line.split("#")[0] for line in source.splitlines())


class ResourceIntegrationStaticTests(unittest.TestCase):
    def test_world_owns_component_and_legacy_apis_remain_independent(self):
        self.assertIn("var _resource_v2 := ResourceGenerationV2Integration.new()", WORLD)
        init = body(WORLD, "_init")
        self.assertIn("_world_generation_seed = world_seed", init)
        self.assertIn("configure_resource_generation_v2()", init)
        self.assertIn("_ferrite = FerriteRegionGenerator.new(world_seed)", init)
        legacy_routes = {
            "is_resource_generation_ready": "_ferrite.is_ready()",
            "resource_generation_error": "_ferrite.initialization_error()",
            "get_deposit_region": "_ferrite.region(owner)",
            "query_deposit_descriptors": "_ferrite.query(area)",
            "deposit_query_owners": "_ferrite.query_owners(area)",
            "deposit_resource": "_ferrite.resource(descriptor)",
            "get_deposit_variant": "_ferrite.variant_metadata(variant_id)",
        }
        for name, route in legacy_routes.items():
            self.assertIn("return " + route, code(body(WORLD, name)), name)
        for name in ("get_deposit", "deposit_at", "get_deposits_in_area"):
            self.assertIn("_ferrite.", code(body(WORLD, name)), name)
            self.assertIn("_deposits", code(body(WORLD, name)), name)
        # Protect the isolation boundary as methods evolve, without freezing their
        # entire historical implementation or banning later unrelated features.
        for name in re.findall(r"^func (\w+)\(", WORLD, re.M):
            if name != "_init" and not (name.endswith("_v2") or "resource_generation_v2" in name
                                       or name == "resource_descriptor_v2_by_id"):
                block = code(body(WORLD, name))
                self.assertNotIn("_resource_v2", block, name)
                self.assertNotIn("resource_generation_v2", block, name)

    def test_seed_is_authoritative_and_in_place_reseed_fails_closed(self):
        configure = body(WORLD, "configure_resource_generation_v2")
        self.assertIn("seed_value != _world_generation_seed", configure)
        self.assertIn("_resource_v2.invalidate(", configure)
        self.assertIn("_resource_v2.configure(seed_value,", configure)
        setter = WORLD.split("var seed_value: int:", 1)[1].split("var revision:", 1)[0]
        self.assertIn("if seed_value != value", setter)
        self.assertIn("_resource_v2.invalidate(", setter)
        self.assertNotIn("rand", code(SOURCE))

    def test_fixed_native_inputs_and_no_protection_override(self):
        self.assertIn("extends RefCounted", SOURCE)
        for kind in ("ferrite", "carbite", "cuprite"):
            path = f"scenes/world/resource_definitions/v2/{kind}.tres"
            self.assertIn(f'res://{path}', SOURCE)
        self.assertIn("CrashSite.protected_bounds()", SOURCE)
        self.assertIn("CrashSite.SHIP_REFERENCE", SOURCE)
        self.assertIn("if protection.is_empty():", SOURCE)
        self.assertIn("definitions.append(definition.duplicate(true))", SOURCE)
        for parameter in ("protected_bounds:", "ship_reference:", "definitions:"):
            self.assertNotIn(parameter, body(SOURCE, "configure").split("-> Dictionary:")[0])

    def test_atomic_publication_and_idempotency(self):
        configure = body(SOURCE, "configure")
        operations = ['if is_ready() and supported and world_seed == _seed:',
                      'invalidate("v2 replacement is incomplete")',
                      'if not supported:', 'var candidate := Starting.new(',
                      'if not candidate.is_ready():', 'var layout := candidate.reservations()',
                      '_error = _reservation_error(', 'if not _error.is_empty():',
                      '_source = candidate', '_token = RefCounted.new()']
        positions = [configure.index(value) for value in operations]
        self.assertEqual(positions, sorted(positions))
        self.assertEqual(configure.count("_source ="), 1)
        retire = body(SOURCE, "invalidate")
        for statement in ("_source = null", "_token = null", "_error = reason"):
            self.assertIn(statement, retire)

    def test_complete_layout_admission_uses_existing_schema(self):
        admission = body(SOURCE, "_reservation_error")
        for check in ("locations.size() > 7", "Descriptors.configured_location_error(",
                      "location.world_seed != world_seed", "Starting.STARTING_POLICY",
                      "Starting.START_SLOT", "Ordinary.owner_is_supported(",
                      "Ordinary.owner_at(", "seen.has(location.location_id)",
                      "seen.has(member.deposit_id)", "counts != Starting.REQUIRED"):
            self.assertIn(check, admission)
        self.assertNotIn("_arrangement(", SOURCE)

    def test_errors_never_supply_success_payloads(self):
        failure = body(SOURCE, "_failure")
        self.assertIn('{"ok": false, "code": code, "error": error}', failure)
        for label in ("unavailable", "stale_context", "invalid_query", "invalid_identity",
                      "not_found", "incompatible_context", "initialization_failed"):
            self.assertIn(f'"{label}"', SOURCE)
        admitted = body(SOURCE, "_admission")
        self.assertLess(admitted.index("if not is_ready():"), admitted.index("token != _token"))
        self.assertIn("not_found", body(SOURCE, "descriptor_by_id"))

    def test_bounded_deep_copied_reads_and_narrow_public_api(self):
        for method in ("query", "descriptor_by_id", "reservations"):
            block = body(SOURCE, method)
            self.assertIn("_admission(token)", block)
            self.assertIn("duplicate(true)", block)
            self.assertIn(f"_source.{method}(", block)
        self.assertNotIn("region(", code(SOURCE))
        self.assertNotIn("_cache", code(SOURCE))
        self.assertNotIn('"source":', SOURCE)
        self.assertIn('"token": _token', body(SOURCE, "context"))
        for name in ("query_resource_descriptors_v2", "resource_descriptor_v2_by_id",
                     "starting_resource_reservations_v2"):
            self.assertIn("token: RefCounted", body(WORLD, name))

    def test_no_gameplay_activation_or_streaming_callers(self):
        for forbidden in ("ResourceDeposit", "ResourcePresenter", "Texture2D", "Node2D",
                          "occupancy", "inventory.", "deploy_machine", "advance_production",
                          "add_child", "autoload", "FileAccess"):
            self.assertNotIn(forbidden, code(SOURCE))
        for root in ("scenes", "construction", "inventory"):
            for path in (ROOT / root).rglob("*.gd"):
                if path in (ROOT / WORLD_PATH, ROOT / COMPONENT_PATH):
                    continue
                text = code(path.read_text(encoding="utf-8"))
                self.assertNotIn("resource_generation_v2_integration", text, str(path))
                self.assertNotIn("configure_resource_generation_v2(", text, str(path))

    def test_approved_generation_contracts_and_frozen_artwork(self):
        # Approved versioned contracts remain guarded; unrelated future files,
        # authorized feature additions and test maintenance are not frozen.
        ordinary = (ROOT / "scenes/world/ordinary_resource_generator.gd").read_text()
        starting = (ROOT / "scenes/world/starting_resource_generator.gd").read_text()
        descriptors = (ROOT / "scenes/world/resource_generation_descriptors.gd").read_text()
        definition = (ROOT / "scenes/world/world_resource_definition.gd").read_text()
        self.assertIn('const POLICY: String = "ordinary-v2-1"', ordinary)
        self.assertIn('const STARTING_POLICY: String = "starting-v2-2"', starting)
        self.assertIn('const TRANSITION_SAMPLING_DOMAIN: String = "starting-v2-1"', starting)
        self.assertIn('const SCHEMA_VERSION: int = 1', descriptors)
        self.assertIn('const REQUIRED := {"ferrite": 3, "carbite": 2, "cuprite": 2}', starting)
        self.assertIn('const ANCHOR_CELLS := Vector2i(4, 4)', definition)
        for constant, value in (("REGION_SIZE", 1536), ("MAX_QUERY_REGIONS", 64), ("CACHE_LIMIT", 32)):
            self.assertIn(f"const {constant}: int = {value}", ordinary)
        artwork = ROOT / "assets/environment/exterior/cuprite/cuprite_prototype_v1.png"
        self.assertEqual(hashlib.sha256(artwork.read_bytes()).hexdigest(),
                         "6a3ed462b0da325b0dc334b0fb0f5d467242d7758dbd71bfe2aa46dff8b531fe")

    def test_behavioral_tests_are_authored_only_and_references_exist(self):
        for label in ("successful initialization", "complete seven-deposit starting reservations",
                      "stable descriptor queries", "stable deposit-ID resolution",
                      "same-context idempotency", "changed-context invalidation",
                      "failed replacement behavior", "rejection of stale references",
                      "invalid query distinction", "unavailable context distinction",
                      "preservation of legacy Ferrite behavior", "streaming-independent resource identity",
                      "seed changes cannot resurrect context", "partial layout rejected",
                      "incompatible identity policy with current seed", "wrong identity seed with current policy",
                      "failed context has no token", "failed component has no reservations",
                      "repeated failure cannot restore retired context"):
            self.assertIn(label, BEHAVIOR)
        self.assertIn('"resource:ordinary-v2-1:%d:0:0:0:0" % seed_value', BEHAVIOR)
        self.assertIn('"resource:starting-v2-2:%d:0:0:0:0" % (seed_value + 1)', BEHAVIOR)
        self.assertIn('_check_failure(world.resource_descriptor_v2_by_id(wrong_policy, token), "incompatible_context"', BEHAVIOR)
        self.assertIn('_check_failure(world.resource_descriptor_v2_by_id(wrong_seed, token), "invalid_identity"', BEHAVIOR)
        for guard in ('result.size() == 3', 'result.get("ok") == false',
                      'result.get("code") == expected_code', 'result.get("error") is String'):
            self.assertIn(guard, body(BEHAVIOR, "_check_failure"))
        for source in (SOURCE, WORLD, BEHAVIOR):
            for ref in re.findall(r'(?:preload\(|extends )"res://([^"\n]+)"', source):
                self.assertTrue((ROOT / ref).is_file(), ref)
        for runner in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("resource_generation_v2_integration_test", runner.read_text())


if __name__ == "__main__":
    unittest.main()
