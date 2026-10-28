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

## Proposed future native phases - not implemented or authorized

The dry-run prints this sequential plan using only the explicitly pinned binary:

1. `--headless --editor --path <stage> --quit`: cold import, 60 seconds.
2. Only after successful import: `--headless --path <stage> --script res://tests/fabricator_recipe_switching_test.gd`, 30 seconds.

Each phase would allow 1 MiB **combined raw stdout/stderr bytes**, one process at a
time, no retries and no additional flags/scripts/scenes. The generic process helper
is exercised with synthetic processes: asynchronous byte reads avoid full-pipe
deadlocks, capture at most a 4096-byte excerpt and stop on timeout/output overflow.
Detection can consume up to one read buffer per stream beyond the ceiling; retained
output stays bounded. It requests process-tree termination with a two-second wait.
Cleanup is best effort: escaped descendants, inherited pipes and host failures are
not guaranteed recoverable. A disposable copy is not a security sandbox; a timeout
cannot guarantee recovery from a host-wide freeze.

Future execution wiring must also classify engine `ERROR`, `SCRIPT ERROR`, parse
errors and abnormal exits as failures even when the exit code is zero. Only the
allowlisted test's expected terminal failure-count message with zero failures,
exit 0 and no engine errors could establish test PASS. A positive assertion count
would be assertion FAIL; missing/malformed completion, crash, parse/import errors,
timeout and overflow would be infrastructure FAIL. Later phases must stay NOT RUN
after any earlier failure. This engine-output classification and real process-tree
behavior with Godot remain unimplemented/unverified; planning cannot certify them.

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
> stop on engine errors, abnormal exit, timeout or output overflow. No other Godot
> invocation, script, scene, extra flag, graphical launch, benchmark, prolonged
> test, VM/SSH integration or freeze reproduction is permitted by this exception.
> All other execution restrictions and preservation requirements remain active.

The first real Godot run requires **separate owner approval after code review**
with the exact executable identity, commands, paths and limits. This PR changes
neither AGENTS.md nor the execution policy and adds no VM or CI integration.
