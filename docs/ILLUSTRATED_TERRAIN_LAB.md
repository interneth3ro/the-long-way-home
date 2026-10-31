# Illustrated terrain laboratory / baked Stage 2 (pending merge)

The owner approved Stage 1's offline visual method on 2026-10-31: broad painterly
groundwork, soft transitions, common corners, endpoints, narrow links and isolated
patches. Minor rounded stepping, occasional corner pockets and repetition with
the three existing interior alternatives are accepted prototype limitations.
The owner subsequently accepted the baked Stage 2 laboratory: **12/12 graphical
tests PASS** at `2c7c392cc580e56bcfc8a9fd0c5fd699726339b4`. This includes native
painting and both vertical-boundary orientations with their endpoints in the
tested laboratory. PR #100 remains draft for the owner's final review and merge.
Production chunk integration and runtime performance have not been tested or accepted.

## Current acceptance path

Open [illustrated_baked_v2.tscn](../scenes/experiments/native_terrain_47_96/illustrated_baked_v2.tscn).
Select `PaintingWorkspace` > TileMap > Terrains > Connect. Fill a broad Earth
background, then paint Green over it; repeat with colors and paint order reversed.
No F5/F6 is needed. This is an empty, script-free editor workspace with 128-unit
cells, nearest filtering and no collisions/navigation.

The [baked TileSet](../assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres)
has one Match Corners and Sides set: Earth `0`, Green `1`. It references only baked
PNGs. There is no ShaderMaterial, edge repair, diagnostic texture or custom matcher.

| Atlas source | Artwork and assignments |
| --- | --- |
| 0: [baseline_94.png](../assets/experiments/native_terrain_47_96/baked_v2/baseline_94.png) | 1536x1024 RGB, original 12x8 coordinates, 128px cells. All 94 original signatures (47 Earth + 47 Green) and 752 peers unchanged. |
| 1: [interiors_bc.png](../assets/experiments/native_terrain_47_96/baked_v2/interiors_bc.png) | 256x256 RGB, four tiles: Earth B/C at (0,0)/(1,0), Green B/C at (0,1)/(1,1). Only the two existing solid signatures are repeated. |

There are **94 unique baseline signatures**, plus four deliberate solid-art
alternatives: **98 paintable records and 784 explicit peers** in total. The extra
records do not add configurations or change the original 752 baseline assignments.
A is the baseline solid; B/C are the approved source-derived interior alternatives.
Only solid interiors have alternatives; all transitions use A. The owner accepted
native A/B/C selection in the laboratory; no fixed statistical distribution is
claimed. No new style or variation system.

Baseline slots (10,1)/(10,5) remain unconfigured; their black pixels are unused
atlas space, not paintable placeholders. Every configured tile has baked artwork.
The [manifest](../assets/experiments/native_terrain_47_96/baked_v2/mapping.json)
records signatures, original coordinates, raster/source hashes and exact Stage 1
proof provenance. Peer order is NW,N,NE,W,E,SW,S,SE.

## Approved offline method

The [authoring recipe](../tools/bake-illustrated-terrain.py) uses the unchanged
approved `earth_solid.png` and `green_solid.png`. It reproduces Stage 1 v3's math:
interpolate three shared peers along each edge; construct a Coons surface between
the four curves; enforce the center through an edge-zero interior bubble; add the
same periodic perturbation; feather at field values 0.30..0.70; blend in linear
light and encode sRGB PNGs. All nine raster anchors are checked against each signature.

B/C sampling offsets, rotations and sine-squared interior envelope are unchanged.
B/C preserve every edge pixel. Twenty approved baseline rasters and four B/C
rasters are exact pixel regression fixtures. Original unmatched corner PNGs remain
reference assets and are not force-mapped.

The recipe reads fixed local art/inventory. Its command creates a **new** output
directory and refuses an existing directory. It invokes no engine and requires
no third-party dependency:

```powershell
python -B tools/bake-illustrated-terrain.py <new-output-directory>
```

This is offline authoring tooling, not a game dependency or Native-runner command.

## Preservation and earlier experiments

The [original diagnostic laboratory](../scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn),
its TileSet/PNG, [94-record inventory](experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv)
and [PR #98 record](NATIVE_TERRAIN_47_PROTOTYPE.md) remain unchanged.
The earlier [10-illustrated/84-diagnostic lab](../scenes/experiments/native_terrain_47_96/illustrated_v1.tscn)
and its edge shader are preserved as history, outside the current acceptance path.
No old experiment or owner-generated import file is removed.

All fourteen original approved PNGs and supplied README remain byte-identical in
`assets/experiments/native_terrain_47_96/illustrated_v1/originals/`.
The supplied ZIP SHA-256 remains
`75beb531dc5aaf238fc05cb46a4a671a73d5470be581ba990a69db9efede7b50`.
Existing exact-path README and root attributes remain unchanged.

All six protected working resources retain their recorded hashes. Separate
owner-saved versions remain recoverable at
`326591e1a1438944d79b0be4c52992b3eb86af0f` / [draft PR #99](https://github.com/interneth3ro/the-long-way-home/pull/99).
Stage 1 proofs/evidence, untracked art/imports, ignored evidence and owner data are
preserved. Production rendering, chunk integration, startup, gameplay and narrative
state remain unchanged.

## Static checks and offline previews

```powershell
python -B -m unittest discover -s tests -p 'static_*test.py'
```

The [baked static checks](../tests/static_baked_terrain_test.py) inspect PNG CRCs,
dimensions/scanlines, exact 94/752 inventory, four solid alternatives, raster
anchors, Stage 1 goldens, every compatible saved tile edge, shader-free references
and protected bytes. Earlier terrain/preservation assertions remain in force.
Six new inputs are individually pinned in
[baked_terrain_preservation.py](../tests/baked_terrain_preservation.py).
Existing diagnostic/first-illustrated pins remain unchanged. The offline recipe
gets only an exact-path/hash allowance in historical scope checks. No directory
exemption, Native staging expansion, runner command or execution permission is added.

Stage 2 validation on 2026-10-31: **131/131 static tests PASS**, zero failures or
errors, including six new baked tests. All 2,788 compatible saved-atlas edge pairs
match exactly, the 24 approved raster goldens match, and local Markdown links and
`git diff --check` pass. Preservation checks retain all earlier art/labs and Stage 1
evidence. No engine or graphical verification is included in these results.

Eight ignored local previews in `artifacts/evidence/pr100-stage2-baked-v2/` use
**saved PNG cells**: irregular Earth/Green regions, a meandering boundary, both
vertical directions with finite endpoints, a narrow vertical link, and isolated
patches of both terrains. B/C apply only to solids, matching the TileSet. Their
1,110 shared tile boundaries match exactly. `previews.json` stores assignments and
hashes; `preservation_snapshot.json` captures working files and Stage 1 evidence.

Preview assignments are offline constraints, not Godot Connect or brush-order
verification. Equal edge pixels do not establish smooth derivatives, imported
filtering or visual seam acceptance. The 128-unit lab does not replace production's
64-unit terrain scale. No numerical performance claim is made. **Codex did not run
Godot, Native, graphical automation, profiling or benchmarks.** Owner graphical
acceptance below is separate from Codex's static validation. Production chunk
integration and runtime performance have not been tested or accepted. Follow the
[execution policy](../AGENTS.md#godot-execution-safety).

## Owner graphical acceptance / 12 of 12 PASS

The owner completed all twelve Stage 2 graphical tests at
**`2c7c392cc580e56bcfc8a9fd0c5fd699726339b4`: 12/12 PASS**.
These are owner-reported results, not Codex graphical execution or a performance
benchmark. The grouped coverage below summarizes the accepted laboratory scope.

Owner observations:

> Much, much stronger candidate. Could not produce any odd tiles that looked out of place, transitions are smooth, editor was very responsive. Very, very good.

| Coverage | Owner result / accepted scope |
| --- | --- |
| Import/correct scene | **PASS**: baked v2 scene, TileSet and PNGs; shader-free acceptance path without magenta placeholders. |
| Broad Earth | **PASS**: groundwork, source repetition and A/B/C appearance in the tested laboratory. |
| Broad Green | **PASS**: cover readability, A/B/C appearance and tile joins. |
| Native A/B/C selection | **PASS**: three valid solid-interior alternatives; no fixed distribution claim. |
| Horizontal boundaries | **PASS**: both directions and paint orders. |
| Vertical Earth-left / Green-right | **PASS**: full boundary and both endpoints, including reversed paint order, graphically accepted in the tested laboratory. |
| Vertical Green-left / Earth-right | **PASS**: full boundary and both endpoints, including reversed paint order, graphically accepted in the tested laboratory. |
| Corners/endpoints/narrow links | **PASS**: illustrated coverage; minor approved rounded stepping and corner pockets remain acceptable limitations. |
| Isolated patches | **PASS**: Green in Earth and Earth in Green. |
| Irregular regions/repainting | **PASS**: overlapping strokes, direction changes and native matching. |
| Seams/readability | **PASS**: broad appearance and smooth transitions; owner reported no odd tiles out of place. |

The historical PR #98 diagnostic endpoint failures remain part of that record.
The baked laboratory's corresponding vertical boundaries and endpoints are now
graphically accepted by the owner at the commit above. This does not establish
production chunk continuity, gameplay integration or runtime performance acceptance.
The owner's editor-responsiveness observation is qualitative; no profiling or
benchmark result is claimed. The tested implementation is unchanged by this
documentation correction. The owner will merge personally after final review;
no merge or post-merge cleanup is performed or authorized by this record.
