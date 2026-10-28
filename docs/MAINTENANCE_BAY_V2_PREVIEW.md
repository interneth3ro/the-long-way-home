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
