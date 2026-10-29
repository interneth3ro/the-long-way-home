# Local testing runner (simplification, pending merge)

Use PowerShell **7+** on Windows, with trusted Git and Python applications on PATH,
from the actual checkout. No new testing framework or engine discovery is used.

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1
pwsh -NoProfile -File tests/local_runner_fixture_test.ps1
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode NativePlan
```

`Static` (the default) runs the unchanged Python suite:
`python -B -m unittest discover -s tests -p 'static_*test.py'`.
Its historical Git baselines must be available. Static success is not engine or
runtime validation. The fixture suite uses inert temporary files, scoped named
mocks and harmless PowerShell children; it never invokes Godot.

`NativePlan` hashes the fixed executable without invoking it, requires static
PASS, creates a fresh external stage and prints revision, complete working status,
index digest, observational control hashes, full approved input hashes, stage,
fixed command arrays and limits. This console data is neither authorization nor a
loadable approval record. Native always creates its own fresh stage after static
PASS; a plan stage is never reused. Do not edit files during a plan or run.

## Authorization and standing scope

**Godot was NOT RUN during this code-only implementation. No first real run has
been authorized.** The owner approved the narrow standing scope in principle;
this feature branch leaves `Assert-NativeExecutionAuthorization` as an
unconditional denial. Public Native fails before prerequisites, static validation,
staging or process calls. The internal dispatcher also checks the gate before
staging and each prospective engine launch. Flags, environment, local files,
merge and test PASS cannot enable it.

After reviewing this PR, the owner must separately explicitly approve the first
controlled real run and activation of the standing scope in
[AGENTS.md](../AGENTS.md#godot-execution-safety). The minimal later reviewed code
change removes that function's unconditional denial. There is no frozen scope
embedded in its own hashed runner, approval provider, receipt, withdrawal marker,
GitHub-comment flow, token, external service or expiration machinery. This PR
neither makes that change nor grants permission. Preserve any historical receipts,
withdrawal files and evidence; the simplified runner does not read or delete them.

Once expressly activated, the standing scope permits repeated local use of the
reviewed runner during feature development, without per-run approval records:

```powershell
# Future use only, after explicit owner permission and reviewed gate removal:
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Native
```

The sole executable is the standard Windows Godot 4.7.2 binary:

- Path: `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`
- SHA-256: `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`

The runner accepts only `-Mode`; no executable/hash/script/scene/flag override.
The path must be plain and the file hash must match, including immediately before
each launch. No version/help invocation or discovery is performed.

Keep runner, policy, static suite and native test assertions reviewed. Native
requires tools, AGENTS.md, this guide, fixture, Python static files and recipe-switching test/UID to match the
captured source revision. The runner must reside in the actual checkout and HEAD
must remain unchanged. Working resource edits within the reviewed allowlist are
allowed; changes to test assertions, command/limit scope or inventory expansion
require owner review before use. These local checks do not prove a commit has
received human review; the repository workflow supplies that requirement.
Owner withdrawal suspends Native use immediately; renew explicit permission before
resuming. Changed executable identity or expanded scope requires renewed approval.
Test success never broadens the policy or enables unattended scheduling.

All other Godot headless invocations, arbitrary tests, graphical launches,
performance probes, benchmarks, stress/freeze reproduction remain restricted.

## Fresh disposable input copy

The owner-provisioned plain parent is `D:\GameDev\Godot\TLWH-NativeStages`.
It must exist, be readable, have no reparse points and be separate from the source
checkout (neither ancestor nor descendant). No temp/environment fallback exists.
Each plan/run creates a unique `tlwh-native-plan-<GUID>` directory there and never
runs Godot in the checkout. Stages, including partial failures, remain for inspection;
there is no automatic deletion or reuse. Only the fixture's own new inert tree is
removed by its verified cleanup.

Git index regular-file entries select **current tracked working bytes**, including
staged/unstaged edits and staged additions. Untracked files are excluded. Add
intended inputs first; missing/deleted tracked inputs fail closed (stage intentional
deletions first). Unmerged entries, submodules/Git links and filesystem reparse
points fail closed. Preserve paths, bytes, UIDs and import sidecars.

The unchanged allowlist includes `project.godot`, only
`tests/fabricator_recipe_switching_test.gd` and its UID, and reviewed resource
extensions under assets, construction, dialogue, inventory, objectives, scenes and
shaders. Other tests, tools, docs, hidden paths, .git, .godot, artifacts, saves,
settings and credential/secret names are excluded. Filename filters cannot detect
secrets embedded in approved content. No owner save/settings/artwork is deleted.

Source revision, full working status/index and input hashes are captured before
static validation. After actual Python PASS, Native verifies reviewed controls,
copies fresh inputs, compares their hashes with the pre-static snapshot and
rechecks source/stage identity before and after each process. Unexpected stage
contents and links fail closed. A generated `.godot/` tree is allowed only after
clean import; source sidecars and other staged inputs must remain unchanged.
Checks are observational, not an atomic snapshot or a security sandbox.

## Fixed commands, results and preservation

Both commands use the fresh stage as their working directory and `--path`:

| Phase | Exact arguments | Deadline | Combined raw stdout/stderr |
| --- | --- | --- | --- |
| Cold import | `["--headless","--editor","--path","<stage>","--quit"]` | 60 seconds | 1,048,576 bytes |
| Recipe test, only after import PASS | `["--headless","--path","<stage>","--script","res://tests/fabricator_recipe_switching_test.gd"]` | 30 seconds | 1,048,576 bytes |

One engine process runs at a time, sequentially; no automatic retries. Stop on
engine/script/parse errors (including exit zero), assertions, missing/malformed or
duplicate completion, abnormal exit/crash, timeout, overflow, uncertain termination
or identity/input changes. Native PASS requires exactly one completion record as
the last nonempty stdout line:
`Fabricator recipe switching regression failures: 0`. Import needs no such record.

Exit 0 means the requested operations passed; exit 1 means failure. The JSON
summary distinguishes Static, Import, Native, Infrastructure and Authorization
outcomes, provenance, actual attempted commands, bounded diagnostic, evidence path
and evidence-save error. A process not attempted remains NOT RUN; an attempted
phase whose final checks fail is FAIL. Example future outcomes:

- Success: `Static=PASS; Import=PASS; Native=PASS; Infrastructure=PASS` (exit 0).
- Import error: `Static=PASS; Import=FAIL; Native=NOT RUN` (exit 1).
- Recipe failure: `Static=PASS; Import=PASS; Native=FAIL` (exit 1).
- Current disabled gate: `static=NOT RUN; native import=NOT RUN; recipe test=NOT RUN;
  overall=FAIL` (exit 1).

Failure evidence uses ignored `artifacts/logs/native-failure-<GUID>.json` only
after Git confirms the ignored plain destination. Files are exclusively created,
never overwritten, bounded to 64 KiB with at most 4096 diagnostic raw bytes,
revision/executable/stage/attempted commands and status/inventory digests. Evidence
save failure is a separate failure. Success creates no permanent success log.
Preserve stages, bounded failure evidence and all existing owner material under
[the repository preservation policy](../AGENTS.md#generated-files-and-retention).

## Verification limits

Synthetic fixtures cover static propagation, fresh stage selection, fixed command
arrays/deadlines/byte limits, pinned identity and source/index/input protection,
unsafe paths/links/unexpected files, output/completion/error classification,
sequential failure stops, no retries, bounded unique evidence, owner-file
preservation and the disabled public gate. They do not execute Godot or establish
native compatibility, GDScript parsing, runtime assertions or graphical behavior.
The Python baseline assertions and GDScript assertions remain unchanged.

The process helper reads both streams asynchronously. Detection may consume one
read buffer per stream beyond the output ceiling while retaining at most 1 MiB.
Timeout/overflow requests process-tree termination with at most a two-second wait
and reports uncertainty. Normal exit plus EOF certifies only observed process/pipes,
not escaped descendants. Host freeze recovery is not guaranteed; local path/hash
checks do not defend against hostile concurrent changes. Never start concurrent
runner invocations or retry an uncertain termination without owner direction.

Actual import compatibility, Godot parsing/completion output, process containment,
first-run host stability and graphical behavior remain **unverified**. A Godot
import that rewrites tracked sidecars will correctly fail these preservation checks
and needs review; this assignment does not authorize trying it.
