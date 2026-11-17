# TLWH comprehensive test-suite audit — 2026-11-13

Audit target: interneth3ro/the-long-way-home, local main at d6802406feed90f6c4a7bdedde8cebfeafca4068 (PR #195 merge).

This is an investigation and recommendation, not implementation or execution authorization. The owner separately approved creating this report and its CSV appendix during the audit. No source/test/runner/policy files were changed, no branch was created, and nothing was committed, pushed, merged or cleaned up.

## A. Executive assessment

The suite provides substantial asset, scene, data-contract and historical-preservation protection, but weak evidence of current automated gameplay behavior. Its routine gate has become a mixture of useful validators, duplicated Python models, milestone-specific source checks and historical implementation freezes. Consequently the current gate is red even though many failures follow documented, merged feature changes.

The documented Python command ran 683 methods in 375.772 seconds. There were 630 passing methods, 51 distinct failing methods producing 84 failure records, no errors, and two optional skips. Do not subtract 84 from 683 to calculate passing methods: unittest records multiple failed subtests within a single method.

Both maintained inert PowerShell suites passed: local runner 60/60, codec runner 55/55. These execute real runner helpers, filesystem operations on owned inert fixtures and harmless PowerShell children. They do not establish Godot loading, parsing, physics, production, graphics or gameplay correctness.

No Godot executable was launched in this audit, including version/help/import commands. No GDScript test was executed. Resource Generation v2, Cuprite production, construction transactions and recent presentation lifecycle fixes therefore lack a current automated runtime PASS established here. Owner-reported F5 acceptance is separate evidence, and historical codec/metadata PASS records remain valid only for their tested revisions and scopes.

The best modernization opportunity is to use the existing standalone GDScript assertions, after fixing obsolete fixtures and reviewing their dependency/runtime scope, rather than building a large framework. Preserve useful static integrity checks and runner safety behavior. Move historical provenance checks to explicit preservation validation, and replace source-spelling assertions with small behavioral cases that call the real implementation.

## Scope, checkout and preservation

- Read AGENTS.md and docs/LOCAL_TESTING.md, including consumed metadata grants. Also inspected the dedicated codec runner and docs/SAVE_CODEC_RUNNER.md.
- HEAD, local main and cached origin/main all equaled d6802406. A read-only git ls-remote origin refs/heads/main attempt failed with getaddrinfo() thread failed to start. Live remote synchronization could not be established; no fetch, pull or checkout was performed.
- Initial working status contained 22 untracked .gd.uid files under construction/, scenes/ and tests/. Tracked working files and the index were clean. The same untracked UIDs were still present before writing the approved report files.
- The task explicitly forbids all Godot execution and supersedes the narrower standing Native permission for this audit. NativePlan was not run: although it does not launch Godot, it creates a real retained external stage.
- MetadataSmoke is inactive; all three documented grants are consumed. The codec runner returns PREPARED and its historical grant is consumed. No activation or inventory amendment was made.
- Existing fixtures create fresh inert temporary trees and verify their exact ownership before their own cleanup. Running those documented fixtures did not authorize cleanup of any existing owner artifact or real engine stage.
- Python used -B. No deliberate bytecode generation, artwork modification, save/settings operation or historical-project work occurred. There was no pre-audit hash census of every ignored file, so this report does not claim such a census.

## B. Inventory and counting method

The CSV beside this report is the detailed inventory. Filter row_kind for python_case, gd_assertion, powershell_group, historical_python_case, infrastructure or failure_record. It records path/line/name, claimed protection, actual artifact/helper references, real-logic execution boundary, category, dispatch, result, failure implication, relevance, overlap, maintenance/value, disposition, replacement rationale and assertion expressions.

A Python method is one independently meaningful assertion group; its loops and subtests are retained inside that group. Assertions and referenced helpers are catalogued, rather than treating every assert or input value as an independent test. GDScript uses one assertion/rejection call site per row; helper calls and helper definitions' internal assertions are both visible, not flattened into a claimed runtime count. PowerShell uses one authored Check block per group; loops can instantiate it several times. Historical test methods outside tests/ are counted separately.

The inventory includes all tracked files in tests/, all 13 tools/ files, the additional experiment validator, historical Python validation/review scripts, testing-related documentation/configuration, fixture data and directly named existing production inputs. Dynamic asset families remain represented by the tests' authoritative manifests and helpers; the CSV does not duplicate every production texture manifest or count artwork as test cases. Infrastructure rows are not extra executable cases.

Category tags overlap. A case can inspect source text, compute a Python model and verify historical bytes. Category totals below are tags on method groups, not independent tests or runtime coverage percentages. The assertion column supplies the concrete evidence behind each group. A passing source check is not execution of the described gameplay behavior.

### Verified inventory

| Item | Count / status |
| --- | --- |
| Tracked files under tests/ | 145 |
| Python discovery files | 88 |
| Declared and actually discovered Python methods | 683 |
| Other Python helper/reference modules under tests/ | 19 |
| GDScript scripts under tests/ | 19 |
| Additional GDScript validator | scenes/experiments/production_terrain/engine_validation.gd |
| Maintained PowerShell fixture scripts | 2 |
| Authored PowerShell Check groups | 60 local + 33 codec = 93 |
| Actual PowerShell checks in this audit | 60 local + 55 codec = 115 |
| Historical Python test methods outside discovery | 25 PR103 + 4 PR104 = 29 |
| GDScript assertion/rejection source call sites | 984 under tests/ + 64 experiment = 1,048 |
| GDScript scripts in ordinary Native dispatch | 1, recipe switching only |
| GDScript scripts behind inactive dedicated recipes | 2, metadata smoke and codec |
| Other GDScript scripts with no maintained current dispatch | 17 including the experiment validator |
| GDScript scripts executed by this audit | 0 |

Tests/ also contains ten tracked UID files (including the metadata builder alias), four JSON fixtures/inventories, two minimal project.godot templates and one Cuprite .tres fixture. The production project is a target, not a universal test launcher.

### Discovery and entry points

| Entry point | Actual scope | Audit execution |
| --- | --- | --- |
| python -B -m unittest discover -s tests -p 'static_*test.py' | All 88 matching files and 683 methods; imports helper modules | Executed once |
| tools/run-local-tests.ps1 default/Static | Same Python selection, 60-second bound | Inspected; not redundantly rerun |
| tests/local_runner_fixture_test.ps1 | Actual runner helper behavior with inert inputs/doubles | 60 PASS |
| tools/run-local-tests.ps1 -Mode NativePlan | Static gate, hash identity and fresh retained real external stage; no engine | Not run |
| tools/run-local-tests.ps1 -Mode Native | Static gate, cold import, recipe-switching script only | Not run; task forbids Godot |
| tools/run-local-tests.ps1 -Mode MetadataSmoke | Draft 32-input recipe, denied by inactive gate | Not run |
| tests/save_codec_runner_fixture_test.ps1 | Dedicated codec-runner inert behavior and grant-consumption safety | 55 PASS |
| tools/run-save-codec-tests.ps1 -Mode Static | Inert codec fixtures then Python suite; static bound 600 seconds | Inspected; components run directly once |
| tools/run-save-codec-tests.ps1 default/Run | PREPARED denial before workflow side effects | Exercised only by documented inert denial probes; no engine |
| tools/terrain-stage2b2-diagnostics.py | Explicit offline gate plus bounded diagnostic image generation | Inspected; not run, would create unrequested outputs |
| tests/extractor_artwork_offline.py, tests/smelter_artwork_offline.py | Explicit active-art checks or optional external frozen-package reconstruction | Active validators covered through suite; no redundant CLI/external package run |
| Historical artifacts/evidence Python scripts | PR-specific supervisor/review/regeneration/report logic | Inspected, not dispatched or rerun |

No tracked .github workflow or pytest/Pester configuration was found. Routine discovery is the explicit unittest glob. Default unittest discovery uses test*.py and would miss static_*test.py. GDScript filenames do not create automatic discovery. Merely checking that assertion labels occur in a .gd file does not dispatch it or establish that it parses.

Historical scripts under artifacts include PR98 static-diagnosis/verification wrappers, PR100 proof/render scripts, PR103 supervisor plus 25 inert test methods, and PR104 supervisor/review checks. Several depend on old external review locations or write evidence. Preserve them as historical material; do not silently enroll them in routine discovery.

### What the files protect

The complete 88-file Python table and 20-script GDScript table follow the recommendations below. Every individual method/call site is in the CSV.

- Application, loading, pause, doorway, hatch and transition tests mostly parse scripts/scenes, assert literal guard/order fragments and run independent Python geometry/state models. They do not schedule real Godot awaits, signals, tweens or physics.
- Resource v2 definition/generator/starting/integration/placement/presenter/Cuprite static tests mostly inspect text and calculate policy bounds or independent examples. This includes useful negative-coordinate, halo, query-budget and spacing reasoning, but not execution of the actual generator.
- Ferrite tests execute the production Python catalog builder/geometry functions in places; region/streaming behavior is largely a separate Python Oracle/model paired with source fragments. This is not a runtime test of FerriteRegionGenerator.
- Terrain tests check real asset bytes, scene/resource declarations, mapping completeness, shared edges, source contracts and extensive rational/numerical reference models. Some invoke actual Python authoring/baking functions in memory. They do not establish GPU sampling, Godot numeric parity or current renderer runtime correctness.
- Machine artwork/animation tests decode actual PNG data, verify imports/registration/provenance and model motion. Shared footprint and transaction requirements are frequently asserted through source spelling or historical equality. They do not animate actual Godot tweens or perform current gameplay transactions.
- Codec/journal static tests provide useful independent byte vectors and checksum/framing models. Native decode, actual rejection ordering and authoritative recovery remain authored GDScript behavior, except for the recorded historical codec run.
- Preservation helpers mix legitimate immutable evidence/artwork identity with fragile projections of current gameplay source back to old feature revisions. The latter creates cross-feature maintenance and failure cascades.

## C. Baseline and quantitative interpretation

Executed once:

    python -B -m unittest discover -s tests -p 'static_*test.py'

Result: 683 tests in 375.772s; FAILED (failures=84, skipped=2); exit 1. No ERROR records. Distinct failing methods: 51. Passing methods: 630.

The two skips are optional external Fabricator packages:

- FabricatorArtworkStaticTest.test_external_frozen_packages_and_direct_png_byte_equality: TLWH_FABRICATOR_FROZEN_ROOTS not supplied.
- FabricatorAnimationStaticTest.test_complete_external_inventory_exact_copy_and_seventeen_frozen_poses: TLWH_FABRICATOR_FRONT_FROZEN_ROOT not supplied.

These skips are honest limits on external-source reconstruction. Repository PNG checks still ran. No external package identity claim is made.

The local fixture script ended Fixtures: 60 PASS, 0 FAIL. Godot import/test: NOT RUN. The codec fixture script ended Codec runner fixtures: 55 PASS, 0 FAIL and Godot import/runtime: NOT RUN. Deliberately injected failure/timeout/denial messages in their output are successful negative scenarios, not failed fixture results.

Normal Static, NativePlan and Native wrappers retain a 60-second Python budget; MetadataSmoke has 360 seconds; the codec path has 600 seconds. The direct suite's 375.772s exceeds both 60 and 360. This is an observed budget mismatch on this audit run, not a benchmark or proof of timing on an isolated future run. Fixtures assert these values, so casually changing a deadline would itself violate reviewed controls. First reduce routine selection/cost and review the resulting gate; do not remove bounded supervision.

No coverage instrumentation was used. Test counts and source call-site counts are not branch coverage, state-space coverage or numerical certification.

## D. Failure analysis

All 84 failure records appear in the CSV with a stable F001–F084 identifier, full method/subtest identity, cause group and disposition. The table below groups underlying causes without suppressing individual traceability.

| Group | Failure records | Assessment / action |
| --- | ---: | --- |
| H1 | 16 | Historical initial-preparation projection no longer reverses current exterior-resource changes; nested mutation checks fail before the intended injected path is evaluated. ARCHIVE old-source projection or REWRITE the current contract. |
| H2 | 45 | Current source, feature inventory or old inactive-plan input differs from an earlier milestone snapshot after merged v2/Cuprite/layout/lifecycle changes. Approved implementation evolution conflicts with historical preservation scope. Separate immutable evidence from current behavior. |
| S1 | 8 | Valid checks tied to literal method location or limit spelling. Validation moved to shared helpers or adapter-selected bounds. REWRITE around the call graph/real behavior. |
| O1 | 8 | Obsolete isolated/inactive/exclusive-Ferrite boundaries conflict with merged live v2/Cuprite behavior. Replace the old expectation while retaining authority separation and legacy compatibility. |
| M1 | 1 | Current inactive metadata package has real dependency-closure drift. INVESTIGATE; keep gate inactive. |
| G1 | 5 | Reference extractor mistakes a directory prefix string for an actual dependency and masks negative-fixture diagnostics. REWRITE parser and isolate its fixture graph. |
| P1 | 1 | Historical local-only bytecode inventory mismatch. INVESTIGATE separately; preserve file and immutable receipt. |

### Concrete findings

H1: initial_exterior_preservation.verified_initial_paths() attempts to reconstruct the old exterior at 5ab32bd using exact textual reversals. Later resource presenter setup/lifecycle code survives that projection. Its failure affects Fabricator preservation cases and the pause-menu case. The application-shell mutation test contributes twelve records because all four injected unexpected paths encounter the same earlier failure in three consumer cases. This demonstrates diagnostic coupling; it does not establish twelve separate unsafe admissions.

H2: whole-file/method equality and git diff since old feature baselines freeze construction_controller.gd, placement_rules.gd, planet_world_state.gd, planet_exterior.gd, machine_ui.gd, extractor.tres and starting_resource_generator.gd. Local history records the relevant live integration/production changes in PRs #192–#194 and layout/window/retention changes merged in PR #195. In particular b6ee5c2 changes starting-v2-2, band preferences and the 4,096-attempt ceiling; ba48f71 changes live presentation bounds; 1592275 retains presentation across visits. These conflicts have an identifiable evolution path. Their failing first assertions do not prove later assertions in the same method would pass, nor prove those feature implementations bug-free.

S1: deploy_machine_instance() now delegates to _deploy_machine_transaction(), which still checks legacy generation readiness, PlacementRules.rejection(), inventory removal, shared claim/registry writes and guarded notifications. ExtractorAnchorRules.rejection() delegates compatibility/alignment/occupancy to member_rejection(). Tests demanding those strings directly in the old entry method fail although the guard still exists. Presenter bounds now select area_limit and descriptor_limit according to adapter; the guard is no longer the exact MAX_AREA_AXIS/MAX_DESCRIPTORS expression. Replace these source-local assertions with actual invalid-placement/query tests.

O1: live_extractor_v2_test.gd still expects “no Cuprite production or legacy Ferrite output”, and its static companion requires inactive v2 production/inspection. Current Cuprite production is deliberately enabled. Other old checks ban starting-generator callers, PlanetWorldState in the presenter, resource-definition paths in the exterior or any preload in PlanetExterior. Those bans overreach the current architecture. Keep the meaningful boundaries: simulation must not depend on presentation state, presenter queries cannot mutate authority, and legacy Ferrite output must remain correct. A type annotation or read-only world adapter is not by itself ownership of gameplay state.

M1: static_metadata_smoke_test.test_fixed_inventory_dependency_closure_and_no_assets fails on unstaged construction/extractor_anchor_rules.gd. A complete static scan also finds ResourceGenerationV2Integration and preloads of inventory/cuprite_ore.tres and inventory/ferrite_ore.tres referenced by staged PlanetWorldState. These are newly missing direct dependencies of the fixed inventory; this scan is not a complete substitute for a future reviewed transitive-closure review. The historical 32-input smoke PASS is for its old revision. Do not widen its allowlist, strip production methods, run it or label the current package compatible without a scoped decision and renewed review/authorization.

G1: static_v2_production_host_test.assert_resource_graph() follows every regex match for res://... in script text. resource_presentation_catalog.gd:47 contains begins_with("res://assets/") for path validation. The scanner enqueues assets/ and asserts it is a file. That causes the ordinary graph test and Keep-metadata test to fail, and three subtests of the negative-reference validator to fail for the wrong reason. This is a valid reference-closure safeguard implemented with an overbroad extractor, not evidence that assets/ should become a file. Prefer extracting actual ext_resource/preload/load constant operands and distinguishing directory/prefix validation strings. Keep injected forbidden-path/unknown-UID tests on a small synthetic graph so unrelated current code cannot mask the expected rejection.

P1: static_housekeeping_test.test_disposition_integrity_and_deferred_files_are_preserved reads any currently existing path in the historical Stage 2A deletion inventory and requires its original bytes. tests/__pycache__/current_preservation.cpython-314.pyc currently has 2,838 bytes and SHA-256 112226ce406970261cb1cb97b075c139e28b816b03e0c72c6d6b86c6fd0752a4. The immutable historical entry records 12,520 bytes and b3294aba6c41c64b7265ffeebcb214e435720ecf658cda867480b584ef3f9b49. This is a deletion-inventory entry, not an approved current source asset. Its origin/time of recreation was not established. -B avoids this audit intentionally writing bytecode. Do not delete, restore or rebaseline it to make the gate green; resolve its relationship to historical ownership/completion records separately. A routine clone should not need to reproduce a transient cache's old identity.

None of the observed failures independently establishes a gameplay regression. M1 is a present test-package defect; G1 is a present validator defect; P1 is unresolved local historical-state evidence. The rest predominantly identify stale/rigid expectations with a documented change path. Actual gameplay regressions remain possible because the relevant current GDScript behavior has not been executed.

## E. Coverage gaps, ordered by gameplay risk

| Risk | Existing useful material | Missing confidence / next focused cases |
| --- | --- | --- |
| V2 determinism and identity | ordinary_resource_generator_test.gd, contract test, integration test; static hash/channel/halo math | Actual production generator equality across signed seeds, query order, eviction/reload, canonical IDs and defensive copies. Retain a small explicit seed/coordinate corpus; do not claim all-seed proof. |
| Starting guarantees | starting_resource_generator_test.gd and cuprite_world_layout_test.gd; Python feasibility examples | Real exact 3 Ferrite/2 Carbite/2 Cuprite layouts, revised policy rejection, complete-arrangement admission, protected bounds and deterministic budget exhaustion without partial publication. |
| Spacing/protection/ownership | Independent spacing/halo calculations; authored raw-competitor and reservation-priority scenarios | Actual cross-owner conflict chains, all-or-nothing groups, negative boundaries, query completeness and no ordinary displacement of reserved deposits. |
| Construction and occupancy | extractor_anchor_test.gd and overlapping live/Cuprite fixtures | Actual current authoritative ticket validation, frozen click selection, geometry/rotation, physics obstruction, inventory rejection, one claim/ID registry and reentrant notification rollback. |
| Cuprite / Ferrite compatibility | cuprite_gameplay_test.gd, new static cases, owner F5 report | Correct authoritative item at production/collection/recovery; stale/forged metadata; full-buffer no backlog; failed insertion preserves state; legacy Ferrite route works with unavailable v2; replace obsolete inactive-Cuprite fixture. |
| Streaming and retained presentation | resource_presenter_v2_test.gd, cuprite gameplay/lifecycle fixtures; live-window bounds | Real page-sized queries under 49-chunk startup and larger retention windows; loaded-chunk filtering; exactly retained sprite identity; cancellation versus detach/revisit; world/token replacement; no stale publication; failed admission clears state. |
| Production / transactions / recovery | Fabricator production/deployment/switching/recovery scripts and computer restoration script | Actual multi-ingredient rollback, independent stored product identity, finite/invalid deltas, capacity boundaries, pause lease ownership, recovery contents and callbacks observing committed state. |
| Scene transition / startup cancellation | Strong static/source checks and Python decision tables | No dedicated current behavioral script for all controller/startup await points. Add finite scene-tree cases for cancellation/detach/replacement, fail-closed readiness, rollback, input drain, pause restoration and exactly one unlock/success notification. |
| World-state integrity | Copy/token/revision assertions spread across authored scripts | Consolidated real mutation-invariance tests: caller snapshots cannot mutate authority; stale context cannot resolve or redirect; failed replacement cannot resurrect prior state; claim cleanup follows successful recovery. |
| Persistence | Codec historical 261-check PASS, current static vectors; journal authored rejection/authority suite | Current codec runtime rerun needs separate approval; journal has no maintained dispatch. Gameplay snapshot mapping, publication filesystem protocol, save discovery, load into gameplay and migration are not implemented, so no end-to-end save/load coverage exists to certify. |

The newer Cuprite fixture substantially repeats live_extractor_v2_test.gd. Prefer one current deployment/claims fixture plus resource-specific production cases. Keep the older inactive milestone only as historical evidence if needed; never run mutually contradictory expectations as the same current contract.

Many fixtures use private fields, direct seeded machine dictionaries, synthetic inventory subclasses or simplified source doubles. These are useful fault-injection seams and transaction tests, but they do not prove an ordinary player can reach every state. Pair a small engine integration layer with focused owner playtests for visible presentation and input feel. Avoid turning all current authored assertions into one enormous default engine run.

## F. Lean modernization strategy

Use four explicit scopes with honest result labels:

1. **Routine static integrity:** real scene/resource references and UID validity, schema/data validation, stable public architecture boundaries, current definition geometry and accepted asset identity. Share parsers and data tables; do not copy a regex parser into each feature test.
2. **Bounded behavior on real GDScript:** existing SceneTree scripts for descriptor/generation/transactions first. Use the current pinned engine and reviewed external-stage controls only after explicit approval of new inventory/commands/assertions. A small fixed manifest suffices; no third-party plugin is required.
3. **Small integration/owner acceptance:** scene-tree/physics/UI lifecycle cases separately from scene-free logic. Keep graphical visual acceptance explicit. A headless sprite or Control assertion does not verify rendered artwork, clipping, sound or interaction feel.
4. **Explicit preservation/offline mathematics:** immutable historical receipts, approved original artwork/packages and substantial reference-model proofs remain available outside the routine gameplay gate. Retain meaningful independent vectors; avoid two large Python copies of a generator standing in for its execution.

Source identity checks before and during an authorized engine run are useful controls: they ensure that reviewed/tested inputs did not change. They serve a different purpose from a regression test demanding that an evolving gameplay method remain byte-identical to an old feature commit. Preserve the former. Rework the latter.

Keep exact wire-format byte vectors, canonical ID examples, immutable published evidence hashes and explicitly approved asset identities where identity is the actual contract. Avoid blanket “remove all hashes” policy. Remove redundant source-fragment/byte-count freezes only when replacement current-contract coverage exists.

A method marked REWRITE in the CSV can contain useful assertions. Split/retain those assertions rather than deleting the whole method. ARCHIVE means remove it from routine dispatch while preserving its history/data, not delete files or alter old receipts. CONSOLIDATE requires one maintained replacement before duplicate removal. No recommendation here authorizes cleanup.

## G. Prioritized implementation roadmap

| Stage | Scope / value | Dependencies and exit evidence | Effort / risk |
| --- | --- | --- | --- |
| 1 | Repair current static signal: G1 extractor/isolated validator fixtures; inventory and retire obsolete milestone expectations; separate current behavior from H1/H2 historical snapshots | Focused tests show real missing references still rejected; each changed expectation traced to approved contract; report complete actual baseline, no blanket skip/rebaseline | Medium; low runtime risk, moderate preservation-review risk |
| 2 | Resolve M1 and P1 explicitly without executing or cleaning up | Decide current metadata-package purpose and review dependency closure; reconcile optional historical cache policy with immutable records; no new engine authority implied | Small investigation, potentially medium package change; safety-sensitive |
| 3 | Consolidate routine static validators and duplicate helper imports; remove test-to-test imports where practical; separate slow math/preservation scope | One shared scene/resource/UID and image/import validator; retain corruption tests and owner pins; deterministic explicit dispatch; justify reviewed static deadline/selection from actual runs | Medium; moderate test-maintenance risk |
| 4 | Prepare minimal behavior recipe for contracts + ordinary/starting generation + world boundary | Review exact input closure and current fixtures, fixed process budgets and completion results; owner separately approves activation/execution; stop on first failure, no retries | Medium; medium engine/fixture risk |
| 5 | Add current transaction and Cuprite/Ferrite behavioral subset | Fix obsolete inactive-Cuprite case; retain unique fault injection; approved run proves production/collection/recovery, occupancy and failure atomicity | Medium; high gameplay value |
| 6 | Add presentation/transition integration only where needed | Bounded lifecycle scenarios; stale callbacks/cancellation/retained sprites; distinguish headless from separately approved graphical checks | Medium to large; higher engine/scene risk |
| 7 | Persistence follow-up when gameplay saving is scoped | Independently authorize codec/journal recipes; retain goldens; design actual snapshot/load/publication coverage with the implementation | Deferred; avoid speculative save infrastructure |

Stages are focused feature PRs if implementation is authorized later. Do not stack a broad test rewrite with gameplay changes. Begin implementation from the required clean synchronized main, preserve the present untracked UIDs, and obtain owner direction if they prevent that precondition. This audit created only the two specifically approved documentation artifacts.

Success is not a target test count. It is a short routine gate that detects damaged current data, a finite approved behavior suite that fails on real production regressions, clear dispatch/results, and historical evidence that no longer freezes ordinary development.

## H. Owner decisions

Only these decisions require owner direction before later work:

- Approve the first scoped modernization stage and the distinction between immutable historical evidence and current-source regression contracts. This is not approval to delete evidence or change canon/artwork.
- Decide whether the old metadata smoke should remain historical-only or be redesigned/reviewed for current inputs; keep the existing inactive gate until a separately approved amendment.
- Decide the disposition of the optional regenerated bytecode mismatch through the preservation workflow. No cleanup is requested or authorized by this audit.
- If behavioral execution is desired, approve the exact prepared recipe, dependency inventory, assertions, binary, budgets and one supervised run or specifically defined future standing scope. Current grants do not cover the proposed suites.

No framework/plugin choice or broad approval ceremony is needed to begin a separately approved static-only improvement. No engine run, deadline expansion, inventory expansion, merge or cleanup has been authorized here.

## Verification limits

Verified: local tracked inventory and dispatch code; all declared Python methods; source assertion/rejection groups in GDScript and inert fixtures; the single complete Python baseline; both inert fixture suites; relevant production/helper call paths and merged local change history; current static metadata-closure omissions.

Inferred: likely cause of historical expectation conflicts based on source/history; priority and effort of modernization; meaningful gameplay risks. The report does not claim full absence of functional regressions.

Not executed: Godot, GDScript, graphical/physics gameplay tests, NativePlan, benchmarks/performance probes, freeze reproduction, historical supervisors, external frozen-package reconstruction or diagnostic generation.

Unknown: live remote main after the network failure; origin/time of the differing local bytecode file; current engine parsing/type-checking of undispatched fixtures; current runtime results of authored gameplay cases; GPU/graphical correctness and all-seed guarantees.

## Appendix 1 — Method-category and disposition totals

Categories overlap and describe assertion methods, not executed gameplay coverage. These classifications include model/data work and direct tool calls within mixed methods.

| Python method tag | Groups |
| --- | ---: |
| Python model/data computation (not gameplay) | 201 |
| executed Python tool behavior | 40 |
| historical preservation | 232 |
| source-text inspection | 451 |
| structural/static validation | 683 |

| Recommended Python method-group disposition | Groups |
| --- | ---: |
| ARCHIVE | 27 |
| CONSOLIDATE | 56 |
| INVESTIGATE | 2 |
| KEEP | 225 |
| REWRITE | 373 |

Disposition applies to the current assertion method. KEEP is not a claim of gameplay execution; REWRITE preserves useful obligations; REMOVE recommendations are limited to obsolete GDScript inactive-Cuprite assertions after replacement.

## Appendix 2 — Every Python discovery file

All paths below are under tests/. Every named method and its assertion expressions are in the CSV. Mixed file dispositions are intentional.

| File | Methods | PASS | FAIL methods | SKIP | Dispositions |
| --- | ---: | ---: | ---: | ---: | --- |
| static_application_shell_test.py | 5 | 4 | 1 | 0 | KEEP 2, REWRITE 3 |
| static_automatic_transitions_test.py | 14 | 14 | 0 | 0 | KEEP 4, REWRITE 10 |
| static_baked_terrain_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, KEEP 3, REWRITE 2 |
| static_computer_restoration_test.py | 9 | 8 | 1 | 0 | KEEP 1, REWRITE 8 |
| static_conversation_ui_test.py | 5 | 5 | 0 | 0 | CONSOLIDATE 2, REWRITE 3 |
| static_cuprite_gameplay_test.py | 13 | 12 | 1 | 0 | CONSOLIDATE 1, KEEP 1, REWRITE 11 |
| static_cuprite_layout_test.py | 8 | 8 | 0 | 0 | CONSOLIDATE 1, REWRITE 7 |
| static_cuprite_presentation_lifecycle_test.py | 8 | 8 | 0 | 0 | KEEP 1, REWRITE 7 |
| static_current_preservation_test.py | 4 | 4 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 1, KEEP 2 |
| static_dave_rework_test.py | 9 | 9 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 1, KEEP 5, REWRITE 2 |
| static_east_idle_test.py | 7 | 7 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 4, KEEP 1, REWRITE 1 |
| static_east_walk_alignment_test.py | 8 | 8 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 4, KEEP 3 |
| static_exterior_boarding_test.py | 8 | 8 | 0 | 0 | REWRITE 8 |
| static_exterior_hatch_audio_test.py | 5 | 5 | 0 | 0 | KEEP 3, REWRITE 2 |
| static_exterior_hatch_visual_test.py | 6 | 6 | 0 | 0 | KEEP 5, REWRITE 1 |
| static_extractor_anchor_test.py | 13 | 10 | 3 | 0 | KEEP 1, REWRITE 12 |
| static_extractor_animation_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, REWRITE 5 |
| static_extractor_artwork_test.py | 8 | 5 | 3 | 0 | CONSOLIDATE 1, KEEP 3, REWRITE 4 |
| static_extractor_inspection_test.py | 2 | 2 | 0 | 0 | REWRITE 2 |
| static_fabricator_animation_test.py | 18 | 16 | 1 | 1 | CONSOLIDATE 2, KEEP 4, REWRITE 12 |
| static_fabricator_artwork_test.py | 10 | 8 | 1 | 1 | CONSOLIDATE 3, KEEP 1, REWRITE 6 |
| static_fabricator_footprint_test.py | 7 | 5 | 2 | 0 | ARCHIVE 1, CONSOLIDATE 2, REWRITE 4 |
| static_fabricator_inspection_test.py | 1 | 1 | 0 | 0 | REWRITE 1 |
| static_ferrite_catalog_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, KEEP 4, REWRITE 1 |
| static_ferrite_initialization_test.py | 6 | 5 | 1 | 0 | KEEP 3, REWRITE 3 |
| static_ferrite_integration_test.py | 9 | 6 | 3 | 0 | ARCHIVE 1, CONSOLIDATE 1, KEEP 2, REWRITE 5 |
| static_ferrite_presentation_test.py | 12 | 12 | 0 | 0 | CONSOLIDATE 1, KEEP 4, REWRITE 7 |
| static_ferrite_region_test.py | 9 | 8 | 1 | 0 | KEEP 5, REWRITE 4 |
| static_ferrite_streaming_test.py | 11 | 11 | 0 | 0 | REWRITE 11 |
| static_ground_admission_test.py | 6 | 6 | 0 | 0 | KEEP 5, REWRITE 1 |
| static_ground_approval_test.py | 4 | 4 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 1, KEEP 1, REWRITE 1 |
| static_ground_full_atlas_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, KEEP 4, REWRITE 1 |
| static_ground_portability_test.py | 4 | 4 | 0 | 0 | KEEP 4 |
| static_ground_publication_test.py | 10 | 9 | 1 | 0 | CONSOLIDATE 1, REWRITE 9 |
| static_ground_refinement_test.py | 9 | 9 | 0 | 0 | ARCHIVE 1, KEEP 8 |
| static_ground_rejection_test.py | 5 | 5 | 0 | 0 | KEEP 3, REWRITE 2 |
| static_ground_softness_test.py | 6 | 6 | 0 | 0 | KEEP 5, REWRITE 1 |
| static_historical_sanitization_test.py | 4 | 4 | 0 | 0 | ARCHIVE 1, KEEP 2, REWRITE 1 |
| static_housekeeping_test.py | 4 | 3 | 1 | 0 | INVESTIGATE 1, KEEP 2, REWRITE 1 |
| static_illustrated_exterior_test.py | 13 | 12 | 1 | 0 | REWRITE 13 |
| static_illustrated_terrain_presenter_test.py | 9 | 9 | 0 | 0 | REWRITE 9 |
| static_illustrated_terrain_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, KEEP 3, REWRITE 2 |
| static_initial_exterior_test.py | 7 | 6 | 1 | 0 | REWRITE 7 |
| static_live_extractor_v2_test.py | 13 | 10 | 3 | 0 | KEEP 1, REWRITE 12 |
| static_loading_screen_test.py | 12 | 11 | 1 | 0 | KEEP 1, REWRITE 11 |
| static_low_green_ground_test.py | 4 | 4 | 0 | 0 | KEEP 2, REWRITE 2 |
| static_machine_icons_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 2, REWRITE 4 |
| static_metadata_smoke_test.py | 6 | 4 | 2 | 0 | ARCHIVE 1, INVESTIGATE 1, REWRITE 4 |
| static_musing_ui_test.py | 3 | 3 | 0 | 0 | ARCHIVE 1, REWRITE 2 |
| static_native_terrain_47_test.py | 6 | 6 | 0 | 0 | CONSOLIDATE 1, KEEP 5 |
| static_north_idle_test.py | 6 | 6 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 4, KEEP 1 |
| static_north_walk_size_test.py | 7 | 7 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 4, KEEP 1, REWRITE 1 |
| static_opening_guidance_test.py | 5 | 5 | 0 | 0 | REWRITE 5 |
| static_ordinary_resource_generator_test.py | 13 | 11 | 2 | 0 | CONSOLIDATE 1, KEEP 1, REWRITE 11 |
| static_pause_menu_test.py | 5 | 4 | 1 | 0 | KEEP 1, REWRITE 4 |
| static_port_console_geometry_test.py | 7 | 7 | 0 | 0 | KEEP 7 |
| static_pr5_preservation_test.py | 6 | 6 | 0 | 0 | KEEP 3, REWRITE 3 |
| static_preservation_guards_test.py | 1 | 1 | 0 | 0 | KEEP 1 |
| static_production_terrain_test.py | 8 | 8 | 0 | 0 | KEEP 2, REWRITE 6 |
| static_publication_journal_test.py | 15 | 15 | 0 | 0 | KEEP 7, REWRITE 8 |
| static_resource_fixture_typing_test.py | 2 | 2 | 0 | 0 | ARCHIVE 2 |
| static_resource_generation_v2_integration_test.py | 10 | 9 | 1 | 0 | CONSOLIDATE 1, REWRITE 9 |
| static_resource_generation_v2_test.py | 8 | 7 | 1 | 0 | KEEP 6, REWRITE 2 |
| static_resource_live_window_test.py | 5 | 4 | 1 | 0 | KEEP 4, REWRITE 1 |
| static_resource_presenter_v2_test.py | 12 | 8 | 4 | 0 | CONSOLIDATE 2, REWRITE 10 |
| static_save_codec_runner_test.py | 9 | 9 | 0 | 0 | KEEP 9 |
| static_save_file_codec_test.py | 5 | 5 | 0 | 0 | KEEP 2, REWRITE 3 |
| static_smelter_artwork_test.py | 10 | 9 | 1 | 0 | ARCHIVE 1, CONSOLIDATE 1, KEEP 2, REWRITE 6 |
| static_smelter_footprint_test.py | 5 | 3 | 2 | 0 | CONSOLIDATE 2, REWRITE 3 |
| static_smelter_thermal_test.py | 13 | 12 | 1 | 0 | ARCHIVE 1, KEEP 3, REWRITE 9 |
| static_south_idle_test.py | 6 | 6 | 0 | 0 | ARCHIVE 1, CONSOLIDATE 4, KEEP 1 |
| static_stage2e_preservation_test.py | 2 | 2 | 0 | 0 | KEEP 2 |
| static_starting_resource_generator_test.py | 11 | 9 | 2 | 0 | KEEP 2, REWRITE 9 |
| static_terrain_c1_test.py | 8 | 8 | 0 | 0 | CONSOLIDATE 1, KEEP 5, REWRITE 2 |
| static_terrain_integration_test.py | 7 | 7 | 0 | 0 | CONSOLIDATE 1, KEEP 5, REWRITE 1 |
| static_terrain_resolver_test.py | 6 | 6 | 0 | 0 | KEEP 5, REWRITE 1 |
| static_terrain_stage2_coverage_test.py | 11 | 10 | 1 | 0 | KEEP 9, REWRITE 2 |
| static_terrain_stage2b2_reconstruction_test.py | 14 | 14 | 0 | 0 | ARCHIVE 1, KEEP 11, REWRITE 2 |
| static_terrain_stage2b_compatibility_test.py | 16 | 16 | 0 | 0 | ARCHIVE 2, KEEP 14 |
| static_terrain_stage3a1_metadata_test.py | 8 | 8 | 0 | 0 | ARCHIVE 1, KEEP 4, REWRITE 3 |
| static_terrain_stage3b_test.py | 7 | 7 | 0 | 0 | ARCHIVE 2, KEEP 3, REWRITE 2 |
| static_terrain_stage3c_test.py | 11 | 9 | 2 | 0 | ARCHIVE 2, KEEP 2, REWRITE 7 |
| static_terrain_stage3d_test.py | 3 | 2 | 1 | 0 | ARCHIVE 1, REWRITE 2 |
| static_transition_safety_test.py | 10 | 10 | 0 | 0 | REWRITE 10 |
| static_v2_connection_test.py | 6 | 6 | 0 | 0 | KEEP 2, REWRITE 4 |
| static_v2_production_host_test.py | 17 | 14 | 3 | 0 | CONSOLIDATE 1, KEEP 3, REWRITE 13 |
| static_v2_stationary_machines_test.py | 8 | 8 | 0 | 0 | KEEP 2, REWRITE 6 |
| static_weathered_earth_test.py | 4 | 4 | 0 | 0 | KEEP 1, REWRITE 3 |

## Appendix 3 — Every GDScript test/validator

Counts are source assertion/rejection call sites, including shared helper calls. They are not dynamic checks, not branch coverage and not runtime results. Every row is NOT RUN in this audit.

| Path | Call sites | Current dispatch | Recommendation |
| --- | ---: | --- | --- |
| tests/computer_restoration_test.gd | 28 | No active maintained runner dispatch; NOT RUN | KEEP 28 |
| tests/cuprite_gameplay_test.gd | 63 | No active maintained runner dispatch; NOT RUN | KEEP 63 |
| tests/cuprite_presentation_lifecycle_test.gd | 26 | No active maintained runner dispatch; NOT RUN | KEEP 26 |
| tests/cuprite_world_layout_test.gd | 12 | No active maintained runner dispatch; NOT RUN | KEEP 12 |
| tests/extractor_anchor_test.gd | 65 | No active maintained runner dispatch; NOT RUN | KEEP 65 |
| tests/fabricator_deployment_test.gd | 160 | No active maintained runner dispatch; NOT RUN | KEEP 160 |
| tests/fabricator_production_test.gd | 68 | No active maintained runner dispatch; NOT RUN | KEEP 68 |
| tests/fabricator_recipe_switching_test.gd | 40 | Fixed Native recipe only; NOT RUN in audit | KEEP 40 |
| tests/fabricator_recovery_test.gd | 42 | No active maintained runner dispatch; NOT RUN | KEEP 42 |
| tests/illustrated_exterior_native_validation.gd | 35 | No active maintained runner dispatch; NOT RUN | ARCHIVE 35 |
| tests/live_extractor_v2_test.gd | 33 | No active maintained runner dispatch; NOT RUN | CONSOLIDATE 32, REMOVE 1 |
| tests/metadata_smoke_test.gd | 27 | Inactive dedicated runner; NOT RUN | KEEP 27 |
| tests/ordinary_resource_generator_test.gd | 41 | No active maintained runner dispatch; NOT RUN | KEEP 41 |
| tests/publication_journal_test.gd | 75 | No active maintained runner dispatch; NOT RUN | KEEP 75 |
| tests/resource_generation_v2_contract_test.gd | 40 | No active maintained runner dispatch; NOT RUN | KEEP 40 |
| tests/resource_generation_v2_integration_test.gd | 65 | No active maintained runner dispatch; NOT RUN | KEEP 65 |
| tests/resource_presenter_v2_test.gd | 46 | No active maintained runner dispatch; NOT RUN | KEEP 46 |
| tests/save_file_codec_test.gd | 72 | Inactive dedicated runner; NOT RUN | KEEP 72 |
| tests/starting_resource_generator_test.gd | 46 | No active maintained runner dispatch; NOT RUN | KEEP 46 |
| scenes/experiments/production_terrain/engine_validation.gd | 64 | No active maintained runner dispatch; NOT RUN | KEEP 64 |

## Appendix 4 — Every failing method and subtest record range

The CSV supplies each individual F-number and subtest arguments. Group counts are failure records, not distinct methods.

| Method | Failure records | Cause group(s) |
| --- | --- | --- |
| static_application_shell_test.ApplicationShellTests.test_uid_amendment_keeps_historical_preservation_consumers_closed | F001, F002, F003, F004, F005, F006, F007, F008, F009, F010, F011, F012 | H1 |
| static_computer_restoration_test.ComputerRestorationStaticTest.test_existing_gameplay_methods_only_add_reviewable_feature_hooks | F013 | H2 |
| static_cuprite_gameplay_test.CupriteGameplayStaticTests.test_generation_construction_and_world_art_unchanged | F014 | H2 |
| static_extractor_anchor_test.ExtractorAnchorStaticTests.test_all_preexisting_gameplay_generation_artwork_and_controls_unchanged | F015 | H2 |
| static_extractor_anchor_test.ExtractorAnchorStaticTests.test_confirmation_resolves_identity_without_retargeting | F016 | S1 |
| static_extractor_anchor_test.ExtractorAnchorStaticTests.test_references_resolve_and_new_scope_is_exact | F017 | H2 |
| static_extractor_artwork_test.ExtractorArtworkStaticTest.test_active_port_free_artifact_identities_and_registration | F018 | H2 |
| static_extractor_artwork_test.ExtractorArtworkStaticTest.test_shared_adapter_and_composite_ghost | F019 | H2 |
| static_extractor_artwork_test.ExtractorArtworkStaticTest.test_simulation_placement_other_machines_and_stationary_preserved | F020, F021, F022, F023, F024 | H2 |
| static_fabricator_animation_test.FabricatorAnimationStaticTest.test_all_other_production_artwork_gameplay_and_execution_controls_preserved | F025 | H1 |
| static_fabricator_artwork_test.FabricatorArtworkStaticTest.test_gameplay_existing_artwork_and_execution_controls_preserved | F026 | H1 |
| static_fabricator_footprint_test.FabricatorFootprintStaticTest.test_preview_commit_obstacles_and_dave_use_shared_footprint | F027 | S1 |
| static_fabricator_footprint_test.FabricatorFootprintStaticTest.test_protected_gameplay_art_and_execution_controls_unchanged | F028 | H1 |
| static_ferrite_initialization_test.FerriteInitializationStaticTest.test_failure_blocks_dependent_session_and_production_paths | F029 | S1 |
| static_ferrite_integration_test.FerriteIntegrationStaticTest.test_extraction_points_near_all_edges_rotations_and_adjacent_machines | F030 | O1 |
| static_ferrite_integration_test.FerriteIntegrationStaticTest.test_extractor_occupancy_grid_and_shared_geometry_contract | F031 | S1 |
| static_ferrite_integration_test.FerriteIntegrationStaticTest.test_footprint_change_preserves_other_definitions_and_gameplay | F032 | H2 |
| static_ferrite_region_test.FerriteRegionStaticTest.test_legacy_contracts_and_persistent_lookup_wiring | F033 | S1 |
| static_ground_publication_test.GroundPublicationTest.test_protected_systems_wiring_and_existing_presenter_mutation_unchanged | F034 | H2 |
| static_housekeeping_test.HousekeepingStaticTest.test_disposition_integrity_and_deferred_files_are_preserved | F035 | P1 |
| static_illustrated_exterior_test.IllustratedExteriorStaticTest.test_default_selection_is_locked_once_and_legacy_does_no_illustrated_work | F036 | O1 |
| static_initial_exterior_test.InitialExteriorTests.test_existing_gameplay_and_publication_methods_are_exactly_preserved | F037 | H2 |
| static_live_extractor_v2_test.LiveExtractorStaticTests.test_unexecuted_behavior_and_preserved_inputs | F038 | H2 |
| static_live_extractor_v2_test.LiveExtractorStaticTests.test_v2_inspection_does_not_advertise_ferrite_production | F039 | O1 |
| static_live_extractor_v2_test.LiveExtractorStaticTests.test_v2_production_is_inactive_without_gates | F040 | O1 |
| static_loading_screen_test.LoadingScreenTests.test_hatch_gameplay_artwork_and_world_implementation_unchanged | F041 | H2 |
| static_metadata_smoke_test.MetadataSmokeTest.test_exact_change_scope_and_preserved_inputs | F042 | H2 |
| static_metadata_smoke_test.MetadataSmokeTest.test_fixed_inventory_dependency_closure_and_no_assets | F043 | M1 |
| static_ordinary_resource_generator_test.OrdinaryResourceStaticTests.test_preserved_foundation_gameplay_assets_and_controls | F044 | H2 |
| static_ordinary_resource_generator_test.OrdinaryResourceStaticTests.test_unregistered_native_definitions_have_provisional_relative_weights | F045 | O1 |
| static_pause_menu_test.PauseMenuTests.test_gameplay_and_assets_match_merged_shell_baseline | F046 | H1 |
| static_resource_generation_v2_integration_test.ResourceIntegrationStaticTests.test_world_owns_component_and_legacy_apis_remain_independent | F047 | O1 |
| static_resource_generation_v2_test.ResourceGenerationV2StaticTests.test_legacy_assets_simulation_and_controls_are_preserved | F048 | H2 |
| static_resource_live_window_test.LiveResourceWindowTests.test_generation_and_terrain_inputs_are_unchanged | F049, F050 | H2 |
| static_resource_presenter_v2_test.ResourcePresenterV2StaticTests.test_incremental_work_and_cardinality_bounds | F051 | S1 |
| static_resource_presenter_v2_test.ResourcePresenterV2StaticTests.test_no_gameplay_authority_or_persistence_in_new_code | F052 | O1 |
| static_resource_presenter_v2_test.ResourcePresenterV2StaticTests.test_preserved_legacy_artwork_generation_and_runner_bytes | F053 | H2 |
| static_resource_presenter_v2_test.ResourcePresenterV2StaticTests.test_spatial_query_covers_painted_edges_without_policy_mutation | F054 | S1 |
| static_smelter_artwork_test.SmelterArtworkStaticTest.test_gameplay_other_presenters_and_stationary_preserved | F055, F056, F057, F058, F059, F060 | H2 |
| static_smelter_footprint_test.SmelterFootprintStaticTest.test_preview_commit_obstacles_and_dave_use_shared_footprint | F061 | S1 |
| static_smelter_footprint_test.SmelterFootprintStaticTest.test_shared_gameplay_presentation_and_stationary_preserved | F062, F063, F064, F065, F066, F067 | H2 |
| static_smelter_thermal_test.SmelterThermalStaticTest.test_recovery_redeployment_and_gameplay_sources_unchanged | F068, F069, F070, F071, F072, F073 | H2 |
| static_starting_resource_generator_test.StartingResourceStaticTests.test_no_live_integration_or_mutable_generation_inputs | F074 | O1 |
| static_starting_resource_generator_test.StartingResourceStaticTests.test_preserved_gameplay_assets_foundation_and_safety_controls | F075 | H2 |
| static_terrain_stage2_coverage_test.Stage2ClassificationTest.test_source_guards_reviewed_provenance_and_protected_files | F076 | H2 |
| static_terrain_stage3c_test.Stage3CTest.test_exact_scope_and_protected_inputs | F077 | H2 |
| static_terrain_stage3c_test.Stage3CTest.test_inactive_gameplay_plan_inputs_transforms_and_dependencies | F078 | H2 |
| static_terrain_stage3d_test.Stage3DTest.test_only_script_default_changes_and_scene_inherits_it | F079 | H2 |
| static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_accepts_canonical_keep_metadata_without_uid | F080 | G1 |
| static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_has_no_dev_dependency_and_valid_declarations | F081 | G1 |
| static_v2_production_host_test.V2ProductionHostStaticTest.test_resource_graph_rejects_dev_paths_and_unknown_uids | F082, F083, F084 | G1 |

## Appendix 5 — Infrastructure manifest

The CSV contains 503 infrastructure/input rows. They enumerate helpers, tools, fixtures, UID sidecars, configuration, testing documentation, historical evidence metadata and directly referenced current resources. They are excluded from test-case counts. It also contains 29 historical Python methods, 93 PowerShell groups, 683 Python discovery methods, 1,048 GDScript call sites and 84 individual failure records.

The nineteen Python helper/reference modules are:

- tests/application_shell_preservation.py
- tests/baked_terrain_preservation.py
- tests/current_preservation.py
- tests/east_idle_preservation.py
- tests/east_walk_alignment_preservation.py
- tests/extractor_artwork_offline.py
- tests/ground_art_preservation.py
- tests/housekeeping_preservation.py
- tests/illustrated_terrain_preservation.py
- tests/initial_exterior_preservation.py
- tests/native_terrain_preservation.py
- tests/north_idle_preservation.py
- tests/north_walk_size_preservation.py
- tests/smelter_artwork_offline.py
- tests/south_idle_preservation.py
- tests/terrain_integration_preservation.py
- tests/terrain_stage2_reference.py
- tests/terrain_stage2b2_reconstruction_reference.py
- tests/terrain_stage2b_compatibility_reference.py

The thirteen tracked tools are:

- tools/bake-illustrated-terrain.py
- tools/build-ferrite-catalog.ps1
- tools/ferrite-catalog-renderer.cs
- tools/ferrite-catalog.py
- tools/generate-hatch-audio.py
- tools/generate-weathered-earth.py
- tools/ground-art-refinement.py
- tools/ground-refinement-full-atlas.py
- tools/ground-transition-softness.py
- tools/run-local-tests.ps1
- tools/run-save-codec-tests.ps1
- tools/terrain-c1-author.py
- tools/terrain-stage2b2-diagnostics.py

The CSV catalogues testing-related documentation by path. Primary current policy/format documents are AGENTS.md, docs/LOCAL_TESTING.md, docs/SAVE_CODEC_RUNNER.md, docs/SAVE_FILE_FORMAT.md, docs/PUBLICATION_JOURNAL.md, docs/RESOURCE_GENERATION_V2_*.md, docs/APPLICATION_SHELL.md and README.md. Historical status statements such as “pending merge” must be interpreted against local Git history; they are not present execution authorization.
