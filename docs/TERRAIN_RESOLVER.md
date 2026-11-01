# Deterministic terrain resolver (PR #101 merged)

The merged resolver-only milestone added opt-in selection logic. The pending
[PR #104 production integration](ILLUSTRATED_EXTERIOR.md) now uses it when the
exterior selects illustrated rendering. Legacy mode does not initialize it.
Procedural sampling, gameplay state, laboratories and baked artwork remain unchanged.

## Interface and rule 1

`TerrainResolver.resolve(cell, materials, lookup, presentation_seed = 0,
rule_version = 1)` accepts absolute **terrain-cell** coordinates and nine material
samples in this order: **center, NW, N, NE, W, E, SW, S, SE**. Earth is material
`0`; provisional Green materials `1..4` all classify as terrain `1`. Other IDs,
incomplete neighborhoods and unknown rule versions report errors and return no
assignment. `signature()` exposes the nine-value terrain signature alone.

The center retains its sampled material class. A shared side is Green only when
both incident cell centers are Green. A corner is Green only when all four
incident centers are Green. All other peers are Earth. Thus Earth centers are
solid Earth, while the 256 binary neighborhoods of a Green center reach exactly
the 47 approved Green signatures. The other 46 Earth signatures remain available
in the complete inventory for future rules.

Call `TerrainAssignmentLookup.new()` and require `initialize()` to succeed before
resolving. Initialization reads native TileData center and peering values from the
[approved TileSet](../assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres)
and verifies all 98 locations and signatures against its existing
[manifest](../assets/experiments/native_terrain_47_96/baked_v2/mapping.json).
Native source enumeration follows the
[TileSetSource API](https://docs.godotengine.org/en/stable/classes/class_tilesetsource.html).
The baseline source is `0`, B/C interiors source `1`; native alternative IDs are
`0`. Baseline records are variant A, including both solid interiors. This adds
no separate signature inventory. Missing, duplicate, unexpected or disagreeing
records fail initialization and clear the lookup. Check `error` for the
diagnostic. Missing signature/variant lookup reports an error without substitution.

A successful result is a copied dictionary with `source_id`, `atlas_coords`
(`Vector2i`), `alternative_id`, `signature` (`PackedInt32Array`, center then eight
peers), and `variant` (`A`, `B`, or `C`). Failure returns `{}`. Reinitialize the
lookup after an intentionally changed inventory; it does not watch resources for
edits. No existing resource is mutated.

## Coordinates, variations and future seeds

For a solid signature only, a dedicated integer coordinate hash selects buckets
`0..99`: A `0..59`, B `60..84`, C `85..99`. Both Earth and Green use their own
approved A/B/C records. Non-solid boundaries always use A. The hash reduces the
seed and signed cell coordinates modulo `2147483647` before multiplication;
intermediates fit signed int64. Presentation channel `193` is local to this
resolver, with no global RNG, generator RNG calls or mutable random state.
Fixed coordinates and presentation seed regenerate identical assignments.

Sampling is the caller's responsibility. The PR #104 integration passes
`PlanetGenerator.sample_ground_material()` results through the existing
presenter's one-cell halo around each chunk. Samples must come from the
same absolute-coordinate material field even when neighboring chunks are
unloaded. No rendered cells, native Connect painting or loaded-neighbor data are
consulted. Negative coordinates need no special case in the resolver. Existing
geometry stays 32 by 32 cells per chunk, 64 world units per cell, 2,048 per chunk,
with a separate 32-unit construction grid.

Future saves should store a world seed and world-generation version for choosing
and constructing the material sampler; neither belongs to terrain rule dispatch.
They can separately supply a stored/derived presentation seed to the existing
`presentation_seed` parameter and a terrain rule version to `rule_version`.
Changing only presentation seed can change interior artwork while preserving
material signatures. Unsupported rule versions fail explicitly. Production seed
selection, generator formulas, save serialization, loading and migrations are
not implemented here. Hash/rule changes affecting saved assignments require a
new presentation rule version rather than silently changing version 1.

## Validation and limits

Run the permitted Python static suite through the
[local runner](LOCAL_TESTING.md). The focused
[static tests](../tests/static_terrain_resolver_test.py) bind arithmetic proofs to
the GDScript expressions, verify native resource text against the manifest,
exhaust binary neighborhoods/shared boundaries, and check signed coordinates,
halos, chunk order/regeneration, seed variation, thresholds and preservation.
The finite representative distribution check is distinct from the exact
60/25/15 bucket thresholds; it proves no exact percentage across an entire world.
These are Python static models and source checks, **not GDScript execution**.
At the resolver-only milestone these engine behaviors were unverified. The
subsequent PR #102 fixture's separately authorized Import and Native Assertions
passed, followed by owner graphical acceptance at the implementation recorded
below. Production integration was untested at that milestone; subsequent
[PR #104 acceptance](ILLUSTRATED_EXTERIOR.md#final-pr-104-acceptance-2026-11-01)
records native PASS and owner gameplay 7/7 PASS with accepted initial-loading
stutter, without formal performance benchmarking. No further Godot execution,
Native, profiling, benchmarks or graphical automation is authorized by this record.

The historical laboratory and machine-art guards admit only the two new resolver script paths,
pinned to exact normalized-content hashes and required to be absent from its
historical baseline. Tampered content and other paths are explicitly rejected.
Existing production/artwork preservation checks and runner controls are retained.

The separate [production-scale fixture](PRODUCTION_TERRAIN_FIXTURE.md) (merged PR #102) exercises shared TileMapLayer insertion/removal and
experimental vertex-sampled CPU tint shading in isolation. Isolated Import and
Native Assertions passed, and the owner reported **10/10 graphical PASS**, with
no observations, for `07337fdfeb5bdd28200d297ea36951b054dd04a0`.
At the PR #102 milestone, production renderer replacement and authored crash-site
shading migration remained deferred. Subsequent shading must retain the existing CPU tint data,
authored masks, feathers, overrides and continuous gradients. This PR does not
establish production integration, visual equivalence or performance acceptance.


## PR #103 presenter integration (feature branch, pending merge)

[IllustratedTerrainPresenter](../scenes/world/illustrated_terrain_presenter.gd)
receives a deterministic `Callable(Vector2i) -> int` in absolute terrain-cell
coordinates, an explicit presentation seed and rule version. Production's dormant
adapter is `Callable(_generator, "sample_ground_material")`; no generator,
resolver, lookup, terrain-rule or distribution changes are included.

Public methods return `{ok, code, chunk, token, message}` with `cell` on cell
failures: `initialize()`, `begin_generation(coordinate, generation_token)`,
`present_chunk(coordinate, generation_token, material_sampler, presentation_seed,
rule_version)`, and `retire_chunk(coordinate, generation_token)`.

Initialization explicitly loads the approved native lookup and baked TileSet;
node construction/attachment does no terrain work. Each presentation samples a
34x34 halo, prepares and validates all 1024 native assignments, then overwrites
its owned rectangle in place without clearing first. Retirement erases only that
rectangle. No loaded-neighbor sampling, Connect painting, scheduler, per-cell
ownership registry, yield or per-cell material is introduced.

The caller issues positive monotonic tokens. Registration must exceed the
presenter's global high-water mark and supersedes authority without erasing old
pixels. Exact active-token matching protects preparation/commit/retirement;
duplicate completion and reentrant mutation fail. Failure retains existing
pixels without restoring older authority. Retirement removes the active record,
while the high-water mark prevents stale resurrection. Detach/reattach resets
neither tokens nor records. Returned diagnostics do not log per-cell failures.
This provides preparation-failure preservation, not engine crash rollback.

Historical PR #103 always selected effective legacy rendering, including
when its reserved illustrated option was requested. Guarded direct lifecycle
boundaries do no lookup initialization, sampling, allocation, resolution or
TileMapLayer writes in legacy mode. Existing chunk ground/details remain intact.
Production activation, ground-only suppression, tint/masks, draw-order acceptance,
streaming performance and gameplay verification belong to #104.

See the [fixture extension and static/preservation gate](PRODUCTION_TERRAIN_FIXTURE.md#pr-103-presenter-extension-feature-branch-pending-merge).
The [final PR #103 acceptance](PRODUCTION_TERRAIN_FIXTURE.md#final-pr-103-acceptance-2026-11-01)
records its isolated native and owner graphical PASS. The pending
[PR #104 activation](ILLUSTRATED_EXTERIOR.md) supersedes the dormant exterior gate
and documents ground/detail separation, tint and explicit legacy rollback. Its
[final acceptance record](ILLUSTRATED_EXTERIOR.md#final-pr-104-acceptance-2026-11-01)
distinguishes native assertions from the owner's 7/7 gameplay PASS and accepted
initial-loading stutter; no formal performance benchmark was performed.
