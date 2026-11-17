# Conduit adapter artwork experiment v1 — shared coupling v2

Isolated artwork experiment on `codex/conduit-adapter-art-v1`, pending owner F6
visual review and merge. The owner authorized creating this directory and a new
draft PR after the original adapter attempt stopped at preflight without creating
an experiment. The directory retains the requested v1 name; its candidate uses
the **shared-coupling v2** composition.

The owner's November 17, 2026 **A4, Option B** artwork amendment combines one
transparent coupling overlay with the approved connector-free straight sprites.
Standard uses one 32x32 cell; Extended uses two consecutive cells and the same
coupling. Standard and Extended remain distinct equipment in the approved design.
This scene implements presentation samples only, with no gameplay equipment,
ports, construction, inventory, transfer, recovery, faults, costs or topology.

[Issue #214](https://github.com/interneth3ro/the-long-way-home/issues/214) remains
unchanged. D11/D12/D16, D26-D28 and D57/D58 supply the machine/adapter design
context; exact port cells remain provisional. D105 excludes transported-item
sprites. The owner-approved artistic direction does not establish acceptance of
this overlay's geometry or final in-game appearance. No production assets or F5
entry point are changed.

## Owner F6 inspection

1. Open [conduit_adapter_art_v1.tscn](conduit_adapter_art_v1.tscn) in TLWH and
   press **F6 / Run Current Scene**. Start at normal gameplay **1x** in the
   existing 1280x720 logical viewport. F5 still opens the application normally.
2. Use **1-5** to center a board and restore 1x. Each board repeats its samples on
   **dirt at left and grass at right**.
3. **Middle-drag** pans. **Mouse wheel** uses the established 0.5-1.5x exterior
   range, 0.1 steps and 0.15-second easing. **Home** restores 1x at the current
   center. Point at a coupling/join and press **C** for a clearly separate **4x
   inspection close-up**; C again returns to 1x. The wheel leaves close-up and
   resumes gameplay zoom.
4. On **board 3**, compare A (underlying line only) with B (Extended overlay).
   Confirm the upper housing is continuous and the lower line is visible on both
   sides. It must read as two independent routes, not a four-way junction.
5. Inspect all rotations, joins, contact/overlap with machine silhouettes, small
   cyan accents and dirt/grass contrast. Return to 1x before judging readability.
6. **F8** stops; **F6 again** restarts at board 1. Supply screenshots identifying
   board, terrain and zoom, with acceptance or requested corrections. Crossing
   acceptance is mandatory; static checks cannot substitute for this review.

These are owner-run instructions. The agent did not launch Godot, perform imports,
load scenes in the engine or run a headless/native/behavioral recipe. See the
[execution policy](../../AGENTS.md#godot-execution-safety).

## Comparison boards

Board origins are y=0, 768, 1536, 2304 and 3072. Panels are 640 units wide, with
terrain from y=80 to y=680 below the fixed header and above the fixed controls.

| Key | Board | Samples per terrain |
| --- | --- | --- |
| 1 | Standard | Smelter east/south and Extractor west/north; one housing cell plus two continuation cells per sample |
| 2 | Extended | The same four machine/orientation combinations; two housing cells plus two continuation cells |
| 3 | Mandatory crossing | Smelter and intact six-cell north-south line in A and B; B adds a two-cell east-west adapter and three continuation cells |
| 4 | Rotation/contact stress | Four Standard orientations around a Smelter and four Extended orientations around an Extractor; one continuation cell per sample |
| 5 | Original candidates versus v2 | Proportional v1 Standard/Extended references beside full-width v2 assemblies, with two continuation cells each |

On board 4, four placements around one silhouette are **independent visual
samples**, not a proposal for four simultaneously permitted adapters. East,
south, west and north name the outward artwork orientation, not transfer direction.
Faint outlines show the 4x4 machine footprint and the one-/two-cell adapter span.
The separate continuation sprites are not part of that adapter footprint.

## Shared coupling and registration

The supplied [coupling PNG](shared_coupling_overlay_v2_candidate_128.png) is
**128x128, 8-bit RGBA**, 19,689 bytes. It is copied byte for byte, with no cropping,
resampling, redrawing, recoloring or alpha change. SHA-256:

```text
14af063fe0b1949069ab041e8aa6d40350cf8919614f2c6ffa610246bfed94e1
```

Its nonzero-alpha bounds are **[6, 2, 73, 125)** in source pixels: 67x123 pixels.
Alpha ranges from 0 to 255. The entire **x=73-127** strip is fully transparent.
At uniform scale **(0.25, 0.25)**, the visible overlay spans 16.75x30.75 world
units and stays inside the first 32x32 cell in every quarter-turn orientation.
It leaves 13.75 world units clear before the outward edge of that cell.

An unrotated assembly extends east. Its first cell center is the parent origin;
the housing and coupling are both centered sprites at local (0,0), scale 0.25.
The coupling's visible bounds relative to that center are
**[-14.5, -15.5, 2.25, 15.25)**. There is no compensating sprite offset, mirroring,
negative scale or machine-specific docking geometry. Extended's second ordinary
housing is at local **(32,0)**. Rotate the whole placement by 0/90/180/270 degrees
for east/south/west/north; housing, coupling and continuation stay aligned.

Cell centers are `(32*x + 16, 32*y + 16)`. Machine footprints begin on grid
boundaries and remain 128x128. Given machine top-left cell `(x,y)`, this experiment
uses the following **provisional visual samples**, without installing logical ports:

| Outward side | First adapter cell |
| --- | --- |
| East | `(x+4, y+2)` |
| South | `(x+2, y+4)` |
| West | `(x-1, y+2)` |
| North | `(x+2, y-1)` |

Each v2 run starts with approved vent phase **00** at the machine-facing cell.
Extended adds **01**; continuation proceeds **02, 03, 00...**. Standard's first
continuation is **01**. Phase order follows the placement's rotated local +X
direction. The overlay adds no pixels to the outgoing edge, and all housing
pixels/alpha and source boundary differences remain those of the approved family.
No separate elongated adapter texture is created.

## Mandatory crossing geometry and draw order

Each A/B pair uses identical child coordinates, machine layers and complete
lower-route sprites; B's comparison root is simply translated down by 256 units.
In comparison-local cell coordinates:

- Smelter footprint: top-left **(3,6)**, four cells square.
- Lower route: **(7,5) through (7,10)**, directly beside the east footprint edge,
  all six original straight sprites rotated 90 degrees, phases 00/01/02/03/00/01.
- B's Extended assembly: **(7,8) and (8,8)**, extending east from the Smelter.
  The first cell crosses the intact lower sprite at **(7,8)**.
- B's continuation: **(9,8), (10,8), (11,8)**, phases 02/03/00.

Terrain is z=0; guides z=1; lower route z=2; machine artwork z=3; adapter housing
and continuation z=4; coupling z=5. The overlay is a separate Sprite2D with
relative z=1 under the z=4 assembly. These are explicit static draw orders, with
no Y-sorting, ramps, supports, artificial shadows, masks, split lower sprites,
custom crossing textures, lighting effects or animation. The lower route's
textures, alpha, scale, rotation and child positions are identical in A and B.

The unchanged Smelter artwork overhangs its logical footprint, so parts of the
adjacent lower line may also be occluded by that machine in **both** comparisons.
This is visible for evaluation in A before the adapter is added. Upper-route
occlusion uses only the existing housing/overlay alpha. No visual sample creates
a connection or transfers anything between the two routes.

## Preserved sources and reference assets

| File | Role |
| --- | --- |
| [shared_coupling_overlay_v2_candidate_128.png](shared_coupling_overlay_v2_candidate_128.png) / [import](shared_coupling_overlay_v2_candidate_128.png.import) | Unchanged owner-supplied v2 overlay and authored import settings |
| [originals/standard_adapter_v1.png](originals/standard_adapter_v1.png) / [import](originals/standard_adapter_v1.png.import) | Byte-identical copy of `conduit adapter.png`, retained for board 5 |
| [originals/extended_adapter_v1.png](originals/extended_adapter_v1.png) / [import](originals/extended_adapter_v1.png.import) | Byte-identical copy of `conduit extended adapter.png`, retained for board 5 |
| [conduit_adapter_art_v1.tscn](conduit_adapter_art_v1.tscn) | Five static comparison boards |
| [inspection_camera.gd](inspection_camera.gd) | Viewing controls only; adds boards 4/5 to the established bridge camera |

Original Standard: **1262x1246 RGBA**, 590,936 bytes, SHA-256
`22cb6bfcd1047a7e219c7cbf58205c304c3afe0b5e78fd4345083d802e3da008`.
Original Extended: **2172x724 RGBA**, 1,134,181 bytes, SHA-256
`f77a8b252ccf27c3f2058b833e4fc82bbac1e1a2d50c01d3d84a457dc7ec23e6`.
All three supplied files remain unchanged at their original external locations.

Board 5 crops only the **display region**, using Standard `(213,352,834,553)` and
Extended `(165,84,1841,549)`, measured at alpha >=8 to exclude almost-transparent
background residue. The PNG files themselves retain every pixel and metadata byte.
Uniform scene scales are respectively `32/834` and `64/1841`, with the outlet
centerlines at source y=636.5 and y=363 aligned to the straight route centerline.
These are labeled historical reference views, not repaired candidates. They show
the previously measured approximately **12.8/11.3-unit** outlets meeting the
approved approximately **31.25-unit** housing. No stretched or padded derivative
assets are produced.

Approved artwork is referenced in place:

- [Connector-free vent phases 00-03](../conduit_art_v1/supplied_no_connectors_v1/),
  from [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215).
  [Rounded corners](../conduit_corner_art_v1/README.md) and
  [simple bridge layering](../conduit_bridge_layering_v1/README.md), merged in
  PRs #216/#217, provide the retained geometry/layering context.
- Existing [earth](../../assets/experiments/terrain_c1/sources/earth.png) and
  [green](../../assets/experiments/terrain_c1/sources/green.png) textures, with the
  same center crop and nominal phase scale 0.9 used by the earlier experiments.
- Front-facing [Extractor](../../construction/extractor_visual.gd) body/barrel/
  foreground at scale `128/1124` and offsets (-566,-1102), (-312,-865), (-336,-873).
- Front-facing [Smelter](../../construction/smelter_visual.gd) body/interior/
  foreground at scale `4/29` and offsets (-571,-999), (-8,-439), (-72,-460).
  Both machine roots use their production bottom-center anchor at footprint
  origin + (64,128). No machine scripts, animation or thermal layer are instanced.
- Existing IBM Plex Sans Regular and the bridge -> straight experiment ->
  gameplay camera inheritance chain.

The three new import sidecars are authored text following the existing lossless
texture convention: `compress/mode=0`, mipmaps enabled, alpha-border fixing,
no premultiplication or size limit. Sprite filtering is linear with mipmaps
(`texture_filter=4`); terrain remains linear (`2`). No engine-generated UID,
cache, import output or temporary validation artifact is committed.

## Static validation and owner acceptance boundary

Static checks cover PNG CRC/dimensions/RGBA/source identity, preserved alpha and
outgoing clear strip, cell-contained coupling bounds in all rotations, ordered
scene parents and resource references, load steps, uniform scales and grid
registration, phase ordering, machine transforms, exact A/B lower-route identity,
crossing coordinates and explicit draw order. The scene has **608 nodes, 17
external resources, 38 coupling overlays and 152 approved straight sprites**.
The latter comprise 58 adapter housing cells, 70 continuation cells and 24 lower
route cells. There are also four displayed v1 references, 24 static machine
composites and ten terrain panels.

Source/preservation hashes, the focused Python preservation tests, local Markdown
links, import settings and Git scope/whitespace are checked; final results are in
the draft PR. The earlier experiments, production code/artwork, F5 startup,
runner policies, ignored owner files and housekeeping branch are preserved.
Documentation-sync is confined to this experiment README; no canon is rewritten.

**No Godot execution or visual acceptance is claimed.** Engine parsing, imports,
mipmap/alpha appearance, actual machine contact, rotated baked lighting, the
unrepaired source-family seams and normal-zoom readability remain owner checks.
The owner must accept the Standard/Extended proportions and identity, all four
orientations, dirt/grass readability, registration and machine-edge contact, and
especially the intact-line perpendicular crossing on board 3. Small upper-edge
silhouette gaps are deliberately exposed; no machine artwork is modified to hide
them. A static PASS neither grants artistic acceptance nor expands execution or
gameplay authority.
