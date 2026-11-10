# Application shell, title screen and pause menu

Milestone 1 merged in [PR #166](https://github.com/interneth3ro/the-long-way-home/pull/166).
Milestone 2, Pause Menu Foundation, merged in [PR #167](https://github.com/interneth3ro/the-long-way-home/pull/167)
after owner 18/18 F5 PASS. Tracks
[Issue #165](https://github.com/interneth3ro/the-long-way-home/issues/165).
Milestone 3 initial exterior preparation is implemented on
`codex/initial-exterior-preparation`, **pending owner F5 acceptance and merge**.
Loading UI and persistence remain future milestones.

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
[MainV2](../scenes/main/main_v2.tscn). Adding the child completes interior
ready/spawn initialization; the shell then awaits the controller's explicit
`prepare_initial_exterior()` success before ending startup. MainV2 retains Main's session-owned
PlaythroughState, Dave, inventory, objectives, HUD and transition controller.
The shell does not move gameplay authority or change input bindings. MainV2 is
explicitly Pausable; the shell and its menu UI use Always so menus remain responsive
while simulation and player input are paused. Existing startup-failure pauses remain
intact. The shell retains the pre-session pause state for session retirement.

F6 with `main_v2.tscn` open still starts gameplay directly; F6 with
`scenes/main/main.tscn` open remains the legacy fallback. These direct-scene paths retain on-demand exterior creation on first exit.
The shell's New Game path prepares and retains the exterior before releasing
Dave inside the ship, as described below. No shared loading screen is added.

## Background

[TitleBackground](../scenes/application/title_background.tscn) is an independent,
script-free presentation scene. The unchanged accepted
[damaged ship PNG](../assets/environment/exterior/crashed_exploration_ship_approved.png)
is fitted with preserved aspect ratio against a dark blue-gray field and dimmed
with local tint/shade for readability. It adds no terrain or playable exterior
instance, animation, artwork or asset/import changes. The restrained static
composition can later be replaced independently of menu logic.

## Pause menu — Milestone 2 (merged)

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

Milestone 2 did not change gameplay systems, scene transitions or accepted artwork,
and introduced no persistence or loading features. Milestone 3 changes only the
New Game exterior lifecycle described below.

## Initial exterior preparation — Milestone 3 (pending acceptance and merge)

Approved [Issue #165](https://github.com/interneth3ro/the-long-way-home/issues/165)
D7/D46 Option B requires 49 starting chunks. The authored `Spawns/FromShip`
position is (-384, -64); floor-based conversion with 2048-unit chunks gives center
**(-1, -1)**. The exact radius-three square covers **(-4, -4) through (2, 2)**.
The extra 24 chunks supplement the existing 25-chunk arrival square. Normal
`loading_radius = 2`, `retention_margin = 1`, renderer envelope and exploration
streaming remain unchanged. No planet-wide preload is performed.

The shell calls [SceneTransitionController](../scenes/main/scene_transition_controller.gd)
after MainV2's synchronous interior spawn setup. The controller locks Dave,
suspends PlaythroughState production, sets its explicit busy state and raises the
existing opaque fade curtain. It owns one newly instantiated exterior and stages
it in `Worlds`, visible for publication checks but with incidental node processing
disabled. Dave stays attached to the interior. The existing
[exterior](../scenes/world/planet_exterior.gd) generator setup is shared with arrival;
`prepare_initial_neighborhood(state)` drives the existing budgeted terrain and
required-only Ferrite steps directly, yielding between frames.

`preparation_is_ready(receipt)` is independent of player attachment. It checks
request generation, world identity, seed, revision, authored center, empty work
queues, no cancellation/failure, all 49 attached current chunk publications,
flushed tint and completed current Ferrite presentation. Generated data or submitted
texture work alone never authorizes success. Existing `arrival_is_ready(receipt)`
retains all player/attachment/spawn/publication checks unchanged. Legacy fallback
startup also requires actual attached revision-current chunks, without adding
illustrated receipts to its existing arrival contract.

After readiness and held-input draining, the controller revalidates, detaches the
exterior into its existing `_worlds[EXTERIOR_SCENE]` cache, and only then marks
`initial_exterior_initialized`, restores production and releases Dave. Detached
worlds have no active processing or physics. Terrain chunk/surface identities,
generation tokens, publication receipts and renderer state survive retention.
First exit retrieves that same exterior; reattachment makes publication evidence
queryable again and runs the existing arrival/fade/input/camera/physics validation.
The 49 current terrain chunks are retained rather than regenerated. Existing
Ferrite teardown invalidates its request token; arrival replans/revalidates required
owners using retained region data, textures and sprites. Existing sprites are
excluded from new registration/publication work. This brief resource revalidation
is intentional; the first exit is not promised to be zero-frame or zero-cost.

`initial_preparation_progress(completed, total)` forwards real completed work:
49 current terrain publications plus one completed required-resource phase, total
50 units. This is a unit count, not equal time weighting or a whole-startup
percentage. Later loading UI can compose this phase with other work. Completion
still requires the success receipt; a progress event alone cannot enable input.
No loading-screen UI, save identity/storage, SQLite, initial autosave (D33), load
restoration (D44) or persistence contract is implemented here.

Cancellation invalidates generation authority and leaves startup locked. Replaced
world/seed/revision, teardown, incomplete publication and genuine terrain/resource
failure cannot report success. Controller ownership is rechecked after awaits;
normal session teardown frees staged children and detached cached worlds. Genuine
publication failures preserve the existing stop/block behavior. A failure may
leave the curtain raised and require restart; no retry/recovery UI is added.
Global pause is not the success contract. Direct F6 startup is outside the shell's
New Game initialization contract and keeps its prior behavior.

Performance remains unmeasured. Continuous sampling keeps its existing work/time
slices, but chunk detail/tint construction, GPU texture publication/tint updates,
illustrated chunk publication and individual resource texture loads still have
synchronous costs. Retaining 49 chunks plus texture/sprite caches raises initial
memory use versus deferred first exit. No terrain quality or resource fidelity is
reduced. Owner F5 time/memory measurements remain required; static tests cannot
certify smooth frames, actual GPU submission, or memory use.

### Milestone 3 owner F5 checklist (not executed by the agent)

- [ ] F5 title and New Game work; startup stays obscured with Dave/control and production locked until preparation completes. Holding movement/activation/Escape during startup does not leak into gameplay.
- [ ] In the debugger, before release, verify center (-1,-1), exactly 49 chunks at x/y -4 through 2, empty pending/continuous work, current publications and completed required Ferrite presentation. Progress advances from completed work to 50/50; initialization marks complete only after validation.
- [ ] On release Dave is at the normal V2 ship spawn with the normal camera; exterior is detached and cached, with no active exterior processing while inside.
- [ ] Record cached exterior/chunk/surface instance IDs and terrain generation/token values. First exit reuses them: all 49 initial terrain chunks remain, generation/token values do not advance for those chunks, and terrain/Ferrite are fully presented before input returns.
- [ ] First exit, repeated boarding/exit and quick-transition cancellation retain fade, facing, spawn, camera, input lock and arrival safety. No duplicate sprites, missing ground or stale requests appear.
- [ ] Explore beyond the initial square: new chunks stream, old chunks retire with the existing retention margin; return to ship remains functional.
- [ ] Return to title and New Game again: old staged/cached exterior is freed; new playthrough gets a distinct exterior and fresh state.
- [ ] With a controlled debugger intervention, cancel preparation or replace its world context while pending; verify false-ready never occurs and no stale callback unlocks Dave. Retire/restart the session afterward. Do not modify frozen assets to inject failures.
- [ ] Observe error output and verify no new parse/runtime errors. Check existing machine deployment, production, inventory, transfers, recovery, narrative and accepted artwork/animations.
- [ ] Measure New Game wall time, first-exit latency, peak/startup and retained memory on the owner system; record observations without running stress tests or freeze reproduction.

Agent checks are Python static fixtures/source/resource inspection and inert runner
fixtures only. No engine parsing, import, headless, graphical or runtime validation
is claimed. Owner graphical acceptance and merge require separate decisions.

## Verification and owner acceptance

Agent verification is static only: Python text/resource-graph, pause lifecycle,
focus/confirmation and preservation checks, plus diff/link validation. These do not
parse GDScript with Godot or establish rendered layout, input behavior, scene
teardown, gameplay or runtime correctness. Godot headless, graphical, playable and
performance checks were not run. The historical Milestone 2 checklist below
received owner 18/18 F5 PASS for PR #167. Milestone 3 acceptance above remains pending.

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
