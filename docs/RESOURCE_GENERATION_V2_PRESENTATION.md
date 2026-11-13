# Resource Generation v2 presentation and Cuprite inspection

PR 4 merged in PR #190 at `5e88e774f13d80befe63c5fb24c0cace24e35f3f`,
based on `f82298e1874ace843455f453aba2de583d2b8f5d`.
Decision 7C permits technical inspection separately from gameplay activation.
No gameplay caller, resource registry, mining, construction, inventory, save or
progression integration is added. The existing exterior, terrain streaming,
legacy Ferrite presenter and accepted stationary Cuprite prototype are unchanged.
PR 5 adds separate [anchor targeting and occupancy contracts](RESOURCE_GENERATION_V2_PLACEMENT.md),
merged in PR #191. Milestone 6's [world-state integration](RESOURCE_GENERATION_V2_INTEGRATION.md)
is pending review and merge, with no presenter or inspection wiring changes.
The presenter remains artwork-only and supplies no placement authority.

## Presentation admission and registration

[`ResourcePresenterV2`](../scenes/world/resource_presenter_v2.gd) is a disposable
`Node2D` view of an immutable `OrdinaryResourceGenerator` or its merged
[`StartingResourceGenerator`](RESOURCE_GENERATION_V2_STARTING.md) extension.
Generation remains authoritative. The presenter never creates `ResourceDeposit`
objects or supplies extraction/placement eligibility.

`configure(source, world_seed, presentation_definitions)` replaces the context
and removes all previous visuals, descriptors, catalogs and texture references.
The source must be a fresh immutable instance whenever seed, policy, generation
definitions or protection changes. The seed argument must match generated
locations; each complete parent is structurally validated, with seed and policy
checked before registration. Policy changes observed during work fail closed.
The presenter does not introspect private generator state or create another
authoritative registry. Calling code owns context replacement.

The supplied presentation definitions are an explicit subset of generated types.
Excluded types remain in generation, reservations and conflicts but never receive
visuals. A selected type must have valid approved artwork; an empty/missing catalog
fails configuration, with no borrowed artwork. Ferrite and Carbite have no v2
artwork catalog and cannot be selected by the provided inspection harness.

[`ResourcePresentationCatalog`](../scenes/world/resource_presentation_catalog.gd)
reads bounded JSON catalogs from `WorldResourceDefinition.presentation_catalog`.
Version 1 has `resource_id` and 1–8 `variants`, each with canonical `id`, PNG
`artwork`, lowercase `sha256`, integer source-pixel `size`, positive uniform
`scale` and world-unit `offset`. Only JSON is currently implemented; canonical
`.tres` references allowed by the foundation fail explicitly here.

Per-member metadata may select `variant_id` and assert the configured
`catalog_ref`. Unknown variants or mismatched catalog references fail admission.
With no variation specified, the lexical first variant ID is used; registration
does not depend on region-query order or random state. Metadata never feeds back
into generation, identity, ownership or placement policy.

The registration record contains resource ID, stable deposit ID, original
`anchor_cells`, logical world bounds, artwork path/hash/source size, scale, offset,
variant ID, centered sprite position and conservative full-canvas illustrated
envelope. It is reconstructed from validated complete locations; it is a view,
not a resource-existence API.

For a top-left construction cell `(x,y)`, logical bounds are
`Rect2((32*x,32*y),(128,128))`. The extraction center is `(32*x+64,32*y+64)`.
Sprite position is that center plus the artwork offset. The full-canvas envelope
is sprite position minus half the scaled pixel dimensions, with scaled dimensions
as its size. Sprites use local linear filtering and z = -5. The presenter root
must have an identity world transform: a transformed ancestor intentionally
transforms the entire view and is outside this world-coordinate contract.

## Cuprite registration and preservation

The [single approved catalog](../scenes/world/resource_presentations/v2/cuprite.json)
uses exactly the existing 1536×1024 PNG, SHA-256
`6a3ed462b0da325b0dc334b0fb0f5d467242d7758dbd71bfe2aa46dff8b531fe`,
scale `0.225`, offset `(0,16)`, and variant `prototype_v1`. Its canvas is
345.6×230.4 world units. The implied 4×4 logical extraction anchor remains
128×128 units, centered 16 units above the painted canvas center. No stationary
prototype position is used for generated placement.

Only a presentation-catalog reference is appended to the Cuprite native
definition. Resource identity, abundance, geology and all generation policy remain
unchanged. Source PNG, import metadata, prototype scene and stationary Extractor
reference retain their existing bytes and transforms. Artistic acceptance of the
[prototype](CUPRITE_VISUAL_PROTOTYPE_V1.md) does not establish acceptance of the
new procedural view.

The approved canvas exceeds the generator's 256×256 conservative policy envelope.
Presentation plans owners using the actual catalog reach, then culls using the
actual illustrated envelope. It never enlarges generation clearance, moves a
deposit, suppresses a conflicting resource, or changes identity. Actual painted
overlap with terrain, authored obstacles or other deposits still needs owner
visual review. Resolving generation-clearance policy would be separate scoped work.

## Bounded lifecycle

`request(area)` cancels the old token and removes old sprites/descriptors before
planning the new area. Areas must have finite ends, positive dimensions and axes
at most 6,144 units, and pass the generator's coordinate/64-owner admission after
artwork reach expansion. This is rejection, not silent truncation.

`step(token)` performs one region reconstruction, one complete-location admission
(at most three members), one bounded ordering pass, or one texture/sprite commit.
It never runs an unbounded sprite loop or asynchronous coroutine. Region snapshots
hold at most 11 locations (four ordinary plus at most seven starting groups);
registrations hold at most 775 members (64×4×3+7). Repeated members across owner
queries deduplicate by deposit ID; inconsistent duplicates fail closed. Final
commit order is lexical deposit ID. The generator's separate 32-region cache and
its complete seven-reservation policy remain unchanged.

There are at most eight selected resource catalogs, each at most 16 KiB with
eight variants, source-image axes at most 2,048 pixels and illustrated reach at
most 512 units from the anchor center. Texture admission checks source length
(at most 16 MiB), SHA-256, imported `Texture2D` availability and dimensions before
creating a sprite. The explicit texture cache evicts its oldest insertion at eight
entries. Attached sprites retain their textures until retirement; eviction does
not imply immediate engine texture-memory release. Node and reference cardinality
are bounded; no memory-byte, frame-time or performance certification is claimed.
Raw-source hash checks make this an editor/source inspection path; packed exports
with transformed/omitted source files are not certified.

`cancel()` invalidates the token, clears pending work and registrations, and
detaches/frees sprites immediately. Texture/catalog caches remain bounded for
the same context. `dispose()`, reconfiguration, errors and tree exit also clear
caches and release the source. During tree exit, sprites are hidden and queued for
deletion without mutating the exiting hierarchy. Old tokens cannot republish. Every area replacement
rebuilds visuals incrementally; rapid movement can cause visible gaps/flicker.
This conservative inspection implementation does not promise seamless movement
or alter normal terrain streaming/startup readiness.

## Explicit development inspection

The [standalone scene](../scenes/experiments/resource_generation_v2/cuprite_inspection.tscn)
and [script](../scenes/experiments/resource_generation_v2/cuprite_inspection.gd)
are unreferenced by ordinary gameplay. The exported developer property
`development_inspection_enabled` defaults to false. Execution requires both that
explicit opt-in, an editor-capable build, and the harness itself as current scene.
This is an editor inspection property, with no user-facing gameplay control,
persisted flag, research requirement or activation state.

Default seed **26026** matches `PlaythroughState` and `PlanetWorldState`.
The harness passes all three unchanged native definitions, the exact authored
`ResourceGenerationCrashSite.protected_bounds()` and ship reference `(-384,-192)`
to `StartingResourceGenerator`. It requires the complete **3 Ferrite / 2 Carbite /
2 Cuprite** reservation counts before presentation. Only `[CUPRITE]` is selected
for presentation. Reservations and ordinary generation remain identical when the
inspection is disabled. The harness has its own camera and one presentation step
per frame, with quantized area replacement; it loads no gameplay world, ship,
terrain, construction, player or machine scene. Cyan guides mark reserved Cuprite
anchors/centers; the white marker is the ship reference. These guides are
presentation only. Ordinary Cuprite within the requested area can also render.

For a **later separately authorized owner graphical inspection**:

1. Open this isolated scene in the editor, enable its developer property, and use
   Run Current Scene. Do not change the project main scene or ordinary exterior.
   This document does not authorize an agent engine launch.
2. Verify there are no parser/import/runtime errors; disabled inspection must show
   its disabled message and construct no generator or presenter.
3. With opt-in enabled, use arrows to pan. Check the approved artwork, centered
   cyan 128×128 anchor and canvas center offset `(0,16)`. Inspect painted overlap
   and transparency. This fixture has no terrain backdrop or Extractor reference;
   use the preserved prototype separately for its accepted artistic comparison.
4. Move across query boundaries and revisit areas; check no duplicate sprites,
   lingering off-area visuals or errors. Reopen with another signed seed and
   verify the complete reservation counts and absence of previous-world visuals.
   Generator/renderer determinism still needs separately authorized assertions.
5. Disable the property and restore the scene to its committed default. Ordinary
   F5 gameplay must retain exactly its previous Ferrite behavior and existing
   stationary Cuprite prototype, with no new generated v2 resource or activation UI.

No graphical run, texture import, gameplay check or performance probe was performed
by the agent. Turning on this property does not widen repository execution authority.

## Validation and file scope

The [focused Python suite](../tests/static_resource_presenter_v2_test.py) checks
source contracts, independent registration arithmetic, approved PNG identity and
dimensions, catalog selection, cancellation/budget guards, isolated wiring,
preservation and unchanged runner dispatch. These checks execute no project code.
The [GDScript assertions](../tests/resource_presenter_v2_test.gd) cover actual
registration, duplicate/reversed owner responses, movement, cancellation, seed and
policy changes, admission failures, work limits, complete reservations and disposal.
They are authored **but not executed**, and are not added to any runner.
The draft PR records actual static results and historical guard failures separately.

File-by-file scope:

- `resource_presentation_catalog.gd`: bounded catalog admission and pure registration.
- `resource_presenter_v2.gd`: bounded incremental descriptor view and lifecycle.
- `resource_presentations/v2/cuprite.json`: one approved frozen artwork registration.
- `resource_definitions/v2/cuprite.tres`: additive catalog reference only.
- `cuprite_inspection.gd` / `.tscn`: disabled standalone editor inspection context.
- New Python and GDScript test files: nonexecuting checks and unexecuted assertions.
- This document, README and existing v2 documents: scope/status links and boundaries.

Preserved: merged generator/descriptors/protection, approved assets and import
metadata, legacy Ferrite gameplay/presentation, exterior/terrain streaming, ship,
machines/construction/inventory/progression/saves, historical evidence and all
test-runner safety controls. Historical tests are not weakened, repinned or repaired.
No third-party dependency, generated cache, permanent evidence or routine success
log is added. No performance or runtime-determinism claim is made. Deferred work
includes gameplay activation/mining, snapping/occupancy, Ferrite redesign/migration,
Carbite artwork, persistence, terrain-backed acceptance and runtime verification.
