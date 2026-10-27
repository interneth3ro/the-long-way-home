# Primary interior V2 visual scale preview

Feature branch implementation, pending merge and owner visual acceptance. The
normal main scene still starts in the original interior. No final scale is chosen.
Collision, gameplay spawns, door opening, Computer restoration, Marvin discovery,
production cutover and legacy retirement remain deferred.

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
   interior and opening gameplay remain unchanged. Report a preferred scale for
   a later owner decision; no selection is committed by this preview.
