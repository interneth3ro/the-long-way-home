# PR #103 native supervisor preparation â€” owner review pending

Decision 16 uses the proven PR #102 isolated model. This package is preparation,
not native authorization. No native stage, Godot import, assertions or graphics
has been created/run. It is deliberately kept under ignored artifacts/evidence;
no implementation, inventory, artwork, tracked test or repository policy changed.

## Identities and unchanged inputs

- Review checkout/PR head: `aa62a6d38c981e08c7c6d70cf5929cad642a5414`.
- Exact native Git blob pin: `123b29b0cef3386f476117b7952d5ad91d6b0f98`.
- [proposal.json](proposal.json) is the unchanged approved inventory (SHA-256
  `3fd7c93864752be48dbd9f43dd52264a1a37d1b034f3c676d8dc9429a0174928`).
  All 54 paths, byte counts and SHA-256 hashes match both commits.
- 367-byte UTF-8/LF project.godot SHA-256:
  `5716c7e88113b18915bc027d3714f60ecc36698c84bec332b5ecbe7a1b08b1a2`.
  Initial stage must contain exactly 55 files. No inventory/output expansion.
- Standard Godot 4.7.2 executable and hash are fixed in supervisor.py; no version
  launch or executable/argument override. Identity was verified by hashing only.

## Exact adaptation

The contiguous Windows Job Object/kernel declarations, EngineLock, Godot process
exclusion, bounded() and classify() code is byte-for-byte identical (after text
newline decoding) to the sealed PR #102 review-v2 supervisor, original SHA-256
`b01d8e488f43dbda976388854fe12b0de572f8040c61e460f75ba6030fb1ba21`.
An inert test verifies the whole copied block, not just selected functions.

Targeted changes around that block:

1. Separate review HEAD and input-source identities, bind this package and a new
   fixed external GUID stage, and seal the unchanged proposal/configuration.
2. Plan is read-only and valid before a stage exists. Stage --execute is a
   separately authorized, single-use copy from Git blobs using exclusive files;
   it never launches Godot. The stage path does not currently exist.
3. Restrict engine phases to Import (60s) and Assertions (30s). No graphical or
   editor-GUI phase, alternate engine/test, command override or automatic chaining.
4. Replace broad generated-cache/sidecar exceptions with the exact 36-path list
   and count cap. Original inputs stay immutable. After successful import, capture
   output hashes and require exact set/hash equality before/during/after assertions.
5. Retain one-attempt state with review identity, running marker, prior-phase
   gates, duplicate rejection and permanent failure stop. Interrupted runs stay
   blocked. Preflight failure also consumes its externally authorized attempt;
   do not retry merely because no state file was written.
6. Extend the original source snapshot to ignored owner files, worktree records
   and all historical PR #102 package files. Git can list an ignored nested repo
   as a directory; the snapshot uses the existing read-only inventory() function
   to hash its contents rather than skipping or altering that protected directory.
   No files were removed, cleaned, normalized or classified as disposable.
7. Compare all captured Git refs strictly; no obsolete PR #102 transient-ref
   exemption is carried forward. Unexpected reference changes require review.
8. Write only new phase evidence in this review directory. Capture/hash the
   immutable controls, owner/source baseline and commands under the review seal.
   No new general testing framework, OS identity, sandbox or VM was introduced.

## Preservation coverage and execution rules

[source-baseline.json](source-baseline.json) captures 4,370 source/owner files,
including existing .godot material, ignored artifacts, all 34 protected untracked
files, raw working bytes, index, full status, branch/HEAD, refs and worktrees.
All 34 owner-file hashes match the retained PR #102 owner capture. It also captures
119 files in the historical PR #102 package. The sole excluded source prefix is
this new review package, whose immutable controls are instead sealed; its future
state/evidence files are task-owned and never overwrite existing files.

The native stage is a new plain direct child of the owner-provisioned
D:/GameDev/Godot/TLWH-NativeStages parent, outside the checkout. The fixed name is
in [commands.json](commands.json). Stage creation rejects existing destinations,
links/reparse points, hard-linked files and unsafe paths. Copy only approved Git
blobs and generated configuration; never import in the source checkout or copy
owner caches/untracked sidecars. Preserve partial/success/failure stages.

Before each phase, verify the reviewed seal, captured source/owner material,
executable and inputs; continuously recheck while the engine runs and again after
exit. The original independent watchdog, concurrent pipe readers and Job Object
kill-on-close/process-tree accounting remain unchanged. Both engine processes
have 1,048,576-byte combined output and 4,096-byte diagnostic limits. Termination
must be confirmed; failures, timeout, overflow, errors, changed inputs/outputs,
malformed completion, unexpected files or uncertain termination stop all further
phases. No retries, profiling, benchmarks or freeze reproduction.

No receipt or flag substitutes for owner authorization. Run one authorized phase
per invocation. A future owner-approved bounded run must retain/recheck the source
baseline before and after its required static gate; no baseline refresh is automatic.
The recorded source static acceptance is 163 tests PASS at this unchanged review
identity. The required fresh static gate before any native run uses
`python -B -m unittest discover -s tests -p 'static_*test.py'` under an explicit
180-second bound without changing the repository runner. This preparation ran
only the inert supervisor checks described below.

## Inert verification

[tests-result.json](tests-result.json) records 25 tests PASS in 4.380 seconds.
Tests use short-lived standard Python children, mocked inventories and read-only
checks; no project/GDScript code is executed and no native stage is created.
Coverage includes both pipes, errors even at exit zero, malformed/duplicate final
markers, output overflow, timeout, independent deadline while a guard is busy,
owned descendant termination, mutex contention, preservation failure before and
during a child, pinned-executable rejection, frozen output additions/removals/
changes, exact path/count rejection, blocked/foreign/duplicate state and prior-phase
requirements. The copied Windows process-control block remains exact.

## Decision 16 residual risk

This is an observational preservation/process guard, not a filesystem sandbox.
Godot retains ordinary Windows user permissions; it is not prevented from touching
other account-accessible locations, including global editor/user settings outside
the captured trees. Pre/post hashes detect changes in captured material but do not
roll them back or guarantee recovery from a system freeze. The owner explicitly
accepted this residual risk. No sandbox, restricted identity or VM is proposed.

Owner review and a separate bounded-run authorization remain required. Graphical
acceptance and PR #104 are outside this package. Historical PR #102 authorizations
and state are never reused. Do not execute Stage/Import/Assertions during review.
