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
Each plan/run creates a unique `tlwh-native-plan-<GUID>` directory there and never
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

## Fixed metadata smoke extension (draft, unexecuted)

Stage 3A-2 adds `MetadataSmoke` to the existing runner on this feature branch,
pending review/merge. **It is inactive:** the authorization gate rejects it
before prerequisites, subprocesses or staging. Do not invoke it for this PR.
A separate explicit owner execution approval and reviewed gate amendment are
required. There is no override flag, environment switch or approval file.
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
Its only commands, **planned but NOT RUN**, are:

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
