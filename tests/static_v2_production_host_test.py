"""Read-only scene/route/geometry checks; no Godot or gameplay code execution."""

import hashlib
import math
import posixpath
import re
import subprocess
import unittest
from unittest.mock import patch

import static_automatic_transitions_test as geometry
from static_automatic_transitions_test import ROOT, PRIMARY, MAINTENANCE, EXTERIOR, read, merged_nodes


# Live post-P6 / pre-P8 main verified for cutover; never follow a moving ref.
P8_BASE = "e14703e64aef961f18feba8a616acec00c4f069e"

# B1 inventory and hotbar context-menu integration replace exactly these UI files.
# Freeze normalized candidate bytes rather than exempting them from preservation.
# Refined inventory scene candidate requires owner review before Native execution.
B1_INVENTORY_SHA256 = {
    "scenes/ui/inventory_ui.gd": "5a5273e46ebd4d0f8817f2f0c4d7bab615d5c054de6faeb8f44f043eba307a48",
    "scenes/ui/inventory_ui.tscn": "aa89e021636a53e9e6d646588bcfd7b48100a57ac4a19c00b03a81349a8497bb",
}

# The inventory hash now delegates artwork/quantity formatting to this exact
# shared helper; retain full normalized-byte protection for the moved code.
HOTBAR_ITEM_PRESENTATION_SHA256 = "90e58359dd26d202848461ddd212dbfc5a37e7d50f5cf1c997f56e4138f47862"

# Hybrid hotbar allowance, pending owner review before Native execution.
# Reverse only these literal, single-occurrence edits, then retain the existing
# immutable historical comparisons. No path/directory exemptions are added.
HOTBAR_BASE = "92947fac8b9a7866c740ae5ee11b5cfd0b549ea4"
HOTBAR_REPLACEMENTS = {'construction/construction_controller.gd': [('\n'
                                              'func get_deployment_item_id() -> StringName:\n'
                                              '\treturn _definition.item_id if _mode == '
                                              'Mode.CONSTRUCTION and _definition != null else &""\n'
                                              '\n'
                                              '\n'
                                              '# Empty string means accepted. Reject before '
                                              'cancel() so a failed switch keeps\n'
                                              '# the current ghost, orientation and pending '
                                              'confirmation intact.\n'
                                              'func activate_hotbar(definition: MachineDefinition) '
                                              '-> String:\n'
                                              '\tif _context_blocked() or _mode == Mode.RECOVERY:\n'
                                              '\t\treturn "Close the current interaction or '
                                              'recovery mode before deploying."\n'
                                              '\tif definition == null or not '
                                              'definition.is_valid():\n'
                                              '\t\treturn "Machine unavailable."\n'
                                              '\tif get_deployment_item_id() == '
                                              'definition.item_id:\n'
                                              '\t\tcancel()\n'
                                              '\t\treturn ""\n'
                                              '\tif '
                                              'progression.inventory.get_quantity(definition.item_id) '
                                              '< 1:\n'
                                              '\t\treturn "No %s in inventory." % '
                                              'definition.display_name\n'
                                              '\tif not begin_deployment(definition):\n'
                                              '\t\treturn "Cannot deploy %s here." % '
                                              'definition.display_name\n'
                                              '\treturn ""\n'
                                              '\n'
                                              '\n'
                                              'func cancel() -> void:\n',
                                              '\nfunc cancel() -> void:\n'),
                                             ('\t\treturn\n'
                                              '\tif event.is_action_pressed("ui_cancel"):\n'
                                              '\t\tcancel()\n',
                                              '\t\treturn\n'
                                              '\tif event.is_action_pressed("ui_cancel") or (event '
                                              'is InputEventMouseButton \\\n'
                                              '\t\t\tand event.pressed and event.button_index == '
                                              'MOUSE_BUTTON_RIGHT):\n'
                                              '\t\tcancel()\n'),
                                             ('\tif event.is_echo() or _context_blocked():\n'
                                              '\t\treturn\n'
                                              '\t# GUI gets first refusal for cancellation too: '
                                              'hotbar context clicks must\n'
                                              '\t# never cancel a placement before their slot '
                                              'receives gui_input.\n'
                                              '\tif _mode != Mode.NONE and event is '
                                              'InputEventMouseButton \\\n'
                                              '\t\t\tand event.pressed and event.button_index == '
                                              'MOUSE_BUTTON_RIGHT:\n'
                                              '\t\tcancel()\n'
                                              '\t\tget_viewport().set_input_as_handled()\n'
                                              '\t\treturn\n',
                                              '\tif event.is_echo() or _context_blocked():\n'
                                              '\t\treturn\n')],
 'construction/construction_controller.tscn': [('offset_left = -390.0\n'
                                                'offset_top = -144.0\n'
                                                'offset_right = 390.0\n'
                                                'offset_bottom = -92.0\n'
                                                'mouse_filter = 2\n',
                                                'offset_left = -390.0\n'
                                                'offset_top = -128.0\n'
                                                'offset_right = 390.0\n'
                                                'offset_bottom = -80.0\n'
                                                'mouse_filter = 2\n')],
 'scenes/main/main.tscn': [('[gd_scene load_steps=17 format=3]\n\n',
                            '[gd_scene load_steps=16 format=3]\n\n'),
                           ('[ext_resource type="Script" '
                            'path="res://scenes/main/display_configuration.gd" id="15_display"]\n'
                            '\n'
                            '[ext_resource type="PackedScene" '
                            'path="res://scenes/ui/hotbar_ui.tscn" id="16_hotbar"]\n'
                            '\n',
                            '[ext_resource type="Script" '
                            'path="res://scenes/main/display_configuration.gd" id="15_display"]\n'
                            '\n'),
                           ('\n'
                            '[node name="InventoryUI" parent="." '
                            'node_paths=PackedStringArray("progression", "construction", '
                            '"transitions") instance=ExtResource("12_inventory")]\n'
                            'progression = NodePath("../PlaythroughState")\n'
                            'construction = NodePath("../Construction")\n'
                            'transitions = NodePath("../SceneTransitions")\n'
                            '\n',
                            '\n'
                            '[node name="InventoryUI" parent="." '
                            'node_paths=PackedStringArray("progression", "construction") '
                            'instance=ExtResource("12_inventory")]\n'
                            'progression = NodePath("../PlaythroughState")\n'
                            'construction = NodePath("../Construction")\n'
                            '\n'),
                           ('construction = NodePath("../Construction")\n'
                            '\n'
                            '[node name="HotbarUI" parent="." '
                            'node_paths=PackedStringArray("progression", "construction", '
                            '"transitions", "player") instance=ExtResource("16_hotbar")]\n'
                            'progression = NodePath("../PlaythroughState")\n'
                            'construction = NodePath("../Construction")\n'
                            'transitions = NodePath("../SceneTransitions")\n'
                            'player = NodePath("../Dave")\n',
                            'construction = NodePath("../Construction")\n')],
 'scenes/main/playthrough_state.gd': [('signal fabricator_recovery_completed\n'
                                       'signal hotbar_changed\n'
                                       '\n',
                                       'signal fabricator_recovery_completed\n\n'),
                                      ('var inventory: InventoryState = InventoryState.new()\n'
                                       '# Type assignments belong to the session, never the '
                                       'disposable HUD or inventory.\n'
                                       'const HOTBAR_SIZE := 10\n'
                                       'var _hotbar: Array[MachineDefinition] = [null, null, null, '
                                       'null, null, null, null, null, null, null]\n'
                                       'var _hotbar_customized: Array[bool] = [false, false, '
                                       'false, false, false, false, false, false, false, false]\n'
                                       'var _hotbar_defaults_seen: Dictionary[StringName, bool] = '
                                       '{}\n'
                                       'var extractor_recovered: bool:\n',
                                       'var inventory: InventoryState = InventoryState.new()\n'
                                       'var extractor_recovered: bool:\n'),
                                      ('func _on_inventory_changed() -> void:\n'
                                       '\t_apply_hotbar_defaults()\n'
                                       '\tif not ferrite_acquired and '
                                       'inventory.get_quantity(FERRITE_ORE.item_id) > 0:\n',
                                       'func _on_inventory_changed() -> void:\n'
                                       '\tif not ferrite_acquired and '
                                       'inventory.get_quantity(FERRITE_ORE.item_id) > 0:\n'),
                                      ('\t\tferrite_plate_acquisition_completed.emit()\n'
                                       '\n'
                                       '\n'
                                       'func get_hotbar_assignment(slot: int) -> '
                                       'MachineDefinition:\n'
                                       '\treturn _hotbar[slot] if slot >= 0 and slot < HOTBAR_SIZE '
                                       'else null\n'
                                       '\n'
                                       '\n'
                                       'func assign_hotbar(slot: int, definition: '
                                       'MachineDefinition) -> bool:\n'
                                       '\tif slot < 0 or slot >= HOTBAR_SIZE or definition == null '
                                       'or not definition.is_valid() \\\n'
                                       '\t\t\tor inventory.get_quantity(definition.item_id) < 1:\n'
                                       '\t\treturn false\n'
                                       '\t_hotbar[slot] = definition\n'
                                       '\t_hotbar_customized[slot] = true\n'
                                       '\thotbar_changed.emit()\n'
                                       '\treturn true\n'
                                       '\n'
                                       '\n'
                                       'func clear_hotbar(slot: int) -> void:\n'
                                       '\tif slot < 0 or slot >= HOTBAR_SIZE:\n'
                                       '\t\treturn\n'
                                       '\t_hotbar[slot] = null\n'
                                       '\t_hotbar_customized[slot] = true\n'
                                       '\thotbar_changed.emit()\n'
                                       '\n'
                                       '\n'
                                       'func _apply_hotbar_defaults() -> void:\n'
                                       '\t# First possession is the existing packaged-machine '
                                       'availability boundary.\n'
                                       '\t# Consider each default once, even when its preferred '
                                       'slot is customized.\n'
                                       '\tvar defaults: Array[MachineDefinition] = [EXTRACTOR as '
                                       'MachineDefinition,\n'
                                       '\t\tSMELTER as MachineDefinition, FABRICATOR as '
                                       'MachineDefinition]\n'
                                       '\tfor slot in defaults.size():\n'
                                       '\t\tvar definition := defaults[slot]\n'
                                       '\t\tif _hotbar_defaults_seen.has(definition.item_id) \\\n'
                                       '\t\t\t\tor inventory.get_quantity(definition.item_id) < '
                                       '1:\n'
                                       '\t\t\tcontinue\n'
                                       '\t\t_hotbar_defaults_seen[definition.item_id] = true\n'
                                       '\t\tvar already_assigned := false\n'
                                       '\t\tfor assigned in _hotbar:\n'
                                       '\t\t\tif assigned != null and assigned.item_id == '
                                       'definition.item_id:\n'
                                       '\t\t\t\talready_assigned = true\n'
                                       '\t\tif not _hotbar_customized[slot] and _hotbar[slot] == '
                                       'null and not already_assigned:\n'
                                       '\t\t\t_hotbar[slot] = definition\n'
                                       '\t\t\thotbar_changed.emit()\n'
                                       '\n',
                                       '\t\tferrite_plate_acquisition_completed.emit()\n\n')],
 'scenes/ui/interaction_ui.tscn': [('offset_left = -280.0\n'
                                    'offset_top = -128.0\n'
                                    'offset_right = 280.0\n'
                                    'offset_bottom = -96.0\n'
                                    'mouse_filter = 2\n',
                                    'offset_left = -280.0\n'
                                    'offset_top = -72.0\n'
                                    'offset_right = 280.0\n'
                                    'offset_bottom = -40.0\n'
                                    'mouse_filter = 2\n')],
 'scenes/ui/musing_ui.tscn': [('offset_left = 24.0\n'
                               'offset_top = -296.0\n'
                               'offset_right = 0.0\n'
                               'offset_bottom = -160.0\n'
                               'grow_vertical = 0\n',
                               'offset_left = 24.0\n'
                               'offset_top = -232.0\n'
                               'offset_right = 0.0\n'
                               'offset_bottom = -96.0\n'
                               'grow_vertical = 0\n')]}


# Owner-approved Option A: only these baseline files may retire in separate PR B.
# Their contents/existence are deliberately not test inputs. This is not a glob
# exemption for other current/future development files or production resources.
APPROVED_DEV_RETIREMENT = frozenset("""
scenes/dev/maintenance_bay_v2_collision_preview.gd
scenes/dev/maintenance_bay_v2_collision_preview.gd.uid
scenes/dev/maintenance_bay_v2_collision_preview.tscn
scenes/dev/maintenance_bay_v2_extractor_preview.gd
scenes/dev/maintenance_bay_v2_extractor_preview.gd.uid
scenes/dev/maintenance_bay_v2_extractor_preview.tscn
scenes/dev/maintenance_bay_v2_fabricator_preview.gd
scenes/dev/maintenance_bay_v2_fabricator_preview.gd.uid
scenes/dev/maintenance_bay_v2_fabricator_preview.tscn
scenes/dev/maintenance_bay_v2_scale_preview.gd
scenes/dev/maintenance_bay_v2_scale_preview.gd.uid
scenes/dev/maintenance_bay_v2_scale_preview.tscn
scenes/dev/maintenance_bay_v2_smelter_preview.gd
scenes/dev/maintenance_bay_v2_smelter_preview.gd.uid
scenes/dev/maintenance_bay_v2_smelter_preview.tscn
scenes/dev/physics_shape_outlines.gd
scenes/dev/physics_shape_outlines.gd.uid
scenes/dev/ship_interior_v2_collision_preview.gd
scenes/dev/ship_interior_v2_collision_preview.gd.uid
scenes/dev/ship_interior_v2_collision_preview.tscn
scenes/dev/ship_interior_v2_scale_preview.gd
scenes/dev/ship_interior_v2_scale_preview.gd.uid
scenes/dev/ship_interior_v2_scale_preview.tscn
scenes/dev/ship_interior_v2_transition_preview.gd
scenes/dev/ship_interior_v2_transition_preview.gd.uid
scenes/dev/ship_interior_v2_transition_preview.tscn
scenes/dev/ship_interior_v2_transition_world.gd
scenes/dev/ship_interior_v2_transition_world.gd.uid
scenes/dev/ship_interior_v2_transition_world.tscn
scenes/dev/transition_test_exterior.tscn
scenes/dev/transition_test_maintenance.tscn
scenes/dev/v2_connection_interior.tscn
scenes/dev/v2_connection_maintenance.tscn
scenes/dev/v2_connection_world.gd
scenes/dev/v2_connection_world.gd.uid
scenes/dev/v2_two_room_connection.gd
scenes/dev/v2_two_room_connection.gd.uid
scenes/dev/v2_two_room_connection.tscn
""".split())


# Exact owner-approved B1 edits only. Normalize them before the existing fixed
# historical comparisons; unrelated properties, transforms and gameplay stay protected.
B1_REPLACEMENTS = {'project.godot': [('window/size/viewport_width=1280\n'
                    'window/size/viewport_height=720\n'
                    'window/size/mode=0\n'
                    'window/size/resizable=true\n'
                    'window/size/borderless=false\n'
                    'window/size/window_width_override=1280\n'
                    'window/size/window_height_override=720\n'
                    'window/stretch/mode="canvas_items"\n'
                    'window/stretch/aspect="expand"\n'
                    '\n'
                    '[input]\n'
                    '\n'
                    'inventory={\n'
                    '"deadzone": 0.2,\n',
                    'window/size/viewport_width=1280\n'
                    'window/size/viewport_height=720\n'
                    'window/stretch/mode="canvas_items"\n'
                    '\n'
                    '[input]\n'
                    '\n'
                    'inventory={\n'
                    '"deadzone": 0.2,\n')],
 'scenes/main/main.tscn': [('[gd_scene load_steps=16 format=3]\n'
                            '\n'
                            '[ext_resource type="Script" path="res://scenes/main/main.gd" '
                            'id="1_main"]\n',
                            '[gd_scene load_steps=15 format=3]\n'
                            '\n'
                            '[ext_resource type="Script" path="res://scenes/main/main.gd" '
                            'id="1_main"]\n'),
                           ('[ext_resource type="PackedScene" '
                            'path="res://construction/construction_controller.tscn" '
                            'id="13_construction"]\n'
                            '[ext_resource type="PackedScene" '
                            'path="res://scenes/ui/machine_ui.tscn" id="14_machine"]\n'
                            '[ext_resource type="Script" '
                            'path="res://scenes/main/display_configuration.gd" id="15_display"]\n'
                            '\n'
                            '[node name="Main" type="Node2D"]\n',
                            '[ext_resource type="PackedScene" '
                            'path="res://construction/construction_controller.tscn" '
                            'id="13_construction"]\n'
                            '[ext_resource type="PackedScene" '
                            'path="res://scenes/ui/machine_ui.tscn" id="14_machine"]\n'
                            '\n'
                            '[node name="Main" type="Node2D"]\n'),
                           ('construction = NodePath("../Construction")\n'
                            '\n'
                            '[node name="DisplayConfiguration" type="Node" parent="."]\n'
                            'script = ExtResource("15_display")\n'
                            '\n'
                            '[node name="Construction" parent="." '
                            'node_paths=PackedStringArray("player", "progression", "transitions", '
                            '"inventory_ui") instance=ExtResource("13_construction")]\n'
                            'player = NodePath("../Dave")\n',
                            'construction = NodePath("../Construction")\n'
                            '\n'
                            '[node name="Construction" parent="." '
                            'node_paths=PackedStringArray("player", "progression", "transitions", '
                            '"inventory_ui") instance=ExtResource("13_construction")]\n'
                            'player = NodePath("../Dave")\n')],
 'scenes/ui/machine_ui.tscn': [('\n'
                                '[ext_resource type="Script" path="res://scenes/ui/machine_ui.gd" '
                                'id="1_ui"]\n'
                                '[ext_resource type="Theme" path="res://assets/ui/b1_theme.tres" '
                                'id="2_b1"]\n'
                                '\n'
                                '[node name="MachineUI" type="CanvasLayer"]\n',
                                '\n'
                                '[ext_resource type="Script" path="res://scenes/ui/machine_ui.gd" '
                                'id="1_ui"]\n'
                                '\n'
                                '[sub_resource type="StyleBoxFlat" id="MachineStyle"]\n'
                                'bg_color = Color(0.045, 0.075, 0.10, 0.97)\n'
                                'border_width_left = 1\n'
                                'border_width_top = 1\n'
                                'border_width_right = 1\n'
                                'border_width_bottom = 1\n'
                                'border_color = Color(0.47, 0.61, 0.60, 1)\n'
                                'content_margin_left = 16.0\n'
                                'content_margin_top = 12.0\n'
                                'content_margin_right = 16.0\n'
                                'content_margin_bottom = 12.0\n'
                                '\n'
                                '[node name="MachineUI" type="CanvasLayer"]\n'),
                               ('grow_vertical = 2\n'
                                'mouse_filter = 2\n'
                                'theme = ExtResource("2_b1")\n'
                                '\n'
                                '[node name="Panel" type="PanelContainer" parent="HUD"]\n',
                                'grow_vertical = 2\n'
                                'mouse_filter = 2\n'
                                '\n'
                                '[node name="Panel" type="PanelContainer" parent="HUD"]\n'),
                               ('grow_horizontal = 0\n'
                                'mouse_filter = 0\n'
                                '\n'
                                '[node name="Content" type="VBoxContainer" parent="HUD/Panel"]\n',
                                'grow_horizontal = 0\n'
                                'mouse_filter = 0\n'
                                'theme_override_styles/panel = SubResource("MachineStyle")\n'
                                '\n'
                                '[node name="Content" type="VBoxContainer" parent="HUD/Panel"]\n'),
                               ('layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_type_variation = &"B1Title"\n'
                                'text = "Extractor"\n'
                                '\n',
                                'layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_override_font_sizes/font_size = 22\n'
                                'text = "Extractor"\n'
                                '\n'),
                               ('layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_type_variation = &"B1MutedLabel"\n'
                                'text = "Production Paused"\n'
                                '\n',
                                'layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_override_colors/font_color = Color(0.55, 0.58, 0.59, 1)\n'
                                'theme_override_font_sizes/font_size = 14\n'
                                'text = "Production Paused"\n'
                                '\n'),
                               ('layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_type_variation = &"B1WarningLabel"\n'
                                'autowrap_mode = 2\n'
                                '\n',
                                'layout_mode = 2\n'
                                'mouse_filter = 2\n'
                                'theme_override_colors/font_color = Color(0.95, 0.65, 0.45, 1)\n'
                                'autowrap_mode = 2\n'
                                '\n')]}


def without_approved_hotbar_changes(path, text):
    for approved, historical in HOTBAR_REPLACEMENTS.get(path, []):
        if text.count(approved) != 1:
            raise AssertionError(f"Missing or modified hotbar edit pending review: {path}")
        text = text.replace(approved, historical, 1)
    return text


def without_approved_b1_changes(path, text):
    text = without_approved_hotbar_changes(path, text)
    if path == "project.godot":
        # Normalize only the inventory action's owner-approved I -> Tab binding.
        start = text.index('inventory={\n')
        end = text.index('\n}', start)
        action = text[start:end]
        if action.count('"physical_keycode":4194306,') != 1:
            raise AssertionError("Inventory must have exactly one physical Tab binding")
        text = text[:start] + action.replace('"physical_keycode":4194306,',
                                             '"physical_keycode":73,', 1) + text[end:]
        # The editor omits default-valued window flags on save. Accept their
        # omission, but still reject nondefault values or unrelated changes.
        anchor = "window/size/viewport_height=720\n"
        for setting in reversed(["window/size/mode=0", "window/size/resizable=true",
                                 "window/size/borderless=false"]):
            key = setting.split("=", 1)[0]
            if not re.search(rf"^{re.escape(key)}=", text, re.M):
                text = text.replace(anchor, anchor + setting + "\n", 1)
    for approved, historical in B1_REPLACEMENTS.get(path, []):
        if text.count(approved) != 1:
            raise AssertionError(f"Missing or modified approved B1 edit: {path}")
        text = text.replace(approved, historical, 1)
    return text


def is_dev_path(path):
    path = posixpath.normpath(path.replace("\\", "/")).casefold()
    return path == "scenes/dev" or path.startswith("scenes/dev/")


def tracked_non_dev_files(pattern):
    # Filter Git metadata before opening anything, including UID sidecars.
    paths = subprocess.check_output(["git", "ls-files", pattern], cwd=ROOT, text=True).splitlines()
    return [path for path in paths if not is_dev_path(path)]


class V2ProductionHostStaticTest(unittest.TestCase):
    def test_f5_v2_host_and_independent_legacy_f6_scene(self):
        project = read("project.godot")
        self.assertEqual(re.findall(r'^[ \t]*run/main_scene[ \t]*=(.*)$', project, re.M),
                         ['"res://scenes/main/main_v2.tscn"'])
        configured = re.search(r'^run/main_scene="res://([^"]+)"$', project, re.M)[1]
        self.assertTrue((ROOT / configured).is_file())
        self.assertIn('[node name="MainV2" instance=ExtResource("1_main")]', read(configured))
        self.assertIn('path="res://scenes/main/main_v2.gd"', read(configured))
        legacy = read("scenes/main/main.tscn")
        self.assertIn('[node name="Main" type="Node2D"]', legacy)
        self.assertIn('path="res://scenes/main/main.gd"', legacy)
        self.assertIn('path="res://scenes/world/ship_interior.tscn"', legacy)
        self.assertIn('instance=ExtResource("2_interior")',
                      geometry.nodes(legacy)["Worlds/ShipInterior"][0])
        self.assertNotIn("main_v2", legacy)

    def test_resource_graph_has_no_dev_dependency_and_valid_declarations(self):
        self.assert_resource_graph(["project.godot", "scenes/main/main.tscn"])

    def assert_resource_graph(self, roots):
        # Follow literal paths, global script classes and tracked UID metadata.
        # Variable load targets remain covered by explicit route-contract tests;
        # this text traversal is not runtime or full GDScript analysis.
        classes = {}
        for path in tracked_non_dev_files("*.gd"):
            match = re.search(r'^class_name (\w+)', read(path), re.M)
            if match:
                self.assertNotIn(match[1], classes, match[1])
                classes[match[1]] = path
        uids = {}
        for pattern, suffix in [("*.uid", ".uid"), ("*.import", ".import")]:
            for path in tracked_non_dev_files(pattern):
                text = read(path)
                uid = text.strip() if suffix == ".uid" else re.search(r'^uid="([^"]+)"', text, re.M)[1]
                self.assertNotIn(uid, uids, uid)
                uids[uid] = path[:-len(suffix)]
        pending = list(roots)
        visited = set()
        while pending:
            path = pending.pop()
            if path in visited:
                continue
            visited.add(path)
            self.assertFalse(is_dev_path(path), path)
            self.assertTrue((ROOT / path).is_file(), path)
            if not path.endswith((".tscn", ".tres", ".gd", ".gdshader", ".godot")):
                continue
            text = read(path)
            references = re.findall(r'res://([^"\s)]+)', text)
            pending.extend(references)
            for uid in re.findall(r'uid://[a-z0-9]+', text):
                self.assertIn(uid, uids, f"Unresolved tracked UID in {path}: {uid}")
                pending.append(uids[uid])
            if path.endswith(".gd"):
                code = "\n".join(line.split("#", 1)[0] for line in text.splitlines())
                pending.extend(target for name, target in classes.items()
                               if re.search(rf'\b{name}\b', code))
            if path.endswith(".tscn"):
                ext = geometry.blocks(text, "ext_resource")
                sub = geometry.blocks(text, "sub_resource")
                self.assertEqual(int(re.search(r"load_steps=(\d+)", text)[1]),
                                 1 + len(ext) + len(sub), path)
                for kind, entries in [("ExtResource", ext), ("SubResource", sub)]:
                    ids = [re.search(r'\bid="([^"]+)"', h)[1] for h, _ in entries]
                    self.assertEqual(len(ids), len(set(ids)), path)
                    self.assertTrue(set(re.findall(rf'{kind}\("([^"]+)"\)', text)) <= set(ids), path)
        for script in ["scenes/main/main_v2.gd", "scenes/world/v2_room_arrival.gd",
                       "scenes/world/stationary_machine_presentation.gd",
                       "scenes/interaction/v2_extractor_recovery.gd",
                       "scenes/interaction/v2_smelter_recovery.gd",
                       "scenes/interaction/v2_fabricator_recovery.gd"]:
            uid = read(script + ".uid").strip()
            self.assertRegex(uid, r"^uid://[a-z0-9]+$")
            self.assertEqual(sum(p.read_text().strip() == uid
                                 for p in (ROOT / path for path in tracked_non_dev_files("*.gd.uid"))), 1)

    def test_resource_graph_rejects_dev_paths_and_unknown_uids(self):
        source_read = read
        cases = [("scenes/main/main.gd", 'res://scenes/dev/forbidden.tscn'),
                 ("scenes/main/main.gd", 'res://SCENES\\DEV\\forbidden.gd'),
                 ("scenes/main/main.gd", 'uid://unmappeddevfixture'),
                 ("inventory/inventory_state.gd", 'res://scenes/dev/forbidden.tscn')]
        for source, edge in cases:
            original = source_read(source)
            with self.subTest(source=source, edge=edge), patch(__name__ + ".read", side_effect=lambda path:
                    original + f'\nconst INVALID = preload("{edge}")\n'
                    if path == source else source_read(path)):
                with self.assertRaisesRegex(AssertionError,
                        "Unresolved tracked UID" if edge.startswith("uid://") else "forbidden"):
                    self.assert_resource_graph(["scenes/main/main.tscn"])

    def test_routes_resolve_to_real_wrapper_identity_and_markers(self):
        expected = [(PRIMARY, "Maintenance", MAINTENANCE, "FromInterior"),
                    (MAINTENANCE, "Interior", PRIMARY, "FromMaintenance"),
                    (PRIMARY, "Exterior", EXTERIOR, "FromShip")]
        for source, door, destination, spawn in expected:
            nodes = merged_nodes(source)
            body = nodes[f"Doorways/{door}"][1]
            self.assertIn(f'destination_scene = "res://{destination}"', body)
            self.assertIn(f'destination_spawn = &"{spawn}"', body)
            self.assertIn(f"Spawns/{spawn}", merged_nodes(destination))
            self.assertIn("GroundObjects", merged_nodes(destination))
            self.assertNotIn("scene_file_path =", read(source))
            if door == "Exterior":
                self.assertIn("presentation = 1", body)
            else:
                self.assertNotIn("presentation =", body)  # Existing QUICK_FADE default.
        host = read("scenes/main/main_v2.gd")
        self.assertIn(f'preload("res://{PRIMARY}")', host)
        self.assertIn(f'EXTERIOR_SCENE: String = "res://{EXTERIOR}"', host)
        self.assertIn('worlds.child_entered_tree.connect(_configure_exterior_return)', host)
        configure = geometry.function(host, "_configure_exterior_return")
        self.assertIn('world.scene_file_path != EXTERIOR_SCENE', configure)
        self.assertIn('world.get_node("GroundObjects/Hatch")', configure)
        self.assertIn('hatch.set("destination_scene", INITIAL_WORLD.resource_path)', configure)
        self.assertIn('hatch.set("destination_spawn", &"FromPlanet")', configure)
        legacy_hatch = merged_nodes(EXTERIOR)["GroundObjects/Hatch"][1]
        self.assertIn('source_scene = "res://scenes/world/planet_exterior.tscn"', legacy_hatch)
        self.assertIn('destination_scene = "res://scenes/world/ship_interior.tscn"', legacy_hatch)
        self.assertIn('destination_spawn = &"FromPlanet"', legacy_hatch)

    def test_one_main_owner_and_initialization_order(self):
        host_scene = read("scenes/main/main_v2.tscn")
        self.assertIn('path="res://scenes/main/main.tscn"', host_scene)
        self.assertEqual(len(geometry.nodes(host_scene)), 2)
        self.assertIn("display_enabled = false", host_scene)
        host = read("scenes/main/main_v2.gd")
        self.assertTrue(host.startswith('extends "res://scenes/main/main.gd"'))
        for script in [host, read("scenes/world/v2_room_arrival.gd")]:
            self.assertNotRegex(script, r"func _(?:unhandled_)?(?:key_)?input\(")
            self.assertNotIn("Input.", script)
        startup = geometry.function(host, "_enter_tree")
        self.assertLess(startup.index("worlds.remove_child"), startup.index("worlds.add_child"))
        self.assertNotIn("initialize()", startup)
        ready = geometry.function(host, "_ready")
        self.assertLess(ready.index("super._ready()"), ready.index("transitions.player.global_position"))
        self.assertNotIn("$Dave", ready.replace("# Parent @onready captures DialogueUI while Dave is still Main/Dave.", ""))
        parent = read("scenes/main/main.gd")
        self.assertIn('@onready var _dialogue: DialogueUI = $Dave/DialogueUI', parent)
        self.assertLess(parent.index("$SceneTransitions.initialize()"),
                        parent.index("_dialogue.conversation_completed.connect"))
        for path in [PRIMARY, MAINTENANCE]:
            text = read(path)
            self.assertIn("scale = Vector2(1.25, 1.25)", text)
            self.assertIn("scale = Vector2(0.8, 0.8)", geometry.nodes(text)["GroundObjects"][1])
            self.assertNotIn('name="Dave"', text)
            for forbidden in ["rack", "request_transition"]:
                self.assertNotIn(forbidden, text.lower())
            if path == MAINTENANCE:
                self.assertNotIn("computer_opening", text)

    def test_computer_reuses_legacy_contract_without_progression_authority(self):
        text = read(PRIMARY)
        nodes = geometry.nodes(text)
        header, body = nodes["ComputerInteraction"]
        self.assertIn('type="Area2D" parent="."', header)
        self.assertIn('collision_layer = 1', body)
        self.assertIn('collision_mask = 0', body)
        self.assertIn('monitoring = false', body)
        self.assertIn('interaction_point = Vector2(0, 0)', body)
        self.assertNotIn('interaction_enabled = false', body)
        legacy = geometry.nodes(read("scenes/world/ship_interior.tscn"))["GroundObjects/WestObstacle"][1]
        for property_name in ["interaction_prompt", "inspection_response"]:
            value = re.search(rf'^{property_name} = .*$', legacy, re.M)[0]
            self.assertIn(value, body)
        for property_name, path in [("script", "scenes/interaction/world_interactable.gd"),
                                    ("conversation", "dialogue/computer_opening.tres")]:
            resource_id = re.search(rf'{property_name} = ExtResource\("([^"]+)"\)', body)[1]
            self.assertTrue(any(f'id="{resource_id}"' in h and f'path="res://{path}"' in h
                                for h, _ in geometry.blocks(text, "ext_resource")))
        self.assertNotIn('[connection ', text)
        self.assertIn('conversation_id = &"computer_opening"', read("dialogue/computer_opening.tres"))
        main = read("scenes/main/main.gd")
        self.assertEqual(main.count('_dialogue.conversation_completed.connect(_on_conversation_completed)'), 1)
        completed = geometry.function(main, "_on_conversation_completed")
        self.assertIn('conversation_id == &"computer_opening"', completed)
        self.assertIn('_objectives.activate_objective(&"restore_computer")', completed)
        dialogue = read("scenes/ui/dialogue_ui.gd")
        self.assertNotIn('conversation_completed.emit', geometry.function(dialogue, "dismiss"))
        self.assertIn('conversation_dismissed.emit', geometry.function(dialogue, "dismiss"))
        self.assertIn('_objectives.activate_objective(&"restore_computer")',
                      geometry.function(main, "_on_ferrite_discovered"))

    def test_computer_front_approach_range_and_solid_clearance(self):
        nodes = geometry.nodes(read(PRIMARY))
        target = geometry.vectors(nodes["ComputerInteraction"][1])[0]
        size = geometry.vectors(geometry.resources(read(PRIMARY))["ComputerInteraction"][1])[0]
        self.assertEqual(target, (0, -214))  # Owner-accepted provisional placement.
        native = read("scenes/world/ship_interior_v2.tscn")
        shapes = geometry.resources(native)
        base = shapes["Footprint_ComputerBase"][1]
        raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', base)[1].split(',')))
        front = max(raw[1::2])
        self.assertGreater(target[1] - size[1]/2, front)
        # Dave detector/feet center is 10 world units above ground. Sample the
        # straight walk from Initial toward Computer without crossing its base.
        for ground_y in range(80, -198, -1):
            center = (0, ground_y - 8)
            for key, (header, body) in shapes.items():
                if key == "Segment_MaintenanceDoorBarrier":
                    continue
                if 'type="SegmentShape2D"' in header:
                    self.assertGreater(geometry.segment_distance(center, *geometry.vectors(body)), 8)
                elif 'type="ConvexPolygonShape2D"' in header:
                    raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                    polygon = list(zip(raw[::2], raw[1::2]))
                    self.assertFalse(geometry.point_in_polygon(center, polygon))
                    self.assertGreater(min(geometry.segment_distance(center, a, b)
                                           for a, b in zip(polygon, polygon[1:] + polygon[:1])), 8)
                    # For the in-range front approach the ray is vertical at x=0.
                    # No polygon intersects this x except Computer, behind target.
                    if min(raw[::2]) <= 0 <= max(raw[::2]):
                        self.assertLessEqual(max(raw[1::2]), front)
                elif 'type="CapsuleShape2D"' in header:
                    self.assertGreater(abs(center[0] - (-387)), 18 + 8)
            if ground_y <= -111:
                self.assertLessEqual(math.dist(center, target) * 1.25, 120)
                self.assertGreater(center[1], target[1])
        dave = read("scenes/player/dave.tscn")
        self.assertIn('radius = 120.0', geometry.resources(dave)["CircleShape2D_interaction"][1])
        self.assertIn('collision_mask = 1', geometry.nodes(dave)["InteractionDetector"][1])
        detector = read("scenes/player/interaction_detector.gd")
        self.assertIn('query.collide_with_areas = true', detector)
        self.assertIn('hit.get("collider") == collider', detector)

    def test_computer_only_world_distance_cap_and_default_preservation(self):
        contract = read("scenes/interaction/world_interactable.gd")
        self.assertIn('@export var max_interaction_distance: float = 0.0', contract)
        body = geometry.nodes(read(PRIMARY))["ComputerInteraction"][1]
        self.assertIn('max_interaction_distance = 45.0', body)
        # P3 adds dormant per-machine caps; legacy Computer still uses defaults.
        scenes = tracked_non_dev_files('scenes/*.tscn')
        overrides = [(path, node) for path in scenes
                     for node, (_, properties) in geometry.nodes(read(path)).items()
                     if re.search(r'^max_interaction_distance =', properties, re.M)]
        self.assertEqual(set(overrides), {(PRIMARY, "ComputerInteraction")} | {
            (MAINTENANCE, f"StationaryMachines/{name}/Interaction")
            for name in ["Extractor", "Smelter", "Fabricator"]})
        refresh = geometry.function(read("scenes/player/interaction_detector.gd"), "_refresh_target")
        cap = ('if body != null and body.max_interaction_distance > 0.0:\n'
               '\t\t\tlimit = minf(limit, body.max_interaction_distance * body.max_interaction_distance)')
        self.assertIn(cap, refresh)
        self.assertIn('body.to_global(body.interaction_point)', refresh)
        self.assertIn('global_position.distance_squared_to(point)', refresh)
        self.assertIn('if distance > limit or distance >= nearest_distance:\n\t\t\tcontinue', refresh)
        self.assertLess(refresh.index(cap), refresh.index('if distance > limit'))
        self.assertLess(refresh.index('if distance > limit'), refresh.index('nearest_distance = distance'))
        # 45 world units = 36 native units at 1.25x, not 45 native units.
        point = (0, -214 * 1.25)
        for dx, dy, eligible in [(0, 45, True), (0, 45.01, False),
                                 (-27, 36, True), (27, 36, True), (27, 36.01, False)]:
            center = (point[0] + dx, point[1] + dy)
            self.assertEqual(math.dist(center, point) ** 2 <= 45.0 ** 2, eligible)

    def test_prompt_and_queued_e_share_fresh_selection_and_line_of_sight(self):
        detector = read("scenes/player/interaction_detector.gd")
        physics = geometry.function(detector, "_physics_process")
        self.assertLess(physics.index('_refresh_target()'), physics.index('if _interaction_requested:'))
        self.assertLess(physics.index('_refresh_target()'), physics.index('dialogue_ui.show_conversation'))
        input_handler = geometry.function(detector, "_unhandled_input")
        self.assertIn('_interaction_requested = true', input_handler)
        self.assertNotIn('show_conversation', input_handler)
        refresh = geometry.function(detector, "_refresh_target")
        self.assertLess(refresh.index('_target = null'), refresh.index('for result in'))
        self.assertIn('PhysicsRayQueryParameters2D.create(global_position, point, collision_mask)', refresh)
        self.assertIn('query.collide_with_areas = true', refresh)
        self.assertIn('if hit.get("collider") == collider:', refresh)
        self.assertIn('prompt = _target.interaction_prompt', refresh)
        self.assertIn('interaction_ui.set_prompt(prompt)', refresh)

    def test_spawn_and_exterior_approach_clearance(self):
        native = read("scenes/world/ship_interior_v2.tscn")
        nodes = merged_nodes(PRIMARY)
        shapes = geometry.resources(native)
        # Same radius-10 world feet circle as production Dave: native radius 8,
        # center 8 above the ground origin at the 1.25x room scale.
        positions = [geometry.vectors(nodes[f"Spawns/{name}"][1])[0]
                     for name in ["Initial", "FromPlanet", "FromMaintenance"]]
        positions += [(-13, y) for y in range(281, 340)]
        for x, y in positions:
            center = (x, y - 8)
            for key, (header, body) in shapes.items():
                if key == "Segment_MaintenanceDoorBarrier":
                    continue
                if 'type="SegmentShape2D"' in header:
                    self.assertGreater(geometry.segment_distance(center, *geometry.vectors(body)), 8, (center, key))
                elif 'type="ConvexPolygonShape2D"' in header:
                    raw = list(map(float, re.search(r'PackedVector2Array\(([^)]+)\)', body)[1].split(',')))
                    polygon = list(zip(raw[::2], raw[1::2]))
                    self.assertFalse(geometry.point_in_polygon(center, polygon), (center, key))
                    self.assertGreater(min(geometry.segment_distance(center, a, b)
                                           for a, b in zip(polygon, polygon[1:] + polygon[:1])), 8, (center, key))
                elif 'type="CapsuleShape2D"' in header:
                    radius = float(re.search(r'radius = ([\d.]+)', body)[1])
                    height = float(re.search(r'height = ([\d.]+)', body)[1])
                    px, py = geometry.vectors(nodes["CollisionContent/PortContainer"][1])[0]
                    self.assertGreater(geometry.segment_distance(center, (px, py-height/2+radius),
                                                                 (px, py+height/2-radius)), 8+radius)
        # Both Primary arrivals and start are outside both thresholds.
        for x, y in positions[:3]:
            for door, origin, size in [("Maintenance", (-552, -39.5), (16, 105)),
                                       ("Exterior", (-13, 323), (170, 16))]:
                distance = math.hypot(max(abs(x-origin[0])-size[0]/2, 0),
                                      max(abs(y-8-origin[1])-size[1]/2, 0))
                self.assertGreater(distance, 8, (x, y, door))
        for path, name, facing in [(PRIMARY, "Initial", 1), (PRIMARY, "FromPlanet", 1),
                                   (PRIMARY, "FromMaintenance", 3), (MAINTENANCE, "FromInterior", 2)]:
            self.assertIn(f"metadata/facing = {facing}", merged_nodes(path)[f"Spawns/{name}"][1])

    def test_shared_inventory_presentation_preserved(self):
        path = "scenes/ui/item_presentation.gd"
        actual = (ROOT / path).read_bytes().replace(b"\r\n", b"\n")
        self.assertEqual(hashlib.sha256(actual).hexdigest(), HOTBAR_ITEM_PRESENTATION_SHA256)

    def test_hotbar_allowance_restores_exact_pre_feature_bytes(self):
        # Prove each allowance recovers the entire pre-feature file, including
        # gameplay not touched by this feature. The old P8 checks still run too.
        for path in HOTBAR_REPLACEMENTS:
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{HOTBAR_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_approved_hotbar_changes(path, read(path)), before)

    def test_hotbar_allowance_rejects_changed_duplicate_and_unrelated_edits(self):
        for path, changes in HOTBAR_REPLACEMENTS.items():
            original = read(path)
            for approved, _historical in changes:
                with self.subTest(path=path, edit=approved[:60]):
                    with self.assertRaises(AssertionError):
                        without_approved_hotbar_changes(path, original.replace(approved, "CHANGED\n", 1))
                    with self.assertRaises(AssertionError):
                        without_approved_hotbar_changes(path, original + approved)
            # Unrelated edits survive normalization and therefore still fail the
            # full-file comparison; they cannot be hidden by the allowance.
            self.assertNotEqual(without_approved_hotbar_changes(path, original + "UNRELATED\n"),
                                without_approved_hotbar_changes(path, original))

    def test_protected_existing_code_art_and_sidecars_unchanged(self):
        # Existing code, project settings, assets and sidecars are protected
        # against post-P6, allowing P8 startup and exactly the approved retirement.
        # Compare working bytes with baseline blobs (normalize text CRLF only,
        # never binary assets).
        files = subprocess.check_output(["git", "ls-tree", "-r", "--name-only", P8_BASE,
                                         "assets", "scenes", "construction", "dialogue",
                                         "inventory", "objectives", "world", "project.godot"],
                                        cwd=ROOT, text=True).splitlines()
        self.assertEqual(len(APPROVED_DEV_RETIREMENT), 38)
        self.assertEqual({path for path in files if is_dev_path(path)}, APPROVED_DEV_RETIREMENT)
        proc = subprocess.Popen(["git", "cat-file", "--batch"], cwd=ROOT,
                                stdin=subprocess.PIPE, stdout=subprocess.PIPE)
        try:
            for path in files:
                if path in APPROVED_DEV_RETIREMENT:
                    continue
                proc.stdin.write(f"{P8_BASE}:{path}\n".encode())
                proc.stdin.flush()
                header = proc.stdout.readline().split()
                expected = proc.stdout.read(int(header[2]))
                self.assertEqual(proc.stdout.read(1), b"\n")
                actual = (ROOT / path).read_bytes()
                if path in B1_INVENTORY_SHA256:
                    actual = actual.replace(b"\r\n", b"\n")
                    self.assertEqual(hashlib.sha256(actual).hexdigest(), B1_INVENTORY_SHA256[path], path)
                    continue
                if path in B1_REPLACEMENTS or path in HOTBAR_REPLACEMENTS:
                    actual = without_approved_b1_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path == "project.godot":
                    actual = actual.replace(b"\r\n", b"\n")
                    expected = expected.replace(b"\r\n", b"\n")
                    approved = b'run/main_scene="res://scenes/main/main_v2.tscn"'
                    baseline = b'run/main_scene="res://scenes/main/main.tscn"'
                    pattern = rb"^[ \t]*run/main_scene[ \t]*=.*$"
                    self.assertEqual(re.findall(pattern, actual, re.M), [approved])
                    self.assertEqual(re.findall(pattern, expected, re.M), [baseline])
                    actual = actual.replace(approved, baseline, 1)
                if not path.endswith(".png"):
                    expected = expected.replace(b"\r\n", b"\n")
                    actual = actual.replace(b"\r\n", b"\n")
                self.assertEqual(hashlib.sha256(actual).digest(), hashlib.sha256(expected).digest(), path)
        finally:
            proc.stdin.close()
            proc.stdout.close()
            proc.wait()


if __name__ == "__main__":
    unittest.main()
