# Ferrite shape catalog v1

Milestone 1 implementation on a feature branch, pending merge and **owner artistic
acceptance**. This is an offline production-candidate library, not procedural
placement or a runtime renderer. Accepted PR #123 artwork and PR #124 production
integration remain unchanged.

## Review package

- [Contact sheet](../assets/experiments/ferrite_catalog_v1/contact_sheet.png):
  ten silhouettes grouped by size, then family, all at 0.30 source scale.
- Individual transparent previews are the candidate PNGs in the inventory.
  There are no redundant clean-preview copies.
- [Small mask/Extractor overlay](../assets/experiments/ferrite_catalog_v1/ferrite_v1_small_table_overlay.png).
- [Medium mask/Extractor overlay](../assets/experiments/ferrite_catalog_v1/ferrite_v1_medium_elbow_overlay.png).
- [Large mask/Extractor overlay](../assets/experiments/ferrite_catalog_v1/ferrite_v1_large_sprawl_overlay.png).

Cyan shows occupied cells. Yellow is exactly 128×128 source pixels: 64×64 world
units, or the existing Extractor's 2×2 construction cells. It is a scale reference,
not new machine artwork. Review images are intentional authoring deliverables
behind their own `.gdignore`; production candidates are outside `.gdignore`.
No scene references this catalog.

## Sources and geometry

[shapes.json](../assets/environment/exterior/ferrite/catalog_v1/shapes.json)
assigns explicit stable IDs, size classes and families. Each ID selects its one
authoritative text mask: `#` occupied, `.` empty, rows north to south and columns
west to east. No independently edited polygon is maintained.

[catalog.json](../assets/environment/exterior/ferrite/catalog_v1/catalog.json)
is derived by the offline geometry compiler. Every entry records version, ID,
class/family, mask path, bounding dimensions, occupied count, local logical
polygon, PNG path, padded image origin/dimensions and display scale. Do not
hand-edit it.

The compiler removes internal cell edges, traces one simple contour and collapses
collinear vertices. Polygons are clockwise in screen coordinates (positive Y
south), with 64-unit grid vertices. Rounded paint/shadows are decorative, never
mining boundaries.

Density is 128 source pixels per terrain cell, displayed uniformly at 0.5.
The padded logical origin is `(64,64)` source pixels. Given eventual logical
world origin `P`, an uncentered sprite's canvas origin is `P - (32,32)`; translate
polygon vertices by `P` directly. This also works at negative coordinates.
No finished image is stretched, rotated or mirrored.

## Inventory

All entries belong to `faceted_ferrite_catalog_v1`.

| Stable ID | Class | Family | Bounding cells | Occupied cells | Image pixels | Asset path / authoritative mask |
| --- | --- | --- | --- | --- | --- | --- |
| `ferrite_v1_small_table` | small | rectangle | 4×3 | 12 | 640×512 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_small_table.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_small_table.txt) |
| `ferrite_v1_medium_slab` | medium | rectangle | 7×5 | 35 | 1024×768 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_medium_slab.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_medium_slab.txt) |
| `ferrite_v1_medium_elbow` | medium | l_shape | 7×5 | 27 | 1024×768 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_medium_elbow.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_medium_elbow.txt) |
| `ferrite_v1_medium_offset` | medium | stepped | 6×5 | 22 | 896×768 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_medium_offset.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_medium_offset.txt) |
| `ferrite_v1_medium_terraces` | medium | stepped | 8×6 | 40 | 1152×896 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_medium_terraces.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_medium_terraces.txt) |
| `ferrite_v1_medium_crown` | medium | organic | 7×6 | 34 | 1024×896 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_medium_crown.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_medium_crown.txt) |
| `ferrite_v1_large_elbow` | large | l_shape | 10×7 | 52 | 1408×1024 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_large_elbow.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_large_elbow.txt) |
| `ferrite_v1_large_stair` | large | stepped | 11×7 | 54 | 1536×1024 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_large_stair.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_large_stair.txt) |
| `ferrite_v1_large_basin` | large | organic | 10×8 | 57 | 1408×1152 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_large_basin.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_large_basin.txt) |
| `ferrite_v1_large_sprawl` | large | organic | 12×8 | 72 | 1664×1152 | [PNG](../assets/environment/exterior/ferrite/catalog_v1/ferrite_v1_large_sprawl.png) / [mask](../assets/environment/exterior/ferrite/catalog_v1/masks/ferrite_v1_large_sprawl.txt) |

One small, five medium and four large entries form a review sample, not spawn
quotas. Future selection targets are rectangular 20%, L-shaped 20%, stepped 25%,
organic 35%; small 10%, medium 50%, large 40%. They are metadata only.
Distance-based large-deposit preference remains deferred and separate from lookup.

## Offline authoring commands

Requires existing Python standard library, Windows PowerShell 5.1, .NET Framework
System.Drawing and Segoe UI. No packages or Godot are required. From repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/build-ferrite-catalog.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File tools/build-ferrite-catalog.ps1 -Check
python -B -m unittest discover -s tests -p 'static_ferrite_catalog_test.py'
python -B -m unittest discover -s tests -p 'static_ferrite_integration_test.py'
```

Execution-policy bypass is process-local. Build writes only derived catalog JSON,
ten candidate PNGs, contact sheet and three overlays. `-Check` derives them in
memory, compares canonical JSON text (LF/CRLF equivalent) and exact PNG bytes,
and writes no outputs. Geometry-only check:
`python -B tools/ferrite-catalog.py --check`.

The builder parses the preserved irregular prototype's PowerShell AST and compiles
only its embedded C# declarations. It never dot-sources that script or calls its
build entry point. A small offline reflection adapter initializes the existing
interior/directional strips and calls the contour compositor. Original source,
components and previews are untouched; the compositor is not copied.
Private-method coupling is confined to this offline tool. A future compositor
refactor requires reviewing the adapter and reproduction results.

All candidates, including rectangles, use the contour renderer. The original
rectangular splice path failed the new faint-alpha connectivity check at the
selected small size. Contour rendering reuses continuous source paint, oriented
perimeters, shallow sidewalls and contact shadows without retouching or new art.
Existing rectangular outputs remain preserved.

## Reconstruction and expansion

Future worlds can pin `faceted_ferrite_catalog_v1` and reference explicit variant
IDs. Array order is not identity. A future save must separately retain seed,
world-generation version and selection-policy/configuration identity. No save
system or region generator is introduced.

Once released, retain a catalog version's IDs, masks, geometry, registration and
approved images. Changes affecting reconstruction require a new catalog version
or explicit migration decision; do not silently reinterpret old IDs. This v1
review package may be revised before release without claiming artistic acceptance.
Git preserves authoring revisions; no whole-source freeze or historical source
dependency is added.

Expand toward 20–30 curated variants with meaningful broad silhouettes and
reviewed paint arrangements through the same mask/derivation workflow. Preserve
released identities and decide version compatibility explicitly. Runtime image
composition is not required.

## Validation and limits

Geometry checks cover legal class dimensions/tokens, four-neighbor connectivity,
outside flood-fill/hole rejection, one simple contour and diagonal-contact
rejection. Every occupied cell must belong to a solid 2×2 terrain-cell block;
removing any one occupied cell must leave the others connected. These deliberately
conservative admission rules exclude narrow tips/arms and one-cell bottlenecks.
They do not change the existing 64×64 Extractor or extraction-point placement rule.

Polygon/cell agreement is checked locally and at negative world translations.
Static tests independently check area/orientation, full-cell interior membership,
ID lookup independent of ordering, PNG chunk CRCs, RGBA headers/decompressed
lengths, image dimensions, registration, review outputs and no runtime dependency.

The artwork check validates opaque interiors, transparent exterior and canvas
borders, occupied/empty cell centers, and raster connectivity at alpha thresholds
1 and 128. Reproduction compares all ten candidate and four review PNGs byte for
byte. Existing Ferrite integration regressions cover accepted production
geometry, artwork and source-level gameplay contracts.

The source still repeats silver highlights and diagonal grain, especially on
large fields. Concave rims are more regular than the strongest hand-painted
corners; blending can soften fractures. These are documented prototype limits.
Variation here is in silhouettes/sizes, without recoloring, rotated lighting,
flat placeholders, per-image retouching or claims of new painted material.
Owner review must assess the delivered small field, broad large interiors and
concave turns. Technical PASS is not artistic acceptance.

No Godot import, graphical/gameplay verification or performance measurement is
claimed. Region candidates, distribution, spacing, streaming, indexing,
presentation/preload/loading UI, distance progression and persistence are out of
scope. ResourceDeposit's contract, terrain, crash-site clearing, introductory
deposit, story and production mechanics remain unchanged.
