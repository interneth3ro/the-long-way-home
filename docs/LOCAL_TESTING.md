# Local testing runner (Stage B feature branch, pending merge)

Use PowerShell **7+** on Windows, Git and Python on PATH, from the actual checkout:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1
pwsh -NoProfile -File tests/local_runner_fixture_test.ps1
```

The first command runs the unchanged static suite:
`python -B -m unittest discover -s tests -p 'static_*test.py'`.
Its historical Git baselines must be available. Exit 0 means requested operations
passed; exit 1 means failure. Static success is not engine or runtime validation.
The fixture suite uses inert temporary files, named helper mocks and harmless
PowerShell children only. It neither executes Godot nor posts GitHub comments.
Git, Python and (for Native only) authenticated GitHub CLI `gh` resolve to the first
application on PATH; use trusted local installations. No engine discovery occurs.

## Native planning only

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode NativePlan `
  -GodotPath 'C:\absolute\reviewed\Godot.exe' -GodotSha256 '<64 hexadecimal SHA-256 characters>'
```

Supply a real absolute path/hash to plan; the example is deliberately incomplete.
NativePlan never invokes that binary, including for version/help. Static and
NativePlan never call the restricted native dispatcher or request authorization.
After static PASS, planning prints executable identity, source revision/status,
stage path, every approved input/hash, and both fixed command arrays and limits.

Git index regular-file entries select inputs copied from **current working files**,
including tracked staged/unstaged edits and staged additions. Untracked files are
excluded; add intended new inputs first. Missing/deleted inputs fail closed; stage
intentional deletions first. Unmerged entries, Git links/submodules and filesystem
reparse points fail closed. The inventory allows `project.godot`, only the recipe
switching test and its UID, and reviewed resource extensions under assets,
construction, dialogue, inventory, objectives, scenes and shaders. Paths, UIDs,
import sidecars and bytes are preserved. Other tests, tools, docs, hidden paths,
.git, .godot, artifacts, saves, settings and credential/secret names are excluded.
Filename filters cannot detect secrets embedded in approved content. Inventory
expansion requires review.

Each plan/run creates a new `tlwh-native-plan-<GUID>` under OS temp, outside the
checkout. Source and copy hashes are compared. Stages (including partial failures)
remain for inspection; the runner never deletes owner files or stages. These are
observational checks, not an atomic snapshot: avoid editing during a plan/run.
Only the fixture's freshly created synthetic tree is removed by the fixture.

## Controlled native activation (Stage B, pending merge)

**No first engine run or recurring native run has been authorized. Godot was NOT
RUN during this implementation.** Merge and the conditional policy amendment in
[AGENTS.md](../AGENTS.md#godot-execution-safety) do not authorize execution.

After review and merge, the owner may start the following command in their own
interactive console to prepare a request for a separate exact authorization:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Native `
  -GodotPath 'C:\absolute\reviewed\Godot.exe' -GodotSha256 '<64 hexadecimal SHA-256 characters>'
```

This is not permission for an agent to start Native now. It does not accept scripts,
scenes, extra engine arguments, test lists, timeouts, approval files, callbacks,
environment overrides or an approval switch. Redirected console input/output is
rejected before prerequisites. Dot-sourcing internal helpers is for non-Godot
fixtures only and never supplies owner approval.

The first-run process is:

1. Require actual static-suite PASS (normal exit, zero code, certain termination).
   Capture source identity and approved input hashes before static checks and
   compare them with the subsequent stage. Any observed change stops the run.
2. Create a fresh external copy. Check the exact source HEAD against live GitHub
   `main` through the read-only authenticated CLI. Refuse working/staged changes
   to tools, AGENTS.md or the Python static tests. The runner must reside at the
   checkout's reviewed path. Gameplay working changes remain visible in the exact
   inventory and must receive separate approval with that specification.
3. Display the entire canonical JSON specification: merged runner/source commit,
   source path, full working status/index, all input hashes, fresh stage, absolute
   executable and SHA-256, both command arrays and deadlines/output limits,
   ignored evidence destination, diagnostic/termination limits, no retries and
   every stop condition. Review all fields before authorizing.
4. Within ten minutes of that display, the owner `interneth3ro` must post a **new**
   issue/PR conversation comment in `interneth3ro/the-long-way-home`, containing
   exactly the displayed text `I authorize one TLWH native run: <specification SHA-256>`.
   This is the separate explicit owner authorization, not a PR merge/review.
   Agents must not create this authorization comment for the owner. Paste its
   full `https://github.com/interneth3ro/the-long-way-home/pull/<number>#issuecomment-<id>`
   (or `/issues/`) URL at the runner prompt. Blank input denies.
5. The runner verifies the comment via GitHub's read-only API: exact repository,
   URL, owner login and User type, exact body and fresh creation time. Missing,
   denied, malformed, stale, non-owner, mismatched or unavailable records fail
   closed. There is no local-record fallback and no secret approval token.
6. Exclusively create `<stage>.approval.json` beside the external stage, recording
   the specification, hash, owner-comment URL and expiration. Existing files are
   never overwritten. This is an authorization record, not a permanent success
   log. Each new invocation creates another stage/hash and needs a new comment;
   the runner has no resume, record-loading, replay or automatic retry route.
7. Before **each** engine call, revalidate live merged revision, approval comment,
   expiry, unchanged local record, source revision/status/index, approved inventory,
   source/stage hashes and no links/unexpected files. Rehash the absolute pinned
   executable last, immediately before dispatch. Editing/deleting the comment
   revokes subsequent phases. Expiration is ten minutes from display, including
   review time; an already-started bounded process may finish after expiry.

Only these two sequential argument arrays exist:

| Phase | Exact arguments (stage substituted) | Deadline | Combined raw stdout/stderr |
| --- | --- | --- | --- |
| Cold import | `["--headless","--editor","--path","<stage>","--quit"]` | 60 seconds | 1,048,576 bytes |
| Recipe test, after import PASS only | `["--headless","--path","<stage>","--script","res://tests/fabricator_recipe_switching_test.gd"]` | 30 seconds | 1,048,576 bytes |

The dispatcher accepts no arbitrary executor or alternate launch route. It stops
without retries on engine/script/parse errors (including zero-exit errors),
assertion failure, absent/malformed/duplicate completion, abnormal exit, timeout,
output overflow, uncertain termination, or identity/input/approval changes.
Native PASS requires exactly one completion record, as the last nonempty stdout
line: `Fabricator recipe switching regression failures: 0`. Import requires no
completion record. Only a generated `.godot/` tree is allowed after import, with
no linked descendants. Rewritten source sidecars cause validation failure.

The returned summary distinguishes Static, Import, Native, Infrastructure and
Authorization outcomes, provenance, attempted commands, reason, bounded diagnostic
and evidence-save error. Pre-dispatch refusal leaves both engine phases NOT RUN;
failed import leaves Native NOT RUN. Actual command attempts are recorded even
when their final validation fails. Successful runs create no permanent success log.

Failures retain exclusively created `artifacts/logs/native-failure-<GUID>.json`
only after Git confirms the location is ignored and path checks reject links.
Evidence is capped at 64 KiB and includes outcomes, commit, executable/stage,
attempted arrays/limits, reason, at most 4096 diagnostic raw bytes, and SHA-256
digests of working status and the input inventory. The console summary contains
the full inventory/status. Save errors remain separate failures; owner files are
never overwritten or deleted. Follow the [preservation policy](../AGENTS.md).

## Validation and remaining limits

Synthetic tests cover fixed arrays/deadlines/byte limits, static gating, approval
denial/expiry/owner/repository/hash/URL mismatches, offline API, exclusive records,
record mutation, stage replay rejection, sequential failure stops, source/index/
stage/executable mutation, completion classification, and bounded unique evidence.
Only mocks establish the prospective native behavior. Python assertions and
GDScript assertions are unchanged; report Python and PowerShell fixture counts
separately from unexecuted engine tests.

The process helper asynchronously reads both streams, retaining at most 1 MiB
combined raw output and 4096 diagnostic bytes. Detection may consume one read
buffer per stream beyond the ceiling. Timeout/overflow requests process-tree
termination with at most a two-second wait, always reporting uncertainty. Normal
exit plus EOF certifies only observed process/pipes, not escaped descendants.
A stage is not a security sandbox; host-wide freeze recovery is not guaranteed.
GitHub author identity relies on the owner's account and trusted CLI/API; local
path/hash checks do not defend against hostile concurrent filesystem changes.

Actual Godot import compatibility, parsing, native assertions/completion output,
process containment, graphical behavior and host stability remain **unverified**.
No Godot invocation (including --version/--help), VM/SSH, CI, benchmark, prolonged
run or freeze reproduction is authorized by this code-only assignment.
