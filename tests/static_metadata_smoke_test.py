"""Non-engine inventory, dependency and production-fixture checks; NOT Godot parsing."""
import hashlib
import json
from pathlib import Path
import re
import subprocess
import unittest

import terrain_stage2_reference as reference

ROOT = reference.ROOT
BASE = "cd91c9086ef24e71ddb6a43a2076c4be5a69485e"
ADDED = {
    "tests/static_metadata_smoke_test.py", "tests/metadata_smoke_test.gd",
    "tests/metadata_smoke_test.gd.uid", "tests/fixtures/metadata_smoke/inputs.json",
    "tests/fixtures/metadata_smoke/project.godot", "tests/fixtures/metadata_smoke/geometry.json",
    "tests/fixtures/metadata_smoke/builder.gd.uid",
}
MODIFIED = {
    "tools/run-local-tests.ps1", "tests/local_runner_fixture_test.ps1", "AGENTS.md",
    "docs/LOCAL_TESTING.md", "docs/experiments/terrain_stage3a1_metadata.md",
    "tests/static_terrain_stage2b_compatibility_test.py",
    "tests/static_terrain_stage2b2_reconstruction_test.py",
    "tests/static_terrain_stage3a1_metadata_test.py",
    "tests/static_ground_publication_test.py", "tests/static_terrain_stage2_coverage_test.py",
}


def read(path):
    return (ROOT/path).read_text()


def before(path):
    return subprocess.check_output(["git", "show", BASE+":"+path], cwd=ROOT, text=True)


class MetadataSmokeTest(unittest.TestCase):
    def test_exact_change_scope_and_preserved_inputs(self):
        # Preserve PR #139's exact merged inventory; the adaptive prototype
        # separately checks its own six-file delta against this endpoint.
        merged = "ee937c98aa5e5bcb087f99c5b0eb8c8960ecf4f0"
        delta = subprocess.check_output(["git", "diff", "--name-status", BASE, merged, "--"], cwd=ROOT, text=True)
        inventory = {path: status for status, path in (line.split("\t", 1) for line in delta.splitlines())}
        untracked = set(subprocess.check_output(["git", "ls-files", "--others", "--exclude-standard"], cwd=ROOT, text=True).splitlines())
        receipt = json.loads(read("artifacts/logs/terrain-preservation-2026-11-03.json"))
        adaptive_additions = {"tests/terrain_adaptive_cpu_reference.py",
                              "tests/static_terrain_adaptive_cpu_test.py",
                              "tools/terrain-adaptive-cpu-diagnostics.py",
                              "docs/experiments/terrain_adaptive_cpu_prototype.md"}
        self.assertEqual(untracked-ADDED-adaptive_additions, set(receipt["protected_sidecars"]))
        inventory.update({path: "A" for path in untracked & ADDED})
        self.assertEqual(inventory, {**dict.fromkeys(ADDED, "A"), **dict.fromkeys(MODIFIED, "M")})
        for path, entry in receipt["protected_sidecars"].items():
            self.assertEqual(hashlib.sha256((ROOT/path).read_bytes()).hexdigest(), entry["sha256"])
        for path in json.loads(read("tests/fixtures/metadata_smoke/inputs.json")):
            if path.startswith(("scenes/", "construction/", "inventory/")):
                self.assertEqual(read(path), before(path), path)

    def test_production_geometry_and_colors_have_not_drifted(self):
        fixture = json.loads(read("tests/fixtures/metadata_smoke/geometry.json"))
        geometry = reference.load_geometry()
        self.assertEqual(fixture["geometry_sha256"], reference.geometry_identity(geometry))
        self.assertEqual(fixture["protected"], [list(p) for p in geometry.gameplay])
        self.assertEqual(fixture["anchors"], [[name, list(p)] for name, p in geometry.anchors])
        for actual, (name, polygon, feather) in zip(fixture["overlays"], geometry.overlays):
            self.assertEqual((actual["name"], actual["polygon"], actual["feather"]),
                             (name, [list(p) for p in polygon], feather))
        self.assertEqual(len(fixture["overlays"]), 4)
        colors = re.findall(r'parent="AuthoredCrashSite"\]\npolygon = [^\n]+\ncolor = Color\(([^)]+)\)', read("scenes/world/planet_exterior.tscn"))
        self.assertEqual([o["color"] for o in fixture["overlays"]], [[float(v) for v in c.split(",")] for c in colors])
        self.assertIn('"feather": 256.0', read("scenes/world/planet_exterior.gd"))

    def test_fixed_inventory_dependency_closure_and_no_assets(self):
        inputs = json.loads(read("tests/fixtures/metadata_smoke/inputs.json"))
        staged = ["project.godot" if p.endswith("metadata_smoke/project.godot") else
                  "scenes/world/continuous_terrain_metadata.gd.uid" if p.endswith("/builder.gd.uid") else p for p in inputs]
        runner = read("tools/run-local-tests.ps1")
        block = runner.split("function Get-MetadataStagePaths {", 1)[1].split("function Get-InputSourcePath", 1)[0]
        self.assertEqual(re.findall(r"'([^']+)'", block), staged)
        self.assertEqual(len(staged), 32)
        self.assertEqual(len(set(staged)), 32)
        self.assertTrue(all((ROOT/p).is_file() for p in inputs))
        self.assertFalse(any(p.startswith("assets/") or p.endswith((".tscn", ".png", ".import")) for p in inputs))
        scripts = [p for p in inputs if p.endswith(".gd")]
        # Inspect all repository class declarations to detect newly referenced types.
        classes = {}
        for directory in ("scenes", "inventory", "construction", "dialogue", "objectives"):
            for path in (ROOT/directory).rglob("*.gd"):
                match = re.search(r"^class_name (\w+)", path.read_text(), re.M)
                if match:
                    classes[match[1]] = path.relative_to(ROOT).as_posix()
        for path in scripts:
            source = read(path)
            code = re.sub(r'"[^"\n]*"|#[^\n]*', '', source)
            for token in set(re.findall(r"\b[A-Za-z_]\w*\b", code)) & classes.keys():
                self.assertIn(classes[token], scripts, (path, token))
            for dependency in re.findall(r'preload\("res://([^"\n]+)"\)', source):
                self.assertIn(dependency, inputs, (path, dependency))
            self.assertIn(path+".uid", staged)
        self.assertNotIn("PlanetWorldState.new", read("tests/metadata_smoke_test.gd"))
        self.assertNotIn("FerriteRegionGenerator.new", read("tests/metadata_smoke_test.gd"))
        self.assertNotIn("[autoload]", read(inputs[0]))
        self.assertNotIn("run/main_scene", read(inputs[0]))
        # Only dormant Ferrite initialization references the unstaged catalog.
        self.assertIn("func _init(world_seed: int)", read("scenes/world/ferrite_region_generator.gd"))

    def test_golden_inventory_preserves_supported_and_unsupported_cases(self):
        path = "tests/fixtures/terrain_stage2_classification_vectors.json"
        # Retain every historical expected material, not just a selected subset.
        self.assertEqual(read(path), before(path))
        records = json.loads(read(path))["records"]
        self.assertEqual(len(records), 14)
        supported, unsupported = [], []
        for record in records:
            cell = tuple(record["cell"])
            owner = tuple(n // 32 for n in cell)  # Independent floor ownership.
            if all(-16 <= n <= 15 for n in owner):
                supported.append(record)
            else:
                unsupported.append((cell, owner, record["material"]))
        self.assertEqual(len(supported), 12)
        self.assertEqual(unsupported, [((16384, -16385), (512, -513), 2),
                                       ((-16385, 16384), (-513, 512), 0)])

    def test_smoke_goldens_check_rejection_and_direct_classifier_outside_envelope(self):
        source = read("tests/metadata_smoke_test.gd")
        loop = source.split("\tfor record in vectors.records:\n", 1)[1].split(
            "\tcheck(WorldCoordinates.world_to_terrain", 1)[0]
        setup, branches = loop.split("\t\tif supported:\n", 1)
        supported, unsupported = branches.split("\t\telse:\n", 1)
        self.assertIn("var owner := WorldCoordinates.terrain_to_chunk(cell)", setup)
        self.assertIn("var local := cell - owner * 32", setup)
        self.assertIn("var result := build(int(record.seed), owner, geometry)", setup)
        self.assertIn("var supported: bool = owner.x >= Metadata.MIN_CHUNK and owner.x <= Metadata.MAX_CHUNK", setup)
        self.assertIn("and owner.y >= Metadata.MIN_CHUNK and owner.y <= Metadata.MAX_CHUNK", setup)
        self.assertIn('check(result.get("ok", false), "golden prepare")', supported)
        self.assertIn('if result.get("ok", false):', supported)
        self.assertIn('check(result.materials[(local.y + 1) * 34 + local.x + 1] == int(record.material), "offline golden")', supported)
        self.assertIn('check(result == {"ok": false, "error": "unsupported_chunk"}, "unsupported golden owner")', unsupported)
        self.assertIn('var golden_generator := Generator.new(int(record.seed), overlays, geometry.protected, anchors)', unsupported)
        self.assertIn('check(golden_generator.sample_ground_material(cell) == int(record.material), "unsupported offline golden")', unsupported)
        self.assertNotIn("result.materials", unsupported)
        self.assertNotIn("continue", loop)
        # Assertions outside the golden loop are intentionally untouched.
        base = "ec3d1911ba117f745aa680a3ebf4ae8380e6b694"
        old = subprocess.check_output(["git", "show", base+":tests/metadata_smoke_test.gd"], cwd=ROOT, text=True)
        start = "\tfor record in vectors.records:\n"
        end = "\tcheck(WorldCoordinates.world_to_terrain"
        self.assertEqual(source.split(start, 1)[0], old.split(start, 1)[0])
        self.assertEqual(source.split(end, 1)[1], old.split(end, 1)[1])

    def test_historical_guard_amendments_only_scope_endpoints(self):
        path = "tests/static_terrain_stage2b2_reconstruction_test.py"
        expected = before(path).replace("['git','diff','--name-status',reference.BASE,'--']",
                                        "['git','diff','--name-status',reference.BASE,'"+BASE+"','--']")
        start = expected.index("        untracked=set(subprocess.check_output(")
        end = expected.index("        self.assertEqual(inventory", start)
        expected = expected[:start]+"        receipt=json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())\n"+expected[end:]
        expected = expected.replace('        self.assertEqual((ROOT/AMENDMENT).read_text(),expected)',
                                    "        historical=subprocess.check_output(['git','show','"+BASE+":'+AMENDMENT],cwd=ROOT,text=True)\n        self.assertEqual(historical,expected)")
        self.assertEqual(read(path), expected)
        path = "tests/static_terrain_stage2b_compatibility_test.py"
        self.assertEqual(read(path), before(path).replace(
            '        current = (ROOT / AMENDMENT).read_text()',
            '        current = subprocess.check_output(["git", "show", "'+BASE+':"+AMENDMENT], cwd=ROOT, text=True)'))
        path = "tests/static_terrain_stage3a1_metadata_test.py"
        self.assertEqual(read(path), before(path).replace(
            '        after = (ROOT/path).read_text()',
            "        # Validate the immutable merged 3A-1 amendment; 3A-2 checks its own exact delta.\n"
            "        after = subprocess.check_output(['git', 'show', '"+BASE+":'+path], cwd=ROOT, text=True)"))
        # Every historical mathematical and source pin stays intact. Only runner
        # comparisons use pre-extension bytes; every other path remains current.
        for path in ("tests/static_ground_publication_test.py", "tests/static_terrain_stage2_coverage_test.py"):
            old = before(path)
            current = read(path)
            actual = re.search(r"            actual = \(subprocess.check_output.*?else \(ROOT/path\).read_bytes\(\)\)\n", current, re.S)
            self.assertIsNotNone(actual)
            self.assertIn("if path == ", actual[0])
            self.assertIn("tools/run-local-tests.ps1", actual[0])
            current = current.replace(actual[0], "")
            current = current.replace("actual.replace(b'\\r\\n', b'\\n')", "(ROOT/path).read_bytes().replace(b'\\r\\n', b'\\n')")
            current = current.replace('actual.replace(b"\\r\\n", b"\\n")', '(ROOT / path).read_bytes().replace(b"\\r\\n", b"\\n")')
            self.assertEqual(current, old)


if __name__ == "__main__":
    unittest.main()
