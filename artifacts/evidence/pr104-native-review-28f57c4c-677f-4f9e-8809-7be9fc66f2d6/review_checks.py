"""Inert PR104 review: no stage creation, engine dispatch or process probes."""
import ast
import hashlib
import json
from pathlib import Path
import runpy
import unittest
from unittest.mock import patch

HERE = Path(__file__).absolute().parent
OLD = Path(r"D:\GameDev\Godot\TLWH-NativeStages")
V2 = OLD / "pr103-supervisor-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b-v2"
V4 = OLD / "pr103-supervisor-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b-v4-final"
SOURCE = (HERE / "supervisor.py").read_text(encoding="utf-8")
S = runpy.run_path(str(HERE / "supervisor.py"), run_name="pr104_inert_review")

def functions(raw):
    return {n.name: ast.dump(n, include_attributes=False) for n in ast.parse(raw).body
            if isinstance(n,(ast.FunctionDef,ast.ClassDef))}

class Review(unittest.TestCase):
    def test_process_controls_unchanged(self):
        before = functions((V2/"supervisor.py").read_text(encoding="utf-8"))
        current = functions(SOURCE)
        for name in ("plain","git","inventory","verify_source","verify_inputs","verify_engine",
                     "STARTUPINFO","PROCESS_INFORMATION","BASIC_LIMIT","IO_COUNTERS","EXTENDED_LIMIT",
                     "ACCOUNTING","PROCESSENTRY32W","kernel","EngineLock","reject_running_godot","bounded"):
            self.assertEqual(current[name],before[name],name)
        changed = {name for name in before if current.get(name)!=before[name]}
        self.assertEqual(changed,{"source_snapshot","is_reviewed_transient","verify_references",
            "load_seal","load_manifest","verify_stage","prepare_stage","classify","main"})
        self.assertEqual(S["LIMIT"],1048576)
        self.assertEqual(S["EXCERPT"],4096)
        self.assertEqual({k:v[1] for k,v in S["PHASES"].items()},{"Import":60,"Assertions":30})

    def test_final_reference_policy_is_exact(self):
        reference = functions((V4/"supervisor.py").read_text(encoding="utf-8"))
        current = functions(SOURCE)
        for name in ("parse_references","is_reviewed_transient","verify_transient_trees","verify_references"):
            self.assertEqual(current[name],reference[name],name)
        v4 = runpy.run_path(str(V4/"supervisor.py"),run_name="pr103_inert_reference")
        for name in ("_CAPTURE_REF","_CHECKPOINT_REF"):
            self.assertEqual(S[name].pattern,v4[name].pattern)
        self.assertFalse(S["is_reviewed_transient"]("refs/heads/codex/preserve-editor-resource-serialization"))

    def test_completion_and_errors_fail_closed(self):
        classify=S["classify"]
        clean={"started":True,"termination_certain":True,"status":"PASS",
               "_stdout":b"Illustrated exterior validation failures: 0\n","_stderr":b""}
        self.assertEqual(classify("Assertions",clean),"PASS")
        for output in (b"",b"Illustrated exterior validation failures: 1\n",
                       clean["_stdout"]*2,clean["_stdout"]+b"extra\n"):
            self.assertEqual(classify("Assertions",dict(clean,_stdout=output)),"INVALID_COMPLETION")
        self.assertEqual(classify("Import",dict(clean,_stderr=b"SCRIPT ERROR: parse")),"ENGINE_ERROR")
        self.assertEqual(classify("Import",dict(clean,termination_certain=False)),"UNCERTAIN_TERMINATION")
        for status in ("TIMEOUT","OUTPUT_LIMIT","NONZERO_EXIT","DESCENDANTS_REMAIN"):
            self.assertEqual(classify("Import",dict(clean,status=status)),status)

    def test_package_bounds_without_creating_stage(self):
        proposal=json.loads((HERE/"proposal.json").read_bytes())
        self.assertEqual(len(proposal["inputs"]),83)
        self.assertEqual(len(proposal["allowed_generated_paths"]),41)
        self.assertFalse(S["PROJECT"].exists())
        self.assertNotIn("Graphical",S["PHASES"])
        self.assertNotIn("Editor",S["PHASES"])
        self.assertEqual(S["ENGINE_SHA"],"ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424")
        # Compile only; never invoke main(), prepare_stage() or bounded().
        compile(SOURCE,str(HERE/"supervisor.py"),"exec")

if __name__ == "__main__":
    unittest.main()
