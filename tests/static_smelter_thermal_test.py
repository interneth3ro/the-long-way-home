from initial_exterior_preservation import without_initial_preparation
"""Source contracts and offline envelope math only; never executes GDScript/Godot."""
import math
import re
import unittest

from current_preservation import ROOT, git_blob, normalized
from smelter_artwork_offline import BODY_PATHS, verify_active_artifacts
from static_automatic_transitions_test import function
from static_fabricator_animation_test import without_presentation_identity

BASE = "ca18cfa4c9f16ab934968aed4fa764f9c1e2b58d"


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def eased(start, end, fraction):
    """Independent sine in/out envelope, used to examine approved numeric bounds."""
    return start + (end - start) * (1 - math.cos(math.pi * fraction)) / 2


class SmelterThermalStaticTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.script = read("construction/smelter_visual.gd")
        cls.constants = {name: float(value) for name, value in re.findall(
            r"^const (HEAT_LOW|HEAT_HIGH|WARMUP_SECONDS|HALF_PULSE_SECONDS|COOLDOWN_SECONDS) := ([\d.]+)$",
            cls.script, re.M)}

    def test_approved_constants_and_full_period(self):
        self.assertEqual(self.constants, dict(HEAT_LOW=.82, HEAT_HIGH=1.,
                         WARMUP_SECONDS=.5, HALF_PULSE_SECONDS=1.8, COOLDOWN_SECONDS=1.))
        self.assertEqual(2 * self.constants["HALF_PULSE_SECONDS"], 3.6)
        pulse = function(self.script, "_start_pulse")
        self.assertEqual(pulse.count("HALF_PULSE_SECONDS)"), 2)
        self.assertIn("HEAT_LOW if from_high else HEAT_HIGH", pulse)
        self.assertIn("HEAT_HIGH if from_high else HEAT_LOW", pulse)
        self.assertIn("create_tween().set_loops()", pulse)

    def test_state_mapping_and_immediate_inactive(self):
        setter = function(self.script, "set_operating_status")
        self.assertIn("match status:", setter)
        self.assertIn("PlanetWorldState.OperatingStatus.PRODUCING:", setter)
        self.assertIn("PlanetWorldState.OperatingStatus.INPUT_EMPTY, PlanetWorldState.OperatingStatus.OUTPUT_FULL:", setter)
        self.assertIn("_transition_to(0.0, COOLDOWN_SECONDS, _finish_cooldown.bind(_generation))", setter)
        self.assertTrue(setter.rstrip().endswith("_:\n\t\t\t_set_heat(0.0)"))
        self.assertIn("if $Illumination.self_modulate.a > 0.0:", setter)

    def test_current_opacity_retarget_and_bounded_warmup(self):
        setter = function(self.script, "set_operating_status")
        self.assertIn("var heat: float = $Illumination.self_modulate.a", setter)
        self.assertIn("WARMUP_SECONDS * (HEAT_LOW - heat) / HEAT_LOW", setter)
        self.assertIn("minf(WARMUP_SECONDS, HALF_PULSE_SECONDS * (HEAT_HIGH - heat) / (HEAT_HIGH - HEAT_LOW))", setter)
        self.assertIn("_start_pulse.bind(_generation, true)", setter)
        transition = function(self.script, "_transition_to")
        self.assertIn('tween_property($Illumination, "self_modulate:a", target, seconds)', transition)
        self.assertNotIn(".from(", transition)
        ordinary = setter.split("match status:", 1)[1]
        producing = ordinary.split("PlanetWorldState.OperatingStatus.INPUT_EMPTY", 1)[0]
        self.assertNotIn("_set_heat(0.0)", producing)

    def test_offline_cold_and_hot_restart_continuity(self):
        low, high = self.constants["HEAT_LOW"], self.constants["HEAT_HIGH"]
        for initial in (0., .001, .4, .81, .82, .83, .95, 1.):
            target = low if initial < low else high
            seconds = (.5 * (low - initial) / low if initial < low
                       else min(.5, 1.8 * (high - initial) / (high - low)))
            self.assertGreaterEqual(seconds, 0.)
            self.assertLessEqual(seconds, .5)
            self.assertEqual(eased(initial, target, 0), initial)
            self.assertAlmostEqual(eased(initial, target, 1), target)
            self.assertGreaterEqual(eased(initial, target, .01), initial)
        self.assertEqual(.5 * (low - 0) / low, .5)

    def test_offline_rapid_reversal_and_pulse_bounds(self):
        low, high = self.constants["HEAT_LOW"], self.constants["HEAT_HIGH"]
        # Interrupt at both early/late cooldown points, then return to producing.
        # Each new envelope starts at the interrupted value, including above low.
        for producing in (low, .91, high):
            for fraction in (.01, .1, .5, .9, .99):
                current = eased(producing, 0, fraction)
                target = low if current < low else high
                self.assertEqual(eased(current, target, 0), current)
                for step in range(101):
                    self.assertTrue(0 <= eased(current, target, step / 100) <= 1)
        for start, end in ((low, high), (high, low)):
            samples = [eased(start, end, i / 1000) for i in range(1001)]
            self.assertGreaterEqual(min(samples), low)
            self.assertLessEqual(max(samples), high)
            self.assertAlmostEqual(samples[-1], end)
        # Both segment joins and the repeating boundary have equal endpoint values.
        self.assertEqual(eased(low, high, 1), eased(high, low, 0))
        self.assertEqual(eased(high, low, 1), eased(low, high, 0))

    def test_single_owner_cancel_before_transition_and_idempotence(self):
        setter = function(self.script, "set_operating_status")
        self.assertLess(setter.index("if _initialized and _status == status:"), setter.index("_cancel_thermal()"))
        self.assertLess(setter.index("_cancel_thermal()"), setter.index("match status:"))
        cancel = function(self.script, "_cancel_thermal")
        self.assertLess(cancel.index("_generation += 1"), cancel.index("_thermal.kill()"))
        self.assertIn("_thermal = null", cancel)
        self.assertEqual(self.script.count("create_tween()"), 2)
        self.assertEqual(self.script.count("var _thermal: Tween"), 1)
        transition = function(self.script, "_transition_to")
        self.assertIn("_thermal.finished.connect(completion, CONNECT_ONE_SHOT)", transition)
        self.assertNotIn("tween_callback", transition)
        for method in ("_start_pulse", "_finish_cooldown"):
            callback = function(self.script, method)
            self.assertIn("generation != _generation", callback)
            self.assertIn("not _initialized or not is_inside_tree()", callback)
            self.assertIn("_status", callback)
            self.assertLess(callback.index("generation != _generation"), callback.index("return"))

    def test_completion_reset_and_smooth_alpha_only_tweens(self):
        finish = function(self.script, "_finish_cooldown")
        self.assertIn("_thermal = null\n\t_set_heat(0.0)", finish)
        self.assertIn("OperatingStatus.INPUT_EMPTY, PlanetWorldState.OperatingStatus.OUTPUT_FULL", finish)
        heat = function(self.script, "_set_heat")
        self.assertIn("clampf(heat, 0.0, 1.0)", heat)
        self.assertIn("$Illumination.visible = heat > 0.0", heat)
        self.assertEqual(self.script.count('"self_modulate:a"'), 3)
        self.assertEqual(self.script.count("set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)"), 2)
        self.assertNotRegex(self.script, r"func _(?:physics_)?process|machine_status\(|get_machine\(|FileAccess|ImageTexture|randf|AnimationPlayer")

    def test_ghost_disable_switching_and_exit(self):
        adapter = function(read("construction/machine_visual.gd"), "_refresh_presentation")
        self.assertIn("_smelter.set_operating_status(status, not is_ghost)", adapter)
        self.assertIn("_smelter.reset_thermal()\n\t\t_smelter_art_container.hide()", adapter)
        setter = function(self.script, "set_operating_status")
        self.assertIn("if not enabled:\n\t\treset_thermal()\n\t\treturn", setter)
        reset = function(self.script, "reset_thermal")
        self.assertIn("_cancel_thermal()", reset)
        self.assertIn("_initialized = false", reset)
        self.assertIn("_set_heat(0.0)", reset)
        self.assertIn("reset_thermal()", function(self.script, "_exit_tree"))

    def test_reentry_same_status_and_nominal_initialization(self):
        setter = function(self.script, "set_operating_status")
        self.assertIn("if _initialized and _status == status:", setter)
        self.assertIn("var initialize := not _initialized", setter)
        self.assertIn("_set_heat(HEAT_LOW if status == PlanetWorldState.OperatingStatus.PRODUCING else 0.0)", setter)
        initialize = setter.split("if initialize:", 1)[1].split("match status:", 1)[0]
        self.assertIn("_start_pulse(_generation)", initialize)
        self.assertNotIn("_transition_to", initialize)
        self.assertIn("request_ready()", function(read("construction/machine_visual.gd"), "_exit_tree"))
        self.assertIn("_state.machine_status(_state.get_machine(machine_id))", function(read("construction/deployed_machine.gd"), "_enter_tree"))

    def test_direction_change_preserves_tween_and_four_selections(self):
        configure = function(self.script, "configure")
        self.assertNotRegex(configure, r"_thermal|_generation|_status|self_modulate|_set_heat|_start_pulse|_cancel_thermal")
        self.assertIn("if index != 2:", configure)
        for direction in (0, 90, 180, 270):
            self.assertEqual(self.script.count(f"smelter_{direction}_illumination.png"), 1)
        old = git_blob(BASE, "construction/smelter_visual.gd").decode().replace("\r\n", "\n")
        self.assertEqual(self.script.split("@onready")[0], old.split("@onready")[0])

    def test_frozen_assets_imports_scenes_and_historical_inventory(self):
        paths = [str(p.relative_to(ROOT)).replace("\\", "/")
                 for p in (ROOT / "assets/machines/smelter").iterdir()]
        self.assertEqual(len(paths), 20)
        paths += ["construction/smelter_visual.tscn", "docs/experiments/smelter_static_artwork.json"]
        verify_active_artifacts()  # Only the four pinned body derivatives may differ.
        for path in paths:
            if path in BODY_PATHS:
                continue
            with self.subTest(path=path):
                # Match repository text checkout conventions; PNGs remain exact bytes.
                self.assertEqual(normalized(path, (ROOT / path).read_bytes()),
                                 normalized(path, git_blob(BASE, path)))

    def test_shared_smelter_branch_changes_only_two_thermal_calls(self):
        path = "construction/machine_visual.gd"
        current = read(path)
        for addition in ("\t\t_smelter.set_operating_status(status, not is_ghost)\n",
                         "\t\t_smelter.reset_thermal()\n"):
            self.assertEqual(current.count(addition), 1)
            current = current.replace(addition, "")
        old = git_blob(BASE, path).decode().replace("\r\n", "\n")
        # Decision 36 adds the separate Fabricator branch; retain the exact
        # Extractor/Smelter branches and all existing status/lifecycle functions.
        start = 'if definition != null and definition.item_id == &"extractor":'
        current_branch = function(current, "_refresh_presentation").split(start, 1)[1].split(
            '\tif definition != null and definition.item_id == &"fabricator":', 1)[0]
        old_branch = function(old, "_refresh_presentation").split(start, 1)[1].split('\t_refresh_smelter_status()', 1)[0]
        self.assertEqual(current_branch, old_branch)
        for method in ("_ready", "_exit_tree", "_refresh_smelter_status", "_draw_smelter_status", "_status_color"):
            self.assertEqual(function(current, method).strip(), function(old, method).strip())

    def test_recovery_redeployment_and_gameplay_sources_unchanged(self):
        # Entire simulation, collision, transfer, recovery, other presenters and
        # scene hierarchy stay pinned; new thermal state cannot enter world data.
        for path in ("construction/deployed_machine.gd", "construction/construction_controller.gd",
                     "construction/machine_definition.gd", "construction/placement_rules.gd",
                     "construction/extractor_visual.gd", "construction/extractor_visual.tscn",
                     "inventory/smelter.tres", "inventory/extractor.tres", "inventory/fabricator.tres",
                     "scenes/main/playthrough_state.gd", "scenes/main/scene_transition_controller.gd",
                     "scenes/world/planet_world_state.gd", "scenes/world/planet_exterior.gd",
                     "scenes/world/planet_exterior.tscn", "scenes/player/dave.gd", "scenes/player/dave.tscn",
                     "scenes/ui/machine_ui.gd", "scenes/ui/smelter_inspection.gd",
                     "scenes/visuals/smelter_stationary.tscn", "scenes/world/stationary_machine_presentation.gd"):
            with self.subTest(path=path):
                # Authorized Fabricator 4x4 amendment; every other byte stays pinned.
                current = normalized(path, without_initial_preparation(path, (ROOT / path).read_bytes()))
                if path == "construction/deployed_machine.gd":
                    current = without_presentation_identity(current.decode()).encode()
                if path == "inventory/fabricator.tres":
                    self.assertEqual(current.count(b"footprint_cells = Vector2i(4, 4)"), 1)
                    current = current.replace(b"footprint_cells = Vector2i(4, 4)",
                                              b"footprint_cells = Vector2i(2, 2)")
                self.assertEqual(current,
                                 normalized(path, git_blob(BASE, path)))


if __name__ == "__main__":
    unittest.main()
