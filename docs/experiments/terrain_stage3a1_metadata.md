# Stage 3A-1: isolated metadata and conditional numerical contract

Feature branch, pending review/merge. Governed by the supplied
[11 approved decisions](terrain_stage3_architecture_decisions.md).
**Stage 3A-2 certification remains blocked/unproven.** No renderer, shader,
production wiring, runtime enclosure, or performance acceptance is supplied.

## Implemented isolated interface

[`ContinuousTerrainMetadata.prepare`](../../scenes/world/continuous_terrain_metadata.gd)
accepts `(seed, chunk, overlays, protected, anchors)` as Variants to prevent
implicit numeric coercion. Seed must be a Godot signed int64; chunk must be
Vector2i. Inputs must come from the same authored context used by
[`PlanetGenerator`](../../scenes/world/planet_generator.gd).
Overlays are an Array of dictionaries with finite PackedVector2Array polygons
(at least three vertices) and finite strictly positive numeric feathers.
Protected polygon has at least three finite vertices; anchors is a finite
PackedVector2Array, possibly empty. Extra overlay fields are retained.
These are structural checks, **not** polygon topology or numerical certification.
Only the existing reviewed production geometry is a certification candidate;
arbitrary custom geometry is not claimed supported by the numerical contract.

Preparation copies the geometry, constructs the unchanged production generator,
and calls its `sample_ground_material` once per absolute halo cell. It does not
reimplement classification, normalize/absolute-value the seed, or accept a
substitute classifier. Generator-owned signed-seed modulo semantics remain
authoritative. There is no dependency on world state, artwork, or a presenter.
The synchronous function is isolated preparation only; it is not a frame-budgeted
job and must not be wired into production before later authorized lifecycle work.

Success dictionary: `ok=true`, `schema=1`, original `seed`, `chunk`, `materials`
(PackedByteArray), copied `geometry` (overlays/protected/anchors), and
`runtime_certified=false`. Failure dictionary contains only `ok=false` and an
`error`: seed_type, chunk_type, unsupported_chunk, unsupported_grid,
geometry_points, overlays_type, overlay_type, overlay_polygon, overlay_feather,
or material_range. No partial payload is returned. Failure must remain failure;
callers must not reinterpret it as Earth or switch renderers. Runtime exceptions
and allocation failures are not claimed recoverable by this isolated function.

Identity is `(schema, original signed seed, absolute chunk, full authored geometry,
production classifier revision)`. The caller must retain the last two context
identities; seed/chunk alone is not a cache key. No cache/digest/persistence is
implemented. The returned geometry is a context snapshot, not a certified
protection field. Results are mutable Godot containers and must be treated as
read-only by future consumers; mutation invalidates the result.

## Layout, ownership, support and encoding

- World cells are 64 units; chunks own 32×32 cells / 2048×2048 units.
- Owned chunks are `[-16,15]²`, world `[-32768,32768)²`. Validate the owner
  **before** calculating halo cells. Owners outside the envelope fail; never
  clamp or wrap. This is a study envelope, not a permanent gameplay world limit.
- Each chunk stores local cells `-1..32` on both axes. Absolute cell is
  `32*chunk + local`; center is `64*cell+32`. Row-major byte index is
  `(local_y+1)*34 + local_x+1`, x fastest. Exactly 1156 unsigned bytes.
- IDs remain `0=Earth`, `1..4=Green subtypes`. No binary reduction is stored.
  Adjacent chunks share two columns/rows (68 samples), diagonal neighbors four.
  All occurrences must classify the same absolute cell in the same context.
- Floor ownership follows [WorldCoordinates](../../scenes/world/world_coordinates.gd).
  For example cell -1 belongs to chunk -1, local 31; world -0.25 belongs to
  cell -1. Integer truncation toward zero is not acceptable.
- Outer support reaches absolute cells `[-513,512]²`, centers
  `[-32800,32800]²`. These are halo samples, not additional owned chunks.
  Candidate A on the closed chunk rectangle needs only this halo. Added gutters,
  pixel footprints or another kernel require a separate support analysis.
- Every retained **owned** chunk must be in range. Halo sampling must not require
  retaining an out-of-range neighbor chunk. Later scheduler retention crossing
  the envelope must fail explicitly; this PR implements no scheduling policy.

CPU integers preserve cell identity within this range; centers are exact integer
multiples plus 32. That does not certify subsequent float transforms. Intended
GPU ID encoding is lossless integer texels 0..4, exact integer fetch, no sRGB,
compression, interpolation or mipmaps. A backend-specific format/upload/fetch
implementation is deliberately absent and must be certified in 3A-2. Raw byte
payload is 1156 bytes; dictionary/geometry/engine overhead is not measured.
No clearance, margin or protection-scale floats are emitted: their precision,
rounding directions and encoding remain gated on an actual enclosure proof.

## Conditional Candidate A and protection contract

For evaluated world point p, let `q=floor((p-32)/64)` componentwise and
`t=(p-(64*q+32))/64`. At q, q+(1,0), q+(0,1), q+(1,1), derive binary indicators
`b=1 iff material>0` without discarding the original IDs. With
`S(z)=z*z*(3-2*z)`, `u=S(t.x)`, `v=S(t.y)`, define

```
f = ((1-u)*b00 + u*b10)*(1-v) + ((1-u)*b01 + u*b11)*v
A = S(clamp((f - 5/32)/(11/16), 0, 1))
coverage = A * P
```

P is a future certified continuous protection factor in [0,1], not a mask or
distance supplied here. Exact pointwise endpoints are mandatory: coverage zero
at every production mandatory-Earth excluded position, and one at every original
Green center. At Earth centers Candidate A itself is zero. No coverage mipmaps,
post-blend blur, tolerance-relaxed endpoints or sampling-only proof is accepted.
Artwork filtering and raster/pixel footprint appearance are separate questions.

The authoritative exclusions are the generator's actual operations: gameplay
polygon membership or edge distance <48; anchor distance <160; authored polygon
membership/recovery weight >0 with clearance 48; and every overlay's full feather
weight >0. `_overlay_weight` uses polygon inclusion then
`1-smoothstep(0, feather, edge_distance)`. Production's bounding-rectangle shortcut
also needs certification; ideal distance predicates cannot silently replace
these floating operations or their boundary semantics.

The [Stage 2B-2 reference](../../tests/terrain_stage2b2_reconstruction_reference.py)
and [proof report](terrain_stage2b2_reconstruction.md) establish conditional
offline Python properties. Its epsilon=1/10000 is **not a Godot/GPU bound**.
Its exact-rational projection, squared-distance surrogate and Green-center scales
are evidence for a possible approach, not runtime code to port by default.
No numerical error budget is asserted here. In particular, classification
identity, Python-model proofs, metadata layout invariants and runtime/GPU
correctness are four distinct claims; only the first is preserved by delegating
to the original source, and its actual new call path still requires engine tests.

## Concrete mandatory Stage 3A-2 certification plan (not authorized here)

1. Freeze exact production geometry, generator source, seed domain, Godot build,
   scalar/Vector2 precision, GPU backend and shader compilation semantics. Obtain
   separate execution authorization. Compare the actual isolated call path to
   the production classifier and existing vectors, including signed int64 ends,
   negative ownership, all envelope corners and overlapping halos. Golden
   agreement is a regression check, not the numerical proof.
2. Establish a conservative one-sided enclosure for the actual Geometry2D
   point-in-polygon and closest-segment operations, degenerate edges, endpoint
   selection, Vector2 rounding, distance/sqrt, bounds construction/growth/merge
   and Rect2 containment. Include division, smoothstep saturation/subtraction
   and the >0 predicate at full feathers. Analyze all evaluated positions in
   the envelope and halo support, not only diagnostic samples.
3. Certify positive Green-center clearance lower bounds, their conversion and
   encoding. Prove that any chosen protection scales retain positivity and
   permit exact saturation to one at original Green centers while remaining
   zero over the entire production excluded set. Seed-dependent Green sets must
   be covered for the supported seed domain, or rejected explicitly in a later
   approved contract; do not silently restrict seeds to fixture seeds.
4. Choose actual integer texture and numeric protection formats. Bound CPU to
   GPU conversion, upload, shader coordinate transforms/rebasing, floor at
   negative boundaries, texel addressing, interpolation evaluation, division,
   min/max/clamp, multiplication, contraction/FMA and backend precision. Include
   composition of protection with Candidate A and demonstrate exact 0/1, with
   strictly positive certified margins. Reject unsupported backend/envelope or
   nonfinite results; never mark uncertified data publishable.
5. Validate retention and halos independently of ownership; run separately
   authorized engine/GPU adversarial checks as corroboration of the rigorous
   enclosure. Record proof assumptions and failure evidence. If certification
   cannot be established, stop for a separate owner decision on adaptive CPU
   protection. No presenter integration precedes this gate.

## Validation and preservation scope

Focused command: `python -B -m unittest discover -s tests -p static_terrain_stage3a1_metadata_test.py -v`.
Tests inspect delegation, strict input checks and layout expressions without
executing GDScript; independently enumerate all 1024 owned-chunk layouts and
support bounds; verify overlap, negative ownership, original offline ID/subtype
goldens, signed-seed model identity and the exact historical guard amendment.
Malformed input checks are **source checks**, not exercised engine branches.
GDScript parsing/type checking, runtime allocation, actual classifier parity,
Geometry2D, encoding, GPU, gameplay, graphics and performance remain untested.

Validation on 2026-11-03: the focused command passed 8 tests in 0.200 seconds.
From `tests/`, the following command passed 3 historical checks in 0.258 seconds:

```text
python -B -m unittest -v static_terrain_stage2b2_reconstruction_test.ReconstructionTest.test_manifest_bounds_and_scope_preservation static_terrain_stage2b2_reconstruction_test.ReconstructionTest.test_exact_historical_amendment static_terrain_stage2_coverage_test.Stage2ClassificationTest.test_independent_goldens_exact_ids_and_provenance
```

The final focused rerun passed 8 tests in 0.197 seconds. Local Markdown target
checks and byte equality against the supplied architecture record passed.
`git diff --cached --check` reports the supplied record's four intentional
Markdown hard-break trailing spaces (lines 3-6), preserved verbatim. All other
files pass the normal whitespace check; the record passes with only
`blank-at-eol` disabled for that one command. No repository rule is relaxed.
These results are non-engine evidence only.

The Stage 2B-2 scope guard admits exactly the four new files; its historical
mathematics, original fixture assertions, source pins and sidecar checks remain.
No source artwork, goldens, diagnostic output or historical lifecycle labels are
rewritten. The supplied decision record is copied verbatim (Git may normalize
line endings). Documentation-sync found no production behavior change requiring
updates to README, Game Vision or existing presenter documentation.

Preflight verified clean tracked state and local/remote main at
`b4abb3ac8d78d5833b232061642297434ec5abc6`; exact 15 untracked sidecar paths/hashes;
A1 preservation branch; all three annotated tag object IDs and commit targets;
backup bundle size/SHA-256; frozen C1 source PNG hashes. Original and readable
Stage 2B-2 diagnostic manifests were read, all seven original and three refined
output sizes/hashes checked, and original manifest/output hashes compared with
the refinement receipt. No recovery clone, regeneration or engine was run.
Stage 2A/2B tracked references/fixtures remain unchanged; no additional separate
Stage 2A/2B local diagnostic manifest was discovered in the stage2 output paths.

Rollback is to omit/revert this isolated addition and its exact guard extension;
production behavior is unchanged. Preserve the approved architecture record
unless the owner separately revises it. No merge, follow-on PR or cleanup is
part of this task.

## Stage 3A-2 fixed smoke recipe (draft, one-time execution failed)

The feature branch adds one `MetadataSmoke` recipe to the existing supervised
local runner. Its metadata-only review controls leave Native's recipe-switching
behavior unchanged. One separately owner-authorized invocation ran at activation
revision `4f1dcaf8d565d657d354f8ba672fa6ed681fa072` on 2026-11-03. The complete
Python suite passed 350 tests in 249.088 seconds and headless preparation passed.
The smoke command failed to parse `tests/metadata_smoke_test.gd:43` because the
`seed` variable's type could not be inferred. Actual metadata generation and
malformed-input rejection were NOT REACHED. No fix or retry was attempted; the
one-time authorization is consumed and the inactive gate is restored. Any further
execution requires renewed explicit owner authorization.

The [exact staging/commands and owner execution checklist](../LOCAL_TESTING.md#fixed-metadata-smoke-extension-draft-one-time-execution-failed)
freeze an asset-free 32-file dependency closure: complete production scripts/types,
a texture-free resource, existing goldens, UID inputs, minimal project template
and a production-authored geometry snapshot. Static drift checks compare the
snapshot to scene/source text. Production methods, geometry, classifiers and
fixture goldens are unchanged. World state is a parsing dependency through the
generator's type signatures; it is never instantiated by the smoke script.

Planned assertions exercise actual builder calls, signed int64 identities,
row-major 34×34 byte IDs, direct classifier parity, halo overlap, negative
ownership, envelope edges, deterministic repetition, copied geometry, explicit
uncertified state and representative invalid-input rejection without partial
payloads. Static checks and inert fixtures validate source/inventory/dispatch
contracts only. They cannot establish engine parsing or runtime parity.
Strict-Earth, Green-center margins and numerical enclosure remain unproven;
Stage 3B remains blocked. A later separately approved smoke PASS would be a
runtime regression milestone, not Stage 3A-2 numerical certification.

The [one-time execution record](../LOCAL_TESTING.md#one-time-metadata-execution-result-2026-11-03)
records the exact invocation, failure, retained stage/evidence and post-run
preservation results. Preparation PASS does not establish successful parsing or
execution of the metadata builder. This failure adds no runtime parity,
malformed-input, numerical or production-integration acceptance.
