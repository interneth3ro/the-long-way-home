# Native terrain configuration prototype — Issue #96

Feature branch `codex/96-native-terrain-prototype`, pending merge and owner review.
This is an isolated technical experiment related to [issue #96](https://github.com/interneth3ro/the-long-way-home/issues/96),
not delivery of that issue's production visual or performance acceptance.
Base: synchronized `main`, PR #95 merge `48cd915`. Tracked baseline was clean;
pre-existing untracked owner artwork/import sidecars were preserved and excluded.

## Files and configuration

- [Temporary atlas](../assets/experiments/native_terrain_96/experimental_corner_masks_16.png):
  128 x 128 RGB PNG, 4 x 4 tiles of 32 x 32 pixels. Its filename, PNG Title metadata,
  resource name and lab label explicitly mark it experimental, not approved art.
- [TileSet](../assets/experiments/native_terrain_96/experimental_match_corners.tres):
  one square atlas source ID 0, terrain set 0, Match Corners (`mode = 1`),
  Earth ID 0 and Green ID 1, base alternative ID 0 only. No side bits, empty bits,
  collision, navigation, custom data, proxies or additional terrains.
- [Painting laboratory](../scenes/experiments/native_terrain_96/terrain_painting_lab.tscn):
  script-free Node2D, empty TileMapLayer `PaintingWorkspace`, neutral backdrop,
  instructions and enlarged atlas reference. Nearest filtering. No game launch
  required for painting; no main-scene setting changes.
- [Static checks](../tests/static_native_terrain_prototype_test.py): PNG CRC and all
  pixels, resource assignments, combination gaps, references and production isolation.

The PNG is an exact technical data fixture constructed with Python standard-library
PNG encoding, without an image model, external assets or dependencies. Earth is
warm brown `#8B5E3C`; Green is muted `#657C4F`. Each corner owns an 16 x 16 quadrant.
This deliberately blocky diagram tests metadata and matching, not organic artwork.
No illustrated 24-tile atlas was created. Production uses 64-unit textured polygons;
this 32-unit grid has no connection to world or construction coordinates.

## Complete atlas inventory

Coordinates are zero-based (column, row). Pixel origin is `(32*x, 32*y)`;
region size is always 32 x 32. Bit weights: TL=1, TR=2, BL=4, BR=8.
A set bit means Green (1); an unset bit means Earth (0), never empty (-1).
Center is explicit: Green only with 3 or 4 green corners; otherwise Earth,
including all six 2:2 ties. This is an experimental choice, not an engine rule.

| Mask | Atlas | Pixel origin | Center | TL | TR | BL | BR |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 0 | (0, 0) | (0, 0) | 0 | 0 | 0 | 0 | 0 |
| 1 | (1, 0) | (32, 0) | 0 | 1 | 0 | 0 | 0 |
| 2 | (2, 0) | (64, 0) | 0 | 0 | 1 | 0 | 0 |
| 3 | (3, 0) | (96, 0) | 0 | 1 | 1 | 0 | 0 |
| 4 | (0, 1) | (0, 32) | 0 | 0 | 0 | 1 | 0 |
| 5 | (1, 1) | (32, 32) | 0 | 1 | 0 | 1 | 0 |
| 6 | (2, 1) | (64, 32) | 0 | 0 | 1 | 1 | 0 |
| 7 | (3, 1) | (96, 32) | 1 | 1 | 1 | 1 | 0 |
| 8 | (0, 2) | (0, 64) | 0 | 0 | 0 | 0 | 1 |
| 9 | (1, 2) | (32, 64) | 0 | 1 | 0 | 0 | 1 |
| 10 | (2, 2) | (64, 64) | 0 | 0 | 1 | 0 | 1 |
| 11 | (3, 2) | (96, 64) | 1 | 1 | 1 | 0 | 1 |
| 12 | (0, 3) | (0, 96) | 0 | 0 | 0 | 1 | 1 |
| 13 | (1, 3) | (32, 96) | 1 | 1 | 0 | 1 | 1 |
| 14 | (2, 3) | (64, 96) | 1 | 0 | 1 | 1 | 1 |
| 15 | (3, 3) | (96, 96) | 1 | 1 | 1 | 1 | 1 |

Godot peering property names are `top_left_corner`, `top_right_corner`,
`bottom_left_corner`, `bottom_right_corner` (neighbor enums 11, 15, 7, 3).
Terrain IDs, not binary mask numbers, are stored in those fields.

## Center interpretation and known gaps

[Godot 4.7.2 terrain solver source](https://github.com/godotengine/godot/blob/4.7.2-stable/scene/2d/tile_map_layer.cpp)
(`terrain_fill_connect`) assigns center constraints and derives corner constraints
from participating centers. Thus Match Corners does not discard the primary terrain.
This is source inspection, not execution of the installed binary.

All 16 binary corner tuples exist once. **The set is not proven sufficient for
native painting.** With independent binary center identity there are 32 possible
metadata tuples; this resource covers 16. Every mask lacks the opposite center
from the table. In particular mask 0 lacks Green center and mask 15 lacks Earth
center: potential single-cell island cases. Mixed masks also lack their opposite
center assignments. No duplicates/alternative tiles are included so the initial
16-configuration hypothesis stays reviewable.

Inference: metadata alternatives may help missing center cases, but copying the
same pixels with another center ID does not add a visible central island. Some
cases may need new pixel geometry as well as additional metadata. Which tuples
native Connect actually requests, and whether alternatives resolve failures,
remain owner-test questions. This PR does not silently expand to 32 tiles.

Masks 6 and 9 are diagonal saddles; their quadrants touch at a point, with no
chosen smooth connection. Tied masks 3, 5, 6, 9, 10 and 12 all use Earth centers;
painting can consequently be asymmetric. The fixture has no Earth/empty or
Green/empty transitions. Test inside a filled backing region with at least a
2-cell margin; record erasing/outer-edge behavior separately. Empty is not Earth.

## Reference comparison and version limits

The [official TileSet reference](https://docs.godotengine.org/en/latest/classes/class_tileset.html)
identifies Match Corners as mode 1. The [official TileSet tutorial](https://docs.godotengine.org/en/stable/tutorials/2d/using_tilesets.html)
is general setup guidance, not proof of this binary atlas's completeness.
These moving documentation URLs may describe a different version.
[Upstream issue #87929](https://github.com/godotengine/godot/issues/87929)
reports center/corner path difficulties in 4.2.1; it is historical context only.
No supplied reference example was represented as a verified 4.7.2 result.
The lab uses TileMapLayer rather than older TileMap examples. UI differences,
center behavior and narrow-strip behavior on the installed 4.7.2 remain unverified.

## Owner-controlled graphical checklist

**Agent status: NOT RUN for all graphical tests.** The owner can perform these
checks or explicitly authorize a bounded agent editor session. Existing Native
permission does not cover this experiment. No F5/F6, playable scene, headless
import, profiler or benchmark is needed/requested here. Do not change the runner
or staging inventory to make this prototype executable under standing scope.

After authorization, open the project in the specified standard Godot 4.7.2
editor and open only the lab scene. Stop on import/parse errors or abnormal
responsiveness; do not retry automatically. Do not start the game. Preserve any
generated import metadata for review; it was not produced/committed by this PR.
Select `PaintingWorkspace`, then the native TileMap **Terrains** panel, terrain
set 0 and **Connect** mode. Confirm the TileSet terrain overlay first. The gray
workspace is 24 x 16 cells; painting beyond it is allowed by the editor. Each test
can replace the previous one using Undo; avoid saving experimental edits over the
reviewed resources. Record results in the review, with optional observations.

Use an Earth 20 x 12 backing at local cells (2,2)..(21,13). Paint Green test shapes
inside (4,4)..(19,11), then repeat each with Green backing and Earth brush. The
backdrop is only a guide. Inspect atlas coordinates/primary terrain via tile
selection when results fail. Use Connect for comparisons; optionally record Path
mode separately, including brush order. Do not interpret manual atlas stamping
as native terrain-painting success.

| Test | Action and PASS criterion | Outcome | Optional observations |
| --- | --- | --- | --- |
| Import/configuration | Lab opens without errors; one source/set, Earth/Green, Match Corners, all 16 masks and overlay IDs match inventory. | NOT RUN (PASS/FAIL) | |
| Large regions | Paint an 8 x 8 opposing block; interiors are uniform, border corners agree, no holes or unrelated terrain. | NOT RUN (PASS/FAIL) | |
| Single-cell islands | Single opposing click inside backing survives as a visible island, with matching surrounding corners; test both materials. | NOT RUN (PASS/FAIL) | |
| Straight boundaries | Paint opposing half-region, horizontal then vertical; continuous shared edges, no unexpected gaps. | NOT RUN (PASS/FAIL) | |
| Convex/concave corners | Paint an L and a notch in a block, all four rotations; intended shape survives and shared corners agree. | NOT RUN (PASS/FAIL) | |
| Narrow strips | Paint a 1-cell-wide horizontal and vertical strip plus an L bend, then 2-cell-wide controls; strips survive without widening or breaks. | NOT RUN (PASS/FAIL) | |
| Diagonals | Paint diagonal single cells and a 2 x 2 checker; record selected masks 6/9, point contacts and any center-driven substitutions. Intended cells survive with consistent corners. | NOT RUN (PASS/FAIL) | |
| Irregular patches | Paint a stepped patch with a notch and isolated tip; compare forward/reverse brush order. No missing tiles or corner mismatches; record any order dependence. | NOT RUN (PASS/FAIL) | |

A failed island/strip is a useful experimental result, not permission to repair
production terrain. Record expected shape, actual shape, mask coordinates, center
IDs, Connect/Path mode and brush order. Optional exact cropped evidence belongs
under ignored `artifacts/screenshots/`; routine successful output need not be saved.

## Static validation and acceptance boundary

Run `python -B -m unittest discover -s tests -p 'static_*test.py'` and
`git diff --check`. Results are recorded in the PR; no Godot or project code is
invoked. These checks validate fixture consistency and unchanged production inputs,
not Godot parsing, importing, painting, appearance, performance or acceptance.

TerrainChunk, PlanetGenerator, streaming, factory/construction systems, crash-site
masks, protected areas and approved environmental artwork remain unchanged.
No production resource references this lab. No Native run, graphical acceptance,
profiling, benchmark, merge or post-merge cleanup is authorized by this document.
Owner review must resolve whether the initial center policy is useful, which
missing tuples matter, and whether additional metadata or new visual tiles are
necessary before any further implementation or integration.
