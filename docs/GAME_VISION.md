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
  Fabricator remains secured without an interaction prompt.
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
feature below. Power and Fabricator rack recovery remain unimplemented.
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
  Smelting and recipes remain subsequent work. Fabricator stays visible,
  noninteractive and unrecoverable.
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
- Fabricator remains visible, noninteractive, unrecoverable and unavailable in
  Equipment. Recipe switching remains future work in
  [issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37).
  Future rotating lower-left input/lower-right output ports remain tracked in
  [issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35).

Implementation is on the Ferrite Ingot production feature branch, pending merge
and owner manual testing. State ownership and validation limits are in the
[implementation notes](../README.md#produce-ferrite-ingots-feature-branch-pending-merge).

## Unresolved design details

- The precise conspiracy behind Dave's arrival remains under development.
- Footprints beyond the approved Extractor and Smelter, port rules, rail behavior, research
  content, chapter structure, dialogue formats, and ending conditions still
  require design work. The approved intentions above do not settle these details.

Bootstrap establishes project files and documentation only. Gameplay systems,
content pipelines, assets, and speculative frameworks are outside its scope.
