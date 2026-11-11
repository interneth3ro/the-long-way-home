# Isolated save codec runner — merged and inactive

For issue [#165](https://github.com/interneth3ro/the-long-way-home/issues/165),
the standalone codec, M5-39 isolated runner and M5-40 one-time authorization
safeguards are merged:

| PR | Scope | Merge commit |
| --- | --- | --- |
| [#172](https://github.com/interneth3ro/the-long-way-home/pull/172) | Codec foundation | `0f151a35c5c5aed6b5ebf2c7343420d03097bdf1` |
| [#173](https://github.com/interneth3ro/the-long-way-home/pull/173) | Isolated runner | `693817e6f8732b89cbe120ef8e4a82ea6960c934` |
| [#174](https://github.com/interneth3ro/the-long-way-home/pull/174) | Inactive authorization safeguards | `b2644d091d368b64e20d5745c6ba933e78637157` |

The original codec baseline is `c048787628843719f693ae0116458242d41b0ead`;
runner preparation was reviewed at `a2206096be202c8b3b0341e96039fb0f5bb815a0`.
The PRs were originally stacked drafts. Their merges do not authorize execution.
The merged runner returns `PREPARED`; the only historical codec runtime grant
is consumed. The codec and runtime assertions were unchanged by runner preparation.

Five historical preservation tests also recognize the now-tracked dedicated
runner through a shared exact-source SHA-256 check in its static test module.
Only that one path, at the reviewed PR #173 or prepared amendment identity, is
accepted; the defined activation line is normalized for identity comparison.
Other code, commands, limits and paths remain protected. This test exception is
not authorization to execute the runner.

## Historical M5-42 validation and restoration

One explicitly authorized isolated invocation ran at activation commit
[`8ae6e6fb040a10c7384d01f62b7b60751326c531`](https://github.com/interneth3ro/the-long-way-home/commit/8ae6e6fb040a10c7384d01f62b7b60751326c531),
a direct child of reviewed inactive preparation
`5f02aec5194413a4bc917b84edb1f151bce67394`.

| Phase | Historical result |
| --- | --- |
| Preflight | PASS |
| Static validation | 515 tests; 513 passed, two optional skips |
| Static duration | 320.473 seconds |
| Isolated cold import | PASS |
| Godot codec runtime | 261 checks, zero failures |
| Independent file reopening | PASS |
| One-time authorization | CONSUMED |

Completion: `SAVE_FILE_CODEC: PASS checks=261 failures=0`.
The runner did not retain exact engine-phase durations. This validates the
standalone synthetic codec scope, not gameplay save/load or performance.

M5-43 restored `return 'PREPARED'` in
[`d544160b92bd488cd29374e505051b1cbb9e64a2`](https://github.com/interneth3ro/the-long-way-home/commit/d544160b92bd488cd29374e505051b1cbb9e64a2).
The restored tree exactly matches reviewed inactive preparation `5f02aec`.
Both commits remain preserved on remote branch
`codex/m5-codec-one-time-activation`; they were not rewritten into the merged PRs.

Retained evidence remains at the original external paths:

- Consumption record: `D:\GameDev\Godot\TLWH-NativeStages\codec-grant-5f02aec5194413a4bc917b84edb1f151bce67394.consumed.json`.
- Isolated validation stage: `D:\GameDev\Godot\TLWH-NativeStages\tlwh-codec-1994fd3302d64e2784d698ddbcadb1c6`, including approved generated outputs.

The historical M5-42/M5-43 reports in the **Add serialized SAV codec** chat
record the run and restoration checks. Preserve the consumption record, stage
and retained runtime evidence. Do not delete, reset or reuse them.

**Current authorization: none for codec execution.** The grant is consumed;
fresh explicit owner approval and a newly reviewed activation are required
before any future import or codec runtime attempt. No runner invocation or
Godot execution was performed for this documentation reconciliation.

## Entry points and inactive gate

[`tools/run-save-codec-tests.ps1`](../tools/run-save-codec-tests.ps1) is separate
from the existing local runner. It dot-sources that runner only for established
bounded-process, plain-path, Git-identity and pinned-engine helpers. It preserves
its own requested mode before dot-sourcing (the existing script has a `Mode`
parameter). Existing Native and MetadataSmoke authorization/behavior, historical
grants, limits and the existing 60-second static timeout are unchanged.

Permitted non-Godot preparation checks:

```powershell
pwsh -NoProfile -File tests/save_codec_runner_fixture_test.ps1
pwsh -NoProfile -File tools/run-save-codec-tests.ps1 -Mode Static
```

Default invocation and `-Mode Run` both return exit 1 and explicit
`AUTHORIZATION_DENIED` **before source preflight, any process, stage, profile or
evidence creation** in the prepared source. Case variations also deny. The
no-input source function `Get-CodecGrantTransition` returns the literal
`PREPARED`; `Get-CodecGrantedRevision` rejects it before any filesystem lookup.
The continuation guard `Assert-CodecAuthorization` is also the first statement
of direct dispatch, stage creation and engine-phase helpers. There is no CLI,
environment, local approval-file, alternate-script, callback, executable or config
activation mechanism. A consumption tombstone can deny, never grant, execution.
Command planning and result
classification helpers are data-only; they do not launch a process or stage.

The proposed pipeline below exists behind the gate for review and inert testing.
Preparing, passing static tests, pushing or merging these PRs **does not authorize execution**.
The mechanism is a trusted-checkout workflow boundary, not a sandbox against
someone rewriting PowerShell functions or maliciously editing reviewed source.
Scoped named doubles exist only in inert fixtures; production has no injected
executor or test bypass parameter.

## Exact source inventory and staging representation

Only these three tracked inputs participate in staging:

| Source | Stage path | SHA-256 of reviewed UTF-8/no-BOM/LF bytes |
| --- | --- | --- |
| `tests/fixtures/save_codec/project.godot` | `project.godot` | `37985F18F83537EC2265306776348FDB0FCAE41A08CD27908F107AED7BDB10F9` |
| `persistence/save_file_codec.gd` | same | `0348779F7170346D4293823F2D118F56FFFFD44F2CC971134D79560A971F5253` |
| `tests/save_file_codec_test.gd` | same | `D816238FF1C5046AEC4F3C5109F76CB6D75F8DDD67E3C82001555ACA0EDC7E41` |

No gameplay project manifest, scene, artwork, resource, save, autoload, tool,
untracked UID or other project content is copied. The minimal manifest has only
`config_version=5`, application name and custom user-data configuration. Its
single `__STAGE_ID__` placeholder is replaced with the fresh stage's lowercase
32-digit GUID. That derived manifest's final bytes/hash are captured in the
stage inventory. It sets `config/custom_user_dir_name="TLWH-codec-<GUID>"`.

Working text is decoded as strict UTF-8 and only CRLF is converted to LF for the
reviewed hash/stage copy. There is no other normalization. The same raw read is
also hashed; both raw and canonical hashes are captured and rechecked. Thus
normal Windows checkout line endings are accepted, while edits (including later
line-ending changes during the run) are rejected. Files must be regular tracked
inputs, at most 1 MiB each, with the exact pins above. This is not an input override.

Before static validation the proposed Run path verifies:

- Actual checkout root and exact origin repository URL, a revision descended from
  the reviewed codec commit, complete working status and regular-file index.
- Runner, helper, policy, ignore/attribute rules, guide, fixture and Python static controls match HEAD;
  required new runner controls and all stage sources must be committed/tracked.
  Untracked Python files matching static-suite discovery are rejected before Run
  can execute them; Static preparation itself permits the newly authored tests.
- Reviewed canonical input hashes and raw working bytes, and the pinned engine.

Unrelated/untracked files are preserved and excluded. Their status is captured;
any source revision/status/index/input change during a run causes failure. A
local hash does not certify owner review: the activation workflow supplies that.

## Proposed fixed workflow after separate activation

1. Capture preflight identity and input hashes; verify the engine without invoking
   it. Run inert fixtures (60-second bound), then actual full Python static suite:
   `python -B -m unittest discover -s tests -p 'static_*test.py'`.
   Require clean process termination, exit zero, `Ran ... tests` and `OK` summary.
2. **Static bound: 600 seconds.** The observed prior full run was about 335 seconds;
   360 leaves little headroom, while 600 gives roughly 79% headroom and remains
   bounded. Timeout at either 60 or 600 seconds is failure, never PASS. This changes
   only the proposed codec workflow, not the existing Native runner.
3. Recheck source identity, then create exactly one new
   `D:\GameDev\Godot\TLWH-NativeStages\tlwh-codec-<GUID>` directory. The parent
   must already exist and be plain. Reject source/parent overlap in either
   direction, relative paths, traversal, links and reparse points. Never reuse,
   overwrite or automatically remove a stage, including partial failures.
4. Copy only the three reviewed inputs and record their final hashes. Reject
   unexpected staged files/directories or changed/missing inputs. Run commands
   sequentially as shown below, with stage as working directory and `--path`.
5. Before and after each phase, recheck source/stage identity and engine hash.
   Only after clean import may the codec phase run. Any failure stops the sequence;
   there are no automatic retries and at most one attempt at each command.

The only proposed engine is:

`D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`

SHA-256: `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.

| Phase | Exact arguments | Bound |
| --- | --- | --- |
| Cold import | `--headless --editor --path <fresh-stage> --quit` | 60 seconds |
| Codec, only after clean import | `--headless --path <fresh-stage> --script res://tests/save_file_codec_test.gd` | 30 seconds |

There are no executable, project, script, scene, argument, deadline or inventory
overrides. The executable is rehashed immediately before each launch. No fallback,
version/help probe, playable scene or graphical execution is included.

Immediately around each proposed engine process, the runner sets its own
process-local `APPDATA`, `LOCALAPPDATA`, `TEMP` and `TMP` to fixed children of
`<fresh-stage>/.codec-profile/` (`appdata`, `localappdata`, `temp`). It restores
the previous process values in `finally`, including on failure. These are fixed
output-isolation paths, never authorization switches or user-selected overrides.
The engine child inherits them through the unchanged bounded-process helper.
Godot's [Windows platform implementation](https://github.com/godotengine/godot/blob/master/platform/windows/os_windows.cpp)
uses APPDATA for config/data and LOCALAPPDATA for caches; the historical M5-42 run
passed with this profile configuration; it does not prove OS access isolation.
No owner settings
or saves are staged or intentionally accessed. This is process configuration,
not a filesystem access-control sandbox.

After clean import, only `.godot/` cache, `.codec-profile/` profile/test outputs,
and the two exact optional generated script sidecars
`persistence/save_file_codec.gd.uid`, `tests/save_file_codec_test.gd.uid` are allowed
outside the input inventory. Sidecars must be small scalar `uid://...` records;
the observed set and hashes (including an empty set) are frozen after import and
must stay unchanged through the codec phase. All generated trees are traversed
only after plain-path checks; source inputs always remain hash-pinned. These are
prospective stage outputs, not permission to add anything to the source checkout.

## Results, limits and evidence

Every process has a **1,048,576-byte combined stdout/stderr limit**. Retained
diagnostics are at most **4,096 UTF-8 bytes**, without splitting code points.
The reused bounded helper stops on timeout/overflow, attempts bounded process-tree
termination and reports uncertainty. Uncertain termination is always failure;
no later engine phase is allowed. Result classification also rejects nonzero or
abnormal exit, engine/script/parse/assertion/crash diagnostics and excessive
reported or actual output even if exit is zero.

Codec success additionally requires exactly one completion record across both
streams, as the last nonempty stdout line, matching exactly:

```text
SAVE_FILE_CODEC: PASS checks=<positive decimal integer> failures=0
```

Missing, malformed, zero-check, duplicated, contradictory, stderr-only and
misplaced records fail. Import needs no codec completion marker. A successful
result does not expand permissions or certify numerical/gameplay behavior.

On a future authorized failure, retain the stage and uniquely create ignored
`artifacts/logs/codec-failure-<GUID>.json`, never overwriting previous evidence.
Require Git's ignore confirmation, plain paths, exclusive creation and a 64 KiB
record cap. Evidence contains revision, fixed requested commands, phase results,
stage, a digest of captured identity/input inventory and bounded diagnostic;
no whole source/status/index dump or unbounded output. Evidence-write failure is
reported separately and prevents success. Denial writes no evidence; successful
runs create no permanent success report. No production cleanup is implemented.
The ignored/plain destination is checked before staging and again when saving
failure evidence. A partial stage-copy failure attaches its fresh directory to
the failure result so that retained partial stages remain identifiable.

The inert fixtures use only fresh GUID-named temp trees, synthetic records,
scoped named doubles and harmless PowerShell children. They create no real
runtime stage and never invoke Godot. Recursive fixture removal verifies the
absolute task-owned target and plain ancestry first. Source files, protected UID,
real stages and unknown files are not cleanup candidates.

## Review and activation

For a future authorization, review the merged baseline and proposed activation
diff, full runner/template, reused helper controls,
synthetic assertions, static results, exact hashes/commands and this contract.
Resolve any input revision change through a new reviewed pin update; do not edit
the codec or runtime assertions to make runner preparation pass. Review any such
blocking codec issue separately.

Then follow the one-time procedure below, consistent with
[AGENTS.md](../AGENTS.md#godot-execution-safety). This adds no standing permission.
Preparing or merging a PR never consumes or supplies an execution grant. The
source transition remains `PREPARED`; historical parse/import, runtime
assertions and independent file reopening passed under M5-42. They confer no
permission for another run.

## M5-40 one-time activation procedure — not authorized now

Four approvals are distinct: preparation approval permits this inactive code;
source activation approval permits only the reviewed transition commit; actual
Godot execution approval names one invocation and scope; merge approval permits
only merging a specific PR. None implies another. Do not schedule or retry runs.

| Lifecycle | Meaning |
| --- | --- |
| Prepared | Reviewed source returns `PREPARED`; default/Run and direct runtime helpers deny. |
| Authorized | Owner explicitly approves the exact prepared revision, source activation and one allowed invocation; the one-line activation is committed/reviewed. |
| Consumed | An invocation begins by exclusively claiming its tombstone before binding/preflight, then verifies its record before dispatch/static validation/staging/engine. Every outcome spends the attempt. |
| Restored | The source returns `PREPARED` again; restoration and denial are independently verified. Tombstone and evidence remain preserved. |

Let **P** be the exact 40-character lowercase SHA of the final reviewed inactive
preparation commit containing this amendment, not merely the older `a220609`
runner baseline. Let **A** be its single-parent direct-child activation commit.
After separate owner approval, A must change **only one line in one file**:

```diff
 function Get-CodecGrantTransition {
-    return 'PREPARED'
+    return 'AUTHORIZED_ONCE:<P>'
 }
```

Replace `<P>` with that exact reviewed commit SHA; it is not a literal token or
CLI argument. No grant is left in this preparation. No other guard, assertions,
inputs, commands, limits or files change in A. The runner requires A's sole
parent to be P, requires the complete tree diff to name only the runner, and
reconstructs the entire exact P runner by replacing only that transition line.
It also performs the existing committed-control/source/index/input-pin checks.
An uncommitted activation, changed codec, extra code/file changes, merge commit,
different ancestry or later unreviewed commit cannot satisfy this binding.
Git ancestry/hashes establish content identity, not the fact of human approval.

The owner must separately authorize the exact invocation
`pwsh -NoProfile -File tools/run-save-codec-tests.ps1 -Mode Run` at reviewed A.
Do not invoke default/Run while merely preparing or reviewing activation.
The grant covers at most one fresh external stage, one cold import, then one
codec test only after clean import, with the unchanged scope and limits above.

At entry with a source authorization transition, the runner exclusively claims
the fixed non-authorizing tombstone before binding/preflight:

`D:\GameDev\Godot\TLWH-NativeStages\codec-grant-<P>.consumed.json`

The existing plain parent must already exist. No directory is created for this
record. `CreateNew`/`FileShare.None` prevents another owner/process from claiming
the same record. The empty claim is flushed first: a failed binding or interrupted
preflight already consumes it. While holding that claim, verify source binding;
`WriteThrough`, `Flush(true)` and record readback are required before dispatch.
The bounded record contains workflow, CONSUMED state, P, A, captured
identity/input digest and UTC start time. It is never an approval input: any
existing file or directory, including empty, malformed or partially written
content, rejects entry without interpreting its contents. There is no overwrite,
deletion, reset, loading/adoption of a receipt or token-based resume path.

The invoking process keeps the exclusive stream until its outer `finally`.
Direct helpers require that live owned stream, unchanged source binding and
record bytes, and the next single-use step. The sequence is Dispatch → Stage →
Import → clean import result → Codec → clean codec result → Done. Each action's
permission is spent before the action. Only the existing successful post-phase
checks advance to the next engine phase. Closing clears the process context;
the persistent tombstone remains. This is not an in-memory-only single-use flag.
An exception, failed static suite, partial stage, failed import/test, timeout,
uncertain termination or abrupt process exit never automatically retries or
releases a recorded grant. A new process cannot adopt the old stream/record.

After **any** attempt (including uncertain or interrupted attempts), stop. Preserve
the tombstone, stage and existing bounded failure evidence. Do not delete or
rename records to reuse P, and do not infer a retry from a repaired test or PASS.
Report the outcome and any uncertain termination before further execution.

Restore the source transition to `return 'PREPARED'` through an explicit reviewed
restoration change/commit; do not reset or rewrite history. Independently inspect
that source line and the restoration diff, parse PowerShell, and run the inert
denial fixtures plus default/Run denial in fresh PowerShell processes. Verify
that no process/stage action follows denial and that the codec/runner contract
and tombstone remain unchanged. Do not test restoration by attempting an active
run. If source restoration or process termination cannot be verified, report
that condition and prohibit further engine execution. The merged PR prepared
this procedure without performing activation/restoration
or writing a real record; the separate historical M5-41–43 work above did so.

**Durability limitation requiring owner review:** this is a workflow control,
not guaranteed crash-safe or power-loss-durable single-use enforcement. Process
interruption after a retained record is handled by exclusive creation/existence
denial (tested with inert PowerShell processes). Filesystem/hardware loss,
external deletion/rollback, or failure before creation persists cannot provide
a durable history. If consumption cannot be created, flushed or verified, no
dispatch is permitted; consider the grant consumed by policy, restore PREPARED
and do not retry even if storage is later repaired. The runner cannot prove that
such a never-persisted record existed. It also cannot itself prove later manual
source restoration or owner approval. No automatic source mutation, Git commit,
record cleanup or standing authorization is implemented. A fresh attempt always
requires fresh owner approval against a newly reviewed inactive revision.

Inert tests use synthetic revision values and tombstones **only in unique
test-owned temporary trees**, with scoped named doubles. They test failed
consumption, out-of-order/repeated steps, failure consumption, restored denial
and an abruptly exiting harmless PowerShell child followed by a denied second
process. They never activate tracked source, write a real tombstone, create a
real external Godot stage, call an activated production Run entry point or
launch Godot. During a future separately authorized attempt, static fixtures
accept the reviewed source transition only as an already-consumed grant; direct
helpers in those child test processes still have no invocation context and deny.
Fixtures refuse an unconsumed activated source before creating temporary files
or probing entries. Real default/Run CLI denial probes run only on PREPARED
source; they are not invoked against activated source during future static work.
In-process prepared-entry denial probes use a scoped PREPARED source-state double.
