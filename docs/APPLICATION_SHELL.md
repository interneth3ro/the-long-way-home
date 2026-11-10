# Application shell, title screen and pause menu

Milestone 1 merged in [PR #166](https://github.com/interneth3ro/the-long-way-home/pull/166).
Milestone 2, Pause Menu Foundation, is implemented on `codex/pause-menu-foundation`,
pending owner F5 acceptance and merge. Tracks
[Issue #165](https://github.com/interneth3ro/the-long-way-home/issues/165).
Loading UI, initial exterior preparation and persistence remain future milestones.

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
The shell does not move gameplay authority or change input bindings. MainV2 is
explicitly Pausable; the shell and its menu UI use Always so menus remain responsive
while simulation and player input are paused. Existing startup-failure pauses remain
intact. The shell retains the pre-session pause state for session retirement.

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

## Pause menu — Milestone 2 (pending owner acceptance and merge)

[PauseMenu](../scenes/application/pause_menu.tscn) is a shell-owned CanvasLayer above
existing gameplay HUD and fades. A translucent dark ColorRect dims the live view;
no background world or screenshot is created. PAUSED and six centered text options
use the title's IBM Plex Sans typography, hover colors and focus underline.
Resume Game, Main Menu and Exit Game form the keyboard focus cycle; Save Game,
Load Game and Settings are muted, disabled and excluded from focus.

The shell opens pause only from `_unhandled_input`, after descendant gameplay and
GUI handlers. Inventory (including assignment popups), machine inspection/recipe
selection, construction/recovery, dialogue/responses and Computer repair keep their
existing Escape handlers unchanged. Computer's automatic cinematic retains its
input lock; active world transitions cannot open pause. A subsequent Escape during
normal gameplay opens pause. Direct gameplay F6 retains its existing behavior;
this milestone's menu belongs to the F5 application shell.

Opening pause captures `SceneTree.paused` before setting it. Resume Game and Escape
at the pause root leave the overlay active while held keys/buttons release, plus
one frame to drain polling state; only then does the shell restore the captured
pause value. Thus an already paused or startup-blocked session remains paused.
The overlay blocks mouse events; UI owns input while gameplay is Pausable.
Confirmation controls stay responsive without running simulation.

Main Menu always asks **Return to Main Menu?**; Exit Game always asks **Exit Game?**.
Both display **Any progress since your last save will be lost.** with Confirm and
Cancel; Cancel is initially focused. Escape cancels only the confirmation, restoring
focus to its pause option. Cancel never resumes gameplay. Confirmed Exit calls
`SceneTree.quit()`. Title-screen Exit retains its existing direct quit behavior.
No action saves progress.

Confirmed Main Menu drains held input while paused, closes the overlay, detaches
and synchronously frees MainV2, then creates a fresh title. Existing transition
teardown frees its detached cached worlds with session-owned state. The shell
restores the pre-session pause value, discarding pauses belonging to the retired
session. Another New Game instantiates fresh MainV2/PlaythroughState/PlanetWorldState;
no gameplay state is cached by the shell. Prior external pause state is preserved.

No gameplay systems, scene transitions, inventory, recipes, research, objectives,
narrative, production, recovery, deployment, accepted artwork, animation or Smelter
thermal behavior change. No persistence, SQLite, autosave, loading screen, exterior
preload, New Game configuration or cinematic is introduced.

## Verification and owner acceptance

Agent verification is static only: Python text/resource-graph, pause lifecycle,
focus/confirmation and preservation checks, plus diff/link validation. These do not
parse GDScript with Godot or establish rendered layout, input behavior, scene
teardown, gameplay or runtime correctness. Godot headless, graphical, playable and
performance checks were not run. Owner checks remain pending.

- [ ] 1. F5 opens the title screen normally.
- [ ] 2. New Game enters production V2.
- [ ] 3. Escape opens the pause menu during normal gameplay.
- [ ] 4. Gameplay remains visible behind the dimmed overlay.
- [ ] 5. PAUSED and all six options are visible and centered.
- [ ] 6. Save Game, Load Game and Settings are disabled and muted.
- [ ] 7. Mouse hover and keyboard focus work; arrows/Tab skip disabled options.
- [ ] 8. Escape at the pause root resumes gameplay.
- [ ] 9. Resume Game restores player movement and machine production.
- [ ] 10. Inventory, assignment/hotbar popups, construction/recovery, machine inspection/recipe selection, dialogue/response and repair UI retain Escape behavior; cinematic input lock and travel remain intact.
- [ ] 11. Main Menu always requests confirmation with the specified warning.
- [ ] 12. Canceling Main Menu (Cancel or Escape) returns to the paused game.
- [ ] 13. Confirming Main Menu returns to the title screen.
- [ ] 14. Starting New Game again creates a fresh session; inventory/progression and cached worlds do not carry over.
- [ ] 15. Exit Game always requests confirmation with the specified warning.
- [ ] 16. Canceling Exit (Cancel or Escape) returns to the paused game.
- [ ] 17. Confirming Exit closes the application.
- [ ] 18. No stale pause state, input leakage or unintended gameplay changes: hold movement/activation during Resume/title return, release and verify; existing machine production/recovery/deployment, artwork/animations and Smelter thermal behavior remain intact.

Static inspection additionally verifies prior-pause restoration and unchanged
startup-failure guards; those failure paths were not reproduced. Owner graphical
acceptance and merge are separate decisions. This document grants no Godot
execution authorization.
