# TLWH Issue #96 — Reference-derived 47-pattern mapping

Source: user-supplied `godot-4-tileset-terrains-docs-master.zip`, `starter_project/terrain_modes/topdown_example/topdown_example.tscn`, Match Corners and Sides atlas resource (`TileSetAtlasSource` referencing `buch_floating_islands_corners_and_sides.png`).

This is a **technical connectivity transcription**, not artwork and not a tested TLWH TileSet. The reference uses 16-pixel cells. The reference Dirt family is translated as reference Grass (1) → TLWH Earth (0), reference Dirt (2) → TLWH Green (1). All 47 primary terrain IDs become Green (1).

Bit order: TL, Top, TR, Left, Right, BL, Bottom, BR. `0` means TLWH Earth; `1` means TLWH Green. Coordinates are zero-based reference atlas coordinates.

| # | Atlas (x,y) | Center | TL | T | TR | L | R | BL | B | BR |
|---:|:---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| 1 | (0,4) | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 0 |
| 2 | (1,4) | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 0 |
| 3 | (2,4) | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 0 |
| 4 | (3,4) | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 1 | 0 |
| 5 | (4,4) | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 0 |
| 6 | (5,4) | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 1 | 1 |
| 7 | (6,4) | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 0 |
| 8 | (7,4) | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| 9 | (8,4) | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 1 | 1 |
| 10 | (9,4) | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |
| 11 | (10,4) | 1 | 0 | 0 | 0 | 1 | 1 | 1 | 1 | 1 |
| 12 | (11,4) | 1 | 0 | 0 | 0 | 1 | 0 | 1 | 1 | 0 |
| 13 | (0,5) | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 1 | 0 |
| 14 | (1,5) | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 0 |
| 15 | (2,5) | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 0 |
| 16 | (3,5) | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 1 | 0 |
| 17 | (4,5) | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 1 | 1 |
| 18 | (5,5) | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 19 | (6,5) | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 1 |
| 20 | (7,5) | 1 | 0 | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| 21 | (8,5) | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 1 |
| 22 | (9,5) | 1 | 0 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| 23 | (11,5) | 1 | 1 | 1 | 0 | 1 | 1 | 1 | 1 | 0 |
| 24 | (0,6) | 1 | 0 | 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 25 | (1,6) | 1 | 0 | 1 | 0 | 0 | 1 | 0 | 0 | 0 |
| 26 | (2,6) | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 0 | 0 |
| 27 | (3,6) | 1 | 0 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |
| 28 | (4,6) | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 1 | 0 |
| 29 | (5,6) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 30 | (6,6) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 0 |
| 31 | (7,6) | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 1 | 0 |
| 32 | (8,6) | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 1 | 1 |
| 33 | (9,6) | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 | 1 |
| 34 | (10,6) | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 1 | 1 |
| 35 | (11,6) | 1 | 1 | 1 | 0 | 1 | 0 | 1 | 1 | 0 |
| 36 | (0,7) | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| 37 | (1,7) | 1 | 0 | 0 | 0 | 0 | 1 | 0 | 0 | 0 |
| 38 | (2,7) | 1 | 0 | 0 | 0 | 1 | 1 | 0 | 0 | 0 |
| 39 | (3,7) | 1 | 0 | 0 | 0 | 1 | 0 | 0 | 0 | 0 |
| 40 | (4,7) | 1 | 0 | 1 | 0 | 1 | 1 | 1 | 1 | 0 |
| 41 | (5,7) | 1 | 0 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 42 | (6,7) | 1 | 1 | 1 | 0 | 1 | 1 | 0 | 0 | 0 |
| 43 | (7,7) | 1 | 0 | 1 | 0 | 1 | 1 | 0 | 1 | 1 |
| 44 | (8,7) | 1 | 0 | 1 | 1 | 0 | 1 | 0 | 0 | 0 |
| 45 | (9,7) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 0 | 0 |
| 46 | (10,7) | 1 | 1 | 1 | 1 | 1 | 1 | 0 | 1 | 0 |
| 47 | (11,7) | 1 | 1 | 1 | 0 | 1 | 0 | 0 | 0 | 0 |

## Findings

- All 47 records have a Green primary terrain ID and eight explicitly assigned bits.
- Every eight-bit signature is unique within the selected family.
- Fully Green pattern(s): #33 at (9,6).
- All-Earth peering pattern(s) with a Green center: #36 at (0,7).
- The source scene contains a separate Grass-to-Water family; it is not included in this mapping.
- A Green-centered 47-pattern family does not establish complete native painting in both directions.
- Do not import the reference PNG or its artwork into TLWH.
- No Godot 4.7.2 runtime/editor compatibility or procedural chunk performance has been established.

## Prototype validation

1. Configure a temporary original flat-color TileSet with mode 0 and these exact mapped signatures.
2. Test painting Green inside Earth, and Earth inside Green, including islands, one-cell strips, diagonals and notches.
3. Record which primary terrain and atlas cell the native painter selects, and any missing patterns.
4. Verify reverse painting order and boundary stability.
5. Only after visual painting works, investigate deterministic per-chunk selection with neighbor halos and generation-order invariance.
6. Preserve PR #97 and existing production terrain; require separate implementation and native-execution approval.
