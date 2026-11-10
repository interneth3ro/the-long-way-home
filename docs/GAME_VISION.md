# The Long Way Home — Game Vision

## Status and identity

This document records approved design direction, not implemented features or an
instruction to build them during bootstrap. The Long Way Home is a story-driven
science-fiction automation adventure. Narrative drives progression; factory
construction, research, and exploration are the means through which Dave
accomplishes his goals.

## Current V2 production status

P1-P6 merged in PRs #59-#64; the verified post-P6 baseline is
`e14703e64aef961f18feba8a616acec00c4f069e`. The owner approved P7 after a
continuous six-phase rehearsal, **6/6 PASS (owner-reported)**. P8 is implemented
on `codex/p8-f5-production-cutover`, pending owner cutover acceptance and merge.

**F5 / Run Project** now starts V2 Primary through `scenes/main/main_v2.tscn`.
**F6 / Run Current Scene** with that scene open also starts V2. For the explicit
**legacy F6 fallback**, stop the game, open `scenes/main/main.tscn` and press F6.
F5 stays configured for V2. This is an editor workflow, with no startup selector.
Computer restoration is implemented on `codex/computer-restoration`, pending
owner normal-F5 acceptance and merge; see the
[approved requirements and acceptance checklist](COMPUTER_RESTORATION.md).
Agent validation is static only; no Godot launch or P8 runtime acceptance is claimed.

**P7 Observation #1 (nonblocking missed implementation):** After the Computer's
opening conversation, the player is not explicitly directed outside to investigate
the Ferrite deposit. P7 owner rehearsal passed 6/6 phases despite this gap. The
approved correction is implemented on `codex/opening-exterior-guidance`, pending
owner normal-F5 acceptance and merge: two appended Computer/Dave lines direct
Dave outside, reinforced by the initial objective description, `Investigate the
area outside the ship.` Existing Ferrite and later progression remain unchanged.
This correction remains **excluded from P8**; static checks do not establish
runtime or graphical acceptance.

See the [P8 scope and owner checklist](V2_PRODUCTION_HOST.md#p8-production-cutover-feature-branch-pending-merge).
Earlier milestone descriptions retain their historical scope and launch expectations.

## Approved visual direction

- Rich, illustrated 2D artwork in an angled overhead perspective.
- Vibrant environments, detailed machinery, and cohesive visual design across
  all assets.
- Atmospheric lighting with strong gameplay readability.
- A contextual construction grid.
- Owner-approved Dave exception: use the legacy helmeted pixel-art walking and
  idle sheets consistently across four directions. This does not change the
  broader environment direction or import legacy gameplay. Implementation is
  merged in PR #25. The owner-approved supplied-atlas rework retains the existing
  AnimationPlayer, four-direction controls and physics, initially matching current
  visual size with conservative transparency cleanup and shared foot registration.
  Its six-frame idle/walk timing starts at 5/10 FPS. Implementation is on a feature
  branch pending owner F5 acceptance and merge; legacy art remains preserved.
  See the [integration and acceptance notes](../README.md#dave-supplied-atlas-rework-feature-branch-pending-acceptance-and-merge).

## Approved primary interior V2 visual comparison

- Dark, worn, retro-industrial prisoner transport: asymmetric damaged compartment,
  moderately open center, Computer on the far wall, maintenance door left and
  exterior hatch below. Marvin stays entirely concealed beneath the approved
  lower-right wreckage placement, with no separate sprite or discovery here.
- Preserve the owner-approved 1536x1024 artwork as a static background with
  aligned full-canvas overlays. Computer starts damaged and doors closed. The
  maintenance closed panel is provisionally approved. The exterior closed hatch
  is painted into the background; its transparent overlay is intentional.
- PR #47's isolated 1.0x/1.25x/1.5x visual comparison remains available. The owner
  selected 1.25x after its tests 1-6, as recorded in the collision implementation
  request. The separate collision/navigation preview uses that fixed scale.
- Approved collision direction: smooth simplified floor perimeter, independent
  Computer/wreckage/permanent-equipment footprints and development-only outlines
  of actual physics shapes. PR #49 merged that isolated slice; owner runtime
  acceptance is separate. F5 production gameplay is unchanged.
- Future environment transitions will activate by walking across thresholds,
  without E, for room-to-room and interior/exterior travel. E remains for
  Computer, machines and intentional interactions. This supersedes the earlier
  E-to-enter doorway design; existing production doorway behavior remains until
  a separate transition slice. The collision preview's door barriers stay solid.
- Gameplay spawns, transitions, opening doors, Computer restoration, Marvin
  discovery, production cutover and legacy retirement remain deferred here.

PR #50 merged a separate development-only automatic-transition harness; owner
runtime acceptance is separate. It uses the approved 1.25x
V2 instance with safe wrapper spawns, automatic thresholds and distinct minimal
test destinations. Closed door artwork and solid barriers remain active; a
separate quick fade conceals transfer. Production routing, special first-exterior
reveal, narrative and progression are unchanged. See the
[transition acceptance guide](INTERIOR_V2_TRANSITIONS.md). This isolated work does
not establish production player access or complete the deferred V2 features.

The [preview controls and ordered owner review](INTERIOR_V2_PREVIEW.md) record
asset provenance and static-only validation limits. No Godot execution or visual
acceptance is claimed.

## Approved maintenance bay V2 visual comparison

The approved machine-free room is a gritty industrial prisoner-transport
compartment, with three empty foundations (Extractor upper-left, Smelter
upper-right, Fabricator lower-left), a central permanent repair platform and
moderate localized crash damage. Its right doorway is the eventual primary
interior connection; the closed top-wall door is reserved, noninteractive and
has no destination. Future arrivals from the primary interior should face left.

The intended apparent usable floor area is about 70-80% of Primary Interior V2,
without stretching artwork. Direct owner comparison must assess scale and style.
PR #51 added an isolated 1.0x/1.25x/1.5x visual preview. The owner subsequently
selected **1.25x** in the maintenance-bay collision implementation request.
Approved collision uses a simplified asymmetric floor perimeter, solid reserved
upper door, one floor-level repair-platform footprint, traversable flat pads and
simple footprints for substantial raised housings and permanent equipment.
Future removable machines own their collision. Workstation mechanics and positions
remain undecided. PR #52 merged that collision and a separate isolated playable
preview with a temporary right-exit barrier and C outlines; owner hands-on
acceptance is separate. The legacy production bay, machines, narrative
and routing are unchanged. Connecting the V2 rooms, gameplay arrivals,
interactions and production integration remain deferred for production. A separate
[two-room development connection](V2_TWO_ROOM_CONNECTION.md), merged in PR #54,
connects the reusable V2 rooms at 1.25x with
fixed inward-facing arrivals. It retains the existing detached-room cache with
one attached room at a time, as explicitly authorized by the owner. This
establishes no production access, machine/story persistence or V2 cutover.

P1's [opt-in production integration](V2_PRODUCTION_HOST.md) merged in PR #59;
runtime acceptance remains separate. It reuses Main's gameplay
ownership with inherited production V2 wrappers, automatic compartment travel,
the existing first exterior reveal and a V2-specific exterior return. Its initial
spawn and exterior return marker are provisional. P2 merged in PR #60 and
adds existing Computer conversation/objective parity only in the production
Primary wrapper, at an owner-accepted provisional front-facing point. The owner
reports 7/7 initial acceptance tests passed; the approved Computer cap is 45 world
units. P3 merged in PR #61 and integrates all
three approved stationary visuals into production Maintenance with removable
base collision, dormant interaction targets and presentation derived from existing
recovery/objective state. P4 merged in PR #62 and
connects only the stationary Extractor to existing recovery after Ferrite discovery.
P5 merged in PR #63 and adds Smelter recovery
after first Ferrite Ore acquisition; the existing musing remains at acquisition.
P6 merged in PR #64 and activates V2 Fabricator recovery after historical ingot
acquisition. The existing seven-second
first-ingot musing remains acquisition-only; recovery advances directly to
**Craft a Ferrite Plate.**, with no deployment objective or recovery musing.
Plate acquisition into inventory clears that guidance; output alone and Rods do
not, and `restore_computer` remains active/incomplete.
P8 selects this host for F5 on its feature branch; legacy Main remains an F6
fallback. Computer repair remains deferred. This changes no approved narrative,
inventory or progression requirements.

Future emergency/partial -> dim/moody -> operational lighting is gated by story
and electrical repairs. The approved background composition does not complete
the initial emergency state. This feature branch adds the approved stationary,
crash-worn but recoverable shipboard Extractor as an independent visual in a new
isolated preview, pending merge and owner acceptance. Optional muted amber
silhouette emphasis and removal are visual simulations only. Recovery, production
integration, other machine visuals and lighting variants remain deferred. See
[preview provenance, controls and ordered acceptance](MAINTENANCE_BAY_V2_PREVIEW.md)
for the isolated previews and their static validation limits.

## Approved construction and logistics direction

- Defined machine connection ports aligned with tile-lane centers along footprint
  boundaries. Compatible adjacent machine ports connect directly.
- Visible physical item transfers, one-way modular transfer rails, and automatic
  visual carriers.
- Explicit splitters and mergers.
- Manual rail drawing with optional smart routing.
- Route replacement with safe cargo recovery.

These are design intentions only; there are no logistics systems in the bootstrap.

## Approved narrative direction

Dave has been wrongfully exiled. Marty is his husband, and Bug is their son.
Marvin is Dave's robotic companion; Computer is the ship's computer. Dr. White is
Dave's trusted mentor and eventual betrayer. The Director provides conflict and
narrative misdirection.

Dave initially seeks justice and a return to his family, but gradually risks
becoming consumed by revenge. He awakens aboard his damaged ship, with Computer
and Marvin initially impaired. Restoring Computer is his first major objective;
Marvin's recovery unfolds gradually.

Dave's arrival on the planet was deliberately arranged. The exact conspiracy
remains under development.

## Approved dialogue and objectives direction

- Story is the primary driver of gameplay; dialogue and quest systems are
  foundational.
- Ambient conversations should generally allow gameplay to continue.
- Cinematic conversations are rare, reserved for major emotional moments.
- The conversation presentation update on `codex/conversation-ui-modernization`
  (pending merge) uses B1 typography, restrained B2 framing and the approved
  Dave/Computer/Marvin portraits. It preserves the provisional opening exchange
  and nonpausing gameplay; it adds no Marvin dialogue, choices or cinematics.
  See the [implementation and acceptance checklist](../README.md#conversation-ui-modernization-feature-branch-pending-merge).
- Dave's internal musings use a separate small, portrait-free, nonpausing
  presentation with automatic dismissal, rather than the conversation panel.
  The approved musing modernization uses a subtle B1 lower-left observation panel,
  upright DAVE label, real italic body text and content-driven sizing. Conversations
  take priority: only the newest pending observation waits, restarts on closure,
  and clears on scene transition. Milestones remain independent of presentation.
  Implementation on `codex/musing-ui-modernization` is pending merge and owner
  graphical acceptance; see the [scope and checklist](../README.md#musing-ui-modernization-feature-branch-pending-merge).
- Dave has an established personality; player choices influence his development.
- Contextual, pinnable objective tracking.
- Starter machine recovery is sequential: Extractor, then Smelter, then
  Fabricator. This restriction applies to the three introductory machines;
  later research and discoveries allow greater freedom.
- A Ship's Log records conversations, discoveries, objectives, and evidence.
- Open-ended gameplay within narrative chapters.
- A few meaningful endings influenced by major decisions.

## Approved research and exploration direction

- Traditional automated research with a science-fiction identity.
- Story-driven technology eras with freedom within each era.
- A continuous planetary surface and handcrafted interiors for significant
  exploration sites.
- Exploration and automation reinforce the same narrative.
- No combat or dungeon system is currently planned.

## Approved world and transition foundations

- Authored ship cabin, a separate compact maintenance bay and a separate
  planetary exterior with an authored crash site. The approved maintenance-bay
  milestone revises the earlier same-scene equipment-room plan. Cabin/bay
  doorway transitions are immediate and reuse the existing controller.
- Terrain tiles are 64 x 64 pixels; chunks are 32 x 32 terrain tiles,
  or 2,048 x 2,048 world units. The construction grid is independently 32 x 32
  world units; machine footprints are not constrained to one terrain tile.
- World Generation Foundation uses seeded deterministic rocky-scrubland terrain,
  a protected authored crash-site overlay, a configurable 5 x 5 chunk neighborhood
  and a modest retention margin. PR #27 is merged; owner runtime acceptance
  remains separate from agent static validation. State is in memory only.
  Building placement is added by the deployment feature described below;
  durable saves remain deferred.
- Generated, explored and surveyed are distinct concepts. Loading terrain does
  not establish exploration or surveying. Future factories must simulate
  independently of whether their terrain presentation is loaded.
- The first ship exit uses an understated fade reveal; later exits and returns
  are immediate. Completion is per playthrough and must eventually participate
  in durable saves. Merged PR #26 provides session
  state only; there is no implemented save/load workflow.

Implementation and coordinate conventions are recorded in the
[README](../README.md#world-generation-foundation-pr-27-merged).

The Weathered Earth foundation merged in PR #94. Initial owner visual
and movement-smoothness acceptance failed; merge alone does not establish renewed acceptance.
Environment Decision 16, Option B approves warm earth with subtle legacy variation.
The focused correction uses one shared provisional Base Soil texture/pass per
terrain cell and bounded brightness/warmth from the existing color halo. The
texture's brown hue dominates; legacy green becomes shading. Three inactive
provisional variants are preserved. The generator, masks, streaming, construction
and gameplay are unchanged. This is not final illustrated art or verified runtime
performance. A focused Low Green Ground Cover prototype is pending merge:
four owner-supplied candidate textures form deterministic presentation-only
clusters beyond protected gameplay space and full authored mask feathers.
The owner accepted corrected PR #95 commit 68f8c9c on 2026-10-31 as a technical
terrain foundation: deterministic distribution, four provisional variants,
single-pass rendering and spatial rejection. Owner-reported exterior movement
is noticeably improved, with smooth stationary/near-spawn/loaded-return gameplay
and normal transition/Windows responsiveness. Agent evidence remains static;
no numeric frame-time improvement is claimed. Occasional minor new-chunk stutter,
hard rectangular Earth/Green boundaries, repetition and provisional art are
accepted limitations, not final environmental presentation.

The PR #95 baseline retains one base polygon per terrain cell and warm-earth tint; gameplay
authority and streaming remain unchanged. Organic transitions, removal of obvious
64-unit squares, reduced repetition and larger-scale variation are deferred to
[issue #96](https://github.com/interneth3ro/the-long-way-home/issues/96), implemented
in a separate PR from updated main after PR #95 merges. Preserve one-pass
rendering where practical, deterministic chunk continuity and avoid expensive
overlapping full-cell passes. New vegetation and clearing remain deferred.
See the [prototype and owner checks](../README.md#low-green-ground-cover-prototype-feature-branch-pending-merge).
See the [implementation, tint formula and owner checks](../README.md#weathered-earth-textured-terrain-foundation-pending-merge).

The pending [PR #104 illustrated exterior integration](ILLUSTRATED_EXTERIOR.md)
uses the accepted baked Earth/Green presentation and preserves the corrected
PR #95 generator/gameplay behavior with a pre-initialization legacy rollback.
Native validation passed, followed by the owner's post-reboot playable-game
acceptance: **7/7 PASS**, zero failures and zero untested checklist items.
Minor initial exterior-loading stutter is explicitly accepted as non-blocking;
no formal performance benchmark was performed. See the
[final acceptance record](ILLUSTRATED_EXTERIOR.md#final-pr-104-acceptance-2026-11-01).
The integration remains pending merge and does not change approved environmental intent.

## Approved Ferrite discovery direction

- Ferrite is the first structural metal resource. The approved new artwork
  direction is **Faceted Ferrite - Slightly Raised Mineral Shelf**: broad cool
  charcoal/gunmetal surfaces, silver-gray facets, shallow fractures, restrained
  oxidation and softly irregular, connected grid-conforming fields, including
  rectangular, L-shaped, stepped and asymmetrical clustered deposits. Avoid
  tall formations. Deposits remain infinite, uniformly rich and never deplete.
- Approved introductory geometry is 10x6 **64-unit terrain cells**
  (640x384 world units / 20x12 construction cells), with a rectangular logical
  footprint. The pending production integration places it east/southeast of the
  ship at logical bounds `(128,128)..(768,512)`.
  A 6x4 terrain-cell example is illustrative, not a procedural size class.
  Medium/large deposits should be common and small deposits relatively rare;
  procedural dimensions, weights and distribution remain undecided.
  The [offline artwork prototype](FERRITE_ARTWORK_PROTOTYPE_V1.md#owner-acceptance-2026-11-02)
  received owner visual/architecture acceptance on 2026-11-02 at `1662a61`, including
  the irregular assemblies and their documented limitations. PR #123 merged.
  The [production integration](FERRITE_ARTWORK_PROTOTYPE_V1.md#production-integration-feature-branch-pending-merge)
  uses the unchanged approved large PNG with a separate rectangular resource
  footprint. Owner graphical acceptance is **PASS** at `2850c3b`; the artwork
  renders correctly and is accepted for production. Its contrast with the
  restrained terrain and placeholder Extractor is an accepted temporary
  visual-cohesion limitation. Reevaluate after additional environmental and machine
  artwork; do not alter Ferrite solely to match current placeholders.
  Deterministic procedural distribution merged in PR #126 and nearby presentation
  in PR #127, using the ten approved connected grid-conforming variants. Pending
  [3B scheduling](FERRITE_REGION_GENERATION.md#milestone-3b-hybrid-preparation--feature-branch-pending-merge)
  preserves that distribution and artwork; owner acceptance is **10/10 PASS** at
  `77f2615`, pending merge. The accepted arrival delay and residual stutter remain
  [nonblocking limitations](FERRITE_REGION_GENERATION.md#final-pr-128-owner-acceptance),
  with no measured performance gain claimed.
- One guaranteed authored deposit near the ship introduces deliberate inspection,
  Dave's engineering deduction and guidance to locate the Extractor in the
  maintenance bay. Computer does not identify the mineral in this sequence.
- Mineral-bearing ground is independent of decorative artwork and terrain chunks.
  Approved Extractors occupy 4 x 4 independent 32-unit construction cells
  (128 x 128 world units), with designated extraction point (64,64); the
  [alignment implementation](#extractor-128x128-footprint-alignment-feature-branch-pending-merge)
  is pending owner acceptance and merge. This center point must overlap
  compatible ground. Other parts may
  extend beyond the deposit. Machines may touch edges but footprints may not
  overlap. All valid points give the same rate. Construction mode highlights
  only compatible deposits; the deployment feature implements this pending
  owner verification.
- Future production: Ferrite Ore → Smelter → Ferrite Ingot → Fabricator →
  Plate / Rod / Bearing. Computer's initial repair requires Plates and Rods.
  Extraction is merged in PR #36; agent validation was static only.
  Smelting is added on the feature branch described below; fabrication remains deferred.

First Ferrite implementation is merged in PR #28. The owner reports all 15 original
manual playtests passed; final musing timing and temporary developer coordinate
HUD adjustments remain pending owner review. One-time discovery and compact
timed musings use session-only state. There is no
durable save/load. See the [implementation notes](../README.md#first-ferrite---discovery-pr-28-merged).

## Approved Extractor recovery direction

- The maintenance bay holds intact packaged Extractor, Smelter and Fabricator
  modules in three visible racks. Extractor becomes recoverable after Ferrite
  discovery; Smelter unlocks after first ore acquisition as described below.
  Fabricator unlocks after first ingot acquisition as described below.
- One-time recovery grants one Extractor and advances Restore Computer guidance
  to deployment on Ferrite. It does not complete the overarching objective.
- Dave's approved recovery musing is independently editable, using the existing
  nonpausing presentation: 0.25-second fade in, 5-second reading period,
  0.35-second fade out; transitions dismiss it.
- One inventory interface shows Materials and Equipment together. This split is
  an approved **provisional experiment pending playtesting**; it may later merge
  into one section. Item identity/quantity storage is shared, and Equipment
  supports quantities greater than one. There is no capacity or weight system
  in this milestone.

The owner-approved UI scaling foundation on `codex/hybrid-ui-scaling` (pending
merge) uses a shared HUD-root behavior with the provisional balanced hybrid
formula `U = P / sqrt(S)`, where `S = min(client_width / 1280, client_height / 720)`.
It preserves B1/B2 artwork, existing presenter ownership, world scale and camera
zoom. The owner reported all six PR #84 functional acceptance tests PASS and
approved **85% as the default UI preference** on 2026-10-29. An editor-only
temporary selector compares 75%, 85% and 100%, starting with 85% selected and no
persistence; 75% remains a valid personal preference. Tooltip sizing,
small-window readability and existing panel-overlap
limits remain explicit in the
[implementation and owner checklist](../README.md#hybrid-ui-scaling-foundation-feature-branch-pending-merge).
This is a scaling foundation, not the Machine Interface Redesign or new narrative
behavior.

The separately approved Extractor visual pilot is implemented on
`codex/extractor-inspection-pilot`, pending merge. The owner accepted its overall
layout, artwork, gauge, styling and proportions, including the header/column
dividers and aligned production-detail rows. Option A portrait minification uses
built-in mipmap import and UI-only Linear with Mipmaps filtering, accepted by the
owner. The source PNG and stationary machine's Linear sampler are unchanged.
The compact header removes forced height/row expansion and uses 12-unit top
clearance with a 10-unit gap before the divider; sides/bottom remain 24 units.
The 26-unit uppercase SemiBold title, Close node/styles and bottom-aligned
statistics remain unchanged. Only Collect All's opt-in primary style gains richer
teal states, a defined edge and subtle depth, pending owner screenshot review.
The outer panel size and B2 nine-patch margins remain unchanged.
It uses existing artwork, B1/B2 styling, two columns, actual cycle progress and
definition-derived nominal production details. Smelter/Fabricator layouts and
production semantics remain unchanged. Machine inspection temporarily suppresses
the objective tracker without changing the player's presentation preference.
The 85% default and hybrid scaling remain intact. See the
[pilot implementation and acceptance steps](../README.md#extractor-inspection-visual-pilot-feature-branch-pending-merge).

The approved B1 inventory follow-up keeps this shared aggregate storage and
uses 24 material positions (three rows of eight) plus eight machine/equipment
positions, with all empty positions visible. This compact follow-up is implemented
on `codex/compact-20-slot-inventory`, pending merge. The owner approved the layout
and validation results on 2026-10-29. These are presentation positions, not capacity limits; extra types retain access in a small overflow list. Tab
replaces I; machine slots continue to request deployment on a single click.
Inventory implementation merged in PR #78; owner graphical acceptance remains
separate. The approved hybrid hotbar follow-up adds ten bottom-centered type
assignments for physical 1-9/0, with Extractor/Smelter/Fabricator defaults on first
packaged availability. Session-owned assignments survive depletion and travel;
custom/cleared slots are never automatically overwritten or restored. Inventory
right-click chooses a destination; hotbar right-click clears. Number keys toggle
the same placement or switch through existing construction guards, with no item
consumption until successful placement. Modal interactions and recovery retain
input ownership. Prompts/hints sit above the bar; responses and transitions
can hide it while ambient musings retain it. The owner-approved PR #89 revision
keeps the bar visible without new dimming during ordinary conversations;
activation, context menus and assignment edits remain blocked until closure. The implementation on
`codex/b1-hybrid-hotbar` now includes the owner-approved visual refinement:
52-unit slots (18.75% smaller), one subtly translucent B1 backing panel with thin
border/four-unit padding, and the same copper-amber placement highlight.
The original implementation and the owner-approved refinement both passed
the restricted Native runner (static suite, cold import and existing recipe
regression). Hotbar graphical/interaction acceptance remains separate; the
feature is pending merge. The hotbar refinement required no preservation-assertion changes. The separate
owner-approved compact inventory eight-column layout sets the panel width to 380 units
(from 242 in the five-column candidate), with unchanged 42-unit slots,
four-unit gaps and reduced local padding. It preserves overflow access and B1
styling; the hint is `Tab / Esc to close`, with deployment/assignment guidance
in tooltips. The owner approved its two exact-file preservation hashes before
one restricted Native run at `f4bc6e8`: all 46 static tests, cold import and the
existing recipe regression passed, with zero recipe failures and all identity
and infrastructure checks passing. The owner inspected the layout in Godot and
approved layout and validation results; no agent graphical execution occurred.
Specific resolution/readability and broader interaction coverage remain separate
from those headless checks.
See the [implementation and acceptance checklist](../README.md#b1-hybrid-hotbar-feature-branch-pending-merge).
No movable stacks, new tools or disk persistence are added. The separate
Ferrite implementation (merged PR #91) integrates the
owner-approved Ore, Ingot, Plate and Rod PNGs into inventory and existing recipe
icons. Its owner-review refinement uses 50-unit inventory slots/34-unit icons,
linear mipmap filtering and unframed 24-unit material storage icons. The owner
approved those sizes, artwork, filtering and populated storage. The final
correction parents inventory icons before centered anchoring and applies one
shared three-unit downward inset. Empty buffers use generic text without icons,
and Fabricator output follows the actual stored item, including
previous-recipe output. Names, quantities, capacity bars, portraits, production
controls and global scale remain intact. Graphical
acceptance and Native authorization remain separate from static checks. See the
[inventory artwork and owner acceptance notes](../README.md#b1-inventory-modernization-pr-78-merged).

The focused `codex/machine-icons-equipment-sizing` feature (pending merge) adds
owner-supplied Extractor, Smelter and Fabricator icons to the canonical mapping,
replacing EX/SM/FB. Equipment retains eight positions and ID ordering in six
columns, with 70-unit slots/56-unit icons; materials stay at eight columns and
50/34 units. The panel widens from 460 to 472 units. Owner Decision 19 makes
its height follow the current content minimum explicitly, with deferred refits
when that minimum changes; it moves upward only as needed to leave 16 units above
the hotbar. Hidden overflow reserves no space, while visible overflow retains its
bounded list. Decision 20 implements Option C: ten 60-unit slots/46-unit icons,
centered subtle key hints immediately below each button, outside the backing,
and unchanged lower-right quantities. There is no header, footer, toggle or
Option B implementation. The centered 662 x 68 backing and external hints reserve
101 units above the bottom; conversation/musing clearances remain 104/112.
The owner approved the machine icons/rendering and visually approved the refined
layout on 2026-10-30. Artwork bytes,
Ferrite icons, capacity, ownership, deployment/recovery, assignment mechanics,
active/hover/unavailable states and the 85% default remain intact. The owner then
authorized restricted testing: at `967b27c`, 90 static tests, cold headless import
and the allowlisted recipe-switching regression passed, with zero failures and
all infrastructure/authorization checks passing. Final documentation changes do
not alter tested runtime inputs or controls. No agent graphical, interactive UI
or performance test, merge or cleanup was performed. Exhaustive functional and
overflow/window coverage remains distinct from visual approval and that narrow
headless test. The branch is ready for owner merge review. See the
[focused acceptance checklist](../README.md#machine-icons-and-equipment-sizing-feature-branch-pending-merge).

Recover the Extractor implementation is merged in PR #30; agent validation was
static only. It adds the bay, inventory and first recovery step. Deployment and
deployed-machine recovery are merged in PR #32; production is added by the
feature below. Power remains unimplemented; Fabricator rack recovery is merged
in PR #42 and deployment/configuration is merged in PR #43. Recipe switching
is pending on the feature branch described below.
Inventory and recovery are session-only and reset with a fresh Main instance. See the
[implementation notes](../README.md#recover-the-extractor-pr-30-merged)
for approved dialogue, ownership and validation limits.

## Approved Extractor deployment direction

- Clicking a deployable packaged machine in Equipment immediately enters
  construction and closes inventory; no separate Deploy button or selection
  state is required.
  Construction uses a neutral translucent machine ghost, green/red footprint
  validity, mouse grid positioning, clockwise quarter turns with R, left-click
  confirmation and
  right-click/Esc cancellation. Successful placement exits the mode.
- Extraction compatibility belongs to machine definitions; resource deposits
  define their mineral geometry and highlight treatment. Compatible visible,
  loaded ground is highlighted without introducing surveying. Environmental
  objects explicitly opt into construction blocking; future trees may block.
- Construction and recovery have independently configurable limited ranges,
  measured to the nearest point on the footprint. Recovery uses the dedicated B
  mode and left-click targeting, exits after one success, and cancels with
  right-click/Esc. Hovering an eligible machine shows Press B to recover.
- Placement transfers one packaged item into one deployed machine, and recovery
  reverses it. Persistent planet state owns identity, position and orientation
  independently of disposable terrain presentation. Persistence remains in memory.
- Dave inspects the introductory Ferrite deposit through a small invisible,
  nonblocking region over recognizable mineral-bearing ground. Contextual E
  triggers the approved discovery musing and disables that interaction for the
  playthrough. Mineral ground and veins look the same before and after discovery;
  resource data, future formations and genuine blocking obstacles remain separate.
- The first successful deployment changes Restore Computer guidance to
  **Produce Ferrite Ore with the Extractor.** Recovery never resets progression.
  PR #32 left the Extractor unpowered and nonproducing; the milestone below
  introduces temporary power-independent production. No new dialogue is added.

Implementation is merged in PR #32. Controls, ranges, state ownership, exclusions
and static-validation limits are recorded in the
[implementation notes](../README.md#deploy-the-extractor-pr-32-merged).

## Extractor 128x128 footprint alignment (feature branch, pending merge)

PR #153 subsequently merged at `0a00034`; owner F5 acceptance remains pending.
The historical heading is retained for existing links.

The owner approved Approach B2: `codex/extractor-footprint-128` changes only
`inventory/extractor.tres` gameplay data from 2x2 cells / extraction point (32,32)
to 4x4 cells / (64,64). The global construction grid remains 32 world units;
At that milestone Smelter and Fabricator remained 2x2 (64x64); the subsequent
[Smelter footprint milestone](#smelter-4x4-footprint-feature-branch-pending-merge)
extends Smelter only. Earlier 2x2 Extractor records describe
their historical milestones and are not revised acceptance evidence.

Existing generic placement, overlap, blocking-solid and Dave collision queries
consume the larger 128x128 rectangle. Its top-left snaps to any 32-unit cell;
all four rotations retain the same square occupancy and centered mineral sample.
Only that point must qualify; full deposit containment is not required. The
bottom-center anchor is footprint origin + (64,128). No shared placement,
collision, production or recovery script changes are included. Production stays
one ore/second into capacity 20; the packaged item identity remains unchanged.
All four accepted directional artwork packages remained frozen and unintegrated
at that footprint-only milestone. The subsequent [static artwork PR A](EXTRACTOR_STATIC_ARTWORK.md)
shared their original body, raised barrel and foreground layers between deployed
and ghost Extractors; PR #154 merged without gameplay changes. Owner Decision 2A
now authorizes the [port-free runtime body integration](EXTRACTOR_STATIC_ARTWORK.md#port-free-runtime-bodies-v1--feature-branch-pending-merge),
prepared on `codex/extractor-port-free-runtime-v1`, pending merge and owner F5.
Only four fixed-crop body derivatives change; the original barrel/foreground
layers, imports, registration and gameplay remain unchanged. Before this integration,
[PR B barrel animation](EXTRACTOR_STATIC_ARTWORK.md#barrel-animation-pr-b)
merged in PR #155 with final owner F5 acceptance (16/16 PASS, zero blocking defects)
for that earlier artwork. Barely perceptible motion at maximum zoom-out is an accepted
nonblocking limitation. Only producing deployed
Extractors reciprocate; ghosts and nonproducing machines stay raised. Animation
does not drive production or inventory. Its 8/8/6/6-source-pixel amplitudes and
1.6-second sine-eased cycle remain provisional. Owner-observed F5 acceptance is
separate from agent static checks; no agent engine execution is claimed.

Inspection and collection retain their 96-unit center-based range. Construction
and B recovery retain their existing 160-unit nearest-footprint ranges. Larger
occupancy intentionally affects adjacency, walking and near-edge mineral
eligibility; corner inspection/collection reach is deferred to gameplay review.
Use a fresh playthrough: current state is session-only, with no disk save/load
workflow, and this change does not migrate or hot-resize existing live machines.

Focused static checks use
`python -B -m unittest discover -s tests -p static_ferrite_integration_test.py`.
They inspect resource values, independent grid/occupancy examples, centered
rotation cases, deposit membership and generic query wiring; baseline comparisons
protect other machine definitions, production, recovery and interaction code.
Static checks do not execute GDScript or certify physics, input or graphical
behavior. The existing Extractor production/recovery fixture retains its test
logic; only its now-outdated extraction-coordinate comment changes.
Implementation static validation: Ferrite integration **9/9 PASS**, Ferrite region
**9/9 PASS**, production terrain **8/8 PASS**. Changed documentation links,
historical README content preservation, all four accepted artwork ZIP hashes and
`git diff --check` also passed. The full static suite was not run for this focused
change. Godot import, GDScript runtime tests and graphical checks remain NOT TESTED.
No Godot import, headless test or graphical run is authorized by this change.

Owner F5 acceptance remains pending; all checks below are NOT TESTED:

- [ ] 4x4 placement preview, 32-unit snapping and all four R rotations.
- [ ] Deposit-center eligibility, including inside/edge/outside positions.
- [ ] Collision and placement rejection for Dave and blocking objects.
- [ ] Adjacent Extractors and mixed Smelter/Fabricator placement; no overlap.
- [ ] Inspection and collection from all sides and corners, including neighbors.
- [ ] B-key recovery and redeployment, preserving equipment and stored output.
- [ ] Existing Extractor production and Smelter/Fabricator regressions.

## Approved Ferrite Ore production direction

- Discrete repeating Extractor cycles provisionally produce 1 Ferrite Ore each
  second (60/minute maximum) into one 20-ore internal buffer. Machine definitions
  configure output, quantity, cycle duration and capacity. Infinite compatible
  ground is required; electrical requirements are temporarily bypassed.
- Persistent planet state owns production, independent of terrain presentation,
  Dave's location and machine UI. Full output pauses work without losing existing
  fractional progress; collection resumes it. There is no offline production or
  disk save/load.
- E opens a compact nonpausing machine panel within its own interaction range.
  Live progress, status, stored quantity/capacity and Collect All are shown.
  Producing is green, Output Full amber and Inactive gray on a subtle steady light.
  Movement remains available; range exit, inventory, tools and transitions close
  the panel, as do Esc and its close button.
  While the panel is open, B cannot activate recovery; close it first. R does not
  rotate a preview and E does not trigger another world interaction.
- Collect All transfers available ore into Materials. B recovery automatically
  returns stored solid ore and packaged machinery together, discarding incomplete
  work. Failed transfers leave both inventories and the machine unchanged.
- First successful acquisition through collection or recovery advances Restore
  Computer guidance to **Locate the Smelter in the maintenance bay.** Production
  alone does not advance it. Progression is permanent for this playthrough.
- Smelter recovery is the next approved milestone below. Smelting, electrical
  networks and logistics remain deferred.
  Future material conduits and two Extractor outputs sharing one buffer are
  documented in [issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35).
  No ports or transport are implemented in this milestone.

Implementation is merged in PR #36. Agent validation was static only; controls,
ownership and limits are in the
[implementation notes](../README.md#produce-ferrite-ore-pr-36-merged).

## Approved Smelter recovery direction

- First Ferrite Ore acquisition into Materials, through collection or recovery of
  an ore-containing Extractor, triggers Dave's approved one-time internal musing:
  “Ore's no good to me like this. Need to refine it first.” followed by
  “That smelter should do the job.” Production into the buffer alone does not.
  Reuse the existing acquisition milestone and nonpausing, automatic musing UI.
- The existing bay Smelter is visible but noninteractive until that acquisition.
  Then **E — Recover Smelter** transfers exactly one packaged Smelter to Equipment,
  without inspection, Computer interaction or another musing. Failed insertion
  cannot complete recovery. One-time recovery persists through scene revisits,
  leaving the rack empty; a fresh playthrough restores it.
- Successful recovery advances Restore Computer guidance to **Deploy the Smelter
  near the Extractor.** Inventory possession alone does not advance it and item
  removal cannot revert it. “Near” is guidance only. PR #38 kept the packaged
  Smelter inert; the approved deployment milestone below makes it deployable.
  Smelting and recipes remained subsequent work in PR #38. Fabricator recovery
  is added on the feature branch described below.
- The maintenance bay arrangement is temporary. Future HD environments should
  include varied mounting, damaged infrastructure, maintenance access and
  environmental storytelling rather than three evenly spaced machines. This
  milestone preserves the current layout and collision.

Implementation is merged in PR #38. Agent validation was static only; state
ownership, the original inert item representation and exact musing presentation
are recorded in the
[implementation notes](../README.md#smelter-recovery-pr-38-merged).

## Approved Smelter deployment direction

This section preserves PR #39's original deployment milestone. The subsequent
[4x4 footprint milestone](#smelter-4x4-footprint-feature-branch-pending-merge)
updates deployed geometry; production is described separately below.

- Reuse the packaged Smelter identity and existing construction system: click
  Equipment to deploy, 2×2 construction cells (64×64 units), R quarter turns,
  neutral ghost, validity footprint and ordinary range/obstacle/occupancy rules.
  Empty resource compatibility permits general ground without deposit
  highlighting. “Near the Extractor” imposes no proximity constraint.
- Use a distinctive provisional cold furnace silhouette and neutral gray status
  indicator, without active furnace effects. The shared E panel shows Inactive
  and “No production configured.” and hides production-only controls.
- Existing planet ownership retains identity, position and rotation through
  interior visits and terrain unloading. B recovery returns one packaged
  Smelter. First successful deployment permanently advances Restore Computer
  guidance to **Produce Ferrite Ingots with the Smelter.** Recovery cannot reverse
  it; redeployment cannot repeat it. A fresh playthrough resets both states.
- PR #39 deferred actual smelting, inputs/outputs, recipes and material transfer;
  the approved smelting milestone below extends those capabilities. Ports and power
  remain deferred. Future ports should rotate with the machine, with default
  lower-left input and lower-right output as tracked in
  [issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35).
  No new dialogue or Fabricator functionality is added.

Implementation is merged in PR #39. Agent validation was static only; evidence
and limitations are recorded in the
[implementation notes](../README.md#deploy-the-smelter-pr-39-merged).

## Smelter thermal illumination (feature branch, pending merge)

Owner Thermal Decisions 1A–10A, approved November 9, 2026, are implemented on
`codex/smelter-thermal-illumination`; owner F5 accepted, pending review and merge.
The presenter consumes existing operating-status updates and owns one local tween:
cold production warms to 0.82 in 0.5 seconds, then pulses between 0.82 and 1.00
over 3.6 seconds. Input-empty/output-full cool over 1.0 second without a hold;
inactive resets immediately. Rapid transitions retarget from displayed opacity.
Direction changes preserve animation phase. Ghosts/deactivated subtrees reset
cold. Retained-world re-entry initializes producing at 0.82 and all other states
cold, including unchanged status. No thermal state enters simulation. Frozen
assets, registration, dot, gameplay, other presenters and stationary machinery
are unchanged. On November 9, 2026, the owner reported **19/19 F5 PASS** against
`8d6e2db79c204ed334372447ca801771351e378b`, with no observations, defects or
blocking concerns and no new Godot import, parser or runtime errors. The
[behavior, static results and completed owner acceptance](SMELTER_THERMAL_ILLUMINATION.md)
record preserves the original 68/68 static results separately from owner
gameplay/graphical observations. No agent Godot execution or merge is authorized.

## Static directional Smelter artwork (feature branch, pending merge)

Historical milestone: PR #157 merged at
`ca18cfa4c9f16ab934968aed4fa764f9c1e2b58d`. The idle-only behavior below describes
its accepted baseline; the thermal feature above extends that presentation.

Owner-authorized on November 5, 2026, with decisions 1A/2A/3A: retain the status
dot, use local mipmapped linear filtering, and keep accepted idle illumination in
every operating state. Implemented on `codex/smelter-static-artwork`, owner F5
accepted and merged in PR #157, from PR #156's merged 4x4 footprint baseline
`65564d5d95502fcc0368a2b5396d1855311c5806`.

The dedicated Smelter presenter replaces only deployed procedural artwork and its
placement ghost. Ten frozen PNGs retain four independent illustrations, directional
ground anchors, exact crop offsets, source-over layer order and uniform 4/29 scale
at footprint-local (64,128). The 0-degree view keeps its cold interior and fixed
foreground; illumination is hidden for all views regardless of production state.
Warm metal reflections and permanent painted/amber accents remain authored pixels.

The existing status dot retains its colors, radius and direction-dependent logical
position in a foreground sibling outside the artwork scale; ghosts omit it. Ghost
layers composite before a single 0.5 fade. Deployed machines retain their existing
bottom-center Y-sort ownership, collision and 128x128 footprint. Visual overhang
adds no occupancy or interaction geometry. Production, buffers, 96-unit
center-based inspection/transfers, accepted diagonal-corner reach limitation,
160-unit nearest-footprint B recovery and retained travel state remain unchanged.
Extractor animation, Fabricator, Dave and stationary Smelter remain unchanged.

Owner F5 acceptance was reported November 9, 2026 against implementation commit
`36a5214761ea66398dd78b5077f6062ed84e96d3`: **15/15 PASS**, no observations,
defects or blocking concerns. Coverage includes all directional/ghost views,
zoom/filtering, overhang/collision, sorting, multiple-machine responsiveness,
status/idle state, inspection/transfers/production/collection, recovery and
redeployment, travel retention, other-machine/Dave regressions and no new Godot
import, parser or runtime errors. The
[implementation and acceptance record](SMELTER_STATIC_ARTWORK.md) preserves the
original 55/55 static results separately from owner observations. The agent did
not execute Godot for either implementation or this documentation update.
Thermal animation, production-driven illumination, physical ports and conduits
remain outside this milestone. The footprint-only record below retains its
historical scope and acceptance results.

## Smelter 4x4 footprint (feature branch, pending merge)

Prepared on `codex/smelter-footprint-128`; PR #156 has owner F5 acceptance
**10/10 PASS**, with no observations or blocking defects, pending review and merge.
Only `inventory/smelter.tres` production data changes: its explicit footprint
becomes 4x4 construction cells, or 128x128 world units on the unchanged 32-unit
grid. All four orientations retain 16 occupied cells. Shared snapping, ghosts,
overlap/obstacle/Dave checks, collision and lifecycle derive from that definition.
The interaction center is origin + (64,64); the bottom-center presentation anchor
is origin + (64,128). MachineVisual's existing procedural drawing remains in use.
At the Smelter milestone, Extractor remained 4x4 and Fabricator remained 2x2;
the shared definition default remains 2x2. The inherited extraction point (32,32) stays unchanged and is neither
a Smelter interaction anchor nor a physical port.

Owner-selected Option A preserves **96-unit center-based inspection and material
transfer reach**. Cardinal side access remains possible. Dave may be slightly
outside reach at diagonal corner contact; this is an accepted limitation, with
no compensating range or policy change. B recovery retains **160-unit distance
from the nearest footprint point**. Production remains 1 Ferrite Ore -> 1 Ferrite
Ingot per 2 seconds, with independent 20-item input and output buffers. UI,
transfers, production simulation and world-state ownership are unchanged.

The separate stationary maintenance-bay Smelter retains its presentation and
E-key recovery route. Static directional artwork integration and production-driven
thermal illumination are separate, unauthorized milestones. Physical material
ports and conduits remain unimplemented; no frozen artwork is integrated here.

Validation uses Python static resource/source contracts, independent geometry
examples and exact baseline comparisons. Historical Stage 3C input-plan hashes
and provenance remain sealed to their original source; only its Smelter input
lookup gains a narrow historical exception, with current state checked separately.
Extractor artwork and Ferrite guards admit only the Smelter footprint line change.
The Extractor animation shared-adapter protections remain unchanged.

Focused commands (run from the repository root):

```powershell
python -B -m unittest discover -s tests -p static_smelter_footprint_test.py
python -B -m unittest discover -s tests -p static_ferrite_integration_test.py
python -B -m unittest discover -s tests -p static_extractor_artwork_test.py
python -B -m unittest discover -s tests -p static_extractor_animation_test.py
python -B -m unittest discover -s tests -p static_terrain_stage3c_test.py
python -B -m unittest discover -s tests -p static_v2_stationary_machines_test.py
python -B -m unittest discover -s tests -p static_current_preservation_test.py
```

Implementation results: Smelter **5/5**, Ferrite integration **9/9**, Extractor
artwork **5/5**, Extractor animation **6/6**, Stage 3C **9/9**, stationary machines
**8/8** and current preservation **4/4 PASS** (46 total). Changed Markdown links
and anchors, original README byte preservation, exact production-change scope,
unchanged historical plans/evidence and `git diff --check` also passed. The full
static suite was not run for this focused milestone.

Static checks do not execute GDScript, verify engine physics or establish gameplay
or graphical PASS. The agent did not execute Godot for implementation or this
acceptance update. The owner separately completed normal-F5 gameplay acceptance
on **November 5, 2026**, against implementation commit
`ddf2dcd2a34853bdcc6b8d8283ddfdadfcea3550`: **10/10 PASS**, no observations and
no blocking defects. This owner-observed result is separate from the original
46/46 static results above; those results and implementation history are preserved.
Machine state remains session-only; live machines are not migrated or hot-resized.

### PR #156 owner F5 acceptance — November 5, 2026

All ten checks below passed at the accepted implementation commit above.

| # | Owner-observed check | Result |
| --- | --- | --- |
| 1 | Fresh playthrough, Extractor progression and stationary Smelter E recovery | PASS |
| 2 | Four orientations, 4x4 footprint and grid snapping | PASS |
| 3 | Valid/invalid placement, Dave/obstacle rejection, adjacency and overlap | PASS |
| 4 | Collision around all sides and corners | PASS |
| 5 | Cardinal inspection and accepted diagonal-corner reach limitation | PASS |
| 6 | Ore transfers, production, capacities and ingot collection | PASS |
| 7 | B recovery with both buffers populated and exact inventory returns | PASS |
| 8 | Redeployment and resumed production | PASS |
| 9 | Exterior/interior travel and retained machine state | PASS |
| 10 | Extractor and Fabricator gameplay regression | PASS |

The original detailed checklist is retained below as implementation history.
The accepted diagonal-corner reach limitation remains unchanged. Directional
artwork and thermal illumination remain outside PR #156. Review and explicit
owner merge authorization remain required; this acceptance does not merge the PR.

Documentation-update validation: changed Markdown links/anchors, preservation of
the original static results and historical checklist, unchanged gameplay/resources,
tests/artwork and historical plans/evidence, and `git diff --check` passed. The
five owner-authorized Extractor import sidecars were inspected and found already
byte-identical to the accepted commit; their contents were preserved.
Focused static rechecks also passed: Smelter footprint **5/5**, Extractor animation
**6/6** and current preservation **4/4** (15 total). No tests were modified and
the full static suite was not rerun for this acceptance update.

Original owner F5 checklist (now accepted above):

1. Start a fresh F5 playthrough; complete the normal opening, recover/deploy the
   Extractor, acquire ore, then use E to recover the stationary Smelter. Check its
   unchanged presentation, unlock and one-time recovery behavior.
2. Deploy the Smelter in each of four R orientations, recovering/redeploying as
   needed. Confirm a 4x4 preview, 128x128 occupied area and 32-unit top-left
   snapping at positive and negative coordinates.
3. Place on clear ground; reject Dave, ship/solid obstacles and occupied cells.
   Check exact edge adjacency with Smelter/Extractor/Fabricator and rejection of
   one-cell incursions. Invalid placement must preserve packaged equipment.
4. Walk Dave around every side and corner; verify collision blocks the whole
   footprint without trapping him or leaving unexpected gaps.
5. Inspect from north, east, south and west. Confirm the unchanged 96-unit center
   reach and accepted diagonal-corner limitation; approach a side to interact.
   Check transfer/collection availability when entering/leaving reach.
6. Transfer ore, observe unchanged 1:1 / 2-second production and 20/20 capacities,
   then collect ingots. Check Input Empty/Producing/Output Full and partial work.
7. Close the panel, populate both input and output buffers, then use B recovery.
   Confirm packaged Smelter plus all stored ore/ingots return exactly once, no
   inventory loss/duplication, and the unchanged 160-unit nearest-footprint reach.
8. Redeploy, load ore and resume production; verify geometry, rotation and guidance.
9. Leave a deployed Smelter with materials, travel exterior -> interior -> exterior,
   and verify position, orientation, collision, buffers, production and inspection.
10. Check Extractor deployment, animation, ore collection and recovery; check
    Fabricator 2x2 placement, recipes, transfer, production, collection and recovery.

## Approved Ferrite Ingot production direction

- Smelter processes one Ferrite Ore into one Ferrite Ingot every two seconds
  (provisional 30/minute), with independent 20-item input and output storage.
  Extractor remains output-only at 60 ore/minute: one can theoretically supply two
  Smelters. No power, conduits, ports, recipe selection or queues are added.
- Reuse the nonpausing machine panel with separate vertical input/output sections,
  Transfer All and Collect All. Transfer inserts as much ore as fits; collection
  withdraws only finished ingots. Both preserve partial progress and keep the panel
  open. Existing interaction guards and Extractor controls remain.
- Persistent planet simulation consumes input only on successful cycle completion,
  together with output creation. Pause when input is insufficient or output cannot
  accept another cycle, retain fractional progress and discard blocked elapsed
  time. Status priority is Inactive, Output Full, Input Empty, Producing, with
  gray/amber/blue/green lights. Simulation continues independently of presentation.
- Recovery returns all input, output and one packaged machine atomically, discards
  fractional progress, and commits inventory and world changes before notifying
  observers. Failed recovery changes nothing; incomplete cycles retain their ore.
- First ingot acquisition into Materials through collection or recovery permanently
  advances Restore Computer guidance to **Locate the Fabricator in the maintenance
  bay.** Buffer production alone does not qualify. Present Dave's exact musing once:
  “One step closer. Assuming that fabricator survived the crash.” followed by
  “Guess there's only one way to find out.” Use the existing nonpausing automatic
  musing presentation. Spending, travel, recovery and redeployment cannot reset it.
- PR #40 left Fabricator visible, noninteractive, unrecoverable and unavailable in
  Equipment; the recovery milestone below extends this. Recipe switching remains future work in
  [issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37).
  Future rotating lower-left input/lower-right output ports remain tracked in
  [issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35).

Implementation is merged in PR #40. Agent validation was static only. State
ownership and validation limits are in the
[implementation notes](../README.md#produce-ferrite-ingots-pr-40-merged).

## Approved Fabricator recovery direction

- First Ferrite Ingot acquisition into Materials permanently unlocks the existing
  maintenance-bay Fabricator. Collection and Smelter recovery qualify; ingots
  solely inside output storage do not. No further inspection, repair or cost.
- Reuse **E - Recover Fabricator** and the established rack behavior to insert
  exactly one packaged Fabricator into Equipment, then leave the rack empty.
  Failed insertion cannot complete recovery or advance guidance; repeated input
  cannot duplicate equipment. Recovery survives scene visits and item removal;
  a fresh playthrough restores the rack and resets progression and inventory.
- Successful recovery advances Restore Computer directly to **Craft a Ferrite
  Plate.**, without an intermediate deployment objective. No additional dialogue
  or musing is added; the approved ingot-acquisition wording remains unchanged.
- PR #42 introduced inert packaged Equipment; the approved deployment milestone
  below extends it. Production, Ferrite Plate crafting, recipe switching, power
  and logistics remain later work. The crafting objective stays incomplete.

Implementation is merged in PR #42. Agent validation was static only and the
standalone regression checks remain unexecuted under the Godot restriction. See
the [implementation notes](../README.md#recover-the-fabricator-pr-42-merged).

## Fabricator static directional artwork (feature branch, pending acceptance)

Decision 36, Option A integrates the four accepted frozen Fabricator views on
`codex/fabricator-four-orientation-static-artwork`, pending owner normal-F5
acceptance and merge. Existing authoritative quarter turns select front/right/rear/
left through a minimal `MachineVisual` presenter. Independent accepted scales and
anchors are preserved, including the full-canvas front resting composite; there
is no mechanical texture rotation, mirroring or apparent-height normalization.
The 4x4 footprint, ghost conventions, unscaled status dot, sorting, gameplay and
stationary-bay artwork remain unchanged. Extractor barrel animation and Smelter
thermal behavior remain unchanged. Validation is offline/static only; no Godot
execution or runtime acceptance is claimed. Fabricator animation/timing is deferred.
See [source identities, implementation and owner F5 checks](FABRICATOR_STATIC_ARTWORK.md).

## Deployed Fabricator 4x4 footprint (feature branch, pending merge)

`codex/fabricator-4x4-footprint` implements the approved 4x4 construction-cell
footprint (128x128 world units on the 32-unit grid). The top-left placement origin
stays grid-aligned; center is origin + (64,64), bottom-center anchor is origin +
(64,128), and all four clockwise quarter turns retain square bounds. Shared
placement, occupancy, collision and construction ghosts derive from the resource.
The inherited extraction point is unchanged; this machine does not sample mineral
ground and that value is neither a material port nor an interaction anchor.

Inspection and transfer use 96-unit center distance. The accepted Smelter diagonal
corner limitation applies without increasing reach. Construction and deployed
recovery use 160 units from the nearest footprint point. The initial configuration
exception remains available after successful deployment, without authorizing
out-of-range transfer or ordinary recipe switching. Recipes, capacities, pause
leases, transactions and exterior state ownership remain unchanged. The standalone
maintenance-bay Fabricator keeps its own assets, collider and 45-unit recovery cap;
Extractor and Smelter are unchanged. On November 9, 2026, the owner reported
**acceptance PASS** for PR #160 at implementation commit
`1ac525ed70ebc8eb45e95fb6e8e5b74ebc3a26f7`. This is the owner's overall result;
no itemized checklist results were supplied. Agent validation remains static
(440 tests passed); the agent did not run Godot or execute the Godot regression
scripts. The implementation is owner accepted and pending review and merge in
[PR #160](https://github.com/interneth3ro/the-long-way-home/pull/160).

The earlier milestone records below describe the original 2x2 implementation.

## Approved Fabricator deployment and initial configuration

- Deploy recovered Equipment using existing construction controls and placement
  checks, with a 2x2-cell (64x64-unit) footprint and provisional artwork.
- Finish placement and exit construction before opening the shared panel for the
  new instance. Initial selection opens regardless of inspection distance; later
  inspection and all transfers enforce normal range. The placement click cannot
  select a recipe or trigger recovery.
- Offer selectable icon cards for Ferrite Plate (1 Ferrite Ingot -> 1 Plate) and
  Ferrite Rod (1 Ferrite Ingot -> 2 Rods). Selection stays in the panel, showing
  requirements, expected product, stored quantities and Transfer All. Dismissed
  unconfigured machines reopen the chooser directly on in-range E interaction.
- Keep recipe identity separate from material-keyed inputs in authoritative
  world-machine state. Each accepted ingredient independently holds 20 units,
  configurable on the machine definition. Transfer All atomically loads all
  accepted materials, preserving unrelated materials and Smelter storage.
- Recovery atomically returns packaged Equipment and every stored ingredient.
  Redeployment starts unconfigured. Presenter and panel lifetime do not own state.
- Loaded machines stay gray **Inactive** with **Production not yet available**.
  No consumption, progress, output collection, manufacturing or objective advance.
  **Craft a Ferrite Plate.** stays current, without new dialogue or objectives.
  Recipe switching extends this in the approved direction below (issue #37).

Implementation is merged in PR #43. Agent validation was static only; regression
scripts remain unexecuted. Owner-reported playtest results and the remaining
output-label retest are recorded in the
[implementation notes](../README.md#configure-and-load-the-fabricator-pr-43-merged).

## Approved deployed Fabricator recipe switching

- Configured inspection offers Change Recipe using the existing Plate/Rod cards,
  with Current marked. Current and Back return unchanged; Esc closes the entire
  panel. Different recipes apply immediately in the same panel. Cause-aware inline
  errors retain the chooser. No confirmation or automatic ingredient loading.
- Retain compatible inputs by item ID; atomically return incompatible inputs using
  the old recipe definitions. Failure preserves all state. Opening or cancelling
  preserves incomplete progress; only a successful different recipe resets it.
- Pause only the targeted instance while changing, with a subtle Production Paused
  indicator. Release on all exits, range loss, transitions, other UI interruptions,
  removal and stale target invalidation. Initial configuration has no pause or Back
  and keeps its placement range exception; switching uses ordinary inspection range.
- Preserve future completed output independently of selected recipe. Future
  manufacturing must wait while incompatible old output remains uncollected.
  Production, live progress and output collection are not implemented here.
- Plate <-> Rod retains stored Ferrite Ingots with unchanged quantities and
  20-unit per-ingredient capacity. Do not add recipes, manufacturing, logistics,
  power or narrative advancement. Craft a Ferrite Plate stays current.

Implementation is merged in PR #44. Owner acceptance remains separate from agent
static validation, which does not establish runtime behavior. Synthetic tests for
multi-material returns, progress and output preservation remain unexecuted and
are separate from current player-facing acceptance. See the
[implementation and ordered manual checklist](../README.md#switch-deployed-fabricator-recipes-pr-44-merged).

## Approved Fabricator production and first Plate acquisition

- Automatic manufacture when configured, supplied and unblocked. Both starter
  recipes take 3 seconds per cycle, defined in recipe data: 1 Ingot -> 1 Plate or
  1 Ingot -> 2 Rods. No manual Start/Stop/Craft or additional recipes.
- Keep 20 units per accepted input and one shared output buffer holding 20
  individual products. Complete whole batches only. Consume all ingredients at
  completion, atomically with product creation; no reservation at cycle start.
- Preserve partial progress on shortages, insufficient batch space, incompatible
  completed products and the existing per-instance recipe chooser pause. Blocked
  time never becomes a backlog. Only a successful different recipe resets work.
- Completed output carries its own product identity, preserved across switching,
  snapshots and presenter recreation. Collect All returns that stored product
  atomically; recovery returns equipment, all inputs and completed output together.
  Invalid storage or rejected insertion must preserve items and machine state.
- Reuse Producing / Input Empty / Output Full / Inactive, progress and existing
  panel controls. Incompatible output counts as Output Full. Empty output uses
  the generic heading; nonempty output names the stored product. Preserve stable
  interactive visibility and all recipe chooser lease/release behavior.
- First successful Plate acquisition into Dave's Materials completes an idempotent
  session milestone. Manufacture alone does not qualify. Collection and recovery
  follow the existing inventory-acquisition convention. Spending never resets it.
  Clear Craft a Ferrite Plate guidance while `restore_computer` remains active and
  incomplete. No next objective, dialogue, musing, cinematic or repair transition.

Implementation merged in PR #45; owner runtime acceptance remains separate.
Agent checks were static only; added/updated regression scripts were unexecuted.
No Godot type checking, runtime or graphical verification is claimed.
See [implementation and ordered owner checklist](../README.md#fabricator-production-pr-45-merged).
Earlier Fabricator sections retain their milestone-specific historical scope;
this approved production direction extends their formerly deferred behavior.

## Computer restoration (feature branch, pending owner acceptance)

After first Ferrite Plate acquisition, retain the opening conversation and unlock
the approved one-time three-line inspection followed by a compact repair panel.
Require current Materials inventory of **4 Ferrite Plates and 4 Ferrite Rods**;
this newer owner decision supersedes the canonical story's historical **6+8**.
Live guidance asks Dave to gather 4+4, then return to the ship, reverting readiness
if he spends materials. Confirmed repair atomically consumes 4+4 once and completes
`restore_computer`. Fade to black, switch to existing repaired Computer artwork,
fade in, and automatically present the four locked narrative scenes verbatim.
Full text appears immediately at provisional 15 characters/second, 2.5–8 seconds
per line and 1.5 seconds between scenes, with no skip. Restore controls afterward
and activate **Restore the Ship**: `Investigate how to improve manufacturing
capabilities for ship repairs.` Contextual linear Computer dialogue follows.
No saving, dialogue-choice framework, research or upgrade mechanics are added.

This extends the earlier first-Plate milestone's formerly deferred repair scope.
See [implementation, canonical provenance and verification limits](COMPUTER_RESTORATION.md).

## Unresolved design details

- The precise conspiracy behind Dave's arrival remains under development.
- Footprints beyond the approved Extractor, Smelter and Fabricator, port rules, rail behavior, research
  content, chapter structure, dialogue formats, and ending conditions still
  require design work. The approved intentions above do not settle these details.

Bootstrap establishes project files and documentation only. Gameplay systems,
content pipelines, assets, and speculative frameworks are outside its scope.
