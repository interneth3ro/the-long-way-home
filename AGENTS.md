# Development conventions

- Favor small, independently testable changes; stay within the requested scope.
- Separate gameplay simulation, presentation, and narrative state.
- Avoid speculative abstractions and unnecessary managers.
- Maintain stable, clearly defined interfaces.
- Keep narrative content independently editable.
- Validate Godot scenes and scripts before reporting completion. Run headless
  editor import and the main scene; distinguish headless from graphical checks.
- Do not commit Godot-generated caches or temporary test artifacts.
- Do not introduce third-party plugins without approval.
- Do not begin unrelated development or access or modify the previous FactoryGame
  project. This is a fresh implementation; do not reuse its files or architecture.
- Use feature branches and pull requests for future development; do not rewrite
  existing history or merge without authorization.
- Preserve user-authored artwork, saves, settings, and other project data.
- Never perform destructive cleanup without verifying ownership and preservation
  requirements.

## Workflow skills

- Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
  review to reconcile affected documentation in the same feature PR. Preserve
  approved design and narrative canon; flag conflicts for the owner.
- Invoke [post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) only for
  an explicitly requested, specific merged PR. Merge approval does not itself
  request cleanup. Never retire the requesting chat's attached checkout.
- The repository is `interneth3ro/the-long-way-home`; its default branch is `main`.
  Do not merge automatically. Keep changes on focused feature branches.

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
