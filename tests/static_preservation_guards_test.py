"""Regression checks for exact historical projections and dirty-owner rejection."""
import subprocess
import unittest

from native_terrain_preservation import (
    ROOT, REVIEWED_HEAD, TERRAIN_INPUT_SHA256, TEST_UPDATE_SHA256,
    historical_mapping_attributes, verify_terrain_input,
)
from current_preservation import historical_test_bytes


def reviewed(path):
    return subprocess.check_output(['git', 'show', f'{REVIEWED_HEAD}:{path}'], cwd=ROOT)


class PreservationGuardsStaticTest(unittest.TestCase):
    def test_exact_attributes_restore_fonts_and_reject_expansion(self):
        candidate = reviewed('.gitattributes').decode().replace('\r\n', '\n')
        base = subprocess.check_output(['git', 'show', '48cd9150d7aa2e029c7328229e7865cf00e83723:.gitattributes'], cwd=ROOT).decode()
        self.assertEqual(historical_mapping_attributes(base), base)
        self.assertEqual(historical_mapping_attributes(candidate), base)
        for bad in (candidate + '\n', candidate + candidate,
                    candidate.replace('eol=lf', 'eol=crlf', 1),
                    candidate.replace('tlwh_47_pattern_mapping.csv', '*.csv'),
                    candidate.replace(' -text', ' text', 1)):
            with self.subTest(candidate=bad[:60]), self.assertRaises(AssertionError):
                historical_mapping_attributes(bad)

    def test_three_exact_experiment_paths_reject_tampering(self):
        self.assertEqual(len(TERRAIN_INPUT_SHA256), 3)
        for path in TERRAIN_INPUT_SHA256:
            raw = reviewed(path)
            verify_terrain_input(path, raw)
            for bad in (raw + b'UNRELATED', raw + raw, raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    verify_terrain_input(path, bad)
            with self.assertRaises(AssertionError):
                verify_terrain_input(path + '.other', raw)

    def test_test_corrections_are_fully_pinned(self):
        self.assertEqual(set(TEST_UPDATE_SHA256),
                         {'tests/static_musing_ui_test.py', 'tests/static_v2_production_host_test.py'})
        for path in TEST_UPDATE_SHA256:
            old = reviewed(path).replace(b'\r\n', b'\n')
            current = (ROOT / path).read_bytes().replace(b'\r\n', b'\n')
            self.assertEqual(historical_test_bytes(path, old), old)
            self.assertEqual(historical_test_bytes(path, current), old)
            for bad in (current + b'UNRELATED', current + current, current[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    historical_test_bytes(path, bad)

    def test_owner_resource_changes_receive_no_projection_or_whitelist(self):
        for path in ('assets/ui/b1_theme.tres', 'assets/ui/machine_actions.tres',
                     'assets/ui/recipe_chooser.tres', 'construction/recipes/ferrite_plate.tres',
                     'construction/recipes/ferrite_rod.tres', 'dialogue/computer_opening.tres'):
            raw = (ROOT / path).read_bytes() + b'UNREVIEWED OWNER FIXTURE'
            self.assertEqual(historical_test_bytes(path, raw), raw)
            with self.assertRaises(AssertionError):
                verify_terrain_input(path, raw)
