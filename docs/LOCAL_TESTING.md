# Local testing runner (feature branch, pending merge)

Use PowerShell **7+** on Windows, Git and Python on PATH, from the actual checkout:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1
pwsh -NoProfile -File tests/local_runner_fixture_test.ps1
```

The first command runs the unchanged suite in the source checkout:
`python -B -m unittest discover -s tests -p 'static_*test.py'`.
It retains the suite's historical Git baselines; a shallow checkout missing those
objects fails. It prints revision, working status, phase results, process exit
code and a diagnostic excerpt. Exit 0 means the requested static/plan operations
passed; exit 1 means failure. Native import and recipe test always say **NOT RUN**.
The fixture command uses inert temporary files and PowerShell subprocesses only.

Git and Python resolve to the first application on PATH. No engine executable is
discovered or invoked. Missing prerequisites, bad configuration, failed static
checks, timeout and combined stdout/stderr overflow stop the runner. Static-suite
nonzero exit is a suite failure; start/configuration failures, timeouts and output
overflow are infrastructure failures. Successful static checks are not Godot
parsing, gameplay, headless or graphical verification.

## Native planning only

`-Mode Native` fails unconditionally, before prerequisite discovery. There is no
authorization token, environment variable or switch that enables engine execution.
The following opt-in command only checks an executable's bytes and stages inputs;
it never invokes that executable, including for a version check:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode NativePlan `
  -GodotPath 'C:\absolute\reviewed\Godot.exe' -GodotSha256 '<64 hexadecimal SHA-256 characters>'
```

Supply a real absolute path/hash to plan; the example is deliberately incomplete.
The path and hash are printed. After static success, Git index regular-file entries
select inputs, copied from **current working files**, including tracked staged and
unstaged edits and staged additions. Untracked files are excluded: add intended new
inputs to the index first. Missing/deleted approved inputs fail closed; stage their
deletion in Git first. Unmerged entries, Git symlinks/submodules and filesystem
reparse points fail closed. The process never modifies source files or runs code
from the copy.

The inventory allows `project.godot`, the recipe-switching test and its UID, and
reviewed resource extensions in assets, construction, dialogue, inventory,
objectives, scenes and shaders. It preserves paths, UIDs, import sidecars and bytes.
It excludes other tests, tools, docs, .git, .godot, artifacts, hidden paths, saves,
settings, credential/secret names and unrelated ignored/untracked files. Extending
the resource inventory requires review; check the printed complete input/hash list
when a feature introduces a new resource type. Never track secrets in resource
files: filename filtering cannot detect secrets embedded in approved content.

Each plan creates a unique `tlwh-native-plan-<GUID>` directory under the OS temp
directory, outside the checkout. It prints its path and every included SHA-256.
Copies and source hashes are compared. Changes during copying fail; this is not an
atomic snapshot of concurrent editing, so avoid editing while planning. Stages,
including partial stages on failure, are retained for inspection. The runner never
automatically deletes them or other owner files. Routine output stays on console;
retain only meaningful failure evidence under `artifacts/logs/` or
`artifacts/evidence/` following [repository preservation rules](../AGENTS.md).
The fixture test removes only its freshly created synthetic temporary tree.

## Restricted native dispatcher (Stage A code only, pending merge)

The dry-run prints this sequential plan using only the explicitly pinned binary:

1. `--headless --editor --path <stage> --quit`: cold import, 60 seconds.
2. Only after successful import: `--headless --path <stage> --script res://tests/fabricator_recipe_switching_test.gd`, 30 seconds.

`New-NativeCommandPlan` constructs these two commands as data, rechecks the pinned
identity, and rejects changed staged bytes, unexpected files/directories and links.
There are no parameters for extra arguments, scripts, scenes or limits.
`Invoke-SyntheticNativeSequence` consumes fabricated process-result records only:
static PASS permits import; import PASS permits the test; every failure stops the
sequence without retries. It returns separate static/import/native outcomes,
command/identity/stage data, a failure reason and a diagnostic decoded from at most
4096 raw bytes. The command arguments print as unambiguous JSON arrays. These
are **synthetic outcomes**, never evidence of engine execution.
Neither of those helpers launches processes or accepts an executor callback.
Stage A adds `Invoke-RestrictedNativeDispatch`, an internal real-execution
implementation with **no caller in any public mode**. It is tested only through
scoped named helper doubles. Do not invoke it directly: dot-sourcing helpers is
for non-Godot fixtures, not owner authorization to run the engine. There is no
executor callback, bypass flag, environment variable, hidden token, extra command,
script or limit parameter. The public `Native` mode still fails unconditionally,
before prerequisites, staging or dispatch. Static and NativePlan never call it.

The dormant implementation creates its own fresh external stage from approved
tracked working files. It records HEAD, full porcelain working status, input
hashes, executable path/hash, stage path, attempted command arrays and limits,
separate static/import/native status, reason and bounded diagnostic. A non-PASS
static status returns without any identity lookup, staging or process call.
Before each prospective launch it rechecks revision, working status, index,
approved source inventory and source/stage hashes, stage identity and separation,
inventory and filesystem links. It rehashes the absolute pinned executable last,
immediately before the fixed synchronous bounded call. There are two calls at
most, one at a time, with no retry path. Static PASS is an internal precondition;
the later activation PR must connect it to the actual static-suite outcome.

Only after successful import may the copy contain a generated `.godot/` tree;
its descendants are inspected without traversing links. Original inputs remain
immutable and unexpected additions elsewhere fail closed. If a real engine
rewrites an input sidecar, validation will stop; Stage A has not established
compatibility with actual engine import behavior. Revision/status/hash checks
detect observed changes, not a transactional snapshot or protection from hostile
concurrent filesystem modification. Avoid editing during any later approved run.

Failures retain a unique, exclusively created `artifacts/logs/native-failure-<GUID>.json`
in the source checkout, only after Git confirms the destination is ignored and
path checks reject links. Evidence is capped at 64 KiB, contains phase results,
revision, executable/stage identity, attempted arguments/limits, failure reason
and diagnostics decoded from at most 4096 bytes. Working status is represented
in evidence by SHA-256, along with a digest of the input path/hash inventory;
the returned summary has the full status and input list.
Evidence save errors are reported separately and never turn a failure into PASS.
Existing evidence is never overwritten or deleted. Success creates no permanent
log; disposable stages remain retained. Synthetic evidence lives only in the
fixture-owned temporary source and is removed with that fixture tree.

The shared bounded process helper is exercised using PowerShell subprocesses only.
It enforces 1 MiB **combined raw stdout/stderr bytes** with asynchronous reads,
retains at most that much stream data for classification, and limits console
diagnostics to an excerpt of 4096 raw bytes. Errors beyond the excerpt remain visible to
the classifier. Detection can consume up to one read buffer per stream beyond the
ceiling; retained raw output stays bounded. Timeout and overflow fail, with a
process-tree termination request and at most a two-second wait.
Cleanup is best effort: escaped descendants, inherited pipes and host failures are
not guaranteed recoverable. Timeout/overflow always report termination uncertainty,
even if the root exits after a kill; the dispatcher stops further phases. Normal
exit plus pipe EOF confirms only the observed process/pipes, not all possible
escaped descendants. A disposable copy is not a security sandbox; a timeout cannot
guarantee recovery from a host-wide freeze.

`Get-NativeOutcome` classifies `ERROR`, `SCRIPT ERROR`, parse errors and assertion
errors on either stream as failures, including with exit zero. Native PASS also
requires exit zero and exactly one completion record, on stdout as its last
nonempty line: `Fabricator recipe switching regression failures: 0`. Positive
failure counts, missing/malformed/duplicate completion, abnormal exits, uncertain
termination, timeouts and overflow fail. Import does not require a test completion
record. Later phases remain NOT RUN after any earlier failure.

The fixture suite checks the existing staging/preservation behavior plus fixed
arguments and deadlines, sequential stop conditions, output classification,
completion requirements, errors beyond the excerpt, Unicode byte accounting,
timeout/overflow, changed identities/stages and the unconditional public gate.
Stage A also exercises the real dispatcher with mocked launch results: command
order/limits, import/native failures, source/index/stage/engine mutation between
phases, allowed generated cache, unique bounded evidence, ignored-path refusal,
owner-file preservation and evidence failures. An AST check proves the production
script has no call to the dormant dispatcher; gate spies prove Native touches no
prerequisite, stage or process helper even with a putative environment override.
Only inert fixtures and harmless PowerShell child processes run. The unchanged
Python suite retains all 43 test methods and historical Git preservation checks.
Actual Godot parsing, import, test assertions, engine process-tree behavior and
graphical behavior remain **NOT RUN**.

## Proposed AGENTS.md amendment - not applied

The following exact additional paragraph is a proposal for owner review. It does
not lift the existing restriction:

> Narrow local-runner exception: only after a separate explicit owner approval
> recording the reviewed runner commit, full native Godot executable path and
> SHA-256, exact commands, disposable staging paths and limits, that reviewed
> `tools/run-local-tests.ps1` may perform one cold headless import in its disposable
> copy (`--headless --editor --path <approved-stage> --quit`, at most 60 seconds),
> followed only on success by `--headless --path <approved-stage> --script
> res://tests/fabricator_recipe_switching_test.gd` (at most 30 seconds). Each process
> is limited to 1 MiB combined output; execute sequentially without retries and
> stop on engine errors, assertion failure, missing/malformed completion, abnormal
> exit, timeout, output overflow or uncertain termination. No other Godot
> invocation, script, scene, extra flag, graphical launch, benchmark, prolonged
> test, VM/SSH integration or freeze reproduction is permitted by this exception.
> All other execution restrictions and preservation requirements remain active.

The first real Godot run requires **separate owner approval after code review**
with the reviewed commit, exact absolute executable path and SHA-256, both complete
argument arrays, source revision/working-input status and hashes, approved fresh
staging paths, deadlines/output limits, and all stop conditions above. The proposed
exception must first be explicitly authorized and applied to AGENTS.md in a later
reviewed change. A policy edit alone does not enable this implementation: that
later change must replace the unconditional gate with a narrowly reviewed approval
check and connect static success to the dormant fixed dispatcher. Stage A already
implements the prospective bounded calls, per-launch validation, phase reporting
and ignored failure evidence, but supplies no public activation route.
No flag, environment variable or fixture record can enable real execution today.
This PR changes neither AGENTS.md nor execution policy and adds no VM or CI integration.

### First-run authorization checklist (future separate approval)

- Apply the approved narrow policy exception and review activation in a separate PR.
- Record the exact reviewed runner commit and tested source revision, full working
  status and every approved input path/SHA-256. Preserve the 43 existing Python
  assertions and historical Git baselines; require static PASS first.
- Select an exact absolute Godot executable path and compute its SHA-256 without
  executing it. No Godot identity is selected or approved by Stage A fixtures;
  their text identity and PowerShell child executable are not Godot candidates.
- Approve a fresh absolute external `tlwh-native-plan-<GUID>` stage path and its
  input inventory, and the ignored source `artifacts/logs/` evidence destination.
  A later run must create a fresh copy; do not approve a stale committed snapshot.
- Record both complete argument arrays with that exact path substituted:
  `["--headless","--editor","--path","<approved-stage>","--quit"]` (60 seconds),
  then `["--headless","--path","<approved-stage>","--script","res://tests/fabricator_recipe_switching_test.gd"]`
  (30 seconds), only after clean import.
- Approve 1,048,576 combined raw output bytes per process, 4096-byte diagnostic
  excerpts, at most two seconds for best-effort termination, sequential execution,
  no retries, and all failure/uncertain-termination stop conditions above.
- Obtain explicit owner authorization for that exact first run. No engine path,
  hash, native stage or first-run approval can be inferred from this code-only PR.

Without engine execution, actual import compatibility, GDScript/runtime behavior,
native completion output, process-tree recovery and host stability remain unverified.
