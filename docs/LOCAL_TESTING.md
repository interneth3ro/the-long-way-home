# Restricted local testing runner

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

The separate [local behavioral foundation](#local-behavioral-foundation-inactive)
is inactive. The standing staged Native scope below does not authorize it or
execution in the actual checkout.

On **2026-10-29**, the owner approved standing routine use of the existing
restricted Native runner, superseding the earlier one-invocation permission after
PR #75. Only the fixed cold import and recipe-switching phases below are covered.
The dispatcher retains its checks before staging and each prospective launch.
Stop on failure; no automatic retries or unattended runs are authorized. A PASS
or merge does not broaden this scope. See the
[execution policy](../AGENTS.md#godot-execution-safety).

For B1 font compatibility the owner separately authorized staging only the IBM
Plex Sans Regular, Medium and SemiBold `.ttf` files under
`assets/fonts/ibm-plex-sans/` and, after the first B1 run, their three matching
`.ttf.import` sidecars plus one controlled rerun. No executable type, command, test or engine limit is
added. The existing inert fixture checks font byte preservation and rejected
paths/types; this is not a new test framework or Godot test.

On **2026-10-30**, the owner approved tracking the exact IBM Plex Sans Italic
import sidecar, its exact-path LF attribute, and staging only the additional
`assets/fonts/ibm-plex-sans/IBMPlexSans-Italic.ttf` and matching `.ttf.import`.
The sidecar SHA-256 is
`59dcbab3fc80589bdb874f68bfb1cd93e6d979fd96ff56787094500a56d62c20`;
its bytes, UID, import settings and paths are preserved. No other file types,
commands, executable identities, limits or Native assertions are added.
**PR #90 Native execution still requires separate owner authorization.** The
owner's graphical/functional acceptance is 6/6 PASS; it does not authorize Native.


There is no embedded approval scope, self-hash, receipt, environment switch or
local approval file. Authorization is supplied by the owner and repository workflow.
Preserve historical receipts, withdrawal files and evidence; the runner does not
read or delete them.

The authorized invocation, only after preconditions and verification pass:

```powershell
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
Each existing staged plan/run creates a unique `tlwh-native-plan-<GUID>` directory there and never
runs Godot in the checkout. Stages, including partial failures, remain for inspection;
there is no automatic deletion or reuse. Only the fixture's own new inert tree is
removed by its verified cleanup.

Git index regular-file entries select **current tracked working bytes**, including
staged/unstaged edits and staged additions. Untracked files are excluded. Add
intended inputs first; missing/deleted tracked inputs fail closed (stage intentional
deletions first). Unmerged entries, submodules/Git links and filesystem reparse
points fail closed. Preserve paths, bytes, UIDs and import sidecars.

The resource allowlist includes `project.godot`, only
`tests/fabricator_recipe_switching_test.gd` and its UID, and reviewed resource
extensions under assets, construction, dialogue, inventory, objectives, scenes and
shaders, plus the four exact font paths and their four metadata sidecars above.
Other tests, tools, docs, hidden paths, .git, .godot, artifacts, saves,
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
phase whose final checks fail is FAIL. Example outcomes:

- Success: `Static=PASS; Import=PASS; Native=PASS; Infrastructure=PASS` (exit 0).
- Import error: `Static=PASS; Import=FAIL; Native=NOT RUN` (exit 1).
- Recipe failure: `Static=PASS; Import=PASS; Native=FAIL` (exit 1).

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
preservation and authorization-withdrawal stops. They do not execute Godot or establish
native compatibility, GDScript parsing, runtime assertions or graphical behavior.
On the Balanced Simplification maintenance branch, Python checks protect immutable
historical evidence and focused current resource/source contracts. Historical
checkout inventories and test/source admission pins no longer freeze ordinary
development. Runner identity, staging, command, inventory, failure and preservation
controls are unchanged. GDScript recipe-switching assertions remain unchanged.

The process helper reads both streams asynchronously. Detection may consume one
read buffer per stream beyond the output ceiling while retaining at most 1 MiB.
Timeout/overflow requests process-tree termination with at most a two-second wait
and reports uncertainty. Normal exit plus EOF certifies only observed process/pipes,
not escaped descendants. Host freeze recovery is not guaranteed; local path/hash
checks do not defend against hostile concurrent changes. Never start concurrent
runner invocations or retry an uncertain termination without owner direction.

Actual import compatibility, Godot parsing/completion output, process containment,
first-run host stability and graphical behavior require actual verification. A Godot
import that rewrites tracked sidecars will correctly fail these preservation checks
and needs review. A failed first invocation must not be retried automatically.

## Local behavioral foundation (inactive)

The foundation merged in PR #196 at `398a2c9`; its feature branch was retired.
It prepares a small Godot-native workflow; **it grants no execution
authorization**. Current Godot restrictions remain effective. The new launcher
always returns exit 1 and `Behavioral: NOT RUN` with `AUTHORIZATION_DENIED`, before
engine identity checks or process dispatch. There is no CLI switch, environment
variable, approval file or token that enables it. A branch, PR, merge or passing
inert check does not activate it. Do not invoke the dispatcher directly to bypass
the launcher gate.

Proposed local command, currently denied:

```powershell
pwsh -NoProfile -File tools/run-behavioral-tests.ps1
```

After a separately reviewed activation and explicit owner execution approval,
the prepared path would use the pinned executable and SHA-256 from the existing
[identity policy](#authorization-and-standing-scope), with exactly:

```text
<pinned Godot> --headless --path <actual TLWH checkout> --script res://tests/behavioral/test_runner.gd
```

It proposes **one Godot process per suite invocation**, a 30-second deadline,
1,048,576-byte combined output cap and a 4,096-byte diagnostic excerpt. There is
no editor/import preparation, copied project, staging environment, container,
executable/scene/argument override, automatic retry or destructive cleanup.
The launcher dot-sources the existing local runner for helper definitions only,
reusing `Invoke-BoundedProcess`, `Get-StandardGodotIdentity` and `Assert-PinnedEngine`.
It does not call the old dispatcher, static suite, staging or evidence writers.
No existing Native or codec authorization is changed. The inherited process-tree
termination and diagnostic-decoding limitations still apply; uncertain termination
is failure and needs owner direction before any further engine attempt.

### Fixed dispatcher and group contract

[`test_runner.gd`](../tests/behavioral/test_runner.gd) extends `SceneTree`. Its one
explicit manifest entry is `world_coordinates`, backed by
[`smoke_test.gd`](../tests/behavioral/smoke_test.gd). It creates a fresh `RefCounted`
group, synchronously calls `run()` once, retains its data result and releases the
group reference before reporting. `run()` returns a Dictionary with positive
integer `checks` and an Array of failure messages. The dispatcher stops on the
first failed/invalid group, prints group name and diagnostics, and exits nonzero.
It has no dynamic discovery, test selection or migrated legacy tests. The smoke
group makes four calls to the actual production
`WorldCoordinates.world_to_construction()`, checking floor conversion across
negative, positive and exact 32-unit grid boundaries. It creates no scenes or
files and changes no production state.

The engine's successful final nonempty stdout line must occur exactly once across both
streams and match:

```text
TLWH_BEHAVIORAL_V1 PASS groups=<positive integer> checks=<positive integer> failures=0
```

Its group count and total checks must equal the individual stdout group PASS
records. Group names must be unique; malformed, duplicated, contradictory or
stderr-only group records cannot authorize PASS.

Failure prints a `TLWH_BEHAVIORAL_V1 FAIL ...` record and exits 1. The launcher
also fails on missing/malformed/duplicate/misplaced completion, a nonzero process
exit, engine/script/parse/assertion diagnostics even with exit zero, timeout,
output overflow or uncertain termination. `PASS` requires all of these checks;
an unauthorized invocation is `NOT RUN`, never runtime PASS. Group release is
not isolation of autoloads, globals, statics, filesystem writes or leaked external
references. Future groups must declare and release their test-owned resources;
this PR supplies only the scene-free `RefCounted` group.

### Filesystem review and validation boundary

Direct-checkout execution is a proposed departure from the existing external-stage
policy and requires explicit approval of the precise launcher, command, manifest
and allowed filesystem effects. Review Godot's `.godot/` cache, import metadata,
UID generation/rewrites, resource discovery and any user-profile logs/settings
before any run. This launcher provides neither a filesystem sandbox nor cache
rollback. The smoke's lack of file I/O does not prove the engine is write-free.
There is no permission to delete caches, rewrite/publish sidecars, alter owner
files or clean up after a failed attempt. Graphical testing, performance probes,
benchmarks, stress tests and freeze reproduction remain restricted. Any future
standing permission must name the exact reviewed runner and scope.

Non-Godot validation can run the dedicated inert fixtures:

```powershell
pwsh -NoProfile -File tests/behavioral/launcher_fixture_test.ps1
```

These parse PowerShell and use scoped process/identity doubles; they never launch
Godot or create a test project. They validate denial, fixed dispatch and result
classification only. GDScript inspection is static; it does not establish Godot
parsing, loading, completion output, runtime PASS or direct-checkout cache behavior.
The earlier test audit remains local and unchanged; its historical Python failure
baseline is not repaired by this PR.

### First behavioral invocation proposal (inactive)

The preparation amendment merged in PR #197. **It does not activate the launcher
or authorize Godot.** The separately authorized first invocation is recorded below;
its grant is consumed and unconditional denial has been restored.
The production gate still throws unconditionally. The fixture rehearses a
temporary return gate in memory, with inert process doubles, then restores denial
after synthetic success, failure, timeout, output overflow and process exception.
It also checks the fixed identity constants without reading the executable.
No environment switch, token, permission file, persistent grant counter or
general authorization framework is introduced.

After review, a later activation revision may change only the gate's `throw`
statement to `return`. Compare that revision with the reviewed preparation:
the dispatcher, manifest, four production smoke assertions, shared supervisor,
identity and limits must be unchanged. The owner must explicitly approve the
**exact resulting activation revision**, the single invocation and filesystem
scope before any Godot launch. Preparation, merge and inert PASS are not approval.
The temporary return is workflow-controlled, not a technical one-use latch; the
supervisor must prevent a second invocation and restore denial promptly.

The only proposed command is:

```powershell
pwsh -NoProfile -File tools/run-behavioral-tests.ps1
```

Use only `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`, SHA-256
`AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`,
with working directory `D:\GameDev\Godot\Projects\TLWH` and exactly:

```text
--headless --path D:\GameDev\Godot\Projects\TLWH --script res://tests/behavioral/test_runner.gd
```

One process, 30 seconds, 1,048,576 combined output bytes and a 4,096-byte raw
diagnostic excerpt remain fixed. No import/version/help probe, graphical launch,
performance test, automatic retry or concurrent runner is included. The existing
best-effort termination and decoded-diagnostic limitations remain unchanged.

Before the separately authorized invocation:

1. Close applications that could write the checkout or project profile. Confirm
   the reviewed revision, clean tracked/index state and unchanged scope. Preserve
   both untracked `docs/audits/test-suite-audit-2026-11-13` reports (`.md`/`.csv`)
   and all ignored material. Run PowerShell parsing and the inert fixtures on the
   inactive preparation before the temporary gate edit. The denial-specific suite
   must fail against an active gate; after that edit check parsing and the exact
   gate-only diff, obtain approval of the resulting revision, and run the full
   fixtures again after restoration. Unrelated historical Python failures are
   not repaired or waived here.
2. Capture HEAD, Git status including untracked/ignored paths (use
   `git --no-optional-locks status` to avoid index refresh), and index SHA-256.
   Inventory regular files by relative path, byte size and SHA-256: tracked files,
   existing untracked/ignored owner files, `.godot/`, and
   `%APPDATA%\Godot\app_userdata\The Long Way Home\`. Include existing profile
   shader caches, saves/settings and `objectdb_snapshots`, even though changes
   there are not approved. Record Godot editor settings identities separately.
   Do not traverse links; report them and resolve affected scope before running.
   Keep observations in the supervising session; no new inventory tool is needed.
3. Separately obtain owner approval for log-preservation writes. Re-inventory the
   five existing project logs; if the set has changed, stop for review. Create a
   unique, previously absent `artifacts/logs/behavioral-first-run-<GUID>/` only after
   verifying it is ignored and its path has no links. Copy the five logs without
   overwriting, and verify every copy's size/SHA-256 against its source. Preserve
   the copies: engine rotation may rename or prune originals. No log copies or
   other preparation artifacts are created by this amendment or its fixtures.
4. Capture the final baseline after those approved copies and immediately rehash
   the pinned executable without launching it. Any drift or failed precondition
   stops before execution; do not fix and retry under the same grant.

Only the following effects are proposed for approval: ordinary activity in the
existing checkout's `.godot/` cache (excluding protected
`.godot/validation-profile/`) and project-profile log creation/rotation after
verified preservation. This is observation, not a filesystem sandbox or rollback.
New or rewritten UID sidecars, import-sidecar modifications, tracked source or
artwork changes, save/settings changes and unrelated owner-file changes are
unapproved. Profile shader-cache/snapshot changes are also outside this proposal.
Actual write behavior of the pinned binary remains unverified.

After the one invocation, compare the same inventory and Git/index identities;
report added, removed and changed paths, including ignored paths. Report runtime
result and filesystem acceptance separately. Require normal zero exit, observed
termination, no error diagnostics, and exactly these stdout records, with the
completion as the final nonempty line:

```text
TLWH_BEHAVIORAL_GROUP_V1 world_coordinates PASS checks=4
TLWH_BEHAVIORAL_V1 PASS groups=1 checks=4 failures=0
```

Regardless of success, failure or uncertain termination, consume the grant at
the single launcher invocation: no retry, alternate command or direct dispatcher
call. Restore the original unconditional `throw` statement immediately afterward,
before any further engine attempt; compare the launcher against this inactive
preparation and rerun parsing/inert fixtures. This is a targeted source edit,
not a checkout-wide restore. Capture post-run filesystem observations before the
restoration edit (or identify that deliberate edit separately). Record reviewed
activation revision, attempted command, outcome, observed filesystem differences,
restoration verification and consumed grant in the execution PR/chat; publish no
raw private logs without separate privacy review/approval. Retain existing logs,
preservation copies and unexpected outputs. Do not delete, revert or automatically
clean generated files. Unapproved writes or uncertain termination stop further
testing and require owner direction. A PASS grants no standing, graphical,
gameplay or performance authority. Native/codec permissions are unchanged.

### First behavioral invocation result (2026-11-13)

The owner explicitly authorized exactly one supervised invocation at activation
revision `a9aff2d2c2c29650ba338d2ac8c74147862a6244`, including the prescribed
filesystem observations and verified preservation copies of the five project logs.
The reviewed base was `728974c8f8cda3d698bf956a022b07aa7412c9f3`; only the
authorization gate changed from `throw` to `return`. The fixed executable path and
SHA-256, command, one-entry manifest, four smoke assertions, supervisor and
30-second/1,048,576-byte/4,096-byte limits were verified unchanged.

The actual command, once in `D:\GameDev\Godot\Projects\TLWH`, was:

```powershell
pwsh -NoProfile -File tools/run-behavioral-tests.ps1
```

**Runtime: PASS.** Launcher exit 0, with the unchanged supervisor accepting normal
exit/stream completion, no engine/script/assertion errors and exactly the required
final records:

```text
TLWH_BEHAVIORAL_GROUP_V1 world_coordinates PASS checks=4
TLWH_BEHAVIORAL_V1 PASS groups=1 checks=4 failures=0
```

**Filesystem acceptance: PASS.** In-session inventories recorded relative paths,
sizes and SHA-256 for 3,531 checkout files (excluding Git metadata), then 3,536
after the five approved preservation copies, plus 26 project-profile files.
Git HEAD/status and index SHA-256 and editor-settings identity were captured
separately. No links were found. The index, executable and HEAD stayed unchanged.
Post-run differences, before documentation/commit work, were only:

- Intentional restoration of `tools/run-behavioral-tests.ps1` to unconditional denial.
- Profile `logs/godot.log` changed from 719 to 183 bytes.
- Engine log rotation removed `logs/godot2026-11-13T09.09.22.log` (719 bytes) and
  added `logs/godot2026-11-13T11.27.38.log` (719 bytes). The added log's SHA-256
  matches the prior current log and removed rotated log.

All five pre-run log copies remain verified and ignored under
`artifacts/logs/behavioral-first-run-8c1a377323d14b49a8d22fb20e846659/`.
No raw logs are published. Checkout caches, protected validation profile, UIDs,
import sidecars, artwork, both untracked audit reports, other ignored files,
project-profile shader caches/snapshots/saves/settings and editor settings were
unchanged. No agent cleanup or deletion occurred; the removed original was an
approved engine rotation effect with its verified preservation copy retained.

The gate was restored immediately in a `finally` block after the single launcher
invocation. It matches the inactive preparation (normalizing Git line endings).
PowerShell parsing and all 13 inert fixtures passed after restoration, as they
had before activation; denial-specific fixtures were not run against the active
gate. Exact source comparison and `git diff --check` passed. No full Python-suite
PASS is claimed. The one-time authorization is **consumed**; no retry, standing
permission, graphical/gameplay/performance validation or broader test scope
follows. Further Godot execution requires new explicit owner authorization.

## Fixed metadata smoke extension (draft, tested runtime scope passed)

Stage 3A-2 adds `MetadataSmoke` to the existing runner on this feature branch,
pending review/merge. The third separately authorized invocation passed its
**tested metadata runtime scope** on 2026-11-03, recorded below. **The gate is
inactive again and all three grants are consumed.** It rejects before prerequisites,
subprocesses or staging. Any additional invocation requires new explicit owner
execution approval and a reviewed gate amendment. There is no
override flag, environment switch or approval file.
`Static`, `NativePlan` and `Native` keep their existing recipe-switching behavior,
command arrays, allowlist and review controls. Metadata-specific review paths are
appended only for `MetadataSmoke`.

The complete Python suite passed 350 tests in **259.024 seconds** during PR #139
validation on 2026-11-03. MetadataSmoke therefore has a fixed **360-second**
bounded Python static-suite deadline. `Static`, `NativePlan` and `Native` retain
**60 seconds**. Test selection, actual PASS/zero-exit/termination-certainty
requirements, output limits and the stop-before-staging/dispatch failure gate
are unchanged. This deadline amendment does not activate MetadataSmoke. The
planned Godot preparation/smoke deadlines remain **60/30 seconds**, respectively.

The metadata recipe uses the same identity capture, pre-static hashes, actual
Python PASS requirement, reviewed-control checks, fresh external stage, sequential
bounded supervisor, failure evidence, final identity checks and no-retry rules.
The unchanged fixed commands used by the authorized invocations were:

| Phase | Exact arguments | Deadline | Combined output |
| --- | --- | --- | --- |
| Asset-free editor preparation | `["--headless","--editor","--path","<stage>","--quit"]` | 60 seconds | 1,048,576 bytes |
| Metadata smoke, after preparation PASS | `["--headless","--path","<stage>","--script","res://tests/metadata_smoke_test.gd"]` | 30 seconds | 1,048,576 bytes |

Both use `<stage>` as working directory and the pinned executable listed above.
Preparation is intentional: import-free global script-class discovery has not
been established. This task has not run even a version/help probe. Normal zero
exit and no engine/script/parse/assertion errors are required in both phases.
Smoke PASS additionally requires exactly one completion line, the final nonempty
stdout line: `TLWH_METADATA_SMOKE_V1 failures: 0`. Missing, duplicate, malformed,
nonzero or stderr-only completion fails. Diagnostics remain capped at 4096 bytes;
failed evidence remains ignored, unique and bounded to 64 KiB.

### Exact metadata staging and dependency closure

The reviewed [input inventory](../tests/fixtures/metadata_smoke/inputs.json)
contains exactly **32 source files**. The runner independently hardcodes the
same inventory; static tests compare them. All 32 must be tracked regular inputs.
Only two byte-preserving destination aliases exist:

| Tracked source | Stage destination |
| --- | --- |
| `tests/fixtures/metadata_smoke/project.godot` | `project.godot` |
| `tests/fixtures/metadata_smoke/builder.gd.uid` | `scenes/world/continuous_terrain_metadata.gd.uid` |

All other destinations equal their source paths. The minimal project has no
main scene or autoload. It never copies the gameplay project configuration.
The 14 complete, unchanged-or-new script inputs are:

- `tests/metadata_smoke_test.gd` (the sole new executable test script).
- `scenes/world/continuous_terrain_metadata.gd`, `planet_generator.gd`,
  `world_coordinates.gd`, `planet_world_state.gd`, `ferrite_region_generator.gd`,
  `crash_site_protection.gd`, `resource_deposit.gd` (all under `scenes/world/`).
- `construction/placement_rules.gd`, `machine_definition.gd`,
  `recipe_definition.gd`, `recipe_ingredient.gd` (all under `construction/`).
- `inventory/item_definition.gd`, `inventory_state.gd` (both under `inventory/`).

The other 18 inputs are their 14 UID files, the minimal project template, the
[production geometry fixture](../tests/fixtures/metadata_smoke/geometry.json),
the unchanged [classification goldens](../tests/fixtures/terrain_stage2_classification_vectors.json),
and `scenes/world/introductory_ferrite.tres` (texture-free ResourceDeposit).
Existing production UID bytes are copied intact. The builder's stage-only UID
comes from the fixture alias because it has no tracked production UID; the new
test has its own UID. Neither alias modifies production files.

Dependency rationale: metadata preloads the full generator, whose unused
`sample_color`/`sample_detail` method signatures name `PlanetWorldState`. Its
complete script requires ResourceDeposit, FerriteRegionGenerator,
MachineDefinition, InventoryState and PlacementRules; MachineDefinition extends
ItemDefinition and requires RecipeDefinition/RecipeIngredient. Ferrite's script
requires CrashSiteProtection and preloads the texture-free introductory deposit.
WorldCoordinates is shared by these types. Static checks inspect custom class
references and preloads. No production method is stripped, stubbed or copied.
The smoke script instantiates only the metadata builder's actual generator and a
direct reference generator. It never constructs PlanetWorldState or
FerriteRegionGenerator: Ferrite catalog I/O is confined to its unused constructor.
The catalog and its artwork therefore are not staged. Actual engine parsing and
global-class/circular-type compatibility remain unverified until approved execution.

No `planet_exterior.tscn`, gameplay scene, PNG, font, `.png.import` sidecar, source
`.godot` cache, owner save or settings file is admitted. Expected generated files
are confined to the fresh stage's `.godot/` tree after preparation; every staged
input, including UIDs, must remain unchanged. Any generated file elsewhere,
rewritten UID/input, link or unexpected directory fails closed. Preserve the
stage for inspection; never retry automatically or widen inventory after failure.

Fixture geometry is a literal snapshot of production-authored crash-site polygon
order/vertices/colors, 256-unit feathers, gameplay polygon and four ground-object
anchors. Static checks compare it to current scene/source text and the existing
geometry digest. The scene is read as text only, never staged or instantiated.
The smoke assertions cover signed int64 seed identity, 34x34 row-major 1156-byte
IDs 0–4, direct authoritative classifier parity, overlapping halos, negative
ownership, all four supported-envelope corners/outer halos, repeatability, copied
geometry, `runtime_certified=false`, existing offline golden expectations and
representative malformed-input rejection with no partial result. Goldens remain
unaltered; their comparison is a regression check, not a numerical enclosure.

Historical inventory guards now inspect their immutable merged endpoint; their
math and source pins are retained. Only old runner-source comparisons use the
pre-extension bytes; all other production comparisons remain against current
files. The new static test enforces this PR's exact additions/modifications and
protected-sidecar hashes. Inert fixtures verify that Native retains its original
review command and only MetadataSmoke receives the added controls.

### Metadata smoke execution approval checklist

Review all items before requesting or granting any engine run:

- Approve the exact 32-file inventory, two aliases and dependency rationale above;
  inspect the smoke assertions and unchanged production geometry/goldens.
- Verify source HEAD/status/index, committed reviewed controls, all input hashes,
  preservation references/sidecars, and actual Python static-suite PASS. Review
  inert fixture PASS separately; neither is engine validation.
- Verify the executable path and SHA-256 above without launching it, and again
  immediately before each authorized launch. No executable/argument overrides.
- Separately approve **one supervised invocation** after a reviewed metadata-only
  activation amendment. Proposed entry point: `pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode MetadataSmoke`.
  Approval must name the reviewed revision; this draft does not activate it.
- Use a fresh `tlwh-native-plan-<GUID>` under
  `D:\GameDev\Godot\TLWH-NativeStages`; never reuse a stage or run in the checkout.
  Review the exact two commands, 60/30-second deadlines, 1 MiB output caps,
  4096-byte excerpts, completion line and expected `.godot/` outputs above.
- Stop on any static failure, identity/index/input drift, unreviewed control or
  dependency, unexpected generated path/link, engine/script/parse error,
  assertion, missing/malformed/duplicate completion, abnormal exit, timeout,
  overflow or uncertain termination. Preserve bounded failure evidence and stage;
  no automatic retry, cleanup, graphics, benchmark or certification is included.

Even a later smoke PASS will not certify strict-Earth protection, positive
Green-center margins, Geometry2D/GPU numerical enclosure or Stage 3B integration.
Those remain blocked/unproven and require separately authorized work.

## One-time metadata execution result (2026-11-03)

The owner authorized one supervised invocation after a metadata-only activation
amendment based on PR #139 HEAD `33ea31be2aee7f9aa07405e441d61a8b855437a7`.
The activation revision was `4f1dcaf8d565d657d354f8ba672fa6ed681fa072`.
All 60 activation inert fixtures passed; exact runner comparison confirmed that
only the metadata authorization branch changed. Native behavior, the exact 32
inputs, commands, deadlines, supervision, identity and evidence controls remained
unchanged. The invocation was exactly:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode MetadataSmoke
```

| Check | Actual result |
| --- | --- |
| Complete Python static suite, 360-second bound | PASS: 350 tests, 249.088 seconds, exit 0, 513 output bytes |
| Pinned headless editor preparation, 60-second bound | PASS |
| Metadata script command, 30-second bound | FAIL: NONZERO_EXIT; GDScript parse error at `tests/metadata_smoke_test.gd:43` |
| Actual metadata generation | NOT REACHED |
| Actual malformed-input rejection assertions | NOT REACHED |
| Required completion line | Not produced; no smoke PASS |
| Overall runner | Exit 1; Static=PASS, Import=PASS, Native=FAIL, Infrastructure=FAIL, Authorization=PASS |

The diagnostic was: `Cannot infer the type of "seed" variable because the value
doesn't have a set type.` Godot reported failure to load the smoke script with
Parse error. Preparation PASS does not establish that every production script or
metadata call path parsed/executed successfully. The supervisor classified an
observed nonzero child exit, not timeout/overflow/uncertain termination. The
failure format retains that classification but not the numeric child exit code
or per-phase elapsed time; neither is inferred here.

Fresh retained external stage:
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-native-plan-561959bc40e045c08373debfb688aee8`.
Bounded failure evidence remains local and ignored at
`artifacts/logs/native-failure-4bed066295364d2591be929ba8136829.json`;
evidence capture succeeded. It is not committed or republished as a raw log.
Both commands used the pinned executable and the unchanged argument arrays above.
The stage and evidence are preserved; no automatic retry or smoke-script fix
was attempted. The one-time authorization is consumed and the inactive gate and
its inert withdrawal tests are restored to the pre-activation reviewed bytes.

Post-run read-only checks passed: exact 32 source/stage input hashes and allowed
generated paths (only `.godot/` additions); source working-state and input digests
match the failure record; pinned executable unchanged; tracked checkout/index
unchanged by execution; all 15 protected sidecar paths/sizes/hashes; A1 branch,
three annotated tag objects/peeled targets, backup bundle size/hash, frozen C1
source rasters, original/refined diagnostic manifests and all 7+3 output hashes.
No gameplay, graphics, benchmark, GPU/numerical certification, renderer integration,
merge or repository cleanup occurred. Stage 3B remains blocked. Correcting the
smoke-script typing issue and any subsequent execution require separate owner
direction and renewed execution authorization.

### Focused parse correction after the failed run (2026-11-03)

At the owner's separate direction after HEAD
`602d788a89582ed3d3eadb0ef3796118c1e18e82`, the smoke script's line 43 changes
only `var seed := text.to_int()` to `var seed: int = text.to_int()`. The six
original decimal-string signed-seed cases and every assertion remain unchanged.
Inspection of the remaining inferred declarations found constructors, dictionary
literals, explicitly typed call results or expressions with known operand types;
no other inference correction was justified. This is a source inspection result,
not a successful Godot parse.

The failed activation revision, parse diagnostic, retained stage and ignored
failure evidence above remain historical evidence unchanged. The one-time
authorization is consumed, MetadataSmoke stays inactive, and no Godot invocation
or retry accompanies this correction. Relevant Python metadata/static checks and
the inert runner fixtures are the non-engine validation; exact command/results
are recorded in PR #139. Runtime parsing, metadata generation and malformed-input
rejection remain unverified until separately authorized execution. No numerical
certification or Stage 3B integration is authorized by this correction.

## Second one-time metadata execution result (2026-11-03)

The owner separately authorized one additional supervised invocation against
reviewed HEAD `43f0fad4ad238ef798b71c7e78ab859e4b4aef28`. Only the metadata
authorization branch was temporarily changed, in activation commit
`a38ae0249495587213a945622b9aef2b2de5f6c2`. Exact source comparison confirmed
that all 32 input paths and bytes, the two aliases, test assertions, Native
behavior, static selection/PASS gate, 360-second static deadline, 60/30-second
engine commands/limits, supervision, identity and evidence controls were unchanged.
An inert gate/side-effect check and PowerShell AST check passed; the test suite
and its assertions were not changed for this activation.

Exactly one invocation was made:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode MetadataSmoke
```

| Check | Actual result |
| --- | --- |
| Complete Python static suite under 360 seconds | PASS: 350 tests, 246.382 seconds, exit 0, 513 output bytes |
| Headless editor preparation under 60 seconds | PASS |
| Smoke command under 30 seconds | FAIL: NONZERO_EXIT; two `golden prepare` assertion failures |
| Smoke-script parsing and execution | Succeeded; reached the completion print |
| Metadata generation, layout/parity, halo, seed, ownership/envelope, repeatability/copy assertions | Executed; no failures reported outside the two golden preparations |
| Representative malformed-input rejection assertions | Executed; no failures reported |
| Completion output | `TLWH_METADATA_SMOKE_V1 failures: 2`; required zero-failure result not met |
| Overall runner | Exit 1; Static=PASS, Import=PASS, Native=FAIL, Infrastructure=FAIL, Authorization=PASS |

The two stderr diagnostics were both `SMOKE_FAIL: golden prepare`. They do not
identify the failing vectors or returned errors. No cause is inferred or fixed
in this execution task. The script parsed, invoked the real metadata builder, instantiated the production
generator and exercised the rejection checks, but **overall metadata
runtime validation remains FAIL**. These partial results do not establish a
passing golden suite, numerical protection, GPU parity or production acceptance.
The existing failure format does not retain numeric child exit code or per-phase
elapsed/output-byte totals; no such values are inferred.

The new retained stage is
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-native-plan-a4ca78ba7db646f282f04144895e9138`;
it is distinct from, and did not reuse, the earlier failed stage. Local ignored
failure evidence capture succeeded at
`artifacts/logs/native-failure-cd532128e7494e078edcd44b1a1cf293.json`, SHA-256
`F4955B08161380080B996AD5AA036744D43C5B3975305C097586CE3A1612C107`.
The input digest is
`E728F9AD38BD26BDA2B3B5192965E83F7FDEC8673B7762F2C628EBF6D90C5CAB`.
Both stage and raw evidence remain local/preserved; the evidence is not committed.

After failure, no fix or retry was attempted. The inactive gate was restored
exactly to reviewed `43f0fad` source. Both one-time grants are consumed. Any new
engine invocation needs new explicit owner approval. Post-run read-only checks
passed for all 32 source/stage hashes, input/working-state digests, executable,
allowed generated inventory, clean tracked/index state, 15 protected sidecars,
A1 branch, three annotated tag objects/targets, backup bundle, C1 source hashes,
original/refined diagnostic manifests and 7+3 output hashes. The prior failure
evidence SHA-256 and earlier stage's 32-file digest also remain unchanged.
No gameplay, unrelated engine command, production modification, numerical/GPU
certification, presenter integration, merge or repository cleanup occurred.

### Golden-vector ownership correction after the second run (2026-11-03)

Source inspection of all 14 unchanged golden records explains the two preparation
failures: cells `(16384,-16385)` and `(-16385,16384)` have floor-owned chunks
`(512,-513)` and `(-513,512)`, outside the metadata owner's `[-16,15]` range on
each axis. Their historical expected materials remain 2 and 0. The generator can
classify these cells; metadata preparation must reject their unsupported owners.
The former smoke loop incorrectly required success for every golden.

The corrected loop still visits every vector. For the 12 supported owners it
requires metadata success and the original row-major material-byte comparison.
For the two unsupported owners it requires exactly `ok=false` and
`error="unsupported_chunk"`, with no partial payload, and independently compares
the original material ID through the unchanged production generator using the
same reviewed seed/overlays/protected polygon/anchors. The metadata envelope,
production code, golden bytes and non-golden smoke assertions are unchanged.
Focused static guards check the 12/2 partition, exact out-of-range cells/owners/IDs,
both branches and retained direct classifier coverage.

Both previous execution records, stages and failure evidence remain unchanged.
This correction has non-engine static/inert validation only; exact results are
recorded in PR #139. MetadataSmoke stays inactive. No Godot invocation or retry
accompanies this change, and neither prior grant permits another run. Runtime
success, numerical certification and Stage 3B integration remain unestablished.

## Third one-time metadata execution result (2026-11-03)

The owner authorized one additional supervised invocation against reviewed PR #139
HEAD `d5c5789142c68b7ce09f25c19e178e13635f9107`. The only activation change was
the metadata authorization branch, committed at
`e0640b9ac867da2008a330c66f62a2da868ab789`. Exact source comparison and inert
side-effect/AST checks passed. All reviewed inputs, assertions, inventory, two
aliases, Native behavior and execution/preservation controls stayed unchanged.

Exactly one invocation was made:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode MetadataSmoke
```

| Check | Actual result |
| --- | --- |
| Complete static suite under 360 seconds | PASS: 352 tests, 247.764 seconds, exit 0, 515 output bytes |
| Pinned headless editor preparation under 60 seconds | PASS |
| Metadata smoke command under 30 seconds | PASS |
| Completion | Exactly one final stdout record: `TLWH_METADATA_SMOKE_V1 failures: 0` |
| Overall runner | Exit 0; Static=PASS, Import=PASS, Native=PASS, Infrastructure=PASS, Authorization=PASS, Reason=OK |

The reviewed golden-scope correction added two static guards, so the complete
unchanged discovery command now runs 352 tests rather than the older 350-test
baseline. No test was skipped or selection/PASS condition changed.

Actual GDScript loading/parsing, production generator construction and metadata
builder execution succeeded within the smoke's tested scope. Passing assertions
cover six decimal-string signed seeds (including both int64 endpoints), eight
owned chunks per seed (adjacent negative/origin owners and four envelope corners),
34x34/1156-byte row-major IDs 0-4, direct production-classifier parity, overlapping
halos, negative ownership, outer support, repeatability, copied geometry and
`runtime_certified=false`. All 14 historical goldens are retained: the 12 supported
owners pass metadata/material-byte checks; the two unsupported owners are rejected
with `unsupported_chunk` and pass direct generator/material-ID comparisons.
Representative malformed seed/chunk/geometry/overlay input rejection assertions
also passed with no partial payload. This is finite runtime regression evidence,
not exhaustive proof for every seed, coordinate, malformed value or numeric case.

Both engine phases satisfied zero exit, no engine/script/assertion errors,
bounded output and observed termination certainty. The commands and 60/30-second,
1,048,576-byte output and 4096-byte excerpt limits were unchanged. The summary
does not retain per-phase elapsed/output-byte totals; none are inferred.
The fresh retained stage is
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-native-plan-6ef08cf483f4442cad850d02f18c99b5`,
distinct from both previous stages. Its 32-input digest is
`9517204CBADA45D2E36BD722BCABB8DA44419C3555F7E36309E722E57DFA0090`.
Success returned empty Evidence/EvidenceError fields, as designed; no routine
permanent success log was created. This execution record and PR #139 retain the
meaningful result. All three stages and both earlier failure records are preserved.

Post-run checks passed for unchanged source revision/status/index, exact 32
source/stage hashes and digest, allowed generated paths (only stage `.godot/`
additions), executable, 15 protected sidecar paths/sizes/hashes, A1 branch, three
annotated tag objects/targets, backup bundle size/hash, frozen C1 rasters,
original/refined diagnostic manifests and 7+3 output sizes/hashes, prior failure
record SHA-256s and both earlier stage digests. All 309 tracked asset files
(118,944,410 bytes, including artwork) matched a pre/post aggregate digest of
`91d4f6c31cf28b2f1980a2213aaf0badb7c430d02668b6be56bac681303af4b5`.
That aggregate hashes sorted relative paths, byte sizes and each file's SHA-256;
no artwork was imported into the smoke stage or changed.

The inactive gate is restored exactly to reviewed `d5c5789` source. All three
one-time grants are consumed, with no automatic retry or standing execution
authority. **PASS validates only the tested metadata runtime behavior.** It does
not prove strict-Earth protection, positive Green-center margins, runtime/GPU
numerical enclosure, GPU correctness, graphics, gameplay or performance. Stage
3A-2 numerical certification and Stage 3B presenter integration remain unproven
and unauthorized. No production renderer change, merge or repository cleanup
occurred; the PR remains draft.
