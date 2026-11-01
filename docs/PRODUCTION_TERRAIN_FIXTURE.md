# Production-scale illustrated terrain fixture (PR #102 merged)

Owner graphical acceptance is **10/10 PASS**, with **no observations**, for exact
implementation commit `07337fdfeb5bdd28200d297ea36951b054dd04a0`.
The isolated cold Import and Native Assertions also passed, as recorded below;
these engine results are separate from the owner's graphical acceptance.

Open [fixture.tscn](../scenes/experiments/production_terrain/fixture.tscn) for text
inspection. Any further engine launch requires fresh owner authorization. The
historical inspection workflow uses **F6 / Run Current Scene** in the approved
stage; F5 still starts production V2. No exterior, production scene, generator,
renderer, mask, construction definition, resolver, artwork or terrain metadata
is changed. This acceptance update changes documentation only.

## Presentation and bounded chunks

One shared TileMapLayer uses the original 128px baked TileSet at uniform **0.5**
scale, at identity position: origins are `cell * 64`, centers `(cell + 0.5) * 64`.
Two 32-unit construction intervals fit along each terrain-cell axis (four
construction cells by area). Negative positions retain WorldCoordinates' floor
convention. Orange dots mark origins, white dots mark centers; the optional small
32-unit grid surrounds the origin. View buttons control only the fixture camera.

Four logical 32x32 chunks occupy `(-1,-1), (0,-1), (-1,0), (0,0)`: at most
4096 cells across a 4096-unit square. The coordinate-only material field contains
broad Earth/Green interiors, horizontal/vertical boundaries, a pocket, islands,
stair-step contours and narrow seam-crossing bridges. Its ordered rectangles and
irregular predicate are fixture data, independent of production generation. Each
generation samples its own 34x34 halo, then calls the actual PR #101 resolver
and initialized native assignment lookup. Direct `set_cell` uses returned source,
atlas and alternative IDs; there is no second mapping or Connect painting.

Choose a chunk, **Load / replace**, or **Unload**. Replacement builds all
assignments first, checks an existing snapshot for equality, erases exactly the
retired chunk's owned cells, then inserts its replacement. Forward/reverse
buttons retire all four and regenerate in that order. No neighbors need be
loaded. Status lists loaded coordinates and the logical assignment count, not an
independent GPU cell-count measurement. There are no timers, streaming,
background generation, production state mutations or persistent settings.

Presentation seed 19 and an explicit resolver rule version retain A/B/C bucket
weights 60/25/15 for solid interiors. Independent color-sample seed 19 constructs
a fixture-local PlanetGenerator. Future integration can supply stored/derived
presentation seed and rule version alongside a future world sampler. No world
seed selection, save format, serialization or migration is implemented here.

## Shared experimental shading

The picker selects **Unshaded**, **CPU tint**, or **Crash-style tint + override**.
Classification and assignments are identical in all modes. The sequence is:

1. Unchanged `PlanetGenerator.sample_color()` procedural ground color.
2. Its unchanged `PlanetWorldState.terrain_color()` override lookup.
3. Its ordered overlay loop. Crash mode supplies synthetic feathered polygons,
   outer recovery then dark core, plus an override at cell `(-12,0)`.
   These are illustrative data, not the authored crash-site masks.
4. CPU average of the four center samples around each absolute terrain vertex.
5. Unchanged static `TerrainChunk._earth_tint()` calculation.
6. One 65x65 RGBA float numerical tint texture on one shared ShaderMaterial.

Reuse loads existing RefCounted classes and resource/type dependencies (see the
proposed inventory), but instantiates no production scene, TerrainChunk node,
gameplay system or autoload. State belongs exclusively to this fixture. Calling
the existing underscore helper is limited experimental coupling, with no
production API change or duplicate formula.

66x66 color samples cover all 65x65 vertices, including border contributors.
Chunk edges address the same absolute vertex/texel. Shader vertices use
`MODEL_MATRIX` for world coordinates; tint UV is
`((world - field_origin) / 64 + 0.5) / 65`, origin `(-2048,-2048)`.
The [CanvasItem shader API](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/canvas_item_shader.html)
defines this local-to-world transform. A linear nonrepeating numerical sampler
reads level zero in the vertex stage; an interpolated varying modulates artwork
in the fragment stage. It changes neither vertices nor atlas coordinates.
No `source_color` conversion applies to tint. RGBA float data avoids 8-bit tint
quantization. The owner accepted the shaded modes on the reviewed host;
compatibility across other hardware/renderers remains untested.

The field uploads once per change to a shaded mode. Unshaded switching and chunk
operations upload nothing. There are no per-cell materials or second ground pass.
Debug rectangles are unfilled; the grid contains lines/dots. Terrain renders
behind the parent's debug drawing. No internal TileMapLayer updates are forced.

This evaluates vertex sampling first. The owner accepted the fixture's shading,
transitions and seams on the reviewed host. Visually equivalent shading is the aim;
exact interpolation/pixel parity is **not proven**. Use detail views for narrow
features hidden by overview downsampling. UI is a small desktop fixture panel.
Shared rendering proves no speed improvement. The owner's short fixture
responsiveness check passed. Actual production exterior integration, real
chunk-streaming performance and save/load behavior remain untested; no numeric
performance improvement or prolonged host-stability result is claimed.

## Gate 1: static verification

Permitted command, without Godot or project-code execution:

```powershell
pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Static
python -B -m unittest discover -s tests -p 'static_*test.py'
```

Implementation verification on 2026-10-31: the complete Python suite passed
**150 tests in 92.575 seconds**, including 11 fixture tests. The existing wrapper
stopped at its fixed 60-second static timeout; the direct command above completed
the same suite. Runner limits/policy were not changed. Markdown links and staged
diff whitespace passed. Production/artwork/control diffs are empty against
`74f4ecb3f5a831bbeed4436ec2324441c60b8c77`; all 34 existing untracked artwork/
sidecar files retained their captured SHA-256 hashes. The PR #99 preservation
branch remains `326591e1a1438944d79b0be4c52992b3eb86af0f`. That initial Gate 1
verification invoked no engine.

[Focused Python tests](../tests/static_production_terrain_test.py) use source-bound
models, the existing resolver oracle and resource text. They cover the halo,
24 chunk orders, replacement/retirement/regeneration, all adjacent boundaries,
variants, signed coordinates, texel mapping, shared tint contributors, shading
order, upload bounds, references and preservation. These are not engine tests.
Historical guards admit only four exact new paths with normalized-content hashes,
rejecting tampering/path expansion. Existing artwork pins and Native controls stay.

## Gate 2: completed isolated validation

All three phases used the existing isolated stage for implementation commit
`07337fdfeb5bdd28200d297ea36951b054dd04a0`, the pinned standard Godot 4.7.2
executable, and the separately reviewed external `review-v2` supervisor. Its seal
SHA-256 is `45a375965f2c8e087d48b6a65cf36a423c52d5dff221cdb9403eddab164b1ef0`.
Each phase had separate one-attempt owner authorization. No Editor phase,
production launch, profiling or benchmark was performed.

| Phase | Supervisor / Godot exit | Result | Supervisor wall time | Combined output |
| --- | --- | --- | --- | --- |
| Cold headless Import | 0 / 0 | PASS; termination confirmed, no reported error diagnostics | 5.6873142 seconds | 4,896 bytes |
| Native Assertions | 0 / 0 | PASS; zero failures, exactly one final success marker, termination confirmed | 2.7619124 seconds | 115 bytes |
| Owner-controlled Graphical process | 0 / 0 | PROCESS_OK_OWNER_REVIEW_PENDING; termination confirmed, no reported error diagnostics | 30.2612761 seconds | 172 bytes |

Times include supervisor preservation gates; engine-only duration was not
separately recorded. Diagnostics were retained within the reviewed 4 KiB bound.
The Assertions harness executed the real lookup/resolver and TileMapLayer checks,
including order-independent regeneration, replacement, retirement/reload, native
cell assignments, centers/floor mapping and both tint-field modes. Its final
success marker was exactly `Production terrain fixture failures: 0`.

The Graphical process result did not infer acceptance. The owner subsequently
reported the separate **10/10 graphical PASS** below, with no observations.
The process record's original pending-review classification is retained unchanged.

Evidence is preserved outside the checkout under:

`D:\GameDev\Godot\TLWH-NativeStages\tlwh-pr102-prepared-8e9b3e23-9c43-4f9b-8f35-dbb6e25a29a7\review-v2\`

It includes `execution-Import.json`, `execution-Assertions.json`,
`execution-Graphical.json`, the three matching `generated-*.json` inventories,
and `import-postcheck.json`, `assertions-postcheck.json`,
`graphical-postcheck.json`. Import generated 35 permitted files: 23 `.godot/`
cache files, seven import sidecars and five UID sidecars. Assertions and Graphical
added, removed or changed none of those files. Post-execution checks passed for
all 393 captured source files, 54 original staged inputs, protected references,
sealed controls, executable hash and prior evidence. No generated material was
copied back or cleaned up.

The initial supervisor's earlier preflight reference mismatch launched no Godot;
its evidence and original baseline remain preserved. The separately reviewed
correction permits only validated capture/checkpoint rotation targeting the
retained approved tree. It did not refresh the original source baseline or alter
the 54 staged inputs. The 53-file proposed raw-working inventory remains preserved;
the external manifests explicitly reconcile its 38 CRLF/LF differences against
exact committed staging bytes.

This documentation-only acceptance commit does not change the graphically
accepted implementation. It does change checkout identity; the retained external
baseline remains pinned to the tested implementation and is not refreshed.
All phase authorizations are consumed. Further engine execution requires fresh
owner authorization and reviewed identity checks.

### Retained Gate 2 plan and execution restrictions

Do not run Godot, Native, NativePlan, imports, graphics, profiling, benchmarks or
automation under this documentation-only update. The standing recipe-switching exception covers
neither these commands nor this inventory. This plan grants no permission and
does not change [LOCAL_TESTING.md](LOCAL_TESTING.md).

Before owner authorization, review these exact commands and the
[explicit input inventory](experiments/production_terrain_stage.json), including
raw byte hashes. The plan below is retained as historical context for the
completed isolated runs; it is not an instruction to repeat them. The reviewed
supervisor exists only in the external evidence package; no runner is installed
in the project. Dependencies exist because real tint
functions reference production state/types. No production scene/main startup is
included. No untracked sidecars, caches, ignored files, secrets, saves, owner
settings or evidence are inputs.
The inventory snapshots this Windows checkout's raw bytes; changed line endings
also require reconciliation/review before execution, never silent normalization
of owner inputs.

Use only `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`, SHA-256
`AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.
Capture branch/commit, full status, index digest and input hashes before Gate 1;
require actual static PASS. Recheck identities throughout. Create a fresh unique
plain `<stage>` under `D:\GameDev\Godot\TLWH-NativeStages`, outside source;
never reuse a stage. Copy only inventoried bytes, retaining paths/UIDs/sidecars.
Generate only this stage-local UTF-8/LF `project.godot`, with final newline:

```ini
config_version=5

[application]
config/name="TLWH PR102 isolated validation"
config/features=PackedStringArray("4.7", "GL Compatibility")

[display]
window/size/viewport_width=1280
window/size/viewport_height=720

[editor]
import/use_multiple_threads=false

[rendering]
renderer/rendering_method="gl_compatibility"
renderer/rendering_method.mobile="gl_compatibility"
```

The stage has no main scene, input map, autoload or saves. Verify exact initial
inventory/config bytes; reject links/reparse points. Generated `.godot/`, new
import sidecars and script/shader UIDs may appear only inside this stage after
import; record them, never copy them to source, and require original staged
inputs unchanged. Preserve stages on success/failure. This proposed allowance
is separate from standing Native policy.

Commands use the stage as working directory. Rehash the executable before each
launch, one process at a time, stopping on any failure; no retries.

| Phase | Exact executable arguments | Wall limit | Combined stdout/stderr bound |
| --- | --- | --- | --- |
| Cold import/classes | `["--headless","--editor","--path","<stage>","--quit"]` | 60 seconds | 1,048,576 bytes |
| Native assertions | `["--headless","--path","<stage>","--script","res://scenes/experiments/production_terrain/engine_validation.gd"]` | 30 seconds | same |
| Owner graphical fixture | `["--path","<stage>","res://scenes/experiments/production_terrain/fixture.tscn"]` | 120 seconds, close sooner after checks | same |
| Optional owner editor check, separately included in authorization | `["--editor","--path","<stage>","res://scenes/experiments/production_terrain/fixture.tscn"]` | 60 seconds | same |

Each phase requires prior required phases to pass. Import needs no engine/script/
parse errors and exit zero. Assertions need exit zero and exactly one final
nonempty stdout line `Production terrain fixture failures: 0`. The script executes
lookup/resolver, compares forward/reverse/replacement/reload assignments, checks
erased/inserted cells and coordinate centers/floor conversion, and creates both
shaded fields. Headless success alone proves no visible shader compilation or
shading. The graphical phase must inspect output/debugger for shader errors and
complete the checklist below. Editor responsiveness is short owner observation,
not a benchmark. None of these phases runs production exterior.

Stop on engine/script/parse/shader errors even with exit zero, assertions,
missing/malformed/duplicate completion, abnormal exit/crash, timeout, overflow,
changed source/index/stage/executable identity or uncertain termination. Retain
at most 4096 diagnostic bytes per phase; preserve useful bounded failure evidence
under ignored `artifacts/logs/` without overwrites. Timeout/overflow needs bounded
process-tree termination and owner direction before any subsequent launch. Never
retry automatically. Preserve source, stages and owner files. A supervisor must
enforce bounds, read both pipes and verify termination; raw commands do not supply
those safeguards.

Risks include PR #101 parsing/API errors, shader/float texture compatibility,
TileMap batching/transform assumptions, an unresponsive editor/game and host
instability. Bounds cannot guarantee recovery from a system freeze. No stress
test, performance probe, benchmark, freeze reproduction or unattended run is proposed.

## Owner graphical acceptance

**Owner-reported result: 10/10 PASS. Owner observations: None.**
Exact graphically accepted implementation:
`07337fdfeb5bdd28200d297ea36951b054dd04a0`.

1. [x] Terrain appearance.
2. [x] Transitions.
3. [x] Cell alignment.
4. [x] Chunk loading.
5. [x] Chunk lifecycle.
6. [x] CPU shading.
7. [x] Crash-style shading.
8. [x] Unshaded comparison.
9. [x] Seams and tint.
10. [x] Responsiveness.

This accepts the bounded isolated fixture. Actual production exterior integration,
real chunk-streaming performance and save/load behavior remain untested. No
pixel-perfect legacy shading parity or numeric performance improvement is claimed.
Production integration and cleanup were outside PR #102. PR #102 subsequently
merged at `4c5bccc1877472a3551df756b673ef5e059dccf6`; the historical execution
authorizations above remain consumed.


## PR #103 presenter extension (feature branch, pending merge)

The default **PR #102 reference** backend retains its original material field,
seeds, resolution, load/unload/reload methods, camera views and shading formulas.
The opt-in **PR #103 presenter** backend exercises the shared presenter in this
same bounded fixture. Switching retires the previous backend before populating
the selected one; no competing ground passes remain. Both layers use the existing
single ShaderMaterial, 0.5 scale and tint field. The presenter itself owns no tint
logic. The accepted #102 engine and graphical results above apply only to the
historical implementation, not to this extension.

The extended native harness passed the separately authorized PR #103 assertions.
It checks reference/presenter assignment
parity, single/adjacent regions, negative ownership, neighbor preservation,
in-place replacement, reversed order, regeneration, stale/duplicate requests,
retirement/reload, reentrancy, invalid material/version/assignment rejection,
failure preservation and restoration of reference mode. Malformed assignments
use a private preparation override in the harness, not a production injection API.
It remains bounded to the existing four-chunk field; the malformed test runs only
after retiring presenter cells. No timers or streaming loop are added.

### Final PR #103 acceptance (2026-11-01)

**Owner-confirmed result: 12/12 PASS, zero failures, zero untested items.
Owner observations: None.** This accepts the shared terrain presenter in isolation,
pending owner merge of PR #103.

Validated implementation and native/graphical review HEAD:
`aa62a6d38c981e08c7c6d70cf5929cad642a5414`, branch
`codex/103-illustrated-terrain-presenter`. All 54 committed staged inputs match
that implementation and pinned input-source commit
`123b29b0cef3386f476117b7952d5ad91d6b0f98`. The acceptance documentation commit
changes no implementation or validation controls.

| # | Graphical check | Owner result |
| --- | --- | --- |
| 1 | PR #102 reference startup | PASS |
| 2 | PR #103 presenter visual equivalence | PASS |
| 3 | No overlapping or double-rendered ground | PASS |
| 4 | Earth/Green boundaries and negative-coordinate seams | PASS |
| 5 | Chunk loading, replacement and retirement | PASS |
| 6 | Reverse loading and deterministic regeneration | PASS |
| 7 | Unshaded terrain | PASS |
| 8 | CPU tint shading | PASS |
| 9 | Crash-style shading and terrain-color override | PASS |
| 10 | Restoration of PR #102 reference appearance | PASS |
| 11 | Camera views | PASS |
| 12 | Fixture responsiveness | PASS |

Completed validation gates, recorded from the existing execution evidence:

- **Static:** 163 full static tests PASS, including 13 focused presenter tests
  (the startup follow-up below records commands and timings).
- **Native Phase 1:** cold headless import PASS; Godot exit 0, supervisor exit 0;
  all 55 initial inputs and 36 generated outputs verified.
- **Native Phase 2:** assertions PASS; Godot exit 0, supervisor exit 0; exactly
  one final nonempty completion line `Production terrain fixture failures: 0`.
- **Graphical:** Godot exit 0, supervisor exit 0; supervised invocation duration
  58.18 seconds, with confirmed process-tree termination. Output contained only
  engine/renderer identification; no reported engine errors or warnings.
  The process result was `PROCESS_OK_OWNER_REVIEW_PENDING`; the subsequent
  owner report above independently completes graphical acceptance.
- **Preservation:** 4,370 source/owner files verified; historical PR #102 evidence,
  protected Git references, index and worktree registrations unchanged through
  execution. All 55 staged inputs and 36 frozen generated outputs remained
  unchanged. Acceptance recording does not refresh any preservation baseline.

Existing local evidence remains at these locations (not committed to Git):

- Native v2 package:
  `D:\GameDev\Godot\TLWH-NativeStages\pr103-supervisor-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b-v2`.
  `execution-Import.json`, `execution-Assertions.json`,
  `phase1-v2-import-controller.json`, `phase2-v2-assertions-controller.json`,
  their preflight/postcheck records, and `generated-Import.json` retain results.
  Seal SHA-256:
  `167edb6f3f3387b28da8dc4ded734e392cca758d64eee3d3e9065e466e9a7ca4`.
- Final graphical v4 package:
  `D:\GameDev\Godot\TLWH-NativeStages\pr103-supervisor-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b-v4-final`.
  `execution-Graphical.json`, `graphical-run-envelope.json`,
  `generated-Graphical.json` and `execution-state.json` retain the process result,
  duration and output integrity. Seal SHA-256:
  `9376b38f021ddd38769d4a71435a86a0c5b6a2fc5184ae40e7554475413ed34c`.
- Existing imported/assertion-tested stage:
  `D:\GameDev\Godot\TLWH-NativeStages\tlwh-pr103-review-28d3f7d6-9d1b-413e-a68a-390d05296c4b`.
  The [54-input inventory and generated configuration](experiments/illustrated_terrain_presenter_stage.json)
  remain unchanged. Native and graphical packages retain the original
  `source-baseline.json`, SHA-256
  `973320ab24d74fcd7daa022d3b4214fb05d9ab475829b458f5074886ea99ffac`.

Earlier proposal and static-only statements below record their status at that
time; the completed gates above supersede their pending-execution status.
All one-run authorizations are consumed. This record grants no further launch,
merge or cleanup authorization. Historical packages and execution evidence remain
unchanged.

### Deferred production scope (PR #104)

PR #103 validates the shared presenter only in the isolated fixture. PR #104
retains production illustrated terrain activation; selective suppression of legacy
ground polygons while retaining decorative details; production tint and crash-site
shading integration; actual streamed-chunk integration; gameplay and construction
compatibility; production draw-order verification; and production performance
acceptance. None of these production gates is established by PR #103. Visual
equivalence and responsiveness are owner observations, not pixel-perfect
equivalence or measured performance improvement.

### Static acceptance and exact preservation amendments

The focused [static suite](../tests/static_illustrated_terrain_presenter_test.py)
checks actual source order/guards, rectangle arithmetic, a source-bound token
predicate with an independent lifecycle/pixel model, resolver arithmetic/metadata,
reference-method equality, dormant boundaries and negative tampering. Python
models do not execute GDScript or establish TileMapLayer runtime behavior.

The [preservation helper](../tests/production_terrain_preservation.py) pins six exact
#103 source/scene inputs and the amended historical test candidates. Only verified
candidate bytes may project back to immutable PR #102 merge bytes for historical
comparisons; unlisted paths are returned unchanged. Original fixture hashes remain
unchanged. Candidate helper bytes are pinned by the focused suite. Appended,
truncated, duplicated and alternate-path candidates are rejected. No directory,
asset, runner-policy, command or native execution exemption is added.

| Amended file in `tests/` | Original purpose / #103 conflict | Narrow amendment and retained protection |
| --- | --- | --- |
| `static_weathered_earth_test.py` | Exact exterior preservation conflicts with dormant wiring | Verify exact exterior candidate before original historical-byte comparison; all other checks retained |
| `static_low_green_ground_test.py` | Same exterior-byte conflict | Same verified projection; masks, material distribution, tint/detail assertions retained |
| `static_illustrated_terrain_test.py` | Whole-tree production preservation rejects wiring | Exact candidate projection before original comparison; artwork and original lab checks retained |
| `static_native_terrain_47_test.py` | Protected path inventory excludes presenter/wiring | Verify six exact source/scene candidates; every other path follows original guard |
| `static_machine_icons_test.py` | Changed-path inventory excludes presenter/wiring | Remove only exact hash-verified candidates from historical changed set; original asset/tool checks retained |
| `static_terrain_resolver_test.py` | Production-preservation and resolver-reference bans reject integration | Exact verified candidate paths only; resolver/lookup hashes and arithmetic tests unchanged |
| `static_production_terrain_test.py` | #102 fixture/source and raw stage inventory describe historical bytes | Verify current candidates, then test immutable #102 source and inventory; new suite checks actual #103/default-reference methods |
| `static_v2_connection_test.py` | Shared exterior exact-byte guard rejects wiring | Exact verified projection before its original comparison; other worlds/art remain exact |
| `static_v2_production_host_test.py` | Older whole-tree guard also includes exterior | Exact candidate projection before existing P8 comparison; unrelated production/artwork checks retained |
| `native_terrain_preservation.py` | Existing pinned V2-test correction rejects its new exact amendment | Verify #103 candidate before unchanged PR #98 correction/hash checks |
| `production_terrain_preservation.py` | Four #102 fixture pins reject extended fixture | Retain original pins after exact verified candidate projection; add only explicit #103 inputs/test hashes |

The focused suite supplies altered/appended/duplicated/path-expansion negatives
for every pinned candidate, helper identity checks, and unchanged/unlisted owner
resource rejection. The original #102 stage manifest and external evidence remain
immutable. Its historical raw-working CRLF hashes are reconciled only against
immutable committed LF/CRLF representations after current candidate verification.
This historical inventory is not a #103 execution inventory. Its reconciliation
requires unchanged inputs to equal immutable committed text after newline
normalization, with binary inputs exact; changed/duplicated/truncated bytes and
incorrect manifest digests are rejected. The original ground-rejection test is
unchanged and receives the same exact projection through its existing historical
helper call.

Static command (non-native, `-B` disables bytecode writes):
`python -B -m unittest discover -s tests -p 'static_*test.py'`.
Use an explicit bounded external wait/process timeout; do not silently expand the
runner's 60-second control. Record results/count/timing separately from native
and graphical validation. The static suite's existing authoring module is loaded
with `runpy` under a non-main name and computes PNG bytes in memory; its file-write
entry point is not invoked. Git subprocesses are read-only inspections.

Static verification on 2026-11-01: **161 tests PASS in 111.970 seconds**
(112.546 seconds including the external controller), including 11 focused
presenter checks. The direct Python command above ran under a separate 180-second
subprocess timeout, without changing the runner's fixed 60-second bound. The
focused command with pattern `static_illustrated_terrain_presenter_test.py` passed
11 tests in 4.893 seconds under a 60-second bound. The initial full run exposed
four historical-guard/newline compatibility failures; those exact checks were
corrected and the full suite then passed. Markdown target paths and staged diff
whitespace passed. All 34 pre-existing untracked owner files retained their
captured SHA-256 hashes; the PR #99 preservation reference is unchanged. No
Godot/import/native/graphical/performance validation was executed, and production
illustrated terrain is not activated. No routine success logs were saved.

### Historical isolated-validation proposal (subsequently executed)

The following was the preparation proposal before the separately authorized runs
recorded above; it is not a new execution instruction.

Before any launch, review a new exact #103 input inventory, commands, executable
hash, process/output limits, dependency closure and preservation captures. Do not
reuse or edit #102 stages, manifest or evidence. Create a fresh unique external
stage only after separate authorization. Include the extended fixture/harness,
presenter, unchanged resolver/lookup, approved baked resources, and the existing
fixture tint/state/type dependencies. Exclude production scenes/startup, autoloads,
owner files, untracked inputs, caches and historical evidence. Generate only the
reviewed stage-local configuration, with no production main scene.

Propose sequential one-attempt cold import (60 seconds), then bounded extended
native assertions (30 seconds), then separately owner-controlled fixture graphics
(120 seconds). Use the pinned standard executable, 1,048,576-byte combined output
limit and 4096-byte diagnostics, confirm termination, and stop on any error,
assertion, malformed completion, timeout, overflow or identity change. No retries,
profiling, benchmarks, editor launch or production gameplay are included. Exact
commands/inventory/supervisor require review before authorization; the standing
recipe-switching Native exception does not cover this fixture.

Graphical review must compare both backends in all three existing shading modes,
negative cells, seams, retirement/replacement/reload and original camera views.
Production tint, selective ground suppression with details retained, effective
Z ordering near -10 below minerals/highlights, streaming and gameplay remain #104.

### Startup visibility follow-up (PR #103, pending merge)

Inspection at `123b29b0cef3386f476117b7952d5ad91d6b0f98` found the existing
configuration already safe: the root/reference Terrain retain default visibility,
the presenter parent explicitly has `visible = false`, and its Terrain child has
no TileSet or serialized cells. `_presenter_mode` starts false; `_ready()` loads
only reference chunks and never initializes the presenter. The backend picker
lists reference first. No fixture script, scene, native harness, production code,
artwork, preservation candidate hash or historical comparison was changed.

Two focused static checks now bind those startup facts and the switching order:
retire the old backend, set complementary visibility flags without yielding,
then populate the selected backend. Initialization/retirement failure returns
before changing visibility. These are source contracts, not observed engine
rendering. The existing reference/shading/camera/determinism checks remain intact.

Follow-up validation on 2026-11-01: **13 focused tests PASS in 4.668 seconds**
(4.872 seconds with controller; 60-second bound); **163 full static tests PASS
in 103.812 seconds** (104.408 seconds with controller; 180-second bound). Commands
use the same `python -B -m unittest discover -s tests` invocation above, with
patterns `static_illustrated_terrain_presenter_test.py` and `static_*test.py`.
Exact candidate pins, helper identities, historical comparisons and tamper
negatives passed unchanged. No engine/native/graphical checks were performed.

### Historical exact native fixture proposal (subsequently executed)

This section preserves the pre-execution proposal. Its former unexecuted status
is superseded by the final acceptance record above.

The [new #103 inventory](experiments/illustrated_terrain_presenter_stage.json)
lists **54 committed input paths with exact byte counts and SHA-256 hashes**, plus
the complete generated `project.godot` text and its byte count/hash. Use exact Git
blob bytes from `123b29b0cef3386f476117b7952d5ad91d6b0f98`; the follow-up changes
only static tests and review documents. Do not copy working-tree CRLF variants,
untracked sidecars, caches, owner files, historical outputs or a whole checkout.
Resource/global-class dependency closure was inspected without executing source.
The original #102 inventory and evidence remain unchanged.

The committed LF inventory SHA-256 is
`3fd7c93864752be48dbd9f43dd52264a1a37d1b034f3c676d8dc9429a0174928`.
Generated configuration SHA-256 is
`5716c7e88113b18915bc027d3714f60ecc36698c84bec332b5ecbe7a1b08b1a2`.
It uses Compatibility rendering, serial imports, a 1280x720 viewport, and no main
scene, autoload, production input map or save system. It is UTF-8 without BOM,
LF with final newline. No stage or stage-local file has been created.

**Executable:** `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`,
SHA-256 `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.
Nonexecuting file metadata reports FileVersion `4.7.2` and ProductVersion
`4.7.2.stable.official`; the executable hash was read and matched. No `--version`
launch was performed. Rehash before every proposed process.

After separate authorization, use a new, previously nonexistent plain directory
`D:\GameDev\Godot\TLWH-NativeStages\tlwh-pr103-review-<fresh-guid>`. Verify resolved
paths stay inside that parent; reject links/reparse points in inputs, outputs and
stage paths. Never reuse or modify a #102 stage or its supervisor/evidence. Copy
only the 54 inventoried blobs and generate only the sealed configuration; verify
the exact initial 55-file set and all hashes before import.

Capture source revision/branch, complete status, index digest, input identities,
protected branch refs and hashes of tracked and protected untracked/ignored owner
files before the required static gate. Require fresh actual static PASS and
unchanged captures before/during/after each phase; never silently refresh an old
baseline. Source `.godot/`, saves/settings, assets and evidence are never engine
inputs or output destinations. Preserve source and every stage on failure/success.

The JSON lists **36 exact allowed generated output paths**: 23 engine cache paths,
seven absent PNG import sidecars and six absent script/shader UID sidecars. The
paths derive from the read-only #102 generated-output inventory plus the new
presenter UID; its historical hashes are not reused as new output hashes. Reject
all other new paths and any original-input modification, including rewrites of
the two staged tracked item import sidecars. After clean import, capture the
actual allowed outputs and their hashes. Assertions/graphics must not add,
remove or modify that captured output set. No blanket `.godot/` or executable
extension exemption is proposed. The complete supervisor implementation and seal
must be separately reviewed against this inventory before any launch; no #103
supervisor has been prepared or approved by this follow-up.

Run sequentially with working directory `<stage>`, one process at a time, no
automatic retries. Every row uses the exact pinned executable above:

| Phase | Exact argument vector | Timeout |
| --- | --- | --- |
| Cold import | `["--headless", "--editor", "--path", "<stage>", "--quit"]` | 60 seconds |
| Assertions, only after import PASS | `["--headless", "--path", "<stage>", "--script", "res://scenes/experiments/production_terrain/engine_validation.gd"]` | 30 seconds |
| Owner-controlled graphical acceptance, separately authorized after both PASS | `["--path", "<stage>", "res://scenes/experiments/production_terrain/fixture.tscn"]` | 120 seconds; owner closes sooner after checks |

Each process has a **1,048,576-byte combined stdout/stderr limit** and a maximum
**4096-byte retained diagnostic excerpt**. A reviewed external supervisor must
drain both pipes, enforce time/output limits and confirm process-tree termination.
Stop on engine/script/parse/shader errors even with exit zero, assertion failure,
abnormal exit/crash, timeout, output overflow, missing/duplicate/malformed final
completion, unexpected files, changed source/stage/executable identities or
uncertain termination. Assertions require exit zero and exactly one final nonempty
stdout line `Production terrain fixture failures: 0`. Timeout/overflow requires
bounded process-tree termination and review before any further launch. Never
automatically retry or escalate to profiling, stress testing or freeze reproduction.
Keep bounded useful diagnostics in new evidence files without overwriting history.

Owner graphical acceptance must remain separate from process completion:

1. On the first frame, before selecting anything, confirm **PR #102 reference**
   is selected, only reference ground appears, and all four chunks are present.
   The native harness checks reference state/cells; visible startup itself still
   requires this graphical check, not an inferred headless result.
2. Check Unshaded, CPU tint and Crash-style tint + override at the original
   Overview, Origin/shading, Negative/pocket, Narrow/seam and Irregular/islands
   views. Compare accepted #102 appearance without changing historical evidence.
3. Explicitly select **PR #103 presenter**. Repeat the same shading/views and
   load/unload/replace/forward/reverse controls. Confirm no duplicate full-ground
   pass, seams, displaced cells or loss of negative-coordinate ownership.
4. Switch back to reference and repeat both directions. Confirm only the selected
   backend remains visible and the reference comparison is restored unchanged.
5. Inspect diagnostics for errors, record explicit owner PASS/observations for
   startup, switching, comparisons and lifecycle, then close inside the bound.
   If responsiveness becomes abnormal, stop; do not attempt to reproduce a freeze.

This proposal grants no execution permission. No editor GUI, production gameplay,
profiling, benchmark, merge, cleanup or PR #104 activity is included.
