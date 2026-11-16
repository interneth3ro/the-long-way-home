# Resource Generation v2 presentation and Cuprite inspection

## Three-resource live cutover (pending merge)

`codex/ferrite-v2-live-authority` configures the existing `ResourcePresenterV2`
with Ferrite, Cuprite and Carbite. The live Ferrite definition references
[`ferrite.json`](../scenes/world/resource_presentations/v2/ferrite.json).
PR #212's approved 1536x1024 RGBA image is unchanged, SHA-256
`bd0f7696d64f8f96dca3cbfa0baecb7bba7da96876242eabc5056916574825a0`.
Its scale 0.225, offset (0,16), linear filtering, z-index -5 and 128x128 logical
anchor are unchanged. Cuprite and Carbite artwork/catalogs are unchanged.

The dedicated legacy presenter, authored Ferrite sprite, legacy request token,
readiness gates, lookahead work and polygon clipping are retired. Existing shared
catalog admission, bounded paged descriptor queries, sprite retention, cancellation
and reattachment serve all three resources. Construction highlights use deduplicated
V2 anchor rectangles and the existing shared highlight layer/ghost feedback.
Initial preparation and arrival receipts bind the current shared resource request;
completion also requires the presenter's current generation context. Terrain
publication, loading square, failure handling and transition protections remain.

The [PR #212 isolated preview](../scenes/experiments/resource_generation_v2/ferrite_inspection.tscn)
remains available for artwork inspection. Earlier sections below retain their
historical scope; unchanged-legacy and missing-catalog statements no longer describe
this branch. See [authority and legacy disposition](RESOURCE_GENERATION_V2_INTEGRATION.md#ferrite-live-authority-cutover-pending-merge).
Godot parsing, graphics, streaming/revisits and gameplay acceptance remain unverified.



The earlier sections below record the isolated PR #190 implementation.
[Milestone 8](#milestone-8-normal-gameplay-pending-merge) supersedes its lack of normal gameplay wiring.
The [Carbite production integration](#carbite-production-integration-feature-branch-pending-merge)
extends normal world presentation and extraction; earlier Cuprite-only scope
descriptions below remain historical.

PR 4 merged in PR #190 at `5e88e774f13d80befe63c5fb24c0cace24e35f3f`,
based on `f82298e1874ace843455f453aba2de583d2b8f5d`.
Decision 7C permits technical inspection separately from gameplay activation.
No gameplay caller, resource registry, mining, construction, inventory, save or
progression integration is added. The existing exterior, terrain streaming,
legacy Ferrite presenter and accepted stationary Cuprite prototype are unchanged.
PR 5 adds separate [anchor targeting and occupancy contracts](RESOURCE_GENERATION_V2_PLACEMENT.md),
merged in PR #191. Milestone 6's [world-state integration](RESOURCE_GENERATION_V2_INTEGRATION.md)
merged in PR #192, with no presenter or inspection wiring changes. Milestone 7
connects live construction/occupancy through world-state descriptors, pending merge.
Its construction-only anchor outline is independent of this artwork-only presenter,
which supplies no placement authority. Normal Cuprite artwork remains deferred.

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


## Milestone 8 normal gameplay (pending merge)

`PlanetExterior` now configures the existing `ResourcePresenterV2` with
`configure_world(state, [CUPRITE])`. The isolated generator-based `configure` API
remains available for the preserved inspection harness. The live adapter receives
only current-token context and bounded copied descriptors from `PlanetWorldState`;
the underlying generator is private and no second generator exists.

The exterior derives the presentation rectangle and loaded mask from attached
terrain chunks. A changed chunk set requests a new bounded job; sprites whose
illustrated envelopes no longer intersect loaded terrain retire immediately.
Live requests retain valid existing registrations/sprites within the requested
area, avoiding duplicate nodes and blanking retained deposits during streaming.
New sprites require loaded terrain. No discovery, research, proximity or occupancy
state participates in visibility. Initial preparation and arrival wait for Cuprite
presentation as well as existing terrain/Ferrite work before reporting readiness.
Explicit cancellation retires work and completion. Temporary tree exit retires
work tokens while preserving valid live presentation for same-context reuse.

Each live step performs one fixed 1536-unit page query grown by approved artwork
reach, one candidate admission, one ordering pass or at most one texture/sprite
publication. Query results retain the authority's 64-owner/775-descriptor bound.
The live adapter has separate whole-window limits: 26,624 units per axis (the
supported radius 4 plus retention 2, or 13 actual 2,048-unit chunks), at most
361 query pages and 5,815 accumulated descriptors/sprites. A maximum interval
touches 19 aligned 1,536-unit pages; their artwork/query halo touches at most
22x22 owners, each with at most four slots of three members, plus seven starting
reservations. Catalog and texture limits are unchanged. The isolated inspection
adapter retains its 6,144-unit, 64-owner and 775-descriptor limits.

This startup correction is pending review in PR #195. The owner-reported New Game
failure was traced to the shared 6,144-unit guard rejecting live terrain windows:
the initial 7x7 neighborhood spans 14,336 units. Live requests now select the
separate whole-window limits while continuing to issue one small page query per
query step. This changes no terrain/generation policy or authority-query limit.

Current maintained live-window coverage on PR #203 (pending merge) contains four
Python methods. Only the whole-file generation/terrain preservation method is
retired; dimensions, signed-window geometry, page/owner budgets and adapter-limit
assertions remain unchanged. The five-check and 20-test PASS counts in the
following paragraph are original PR #195 evidence, not new validation results.

[`static_resource_live_window_test.py`](../tests/static_resource_live_window_test.py)
passes five nonexecuting checks for actual dimensions, signed windows, page/owner
bounds, adapter-specific limits and unchanged generation/terrain controls. Together
with Cuprite and fixture-typing checks, 20 focused static tests pass. Live-window
GDScript assertions are authored in `tests/cuprite_gameplay_test.gd` but unexecuted;
no Godot parsing, import, gameplay, graphical or performance check was run by the
agent. The original broad-suite record is not a rerun of this correction.

Page overlap deduplicates authoritative deposit IDs. Context retirement
clears visuals and reports failure through the existing exterior terrain-failure
path. These are bounded-work contracts, not measured performance results.

Both adapters share catalog admission, registration, hash/dimension validation,
texture loading/cache and sprite creation. Approved Cuprite world PNG/catalog,
scale `0.225`, center offset `(0,16)` and all generation inputs remain unchanged.
The separate supplied ore icon is used only by shared inventory/material UI;
see [output and asset identity](RESOURCE_GENERATION_V2_INTEGRATION.md#milestone-8-cuprite-gameplay-pending-merge).
Legacy Ferrite presentation remains independent and unchanged. Carbite has no
selected catalog or production path. No placement or production authority is held
by the presenter.

Focused static checks pass; actual world presentation/streaming assertions are
authored in `tests/cuprite_gameplay_test.gd` but unexecuted. No Godot parsing,
import, graphical, gameplay or performance claim is made. The historical isolated
inspection checklist above describes its original scope, not Milestone 8 normal
F5 behavior. Approved canvas-versus-clearance visual review remains outstanding;
no artwork scale/offset or deterministic clearance policy was changed.


### Obsolete live prototype removal (PR #195, pending merge)

Following owner runtime acceptance of generated Cuprite, Decision 11A removes
only `GroundObjects/CupriteVisualPrototype` from `planet_exterior.tscn`, its unused
PackedScene declaration and its instance-only editability entry. The scene's
`load_steps` is adjusted accordingly. The reference prototype scene, approved PNG,
v2 catalog/registration and generated presenter remain unchanged; other authored
objects are preserved. This removes the redundant manual illustration, not an
authoritative deposit. Starting preferences/identity are described in the
[layout correction](RESOURCE_GENERATION_V2_STARTING.md#cuprite-layout-correction-pr-195-pending-merge).

### Cached exterior presentation lifecycle (PR #195, pending merge)

Completed Cuprite presentation now survives initial preparation's detachment and
subsequent cached exterior visits. Live presenter tree exit cancels queued work
and advances its token, retaining registrations, child sprites, textures and
catalogs only while the world generation context remains valid. Reattachment
rearms completed presentation with the new token rather than querying deposits
and rebuilding sprites again. Interrupted work remains incomplete and restarts
through the normal bounded request path; explicit arrival cancellation continues
to clear registrations/visuals and reset the exterior's presentation coverage.

`configure_world` reuses state only for the same `PlanetWorldState` instance,
opaque generation token and seed, with the same resource/catalog references and
equal freshly admitted catalog contents. A changed, missing or incompatible
configuration follows destructive configuration/admission; invalid inputs fail
closed. Explicit `dispose`, configuration replacement, failure and actual node
deletion release retained state. Detached scenes remain owned by the existing
transition controller and are freed during session retirement.

The exterior reuses completion only when its attached-chunk coverage is unchanged
and the presenter reports completion for its current token/context. Changed
coverage still applies the loaded mask, immediately retires off-terrain sprites
and issues a bounded streaming request. Terrain publication, legacy Ferrite
readiness, fresh arrival-generation receipts, cancellation guards and Dave's input
lock are preserved. Neither the starting policy/search ceiling nor gameplay,
fade timing, terrain architecture or approved artwork changes.

Eight focused nonexecuting contracts in
[`static_cuprite_presentation_lifecycle_test.py`](../tests/static_cuprite_presentation_lifecycle_test.py)
pass. The authored
[`cuprite_presentation_lifecycle_test.gd`](../tests/cuprite_presentation_lifecycle_test.gd)
exercises actual presenter/exterior initialization and resource service with a
descriptor-query fixture and supplied chunk coverage: completed initial work,
three detach/reattach visits without new queries, object/cache identity,
interrupted and explicit cancellation, streaming unload/reload, world replacement,
invalid context, stale readiness receipts, disposal and actual node retirement.
It does not generate the initial terrain neighborhood or certify full transition
behavior. It is unexecuted and absent from approved runners. No Godot parse,
headless, graphical or performance verification was performed; timing improvement
is unmeasured and owner F5 runtime acceptance remains required.

Related executed checks: eight layout and two fixture-typing checks pass; the
gameplay/window modules have 16 passing test methods and two failing methods
(three whole-source preservation subcases). Two cases already reject the approved
starting-layout change; the additional case freezes the exterior source before
this approved lifecycle edit. These guards remain unchanged and failures are
reported, not treated as functional/runtime PASS. The full historical discovery
suite was not rerun for this follow-up.


<a id="carbite-world-presentation-preview-pending-merge"></a>

## Carbite production integration (feature branch, pending merge)

PR #210 merged the shared Carbite world presentation at
`305e17e405bae955c6e2086f58d87e89206bb2cb`. That milestone excluded extraction.
`codex/carbite-gameplay-integration` promotes the same presentation and adds
Carbite Ore through the existing Extractor and inventory paths, merged in PR #211
at `b21cd0490c1ece3c5905843fd593ad8f8d38b034`; owner acceptance remains unrecorded.
The retained filename and `candidate_v1` identifier are
stable catalog references, not a restriction on production use.

The owner-approved `carbite_deposit_candidate_v1.png` is copied byte-for-byte to
[`assets/environment/exterior/carbite/`](../assets/environment/exterior/carbite/carbite_deposit_candidate_v1.png).
It is a 1536x1024, 8-bit RGBA PNG with SHA-256
`f2c72ef73cd9dbdb9fc15faf3d3cd4aeeb15d135f9944c39c59970ad93948022`.
The supplied image has alpha values from 0 through 254; transparency is preserved,
including its partially transparent painted terrain fringe. It is not resized,
repainted or regenerated. Import metadata is authored from Cuprite's existing
settings: lossless texture, no mipmaps, alpha-border fixing, no premultiplied alpha
and no size limit. Godot has not generated or verified an imported texture here.

The [Carbite catalog](../scenes/world/resource_presentations/v2/carbite.json)
uses the existing version-1 schema with one `candidate_v1` variant, scale 0.225
and offset (0,16). Its centered image rectangle is 345.6x230.4 world units;
registration uses the existing 128x128 V2 logical anchor. The unchanged shared
presenter supplies linear filtering and z-index -5, matching Cuprite. Production
promotion preserves these scale and offset values; visual acceptance is unrecorded.

The existing Carbite definition references this catalog. Exterior initialization
configures the same `ResourcePresenterV2` for Cuprite and Carbite; it consumes the
already authoritative descriptors through the existing world-state query API.
There is no separate presenter, spawn path, teleportation or Carbite-specific UI.
The disabled historical Cuprite-only harness remains Cuprite-only. Generation
weights, starting guarantees (3 Ferrite, 2 Carbite, 2 Cuprite), identities, placement,
legacy Ferrite visuals, shared failure checks and streaming lifecycle are unchanged.

The shared Extractor accepts Ferrite, Cuprite and Carbite. The packaged Ferrite
output remains unchanged. `PlanetWorldState.extractor_output_item()` resolves
the committed deposit through current V2 authority before mapping Carbite to
[`inventory/carbite_ore.tres`](../inventory/carbite_ore.tres). Cached resource labels
and presentation metadata grant no extraction authority. Exact identity, token,
anchor, compatibility and occupancy validation remain; unavailable or unsupported
output fails closed with no V2 fallback to packaged Ferrite.

Carbite produces one ore per second (60/min) into the existing 20-item buffer.
Generic inspection, collection and recovery use the same resolved item. Inventory
rejection preserves stored contents and claims; unresolved stored output cannot
be collected or recovered until authority is restored. No production, storage or
transaction implementation is duplicated.

The owner's unchanged inventory icon is
[`assets/items/carbite_ore.png`](../assets/items/carbite_ore.png): 256x256, 8-bit RGBA,
alpha range 0-255, SHA-256
`002eb84e1ccfc9bf63b54ee97e9ec4af6e176c25c430cd65158e58e8266ac17b`.
`ItemPresentation.ICONS` supplies inventory and inspection artwork. Its authored
import sidecar matches Cuprite's inventory settings, including mipmaps, with a
unique UID and source-specific import destination. No texture import was run.
Carbite Briquettes, Smelter recipes, thermal research, automated power generation,
distribution changes, Ferrite migration and durable save migration are excluded.

Seven focused nonexecuting tests in
[`static_carbite_presentation_test.py`](../tests/static_carbite_presentation_test.py)
cover artwork/catalog/import identity, shared configuration, unchanged generation
and presentation, item/icon identity and the exact shared gameplay extension.
Obsolete incompatibility/output prohibitions are replaced with support assertions;
authority, transaction, geometry and legacy regression protections remain.
The existing `cuprite_gameplay_test.gd` exercises both resources, including starting
and ordinary Carbite authority, production, inspection, collection, recovery and
failure cases. Mixed-resource lifecycle assertions extend
`cuprite_presentation_lifecycle_test.gd`. These GDScript assertions are authored
only, unexecuted and absent from approved runner dispatch. The old live Extractor
fixture retains incompatibility coverage through a restricted machine definition
and now expects current Cuprite production.
Static checks do not establish Godot parsing, texture import, runtime streaming,
alpha blending, apparent scale, placement feedback or gameplay acceptance. No
Godot execution, runner amendment or expanded runtime authority accompanies this
integration. The metadata smoke package remains fixed and inactive; its static
dependency-gap expectation records the additional Carbite ore preload. The
unapproved PR #201 behavioral closure also gains that resource dependency;
no manifest, runner or execution authorization changes.

### Owner acceptance (requires separate execution authorization)

1. Open this feature checkout using the approved Godot 4.7.2 Standard environment.
   Run Project (F5), choose New Game, and exit the ship through the normal flow.
2. Explore the starting region for a dark Carbite deposit. The unchanged starting
   layout reserves two Carbite anchors with centers 384-2304 world units from the
   ship reference; this integration adds no marker or special spawn.
3. Compare its apparent size with generated Cuprite. Both use scale 0.225 and the
   same source dimensions, but their painted silhouettes can read differently.
4. Inspect the transparent fringe and shadow against terrain for dark halos,
   rectangular edges or excessive translucency. Inspect the central surface's
   positioning relative to the 128x128 anchor when previewing an Extractor.
5. Walk across deposit and terrain-chunk edges, move away and return, and revisit
   the exterior after entering the ship. Check clipping, duplication, disappearance
   and alignment as the normal streaming lifecycle runs.
6. With a recovered Extractor available, place it on Carbite away from overlapping
   legacy Ferrite. Check exact anchor alignment, occupied-anchor rejection,
   Carbite Ore inspection, one-second production and the 20-item buffer. Collect
   output, confirm production resumes, then recover the machine and its contents.
   Check the approved inventory icon and recheck Ferrite/Cuprite placement,
   production, collection and recovery through their existing paths.

Owner execution and visual results are not yet recorded. Report scale/offset,
blending or positioning feedback before any further artwork or gameplay changes.

## Ferrite V2 isolated artwork preview (feature branch, pending merge)

`codex/ferrite-v2-isolated-preview` integrates the owner-approved
[`ferrite_v2_production_candidate_v1.png`](../assets/environment/exterior/ferrite/ferrite_v2_production_candidate_v1.png)
byte-for-byte, based on synchronized `main` including merged PR #211.
Its SHA-256 is
`bd0f7696d64f8f96dca3cbfa0baecb7bba7da96876242eabc5056916574825a0`.
Offline decoding verifies a 1536x1024 RGBA8 PNG, 963,188 fully transparent pixels,
609,676 partially transparent pixels and 255 alpha levels (0-254). The image has
no fully opaque pixels; the bottom-left corner has alpha 1. It is not resized,
recolored, recompressed or regenerated. The import sidecar is authored using
Carbite's existing settings, with its own UID and source-specific destination;
Godot import remains unverified.

The [Ferrite catalog](../scenes/world/resource_presentations/v2/ferrite.json)
uses existing version-1 admission rules and one `production_candidate_v1`
variant. Provisional scale is **0.225**, offset **(0,16)**, giving a centered
345.6x230.4 image rectangle around a **128x128** logical anchor. The unchanged
shared presenter supplies linear filtering and z-index **-5**. Its limits,
validation and rendering implementation are unchanged.

Only the isolated
[`ferrite_preview.tres`](../scenes/experiments/resource_generation_v2/ferrite_preview.tres)
references this catalog. It matches the live Ferrite definition except for its
presentation reference. The live definition has no presentation catalog, and
`PlanetExterior` continues to configure V2 presentation for Cuprite and Carbite
only. Legacy Ferrite, the authored crash-site deposit, generation weights,
seven starting reservations, anchor geometry, deposit identities, Extractor
placement/production/collection/recovery and opening discovery are unchanged.
Historical Ferrite artwork and documentation are preserved.

The standalone [preview scene](../scenes/experiments/resource_generation_v2/ferrite_inspection.tscn)
reuses `StartingResourceGenerator`, `ResourcePresenterV2`,
`ContinuousTerrainPresenter`, `PlanetGenerator.sample_ground_material` and the
normal exterior `FollowCamera` zoom controls. It uses seed 26026, all three
definitions and all seven starting reservations. Tab visits the actual generated
anchors; there are no fabricated deposit identities or relocated sprites.
Rendering uses one shared-presenter step and at most one terrain slice per frame,
within existing limits. Each focus requests a 2048x2048 presentation area and
prepares its central terrain chunk and eight neighbors. Arrow panning is bounded
to 320 units around the focused anchor.

Terrain uses normal continuous textures, material transitions and rendering
order (terrain -11, deposits -5, optional anchor overlay 0). A neutral white
tint field excludes gameplay terrain edits and crash-site masks; this is an
unmodified procedural terrain comparison, not a reproduction of the authored
crash site. The artwork's angled overhead perspective is preserved. No live world
state, player, machines, narrative session or save is created. The scene runs
only as the editor's current standalone scene, with its inspection flag enabled;
it is not referenced by gameplay or test dispatch.

### Owner preview inspection (graphical acceptance outstanding)

The owner performs this check separately; this PR does not authorize an agent
Godot invocation or amend execution policy.

1. In the approved Godot 4.7.2 Standard editor, open
   `res://scenes/experiments/resource_generation_v2/ferrite_inspection.tscn`.
   Its `development_inspection_enabled` flag is already enabled in this scene.
2. Use **F6 / Run Current Scene**. F5 retains the normal application entry point.
   Allow terrain and deposits to finish appearing. Any input/admission failure
   stops the preview and displays a diagnostic.
3. Use **Tab / Shift+Tab** to visit all seven reserved deposits. The HUD identifies
   each resource. Compare Ferrite against Cuprite and Carbite at the same zoom.
   Initial zoom is 1.0; mouse wheel uses the normal exterior 0.5-1.5 range.
4. Use **arrow keys** to pan slightly; **A** toggles cyan 128x128 anchor outlines
   and center markers. Inspect the (0,16) registration, painted overhang, scale,
   rendering order and readability from the normal angled overhead perspective.
5. Hide anchors and inspect terrain fringes, shadows and natural transitions
   for rectangular edges, halos, excessive translucency and poor blending on
   earth and green terrain. Compare multiple Ferrite anchors. Stop with F8.
6. Record the checked commit and visual feedback, including whether scale 0.225
   and offset (0,16) are acceptable. No acceptance PASS is recorded yet.

Preview acceptance concerns artwork and provisional presentation values only.
It does **not** approve live Ferrite migration, removal of the legacy presenter,
a second live deposit representation or changes to generation/gameplay authority.
Those require a separate owner-approved scope and PR.

[`static_ferrite_v2_preview_test.py`](../tests/static_ferrite_v2_preview_test.py)
checks exact PNG bytes, decoded alpha, catalog/import identity, preview wiring,
resource references and isolation, and unchanged live authority/shared limits
against PR #211's merge revision. These are static file checks; they establish
neither Godot parsing/import compatibility nor graphical/runtime acceptance.
No Godot, headless runner, metadata dispatch or behavioral tests are executed.
