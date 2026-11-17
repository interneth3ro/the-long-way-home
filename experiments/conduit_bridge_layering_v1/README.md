# Simple conduit bridge layering experiment v1

Isolated artwork prototype on `codex/conduit-bridge-layering-v1`, pending owner
F6 visual acceptance and merge. Ordinary straight sprites cross by draw order:
the uninterrupted upper housing occludes the perpendicular lower housing.
There is no special bridge texture, junction artwork or connection between routes.

Design reference: [Issue #214, Decisions 102-105](https://github.com/interneth3ro/the-long-way-home/issues/214).
D102-D104 retain a dedicated three-cell bridge and independent perpendicular
routes. This owner-requested experiment tries flat sprite layering to evaluate
the appearance; it does not amend the canonical design or implement placement,
costs, topology, transport, inventory or recovery. D105 excludes transported-item
sprites. Visual acceptance must establish whether this reads as a crossing
rather than a four-way junction at normal gameplay zoom.

## Owner F6 inspection

1. Open [conduit_bridge_layering_v1.tscn](conduit_bridge_layering_v1.tscn) in
   the existing TLWH project and press **F6 / Run Current Scene**. F5 keeps the
   normal application startup scene.
2. Start at **1x** in the normal 1280x720 logical viewport. Compare the left
   dirt panel with the right grass panel. OS/window scaling may change the
   physical screen pixels per world unit.
3. Press **1** for horizontal over vertical, **2** for vertical over horizontal,
   or **3** for extended routes. Each key centers its board and restores 1x.
4. Check that the upper rails remain continuous, the lower route is visible
   on both sides, and the crossing reads as two independent routes. Boards 1
   and 2 have identical geometry and artwork, with the stacking reversed.
5. On board 3, follow the four-phase repetition through the crossing and out
   to the nearby rounded corners. Compare width with the Extractor and Smelter
   artwork beneath each panel; neither machine connects to a route.
6. **Middle-drag** pans. **Mouse wheel** uses the existing exterior camera's
   0.5-1.5x range, 0.1 steps and 0.15-second easing. **Home** restores 1x at
   the current center. Point at a crossing and press **C** to center it at 4x;
   C again returns to 1x. The wheel leaves close-up and resumes gameplay zoom.
7. **F8** stops. F6 restarts at board 1. Provide screenshots identifying board,
   terrain and zoom, then approve or request corrections. A focused pre-merge
   audit follows visual acceptance.

## Boards and three-cell spans

Boards occupy 1280x720 logical units, with origins at y=0, 768 and 1536.
Each has two 640-unit terrain panels and the same machine references. Coordinates
below are panel-local **cell indices**, not world pixels or transport direction.

| Board | Horizontal route | Vertical route | Upper span: approach / crossing / departure |
| --- | --- | --- | --- |
| 1: Horizontal over vertical | (2,10) to (17,10) | (10,5) to (10,15) | (9,10) / (10,10) / (11,10) |
| 2: Vertical over horizontal | Same as board 1 | Same as board 1 | (10,9) / (10,10) / (10,11) |
| 3: Extended, horizontal over vertical | (1,10) to (16,10), turning up to (16,7) | (17,5) to (9,5), turning down to (9,15) | (8,10) / (9,10) / (10,10) |

Every upper route has an explicit `BridgeSpan` node with exactly three ordinary
straight sprites named `Approach`, `Crossing` and `Departure`. Each board's
caption identifies their coordinates. The lower route retains its complete
crossing sprite underneath; no cell is removed, cut, masked or replaced.
The span is 96 world units long and one cell wide. These are presentation nodes,
not a construction or layered-occupancy implementation.

Terrain is at z=0. Each route has an explicit `z_index`: **lower=1, upper=2**.
The span inherits its upper route's z value; there are no Y-sorting, depth or
elevation offsets. Draw order is identical on both terrain materials. Existing
source alpha is preserved with default full-white sprite modulation. No ramps,
supports, artificial shadows, conduit animations or additional lights are added.

All conduit textures are 128x128, displayed at positive **(0.25, 0.25)** scale
with linear mipmap filtering. Centers are `(32*x + 16, 32*y + 16)` and board/panel
translations are multiples of 32. Rotations are quarter turns without mirroring.
The six panels contain **184 conduit sprites: 180 straights and 4 corners**.

## Artwork, phases and references

The four approved connector-free Heavy Industrial v2 **vent** phases are
referenced directly from
[supplied_no_connectors_v1](../conduit_art_v1/supplied_no_connectors_v1/).
Each uninterrupted straight run follows **00 -> 01 -> 02 -> 03 -> repeat** in
its texture's local +X direction. Crossing a lower line does not reset the phase.
Boards 1 and 2 begin at phase 00 at their left/top endpoints. Their upper span
phases are respectively **03/00/01** and **00/01/02**.

Board 3's horizontal main run starts at 00 on the left. Its bridge uses
03/00/01. The horizontal route turns at (16,10) using the approved corner at
0 degrees; the other route turns at (9,5) using it at 180 degrees. Both corner
openings meet **vent phase 02**, retaining the accepted rail orientation.
Corner arms restart phase anchoring, following the
[corner experiment's convention](../conduit_corner_art_v1/README.md#straight-phases-at-the-corner).
The upper route's upward arm starts at 02 beside the corner and rotates 270
degrees. One empty cell separates its endpoint from the other route's top arm.
The lower route's downward arm
also starts at 02; its right-hand arm is rotated 180 degrees and reads
03/00/01/02/03/00/01/02 from right to left toward the corner.

Only the unlit straight family is used to isolate the layering comparison.
The existing cyan-recess correction is available but unused; it adds no needed
crossing distinction here. Existing baked cyan details remain part of the
unchanged source art. No source PNGs, import sidecars or earlier experiments
are edited or copied into this directory, and no new textures are created.

Shared references:

- [Straight experiment](../conduit_art_v1/README.md), merged in
  [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215).
- [Rounded corner experiment](../conduit_corner_art_v1/README.md), merged in
  [PR #216](https://github.com/interneth3ro/the-long-way-home/pull/216).
  Historical pending-merge/acceptance wording in those files is preserved.
- Terrain: existing [earth](../../assets/experiments/terrain_c1/sources/earth.png)
  and [green](../../assets/experiments/terrain_c1/sources/green.png) samples, with
  the same fixed center crop, nominal phase scale 0.9 and linear filtering.
- Existing front-facing Extractor and Smelter texture layers, production
  scales/child offsets and 128x128 four-by-four-cell footprint outlines from
  the corner experiment. No machine scripts or animations are instanced.
- IBM Plex Sans Regular and the existing straight-experiment/gameplay camera
  chain. The only new script, [inspection_camera.gd](inspection_camera.gd),
  adapts the corner experiment's navigation to these three boards.

The PR contains only this scene, its camera script and this README. There is
no production entry point or scene dependency on the experiment. Issue #214,
production code, project settings and the eight owner-preserved untracked
files remain untouched.

## Validation boundary

Static checks cover source PNG identity, no new textures, external resource
paths, scene hierarchy/load steps, cell registration, scale, phase order,
corner joins, one perpendicular overlap per panel, three-cell span membership,
explicit stacking, matching board 1/2 geometry, machine transforms, local
Markdown links and Git diff scope. Results are reported in the draft PR;
routine successful check output is not retained as a separate artifact.

**No Godot editor/game, headless command, import or F6 execution was performed
by the agent.** Static checks do not establish engine loading, mipmap behavior,
crossing readability or artistic acceptance. Those remain for owner F6 review.
The [execution policy](../../AGENTS.md#godot-execution-safety) is unchanged.
