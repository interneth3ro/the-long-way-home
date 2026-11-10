"""Nonexecuting content, transaction ordering and presentation wiring checks.

These inspect source/resources, not Godot behavior. Runtime cases are in the
separately restricted, unexecuted computer_restoration_test.gd.
"""
import hashlib
import json
import re
import struct
import subprocess
import unittest

from static_automatic_transitions_test import ROOT, blocks, function, read


class ComputerRestorationStaticTest(unittest.TestCase):
    def test_existing_gameplay_methods_only_add_reviewable_feature_hooks(self):
        baseline = "993ffc14c1fad1032227801870cd3a3fce50f7a5"
        modal_guard = '\tif player.get_node("InteractionDetector").computer_modal_open():\n\t\treturn\n'
        amendments = {
            "scenes/main/playthrough_state.gd": [],
            "inventory/inventory_state.gd": [],
            "scenes/main/scene_transition_controller.gd": [
                (modal_guard.replace('return\n', 'return false\n'), ''),
                ('\t_initial_generation += 1\n\tinitial_exterior_initialized = false\n\t_initial_world = null\n', '')],
            "construction/construction_controller.gd": [
                # Static Extractor art fades the completed ghost composite.
                # The separate PR A guard compares all other controller bytes.
                ('_ghost.is_ghost = true', '_ghost.modulate = Color(1, 1, 1, 0.5)'),
                ('return _detector.computer_modal_open() or transitions.is_transitioning()',
                 'return transitions.is_transitioning()')],
            "scenes/player/interaction_detector.gd": [
                ('_tool_active or computer_modal_open() or', '_tool_active or'),
                ('\t\t\tif is_instance_valid(computer_restoration) and computer_restoration.handles(_target):\n'
                 '\t\t\t\tcomputer_restoration.interact_with(_target)\n'
                 '\t\t\telif _target.has_valid_conversation():', '\t\t\tif _target.has_valid_conversation():')],
            "scenes/ui/dialogue_ui.gd": [
                ('if _automatic or not is_conversation_open():', 'if not is_conversation_open():'),
                ('\t_automatic = false\n\t$HUD/Conversation/Content/Actions.show()\n', '')],
            "scenes/ui/hotbar_ui.gd": [
                (modal_guard, ''),
                ('\tif player.get_node("InteractionDetector").computer_modal_open():\n\t\t_clear_menu.hide()\n', '')],
            "scenes/ui/inventory_ui.gd": [
                ('\tif (construction.get("player") as CharacterBody2D).get_node("InteractionDetector").computer_modal_open():\n\t\treturn\n', '')],
            "scenes/main/main.gd": [
                ('\t$PlaythroughState.inventory.changed.connect(_refresh_objective_tracker)\n', ''),
                ('\t$PlaythroughState.computer_restoration_completed.connect(_on_computer_restored)\n', ''),
                ('\t$PlaythroughState.computer_cinematic_completed.connect(_on_computer_cinematic_completed)\n', ''),
                ('definition = REPAIR_READY_GUIDANCE if $PlaythroughState.has_computer_materials() else REPAIR_MATERIAL_GUIDANCE',
                 'definition = null')],
        }
        def methods(text):
            # Comments/new functions do not alter existing executable method bodies.
            return {name: '\n'.join(line.rstrip() for line in body.splitlines()
                                     if line.strip() and not line.lstrip().startswith('#'))
                    for name, body in re.findall(r'^func (\w+)(.*?)(?=^func |\Z)', text, re.M | re.S)}
        for path, replacements in amendments.items():
            current = read(path)
            for new, old in replacements:
                self.assertIn(new, current, path)
                current = current.replace(new, old)
            original = subprocess.check_output(['git', 'show', baseline + ':' + path], cwd=ROOT).decode('utf-8')
            after = methods(current)
            for name, body in methods(original).items():
                self.assertEqual(after[name], body, path + ':' + name)

    def test_locked_narrative_and_inspection(self):
        content = json.loads(read("dialogue/computer_restoration.json"))
        scenes = content["scenes"]
        # Golden digest captured directly from section 6 of the owner handoff,
        # covering scene titles, order, speakers, every line and stage direction.
        digest = hashlib.sha256(json.dumps(
            scenes, ensure_ascii=False, separators=(",", ":")).encode()).hexdigest()
        self.assertEqual(digest, "875a3dc53d0f587dd00b677e669899b97b2694fdac25823652bd038e296059f3")
        self.assertEqual([len([c for c in s["cues"] if c["kind"] == "line"])
                          for s in scenes], [10, 12, 7, 10])
        self.assertEqual(content["inspection"], [
            {"speaker": "dave", "text": "I've got some materials together. Tell me what you need."},
            {"speaker": "computer", "text": "Core restoration requires four Ferrite Plates and four Ferrite Rods."},
            {"speaker": "dave", "text": "All right. I'll see what I can do."},
        ])
        for scene in scenes:
            for cue in scene["cues"]:
                self.assertTrue(cue["text"].strip())
                if cue["kind"] == "line":
                    self.assertIn(cue["speaker"], ("dave", "computer"))

    def test_material_identity_quantities_and_atomic_publication(self):
        state = read("scenes/main/playthrough_state.gd")
        self.assertIn("const COMPUTER_REPAIR_QUANTITY := 4", state)
        for item in ("plate", "rod"):
            text = read(f"inventory/ferrite_{item}.tres")
            self.assertIn(f'item_id = &"ferrite_{item}"', text)
            self.assertNotIn("section = 1", text)
        readiness = function(state, "has_computer_materials")
        for item in ("PLATE", "ROD"):
            self.assertIn(f"FERRITE_{item}.is_valid()", readiness)
            self.assertIn(f"FERRITE_{item}.section == ItemDefinition.Section.MATERIALS", readiness)
            self.assertIn(f"inventory.get_items().has(FERRITE_{item})", readiness)
            self.assertIn(f"inventory.get_quantity(FERRITE_{item}.item_id) >= COMPUTER_REPAIR_QUANTITY", readiness)
        repair = function(state, "restore_computer")
        order = [repair.index(token) for token in (
            "if not can_restore_computer()", "_restoring_computer = true",
            "inventory.remove_items", "_computer_restored = true",
            "computer_restoration_completed.emit()", "inventory.changed.emit()")]
        self.assertEqual(order, sorted(order))
        self.assertIn("], false)", repair)
        self.assertEqual(repair.count('"quantity": COMPUTER_REPAIR_QUANTITY'), 2)
        self.assertNotIn("remove_item(", repair)
        batch = function(read("inventory/inventory_state.gd"), "remove_items")
        self.assertLess(batch.index("for item in items:"), batch.index("_definitions = definitions"))
        self.assertLess(batch.index("_quantities = quantities"), batch.index("changed.emit()"))

    def test_first_plate_opening_inspection_retry_and_operational_paths(self):
        script = read("scenes/ui/computer_restoration.gd")
        dispatch = function(script, "interact_with")
        sequence = [dispatch.index(token) for token in (
            "not _state.computer_opening_completed", "_state.computer_restored",
            "not _state.ferrite_plate_acquired", "not _state.computer_inspection_completed", "_open_panel()")]
        self.assertEqual(sequence, sorted(sequence))
        self.assertIn("target.conversation", dispatch)
        complete = function(script, "_on_conversation_completed")
        self.assertIn('_state.computer_opening_completed = true', complete)
        self.assertIn('and _inspection_pending:', complete)
        self.assertIn('_state.computer_inspection_completed = true', complete)
        self.assertIn('_open_panel.call_deferred()', complete)
        dismiss = function(script, "_on_conversation_dismissed")
        self.assertNotIn('computer_inspection_completed = true', dismiss)
        self.assertIn('_inspection_pending = false', dismiss)
        self.assertNotIn('restore_computer()', function(script, "close"))

    def test_objective_guidance_and_completion_boundaries(self):
        main = read("scenes/main/main.gd")
        self.assertIn('$PlaythroughState.inventory.changed.connect(_refresh_objective_tracker)', main)
        self.assertIn('REPAIR_READY_GUIDANCE if $PlaythroughState.has_computer_materials() else REPAIR_MATERIAL_GUIDANCE', main)
        for name, desc in (
            ("restore_computer_materials", "Gather 4 Ferrite Plates and 4 Ferrite Rods to restore Computer."),
            ("restore_computer_ready", "Return to the ship and restore Computer."),
            ("restore_ship", "Investigate how to improve manufacturing capabilities for ship repairs."),
        ):
            self.assertIn(f'description = "{desc}"', read(f"objectives/{name}.tres"))
        self.assertIn('_objectives.complete_objective(&"restore_computer")', function(main, "_on_computer_restored"))
        self.assertIn('_objectives.activate_objective(&"restore_ship")', function(main, "_on_computer_cinematic_completed"))
        self.assertIn('title = "Restore the Ship"', read("objectives/restore_ship.tres"))
        confirm = function(read("scenes/ui/computer_restoration.gd"), "_confirm_repair")
        self.assertNotIn("finish_computer_cinematic", confirm)
        next_cue = function(read("scenes/ui/computer_restoration.gd"), "_next_cue")
        self.assertLess(next_cue.index('_state.finish_computer_cinematic()'), next_cue.index('_cleanup()'))

    def test_scene_resources_and_panel_callbacks(self):
        script = read("scenes/ui/computer_restoration.gd")
        scene = read("scenes/ui/computer_restoration.tscn")
        paths = set()
        for name, parent in re.findall(r'\[node name="([^"]+)"(?: type="[^"]+")?(?: parent="([^"]+)")?', scene):
            paths.add(name if not parent or parent == "." else parent + "/" + name)
        for path in re.findall(r'\$([A-Za-z][A-Za-z0-9_/]*)', script):
            self.assertIn(path, paths)
        for path in re.findall(r'path="res://([^"]+)"', scene):
            self.assertTrue((ROOT / path).is_file(), path)
        self.assertEqual(int(re.search(r'load_steps=(\d+)', scene)[1]),
                         1 + len(blocks(scene, "ext_resource")) + len(blocks(scene, "sub_resource")))
        for method in re.findall(r'\[connection [^\n]*method="([^"]+)"\]', scene):
            self.assertTrue(function(script, method))
        self.assertIn('text = "Not yet"', scene)
        self.assertIn('text = "Restore Computer"', scene)
        refresh = function(script, "_refresh")
        self.assertIn('_confirm.disabled = not _state.can_restore_computer()', refresh)
        self.assertEqual(refresh.count('inventory.get_quantity('), 2)
        self.assertIn('_state.inventory.changed.connect(_refresh)', script)

    def test_modal_range_transition_and_input_guards(self):
        script = read("scenes/ui/computer_restoration.gd")
        context = function(script, "_context_available")
        for token in ('target.is_inside_tree()', 'target.can_interact()', 'target.max_interaction_distance',
                      'distance_to(target.to_global(target.interaction_point))',
                      '_dialogue.is_conversation_open()', '_transitions.is_transitioning()',
                      '"InventoryUI"', '"MachineUI"', '"Construction").is_active()'):
            self.assertIn(token, context)
        for path, method in (
            ("construction/construction_controller.gd", "_context_blocked"),
            ("scenes/main/scene_transition_controller.gd", "request_transition"),
            ("scenes/ui/inventory_ui.gd", "_toggle"),
            ("scenes/ui/hotbar_ui.gd", "_activate"),
            ("scenes/ui/hotbar_ui.gd", "_clear_assignment"),
            ("scenes/player/interaction_detector.gd", "_physics_process"),
            ("scenes/player/interaction_detector.gd", "_unhandled_input"),
        ):
            self.assertIn('computer_modal_open()', function(read(path), method))
        confirm = function(script, "_confirm_repair")
        self.assertLess(confirm.index('_cinematic = true'), confirm.index('_state.restore_computer()'))
        self.assertLess(confirm.index('_prepare_cues()'), confirm.index('_state.restore_computer()'))

    def test_pacing_no_skip_and_separate_dialogue_instance(self):
        script = read("scenes/ui/computer_restoration.gd")
        for token in ('CHARACTERS_PER_SECOND := 15.0', 'MIN_LINE_SECONDS := 2.5',
                      'MAX_LINE_SECONDS := 8.0', 'SCENE_GAP_SECONDS := 1.5'):
            self.assertIn(token, script)
        self.assertIn('index > 0', function(script, '_prepare_cues'))
        self.assertIn('_cues.append({"kind": "gap"})', script)
        self.assertIn('_playback = DIALOGUE_SCENE.instantiate() as DialogueUI', script)
        self.assertIn('clampf(String(cue.text).length() / CHARACTERS_PER_SECOND', script)
        self.assertNotIn('_next_cue', function(script, '_input'))
        dialogue = read("scenes/ui/dialogue_ui.gd")
        for method in ('advance', 'dismiss'):
            self.assertIn('if _automatic or not is_conversation_open():', function(dialogue, method))
        self.assertIn('$HUD/Conversation/Content/Actions.hide()', function(dialogue, 'show_automatic_entry'))
        self.assertNotIn('conversation_completed.emit', function(dialogue, 'close_automatic'))

    def test_fade_visual_reattach_and_cleanup(self):
        script = read("scenes/ui/computer_restoration.gd")
        out = function(script, '_fade_out')
        self.assertLess(out.index('"color:a", 1.0'), out.index('_reveal_repair'))
        reveal = function(script, '_reveal_repair')
        self.assertLess(reveal.index('_sync_visual()'), reveal.index('"color:a", 0.0'))
        self.assertIn('_sync_visual()', function(script, '_on_arrival'))
        visual = function(script, '_sync_visual')
        self.assertIn('damaged.visible = not _state.computer_restored', visual)
        self.assertIn('repaired.visible = _state.computer_restored', visual)
        cleanup = function(script, '_cleanup')
        for token in ('_tween.kill()', '_flicker.kill()', '_curtain.hide()', '_curtain.color.a = 0.0',
                      '_player.process_mode = _previous_player_mode', '_hum.stop()',
                      '_playback.close_automatic()', 'node.process_mode = record.mode',
                      'node.visible = record.visible', '_cinematic = false'):
            self.assertIn(token, cleanup)
        self.assertNotIn('finish_computer_cinematic', cleanup)
        self.assertNotIn('inventory.', cleanup)
        self.assertIn('_cleanup()', function(script, '_exit_tree'))
        # Existing V2 overlays share the same room-sized canvas and zero offset;
        # switching visibility never edits geometry, scale, collision or range.
        for name in ('damaged', 'repaired'):
            data = (ROOT / f'assets/environment/ship_interior_v2/computer_{name}_overlay.png').read_bytes()
            self.assertEqual(data[:8], b'\x89PNG\r\n\x1a\n')
            dimensions = struct.unpack('>II', data[16:24])
            if name == 'damaged':
                expected = dimensions
            else:
                self.assertEqual(dimensions, expected)


if __name__ == "__main__":
    unittest.main()
