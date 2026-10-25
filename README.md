# The Long Way Home

A story-driven science-fiction automation adventure. This fresh Godot project
has a player movement prototype with camera follow and mouse-wheel zoom, plus a
minimal ship-interior environment and collision foundation, plus data-driven
Computer dialogue and inspection. The minimal objective foundation on
`codex/objective-foundation` is pending merge and owner runtime verification.
It is independent of the previous FactoryGame project.

## Requirements and setup

Codex must follow the [Godot execution safety policy](AGENTS.md#godot-execution-safety)
before using the setup or launch instructions below. Graphical execution requires
explicit owner authorization; all headless execution is suspended following the
PR #5 incident until the owner explicitly lifts that restriction.

- Godot **4.7.2 stable**, standard build. GDScript is the initial scripting language;
  no .NET SDK or third-party plugins are required.
- Git for cloning the repository.

```sh
git clone https://github.com/interneth3ro/the-long-way-home.git
cd the-long-way-home
godot --editor --path .
```

`godot` denotes your Godot executable; use its full path if it is not on `PATH`.
Alternatively, import `project.godot` through Godot's Project Manager.

## Launch and validation

Press **F6** with `scenes/main/main.tscn` open, or **F5** to run the project.
From a terminal in the project root:

```sh
godot --path .
godot --headless --editor --path . --quit
godot --headless --path . --quit-after 60
```

The last two commands validate editor import and a bounded main-scene launch.
Headless checks do not verify graphical appearance. While execution is restricted,
use only nonexecuting checks under the policy above and report them as static
validation; runtime and engine verification remain unperformed.

## Layout and development

- `project.godot`: engine settings and main-scene entry point.
- `scenes/main/main.tscn`: primitive test floor, a central ship-deck composition,
  four static perimeter walls, and a Y-sorted group containing three static
  obstacles with ship-fixture visuals and an instance of Dave.
- `scenes/player/dave.tscn`: reusable `CharacterBody2D`, a collision shape, a
  `Camera2D` child, and a separate `Visual` child containing placeholder polygons.
- `scenes/player/dave.gd`: movement through `_physics_process()` and
  `move_and_slide()`.
- `scenes/player/follow_camera.gd`: wheel input and bounded zoom transitions using
  a built-in Tween; following uses the child camera's built-in behavior.
- `scenes/player/interaction_detector.gd`: Dave's proximity selection, solid-body
  visibility check and interaction requests; attached to an `Area2D` child.
- `scenes/interaction/world_interactable.gd`: small `StaticBody2D` interface owning
  availability, prompt, optional conversation and fallback inspection text.
- `scenes/ui/interaction_ui.tscn` and `interaction_ui.gd`: screen-space prompt and
  dismissible response, instantiated under Dave as a `CanvasLayer`.
- `dialogue/`: Inspector-editable `DialogueConversation` and `DialogueEntry`
  Resources, with temporary opening content in `computer_opening.tres`.
- `scenes/ui/dialogue_ui.tscn` and `dialogue_ui.gd`: reusable screen-space
  dialogue presentation and active entry position, instantiated under Dave.
- `objectives/`: editable objective definitions, scene-local state controller,
  and an isolated development-only input adapter with temporary demo content.
- `scenes/ui/objective_tracker.tscn` and `objective_tracker.gd`: screen-space
  objective data presentation and pin/hide preferences.
- `scenes/main/main.gd`: local objective state-signal wiring to the tracker.
- `docs/GAME_VISION.md`: approved direction and unresolved design questions.
- `AGENTS.md`: development conventions.

Use **WASD** or the **arrow keys** to move. The Input Map actions are `move_left`,
`move_right`, `move_up`, and `move_down`; WASD uses physical key positions.
`Input.get_vector()` limits direction length to one, keeping diagonal keyboard
movement at the same 240 pixels per second as cardinal movement. Dave's local
origin is his ground-contact position; replace the contents of `Visual` with
future artwork aligned to that origin without changing the controller or camera.

The camera follows Dave's ground-contact origin independently of `Visual`.
**Mouse wheel up** zooms in; **mouse wheel down** zooms out, centered on Dave.
Zoom starts at 1.0, changes its target by 0.1 per wheel press, and is clamped to
0.75–1.5. These are provisional tuning values in `follow_camera.gd`. Each changed
target starts a 0.15-second eased Tween from the current zoom; rapid scrolling
retargets the transition, and repeated input at a bound leaves it running to
completion. No per-frame zoom callback runs when a transition is idle.

The test floor spans x = -2048 to 2048 and y = -1536 to 1536 (4096 × 3072).
Dave spawns at (0, 0), clear of all collision footprints. Four 32-pixel-thick
`StaticBody2D` walls sit just outside the floor; their rectangular shapes meet at
the corners. Three obstacles sit at (-320, -180), (360, 40), and (0, 420), with
160 × 48, 96 × 64, and 160 × 48 collision footprints respectively. All bodies use
the default collision layer/mask, matching Dave. Shapes and colored polygon
visuals are separate children; the console also has a small interaction script.

`GroundObjects` enables built-in Y-sorting for Dave and the obstacle roots at the
same default Z index. Each obstacle root is anchored at the bottom center of its
ground footprint, matching Dave's ground-contact origin. Its collision rectangle
extends upward from that anchor, while its taller visual extends above the
footprint to allow overlap when Dave stands behind it. Visual children stay
together as one sorted object. The floor and perimeter are outside this group.
There are no camera limits; floor edges can still become visible near the walls.
Existing movement, camera/zoom, display, rendering, and physics settings are
preserved.

The ship visual pass uses only built-in `Polygon2D` and `Line2D` details.
`ShipDeck` covers x = -656 to 656 and y = -448 to 592, leaving the rest of the test
floor open. Sixteen inset panels, muted amber route guides and service markings
frame a clear central walking area. This is a deck section, not a new enclosed
room; the original distant perimeter remains the only boundary collision.
Blue-teal housings, pale metal edges and restrained amber/coral accents form a
temporary palette, not production artwork or a lighting system.

The existing `WestObstacle` now depicts a damaged computer console with a fractured
screen, warning indicator, ribbed front and exposed service cable. `EastObstacle`
depicts a life-support filter unit with a faceted cap, filter window and service
pipe. `SouthObstacle` depicts a storage workbench with cabinet doors, a work mat,
loose cover and tool tray. The console supports temporary dialogue with
inspection fallback; the other fixtures remain noninteractive
placeholders.
These visual identities establish no new narrative state or objectives.
All fixture details remain under each existing `Visual` child, within its original
visual bounds, with no individual Z overrides or nested Y-sorting. The three body
positions, bottom-center anchors and collision shapes are unchanged. Flat deck
details are outside `GroundObjects`, drawn before it at the default Z index.

Validation for this feature is static only: scene/resource references, rectangle
placement, spawn clearance, Y-sorting hierarchy, unchanged scripts/settings,
documentation links, and Git diff checks. Godot has not been executed; engine
loading, collision response, and graphical layering remain unverified. Before
merging, the owner should manually check all four walls and corners, walk around
each obstacle from every direction, slide along its edges, and confirm Dave
appears behind its upper visual and in front below its anchor. Also verify camera
follow and mouse-wheel zoom throughout the area, including both zoom bounds.
For the ship visual pass, also assess the palette, fixture recognition, floor
marking readability and clear walking routes at the starting view and both zoom
bounds. Check that all fixture details occlude together as Dave walks behind and
in front, and that their visible bases agree with collision contact. No engine,
runtime or graphical verification was performed for this pass.

The interaction requires Dave's collision center to be **at most 120
world units from the interaction point**, measured as straight-line distance.
The detector's circle radius in `dave.tscn` supplies this single distance limit.
A direct physics shape query at Dave's current position finds candidate bodies;
the explicit point-distance check then rejects candidates beyond the limit.
Cached `Area2D` overlap monitoring is disabled. It selects the nearest available
point whose physics ray first hits that target's solid body, excluding Dave.
The console's point is the center of its existing 160 × 48 footprint: its sides
and corners are reachable within the limit without changing collision geometry.
A solid obstacle between Dave and the target blocks the prompt and interaction.
All proximity, distance and obstruction checks run in the physics callback,
including before fulfilling an interaction request.

When available, a screen-space **E — Talk to Computer** prompt appears. Physical
**E** uses the existing `interact` action. The detector routes a valid conversation
to DialogueUI; an absent or invalid conversation falls back to inspection text.
An interactable is available when enabled and either content source is valid.
Inspection still closes with E, Esc or its Close button. Only one panel opens at
a time; new interactions and contextual prompts are suppressed during dialogue.

A fresh E press or **Next** advances entries in order. On the last entry,
**Finish** or E completes the conversation; **Dismiss** or Esc closes it without
completion. DialogueUI emits distinct completion and dismissal signals, clears
its active position on close and starts at the first entry on reinteraction.
No persistent state is recorded. Key echoes are ignored, and opening is deferred
to the physics callback so the opening key event cannot advance the first entry.
Leaving range does not close either panel. Movement and wheel zoom continue;
the screen-space UI does not pause the game or follow camera zoom.

Content ownership stays separate from presentation: `DialogueConversation` exports
a stable `conversation_id` and ordered `Array[DialogueEntry]`; each entry exports
`entry_id`, `speaker_id`, `speaker_display_name` and multiline `text`. Edit these
in `dialogue/computer_opening.tres`, assigned through the console's exported
`conversation` property in `main.tscn`. Keep IDs stable and entry IDs unique within
a conversation. Empty IDs, speakers/text, null entries and duplicate entry IDs
make a conversation invalid. The three opening lines are temporary content, not
finalized narrative canon. The console's existing inspection response is retained.
Dialogue does not change objective state. No choices, narrative flags, log or save
system are implemented.

Dialogue validation is static only: resource paths and UID sidecars, typed exports,
nonempty content and unique IDs, scene/UI wiring, input flow, completion versus
dismissal, inspection fallback and preserved range/obstruction logic. Movement,
camera, collision, rendering and project settings are unchanged. Godot was not
executed; engine loading, runtime input and graphical behavior remain unverified.
Before merging, the owner must manually check all three speakers/lines in order,
E and Next/Finish, Esc and Dismiss, held E without skipped entries or automatic
reopening, reinteraction starting at the first entry, and leaving range while
open. Check prompt suppression, movement and zoom during dialogue and readability
at both zoom bounds. Temporarily clear the console's conversation reference (and
separately assign invalid content) to verify inspection fallback, then restore it.
Also verify range boundaries, approach from all sides/corners, obstruction,
inspection dismissal and the other fixtures remaining noninteractive.

## Objective foundation (feature branch, pending merge)

`ObjectiveDefinition` exports a stable `objective_id`, short `title` and multiline
`description`, editable through `.tres` resources. Treat definitions as read-only
content during play; activation and completion are never stored in Resources.
`ObjectiveController` owns one dictionary of runtime states: `INACTIVE`, `ACTIVE`
and `COMPLETED`. `activate_objective(id)` accepts only inactive objectives;
`complete_objective(id)` accepts only active objectives. Both return `true` only
for a transition and emit `objective_state_changed(id, state)` once. Unknown IDs,
repeated calls and invalid transitions return `false` without an emission.
`get_objective_state(id)` returns the state, or `-1` for an unknown/rejected ID.
Null/invalid definitions are ignored; duplicate valid IDs are rejected entirely.
Completed objectives cannot reactivate. State resets on scene reload.

The main scene wires the controller signal to `ObjectiveTracker.show_objective()`.
The first active definition in exported list order is shown; completing it reveals
the next active definition, if any. There is no separate current-objective state.
The tracker only reads supplied content and owns presentation preferences; it
never activates or completes objectives. No autoload, dialogue dependency, Dave
controller changes, persistence or quest graph are introduced.

The tracker occupies the top right of its own `CanvasLayer`, using the existing
ship UI palette. It is independent of camera zoom, above the bottom dialogue and
inspection region at the configured 1280 × 720 viewport. **Pin** selects pinned
mode; **Unpin** returns to contextual mode. In this foundation both modes stay
visible while an objective is active; there is no timed fade or extra contextual
suppression rule. **Hide** conceals the panel and leaves **Show objective** in its
place; restoring returns to contextual mode. Preferences survive supplied-data
changes within the scene, so hidden stays hidden until restored. With no active
objective neither the panel nor restore button is shown, even when pinned.

For owner manual testing in a debug build, physical **J** activates the temporary
`demo_investigate_computer` objective; physical **K** completes it. Key repeats
and modified key presses are ignored. These keys do not overlap the current
movement, interaction, zoom or UI controls and add no project Input Map entries.
The objective starts inactive. Its temporary title is **Investigate Computer**;
its description is **Examine the damaged ship's Computer console.** This is demo
content only, independent of Computer's dialogue and inspection. The isolated
`ObjectiveDemo` node is disabled outside debug builds. Remove that node, its
`objective_demo.gd` script/UID, and the demo resource/list assignment when replacing
the demonstration with narrative integration. No debug menu or console is added.

Validation is static only: resource references, script UID sidecars, transition
guards, signal wiring, pin/hide/restore paths, UI anchors, documentation links,
preserved gameplay/settings and Git diff checks. Godot was not executed; engine
loading, runtime input, text wrapping and graphical behavior remain unverified.
Before merging, the owner must activate with J, try repeated/held J, test Pin,
Unpin, Hide and Show objective, then complete with K and repeat it. Try K before
activation and J after completion (both must have no effect); reload the scene
to repeat the demo. Check the tracker at zoom 0.75 and 1.5, with dialogue and
inspection open, and confirm existing movement, interactions, dismissal and
wheel zoom still work. Unknown IDs, duplicate definitions and signal counts
require owner-authorized runtime API verification; they were inspected statically.

Add feature directories and GDScript files when they have a concrete purpose.
Keep Godot's `.godot/` cache untracked. Use feature branches and pull requests;
validate affected scenes and scripts before requesting review.

Keep authoritative documentation in `docs/` and generated evidence out of Git;
the artifact retention and ZIP policies are in [AGENTS.md](AGENTS.md).
Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
review. After an approved merge, separately request
[post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) for that PR number
from a chat attached to a surviving checkout. Cleanup stops when preservation,
attachment or Windows lock safety cannot be verified.
