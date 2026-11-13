# Resource Generation v2 live world-state integration

Milestone 6 merged in PR #192 at `fc3b0947be5e3cb217e4de12f95ec23d550a5003`.
Its read boundary and lifecycle are described below. Milestone 7 live construction
merged in [PR #193](https://github.com/interneth3ro/the-long-way-home/pull/193).
The Milestone 6/7 records below retain their historical scope; Milestone 8 supersedes
their inactive-production and deferred-presentation boundaries.

## Milestone 8 Cuprite gameplay (pending merge)

Implemented on `codex/resource-generation-v2-cuprite-gameplay`, based on
`5c70fba96fc05053d9ce7c059a0d6fcd0811c3cb`. Owner Decisions 10A-10E authorize
immediate normal gameplay integration, without discovery, research or developer gates.

`PlanetWorldState.extractor_output_item(snapshot)` is the single Extractor output
resolver used by `machine_status` and `stored_output_item`. It obtains the committed
machine by ID and rejects altered snapshots. V2 records must own the deposit claim;
the resolver obtains the current context and resolves the exact committed deposit
ID, validates compatibility and 4x4 anchor geometry, then maps authoritative Cuprite
to `cuprite_ore` and Ferrite to `ferrite_ore`. The cached `v2_resource_type` label and
packaged Ferrite output cannot override that authority. Unsupported resources,
missing claims and unavailable context return no product, so production is inactive.
Legacy Extractors resolve Ferrite at their existing rotated extraction point without
requiring v2 context. Carbite remains incompatible and has no production mapping.

The existing `advance_production` implementation is unchanged: one ore per one-second
cycle (60/min), 20-item output capacity, full-output pause, no blocked backlog, and
resumption after collection. No separate resource loop or extraction recipe exists.
Smelter and Fabricator production/recipes are unchanged.

Existing `collect_output` and `recover_machine` implementations are unchanged. Both
consume `stored_output_item`; silent inventory acceptance precedes output clearing
or machine/claim removal and guarded notifications. Identity conflicts, quantity
overflow or rejected payloads retain all stored output. If v2 authority is unavailable,
collection/recovery of nonempty output fails safely and retains the machine/claim;
a restored compatible context permits exact resolution again. Empty machine recovery
still works after retirement. No migration or administrative fallback is introduced.

[`cuprite_ore.tres`](../inventory/cuprite_ore.tres) follows the existing material item
convention: ID `cuprite_ore`, display name `Cuprite Ore`, materials section. Definitions
are registered by accepted inventory transfers, using the existing identity checks;
there is no second item registry. The supplied 256x256 RGBA inventory PNG was copied
byte for byte to [`assets/items/cuprite_ore.png`](../assets/items/cuprite_ore.png),
SHA-256 `5bf845d4d3620e935ccfe0037e4c0d6ecf98c1b54cfae1f6e7445b5bda9ac129`.
Its transparency/content are unchanged. Authored import metadata matches Ferrite's
lossless/mipmap/alpha settings and has a distinct UID; no importer was executed.
`ItemPresentation.ICONS` supplies the same artwork to inventory/hotbar and material
rows. Machine UI passes the resolved product into Extractor inspection for the
correct icon, name, yield and collection eligibility, including an empty buffer.

Normal world artwork uses the [shared world-state presenter adapter](RESOURCE_GENERATION_V2_PRESENTATION.md#milestone-8-normal-gameplay-pending-merge).
Construction routing, exact click tickets, physical safeguards, atomic deployment,
claim release, IDs and all generation policies/reservations are unchanged. Legacy
Ferrite still wins overlapping placement geometry and retains its own presenter.
Carbite extraction, Cuprite smelting/wire, power, research, discovery and persistence
remain outside scope.

### Milestone 8 verification

[`static_cuprite_gameplay_test.py`](../tests/static_cuprite_gameplay_test.py) checks
approved asset identity, item/import conventions, authority mapping, shared timing,
transaction ordering, inspection, bounded descriptor presentation, loaded-terrain
lifecycle and preservation. Focused Python checks: **12/12 PASS** using `python -B`.
[`cuprite_gameplay_test.gd`](../tests/cuprite_gameplay_test.gd) authors actual production,
capacity/full pause/resume, item identity, collection/recovery rejection, retired
context, unsupported-resource inactivity, legacy Ferrite, physical construction,
occupancy, presentation positioning, streaming/revisit and duplicate assertions.
It is **unexecuted**, with no runner dispatch added. Historical Milestone 7 behavior
fixtures remain unchanged, including their now-superseded inactive-output assertions.

Complete broad discovery ran **659 tests / 87 failure cases / 0 errors / 2 skips**
in 375.325 seconds with unchanged source/diff identity throughout the run. The broad
suite remains **FAIL**: **55 previously recorded cases + 32 authorized source-shape
or preservation conflicts**, with no outstanding unexpected regression identified
by static investigation. The added cases are nested shell preservation (12),
Extractor artwork byte guards (2), exterior preload ban (1), prior inactive v2
construction/inspection guards (3), world-state isolation naming (1), presenter
isolation/ordering assumptions (2), Smelter artwork/footprint/thermal byte guards
(2 each), and literal resource-graph traversal of the catalog's existing assets
validation prefix (5). An independent static traversal checked 247 existing files
and confirmed that exact prefix is not a load target; no missing file was found.
The draft PR records the full module-by-module classification against
PR #193's published **647 tests / 55 failure cases / 0 errors / 2 skips**. Historical
tests are not weakened, deleted, repinned or skipped; final v2 suite stabilization
remains separate. No Godot parser/import, headless, graphical, gameplay or performance
verification occurred. Static checks do not establish runtime acceptance. Existing
runner controls and inactive metadata inventory are preserved; live asset dependencies
will require review before any separately authorized metadata execution.


## Ownership and fixed inputs

[`PlanetWorldState`](../scenes/world/planet_world_state.gd) owns one
[`ResourceGenerationV2Integration`](../scenes/world/resource_generation_v2_integration.gd)
`RefCounted`. The existing constructor signature and legacy Ferrite initialization
remain. After legacy initialization, the constructor explicitly initializes v2
using authoritative `seed_value`. V2 failure is independent of legacy readiness,
construction, production, transactions, recovery, inventories and signals.

The component loads and snapshots the existing native Ferrite, Carbite and Cuprite
definitions. It constructs the existing `StartingResourceGenerator` with the exact
`ResourceGenerationCrashSite.protected_bounds()` and `SHIP_REFERENCE`. No caller
can substitute definitions, protection geometry or ship position. Empty protection
fails initialization. The inherited `ordinary-v2-1`, `starting-v2-1` and schema 1
contracts and numerical values are unchanged. Artwork catalogs are not loaded.

A candidate stays local until generator readiness and `reservations()` succeed.
Complete locations pass configured descriptor validation, expected seed/policy,
supported first-anchor ownership, starting slot bounds, unique location/deposit
identities and exact 3 Ferrite / 2 Carbite / 2 Cuprite counts. Spatial eligibility,
bounded arrangement search and clearance remain the existing generator's
responsibility; the bridge neither reconstructs nor trims the arrangement.
No fallback seed, empty protection or ordinary-only context is published.

## Public world-state API

These separate names preserve the semantics of legacy
`is_resource_generation_ready()`, `resource_generation_error()`,
`query_deposit_descriptors()` and every existing legacy query.

| Method | Contract |
| --- | --- |
| `is_resource_generation_v2_ready()` | Whether a complete v2 context is published. |
| `resource_generation_v2_error()` | Initialization/retirement diagnostic; empty only while healthy. |
| `resource_generation_v2_context()` | Success contains opaque `token`, `world_seed`, `ordinary_policy`, `starting_policy`, `schema_version`. Failure has no token. |
| `query_resource_descriptors_v2(area, token)` | Existing bounded visual-envelope broad phase; success has `deposits`. Empty success is valid absence. Logical anchors remain extraction geometry. |
| `resource_descriptor_v2_by_id(identity, token)` | Exact generator resolution of accepted canonical deposit or location identity; success has `descriptor`. |
| `starting_resource_reservations_v2(token)` | Complete deep-copied `locations` plus generator `attempts`. |
| `configure_resource_generation_v2(ordinary_policy = "ordinary-v2-1", starting_policy = "starting-v2-1", schema_version = 1)` | Explicit initialization/replacement using the authoritative seed and fixed authored inputs. Unsupported policies/schema retire the previous context and fail. |
| `invalidate_resource_generation_v2()` | Explicit teardown of v2 only. Releases generator/cache and retires the token. |

All result Dictionaries have `ok`. Failures contain only `ok: false`, `code`
and `error`; no apparently successful empty payload accompanies a failure.
The codes are:

| Code | Meaning |
| --- | --- |
| `unavailable` | No complete context, including after initialization failure or teardown. Checked before request validity/token. |
| `stale_context` | Healthy context, but token is null, foreign or retired. Checked before query/identity. |
| `invalid_query` | Generator rejects rectangle, extent, domain or owner budget. |
| `invalid_identity` | Generator rejects canonical shape/integer/world/owner/slot admission. |
| `incompatible_context` | Unsupported configuration/schema, changed world seed, or incompatible identity policy. |
| `not_found` | Generator admits the identity request but has no accepted descriptor. |
| `initialization_failed` | Native definition, protection, generator preparation or reservation validation failed. |

The existing generator defines identity admission; an identity with a different
seed is `invalid_identity` under that contract. Tokens independently reject stale
or foreign context references. An invalid query does not retire a healthy context.

Descriptor/array payloads are recursively copied, including nested presentation
metadata. Callers may edit their copies without changing generation. Those copies
are observations, never placement authority. Consumers retain the accompanying
token and re-resolve the stable ID before future use. The token is a plain
`RefCounted` identity, holds no generator reference and is process-local, not save
data. The generator itself is never returned.

## Atomic lifecycle and seed limitation

Identical supported configuration on a healthy component returns the same token
without reloading definitions, rebuilding reservations or discarding caches.
Any replacement first drops the published generator/token. Only after complete
synchronous validation is a fresh generator/token published. Failed replacement
leaves v2 unavailable, retains the diagnostic and cannot serve old descriptors.
An explicit later configuration can recover; even restoration of identical seed
and policies receives a fresh token after retirement. No asynchronous callbacks,
automatic synchronization, background retries or global deposit registry exists.

The world records its construction seed. Assigning a different `seed_value`
immediately retires v2, even if the field is subsequently restored. Configuration
while the seed differs from the construction seed fails explicitly and requests
a fresh `PlanetWorldState`. Existing legacy/terrain generators cannot be safely
reseeded in place within this scope. This limitation does not reset or migrate
legacy state. A fresh world is required for an actual seed change; restoring the
original seed permits explicit v2 reinitialization with a fresh token.

Teardown drops only component-owned references/caches. It does not change machines,
terrain edits, removed details, revision, inventories, legacy deposits or signals.
Ordinary ownership, identity resolution and query order remain deterministic
generator responsibilities. Queries retain the 64-owner admission budget, 32-region
cache and maximum 775 deposits. No whole-world enumeration or additional cache
is introduced. These are work bounds, not measured performance guarantees.

Terrain chunk creation/disposal and exterior streaming have no v2 configuration
callers. The authoritative component survives disposable views. The generation
presenter and inspection harnesses remain separate. Milestone 7
wires the construction controller to these authoritative descriptor reads; shared
anchor geometry and placement checks retain the boundaries described above.

## Isolation, verification and deferred work

The Milestone 6 bridge itself performs no rendering, occupancy or inventory mutation.
Milestone 7 adds live targeting and world-state occupancy under the existing machine
transaction, extends construction compatibility to Cuprite, and leaves all v2
Extractors inactive for production. No v2 `ResourceDeposit` registration, normal
Cuprite rendering, Cuprite inventory output, recipe, save migration or progression
change occurs. Legacy Ferrite queries, production, transfers and presentation
retain their original methods; deployment/recovery share the extended transaction.
All seven v2 reservations remain unchanged.

[`static_resource_generation_v2_integration_test.py`](../tests/static_resource_generation_v2_integration_test.py)
checks ownership, legacy API routing/isolation, seed integrity, fixed dependencies,
publication order, complete-layout admission, error distinctions, bounded copied
reads, gameplay isolation, approved generation contracts, frozen artwork and
unexecuted test wiring. These are ongoing invariants, not exact comparisons to
pre-PR world-state methods or the repository's historical changed-file set.
[`resource_generation_v2_integration_test.gd`](../tests/resource_generation_v2_integration_test.gd)
authors multi-seed initialization, direct-generator equivalence, seven counts,
query/resolution/copy behavior, identity failures, idempotency, replacement,
failure, teardown, stale/foreign tokens, seed invalidation and legacy isolation.
Policy-mismatch fixtures use the current seed; separate wrong-seed fixtures use
the current policy and expect the documented `invalid_identity` result. Failure
assertions require the exact error-only envelope, nonempty retained diagnostics,
no token/reservation/descriptor publication, and continued failure on repeated
invalid configuration. No production configuration override is added for testing.
Its unrelated-node disposal/terrain-edit assertion models lifecycle independence;
actual terrain streaming has not been exercised.

GDScript tests are **authored but not executed** and absent from every approved
runner. No Godot parser, import, headless runtime, graphical, performance or live
gameplay validation is claimed. The narrow standing Native authorization does
not authorize these tests; no runner or execution gate changes occur.
See [execution restrictions](LOCAL_TESTING.md#authorization-and-standing-scope).
Focused Python checks passed 10/10. The untouched baseline ran 624 tests with
25 failures, zero errors and two skipped. The staged implementation ran 634 tests
with 34 failures, zero errors and two skipped. The nine additional failure cases
are authorized scope conflicts: old whole-world byte/scope guards and the inactive
metadata-smoke dependency inventory. The original failures are historical guards
plus the existing environment-specific bytecode-cache mismatch; several now also
encounter the authorized bridge. No new functional regression was detected by
static inspection; this is not runtime certification. The draft PR classifies
every failure. Historical guards are not weakened or repinned.

The inactive metadata-smoke inventory no longer closes over the world state's
new v2 dependency. Any future metadata activation requires separate owner review
of that closure and a reviewed inventory amendment, as well as fresh execution
authorization. This PR preserves the inactive gate and all fixed inventories.

Milestone 7 now uses current context tokens without exposing the generator and
owns occupancy in PlanetWorldState, as documented in the live placement contract.
Milestone 8 now implements Cuprite extraction, output and presentation on the pending
feature branch described above.
Carbite production, Ferrite v2 migration and final mandatory test-suite
stabilization remain later work.
The painted Cuprite canvas versus conservative clearance envelope remains deferred
owner visual review; no clearance/offset/scale/artwork change is made here.
Runtime/graphical verification requires separate explicit owner authorization.
