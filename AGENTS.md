# Development conventions

- Favor small, independently testable changes; stay within the requested scope.
- Separate gameplay simulation, presentation, and narrative state.
- Avoid speculative abstractions and unnecessary managers.
- Maintain stable, clearly defined interfaces.
- Keep narrative content independently editable.
- Validate affected Godot scenes and scripts before reporting completion, subject
  to the execution safety policy below; distinguish static, headless and graphical
  checks.
- Do not commit Godot-generated caches or temporary test artifacts.
- Do not introduce third-party plugins without approval.
- The previous FactoryGame project is a historical reference. When an
  owner-approved task requires it, Codex may inspect its repository, source,
  artwork, assets and documentation in read-only mode. Historical inspection
  does not authorize modifications to the old project or copying, importing or
  reusing its files, code or architecture in TLWH. Any reuse or adaptation requires
  separate explicit owner approval, provenance/licensing review as applicable,
  and a scoped implementation plan. Prefer the current TLWH architecture; avoid
  reintroducing legacy complexity without demonstrated benefit. Preserve
  historical files and repository state; do not clean up, migrate or destructively
  alter them without explicit authorization. Historical inspection grants no
  execution authorization. Do not begin unrelated historical-project work.
- Use feature branches and pull requests for future development; do not rewrite
  existing history or merge without authorization.
- Preserve user-authored artwork, saves, settings, and other project data.
- Never perform destructive cleanup without verifying ownership and preservation
  requirements.

## Godot execution safety

- Obtain explicit owner authorization before launching the Godot editor or game
  graphically, running playable scenes, performing graphical verification, or
  running automated graphical interaction tests.
- Obtain explicit owner authorization before running performance probes,
  benchmarks, prolonged runtime tests, or attempts to reproduce system-level
  freezes or severe performance failures. Never reproduce a reported system
  lockup without explicit owner authorization.
- **Headless restriction following PR #5 remains active.** On 2026-10-29 the
  owner approved standing routine use of
  `pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Native`, superseding the
  earlier one-invocation permission after PR #75. Only its fixed import and
  recipe-switching phases are authorized. No embedded approval scope, self-hash,
  receipt, environment switch or local approval file is required. Stop on failure;
  standing authorization does not permit automatic retries or unattended runs.
- This restricted exception permits execution only through
  the reviewed `tools/run-local-tests.ps1 -Mode Native`, with the exact standard
  Windows executable `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`,
  SHA-256 `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.
  No executable, script, scene or argument overrides are permitted. Only the
  reviewed allowlisted recipe-switching test may run; review changes to runner,
  policy, static tests, native test assertions and inventory/command scope before use.
- For the B1 UI implementation the owner separately authorized a minimal font
  staging amendment: only the required IBM Plex Sans Regular, Medium and SemiBold
  `.ttf` assets under `assets/fonts/ibm-plex-sans/`, plus their three matching
  `.ttf.import` metadata sidecars (separately approved after the first B1 run
  rejected generated sidecars, together with one controlled rerun). This authorizes no additional
  executable types, engine commands, tests or runner capabilities. All existing
  staging, identity, limit, failure and preservation checks remain required.
- On 2026-10-30 the owner separately approved tracking the exact IBM Plex Sans
  Italic `.ttf.import` sidecar, its exact-path LF rule, and staging only the
  additional `assets/fonts/ibm-plex-sans/IBMPlexSans-Italic.ttf` and its matching
  `.ttf.import`. Preserve the sidecar SHA-256
  `59dcbab3fc80589bdb874f68bfb1cd93e6d979fd96ff56787094500a56d62c20`.
  This adds no commands, executable types, tests or runner capabilities beyond
  those two input paths. PR #90 Native execution requires separate owner
  authorization; the standing routine exception does not authorize that run.
- Stage 3A-2 adds a fixed `MetadataSmoke` recipe in draft form only. Its additional
  assertion/fixture review controls apply only to that mode; existing `Native`
  recipe-switching controls and standing authorization remain unchanged.
  `MetadataSmoke` is inactive and rejects dispatch before any process or stage.
  The separately approved one-time invocation on 2026-11-03 was consumed at
  `4f1dcaf8d565d657d354f8ba672fa6ed681fa072`: preparation passed, but the smoke
  script failed to parse. The inactive gate was restored without fixing/retrying
  the test. Any further metadata invocation requires new explicit owner approval.
  A second separately authorized invocation, based on reviewed `43f0fad`, was
  consumed at `a38ae0249495587213a945622b9aef2b2de5f6c2`: preparation passed;
  the smoke ran but reported two `golden prepare` assertion failures. No fix or
  retry followed; the gate is inactive again. Neither grant permits another run.
  The third separately authorized invocation against reviewed `d5c5789` passed
  the tested metadata runtime scope at `e0640b9ac867da2008a330c66f62a2da868ab789`.
  The gate was restored inactive; all three grants are consumed. Runtime smoke
  PASS grants no further execution, numerical certification or Stage 3B authority.
  No metadata import, execution, real-stage creation, or numerical certification
  is authorized by this implementation or its inert/static checks. Separate
  explicit owner approval and a reviewed activation amendment are required;
  see [the exact execution checklist](docs/LOCAL_TESTING.md#metadata-smoke-execution-approval-checklist).
- Each authorized run requires actual Python static-suite PASS, unchanged reviewed
  controls, and a fresh unique copy of approved tracked working inputs under
  `D:\GameDev\Godot\TLWH-NativeStages`, outside the checkout. Working resource
  edits within the allowlist are permitted; capture revision/status/index and
  input hashes before static validation, then reject changes throughout the run.
  Never run Godot in the source checkout or reuse a previous stage.
- The only engine commands are one cold headless import (60 seconds), then only
  after clean PASS the recipe-switching test (30 seconds). Run sequentially, one
  engine process at a time, with no automatic retries; rehash the pinned executable
  before each launch. Each process has a 1,048,576-byte combined output limit and
  4,096-byte diagnostic excerpts. Stop on engine/script/parse errors, assertion
  failure, missing/malformed completion, abnormal exit/crash, timeout, overflow,
  uncertain termination or changed source/stage/executable identity. Preserve
  bounded failure evidence in ignored `artifacts/logs/` and all owner files/stages.
- This scope allows no arbitrary headless tests, graphical launch, performance
  probe, benchmark, stress test or freeze reproduction. Owner withdrawal suspends
  the exception immediately; stop using Native until renewed explicit permission.
  Engine identity, command, limit or inventory expansion requires owner review and
  renewed authorization. A test PASS never expands permissions or schedules runs.
  See the [local-runner policy](docs/LOCAL_TESTING.md#authorization-and-standing-scope).
- While execution is restricted, use static code inspection, scene and resource
  text inspection, Git diff validation, Markdown and documentation checks, and
  other nonexecuting checks that invoke neither Godot nor project code.
- Clearly distinguish static validation from actual runtime verification. Do not
  claim gameplay, graphical, or engine validation when those checks were not
  performed.
- The proposed local behavioral foundation at `tools/run-behavioral-tests.ps1`
  is **inactive** and has no standing execution authorization. It rejects with
  `NOT RUN` before engine identity checks or process dispatch. Its proposed
  direct-checkout workflow is separate from the existing staged Native and codec
  recipes; their permissions and controls are unchanged. Implementation, a branch,
  a PR or a merge does not activate this runner or authorize direct-checkout runs.
  Before any activation, the owner must explicitly approve the precise launcher,
  fixed command, test manifest and allowed filesystem effects, including Godot
  cache/import/UID behavior in the actual checkout and user-profile effects.
  No cache or sidecar creation/rewrite is approved by this foundation. Any future
  standing authorization applies only to the exact reviewed runner and scope.
  No automatic retries, destructive cleanup, graphical tests, performance probes,
  benchmarks, stress tests or freeze reproduction are authorized. See the
  [inactive behavioral workflow](docs/LOCAL_TESTING.md#local-behavioral-foundation-inactive).
- The first behavioral activation amendment is preparation only, pending review
  and separate explicit owner approval; unconditional denial remains in place.
  Any later grant must name the exact reviewed activation revision and permit
  exactly one supervised `pwsh -NoProfile -File tools/run-behavioral-tests.ps1`
  invocation in `D:\GameDev\Godot\Projects\TLWH`, using the pinned executable
  above, unchanged manifest, fixed command and 30-second/1 MiB/4 KiB limits.
  Proposed acceptable effects are only existing `.godot/` cache activity and
  project-profile log creation/rotation after separately approved preservation
  copies of the five existing logs. The protected `.godot/validation-profile/`
  is excluded. No UID creation/rewrite, import-sidecar modification, tracked
  source/artwork change, save/settings change or unrelated owner-file change is
  approved. Observe pre/post paths, sizes and hashes; stop on unapproved changes
  without deleting, reverting or cleaning them. After the single invocation,
  regardless of result, restore unconditional denial and record the grant as
  consumed before any further attempt. No standing grant, automatic retry or
  broader engine permission follows. See the
  [proposed single-run procedure](docs/LOCAL_TESTING.md#first-behavioral-invocation-proposal-inactive).
- Preserve all existing repository safety, worktree, artifact and branch
  preservation requirements. Do not alter the abandoned PR #5 worktree,
  branches, archives, or conversation.

## Workflow skills

- Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
  review to reconcile affected documentation in the same feature PR. Preserve
  approved design and narrative canon; flag conflicts for the owner.
- Invoke [post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) only for
  an explicitly requested, specific merged PR. Merge approval does not itself
  request cleanup. Never retire the requesting chat's attached checkout.
- The repository is `interneth3ro/the-long-way-home`; its default branch is `main`.
  Do not merge automatically. Keep changes on focused feature branches.
- Use the dedicated maintenance conversation for explicitly requested post-merge
  cleanup.

## Git development workflow

- Use traditional Git feature branches in the primary local checkout by default.
- Do not create Git worktrees or use Codex Worktree mode unless the owner
  explicitly requests them.
- Begin each implementation from a clean, synchronized `main`.
- Create one focused feature branch per implementation.
- Do not develop multiple feature branches concurrently in the same checkout.
- Commit and push reviewed changes to the feature branch.
- Open a pull request against `main`. Never merge automatically.
- After the owner merges the PR, synchronize local `main` and retire the verified
  feature branch using the post-merge-cleanup skill, only when cleanup is
  explicitly requested for that PR.
- Preserve uncommitted changes, ignored files, user-authored assets, settings,
  saves and historical evidence.
- Do not use destructive Git shortcuts to make a checkout appear clean.

The primary checkout may temporarily be on a feature branch during implementation.
This is expected and is not a workflow violation.

## Generated files and retention

Create files only for a clear development purpose. Prefer console output for
routine checks and summaries; avoid duplicate reports, screenshots, logs and
overlapping documents. Do not introduce custom tooling without a concrete need.

| Category | Retention and location |
| --- | --- |
| Permanent | Source, scenes, approved production artwork/source assets, narrative content and authoritative documentation. Keep documentation in `docs/` and approved assets in `assets/` when needed. Preserve existing conventions. |
| Historical evidence | Commit explicitly owner-approved, privacy-reviewed permanent screenshots, useful failure logs and meaningful PR verification records under `artifacts/evidence/` or `artifacts/logs/`. Preserve exact historical bytes and provenance. Temporary outputs remain ignored. |
| Disposable | Proven regenerable temporary outputs and routine successful check output with no continuing value. Prefer no saved output; remove only exact, verified task-owned files when authorized. |

Use `artifacts/screenshots/` for temporary visual evidence, `artifacts/logs/` for
retained diagnostics, `artifacts/evidence/` for meaningful PR evidence,
`artifacts/archive/` for verified historical ZIPs and `artifacts/tmp/` for
disposable generated output. Create directories only when used. Keep generated
evidence outside tracked source directories and out of Git unless explicitly
approved; do not retain routine successful validation logs permanently.

Preserve user-authored artwork, saves, settings and irreplaceable material.
Unknown files remain protected even when ignored, named as caches or located in
`artifacts/tmp/`. Location and extension alone never authorize deletion.


The Stage 2A housekeeping disposition in
`docs/experiments/repository_housekeeping_stage2a.json` records only the exact
owner-approved retention and deletion scope. It does not change historical
receipts or authorize further cleanup. The owner-approved Stage 2C disposition in
`docs/experiments/repository_housekeeping_stage2c.json` permits four sanitized
historical derivatives and deletion of exactly their four private originals and
redundant ZIP after verified preservation commit. Its separate completion record
records the actual deletions. Historical receipts and original hash pins remain
immutable; derivatives have new identities. This grants no further cleanup or
engine execution authority. Never publish the original private path values.
PR #5 archives, nested diagnostic clones, ordinary Godot
cache and isolated-profile settings/logs remain protected exclusions.

Permanent evidence requires explicit publication approval and privacy review;
ignored status is not a retention decision. Keep permanent source assets in
`assets/`, documentation in `docs/`, and approved evidence in the existing
`artifacts/` conventions. An `artifacts/.gdignore` marker prevents editor imports
of evidence; it does not authorize deleting or executing anything there.

## Historical evidence archives

Archive only clearly identified meaningful evidence, with provenance tied to the
relevant PR. Do not create an archive for every PR or duplicate source already
preserved in Git. PNGs and other compressed media may save little space.
Saves, source assets, settings, secrets and unrelated personal files are not
eligible evidence under this automatic archive policy.

Place archives in a verified surviving primary checkout's `artifacts/archive/`,
outside any retiring worktree. Never overwrite an existing archive. Record PR,
original relative paths, sizes and SHA-256 hashes in an in-archive manifest.
Close and independently reopen the ZIP, require the exact intended safe entry set,
fully read entries to check CRC/integrity, and compare decompressed sizes and
hashes with the originals. Before any exact original deletion, recheck that the
source has not changed and the verified destination remains available. Preserve
originals on any mismatch or failure. Preserve and report ambiguous material;
request clarification instead of classifying it as disposable.

Cleanup authorization covers preservation and retirement only of verified
PR-specific historical evidence under this policy. Other protected material
requires an explicit owner decision. Do not run cleanup or archive existing files
merely while developing or validating these workflow instructions.
