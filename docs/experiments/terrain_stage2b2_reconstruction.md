# Stage 2B-2: paired offline reconstruction

Status: offline implementation and bounded diagnostics complete, pending owner
review. No artistic or production acceptance is implied. Baseline is PR #135 merge
`1f4ac408c31b99be4ab7158960dab06adec93871`. Production remains unchanged.

## Numerical contract and one-sided enclosure

`K` is the closed ideal union defined by the unchanged Stage 2B-1 primitives.
`E_Python` uses the unchanged Stage 2A computed predicates. `E_Godot` is not
certified. Query coordinates are finite binary64 values in `[-2^21,2^21]^2`;
integer center coordinates are formed before conversion. This is an offline
arithmetic ceiling, not a production coordinate contract. Squared distances
and dot products have squared-unit dimensions, not world-coordinate units.

Assumptions: CPython 3.14.7, IEEE binary64, round-to-nearest/ties-to-even,
ordinary gradual underflow, and the upstream CPython norm implementation's
under-one-ulp accuracy contract. No code changes the arithmetic environment.
These are explicit platform assumptions, not an attestation of engine parity.
The inspected local executable metadata reports 3.14.7. Upstream
[mathmodule.c](https://github.com/python/cpython/blob/v3.14.7/Modules/mathmodule.c)
uses rounded coordinate differences and the shared `vector_norm` for `dist`
and `hypot`; [Python documentation](https://docs.python.org/3/library/math.html#math.hypot)
states the norm accuracy. Tests must verify the supported runtime and source
geometry before using this contract; another runtime requires renewed analysis.

All current polygon coordinates are integers of magnitude at most 1024.
Differences of vertices are exact integers of magnitude at most 2048; nonzero
vertical differences have magnitude at least 1. Circle anchors obey the same
coordinate bound. Reaches are exactly 48, 160 and 256. Finite intermediates in
the classifier neither overflow nor approach an underflow-sensitive threshold.

The following deliberately loose absolute bounds apply to every query in the
domain, not just sampled points. Let `u=2^-53`.

1. **Segment reconstruction:** the computed projection is clamped to `[0,1]`.
   Whatever its projection error, the exact point `a+t*(b-a)` belongs to the
   segment. Multiplication and addition reconstruct it with error less than
   `2^-40` per coordinate (product magnitude <=2048, sum bounded by 1024 plus
   product rounding). Thus no accuracy assumption about the projection itself
   is needed for a lower distance bound.
2. **Norm:** subtracting a reconstructed coordinate from a query has error at
   most `2^-32` per coordinate. The norm is below `2^22`, hence its one-ulp
   error is at most `2^-31`. By the norm's Lipschitz property the total distance
   underestimation is less than `sqrt(2)*(2^-40+2^-32)+2^-31 < 10^-8`.
   Taking a minimum of finitely many segment distances preserves this bound.
   Anchor circles use the same argument without reconstruction error.
3. **Polygon inclusion:** the vertical straddle comparisons are exact for the
   supplied binary64 point and integer vertices. A straddling edge has
   `|y-a.y|<=2048`. Subtraction error <=`2^-42`, multiplication error <=`2^-31`,
   propagation of subtraction error <=`2^-31`, division by an integer of
   magnitude >=1 and final addition together contribute less than `2^-30`.
   Consequently crossing-x error is below `2^-28 < 10^-8`. If parity differs,
   at least one comparison differs, placing the query within `10^-8` of an
   actual segment. The preliminary computed-zero-distance inclusion is covered
   by the segment bound. These possible false positives are already inside the
   ideal positive-reach offset.
4. **Feather:** outside polygon inclusion, positive weight requires clamped
   `t<1`: at `t=1`, `1-t*t*(3-2*t)` is exactly zero. Correct rounding of division
   cannot map a real quotient >=1 below 1. Hence positive weight implies
   computed distance < reach. Cancellation-induced false negatives do not
   enlarge the excluded set. The exact cancellation boundary is unnecessary.

It follows conditionally on the stated arithmetic contract that
`E_Python intersect D` is contained in `K_delta`, with `delta=10^-8`.
Choose the larger coverage-policy enclosure `epsilon=1/10000`; this is newly
derived from the one-sided argument, not inherited from a pointwise audit.
It never changes classification or the mandatory predicates. `K_epsilon`
contains the closure of the modeled excluded points as well.

## Continuous protection and exact numerical evaluation

Use the amendment's permitted conservative alternative to square-root distance,
so protection evaluation itself can be exact rational arithmetic. This is a
shared protection function, not a third terrain reconstruction family.
For primitive j with enlarged radius `r'=r+epsilon`, let `Q_j(p)` be exact
squared distance to its filled polygon, or to its circle center. Define

```
g_j(p) = min(16, max(0, (Q_j(p)-r'^2)/(2*r'+16)))
g(p) = min_j g_j(p)
S(z) = z*z*(3-2*z)
A(p) = S(clamp(g(p)/T(p), 0, 1))
```

Squared distance to a closed filled polygon is continuous, including concave
corners. All min/max operations are finite and continuous. If d is distance
outside the enlarged primitive, the unclipped expression is
`d*(2*r'+d)/(2*r'+16)`. For `0<=d<=16` it is between `(6/7)*d` and d;
for `d>=16`, g_j=16. Thus g is a continuous conservative lower surrogate for
distance to `K_epsilon`, zero throughout that union and saturated at 16 when
distance to the union is >=16. Its profile differs slightly from a distance
taper; both candidates use exactly the same profile.

At every Green center obtain a new rational lower bound `L_i` on distance to
`K_epsilon`, using exact squared geometry and integer square-root intervals.
Reject `L_i<=0`. Set `t_i=min(16,L_i/2)`; Earth scales are 16. Interpolate these
positive scales using exact four-center smooth weights. At a Green center with
actual enlarged clearance d<16, g >=(6/7)*d >=L_i/2; for d>=16, g=16>=t_i.
Therefore A=1 at every certified Green center. The candidate's exact binary
anchors then give `C(center)=B(cell)`; A=0 throughout `E_Python`.

The interval square-root routine supplies center constants only. It is NOT
used as a spatial field. For each supplied binary64 query, Fraction conversion,
polygon inclusion, projection, squared distances, g, T and S are exact rational
operations. Only final conversion of A to binary64 rounds; exact zero and one
remain exact. This separates analytic continuity from discrete computer output.
No texture sampling, mipmap or engine guarantee follows. Rational evaluation
cost remains unmeasured and must fit the original diagnostic budgets.

## Separate protection and diagnostic domains

The primitive bounds give `K subset [-1280,1280]^2`. Since T<=16 and g saturates
at 16, A is identically one outside `[-1296-epsilon,1296+epsilon]^2`, including
its boundary. This permits an exact shortcut without a hard-mask discontinuity.
Centers outside the old audited cell box `[-21,20]^2` have ideal clearance >=96;
their new lower bound is `96-epsilon` and their scale is exactly 16. No call to
the old compatibility oracle outside its numeric envelope is needed.

The [immutable case manifest](../../tests/fixtures/terrain_stage2b2_cases.json)
freezes 58 cases, sample grids, one-unit gutters, seeds, and source halos. Samples
include both rectangle endpoints; the overview therefore includes the closure
of the required half-open crash rectangle. Image scales .5/1/1.5 are nearest
offline rescalings of that same sampled grid, not world-pixel or Godot zoom tests.
Sub-unit minimum-clearance crops use 0.25-world-unit sample spacing. Overview
and long strips are deliberately coarse; they cannot certify fine visual detail.

For a closed query axis [L,U] expanded by gutter g, A needs center indices
`floor((L-g-32)/64)` through `floor((U+g-32)/64)+1`. B searches every square
whose closed box intersects [L-g-w,U+g+w]: indices
`ceil((L-g-w-96)/64)` through `floor((U+g+w-32)/64)`, plus corner centers.
This includes relevant segments outside the containing square. The point search
uses the same derivation with zero gutter; it never traverses a global contour.
All resulting source centers must satisfy the coordinate ceiling.

## Paired reconstruction

A uses four-center cubic weights S(t)=t*t*(3-2*t), both unremapped and remapped
with a=5/32. Derivatives S'(0)=S'(1)=0 make the analytic interpolant C1 across
square edges; symmetric sharpening is C1 too. All coefficients are convex and
centers remain exact. Checkerboard centers stay at .5; no connectivity choice
is introduced. Its support is four canonical centers.

B uses the original midpoint table, NW/NE/SE/SW bits 1/2/4/8. Ties use the low
bit of SHA-256 over exact UTF-8 `midpoint-tie-v1|seed_mod|qx|qy` (decimal signed
square coordinates, nonnegative seed modulo 2147483647, no whitespace/newline).
Low bit zero chooses N-E/S-W, one chooses N-W/E-S. Independent frozen digests
were calculated using .NET SHA-256. Sign is the left edge corner bit (NW above
midpoint, SW below) toggled by horizontal segment crossings with half-open y
ownership. This gives the specified isolated triangles and complementary signs.
Adjacent squares share midpoint endpoints and edge signs, so the assembled
contour and signed-distance reconstruction are continuous. Distance itself need
not be differentiable at corners or medial axes; B is not claimed C1 everywhere.

All segments lie in their square. For an incident center the closest possible
segment is a corner diagonal, distance 16*sqrt(2); straight midlines are 32 away.
A nonincident square is at least 64 away in one axis. Thus w=16 saturates every
canonical anchor. Searches are clipped at distance 16; beyond that the value
is already exactly 0/1. Square-root rounding affects only transition values,
not saturated anchors or exact contour zeros. Fraction geometry and convex
clamping bound numerical values to [0,1]. Shared rational protection makes
computed strict-Earth outputs exactly zero and Green anchors exactly one.

The optional 16-wide pair is not implemented. A a=5/32 and B w=16 have equal
32-world-unit full transition width only for straight axis-aligned reference
edges. No universal Euclidean-width equality is claimed.

## Validation and owner review

The initial six protection tests passed before paired implementation. The full
gate subsequently passed 70 tests: 14 new reconstruction/protection, 11 Stage 2A,
16 Stage 2B-1, 5 ground rejection, 4 low Green, 10 publication and 10 transition.
Tests
cover every audited Green center for all seven seeds, original 14 vectors,
all patterns/ties, table edge incidence, complement, anchor distance, straight
widths, signed seams, reload/order/alias identity, locality and exact inventory.
Existing Stage 2A, Stage 2B-1, rejection, low Green, publication and transition
suites are required by the explicit generator gate. No test success authorizes
engine execution. The compatibility test's only amendment freezes historical
inventory at PR #135; the new suite takes current-tree/untracked scope ownership.

The [generator](../../tools/terrain-stage2b2-diagnostics.py) requires explicit
`python -B tools/terrain-stage2b2-diagnostics.py --generate`. It runs the gate
before creating a fresh ignored folder, refuses overwrite, rehashes inputs and
enforces the original limits. A watchdog terminates at 120 seconds, without
retry. Peak working set/private memory are observed at each sample row and major
allocation; image dimensions and sample counts bound intermediate allocations.
Outputs have grayscale coverage and separately sampled grayscale overlays:
strict computed exclusion edge 96, pre-protection .5 contour 160, final .5
contour 224, exact sampled canonical centers 255. Coarse grids can miss a line
or center; overlays are explanatory samples, not geometric/filtered guarantees.

Preservation at start: 15 sidecars, A1 branch, three annotated tags and backup
bundle size/hash matched the existing receipt. No historical material is changed.
Documentation-sync reviewed README, GAME_VISION and related experiment reports.
Their historical pending lifecycle labels remain untouched; this offline-only
comparison changes no production behavior or narrative canon.

Owner visual review must compare organic continuity, grid rhythm, diagonal
wallpaper, scallops, diamond islands, checkerboard joins, narrow Green features,
crash Earth readability, seams and scale readability. Both candidates may fail.
The generated pattern sheet exposes A's curved corner response and B's straight
midpoint segments/checkerboard routing. The minimum-clearance crops show the
shared narrow protection transition. Small coarse overview panels cannot settle
fine organic quality, narrow-feature readability or grid-rhythm acceptance.
No artistic winner is selected. Rollback is leaving
the draft unmerged, or a separately reviewed revert; there is no runtime migration.

Neither enclosure certification nor runtime assumptions alone authorize generation.
The original six-file scope, preservation requirements, test gate and diagnostic
limits remain in force. No Godot, Native runner, FactoryGame access, merge or
cleanup is authorized.

## Actual bounded run and evidence location

The explicit generator command above completed once, without retries, after all
seven gate suites passed. The initial proof command was
`python -B -m unittest discover -s tests -p static_terrain_stage2b2_reconstruction_test.py -v`
(six tests at that checkpoint). Gate suites are selected explicitly by filename
in the generator; the full Native/static runner is never invoked.

Local ignored output directory: `artifacts/tmp/stage2b2-20261103-132958/`.
Its `manifest.json` records exact grids, geometry identity, source hashes,
per-suite counts, filenames, image hashes and the uncommitted source snapshot
against baseline HEAD. It is local diagnostic provenance, not publication evidence.
No generated output is included in the PR.

The run produced one contact sheet and six stress sheets, 89,550 candidate
evaluations, 193,194 total bytes including provenance, 68.31 seconds including
the gate, and 54,132,736 bytes peak observed working/private memory. Largest
image: 1536x1300. All samples are dyadic coordinates exactly representable in
binary64. The named grayscale levels are diagnostic overlays, not art.

Read each row as three consecutive groups: unremapped control, sharpened A,
then B. Each group contains clean/overlay pairs at .5, 1 and 1.5 offline image
scale. Grid resolution is unchanged between candidates and display scales.
Use the contact sheet for pattern behavior, minima for sub-unit protection,
probes/outside for production labels, and seams for signed absolute identities.
These are small diagnostic panels; enlargement cannot recover unsampled detail.
