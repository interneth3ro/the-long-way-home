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

- Authored ship interior (including the eventual equipment room in the same
  scene) and a separate planetary exterior with an authored crash site.
- Terrain tiles are 64 x 64 pixels; future chunks are 32 x 32 terrain tiles,
  or 2,048 x 2,048 world units. The construction grid is independently 32 x 32
  world units; machine footprints are not constrained to one terrain tile.
- Future expansion uses seeded deterministic generation with persistent
  buildings, resources and terrain modifications. These systems are deferred.
- The first ship exit uses an understated fade reveal; later exits and returns
  are immediate. Completion is per playthrough and must eventually participate
  in durable saves. The First Step feature branch currently provides session
  state only; there is no implemented save/load workflow.

Implementation and coordinate conventions are recorded in the
[README](../README.md#the-first-step-feature-branch-pending-merge).

## Unresolved design details

- The precise conspiracy behind Dave's arrival remains under development.
- Detailed machine footprints, port rules, rail behavior, research content,
  chapter structure, dialogue formats, and ending conditions still require
  design work. The approved intentions above do not settle these details.

Bootstrap establishes project files and documentation only. Gameplay systems,
content pipelines, assets, and speculative frameworks are outside its scope.
