"""PR B source contracts only; no GDScript execution or runtime claims."""
import unittest

from current_preservation import git_blob
from static_automatic_transitions_test import function
from static_extractor_artwork_test import read
from static_fabricator_animation_test import without_presentation_identity

BASE = "c5729c00f8d4055ac900e1b6221fe32a3e1ad5e6"
# Owner-run Godot 4.7.2 canonicalized text while preserving numeric identity.
# Only these five exact replacements are admitted; every other byte stays pinned.
CANONICAL_TEXTURE_UIDS = {
    "extractor_0_barrel.png.import": ("b9553028581b", "ca553028581b"),
    "extractor_90_body.png.import": ("bb5dbe9b0a32", "bb5dbfab0a32"),
    "extractor_90_barrel.png.import": ("b073c49412a2", "b073c5a412a2"),
    "extractor_180_body.png.import": ("bb4e10e3493f", "bb4e10e35a3f"),
    "extractor_180_foreground.png.import": ("bfd19198db79", "bfd2a2a8db8a"),
}


class ExtractorAnimationStaticTest(unittest.TestCase):
    def test_property_setters_have_declaration_colons(self):
        # Narrow syntax tripwire: an indented setter needs a property block.
        # This is not a replacement for authorized Godot parsing.
        for path in ("construction/machine_visual.gd", "construction/extractor_visual.gd"):
            lines = read(path).splitlines()
            for index, line in enumerate(lines):
                if line.startswith("\tset("):
                    with self.subTest(path=path, line=index + 1):
                        self.assertTrue(lines[index - 1].rstrip().endswith(":"))

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
	if _state == null or _visual == null:
		return
	# Parent entry precedes child readiness, including retained exterior re-entry.
	_visual.status = _state.machine_status(_state.get_machine(machine_id))''')
        # Narrow guard amendment: all polling, configure, collisions stay byte-identical.
        self.assertEqual(without_presentation_identity(script).replace(entry, ""),
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
        # The new Smelter branch must not alter the existing Extractor lifecycle.
        original_refresh = function(git_blob("65564d5d95502fcc0368a2b5396d1855311c5806",
                                            "construction/machine_visual.gd").decode().replace("\r\n", "\n"),
                                    "_refresh_presentation")
        current_extractor = refresh.split('if definition != null and definition.item_id == &"extractor":', 1)[1].split(
            'if definition != null and definition.item_id == &"smelter":', 1)[0].rstrip()
        original_extractor = original_refresh.split("if illustrated:", 1)[1].split("\tqueue_redraw()", 1)[0].rstrip()
        self.assertEqual(current_extractor, original_extractor)
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
                current = read(path)
                pair = CANONICAL_TEXTURE_UIDS.get(path.rsplit("/", 1)[-1])
                if pair is not None:
                    old, canonical = pair
                    # ResourceUID text_to_id uses base 34, a..z -> 0..25,
                    # 0..9 -> 25..34; id_to_text emits a..y and 0..8.
                    # https://github.com/godotengine/godot/blob/4.7.2-stable/core/io/resource_uid.cpp
                    def identity(text):
                        value = 0
                        for c in text:
                            value = value * 34 + (ord(c) - ord("a") if c.isalpha() else int(c) + 25)
                        return value & 0x7fffffffffffffff
                    self.assertEqual(identity(old), identity(canonical))
                    self.assertNotRegex(canonical, r"[z9]")
                    old_line, new_line = f'uid="uid://{old}"', f'uid="uid://{canonical}"'
                    self.assertEqual(current.count(new_line), 1)
                    current = current.replace(new_line, old_line)
                self.assertEqual(current, git_blob(BASE, path).decode().replace("\r\n", "\n"))
