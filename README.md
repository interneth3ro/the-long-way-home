# The Long Way Home

A story-driven science-fiction automation adventure. This fresh Godot project
has a player movement prototype with camera follow and mouse-wheel zoom, plus a
minimal ship-interior environment and collision foundation, plus data-driven
Computer dialogue and inspection. The objective foundation is present; first
narrative integration on
`codex/first-narrative-integration` is pending merge and owner runtime verification.
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
  `Camera2D` child, and a separate `Visual` child containing Dave's illustrated
  static fallback `Sprite2D`, south/north walk and idle sprites, and the shared
  `AnimationPlayer` described below (directional idle pending merge).
- `scenes/player/dave.gd`: movement through `_physics_process()` and
  `move_and_slide()`, with input-based north/south walk presentation selection
  and presentation-only last-facing retention (pending merge).
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
  and provisional opening content in `restore_computer.tres`.
- `scenes/ui/objective_tracker.tscn` and `objective_tracker.gd`: screen-space
  objective data presentation with expand, pin, hide and restore controls.
- `scenes/main/main.gd`: scene-local dialogue completion, objective activation
  and tracker wiring.
- `docs/GAME_VISION.md`: approved direction and unresolved design questions.
- `AGENTS.md`: development conventions.

Use **WASD** or the **arrow keys** to move. The Input Map actions are `move_left`,
`move_right`, `move_up`, and `move_down`; WASD uses physical key positions.
`Input.get_vector()` limits direction length to one, keeping diagonal keyboard
movement at the same 240 pixels per second as cardinal movement. Dave's local
origin is his ground-contact position; artwork stays under `Visual`, aligned to
that origin without changing the controller or camera.

### Dave static sprite baseline (PR #21, merged)

The merged static replacement uses the approved
`assets/characters/dave/dave_static_approved_v2.png`: a 1184 × 1328, 8-bit RGBA
PNG copied byte-for-byte from the owner's local `dave v2.png`. The original
`dave_idle_angled_overhead_pilot.png` and its import metadata remain available
for comparison and rollback. Its prior transform was scale `(0.065, 0.065)`
and offset `(-324.5, -1431)`, with `centered = false`. Historical owner testing
at the earlier 0.045 scale passed nine of ten checks but found Dave too small;
the subsequent 0.065 refinement had no recorded gameplay verification. Those
results do not validate this replacement. The source PNGs are not edited or recompressed.
The new `.png.import` sidecar follows the existing lossless texture settings,
with a distinct UID, disabled mipmaps and no size limit. It was prepared as text;
Godot has not imported it. Generated `.godot/` data stays ignored.

Provisional tuning is local to `Visual/Sprite2D`: uniform
`scale = (0.0744, 0.0744)`, default position `(0, 0)`, `centered = false`, and
texture-pixel `offset = (-588.5, -1287)`. Linear texture filtering is retained.
At alpha >= 32, exclusive bounds are `(289, 58)`–`(888, 1287)` for the new art
and `(24, 24)`–`(624, 1431)` for the previous art. Matching visible height gives
`(1431 - 24) * 0.065 / (1287 - 58) = 0.074414…`, rounded to 0.0744.
The new visible extent is approximately 44.57 × 91.44 world units, versus
39.00 × 91.46 previously: essentially the same height, with a roughly 14% wider
silhouette. The offset centers the substantial horizontal bounds and maps the
lower boot edge to y = 0. Faint alpha extends beyond those bounds, including
below the boot; the canvas bottom is not the ground anchor. The full new canvas
spans about 88.09 × 98.80 world units. Preserve the source-pixel offset when
adjusting uniform scale to retain this anchor.

Dave's root and `Visual` origins, radius-10 collision circle at `(0, -10)`,
Y-sorting and Z settings are unchanged. Camera, movement, input, interaction,
dialogue, objectives, Computer artwork and project settings are unchanged.
There is no animation, shader or new gameplay behavior in this replacement.

Validation is static only: PNG decoding and transparency, source/copy SHA-256
identity, resource paths and import metadata, transform calculations, unchanged
nonvisual scene data and gameplay files, Markdown links and Git diff checks.
Neither graphical nor headless Godot execution was performed. Engine import,
rendering and gameplay behavior remain unverified for this replacement.

The owner must manually assess normal-zoom readability, proportions beside damaged
Computer and other objects, dark-background readability, boot contact, collision
and Y-sorting. Repeat visual checks at 0.75× and 1.5× zoom, check camera follow
and movement, then interactions, dialogue and objective progression. Inspect
transparency fringes, the source's faint halo, clipping and scaling artifacts.
Scale and alignment remain provisional until this playtest.

### Dave south-facing walk baseline (PR #22, merged)

PR #22 added south-facing walking presentation. The owner reports it was
validated and merged; the static-only results below record the original agent
validation. The north extension preserves its artwork, transforms and animation.
The original approved `assets/characters/dave/dave_walking.png` is preserved
byte-for-byte: 1983 x 793 RGBA, SHA-256
`02c9d474a90e7a6bd1f88bb2a954e88afb3df50c408f88dc1476596dcbf1a7a7`.
After inspection, the owner authorized removing only stray margin pixels in
derived frames. The derived `dave_walk_south_atlas.png` is 1920 x 784 RGBA,
containing four 480 x 784 cells in the original left-to-right order: left-foot
contact, opposite knee passing, right-foot contact, other knee passing.

Preparation uses integer translations only, with no resampling, repainting or
pose changes. Starting with source cells at x `[0,500)`, `[500,989)`,
`[989,1478)`, `[1478,1983)`, retain all pixels inside each alpha >= 32 bounding
box and all nonzero-alpha pixels 8-connected to the main silhouette. Remove
only detached pixels outside that box: 160, 46, 68 and 40 pixels respectively
(314 total, all alpha 1/255). Connected faint outlines remain. Crop transparent
margins and translate each retained image onto a transparent cell using these
source anchors; all bounds and baselines below are exclusive pixel edges.

| Frame | Retained source bounds (x0, y0, x1, y1) | Source anchor (x, y) | Cell anchor |
| --- | --- | --- | --- |
| 1 | (33, 20, 471, 779) | (254, 770) | (240, 770) |
| 2 | (528, 17, 967, 763) | (745, 755) | (240, 770) |
| 3 | (1013, 15, 1453, 779) | (1233, 770) | (240, 770) |
| 4 | (1500, 15, 1941, 764) | (1724, 755) | (240, 770) |

Horizontal anchors use rounded substantial silhouette centers; vertical anchors
use the substantial lower boot edge. This aligns ground contact, preserving the
poses' small torso bob (about 1.8 world units). `Visual/WalkSouthSprite` uses
`hframes = 4`, `centered = false`, offset `(-240, -770)` and uniform scale
`(0.1224, 0.1224)`. Contact poses are approximately 91.2-91.4 world units tall,
matching the static baseline's 91.44; the walking silhouette is wider, about
52.5 units versus 44.57. Both sprites retain linear filtering. Original artwork,
static sprite properties, body/Visual origins, collision and Y-sorting remain
unchanged. Both new PNG import sidecars use distinct UIDs and existing lossless,
no-mipmap, unlimited-size settings; they were written as text without engine import.

`Visual/AnimationPlayer` owns an editor-editable embedded AnimationLibrary in
`scenes/player/dave.tscn`. Its looping `walk_south` animation lasts 0.5 seconds:
discrete `WalkSouthSprite:frame` keys 0, 1, 2, 3 at 0, 0.125, 0.25, 0.375 seconds
give 8 FPS at the default playback speed of 1.0. `RESET` restores frame 0 for
editor preview. No animation track modifies transforms, collision or world position.

The controller checks the existing input vector after the unchanged movement
code: positive y and approximately zero x means straight south. Diagonals use
the static sprite. Entry starts the animation and applies its first frame
immediately; sustained south input does not restart it. Idle or another direction
stops playback, hides the walk sprite and shows the original static sprite with
its approved scale/offset. The trigger follows input, so pushing south against a
wall still animates. There are no other directional animations, speed modifiers,
sprinting, input-map changes or changes to camera, interactions, dialogue or objectives.

Validation is static only: decoded PNG dimensions/transparency and pixel identity
under the documented translations, original SHA-256, scene/resource references,
animation frame sequence/timing/loop configuration, explicit fallback, unchanged
existing scene nodes and movement statements, protected gameplay/settings files,
Markdown links and Git diff checks. Godot was not run graphically or headlessly;
engine import, playback, appearance and gameplay remain unverified.

Owner manual playtest: run the main scene and move straight south using S and
Down. Confirm all four poses in order at 8 FPS, including repeated stop/start;
assess gait, torso bob, foot sliding, halos and transitions at normal zoom and
0.75/1.5 zoom. Release movement and switch to every other direction, including
south diagonals: each must immediately restore the static sprite. Check collision,
Y-sorting, ground contact, camera follow/zoom, Computer interaction, dialogue and
objectives. Confirm Shift never changes speed. Foot sliding and the wider walking
silhouette require owner visual evaluation; no runtime result is claimed.

### Dave north-facing walk baseline (PR #23, merged)

PR #23 extended the baseline above with straight-north input. The owner reports
it was manually validated and merged; the checks below record agent static
validation of that baseline. Its historical idle behavior is superseded by the
directional idle feature below when merged.
The owner-approved `assets/characters/dave/dave_walk_north.png` is preserved
byte-for-byte: 1983 x 793, 8-bit RGBA, SHA-256
`17d8b3d999450e820ce368a905fbcdd548de62d7894197077430a75bf0aee39c`.
The derived `dave_walk_north_atlas.png` is 2176 x 832 RGBA: four uniform
544 x 832 cells in the original left-to-right order. No pixels are removed,
repainted or resampled; each complete source cell is translated by integer
pixels onto a transparent cell. Source and atlas import sidecars match the
baseline's lossless, no-mipmap, unlimited-size settings with distinct UIDs;
they are prepared as text without running an engine import.

| Frame | Source cell x range | Source anchor (x, y) | Atlas cell anchor |
| --- | --- | --- | --- |
| 1 | [0, 496) | (240, 769) | (272, 784) |
| 2 | [496, 992) | (744, 753) | (272, 784) |
| 3 | [992, 1488) | (1236, 769) | (272, 784) |
| 4 | [1488, 1983) | (1734, 753) | (272, 784) |

Anchors use rounded alpha >= 32 horizontal silhouette centers and exclusive
lower boot edges. `Visual/WalkNorthSprite` uses `centered = false`, `hframes = 4`,
offset `(-272, -784)` and the south sprite's uniform scale `(0.1224, 0.1224)`
and linear filtering. Substantial boot edges map to local y = 0 in every frame;
contact poses are about 91.07 world units tall, close to the existing baseline.
Larger cells preserve all faint margins without clipping or crossing cells.
Inspection found 846 detached nonzero-alpha pixels in total, all alpha <= 7/255;
these and the connected alpha fringe remain unchanged. Halos still need owner
visual assessment. There is no substantial cleanup or reconstruction.

The existing `Visual/AnimationPlayer` gains only `walk_north`: a 0.5-second loop
with discrete `WalkNorthSprite:frame` keys 0, 1, 2, 3 at 0, 0.125, 0.25 and
0.375 seconds (8 FPS at default playback speed 1.0). `walk_south` and `RESET`
remain unchanged. No animation modifies transforms or gameplay.

The presentation helper now selects north for negative y and south for positive
y, each with approximately zero x in the existing input vector. It starts on
entry or direction change and applies frame 0 immediately; sustained input does
not restart playback. Exactly one sprite is shown. Idle, east, west and all
diagonals stop playback and restore the approved static sprite. Directional idle
poses and other directional animations remain deferred. As before, input against
a wall still animates. Movement remains 240 pixels per second without sprinting;
input, collision, Y-sorting, camera, interaction, dialogue and objectives are unchanged.

Validation is static only: source SHA-256, complete source-cell pixel identity
under the documented translations, atlas dimensions and alignment, scene/resource
references and unique import UIDs, animation configuration, direction selection
and fallback review, unchanged south animation and existing scene nodes,
protected gameplay/settings files, Markdown links and Git diff checks. Godot
was not executed graphically or headlessly; import, playback, rendering and
gameplay verification remain for the owner.

Owner manual playtest: use W/Up for north and S/Down for south; check four frames
in order and continuous 8 FPS loops, repeated stop/start and north/south switching.
Confirm idle, east, west and diagonals restore static art. Inspect transparency,
clipping, halos, ground contact and foot sliding at normal zoom and both zoom
bounds. Verify collision, Y-sorting, camera follow/zoom, Computer interactions,
dialogue and objectives. Confirm Shift never changes speed. The south animation
must retain its previously approved appearance.

### Dave directional idle (feature branch, pending merge)

`codex/dave-directional-idle` adds static `Visual/IdleSouthSprite` and
`Visual/IdleNorthSprite` nodes using the exact owner-approved PNGs. No derived
images, pixel edits, resampling or new animations are needed. Original PNGs are
preserved byte-for-byte, including faint alpha fringes and margin pixels.

| Source PNG under `assets/characters/dave/` | Dimensions (RGBA) | SHA-256 |
| --- | --- | --- |
| `dave_idle_south.png` | 1279 x 1230 | `07f8353a3c225c4b547df055cd7e1d1620cdce9f5529eb4b24f399c3a733b99d` |
| `dave_idle_north.png` | 1145 x 1374 | `df2c97edcd7fcc38929b025ffb3a7c753647b086978df8c3db7b23112fc69e53` |

Both sprites use linear filtering and `centered = false`. Exclusive alpha >= 32
bounds are `(285, 106, 986, 1195)` south and `(188, 95, 952, 1301)` north.
South uses uniform scale `0.084` and source-pixel offset `(-635.5, -1195)`;
north uses uniform scale `0.0758` and offset `(-570, -1301)`. These center the
substantial silhouette and align its lower boot edge to Dave's unchanged local
ground origin. Substantial extents are about 58.88 x 91.48 world units south and
57.91 x 91.41 north, matching walking height (about 91.1-91.4) while preserving
approved proportions. Faint alpha extends beyond these bounds and remains intact.
The two import sidecars follow existing lossless, no-mipmap, unlimited-size
settings with distinct UIDs; they were prepared as text without engine import.

`last_facing` is presentation-only, initially `SOUTH`; the scene itself also
shows only south idle on spawn. Straight north/south input updates that value and
selects the existing walk animation. Sustained walking does not restart playback;
direction changes apply the first frame immediately. Zero input stops playback
and displays the remembered static idle. East/west and diagonal movement stop
playback and display the existing static fallback, leaving `last_facing`
unchanged. Stopping unsupported movement therefore returns to the last supported
north/south idle, or south if neither has occurred. Exactly one of the five
sprites is selected per state. `AnimationPlayer` remains the sole animation
controller; both walk animations, their 8 FPS timing and frame order are unchanged.
The input vector, 240 movement speed, `move_and_slide()`, collision, Y-sorting,
camera, interactions, dialogue, objectives and project settings are unchanged.

Validation is static only: PNG decode/integrity and SHA-256 preservation,
alpha/anchor calculations, scene and import references, animation and protected
scene-block comparison, presentation branch review, movement-statement identity,
Markdown links and Git diff checks. Neither Godot nor project code was executed.
Engine import, rendering, transition appearance and gameplay remain unverified;
faint fringes, wider idle silhouettes and ground alignment need owner assessment.

Owner manual playtest: confirm initial south idle, north/south walk-to-idle and
idle-to-walk transitions, repeated release and direct north/south switching.
Check all east/west and diagonal movement uses the original fallback and stopping
it retains the last north/south facing (including before any supported walk).
Confirm unchanged walk frame order and 8 FPS playback. Inspect size, boot contact,
clipping, transparency tearing and halos at normal zoom and 0.75/1.5 zoom. Check
collision, Y-sorting, camera follow/zoom, Computer interaction, dialogue and
objectives. Confirm Shift does not change speed and no new movement mechanics exist.

### Existing environment and gameplay

The camera follows Dave's ground-contact origin independently of `Visual`.
**Mouse wheel up** zooms in; **mouse wheel down** zooms out, centered on Dave.
Zoom starts at 1.0, changes its target by 0.1 per wheel press, and is clamped to
0.75â€“1.5. These are provisional tuning values in `follow_camera.gd`. Each changed
target starts a 0.15-second eased Tween from the current zoom; rapid scrolling
retargets the transition, and repeated input at a bound leaves it running to
completion. No per-frame zoom callback runs when a transition is idle.

The test floor spans x = -2048 to 2048 and y = -1536 to 1536 (4096 Ã— 3072).
Dave spawns at (0, 0), clear of all collision footprints. Four 32-pixel-thick
`StaticBody2D` walls sit just outside the floor; their rectangular shapes meet at
the corners. Three obstacles sit at (-320, -180), (360, 40), and (0, 420), with
160 Ã— 48, 96 Ã— 64, and 160 Ã— 48 collision footprints respectively. All bodies use
the default collision layer/mask, matching Dave. Shapes and colored polygon
visuals are separate children; the console also has a small interaction script.
The Computer HD art pilot below replaces only the console's polygon visuals.

`GroundObjects` enables built-in Y-sorting for Dave and the obstacle roots at the
same default Z index. Each obstacle root is anchored at the bottom center of its
ground footprint, matching Dave's ground-contact origin. Its collision rectangle
extends upward from that anchor, while its taller visual extends above the
footprint to allow overlap when Dave stands behind it. Visual children stay
together as one sorted object. The floor and perimeter are outside this group.
There are no camera limits; floor edges can still become visible near the walls.
Existing movement, camera/zoom, display, rendering, and physics settings are
preserved.

The original ship visual pass used built-in `Polygon2D` and `Line2D` details.
`ShipDeck` covers x = -656 to 656 and y = -448 to 592, leaving the rest of the test
floor open. Sixteen inset panels, muted amber route guides and service markings
frame a clear central walking area. This is a deck section, not a new enclosed
room; the original distant perimeter remains the only boundary collision.
Blue-teal housings, pale metal edges and restrained amber/coral accents form a
temporary palette, not production artwork or a lighting system.

The existing `WestObstacle` depicts Computer, now using the HD pilot described
below instead of its temporary polygon console. `EastObstacle`
depicts a life-support filter unit with a faceted cap, filter window and service
pipe. `SouthObstacle` depicts a storage workbench with cabinet doors, a work mat,
loose cover and tool tray. The console supports temporary dialogue with
inspection fallback; the other fixtures remain noninteractive
placeholders.
These visual identities establish no new narrative state or objectives.
All fixture details remain under each existing `Visual` child, with no individual
Z overrides or nested Y-sorting. Computer's HD visual exceeds its original visual
bounds; the other fixtures retain theirs. The three body
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
The console's point is the center of its existing 160 Ã— 48 footprint: its sides
and corners are reachable within the limit without changing collision geometry.
A solid obstacle between Dave and the target blocks the prompt and interaction.
All proximity, distance and obstruction checks run in the physics callback,
including before fulfilling an interaction request.

When available, a screen-space **E â€” Talk to Computer** prompt appears. Physical
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
Main listens for completion of `computer_opening` to activate `restore_computer`;
DialogueUI remains independent of objectives. No choices, narrative flags, log or
save system are implemented.

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

## Computer HD art pilot (feature branch, pending merge)

`codex/computer-hd-art-pilot` replaces only the artwork beneath
`GroundObjects/WestObstacle/Visual` in `scenes/main/main.tscn`. One `Sprite2D`
displays the approved damaged texture by default. Both source PNGs in
`assets/environment/computer/` are preserved byte-for-byte: 1086 Ã— 724, RGBA,
with transparent backgrounds. Both existing owner-generated `.png.import` sidecars
are retained unchanged in the PR, preserving their texture UIDs, lossless import
settings, disabled mipmaps and no size limit. The owner's local Dave sidecar
change remains untouched outside this commit. The agent ran no imports.
Generated `.godot/` caches stay ignored.

The provisional local sprite scale is `(0.24, 0.24)`, position `(0, 0)`,
`centered = false`, and offset `(-543, -718)` in source pixels. Source point
`(543, 718)` maps to the unchanged body ground/sort origin `(-320, -180)` in
world space. Both states share that transform and linear texture filtering.
At alpha greater than 16, inclusive image bounds are `(51, 15)`â€“`(1023, 711)`
for damaged and `(47, 14)`â€“`(1021, 717)` for repaired. Very faint pixels extend
to `(0, 13)`â€“`(1085, 713)` and `(1, 12)`â€“`(1053, 723)` respectively.
The common anchor sits just below both substantial bases; the six-pixel base
difference remains about 1.44 world units. No per-state alignment correction is
applied. Visible extents are approximately 234 Ã— 169 world units versus Dave's
roughly 93-unit height. The owner has manually confirmed that damaged Computer is
appropriately proportioned relative to Dave. The very minor perceived shift
between artwork states was explicitly accepted for this pilot; no correction is
applied.

The sprite directly references `computer_damaged_pilot.png` and has no attached
script. Temporary keyboard controls, their script and UID, and the scene's script
resource reference have been removed. No Inspector state tooling, input handler
or visual-state controller remains for this pilot. The repaired PNG and its import
metadata remain available for a future narrative-driven repair implementation;
there is no repair gameplay or objective completion path in this PR.

Static checks cover PNG decoding, chunk integrity, alpha bounds, source hashes,
resource paths, the shared transform, and comparison of
all non-Computer-visual scene data against `main`. Collision (160 Ã— 48 at local
`(0, -24)`), interaction point `(0, -24)`, dialogue, Y-sorting, Dave, other
fixtures, existing gameplay scripts and project settings are unchanged. Final
static checks cover complete removal of temporary switching functionality,
damaged texture assignment, preserved asset/sidecar hashes, resource counts and
references, unchanged scene configuration, documentation links and Git diff checks.

The owner reports all eight visual-state playtest checks passed: damaged
proportions relative to Dave, both artwork appearances, switching and visual
continuity, collision and interaction in both states, movement/dialogue/objective/
camera/zoom regressions, and system stability. The minor perceived shift is
accepted. These are owner-reported runtime results from before removal of the
temporary controls. Finalization was validated statically only; the agent did not
run Godot or perform post-removal runtime or graphical verification. Agent
execution remains subject to
[AGENTS.md](AGENTS.md#godot-execution-safety).

## Objectives and first narrative integration (feature branch, pending merge)

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
never activates or completes objectives.

Main connects Dave's existing `DialogueUI.conversation_completed` signal to a
scene-local handler. Only `computer_opening` activates `restore_computer`;
dismissal has no activation connection, and unrelated conversation IDs are ignored.
Repeated completion is harmless: the controller rejects activation unless the
objective is inactive, without emitting another state change. DialogueUI, Dave's
movement controller and the interaction detector have no objective dependency.

The registered objective starts inactive. Its independently editable definition
in `objectives/restore_computer.tres` has title **Restore Computer** and description
**Investigate the damage to Computer and determine what is needed to restore its
systems.** This is provisional opening narrative content. No repair mechanics or
narrative completion path are implemented. The temporary J/K demo adapter, node,
script/UID and resource have been removed; no replacement debug controls exist.

The tracker occupies the top right of its own `CanvasLayer`, using the existing
ship UI palette. It is independent of camera zoom and is laid out above the bottom
dialogue and inspection region at the configured 1280 Ã— 720 viewport. When the
objective activates, only **Show Objective** appears. Clicking it expands the
contextual panel. **Pin** keeps the full panel visible; **Unpin** returns to
collapsed contextual mode. **Hide** conceals the full panel and leaves
**Show Objective** available; clicking it expands in contextual mode again.
With no active objective, neither panel nor button appears, even when pinned.
Presentation preferences remain scene-local; there are no timers or animations.

Validation for this integration is static only: resource references, script UID
sidecars, inactive-state initialization, completion ID guard, dismissal separation,
idempotent activation, scene/signal wiring, tracker transitions, UI anchors,
documentation links, preserved gameplay/settings and Git diff checks. Godot was
not executed; engine loading, runtime behavior, text wrapping and graphical
nonoverlap remain unverified.

Before merging, the owner must manually verify that no tracker appears initially;
Esc/Dismiss before finishing Computer's dialogue leaves it inactive; and E/Finish
on its last entry reveals Show Objective. Expand, Pin, Unpin, Hide and restore the
panel, then repeat the conversation and confirm it neither duplicates the objective
nor resets the chosen tracker presentation. Check the tracker with dialogue and
inspection open, readability and nonoverlap at both zoom bounds, and continued
movement, camera follow, wheel zoom and interaction behavior. Reloading the scene
must reset the objective to inactive. Unrelated conversation IDs and signal counts
require owner runtime verification; their paths were inspected statically.

Add feature directories and GDScript files when they have a concrete purpose.
Track approved source artwork, source-adjacent asset `.import` sidecars (import
settings and stable resource UIDs), and `.gd.uid` files. The `.import/` ignore rule
applies to cache directories, not these sidecar files. Keep generated `.godot/`
data, including its import cache, editor caches, generated thumbnails and temporary
logs out of source control. Preserve existing local data under the retention rules
in [AGENTS.md](AGENTS.md); being untracked does not authorize deletion.
Use feature branches and pull requests;
validate affected scenes and scripts before requesting review.

Keep authoritative documentation in `docs/` and generated evidence out of Git;
the artifact retention and ZIP policies are in [AGENTS.md](AGENTS.md).
Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
review. After an approved merge, separately request
[post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) for that PR number
from a chat attached to a surviving checkout. Cleanup stops when preservation,
attachment or Windows lock safety cannot be verified.
