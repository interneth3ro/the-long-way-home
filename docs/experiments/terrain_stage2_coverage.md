# Stage 2A: production ground classification specification

Status: additive offline reference on a feature branch, pending owner acceptance
and merge. This document's filename reserves the Stage 2 topic; **Stage 2A defines
classification only**. It implements no continuous coverage, interpolation field,
distance field, shader, cache, artwork change or runtime integration.

## Authority and provenance

Reviewed production baseline: `06666cc108d431294aba25d1ba0bd652d448c18b`, the
verified merge of [PR #133](https://github.com/interneth3ro/the-long-way-home/pull/133).
Production remains the illustrated baked TileSet renderer. C1 is isolated.
The owner-reported Stage 1 7/7 Godot acceptance is prior owner evidence, not
verification performed by this package.

The canonical authority is
[PlanetGenerator](../../scenes/world/planet_generator.gd), lines 17–62 and
83–150, especially `sample_ground_material()` at lines 137–150. No source
deviation from the Stage 2A handoff was found. The offline rule label
`production-ground@06666cc108d431294aba25d1ba0bd652d448c18b` identifies this
reviewed snapshot; it is **not a new production generation version**.
[TerrainResolver](../../scenes/world/terrain_resolver.gd), lines 4–13, separately
versions illustrated presentation resolution with `RULE_VERSION = 1`.

The [vectors](../../tests/fixtures/terrain_stage2_classification_vectors.json)
pin LF-normalized SHA-256 identities for generator, coordinate definitions,
scene and gameplay geometry. The geometry digest hashes compact JSON of ordered
gameplay vertices, `(name, vertices, feather)` overlays and `(name, point)`
anchors, using the reference's float-valued coordinates. Colors and state
revision are excluded from that semantic geometry digest. Full scene hashes
are broader provenance pins, not proposed cache keys.

## Existing classification behavior

Input is a signed integer world seed and an **absolute terrain cell** `(x,y)`.
Its center is `(64x+32, 64y+32)`. All four original Green subtypes are retained:

| ID | Meaning | Legacy texture basename |
| --- | --- | --- |
| 0 | Weathered Earth | `a_base_soil` |
| 1 | Green | `a_balanced_cover` |
| 2 | Green | `b_moss_dominant` |
| 3 | Green | `c_exposed_earth` |
| 4 | Green | `d_fine_grass` |

The names come from [TerrainChunk](../../scenes/world/terrain_chunk.gd), lines
5–10. Illustrated presentation collapses IDs 1–4 to binary Green; this oracle
preserves the exact original ID, not just that binary label.

At the center, exclusions take precedence and return 0. Otherwise:

```text
cover = noise(center / 768, 8) + 0.18 * noise(center / 192, 9)
cover < 0.64 -> 0
otherwise -> 1 + min(3, int(coordinate_random(cell, 10) * 4))
```

Equality at the noise threshold takes the Green branch. Random values lie in
`[0,1)`, so truncation chooses subtypes at intervals `[0,.25)`, `[.25,.5)`,
`[.5,.75)`, `[.75,1)`.

For hash modulus `P = 2147483647`, start with `seed posmod P`; update in order:

1. `(value*48271 + (x posmod P)*69621) posmod P`.
2. `(value*48271 + (y posmod P)*907) posmod P`.
3. `(value*48271 + channel*104729) posmod P`.
4. `((value XOR (value >> 13))*48271) posmod P`.
5. Convert to float and divide by `P`.

Positive-modulus Python `%` models the nonnegative `posmod` residues. Seeds
differing by `P` are expected aliases when both are valid source integers.
This does not assert that different non-alias seeds always produce different
material IDs. Hash channels used here are fixed 8, 9 and 10; no arbitrary-channel
overflow guarantee is implied. Reduced integer intermediates fit source int64.

Noise floors both lattice coordinates, applies `t*t*(3-2*t)` per fractional
axis, then interpolates the four coordinate-hash corner values. It has no mutable
RNG, exploration order or loaded-neighbor dependency.

## Geometry, exclusions and boundaries

[PlanetExterior](../../scenes/world/planet_exterior.gd), lines 69–79, collects
direct `Polygon2D` children of `AuthoredCrashSite` in scene order and supplies
feather 256 for each. It collects positions of direct `StaticBody2D` children of
`GroundObjects`. Current local coordinates are consumed directly, without
scene-transform evaluation by the oracle.

| Ordered input | Current data/source |
| --- | --- |
| Gameplay polygon | Six vertices in [CrashSiteProtection](../../scenes/world/crash_site_protection.gd), lines 6–8 |
| Clearing | Eight vertices in [scene](../../scenes/world/planet_exterior.tscn), lines 55–57 |
| ImpactScar | Five vertices, scene lines 59–61 |
| NorthRidge | Seven vertices, scene lines 63–65 |
| SouthShelf | Seven vertices, scene lines 67–69 |
| CrashedShip anchor | `(-384,-192)`, scene lines 96–98 |
| Hatch anchor | `(-384,-176)`, scene lines 153–156 |
| WestRock anchor | `(-768,384)`, scene lines 185–187 |
| EastRock anchor | `(704,-384)`, scene lines 197–199 |

All vertices remain independently editable in their original source. The parser
reads those inputs rather than duplicating production polygons in Python.
Inventory/order tests reject an unreviewed authoring change.

The precise short-circuit order in generator lines 98–112 and 137–145 is:

1. Gameplay polygon inclusion **or** polygon-edge distance **<48**.
2. Any object-anchor distance **<160**.
3. Any authored polygon's `overlay_weight(point, polygon, 48) > 0`.
4. Any authored polygon's `overlay_weight(point, polygon, 256) > 0`.

Overlay weight is 1 inside a polygon, otherwise
`1 - smoothstep(0, feather, minimum_segment_distance)`.
Retain the **computed weight >0** predicate; do not replace it with a larger
closed polygon or assume exact real-number equivalence near floating endpoints.
At simple axis-aligned exact distances, 48 is outside the first clearance and
160 outside an anchor circle; overlay distance 256 has zero weight. A 48-unit
authored clearance boundary can still be inside its separate 256-unit skirt.
Overlaps can cause another exclusion to win.

The reference's polygon inclusion convention includes polygon boundaries.
Stage 2A does not claim Geometry2D's isolated boundary tie policy. For this final
classification predicate, zero edge distance is already protected by positive
48/256-unit reach regardless of that tie. Near-boundary floating-point parity
remains unverified; synthetic exact cases and offset probes are model evidence.

Generator lines 23–31 build a conservative union bounding rectangle: gameplay
grown by 49, anchor rectangles by 161, overlay bounds by `max(48,feather)+1`.
`Rect2.has_point` excludes right/bottom edges. This only skips distant precise
queries; it does not force Earth. The new reference deliberately evaluates the
precise predicates without this optimization. The existing broad-phase suite
compares optimized and unoptimized offline models.

Ferrite generation has separate gameplay bounds in
[FerriteRegionGenerator](../../scenes/world/ferrite_region_generator.gd), lines
64–68. It is not an additional ground-material input. Do not infer new Earth
exclusions from mineral artwork, Ferrite region bounds or collision silhouettes.

## Coordinates and independent state contracts

[WorldCoordinates](../../scenes/world/world_coordinates.gd), lines 4–27, retains
64-unit terrain/Ferrite cells, 32-unit construction cells and 32 terrain cells
per 2048-unit chunk. World ownership uses floor: cells and chunks own their
left/top boundaries and exclude right/bottom. Cell `-1` has chunk `-1`, local 31;
world `(-.001,0)` maps to terrain `(-1,0)`. The production 128-pixel TileSet
retains its scene scale 0.5 (scene lines 45–50).

Classification has no state argument. Terrain color and detail-removal records
in [PlanetWorldState](../../scenes/world/planet_world_state.gd), lines 534–550,
can increment revision but do not alter material input or identity. Source
guards establish that separation; Stage 2A does not execute state mutations in
GDScript or create a pretend Python gameplay-state implementation.

The unchanged visual pipeline is baseline color -> state override -> overlays
in scene order (generator lines 67–80) -> four center samples averaged at each
shared halo vertex -> Earth tint conversion (TerrainChunk lines 31–44, 62–67).
Decorations retain absolute-cell removal identity and protection/recovery
suppression (generator lines 116–132). Gameplay, construction and deposits do
not consume ground IDs. Stage 1 publication receipts, revision checks, arrival
and transitions remain separate existing authorities.

## Evidence and limits

The [reference](../../tests/terrain_stage2_reference.py) is Python binary64
arithmetic, not an engine emulator. Its four-corner weighted sum is independently
derived from the interpolation equation. Production uses Vector2 operations and
`lerpf`; Vector2 precision and intermediate rounding can differ. Exact material
IDs in this bounded set do not prove all-input GDScript/Python parity.

The [tests](../../tests/static_terrain_stage2_coverage_test.py) distinguish:

- **Independent mathematical checks:** hand-derived rectangle/circle thresholds,
  floor ownership, zero hash, subtype intervals, and exact Fraction evaluation
  of center noise. Fractions interpret decimal .18/.64 as 9/50 and 16/25;
  they do not model engine rounding.
- **Frozen goldens:** 14 records, including all IDs 0–4. Ten noise cases were
  calculated separately using exact rational arithmetic and cross-checked against
  the pre-existing `static_ground_rejection_test.material_at` model. Their exact
  cover fractions and subtype hash numerators are retained for review. They are
  more than `1e-4` from the noise threshold. Four geometry cases were reviewed as
  polygon interiors and cross-checked with the existing geometry oracle. These
  expectations were not generated from the new classifier.
- **Model comparisons:** the new extraction/geometry/hash/noise/classifier versus
  existing offline models. Shared source equations limit independence; agreement
  is not runtime parity. Real geometry edge/vertex probes supplement hand cases.
- **Metamorphic checks:** signed-seed aliases, reversed/shuffled queries and
  discarding/reloading geometry. There is no renderer eviction implementation.
- **Source guards:** fixed-baseline comparisons of existing tracked systems,
  source provenance hashes and tint/detail/publication wiring. These prove byte
  preservation and source relationships, not executed behavior.

Seeds include 0, 26026, -42, -1 and modulus-related values; hash checks also
exercise signed-int64 endpoints. Offline classification samples cover chunk
origins `[-4,4]` on both axes with offsets -1, 0, 15, 31, 32, crash surroundings,
and selected corner probes near chunks +/-512. This is a finite **test scope**,
not a production coordinate envelope or a performance/resource budget. Tests use
exact comparisons for IDs/hashes and 14-decimal-place tolerance only for model
noise comparison. Threshold-adjacent tests exercise the Python branch directly;
they do not establish engine threshold parity.

Permitted focused command, run from repository root:

```powershell
python -B -m unittest discover -s tests -p 'static_terrain_stage2_coverage_test.py' -v
```

Relevant existing source/offline suites are `static_ground_rejection_test.py`,
`static_low_green_ground_test.py`, `static_ground_publication_test.py` and
`static_transition_safety_test.py`. No test writes vectors, runs Godot or changes
the engine runner inventory. Record actual counts/timings in the PR, not as a
new permanent successful-run log.

No Godot editor/headless/import/test, GPU validation, gameplay, art regeneration,
shader compilation or benchmark is supplied by Stage 2A. If a mismatch is
unexplained, preserve evidence and stop; do not alter source, relax guards or
regenerate expected values to force a pass.

## Deferred decisions and review gate

Stage 2B must separately address reconstruction, strict-Earth filtering and
compatibility with canonical Green centers. Stage 3 may consider opt-in artwork
and renderer integration. Distribution, crash tint, recovery appearance, coordinate
support and numerical budgets retain their separate owner gates. No Stage 2A
test authorizes those changes or expands execution permissions.

Documentation-sync review found stale lifecycle labels at
[ILLUSTRATED_EXTERIOR](../ILLUSTRATED_EXTERIOR.md), line 13 (Stage 1 pending), and
[terrain_c1](terrain_c1.md), line 37 (PR #131 unmerged). They are reported rather
than edited outside this four-file scope. This new classification contract fills
the documentation gap without changing design/narrative canon or those records.

Owner/ChatGPT review must accept the specification and independently justified
vectors before merge. Leave the PR draft; no ready-for-review, merge, cleanup or
Stage 2B action is implied. Rollback is leaving the draft unmerged, or a separately
reviewed revert after an owner-approved merge; no asset/state migration is involved.
