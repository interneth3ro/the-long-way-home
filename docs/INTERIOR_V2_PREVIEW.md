# Primary interior V2 development previews

PR #47's visual comparison is merged. The owner selected **1.25x** following its
tests 1-6, as recorded in the collision implementation request. This feature
branch adds a separate collision/navigation preview, pending merge and owner
acceptance. The normal main scene still starts in the original interior.
Gameplay spawns, transitions, door opening, Computer restoration, Marvin
discovery, production cutover and legacy retirement remain deferred.

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
the corresponding barrier; there are no Area2D triggers or scene changes here.

Six independent convex floor footprints block Computer's base, Marvin's wreckage,
the port console, port storage, north crate and starboard cabinet. Tall silhouettes,
shadows and small scattered debris do not define their outlines. Cables, papers,
floor grates, lighting and scratches have no bodies. Wreckage can later be removed
independently; no Marvin sprite, discovery or clearing behavior is introduced.
Computer has no interaction script.

These are conservative interpretations of illustrated contact points, especially
the wreckage's irregular lower edge and stacked storage. The owner must assess
alignment and corner feel in the ordered tests below; static inspection does not
establish runtime navigation quality.

The development-only
[`physics_shape_outlines.gd`](../scenes/dev/physics_shape_outlines.gd)
reads enabled CollisionShape2D resources: segment endpoints, convex polygon
points and Dave's circle radius (drawn with 64 samples). Shape-global to
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
Owner Test 2 reported **FAIL**: Dave could stand partly on the port console.
The focused amendment below awaits a Test 2 retest. No acceptance pass is inferred
from static checks; do not advance to Test 3 until the owner confirms Test 2 passes.

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

Resume **Test 2 of 8** in the same F6 collision preview, with C outlines enabled.
Approach the console from the floor and both wall sides: Dave must no longer
stand on its upper surface or enter behind it. Repeat the full perimeter for
gaps/snags. This retest remains pending owner confirmation; no runtime success
is claimed.

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
5. **Permanent equipment:** Check substantial consoles/storage/crate/cabinet
   block movement, while small decorative details do not.
6. **Doors:** Approach maintenance and exterior thresholds naturally. Both
   remain solid and neither changes scenes.
7. **Circulation/debug:** Walk between important areas, press C to inspect
   shape alignment and Dave's feet circle, then toggle repeatedly. Physics must
   remain identical; H only hides/shows the readout.
8. **Production regression:** Stop the preview, run the regular game with F5,
   and verify the original interior, Computer, exterior/maintenance transitions,
   inventory/objectives and factory gameplay remain unchanged.

Future automatic doorway transitions use threshold walking without E. That
approved behavior is deferred; E remains for intentional object interactions.
Collision acceptance provides no evidence that future transitions work.
