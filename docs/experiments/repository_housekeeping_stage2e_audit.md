# TLWH — Repository Housekeeping
## Stage 2E: Nested Diagnostic Clone Audit

Audit date: 2026-11-02.

Publication status: owner-requested temporary draft PR for external review and access. Pending review; no merge, clone retirement, cleanup, or engine execution is authorized.

**Disposition: two clones are safe retirement candidates; one needs its unique validation commit preserved first. No retirement is authorized or performed by this report.**

This file compiles the completed read-only audit. It was created afterward at the owner's explicit request; the read-only verification below describes the audit before this report file was added. No audit was rerun to create this document.

## A. Repository baseline

- Repository: `interneth3ro/the-long-way-home`.
- Primary checkout: `<PRIMARY_CHECKOUT>`.
- Initial and final branch: `main`.
- Initial and final HEAD: `59348ae29116f34865d8be0f58bf163551fe350e`.
- Local `main`, `origin/main`, and live GitHub `main` matched.
- [PR #116](https://github.com/interneth3ro/the-long-way-home/pull/116) was merged. Its feature branch was absent locally and remotely; only the primary checkout was registered.
- Initial and final ordinary Git status: clean.
- Inventory matched Stage 2D: 691 tracked files, zero untracked files, and 625 ignored entries. These comprise 618 ordinary Godot-cache files, three validation-profile files, one protected audit Markdown file, and three nested-repository placeholders.

`AGENTS.md` and the Stage 2A, 2C, and 2D disposition/completion records were reviewed. Historical “acceptance pending” wording remains unchanged; live GitHub confirms the subsequent merge.

Direct `git ls-remote` failed because of a network-resolution error. Live GitHub identity and merge verification used the connected GitHub service instead. No fetch was performed.

## B. Clone inventory

The following repository-relative paths identify the exact proposed retirement boundaries. All are beneath the primary checkout above.

| ID | Clone path |
| --- | --- |
| V — validation | `artifacts/tmp/pr98-reviewed-commit-validation-f0b58fe35a6a4e79b7c94c873af5a831/isolated` |
| M — baseline | `artifacts/tmp/pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b/main` |
| P — corrected PR | `artifacts/tmp/pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b/pr98` |

| Clone | HEAD prefix | Local / remote refs | Working files | Working bytes | Git files / bytes | Total logical bytes | State |
| --- | --- | --- | ---: | ---: | --- | ---: | --- |
| V | `791c48b1` | 1 / 4 | 315 | 32,141,460 | 27 / 64,551 | 32,206,011 | Clean, detached |
| M | `48cd9150` | 1 / 4 | 303 | 31,998,315 | 26 / 62,489 | 32,060,804 | Clean, detached |
| P | `56e2990f` | 1 / 4 | 314 | 32,121,567 | 26 / 63,869 | 32,185,436 | Dirty, detached |
| **Total** | | | **932** | **96,261,342** | **79 / 190,909** | **96,452,251** | |

Four remote refs include three remote-tracking branches and symbolic `origin/HEAD`. Each clone has zero tags and zero other refs.

### Exact HEAD identities

```text
V 791c48b1c4001d9b2b52f6ecd73535417514af6b
M 48cd9150d7aa2e029c7328229e7865cf00e83723
P 56e2990fb8866b36f87d49d746e0cf7b9f9062e2
```

### Repository administration and configured remotes

All three have independent `.git` directories and indexes, with `origin` pointing to the parent checkout, `<PRIMARY_CHECKOUT>`. These origins are local paths, not GitHub URLs. Their history belongs to the parent TLWH repository.

All borrow the parent's `.git/objects` through alternates. None is a linked worktree, shallow repository, or self-contained clone. No reparse points, replacement refs, grafts, custom hooks, or local packs were found. The parent has no reciprocal alternate dependency.

Each clone has the same five refs:

| Ref | Target |
| --- | --- |
| `refs/heads/codex/96-native-47-pattern-prototype` | `56e2990fb8866b36f87d49d746e0cf7b9f9062e2` |
| `refs/remotes/origin/HEAD` | Symbolic reference to `refs/remotes/origin/codex/96-native-47-pattern-prototype` |
| `refs/remotes/origin/codex/96-native-47-pattern-prototype` | `56e2990fb8866b36f87d49d746e0cf7b9f9062e2` |
| `refs/remotes/origin/codex/96-native-terrain-prototype` | `840ca4df88feeb6ce0fd40d20d590631db4234fc` |
| `refs/remotes/origin/main` | `48cd9150d7aa2e029c7328229e7865cf00e83723` |

These are historical local-clone refs. The live GitHub `codex/96-native-47-pattern-prototype` branch had advanced to `1d2a506eb81ddaf863a2287688134dc451cc466e` at audit time.

## C. Git history findings

- M and P contain no objects absent from the parent database.
- V contains exactly one unique commit, with no unique trees or blobs.
- Both historical HEADs `48cd9150…` and `56e2990f…` are ancestors of current `main`.
- The `840ca4df…` prototype tip remains protected locally and matches its live GitHub branch.
- V's local-only commit was unavailable through GitHub's commit endpoint, which reported no commit for that SHA.

### Unique validation commit

```text
Commit: 791c48b1c4001d9b2b52f6ecd73535417514af6b
Parent: 56e2990fb8866b36f87d49d746e0cf7b9f9062e2
Tree:   18c623b778fc3dc35fd142f066b328eaec2079da
```

Its message identifies it as an isolated validation snapshot of the owner-reviewed PR #98 correction tree. Its author and committer use the synthetic Codex Static Validation identity.

Its tree exactly matches published commit:

```text
1e5b5ee2a92d75b384ae8c9aa74b8a23a099a898
Fix reviewed static preservation and resource UID checks
```

GitHub confirmed that published correction is an ancestor of live `main`. Thus V's source content is preserved, but its distinct validation commit identity is not independently preserved.

The exact commit payload is **327 bytes**, SHA-256:

```text
e3b833c248c6c629b36778febe7d286a03641cac32edaa99e53bb4c8113c64d6
```

The existing compressed loose-object file is 211 bytes, SHA-256:

```text
96dfcb121b456635677ac75783fb498dcce5976d5848c353035ca73bd920d59f
```

### Reflogs, reachability, and integrity

Reflogs contain five entries in V and four each in M/P. Their commit targets are already preserved except for V's snapshot. Remaining events describe cloning and detached checkouts; no additional lost development history was found.

Visible inventories, including borrowed objects, are:

| Clone | Commits | Trees | Blobs | Commits reachable from clone refs and HEAD |
| --- | ---: | ---: | ---: | ---: |
| V | 322 | 1,536 | 1,668 | 259 |
| M | 321 | 1,536 | 1,668 | 258 |
| P | 321 | 1,536 | 1,668 | 258 |

Read-only full Git integrity checks exited successfully. With reflogs excluded as roots, V reported 63 unreachable commits, 659 trees, and 600 blobs; M/P each reported 63 commits, 662 trees, and 608 blobs. These reported unreachable objects belong to the shared parent object database. None represents another unique clone-local object.

V physically stores only its one unique loose commit object. M and P physically store no loose or packed Git objects. No objects were imported into the parent.

## D. Working-file findings

Every working file maps to a blob reachable from current `main`:

| Clone | Byte-identical to current tracked files | Historical CRLF checkout form | Exact historical blob |
| --- | ---: | ---: | ---: |
| V | 253 | 62 | 0 |
| M | 245 | 58 | 0 |
| P | 253 | 59 | 2 |

CRLF equivalents were distinguished from byte-identical copies. No original was normalized or rewritten.

P has no staged changes. Its unstaged modifications are:

```text
tests/static_ground_rejection_test.py
tests/static_machine_icons_test.py
tests/static_musing_ui_test.py
tests/static_v2_production_host_test.py
```

Its untracked files are:

```text
tests/native_terrain_preservation.py
tests/static_preservation_guards_test.py
```

All six match the versions committed in `1e5b5ee2…`: the four modified files differ only by checkout line endings, and the two untracked files match committed bytes exactly.

| File under P | Raw working-file SHA-256 |
| --- | --- |
| `tests/static_ground_rejection_test.py` | `80c7b91736ccfaae6e5713d158746a3abf3cf72c074f9680541443c1b508a4ad` |
| `tests/static_machine_icons_test.py` | `90b755505146a706c2e5ef5f143e9a40853442a15c258182e42b600ec23164d8` |
| `tests/static_musing_ui_test.py` | `15510006e5e47d1c4fb71536671517ba8db754f220bc12068f15c3825addc6fa` |
| `tests/static_v2_production_host_test.py` | `abe79a6f770d04d5d647da748979d38573ba8c0f6be0992c5ecfda92ac25780e` |
| `tests/native_terrain_preservation.py` | `79ecfda2de8e8765ffcb42c2dff67232bc5e7e30f82bd3d36239cca95857b40f` |
| `tests/static_preservation_guards_test.py` | `6f2cf93c2d35755b67d81579288333c1f5052b9a220c90ec47568318a8df0a3a` |

No clone contains ignored working files, generated Godot caches, saves, additional diagnostic outputs, or unique artwork.

### Historical purpose and preservation evidence

The [PR #98 investigation](../PR98_STATIC_TEST_INVESTIGATION.md) and committed evidence establish their purpose:

- M held the clean historical main baseline.
- P held PR #98 inputs plus proposed static-test corrections.
- V held the exact reviewed correction tree for isolated validation.

These were static-test diagnostic copies. Their purpose is not inferred from their names.

The PR #103 and #104 Native source baselines subsequently recorded all **1,011 files**, including Git administration; every recorded hash still matched:

- `artifacts/evidence/pr103-native-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b/source-baseline.json`
- `artifacts/evidence/pr104-native-review-28f57c4c-677f-4f9e-8809-7be9fc66f2d6/source-baseline.json`

Related committed PR #98 evidence identities:

| Record | SHA-256 |
| --- | --- |
| `artifacts/evidence/pr98-reviewed-commit-validation-f0b58fe35a6a4e79b7c94c873af5a831.json` | `a49a35183dca8310832b47a4533e941dd715e5094c0f6b3fccd6512204b00951` |
| `artifacts/evidence/pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b.json` | `8cbcb49ca8321b83b35cb31246fa3bb205a683198b9887f96ee3f13e36b97c03` |

No unique freeze, performance, or headless-smoke result was discovered. No PR #107/#108 experimental content was reintroduced.

### Privacy review

The unique commit contains synthetic validation identity and provenance. No credential patterns or account-directory paths were found in the six test candidates. Their source is already published.

Git configuration and reflogs contain local checkout information and identity metadata. A future preservation record should summarize those relationships with role placeholders rather than publish raw configuration or reflogs. Existing private originals and historical receipts should remain untouched.

## E. Recommended disposition

| Clone | Recommendation | Confidence |
| --- | --- | --- |
| V | **B — Preserve unique material, then retire** | High |
| M | **A — Safe retirement candidate** | High |
| P | **A — Safe retirement candidate**, with its dirty state explicitly recorded | High |

For P, retirement would discard an uncommitted state, but no unique file content: all six changes are already committed and historically hash-pinned. Do not reset or clean it before retirement.

No clone currently warrants permanent protected-exception status.

## F. Proposed future implementation plan

1. Prepare a focused preservation/retirement feature PR from clean, synchronized `main`.
2. Preserve V's exact 327-byte commit payload as inert historical evidence, plus a privacy-reviewed provenance record. Verify its SHA-256, recomputed Git commit identity, parent, tree, and equivalence to `1e5b5ee2…`. No object import is necessary.
3. Record all three clone HEADs, refs, statuses, working-file hashes, administration hashes, counts, sizes, and alternate relationships. Preserve existing historical receipts unchanged.
4. Commit and verify preservation before any deletion. Use documentation-sync before PR review to reconcile maintained documentation in the same feature PR; do not rewrite historical evidence.
5. Obtain explicit authorization for the three exact directories in section B. Recheck immediately before retirement:
   - Expected HEADs, refs, counts, hashes, and dirty state.
   - No new files, commits, refs, dependencies, or external activity.
   - Every target and ancestor remains inside the intended checkout and is free of reparse points.
   - Parent history and preservation evidence remain available.
6. Remove only those verified directory boundaries using native exact-path operations. They are standalone repositories, so linked-worktree retirement is unnecessary. Do not use broad `git clean` or delete their containing diagnostic directories.
7. Verify parent status, protected refs, evidence, caches, and profiles afterward. Reconcile ignored inventory and update maintained documentation without rewriting historical receipts.

Expected removal: **1,011 files totaling 96,452,251 logical bytes**, approximately **91.98 MiB**. This excludes the parent object database and is not a measurement of allocated space or net free-space gain. New preservation evidence would slightly reduce net savings.

Stop on any identity mismatch, new material, changed dependency, reparse point, or failed preservation check. Owner decisions remain publication approval for V's payload/provenance and explicit retirement authorization. This report does not grant those approvals.

### Working-file manifest digests

These digests can support future verification. Each hashes UTF-8 JSON with sorted keys and compact separators, mapping clone-relative paths to `[file_length, lowercase_sha256]`. Working manifests exclude `.git`; administration manifests contain its files. Recompute the full per-file manifests and compare individual identities as well as these aggregate digests before retirement.

| Clone | Working manifest SHA-256 | Administration manifest SHA-256 |
| --- | --- | --- |
| V | `8b4de98a2718e045d765b010fd6c904128ec4a4af74482f1a8e6badec0eb3512` | `c1e88dc36e31f981453eb7f8613e97b33d2e6a2402f0e72df825320a1b257aef` |
| M | `ad6536598ad1cc676c92b59f7f68f32983fe754d21574bdce7447c98b061f7f2` | `e19ec017d5ebca8dbff19cbf3a0d73f4fcba306434f4aca3706882117aa49684` |
| P | `da89e5b61f790bb351658e158b5e1d324f7445d371237d16d89d129f1e1a38c3` | `3f35b11796cc51f29705822cca7fb06649cce32b1330d73ea0f7489a88168b25` |

## G. Read-only audit confirmation

Final verification matched the audit baseline for all **2,707 inspected files**, including sizes, modification times, and SHA-256 hashes. Parent and clone HEADs, statuses, refs, configurations, and complete visible object inventories were unchanged. No external repository-state changes were detected between the captured baseline and final verification.

The 618 ordinary cache files, three validation-profile files, PR #5 bundle, and preserved PR #5 diagnostic evidence remained unchanged. PR #5 evidence also matched its committed preservation pins. Its previously approved deleted ZIP remained absent.

During the audit, no files, branches, commits, PRs, temporary inspection files, refs, or objects were created or removed. No fetch, checkout, maintenance, cleanup, project tests, historical scripts, or Godot execution occurred. All verification was static/read-only; no runtime, graphical, gameplay, or performance acceptance is claimed.

The local Markdown compilation was created after the audit at the owner's request. This publication copy was subsequently authorized for a temporary draft PR. It replaces the absolute checkout location with `<PRIMARY_CHECKOUT>`, adjusts the relative documentation link, and adds publication context. Audit findings and historical verification remain unchanged; no new audit or engine verification is claimed. No historical receipt, clone, cache, profile, or PR #5 evidence is modified by publication. The work stops at the draft PR for owner review.
