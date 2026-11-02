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
    def test_forward_helper_identity_is_independently_pinned(self):
        self.assertEqual(guard.digest(guard.lf(guard.read("tests/terrain_integration_preservation.py"))),
                         "ee873015e0039d2dd0ade930da60d14e2cbff34d2d42849a1fc497d2bf751a50")

    def test_exact_active_artwork_and_preserved_originals(self):
        guard.verify_all()
        for name, expected in guard.ATLAS_SHA256.items():
            self.assertEqual(hashlib.sha256(guard.read(guard.ACTIVE + name)).hexdigest(), expected)
            self.assertEqual(guard.read(guard.ACTIVE + name), guard.original(guard.OFFLINE + name))

    def test_lookup_has_only_the_authorized_path_change(self):
        self.assertEqual(guard.lf(guard.read(guard.LOOKUP)), guard.expected_lookup())
        self.assertEqual(guard.predecessor(guard.LOOKUP, guard.read(guard.LOOKUP)), guard.original(guard.LOOKUP))
        self.assertEqual(guard.predecessor(guard.LOOKUP, guard.original(guard.LOOKUP)), guard.original(guard.LOOKUP))
        self.assertIn(('res://' + guard.ACTIVE + 'terrain.tres').encode(), guard.read(guard.LOOKUP))

    def test_exact_tileset_structure_and_inventory(self):
        before = guard.original(guard.OLD + 'baked_terrain.tres').decode()
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

    def test_unauthorized_lookup_changes_and_wrong_paths_are_rejected(self):
        raw = guard.read(guard.LOOKUP)
        for bad in (raw+b'\n# unauthorized', raw[1:], raw.replace(b'func initialize()', b'func changed()'),
                    raw.replace(b'ground_refined_v1', b'ground_refined_wrong')):
            with self.subTest(bad=bad[:30]), self.assertRaises(AssertionError):
                guard.predecessor(guard.LOOKUP, bad)
        with self.assertRaises(AssertionError):
            guard.verify_resource(guard.LOOKUP + '.other', raw)

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
                       *(guard.ACTIVE + n for n in guard.ATLAS_SHA256), *guard.AMENDMENTS):
            def missing(instance):
                if instance == guard.ROOT/target:
                    raise FileNotFoundError(target)
                return reader(instance)
            with patch.object(Path, 'read_bytes', missing), self.assertRaises(AssertionError):
                guard.without_integration_changes([])

    def test_complete_amendments_are_pinned_and_unrelated_paths_are_not_hidden(self):
        for path in guard.AMENDMENTS:
            raw = guard.read(path)
            self.assertEqual(guard.predecessor(path, raw), guard.original(path))
            for bad in (raw+b'X', raw[1:]):
                with self.assertRaises(AssertionError):
                    guard.predecessor(path, bad)
        self.assertEqual(guard.without_integration_changes(['scenes/world/planet_generator.gd', 'tests/unknown.py']),
                         ['scenes/world/planet_generator.gd', 'tests/unknown.py'])
        # Every sibling is checked before filtering, even when not requested.
        reader = guard.read
        for target in guard.AMENDMENTS:
            def altered(path):
                raw = reader(path)
                return raw+b'X' if path == target else raw
            with patch.object(guard, 'read', side_effect=altered), self.assertRaises(AssertionError):
                guard.without_integration_changes([])

    def test_procedural_shading_scene_and_resolver_sources_are_unchanged(self):
        for name in ('terrain_resolver.gd', 'illustrated_terrain_presenter.gd',
                     'planet_exterior.gd', 'planet_exterior.tscn', 'terrain_chunk.gd',
                     'planet_generator.gd', 'illustrated_terrain_tint.gdshader', 'world_coordinates.gd'):
            path = 'scenes/world/' + name
            self.assertEqual(guard.lf(guard.read(path)), guard.original(path), path)


if __name__ == '__main__':
    unittest.main()
