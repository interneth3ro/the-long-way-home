# Resource Generation v2 live world-state integration

Milestone 6 on `codex/resource-generation-v2-world-state-integration`, **pending
owner review and merge**, based on `2614769057ece59bd38df8b744be724c9f4802b3`
(merged PR #191). Approved Decisions 8A–8E separate this bridge from Milestone 7
construction/occupancy and Milestone 8 Cuprite production/presentation.
Normal v2 gameplay remains inactive.

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
callers. The authoritative component survives disposable views. The presenter,
construction controller, placement/anchor rules and inspection harnesses are
unchanged; this API is not wired into their normal gameplay paths.

## Isolation, verification and deferred work

No v2 `ResourceDeposit` registration, rendering, extractor targeting, occupancy,
eligibility, extraction, Cuprite inventory output, machine definition, recipe,
save migration or research/progression change occurs. Legacy Ferrite generation,
placement, production, recovery and presentation retain their original methods.
All seven v2 reservations exist regardless of resource activation.

[`static_resource_generation_v2_integration_test.py`](../tests/static_resource_generation_v2_integration_test.py)
checks ownership, legacy method preservation, seed integrity, fixed dependencies,
publication order, complete-layout admission, error distinctions, bounded copied
reads, gameplay isolation, protected baseline scope and unexecuted test wiring.
[`resource_generation_v2_integration_test.gd`](../tests/resource_generation_v2_integration_test.gd)
authors multi-seed initialization, direct-generator equivalence, seven counts,
query/resolution/copy behavior, identity failures, idempotency, replacement,
failure, teardown, stale/foreign tokens, seed invalidation and legacy isolation.
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

Milestone 7 must adapt live construction/occupancy under existing transactions and
use current context tokens without exposing the generator. Milestone 8 must
separately authorize Cuprite extraction, output and presentation. Ferrite/Carbite
v2 activation and final mandatory test-suite stabilization remain later work.
The painted Cuprite canvas versus conservative clearance envelope remains deferred
owner visual review; no clearance/offset/scale/artwork change is made here.
Runtime/graphical verification requires separate explicit owner authorization.
