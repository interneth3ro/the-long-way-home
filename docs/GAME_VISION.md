# The Long Way Home — Game Vision

## Status and identity

This document records approved design direction, not implemented features or an
instruction to build them during bootstrap. The Long Way Home is a story-driven
science-fiction automation adventure. Narrative drives progression; factory
construction, research, and exploration are the means through which Dave
accomplishes his goals.

## Approved visual direction

- Rich, illustrated 2D artwork in an angled overhead perspective.
- Vibrant environments, detailed machinery, and cohesive visual design across
  all assets.
- Atmospheric lighting with strong gameplay readability.
- A contextual construction grid.
- Owner-approved Dave exception: use the legacy helmeted pixel-art walking and
  idle sheets consistently across four directions. This does not change the
  broader environment direction or import legacy gameplay. Implementation is
  merged in PR #25; runtime acceptance remains with the owner.

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
P5's feature branch, pending merge and owner acceptance, adds Smelter recovery
after first Ferrite Ore acquisition; the existing musing remains at acquisition.
Fabricator stays dormant. F5 stays legacy; Computer repair, Fabricator recovery
wiring and cutover remain deferred. This changes
no approved narrative, inventory or progression requirements.

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
- Dave's internal musings use a separate small, portrait-free, nonpausing
  presentation with automatic dismissal, rather than the conversation panel.
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

## Approved Ferrite discovery direction

- Ferrite is the first structural metal resource: dark slate-gray mineral ground
  with silver metallic veins, a broadly oval usable area and occasional raised
  formations. Deposits are infinite, uniformly rich and never deplete.
- One guaranteed authored deposit near the ship introduces deliberate inspection,
  Dave's engineering deduction and guidance to locate the Extractor in the
  maintenance bay. Computer does not identify the mineral in this sequence.
- Mineral-bearing ground is independent of decorative artwork and terrain chunks.
  Approved Extractors occupy 2 x 2 independent 32-unit construction cells; their
  designated extraction point must overlap compatible ground. Other parts may
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

Implementation is on the production feature branch, pending owner acceptance and
merge. Agent checks are static only; regression scripts are added/updated but
unexecuted. No Godot type checking, runtime or graphical verification is claimed.
See [implementation and ordered owner checklist](../README.md#fabricator-production-feature-branch-pending-merge).
Earlier Fabricator sections retain their milestone-specific historical scope;
this approved production direction extends their formerly deferred behavior.

## Unresolved design details

- The precise conspiracy behind Dave's arrival remains under development.
- Footprints beyond the approved Extractor, Smelter and Fabricator, port rules, rail behavior, research
  content, chapter structure, dialogue formats, and ending conditions still
  require design work. The approved intentions above do not settle these details.

Bootstrap establishes project files and documentation only. Gameplay systems,
content pipelines, assets, and speculative frameworks are outside its scope.
