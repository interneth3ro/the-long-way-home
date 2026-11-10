# Application shell and title screen — Milestone 1

Implemented on `codex/application-shell-title-screen`, pending owner F5 acceptance
and merge. Tracks [Issue #165](https://github.com/interneth3ro/the-long-way-home/issues/165).
Only the title/startup shell is implemented. Loading UI, initial exterior
preparation, persistence and pause remain future milestones.

## Startup and ownership

F5 starts [Application](../scenes/application/application.tscn). Its small
[script](../scenes/application/application.gd) owns title and gameplay child
lifetimes, without an autoload. The title emits New Game and Exit requests.
Load Game and Settings are disabled and excluded from keyboard focus. New Game
starts focused; arrows and Tab cycle between enabled options, using normal Godot
activation and mouse conventions. Hover brightens text; focus adds an underline.
Exit calls `SceneTree.quit()` without confirmation.

New Game guards duplicate requests and disables the menu immediately. The shell
consumes transition input and waits for held keys/buttons to release, plus a frame
to drain polling state, before detaching the title and instantiating a fresh
[MainV2](../scenes/main/main_v2.tscn). Adding the child completes the existing
synchronous ready/spawn initialization. MainV2 retains Main's session-owned
PlaythroughState, Dave, inventory, objectives, HUD and transition controller.
The shell never resets gameplay pause/input bindings or moves gameplay authority.
Normal tree teardown frees the session child and its state. No return-to-title
action is introduced.

F6 with `main_v2.tscn` open still starts gameplay directly; F6 with
`scenes/main/main.tscn` open remains the legacy fallback. Exterior creation remains
on first exit, with its existing initialization delay. No loading screen or
progress reporting is added, including during synchronous New Game setup.

## Background

[TitleBackground](../scenes/application/title_background.tscn) is an independent,
script-free presentation scene. The unchanged accepted
[damaged ship PNG](../assets/environment/exterior/crashed_exploration_ship_approved.png)
is fitted with preserved aspect ratio against a dark blue-gray field and dimmed
with local tint/shade for readability. It adds no terrain or playable exterior
instance, animation, artwork or asset/import changes. The restrained static
composition can later be replaced independently of menu logic.

## Verification and owner acceptance

Agent verification is static only: Python text/resource-graph checks and diff/link
validation. These do not parse GDScript with Godot or establish rendered layout,
input behavior, gameplay or runtime correctness. Godot headless, graphical,
playable and performance checks were not run. All owner checks remain pending.

- [ ] F5 opens the title screen without gameplay input or HUD.
- [ ] THE LONG WAY HOME is centered near the top and readable.
- [ ] All four options are visible, vertically stacked and centered beneath the title.
- [ ] Load Game and Settings are muted, cannot activate and are skipped by focus.
- [ ] Mouse hover brightens enabled text; focus has a readable underline.
- [ ] Arrows and Tab/Shift+Tab navigate; Enter/Space activate enabled options.
- [ ] New Game enters the production V2 ship; repeated activation creates one session.
- [ ] Hold activation/movement during New Game, then release: menu input does not carry into gameplay.
- [ ] Dave spawns with existing Initial position/facing; movement works once ready.
- [ ] Existing inventory and hotbar initialize correctly for a fresh session.
- [ ] Ship-to-exterior and return transitions work, including existing first-exit preparation.
- [ ] Existing machine gameplay, animations and Smelter thermal behavior remain intact.
- [ ] Stop/relaunch: New Game starts fresh without prior in-memory progression.
- [ ] Exit closes the game with mouse and keyboard activation (separate launches).

Owner graphical acceptance and merge are separate decisions. This document grants
no Godot execution authorization.
