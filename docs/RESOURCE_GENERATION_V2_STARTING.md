# Resource Generation v2 starting reservations and migration safeguards

PR 3 merged in PR #189 at `f82298e1874ace843455f453aba2de583d2b8f5d`,
based on `499a86cfb35428b70fb24644fe80b3312d8abdef` (merged PR #188). The pasted implementation request authorizes this scope;
the supplied specification is design context, not execution authority.
Decisions 4B–4G, 5A–5H, 6A–6C and 7B apply. No gameplay caller is connected.
PR 4 adds [shared presentation and disabled Cuprite inspection](RESOURCE_GENERATION_V2_PRESENTATION.md),
pending review. Its isolated harness retains this complete reservation policy,
all definitions, the authored protection snapshot and ship reference unchanged.

## Policy boundary and interfaces

[`StartingResourceGenerator`](../scenes/world/starting_resource_generator.gd)
extends the [ordinary generator](RESOURCE_GENERATION_V2_GENERATOR.md). It is the
shared v2 policy with bounded starting preparation, not a second gameplay registry.
Starting and ordinary results use unchanged [schema 1 descriptors](RESOURCE_GENERATION_V2_CONTRACTS.md),
validation, query planning, deduplication, clearance, raw-neighbor competition and
cache implementation. There are no legacy, activation, machine or streaming inputs.

The explicit new token **`starting-v2-1`** is necessary because priority and thinning
change accepted ordinary locations. **`ordinary-v2-1`** remains constructible with
unchanged semantics. The only base extension is `identity_policy()`, returning the
old token by default and allowing new-policy ordinary IDs to resolve. No identity
aliasing or saved-world migration is supplied. Distant locations also receive new
IDs, even where their geometry remains identical.

Construction takes seed, native definitions, immutable authored protection bounds,
ship reference and optionally the exact policy token. All three required definitions
must be present, regardless of later activation. Ordinary definition snapshots,
supported vocabulary and finite-weight admission remain. Ship coordinates must be
finite and within ±8,188×1,536 units, leaving room for starting anchors/query halos.
Protection and reference positions are fixed policy inputs; changing them requires
a reviewed policy revision for an existing world. No active-resource input exists.

`reservations()` returns `ok`, deep-copied complete `locations` and `attempts`.
Failure returns `ok: false`, `error`, `attempts`, with no locations. Inherited
readiness/error, bounded `region`, `query_owners`, `query` and `descriptor_by_id`
APIs apply. Layout failure makes the entire generator unready, including ordinary
queries. No partial guarantee or ordinary-only fallback is published.

## Complete arrangement search

Attempts are ordered **0 through 511**. Each constructs all seven members before
validation. Channels use the first seven SHA-256 hex digits of UTF-8
`starting-v2-1:<seed>:<attempt>:<slot>:<channel>`: `group`, `band`, `radius`,
`direction`, `rotation`. Resource order is Ferrite, Carbite, Cuprite. Remaining
resource count decreases by `1 + sample % remaining`, creating complete groups
of up to three. There is no mutable RNG or retry beyond the fixed loop.

Groups choose one of 16 integer direction vectors, a radial cell value and a
quarter-turn of offsets `(0,0)`, `(12,-2)`, `(4,12)` construction cells. Centers
round onto the 32-unit grid before subtracting the 2-cell half-anchor. Maximum
axis offset is 384 units, within the ordinary generator's 448-unit bound. Templates
respect existing within-group distance/gap rules. No rejected member is trimmed.

Configured descriptor admission and existing whole-location protection/spacing
checks apply. Whole-arrangement validation requires exact **3 Ferrite, 2 Carbite,
2 Cuprite** counts, unique identities, correct policy/seed/slot domain, supported
first-anchor owners, every anchor center within **384–2,304** units of the ship,
and inter-location clearance among all seven members. First valid arrangement wins.
Exhaustion explicitly fails generation, rather than claiming that no unrestricted
solution exists. A valid world under this policy passes bounded preparation;
there is no proof that every int64 seed and arbitrary protection input will fit.

Band weights are Ferrite **25/65/10**, Carbite **10/55/35**, Cuprite **5/25/70**
percent for nearby/local/outer. Every resource can select every band. Group offsets
and grid rounding can move members between bands; final validation applies the
total range. Authored protection removes many nearby candidates. Nearer Ferrite
is a preference, not a promised valid deposit in every nearby sector.

## Ownership and query bounds

Regions remain **1,536 units = 24 terrain cells = 48 construction cells** per axis.
Floor of the first anchor's top-left determines ownership, including negatives.
Cross-boundary members keep that owner. Ordinary slots **0–3** and starting slots
**4–10** cannot collide within one owner. Identities exclude artwork/activation/chunks.

`region` appends only its owned reservations to ordinary results. The ordinary
cache stores ordinary results alone; return copies prevent duplicate appends on
cache hits. Preparation stores seven members once. Inherited symmetric 640-unit
query expansion covers reserved offsets; inherited ID deduplication applies.

The 64-owner query budget remains. Maximum returned members are **775** (768+7).
Preparation constructs at most 512×7 members, checking at most 21 member pairs per
arrangement plus configured admission/protection. Each raw ordinary candidate adds
at most seven reservation-member comparisons. Existing 100-raw-candidates-per-region
and 32-region ordinary cache limits remain. These are cardinality/work bounds,
not measured latency guarantees. Definition/protection list size also affects work.

## Transition and priority

The new policy retains `ordinary-v2-1` position, presence, geology, resource, group
and priority hash channels intentionally. A separate normalized 28-bit presence
roll hashes `starting-v2-1:<seed>:0:<slot>:transition:<owner_x>:<owner_y>` and must
be below `smoothstep(1536, 3072, distance_to_ship)` at the first anchor center.
Expected candidate density is zero through 1,536, rises continuously to one at
3,072, then remains one. This is not a regional quota or certification that a
finite visual sample looks seamless.

Transition and reservation rejection run inside `_candidate` for **every raw
competitor before acceptance**, never filtering already-accepted locations.
Inactive reservations block equally. One conflict rejects the complete ordinary
location. Removed candidates cannot suppress others; remaining raw losers still
participate in the original conservative priority rule. No recursive accepted-
neighbor dependency or query-order state is added. Preparation validates authored
protection first, so reservation priority cannot override physical clearance.

Outside transition/reservation reach, raw selection and grouping remain identical.
Acceptance can change near their edges through the existing finite conflict reach;
this is explicitly part of the new policy. Beyond that boundary, wider-world
abundance remains independent of ship distance.

## Authored snapshot

[`ResourceGenerationCrashSite`](../scenes/world/resource_generation_crash_site.gd)
provides a scene-independent snapshot. Ship reference **(-384,-192)** is the authored
`GroundObjects/CrashedShip` origin, not artwork center or player spawn. Protection
includes shared `CrashSiteProtection.GAMEPLAY` bounds (hatch/approach/factory),
grounded hull collision union, authored rocks and four clearing/scar/ridge/shelf
bounds. Construction clearance is 96 units, terrain protection margin 48 units;
the existing 64-unit v2 visual margin also applies. AABBs intentionally reject
some usable polygon corners. Legacy Ferrite and prototype artwork are not inputs.

No scene, texture or legacy catalog is loaded. Static tests compare ship/terrain
bounds against scene text and pin existing geometry against the PR baseline.
Later authored edits require snapshot and policy review together. Live simulation
and scene integration remain deferred.

## Temporary migration diagnostics

[`ResourceMigrationDiagnostics`](../scenes/world/resource_migration_diagnostics.gd)
is an unconnected read-only utility, not a synchronization service.
`legacy_snapshot(id, polygon, envelope)` converts existing logical polygons and
artwork envelopes to validated conservative rectangles. A separately authorized
caller can use existing bounded legacy query/resource APIs; introductory Ferrite
uses its authored footprint with existing 32-unit artwork padding. The utility
neither generates legacy deposits nor loads artwork.

`inspect(legacy_snapshots, complete_v2_locations, authored_rectangles)` accepts
up to **128** legacy snapshots, **128** v2 locations (384 members), **32** protection
bounds. Callers supply reservations and accepted ordinary locations together,
deduplicated by ID. Malformed/duplicate input fails before work. Copies are sorted
by stable IDs. Protection IDs use stable caller array indices. Reports contain
both identities, tested rectangles, kind and owner-review flag.

At **256** reports, overflow returns `ok: false`, `complete: false`, owner review
required and bounded partial evidence. Callers must page and finish inspection;
overflow is never clearance. Logical AABB/anchor contact is a **potential gameplay
overlap**, not proof of polygon intersection. Artwork contact is visual overlap;
separation within 128 units is visual proximity. Only visual proximity alone is
marked harmless. Legacy/authored and v2/authored contacts are also reported.
Conservative false positives are intentional. No relocation, trimming, suppression,
activation, gameplay mutation or automatic resolution occurs.

**Migration acceptance is unresolved.** Diagnostics have not run against a
Godot-generated world; no seed is certified conflict-free. Existing introductory
Ferrite intentionally occupies the authored gameplay/clearing protection area.
That legacy/authored overlap predates v2. Potential gameplay conflicts, incomplete
inspection and visual overlaps need explicit owner review before phase acceptance.
Legacy conflicts never change permanent reservations.

## Provisional numerical register

These are implementation values pending separately authorized owner F5 evaluation.
They do not supersede approved design or widen execution authority.

| Parameter | Initial value / code location |
| --- | --- |
| Complete arrangement budget | 512, `ARRANGEMENT_BUDGET` |
| Search order | Ascending attempt, Ferrite/Carbite/Cuprite, ascending slots |
| Band weights | 25/65/10, 10/55/35, 5/25/70, `BAND_THRESHOLDS` |
| Base radius cells | 14–22, 26–46, 50–68, `BAND_CELLS` |
| Direction/group variation | 16 integer vectors, rotated offsets, `_arrangement` |
| Inner suppression / transition width | 1,536 / 1,536 units |
| Authored construction / terrain margin | 96 / 48 units, snapshot |
| Diagnostic proximity | 128 units |
| Diagnostic limits | 128 legacy / 128 locations / 32 protection / 256 reports |
| Ordinary geometry and distribution | Unchanged [PR #188 register](RESOURCE_GENERATION_V2_GENERATOR.md#provisional-tuning-register) |

Approved counts, infinite deposits, 4×4 anchors, region units and initial
384–768 / 768–1,536 / 1,536–2,304 targets are distinct from provisional mechanics.
Changing generation semantics requires a new policy token.

## Validation, file summary and preservation

[`static_starting_resource_generator_test.py`](../tests/static_starting_resource_generator_test.py)
checks source contracts, independent transition math and numerical layout examples
for seven signed seeds, ownership/reach, scene provenance, inert wiring and
preservation. These do not execute project code or establish Godot reconstruction.
The draft PR records actual Python-suite results and historical failures separately.

[`starting_resource_generator_test.gd`](../tests/starting_resource_generator_test.gd)
authors multi-seed reconstruction/count/group/distance tests, cross-region queries,
exhaustion, admission, protection, stable identities, copies, reverse order/cache,
inactive priority, atomic competition, transition endpoints, distant-policy geometry
and read-only diagnostic/overflow assertions. They are **not executed** or added
to any runner. Godot parser/type checking, runtime determinism, graphical acceptance,
gameplay and performance remain unverified. No Godot process is launched.

File-by-file scope:

- `starting_resource_generator.gd`: shared policy extension and complete preparation.
- `ordinary_resource_generator.gd`: default identity-policy accessor only.
- `resource_generation_crash_site.gd`: inert authored geometry snapshot.
- `resource_migration_diagnostics.gd`: bounded temporary compatibility inspection.
- New Python/GDScript tests: static checks and unexecuted behavior assertions.
- `static_ordinary_resource_generator_test.py`: allow exactly two inert consumers;
  retain the ban on gameplay/scene/resource registration.
- This document, ordinary/foundation status and README: reconcile scope and limits.

Preserved against PR #188: foundation source/schema, native definitions, legacy
Ferrite generation/presentation/extraction, world state/exterior, ship/hatch,
machines/inventory/progression/saves, approved Cuprite prototype and original artwork,
historical evidence and runner controls. No generated caches or retained successful
check logs are added. Historical Python guards are not repaired, weakened or repinned.

Deferred: activation, shared presenter, snapping/occupancy, mining/research,
Carbite artwork, Ferrite redesign/migration/retirement, save/terrain redesign,
environment classification and runtime/graphical acceptance. No new resource
becomes visible or mineable.
