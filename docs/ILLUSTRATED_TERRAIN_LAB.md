# Illustrated terrain laboratory v1 (feature branch, pending merge)

This isolated editor-painting experiment uses the approved painterly Weathered
Earth and Low Green Cover prototypes. Broad groundwork, common boundaries and
readability take priority over rare cosmetic combinations. Future bushes, trees,
cliffs, rocks and other environmental layers are outside this experiment.

The [original 16px diagnostic lab](../scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn),
its TileSet, PNG, mappings and [PR #98 record](NATIVE_TERRAIN_47_PROTOTYPE.md)
are unchanged. Production rendering, startup, gameplay and native-test controls
are unchanged. This is not a full illustrated atlas or production integration.

## Inputs and preservation

The owner-supplied `tlwh_transition_prototypes_v1.zip` SHA-256 is
`75beb531dc5aaf238fc05cb46a4a671a73d5470be581ba990a69db9efede7b50`.
Its fourteen 128x128 RGB PNGs and README are preserved byte-for-byte in
[`originals/`](../assets/experiments/native_terrain_47_96/illustrated_v1/originals/).
The original ZIP and its two previews remain in the supplied package; previews
are not duplicated into project assets. The README describes neighborhood
examples, not verified terrain signatures or execution authority.

[`mapping.json`](../assets/experiments/native_terrain_47_96/illustrated_v1/mapping.json)
records all original hashes, illustrated signatures, original inventory cells,
source IDs, orientation and protected-resource hashes. The baseline is
`44d83bc46aebe5409d0c2e7ca0e388531ae1e3c3`, verified against a fresh main fetch.

All six protected working resources remain byte-for-byte as initially inspected.
Their separate owner-saved versions remain recoverable at preservation commit
`326591e1a1438944d79b0be4c52992b3eb86af0f`, associated with
[draft PR #99](https://github.com/interneth3ro/the-long-way-home/pull/99).
Neither set is normalized, overwritten, staged or included as resource changes.
Existing untracked artwork, imports and ignored evidence remain preserved. A new
experiment-local `.gitattributes` sets only `originals/README.txt -text` to prevent
Windows checkout conversion of its supplied bytes; root attributes are unchanged.

## Separate 128px TileSet and exact mapping

The [new lab](../scenes/experiments/native_terrain_47_96/illustrated_v1.tscn)
uses a [separate TileSet](../assets/experiments/native_terrain_47_96/illustrated_v1/illustrated_terrain.tres)
with 128x128 cells/regions, one Match Corners and Sides set, Earth `0`, Green `1`,
and all **94 original center-plus-eight-peer signatures**. There are 752 explicit
peer assignments, no duplicate signatures and no missing configurations.

Source 0 contains 84 unsupported configurations. Sources 1..10 each contain one
illustrated tile at atlas (0,0), alternative 0. The table's original cells refer
to the preserved 94-record inventory. Peer order is **NW,N,NE,W,E,SW,S,SE**.
H/V mirror sampled artwork only; serialized peers describe the final orientation.

| Source | Original cell | Center | Eight peers | Original PNG | Mirror |
| --- | --- | --- | --- | --- | --- |
| 1 | (9,2) | 0 | `00000000` | earth_solid | none |
| 2 | (9,6) | 1 | `11111111` | green_solid | none |
| 3 | (9,3) | 0 | `00000111` | horizontal_earth_above | none |
| 4 | (10,0) | 0 | `11100000` | horizontal_earth_above | V |
| 5 | (11,2) | 0 | `00101001` | vertical_earth_left | none |
| 6 | (8,1) | 0 | `10010100` | vertical_earth_left | H |
| 7 | (9,7) | 1 | `11111000` | horizontal_green_above | none |
| 8 | (10,4) | 1 | `00011111` | horizontal_green_above | V |
| 9 | (11,6) | 1 | `11010110` | vertical_green_left | none |
| 10 | (8,5) | 1 | `01101011` | vertical_green_left | H |

Two interiors plus four boundary orientations per center provide the minimal
symmetric subset for long straight boundaries with either terrain painted first.
Opposite center families do not automatically share an edge: all three shared
peers must agree. Each illustrated straight edge has compatible illustrated
neighbors, including the appropriate solid interior.

The four corner PNGs have no direct center-plus-peer match and remain reference
assets. Narrow-connection and isolated-patch PNGs also remain reference-only in
this smaller implementation. Candidate signature matches alone do not establish
visual edge compatibility.

## Minor edge compatibility treatment

The supplied transitions reach approximately 50/50 Earth/Green mixtures on some
border samples. Direct neighborhood-to-peer assignment would not make those
pixels match a neighboring solid tile.

An [experimental TileData shader](../assets/experiments/native_terrain_47_96/illustrated_v1/edge_compatibility.gdshader)
conditions only the outer **eight pixels** of straight-boundary tiles. Pixels
8..119 in both axes (112x112) remain the original sampled artwork. The shader
interpolates three native peers along each edge, then blends the two original
solid textures to reach that shared boundary. Corner ties use the same corner
peer. Correction fades to zero eight pixels inward. Mirrored orientations reuse
the same PNGs; solid interiors have no shader.

No PNG is edited or regenerated and no new art direction is introduced. A slight
rim or contour tightening may appear in the perimeter band; owner inspection
must determine whether it is unobtrusive. Significant contour redesign, broader
repainting or a new illustrated mask family requires owner approval.

Each illustrated source is one unpadded texture so shader UVs address that tile.
Nearest sampling avoids neighboring atlas interpolation. These settings use the
documented [TileSetAtlasSource](https://docs.godotengine.org/en/stable/classes/class_tilesetatlassource.html)
and [TileData material](https://docs.godotengine.org/en/stable/classes/class_tiledata.html)
interfaces. Godot 4.7.2 import, shader compilation and rendering remain unverified.
Eight experimental materials add texture sampling; no performance result or
production suitability is claimed.

## Unsupported configurations and limits

All other **84 configurations** retain diagnostic sector artwork with a magenta
center square. The enlarged SVG is a technical fixture, not finished illustrated
terrain. It may appear at corners, islands, narrow links, irregular contours and
boundary endpoints. Its color discontinuities must be distinguished from seams
between illustrated cells. No approximate corner signatures are introduced.

The scene has no gameplay scripts, prepainted map, collisions or navigation.
It uses native editor Connect painting with 128-unit cells. This does not replace
the production 64-unit terrain scale; editor zoom is a comparison aid, not final
gameplay-scale acceptance.

## Static validation and preservation guards

Run only the permitted static suite:

```powershell
python -B -m unittest discover -s tests -p 'static_*test.py'
```

The [focused static checks](../tests/static_illustrated_terrain_test.py) cover PNG
hashes, CRCs, decoding, dimensions and opposite solid-edge equality; all original
signatures; material peers/orientations; compatible shared-edge mathematics;
references; diagnostic markers; protected bytes; and unchanged baseline production
assets and scenes.

The historical artwork guard gains only twenty-one exact new experiment paths with
individually pinned hashes in
[`illustrated_terrain_preservation.py`](../tests/illustrated_terrain_preservation.py).
Existing hashes and the original three-path terrain guard remain intact. Negative
checks reject altered candidates and all six protected resources. There is no
directory exemption or expansion of Native execution/staging scope.

Static checks establish a resource/data and mathematical boundary contract. They
do not execute the shader, parse resources in Godot, prove native Connect choices
or establish visual seam quality. Godot, Native, graphical tests, profiling and
benchmarks are **NOT RUN**. Follow the [execution policy](../AGENTS.md#godot-execution-safety).

Final feature validation on 2026-10-31: **125/125 static tests PASS** (including
six new focused tests), zero failures/errors. Staged originals match the ZIP
byte-for-byte, all six protected working hashes match their initial snapshot,
new local Markdown links resolve, and `git diff --cached --check` passes.

## Owner graphical acceptance

These are owner-only instructions; they do not authorize agent graphical work.
Open `scenes/experiments/native_terrain_47_96/illustrated_v1.tscn` in the editor.
Select `PaintingWorkspace`, then TileMap > Terrains > Connect, and choose Earth
or Green. No F5/F6 is needed. Start with broad filled regions and long straight
boundaries; zoom out to assess the ground as background. Keep checks modest and
stop if Windows or the editor becomes unresponsive. No stress test is requested.

Record **PASS/FAIL**, optional observations, selected sources/cells and brush
order for each row. All rows currently remain **NOT RUN**.

| Check | PASS criterion / observation |
| --- | --- |
| Resource import | Scene, textures, TileSet and shader load without errors. |
| Earth interior | Broad region reads as warm, quiet groundwork; no conspicuous grid. |
| Green interior | Broad region reads as restrained natural cover; no conspicuous grid. |
| Horizontal boundaries | Earth-above-Green and Green-above-Earth work with either paint order. Separate central illustrated spans from diagnostic endpoints. |
| Vertical: Earth left / Green right | Inspect full length and both endpoints; record protrusions, source IDs and brush order. Repeat opposite paint order. |
| Vertical: Green left / Earth right | Repeat full-length and both-endpoint checks in the other direction. PR #98 endpoint failures remain unresolved without owner evidence. |
| Inner/outer corners | Identify magenta placeholders; distinguish matching defects from unsupported artwork. No corner-art acceptance claimed. |
| Narrow connections | Record diagnostic coverage, unexpected holes or matching errors. |
| Isolated patches | Both center terrains remain selectable; record placeholders and holes. |
| Large irregular regions | Broad interiors/common spans remain readable; distinguish diagnostic contours from illustrated defects. |
| Seams, rims and repetition | No conspicuous seams or eight-pixel rims between illustrated neighbors; note repetition. Minor uncommon flaws may be documented and accepted. |
| Gameplay-scale readability | Review at intended apparent ground size; assess whether future machinery/characters would remain prominent. Final gameplay integration is outside this lab. |

Unsupported artwork can be an accepted limitation. Incorrect data, holes in common
spans or conspicuous seams between illustrated neighbors require investigation.
Owner acceptance, merge and post-merge cleanup remain separate decisions.
