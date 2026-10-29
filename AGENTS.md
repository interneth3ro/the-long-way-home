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
- Do not begin unrelated development or access or modify the previous FactoryGame
  project. This is a fresh implementation; do not reuse its files or architecture.
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
- **Temporary headless restriction following the PR #5 incident:** all Godot
  headless execution is suspended, including editor imports, headless scene
  launches, and GDScript tests executed through Godot. This restriction remains
  active until the owner explicitly lifts it.
- Local-runner authorization has two separate stages; neither is active in this
  code-only PR. First-run execution requires separate explicit owner approval of
  the exact reviewed runner commit, absolute executable path/SHA-256, source and
  working-input identity, external stage, fixed commands, limits, evidence
  destination and stop conditions. Merge or this policy text is not that approval.
- After successful first-run validation, routine local native testing additionally
  requires a separately owner-approved, narrowly scoped repository execution
  policy. First-run approval and a successful test do not grant routine permission.
  That later policy must define the approved runner/executable identities, allowed
  source/working-input variation, invocation scope, revocation and reapproval when
  scope or identities change. It may allow repeated local runs within that scope
  without a new GitHub comment for each run. This PR enables neither routine nor
  unattended execution; its public Native gate remains unconditionally inactive.
  Activation requires a separate reviewed owner-authorized change, not a switch,
  environment variable, local approval file or automatic reaction to test PASS.
- Any later authorized runner execution retains actual static-suite PASS, a fresh
  external project copy, source/executable hash verification, and precisely one
  cold headless import (60 seconds) followed only on PASS by the recipe-switching
  test (30 seconds). Each process has a 1,048,576-byte combined output limit;
  commands run sequentially without retries. Stop on engine/script errors,
  assertion failure, missing/malformed completion, abnormal exit/crash, timeout,
  overflow, uncertain termination, or changed source/executable identity.
  Preserve bounded failure evidence and all owner files. See the two-stage
  [authorization process](docs/LOCAL_TESTING.md#controlled-native-activation-stage-b-pending-merge).
  All other headless, graphical, performance and preservation restrictions remain.
- While execution is restricted, use static code inspection, scene and resource
  text inspection, Git diff validation, Markdown and documentation checks, and
  other nonexecuting checks that invoke neither Godot nor project code.
- Clearly distinguish static validation from actual runtime verification. Do not
  claim gameplay, graphical, or engine validation when those checks were not
  performed.
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
| Historical evidence | Selected screenshots, useful failure logs and meaningful PR verification records. Retain only evidence useful after merge; store under the ignored `artifacts/` paths below. |
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
