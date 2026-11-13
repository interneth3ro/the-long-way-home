"""Nonexecuting Milestone 6 source, isolation and preservation checks.
No Godot or project code executes; behavioral assertions remain unexecuted.
"""
from pathlib import Path
import hashlib
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "2614769057ece59bd38df8b744be724c9f4802b3"
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


def git(*args):
    return subprocess.check_output(["git", *args], cwd=ROOT)


class ResourceIntegrationStaticTests(unittest.TestCase):
    def test_world_owns_component_and_preserves_every_legacy_method(self):
        self.assertIn("var _resource_v2 := ResourceGenerationV2Integration.new()", WORLD)
        init = body(WORLD, "_init")
        self.assertIn("_world_generation_seed = world_seed", init)
        self.assertIn("configure_resource_generation_v2()", init)
        old = git("show", f"{BASE}:{WORLD_PATH}").decode()
        for name in re.findall(r"^func (\w+)\(", old, re.M):
            if name != "_init":
                self.assertEqual(body(WORLD, name), body(old, name), name)
        self.assertIn("_ferrite = FerriteRegionGenerator.new(world_seed)", init)

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

    def test_protected_tracked_inputs_are_unchanged_from_baseline(self):
        paths = git("ls-tree", "-r", "--name-only", BASE).decode().splitlines()
        protected = [p for p in paths if p.startswith(("assets/", "construction/", "inventory/",
                     "persistence/", "scenes/", "tools/", "tests/"))
                     or p in ("AGENTS.md", "project.godot", ".gitattributes")]
        changed = set(git("diff", "--name-only", BASE).decode().splitlines())
        self.assertLessEqual(changed.intersection(protected), {WORLD_PATH})
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
                      "seed changes cannot resurrect context", "partial layout rejected"):
            self.assertIn(label, BEHAVIOR)
        for source in (SOURCE, WORLD, BEHAVIOR):
            for ref in re.findall(r'(?:preload\(|extends )"res://([^"\n]+)"', source):
                self.assertTrue((ROOT / ref).is_file(), ref)
        for runner in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("resource_generation_v2_integration_test", runner.read_text())


if __name__ == "__main__":
    unittest.main()
