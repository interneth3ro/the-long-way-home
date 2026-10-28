# Maintenance bay V2 development previews

The separate [two-room connection](V2_TWO_ROOM_CONNECTION.md) now supplies a
development-only route to Primary Interior V2, pending merge and owner acceptance.
New room-owned doorway components stay disabled in both previews documented here;
their controls and collision-preview right-exit barrier remain unchanged.

This new isolated visual slice uses the exact owner-approved machine-free room.
It does not replace the production maintenance bay or connect to any scene route.
The owner selected **1.25x** in the subsequent collision implementation request.
The PR #51 visual comparison controls remain available. Existing
primary-interior previews from merged PRs #47, #49 and #50 remain unchanged.
Visual isolation follows PR #47. The new collision slice below reuses PR #49's
outline renderer without PR #50 transition wiring; it is pending merge and owner
hands-on acceptance.

## Owner-operated launch and controls

Follow the [execution policy](../AGENTS.md#godot-execution-safety). These owner
instructions do not authorize agent execution. Open
[`maintenance_bay_v2_scale_preview.tscn`](../scenes/dev/maintenance_bay_v2_scale_preview.tscn)
in Godot and press **F6** (Run Current Scene). Project startup is unchanged.

| Control | Preview behavior |
| --- | --- |
| 1 / 2 / 3 | Uniform room scale 1.0x / 1.25x / 1.5x |
| 4 | Clear floor inside right entrance (initial position) |
| 5 | In front of central repair platform |
| 6 / 7 / 8 | Beside empty Extractor / Smelter / Fabricator foundations |
| 9 | Below reserved top door |
| WASD / arrows | Existing Dave movement |
| Mouse wheel | Existing camera zoom, clamped to 0.75x-1.5x |
| H | Toggle preview HUD |

Dave starts facing inward (left), using his existing facing property. His scene,
sprite scale, movement and camera are unchanged. Restart F6 to restore exact
camera 1.0x, then choose a room scale for like-for-like comparisons. Scale changes
preserve Dave's image-space location and camera zoom. Comparison positions are
preview conveniences, not gameplay spawns or verified walkable positions.

**Walking through artwork and leaving room bounds are expected.** Only this
Dave instance's body shape/layers and interaction processing are disabled; unused
interaction/dialogue UI is hidden. Dave renders above the room without prop
occlusion. No progression, inventory, machine or transition controller is created.
Both doors are background pixels; neither can initiate travel.

## Artwork, design and implementation

Source: `TLWH_Maintenance_Bay_V2_Art_Handoff_v1.zip`. Its unchanged
[manifest](../assets/environment/maintenance_bay_v2/manifest.json) retains the
original ZIP-relative asset path; the verified PNG is stored under the project's
environment convention at
[`maintenance_bay_v2_machine_free_background.png`](../assets/environment/maintenance_bay_v2/maintenance_bay_v2_machine_free_background.png).

- SHA-256: `968d4deca9e8df72bd5abb205a018d11a866b902de0ac0c1440750caa5ef99e1`.
- Native 1536x1024, 8-bit RGB, opaque; no PNG transparency chunk. PNG chunk CRCs
  and decompressed scanline lengths were checked before copying, with unchanged
  bytes. No art substitution, recompression or retouching.
- [`maintenance_bay_v2.tscn`](../scenes/world/maintenance_bay_v2.tscn) retains
  one centered Sprite2D: source pixel (768, 512) maps to local (0, 0). The scene
  has native scale; only its preview instance scales uniformly. No stretching,
  region crop or extra rendered layer is used.
- Illustrated art uses linear filtering, consistent with Primary Interior V2;
  Dave retains nearest filtering. The authored import sidecar requests lossless
  compression, no mipmaps or resizing. Engine import remains unverified.
- Three foundations are empty: Extractor upper-left, Smelter upper-right,
  Fabricator lower-left. The repair platform has no interaction mechanics. Right doorway
  is the eventual primary-interior connection; no arrival or transition contract
  exists. Closed top door is reserved, noninteractive and has no destination.
- Moderate localized damage and current background composition are preserved.
  Emergency/partial -> dim/moody -> operational lighting remains future work,
  gated by story/electrical repairs. This image does not establish completed
  emergency lighting. Future machines and lighting may be independent overlays;
  none are extracted or implemented here.
- Intended apparent usable floor area is about 70-80% of Primary Interior V2.
  It is an owner visual acceptance target, not a measured result or reason to
  stretch pixels. Style consistency, perspective, apparent floor size and final
  scale were visual acceptance targets. The subsequent collision request fixes
  world scale at the selected 1.25x.

## Stationary Fabricator visual (feature branch, pending merge)

Owner launch, subject to the [execution policy](../AGENTS.md#godot-execution-safety):
F6 [the isolated Fabricator preview](../scenes/dev/maintenance_bay_v2_fabricator_preview.tscn).
Its [script](../scenes/dev/maintenance_bay_v2_fabricator_preview.gd) inherits the
collision preview and calls its isolation setup. The room stays at **1.25x**,
with the existing collisions, right-exit barrier, disabled doorways and Dave/camera.
The preview does not instantiate the Extractor, Smelter or PR #54 connection
harness. F5 production, reusable rooms and prior previews remain unchanged.

The [reusable Fabricator visual](../scenes/visuals/fabricator_stationary.tscn)
groups one sprite, its scene-local outline material and a separate contact shadow
under one hideable Node2D. This is stationary shipboard equipment artwork only:
no recovery, inventory mutation, save state, deployment, production, animation,
lighting effects, objective wiring or scene cutover. **No Fabricator collision is
added; Dave walking through it is expected.** Existing room fixtures still collide.
Painted amber lighting remains part of the unchanged source artwork. The owner
reports completion of the initial acceptance scenarios and approves the final
in-engine position below. This records owner feedback, not agent runtime
verification. Final locked-file retests remain pending.

### Source verification and final owner-approved foundation placement

- Owner source: `C:/Users/inter/Downloads/fabricator.png`, copied byte-for-byte to
  [fabricator_stationary.png](../assets/environment/maintenance_bay_v2/machines/fabricator_stationary.png).
  PNG signature, all chunk CRCs and full image decode pass static inspection.
  Native **1326 x 1186**, 8-bit RGBA, noninterlaced. SHA-256:
  `b8639413684ed4ea90068ef9a330087dd4c48b696633b9f5f4a7040262e7ce12`.
  No crop, resampling, recompression, recoloring, alpha cleanup or alternate PNG.
- Alpha: 444,104 fully transparent pixels; 15,300 at alpha 1–31; 2,553 at
  32–127; 1,110,192 at 128–254; 487 fully opaque. All four corners are
  transparent black. Exclusive nonzero bounds `(0,49)`–`(1326,1156)`;
  alpha >=32 bounds `(11,96)`–`(1323,1118)`; alpha >=128 bounds
  `(11,96)`–`(1322,1118)`. Border maximum alpha is 13/255. The main
  8-connected nonzero component contains 1,128,475 pixels; 57 detached pixels
  across 43 other components are all alpha 1/255. Genuine usable transparency
  passes the static handoff gate: no opaque rectangular backdrop is present.
  Faint fringe/specks remain intact for owner review at multiple zoom levels;
  the owner reports initial acceptance complete, while final locked-file
  reproduction remains pending. No agent in-engine edge-quality PASS is claimed.
- The real, unchanged 1536 x 1024 room background has the SHA-256 recorded above.
  Static image inspection places the lower-left mounting pad at approximately
  image **X=210–425, Y=630–845**, below the west cabinet, left of the repair
  platform, and inside the bottom wall. These are provisional visual measurements,
  not a collider definition. Image `(768,512)` maps to room-local `(0,0)`.
- Final owner-approved front-center mounting point: image **`(317,807)`**,
  room-local **`(-451.00,295.00)`**, preview-world **`(-563.75,368.75)`** at
  1.25x. This moves 24 room-local pixels upward from provisional `(-451,319)`.
  The source mounting-base anchor is **`(663,1100)`**, on the lower central
  plinth contact edge, rather than the canvas center. Sprite `centered=false`,
  source offset **`(-663,-1100)`**, uniform scale **`0.16`** (effective preview
  scale 0.20). These values derive from this PNG and the lower-left pad, not
  Extractor/Smelter coordinates. Source scale, offset and anchor remain unchanged;
  position comes from the owner's actual preview acceptance.
- Alpha >=32 maps to image approximately `(212.68,646.36)`–`(422.60,809.88)`,
  size **209.92 x 163.52 room units**, or room-local
  `(-555.32,134.36)`–`(-345.40,297.88)`. Faint nonzero canvas bounds extend
  to image `(210.92,638.84)`–`(423.08,815.96)`. The machine is centered over
  the lower-left pad without covering the central repair platform. These are
  static placement calculations at the owner-approved position; final scene-file
  reproduction still requires focused owner retests.
- Separate shadow: visual-local `(0,-7)`, radial GradientTexture2D 128 x 64,
  scale `(1.5,0.5)` = **192 x 32 room units**; black alpha 0.16 at center,
  0.08 at radius 0.65, zero at edge. It follows the root for movement/removal.
  Preview/root and PreviewRoom Y-sort, with Fabricator and Dave Z=1, follow the
  accepted machine previews. No production sorting changes are introduced.
- Existing [objective shader](../shaders/objective_silhouette.gdshader) is unchanged;
  its supported width hint is 0–20, with quad expansion and UV remapping.
  Scene-local material fixes **width=20.0 source texels; opacity=1.00**,
  amber RGB **`(0.65,0.43,0.19)`**, outline **OFF** by default. Radius is
  3.2 room units / 4 preview-world units at camera zoom 1. The shader samples
  sprite alpha for a silhouette, with out-of-bounds zero sampling; no rectangle
  border or extra highlighted image. `resource_local_to_scene=true` isolates
  material state from other instances and the accepted machines.

### Locked preview controls and HUD

| Key | Fabricator preview behavior |
| --- | --- |
| O | Toggle the fixed amber outline, initially OFF |
| V | Hide/restore machine, shadow and outline together; retain requested outline |
| C / H | Inherited collision-outline/HUD toggles, initially OFF/ON |
| WASD / arrows; wheel | Existing Dave movement; camera zoom |

Temporary I/K/J/L, Shift coarse movement and R reset handlers are removed,
along with their baseline/delta state, position legend and recording line.
Position is authored only in the preview scene; width/color remain fixed in the
scene-local material. No live position or outline-parameter adjustment remains.
No global InputMap bindings, clipboard actions, saved tuning or disk writes are
introduced. Key releases/repeats and Ctrl/Alt/Meta combinations are ignored.

The compact HUD shows installed/removed, requested outline ON/OFF, collision
outlines ON/OFF, the retained key legend and fixed outline values. H hides/restores
it; C/H delegate to the inherited handler then refresh status. O while removed
retains its requested state for V restoration. Dave movement and camera behavior
remain inherited and unchanged.

### Static validation and focused owner retests

Validation is static only: PNG integrity/alpha and source-copy/background hashes,
scene reference/load counts, placement math, fixed shader/material settings,
retained input/HUD and absent tuning checks, existing Python
transition/geometry/connection suites (24 tests passing), protected
tracked-file comparison, local documentation links and `git diff --check`.
No Godot import, GDScript engine/type check, shader compilation, headless run,
graphical launch, gameplay or performance verification is claimed. Extractor
`(-442,-156.00)` and Smelter `(435.00,-159.00)`, their 20.0/1.00 outlines,
PNGs/scenes/shadows/controls, room background/collision, earlier previews,
PR #54 harness, Dave/camera and F5 production are unchanged.

The owner reports the initial Fabricator acceptance scenarios complete and
approved X=-451.00, Y=295.00, width=20.0, opacity=1.00, unchanged amber RGB,
outline initially OFF. This amendment locks those values and removes tuning;
static validation does not establish a new runtime PASS.

Final locked-file retests are **pending, one result at a time**. These owner
instructions do not authorize agent execution:

1. F6 Fabricator preview: owner-approved location, outline OFF, no Godot errors.
2. O ON/OFF: fixed 20.0/1.00 amber silhouette, no clipping or residual halo.
3. V with outline ON/OFF: machine/shadow/outline hide/restore; foundation remains.
4. C/H, movement/camera; former tuning keys no longer move the Fabricator.
5. Check the debugger and targeted regressions warranted by the final diff.

Stop for owner retesting and separate merge approval. The isolated preview
scene/script remain future retirement-audit candidates after V2 production
migration; no existing files are retired here. Do not merge, clean up or begin
the separate production-migration architecture review in this amendment.

## Stationary Smelter visual (feature branch, pending merge)

Owner launch, subject to the execution policy: F6
[the isolated Smelter preview](../scenes/dev/maintenance_bay_v2_smelter_preview.tscn).
Its [script](../scenes/dev/maintenance_bay_v2_smelter_preview.gd) extends the
collision-preview script and calls its isolation setup. It inherits the actual
room at 1.25x, right-exit barrier, disabled doorways, existing Dave/feet/camera,
and C/H controls. It does not instantiate PR #54's transition/progression harness
or the Extractor preview. F5, older previews and the reusable room are unchanged.

The [reusable Smelter visual](../scenes/visuals/smelter_stationary.tscn) contains
one sprite and a separate contact shadow under one hideable Node2D. No machine
collision is added: Dave can walk through the sprite; existing room fixtures
still collide. This is dormant stationary artwork only. The source's painted
orange furnace lighting remains authoritative; no effects, animation, production,
recovery, deployment, progression, persistent state or production cutover is added.
O/V are visual simulations. The owner reports all nine initial acceptance tests
PASS and approved the locked values below through the actual Godot preview.
This records owner feedback, not agent runtime verification. Final locked-file
retests remain pending before merge approval.

### Source and final owner-approved foundation placement

- Provenance: owner attachment `C:\Users\inter\Downloads\smelter.png`, copied
  byte-for-byte to
  [smelter_stationary.png](../assets/environment/maintenance_bay_v2/machines/smelter_stationary.png).
  No crop, retouching, alpha cleanup, substitution or recompression.
- PNG: 1536 x 1024, 8-bit RGBA. SHA-256:
  `bf11742f8ca6fecc08ddf4a7a4b18b5a3fce1a57d4508524359dcd6d73a0f54d`.
  Fully transparent: 774,069 pixels; alpha 1–31: 18,237; 32–127: 2,791;
  128–254: 777,767; fully opaque: zero. Maximum alpha is 254/255.
  Exclusive nonzero bounds `(0,17)`–`(1528,1024)`; alpha >=32 bounds
  `(260,32)`–`(1335,944)`; alpha >=128 bounds `(260,32)`–`(1334,944)`.
  There are 1,618 detached nonzero-alpha pixels outside the main 8-connected
  component, all alpha <=2/255. Canvas-edge maximum alpha: top 0, bottom 1,
  left 1, right 0. Faint specks/fringe remain unchanged. Genuine background
  transparency passed the static asset gate; the owner reports the initial
  alpha/shadow acceptance test PASS. Final locked-file reproduction is pending.
- Background remains native 1536 x 1024 and byte-identical with the SHA-256
  recorded above. Image center `(768,512)` maps to room-local `(0,0)`.
  The owner-approved front-center mounting point is now locked at
  **image `(1203,353)`**, room-local **`(435.00,-159.00)`**, scaled preview world
  **`(543.75,-198.75)`**. These values supersede provisional `(424,-139)`.
  The gridded pad sits right of the raised side housing, under ventilation
  artwork and left of the east cabinets. This base anchor adds no collider/spawn.
- Sprite: `centered=false`, source-pixel offset **`(-800,-944)`**, uniform
  scale **`0.18`**. Source `(800,944)` maps to the visual root at the base's
  lower contact edge. Alpha >=32 yields room bounds approximately
  `(337.8,-323.16)`–`(531.3,-159)`, image `(1105.8,188.84)`–`(1299.3,353)`,
  or 193.5 x 164.16 native room pixels. Multiply room coordinates by 1.25 for
  preview world bounds. Source texels scale to 0.225 world units; camera zoom
  further changes screen size. Placement comes from the owner's live tuning;
  no Extractor transforms were reused. Scale and offset are unchanged.
- Contact shadow: separate Sprite2D at visual-local `(0,-8)`, radial gradient
  texture 128 x 64, scale `(1.45,0.5)` = 185.6 x 32 room units. Black alpha
  0.16 at center, 0.08 at radius 0.65, zero at edge. It moves and hides with
  the machine and adds no collision. Sorting follows the Extractor pattern:
  preview/root and PreviewRoom Y-sort, machine and Dave Z=1.
- Outline reuses the unchanged
  [objective silhouette shader](../shaders/objective_silhouette.gdshader).
  Locked width **20.0 source texels**, opacity **1.00**, amber RGB
  **`(0.65,0.43,0.19)`**, outline **OFF**, machine **installed**.
  The shader's supported hint range remains **0–20**. No shader edit is needed.
  At 20 texels the radius is 3.6 room units / 4.5 preview-world units.
  `resource_local_to_scene=true` isolates each Smelter ShaderMaterial instance;
  only that instance receives outline-toggle updates. Extractor's approved position,
  material values and behavior remain unchanged.

### Locked preview controls and HUD

| Key | Action in this preview only |
| --- | --- |
| O | Toggle requested objective outline, initially OFF |
| V | Hide/show sprite, shadow and outline together; requested outline retained |
| C / H | Inherited collision-outline/HUD toggles, initially OFF/ON |
| WASD / arrows; wheel | Existing movement; camera zoom |

Temporary I/K/J/L (including Shift), U/P, brackets and R tuning handlers are
removed, along with tuning baselines, deltas, reset logic, tuning legend and
recording line. Position and outline width/color are authored in the scenes;
only outline-enabled state changes through the instance-local material at runtime.
No global InputMap bindings, clipboard, saved settings or additional controls
are introduced. Key releases/repeats and Ctrl/Alt/Meta combinations are ignored.

The development-only HUD shows installed/removed, requested outline ON/OFF,
collision outlines ON/OFF and the retained controls. H hides/restores it. O while
removed retains the requested state for V restoration. C/H refresh the status
after the inherited handler. The preview scene/script remain future
retirement-audit candidates; reusable scene/art remain.

### Validation and focused owner retests

The owner reports **9/9 initial acceptance tests PASS** in the final-lock prompt,
including placement, alpha/shadow, tuning, O/V/C/H, prior previews and production.
The owner selected X=435.00, Y=-159.00, width=20.0, opacity=1.00, unchanged amber
RGB (0.65,0.43,0.19), initial outline OFF. This amendment locks those values and
removes temporary tuning; it does not infer a new runtime PASS.

Amendment validation is static only: exact scene position/material values,
unchanged shader range, retained O/V/C/H code paths, absent temporary handlers
and HUD text, scene/resource references/load counts, protected-file and image
hashes, placement math, local documentation links and Git whitespace. The 24
existing Python static transition/geometry/connection tests pass. Original PNG
integrity and alpha analysis above were performed during the initial slice.
No Godot import, GDScript engine/type check, shader compilation, headless execution,
graphical launch, gameplay or performance verification was performed by the agent.
The reusable Smelter scene, PNG, shadow, Extractor, background/collision, prior
previews, PR #54 harness, Dave/camera and F5 production remain unchanged.

Final locked-file retests are **pending, one result at a time**. These owner
instructions do not authorize agent execution:

1. F6 the Smelter preview: approved tuned position and outline initially OFF.
2. O shows the approved amber silhouette width/intensity; O again removes it.
3. V with outline ON and OFF hides/restores machine, shadow and outline together;
   the original foundation stays intact.
4. C/H and movement/camera still work; former tuning keys no longer adjust values.
5. Check debugger errors and only the targeted regressions warranted by the diff.

Stop for owner verification. Do not merge or perform cleanup. Owner merge
approval remains a separate decision; any later cleanup must be explicitly
requested through the dedicated maintenance conversation under repository policy.

## Stationary Extractor visual (feature branch, pending merge)

Owner launch: F6 [the Extractor preview](../scenes/dev/maintenance_bay_v2_extractor_preview.tscn)
under the execution policy. It inherits the existing collision preview: actual
room, 1.25x transform, right-exit barrier, disabled doorways, Dave, feet collider
and camera. The [derived script](../scenes/dev/maintenance_bay_v2_extractor_preview.gd)
calls the existing isolation setup. O toggles objective outline (default OFF);
V hides/restores machine, shadow and outline together (default installed).
The HUD reports visibility, requested outline state and collision outlines.
O also updates the requested state while removed; V restores that state.
C/H retain collision outlines/HUD, WASD/arrows move and wheel zooms. No global
bindings change; O/V have no existing binding conflict.

### Final owner-approved values

The owner selected these authoritative values in the actual Godot live-tuning
preview and approved them in the finalization amendment. They are now locked:
room-local position `(-442, -156.00)`, outline width `20.0` source texels,
opacity `1.00`, unchanged amber RGB `(0.65, 0.43, 0.19)`. Outline starts OFF.
These supersede all provisional values and recording examples. Temporary I/K,
Shift variants, U/P, J/L and R handlers, runtime tuning state, reset logic and
copy-values HUD are removed. No live adjustment or persistence remains.
The compact HUD shows installed/removed, outline ON/OFF and collision outlines;
O/V/C/H, movement and camera controls remain. H restores current status, and
O changes the requested outline state while V hides the visual group.

Width 20 source texels equals 3.2 room units / 4 preview-world units, not 20
world pixels. Shader hint remains 0–20 with no smaller clamp; quad expansion,
UV remapping and out-of-bounds zero sampling all use the same width. Rendering
algorithm and shader fallback defaults are unchanged; the scene-local material
explicitly supplies the approved width/color. Final locked-file appearance and
clipping still require owner retest; static inspection is not engine validation.

The [reusable visual](../scenes/visuals/extractor_stationary.tscn) contains only
presentation nodes and a scene-local material. No controls, machine collision,
recovery, objectives, inventory, deployment, animation or production logic is
added. The approved flat pad stays walkable: Dave can pass through the installed
visual. This is a limitation of preserving collision in this visual-only slice.
Preview-only Y sorting puts Dave and machine at their ground anchors on Z 1;
the unchanged room stays on Z 0. Occlusion requires owner review. No new
architectural overlay is indicated by static placement. Existing previews,
PR #54 harness, transition infrastructure and F5 production files are unchanged.

### Provenance and placement

- Owner source: `C:/Users/inter/Downloads/TLWH_Extractor_Standalone_Transparent.png`,
  copied byte-for-byte to [the asset](../assets/environment/maintenance_bay_v2/machines/extractor_stationary.png).
  SHA-256: `1640723731cb25a224ac797b1c0b5006ea82895507bba39e41e61f62e5abc9bb`.
- Decoded 1319 x 1186 RGBA, alpha 0–255: 563,758 transparent, 1,000,447
  partial-alpha, 129 opaque pixels. Alpha > 16 exclusive bounds are
  `(113, 11)`–`(1227, 1127)`; nonzero bounds `(0, 8)`–`(1311, 1186)`.
  Alpha-1 residuals touch the border. Inspection shows colored edge fringe
  and faint residual transparency; no solid rectangular background. Bytes are
  preserved, with no optimized derivative. Initial halo review passed per the
  owner's amendment report; no agent graphical verification was performed.
- The immutable 1536 x 1024 background hash documented above matches before
  and after implementation. No background or existing import metadata changes.
- Actual pad rim is approximately image x 230–424, y 220–390, measured visually
  from the approved background, not old concept labels. Chosen front-center
  final anchor: image `(326, 356)`, room local `(-442, -156.00)` after
  subtracting the centered image origin `(768, 512)`, preview world
  `(-552.5, -195)` at 1.25x. This is the owner-selected rearward placement.
- Artwork base anchor `(669, 1108)` maps to that location with uncentered sprite
  offset `(-669, -1108)` and uniform scale `0.16` (effective preview scale `0.20`).
  Alpha > 16 bounds map to room-image `(237.04, 180.48)`–`(415.28, 359.04)`,
  size 178.24 x 178.56 room units. Body overhangs the rear rim about 40 units.
  Right edge stays left of raised side housing x 432–476;
  left edge stays right of west cabinet, which reaches about x 202. Faint-alpha
  canvas extends further. The owner chose this fit during live tuning; final
  scene-file reproduction awaits the focused retests below.
- Separate contact-shadow Sprite2D: local `(0, -7)`, radial GradientTexture2D
  128 x 64, scale `(1.4, 0.55)`, extent 179.2 x 35.2 room units. Black alpha
  0.18 at center, 0.10 at radius 0.65, zero at edge; transform, visibility and
  gradient are independently editable. Parent visibility hides all components.
- [Reusable shader](../shaders/objective_silhouette.gdshader): eight radial alpha
  samples; soft threshold 0.08–0.45 ignores faint specks. Locked scene-local width
  20 source texels = 3.2 room units = 4 preview-world units at camera zoom 1.
  Muted amber `(0.65, 0.43, 0.19, 1.00)`, disabled by default. Reusable shader
  rendering, fallback defaults and editor width hint 0–20 remain unchanged.
  Expanded quad and UV remapping
  with zero sampling outside bounds accommodate edge-touching silhouettes.
  Original RGBA composites over the outline without permanent tint. Linear
  filtering; no glow, pulse, animation or per-frame CPU outline work. Locked width
  and color reside in the scene-local material; status updates only on input.

### Validation and sequential owner acceptance

Agent checks are static only: image decode/hash identity, scene references/load
counts, coordinate math, protected-file preservation, Markdown links and Git
whitespace. No Godot import, shader compilation, GDScript engine/type check,
headless, graphical, gameplay or performance verification was performed. No owner
PASS is inferred. New development-only preview scene/script are retirement-audit
candidates after production migration; reusable visual/art/shader remain.

The 24 existing static automatic-transition, port-console geometry and V2
connection checks pass. The connection suite's preservation check now enumerates
baseline preview files from `origin/main`, retaining byte/text comparison of old
previews while allowing later isolated previews to add files. Resource/load-count,
hash, placement-math, local-link and whitespace checks also pass. These results
provide no engine or visual acceptance.

The owner reports all nine initial tests below PASS, with no failures, in the
PR #55 polish amendment. This records owner feedback, not agent runtime checks.
The owner subsequently completed live tuning and approved the final values
above. This records the owner's outcome, not agent runtime verification. Final
locked-file retests remain pending, **one result at a time**, before merge approval:

1. F6 the Extractor preview: approved rearward position and outline initially OFF.
2. O shows the approved stronger amber silhouette, without clipping or rectangular
   artifacts; O again removes it completely.
3. V with outline ON and OFF hides/restores machine, shadow and outline together;
   unchanged foundation remains intact.
4. C/H still work and movement/camera remain normal. Former tuning keys no longer
   adjust position, width or opacity.
5. Check debugger errors and only the targeted regressions warranted by this diff.
   Return for owner merge approval after retests pass; no automatic merge.

Initial nine-test acceptance plan (owner-reported PASS before polish):

1. F6 the new preview in Godot 4.7: approved bay at 1.25x, machine installed,
   outline OFF, existing Dave/camera, no errors.
2. Check scale, perspective and base anchor against actual pad and approved
   concept; reject unacceptable overlap with fixtures or walkable approaches.
3. Check normal transparency, colored edge fringe and subtle shadow at camera
   zoom 1.0x, 0.75x and 1.5x; no checkerboard or unwanted outline.
4. O enables a thin soft amber silhouette, without rectangle, clipping or bloom.
5. O disables it completely; repeat while standing/moving and check HUD state.
6. Walk around the pad with C: collision unchanged. Assess sorting; walking
   through the machine is expected in this visual-only preview.
7. V hides/restores machine, shadow and outline together, revealing intact pad.
   Test O while removed, then V. HUD labels removal as visual simulation.
8. Separately regress original bay visual/collision previews and PR #54 harness.
9. F5 production smoke test: original rooms, interactions, progression, all three
   machine systems and saves unaffected.

Screenshot comparison plan (owner-operated): after placement review, hold Dave,
camera and zoom fixed; capture OFF, O/ON, restored OFF and V/removed. Compare
anchor, silhouette width, shadow, fringe and revealed pad. Inspect zoom extremes,
then return to 1.0x for like-for-like comparisons. Retain only selected meaningful
evidence in ignored `artifacts/screenshots/`. Agent captured no engine screenshots.

## Isolated collision preview (feature branch, pending merge)

Subject to the execution policy, open
[`maintenance_bay_v2_collision_preview.tscn`](../scenes/dev/maintenance_bay_v2_collision_preview.tscn)
and press **F6**. Existing Dave movement, wheel camera zoom and feet collision
remain active. **C** toggles resource-derived outlines, initially off; **H** toggles
the HUD. These keys are handled only by this preview, without InputMap changes.
Stop the running scene, open the original scale preview and press F6 to return
to its comparison controls. No in-game scene switching is added.

`PreviewRoom` applies uniform 1.25x to the native room and its separate temporary
right-exit barrier. Dave is unscaled and starts facing left at source-image
(1270, 565). His radius-10 feet circle is centered 10 world units above that
anchor, equivalent to source-image center (1270, 557) and radius 8 at this scale.
Only this instance's interaction processing/UI is disabled; no progression or
transition controller is instantiated. The visual preview's existing zero
collision layers/mask keep it traversable despite the shared room gaining shapes.

The room's `StaticCollision` contains five layer-1/mask-1 StaticBody2D categories:

- `Perimeter`: joined segments following a simplified asymmetric floor boundary.
- `DoorwayBoundaries`: solid reserved upper door. The right doorway stays open
  in the reusable room; its closing segment belongs exclusively to the preview.
- `RepairPlatform`: one convex floor-body footprint, excluding elevated clamps
  and the full illustrated silhouette. No workstation positions are chosen.
- `MachineFoundations`: raised Extractor/Smelter side housings and Fabricator
  side cabinets only. The three flat gridded pads remain traversable; no machine
  actors or future removable-machine footprints are included.
- `EnvironmentalObstacles`: substantial west/east cabinets, lower-west mounting
  block, north tanks and southeast floor equipment. Small debris, loose floor
  plates, markings, cables and elevated details have no independent collision.

Geometry is authored relative to image center (768, 512), with no background
transform or asset changes. The largest southeast footprint simplifies contiguous
equipment into one convex obstacle; fine decorative gaps are intentionally
obstructed. Owner review must assess the inferred floor contact edges, especially
the raised foundation housings and southeast equipment. No design conflict was
identified; perspective-dependent geometry still requires hands-on judgment.

Static checks on the original slice passed: scene resource paths/load counts, direct
physics-body ownership of all shapes, unique script UID, 12 convex footprints,
and exact perimeter/barrier endpoint continuity. A conservative 8-source-pixel
grid with 12-pixel obstacle clearance connected the entry to all three pad centers
and the four accessible platform sides (8,785 reachable samples, none at image
edges). This checks geometry only, not Godot physics or runtime navigation. Spawn
feet clearance is approximately 106.5 source pixels versus the required radius 8.

### Test 4 platform amendment (owner-reported retest PASS)

The owner's Test 4 screenshot showed Dave standing on the upper metal rim:
the original collision edge at source-image Y=430 lay inside that rim. Native
artwork inspection places the broad upper rim near Y=415. Only the two upper
`MainFloorBody` vertices move from room-local `(-223, -82)` / `(132, -82)` to
`(-223, -100)` / `(132, -100)`, placing the edge at image Y=412, just outside
the rim. This is 18 source pixels outward (22.5 world units at 1.25x). Dave's
unchanged feet-circle offset and radius put his lower contact/anchor at that
edge when approaching from above. The subsequent Test 5 amendment request reports
that the owner passed the Test 4 retest. In the Test 4 amendment, the other six
vertices, all other collision resources and all preview files were unchanged.
Static convexity, resource/ownership and scoped-diff checks passed;
the earlier grid sample count above describes the original geometry only.

### Test 5 prop amendment (pending owner retest)

The three supplied owner screenshots were inspected against native artwork.
They identify these `CollisionShape2D` nodes under `StaticCollision` in the room;
each uses the identically named `ConvexPolygonShape2D` resource:

| Screenshot | Category / node | Correction |
| --- | --- | --- |
| `maintenance bay collision 1.png` | `EnvironmentalObstacles/WestUpperCabinet` | Extend the upper edge to the solid stacked cabinet casing, closing the false standing area against the wall; trim the bottom to its metal base rather than the cable/shadow below. |
| `maintenance bay collision 2.png` | `EnvironmentalObstacles/WestLowerMountingBlock` | Move the upper edge to the twin permanent mounting rails; tighten the lower corners around their base, excluding the conduit below. |
| `maintenance bay collision 3.png` | `MachineFoundations/SmelterRaisedSideHousing` | Level the upper edge with the solid side housing's top/base extent and tighten the lower mounting corners; retain traversable flat pad. |

Exact vertex changes, in **room-local coordinates**, in polygon order:

```text
WestUpperCabinet
before: (-628,-222), (-573,-222), (-566,-162), (-588,-137), (-628,-157)
after:  (-628,-300), (-574,-300), (-566,-164), (-584,-152), (-628,-162)

WestLowerMountingBlock
before: (-620,188), (-573,188), (-573,258), (-608,273), (-620,258)
after:  (-620,160), (-574,160), (-574,252), (-588,266), (-620,258)

SmelterRaisedSideHousing
before: (277,-227), (327,-242), (342,-192), (312,-162), (277,-184)
after:  (280,-263), (328,-263), (342,-192), (312,-168), (275,-185)
```

Only those three resources change; each remains a single five-point convex
footprint. The cabinet's rear cap meets the existing wall boundary. Narrow gaps
beside neighboring fixtures are not intended routes; the room-facing approaches
and flat installation pads remain accessible in static geometry. No overhead
arms, loose cables or cast shadows are added as obstacles. The accepted Test 4
platform, all other shapes, ownership, layers and preview/production files remain
unchanged. The original PNG hash and existing local import-sidecar bytes match
their pre-amendment values; the sidecar is excluded from the commit.

Static checks passed: all 12 polygons strictly convex/nondegenerate, no target
polygon overlaps another prop polygon, exact perimeter/preview-barrier endpoint
continuity, resource paths/load counts and shape ownership. A conservative 4-pixel
source-coordinate grid with greater than 10-pixel obstacle clearance (feet radius
8 at 1.25x, plus edge-sampling margin) has **35,193 connected clear floor samples
and zero detached clear samples**. Entry connects to all three pad centers, all
four platform sides and the corrected props' room-facing approaches. This is
geometric evidence, not a physics, visual, snagging or runtime acceptance test.
Only the three scene resource lines and this existing guide changed.

### Collision owner acceptance — Test 5 retest pending

The Test 5 amendment request reports **Tests 1–3 PASS**, **Test 4 retest PASS**,
and **Test 5 FAIL** for the three pictured props. Tests 6–9 remain paused. Resume
with **Test 5 only**: inspect all three corrected props with C outlines and walk
around their neighboring fixtures and pad approaches. Continue to Tests 6–9
sequentially only after the owner confirms Test 5 passes. No new owner PASS or
agent runtime acceptance is claimed; PR merge readiness remains unestablished.

Run **one test at a time**, recording PASS/FAIL and optional observations before
continuing. These owner instructions do not authorize agent execution.

1. F6 the collision preview: confirm exact artwork, Dave/camera and 1.25x scale.
2. Walk the perimeter: check solid floor boundaries, leaks and corner snagging.
3. Check the temporary right-exit barrier and fully solid reserved upper door.
4. Circle accessible platform sides and assess its floor-body footprint.
5. Visit Extractor, Smelter and Fabricator installations: flat pads walkable,
   raised housings/cabinets solid.
6. Compare substantial obstacles with traversable small debris and decorations.
7. Repeat entry/platform/installation routes: comfortable movement, no trapping.
8. Toggle C outlines on/off and H HUD; confirm feet, permanent shapes and preview
   barrier outlines align. Debug controls remain confined to this preview.
9. Stop and F6 the original visual preview; check its scale/position controls and
   walk-through behavior. Separately check the original production game/routes.

## Verification and sequential owner acceptance

Agent validation is **static only**: source hash/PNG integrity, scene/resource
paths and load counts, transforms, isolation, unchanged protected production
files, Markdown links and Git whitespace checks. No Godot editor/import, headless,
engine GDScript/type check, runtime, graphical tests, screenshots or performance
probes were performed. Static inspection cannot establish visual acceptance.

Run and report **one test at a time**, waiting for confirmation before advancing.
The following original visual-review plan is retained from PR #51 for reference;
the later collision request records the approved 1.25x selection without supplying
individual test results. No new owner test pass is recorded here.

1. **Launch and art fidelity:** F6 the new preview. Confirm no errors, exact
   approved machine-free room, right doorway, closed reserved top door, no
   machines and visible Dave on clear floor near the entry, facing left.
2. **1.0x:** Press 1 at camera 1.0x. Use 4-9 to inspect Dave versus repair
   platform, each foundation, right doorway, top door and camera framing.
3. **1.25x:** Press 2; repeat the same points/camera zoom and compare with the
   actual Primary Interior V2 preview. Assess apparent usable floor area.
4. **1.5x:** Press 3; repeat identical comparisons for proportions and clarity.
5. **Camera and style:** Inspect wheel zoom extremes (0.75x and 1.5x), filtering,
   seams, edge detail and style against the approved primary interior. Select a
   preferred bay scale only after review; no collision approval is implied.
6. **Visual navigation:** Move freely; check scale/position/HUD controls and
   absence of interactions or travel. Walking through all artwork is expected.
7. **Production regression:** Stop preview, F5 normal game. Confirm original
   maintenance bay/interior, interactions, factory progression and travel.

The original visual preview includes no navigation collision. The separate slice
above adds static collision and isolated navigation only; production cutover,
machine implementation, doorway triggers, reciprocal gameplay spawns, repair
interaction and legacy retirement remain excluded.
