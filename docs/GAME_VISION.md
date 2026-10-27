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
  remains separate from agent static validation. State is in memory only. Buildings and
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
  Future Extractors occupy 2 x 2 independent 32-unit construction cells; their
  designated extraction point must overlap compatible ground. Other parts may
  extend beyond the deposit. Machines may touch edges but footprints may not
  overlap. All valid points give the same rate. Construction mode will highlight
  only compatible deposits.
- Future production: Ferrite Ore → Smelter → Ferrite Ingot → Fabricator →
  Plate / Rod / Bearing. Computer's initial repair requires Plates and Rods.
  These machines, recipes and extraction remain unimplemented.

First Ferrite implementation is merged in PR #28. The owner reports all 15 original
manual playtests passed; final musing timing and temporary developer coordinate
HUD adjustments remain pending owner review. One-time discovery and compact
timed musings use session-only state. There is no
durable save/load. See the [implementation notes](../README.md#first-ferrite---discovery-pr-28-merged).

## Approved Extractor recovery direction

- The maintenance bay holds intact packaged Extractor, Smelter and Fabricator
  modules in three visible racks. Only Extractor becomes recoverable after
  Ferrite discovery; the other two remain secured without interaction prompts.
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

Recover the Extractor implementation is pending merge and owner gameplay testing.
It adds only the bay, inventory and first recovery step; deployment, mining,
power, production and later recovery remain unimplemented. Inventory and recovery
are session-only and reset with a fresh Main instance. See the
[implementation notes](../README.md#recover-the-extractor-feature-branch-pending-merge)
for approved dialogue, ownership and validation limits.

## Unresolved design details

- The precise conspiracy behind Dave's arrival remains under development.
- Detailed machine footprints, port rules, rail behavior, research content,
  chapter structure, dialogue formats, and ending conditions still require
  design work. The approved intentions above do not settle these details.

Bootstrap establishes project files and documentation only. Gameplay systems,
content pipelines, assets, and speculative frameworks are outside its scope.
