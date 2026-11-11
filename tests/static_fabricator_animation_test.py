from initial_exterior_preservation import verified_initial_paths
from static_save_codec_runner_test import verified_codec_runner_paths
"""Decision 62 offline source/scene/math/preservation checks; never executes Godot.

TLWH_FABRICATOR_FRONT_FROZEN_ROOT optionally enables complete external inventory,
byte equality and all 17 frozen pose comparisons. No package scripts are executed.
Independent math and control-flow tripwires do not certify GDScript or rendering.
"""
from application_shell_preservation import verified_application_paths
from fractions import Fraction
from functools import lru_cache
import hashlib
import json
import math
import os
from pathlib import Path
import re
import subprocess
import unittest

from current_preservation import ROOT, git_blob, normalized
from extractor_artwork_offline import ACTIVE_INVENTORY, BODY_PATHS, decode_png, place, verify_active_artifacts
from smelter_artwork_offline import (ACTIVE_INVENTORY as SMELTER_INVENTORY,
                                     BODY_PATHS as SMELTER_BODIES,
                                     verify_active_artifacts as verify_smelter_artifacts)
from static_automatic_transitions_test import function, nodes, vectors

BASE = "fd1f3347ad14a3735f5ffcc22b05730421b16212"
SCRIPT = "construction/fabricator_visual.gd"
SCENE = "construction/fabricator_visual.tscn"
DEPLOYED_ID_LINE = "\tvisual.presentation_machine_id = machine_id\n"
ROLES = ["body", "gantry", "tool", "carriage", "foreground"]
LAYER_PATHS = [f"assets/machines/fabricator/fabricator_0_{role}.png" for role in ROLES]
LAYER_HASHES = [
    "659c3e4f67ab5da4b331e76f6a5027fcd4411a38f5c9eeeec9b7be2524a80b53",
    "ba0c6f46b257fc6674a97afbc4e443c41426dba4850c85eb26b75961c4adbbb3",
    "bae53754b821dde684578f909eb6eca7cc68620f7df50d970c59106caabfc2b6",
    "47cb483f5b31d78ebf3acbfcab375ed61ffff4e921ab3c453fb9f6de329b30ac",
    "63714016278479350165651585b6d93e6286e8acaca0549214d698b96d0e207d",
]
SIZES = [(1120, 983), (422, 78), (68, 259), (134, 161), (501, 224)]
OFFSETS = [(-559, -957), (-211, -514), (-34, -512), (-67, -546), (-250, -312)]
LAYER_NODES = ["FrontAssembly/BodyLayer", "FrontAssembly/GantryY/Gantry",
               "FrontAssembly/GantryY/CarriageX/ToolZ/Tool",
               "FrontAssembly/GantryY/CarriageX/Carriage", "FrontAssembly/Foreground"]
GROUPS = {"FrontAssembly/GantryY": (0, 1, 0),
          "FrontAssembly/GantryY/CarriageX": (1, 0, 0),
          "FrontAssembly/GantryY/CarriageX/ToolZ": (0, 0, 1)}
# Independent approved tables: centiseconds, X, Y, Z, including each entry pose.
APPROVED = [
    [(0, -65, -20, -6), (18, -65, -20, 20), (198, 65, -20, 20),
     (216, 65, -20, -6), (286, 45, 18, -6), (304, 45, 18, 20),
     (419, -35, 18, 20), (437, -35, 18, -6), (500, -40, -8, -6)],
    [(0, -40, -8, -6), (16, -40, -8, 10), (106, -28, -8, 10),
     (122, -28, -8, -6), (162, 0, 12, -6), (172, 0, 12, -6),
     (188, 0, 12, 10), (278, 12, 12, 10), (294, 12, 12, -6),
     (334, 40, -8, -6), (350, 40, -8, 10), (440, 28, -8, 10),
     (456, 28, -8, -6), (500, 55, 26, -6)],
    [(0, 55, 26, -6), (18, 55, 26, 20), (318, -55, 26, 20),
     (336, -55, 26, -6), (376, -55, 26, -6), (500, -65, -20, -6)],
]


def read(path):
    return (ROOT / path).read_text(encoding="utf-8")


def without_presentation_identity(source):
    """Undo exactly the approved one-line addition; never exempt the source file."""
    if source.count(DEPLOYED_ID_LINE) != 1:
        raise AssertionError("Expected exactly one machine identity forwarding assignment")
    return source.replace(DEPLOYED_ID_LINE, "")


def patterns():
    section = read(SCRIPT).split("const PATTERNS := [", 1)[1].split("enum PresentationState", 1)[0]
    result = []
    for group in re.split(r'\[ # [^\n]+\n', section)[1:]:
        result.append([(Fraction(t), tuple(map(int, (x, y, z))))
                       for t, x, y, z in re.findall(
                           r'\[([0-9.]+), Vector3\((-?\d+), (-?\d+), (-?\d+)\)\]', group)])
    return result


def fractions(u):
    # Independent approved interpolation model, coupled to source formulas below.
    a, b, v = 0.12, 0.18, 20 / 17
    x = v*u*u/(2*a) if u < a else v*(u-a/2) if u <= 1-b else 1-v*(1-u)**2/(2*b)
    return x, (1-math.cos(math.pi*u))/2, 4*u**3 if u < 0.5 else 1-(-2*u+2)**3/2


def interpolate(start, end, u):
    return tuple(a + (b-a)*f for a, b, f in zip(start, end, fractions(u)))


@lru_cache(maxsize=1)
def decoded_layers():
    return [decode_png((ROOT / p).read_bytes()) for p in LAYER_PATHS]


def compose(pose):
    composite = bytearray(1254 * 1254 * 4)
    x, y, z = pose
    for role, (ox, oy), (w, h, rgba) in zip(ROLES, OFFSETS, decoded_layers()):
        if role in ("tool", "carriage"):
            ox += x
        if role in ("gantry", "tool", "carriage"):
            oy += y
        if role == "tool":
            oy += z
        place(rgba, w, h, (627 + ox, 1080 + oy), composite)
    return composite


class FabricatorAnimationStaticTest(unittest.TestCase):
    def test_five_encoded_identities_dimensions_and_alpha(self):
        for path, digest, size, (w, h, rgba) in zip(LAYER_PATHS, LAYER_HASHES, SIZES, decoded_layers()):
            with self.subTest(path=path):
                self.assertEqual(hashlib.sha256((ROOT / path).read_bytes()).hexdigest(), digest)
                self.assertEqual((w, h), size)
                self.assertIn(0, rgba[3::4])
                self.assertIn(255, rgba[3::4])

    def test_import_parameters_paths_and_unique_canonical_resource_identities(self):
        template = read("assets/machines/fabricator/fabricator_0_resting.png.import")
        uids = []
        for path in LAYER_PATHS:
            sidecar = read(path + ".import")
            self.assertEqual(sidecar.split("[params]", 1)[1], template.split("[params]", 1)[1])
            cache = f"res://.godot/imported/{Path(path).name}-" + hashlib.md5(
                ("res://" + path).encode()).hexdigest() + ".ctex"
            self.assertIn(f'path="{cache}"', sidecar)
            self.assertIn(f'dest_files=["{cache}"]', sidecar)
            self.assertIn(f'source_file="res://{path}"', sidecar)
            uid = re.search(r'uid="uid://([^"]+)"', sidecar)[1]
            self.assertRegex(uid, r'^[b-y0-8][a-y0-8]*$')
            value = 0
            for char in uid:
                value = value * 34 + "abcdefghijklmnopqrstuvwxy012345678".index(char)
            self.assertTrue(0 < value < 2**63)
            uids.append("uid://" + uid)
        self.assertEqual(len(set(uids)), 5)
        paths = subprocess.check_output(["git", "ls-files", "-z"], cwd=ROOT).decode().split("\0")
        for path in paths:
            if path.endswith((".uid", ".import")) and path not in [p + ".import" for p in LAYER_PATHS]:
                self.assertFalse(set(uids) & set(re.findall(r'uid://[a-y0-8]+', read(path))), path)

    def test_hierarchy_draw_order_identity_groups_and_crop_offsets(self):
        scene = read(SCENE)
        entries = nodes(scene)
        self.assertEqual(list(entries), ["FabricatorVisual", "Body", "FrontAssembly",
            LAYER_NODES[0], "FrontAssembly/GantryY", LAYER_NODES[1],
            "FrontAssembly/GantryY/CarriageX", "FrontAssembly/GantryY/CarriageX/ToolZ",
            *LAYER_NODES[2:]])
        self.assertEqual(vectors(entries["FabricatorVisual"][1]), [(64, 128)])
        self.assertIn("texture_filter = 4", entries["FabricatorVisual"][1])
        for group in GROUPS:
            self.assertEqual(entries[group][1].strip(), "")
        resources = dict(re.findall(r'path="res://([^"]+\.png)" id="([^"]+)"', scene))
        for node, path, offset in zip(LAYER_NODES, LAYER_PATHS, OFFSETS):
            self.assertIn('type="Sprite2D"', entries[node][0])
            self.assertEqual(vectors(entries[node][1]), [offset])
            self.assertIn('texture = ExtResource("' + resources[path] + '")', entries[node][1])
            self.assertIn("centered = false", entries[node][1])
        self.assertNotRegex(scene, r'rotation|scale =|flip_[hv]|z_index|y_sort_enabled|material|shader')

    def test_nested_motion_equations_and_world_registration(self):
        entries = nodes(read(SCENE))
        for pose in [(0, 0, 0), (-70, -28, -6), (70, 32, 20), (12, 4, 10)]:
            x, y, z = pose
            expected = [(-559, -957), (-211, -514+y), (-34+x, -512+y+z),
                        (-67+x, -546+y), (-250, -312)]
            for node, position in zip(LAYER_NODES, expected):
                px, py = vectors(entries[node][1])[0]
                # Walk actual scene ancestors, accumulating only their assigned axes.
                ancestor = node.rsplit("/", 1)[0]
                while ancestor:
                    dx, dy, dz = GROUPS.get(ancestor, (0, 0, 0))
                    px += dx*x
                    py += dy*y + dz*z
                    ancestor = ancestor.rsplit("/", 1)[0] if "/" in ancestor else ""
                self.assertEqual((px, py), position)
        self.assertEqual(Fraction(1040) * Fraction(8, 65), 128)
        set_pose = function(read(SCRIPT), "_set_pose")
        for statement in ("Vector2(0, pose.y)", "Vector2(pose.x, 0)", "Vector2(0, pose.z)"):
            self.assertIn(statement, set_pose)
        self.assertEqual(re.findall(r'(_\w+)\.position =', set_pose), ["_gantry_y", "_carriage_x", "_tool_z"])

    def test_resting_composite_exact_source_pixel_equivalence(self):
        _, _, expected = decode_png((ROOT / "assets/machines/fabricator/fabricator_0_resting.png").read_bytes())
        self.assertEqual(hashlib.sha256(compose((0, 0, 0))).digest(), hashlib.sha256(expected).digest())

    def test_all_approved_keyframes_and_contiguous_five_second_handoffs(self):
        actual = patterns()
        self.assertEqual(actual, [[(Fraction(t, 100), (x, y, z)) for t, x, y, z in p] for p in APPROVED])
        for i, frames in enumerate(actual):
            self.assertEqual(frames[0][0], 0)
            self.assertEqual(frames[-1][0], 5)
            durations = [b[0]-a[0] for a, b in zip(frames, frames[1:])]
            self.assertTrue(all(d > 0 for d in durations))
            self.assertEqual(sum(durations), 5)
            self.assertEqual(frames[-1][1], actual[(i+1) % 3][0][1])
        runner = function(read(SCRIPT), "_start_pattern")
        self.assertIn("range(1, frames.size())", runner)
        self.assertIn("frames[index][0] - frames[index - 1][0]", runner)
        self.assertNotIn("_set_pose", runner)

    def test_safe_engagement_fixed_depth_repositioning_and_holds(self):
        holds = []
        engagements = []
        for i, frames in enumerate(patterns()):
            depths = []
            for (ta, a), (tb, b) in zip(frames, frames[1:]):
                if a[2] != b[2]:
                    self.assertEqual(a[:2], b[:2])
                    if b[2] > 0:
                        depths.append(b[2])
                elif a[1] != b[1]:
                    self.assertEqual((a[2], b[2]), (-6, -6))
                elif a[0] != b[0]:
                    self.assertIn(a[2], (-6, 10, 20))
                if a == b:
                    holds.append((i, ta, tb-ta))
            engagements.append(depths)
        self.assertEqual(engagements, [[20, 20], [10, 10, 10], [20]])
        self.assertEqual(holds, [(1, Fraction(162, 100), Fraction(1, 10)),
                                 (2, Fraction(336, 100), Fraction(4, 10))])
        append = function(read(SCRIPT), "_append_phase")
        self.assertIn("if start == target:\n\t\t_motion.tween_interval(seconds)", append)

    def test_easing_continuity_velocity_monotonicity_and_no_overshoot(self):
        source = read(SCRIPT)
        x = function(source, "_carriage_fraction")
        for formula in ("const A := 0.12", "const B := 0.18", "const V := 20.0 / 17.0",
                        "u < A", "u <= 1.0 - B", "V * u * u / (2.0 * A)",
                        "V * (u - A / 2.0)", "1.0 - V * (1.0 - u) * (1.0 - u) / (2.0 * B)"):
            self.assertIn(formula, x)
        interpolation = function(source, "_interpolate_pose")
        self.assertIn("(1.0 - cos(PI * u)) / 2.0", interpolation)
        self.assertIn("4.0 * u * u * u if u < 0.5 else 1.0 - pow(-2.0 * u + 2.0, 3.0) / 2.0", interpolation)
        values = [fractions(i/1000) for i in range(1001)]
        self.assertEqual(values[0], (0, 0, 0))
        self.assertEqual(values[-1], (1, 1, 1))
        for axis in zip(*values):
            self.assertTrue(all(0 <= n <= 1 for n in axis))
            self.assertTrue(all(a <= b for a, b in zip(axis, axis[1:])))
        for u in (0.12, 0.4, 0.82):
            velocity = (fractions(u+1e-7)[0] - fractions(u-1e-7)[0]) / 2e-7
            self.assertAlmostEqual(velocity, 20/17, places=5)
        for u in (0, 1):
            near = 1e-7 if u == 0 else 1-1e-7
            self.assertAlmostEqual(abs(fractions(u)[0]-fractions(near)[0])/1e-7, 0, places=5)

    def test_every_sample_stays_inside_approved_and_frozen_envelopes(self):
        for frames in patterns():
            for (_, a), (_, b) in zip(frames, frames[1:]):
                for step in range(101):
                    pose = interpolate(a, b, step/100)
                    for value, (low, high), (frozen_low, frozen_high) in zip(
                            pose, [(-70, 70), (-28, 32), (-6, 20)], [(-90, 90), (-36, 42), (-8, 24)]):
                        self.assertTrue(frozen_low <= low <= value <= high <= frozen_high)

    def test_startup_shutdown_formulas_and_actual_pose_capture_before_cancellation(self):
        source = read(SCRIPT)
        for method, coefficient in [("_start_initializing", "0.15"), ("_start_shutdown", "0.18")]:
            body = function(source, method)
            self.assertLess(body.index("var pose := _displayed_pose()"), body.index("_begin_motion("))
            self.assertIn(f"_append_phase(pose, raised, {coefficient} * (pose.z + 6.0) / 26.0)", body)
            self.assertNotIn("_set_pose", body)
        self.assertIn("_append_phase(raised, entry, 0.45)", function(source, "_start_initializing"))
        shutdown = function(source, "_start_shutdown")
        self.assertLess(shutdown.index("pose, raised"), shutdown.index("raised, home, 0.70"))
        self.assertLess(shutdown.index("raised, home, 0.70"), shutdown.index("home, Vector3.ZERO, 0.12"))
        self.assertAlmostEqual(0.15*6/26+0.45, 0.4846153846153846)
        self.assertEqual(0.15*0/26+0.45, 0.45)
        for z, expected in [(20, 1.0), (10, 0.9307692307692308), (-6, 0.82)]:
            self.assertAlmostEqual(0.18*(z+6)/26+0.70+0.12, expected)
        # Stop and resume from samples of every phase, including outgoing handoffs.
        for frames in patterns():
            for (_, a), (_, b) in zip(frames, frames[1:]):
                for u in (0, 0.01, 0.5, 0.99, 1):
                    pose = interpolate(a, b, u)
                    raised = (*pose[:2], -6)
                    self.assertEqual(interpolate(pose, raised, 0), pose)
                    self.assertEqual(interpolate(pose, raised, 1), raised)
                    self.assertTrue(0 <= 0.18*(pose[2]+6)/26 <= 0.18)
                    for entry in [p[0][1] for p in patterns()]:
                        redirect = interpolate(raised, entry, 0.5)
                        self.assertEqual(redirect[2], -6)

    def test_single_owner_and_stale_completion_guards(self):
        source = read(SCRIPT)
        self.assertEqual(source.count("var _motion: Tween"), 1)
        self.assertEqual(source.count("create_tween()"), 1)
        begin = function(source, "_begin_motion")
        self.assertLess(begin.index("_cancel_motion()"), begin.index("create_tween()"))
        cancel = function(source, "_cancel_motion")
        self.assertLess(cancel.index("_generation += 1"), cancel.index("_motion.kill()"))
        self.assertLess(cancel.index("_motion.kill()"), cancel.index("_motion = null"))
        guard = function(source, "_completion_valid")
        for condition in ("generation == _generation", "_state == state", "_initialized",
                          "_can_animate()", "_production_intent == producing"):
            self.assertIn(condition, guard)
        for method, state, intent in [("_finish_initializing", "INITIALIZING", "true"),
                                      ("_finish_pattern", "FABRICATING", "true"),
                                      ("_finish_shutdown", "SHUTTING_DOWN", "false")]:
            body = function(source, method)
            self.assertIn(f"if not _completion_valid(generation, PresentationState.{state}, {intent}):\n\t\treturn", body)
            self.assertLess(body.index("_completion_valid"), body.index("_motion = null"))
        self.assertEqual(source.count("CONNECT_ONE_SHOT"), 3)
        self.assertIn("generation != _generation or not _can_animate()", function(source, "_interpolate_pose"))

    def test_status_idempotence_abandonment_and_cursor_ownership(self):
        source = read(SCRIPT)
        setter = function(source, "set_operating_status")
        self.assertIn("var producing := status == PlanetWorldState.OperatingStatus.PRODUCING", setter)
        self.assertIn("if _production_intent == producing and _enabled == enabled:\n\t\treturn", setter)
        self.assertLess(setter.index("if _production_intent =="), setter.index("_production_intent = producing"))
        refresh = function(source, "_refresh_motion")
        self.assertIn("if _state in [PresentationState.REST, PresentationState.SHUTTING_DOWN]:\n\t\t\t_start_initializing()", refresh)
        self.assertIn("elif _state in [PresentationState.INITIALIZING, PresentationState.FABRICATING]:", refresh)
        advance = "_pattern_cursor = (_pattern_cursor + 1) % 3"
        self.assertLess(refresh.index(advance), refresh.index("_start_shutdown()"))
        self.assertEqual(source.count(advance), 2)
        self.assertIn(advance, function(source, "_finish_pattern"))
        # Attempt reservation and outgoing handoff ownership share the same cursor;
        # only completion OR a producing->nonproducing edge advances that attempt.
        for cursor in range(3):
            for phase in ("INITIALIZING", "FABRICATING", "OUTGOING_HANDOFF"):
                next_cursor = (cursor + 1) % 3
                self.assertEqual(patterns()[cursor][-1][1], patterns()[next_cursor][0][1], phase)
        deployed = read("construction/deployed_machine.gd")
        self.assertIn("if status == _visual.status:\n\t\treturn", function(deployed, "_process"))
        self.assertIn("if status == value:\n\t\t\treturn", read("construction/machine_visual.gd"))

    def test_visibility_orientation_ghost_exit_and_reentry_contracts(self):
        source = read(SCRIPT)
        gate = function(source, "_can_animate")
        for condition in ("is_node_ready()", "is_inside_tree()", "is_visible_in_tree()", "_enabled", "_turns == 0"):
            self.assertIn(condition, gate)
        view = function(source, "_refresh_view")
        self.assertIn("var layered := _enabled and _turns == 0", view)
        self.assertIn("_body.visible = not layered", view)
        self.assertIn("_front_assembly.visible = layered", view)
        self.assertNotIn("_production_intent", view)
        self.assertIn("visibility_changed.connect(_on_visibility_changed)", function(source, "_ready"))
        self.assertIn("_refresh_motion()", function(source, "_on_visibility_changed"))
        self.assertIn("if not _can_animate():\n\t\t_reset_motion()", function(source, "_refresh_motion"))
        reset = function(source, "_reset_motion")
        for statement in ("_cancel_motion()", "_state = PresentationState.REST", "_initialized = false",
                          "_pattern_cursor = _starting_pattern()", "_set_pose(Vector3.ZERO)"):
            self.assertIn(statement, reset)
        exit_tree = function(source, "_exit_tree")
        for statement in ("_reset_motion()", "_production_intent = false", "_applied_turns = -1", "request_ready()"):
            self.assertIn(statement, exit_tree)
        self.assertIn("_reset_motion()", function(source, "configure"))
        adapter = read("construction/machine_visual.gd")
        self.assertIn("_fabricator.set_operating_status(status, not is_ghost)", adapter)
        self.assertIn("_fabricator.set_operating_status(status, false)\n\t\t_fabricator_art_container.hide()", adapter)
        self.assertIn("request_ready()", function(adapter, "_exit_tree"))

    def test_deterministic_identity_forwarding_before_tree_and_status(self):
        source = read(SCRIPT)
        self.assertIn("return posmod(_machine_id - 1, 3) if _machine_id > 0 else 0", function(source, "_starting_pattern"))
        self.assertNotRegex(source, r'rand[if]|RandomNumberGenerator|FileAccess|machine_status\(|recipe|inventory')
        self.assertEqual([(i-1) % 3 if i > 0 else 0 for i in range(10)], [0, 0, 1, 2, 0, 1, 2, 0, 1, 2])
        deployed = function(read("construction/deployed_machine.gd"), "configure")
        self.assertLess(deployed.index(DEPLOYED_ID_LINE.strip()), deployed.index("add_child(visual)"))
        adapter = function(read("construction/machine_visual.gd"), "_refresh_presentation")
        self.assertLess(adapter.index("_fabricator.set_presentation_identity(presentation_machine_id)"),
                        adapter.index("_fabricator_art_container.add_child(_fabricator)"))
        self.assertLess(adapter.index("_fabricator.configure(turns)"),
                        adapter.index("_fabricator.set_operating_status(status, not is_ghost)"))

    def test_deployed_machine_preserved_except_exact_identity_assignment(self):
        path = "construction/deployed_machine.gd"
        self.assertEqual(without_presentation_identity(read(path)), git_blob(BASE, path).decode().replace("\r\n", "\n"))

    def test_shared_adapter_preserved_except_exact_fabricator_additions(self):
        path = "construction/machine_visual.gd"
        current = read(path)
        for addition in ("var presentation_machine_id: int = 0\n",
                         "\t\t\t_fabricator.set_presentation_identity(presentation_machine_id)\n",
                         "\t\t_fabricator.set_operating_status(status, not is_ghost)\n",
                         "\t\t_fabricator.set_operating_status(status, false)\n"):
            self.assertEqual(current.count(addition), 1)
            current = current.replace(addition, "")
        pair = "\t\t_fabricator.configure(turns)\n\t\t_fabricator_art_container.show()\n"
        self.assertEqual(current.count(pair), 1)
        current = current.replace(pair, "\t\t_fabricator_art_container.show()\n\t\t_fabricator.configure(turns)\n")
        self.assertEqual(current, git_blob(BASE, path).decode().replace("\r\n", "\n"))

    def test_all_other_production_artwork_gameplay_and_execution_controls_preserved(self):
        changed = subprocess.check_output(["git", "diff", "--name-only", BASE, "--", "inventory",
            "construction", "scenes", "assets", "objectives", "dialogue", "project.godot", "tools",
            "AGENTS.md", "docs/LOCAL_TESTING.md", "docs/experiments"], cwd=ROOT, text=True).splitlines()
        allowed = {SCRIPT, SCENE, "construction/machine_visual.gd", "construction/deployed_machine.gd",
                   *LAYER_PATHS, *(p + ".import" for p in LAYER_PATHS)}
        # Decision 2A: four exact identities, plus their one derivative record.
        verify_active_artifacts()
        allowed.update(BODY_PATHS)
        allowed.add(ACTIVE_INVENTORY.relative_to(ROOT).as_posix())
        # Port-free Smelter v1: four verified bodies and one exact provenance path.
        verify_smelter_artifacts()
        allowed.update(SMELTER_BODIES)
        allowed.add(SMELTER_INVENTORY.relative_to(ROOT).as_posix())
        allowed.update(verified_application_paths())
        allowed.update(verified_initial_paths())
        allowed.update(verified_codec_runner_paths())
        self.assertFalse(set(changed) - allowed, changed)
        # Explicit immutable files/trees also protect dirty working data before staging.
        protected = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", BASE, "--",
            "assets/machines", "inventory", "construction", "scenes/world/planet_world_state.gd",
            "docs/experiments/fabricator_static_artwork.json"], cwd=ROOT, text=True).splitlines()
        for path in protected:
            if path in BODY_PATHS or path in SMELTER_BODIES:
                continue  # Exact active and historical identities checked above.
            if path not in (SCRIPT, SCENE, "construction/machine_visual.gd", "construction/deployed_machine.gd"):
                self.assertEqual(normalized(path, (ROOT / path).read_bytes()), normalized(path, git_blob(BASE, path)), path)

    @unittest.skipUnless(os.environ.get("TLWH_FABRICATOR_FRONT_FROZEN_ROOT"), "External front package root not supplied")
    def test_complete_external_inventory_exact_copy_and_seventeen_frozen_poses(self):
        root = Path(os.environ["TLWH_FABRICATOR_FRONT_FROZEN_ROOT"]).resolve(strict=True)
        record = json.loads(read("docs/experiments/fabricator_static_artwork.json"))["directions"][0]
        self.assertEqual(hashlib.sha256((root / "freeze/manifest.json").read_bytes()).hexdigest(), record["manifest_sha256"])
        snapshot = {}
        for path in sorted(root.rglob("*")):
            self.assertFalse(path.is_symlink() or path.is_junction())
            if path.is_file():
                raw = path.read_bytes()
                snapshot[path.relative_to(root).as_posix()] = [len(raw), hashlib.sha256(raw).hexdigest()]
        self.assertEqual(len(snapshot), 81)
        self.assertEqual(hashlib.sha256(json.dumps(snapshot, sort_keys=True, separators=(",", ":")).encode()).hexdigest(),
                         record["frozen_inventory_sha256"])
        for line in (root / "freeze/SHA256SUMS.txt").read_text().splitlines():
            digest, relative = line.split("  ", 1)
            path = (root / "freeze" / relative).resolve(strict=True)
            self.assertTrue(path.is_relative_to(root))
            self.assertEqual(hashlib.sha256(path.read_bytes()).hexdigest(), digest)
        for path in LAYER_PATHS:
            self.assertEqual((ROOT / path).read_bytes(), (root / "payload/runtime" / Path(path).name).read_bytes())
        registration = json.loads((root / "payload/manifest.json").read_text())["registration"]
        poses = registration["poses"] + registration["y_sweep"]
        self.assertEqual(len(poses), 17)
        for pose in poses:
            _, _, expected = decode_png((root / f'payload/previews/pose_{pose["name"]}.png').read_bytes())
            self.assertEqual(hashlib.sha256(compose((pose["x"], pose["y"], pose["z"]))).digest(),
                             hashlib.sha256(expected).digest(), pose["name"])


if __name__ == "__main__":
    unittest.main()
