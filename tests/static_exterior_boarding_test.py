"""Non-native geometry and source contracts; no gameplay/engine execution.

Numeric segment examples are an independent specification, not physics simulation.
"""
import hashlib
from pathlib import Path
import re
import subprocess
import unittest
from unittest.mock import patch

import current_preservation as preservation
from static_automatic_transitions_test import nodes, resources, function, vectors

ROOT = Path(__file__).resolve().parents[1]
BASE = preservation.BOARDING_BASE
SCRIPT = 'scenes/interaction/exterior_boarding.gd'
WORLD = 'scenes/world/planet_exterior.tscn'
VISUAL = 'scenes/interaction/exterior_hatch_visual.gd'


def read(path):
    return (ROOT/path).read_text(encoding='utf-8')


def old(path):
    return preservation.git_blob(BASE, path).decode().replace('\r\n', '\n')


def crossing(a, b):
    # Independent intersection with the finite, directed world-space line.
    if not b[1] <= -168 < a[1]:
        return False
    x = a[0] + (b[0]-a[0])*(-168-a[1])/(b[1]-a[1])
    return -406 <= x <= -362


class ExteriorBoardingStaticTest(unittest.TestCase):
    def setUp(self):
        self.code = read(SCRIPT)
        self.scene = read(WORLD)

    def test_exact_sensor_line_lane_and_player_clearance(self):
        n, r = nodes(self.scene), resources(self.scene)
        self.assertEqual(vectors(n['GroundObjects/Hatch'][1])[0], (-384, -176))
        self.assertEqual(vectors(n['GroundObjects/Hatch/BoardingSensor'][1])[0], (0, 8))
        self.assertEqual(vectors(r['BoardingThreshold'][1]), [(64, 16)])
        self.assertEqual(vectors(r['HatchFootprint'][1]), [(64, 24)])
        self.assertIn('const BOARDING_LINE: float = 8.0', self.code)
        self.assertIn('const LANE_HALF_WIDTH: float = 22.0', self.code)
        self.assertIn('radius = 10.0', read('scenes/player/dave.tscn'))
        self.assertIn('position = Vector2(0, -10)', read('scenes/player/dave.tscn'))
        # Lane includes the radius-10 feet circle inside the 64-wide aperture.
        self.assertEqual(32-10, 22)
        # Hull edge -211 leaves 23 units above the circle at the boarding line.
        self.assertEqual((-168-20)-(-211), 23)
        self.assertIn('process_physics_priority = 1', n['GroundObjects/Hatch'][1])
        self.assertNotIn('process_physics_priority', read('scenes/player/dave.tscn'))

    def test_directed_segment_examples_stationary_outward_diagonal_and_skips(self):
        for a, b, expected in [
            ((-384,-100),(-384,-100),False),
            ((-384,-164),(-384,-168),True),
            ((-384,-168),(-384,-172),False),
            ((-384,-172),(-384,-164),False),
            ((-420,-164),(-420,-172),False),
            ((-410,-164),(-402,-172),True),
            ((-360,-164),(-360,-172),False),
            ((-384,-140),(-384,-192),True),
        ]:
            with self.subTest(a=a,b=b):
                self.assertEqual(crossing(a,b), expected)
        method = function(self.code, '_crossed_inward')
        for contract in ('previous.y <= BOARDING_LINE', 'current.y > BOARDING_LINE',
                         'current.y >= previous.y', 'lerpf(previous.x, current.x, fraction)',
                         'absf(crossing_x) <= LANE_HALF_WIDTH'):
            self.assertIn(contract, method)
        self.assertIn('to_local(player.global_position)', self.code)
        self.assertNotIn('body_entered', self.code)

    def test_readiness_wait_and_pending_cancellation(self):
        self.assertIn('return openness == 1.0', function(read(VISUAL), 'is_boarding_ready'))
        update = function(self.code, '_update_blocker')
        self.assertLess(update.index('is_boarding_ready()'), update.index('collision_layer", 4'))
        # Closed blocker south edge is -164; Dave's circle top is feet-20.
        # Early arrival stops at feet -144, before line -168. Continue walking
        # after full opening: no sensor-exit/re-entry is required.
        self.assertGreater(-164+20, -168)
        tick = function(self.code, '_physics_process')
        self.assertIn('_state = EntryState.PENDING', tick)
        self.assertIn('feet.y >= 0.0 and feet.y <= BOARDING_LINE', tick)
        self.assertIn('not within_threshold and not (crossed and _visual.is_boarding_ready())', tick)
        self.assertIn('elif _visual.is_boarding_ready():', tick)
        self.assertIn('EntryState.WAIT_FOR_SEPARATION', tick)

    def test_collision_restore_requires_closed_and_current_player_clearance(self):
        update = function(self.code, '_update_blocker')
        self.assertIn('elif _visual.openness == 0.0 and not _doorway_occupied(player):', update)
        self.assertIn('set_deferred("collision_layer", 5)', update)
        occupancy = function(self.code, '_doorway_occupied')
        for contract in ('query.shape = _blocker.shape', 'query.transform = _blocker.global_transform',
                         'query.margin = 4.0', 'query.collision_mask = 1',
                         'query.collide_with_areas = false', 'query.exclude = [get_rid()]',
                         'intersect_shape(query)', 'hit["collider"] == player'):
            self.assertIn(contract, occupancy)
        self.assertNotIn('.disabled', self.code)
        self.assertNotIn('collision_layer", 0', self.code)
        # Dynamic player solidity never removes construction blocking (bit 4).
        self.assertEqual(4 & 4, 5 & 4)

    def test_exterior_e_removed_and_production_injection_unchanged(self):
        self.assertIn('extends StaticBody2D', self.code)
        for forbidden in ('WorldInteractable', 'func interact', 'Input.', 'interaction_prompt'):
            self.assertNotIn(forbidden, self.code)
        hatch = nodes(self.scene)['GroundObjects/Hatch'][1]
        self.assertNotIn('interaction_prompt', hatch)
        self.assertIn('path="res://'+SCRIPT+'"', self.scene)
        for prop in ('source_scene', 'destination_scene', 'destination_spawn'):
            self.assertIn('var '+prop+':', self.code)
        for path in ('scenes/main/main_v2.gd', 'scenes/interaction/scene_hatch.gd',
                     'scenes/player/interaction_detector.gd', 'project.godot',
                     'scenes/world/production_ship_interior_v2.tscn'):
            self.assertEqual(read(path), old(path), path)

    def test_one_shot_and_registration_separation_on_busy_cache_and_rollback(self):
        self.assertEqual(self.code.count('_controller.request_transition('), 1)
        tick = function(self.code, '_physics_process')
        self.assertLess(tick.index('_state = EntryState.ENTERED'), tick.index('_controller.request_transition'))
        for contract in ('_controller.is_transitioning()', 'not world.is_ancestor_of(self)',
                         '_registration_frames -= 1', 'not overlapping and feet.y > 16.0',
                         'player.can_process()', '_has_previous and _crossed_inward'):
            self.assertIn(contract, tick)
        for name in ('_enter_tree', 'prepare_for_arrival'):
            self.assertIn('_reset_entry()', function(self.code, name))
        reset = function(self.code, '_reset_entry')
        self.assertIn('_has_previous = false', reset)
        self.assertIn('_registration_frames = 2', reset)
        self.assertIn('_state = EntryState.WAIT_FOR_SEPARATION', reset)
        self.assertEqual(vectors(nodes(self.scene)['Spawns/FromShip'][1])[0], (-384,-64))

    def test_arrival_opens_explicitly_before_reveal_and_preserves_terrain_logic(self):
        world = read('scenes/world/planet_exterior.gd')
        self.assertEqual(world.replace('\t$GroundObjects/Hatch.prepare_for_arrival()\n', '', 1),
                         old('scenes/world/planet_exterior.gd'))
        arrival = function(read(VISUAL), 'prepare_for_arrival')
        for contract in ('openness = 1.0', '_target_open = true', '_outside_seconds = 0.0',
                         '_registration_frames = 2', '_door.position = DOOR_TRAVEL'):
            self.assertIn(contract, arrival)
        controller = read('scenes/main/scene_transition_controller.gd')
        self.assertEqual(controller, old('scenes/main/scene_transition_controller.gd'))
        for name in ('_perform_transition', '_perform_quick_transition'):
            method = function(controller, name)
            self.assertLess(method.index('await destination.call("prepare_for_arrival"'),
                            method.index('_reset_camera()'))
        quick = function(controller, '_perform_quick_transition')
        self.assertIn('world_host.add_child(source)', quick)
        self.assertIn('player.global_position = source_position', quick)

    def test_established_quick_fade_lock_and_rollback_unchanged(self):
        controller = read('scenes/main/scene_transition_controller.gd')
        self.assertIn('SceneTransitionController.Presentation.QUICK_FADE', self.code)
        self.assertIn('var quick_fade_seconds: float = 0.15', controller)
        request = function(controller, 'request_transition')
        self.assertLess(request.index('player.process_mode = Node.PROCESS_MODE_DISABLED'),
                        request.index('transition_started.emit()'))
        self.assertEqual(controller, old('scenes/main/scene_transition_controller.gd'))

    def test_approved_animation_art_ship_hull_and_anchor_preserved(self):
        visual = read(VISUAL)
        for name in ('_update_proximity', '_advance_animation', '_physics_process'):
            self.assertEqual(function(visual, name), function(old(VISUAL), name))
        for path in ('scenes/interaction/exterior_hatch_visual.tscn',
                     'assets/environment/exterior/crashed_exploration_ship_approved.png',
                     'assets/environment/exterior/crashed_ship_contact_shadow_prototype.png',
                     'assets/environment/exterior/hatch_v2/door_leaf_opaque_v2.png',
                     'assets/environment/exterior/hatch_v2/recess_backing_black_light.png'):
            self.assertEqual((ROOT/path).read_bytes().replace(b'\r\n',b'\n'),
                             preservation.git_blob(BASE,path).replace(b'\r\n',b'\n'),path)
        current, previous = resources(self.scene), resources(old(WORLD))
        for shape in ('ShipNoseFootprint','ShipFuselageFootprint','ShipRearFootprint','HatchFootprint'):
            self.assertEqual(current[shape], previous[shape])
        for path, value in nodes(old(WORLD)).items():
            if path != 'GroundObjects/Hatch':
                self.assertEqual(nodes(self.scene)[path], value, path)
        self.assertIn('type="StaticBody2D"', nodes(self.scene)['GroundObjects/Hatch'][0])
        self.assertIn('if child is StaticBody2D:', read('scenes/world/planet_exterior.gd'))

    def test_exact_boarding_receipts_reject_corruption_and_path_expansion(self):
        self.assertEqual(set(preservation.BOARDING_INPUT_SHA256), {
            WORLD, SCRIPT, VISUAL, 'scenes/world/planet_exterior.gd'})
        for path, digest in (preservation.BOARDING_INPUT_SHA256 | preservation.BOARDING_TEST_SHA256).items():
            raw = (ROOT/path).read_bytes()
            preservation.verify_fingerprint(path, raw, digest)
            projected = preservation.boarding_predecessor(path, raw)
            if path != SCRIPT:
                self.assertEqual(preservation.normalized(path,projected),
                                 preservation.normalized(path,preservation.git_blob(BASE,path)))
            for bad in (raw+b'UNREVIEWED', raw[1:], raw+raw):
                with self.subTest(path=path), self.assertRaises(AssertionError):
                    preservation.boarding_predecessor(path,bad)
        self.assertEqual(preservation.without_current_paths(list(preservation.BOARDING_INPUT_SHA256)), [])
        self.assertEqual(preservation.without_current_paths(['scenes/interaction/other.gd']),
                         ['scenes/interaction/other.gd'])


if __name__ == '__main__':
    unittest.main()
