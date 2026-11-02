"""Immutable original terrain experiment corruption checks."""
import unittest

from native_terrain_preservation import ROOT, TERRAIN_INPUT_SHA256, verify_terrain_input


class PreservationGuardsStaticTest(unittest.TestCase):

    def test_three_exact_experiment_paths_reject_tampering(self):
        self.assertEqual(len(TERRAIN_INPUT_SHA256), 3)
        for path in TERRAIN_INPUT_SHA256:
            raw = (ROOT/path).read_bytes()
            verify_terrain_input(path, raw)
            for bad in (raw + b'UNRELATED', raw + raw, raw[1:]):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    verify_terrain_input(path, bad)
            with self.assertRaises(AssertionError):
                verify_terrain_input(path + '.other', raw)
