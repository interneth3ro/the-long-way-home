# Stage 3A-2: bounded adaptive CPU protection prototype

**2026-11-03; feature branch, pending owner review/merge.**
**Recommendation: NOT VIABLE** for this single candidate as a simpler route to
the accepted continuous terrain presenter. This is a negative prototype result,
not evidence that all adaptive representations are incompatible. No optional
refinement was used: finer boundary boxes would grow the cover without resolving
its remaining production geometry obligation. No production integration follows.

## Candidate and declared model

The [isolated reference](../../tests/terrain_adaptive_cpu_reference.py) builds one
seed-independent quadtree cover of the original authored protection geometry.
It reads the existing scene as text through the unchanged Stage 2A parser. The
geometry digest remains
`5846d34ec602ba20d3a4f84c63c123b4cfd41104d4a943986df600174520b590`.
All original polygons, gameplay clearance (48), anchor disks (160), overlay
clearances (48) and skirts (256) remain inputs. No authored files change.

The mathematical target is the **closed ideal union K**, expanded by the prior
`1/10000` guard, using rational filled-polygon distance and the existing rational
sqrt enclosure. Closing the open production exclusion boundaries is conservative
in this model. The guard is **not a bound for Godot Geometry2D**. Exact geometry
membership, the frozen Python computed exclusion predicate, and Godot's actual
predicate remain distinct. Original IDs still come from the unchanged Python
classification reference, independently of binary reconstruction. They are
offline expectations, not newly executed production metadata.

For each square, evaluate distance to each primitive at its midpoint. The side
length bounds the Euclidean displacement from midpoint to any point in the box
via the L1 norm. The 1-Lipschitz distance bound certifies an OUTSIDE leaf if all
lower bounds are positive, or INSIDE if any upper bound is nonpositive. A cheap
exact primitive-AABB test can also certify separation; its sentinel values carry
only signs, not tight numerical interval endpoints. Other leaves are UNCERTAIN.
Subdivide uncertain leaves to side 8; refine further only when a leaf touches an
original lattice center outside the guarded union. Stop explicitly at depth 18,
20,000 visited nodes or 60 seconds. The tested minimum side was 1/2.

Retain **both INSIDE and UNCERTAIN closed boxes**. The cover is a finite union
`B` containing the entire guarded ideal union. Queries use
`g(p) = min(16, distance(p,B)^2 / 32)`, with exact squared AABB distances.
This is not interpolation of a sampled binary permission mask. Within B, g is
identically zero, including every unresolved leaf and every box boundary.

As in the accepted protection construction, smooth four-center weights interpolate
positive scales: Earth scale 16; original Green scale `min(16,g(center)/2)`.
Preparation/query rejects any Green center with zero g. Coverage is unchanged
Candidate A (`a=5/32`) times `smooth(clamp(g/interpolated_scale))`. IDs and signed
int64 seed identity are separate. No ID, center, seed, or parameter is repaired.

## Guarantees, independent checks and limits

In exact arithmetic, induction over the quadtree partition proves K is inside B:
an OUTSIDE leaf cannot intersect K; every other terminal leaf is retained. The
root is `[-2048,2048]^2`; all guarded primitive AABBs are strictly inside it.
Consequently coverage is exactly zero on K. At any original Green center with
positive box clearance, interpolation selects that center's scale, making the
protection factor and Candidate A exactly one. The query code returns rational
values; PNG conversion happens only after coverage evaluation.

Squared distance to a finite closed box union is continuous; the positive scale
interpolant and Candidate A are continuous across lattice boundaries. The cover
is shared in absolute coordinates, so chunk ownership introduces no separate
field. The 64-unit query index expands each box by 24: every box able to reduce
g below its cap has distance less than sqrt(512), which is less than 24. Omitting
other boxes cannot change the capped result. This also explains why changing
index buckets cannot create a mathematical seam. The index is derived storage,
not an additional permission classifier.

The [focused tests](../../tests/static_terrain_adaptive_cpu_test.py) independently
check OUTSIDE certificates without the AABB fast path, total partition area,
deterministic reconstruction of the cover, exact serialized round trips, indexed
versus full-list queries, original IDs and Green endpoints over seven historical
seeds, seed-independent unexcluded centers in `[-33,32]^2`, minimum-clearance
center `(608,-544)`, negative coordinates, chunk/lattice boundaries, explicit
outer center halos, unsupported inputs, and vertices/edge midpoints/cardinal
disk and feather boundaries with ±guard perturbations. These finite checks
support the implementation; they do not prove all Godot/GPU evaluated points.

Owned queries accept only world `[-32768,32768)` on each axis, corresponding to
owned chunks `[-16,15]^2`. Separate center support admits `[-32800,32800]` for
the four-center reconstruction at outer edges. Outside the localized box cover,
the index yields g=16 exactly. No full-world image or million-center traversal
was performed. Tests of halo behavior and domain rejection do not certify
float32 conversions, texture encoding, GPU filtering, retention or publication.

**Unresolved:** OUTSIDE certificates concern ideal rational geometry. They do
not enclose actual Godot polygon inclusion or its computed segment/distance
operations. Evaluating Godot at a box midpoint would not establish a certificate
for the whole box. A production version would still need a conservative CPU
geometry oracle plus numerical bounds on distance/scale encoding and GPU box
evaluation, including the tiny-center scale. These remain the central gate.
No Godot, asset import, shader compilation, graphics or gameplay was executed.

## Measured evidence and appearance

One fixed-seed (`26026`) diagnostic run used the initial candidate, bounded by
120 seconds and 512 MiB observed process memory, with checks every image row.
Preparation also checks its deadline/node budget at every subdivision. The
memory observation reuses the existing Windows process-memory helper; it reports
the greater of peak working set and current private usage, for the **whole Python
process**, including source hashing, baseline comparison and images. It is not
isolated cover allocation or an enforced OS memory quota. Inputs and preservation
identities were rehashed before/after; failures stop without automatic retries.

| Metric | Observed offline result |
|---|---:|
| Shared cover preparation | 5.3203 s |
| Complete diagnostics and fixed query pass | 25.6468 s |
| Whole-process memory observation | 181,755,904 bytes (173.34 MiB) |
| Visited nodes / leaves | 11,449 / 8,587 |
| Retained boxes / uncertain leaves | 5,676 / 2,927 |
| Canonical exact box JSON, excluding index/metadata | 168,900 bytes |
| Index buckets / references / maximum bucket | 1,635 / 24,491 / 110 |
| Additional cached-center query pass | 1,089 points in 1.03945 s (~0.955 ms/point) |
| Minimum-clearance center distance squared to B | 1/2, positive |

These are Python rational arithmetic measurements, not estimates of Godot chunk
preparation or GPU frame time. Preparation is global for the localized geometry,
not per chunk. The JSON is also shared, so comparing it directly to the 128 KiB
per-chunk payload target would be misleading. No runtime budget acceptance is
claimed. As a **storage estimate only**, four signed 16-bit half-unit box
coordinates would occupy 45,408 bytes before index and engine overhead; the
24,491 references alone would add 97,964 bytes as 32-bit integers. Neither
packing nor a production upload format was implemented or certified.

The four images contain accepted protected Candidate A / adaptive protected A /
absolute coverage difference, clearly labeled **OFFLINE CONDITIONAL PROTOTYPE**.
Original images were read/preserved, never regenerated. The baseline comparison
evaluates the unchanged accepted reference on the same points.

| Crop | Grid | Mean / max absolute difference | Protected samples, all zero |
|---|---|---|---:|
| Minimum clearance, `[604,-548,612,-540]` | 33×33 | 0.29315 / 1 | 331 |
| Crash site, `[480,-672,736,-416]` | 65×65 | 0.03525 / 1 | 3,341 |
| Natural, `[2496,2496,3008,2752]` | 65×33 | 0 / 0 | 0 |
| Negative/zero seam, `[-64,-1344,64,-1216]` | 33×33 | 0 / 0 | 528 |

Visual inspection confirms a coarse stair-step boundary and substantial removal
of accepted near-crash-site Green coverage. Natural transitions outside protection
match exactly on this grid. The seam crop has no sampled Green coverage, so its
zero difference is weak visual evidence; seam assurance rests on the shared-field
argument and independent indexed/full-list tests. No owner artistic acceptance
or engine screenshot is implied. A zero sample difference is not a continuous
equality proof. The 4,200 protected diagnostic samples passed; no endpoint or
protection failure was silently clamped or relaxed.

## Reproduction, preservation and decision

Commands from the checkout, using Python only:

```powershell
python -B -m unittest discover -s tests -p static_terrain_adaptive_cpu_test.py -v
python -B tools/terrain-adaptive-cpu-diagnostics.py --generate
python -B -m unittest discover -s tests -p 'static_*test.py'
git diff --check
```

The initial seven focused tests passed in 29.109 seconds before diagnostics.
The complete Python static suite passed **361 tests in 287.571 seconds**,
including the final nine focused tests (two additional scope/seed-independent
center tests). Changed local Markdown links, new Python syntax/whitespace and
`git diff --check` passed. These are offline/static checks only. The diagnostic command
was invoked exactly once; it creates a fresh ignored directory, never overwrites
an earlier run. No new runner or third-party package was introduced. Existing
non-engine PNG/label/memory helpers are reused without invoking their entrypoints.

Local output is
`artifacts/tmp/adaptive-cpu-1c4ee892573242e1818fdd2ff3eb866e/`:
`minimum-clearance.png`, `crash-site.png`, `natural.png`, `seam-patches.png`,
`boxes.json`, and `manifest.json`. The manifest records grids, hashes, full
tracked-source identities and measured costs. Outputs remain ignored and local;
no permanent image publication or cleanup is performed. Diagnostics used the
initial source snapshot; subsequent changes add validation/documentation only,
with no candidate refinement. Use the manifest hashes for exact provenance.

Preflight verified local/live GitHub `main` and origin tracking at
`ee937c98aa5e5bcb087f99c5b0eb8c8960ecf4f0`, clean tracked/index state and the exact
15 exterior-sidecar untracked exception. Local Git transport could not resolve
GitHub in the sandbox; the connected GitHub commit endpoint verified live main.
Sidecars, A1 branch, three annotated tag types/targets, backup bundle size/hash,
frozen C1 source PNGs and seven original plus three refined diagnostic outputs
matched their receipts. Original/refined manifest hashes respectively:
`a24340c1b006283270d04c7c43aa1fe4b1b1ca85019b43af2fd56817107ac2f7` and
`332fa252dca79d2112dc071831c28e86f28bd3d88c0470e292335620180e8063`.
The diagnostic run repeated those preservation checks. Private backup paths and
raw receipt content are not published. The PR #139 inventory guard now checks
its immutable merged endpoint; this candidate's test checks the exact new delta.
Historical assertions, math, goldens and all production bytes remain intact.

**Does this materially shorten the path? No demonstrated shortening.** The box
math is simple, but preparation still needs the missing whole-region production
geometry enclosure. The retained cover introduces thousands of boxes, a query
index, small positive scale obligations and visibly worse protection transitions.
The tested candidate therefore does not justify proceeding to a certification
implementation. No further architecture or tuning is attempted. If the owner
chooses to revisit CPU protection, the decision needed first is whether there is
a bounded, credible way to certify a complete CPU OUTSIDE box against actual
Godot geometry; midpoint samples alone are insufficient. Alternatively the owner
may separately authorize a non-production visual laboratory. Neither next step,
engine execution, Stage 3B integration, merge nor cleanup is authorized here.
