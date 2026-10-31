# Production-scale illustrated terrain fixture (PR #102, pending merge)

Open [fixture.tscn](../scenes/experiments/production_terrain/fixture.tscn) for text
inspection. Running it requires the separate Gate 2 authorization below. After
authorization, use **F6 / Run Current Scene** only in the approved stage. F5 still
starts production V2. No exterior, production scene, generator, renderer, mask,
construction definition, resolver, artwork or terrain metadata is changed.

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
quantization; float vertex texture support/compilation remain unverified.

The field uploads once per change to a shaded mode. Unshaded switching and chunk
operations upload nothing. There are no per-cell materials or second ground pass.
Debug rectangles are unfilled; the grid contains lines/dots. Terrain renders
behind the parent's debug drawing. No internal TileMapLayer updates are forced.

This evaluates vertex sampling first. Quad triangulation/interpolation, filtering
and texture edges require visual review. Visually equivalent shading is the aim;
exact interpolation/pixel parity is **not proven**. Use detail views for narrow
features hidden by overview downsampling. UI is a small desktop fixture panel.
Shared rendering proves no speed improvement. Performance, responsiveness,
host stability and GPU behavior remain unverified.

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
branch remains `326591e1a1438944d79b0be4c52992b3eb86af0f`. No engine was invoked.

[Focused Python tests](../tests/static_production_terrain_test.py) use source-bound
models, the existing resolver oracle and resource text. They cover the halo,
24 chunk orders, replacement/retirement/regeneration, all adjacent boundaries,
variants, signed coordinates, texel mapping, shared tint contributors, shading
order, upload bounds, references and preservation. These are not engine tests.
Historical guards admit only four exact new paths with normalized-content hashes,
rejecting tampering/path expansion. Existing artwork pins and Native controls stay.

## Gate 2: proposed engine execution, NOT AUTHORIZED

Do not run Godot, Native, NativePlan, imports, graphics, profiling, benchmarks or
automation during implementation. The standing recipe-switching exception covers
neither these commands nor this inventory. This plan grants no permission and
does not change [LOCAL_TESTING.md](LOCAL_TESTING.md).

Before owner authorization, review these exact commands and the
[explicit input inventory](experiments/production_terrain_stage.json), including
raw byte hashes. A future supervised execution implementation must be reviewed
before use; no runner is installed here. Dependencies exist because real tint
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

## Owner graphical acceptance (all pending)

- [ ] Imports/classes load cleanly; lookup verifies all 98 native assignments.
- [ ] Overview/detail show broad interiors, both boundary axes, pocket, islands,
      narrow bridges and irregular transitions without missing tiles.
- [ ] Origin view: orange origins/white centers align; 32-unit grid divides each
      64-unit cell in two per axis, including negative regions.
- [ ] Forward/reverse loads look identical; seam geometry matches.
- [ ] Unload each chunk: all 1024 cells disappear, others remain. Reload/replace
      restore identical assignments and A/B/C artwork.
- [ ] CPU/crash-style tint compile cleanly and preserve geometry; gradients remain
      continuous across both seams and the four-chunk junction.
- [ ] Synthetic recovery/core/override affect tint only; unshaded restores artwork.
      No doubled ground pass appears.
- [ ] Detail views show no unacceptable atlas cracks/diagonal tint interpolation;
      chunk/grid overlay toggles cleanly.
- [ ] Brief game/editor interaction stays responsive; close within authorized
      bounds and inspect output, recording issues without profiling/reproduction.

No engine validation, graphical acceptance or performance acceptance is claimed.
Production exterior integration remains a separate milestone.
