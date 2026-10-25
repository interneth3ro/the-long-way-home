---
name: post-merge-cleanup
description: Safely synchronize main and retire verified feature branches for an explicitly requested merged PR number in interneth3ro/the-long-way-home. Branch-only development is the default; retain all safety gates for historical or explicitly authorized worktrees. Stop on uncertain preservation, incorporation, chat attachment or applicable Windows locks.
---

# Post-merge cleanup

Invoke only when the user requests cleanup for a specific PR number in
`interneth3ro/the-long-way-home`. Read [AGENTS.md](../../../AGENTS.md), including
retention and ZIP policies. This skill does not merge, implement follow-up work,
create commits/reports, archive chats or touch the former project.
Use ordinary Git and available read-only tools; do not run old cleanup scripts or
introduce helpers to bypass an unavailable safety check.

Choose and record one cleanup case before mutation. Case B is the default expected
workflow; Case A covers historical worktrees and future worktrees explicitly
requested by the owner. Never infer the case from the default alone.

- **Case B: Branch-only development (default).** Require reliable development/session
  history establishing that no separate feature worktree was created, corroborated
  by current worktree registrations and checks that no associated residual
  directory exists. An empty registration list for the feature, a missing path or
  unknown history alone is insufficient. Uncertainty blocks cleanup; never create
  a worktree to satisfy these checks. Worktree retirement and directory-specific
  handle inspection are not applicable. Retain every PR, incorporation, fresh
  local/remote branch-tip, clean-state, preservation, fast-forward-only, guarded
  branch-deletion and conversation archival reporting requirement below.
- **Case A: Feature worktree exists.** Apply all worktree identity, preservation,
  session-attachment, Windows handle-inspection and safe retirement gates below.

## Establish identity before mutation

1. Retrieve live GitHub PR URL/number, merged status/time, base/head repositories,
   base/head branch names, historical head SHA and merge SHA. Require merged into
   this repository's `main`, with the head in this repository too. Closed without
   merge, forks, missing metadata or ambiguous historical identity stop cleanup.
   Reject `main` or any protected/default branch as a feature retirement target.
2. Resolve canonical absolute Git roots/common directories and
   `git worktree list --porcelain`. Identify the surviving primary checkout on
   `main` or, in Case B, still on the exact historical feature branch pending the
   guarded switch in step 6. Identify that feature branch. In Case A identify the
   feature worktree by registered branch **and** HEAD, not its directory name;
   verify both roots share
   the expected common directory. In Case B verify that no worktree uses the branch.
   Resolve path casing and aliases on Windows; uncertain links or root overlap stop.
   Verify origin fetch and push URLs identify this repository; check fetch refspecs
   and configuration for unexpected ref updates/pruning. Do not touch unrelated
   repositories, worktrees, branches, preservation refs, tags or snapshots.
3. Establish the requesting chat's current attached checkout using supported
   current-chat metadata; historical artifact lists, shell cwd and command
   `workdir` are insufficient. If metadata is unavailable, stop for the owner's
   explicit confirmation of this chat's exact attached checkout. Require this chat
   at the verified surviving primary checkout in Case B. In Case A require it outside
   the retiring root (and its descendants). If self-attached, retain everything
   and request cleanup from a chat based at the verified surviving primary checkout.
   Changing shell cwd does not relocate the chat or persistent MCP/REPL servers.
4. Record local/live `main` and feature tips plus relevant preservation refs.
   Every surviving feature tip must equal the historical PR head. A changed/reused
   branch, ambiguous detached checkout, locked/missing expected registration or inaccessible
   path blocks retirement. If targets are already absent, verify historical identity
   and actual absence; do not recreate them. An unregistered residual directory is
   a blocker, not an absent-success case. Do not guess its ownership or prune it.

## Verify incorporation and synchronize

5. After these gates, fetch narrowly without pruning or tags, for example
   `git fetch --no-prune --no-prune-tags --no-tags origin refs/heads/main:refs/remotes/origin/main`.
   Require the recorded merge result reachable from fresh `origin/main`.
   For a normal merge also verify the historical head is incorporated.
   For squash/rebase, obtain the original PR base/commits and exact incorporated
   delta/series; compare stable patch IDs or `git range-diff` **and review actual
   diffs**. Merge-commit ancestry alone does not prove squash/rebase equivalence.
   Explain conflict resolutions and later changes; stop retirement for unavailable
   history, unexplained differences or reverted/absent work. Never undo later edits.
6. Require clean tracked state in every affected checkout (the primary only in
   Case B), no in-progress Git operations, and local `main` equal to or an ancestor
   of fetched `origin/main`.
   Inspect the incoming diff and exact destination paths/ancestors for untracked
   or ignored collisions and protected local assets, settings, saves and evidence.
   Git can overwrite ignored files: a clean tracked status is insufficient.
   Do not recursively scan unrelated primary material. Stop on collisions,
   inaccessible paths, links/reparse points or uncertain preservation.
   In Case B, if the primary checkout remains on the verified historical feature
   branch, the explicit cleanup request authorizes `git switch main` only after
   all preceding identity, incorporation, attachment and preservation gates pass.
   Before switching, inspect the feature-to-local-main diff and its exact
   destination paths/ancestors for the same untracked/ignored collisions and
   protected material described above. Stop on any preservation uncertainty or
   switch refusal; never switch an unrelated owner's branch to make cleanup
   succeed. Recheck clean tracked state and preservation after switching.
   From the verified primary checkout on `main`, run
   `git merge --ff-only origin/main` (equal tips are a no-op). Never stash, reset
   or force-update `main` to make this succeed. Case A still requires the primary
   checkout already on `main`.

## Preserve material and establish retirement safety

7. In Case A inspect the feature worktree's untracked and ignored material with
   compact queries such as
   `git ls-files --others --exclude-standard --directory -z` and the same query
   with `--ignored`. Parse NUL-delimited paths safely. Inspect filesystem entries
   along indexed directories for Git-invisible/empty material, nested repositories,
   submodules, links/junctions and access failures. Git output alone is insufficient.
   Expand only flagged paths needed for a preservation decision; avoid repeated
   whole-tree inventories/hashes. Any unknown material blocks removal.
   In Case B there is no feature directory to inventory or remove. Preserve all
   material in the surviving checkout; retain step 6's collision checks and step 8's
   preservation policy. Do not classify primary material as disposable or create a
   ZIP merely because a feature branch is being retired.
8. Preserve saves, source artwork, settings, tools and unverified evidence. Ignore
   status, extensions or cache names (including `.godot/`) prove no disposal right.
   Archive only verified meaningful PR evidence under AGENTS.md's ZIP policy,
   outside the retiring checkout; verify contents/integrity and unchanged originals
   before exact eligible source retirement. No meaningful evidence means no ZIP.
   Only proven task-owned regenerable outputs may be removed as disposable.
   Use native PowerShell literal paths for exact file operations; verify resolved
   targets and ancestors remain in the intended root. Never recursively delete a
   checkout or unknown directory. Stop for clarification on uncertain preservation;
   report retained paths without disclosing private file contents.
9. Immediately before retirement, require quiescence and fresh chat-attachment,
   branch/HEAD, registration, tracked-state and material checks in both cases.
   In Case B revalidate the no-worktree evidence and absence of associated residuals;
   directory-specific handle inspection is not required because no directory is
   retired. Concurrent writers or uncertain quiescence still block branch retirement.
   In Case A on Windows use an already available read-only handle inspection tool
   with reliable coverage of
   the exact root and descendants, including directory cwd owners and relevant
   file handles. Record tool/method, scope, owners and coverage limits in the
   response. Process names or a lack of Git locks do not establish lock safety.
   Known locks, incomplete access/coverage, concurrent writers or unavailable
   inspection tools stop Case A retirement of the worktree **and branches**.
   Do not kill processes, close handles remotely or bypass an app removal guard. A non-forced
   Git removal is the final gate, not a substitute for these checks.

## Retire only verified targets and verify the result

10. In Case B report worktree retirement as not applicable and proceed to step 11
    only after all applicable gates pass. In Case A, from a surviving directory,
    run `git worktree remove <exact-feature-path>`
    without force, only after all gates pass. Never remove the primary checkout,
    requesting chat's checkout or a containing directory. On refusal or partial
    removal stop and retain branches; inspect/report registration and residual
    path state. Never fall back to recursive deletion, forced removal or pruning.
11. Recheck exact local feature tip and that no registered worktree uses it.
    Use `git branch -d <feature-branch>`. If and only if verified squash/rebase
    equivalence explains its ancestry refusal, `git update-ref -d
    refs/heads/<feature-branch> <historical-head-sha>` permits compare-and-delete
    after confirming no unique work. Other refusals stop. Never use `branch -D`.
    Recheck the remote feature tip. If still the historical head, delete with an
    exact lease: `git push --force-with-lease=refs/heads/<feature-branch>:<historical-head-sha>
    origin :refs/heads/<feature-branch>`. Never retry a rejected lease with a new
    expected SHA or unguarded force. Already-absent branches are no-ops.
12. Verify live `main`/feature tips, local `main` equality to current remote,
    incorporation, expected worktree/branch absence, clean tracked primary state
    and unchanged preservation refs/material. If live `main` moved, reassess rather
    than claiming equality to stale tracking refs. Do not routinely prune refs or
    worktree registrations. Missing targets are repeatable no-ops only after all
    applicable identity/incorporation checks; unresolved residuals remain blockers.

Never use blanket `git clean`, hard resets, force worktree removal or destructive
shortcuts. Do not launch games or save-writing checks as part of cleanup.
Stop on any failure; retain remaining targets and never claim complete cleanup
after a partial failure. No scan is atomic: if quiescence cannot be established,
preserve the target and report the uncertainty.

Report PR/merge/head identity, primary/local/live `main` state, exact worktree and
branch outcomes, preserved material/archive verification, checks and limitations,
and any blocker with the action needed to resolve it. Do not generate a separate
report file. Distinguish completed phases, intentional no-ops and pending work.

## Conversation archival eligibility

Every final cleanup report, including blocked or partial results, must include a
**Conversation archival eligibility** section. Identify the original feature
conversation and the separate cleanup conversation; assess each independently
and explicitly report exactly one of these outcomes for each:

- **Safe to archive:** The original feature PR is merged, its changes are verified
  as incorporated, the local/remote feature branches are safely retired or
  verified absent, any associated feature worktree is safely retired or verified
  absent (not applicable in Case B), and no unresolved preservation or session
  dependencies remain for the conversation being assessed.
- **Not safe to archive:** Cleanup is incomplete or blocked, or known dependencies
  remain for the conversation being assessed.
- **Requires owner review:** Cleanup status or the conversation's identity,
  attachment or preservation state cannot be established confidently. This
  includes uncertainty about the original feature conversation even when the
  separate cleanup conversation's state is known.

Give the evidence and reasoning supporting each result, remaining blockers and
what would resolve them. In Case B, the feature conversation remaining attached to
the surviving primary checkout does not itself prevent safe archival once all
relevant preservation, Git and session dependencies are resolved. Do not require
directory-specific Windows handle inspection when no directory is retired.
Git cleanup success alone does not establish that either or both conversations
are safe to archive. Never automatically archive
conversations; the owner makes that decision.
