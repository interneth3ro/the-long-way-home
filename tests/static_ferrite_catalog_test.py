"""Offline catalog geometry/PNG contracts; no Godot or gameplay execution."""
import importlib.util
import json
from pathlib import Path
import struct
import unittest
import zlib


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location('ferrite_catalog', ROOT/'tools/ferrite-catalog.py')
catalog = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(catalog)


def png(path):
    raw = path.read_bytes()
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    offset, chunks = 8, []
    while offset < len(raw):
        size = struct.unpack_from('>I', raw, offset)[0]
        kind = raw[offset+4:offset+8]
        body = raw[offset+8:offset+8+size]
        crc = struct.unpack_from('>I', raw, offset+8+size)[0]
        assert zlib.crc32(kind+body) == crc, (path, kind)
        chunks.append((kind, body))
        offset += size+12
    assert offset == len(raw) and chunks[0][0] == b'IHDR' and chunks[-1] == (b'IEND', b'')
    width, height, depth, color, compression, filtering, interlace = struct.unpack('>IIBBBBB', chunks[0][1])
    assert (depth, color, compression, filtering, interlace) == (8, 6, 0, 0, 0)
    scanlines = zlib.decompress(b''.join(body for kind, body in chunks if kind == b'IDAT'))
    assert len(scanlines) == height*(1+width*4)
    return width, height


class FerriteCatalogStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.data = json.loads((ROOT/catalog.ASSET/'catalog.json').read_text(encoding='utf-8'))

    def test_derived_catalog_and_explicit_ids(self):
        self.assertEqual(self.data, catalog.compile_catalog())
        identities = [v['id'] for v in self.data['variants']]
        self.assertEqual(len(identities), len(set(identities)))
        self.assertEqual(len(identities), 10)
        targets = self.data['future_selection_targets']
        self.assertEqual(targets['size_class'], {'small': .1, 'medium': .5, 'large': .4})
        self.assertEqual(targets['shape_family'], {'rectangle': .2, 'l_shape': .2, 'stepped': .25, 'organic': .35})

    def test_topology_rejects_invalid_and_impractical_masks(self):
        invalid = [[], [''], ['##', '#'], ['##', '#x'], ['##..##', '##..##'],
                   ['####', '#..#', '#..#', '####'], ['##..', '##..', '..##', '..##'],
                   ['##...', '#####', '...##'], ['####', '###.', '####', '####']]
        for rows in invalid:
            with self.subTest(rows=rows), self.assertRaises(ValueError):
                catalog.geometry(rows)

    def test_polygon_area_orientation_and_extractor_room(self):
        for item in self.data['variants']:
            rows = (ROOT/item['mask_path']).read_text().splitlines()
            cells, polygon = catalog.geometry(rows)
            area2 = sum(a[0]*b[1]-b[0]*a[1] for a, b in zip(polygon, polygon[1:]+polygon[:1]))
            self.assertEqual(area2, 2*len(cells)*64*64, item['id'])
            self.assertTrue(all(value % 64 == 0 for point in polygon for value in point))
            # Every occupied terrain cell is large enough for a 64x64 Extractor.
            # Exercise exact full-cell corners inset from polygon boundaries.
            for x, y in cells:
                for dx, dy in ((.01,.01), (63.99,.01), (.01,63.99), (63.99,63.99)):
                    self.assertTrue(catalog.contains((x*64+dx, y*64+dy), polygon))

    def test_negative_translation_and_reconstruction_by_id(self):
        by_id = {v['id']: v for v in reversed(self.data['variants'])}
        for item in self.data['variants']:
            self.assertEqual(by_id[item['id']], item)
            rows = (ROOT/item['mask_path']).read_text().splitlines()
            polygon = [[x-2048, y-4096] for x, y in item['logical_polygon_world_units']]
            for y in range(-1, item['height_cells']+1):
                for x in range(-1, item['width_cells']+1):
                    expected = 0 <= y < len(rows) and 0 <= x < len(rows[0]) and rows[y][x] == '#'
                    self.assertEqual(catalog.contains(((x+.5)*64-2048, (y+.5)*64-4096), polygon), expected)

    def test_candidate_png_integrity_and_registration(self):
        for item in self.data['variants']:
            path = ROOT/item['png_path']
            self.assertEqual(png(path), tuple(item['image_size_pixels']))
            self.assertEqual(item['logical_origin_source_pixels'], [64,64])
            self.assertEqual(item['display_scale'], .5)
            self.assertEqual((item['image_size_pixels'][0]-128)*.5, item['width_cells']*64)
            self.assertEqual((item['image_size_pixels'][1]-128)*.5, item['height_cells']*64)
            self.assertEqual(64*.5, 32)  # canvas origin = world logical origin - (32,32)
            for parent in path.parents:
                self.assertFalse((parent/'.gdignore').exists())
                if parent == ROOT:
                    break

    def test_review_package_and_no_runtime_dependency(self):
        review = ROOT/'assets/experiments/ferrite_catalog_v1'
        self.assertTrue((review/'.gdignore').is_file())
        self.assertEqual(png(review/'contact_sheet.png'), (1740,2400))
        for identity in ('small_table', 'medium_elbow', 'large_sprawl'):
            entry = next(v for v in self.data['variants'] if v['id'] == 'ferrite_v1_'+identity)
            self.assertEqual(png(review/(entry['id']+'_overlay.png')), tuple(entry['image_size_pixels']))
        for folder in ('scenes', 'construction', 'inventory'):
            for path in (ROOT/folder).rglob('*'):
                if path.suffix in ('.gd', '.tscn', '.tres'):
                    if path == ROOT/'scenes/world/ferrite_region_generator.gd':
                        source = path.read_text(encoding='utf-8')
                        self.assertIn('catalog_v1/catalog.json', source)
                        for forbidden in ('Texture2D', 'Sprite2D', 'Image.', 'load('):
                            self.assertNotIn(forbidden, source.replace('preload(', ''))
                        continue  # Catalog metadata validation adds no image I/O.
                    self.assertNotIn('ferrite/catalog_v1', path.read_text(encoding='utf-8'))


if __name__ == '__main__':
    unittest.main()
