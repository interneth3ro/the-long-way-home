# Illustrated playable exterior (PR #104 feature branch, pending merge)

The production exterior uses the approved baked Earth/Green artwork through the
shared PR #103 presenter. Static and isolated native validation passed, followed
by the owner's post-reboot playable-game acceptance: **7/7 PASS**, zero failures
and zero untested checklist items. Minor initial exterior-loading stutter is
explicitly accepted as non-blocking. No formal performance benchmark was performed.
See the [final acceptance record](#final-pr-104-acceptance-2026-11-01) for scope
and evidence. PR #95 is the corrected exterior
comparison baseline; the [PR #102/#103 acceptance record](PRODUCTION_TERRAIN_FIXTURE.md)
applies only to its isolated fixture and remains unchanged.

## Selection and rollback

`PlanetExterior.terrain_renderer` defaults to `ILLUSTRATED`. Before the first
`prepare_for_arrival()`, set it to `LEGACY` on the exterior instance, or set the
root's Terrain Renderer Inspector property in
[planet_exterior.tscn](../scenes/world/planet_exterior.tscn) to Legacy before
starting a fresh playthrough. The equivalent serialized property is
`terrain_renderer = 0` under the root node. Remove that explicit property to use
the script's illustrated default again. A graphical launch still requires owner
authorization. Renderer selection is captured once; cached hatch revisits retain
it. Stop and restart the playthrough to compare modes. There is no live hot toggle
or automatic partial fallback.

Legacy does not initialize the lookup/TileSet/presenter, allocate tint data, load
the production shader, resolve illustrated assignments or write illustrated cells.
Its chunk ground polygons and details retain their original drawing commands.
Illustrated mode skips only those polygons and their legacy material-ID sampling;
the same chunk nodes still sample colors and generate/draw decorative details.
Detail removal identities and state revisions are unchanged.

## Live lifecycle and ownership

| Boundary | Action |
| --- | --- |
| `prepare_for_arrival()` | Lock renderer selection once, initialize illustrated resources if selected, reuse authored masks/generator and drain the initial neighborhood with the existing frame yields |
| `_update_neighborhood()` | Keep radius 2 loading/radius 3 retention defaults, retire beyond retention before freeing chunks, replace stale requests after movement and enqueue retained revision mismatches |
| `_generate_budget()` | Configure at most two replacement chunks per call; register/present illustrated terrain before replacing old detail nodes or tint data; flush tint once after the budget |
| `_present_illustrated_chunk()` | Increment the exterior's monotonic token, call `begin_generation`, retain its token by chunk, then call `present_chunk` with the unchanged absolute material sampler, world seed and rule version |
| `_retire_illustrated_chunk()` | Require the current token's successful retirement before dropping its token or clearing its tint slot; then the caller removes the detail chunk |

The unchanged presenter owns exactly 32x32 cells per chunk, samples a 34x34
material halo, validates all assignments before writes, and rejects stale,
duplicate and reentrant operations. Failed preparation leaves old displayed
terrain intact. No presenter scheduler, second queue or per-cell ownership table
is added. Negative coordinates use existing floor geometry and absolute sampling.
128px tiles remain half-scale (64 world units); construction remains 32 units.
The unchanged resolver retains Green/Earth peers and seeded 60/25/15 A/B/C rules.

A failed presentation puts the popped coordinate back at the front of `_pending`
and stops further generation. Initialization/registration/retirement failures also
stop terrain work. `terrain_failure()` returns a copied diagnostic dictionary;
one warning records the first failure. Arrival exits its preparation loop instead
of spinning. There is no automatic retry or silent request loss. Existing visuals
survive a failed replacement; a failed initial region can remain absent and must
be treated as failed acceptance. Correct the input and start a fresh playthrough.
This is bounded failure reporting, not a transition rollback or engine-crash
transaction. Detach/reattach clears neither tokens nor failure/tint state.

## Shared production tint

The existing chunk calculation remains exact: `PlanetGenerator.sample_color()`
applies procedural color, stored override, then authored masks in scene order.
Masks retain their 256-world-unit recovery feather. A 34x34 color halo contributes
four center samples to each of the 33x33 vertices; `_earth_tint()` is unchanged.
`TerrainChunk.write_tint()` copies these calculated values without resampling.

The exterior owns one RGBA-float Image, ImageTexture and ShaderMaterial. Each
chunk has a 33x33 slot at `posmod(chunk, diameter) * 33`, with diameter
`2 * (loading_radius + retention_margin) + 1`. The default is a fixed 231x231
texture (853,776 bytes of RGBA-float data). All retained chunk slots are distinct;
outgoing chunks retire before an incoming chunk can reuse their slot. Retirement
clears exactly that slot. Configure radii/budgets before initialization; changing
them during a playthrough is unsupported, like changing the renderer.

Only successful generations write tint. Each successful write also copies shared
border vertices into the up to eight already retained neighbor slots, keeping
edges/corners continuous while adjacent revision replacements await their budget.
It changes no neighbor assignments or detail state. Clearing a retired slot does
not clear neighbor borders. There is no full-field CPU resampling or per-cell
material. Dirty changes upload the fixed texture once per budget call, including
retirement-only changes; idle calls upload nothing. This is bounded shared upload
work, not a measured optimization. Owner-observed appearance and responsiveness
acceptance is recorded below; GPU upload and fragment sampling costs have not
been formally measured.

The [production shader](../scenes/world/illustrated_terrain_tint.gdshader) adapts
the accepted fixture's numerical tint field. MODEL_MATRIX yields world positions;
inverse exterior-transform columns convert them back to exterior space. These
uniforms refresh on arrival/reattachment. Fragment sampling selects the chunk's
own slot and linearly interpolates its vertices, including beside unloaded
neighbors. GLSL modulo matches CPU positive modulo at negative coordinates. The
sampler uses linear filtering without repeat or source-color conversion. The
fragment interpolation may differ from the fixture/legacy triangle interpolation;
visual equivalence, not pixel equality, is the acceptance target. Godot's
[CanvasItem coordinate API](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/canvas_item_shader.html)
defines the local-to-world MODEL_MATRIX contract. Normal near-origin Godot float
precision limits remain; no unlimited-coordinate claim is made.

The shared ground is Z -11, chunk details Z -10, Ferrite artwork Z -5,
construction highlights Z -4, and authored GroundObjects/Dave remain above these.
Only ground is shaded. Deposits, collisions, protected exclusions, construction,
machine simulation, player spawn and arrival/hatch code remain unchanged. Actual
visual order beyond the seven accepted checklist items is not separately certified
by the owner's gameplay acceptance below.

## Static gate and exact preservation amendments

The focused [activation checks](../tests/static_illustrated_exterior_test.py)
inspect actual source order/guards and immutable gameplay, generator, presenter,
resolver, scene and transition bytes. Independent finite models cover initial 25
chunks, two-request budgets, retained revisions, movement/reload, modulo slot
uniqueness/reuse, negative UVs, halo vertex continuity, shared revision borders
and bounded failed requests. These are Python/text checks, not GDScript execution.

Historical guards still protect their original baselines. The new exact
[activation projection](../tests/exterior_activation_preservation.py) verifies
four complete candidate inputs: exterior script, exterior scene, chunk script and
new production shader. Only verified pre-existing candidates project to immutable
PR #103 merge `63318e464898b8ecf4596216f9577cd64e72dbcc`; the new shader has no
historical representation. Existing PR #103/#102 pins remain unchanged.

| Amended file in `tests/` | Protected purpose and precise activation conflict | Narrow amendment |
| --- | --- | --- |
| `production_terrain_preservation.py` | Exact #103 wiring/changed-path pins reject production activation and ground gate | Verify #104 exact candidates before the unchanged #103 projection; exclude only exact verified activation paths from historical changed sets |
| `static_weathered_earth_test.py` | Exact green chunk pin rejects the ground-only gate/tint copy | Verify/project only that exact current chunk before the unchanged original-green hash and historical comparison |
| `static_low_green_ground_test.py` | Structural rollback comparison expects ungated drawing/configuration | Compare verified historical chunk for that historical assertion; live ground/tint/detail equality is covered by the activation suite |
| `static_illustrated_terrain_presenter_test.py` | Dormant #103 gate and unchanged chunk/helper assertions conflict with activation | Test verified #103 representation for those historical checks, remove chunk from the unrelated-input list, and pin the precise updated helper; presenter and fixture behavior remain checked live |
| `static_native_terrain_47_test.py` | Historical staged/committed path guard rejects chunk/shader production inputs | Accept only the four exact activation inputs before original unrelated-path protections |

The four amended historical test candidates and both preservation helpers are
also pinned. Appended, truncated, duplicated and alternate-path tamper cases are
rejected. Unlisted owner resources, artwork, generator/gameplay, runner, policy,
stage manifests and historical fixture evidence receive no exemption. This is a
static preservation amendment only, with no new engine command or input authority.

On 2026-11-01, the final staged implementation passed **177/177 static tests in
107.279 seconds** (107.918 seconds including the external controller). The focused
activation suite separately passed **14/14 in 2.821 seconds**. An earlier full
run exposed one double-projection compatibility failure in an older preservation
caller; the exact historical-byte handling and negative cases were corrected.
Final inspection also restored the idle queue early return to avoid rebuilding
highlights each frame; the final full PASS includes its regression check.
Changed Markdown targets and `git diff --cached --check` passed. All 34 initial
untracked owner files retain their captured SHA-256 hashes; PR #99's preservation
branch remains at `326591e1a1438944d79b0be4c52992b3eb86af0f`. Routine success logs
were not saved. Native, graphical, gameplay and performance checks were not run.

The suite runs as `python -B -m unittest discover -s tests -p 'static_*test.py'`
under the established separate 180-second external subprocess limit; the local
runner's 60-second limit is unchanged. `-B` prevents bytecode writes. Inspected
tests perform read-only Git/file checks and in-memory arithmetic/PNG generation;
the PNG tool's file-writing main entry point is not invoked. No native, graphical,
performance, runner Native/NativePlan, supervisor or staging operation is part of
this implementation.

## Separately authorized validation proposal

This section preserves the pre-execution proposal. Completed validation and owner
acceptance are recorded below; the proposal grants no further execution authority.

No phase below is authorized by this document. Before any launch, review the
final candidate and a concrete, sealed fresh-stage inventory and focused native
harness. Reuse the established PR #103 external procedure and its stable handling
of temporary Codex bookkeeping, preserving meaningful refs and owner files. Do
not alter or reuse its existing packages/stages/evidence. Ordinary Windows
filesystem permissions retain the residual risk acknowledged in Decision 16;
no new sandbox or supervisor architecture is proposed.

The old 54-input fixture package cannot instantiate the production exterior.
Read-only resource/global-class closure inspection finds these **17 additional
existing/new paths** relative to that package, before a new assertion harness:

- `assets/dialogue/portraits/computer_dialogue_portrait.png`
- `assets/dialogue/portraits/dave_dialogue_portrait.png`
- `assets/dialogue/portraits/marvin_dialogue_portrait.png`
- `construction/deployed_machine.gd`
- `construction/machine_visual.gd`
- `dialogue/dialogue_conversation.gd`
- `dialogue/dialogue_entry.gd`
- `scenes/interaction/ferrite_inspection.gd`
- `scenes/interaction/scene_hatch.gd`
- `scenes/interaction/world_interactable.gd`
- `scenes/main/scene_transition_controller.gd`
- `scenes/player/interaction_detector.gd`
- `scenes/ui/dialogue_ui.gd`
- `scenes/ui/interaction_ui.gd`
- `scenes/world/illustrated_terrain_tint.gdshader`
- `scenes/world/planet_exterior.gd`
- `scenes/world/planet_exterior.tscn`

These include parse-time global-class dependencies even where nodes are not
instantiated. Existing fixture inputs that overlap production must use the final
reviewed feature commit's bytes, not old #103 hashes. This list is a proposal,
not an amended execution manifest. Review generated import/UID destinations and
the minimal new production assertion harness before granting authority. Full
playable Main/V2 transitions need a separately enumerated larger gameplay package;
the isolated exterior dependency list does not authorize that package.

Use the pinned standard Godot 4.7.2 executable and hash in
[AGENTS.md](../AGENTS.md#godot-execution-safety), one process at a time:

1. Cold import/parse in a fresh isolated package: 60 seconds, no gameplay startup.
2. Only after clean import PASS, focused assertions: 30 seconds. Check actual
   production initial loading, direct replacement/retirement/stale requests,
   failed-request preservation/stop, negative coordinates, revision tint borders,
   slot reuse, cached reattachment, and legacy's empty illustrated resources.
   Require one exact completion line and exit zero. Review the new harness first;
   the old fixture harness does not establish these production assertions.
3. Separately authorized owner-controlled graphical/playable acceptance: at most
   120 seconds per approved comparison session, closed sooner by the owner.
   Observe startup and a short normal streaming path; no artificial pauses,
   benchmark, profiler, prolonged test or freeze reproduction. Further gameplay
   observations or a second renderer session require their own bounded approval.

Retain the existing 1,048,576-byte combined output cap and 4,096-byte diagnostic
excerpts. Rehash executable/inputs, capture revision/index/status/refs and protected
owner-file identities, reject links/unexpected outputs/changed identities, and
stop on parse/shader/script errors, failed assertions, abnormal exits, timeouts,
overflow, malformed completion or uncertain termination. No automatic retries.
No source-checkout Godot launch. Preserve bounded failure evidence and all owner
files/stages. A static or native PASS never expands authority.

Owner observations must separately cover Earth/Green transitions/corners/pockets
and seams; negative streaming/unload/reload; crash masks, feather and overrides;
details/removal; Ferrite/highlights; construction grid/collisions; Dave/props draw
order; arrival/hatch/controls; deterministic regeneration/revisions; explicit
legacy fallback; and qualitative responsiveness against corrected PR #95.
Record actual PASS/FAIL/untested observations; process completion cannot supply
graphical acceptance. No merge, cleanup or historical-evidence changes are included.

## Focused native preparation (2026-11-01; execution unauthorized)

Historical preparation status: execution was unauthorized at preparation time.
The separately authorized phases subsequently passed as recorded in the final
acceptance section below. Existing package records and manifests remain unchanged.

The implementation baseline is `061b9e24bd1a322a9acf0e45d07b5cb9b6450c31`.
This follow-up changes only the proposed validation harness, input inventory,
focused static contract and this guide, on the same PR #104 branch. Production
scripts/scenes, PR #103 presenter, gameplay, budgets and rollback are unchanged.

The exact [proposed manifest](experiments/illustrated_exterior_stage.json) lists
**83 committed input paths with byte counts and SHA-256 hashes**, plus one generated
minimal `project.godot` (84 initial files). `source_commit = seal.review_head`
means the concrete review package seals the final feature commit containing both
the manifest and harness; every staged source input must match its Git blob there.
It does not permit working-tree substitutions. This resolves the earlier 17-path
dependency finding with the required existing import/UID metadata and harness;
it omits the old fixture scripts/scenes and includes only the exterior scene.
There is no Main scene, autoload, player-controller scene, main-scene setting or
playable input-map package. Stored hatch destination strings are not followed or
executed by this test. No unresolved static dependency was found.

The [Phase 2 harness](../tests/illustrated_exterior_native_validation.gd) uses the
real exterior's arrival hook once, requires 25 chunks/25,600 cells, and checks
ground-only suppression with retained detail data/nodes; deterministic token
replacement, stale rejection, exact negative retirement/reload; shared tint and
shader binding; a stored override outside crash-mask coverage and shared revision
borders; cached reattachment; one invalid test-only material sampler preserving
old data and stopping work; and one direct legacy chunk without illustrated work.
Exterior automatic processing is disabled in the harness; explicit calls use the
existing production budget. No movement automation, full-game startup, prolonged
simulation or benchmark is included. Native checks establish structural binding,
not actual shader GPU compilation, visible details or gameplay correctness.

The review package is retained at
`artifacts/evidence/pr104-native-review-28f57c4c-677f-4f9e-8809-7be9fc66f2d6/`.
It reuses the PR #103 v2 Stage/Import/Assertions supervisor with the final v4
reference-policy block. Fixed paths, commit/proposal identities, counts and the
assertion command/completion marker are rebound. Job Object suspended-start
assignment, watchdog, pipe limits, termination accounting, no-retry state and
protected-reference rules remain exact. Historical PR #103 packages/stage are
hash-bound in the package's prior-evidence record; original evidence is untouched.
The package is preparation material, not a native stage. Its source snapshot
protects tracked, untracked and ignored owner files, index, branch, worktrees and
meaningful refs, using the accepted narrow temporary Codex-tree reference policy.
Decision 16's residual ordinary Windows filesystem-permission risk is unchanged.

Reserved stage, **not created**:
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-pr104-review-28f57c4c-677f-4f9e-8809-7be9fc66f2d6`.
Only after owner authorization may Stage copy the exact 83 committed blobs and
generate the sealed configuration there. Import then uses the pinned executable:

```text
--headless --editor --path <reserved-stage> --quit
```

After clean Import PASS and separate owner authorization, Assertions uses:

```text
--headless --path <reserved-stage> --script res://tests/illustrated_exterior_native_validation.gd
```

Timeouts remain 60s/30s, combined output 1,048,576 bytes, diagnostic excerpt
4,096 bytes, one process at a time and no retries. The manifest allows **41 exact
generated paths** during import (specific cache/import/UID outputs), with all
original inputs immutable. Actual allowed outputs are captured after clean import
and must remain identical during assertions. Require exit zero, no engine errors,
certain process-tree termination and exactly one final stdout completion line
`Illustrated exterior validation failures: 0`. Stop on any error, changed identity,
unexpected output, timeout, overflow, malformed completion or uncertain termination.
The preparation assignment grants neither stage creation nor either native phase.

### Eventual owner manual playtest

After separately approved native gates and a separately authorized playable launch:

1. Start a fresh normal playthrough; enter the exterior and inspect illustrated
   ground, crash-site Earth treatment and the recovery feather.
2. Walk across Earth/Green transitions and seams, far enough to load chunks;
   return through previously visited ground and note missing/doubled ground or stalls.
3. Inspect decorative details, Ferrite artwork/highlights, construction grid,
   machine placement/collisions and Dave/prop draw order.
4. Enter and exit the ship; verify arrival, controls and retained terrain.
5. Compare responsiveness qualitatively with corrected PR #95; stop on abnormal
   responsiveness. No profiler, benchmark or freeze reproduction.

For a separately authorized legacy comparison, stop the game, set the exterior
root's Terrain Renderer to Legacy (`terrain_renderer = 0`) before starting another
fresh playthrough, then repeat the short route. Remove that explicit property to
restore illustrated default. Do not change the running instance. Record actual
PASS/FAIL/untested observations; this checklist does not authorize a launch.

## Final PR #104 acceptance (2026-11-01)

The owner completed a successful post-reboot playtest of the actual playable
game on `codex/104-illustrated-exterior-activation` at validation-preparation HEAD
`4a364481e5eba90bba0d88b2518a8fce004dc979`. Production implementation remains
unchanged from `061b9e24bd1a322a9acf0e45d07b5cb9b6450c31`; the later acceptance
commit changes documentation only. PR #104 remains draft and pending owner merge
authorization.

| # | Acceptance check | Result |
| --- | --- | --- |
| 1 | Ship interior responsiveness | PASS |
| 2 | Illustrated exterior loading | PASS |
| 3 | Terrain appearance and shading | PASS |
| 4 | Chunk streaming | PASS |
| 5 | Ferrite interaction | PASS |
| 6 | Return to ship | PASS |
| 7 | Windows responsiveness | PASS |

Overall: **7/7 PASS, zero failures, zero untested items** in this owner checklist.
The owner reports minor stuttering when the exterior initially loads and explicitly
accepts it as a known, non-blocking performance limitation. This does not claim
that all stuttering has been eliminated. These are qualitative owner observations;
no formal performance benchmarking was performed. The earlier broader proposed
checklist is not an additional set of certified results.

### Existing validation and preservation evidence

The retained local evidence package is
`artifacts/evidence/pr104-native-review-28f57c4c-677f-4f9e-8809-7be9fc66f2d6/`.
The following references are existing files within that ignored package, not
newly generated test results or published repository artifacts:

| Evidence | Recorded result |
| --- | --- |
| `verification.json` | Full static suite **178/178 PASS** (108.612 seconds); focused activation checks **15/15 PASS** (3.051 seconds) at `4a36448` |
| `execution-Stage.json`, `execution-state.json` | Stage PASS; Stage/Import/Assertions all PASS, not blocked, no running phase |
| `execution-Import.json` | Phase 1 cold headless import PASS, exit 0, termination certain |
| `execution-Assertions.json` | Phase 2 native assertions PASS, exit 0, termination certain; exact completion marker `Illustrated exterior validation failures: 0` |
| `manifest.json`, `generated-Import.json`, `generated-Assertions.json` | Stage input/output integrity PASS; original staged input hashes retained and import/assertion output inventories identical |
| `seal.json`, `source-baseline.json`, `prior-evidence.json` | Preserved package identities and source/owner/historical-evidence safeguards; successful native classifications include preservation checks |
| Owner report in this acceptance assignment | Post-reboot manual playable-game acceptance **7/7 PASS** as listed above |

The exact [committed-input manifest](experiments/illustrated_exterior_stage.json)
and [native harness](../tests/illustrated_exterior_native_validation.gd) remain
unchanged. The seal SHA-256 remains
`55c05b996cfafe30ecf60db3e866e599ed00e8916d372fd9462e91b3409be7e4`.
The stage remains at
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-pr104-review-28f57c4c-677f-4f9e-8809-7be9fc66f2d6`.
Stage inputs/outputs and sealed review files were checked by read-only hash and
inventory comparison for this documentation update. Historical records were not
modified. The preparation-time `verification.json` correctly retains its original
`engine_executed: false` and `stage_created: false`; subsequent execution records
provide the native results. The native negative case deliberately emits the
material-validation warning visible in the assertion record; its final failure
count is zero.

Automated native assertions establish their isolated structural/lifecycle checks;
the seven manual results establish owner-observed gameplay acceptance. Neither
establishes formal frame-time measurements or comprehensive performance testing.
Production code, artwork, TileSets, budgets, test guards and stage packages are
unchanged. Owner material and the PR #99 preservation branch at
`326591e1a1438944d79b0be4c52992b3eb86af0f` are preserved. No Godot launch or native
rerun was performed for this documentation update.

No acceptance blocker remains in the agreed seven-item checklist. PR #104 is ready
for owner merge consideration with the accepted initial-loading stutter. It stays
draft; merge, further execution and cleanup require separate owner authorization.
