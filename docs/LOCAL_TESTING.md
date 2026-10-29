# Local testing runner (first-run review preparation, pending merge)

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
PowerShell children only. It never executes Godot.
Git and Python resolve to the first application on PATH; use trusted local
installations. The runner has no GitHub API or GitHub CLI dependency and performs
no engine discovery.

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
The proposed first-run review scope also includes the absolute runner path,
tracked runner/policy/static-suite/documentation/fixture control hashes, index
digest, evidence directory, one attempt per phase and one concurrent process.
NativePlan now captures source identity/input hashes before the static suite and
rejects changes against that snapshot before producing the scope. Its JSON is
console review data only: no gate reads it, and neither a matching scope nor
synthetic PASS authorizes execution. Controls may have working changes during
planning; their hashes describe those bytes, not an approved runner commit.

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

The workflow has two distinct owner decisions:

1. **First-run authorization:** after runner review, present the exact reviewed
   runner commit, absolute executable path and SHA-256, source revision and
   working status/input hashes, newly created external stage, both complete
   command arrays, deadlines/output limits, evidence destination and stop
   conditions. NativePlan supplies nonexecuting stage/input/command data; record
   its provenance for owner review. Obtain separate explicit owner authorization
   for the first real run in the owner conversation/review record. No GitHub
   comment, expiring token or network approval service is required. This PR and
   its merge do not supply that authorization. A later reviewed activation change
   must bind the gate to that exact approved first-run scope before execution.
2. **Routine authorization:** only after the first real import and recipe test
   have both passed and their results have been reviewed may the owner separately
   approve a narrowly scoped repository execution policy. Record the accepted
   first-run evidence and explicit routine authorization in that later policy.
   Define allowed runner/executable identities, commands/limits, source and working
   input variation, local invocation scope, evidence handling, revocation and
   reapproval requirements. That policy may permit repeated runs within its scope
   without asking for a new GitHub comment each time. Changes outside its scope
   require renewed owner review. Successful first-run validation must never
   automatically activate routine or unattended testing.

**Current implementation:** `Assert-NativeExecutionAuthorization` fails closed
unconditionally. Public `-Mode Native` exits 1 before prerequisites, staging or
process calls, regardless of console type, flags, environment or local files.
The internal dispatcher checks the same gate before its sequence and each
prospective launch. It remains available for non-Godot scoped mocks only.
There is deliberately no approval-record loader, online identity check,
expiration timer, interactive authorization prompt or self-activation switch.
Neither stage can be enabled by editing prose or by merging this PR. A separate
owner-authorized activation change is still needed; first-run and routine
permissions have not been granted by this workflow simplification request.

### First-run checklist and separate activation patch

This preparation patch leaves the gate unchanged. The minimal second patch must
be reviewed and separately authorized before any engine invocation. It must:

1. Bind the exact reviewed runner commit and control hashes, source checkout and
   revision, working status/index digest and complete tracked input hashes.
   Replan after committing/reviewing changes; a precommit plan is not that scope.
2. Bind the owner-verified absolute **Windows Godot 4.7.2** executable path and
   SHA-256. Both are **pending owner verification**; this implementation does not
   search for an installation or invoke version/help to infer them.
3. Bind one fresh, external, pristine stage and its input hashes, the two complete
   argument arrays in the table below, 60/30-second deadlines and 1,048,576-byte
   per-process output caps. Current Native dispatch generates another random
   stage; the later patch must validate/use the exact reviewed stage rather than
   silently substitute a different one. Revalidate source, stage, controls and
   executable immediately before each launch, after actual static PASS.
4. Bind the absolute evidence directory and failure stops below. Preserve all
   source/stage/owner files. Stop if authorization is withdrawn or any identity
   changes. No arbitrary flags, scripts, scenes, retries or parallel launches.
5. Consume the single authorized attempt **before** import, including failed or
   interrupted attempts. The later reviewed patch must specify an exclusively
   created, fail-closed attempt receipt at an owner-approved destination and
   refuse reuse or uncertain receipt state across process restarts. A receipt
   records consumption; it must never serve as a loadable approval or bypass.
   Do not implement activation as merely replacing the unconditional throw with
   an identity comparison: that would permit repeated runs. Review any receipt
   failure/race handling and authorization revocation before activation.
6. Record explicit owner authorization of that exact activation revision and
   scope in the owner conversation/review record, then permit only that one
   attempt. Do not interpret merging either patch as execution permission.
   Keep routine/unattended execution inactive after PASS or failure; a later
   routine policy remains a separate decision.

The current code emits review data and tests its identity checks only. No attempt
receipt, approval loader, activation parameter or live authorization path is
implemented here. The second patch and exact first-run owner decision remain
outstanding; no GitHub-comment gate or online approval service is proposed.

The dormant static-to-dispatch wiring still requires actual Python static-suite
PASS (normal exit, zero exit code and certain termination). It captures source
identity and input hashes before the suite and compares them with the external
stage. Before each prospective engine call it rechecks local reviewed-runner identity, rejects
working/staged runner, policy or Python static-suite changes, and checks source
revision, working status/index, approved inventory and source/stage hashes, links and
unexpected files; the pinned absolute executable is rehashed last. These checks
remain mandatory in any later activation change, including routine use.

Only these two sequential argument arrays exist:

| Phase | Exact arguments (stage substituted) | Deadline | Combined raw stdout/stderr |
| --- | --- | --- | --- |
| Cold import | `["--headless","--editor","--path","<stage>","--quit"]` | 60 seconds | 1,048,576 bytes |
| Recipe test, after import PASS only | `["--headless","--path","<stage>","--script","res://tests/fabricator_recipe_switching_test.gd"]` | 30 seconds | 1,048,576 bytes |

The dispatcher accepts no arbitrary executor or alternate launch route. It stops
without retries on engine/script/parse errors (including zero-exit errors),
assertion failure, absent/malformed/duplicate completion, abnormal exit, timeout,
output overflow, uncertain termination, or identity/input changes or withdrawn authorization.
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

Synthetic tests cover fixed arrays/deadlines/byte limits, actual static-result
wiring, the inactive first-run/routine gate, rejection of invented approval
switches, absence of online approval machinery, sequential failure stops,
authorization withdrawal, source/index/stage/executable mutation, completion
classification and bounded unique evidence. Public-gate spies require zero
prerequisite, staging or process calls even with an environment override.
First-run review fixtures additionally check scope provenance/control hashes,
static-snapshot changes, stage/executable changes, missing control identity and
continued denial after repeated successful planning. They use inert files only.
Only mocks establish the prospective native behavior. Python assertions and
GDScript assertions are unchanged; report Python and PowerShell fixture counts
separately from unexecuted engine tests.

The process helper asynchronously reads both streams, retaining at most 1 MiB
combined raw output and 4096 diagnostic bytes. Detection may consume one read
buffer per stream beyond the ceiling. Timeout/overflow requests process-tree
termination with at most a two-second wait, always reporting uncertainty. Normal
exit plus EOF certifies only observed process/pipes, not escaped descendants.
A stage is not a security sandbox; host-wide freeze recovery is not guaranteed.
Local path/hash checks do not defend against hostile concurrent filesystem
changes. Future first-run activation and routine-policy enforcement remain
unimplemented until separately authorized and reviewed; no unattended scheduling
or automatic promotion from first-run success is present.

Actual Godot import compatibility, parsing, native assertions/completion output,
process containment, graphical behavior and host stability remain **unverified**.
No Godot invocation (including --version/--help), VM/SSH, CI, benchmark, prolonged
run or freeze reproduction is authorized by this code-only assignment.
