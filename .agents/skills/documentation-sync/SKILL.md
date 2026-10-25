---
name: documentation-sync
description: Reconcile documentation with a scoped feature diff or PR in The Long Way Home, normally before PR review. Preserve approved design and narrative canon, and report conflicts without inventing resolutions.
---

# Documentation sync

Use for a named feature branch, diff or PR in `interneth3ro/the-long-way-home`.
Normally update affected documents in the same feature PR before review and merge.
For a requested dry run, return proposed edits only; make no writes.

1. Read [AGENTS.md](../../../AGENTS.md), [README.md](../../../README.md) and
   [GAME_VISION.md](../../../docs/GAME_VISION.md). Inspect current branch/status,
   the scoped diff against its actual base (normally `main`), affected code and
   relevant existing documents. Preserve unrelated changes. Read only what the
   change affects; do not inventory the former project.
2. Identify the smallest set of authoritative documents affected by changed
   behavior, interfaces, architecture ownership, setup or validation instructions.
   Update existing records and link to them rather than duplicating specifications.
   A new document requires a concrete gap; no routine report or handoff file.
3. Keep **approved design**, **proposed/unresolved design** and **implemented
   behavior** explicit. Code does not silently supersede approved intent.
   Describe feature-branch behavior as pending merge. A passing isolated test does
   not establish player access or narrative completion; cite actual verification
   and state what remains unverified.
4. Align architecture descriptions with actual code and stable interfaces; create
   no speculative architecture document or manager. Preserve established canon in
   GAME_VISION and narrative sources. Flag contradictions and unresolved owner
   decisions in the response; do not invent story details, silently change canon
   or mark a proposal approved to reconcile a mismatch.
5. Make minimal factual edits. Preserve historical evidence and avoid cosmetic
   churn. If no documentation is affected, report that with the reason. For a
   post-merge request, verify live PR merge/current `main` and inspect current
   behavior before claiming delivery; report unavailable evidence. Put any needed
   correction on an authorized feature branch, never directly on `main`.
6. Check changed local Markdown links and `git diff --check`; inspect final scope.
   Reuse relevant validation results with their provenance and limits. Follow
   AGENTS.md for engine checks when required; distinguish headless and graphical
   verification. Do not create logs merely to prove a successful docs check.

Report changed/proposed files, the behavior and evidence they reflect, validation
limits and unresolved design conflicts concisely in the response. Do not create
GitHub issues/comments, implement features, merge, delete files or invoke cleanup
implicitly. External writes require the user's authorization for that action.
