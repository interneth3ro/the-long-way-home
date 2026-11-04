"""Opening guidance resource/control-flow checks; never invokes Godot/gameplay."""

import re
import unittest

from static_automatic_transitions_test import blocks, function, read


class OpeningGuidanceStaticTest(unittest.TestCase):
    def test_exact_entries_types_ids_and_order(self):
        text = read("dialogue/computer_opening.tres")
        expected = [
            ("dave_question", "dave", "Dave", "Computer? Can you hear me?"),
            ("computer_status", "computer", "Computer",
             "Primary systems offline. Emergency functions operating at minimal capacity."),
            ("dave_response", "dave", "Dave",
             "Then we'd better figure out how to get you running again."),
            ("computer_sensors", "computer", "Computer",
             "External sensors are unreliable. I cannot assess the surrounding area."),
            ("dave_outside", "dave", "Dave",
             "Then I'll take a look outside. See what we're dealing with."),
        ]
        resources = blocks(text, "sub_resource")
        self.assertEqual(len(resources), len(expected))
        for (header, body), (suffix, speaker, name, line) in zip(resources, expected):
            self.assertEqual(header, f'type="Resource" id="Resource_{suffix}"')
            self.assertEqual(body.strip(), '\n'.join([
                'script = ExtResource("2_entry")',
                f'entry_id = &"computer_opening.{suffix}"',
                f'speaker_id = &"{speaker}"',
                f'speaker_display_name = "{name}"', f'text = "{line}"',
            ]))
        refs = ', '.join(f'SubResource("Resource_{item[0]}")' for item in expected)
        self.assertIn(f'entries = Array[ExtResource("2_entry")]([{refs}])', text)
        self.assertIn('conversation_id = &"computer_opening"', text)
        external = blocks(text, "ext_resource")
        self.assertEqual(len(external), 2)
        for path, resource_id in [("dialogue_conversation.gd", "1_conversation"),
                                  ("dialogue_entry.gd", "2_entry")]:
            self.assertTrue(any(f'path="res://dialogue/{path}"' in header
                                and f'id="{resource_id}"' in header
                                for header, _ in external))
            self.assertIn('extends Resource', read(f"dialogue/{path}"))
        self.assertEqual(int(re.search(r'load_steps=(\d+)', text)[1]),
                         1 + len(external) + len(resources))

    def test_initial_objective_and_tracker_use_resource_content(self):
        text = read("objectives/restore_computer.tres")
        self.assertIn('objective_id = &"restore_computer"', text)
        self.assertIn('title = "Restore Computer"', text)
        self.assertIn('description = "Investigate the area outside the ship."', text)
        self.assertIn('path="res://objectives/objective_definition.gd"', text)
        self.assertIn('path="res://objectives/restore_computer.tres"',
                      read("scenes/main/main.tscn"))
        tracker = function(read("scenes/ui/objective_tracker.gd"), "show_objective")
        self.assertIn('_title.text = definition.title if _has_objective else ""', tracker)
        self.assertIn('_description.text = definition.description if _has_objective else ""', tracker)

    def test_completion_and_early_discovery_keep_one_activation(self):
        main = read("scenes/main/main.gd")
        completed = function(main, "_on_conversation_completed")
        self.assertIn('if conversation_id == &"computer_opening":\n'
                      '\t\t_objectives.activate_objective(&"restore_computer")', completed)
        self.assertIn('_dialogue.conversation_completed.connect(_on_conversation_completed)', main)
        discovered = function(main, "_on_ferrite_discovered")
        self.assertIn('_objectives.activate_objective(&"restore_computer")', discovered)
        self.assertIn('_refresh_objective_tracker()', discovered)
        activation = function(read("objectives/objective_controller.gd"), "activate_objective")
        self.assertIn('if not _states.has(objective_id) or _states[objective_id] != State.INACTIVE:\n'
                      '\t\treturn false\n\t_states[objective_id] = State.ACTIVE', activation)
        self.assertIn('_refresh_objective_tracker()', function(main, "_on_objective_state_changed"))
        # Both event orders reach the same milestone-derived display. An already
        # active objective rejects reactivation without resetting any milestones.
        self.assertNotIn('PlaythroughState', completed)
        dialogue = read("scenes/ui/dialogue_ui.gd")
        advance = function(dialogue, "advance")
        self.assertIn('if _entry_index == _conversation.entries.size() - 1:', advance)
        self.assertIn('conversation_completed.emit(completed_id)', advance)
        self.assertNotIn('conversation_completed.emit', function(dialogue, "dismiss"))

    def test_milestone_precedence_and_existing_later_guidance(self):
        main = read("scenes/main/main.gd")
        tracker = function(main, "_refresh_objective_tracker")
        self.assertIn('var definition := _objectives.get_active_objective()', tracker)
        self.assertEqual(re.findall(
            r'(?:if|elif) \$PlaythroughState\.(\w+):\n(?:\s*#[^\n]*\n)*\s*definition = (\w+)',
            tracker), [
                ("ferrite_plate_acquired", "null"),
                ("fabricator_recovered", "PLATE_GUIDANCE"),
                ("ferrite_ingot_acquired", "FABRICATOR_GUIDANCE"),
                ("smelter_deployed", "SMELTING_GUIDANCE"),
                ("smelter_recovered", "SMELTER_DEPLOYMENT_GUIDANCE"),
                ("ferrite_acquired", "SMELTER_GUIDANCE"),
                ("extractor_deployed", "PRODUCTION_GUIDANCE"),
                ("extractor_recovered", "EXTRACTOR_GUIDANCE"),
                ("ferrite_discovered", "FERRITE_GUIDANCE"),
            ])
        self.assertNotIn('\n\t\telse:', tracker)
        self.assertIn('_tracker.show_objective(definition)', tracker)
        self.assertIn('const FERRITE_GUIDANCE: ObjectiveDefinition = '
                      'preload("res://objectives/restore_computer_ferrite.tres")', main)
        self.assertIn('description = "Locate the Extractor in the maintenance bay."',
                      read("objectives/restore_computer_ferrite.tres"))

    def test_normal_f5_inherits_progression_authority(self):
        self.assertIn('run/main_scene="res://scenes/main/main_v2.tscn"', read("project.godot"))
        self.assertIn('path="res://scenes/main/main.tscn"', read("scenes/main/main_v2.tscn"))
        v2 = read("scenes/main/main_v2.gd")
        self.assertTrue(v2.startswith('extends "res://scenes/main/main.gd"'))
        self.assertIn('super._ready()', function(v2, "_ready"))
        for name in ("_on_conversation_completed", "_on_ferrite_discovered", "_refresh_objective_tracker"):
            self.assertNotIn(f'func {name}(', v2)


if __name__ == "__main__":
    unittest.main()
