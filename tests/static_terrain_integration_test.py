"""Production artwork identity and adversarial preservation checks; no Godot."""
import hashlib
import json
from pathlib import Path
import re
import unittest
from unittest.mock import patch

import terrain_integration_preservation as guard
from static_terrain_resolver_test import inventory


class TerrainIntegrationTest(unittest.TestCase):
    def test_current_lookup_path_contract_accepts_authorized_change(self):
        raw = guard.read(guard.LOOKUP)
        # No reference to historical script bytes: an explicitly selected future
        # resource path and an unrelated source comment satisfy this contract.
        chosen = 'res://assets/environment/exterior/future_ground/terrain.tres'
        changed = raw.replace(('res://' + guard.ACTIVE + 'terrain.tres').encode(), chosen.encode())
        guard.verify_lookup(changed + b'\n# unrelated implementation change\n', chosen)
        with self.assertRaisesRegex(AssertionError, 'TileSet path'):
            guard.verify_lookup(changed)

    def test_unrelated_feature_files_are_outside_terrain_integrity(self):
        reader = guard.read
        requested = []
        additions = {
            'scenes/world/future_feature.gd': b'extends Node\n',
            'assets/future_feature.png': b'new art',
            'tests/static_future_feature_test.py': b'# new test',
            'docs/FUTURE_FEATURE.md': b'# new documentation',
        }
        def working(path):
            requested.append(path)
            return additions[path] if path in additions else reader(path)
        with patch.object(guard, 'read', side_effect=working):
            guard.verify_all()
        self.assertFalse(set(requested) & additions.keys())


    def test_exact_active_artwork_and_preserved_originals(self):
        guard.verify_all()
        for name, expected in guard.ATLAS_SHA256.items():
            self.assertEqual(hashlib.sha256(guard.read(guard.ACTIVE + name)).hexdigest(), expected)
            self.assertEqual(guard.read(guard.ACTIVE + name), guard.read(guard.OFFLINE + name))


    def test_exact_tileset_structure_and_inventory(self):
        before = guard.lf(guard.read(guard.OLD + 'baked_terrain.tres')).decode()
        after = guard.lf(guard.read(guard.ACTIVE + 'terrain.tres')).decode()
        self.assertEqual(after, guard.expected_tileset().decode())
        mapping = json.loads(guard.read(guard.OLD + 'mapping.json'))
        self.assertEqual(inventory(before, mapping), inventory(after, mapping))
        self.assertEqual(len(mapping['baseline']), 94)
        self.assertEqual(len({tuple(e['signature']) for e in mapping['baseline']}), 94)
        self.assertEqual(len(mapping['interiors']), 4)
        self.assertEqual(len(inventory(after, mapping)), 98)
        peers = re.findall(r'^.*terrains_peering_bit/.*$', after, re.M)
        self.assertEqual(peers, re.findall(r'^.*terrains_peering_bit/.*$', before, re.M))
        self.assertEqual(len(peers), 98 * 8)
        self.assertNotIn('uid=', after)

    def test_import_paths_are_outside_ignored_evidence(self):
        tiles = guard.read(guard.ACTIVE + 'terrain.tres').decode()
        for relative in (guard.ACTIVE + 'terrain.tres', *re.findall(r'path="res://([^"]+)"', tiles)):
            path = guard.ROOT/relative
            self.assertTrue(path.is_file(), relative)
            for parent in path.parents:
                self.assertFalse((parent/'.gdignore').exists(), relative)
                if parent == guard.ROOT:
                    break
        self.assertTrue((guard.ROOT/guard.OFFLINE/'.gdignore').is_file())


    def test_changed_peering_metadata_atlas_coordinates_and_texture_paths_are_rejected(self):
        path = guard.ACTIVE + 'terrain.tres'
        raw = guard.read(path)
        mutations = (raw+b'\n', raw.replace(b'top_side = 1', b'top_side = 0', 1),
                     raw.replace(b'0:0/0 = 0', b'99:99/0 = 0', 1),
                     raw.replace(b'Vector2i(128, 128)', b'Vector2i(64, 64)', 1),
                     raw.replace(b'ground_refined_v1', b'wrong_location', 1),
                     raw.replace(b'format=3', b'format=3 uid="uid://duplicate"', 1))
        for bad in mutations:
            self.assertNotEqual(bad, raw)
            with self.assertRaises(AssertionError):
                guard.verify_resource(path, bad)

    def test_altered_atlas_bytes_and_missing_inputs_are_rejected(self):
        for name in guard.ATLAS_SHA256:
            path = guard.ACTIVE + name
            raw = guard.read(path)
            for bad in (raw+b'X', raw[1:], bytes([raw[0] ^ 1])+raw[1:]):
                with self.assertRaises(AssertionError):
                    guard.verify_resource(path, bad)
        reader = Path.read_bytes
        for target in (guard.LOOKUP, guard.ACTIVE + 'terrain.tres',
                       *(guard.ACTIVE + n for n in guard.ATLAS_SHA256)):
            def missing(instance):
                if instance == guard.ROOT/target:
                    raise FileNotFoundError(target)
                return reader(instance)
            with patch.object(Path, 'read_bytes', missing), self.assertRaises(AssertionError):
                guard.verify_all()


if __name__ == '__main__':
    unittest.main()
