# Isolated save codec runner — preparation only

M5-39 Option A, issue [#165](https://github.com/interneth3ro/the-long-way-home/issues/165).
This dependent draft is based on codec [PR #172](https://github.com/interneth3ro/the-long-way-home/pull/172),
`codex/m5-sav-codec` at `c048787628843719f693ae0116458242d41b0ead`.
Runner preparation is on `codex/m5-codec-runner-preparation`, targeting the codec
branch so its PR diff excludes the codec implementation. Neither PR is merged.
The codec and its runtime assertions are unchanged by this preparation.

**Godot import/runtime: NOT RUN — OWNER AUTHORIZATION REQUIRED.**

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
evidence creation**. Case variations also deny. The source function
`Assert-CodecAuthorization` unconditionally throws and accepts no inputs. It is
also the first statement of direct dispatch, stage creation and engine-phase
helpers. There is no CLI, environment, local-file, token, alternate-script,
callback, executable or config activation mechanism. Command planning and result
classification helpers are data-only; they do not launch a process or stage.

The proposed pipeline below exists behind the gate for review and inert testing.
Preparing, passing static tests, pushing or merging this PR **does not authorize execution**.
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
uses APPDATA for config/data and LOCALAPPDATA for caches; actual pinned-engine
behavior remains unverified until a separately authorized run. No owner settings
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

Review the dependent PR diff, full runner/template, reused helper controls,
synthetic assertions, static results, exact hashes/commands and this contract.
Resolve any input revision change through a new reviewed pin update; do not edit
the codec or runtime assertions to make runner preparation pass. Review any such
blocking codec issue separately.

Then obtain **separate explicit owner execution authorization** naming the reviewed
revision and bounded scope, and prepare a reviewed source activation amendment
consistent with [AGENTS.md](../AGENTS.md#godot-execution-safety). The amendment must
define grant consumption/restoration and failure stops; this PR adds no standing
permission. Recheck all inputs/controls and actual static PASS before any engine
attempt. Preparing or merging either PR never consumes or supplies an execution
grant. Until then the gate stays an unconditional rejection, and codec parse,
import, runtime assertions and independent file reopening remain unverified.
