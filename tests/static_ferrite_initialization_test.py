"""Initialization specification and source checks only; no GDScript execution.

Python JSON tests cover a shared strict subset, not Godot parser equivalence.
"""
from copy import deepcopy
import json
import math
import unittest

from static_ferrite_region_test import DATA, Oracle, SOURCE
from static_automatic_transitions_test import ROOT, function


def whole(value, minimum, maximum):
    return (type(value) in (int, float) and math.isfinite(value)
            and value == math.floor(value) and minimum <= value <= maximum)


def pair(value):
    return isinstance(value, list) and len(value) == 2


def validate(data):
    if not isinstance(data, dict):
        return 'top-level'
    if data.get('catalog_version') != 'faceted_ferrite_catalog_v1':
        return 'catalog_version'
    variants = data.get('variants')
    if not isinstance(variants, list) or len(variants) != 10:
        return 'variants'
    ids, sizes = set(), set()
    for entry in variants:
        if not isinstance(entry, dict):
            return 'entry'
        identity = entry.get('id')
        if not isinstance(identity, str) or not identity or identity in ids:
            return 'id'
        ids.add(identity)
        if entry.get('size_class') not in ('small', 'medium', 'large'):
            return 'size_class'
        if entry.get('shape_family') not in ('rectangle', 'l_shape', 'stepped', 'organic'):
            return 'shape_family'
        sizes.add(entry['size_class'])
        for field in ('width_cells', 'height_cells'):
            if not whole(entry.get(field), 1, 12):
                return field
        if entry.get('display_scale') != .5:
            return 'display_scale'
        origin = entry.get('logical_origin_source_pixels')
        if not pair(origin) or not all(whole(v, 64, 64) for v in origin):
            return 'logical_origin_source_pixels'
        image = entry.get('image_size_pixels')
        if not pair(image):
            return 'image_size_pixels'
        for value, dimension in zip(image, (entry['width_cells'], entry['height_cells'])):
            expected = dimension*128+128
            if not whole(value, expected, expected):
                return 'image_size_pixels'
        polygon = entry.get('logical_polygon_world_units')
        if not isinstance(polygon, list) or len(polygon) < 3:
            return 'logical_polygon_world_units'
        for vertex in polygon:
            if not pair(vertex) or not all(whole(v, 0, dimension*64) for v,dimension in
                                           zip(vertex,(entry['width_cells'],entry['height_cells']))):
                return 'vertex'
            if any(v % 64 for v in vertex):
                return 'grid'
    return '' if len(sizes) == 3 else 'size coverage'


class InitializationModel:
    def __init__(self, text):
        self.variants, self.by_id, self.error = [], {}, 'not initialized'
        if text is None:
            self.error = 'cannot open'
            return
        if not text.strip():
            self.error = 'empty'
            return
        try:
            data = json.loads(text)
        except (ValueError, TypeError):
            self.error = 'JSON'
            return
        self.error = validate(data)
        if self.error:
            return
        variants = sorted(data['variants'], key=lambda v: v['id'])
        by_id = {v['id']: v for v in variants}
        self.variants, self.by_id = variants, by_id


class FerriteInitializationStaticTest(unittest.TestCase):
    def test_valid_catalog_and_float_numbers_are_preserved(self):
        original = json.dumps(DATA, sort_keys=True)
        model = InitializationModel(original)
        self.assertEqual(model.error, '')
        self.assertEqual(model.by_id, {v['id']:v for v in DATA['variants']})
        self.assertEqual(json.dumps(DATA,sort_keys=True),original)
        # Godot JSON decodes numeric values as floats. Validation must allow them
        # without converting/reordering polygon or registration values.
        floats = json.loads(original, parse_int=float)
        self.assertEqual(validate(floats),'')
        self.assertEqual(floats,DATA)
        before = Oracle(-42).region((-2,3))
        self.assertEqual(before,Oracle(-42).region((-2,3)))

    def test_io_parse_top_level_and_version_failures_do_not_publish(self):
        cases = [None, '', ' \n ', '{invalid', 'null', '[]', 'true', '42', '"text"',
                 '{}', '{"catalog_version":"wrong","variants":[]}']
        for text in cases:
            with self.subTest(text=text):
                model = InitializationModel(text)
                self.assertTrue(model.error)
                self.assertEqual((model.variants,model.by_id),([],{}))

    def test_missing_consumed_fields_and_malformed_late_entry_are_atomic(self):
        fields = ('id','size_class','shape_family','width_cells','height_cells',
                  'display_scale','logical_origin_source_pixels','image_size_pixels',
                  'logical_polygon_world_units')
        for field in fields:
            for bad in ('missing', None, {}, [], True, 'unexpected'):
                if field == 'id' and bad == 'unexpected':
                    continue  # A unique nonempty ID satisfies the consumed schema.
                data = deepcopy(DATA)
                if bad == 'missing':
                    del data['variants'][-1][field]
                else:
                    data['variants'][-1][field] = bad
                with self.subTest(field=field,bad=bad):
                    model = InitializationModel(json.dumps(data))
                    self.assertTrue(model.error)
                    self.assertEqual((model.variants,model.by_id),([],{}))

    def test_numeric_registration_identity_and_size_coverage_rejections(self):
        cases = [('width_cells',0),('height_cells',13),('width_cells',1.5),
                 ('display_scale',1),('logical_origin_source_pixels',[64,32]),
                 ('image_size_pixels',[128,128]),('logical_polygon_world_units',[[0,0],[64,0]]),
                 ('logical_polygon_world_units',[[0,0],[1,64],[64,64]]),
                 ('logical_polygon_world_units',[[0,0],[64,0],[99999,64]])]
        for field,value in cases:
            data = deepcopy(DATA)
            data['variants'][-1][field] = value
            self.assertTrue(validate(data),(field,value))
        data = deepcopy(DATA)
        data['variants'][-1]['id'] = data['variants'][0]['id']
        self.assertTrue(validate(data))
        data = deepcopy(DATA)
        data['variants'][0]['size_class'] = 'medium'
        self.assertTrue(validate(data))
        for value in (float('inf'),float('-inf'),float('nan'),True,'4'):
            self.assertFalse(whole(value,1,12))

    def test_runtime_source_validates_before_publishing_and_reports_specific_errors(self):
        init = function(SOURCE,'_init')
        for expression in ('FileAccess.open(CATALOG_PATH, FileAccess.READ)',
                           'FileAccess.get_open_error()', 'file.get_error()', 'file.close()',
                           'text.strip_edges().is_empty()', 'parser.parse(text) != OK',
                           'parser.get_error_line()', 'parser.get_error_message()',
                           '_catalog_error(parser.data)'):
            self.assertIn(expression,init)
        self.assertLess(init.index('_catalog_error(parser.data)'),init.index('var catalog: Dictionary'))
        self.assertLess(init.index('by_id[variant.id] = variant'),init.index('_variants = variants'))
        self.assertNotIn('_by_id[',init)
        self.assertTrue(init.rstrip().endswith('_initialization_error = ""'))
        self.assertNotIn('assert(',SOURCE)
        self.assertIn('Correct the input/package and restart the session.',SOURCE)
        for method in ('region','query_is_bounded','descriptor_by_id','resource'):
            self.assertIn('if not is_ready():',function(SOURCE,method).split('\n')[1])
        self.assertIn('if not query_is_bounded(area):',function(SOURCE,'query'))

    def test_failure_blocks_dependent_session_and_production_paths(self):
        state = (ROOT/'scenes/world/planet_world_state.gd').read_text()
        for method in ('deploy_machine_instance','machine_status','advance_production'):
            self.assertIn('not is_resource_generation_ready()',function(state,method))
        self.assertIn('_ferrite.initialization_error()',function(state,'resource_generation_error'))
        main = function((ROOT/'scenes/main/main.gd').read_text(),'_ready')
        self.assertLess(main.index('is_resource_generation_ready()'),main.index('$SceneTransitions.initialize()'))
        self.assertIn('get_tree().paused = true\n\t\treturn',main)
        v2 = function((ROOT/'scenes/main/main_v2.gd').read_text(),'_ready')
        self.assertLess(v2.index('super._ready()'),v2.index('is_resource_generation_ready()'))
        self.assertLess(v2.index('is_resource_generation_ready()'),v2.index('transitions.get_current_world()'))


if __name__ == '__main__':
    unittest.main()
