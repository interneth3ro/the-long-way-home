"""Inert supervisor tests: standard Python children only; never Godot/project code."""
import importlib.util
import json
from pathlib import Path
import sys
import unittest
from unittest import mock

HERE = Path(__file__).absolute().parent
spec = importlib.util.spec_from_file_location("pr103_supervisor", HERE / "supervisor.py")
m = importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class SupervisorTests(unittest.TestCase):
    def run_child(self, code, seconds=3, limit=m.LIMIT, guard=lambda: None):
        return m.bounded(Path(sys.executable), ["-B", "-c", code], HERE, seconds, guard, limit)

    def test_success_and_two_pipes(self):
        r = self.run_child("import sys; print('ok'); print('stderr-ok',file=sys.stderr)")
        self.assertEqual(r["status"], "PASS", r)
        self.assertEqual(r["exit_code"], 0)
        self.assertTrue(r["termination_certain"])
        self.assertIn(b"ok", r["_stdout"])
        self.assertIn(b"stderr-ok", r["_stderr"])

    def test_nonzero_exit(self):
        self.assertEqual(self.run_child("raise SystemExit(7)")["status"], "NONZERO_EXIT")

    def test_error_even_without_nonzero_exit(self):
        r = self.run_child("print('SCRIPT ERROR: inert fixture',flush=True)")
        self.assertEqual(r["status"], "ENGINE_ERROR", r)

    def test_success_completion(self):
        r = self.run_child("print('Production terrain fixture failures: 0')")
        self.assertEqual(m.classify("Assertions", r), "PASS", r)

    def test_missing_malformed_duplicate_and_not_last_completion(self):
        for text in ("nothing", "Production terrain fixture failures: 1",
                     "Production terrain fixture failures: 0\nProduction terrain fixture failures: 0",
                     "Production terrain fixture failures: 0\nextra"):
            with self.subTest(text=text):
                r = self.run_child("print(" + repr(text) + ")")
                self.assertEqual(m.classify("Assertions", r), "INVALID_COMPLETION", r)

    def test_output_limit_and_retention_bound(self):
        r = self.run_child("import sys; sys.stdout.write('x'*2000000); sys.stdout.flush()", limit=32768)
        self.assertEqual(r["status"], "OUTPUT_LIMIT", r["status"])
        self.assertTrue(r["termination_certain"])
        self.assertLessEqual(len(r["_stdout"]) + len(r["_stderr"]), 32768)
        self.assertLessEqual(len(r["diagnostic"].encode()), 4096)

    def test_timeout(self):
        r = self.run_child("import time; time.sleep(5)", seconds=.25)
        self.assertEqual(r["status"], "TIMEOUT", r)
        self.assertTrue(r["termination_certain"])

    def test_preservation_failure_before_launch(self):
        def fail(): raise RuntimeError("inert changed input")
        r = self.run_child("print('must not start')", guard=fail)
        self.assertFalse(r["started"])
        self.assertEqual(m.classify("Import", r), "PRESERVATION_OR_INFRASTRUCTURE_FAILURE")

    def test_preservation_failure_during_child(self):
        calls = []
        def guard():
            calls.append(True)
            if len(calls) > 1: raise RuntimeError("inert changed input")
        r = self.run_child("import time; time.sleep(4)", guard=guard)
        self.assertEqual(r["status"], "PRESERVATION_OR_INFRASTRUCTURE_FAILURE", r)
        self.assertTrue(r["termination_certain"])

    def test_independent_deadline_while_guard_is_busy(self):
        calls = []
        def guard():
            import time
            calls.append(True)
            if len(calls) > 1: time.sleep(.5)
        r = self.run_child("import time; time.sleep(5)", seconds=1.15, guard=guard)
        self.assertEqual(r["status"], "TIMEOUT", r)
        self.assertTrue(r["termination_certain"])

    def test_job_terminates_only_owned_descendant(self):
        code = "import subprocess,sys; subprocess.Popen([sys.executable,'-B','-c','import time; time.sleep(10)'])"
        r = self.run_child(code)
        self.assertEqual(r["status"], "DESCENDANTS_REMAIN", r)
        self.assertTrue(r["termination_certain"])

    def test_mutex_contention(self):
        with m.EngineLock():
            # Windows mutex is reentrant in one thread: contend from another.
            import threading
            results = []
            def contend():
                try:
                    with m.EngineLock(): results.append("unexpected acquired")
                except RuntimeError: results.append("rejected")
            t = threading.Thread(target=contend)
            t.start()
            t.join(2)
            self.assertFalse(t.is_alive())
            self.assertEqual(results, ["rejected"])

    def test_reject_hash_drift_without_launch(self):
        with mock.patch.object(m, "plain", return_value=mock.Mock(read_bytes=lambda: b"inert")):
            with self.assertRaisesRegex(RuntimeError, "SHA-256 mismatch"):
                m.verify_engine()

    @mock.patch.object(m.os, "walk", return_value=[])
    def test_stage_changes_extra_files_and_generated_scope(self, walk):
        original = {"scene.gd": "abc", "image.png": "def", "project.godot": "ghi"}
        policy = {"project_files": original, "allowed_generated_paths": [".godot/cache", "scene.gd.uid", "image.png.import"]}
        with mock.patch.object(m, "inventory", return_value=original):
            self.assertEqual(m.verify_stage(policy), {})
        for actual in ({"scene.gd": "changed"}, {**original, "unexpected.txt": "x"}):
            with mock.patch.object(m, "inventory", return_value=actual):
                with self.assertRaises(RuntimeError):
                    m.verify_stage(policy, True)
        generated = {".godot/cache": "a", "scene.gd.uid": "b", "image.png.import": "c"}
        with mock.patch.object(m, "inventory", return_value={**original, **generated}):
            self.assertEqual(m.verify_stage(policy, True), generated)
            with self.assertRaises(RuntimeError):
                m.verify_stage(policy, False)

    def test_cli_refuses_execution_by_default(self):
        import subprocess
        r = subprocess.run([sys.executable, "-B", str(HERE / "supervisor.py"),
                            "--phase", "Import", "--review-seal-sha256", "0"*64],
                           capture_output=True, timeout=5)
        self.assertNotEqual(r.returncode, 0)
        self.assertIn(b"Execution disabled", r.stderr)
        self.assertFalse((HERE / "execution-state.json").exists())

    def test_source_gate_and_no_visual_pass_claim(self):
        with mock.patch.object(m, "source_snapshot", return_value={"changed": True}):
            with self.assertRaises(RuntimeError):
                m.verify_source({"expected": True})
        r = {"started": True, "termination_certain": True, "status": "PASS", "_stdout": b"", "_stderr": b""}
        self.assertEqual(m.classify("Graphical", r), "PROCESS_OK_OWNER_REVIEW_PENDING")


    def test_windows_process_control_block_unchanged(self):
        old = (m.HISTORICAL / "review-v2/supervisor.py").read_text()
        new = (HERE / "supervisor.py").read_text()
        self.assertEqual(old[old.index("# Windows Job Object:"):old.index("def main():")],
                         new[new.index("# Windows Job Object:"):new.index("def main():")])

    @mock.patch.object(m.os, "walk", return_value=[])
    def test_frozen_outputs_reject_added_removed_and_changed(self, walk):
        original = {"project.godot": "input"}
        frozen = {".godot/cache": "original"}
        policy = {"project_files": original, "allowed_generated_paths": [".godot/cache", "scene.gd.uid"]}
        with mock.patch.object(m, "inventory", return_value={**original, **frozen}):
            self.assertEqual(m.verify_stage(policy, True, frozen), frozen)
        for outputs in ({}, {".godot/cache": "changed"}, {**frozen, "scene.gd.uid": "new"}):
            with mock.patch.object(m, "inventory", return_value={**original, **outputs}):
                with self.assertRaisesRegex(RuntimeError, "Post-import"):
                    m.verify_stage(policy, True, frozen)

    @mock.patch.object(m.os, "walk", return_value=[])
    def test_exact_allowlist_rejects_broad_cache_and_sidecar_exceptions(self, walk):
        policy = {"project_files": {"project.godot": "input"}, "allowed_generated_paths": [".godot/uid_cache.bin"]}
        for unexpected in (".godot/anything_else", "image.png.import", "scene.gd.uid"):
            with mock.patch.object(m, "inventory", return_value={**policy["project_files"], unexpected: "x"}):
                with self.assertRaises(RuntimeError): m.verify_stage(policy, True)

    @mock.patch.object(m.os, "walk", return_value=[])
    def test_generated_count_bound(self, walk):
        outputs = {".godot/"+str(i): "x" for i in range(37)}
        policy = {"project_files": {}, "allowed_generated_paths": list(outputs)}
        with mock.patch.object(m, "inventory", return_value=outputs):
            with self.assertRaises(RuntimeError): m.verify_stage(policy, True)

    def test_current_review_and_source_pin_are_separate(self):
        proposal = json.loads((HERE / "proposal.json").read_text())
        self.assertNotEqual(m.HEAD, m.INPUT_SOURCE)
        self.assertEqual(proposal["source_commit"], m.INPUT_SOURCE)
        self.assertEqual(len(proposal["inputs"]), 54)
        self.assertEqual(len(proposal["allowed_generated_paths"]), 36)
        config = proposal["generated_inputs"]["project.godot"]
        self.assertEqual(len(config["text"].encode()), 367)
        self.assertEqual(m.sha(config["text"].encode()), config["sha256"])

    def test_commands_limits_and_no_graphical_or_editor_phase(self):
        self.assertEqual(set(m.PHASES), {"Import", "Assertions"})
        self.assertEqual(m.PHASES["Import"], (["--headless", "--editor", "--path", str(m.PROJECT), "--quit"], 60))
        self.assertEqual(m.PHASES["Assertions"][1], 30)
        self.assertEqual(m.PHASES["Assertions"][0][-1], "res://scenes/experiments/production_terrain/engine_validation.gd")
        self.assertEqual((m.LIMIT, m.EXCERPT), (1048576, 4096))

    def test_protected_owner_refs_worktrees_and_history_drift_rejected(self):
        baseline = {"files": {".godot/owner": "a"}, "refs_hex": "a", "worktrees_hex": "a", "historical_pr102": {"evidence": "a"}}
        for key in baseline:
            current = dict(baseline, **{key: "changed"})
            with mock.patch.object(m, "source_snapshot", return_value=current):
                with self.assertRaises(RuntimeError): m.verify_source(baseline)
        text = (HERE / "supervisor.py").read_text()
        self.assertIn('"--ignored", "--exclude-standard"', text)
        self.assertIn('"worktree", "list", "--porcelain"', text)
        self.assertNotIn("APPROVED_TRANSIENT_TREE", text)

    def test_stage_and_engine_attempts_refuse_without_explicit_execute_flag(self):
        import subprocess
        for phase in ("Stage", "Import", "Assertions"):
            r = subprocess.run([sys.executable, "-B", str(HERE / "supervisor.py"),
                "--phase", phase, "--review-seal-sha256", "0"*64], capture_output=True, timeout=5)
            self.assertNotEqual(r.returncode, 0)
            self.assertIn(b"Execution disabled", r.stderr)
        self.assertFalse(m.PROJECT.exists())
        self.assertFalse((HERE / "execution-state.json").exists())

    def test_prior_phase_duplicate_blocked_and_foreign_state_stop_before_launch(self):
        identity = {"review_head": m.HEAD, "input_source_commit": m.INPUT_SOURCE}
        cases = [
            ("Import", {**identity, "results": {}}, "Required prior"),
            ("Assertions", {**identity, "results": {"Stage": "PASS"}}, "Required prior"),
            ("Import", {**identity, "results": {"Stage": "PASS", "Import": "PASS"}}, "already attempted"),
            ("Import", {**identity, "blocked": True}, "Previous failure"),
            ("Import", {**identity, "running": "Import"}, "Previous failure"),
            ("Import", {**identity, "review_head": "old"}, "another review"),
            ("Stage", identity, "single-use"),
        ]
        for phase, state, reason in cases:
            def inert_plain(path, file=False):
                payload = {"head": m.HEAD} if path.name == "source-baseline.json" else state
                return mock.Mock(read_bytes=lambda: json.dumps(payload).encode())
            with mock.patch.object(m.sys, "argv", ["supervisor.py", "--phase", phase, "--execute", "--review-seal-sha256", "0"*64]), \
                 mock.patch.object(m, "load_seal"), mock.patch.object(m, "load_manifest", return_value=({}, {})), \
                 mock.patch.object(m, "plain", side_effect=inert_plain), mock.patch.object(Path, "exists", return_value=True), \
                 mock.patch.object(m, "verify_source"), mock.patch.object(m, "verify_engine"), \
                 mock.patch.object(m, "EngineLock"), mock.patch.object(m, "reject_running_godot"), \
                 mock.patch.object(m, "bounded") as bounded, mock.patch.object(m, "prepare_stage") as stage:
                with self.subTest(phase=phase, reason=reason), self.assertRaisesRegex(RuntimeError, reason):
                    m.main()
                bounded.assert_not_called(); stage.assert_not_called()


if __name__ == "__main__":
    unittest.main(verbosity=2)
