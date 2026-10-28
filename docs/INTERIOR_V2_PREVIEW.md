# Primary interior V2 development previews

PR #47's visual comparison is merged. The owner selected **1.25x** following its
tests 1-6, as recorded in the collision implementation request. PR #49's separate
collision/navigation preview is merged; its historical acceptance record below
is preserved. The normal main scene still starts in the original interior.
Gameplay spawns, transitions, door opening, Computer restoration, Marvin
discovery, production cutover and legacy retirement remain deferred.

The current feature branch adds a third, isolated
[automatic-transition harness](INTERIOR_V2_TRANSITIONS.md), pending merge and
owner acceptance. Its development-only wrapper provides arrival spawns and
doorway wiring. The scale/collision previews and V2 scene described below remain
unchanged; their solid doors still do not initiate travel.

## Open and compare (owner-operated)

Follow the [execution safety policy](../AGENTS.md#godot-execution-safety). These
manual owner instructions do not authorize agent engine execution.
Open the project in Godot, open
[`scenes/dev/ship_interior_v2_scale_preview.tscn`](../scenes/dev/ship_interior_v2_scale_preview.tscn),
then run **Current Scene (F6)**. Keep the project's main scene unchanged.
The preview starts at world **1.0x** and camera **1.0x**, using existing Dave and
his existing follow/zoom camera.

| Key | Preview action |
| --- | --- |
| 1 / 2 / 3 | Set the entire environment to 1.0x / 1.25x / 1.5x |
| 4 / 5 / 6 / 7 / 8 | Place Dave near Computer / maintenance doorway / wreckage / exterior hatch / center |
| WASD / arrows | Existing Dave movement, without collision in this harness |
| Mouse wheel | Existing camera zoom, clamped to 0.75x-1.5x |
| H | Hide/show the preview readout for screenshots |

Scale changes preserve Dave's image-space position without changing his size or
camera zoom. Numbered positions are comparison points, not gameplay spawn markers
or verified walkable locations. Dave renders above the room; prop occlusion and
depth sorting are not implemented. Only this instance's body collision and
interaction processing are disabled; its unused dialogue/interaction UI is hidden.
Production Dave files are unchanged. No progression, inventory or transition
controller is instantiated.

The HUD shows world scale and actual camera zoom. Review at camera 1.0x first.
Restart Current Scene to restore exact camera 1.0x, then select the desired world
scale. Scroll to either zoom clamp to reach exactly 0.75x or 1.5x.

## Art alignment, import settings and static evidence

All nine source PNGs from `TLWH_Primary_Interior_Handoff_v1.zip` were verified
against its [unchanged manifest](../assets/environment/ship_interior_v2/manifest.json)
before copying to `assets/environment/ship_interior_v2/`. All are 1536x1024.
Approved pixels are unchanged. The background renders once; wreckage, damaged
Computer, closed maintenance and intentionally transparent closed exterior
overlays render above it in that order. Repaired Computer is a hidden node.
Open-door overlays and the flattened reference remain assets without rendered
nodes. Marvin has no separate sprite or interaction.

In [`ship_interior_v2.tscn`](../scenes/world/ship_interior_v2.tscn), every sprite
shares its default centered origin, position, offset and scale under one
`VisualContent` parent: image pixel (768, 512) maps to local (0, 0). Only that
parent scales; props have no independent adjustments. Linear filtering follows
the existing illustrated Computer-art convention; Dave retains nearest filtering.
Linear sampling can soften details at fractional scales and camera zooms.
Full-canvas coincident layers avoid tile boundaries; actual seams and edges need
owner review. Authored `.import` sidecars request lossless compression, no mipmaps
or resizing, straight alpha and no alpha-border pixel modification. Godot has not
generated or verified these imports; no `.godot` cache is included.

A static System.Drawing source-over composition at native resolution compared
with the flattened reference found 98,444 differing pixels of 1,572,864, with a
maximum absolute RGB channel difference of **1/255**. This is consistent with
alpha-rounding differences; it is not a pixel-identical comparison or a Godot
render. No compensating artwork edits were made. Engine filtering, color and
compositing remain unverified.

Static validation covers source hashes, PNG dimensions/format/integrity,
resource paths, common layer transforms, isolated references and preservation of
existing production files. No Godot import, GDScript engine/type check, headless,
runtime, graphical test or screenshots were performed under the restriction.

## Ordered owner review (one test at a time)

1. Run only the isolated preview and inspect the initial room against
   `approved_initial_composite_REFERENCE.png`. Confirm damaged Computer, closed
   doors and concealed Marvin, with no flattened reference double-rendered.
2. At camera 1.0x, select world 1.0x (1); use 4-8 to compare Dave with Computer,
   doorways and wreckage. Capture a screenshot, optionally hiding the HUD with H.
3. Repeat at world 1.25x (2), keeping the same comparison point and camera 1.0x.
4. Repeat at world 1.5x (3), keeping the same comparison point and camera 1.0x.
5. Compare the preferred candidate at camera 0.75x and 1.5x. Inspect floor detail,
   proportions, perspective, framing, overlay edges and fractional-scale seams.
   No collision clearance or traversal is validated in this slice.
6. Stop the preview, then launch the regular game (F5) and confirm the original
   interior and opening gameplay remain unchanged. These historical comparison
   steps remain available; the later owner decision selected 1.25x.

## Collision/navigation preview (feature branch, pending merge)

Under the same [execution safety policy](../AGENTS.md#godot-execution-safety),
the owner can open
[`ship_interior_v2_collision_preview.tscn`](../scenes/dev/ship_interior_v2_collision_preview.tscn)
and press **F6 (Run Current Scene)**. The project main scene is unchanged.
WASD/arrows and mouse-wheel zoom use the original Dave controller/camera.
**C** toggles actual physics outlines (initially off); **H** toggles the HUD.
No teleports, interactions, progression or transition controller are present.
Dave's body is enabled; only this instance's interaction detector is disabled
and its unused UI hidden. Dave renders above the full-canvas art, as in the
comparison preview; prop occlusion/depth sorting remains deferred.

The V2 instance root is uniformly scaled **1.25x**, covering both unchanged
`VisualContent` and new `CollisionContent`. The source canvas remains 1536x1024,
displayed as 1920x1280 world units. All physics points are authored as
`source_pixel - Vector2(768, 512)`; thus an image point maps to preview position
`(source_pixel - center) * 1.25`. Moving/rotating the V2 root carries art and
physics together. Dave is a sibling at original scale: radius **10** with the
original shape offset `(0, -10)`. His root starts at `(-110, 28.75)`, source
pixel `(680, 535)`; the circle center is source `(680, 527)` and radius is
8 source pixels. Static geometry checks find it clear of all blockers.

### Authored floor geometry

`CollisionContent` contains layer-1/mask-1 StaticBody2D children, matching Dave's
unchanged default layer/mask. The closed, simple perimeter uses 23 SegmentShape2D
edges sharing exact endpoints. It follows a smoothed usable-floor boundary,
ignoring small recesses. The central floor is empty, rather than a filled
perimeter polygon. No alpha-derived collisions are used.

Two edges belong to independently disableable/removable bodies:
`MaintenanceDoorBarrier` at source `(200,535)-(200,410)`, and
`ExteriorDoorBarrier` at `(850,855)-(660,855)`. Short approach alcoves remain
inside these boundaries. A later crossing implementation must explicitly disable
the corresponding barrier. Reusable Area2D doorway additions for the separate
[two-room connection](V2_TWO_ROOM_CONNECTION.md) are disabled here; this preview
still performs no scene changes and keeps its door barriers solid.

Six independent convex floor footprints block Computer's base, Marvin's wreckage,
the port console, port storage, north crate and starboard cabinet. Tall silhouettes,
shadows and small scattered debris do not define their outlines. Cables, papers,
floor grates, lighting and scratches have no bodies. Wreckage can later be removed
independently; no Marvin sprite, discovery or clearing behavior is introduced.
Computer has no interaction script.
An additional independent wall-connected capsule blocks the port container; see
the Test 5 amendments below.

These are conservative interpretations of illustrated contact points, especially
the wreckage's irregular lower edge and stacked storage. The owner must assess
alignment and corner feel in the ordered tests below; static inspection does not
establish runtime navigation quality.

The development-only
[`physics_shape_outlines.gd`](../scenes/dev/physics_shape_outlines.gd)
reads enabled CollisionShape2D resources: segment endpoints, convex polygon
points, circle radius (64 samples) and capsule radius/height (32 segments per
semicircle, joined by the straight sides). Shape-global to
overlay-local transforms include all ancestor transforms. Disabled shapes and
layer-zero bodies are omitted. There is no duplicate outline geometry or
physics/state mutation when toggling. The outline node exists only in this
preview. The original scale-preview files are unchanged; Dave's layer/mask zero
there keeps the new V2 physics inert while its visual-only scale controls remain.

### Static verification and runtime limits

Checks cover all nine manifest SHA-256 hashes, resource dependencies, supported
shape resources, convex/nondegenerate prop polygons, a simple closed perimeter,
shared endpoints, initial radius-10 circle clearance, and central route clearance.
The source-pixel floor route from center `(680,527)` through `(760,650)` to hatch
approach `(760,835)`, plus routes to Computer `(768,325)` and maintenance
`(220,490)`, clears blockers for the circle's 8-source-pixel radius.
These are mathematical checks of authored geometry, not simulated movement.
PNG assets, manifest, original scale-preview files, production Dave/interior,
main scene, project settings and transition code are unchanged.
Changed Markdown links and `git diff --check` are checked.

No Godot/editor/import, headless execution, engine GDScript/type validation,
runtime, graphical tests, performance probes or engine screenshots were performed.
Owner Test 2 previously reported **FAIL** and prompted the console amendment below.
The owner has since progressed to **Test 5 of 8: FAIL**, reporting missing container
collision. The circle added in amendment 2 also failed the owner's retest:
Dave could reach the upper artwork through its rear passage. Resume Test 5
after amendment 3; do not restart already-passed tests.
No runtime success is inferred from agent static checks.

### Port console alignment amendment

The owner's outlined screenshot shows a feet-circle center near source
`(290,338)`, above the old footprint's y=365 rear edge. The old polygon blocked
the lower cabinet but omitted its sloped upper/rear extent, leaving access from
the wall side. This is a local footprint omission, not a 1.25x scale mismatch.

Only `Footprint_PortConsole` changes. Its source-pixel vertices are now
`(240,330), (295,307.5), (345,330), (345,415), (320,435), (270,420), (240,390)`.
The front/lower contact points remain; the rear extends into the illustrated
wall mount. Its rear edge shares part of existing `Segment_Wall01`, and its
left edge shares part of `Segment_Wall23`, closing the former rear pocket.
Those wall resources and every unrelated shape remain unchanged. The extension
stays within the equipment/wall-mount region; the floor approaches east and
south remain clear for Dave's 8-source-pixel-radius circle. Dave's unchanged
`(0,-10)` shape offset puts his ground origin 8 source pixels below its center.

Run the focused text-only check from the repository root:
`python tests/static_port_console_geometry_test.py`. It checks convexity/local
bounds, screenshot/art surface witnesses, continuous attachment to both existing
wall edges, fixed scale/radius and circle clearance along east/south approaches.
It reads scene text without Godot or gameplay execution. The upper-surface and
wall-attachment checks reject the previous polygon. Sampled approach clearance
and geometric contact do not establish engine collision response or corner feel.

The original amendment requested a **Test 2 of 8** retest with C outlines enabled:
Approach the console from the floor and both wall sides: Dave must no longer
stand on its upper surface or enter behind it. Repeat the full perimeter for
gaps/snags. The current review is now Test 5; recheck the corrected console only
as part of the nearby container circulation test.

### Amendment 2: base-only container circle (superseded; Test 5 failed)

The approved background shows a cylinder at about source x=364-398, with the
bottom rim near y=337 and raised lid near y=293. No existing body covered its
floor base; it was omitted from the original six equipment footprints.
The corrected console is separate and unchanged.

Added `CollisionContent/PortContainer` (StaticBody2D, layer 1/mask 1) with a
`Shape` CollisionShape2D using `Footprint_PortContainer` (CircleShape2D).
Source center **(381,320)** maps to local **(-387,-192)**. Radius is **17**
source/local units (34 diameter); at environment scale 1.25x, the preview center
is **(-483.75,-240)** and radius **21.25** world units (42.5 diameter).
The circle approximates the floor base, not the raised lid or cast shadow.
There are no individual shape/visual scaling adjustments.

At this stage the C outline renderer read the actual CircleShape2D and
its body transform; no debug-code change is needed. Walls, six existing polygons,
corrected console, artwork, Dave, camera, production interior and preview entry
points are unchanged.

The original static checks covered the base circle and allowed routes on all
four sides. They did not require upper-art coverage or wall attachment and thus
missed the owner's reported defect. The rear passage was narrow
(18 source pixels between circle and wall, versus Dave's 16-source-pixel diameter).
Static clearance does not establish comfortable movement, visual alignment or
engine response. All nine PNG hashes still match the approved manifest.
Godot was not run.

### Amendment 3: wall-connected container capsule (Test 5 retest pending)

Replaced `Footprint_PortContainer` with a vertical **CapsuleShape2D**, radius
**18**, full height **58** (width **36**) in source/local units. The background's
approximately x=364-398 cylinder, y=282 lid and y=337 bottom rim set the practical
width/front extent; the horizontal wall at y=285 sets the required rear reach.
The resulting bounds are source x=363-399 and y=280-338, including 5 source pixels
past the wall. This covers both the visible upper portion and the physical base.

`CollisionContent/PortContainer` is at local **(-387,-203)**, source **(381,309)**,
with no rotation. Cap centers are source **(381,298)** and **(381,320)**.
The rear cap intersects unchanged `Segment_Wall02` at y=285 along a continuous
chord approximately x=368.55-393.45 (24.9 source pixels wide), closing the rear
route including diagonal passage. No wall, console or unrelated shape was moved.
Layer/mask remain 1/1. At 1.25x, center is **(-483.75,-253.75)** and dimensions
are **45 x 72.5** world units, with radius **22.5**.

The development C renderer now supports CapsuleShape2D: the straight section and
two semicircles come only from `shape.height` and `shape.radius`, then use the
existing collider-global to overlay-local transform. No independent outline
dimensions or collision mutations are introduced.
The owner subsequently reported a GDScript inference error for `cap_offset`.
The renderer now casts the resource to CapsuleShape2D and explicitly declares
that offset as a float. This follow-up is statically reviewed; engine parsing
and rendering still require owner verification.

`python tests/static_port_console_geometry_test.py` retains the four console
checks and updates the three container checks to require a capsule, upper/lower
art coverage, a continuous wall intersection and feet-circle-clear front/side
routes. The old base-only circle fails the coverage and attachment checks.
The rear route is deliberately no longer a valid navigation path. Mathematical
clearance on the west route is tight (minimum 1 source pixel beyond Dave's circle);
comfortable movement and illustrated alignment still require owner assessment.

All nine approved PNG hashes match, prior wall/console/other collision resources
are unchanged, and production gameplay, Dave, scale and camera are unchanged.
No Godot/editor/headless, engine GDScript/type check or runtime test was performed.
Resume **Test 5 of 8**, F6 preview and C outlines: verify Dave cannot pass through,
slip behind or stand on the upper container artwork, inspect comfortable front
and side approaches, and recheck the corrected console. Do not proceed to Test 6
until the owner confirms Test 5 passes.

### Ordered collision acceptance (one test at a time)

After each test, obtain owner confirmation before treating it as passed.

1. **Launch/artwork:** Open the collision preview and F6. Confirm no errors,
   unchanged artwork and correct fixed 1.25x scale.
2. **Perimeter:** Walk the entire asymmetric boundary. Check for escape gaps,
   snagging corners and obvious wall misalignment.
3. **Computer:** Approach from the open floor; confirm the base blocks walking
   through the workstation while its accessible side remains reachable.
4. **Wreckage:** Walk its accessible edge; confirm the floor pile blocks Dave
   and the central route stays open.
5. **Permanent equipment:** Check substantial consoles/storage/crate/cabinet/container
   block movement, while small decorative details do not.
6. **Doors:** Approach maintenance and exterior thresholds naturally. Both
   remain solid and neither changes scenes.
7. **Circulation/debug:** Walk between important areas, press C to inspect
   shape alignment and Dave's feet circle, then toggle repeatedly. Physics must
   remain identical; H only hides/shows the readout.
8. **Production regression:** Stop the preview, run the regular game with F5,
   and verify the original interior, Computer, exterior/maintenance transitions,
   inventory/objectives and factory gameplay remain unchanged.

Automatic doorway transitions use threshold walking without E in the separate
feature-branch [transition harness](INTERIOR_V2_TRANSITIONS.md); production
cutover remains deferred. E remains for intentional object interactions.
Collision acceptance provides no evidence that automatic transitions work.
