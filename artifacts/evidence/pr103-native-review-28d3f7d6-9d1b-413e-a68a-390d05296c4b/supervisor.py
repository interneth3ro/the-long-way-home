"""PR103 isolated supervisor. Preparation is not execution authorization.
Decision 16: ordinary user-level Windows permissions; no filesystem sandbox.
"""
import argparse
import ctypes as C
from ctypes import wintypes as W
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import threading
import time

HEAD = "aa62a6d38c981e08c7c6d70cf5929cad642a5414"
INPUT_SOURCE = "123b29b0cef3386f476117b7952d5ad91d6b0f98"
ENGINE = Path(r"D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe")
ENGINE_SHA = "ab1824f85bfd8e0e4128182c000c4003a3e042245b2967848d089b2a04b22424"
PROPOSAL_SHA = "3fd7c93864752be48dbd9f43dd52264a1a37d1b034f3c676d8dc9429a0174928"
PARENT = Path(r"D:\GameDev\Godot\TLWH-NativeStages")
PROJECT = PARENT / "tlwh-pr103-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b"
REPO = Path(r"D:\GameDev\Godot\Projects\TLWH")
HERE = Path(__file__).absolute().parent
HISTORICAL = PARENT / "tlwh-pr102-prepared-8e9b3e23-9c43-4f9b-8f35-dbb6e25a29a7"
LIMIT = 1048576
EXCERPT = 4096
ERROR_PATTERN = re.compile(rb"(?:SCRIPT ERROR|Parse Error|SHADER ERROR|Shader Error|ERROR:|Assertion failed|AssertionError)", re.I)
PHASES = {
    "Import": (["--headless", "--editor", "--path", str(PROJECT), "--quit"], 60),
    "Assertions": (["--headless", "--path", str(PROJECT), "--script", "res://scenes/experiments/production_terrain/engine_validation.gd"], 30),
}


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def plain(path, file=False):
    path = Path(os.path.abspath(path))
    for part in (path, *path.parents):
        st = part.lstat()
        if getattr(st, "st_file_attributes", 0) & 0x400 or part.is_symlink():
            raise RuntimeError("Reparse/symlink rejected: " + str(part))
    if file and (not path.is_file() or path.stat().st_nlink != 1):
        raise RuntimeError("Nonregular or hard-linked file rejected: " + str(path))
    return path


def git(*args):
    return subprocess.check_output(["git", "--no-optional-locks", "-C", str(REPO), *args],
        env=dict(os.environ, GIT_OPTIONAL_LOCKS="0"), stderr=subprocess.PIPE, timeout=15)


def inventory(root):
    plain(root)
    result = {}
    for parent, directories, files in os.walk(root, followlinks=False):
        plain(parent)
        for name in directories:
            plain(Path(parent) / name)
        for name in files:
            path = plain(Path(parent) / name, True)
            result[path.relative_to(root).as_posix()] = sha(path.read_bytes())
    return result


def source_snapshot():
    paths = set()
    for args in (("ls-files", "-z"),
                 ("ls-files", "--others", "--exclude-standard", "-z"),
                 ("ls-files", "--others", "--ignored", "--exclude-standard", "-z")):
        paths.update(git(*args).decode("utf-8").split("\0"))
    own = HERE.relative_to(REPO).as_posix() + "/"
    files = {}
    for relative in sorted(paths - {""}):
        if not relative.startswith(own):
            path = plain(REPO / relative)
            if path.is_dir():
                # Git can report an ignored nested repository as one directory.
                # Read/hash its contents; never alter or classify it disposable.
                files.update({relative.rstrip("/")+"/"+p: h for p, h in inventory(path).items()})
            else:
                files[relative] = sha(plain(path, True).read_bytes())
    return {
        "head": git("rev-parse", "HEAD").decode().strip(),
        "branch": git("symbolic-ref", "--short", "HEAD").decode().strip(),
        "status_hex": git("status", "--porcelain=v1", "-z", "--untracked-files=all").hex(),
        "index_sha256": sha(plain(REPO / ".git/index", True).read_bytes()),
        "refs_hex": git("show-ref").hex(),
        "worktrees_hex": git("worktree", "list", "--porcelain").hex(),
        "files": files,
        "historical_pr102": inventory(HISTORICAL),
    }


def verify_source(baseline):
    if source_snapshot() != baseline:
        raise RuntimeError("Source/protected owner material/references/worktrees/history changed")


def write_new(path, value):
    raw = (json.dumps(value, indent=2, sort_keys=True) + "\n").encode("utf-8")
    with open(path, "xb") as stream:
        stream.write(raw)


def load_seal(expected):
    plain(HERE)
    if HERE.parent != REPO / "artifacts/evidence" or HERE.name != "pr103-native-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b":
        raise RuntimeError("Unexpected review package location")
    raw = plain(HERE / "seal.json", True).read_bytes()
    if sha(raw) != expected.lower():
        raise RuntimeError("Reviewed seal SHA-256 mismatch")
    seal = json.loads(raw)
    if seal["review_head"] != HEAD or seal["input_source_commit"] != INPUT_SOURCE or seal["project"] != str(PROJECT):
        raise RuntimeError("Seal identity mismatch")
    for relative, digest in seal["review_files"].items():
        if sha(plain(HERE / relative, True).read_bytes()) != digest:
            raise RuntimeError("Reviewed control changed: " + relative)
    return seal


def load_manifest():
    raw = plain(HERE / "proposal.json", True).read_bytes()
    if sha(raw) != PROPOSAL_SHA:
        raise RuntimeError("Approved proposal changed")
    proposal = json.loads(raw)
    manifest = json.loads(plain(HERE / "manifest.json", True).read_bytes())
    if (manifest["review_head"] != HEAD or manifest["input_source_commit"] != INPUT_SOURCE
            or manifest["project"] != str(PROJECT) or len(proposal["inputs"]) != 54
            or proposal["source_commit"] != INPUT_SOURCE):
        raise RuntimeError("Manifest identity/inventory mismatch")
    expected = {p: v["sha256"] for p, v in proposal["inputs"].items()}
    for path, record in proposal["generated_inputs"].items():
        raw = record["text"].encode("utf-8")
        if sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise RuntimeError("Generated configuration identity mismatch")
        expected[path] = record["sha256"]
    if manifest["project_files"] != expected or len(expected) != 55:
        raise RuntimeError("Initial staged inventory mismatch")
    if (manifest["allowed_generated_paths"] != proposal["allowed_generated_paths"]
            or len(set(manifest["allowed_generated_paths"])) != 36):
        raise RuntimeError("Output allowlist mismatch")
    for path in [*expected, *manifest["allowed_generated_paths"]]:
        parts = Path(path).parts
        if Path(path).is_absolute() or ".." in parts or ":" in path or "\\" in path:
            raise RuntimeError("Unsafe staged path")
    return manifest, proposal


def verify_inputs(proposal):
    for path, record in proposal["inputs"].items():
        raw = git("show", INPUT_SOURCE + ":" + path)
        current = git("show", HEAD + ":" + path)
        if raw != current or sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise RuntimeError("Pinned Git input changed: " + path)


def verify_stage(manifest, outputs_allowed=False, frozen=None):
    actual = inventory(PROJECT)
    original = manifest["project_files"]
    allowed = set(manifest["allowed_generated_paths"]) if outputs_allowed else set()
    allowed_dirs = {parent.as_posix() for p in set(original) | allowed
                    for parent in Path(p).parents if str(parent) != "."}
    for directory, names, files in os.walk(PROJECT, followlinks=False):
        for name in names:
            if (Path(directory) / name).relative_to(PROJECT).as_posix() not in allowed_dirs:
                raise RuntimeError("Unexpected stage directory")
    for relative, digest in original.items():
        if actual.get(relative) != digest:
            raise RuntimeError("Missing/changed staged input: " + relative)
    extra = {p: h for p, h in actual.items() if p not in original}
    if set(extra) - allowed or len(extra) > 36:
        raise RuntimeError("Unexpected generated stage file")
    if frozen is not None and extra != frozen:
        raise RuntimeError("Post-import generated output added/removed/changed")
    return extra


def verify_engine():
    if sha(plain(ENGINE, True).read_bytes()) != ENGINE_SHA:
        raise RuntimeError("Pinned executable SHA-256 mismatch")


def prepare_stage(manifest, proposal, baseline):
    # Called only by explicitly authorized Stage --execute; never by Plan/tests.
    plain(PARENT)
    if PROJECT.parent != PARENT or not re.fullmatch(r"tlwh-pr103-review-[0-9a-f-]{36}", PROJECT.name):
        raise RuntimeError("Unexpected stage location")
    if REPO == PARENT or REPO in PARENT.parents or PARENT in REPO.parents:
        raise RuntimeError("Stage parent overlaps source")
    verify_source(baseline)
    PROJECT.mkdir(exist_ok=False)
    for path, record in proposal["inputs"].items():
        raw = git("show", INPUT_SOURCE + ":" + path)
        if sha(raw) != record["sha256"] or len(raw) != record["bytes"]:
            raise RuntimeError("Input changed during copy: " + path)
        destination = PROJECT / path
        destination.parent.mkdir(parents=True, exist_ok=True)
        plain(destination.parent)
        with open(destination, "xb") as stream:
            stream.write(raw)
    for path, record in proposal["generated_inputs"].items():
        with open(PROJECT / path, "xb") as stream:
            stream.write(record["text"].encode("utf-8"))
    verify_stage(manifest)
    verify_source(baseline)


# Windows Job Object: child starts suspended, joins kill-on-close job, then resumes.
# No process-name kill or broad cleanup is used.
class STARTUPINFO(C.Structure):
    _fields_ = [("cb", W.DWORD), ("lpReserved", W.LPWSTR), ("lpDesktop", W.LPWSTR),
                ("lpTitle", W.LPWSTR), ("dwX", W.DWORD), ("dwY", W.DWORD),
                ("dwXSize", W.DWORD), ("dwYSize", W.DWORD),
                ("dwXCountChars", W.DWORD), ("dwYCountChars", W.DWORD),
                ("dwFillAttribute", W.DWORD), ("dwFlags", W.DWORD),
                ("wShowWindow", W.WORD), ("cbReserved2", W.WORD),
                ("lpReserved2", C.POINTER(W.BYTE)), ("hStdInput", W.HANDLE),
                ("hStdOutput", W.HANDLE), ("hStdError", W.HANDLE)]
class PROCESS_INFORMATION(C.Structure):
    _fields_ = [("hProcess", W.HANDLE), ("hThread", W.HANDLE),
                ("dwProcessId", W.DWORD), ("dwThreadId", W.DWORD)]
class BASIC_LIMIT(C.Structure):
    _fields_ = [("PerProcessUserTimeLimit", C.c_int64), ("PerJobUserTimeLimit", C.c_int64),
                ("LimitFlags", W.DWORD), ("MinimumWorkingSetSize", C.c_size_t),
                ("MaximumWorkingSetSize", C.c_size_t), ("ActiveProcessLimit", W.DWORD),
                ("Affinity", C.c_size_t), ("PriorityClass", W.DWORD), ("SchedulingClass", W.DWORD)]
class IO_COUNTERS(C.Structure):
    _fields_ = [(name, C.c_uint64) for name in
                ("ReadOperationCount", "WriteOperationCount", "OtherOperationCount",
                 "ReadTransferCount", "WriteTransferCount", "OtherTransferCount")]
class EXTENDED_LIMIT(C.Structure):
    _fields_ = [("BasicLimitInformation", BASIC_LIMIT), ("IoInfo", IO_COUNTERS),
                ("ProcessMemoryLimit", C.c_size_t), ("JobMemoryLimit", C.c_size_t),
                ("PeakProcessMemoryUsed", C.c_size_t), ("PeakJobMemoryUsed", C.c_size_t)]
class ACCOUNTING(C.Structure):
    _fields_ = [(n, C.c_int64) for n in
                ("TotalUserTime", "TotalKernelTime", "ThisPeriodTotalUserTime", "ThisPeriodTotalKernelTime")]
    _fields_ += [(n, W.DWORD) for n in ("TotalPageFaultCount", "TotalProcesses", "ActiveProcesses", "TotalTerminatedProcesses")]
class PROCESSENTRY32W(C.Structure):
    _fields_ = [("dwSize", W.DWORD), ("cntUsage", W.DWORD), ("th32ProcessID", W.DWORD),
                ("th32DefaultHeapID", C.c_size_t), ("th32ModuleID", W.DWORD),
                ("cntThreads", W.DWORD), ("th32ParentProcessID", W.DWORD),
                ("pcPriClassBase", W.LONG), ("dwFlags", W.DWORD), ("szExeFile", W.WCHAR * 260)]

def kernel():
    k = C.WinDLL("kernel32", use_last_error=True)
    declarations = {
        "CreateJobObjectW": ([C.c_void_p, W.LPCWSTR], W.HANDLE),
        "SetInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD], W.BOOL),
        "QueryInformationJobObject": ([W.HANDLE, C.c_int, C.c_void_p, W.DWORD, C.c_void_p], W.BOOL),
        "AssignProcessToJobObject": ([W.HANDLE, W.HANDLE], W.BOOL),
        "TerminateJobObject": ([W.HANDLE, W.UINT], W.BOOL),
        "CreateProcessW": ([W.LPCWSTR, W.LPWSTR, C.c_void_p, C.c_void_p, W.BOOL,
                            W.DWORD, C.c_void_p, W.LPCWSTR, C.POINTER(STARTUPINFO),
                            C.POINTER(PROCESS_INFORMATION)], W.BOOL),
        "ResumeThread": ([W.HANDLE], W.DWORD),
        "WaitForSingleObject": ([W.HANDLE, W.DWORD], W.DWORD),
        "GetExitCodeProcess": ([W.HANDLE, C.POINTER(W.DWORD)], W.BOOL),
        "CloseHandle": ([W.HANDLE], W.BOOL),
        "TerminateProcess": ([W.HANDLE, W.UINT], W.BOOL),
        "CreateMutexW": ([C.c_void_p, W.BOOL, W.LPCWSTR], W.HANDLE),
        "ReleaseMutex": ([W.HANDLE], W.BOOL),
        "CreateToolhelp32Snapshot": ([W.DWORD, W.DWORD], W.HANDLE),
        "Process32FirstW": ([W.HANDLE, C.POINTER(PROCESSENTRY32W)], W.BOOL),
        "Process32NextW": ([W.HANDLE, C.POINTER(PROCESSENTRY32W)], W.BOOL),
    }
    for name, (args, result) in declarations.items():
        f = getattr(k, name)
        f.argtypes, f.restype = args, result
    return k

class EngineLock:
    def __enter__(self):
        self.k = kernel()
        self.handle = self.k.CreateMutexW(None, False, "Global\\TLWH-Godot-PR102-supervisor")
        if not self.handle:
            raise C.WinError(C.get_last_error())
        wait = self.k.WaitForSingleObject(self.handle, 0)
        if wait != 0:  # abandoned mutex also requires explicit investigation
            self.k.CloseHandle(self.handle)
            raise RuntimeError("Engine mutex busy/abandoned; no launch")
        return self
    def __exit__(self, *args):
        self.k.ReleaseMutex(self.handle)
        self.k.CloseHandle(self.handle)

def reject_running_godot():
    k = kernel()
    handle = k.CreateToolhelp32Snapshot(2, 0)
    if handle == C.c_void_p(-1).value:
        raise C.WinError(C.get_last_error())
    try:
        entry = PROCESSENTRY32W()
        entry.dwSize = C.sizeof(entry)
        if not k.Process32FirstW(handle, C.byref(entry)):
            raise C.WinError(C.get_last_error())
        while True:
            if entry.szExeFile.lower().startswith("godot"):
                raise RuntimeError("An existing Godot process is present; no launch")
            if not k.Process32NextW(handle, C.byref(entry)):
                if C.get_last_error() != 18:
                    raise C.WinError(C.get_last_error())
                break
    finally:
        k.CloseHandle(handle)

def bounded(executable, arguments, directory, seconds, guard, output_limit=LIMIT):
    import msvcrt
    k = kernel()
    job = k.CreateJobObjectW(None, None)
    if not job:
        raise C.WinError(C.get_last_error())
    limits = EXTENDED_LIMIT()
    limits.BasicLimitInformation.LimitFlags = 0x2000
    pi = PROCESS_INFORMATION()
    out_r = out_w = err_r = err_w = null = None
    threads = []
    mutex = threading.Lock()
    done = threading.Event()
    failure = []
    data = [bytearray(), bytearray()]
    excerpt = bytearray()
    total = 0
    status, code, certain, started = "PASS", None, False, False
    root_exit_seen = None
    ended = [False, False]
    def check(ok):
        if not ok: raise C.WinError(C.get_last_error())
    def active():
        info = ACCOUNTING()
        check(k.QueryInformationJobObject(job, 1, C.byref(info), C.sizeof(info), None))
        return info.ActiveProcesses
    def stop(reason):
        with mutex:
            if not failure: failure.append(reason)
        k.TerminateJobObject(job, 1)
    def reader(fd, stream):
        nonlocal total
        try:
            while not done.is_set():
                raw = os.read(fd, 4096)
                if not raw: break
                reason = None
                with mutex:
                    total += len(raw)
                    remaining = max(0, output_limit - sum(map(len, data)))
                    data[stream].extend(raw[:remaining])
                    excerpt.extend(raw[:max(0, EXCERPT-len(excerpt))])
                    if total > output_limit: reason = "OUTPUT_LIMIT"
                    elif ERROR_PATTERN.search(data[stream]): reason = "ENGINE_ERROR"
                if reason:
                    stop(reason)
                    break
        except OSError:
            if not done.is_set(): stop("PIPE_ERROR")
        finally:
            os.close(fd)
            ended[stream] = True
    def watchdog():
        if not done.wait(seconds):
            stop("TIMEOUT")
    try:
        check(k.SetInformationJobObject(job, 9, C.byref(limits), C.sizeof(limits)))
        out_r, out_w = os.pipe()
        err_r, err_w = os.pipe()
        os.set_inheritable(out_w, True)
        os.set_inheritable(err_w, True)
        null = os.open(os.devnull, os.O_RDONLY)
        os.set_inheritable(null, True)
        si = STARTUPINFO()
        si.cb, si.dwFlags = C.sizeof(si), 0x100
        si.hStdInput = msvcrt.get_osfhandle(null)
        si.hStdOutput = msvcrt.get_osfhandle(out_w)
        si.hStdError = msvcrt.get_osfhandle(err_w)
        command = C.create_unicode_buffer(subprocess.list2cmdline([str(executable), *arguments]))
        guard()  # immediately before child creation
        check(k.CreateProcessW(str(executable), command, None, None, True, 0x4 | 0x08000000,
                               None, str(directory), C.byref(si), C.byref(pi)))
        started = True
        check(k.AssignProcessToJobObject(job, pi.hProcess))
        # Deadline enforcement runs independently of preservation checks/pipe handling.
        timer = threading.Thread(target=watchdog, daemon=True)
        timer.start()
        threads.append(timer)
        if k.ResumeThread(pi.hThread) == 0xffffffff: raise C.WinError(C.get_last_error())
        k.CloseHandle(pi.hThread)
        pi.hThread = None
        for fd in (out_w, err_w, null): os.close(fd)
        out_w = err_w = null = None
        for stream, fd in enumerate((out_r, err_r)):
            t = threading.Thread(target=reader, args=(fd, stream), daemon=True)
            t.start()
            threads.append(t)
        out_r = err_r = None
        next_guard = time.monotonic() + 1
        while True:
            if failure:
                status = failure[0]
                break
            if time.monotonic() >= next_guard:
                guard()
                next_guard = time.monotonic() + 1
            wait = k.WaitForSingleObject(pi.hProcess, 20)
            if wait == 0:
                value = W.DWORD()
                check(k.GetExitCodeProcess(pi.hProcess, C.byref(value)))
                code = value.value
                if active() != 0:
                    # Job accounting can lag the signaled root handle briefly.
                    if root_exit_seen is None: root_exit_seen = time.monotonic()
                    if time.monotonic() - root_exit_seen >= .25:
                        status = "DESCENDANTS_REMAIN"
                        break
                    time.sleep(.005)
                    continue
                if all(ended):
                    certain = True
                    status = failure[0] if failure else ("PASS" if code == 0 else "NONZERO_EXIT")
                    break
                time.sleep(.005)
            elif wait != 258: raise C.WinError(C.get_last_error())
    except Exception as exc:
        status = "PRESERVATION_OR_INFRASTRUCTURE_FAILURE"
        with mutex:
            excerpt.extend(str(exc).encode("utf-8")[:max(0, EXCERPT-len(excerpt))])
    finally:
        if started and not certain:
            k.TerminateJobObject(job, 1)
            if pi.hProcess and k.WaitForSingleObject(pi.hProcess, 0) != 0:
                k.TerminateProcess(pi.hProcess, 1)  # suspended child if job assignment failed
            deadline = time.monotonic() + 2
            while time.monotonic() < deadline:
                try:
                    if k.WaitForSingleObject(pi.hProcess, 0) == 0 and active() == 0:
                        certain = True
                        break
                except OSError: break
                time.sleep(.02)
        done.set()
        for t in threads: t.join(timeout=.1)
        for fd in (out_r, out_w, err_r, err_w, null):
            if fd is not None:
                try: os.close(fd)
                except OSError: pass
        for handle in (pi.hThread, pi.hProcess, job):
            if handle: k.CloseHandle(handle)
    # Text presentation also remains within the diagnostic UTF-8 byte ceiling.
    diagnostic = bytes(excerpt).decode("utf-8", "replace").encode("utf-8")[:EXCERPT].decode("utf-8", "ignore")
    return {"status": status, "exit_code": code, "output_bytes": total,
            "diagnostic": diagnostic, "termination_certain": certain, "started": started,
            "_stdout": bytes(data[0]), "_stderr": bytes(data[1])}

def classify(phase, result):
    if result["started"] and not result["termination_certain"]:
        return "UNCERTAIN_TERMINATION"
    if result["status"] != "PASS":
        return result["status"]
    stdout, stderr = result["_stdout"], result["_stderr"]
    if ERROR_PATTERN.search(stdout) or ERROR_PATTERN.search(stderr):
        return "ENGINE_ERROR"
    if phase == "Assertions":
        lines = [p.strip() for p in stdout.decode("utf-8", "replace").splitlines() if p.strip()]
        completions = [p for p in lines if p.startswith("Production terrain fixture failures:")]
        if completions != ["Production terrain fixture failures: 0"] or not lines or lines[-1] != completions[0]:
            return "INVALID_COMPLETION"
    return "PROCESS_OK_OWNER_REVIEW_PENDING" if phase in ("Graphical", "Editor") else "PASS"

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--phase", choices=["Plan", "Stage", *PHASES], default="Plan")
    parser.add_argument("--execute", action="store_true", help="Not authorization: owner approval required per phase")
    parser.add_argument("--review-seal-sha256", required=True, help="Integrity digest, not execution permission")
    args = parser.parse_args()
    if args.phase == "Plan" and args.execute:
        raise RuntimeError("Plan is read-only")
    if args.phase != "Plan" and not args.execute:
        raise RuntimeError("Execution disabled; owner authorization and --execute required")
    load_seal(args.review_seal_sha256)
    manifest, proposal = load_manifest()
    baseline = json.loads(plain(HERE / "source-baseline.json", True).read_bytes())
    if baseline["head"] != HEAD:
        raise RuntimeError("Review checkout identity mismatch")
    state_path = HERE / "execution-state.json"
    state = json.loads(plain(state_path, True).read_bytes()) if state_path.exists() else {}
    if state and (state.get("review_head") != HEAD or state.get("input_source_commit") != INPUT_SOURCE):
        raise RuntimeError("Execution state belongs to another review")
    if state.get("blocked") or state.get("running"):
        raise RuntimeError("Previous failure/incomplete run: stop; no retry")
    verify_source(baseline)
    verify_engine()
    if args.phase == "Plan":
        verify_inputs(proposal)
        if PROJECT.exists():
            frozen = None
            if state.get("results", {}).get("Import") == "PASS":
                raw = plain(HERE / "generated-Import.json", True).read_bytes()
                if sha(raw) != state.get("import_outputs_sha256"):
                    raise RuntimeError("Captured import output inventory changed")
                frozen = json.loads(raw)
            verify_stage(manifest, bool(state.get("results", {}).get("Import")), frozen)
        elif state:
            raise RuntimeError("Prepared stage missing")
        print(json.dumps({"execution": "NOT ATTEMPTED", "review_head": HEAD,
            "input_source_commit": INPUT_SOURCE, "stage_exists": PROJECT.exists(),
            "input_count": 54, "initial_file_count": 55, "allowed_generated_count": 36,
            "state": state, "phases": PHASES}, indent=2))
        return
    with EngineLock():
        reject_running_godot()
        if args.phase == "Stage":
            if state or PROJECT.exists():
                raise RuntimeError("Stage preparation is single-use; preserve existing stage")
        else:
            prior = "Stage" if args.phase == "Import" else "Import"
            if state.get("results", {}).get(prior) != "PASS":
                raise RuntimeError("Required prior phase did not pass")
            if args.phase in state.get("results", {}):
                raise RuntimeError("Phase already attempted; no repeat")
        if not state:
            state = {"review_head": HEAD, "input_source_commit": INPUT_SOURCE,
                     "results": {}, "blocked": False}
            write_new(state_path, state)
        state["running"] = args.phase
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        state_hash = sha(state_path.read_bytes())
        frozen = None
        if args.phase == "Assertions":
            raw = plain(HERE / "generated-Import.json", True).read_bytes()
            if sha(raw) != state.get("import_outputs_sha256"):
                raise RuntimeError("Captured import output inventory changed")
            frozen = json.loads(raw)
        guard_calls = 0
        def guards():
            nonlocal guard_calls
            load_seal(args.review_seal_sha256)
            if sha(plain(state_path, True).read_bytes()) != state_hash:
                raise RuntimeError("Execution state changed during phase")
            verify_source(baseline)
            verify_engine()
            if args.phase != "Stage":
                verify_stage(manifest, args.phase == "Assertions" or guard_calls > 0, frozen)
            guard_calls += 1
        try:
            if args.phase == "Stage":
                guards()
                verify_inputs(proposal)
                prepare_stage(manifest, proposal, baseline)
                classification = "PASS"
                result = {"started": False, "engine_attempted": False, "initial_files": 55}
            else:
                arguments, seconds = PHASES[args.phase]
                result = bounded(ENGINE, arguments, PROJECT, seconds, guards)
                classification = classify(args.phase, result)
                guards()
                outputs = verify_stage(manifest, True, frozen)
                if classification == "PASS":
                    write_new(HERE / ("generated-" + args.phase + ".json"), outputs)
                    if args.phase == "Import":
                        state["import_outputs_sha256"] = sha((HERE / "generated-Import.json").read_bytes())
        except Exception as exc:
            classification = "PRESERVATION_OR_INFRASTRUCTURE_FAILURE"
            result = {"diagnostic": str(exc).encode("utf-8")[:EXCERPT].decode("utf-8", "ignore")}
        state["running"] = None
        state["results"][args.phase] = classification
        state["blocked"] = classification != "PASS"
        record = {k: v for k, v in result.items() if not k.startswith("_")}
        record.update({"phase": args.phase, "classification": classification,
                       "review_head": HEAD, "input_source_commit": INPUT_SOURCE})
        write_new(HERE / ("execution-" + args.phase + ".json"), record)
        state_path.write_text(json.dumps(state, indent=2) + "\n", encoding="utf-8")
        print(json.dumps(record, indent=2))
        if state["blocked"]:
            raise RuntimeError("STOP: failure; no subsequent phase or retry")


if __name__ == "__main__":
    main()
