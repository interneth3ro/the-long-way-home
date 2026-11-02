"""Nonexecuting conversation integration/preservation checks; no engine launch."""
import hashlib
import re
import struct
import unittest

from static_automatic_transitions_test import ROOT, read
from static_extractor_inspection_test import functions


class ConversationUIStaticTest(unittest.TestCase):
    def test_visible_hotbar_guards_actions_without_changing_other_inputs(self):
        path = "scenes/ui/hotbar_ui.gd"
        after = functions(read(path))
        changed = {"_process", "_activate", "_slot_input", "_clear_assignment"}
        guard = '\tif _dialogue.is_conversation_open():\n\t\treturn\n'
        for name in changed - {"_process"}:
            # Every mutation/activation callback is guarded, including queued
            # menu signals; its original non-dialogue behavior stays identical.
            self.assertEqual(after[name].count(guard), 1)
        self.assertIn('not transitions.is_transitioning() and not _interaction.is_response_open()', after["_process"])
        self.assertIn('if not _root.visible or _dialogue.is_conversation_open():\n\t\t_clear_menu.hide()', after["_process"])
        # Number-key dispatch still consumes recognized input, then reaches the
        # same guarded _activate callback as mouse activation. No disabled/dim style.
        self.assertIn('_activate(slot)', after["_unhandled_key_input"])
        self.assertNotIn('disabled =', after["_process"])
        self.assertNotIn('modulate', after["_process"])

    def test_inventory_assignment_guard_preserves_inventory_escape_priority(self):
        path = "scenes/ui/inventory_ui.gd"
        after = functions(read(path))
        changed = {"_input", "_machine_context_input", "_assign_to_hotbar"}
        guard = '\tif _dialogue.is_conversation_open():\n\t\treturn\n'
        for name in changed - {"_input"}:
            self.assertEqual(after[name].count(guard), 1)
        hide = '\tif _dialogue.is_conversation_open():\n\t\t_assignment_menu.hide()\n'
        self.assertIn(hide, after["_input"])

    def test_compact_controls_leave_layout_text_and_shared_styles_unchanged(self):
        current = functions(read("scenes/ui/dialogue_ui.gd"))
        self.assertIn('.duplicate() as StyleBox', current["_ready"])
        self.assertIn('custom_minimum_size = Vector2(76, 32)', current["_ready"])

    def test_scene_references_and_mouse_callbacks_resolve(self):
        scene = read("scenes/ui/dialogue_ui.tscn")
        script = read("scenes/ui/dialogue_ui.gd")
        paths = set()
        for name, parent in re.findall(r'\[node name="([^"]+)"(?: type="[^"]+")?(?: parent="([^"]+)")?', scene):
            paths.add(name if not parent or parent == "." else parent + "/" + name)
        for path in re.findall(r'\$([A-Za-z][A-Za-z0-9_/]*)', script):
            self.assertIn(path, paths)
        for source, method in re.findall(r'\[connection signal="pressed" from="([^"]+)" to="\." method="([^"]+)"\]', scene):
            self.assertIn(source, paths)
            self.assertIn(method, functions(script))
        self.assertIn('horizontal_scroll_mode = 0', scene)
        self.assertIn('vertical_scroll_mode = 3', scene)
        # Only the body belongs to the scroll region; identity/footer stay outside.
        self.assertIn('parent="HUD/Conversation/Content/Entry/Body/Scroll"', scene)
        self.assertNotRegex(scene, r'name="(?:Portrait|Speaker|Actions)"[^\n]*parent="[^"]*/Scroll')

    def test_owner_portraits_and_import_settings(self):
        approved = {
            "dave": "0233cabd720b47de79d57634e3796f9740e7ad2da185d0761c27e6608c12b6bc",
            "computer": "fa16376edbb9003970f23a91017f8020b61c05146f193dfa248c7b019a100e72",
            "marvin": "76e4ae9627a51bdd054bddfa17a4dc5cf1474be41b08d9bc33447570e4b4eb63",
        }
        for speaker, digest in approved.items():
            path = f"assets/dialogue/portraits/{speaker}_dialogue_portrait.png"
            data = (ROOT / path).read_bytes()
            self.assertEqual(hashlib.sha256(data).hexdigest(), digest)
            self.assertEqual(data[:8], b"\x89PNG\r\n\x1a\n")
            self.assertEqual(struct.unpack(">IIBB", data[16:26]), (768, 768, 8, 6))
            settings = read(path + ".import")
            self.assertIn("mipmaps/generate=true", settings)
            self.assertIn("process/size_limit=0", settings)
            self.assertIn(f'source_file="res://{path}"', settings)


if __name__ == "__main__":
    unittest.main()
