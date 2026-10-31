"""Read-only scene/route/geometry checks; no Godot or gameplay code execution."""

import hashlib
import math
import posixpath
import re
import subprocess
import unittest
from unittest.mock import patch
from static_weathered_earth_test import TERRAIN_SHA256, preserved_terrain_bytes

import static_automatic_transitions_test as geometry
from static_automatic_transitions_test import ROOT, PRIMARY, MAINTENANCE, EXTERIOR, read as raw_read, merged_nodes


# Live post-P6 / pre-P8 main verified for cutover; never follow a moving ref.
P8_BASE = "e14703e64aef961f18feba8a616acec00c4f069e"

# Proposed Smelter presentation allowance: owner review required before Native use.
# Pin the exact candidate bytes and restore PR #85 main before older checks.
# No preservation path is exempted and all historical hashes remain unchanged.
SMELTER_PILOT_BASE = "cb6304f4fa81c2510d056c63c21e6a8ce72bf6b6"
SMELTER_PILOT_SHA256 = {
    # Provisional serial-import candidate; owner review required before Native.
    "project.godot": "993aa7cf7ec6403720094f43f5b3522f9ee3a8e4557bf81e95b93a1fd70e4b96",
    "assets/environment/maintenance_bay_v2/machines/smelter_stationary.png.import": "56281b1985e2f862b229695b7a713780419ca32d2f7550239065c1b07cc0d225",
    # Width refinement candidate; renewed owner review before Native use.
    "scenes/ui/machine_ui.gd": "e7f86dc75e5d3b7f1ab9fd65e966872bf5a1d70f89b76c2a9b699452f0ac9a68",
    "scenes/ui/machine_ui.tscn": "8664835ab0acf506adaebe758db36af013fbd13d48506222d5dcb32a3bf8e486",
}

# Proposed Extractor pilot allowance: owner review required before Native use.
# Pin complete LF-normalized candidate files, then restore immutable main bytes
# for every existing historical comparison. No file or directory is exempted.
EXTRACTOR_PILOT_BASE = "17c67d8c4bbab3a799686c30f341b1f602231640"
EXTRACTOR_PILOT_SHA256 = {
    # Option A: only mipmaps/generate false -> true; source PNG stays protected.
    "assets/environment/maintenance_bay_v2/machines/extractor_stationary.png.import": "0ff7f4f219cafef7aba8a63a801838fcfdb1a6ffa12765fcb806c4c8b414d6d1",
    "scenes/main/main.tscn": "3f703899f344f969df442886a0ccd4292968aea9d1c0dc4007606fbc210b8f73",
    "scenes/ui/machine_ui.gd": "614fea11ecbd3ec3c01d5bd723ea15ee309558bb5f407ac0a45d07c484a8e5b6",
    "scenes/ui/machine_ui.tscn": "6a2a86d358a4ce0c7dca7bc4c15ba32ca2b1ed33df6efc767fe9fd7b31b67911",
    "scenes/ui/objective_tracker.gd": "19424588dde32237a9dd078414d39355516128844889598dae9aabe7b81312c3",
}

# Proposed UI scaling presentation bytes, pending owner review before Native.
# Normalize these exact files to the immutable pre-scaling main, then run all
# existing B1/hotbar/P8 preservation comparisons unchanged. No path exemption.
UI_SCALING_BASE = "2906ba9b0409658ba4b28b397a3190cd2c69c524"
UI_SCALING_SHA256 = {
    "construction/construction_controller.tscn": "4b731249cded15efada5dd5795d6c35812f106f0bac57b2cecc492edce151e5d",
    "scenes/main/main.tscn": "4133bbc7342d8c34b476cf2b17e4a742883f0b0af6a052d11a3c35b1363f89cd",
    "scenes/ui/dialogue_ui.tscn": "d9fd226b7069a507a2f132141acaff427329dc21a3022d523ae60e16f90f285e",
    "scenes/ui/hotbar_ui.gd": "645f79c12953582bdcc38ca3ea1603304e6454286be62362a7ea4f17970a32e4",
    "scenes/ui/hotbar_ui.tscn": "058642f05f0193145c09b23d84e59c5f42a251dbf3a136e63dfc29ac61f0910a",
    "scenes/ui/interaction_ui.tscn": "ed23b1986121186658cc31819616c6fb4cf9d9a4b30c12a65caa836707cb6550",
    "scenes/ui/inventory_ui.gd": "90f7a122a28d14668eaea6e5243566e6b609ddffea5b9ad8a958509777fd76cf",
    "scenes/ui/inventory_ui.tscn": "2160388cf6c87ed2ce6226ae5d10a66c87face09ab851b855e9951b176adfad4",
    "scenes/ui/machine_ui.tscn": "348f46ce3a42076bfc676b55605c728e3f66cd6782241cfdd819be9bffaae630",
    "scenes/ui/musing_ui.tscn": "655671aa5e032ba9472cda1e41b7b477fc56a71c42095643f98b9e1c598d31ec",
    "scenes/ui/objective_tracker.tscn": "17c648701073002421aeaaf0c67c72fa0cd59ab55231f99dd1c186e88b567123",
}

# B1 inventory and hotbar context-menu integration replace exactly these UI files.
# Freeze normalized candidate bytes rather than exempting them from preservation.
# B2 nine-patch inventory scene candidate requires owner review before Native execution.
B1_INVENTORY_SHA256 = {
    "scenes/ui/inventory_ui.gd": "9a9e68709e46ca84bddfc0f0e552e2218d1b2417f3be3e76057094b28d1d6817",
    "scenes/ui/inventory_ui.tscn": "ffa02b016227dab6cc54a709af3ccf671c94ea28d8b675274f191be2f22ce601",
    "scenes/ui/machine_ui.gd": "7ba1d9386cc84891c947647077f6836dd940933c74bbdd782bbef3b3c6a8ce2a",
    "scenes/ui/machine_ui.tscn": "fd1673368a5dfc184d7b19d2eabfe04a8e1c9843f0064edb45f0fe62707c6739",
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


# Proposed Fabricator presentation bytes; owner approval required before Native.
# Exact LF-normalized files restore PR #86 main for all historical assertions.
# Shared gauge amendment remains proposed pending renewed owner review before Native.
FABRICATOR_BASE = 'cf4536eeef5c64b057b7951ad0ae554332d25df6'
FABRICATOR_SHA256 = {'scenes/ui/cycle_gauge.gd': '20b7cc41c5922c0d798b15b5974e8af6875860aac43d48a76dbdfb363d80317d',
 'scenes/ui/machine_ui.gd': '581d7d11d7b1da02d7d9a4b7c4b48b65a183e6bd0c55e4825bdf64474b1baa56',
 'scenes/ui/machine_ui.tscn': '055bc45d1aaac64eaeb9d34f21c0a7aef1d1fa1f5b455cbd3f0b91fcd57110be',
 'assets/environment/maintenance_bay_v2/machines/fabricator_stationary.png.import': 'e76f75e09b9dc98dc7348f321b7f0bc2665da73c45588e8e76c2dacfcc16f4f8'}


# Owner approved these exact UTF-8/LF candidates, including the compact footer
# and visible/noninteractive hotbar refinement, on 2026-10-30. Restore the
# immutable PR #88 bytes before older comparisons; no historical hash changes.
CONVERSATION_BASE = "8ec5e6ca8ba424b6c4ba2973ebbab9882e202422"
CONVERSATION_SHA256 = {
    "scenes/ui/dialogue_ui.gd": "ab7db168b7c5aa225305614e8fa974d73dd031abdf525f3ec1a00e7f780107e2",
    "scenes/ui/dialogue_ui.tscn": "bddaefb4e36ed220e7fc018915c6518605b5dc3a109c81a660eede6b56499390",
    "scenes/ui/hotbar_ui.gd": "08a2c44c4dd68836001eff43acbddd44a4bdcbd2aef252d55f9d5d6855674583",
    "scenes/ui/inventory_ui.gd": "45c56d972b694137a2df57f38ed806d56e3f13bced38e755b52ef8f6cfde4b30",
}


# Owner approved the initial musing bytes/amendment on 2026-10-30. The
# owner-approved layout uses maximum width 540 and body size 16. The border
# color (0.46, 0.60, 0.62, 0.88), exact scene hash and preservation amendment
# were separately approved by the owner on 2026-10-30.
# Retain PR #89 and all older comparisons.
# Native remains blocked by the unchanged font staging scope.
MUSING_BASE = "a03057408cbee6301b42e00a2a26c01e25d3c8ac"
MUSING_SHA256 = {
    "scenes/ui/musing_ui.gd": "6eb048c21b625ba9d945492ca38f9357b2ba5393f0c7fdf39222c706930bf4f7",
    "scenes/ui/musing_ui.tscn": "3ee90563975f5e0d161059e0d041b74cd1e302c18eb1442ca7da8afc4bfac887",
}


# Owner approved only the Italic font/sidecar staging expansion on 2026-10-30.
# Pin the complete reviewed controls, then retain all prior comparisons.
ITALIC_STAGING_BASE = "081630c07938a5a71e0b47976324d2cdbac7ea0c"
ITALIC_STAGING_SHA256 = {
    "tools/run-local-tests.ps1": "6fbb3fd6b4a9478775d15f01cb33628a29e0629eef0146acebdd32c3898114c5",
    "docs/LOCAL_TESTING.md": "7ff3eb595b2a8528051ec798e1755ab302a34d3ae36ed458be2e46cf77921afc",
}


# Ferrite artwork candidate: review this preservation amendment before Native.
# Pin complete candidate files, restore immutable main for older comparisons,
# and retain every historical hash. No runner/policy or command scope changes.
FERRITE_ICONS_BASE = "74687ba6b1fa35af198e8fc3321a073935f65c1d"
FERRITE_ICONS_SHA256 = {
    "scenes/ui/item_presentation.gd": "7c695d80588d4c272f25a043c93231bf83757708267455b06be5af1a0bbfe068",
    "construction/recipes/ferrite_plate.tres": "9122fee113937ab561101ddeb0624877a38b2289f7b7307b0ad8c6ff16209614",
    "construction/recipes/ferrite_rod.tres": "0e530192ce484d485cd6a9fa2be79e51987d30173fd350793a60f38d4ec2aec4",
}
FERRITE_ART_SHA256 = {
    "ferrite_ore": "8604e53c8a33d349c8335c35497aaaea7deaf083ef56724f41c2f6c7d87fdbd5",
    "ferrite_ingot": "672e48eef6ac2ac8852fdaebd57bca3c7ffff119dad82def02bd08fec5b65335",
    "ferrite_plate": "8bb7ed820b3f25d0cbe9ba8053311fc83f5e666611d82fdff9b1bc26151ebc64",
    "ferrite_rod": "be51d5a195e4df6c0d83d618e79ea3c72e500faafa68cc47c40b8caaa8f3b767",
}


# PR #91 owner-review candidate. Restore the initial PR's exact files before
# historical assertions; no earlier hash or comparison is replaced or skipped.
# This expanded preservation amendment requires review before any Native run.
FERRITE_REFINEMENT_BASE = "6cb185b916ddb7fe90f67a6c59ad68c5c1e6892b"
FERRITE_REFINEMENT_SHA256 = {
    "scenes/ui/item_presentation.gd": "89e1c205a3c3b284a49b6f6df293cf700c0fc5b875083edb8e0ea58df4eb8f10",
    "scenes/ui/inventory_ui.gd": "2accafdaf65fea53aac39af748a62a8efeab2a67ff953af8f2bd56c3e1816622",
    "scenes/ui/inventory_ui.tscn": "7861c43c68fa62ad24337552dbceef81acee4a7e36ef4367991a495a0dff0fa6",
    "scenes/ui/recipe_card_content.gd": "b4acf50fc32dd07c3bafe119bb0960faafc1abd344d2f138745dc15c01ce0f56",
    "scenes/ui/extractor_inspection.gd": "9efc079d16ff444cdefa6883ccaffa04c5d13463c92eac671c915d140c45ce7f",
    "scenes/ui/smelter_inspection.gd": "b76db5279ee3491d274431a98c340930b891bed6f3ae40bd0172b137d838b05a",
    "scenes/ui/fabricator_inspection.gd": "a3100624a8a63adb9fe9eb779ad650e959a92a9a554898347d398cb130b36a32",
    "scenes/ui/fabricator_inspection.tscn": "346b47d833bd29b5a0b3ced08d60f2ad16aebc5b6ceecbec017b03401083308b",
}
# Existing untracked sidecars supplied by the owner's local import. Only the
# mipmap parameter changes; LF-normalized hashes protect original UIDs/metadata.
FERRITE_IMPORT_ORIGINAL_SHA256 = {
    "ferrite_ore": "7a54f0f00e02d69c1ea98271f0125eb64623bfac4b1565f26faa30488368df75",
    "ferrite_ingot": "96a9c6442d273112cf74e501ca1b2d78c32d04487281f6c8d0e9f7ab568facb1",
    "ferrite_plate": "b401d8eb1ed3a97f7405d3ab968152ecac6f7d1c8c1e4e18eeb19453aaf7e786",
    "ferrite_rod": "1b5a69a51b530e3ad5a6fda86f2619d3d381e09fb0a37aba8dbd6efa1e0181e0",
}


# Final owner corrections: preserve all previous candidate hashes by restoring
# the exact second PR revision before its assertions. Review before Native.
FERRITE_FINAL_BASE = "5788c67dc46a2f2eb925045ceae81e0f9f457d6a"
FERRITE_FINAL_SHA256 = {
    "scenes/ui/inventory_ui.gd": "0f1ad645bc5bdcce2a067c58610db061d2af47f50734826ea8e5875dc17d35f8",
    "scenes/ui/extractor_inspection.gd": "edbc8815730e719aee991689b78b8915ad7b80acbbaaaba3ac0ea24774fd7567",
    "scenes/ui/smelter_inspection.gd": "822b7c77bcc4a6f390e59d227dd4ec269307d1e4e1860594aa3691db1d2f49d6",
    "scenes/ui/fabricator_inspection.gd": "d530aaac53804c5a6693ce3da3e67aaf1f86c988612cd85491b4fbd291fc9f1e",
}


# Machine icon/layout candidate: owner review required before any Native use.
# Pin complete LF-normalized files, restoring merged PR #91 for every older
# comparison. No historical hashes, assertions or protected paths are removed.
MACHINE_ICONS_BASE = "4072c516c6f73728e7f7a190632a359021e6ce9c"
MACHINE_ICONS_SHA256 = {
    "scenes/ui/item_presentation.gd": "4e405e6da4a63195214602bd42f9e447a4eb48e49443b644ceaa33d0aab8121d",
    "scenes/ui/inventory_ui.gd": "9f0ba955d4fec84dc66996fdd8a151287b63274409e11167e16ddfb89f4148b6",
    "scenes/ui/inventory_ui.tscn": "6b9fcdc90f20b2188c08bb33bbe570e4fa82011f91a08b1fb82fa7ff150752d7",
    "scenes/ui/hotbar_ui.gd": "7fc8e27961d87b646ac4e41a7d58246ce7aea4bd34146a9f74bfeca9ca343e1a",
    "scenes/ui/hotbar_ui.tscn": "9eb1559dff162db83d7c5d8d9547ab647c6659558691e89bf07c84824fce48a8",
}


# Owner Decisions 19/20: review these three exact layout candidates before Native.
# Restore the initial PR #92 files before its existing five pins and every older
# comparison. No earlier digest/assertion or unrelated path allowance changes.
MACHINE_LAYOUT_BASE = "6eb83eaae51850b1954ba20eef21a02ab695f6f0"
MACHINE_LAYOUT_SHA256 = {
    "scenes/ui/inventory_ui.gd": "24fa2621893126623693185d79fb96c364b3a139ca0ab599dbdff51d55433480",
    "scenes/ui/hotbar_ui.gd": "b0515998b57f11a89e6feed4771883943d83c64083a3d4f5eac52e94b982a0b3",
    "scenes/ui/hotbar_ui.tscn": "6848bb90a248b7b748e4c527b0d1255269de369ea7685790428eb8c18c882331",
}


def without_machine_layout_changes(path, text):
    if path not in MACHINE_LAYOUT_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != MACHINE_LAYOUT_SHA256[path]:
        raise AssertionError(f"Missing or modified machine layout candidate bytes: {path}")
    return subprocess.check_output(["git", "show", f"{MACHINE_LAYOUT_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_machine_icon_changes(path, text):
    text = without_machine_layout_changes(path, text)
    if path not in MACHINE_ICONS_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != MACHINE_ICONS_SHA256[path]:
        raise AssertionError(f"Missing or modified machine icon candidate bytes: {path}")
    return subprocess.check_output(["git", "show", f"{MACHINE_ICONS_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def machine_baseline_read(path):
    return without_machine_icon_changes(path, raw_read(path))


def without_ferrite_final_changes(path, text):
    if path not in FERRITE_FINAL_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != FERRITE_FINAL_SHA256[path]:
        raise AssertionError(f"Missing or modified final Ferrite candidate bytes: {path}")
    return subprocess.check_output(["git", "show", f"{FERRITE_FINAL_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_ferrite_refinement_changes(path, text):
    text = without_machine_icon_changes(path, text)
    text = without_ferrite_final_changes(path, text)
    if path not in FERRITE_REFINEMENT_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != FERRITE_REFINEMENT_SHA256[path]:
        raise AssertionError(f"Missing or modified Ferrite refinement candidate bytes: {path}")
    return subprocess.check_output(["git", "show", f"{FERRITE_REFINEMENT_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def read(path):
    # Historical tests retain their original view only after full-file pinning.
    # New refinement assertions below explicitly use raw_read for working bytes.
    return without_ferrite_refinement_changes(path, raw_read(path))


def without_ferrite_icon_changes(path, text):
    if path not in FERRITE_ICONS_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != FERRITE_ICONS_SHA256[path]:
        raise AssertionError(f"Missing or modified Ferrite icon candidate bytes: {path}")
    return subprocess.check_output(["git", "show", f"{FERRITE_ICONS_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_italic_staging_changes(path, text):
    if path not in ITALIC_STAGING_SHA256:
        return text
    if hashlib.sha256(text.encode()).hexdigest() != ITALIC_STAGING_SHA256[path]:
        raise AssertionError(f"Missing or modified approved italic staging bytes: {path}")
    return subprocess.check_output(["git", "show", f"{ITALIC_STAGING_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_musing_changes(path, text):
    if path not in MUSING_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != MUSING_SHA256[path]:
        raise AssertionError(f"Missing or modified candidate musing bytes: {path}")
    return subprocess.check_output(["git", "show", f"{MUSING_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_conversation_changes(path, text):
    text = without_musing_changes(path, text)
    if path not in CONVERSATION_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != CONVERSATION_SHA256[path]:
        raise AssertionError(f"Missing or modified approved conversation bytes: {path}")
    return subprocess.check_output(["git", "show", f"{CONVERSATION_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_fabricator_changes(path, text):
    if path not in FABRICATOR_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != FABRICATOR_SHA256[path]:
        raise AssertionError(f"Missing or modified Fabricator presentation bytes pending review: {path}")
    return subprocess.check_output(["git", "show", f"{FABRICATOR_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_smelter_pilot_changes(path, text):
    text = without_fabricator_changes(path, text)
    if path not in SMELTER_PILOT_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != SMELTER_PILOT_SHA256[path]:
        raise AssertionError(f"Missing or modified Smelter pilot bytes pending review: {path}")
    return subprocess.check_output(["git", "show", f"{SMELTER_PILOT_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_extractor_pilot_changes(path, text):
    text = without_smelter_pilot_changes(path, text)
    if path not in EXTRACTOR_PILOT_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != EXTRACTOR_PILOT_SHA256[path]:
        raise AssertionError(f"Missing or modified Extractor pilot bytes pending review: {path}")
    return subprocess.check_output(["git", "show", f"{EXTRACTOR_PILOT_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_approved_ui_scaling_changes(path, text):
    text = without_conversation_changes(path, text)
    text = without_extractor_pilot_changes(path, text)
    if path not in UI_SCALING_SHA256:
        return text
    if hashlib.sha256(text.encode("utf-8")).hexdigest() != UI_SCALING_SHA256[path]:
        raise AssertionError(f"Missing or modified UI scaling bytes pending review: {path}")
    return subprocess.check_output(["git", "show", f"{UI_SCALING_BASE}:{path}"],
                                   cwd=ROOT).decode("utf-8").replace("\r\n", "\n")


def without_approved_hotbar_changes(path, text):
    for approved, historical in HOTBAR_REPLACEMENTS.get(path, []):
        if text.count(approved) != 1:
            raise AssertionError(f"Missing or modified hotbar edit pending review: {path}")
        text = text.replace(approved, historical, 1)
    return text


def without_approved_b1_changes(path, text):
    text = without_approved_ui_scaling_changes(path, text)
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
    def test_fabricator_allowance_restores_main_and_rejects_tampering(self):
        for path in FABRICATOR_SHA256:
            original = read(path)
            before = subprocess.check_output(["git", "show", f"{FABRICATOR_BASE}:{path}"],
                                             cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
            with self.subTest(path=path):
                self.assertEqual(without_fabricator_changes(path, original), before)
                for changed in (original.replace("\n", "\nCHANGED\n", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_fabricator_changes(path, changed)

    def test_smelter_pilot_allowance_restores_main_and_rejects_tampering(self):
        for path in SMELTER_PILOT_SHA256:
            original = read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{SMELTER_PILOT_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_smelter_pilot_changes(path, original), before)
                for changed in (original.replace("\n", "\nCHANGED\n", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_smelter_pilot_changes(path, changed)

    def test_serial_import_candidate_rejects_setting_tampering(self):
        original = read("project.godot")
        setting = "import/use_multiple_threads=false\n"
        self.assertEqual(original.count(setting), 1)
        for changed in (original.replace(setting, "", 1),
                        original.replace(setting, "import/use_multiple_threads=true\n", 1),
                        original.replace(setting, setting * 2, 1),
                        original.replace("[editor]\n", "[wrong_section]\n", 1)):
            with self.assertRaises(AssertionError):
                without_smelter_pilot_changes("project.godot", changed)

    def test_extractor_pilot_allowance_restores_main_and_rejects_tampering(self):
        for path in EXTRACTOR_PILOT_SHA256:
            original = read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{EXTRACTOR_PILOT_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_extractor_pilot_changes(path, original), before)
                for changed in (original.replace("\n", "\nCHANGED\n", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_extractor_pilot_changes(path, changed)

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
        # Text scenes/resources declare their own UID in the file header.
        # It is an identity declaration, not a dependency requiring a sidecar.
        for pattern in ('*.tscn', '*.tres'):
            for path in tracked_non_dev_files(pattern):
                header = re.match(r'^\[(?:gd_scene|gd_resource)\b[^\n]*\]', read(path))
                if header and re.search(r'\buid=', header[0]):
                    match = re.search(r'\buid="(uid://[a-z0-9]+)"', header[0])
                    self.assertIsNotNone(match, f'Malformed resource UID declaration: {path}')
                    uid = match[1]
                    self.assertNotIn(uid, uids, f'Duplicate resource UID: {uid}')
                    uids[uid] = path
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
            for header, _ in geometry.blocks(text, 'ext_resource'):
                uid = re.search(r'\buid="(uid://[a-z0-9]+)"', header)
                target = re.search(r'\bpath="res://([^"]+)"', header)
                if uid:
                    self.assertIn(uid[1], uids, f'Unresolved tracked UID in {path}: {uid[1]}')
                    if target:
                        self.assertEqual(uids[uid[1]], target[1], f'UID/path mismatch in {path}')
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

    def test_resource_graph_registers_text_uids_and_rejects_duplicates(self):
        source_read = read
        source = 'assets/ui/b1_theme.tres'
        fixture = '[gd_resource type="Theme" format=3 uid="uid://testheader1"]\n\n[resource]\n'
        with patch(__name__ + '.read', side_effect=lambda path: fixture if path == source else source_read(path)):
            self.assert_resource_graph([source])
        with patch(__name__ + '.read', side_effect=lambda path:
                   fixture if path in (source, 'assets/ui/machine_actions.tres') else source_read(path)):
            with self.assertRaisesRegex(AssertionError, 'Duplicate resource UID'):
                self.assert_resource_graph([source])

    def test_resource_graph_rejects_uid_path_mismatch_and_unknown_reference(self):
        source_read = read
        source = 'assets/ui/b1_theme.tres'
        header = '[gd_resource type="Theme" format=3 uid="uid://testheader1"]\n\n'
        medium_uid = re.search(r'^uid="([^"]+)"', source_read('assets/fonts/ibm-plex-sans/IBMPlexSans-Medium.ttf.import'), re.M)[1]
        for uid, message in ((medium_uid, 'UID/path mismatch'), ('uid://unknownheader1', 'Unresolved tracked UID')):
            fixture = header + f'[ext_resource type="FontFile" uid="{uid}" path="res://assets/fonts/ibm-plex-sans/IBMPlexSans-Regular.ttf" id="1_font"]\n\n[resource]\n'
            with self.subTest(uid=uid), patch(__name__ + '.read', side_effect=lambda path:
                                            fixture if path == source else source_read(path)):
                with self.assertRaisesRegex(AssertionError, message):
                    self.assert_resource_graph([source])

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
        actual = without_ferrite_icon_changes(path, read(path)).encode("utf-8")
        self.assertEqual(hashlib.sha256(actual).hexdigest(), HOTBAR_ITEM_PRESENTATION_SHA256)

    def test_ferrite_icon_candidate_restores_main_and_rejects_tampering(self):
        for path in FERRITE_ICONS_SHA256:
            original = read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{FERRITE_ICONS_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_ferrite_icon_changes(path, original), before)
                for changed in (original.replace(".png", ".svg", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_ferrite_icon_changes(path, changed)

    def test_ferrite_art_matches_owner_archive_and_active_references(self):
        helper = read("scenes/ui/item_presentation.gd")
        for item_id, expected in FERRITE_ART_SHA256.items():
            with self.subTest(item_id=item_id):
                resource = f"res://assets/items/{item_id}.png"
                raw = (ROOT / "assets/items" / f"{item_id}.png").read_bytes()
                self.assertEqual(hashlib.sha256(raw).hexdigest(), expected)
                self.assertEqual(raw[:8], b"\x89PNG\r\n\x1a\n")
                self.assertEqual(raw[12:16], b"IHDR")
                self.assertEqual(int.from_bytes(raw[16:20], "big"), 256)
                self.assertEqual(int.from_bytes(raw[20:24], "big"), 256)
                self.assertEqual(raw[24:26], b"\x08\x06")  # 8-bit RGBA.
                self.assertIn(f'&"{item_id}": preload("{resource}")', helper)
                if item_id in ("ferrite_plate", "ferrite_rod"):
                    recipe = read(f"construction/recipes/{item_id}.tres")
                    self.assertIn(f'path="{resource}" id="5_icon"', recipe)
                    self.assertNotIn(f"{item_id}.svg", recipe)
        self.assertNotIn(".svg", helper)

    def test_ferrite_refinement_restores_initial_pr_and_rejects_tampering(self):
        for path in FERRITE_REFINEMENT_SHA256:
            original = raw_read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{FERRITE_REFINEMENT_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_ferrite_refinement_changes(path, original), before)
                for changed in (original.replace("\n", "\nCHANGED\n", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_ferrite_refinement_changes(path, changed)
        self.assertEqual(without_ferrite_refinement_changes("unrelated.gd", "sentinel"), "sentinel")

    def test_ferrite_imports_preserve_local_metadata_except_mipmaps(self):
        for item_id, digest in FERRITE_IMPORT_ORIGINAL_SHA256.items():
            with self.subTest(item_id=item_id):
                raw = (ROOT / "assets/items" / f"{item_id}.png.import").read_bytes().replace(b"\r\n", b"\n")
                self.assertEqual(raw.count(b"mipmaps/generate=true"), 1)
                original = raw.replace(b"mipmaps/generate=true", b"mipmaps/generate=false", 1)
                self.assertEqual(hashlib.sha256(original).hexdigest(), digest)
                self.assertIn(b"process/fix_alpha_border=true", raw)
                self.assertIn(b"process/premult_alpha=false", raw)
        for path in ("scenes/ui/inventory_ui.gd", "scenes/ui/recipe_card_content.gd",
                     "scenes/ui/item_presentation.gd"):
            self.assertIn("CanvasItem.TEXTURE_FILTER_LINEAR_WITH_MIPMAPS", machine_baseline_read(path))
        scene = raw_read("scenes/ui/fabricator_inspection.tscn")
        icon = scene.split('[node name="Icon"', 1)[1].split('[node ', 1)[0]
        self.assertIn("texture_filter = 4", icon)

    def test_ferrite_inventory_geometry_and_storage_identity_boundaries(self):
        path = "scenes/ui/inventory_ui.gd"
        inventory = without_ferrite_final_changes(path, machine_baseline_read(path))
        self.assertIn("const SLOT_SIZE := Vector2(50, 50)", inventory)
        self.assertIn("icon.size = Vector2(34, 34)", inventory)
        self.assertIn("icon.position = Vector2(-17, 0)", inventory)
        self.assertIn("quantity.offset_top = -16", inventory)
        self.assertEqual(34, 50 - 16)  # Separate icon and quantity rectangles.
        self.assertIn("offset_right = 484.0", machine_baseline_read("scenes/ui/inventory_ui.tscn"))
        self.assertEqual(8 * 50 + 7 * 4 + 2 * 16, 484 - 24)
        helper = machine_baseline_read("scenes/ui/item_presentation.gd")
        self.assertIn("item != null and quantity > 0 else null", helper)
        self.assertIn("icon.visible = icon.texture != null", helper)
        self.assertIn("Vector2(24, 24)", helper)
        self.assertIn("label.reparent(identity, false)", helper)
        extractor = raw_read("scenes/ui/extractor_inspection.gd")
        self.assertIn("set_material_icon(_material_icon, product, machine.output)", extractor)
        smelter = raw_read("scenes/ui/smelter_inspection.gd")
        self.assertIn("set_material_icon(_input_icon, definition.input_item, machine.input)", smelter)
        self.assertIn("set_material_icon(_output_icon, definition.output_item, machine.output)", smelter)
        fabricator = raw_read("scenes/ui/fabricator_inspection.gd")
        self.assertIn("set_material_icon(row.icon, row.item, stored)", fabricator)
        self.assertIn("set_material_icon(_output_icon, product, machine.output)", fabricator)
        self.assertNotIn("set_material_icon(_output_icon, recipe.output_item", fabricator)
        self.assertIn('else "No stored output"', fabricator)

    def test_final_ferrite_correction_preserves_prior_revision_and_rejects_tampering(self):
        for path in FERRITE_FINAL_SHA256:
            text = machine_baseline_read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{FERRITE_FINAL_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_ferrite_final_changes(path, text), before)
                for changed in (text.replace("\n", "\nCHANGED\n", 1), text + text, text + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_ferrite_final_changes(path, changed)
        self.assertEqual(without_ferrite_final_changes("unrelated.gd", "sentinel"), "sentinel")

    def test_final_ferrite_alignment_and_empty_storage_labels(self):
        inventory = machine_baseline_read("scenes/ui/inventory_ui.gd")
        self.assertLess(inventory.index("slot.add_child(icon)"),
                        inventory.index("icon.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)"))
        for line in ("icon.offset_left = -17", "icon.offset_right = 17",
                     "icon.offset_top = 3", "icon.offset_bottom = 37",
                     "const SLOT_SIZE := Vector2(50, 50)",
                     "quantity.offset_top = -16", "quantity.offset_bottom = 0"):
            self.assertIn(line, inventory)
        # Approved PNG hashes above freeze these measured nonzero-alpha bounds.
        # Shared 34-unit canvas is horizontally centered; even the lowest source
        # alpha stays above y=34, where the unchanged quantity band starts.
        for bottom in (227, 221, 210, 228):
            self.assertLess(3 + (bottom + 1) * 34 / 256, 50 - 16)
        self.assertEqual(50 / 2 - 17 + (23 + 233) / 2 * 34 / 256, 25)
        extractor = raw_read("scenes/ui/extractor_inspection.gd")
        self.assertIn('(product.display_name if machine.output > 0 else "Output")', extractor)
        smelter = raw_read("scenes/ui/smelter_inspection.gd")
        self.assertIn('(definition.input_item.display_name if machine.input > 0 else "Input")', smelter)
        self.assertIn('(definition.output_item.display_name if machine.output > 0 else "Output")', smelter)
        fabricator = raw_read("scenes/ui/fabricator_inspection.gd")
        self.assertIn('row.label.text = row.item.display_name if stored > 0 else "Input"', fabricator)
        self.assertIn('"label": ingredient_label', fabricator)
        self.assertIn('ingredient_label.text = "Input"', fabricator)
        self.assertIn('product.display_name if machine.output > 0 and product != null else "No stored output"', fabricator)
        self.assertIn("set_material_icon(_output_icon, product, machine.output)", fabricator)
        helper = machine_baseline_read("scenes/ui/item_presentation.gd")
        self.assertIn("item != null and quantity > 0 else null", helper)
        self.assertIn("icon.visible = icon.texture != null", helper)
        self.assertNotIn("identity.custom_minimum_size", helper)

    def test_hotbar_allowance_restores_exact_pre_feature_bytes(self):
        # Prove each allowance recovers the entire pre-feature file, including
        # gameplay not touched by this feature. The old P8 checks still run too.
        for path in HOTBAR_REPLACEMENTS:
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{HOTBAR_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                original = without_approved_ui_scaling_changes(path, read(path))
                self.assertEqual(without_approved_hotbar_changes(path, original), before)

    def test_hotbar_allowance_rejects_changed_duplicate_and_unrelated_edits(self):
        for path, changes in HOTBAR_REPLACEMENTS.items():
            original = without_approved_ui_scaling_changes(path, read(path))
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

    def test_ui_scaling_allowance_rejects_changed_duplicate_and_unrelated_bytes(self):
        for path in UI_SCALING_SHA256:
            original = read(path)
            with self.subTest(path=path):
                before = subprocess.check_output(["git", "show", f"{UI_SCALING_BASE}:{path}"],
                                                 cwd=ROOT).decode("utf-8").replace("\r\n", "\n")
                self.assertEqual(without_approved_ui_scaling_changes(path, original), before)
                for changed in (original.replace("\n", "\nCHANGED\n", 1),
                                original + original, original + "UNRELATED\n"):
                    with self.assertRaises(AssertionError):
                        without_approved_ui_scaling_changes(path, changed)

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
                if path in TERRAIN_SHA256:
                    actual = preserved_terrain_bytes(path, actual)
                if path in MACHINE_ICONS_SHA256 and path not in FERRITE_REFINEMENT_SHA256:
                    actual = without_machine_icon_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path in FERRITE_REFINEMENT_SHA256:
                    actual = without_ferrite_refinement_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path in FERRITE_ICONS_SHA256:
                    actual = without_ferrite_icon_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path == "scenes/ui/musing_ui.gd":
                    actual = without_musing_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path == "scenes/ui/dialogue_ui.gd":
                    actual = without_conversation_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                if path in B1_INVENTORY_SHA256:
                    actual = actual.replace(b"\r\n", b"\n")
                    actual = without_approved_ui_scaling_changes(path, actual.decode("utf-8")).encode("utf-8")
                    self.assertEqual(hashlib.sha256(actual).hexdigest(), B1_INVENTORY_SHA256[path], path)
                    continue
                if path in B1_REPLACEMENTS or path in HOTBAR_REPLACEMENTS:
                    actual = without_approved_b1_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                elif path in UI_SCALING_SHA256:
                    actual = without_approved_ui_scaling_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
                elif path in EXTRACTOR_PILOT_SHA256 or path in SMELTER_PILOT_SHA256 or path in FABRICATOR_SHA256:
                    actual = without_extractor_pilot_changes(path, actual.decode("utf-8").replace("\r\n", "\n")).encode("utf-8")
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
