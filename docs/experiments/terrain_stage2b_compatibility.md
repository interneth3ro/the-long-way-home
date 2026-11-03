# Stage 2B-1: strict-Earth / Green-anchor compatibility

Status: offline implementation on `codex/stage2b1-compatibility-oracle`, pending
owner acceptance and merge. This audits a necessary compatibility condition; it
does not implement or select reconstruction, filtering, a renderer or assets.
No fixed production taper/filter margin is proposed.

## Authority, scope and current lifecycle

Base/main was freshly fetched without pruning or fetching tags and verified as
`1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744`, the live merge of
[PR #134](https://github.com/interneth3ro/the-long-way-home/pull/134).
Stage 2A's [classification specification](terrain_stage2_coverage.md),
[reference](../../tests/terrain_stage2_reference.py) and
[14 frozen vectors](../../tests/fixtures/terrain_stage2_classification_vectors.json)
are reused unchanged. Their production base is PR #133's merge
`06666cc108d431294aba25d1ba0bd652d448c18b`; reviewed production bytes still match.
Stage 1's owner-reported 7/7 acceptance is prior evidence, not this audit's work.
Production remains the illustrated baked TileSet renderer; C1 stays isolated.

The only existing-file edit is the historical inventory assertion in
[Stage 2A tests](../../tests/static_terrain_stage2_coverage_test.py). It now compares
Stage 2A's original base to its immutable merge commit, requires exactly the
original four additions, and retains its working-source hash and production
preservation assertions. Future additions no longer redefine Stage 2A history.
The [new tests](../../tests/static_terrain_stage2b_compatibility_test.py) require
exactly these three additions and that one modification, and compare the amended
test to its original bytes except for the exact authorized replacement. Any other
tracked change, missing/extra scope file, changed golden or changed protected
sidecar fails. Existing test semantics and production guards remain intact.

Documentation-sync reconciliation is confined here: Stage 2A is merged despite
its historical pending label at line 3; its deferred Stage 2B wording at line 219
is now split into this compatibility prerequisite and a separately gated offline
reconstruction comparison. The Stage 1 pending heading in
[ILLUSTRATED_EXTERIOR](../ILLUSTRATED_EXTERIOR.md), line 13, and the previously
reported PR #131 lifecycle wording in [terrain_c1](terrain_c1.md), line 37,
remain untouched. Broader pending labels in README and GAME_VISION are outside
this scope. No approved design or narrative canon is changed.

## Reverified production contract

Links below pin the reviewed main SHA, not a moving branch.

| Contract | Source |
| --- | --- |
| Exact material `M(cell)` is 0..4; center `(64x+32,64y+32)`; exclusions first; noise channels 8/9, scales 768/192, coefficient .18, threshold `<.64`; subtype channel 10 | [PlanetGenerator 137–150](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_generator.gd#L137-L150) |
| Signed seed/coordinate modulo 2147483647; floor and cubic lattice noise | [PlanetGenerator 43–62](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_generator.gd#L43-L62) |
| Gameplay interior or edge distance `<48`; direct anchor distance `<160`; computed authored `overlay_weight >0` at reach 48; full material skirts at reach 256 | [PlanetGenerator 83–112](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_generator.gd#L83-L112), [137–145](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_generator.gd#L137-L145) |
| Ordered authored polygons with feather 256, and direct `StaticBody2D` anchor positions | [PlanetExterior 69–79](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.gd#L69-L79) |
| Clearing, ImpactScar, NorthRidge, SouthShelf vertices | [scene 55–69](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.tscn#L55-L69) |
| CrashedShip `(-384,-192)`, Hatch `(-384,-176)`, WestRock `(-768,384)`, EastRock `(704,-384)` | [scene 96–98](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.tscn#L96-L98), [153–156](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.tscn#L153-L156), [185–199](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.tscn#L185-L199) |
| Six gameplay vertices | [CrashSiteProtection 6–8](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/crash_site_protection.gd#L6-L8) |
| Terrain/Ferrite size 64; construction size 32; 32×32 terrain cells per 2048-unit chunk; negative coordinates use floor | [WorldCoordinates 4–27](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/world_coordinates.gd#L4-L27) |

The [broad-phase bounds](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_generator.gd#L23-L31)
are an optimization, not Earth classification. Stage 1 publication/arrival
authority remains in
[PlanetExterior 253–287](https://github.com/interneth3ro/the-long-way-home/blob/1f083dae00245a0bd5a7ac8a0c59c8f66b1a5744/scenes/world/planet_exterior.gd#L253-L287).
Tint/overlay precedence, detail removal, Ferrite, construction, transition
readiness and state revision retain the separate contracts documented in Stage 2A.
No gameplay source, scenes, assets, runner or C1 experiment is modified.

## Necessary condition and evidence classes

Let `E` be the mandatory Earth set under the production predicates and
`B(cell)=int(M(cell)>0)`. If continuous `C` is zero throughout `E`, it is zero on
`closure(E)`: for any point in the closure, take a sequence from `E` converging
to it and apply continuity. Therefore `C(center)=1` at a Green center requires
that center to lie outside `closure(E)`. An open boundary is not an exemption.
This is a necessary-condition proof, not an implementation or acceptance of a
reconstruction algorithm. Positive clearance alone does not approve a fixed taper.

- **Conflict:** an independently established original Green center is in the
  closure, with no unresolved numerical evidence. Synthetic proof case: open
  radius-160 circle centered at `(192,32)` and canonical center `(32,32)`.
  The predicate is false at equality, but the clearance is zero. *Conditional on
  an original Green ID*, continuity is impossible. This is not production failure.
- **Insufficient margin:** certified positive clearance has upper bound smaller
  than a supplied proposed margin. This is a margin failure, not a contradiction.
- **Unresolved numeric case:** exposed endpoint band, model disagreement,
  insufficient numeric scope, or margin between the established bounds. Certification
  is withheld, even for an Earth-classified unresolved query.
- **Compatible within model/envelope:** all audited Green centers have certified
  positive clearance, sufficient for the optional margin. Earth records are
  reported separately; they are not silently converted from Green.

Original exact IDs and binary anchors are separate fields. Each `Anchor` records
seed, absolute cell, world center, original ID, binary anchor, nearest/responsible
primitive(s), computed predicate/reason, geometric rational distance bounds,
margin, numerical uncertainty, covered endpoint observations and outcome.
`Audit` adds the envelope, outside lower bound and aggregate outcome. Reports are
immutable Python values with canonical ordering; the reference has no output writer.

## Geometry and numerical model

The [reference](../../tests/terrain_stage2b_compatibility_reference.py) reads
geometry using the unchanged Stage 2A loader. Thirteen primitives retain source
order: gameplay offset, four circles, four authored 48-unit influences, four
256-unit skirts. Production predicates are evaluated using Stage 2A's actual
computed binary64 weight. They are not replaced by closed enlarged polygons.

Separately, exact rational geometry computes an ideal offset enclosure. The
distance to a circle's closure is `max(0, length(point-anchor)-160)`. For a filled
polygon and reach `r`, it is `max(0, distance(point,polygon)-r)`. Exact ray crossings
and zero segment distance decide inside/boundary; outside squared distance is the
minimum clamped segment projection distance. This covers concave vertices and
degenerate edges. Distance to the finite union is the minimum primitive distance.
Negative signed offsets indicate interior, but reported distance to the closure
is always nonnegative. All source coordinates and reaches are exact integers.

Square-root bounds use integer `isqrt` with denominator `10^12`: if squared
distance is `n/d`, `k=floor(sqrt(n*10^24/d))` gives `[k/10^12,(k+1)/10^12]`;
an exact square collapses the interval. Squared-bound tests prove enclosure.
These are arithmetic bounds, not a float tolerance or approximate signed distance.

An additional `0.0001` world-unit guard is applied on each side for numerical
certification. The reported interval remains the ideal geometric interval;
the effective interval is `[max(0,lower-.0001), upper+.0001]`.
This deliberately conservative **binary64 model budget** is distinct from Godot:
queries/vertices are restricted to absolute coordinates <=2048, reach <=256,
and every nonzero segment length >=1. Out-of-envelope queries are unresolved.
For these finite scales, binary64 unit roundoff is `2^-53`; subtraction,
dot products, clamped projection and distance evaluation have a conservative
absolute error budget below `10^-7` world units. Smoothstep's bounded operands
allow `32*2^-53` absolute weight error. Writing `s=1-d/r`, ideal endpoint weight
is `s²(3-2s) >= s²` for `0<=s<=1`, so cancellation can erase positive weight
within at most `256*sqrt(32*2^-53) < 0.000016` world units of an endpoint.
The .0001 guard exceeds both budgets. This is an explicitly stated arithmetic
model, not an IEEE emulation or a formal proof of Godot's implementation.

Any computed/ideal primitive disagreement or nearby endpoint is recorded.
Uncertainty at an internal boundary is resolved only when another primitive's
computed predicate is positive and its exact interior depth exceeds the guard:
an open neighborhood is then already in the union. The observation is retained
in `covered_endpoints`. Exposed feather boundaries remain unresolved; exact
strict circle/gameplay boundaries can supply conditional mathematical conflicts.
Tests demonstrate computed zero weight just inside an ideal feather. No uncertain
case relabels a Green center, expands production Earth or forces all-Earth output.

Material evidence uses unchanged Stage 2A classification, cross-checked for every
audited center/seed against the pre-existing ground-rejection model. Unexcluded
centers additionally use Stage 2A's independent rational noise/hash calculation;
their exact cover is more than `10^-10` from 16/25. Source hashes pin provenance.
These checks do not prove Godot Vector2/intermediate-rounding parity.

## Exhaustive envelope and findings

The source-derived union of all ideal offset bounding boxes is exactly
`[-1280,1280]²`. Canonical centers within this box have indices `[-20,19]²`.
Adding one complete center ring gives `[-21,20]²`: **1,764 centers**, queried
regardless of noise label. The production optimization rectangle is instead
`[-1281,1281]²`; the extra unit does not change the exclusion.

For any center outside the audited indices, at least one coordinate is <=-1376
or >=1376. Its axis distance from the exclusion box is >=96, hence its Euclidean
clearance is >=96 in exact geometry (95.9999 after the stated guard). This proves
no omitted canonical center can touch the ideal closure. The proof is geometric
and seed-independent; it does not evaluate all distant materials, establish
engine precision at arbitrary coordinates, or declare global runtime support.
An optional margin above that outside lower bound withholds certification unless
an audited Green center already establishes an insufficient-margin result.

All 1,441 centers inside the ideal union have a positive computed exclusion and
are Earth for all selected seeds. The other 323 have positive clearance; there
are **zero exposed boundary centers, zero actual Green conflicts and zero
unresolved union cases** in this model. Thus all geometrically hazardous centers
were examined, including those that no selected seed labels Green.

Four ImpactScar feather endpoints are covered, retained observations:

| Cell | Independent covering exclusion | Ideal interior depth (world units) |
| --- | --- | --- |
| `(-14,-18)` | NorthRidge skirt | 160 |
| `(-10,-16)` | NorthRidge skirt | 256 |
| `(-6,-13)` | NorthRidge skirt | >230.89 |
| `(-2,-10)` | Clearing skirt | 256 |

No fixed taper margin was requested. The following minima are across Green
centers in the complete bounded audit; each is smaller than the outside lower
bound. Decimal lower bounds below are rounded **down** after subtracting .0001.

| Seed | Green centers | Minimum cell / exact ID | Nearest primitive | Certified lower clearance | ID at `(16,1)` |
| --- | ---: | --- | --- | ---: | ---: |
| 26026 | 188 | `(9,-9)` / 3 | Clearing skirt | 1.380791048506 | 1 |
| 0 | 215 | `(-18,-8)` / 4 | ImpactScar skirt | 7.087980176648 | 0 |
| -42 | 142 | `(9,-9)` / 4 | Clearing skirt | 1.380791048506 | 4 |
| -1 | 114 | `(-16,8)` / 3 | Clearing skirt | 19.1999 | 0 |
| 2147483647 | 215 | `(-18,-8)` / 4 | ImpactScar skirt | 7.087980176648 | 0 |
| 2147483648 | 42 | `(-18,-6)` / 1 | Clearing skirt | 31.9999 | 0 |
| -2147483648 | 114 | `(-16,8)` / 3 | Clearing skirt | 19.1999 | 0 |

Seeds 0/2147483647 and -1/-2147483648 are modulus aliases. Additional tests check
plus/minus-modulus aliases for 26026 and -42 without treating them as new evidence.
Counts are audit observations cross-checked independently, not replacement goldens.

The smallest clearance among **all** 323 exterior candidates is at `(9,-9)`:
`sqrt(861184/13)-256` lies in `[1.380891048506,1.380891048507]`. This derives from
Clearing's `(192,-512)`–`(768,-128)` segment. The reported near-boundary probe
`(16,1)`, world center `(1056,96)`, has clearance `sqrt(2803712/41)-256` in
`[5.501853745236,5.501853745237]` to Clearing's `(768,-128)`–`(832,448)` segment.
Its production-model predicate is false for all exclusions. It is Green only for
26026 and -42 among these seeds; the investigation's unevaluated ID was not assumed.

## Validation, preservation and next decision

The focused suite covers independent segment, rectangle, circle and concave
polygon cases; overlaps, vertices, signed coordinates, strict boundaries,
conditional proof conflict, computed feather cancellation, exact interval proofs,
positive/insufficient/uncertain optional margins, exhaustive material cross-checks,
all frozen vectors, full reversed/shuffled queries, geometry reload and source/scope
guards. Insufficient-margin examples are synthetic/test inputs, not proposed
production constraints or permission to select a taper.

Run from repository root, with `-B` to avoid bytecode output:

```powershell
python -B -m unittest discover -s tests -p 'static_terrain_stage2b_compatibility_test.py' -v
python -B -m unittest discover -s tests -p 'static_terrain_stage2_coverage_test.py' -v
python -B -m unittest discover -s tests -p 'static_ground_rejection_test.py' -v
python -B -m unittest discover -s tests -p 'static_low_green_ground_test.py' -v
python -B -m unittest discover -s tests -p 'static_ground_publication_test.py' -v
python -B -m unittest discover -s tests -p 'static_transition_safety_test.py' -v
```

Actual command counts/timings and final HEAD belong in the draft PR; no duplicate
successful-run log is created. Static checks also cover diff whitespace, exact
four-file inventory, source identities, Markdown targets and preservation.
Initial checks matched all 15 protected untracked sidecars, original A1 branch,
three annotated A1/C1 tags, receipt identity, and backup size/SHA-256. Reading and
hashing that backup is not a new restore test or offsite-copy verification.
Final preservation is rechecked before publication; private paths are omitted.

No Godot/editor/headless/import/playable execution, engine verification, graphical
validation, shaders, benchmarks, assets, project executables, historical
FactoryGame access, merges or cleanup are part of this work. The guarantee is
mathematical geometry plus bounded Python evidence, not engine/runtime acceptance.
Stop on provenance/scope/preservation drift, unexplained disagreement, actual
Green conflict, unresolved certification or a failed proposed margin; do not
rebaseline, broaden Earth or relax constraints to obtain a passing report.

Risk is overreading model evidence as runtime parity or a taper recommendation.
Rollback is leaving this draft unmerged, or a separately reviewed revert after
an owner-authorized merge; no runtime data migration is involved. Recommended
next decision: owner review/acceptance of the compatibility model and bounds,
then separate authorization for a paired **offline** contour/distance versus
smooth-interpolation comparison. No renderer activation or Stage 3 work follows
automatically from this audit.
