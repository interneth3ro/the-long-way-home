"""Cuprite layout contracts only; no project code or Godot is executed."""
import ast
import hashlib
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "ba48f716c804f03e2073dd191d7df41d48d94dcc"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def original(path):
    return subprocess.check_output(["git", "show", BASE + ":" + path], cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def body(source, name):
    return re.search(r"^(?:static )?func " + name + r"\(.*?(?=^(?:static )?func |\Z)",
                     source, re.M | re.S)[0]


STARTING = read("scenes/world/starting_resource_generator.gd")


class CupriteLayoutTests(unittest.TestCase):
    def test_live_prototype_removed_and_other_authored_nodes_preserved(self):
        path = "scenes/world/planet_exterior.tscn"
        scene = read(path)
        for token in ("CupriteVisualPrototype", "cuprite_visual_prototype.tscn", "9_cuprite_prototype"):
            self.assertNotIn(token, scene)
        self.assertEqual(int(re.search(r"load_steps=(\d+)", scene)[1]),
                         1 + scene.count("[ext_resource ") + scene.count("[sub_resource "))
        nodes = lambda text: dict(re.findall(r'(^\[node [^\n]+\])(.*?)(?=^\[|\Z)', text, re.M | re.S))
        old, new = nodes(original(path)), nodes(scene)
        removed = [key for key in old if 'name="CupriteVisualPrototype"' in key]
        self.assertEqual(len(removed), 1)
        old.pop(removed[0])
        self.assertEqual({k: v.strip() for k, v in new.items()}, {k: v.strip() for k, v in old.items()})

    def test_reference_scene_and_approved_generated_artwork_remain(self):
        prototype = "scenes/world/cuprite_visual_prototype.tscn"
        self.assertEqual(read(prototype), original(prototype))
        catalog = "scenes/world/resource_presentations/v2/cuprite.json"
        self.assertEqual(read(catalog), original(catalog))
        png = ROOT / "assets/environment/exterior/cuprite/cuprite_prototype_v1.png"
        self.assertEqual(hashlib.sha256(png.read_bytes()).hexdigest(),
                         "6a3ed462b0da325b0dc334b0fb0f5d467242d7758dbd71bfe2aa46dff8b531fe")
        self.assertIn('configure_world(state,', read("scenes/world/planet_exterior.gd"))
        self.assertIn('res://scenes/world/resource_definitions/v2/cuprite.tres', read("scenes/world/planet_exterior.gd"))

    def test_exact_band_weights_only_cuprite_preference_changes(self):
        rows = ast.literal_eval(re.search(r"const BAND_THRESHOLDS := (.*)", STARTING)[1])
        self.assertEqual(rows, [[25, 90], [10, 65], [45, 90]])
        for row, expected in zip(rows, ((25, 65, 10), (10, 55, 35), (45, 45, 10))):
            bands = [0 if roll < row[0] else 1 if roll < row[1] else 2 for roll in range(100)]
            self.assertEqual(tuple(bands.count(i) for i in range(3)), expected)
        self.assertIn("const BAND_CELLS := [[14, 22], [26, 46], [50, 68]]", STARTING)

    def test_counts_anchors_spacing_and_protection_remain_active(self):
        self.assertIn('const REQUIRED := {"ferrite": 3, "carbite": 2, "cuprite": 2}', STARTING)
        for fragment in ("const ARRANGEMENT_BUDGET: int = 4096", "Vector2i(4, 4)",
                         "if _arrangement_valid(arrangement):", "not _eligible(location)",
                         "_conflicts(location, locations[previous])", "return counts == REQUIRED",
                         "distance < MIN_DISTANCE or distance > MAX_DISTANCE"):
            self.assertIn(fragment, STARTING)
        for method in ("_arrangement_valid", "_arrangement"):
            self.assertEqual(body(STARTING, method), body(original("scenes/world/starting_resource_generator.gd"), method))
        self.assertEqual(read("scenes/world/resource_generation_crash_site.gd"), original("scenes/world/resource_generation_crash_site.gd"))

    def test_revised_policy_is_current_and_old_token_is_not_an_alias(self):
        self.assertIn('const STARTING_POLICY: String = "starting-v2-2"', STARTING)
        self.assertIn("if policy != STARTING_POLICY:", STARTING)
        self.assertIn("return STARTING_POLICY", body(STARTING, "identity_policy"))
        self.assertIn('starting_policy: String = "starting-v2-2"', read("scenes/world/planet_world_state.gd"))
        integration = read("scenes/world/resource_generation_v2_integration.gd")
        for fragment in ("starting_policy == Starting.STARTING_POLICY", '"starting_policy": Starting.STARTING_POLICY',
                         "location.generation_policy != Starting.STARTING_POLICY"):
            self.assertIn(fragment, integration)

    def test_ordinary_distribution_and_transition_draws_preserved(self):
        ordinary = "scenes/world/ordinary_resource_generator.gd"
        self.assertEqual(read(ordinary), original(ordinary))
        self.assertIn('const TRANSITION_SAMPLING_DOMAIN: String = "starting-v2-1"', STARTING)
        old = original("scenes/world/starting_resource_generator.gd")
        self.assertIn('domain: String = STARTING_POLICY', body(STARTING, "_starting_sample"))
        self.assertIn('[domain, _seed, attempt, slot, channel]', body(STARTING, "_starting_sample"))
        self.assertIn('return key.sha256_text().left(7).hex_to_int()', body(STARTING, "_starting_sample"))
        self.assertIn(', TRANSITION_SAMPLING_DOMAIN)', body(STARTING, "_ordinary_allowed"))
        self.assertEqual(body(STARTING, "_ordinary_allowed").replace(', TRANSITION_SAMPLING_DOMAIN)', ')'),
                         body(old, "_ordinary_allowed"))
        for method in ("transition_density", "_candidate"):
            self.assertEqual(body(STARTING, method), body(old, method))
        for resource in ("ferrite", "carbite", "cuprite"):
            path = "scenes/world/resource_definitions/v2/" + resource + ".tres"
            self.assertEqual(read(path), original(path))

    def test_legacy_ferrite_queries_production_and_construction_unchanged(self):
        path = "scenes/world/planet_world_state.gd"
        world, old = read(path), original(path)
        for method in ("deposit_at", "query_deposit_descriptors", "extractor_target_v2",
                       "advance_production", "collect_output", "recover_machine"):
            self.assertEqual(body(world, method), body(old, method))

    def test_current_policy_behavior_is_authored_without_dispatch(self):
        behavior = read("tests/cuprite_world_layout_test.gd")
        for label in ("revised starting policy", "complete starting counts", "same-seed deterministic layout",
                      "old policy rejected", "anchor geometry", "Cuprite anchor-center distance"):
            self.assertIn(label, behavior)
        integration = read("tests/resource_generation_v2_integration_test.gd")
        self.assertIn('context.starting_policy == "starting-v2-2"', integration)
        self.assertIn('"resource:starting-v2-2:%d:0:0:0:0" % (seed_value + 1)', integration)
        for runner in (ROOT / "tools").glob("*.ps1"):
            self.assertNotIn("cuprite_world_layout_test", runner.read_text())


if __name__ == "__main__":
    unittest.main()
