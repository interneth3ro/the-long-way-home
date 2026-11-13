"""Nonexecuting regression checks for owner-reported fixture inference errors."""
from pathlib import Path
import re
import subprocess
import unittest

ROOT = Path(__file__).resolve().parents[1]
BASE = "3c28f42ffb0b72130c4f7306e5e58649bf1e4098"
FIXTURES = {
    "ordinary_resource_generator_test.gd": {"a", "b", "tight", "middle", "last"},
    "starting_resource_generator_test.gd": {"a", "b", "reservation", "location", "nearby"},
}


class ResourceFixtureTypingTests(unittest.TestCase):
    def test_dictionary_field_results_have_explicit_types(self):
        for filename, expected in FIXTURES.items():
            with self.subTest(fixture=filename):
                source = (ROOT / "tests" / filename).read_text(encoding="utf-8")
                declarations = re.findall(
                    r"var (\w+): Dictionary = Descriptors\.create_location\(", source)
                self.assertEqual(set(declarations), expected)
                self.assertEqual(len(declarations), len(expected))
                self.assertNotRegex(source, r"var \w+ := Descriptors\.create_location\(")

    def test_only_declaration_types_change_existing_fixtures(self):
        for filename in FIXTURES:
            with self.subTest(fixture=filename):
                path = "tests/" + filename
                original = subprocess.check_output(
                    ["git", "show", BASE + ":" + path], cwd=ROOT, text=True)
                source = (ROOT / path).read_text(encoding="utf-8")
                restored = re.sub(
                    r"var (\w+): Dictionary = (Descriptors\.create_location\()",
                    r"var \1 := \2", source)
                self.assertEqual(restored, original)


if __name__ == "__main__":
    unittest.main()
