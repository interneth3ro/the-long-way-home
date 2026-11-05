"""PR B source contracts only; no GDScript execution or runtime claims."""
import unittest

from current_preservation import git_blob
from static_automatic_transitions_test import function
from static_extractor_artwork_test import read

BASE = "c5729c00f8d4055ac900e1b6221fe32a3e1ad5e6"


class ExtractorAnimationStaticTest(unittest.TestCase):
    def test_barrel_only_source_pixel_tween(self):
        script = read("construction/extractor_visual.gd")
        self.assertIn("const STROKE_PX := [8.0, 8.0, 6.0, 6.0]", script)
        self.assertIn("const HALF_STROKE_SECONDS := 0.8", script)
        start = function(script, "_start_motion")
        self.assertIn("not _producing or not is_inside_tree() or _turns < 0 or _motion != null", start)
        self.assertEqual(script.count("create_tween()"), 1)
        self.assertIn("create_tween().set_loops()", start)
        self.assertIn("Tween.TRANS_SINE", start)
        self.assertIn("Tween.EASE_IN_OUT", start)
        self.assertIn("var raised: Vector2 = OFFSETS[_turns][1]", start)
        self.assertIn('tween_property($Barrel, "position", raised + Vector2(0, STROKE_PX[_turns])', start)
        self.assertIn('tween_property($Barrel, "position", raised,', start)
        self.assertEqual(script.count("tween_property("), 2)
        self.assertNotRegex(start, r"scale|Body|Foreground|callback|interval|method")
        # Every original calibration, texture and offset declaration stays intact.
        old = git_blob(BASE, "construction/extractor_visual.gd").decode().replace("\r\n", "\n")
        self.assertEqual(script.split("@onready")[0], old.split("@onready")[0])

    def test_idempotence_rotation_and_exit_reset(self):
        script = read("construction/extractor_visual.gd")
        setter = function(script, "set_producing")
        self.assertLess(setter.index("if _producing == producing:"), setter.index("_stop_motion()"))
        configure = function(script, "configure")
        self.assertLess(configure.index("_stop_motion()"), configure.index("_turns = direction"))
        self.assertLess(configure.index(".position = OFFSETS"), configure.index("_start_motion()"))
        stop = function(script, "_stop_motion")
        self.assertLess(stop.index("_motion.kill()"), stop.index("$Barrel.position = OFFSETS[_turns][1]"))
        self.assertIn("_motion = null", stop)
        exit_tree = function(script, "_exit_tree")
        self.assertIn("_producing = false", exit_tree)
        self.assertIn("_stop_motion()", exit_tree)

    def test_authoritative_initial_reentry_and_changed_status_only(self):
        path = "construction/deployed_machine.gd"
        script = read(path)
        entry = function(script, "_enter_tree")
        self.assertEqual(entry.strip(), '''func _enter_tree() -> void:
	# Parent entry precedes child readiness, including retained exterior re-entry.
	_visual.status = _state.machine_status(_state.get_machine(machine_id))''')
        # Narrow guard amendment: all polling, configure, collisions stay byte-identical.
        self.assertEqual(script.replace(entry, ""),
                         git_blob(BASE, path).decode().replace("\r\n", "\n"))
        poll = function(script, "_process")
        self.assertIn("if status == _visual.status:", poll)
        self.assertIn("visual.status = _state.machine_status(machine)", script)

    def test_adapter_ghost_and_reentry_contract(self):
        script = read("construction/machine_visual.gd")
        self.assertIn("if status == value:", script)
        self.assertIn("status = value\n\t\t_refresh_presentation()", script)
        refresh = function(script, "_refresh_presentation")
        self.assertIn("if not is_node_ready() or not is_inside_tree():", refresh)
        self.assertIn("_extractor.set_producing(not is_ghost and status == PlanetWorldState.OperatingStatus.PRODUCING)", refresh)
        self.assertIn("_extractor.set_producing(false)\n\t\t_art_container.hide()", refresh)
        self.assertIn("request_ready()", function(script, "_exit_tree"))
        self.assertNotRegex(script, r"func _(?:physics_)?process|machine_status\(|create_tween|FileAccess|ImageTexture")
        # Other statuses all map to false; no gameplay enums or resources added.
        self.assertEqual(refresh.count("OperatingStatus."), 1)

    def test_scene_and_frozen_import_metadata_preserved(self):
        paths = ["construction/extractor_visual.tscn", "docs/experiments/extractor_static_artwork.json"]
        paths += [f"assets/machines/extractor/extractor_{d}_{role}.png.import"
                  for d in (0, 90, 180, 270) for role in ("body", "barrel", "foreground")]
        for path in paths:
            with self.subTest(path=path):
                self.assertEqual(read(path), git_blob(BASE, path).decode().replace("\r\n", "\n"))
