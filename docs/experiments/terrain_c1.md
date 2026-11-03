# Terrain Visual Fidelity 2.0 — isolated Prototype C1

Status: implemented for review on `codex/terrain-c1-continuous-prototype`, pending
Godot import, shader compilation and owner visual acceptance. **No Godot has run.**
Base: `fa410ed9b329ffd28a927e142d2362971d54584a`. The draft PR and final chat identify
the exact review HEAD; a commit cannot contain its own hash.

## Question and isolation

Can world-coordinate material windows and cached organic regional fields present
natural grass/Earth without the 64-unit image repetition seen in A1? The supplied
`grassland.png` board was visually reviewed as art direction, never sampled/cropped.
No A1 art revision, FactoryGame input/reuse or production integration is included.
[A1 remains preserved in draft PR #130](https://github.com/interneth3ro/the-long-way-home/pull/130).

Entry point: [terrain_c1.tscn](../../scenes/experiments/terrain_c1/terrain_c1.tscn).
This scene has no production startup reference, construction-world group, gameplay
collisions or persistent writes. Production source/resources remain unchanged.
Only previews have `.gdignore`; live experimental sources/fields are importable
later by the owner. No import metadata or generated Godot cache is committed.

## Data flow and supported bounds

1. [Offline author](../../tools/terrain-c1-author.py) reads current crash polygons,
   gameplay protection and authored object anchors, preserving their order and
   source hashes. No production generation/distribution code is changed.
2. Four 2048-unit chunks at `(-1,-1), (0,-1), (-1,0), (0,0)` meet at origin.
   [fixture.json](../../assets/experiments/terrain_c1/fixture.json) fixes seed 26026,
   field rule `c1_fields_v1` and artwork revision `c1_materials_v1`.
3. Each cached RGB field is **137x137**, with 16-world-unit spacing and four sample
   gutters (64 world units). R is Green coverage, G broad brightness variation,
   B a vegetation-detail-contrast control, not gameplay density/population.
4. Each **7x7 RGB** phase table uses SHA-256 over rule, artwork revision, signed
   seed and absolute integer lattice identities. Neighbor chunks share identities.
5. [Candidate shader](../../scenes/experiments/terrain_c1/continuous.gdshader) uses
   local `VERTEX` positions and metadata, never floating world-coordinate hashes.
   Four smoothly weighted material windows per material use a 512-unit lattice.
   Samples remain inside the source artwork (.10–.90 UV bounds); no source tiling
   or opposite-edge seam repair is required. Explicit texture gradients exclude
   metadata phase jumps. No window rotates the painted lighting.
6. Coverage blends Earth/Green; macro and detail-contrast controls add broad
   variation. A separate optional tint texture multiplies the result.

Support is deliberately limited to the fixed four-chunk fixture, world bounds
`[-2048,2048]` on both axes and its 64-unit sampling halo. Other seeds/regions need
new explicit fixture authoring; this is not an unbounded-world implementation.
The shader receives only local 0–2048 positions. Cross-backend GPU pixel identity
is not required or claimed; CPU field/identity reconstruction is deterministic.

The shader convention was checked against the official
[CanvasItem local-coordinate documentation](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/canvas_item_shader.html)
and [shading-language reference](https://docs.godotengine.org/en/stable/tutorials/shaders/shader_reference/shading_language.html).
Documentation/source inspection is not shader compilation or engine validation.

## Clearing, tint and baseline

Strict Earth excludes the shared gameplay polygon plus 48-unit clearance, authored
object-anchor 160-unit circles, and each visual polygon including its full
256-unit recovery skirt. These reproduce the current material-exclusion predicates
as conservative continuous geometry. Outer visual recovery is allowed only outside
that union. Its width varies smoothly from 120 to 420 units using seeded fields.

Coverage is zero at every grid node within `sqrt(2)*16 + .001` units of the strict
union. Thus all four bilinear footprint nodes around any strictly excluded point
remain zero. Quantization rounds coverage downward. This proof assumes ordinary
bilinear field sampling without mips; the shader explicitly uses `filter_linear`
and no `source_color` conversion for numerical fields. Godot filtering itself is
untested. The conservative guard slightly enlarges visible Earth outside the strict
union; it never changes the gameplay polygon. Normalized global field samples,
including every overlapping gutter node, agree across regions.

The fixed fixture is modestly Green-dominant: 35,830 of 65,536 interior grid nodes
classify Green at coverage >= .5; mean coverage is approximately .545. These are
offline fixture statistics, not production-world coverage or performance results.

The [harness](../../scenes/experiments/terrain_c1/harness.gd) samples this common
coverage field at 64-unit centers for the baseline, then calls the existing
`IllustratedTerrainPresenter`, resolver and production TileSet. The candidate does
not use native assignments or the 94-signature color atlas. Their intended clearing
is shared, but exact contours differ deliberately. Baseline means current illustrated
presentation over the C1 fixture, not a capture of the actual production world.

Normal tint is prepared through unchanged `TerrainChunk.configure()` and
`write_tint()` with the original `PlanetGenerator` and an isolated `PlanetWorldState`.
This retains state override identities and precedence: baseline color, state color
override, then authored overlay order. Both views receive the same prepared tint
vertices. Existing Earth-biased conversion supplies compatibility brightness/warmth;
the separate candidate macro/detail controls retain Green variation independently.
Neither view displays the primitive ground decorations; no detail-removal records
are edited. There is no override editor in this fixed harness.

## Publication, retention and readiness simulation

Preparation is bounded to one fixed chunk per frame. Both paths are prepared so
switching does not change the fixture or camera. Immutable field/phase caches are
limited to four each, and two shared material textures generate mipmaps once.
Per-chunk tint textures and surfaces replace old visuals only after baseline
preparation succeeds and the request epoch, seed and state revision remain current.
Retirement requires the active generation token. R retires/reconstructs all four;
V replaces them in reverse order while retaining old visuals until publication.

The opaque curtain and pan lock release only when all four active regions complete
the current epoch. This is a harness readiness simulation, not an implementation
or verification of `SceneTransitionController` / Main-to-exterior arrival. Unexpected
state identity changes stop the harness. No background jobs, mutable RNG, disk
cache, save system, dynamic stream radius or generalized renderer framework is added.
Both renderer resources stay resident, so this harness is unsuitable for comparing
production memory or performance by toggling B.

## Materials, provenance and offline evidence

Two **new 1254x1254 RGB** image_gen material sources are frozen under
[sources](../../assets/experiments/terrain_c1/sources/green.png). Full prompts,
provider hashes, packaged hashes and dimensions are in
[provenance.json](../../assets/experiments/terrain_c1/provenance.json). Ancillary PNG
metadata was stripped without changing compressed pixel data; provider originals
remain preserved outside the checkout. No private absolute paths are published.
Model generation is not reproducible; saved source pixels are the authoring inputs.

Green has interwoven grass/leaf structure and quieter areas; Earth uses shallow,
muted soil/grit. These are large interior-window sources, not 128-pixel tiles or
accepted production assets. The Green source still contains directional blade
shapes, which remain a visual risk despite the prompt's constraints.

| CPU evidence | Interpretation |
| --- | --- |
| [Recovery 1.0x](../../assets/experiments/terrain_c1/previews/recovery_1x.png) | Same 768x512-world-unit crop and camera on both sides |
| [Recovery 0.5x](../../assets/experiments/terrain_c1/previews/recovery_05x.png) | Same world crop reduced to 384x256 per panel |
| [Long grass 0.5x](../../assets/experiments/terrain_c1/previews/long_green_05x.png) | 4000x240-world-unit strip, including the negative/positive X boundary |
| [Origin junction 0.5x](../../assets/experiments/terrain_c1/previews/junction_05x.png) | Four-way crossing; origin is mandatory Earth, not grass |
| [Regional fields](../../assets/experiments/terrain_c1/previews/fields_overview.png) | Whole fixture at 1:8; R coverage / G macro / B contrast, not final terrain colors |

These are labeled **CPU approximations**, not Godot renderer output. They use
nearest source samples with linear-light window/material blending and omit runtime
tint, GPU material filtering, mip selection, foregrounds and motion. Source-scale
1.0x/0.5x describes world-to-output pixels before viewer scaling. CPU approximations
do not demonstrate shader parity or visual acceptance. Ship/shadow/Ferrite references
are present in the live candidate-only scene at existing scales/registrations; no
offline context image is passed off as a screenshot.

Observed offline: the recovery is continuous instead of signature-scalloped and
there is no 64-unit color-image phase in the candidate model. Larger grass forms
remain recognizable, and broad window blending can soften material structure or
make earthy/green transition bands muddy. The long view is supplied to expose
recurrence rather than assert it has been eliminated. Naturalness, filtering,
shimmer and readability remain owner questions. The concept's flowers/boulders
are not added as background decorations or gameplay objects.

## Checks and limits

Focused checks run without Godot:

- Eight `static_terrain_c1_test.py` tests: saved field pixels; all shared field and
  phase gutters; reconstructed crossings/negative coordinates; strict exclusions
  under bilinear reconstruction; reversed regeneration and retirement reconstruction;
  canonical material identities/window bounds; isolation/identity source checks;
  preservation of production-owned override precedence.
- Nine field/fixture outputs reproduced exactly (JSON LF-normalized).
- Five CPU preview outputs regenerated for byte comparison.
- Changed-file scope, source/asset references, Markdown links, whitespace and
  pre-existing sidecar hash preservation checked.

CPU lifecycle tests reconstruct data and inspect harness authority guards. They do
not execute GDScript, prove runtime token handling or compile scenes/shaders. No
Godot/editor/import/game, broad test suite, benchmark, profiler, performance probe,
GPU rendering, driver test or actual Main arrival was run. Actual draw calls,
frame rate, residency, arrival cost and responsiveness are unknown. Eight material
samples plus metadata/field/tint reads are a design cost, not a performance result.

```powershell
python -B -m unittest discover -s tests -p static_terrain_c1_test.py -v
python -B tools/terrain-c1-author.py --check
python -B tools/terrain-c1-author.py --check-previews
```

`--write` and `--previews` create outputs exclusively and refuse existing files.
Use only a fresh task-owned output copy for regeneration; preserve reviewed files.
The tools use Python's standard library and existing TLWH PNG/label helpers, never
their production writers. No dependency or plugin was installed.

## Later owner acceptance — instructions only, not executed

Requires separate approval for the exact Godot import and graphical run. The
standing Native recipe-switching exception does not authorize this scene.

Open `scenes/experiments/terrain_c1/terrain_c1.tscn` for a separately authorized F6
run; production F5 remains unchanged. B toggles baseline/candidate, T neutral/normal
tint, F material/coverage/macro/contrast diagnostics, G the chunk junction, H ship
and Ferrite references, R retirement/reload, V reverse replacement. WASD pans;
1/2/3 select 1.0x/0.5x/1.5x. Camera presets: 4 recovery `(-1100,750)`, 5 grass
`(0,-1700)`, 6 origin `(0,0)`, 7 ship `(-384,-192)`. Camera clamps to the finite
fixture for the current viewport/zoom; extremely large windows may exceed it.

1. First require a clean import/parse/shader compilation and a released readiness
   curtain. On any error stop and retain diagnostics; do not assume static PASS
   proves the scene can run.
2. At 1.0x and 0.5x, compare the same preset, viewport, reference visibility and tint
   mode. Both use linear base filtering; candidate material mips are deliberately
   enabled while numerical fields have none. Baseline remains the existing atlas,
   with harness-only linear filtering instead of production's nearest setting.
   Record this limitation rather than attributing every difference to architecture.
3. Pan slowly horizontally, vertically and diagonally across the long Green areas,
   recovery boundary, source-window lattice and origin. Use limited 1.5x close-ups.
   Inspect visible motifs, muddy blends, lattice rhythms and shimmer. Compare with
   the concept and A1 failure evidence at native scale.
4. Use F/G to inspect continuity, including grass on the outer axis crossings and
   mandatory Earth at the four-way origin. Check strict clearing protection and
   ship/Ferrite readability in both tint modes.
5. Exercise R/V, including repeated requests while preparation is pending. Require
   consistent appearance, no stale publication, correct token retirement and curtain
   release only for current completion. This cannot prove production retention or
   Main arrival behavior.
6. Record responsiveness/resource observations qualitatively. Stop on unexplained
   growth or unresponsiveness; quantitative benchmarking needs separate approval.

If continuity/readability are convincing and data checks pass, consider a separately
approved integration investigation. If landmarks repeat, consider focused material
revision for this representation. If sampling/field structures remain objectionable
despite suitable art, reconsider architecture. No automatic C2 or integration follows.

## Untouched contracts, future adapters and owner decisions

Construction size 32, shared terrain/Ferrite size 64, deposit regions/stable IDs,
placement/extraction queries, collisions, inventory, progression, saves/session
records, current generator/distribution, crash gameplay geometry and production
arrival/defaults are unchanged. `PlanetWorldState` is local harness data only.
Production references: [coordinates](../../scenes/world/world_coordinates.gd),
[placement](../../construction/placement_rules.gd),
[Ferrite](../../scenes/world/ferrite_region_generator.gd),
[publication](../../scenes/world/planet_exterior.gd),
[arrival guard](../../scenes/main/scene_transition_controller.gd).

Later integration would need an explicit ground publication/retirement adapter,
dynamic bounded field preparation beyond four fixed regions, revision/seed-aware
cache invalidation and production arrival receipts. It must preserve state overrides
and existing gameplay ownership, not substitute visual coverage for deposit queries.
Future seed persistence must distinguish field/art revisions. No disk save workflow
exists here and no save compatibility is claimed.

Rollback: B selects baseline for this fixture; production startup never selects C1.
No deletion, PR cleanup or A1 modification is needed. Owner questions: Does the
larger grass structure read naturally at 0.5x? Is organic recovery too diffuse?
Do windows reveal repeated forms or directional rhythm? Does normal tint preserve
the desired palette and foreground readability? Is scoped owner Godot verification
desired? The prototype is ready for review, not accepted for integration.

## Exact changed-file inventory

24 additions; no pre-existing tracked file modified:

```text
assets/experiments/terrain_c1/fixture.json
assets/experiments/terrain_c1/provenance.json
assets/experiments/terrain_c1/fields/-1_-1_field.png
assets/experiments/terrain_c1/fields/-1_-1_phase.png
assets/experiments/terrain_c1/fields/-1_0_field.png
assets/experiments/terrain_c1/fields/-1_0_phase.png
assets/experiments/terrain_c1/fields/0_-1_field.png
assets/experiments/terrain_c1/fields/0_-1_phase.png
assets/experiments/terrain_c1/fields/0_0_field.png
assets/experiments/terrain_c1/fields/0_0_phase.png
assets/experiments/terrain_c1/previews/.gdignore
assets/experiments/terrain_c1/previews/fields_overview.png
assets/experiments/terrain_c1/previews/junction_05x.png
assets/experiments/terrain_c1/previews/long_green_05x.png
assets/experiments/terrain_c1/previews/recovery_05x.png
assets/experiments/terrain_c1/previews/recovery_1x.png
assets/experiments/terrain_c1/sources/earth.png
assets/experiments/terrain_c1/sources/green.png
scenes/experiments/terrain_c1/continuous.gdshader
scenes/experiments/terrain_c1/harness.gd
scenes/experiments/terrain_c1/terrain_c1.tscn
tools/terrain-c1-author.py
tests/static_terrain_c1_test.py
docs/experiments/terrain_c1.md
```

All 15 pre-existing untracked PNG import sidecars remain untracked with unchanged
hashes. Ignored A1 intermediates and provider originals were preserved. Publication
review found no private paths/secrets in added text; generated-source ancillary
metadata was removed. The documentation-sync review found no production behavior
change to reconcile in README/GAME_VISION; this requested report documents the
isolated experiment without changing production/design status claims.
