"""Static contract/admission/preservation checks; never executes Godot or GDScript.

Behavioral assertions live in resource_generation_v2_contract_test.gd and remain
unexecuted. Formatting vectors below specify bytes, not generator determinism.
"""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "8430aacafa1e1cb08db1d7a5451d1ace66040e15"
DEFINITION_PATH = "scenes/world/world_resource_definition.gd"
DESCRIPTORS_PATH = "scenes/world/resource_generation_descriptors.gd"
RUNTIME_PATH = "tests/resource_generation_v2_contract_test.gd"
DEFINITION = (ROOT / DEFINITION_PATH).read_text(encoding="utf-8")
DESCRIPTORS = (ROOT / DESCRIPTORS_PATH).read_text(encoding="utf-8")
RUNTIME = (ROOT / RUNTIME_PATH).read_text(encoding="utf-8")
SPEC = (ROOT / "docs/RESOURCE_GENERATION_V2_CONTRACTS.md").read_text(encoding="utf-8")


class ResourceGenerationV2StaticTests(unittest.TestCase):
    def test_native_definition_fields_and_unconfigured_default(self):
        self.assertIn("extends Resource", DEFINITION)
        for field in ("resource_id", "abundance_weight", "geological_preferences",
                      "allowed_environments", "restricted_environments",
                      "presentation_catalog", "anchor_cells"):
            self.assertRegex(DEFINITION, rf"@export[^\n]*var {field}:")
        self.assertIn("abundance_weight: float = 0.0", DEFINITION)
        self.assertIn("const ANCHOR_CELLS := Vector2i(4, 4)", DEFINITION)
        fixture = (ROOT / "tests/fixtures/resource_generation_v2/cuprite.tres").read_text()
        self.assertIn('script_class="WorldResourceDefinition"', fixture)
        self.assertIn('path="res://' + DEFINITION_PATH + '"', fixture)
        self.assertIn('resource_id = &"cuprite"', fixture)
        self.assertIn("abundance_weight = 1.0", fixture)
        self.assertIn("synthetic", SPEC)

    def test_focused_configuration_guards(self):
        for guard in ("not is_finite(abundance_weight)", "abundance_weight <= 0.0",
                      "anchor_cells != ANCHOR_CELLS", "seen.has(definition.resource_id)",
                      "definition == null", "supported_geology.has(StringName(key))",
                      "supported_environments.has(environment)", "seen.has(environment)",
                      "restricted_environments.has(environment)", "not is_finite(float(weight))"):
            self.assertIn(guard, DEFINITION)
        self.assertIn('"abcdefghijklmnopqrstuvwxyz0123456789_-"', DEFINITION)
        self.assertIn('value.begins_with("res://")', DEFINITION)
        self.assertIn('["", ".", ".."]', DEFINITION)

    def test_exact_identity_format_and_int64_negative_coordinate_vectors(self):
        location_format = re.search(r'return "(resource-location:[^"]+)"', DESCRIPTORS)[1]
        deposit_format = re.search(r'return "(resource:[^"]+)"', DESCRIPTORS)[1]
        inputs = ("v2", -9223372036854775807, -2, -3, 7)
        self.assertEqual(location_format % inputs,
                         "resource-location:v2:-9223372036854775807:-2:-3:7")
        for index in range(3):
            self.assertEqual(deposit_format % (*inputs, index),
                             f"resource:v2:-9223372036854775807:-2:-3:7:{index}")
        self.assertIn("[policy, seed_value, owner.x, owner.y, slot]", DESCRIPTORS)
        self.assertIn("[policy, seed_value, owner.x, owner.y, slot, index]", DESCRIPTORS)

    def test_descriptor_input_types_and_membership_guards(self):
        for guard in ("data.schema_version is int", "data.world_seed is int",
                      "data.owner_region is Vector2i", "data.location_slot is int",
                      "data.location_slot < 0", "data.deposits.size() < 1",
                      "data.deposits.size() > 3", "member.member_index is int",
                      "member.member_index != index", "member.location_id != identity",
                      "member.resource_type != data.resource_type", "member.deposit_id != expected",
                      "member.anchor_cells is Rect2i", "member.anchor_cells.size != Definition.ANCHOR_CELLS",
                      "anchor.intersects(other)", "MAX_CELL_COORDINATE",
                      "presentation.size() != anchors.size()"):
            self.assertIn(guard, DESCRIPTORS)
        self.assertIn('return "resource_type has no configured definition:', DESCRIPTORS)

    def test_atomic_result_and_metadata_separation(self):
        self.assertIn('presentation[index].duplicate(true)', DESCRIPTORS)
        self.assertIn('key not in ["catalog_ref", "variant_id"]', DESCRIPTORS)
        self.assertIn('return {"ok": false, "error": error}', DESCRIPTORS)
        self.assertLess(DESCRIPTORS.index("var error := location_error(location)"),
                        DESCRIPTORS.index('return {"ok": true, "location": location}'))
        for name in ("LOCATION_FIELDS", "DEPOSIT_FIELDS"):
            self.assertIn(f"_has_fields({'data' if name == 'LOCATION_FIELDS' else 'member'}, {name})", DESCRIPTORS)

    def test_authored_behavioral_coverage_is_not_execution(self):
        for label in ("single pair triple construction", "negative owner and int64 seed golden",
                      "invalid abundance rejected", "unknown geology rejected",
                      "conflicting restrictions rejected", "size overflow overlap rejection",
                      "invalid group publishes no partial location", "reordered membership rejected",
                      "anchor and artwork independent identity", "caller metadata copied",
                      "unconfigured type rejected", "future allowed-only configuration"):
            self.assertIn(label, RUNTIME)
        self.assertIn('"ferrite", &"carbite", &"cuprite"', RUNTIME)
        self.assertIn("not executed", SPEC)

    def test_no_runtime_io_or_generation_dependencies(self):
        for source in (DEFINITION, DESCRIPTORS):
            executable = "\n".join(line.split("#")[0] for line in source.splitlines())
            for forbidden in ("FileAccess", "DirAccess", "OS.", "RandomNumberGenerator",
                              "PlanetWorldState", "FerriteRegionGenerator", "Node2D",
                              "load(", "get_tree(", "Texture2D", "quantity", "depletion"):
                self.assertNotIn(forbidden, executable.replace("preload(", "PRELOAD("))
        for runner in ("tools/run-local-tests.ps1", "tools/run-save-codec-tests.ps1"):
            self.assertNotIn("resource_generation_v2_contract_test", (ROOT / runner).read_text())

    def test_legacy_assets_simulation_and_controls_are_preserved(self):
        protected = ["scenes/world/resource_deposit.gd", "scenes/world/planet_world_state.gd",
                     "scenes/world/ferrite_region_generator.gd", "scenes/world/ferrite_deposit_presenter.gd",
                     "construction", "inventory", "persistence", "assets", "tools", "AGENTS.md",
                     "scenes/world/cuprite_visual_prototype.tscn", "scenes/world/planet_exterior.tscn",
                     "scenes/world/introductory_ferrite.tres"]
        changed = subprocess.check_output(
            ["git", "diff", "--name-only", BASE, "--", *protected], cwd=ROOT, text=True)
        self.assertEqual(changed, "", "Protected tracked inputs differ from reviewed baseline")


if __name__ == "__main__":
    unittest.main()
