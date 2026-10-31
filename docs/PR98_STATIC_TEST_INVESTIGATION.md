# PR #98 static-test investigation

Repository: `interneth3ro/the-long-way-home`; branch `codex/96-native-47-pattern-prototype`.
Reviewed HEAD: `56e2990fb8866b36f87d49d746e0cf7b9f9062e2`.
Main: `48cd9150d7aa2e029c7328229e7865cf00e83723`.

## Current disposition (2026-10-31)

The corrections below were independently reviewed and committed in
`1e5b5ee2a92d75b384ae8c9aa74b8a23a099a898`. Later sections retain the original
pre-publication investigation and its historical HEAD/results. Statements about
proposed or uncommitted corrections describe that earlier phase.

The owner accepts the technical prototype, including the unresolved initial
vertical-boundary limitation in the [prototype report](NATIVE_TERRAIN_47_PROTOTYPE.md#owner-graphical-acceptance-and-accepted-limitation).
Both initial vertical tests remain FAIL. The six local resource modifications are
explained preservation discrepancies with an approved preserve-in-place disposition.
No byte allowances, normalization, test changes or policy exceptions are introduced.

Final documentation validation: clean isolated proposed PR **119/119 PASS**, focused
terrain **6/6 PASS**. A separate corrected-PR representation overlaid with the six
exact owner resources reproduces **119 run, 12 failure records across 10 methods,
0 errors: FAIL**, focused terrain **6/6 PASS**. The attached checkout remains on
main and untouched; this overlay represents the PR with owner working resources,
not main's older suite. All twelve records below remain enforced. Historical Git
objects and exact hash pins introduced by the correction remain unchanged.

### Forensic findings and approved preservation

The chooser retains all 104 stored property values; its changes are UID/header
metadata and ordering, with no numeric-value change or omitted property. Other
resource differences match serialization/default omissions. Six writes occurred
within approximately 107 milliseconds, each followed by an editor-folding write.
This strongly favors a shared Godot resource-save event. The initiating action
and edited-resource origin remain unknown; standalone lab loading was not proven
to cause it. No meaningful resource-property defect was identified statically.

The owner approved preserving all six resources and their evidence unchanged,
excluded from PR #98. Their committed main and reviewed PR blobs are identical.
These hashes are preserved byte-for-byte by this documentation task:

| Owner resource | SHA-256 |
| --- | --- |
| `assets/ui/b1_theme.tres` | `6d917bc7973141b9d67fee7165c042c6233d26147470bd9b81a44645dc51e7de` |
| `assets/ui/machine_actions.tres` | `2c821aca22a4a04607d2a14a7aa7b2b9dea47d503e4cc39d89ef2f1b303a027e` |
| `assets/ui/recipe_chooser.tres` | `2ea79ef841294dc7e935d5cc69cce84db6140c8531b466bc14d6e9940c9f1130` |
| `dialogue/computer_opening.tres` | `daed226185e98955a0a21e4c8839f45d5f28ef36526a95881f3c3ea456a1bcea` |
| `construction/recipes/ferrite_plate.tres` | `b7c9e7a34ace78f51c0a89ee19be23cab62ace2bf2e1f4a565d1643349852bd1` |
| `construction/recipes/ferrite_rod.tres` | `7c687cd3a26b6bb8c471da418992994bf7b34738281a3e12ef42a813c2009631` |

The prior 2,231-file preservation inventory remains unchanged. This task also
inventories current attached-checkout files and verifies them after publication.
No owner file is moved, deleted or modified; its index, branch and HEAD remain
unchanged. Production terrain/gameplay and all mapping records remain unchanged.
PR #97 remains untouched. No Godot, Native, profiling, benchmarking, merge or cleanup.

Readiness is **CLEAN for the limited technical prototype**, pending explicit owner
merge authorization. Accepted limitations do not establish final artwork,
production performance or procedural determinism; Issue #96 remains open.

## Initial read-only comparison

| Scope | Test methods | Failure records | Errors | Failed methods |
| --- | ---: | ---: | ---: | ---: |
| Clean committed main | 107 | 0 | 0 | 0 |
| Clean committed PR #98 | 113 | 3 | 0 | 3 |
| Owner working tree | 113 | 17 | 0 | 13 |

Failure records include failing subtests; 17 does not mean 17 distinct test methods.
Both clean environments were fresh standalone local clones populated from exact
commits. They share Git objects read-only, not owner working files, and have their
own Git indexes. They are not registered worktrees. Initial Git status was empty
and remained empty after static validation. No owner cache/save/local asset was copied.
The owner checkout was neither switched nor altered. Temporary diagnostic copies
are retained under ignored `artifacts/tmp/`; no retirement or cleanup is performed.
The original 6 tracked edits, 16 untracked files and 2,209 ignored files were
inventoried and SHA-256 hashed before testing (87,284,138 bytes total).

Categories: A = genuine PR regression; B = existing main failure; C = owner
working-tree change; D = outdated/incorrect test expectation; E = preservation
conflict requiring owner decision; F = unknown. No initial main failures were found.
Three PR-only failures are historical guard incompatibilities (A/D), not demonstrated
terrain/gameplay regressions. Ten byte-preservation failures are C/E; four UID
failure records are C/D, caused by a test defect exposed by owner serialization.

## Exact original 17-record inventory

Every row has clean-main result PASS. `PR FAIL` means the assertion also fails in
the clean committed PR; all other rows require local owner modifications to reproduce.
None of the six owner-modified production resources differs between committed main
and committed PR #98; all six remain unstaged local changes. The owner previously
authorized keeping them in place and described them as likely manual-playtesting edits.

| # | Module/assertion (including subtest) | Category | Files and change scope | Expected | Actual | Clean PR | Requires owner edits |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | `static_conversation_ui_test.ConversationUIStaticTest.test_compact_controls_leave_layout_text_and_shared_styles_unchanged` | C/E | assets/ui/b1_theme.tres (first mismatch; also guards machine_actions) | Exact historical shared-style bytes | Editor header UID, property order and number formatting differ | PASS | Yes |
| 2 | `static_conversation_ui_test.ConversationUIStaticTest.test_gameplay_ownership_and_narrative_unchanged (path='dialogue/computer_opening.tres')` | C/E | dialogue/computer_opening.tres | Exact historical dialogue bytes | Header UID/load_steps and removed comment differ | PASS | Yes |
| 3 | `static_extractor_inspection_test.ExtractorInspectionStaticTest.test_smelter_dispatch_preserves_approved_extractor_and_fabricator (path='assets/ui/machine_actions.tres')` | C/E | assets/ui/machine_actions.tres | Exact approved theme bytes | Editor header UID/order/number formatting differ | PASS | Yes |
| 4 | `static_fabricator_inspection_test.FabricatorInspectionStaticTest.test_chooser_candidate_and_gameplay_boundary` | C/E | assets/ui/recipe_chooser.tres | Pinned approved SHA-256 | Expected 0be69e2cÃ¢â‚¬Â¦; actual LF hash 2ea79ef8Ã¢â‚¬Â¦ | PASS | Yes |
| 5 | `static_fabricator_inspection_test.FabricatorInspectionStaticTest.test_protected_methods_and_other_presentations_preserved` | C/E | assets/ui/machine_actions.tres | Exact historical adjacent presentation | Editor serialization differs | PASS | Yes |
| 6 | `static_ground_rejection_test.GroundRejectionStaticTest.test_distant_operation_counts_and_unchanged_systems` | A/D | .gitattributes (changed by original PR #98) | Original PR #95 four font-path attributes | Two exact mapping-path attributes appended; original font rules retained | FAIL | No |
| 7 | `static_machine_icons_test.MachineIconsStaticTest.test_protected_assets_gameplay_and_execution_controls_match_pr91` | A/D + C | Three experimental PNG/TileSet/lab paths; six local production resources | Changed paths all belong to historical approved inventory | Committed new experiment is unrecognized; dirty checkout adds six owner paths | FAIL | No |
| 8 | `static_musing_ui_test.MusingUIStaticTest.test_italic_staging_scope_metadata_and_historical_controls` | A/D | .gitattributes (changed by original PR #98) | Original three font rules plus exact Italic rule | Same two mapping-path attributes break full-file equality | FAIL | No |
| 9 | `static_musing_ui_test.MusingUIStaticTest.test_narrative_progression_and_adjacent_ui_preserved (path='assets/ui/b1_theme.tres')` | C/E | assets/ui/b1_theme.tres | Exact historical B1 resource | Editor serialization differs | PASS | Yes |
| 10 | `static_musing_ui_test.MusingUIStaticTest.test_narrative_progression_and_adjacent_ui_preserved (path='dialogue/computer_opening.tres')` | C/E | dialogue/computer_opening.tres | Exact historical narrative resource | Editor serialization differs | PASS | Yes |
| 11 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_ferrite_icon_candidate_restores_main_and_rejects_tampering (path='construction/recipes/ferrite_plate.tres')` | C/E | construction/recipes/ferrite_plate.tres | Pinned Ferrite icon candidate bytes | UIDs added and explicit default quantities/cycle omitted | PASS | Yes |
| 12 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_ferrite_icon_candidate_restores_main_and_rejects_tampering (path='construction/recipes/ferrite_rod.tres')` | C/E | construction/recipes/ferrite_rod.tres | Pinned Ferrite icon candidate bytes | UIDs added and explicit default ingredient quantity/cycle omitted | PASS | Yes |
| 13 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_protected_existing_code_art_and_sidecars_unchanged` | C/E | construction/recipes/ferrite_plate.tres (first mismatch) | Exact protected baseline after verified icon adapter | Adapter rejects non-pinned owner serialization | PASS | Yes |
| 14 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_has_no_dev_dependency_and_valid_declarations` | C/D | assets/ui/b1_theme.tres | All dependency UIDs resolve to tracked resources | Checker mistakes own header UID uid://j1imorduxy1e for unresolved external dependency | PASS | Yes |
| 15 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_rejects_dev_paths_and_unknown_uids (source='scenes/main/main.gd', edge='res://scenes/dev/forbidden.tscn')` | C/D | assets/ui/b1_theme.tres; injected main.gd dev path | Reject injected forbidden dev path | Unrelated self-UID assertion occurs first and masks intended error | PASS | Yes |
| 16 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_rejects_dev_paths_and_unknown_uids (source='scenes/main/main.gd', edge='res://SCENES\\DEV\\forbidden.gd')` | C/D | assets/ui/b1_theme.tres; injected main.gd mixed-case dev path | Reject injected forbidden dev path | Same self-UID assertion masks intended error | PASS | Yes |
| 17 | `static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_rejects_dev_paths_and_unknown_uids (source='inventory/inventory_state.gd', edge='res://scenes/dev/forbidden.tscn')` | C/D | assets/ui/b1_theme.tres; injected inventory_state.gd dev path | Reject injected forbidden dev path | Same self-UID assertion masks intended error | PASS | Yes |

## Final reconciliation of every original record

| Original row | Result with proposed corrections | Remaining cause |
| --- | --- | --- |
| 1 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 2 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 3 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 4 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 5 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 6 | FAIL (owner scope only) | Attribute defect resolved; unchanged guard now reaches local assets/ui/b1_theme.tres byte mismatch |
| 7 | FAIL (owner scope only) | Three pinned experiment paths accepted; all six local owner production-resource edits still rejected |
| 8 | PASS | Exact mapping-attribute projection preserves all font rules |
| 9 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 10 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 11 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 12 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 13 | FAIL (owner scope only) | Original strict byte/hash preservation assertion still rejects the same local owner resource |
| 14 | PASS | UID declaration recognized; dev-path rejection fixture reaches intended assertion |
| 15 | PASS | UID declaration recognized; dev-path rejection fixture reaches intended assertion |
| 16 | PASS | UID declaration recognized; dev-path rejection fixture reaches intended assertion |
| 17 | PASS | UID declaration recognized; dev-path rejection fixture reaches intended assertion |

No new failure IDs were introduced. All 12 final working-tree failure records belong to original methods/subtests. The isolated committed PR inputs plus corrections pass all of them.

## Verified causes and resource review

The six owner changes were present before the 94-pattern revision. In-session
pre-revision hashes match the current files, and the owner explicitly requested
retention. Git confirms their committed blobs are identical on main and PR #98.
The historical tests read working file bytes (using existing pinned adapters for
older accepted changes), not a clean committed snapshot. Their strict byte/hash
failures are therefore legitimate working-tree preservation conflicts, not proof
of PR-introduced gameplay regressions. They are not waived.

A nonexecuting block/property comparison found serialization order, UID/header
metadata, numeric formatting and a removed dialogue comment. The only other
property differences were omitted defaults: ingredient quantity 1, Plate output
quantity 1, recipe cycle 3.0 (matching the unchanged GDScript exports), and B1's
StyleBoxLine thickness 1 (the documented default). This is consistent with editor
serialization; it is not engine or behavioral verification. No production-resource
correction is justified by this investigation, and none is implemented or requested.
See [RecipeDefinition](../construction/recipe_definition.gd),
[RecipeIngredient](../construction/recipe_ingredient.gd) and the official
[StyleBoxLine default](https://docs.godotengine.org/en/stable/classes/class_styleboxline.html#class-styleboxline-property-thickness).

The old resource-graph checker registered only tracked `.uid` and `.import`
sidecars, then treated every `uid://` token as a dependency. The owner's valid
`[gd_resource ... uid="uid://j1imorduxy1e"]` header declares the B1 Theme's own
identity; it does not require a sidecar. That missing registration generated one
false graph failure and masked three negative fixtures that expected a forbidden
path error. The fourth pre-existing unknown-UID negative fixture already passed,
because the unrelated failure text happened to match its expected error phrase.
This masking is why the four failure records did not identify four broken assets.
Godot's [text-resource loader](https://github.com/godotengine/godot/blob/master/scene/resources/resource_format_text.cpp)
reads the header UID as `res_uid` separately from external-resource references.
This source inspection supports the format distinction; no 4.7.2 execution occurred.
After correcting registration, the production graph and all forbidden-path/unknown-UID
fixtures pass against the preserved working resources. No actual dependency defect
was found in that static graph scope; runtime validity remains unverified.

The two exact mapping attribute rules preserve owner-supplied file hashes under
Git newline conversion: the original CSV has CRLF, while the original Markdown
has LF. Removing or broadening those rules would change the data-preservation
contract. Both old assertions froze the entire attributes file to four font rules;
all four font rules still match the main baseline. The new exact full-file hash
projection recognizes only main or the already-reviewed main-plus-two-mapping-rule
bytes. Duplicate rules, wildcard replacements, altered font rules and other edits
are rejected. `.gitattributes` itself is unchanged by this investigation.

The whitelist uses `git diff <historical MACHINE_ICONS_BASE>` with no second commit,
so it intentionally includes working changes relative to that older baseline. It
is not a clean PR diff. The three committed experiment inputs reproduce the failure
in a clean PR clone; owner modifications add six more disallowed paths locally.
The correction retains this working-tree guard, recognizing only three exact paths
with full candidate hashes from reviewed `56e2990`. No directory, production asset,
UID metadata sidecar or new execution capability is exempted.

## Proposed corrections and review destination

These changes are prepared locally on the existing PR #98 branch for owner review.
No new PR, staging, commit, push or PR metadata update is performed. If approved,
the intended destination is a focused test/documentation follow-up commit to draft
PR #98 on `codex/96-native-47-pattern-prototype`.

- [native_terrain_preservation.py](../tests/native_terrain_preservation.py) implements
  exact mapping-attribute and three-input projections. Two corrected historical
  test files are also full-file pinned before older whole-tree checks project
  their reviewed prior bytes; changes, duplication and appended bytes are rejected.
  This avoids opening a path exemption for the test corrections themselves.
- [static_ground_rejection_test.py](../tests/static_ground_rejection_test.py),
  [static_musing_ui_test.py](../tests/static_musing_ui_test.py) and
  [static_machine_icons_test.py](../tests/static_machine_icons_test.py) consume those
  narrow projections. Production working bytes remain protected.
- [static_v2_production_host_test.py](../tests/static_v2_production_host_test.py)
  registers embedded text-resource UIDs, rejects duplicates and malformed
  declarations, and checks external UID/path consistency. Unknown references and
  dev paths still fail. Two added methods cover valid declarations, duplicate IDs,
  UID/path mismatches and missing external UIDs.
- [static_preservation_guards_test.py](../tests/static_preservation_guards_test.py)
  adds four methods for exact attribute/input/test-correction pinning, altered,
  duplicated and appended-byte rejection, and explicit rejection of owner-resource
  projection or whitelisting.
- This investigation and the [terrain report](NATIVE_TERRAIN_47_PROTOTYPE.md) replace
  the earlier attribution of Theme UID failures to invalid resources with verified
  scope-specific findings. Terrain assets, gameplay, main scene, runner, AGENTS.md,
  execution policy and preservation policy are unchanged.

No owner-resource byte allowances, semantic normalization of owner resources,
production edits or policy relaxations are proposed. Satisfying the remaining local
byte guards would require a separate owner decision about exact preserved resource
candidates; that work is outside this correction. The current working-tree suite
must continue reporting FAIL until that conflict is explicitly resolved.

## Results and reproducibility

| Validation scope | Methods | Failure records | Errors | Result |
| --- | ---: | ---: | ---: | --- |
| Exact committed main `48cd915` | 107 | 0 | 0 | PASS |
| Exact committed PR #98 `56e2990` | 113 | 3 | 0 | FAIL |
| Initial preserved owner working tree | 113 | 17 (13 methods) | 0 | FAIL |
| Isolated committed PR inputs plus proposed test corrections | 119 | 0 | 0 | PASS |
| Owner working tree plus proposed test corrections | 119 | 12 (10 methods) | 0 | FAIL |

All methods are discovered with `unittest.defaultTestLoader.discover('tests',
pattern='static_*test.py')` and executed by the normal unittest runner without
filters, skips or monkeypatches added by the diagnostic driver. Six new regression
methods account for 113 -> 119. For normal console reproduction, run
`python -B -m unittest discover -s tests -p 'static_*test.py'` in the named scope.
The temporary diagnostic driver captures every failure/subtest and traceback in
the ignored evidence record; its process exit status is not used as the PASS criterion.
Actual failures/errors determine the table above. No project code or Godot is run.

The focused PR #98 terrain suite is **6/6 PASS**; new preservation regressions are
**4/4 PASS**; focused resource-graph checks are **4/4 PASS**, including original
negative fixtures. Changed Markdown links and Git whitespace checks pass.
A first corrected working-tree run overlapped a documentation-only edit; a final
frozen-input repeat provides the final working-tree evidence. Test sources and all
owner resources remain unchanged during that repeat.

The initial inventory and all complete-suite failure records are retained in
[pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b.json](../artifacts/evidence/pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b.json). The two isolated clones and diagnostic driver remain in
[the task-owned diagnostic directory](../artifacts/tmp/pr98-static-diagnosis-ae589cda0bc94778833d56dfd34bfb6b/). They contain committed inputs and task-created test corrections only;
no owner local/ignored data was copied. No temporary directory is retired here.
Future retirement would require verifying these exact task-owned paths and their
contents against preservation requirements; this investigation authorizes no
cleanup of pre-existing artifacts or the owner's attached checkout.

Preservation checks cover all 2,231 original modified/untracked/ignored files and
compare their exact SHA-256 hashes after the investigation. All are unchanged.
Production terrain/gameplay and control files have no new diff, the Git index is
unchanged with no staged edits, HEAD is still `56e2990`, and PR #97's branch remains
`840ca4df88feeb6ce0fd40d20d590631db4234fc`. PR #98 remains draft and unmodified remotely.
No Godot, Native, profiling, benchmarking, artwork, integration, merge or cleanup occurred.

Recommendation: continue PR #98 as an isolated draft after reviewing the narrow
static-test corrections. The corrected committed-input scope is green. Do not
represent the owner working tree as fully validated or infer graphical acceptance,
production readiness or Native permission from these results.
