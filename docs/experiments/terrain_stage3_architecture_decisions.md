# TLWH — Stage 3 Architecture Decision Record

**Status:** Owner approved, 11/11 decisions, 2026-11-03  
**Project:** The Long Way Home, Godot 4.7  
**Repository:** `interneth3ro/the-long-way-home`  
**Basis:** Stage 3 read-only investigation of `main` at `b4abb3ac8d78d5833b232061642297434ec5abc6` (PR #137 merged), followed by explicit owner decisions.  
**Important:** This is an architectural authorization record, **not** a claim that runtime/GPU correctness, performance, or artistic acceptance has been demonstrated.

## Objective and existing baseline

Evaluate an opt-in continuous painterly ground renderer while retaining the existing illustrated TileSet renderer as the production default. Preserve the original seeded classification and mandatory-Earth exclusion semantics, existing crash-site tint/overlay precedence, streaming/publication/arrival guarantees, and unrelated gameplay systems.

Stage 2B-2 selected **Candidate A**, sharpened smooth four-center lattice interpolation with `a=5/32`, as a **provisional reconstruction baseline**. Candidate B (`w=16` midpoint-contour signed-distance) remains comparison/fallback evidence. Python-model proofs and diagnostics are not Godot/GPU parity evidence. Frozen C1 Earth/Green source artwork is to be evaluated before artistic changes.

## Owner-approved decisions

The original decisions below are retained as history. The dated Stage 3B
amendment below supersedes only their continuous visual protection requirement
and its geometry-enclosure prerequisite; consult it before applying items 1–3
or the original stage boundaries.

1. **Runtime strategy — Option A.** CPU-authoritative original material IDs and protection metadata; GPU evaluates Candidate A interpolation. Do not duplicate authoritative classification on GPU. This is the intended architecture, not yet an implemented or certified renderer.
2. **Numerical protection — Option A.** Require a defensible conservative runtime numerical enclosure and positive certified Green-center margins **before renderer integration**. Strict Earth must remain zero; original Green centers must remain one. If certification fails, stop and seek a separate owner decision on an adaptive CPU mask. Never rebrand Python `epsilon=1/10000` as a Godot/GPU bound.
3. **Sampling semantics — Option A.** Require exact **pointwise** coverage endpoints at evaluated positions; no coverage mipmaps or post-blend coverage blur. Evaluate pixel footprints, filtering, and raster appearance separately. Artwork filtering is distinct from authoritative coverage.
4. **Green subtypes — Option A.** Preserve original material IDs `0=Earth`, `1–4=Green subtypes` exactly in CPU data and diagnostics. Initially render all Green subtypes with the same frozen C1 Green artwork; defer subtype-specific art.
5. **Lifecycle boundary — Option A.** Add a sibling continuous presenter through narrow dispatch in existing `PlanetExterior`; do not replace the world manager or introduce a generalized renderer framework. Existing chunk scheduling, attachment, revision, cancellation and arrival authority remain. Continuous mode must **not** inherit the legacy non-illustrated ground-publication exemption. Incremental work must remain unfinished until live publication succeeds.
6. **Failure and rollback — Option A.** Latch failures and fail closed; no automatic mode switching or per-chunk mixed-renderer fallback. Recovery is through a fresh illustrated exterior/playthrough, with existing transition safety intact.
7. **Preparation and caching — Option A.** Initially one incremental preparation job, bounded frame slices, bounded in-memory cache tied to retained chunks, main-thread attachment/publication, required chunks prioritized. No initial worker threads, disk cache, or aggressive precomputation.
8. **Coordinate study envelope — Option A.** Initially certify owned chunks `[-16,15]` per axis, world `[-32768,32768)` per axis; independently validate halos, retention, negative ownership, and precision. Unsupported coordinates must fail explicitly, not clamp/wrap. This is **not** a permanent world limit; broader support requires later certification.
9. **Artwork and shading — Option A.** Reuse frozen C1 Earth/Green source PNGs unchanged, with C1 four-window sampling and deterministic absolute-coordinate phase identity. Preserve production tint, authored overlay order, and crash-site appearance. Defer repetition/quality revisions until gameplay evidence exists.
10. **Performance budgets — Option A.** Use the Stage 3 investigation's numeric targets as **provisional engineering criteria only**. Later profile on nominated hardware/resolution/backend; owner reviews evidence before revising targets. Severe responsiveness symptoms are immediate stop conditions.
11. **Default activation — Option A.** Illustrated TileSet remains default. Continuous stays explicitly opt-in through numerical, artistic, gameplay and performance acceptance. Default activation requires a **separate future owner decision**.

## Provisional Stage 3 performance targets (not measured)

| Metric | Initial engineering target |
|---|---|
| Main-thread terrain preparation | ≤2 ms/frame allocated; p95 slice ≤2 ms; no slice >5 ms |
| Complete chunk CPU preparation | p95 ≤8 ms accumulated; investigate >16 ms |
| GPU overhead | p95 ≤1 ms added, with total frame target 16.7 ms on nominated machine |
| Incremental resident terrain texture memory | ≤32 MiB at default retained window |
| Incremental CPU preparation/cache memory | ≤64 MiB including replacement buffers |
| Numerical payload | ≤128 KiB per chunk before engine overhead |
| First ground readiness | 25 chunks within 120 serviced frames after shared resources ready |
| Overall first arrival | Initial target ≤4 seconds on nominated machine |
| Warm hatch return | No rebuild/upload if context and publication remain valid |
| Cancellation | Immediate authority invalidation; stop by next slice/frame; no stale commit |

## Stage boundaries and current proof gap

- **3A-1 — Metadata and conditional numerical specification:** isolated deterministic CPU metadata, explicit encoding/interface contract, focused tests, documentation of proof obligations. This milestone may pass **without** runtime geometry/GPU certification. No production wiring, shaders, or art changes.
- **3A-2 — Runtime numerical certification:** bound or otherwise rigorously certify the relevant Godot `Geometry2D`/`Vector2` exclusion operations, numeric conversions, metadata encoding, shader evaluation and their composition over the supported domain. Require strict-Earth zero and Green-center one with positive certified margins. No assumed parity from Python-only evidence. Stage 3A-2 remains a mandatory gate before continuous presenter integration.
- **3B — Isolated presenter:** only after numerical gate and separate authorization; use frozen C1 sources, Candidate A, live publication evidence and focused validation.
- **3C — Opt-in exterior integration:** narrow dispatch, pending-work accounting, cancellation, revision and live arrival receipts; illustrated remains default.
- **3D — Owner acceptance and measured optimization:** authorized Godot/visual/gameplay/performance tests; later activation decision remains separate.

**Specific unresolved issue:** production exclusions use Godot `Geometry2D` and `Vector2` behavior; the Stage 2B-2 one-sided enclosure only certifies a bounded Python exclusion model. There is currently no established one-sided bound for production geometry, subsequent encoding, or runtime/GPU protection evaluation. Stage 3A-1 must **not** assert one.

## Preservation and review contracts

- Preserve all 15 known protected untracked exterior `.png.import` sidecars; compare exact inventory and hashes to the existing preservation receipt, never stage/delete/regenerate them. Treat **only** these verified files as the dirty-checkout exception.
- Preserve A1 branch and three annotated A1/C1 tags, backup bundle/receipts, frozen C1 PNGs and provenance, all Stage 2A/2B reference implementations, goldens, original and refined diagnostic manifests/outputs, and historical tests/guards.
- Existing illustrated renderer, original generator/classifications/exclusions, crash-site tint/overlays, Ferrite, construction, player, hatch/boarding, transitions, seed semantics and unrelated scenes remain unchanged by 3A-1.
- Any historical file-inventory guard adjustment must be strictly scoped to newly approved files, justified, and must not relax prior historical/math/preservation assertions.
- All engine execution, GPU profiling, owner gameplay tests, merges and cleanup require separate authorization.

## Repository source orientation (verify current line numbers)

- `scenes/world/planet_generator.gd`: authoritative material IDs, exclusions and seed sampling.
- `scenes/world/world_coordinates.gd`: cell/chunk geometry and negative-coordinate ownership.
- `scenes/world/planet_exterior.gd`: scheduling, renderer selection and arrival authority.
- `scenes/world/illustrated_terrain_presenter.gd`: current halo/publication behavior.
- `tests/terrain_stage2b2_reconstruction_reference.py` and `docs/experiments/terrain_stage2b2_reconstruction.md`: Candidate A Python reference and conditional numerical enclosure.
- `scenes/experiments/terrain_c1/continuous.gdshader`: preserved C1 experimental presentation precedent, not runtime proof.

## Change control

These decisions were explicitly approved by the owner in ChatGPT on 2026-11-03. Future changes require a new explicit owner decision and a corresponding record update. Do not interpret this document as blanket authorization to implement later stages.

## Owner amendment — 2026-11-03: isolated visible Stage 3B laboratory

The owner-authorized Stage 3B handoff removes exact continuous visual strict-Earth
protection around the crash site. The corresponding geometry-enclosure
certification requirement in decision 2 and original 3A-2/3B boundaries is
**superseded for that removed presentation mask**. Candidate A retains sharpened
smooth four-center interpolation (`a=5/32`) and exact classified center endpoints
as its reconstruction design objective, without multiplying by protection `P`.
Organic interpolation between centers is allowed near the crash site; no
replacement strict-Earth mask is authorized.

Original `PlanetGenerator.sample_ground_material()` classification/exclusion
predicates, original material IDs and gameplay protection remain unchanged.
Historical reports, goldens and proofs above remain evidence of their original
contracts, not requirements to recreate the removed mask. The adaptive CPU
experiment is [unmerged negative PR #141](https://github.com/interneth3ro/the-long-way-home/pull/141)
at `9a75949181349dbecc475bb12328cef69636ce92`; preserve its branch/report/diagnostics.
Its box-cover/quadtree implementation is not part of this laboratory.

This amendment authorizes the isolated [visual lab](terrain_stage3b_visible_lab.md)
and focused draft PR only. It does not certify metadata encoding, GPU parity,
resources, performance or production readiness. All other decisions persist:
illustrated default, eventual narrow sibling presenter, `[-16,15]` owned-chunk
study, bounded preparation/cache, failure closed and measured performance before
activation. No production integration, Godot execution, merge or cleanup is
authorized. Engine/visual inspection requires a separate exact execution approval.
