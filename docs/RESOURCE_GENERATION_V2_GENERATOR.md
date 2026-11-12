# Resource Generation v2 ordinary-world generator

Merged in PR #188. The implementation request authorized PR 2 only; the supplied specification
is design context, not independent authorization for later phases. The
[PR #187 code contracts](RESOURCE_GENERATION_V2_CONTRACTS.md) remain unchanged.
No gameplay or presenter registers this generator or its resource definitions.

PR 3's separately versioned [starting-reservation extension](RESOURCE_GENERATION_V2_STARTING.md)
is pending review on `codex/resource-generation-v2-starting-reservations`. It adds
complete preparation, transition presence and reservation priority without changing
`ordinary-v2-1`. The base `identity_policy()` accessor defaults to `ordinary-v2-1`.

## Ownership and candidates

[`OrdinaryResourceGenerator`](../scenes/world/ordinary_resource_generator.gd) is
one `RefCounted` policy interpreter. Construction requires a signed int64 seed,
native `WorldResourceDefinition` array, explicit authored protection rectangles,
and supported policy `ordinary-v2-1`. Invalid inputs leave an unready generator
with an initialization error. Definitions are deep-copied and sorted by resource
ID; caller array order and later edits cannot affect reconstruction. Protection
rectangles are copied values. They must conservatively contain all fixed authored
polygons/obstacles and required clearance, never live machines. Empty protection
is useful for synthetic worlds. PR 3 supplies an inert authored snapshot; live
crash-site integration remains deferred.

The locked Decision 5E correction is **1,536 world units = 24 terrain cells at
64 units = 48 construction cells at 32 units** per axis. `owner_at` floors both
axes independently: -1 maps to owner -1, exactly -1,536 also maps to owner -1.
Its precondition is a finite point within the supported domain; query admission
validates before conversion. The first anchor's top-left base origin determines
ownership. Other members may cross boundaries, retaining original IDs/owner.

Every sampling channel hashes UTF-8
`ordinary-v2-1:<seed>:<owner_x>:<owner_y>:<slot>:<channel>` using SHA-256 and converts
the first seven hexadecimal digits to an integer. Channels are `x`, `y`, `group`,
`pair_x`, `pair_y`, `triple_x`, `triple_y`, `rotation`, `mirror`, `presence`,
`resource`, `priority`, plus macro-owner slot -1 `concentration`. No mutable RNG,
runtime string hash, load order, camera, machine or visual input participates.
`group % 100` selects single below 60, pair below 90, triple otherwise. This
60/30/10 target counts raw candidate locations, not accepted locations or quotas.
Protection/conflicts may alter accepted proportions.

All anchors are 4×4 construction cells. Pair offsets before shared rotation and
reflection are `(10..14, -2..2)` cells, with third member `(2..6, 12..14)`.
These irregular triangular templates fit the complete-group clearance constraints;
owner visual evaluation of their appearance remains necessary.

## Geology and distribution

Terrain has no public geological classification or biome contract. The generator
uses only existing `PlanetGenerator._noise(point / 768, 1)`, the seed-only numeric
signal used for rock/soil blending. This underscore helper is an explicit internal
dependency that must remain stable for the policy. No final color, material index,
mutable terrain, or loaded scene is sampled. A future public terrain API is deferred.

The supported preference `terrain_geology` means effective resource weight
`abundance_weight * lerp(1, preference, geology)`. Missing preference means 1.
Positive weights keep current resources eligible everywhere; accumulated maximum
weights must remain finite. Selection uses sorted cumulative weights and a separate
hash channel. Nonempty environment lists and unknown geology keys **fail admission**:
there is no authoritative classifier for hard restrictions. Future exclusive minerals
need that contract and a reviewed policy; no invented biome system is supplied.

Four independent slots normally pass an 18% presence gate. A seed-dependent
4×4-region macro cell has an 8% concentration chance; candidates inside it with
geology >=0.55 use a 54% gate. Concentrations increase distinct locations with
unchanged group/spacing caps. No ship-distance gradient, quota, field shape or retry
exists. Baseline expectation is 0.72 raw locations per region before conflicts;
accepted density is unmeasured. Native `.tres` definitions are inert configuration,
separate from inventory, artwork catalogs and activation.

## Atomic validation and conflict reach

Candidates use unchanged schema 1 via `ResourceGenerationDescriptors.create_location`.
Priority wrappers are internal and add no descriptor fields. Each visual clearance
envelope is a 128-unit anchor grown by 64 units, independent of images. Inclusive
contact with authored protection rejects the whole group. Within-group anchor
overlap, visual gap and center-distance checks also reject the complete location.
Soft geological preferences exclude no current terrain; unsupported hard environment
configuration is rejected at initialization.

Between locations, any logical overlap or member-envelope conflict rejects the
lower-priority whole location. Lower integer priority wins, with canonical
location-ID lexical tie-breaking. Compare against **eligible raw neighbors**, including
losers, never accepted neighbors. No recursive acceptance, trimming, retries, or
cache/query-order dependence occurs. Extra empty space from this conservative rule
is intentional.

Each member's axis offset is <=448 units. Conflicting base origins differ by at
most `2*448 + 128 + 2*64 + 448 = 1,600` on either axis. Beyond the two-region halo,
base origins are separated by >3,072 on at least one axis. A one-region halo is
insufficient. Each reconstruction examines 25 owners × 4 raw slots, then at most
four owned candidates against those raw neighbors. Halo candidates just outside
the public domain participate too, avoiding a special acceptance edge.

## Interfaces and bounds

| Interface | Result |
| --- | --- |
| `is_ready()` / `initialization_error()` | Admission status. |
| `owner_at(point)` / `owner_is_supported(owner)` | Floor ownership / domain check. |
| `region(owner)` | `{"ok": true, "locations": [...]}` complete accepted groups in slot order. |
| `query_owners(area)` | `{"ok": true, "owners": [...]}` row-major plan, without generation. |
| `query(area)` | `{"ok": true, "deposits": [...]}` members intersecting conservative envelopes, inclusive of boundaries. |
| `descriptor_by_id(id)` | `{"ok": true, "descriptor": ...}` accepted canonical location or member. |

Failures return `{"ok": false, "error": ...}`, never partial results. Queries can
return only intersecting members; resolve their `location_id` for the complete
group. Filtering does not change generation membership. Returned nested data are
deep copies. Foundation identity serialization is unchanged; foreign seeds/policies,
aliases, overflowing integers, unsupported owners/slots and nonaccepted IDs fail.

Queries expand both sides by 640 units (`448+128+64`) and deduplicate by deposit ID.
Nonfinite/negative rectangles, unsupported coordinates, excessive extents or >64
expanded owners fail before generation. Point queries are valid. Callers explicitly
page larger requests. Maximum result size is 768 members (64×4×3), with at most
6,400 raw-candidate evaluations per uncached maximum query. FIFO cache holds 32
regions / at most 384 members. Order is row-major owner, slot, member; eviction
changes only work, not descriptors by design. Per-candidate cost also scales with
caller-supplied definition/protection counts. No whole-world precomputation occurs.

## Provisional tuning register

These are **initial implementation values, not approved gameplay requirements**.
Change generation semantics under a new policy version; keep descriptor schema
and serialization stable. No accepted-density/performance/visual tuning is certified.

| Parameter | Initial value and purpose | Tuning location |
| --- | --- | --- |
| Policy token | `ordinary-v2-1`, exact generation semantics | `POLICY`, bump after changes |
| Candidate budget | Four per owner, bounded work | `CANDIDATE_SLOTS` |
| Ordinary density | 18% slot gate | `BASE_PERCENT` |
| Concentration scale | 4×4 regions / 6,144-unit side | `CONCENTRATION_REGIONS` |
| Concentration frequency | 8% macro-cell gate | `CONCENTRATION_PERCENT` |
| Concentration strength | 3× gate / 54% | `CONCENTRATION_MULTIPLIER` |
| Concentration geology | >=0.55 numeric terrain sample | `_candidate` |
| Abundance weights | Ferrite 1.2, Carbite 1.0, Cuprite 1.0 | Native definition `.tres` files |
| Geological preferences | Ferrite 1.2, Carbite 0.8, Cuprite 1.1 | Those definitions' `terrain_geology` |
| Geology sampling | Existing 768-unit scale / channel 1 | `_geology`, keep matched to terrain |
| Within-group center distances | 320–704 units | `WITHIN_MIN/MAX` |
| Offset templates | Pair x10..14/y-2..2, third x2..6/y12..14 cells; rotations/reflections | `_anchors`, re-prove bounds |
| Visual envelope | 64-unit anchor margin / 256-unit square | `VISUAL_MARGIN` |
| Within-group gap | >32 units on a separating axis | `WITHIN_GAP` |
| Between-location gap | >448 units on a separating axis | `BETWEEN_GAP` |
| Maximum axis offset | 448 units, derived from templates | `MAX_OFFSET` |
| Conflict reach / halo | 1,600 units / two regions, derived | `CONFLICT_REACH`, `NEIGHBOR_HALO` |
| Query reach | Symmetric 640 units, derived | `QUERY_REACH` |
| Query budget | 64 expanded owners / 768 members | `MAX_QUERY_REGIONS` |
| Cache | 32 regions, FIFO | `CACHE_LIMIT` |
| Domain | Owners ±8,192; query axes within ±8,191×1,536 units | `MAX_REGION_COORDINATE`, conservative float/grid arithmetic |

Region dimensions, infinite supplies, 4×4 anchors and candidate 60/30/10 grouping
are owner requirements, separate from this provisional register.

## Validation, file scope and preservation

[`static_ordinary_resource_generator_test.py`](../tests/static_ordinary_resource_generator_test.py)
checks source contracts, inert wiring, preservation, independent SHA-256 vectors,
group sampling, exhaustive template geometry and halo/query reach proofs. It
executes no project or Godot code. The draft PR records actual baseline/final
Python-suite results, with existing historical failures kept intact.

[`ordinary_resource_generator_test.gd`](../tests/ordinary_resource_generator_test.gd)
authors multi-seed/reverse-order reconstruction, cache/copy isolation, boundaries,
membership, cross-region query/deduplication, priority/tie/losing-raw-neighbor atomic
rejection, protection/clearance, configuration, identity and query-bound assertions.
They are **not executed**, parsed by Godot, or added to a runner. No Godot parser,
headless runtime, graphical, gameplay determinism, mining or performance PASS is
claimed. No engine invocation or safety-control change occurs.

File-by-file scope:

- `ordinary_resource_generator.gd`: isolated ordinary policy and bounded APIs.
- `resource_definitions/v2/ferrite.tres`: provisional Ferrite weights.
- `resource_definitions/v2/carbite.tres`: provisional Carbite weights.
- `resource_definitions/v2/cuprite.tres`: provisional Cuprite weights.
- New Python test: static source/preservation and independent policy checks.
- New GDScript test: authored, unexecuted behavioral assertions.
- This document, foundation-contract status/correction and README: scope and limits.

Foundation source, legacy Ferrite generation/extraction/presentation, world
state/exterior scenes, resource deposits, machine/inventory/progression/save data,
approved Cuprite prototype, artwork/assets, historical files, existing tests and
runner controls are preserved. No new resource appears in normal gameplay; no
depletion quantities/history are introduced.

PR 3 implements starting deposits, reservation search/suppression/transition and
read-only legacy diagnostics under its separately versioned, unconnected policy.
Deferred: shared presentation/streaming, Cuprite/Carbite activation,
snapping/occupancy, mining/progression, save architecture, Carbite artwork and Ferrite
redesign. Starting guarantees and migration safeguards belong to PR 3. Runtime and
visual evaluation need separate authorization; artwork milestones remain required
before later activation. Environment classification remains an explicit limitation.
