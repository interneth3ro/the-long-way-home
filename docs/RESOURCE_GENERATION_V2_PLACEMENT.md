# Resource Generation v2 extractor anchors

PR 5 on `codex/resource-generation-v2-extractor-anchors`, pending owner review
and merge. Base: `5e88e774f13d80befe63c5fb24c0cace24e35f3f` (merged PR #190).
Decisions 7A and 7C remain: one permanent extraction anchor per deposit;
technical readiness and gameplay activation are separate.

## Geometry and targeting

[`ExtractorAnchorRules`](../construction/extractor_anchor_rules.gd) consumes
unchanged [native descriptors](RESOURCE_GENERATION_V2_CONTRACTS.md). Each
`Rect2i` anchor is exactly 4×4 construction cells at 32 world units per cell,
or 128×128 units. The top-left is authoritative, including negative coordinates
and origins that are not multiples of four. Artwork and extraction-point sprites
are never geometry or eligibility inputs.

`target(source, cursor)` uses the existing generator's bounded `query` API over
a 64×64 world-unit square around the cursor. Its existing conservative halo
includes cross-region members. There is no new owner search, generation algorithm
or presenter query. `select(cursor, admitted_deposits)` filters at most 775
returned members using squared Euclidean distance to the nearest point of each
closed logical rectangle. The **32-unit tolerance** is inclusive. At corners,
being 32 units beyond both axes fails. An interior cursor has zero distance.
Equal distance resolves by ascending canonical deposit ID. No nearest-center
fallback or distant snapping exists. The tolerance is an initial inspection
value requiring owner evaluation before gameplay integration.

The selector considers occupied and incompatible deposits for feedback. It never
skips the nearest selected deposit to offer a farther available one. No candidate
returns an empty target. Rotation is absent from selection; a 4×4 square keeps
its top-left through all four turns.

`rejection(source, ticket, definition, cell, turns, occupant, gameplay_eligible)`
resolves the exact deposit ID through `descriptor_by_id` again, checks generator
instance/policy, authoritative geometry, explicit compatible resource, Extractor
identity, exact footprint/cell alignment and occupancy. Its activation argument
defaults to **false**. An otherwise valid inactive anchor returns `Inactive resource`.
No current gameplay caller invokes this contract or supplies activation authority.

## Isolated transaction and preview harness

[`extractor_anchor_inspection.gd`](../scenes/experiments/resource_generation_v2/extractor_anchor_inspection.gd)
is an unconnected, nonvisual inspection subclass of `PlanetWorldState`. There is
no scene, hotbar entry, normal construction mode or automatic dispatch. It is the
equivalent validation harness for this PR, rather than a graphical preview.

`configure(source)` accepts an immutable ready ordinary/starting generator only
when no machine or transaction exists and its seed matches the inherited world
seed. Configuration rejects mismatches without changing context. Preview and
confirmation also recheck the current generator/world seed before targeting or
validation. This inspection-only check reads the generator's existing `_seed`
input; no production generator or descriptor API is changed. Reconfiguration
increments an epoch.
`preview(cursor, definition, turns, context)` returns a reason, exact logical
bounds and a pending ticket containing source instance, policy, epoch, session
seed, deposit ID and anchor rectangle. Empty reason means available **for
inspection**. Tickets are transient process-local values, not save data.

`inspect_rejection` is shared by preview and confirmation. In addition to logical
validation it checks overlap against the inherited authoritative machine records,
range, explicit obstacle/player clearance and actual packaged inventory identity
and quantity. The context requires `player_point: Vector2`, finite nonnegative
`range`, `obstacle_clear: true`, `player_clear: true` and `inventory: InventoryState`.
Missing or invalid context fails closed. These are **synthetic environmental
inputs**, not live physics checks. The harness explicitly bypasses the activation
gate only for inspection; it grants no gameplay eligibility.

`confirm(ticket, definition, cell, turns, context, inventory)` reuses that validator
with the actual transaction inventory, never selects another target, and rejects
busy/repeated/occupied calls before removal. Input/recipe machines are excluded.
Under the inherited transaction guard, it removes one item without notification,
registers the machine and claim, advances the inherited ID, then notifies inventory
and machines before releasing the guard. No asynchronous work or progression
deployment event occurs. Failed removal publishes no record or claim. Normal
`deploy_machine_instance` always returns zero on this subclass; production is a
no-op even when the unchanged legacy Extractor definition has Ferrite output.

## Occupancy and recovery

The existing `_machines` registry remains authoritative. Successful inspection
records add `v2_deposit_id`; `_claims` is only a deposit-ID-to-machine-ID index,
not another machine registry. Lookup is constant work and confirms that the
machine still exists. It does not depend on chunks, visuals or spatial proximity.
Overlap checks use the existing machine set; their cost is linear in deployed
machines, matching existing construction. Generator work retains its existing
bounded region/query budgets. These are work bounds, not performance results.

There is no independent claim setter. Claims arise only within successful
deployment. Duplicate/reentrant confirmations encounter the guard or occupied
index before inventory removal. World replacement is rejected while occupied.
Recovering uses the unchanged parent recovery transaction and same packaged item
identity. Failed inventory returns or range checks preserve the machine/claim.
Parent recovery removes the machine before notifications, so occupancy already
reads zero during callbacks; the subclass then retires the index entry. A future
placement receives a new monotonic machine ID. No deposit identity, position,
quantity, generation input or reservation changes.

## Validation and preservation

[`static_extractor_anchor_test.py`](../tests/static_extractor_anchor_test.py)
contains 13 nonexecuting Python tests: source contracts, independent geometry and
snap vectors, bounded queries, exact revalidation, transaction ordering, isolation,
recovery delegation and baseline preservation. Actual results are recorded in the
draft PR. PR #190 documented 21 broad-suite failures. Old guards are not repaired,
weakened or repinned. Actual broad-suite results and additional scope conflicts
are reported separately in the draft PR.

The initial Python invocation omitted `-B` and created or updated ignored test
bytecode. The housekeeping guard reports a local cache mismatch; a subsequent
read-only audit found 25 existing `tests/__pycache__/` paths differing from the
Stage 2A historical pins. Pre-run cache bytes/absence were not captured, so no
claim of exact cache preservation is made. These files are retained, excluded
from Git and not cleaned up. Subsequent Python invocations use `-B`.

Focused pre-merge verification reproduced the housekeeping failure locally but
not in a fresh isolated checkout of reviewed head `2da11f7`: the unchanged four
housekeeping tests passed there using `python -B`, with no bytecode files created.
This isolates the observed failure to local material; it does not restore caches,
resolve their historical provenance or mark the local incident fixed.

[`extractor_anchor_test.gd`](../tests/extractor_anchor_test.gd) authors geometry,
negative coordinates, tie order/tolerance, rotation, alignment, compatibility,
seed/policy/source invalidation, occupied/overlapping/blocked feedback, inventory
failures, reentrancy, repeated clicks, recovery/release and representative-seed
reservation/query assertions. **Not executed** and absent from every runner.
Python source checks do not establish Godot parsing, runtime determinism, engine
or graphical PASS. No Godot executable, import, scene or performance probe ran.

File-by-file changes:

| File | Purpose |
| --- | --- |
| `construction/extractor_anchor_rules.gd` | Reusable logical geometry, targeting and validation. |
| `scenes/experiments/resource_generation_v2/extractor_anchor_inspection.gd` | Isolated preview/transaction/occupancy harness using existing machine/recovery state. |
| `tests/static_extractor_anchor_test.py` | Focused static guards and independent math. |
| `tests/extractor_anchor_test.gd` | Authored, unexecuted behavioral assertions. |
| This document | Interface, activation, validation and deferred integration record. |
| README and existing v2 documents | Current milestone links and scoped status reconciliation. |

All preexisting source, scenes, assets, historical tests, runner controls, machine
definitions and inventory code remain byte-identical in Git to the PR #190 base.
Legacy Ferrite placement, production and recovery are unchanged. The shared
presenter, Cuprite artwork/prototype, seven starting reservations, save/progression,
ship and terrain remain unchanged. No caches, runtime outputs or successful check
logs are committed. No cleanup or deletion of unknown/ignored files or historical
evidence is performed; the local bytecode incident is disclosed above.

## Deferred gameplay integration

A separately approved activation PR must install authoritative v2 generation and
eligibility in real world state, wire pending tickets into the normal physics-frame
controller, and adapt live planetary ground, range, blocking-layer and player-safety
checks without changing legacy semantics. It must integrate claim registration
and release under the existing production world transaction guard, validate current
inventory, and explicitly decide resource output/activation. The synthetic harness
must never substitute for that live environment/activation adapter.

Cuprite mining/items/output, Carbite activation, Ferrite v2 migration/retirement,
depletion, save redesign, terrain streaming and research/progression are excluded.
The final dedicated v2 test-suite stabilization PR remains required after the
remaining implementation and migration work. Runtime and graphical verification
need separate authorization under [the execution policy](LOCAL_TESTING.md).
