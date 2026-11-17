# Rounded conduit corner artwork experiment v1

Isolated feature-branch experiment, pending merge and owner F6 review. The owner
approved **Heavy Industrial v2 — Grille-Free Rounded Corner v1** as the source
artwork; approval of its joins in this scene remains pending. This does not
promote assets to production or implement logistics, construction, recovery,
inventory, machine behavior, adapters or bridges.

Design reference: [Issue #214, Decisions 1–105](https://github.com/interneth3ro/the-long-way-home/issues/214),
especially D9/D10 (one ordinary 32×32 cell), D84 (no separate corner inventory
item), and D105 (no visible transported items). The preferred straight textures
come from merged [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215)
and its [existing experiment](../conduit_art_v1/README.md).
That experiment, its earlier candidates and the simpler Codex Heavy Industrial
fallback are unchanged. Historical “pending merge” wording in those references
is preserved; GitHub confirms PR #215 merged at `0c1c3447a45efa869335ad1f3451bdf112a08a1a`.
Issue #214 is unchanged. No repository-wide logistics audit was undertaken.

## Files and source preservation

| File | Purpose |
| --- | --- |
| [tlwh_corner_grille_free_128_v1.png](tlwh_corner_grille_free_128_v1.png) | Original owner-supplied master corner, unchanged bytes |
| [tlwh_corner_grille_free_128_v1.png.import](tlwh_corner_grille_free_128_v1.png.import) | Authored lossless/mipmap import settings matching the straight experiment |
| [conduit_corner_art_v1.tscn](conduit_corner_art_v1.tscn) | Three static comparison boards, each repeated on dirt and grass |
| [inspection_camera.gd](inspection_camera.gd) | Inspection navigation only; extends the preserved straight experiment camera |
| [README.md](README.md) | Scope, provenance, phase choices and owner inspection instructions |

The PNG is **128×128, 8-bit RGBA**, 28,381 bytes. SHA-256:

```text
8f6fd4b3f05cd0228312e80fdf44134c5760db7f8b9614ac0c780276f6d7d071
```

The supplied connected preview, `tlwh_corner_grille_free_connected_v1.png`, is
reference material only. It remains outside the repository, unchanged: 640×640
RGBA, 126,288 bytes, SHA-256
`b2269cc9799a94e97349162b04bdb99e9b57f4dd8ebfd979945a3bbc70aa05b6`.
Its four straight cells reproduce **vent phase 02 repeatedly**, not the approved
four-phase sequence. The scene therefore uses the preview to identify the join,
not as a template for repeated straight artwork.

No source image was generated, repainted, recolored, cropped, resampled, masked
or repaired. Rotations and display scaling are scene transforms only. Import
metadata was authored as text; no engine UID or cache was generated. Import
settings use lossless compression, mipmaps, alpha-border fixing, no
premultiplication and no size limit. Sprite filtering is linear with mipmaps,
matching the existing experiment. Actual import/filtering remains unverified.

Shared textures are referenced directly:

- [Connector-free straight sequences](../conduit_art_v1/supplied_no_connectors_v1/),
  vent phases 00–03 and occasional illuminated phase 00.
- Terrain: [earth](../../assets/experiments/terrain_c1/sources/earth.png) and
  [green](../../assets/experiments/terrain_c1/sources/green.png), with the same
  nominal phase scale 0.9 and fixed center sampling as PR #215.
- Existing front-facing Extractor and Smelter layers, with the original sprite
  scales/offsets and 128×128 four-cell-by-four-cell reference outlines. These are
  artwork nodes only, with no machine scripts or attached conduits.
- IBM Plex Sans Regular and the existing inspection/gameplay camera chain.

## Scene layout and registration

Each board is 1280×720 logical units: dirt on the left, grass on the right.
Terrain starts below the header. Board origins are y=0, 768 and 1536.

| Key | Board | Contents per terrain |
| --- | --- | --- |
| 1 | Four orientations | Four separate L routes, each one corner plus four straight cells on each arm; machine references below |
| 2 | Long unlit | One open spiral, 53 unlit straights and four corners; machine references below |
| 3 | Long mixed | Same geometry as board 2; 11 interior phase-00 cells use steady illuminated artwork |

There are **300 conduit sprites: 276 straights and 24 corners** across the six
terrain panels. The 22 illuminated straight sprites occur only on board 3.
The corner's own small cyan light is part of the approved image and remains
visible on every board; “unlit” describes straight segments. There is no animated
lighting, transported item sprite, transport effect or simulation.

All conduit sprites are centered, scale `(0.25, 0.25)`, with no flip, offset or
negative scale. Their 128×128 bounds cover exactly one 32×32 cell. World centers
are `(32*x + 16, 32*y + 16)`; terrain/board translations are multiples of 32.
One corner texture serves all four clockwise rotations:

| Rotation | Connected sides |
| --- | --- |
| 0° | West + North |
| 90° | North + East |
| 180° | East + South |
| 270° | South + West |

Long-route vertices, in panel-local cell coordinates, are
`(1,5) → (17,5) → (17,15) → (3,15) → (3,9) → (13,9)`.
This is an open route, not a closed loop, crossing or connection to a machine.
Its four turns are 270°, 0°, 90°, 180° in that order. The repeated turn direction
keeps the asymmetric orange/rail side consistent; opposite-turn S routes are
not certified by this experiment.

## Straight phases at the corner

**Both openings use unlit vent phase 02.** For the 0° master corner:

- The western straight is unrotated; its right edge meets the corner's left edge.
- The northern straight is rotated **270° clockwise**; its bottom edge is the
  original straight's left column. A 90° rotation puts the asymmetric rails on
  the wrong side. Apply the same additional quarter-turn to the corner and its
  two neighbors for the other orientations; no mirroring is used.

Each uninterrupted straight run follows **00 → 01 → 02 → 03 → repeat in its
texture's local +X direction**, rotated with the sprite. This need not be screen
left-to-right or top-to-bottom. At the base L, the west arm reads `03,00,01,02`
toward the corner; the north arm reads `02,03,00,01` away from it. Rotation
preserves those relationships.

Corners are not extra straight phases: phase anchoring restarts at each arm.
The long route has 9, 13 and 5 straight cells between successive corners,
allowing phase 02 at both ends while retaining the four-phase order. This is an
authored comparison layout, not an automatic phase-selection or routing system.
It does not establish compatibility for arbitrary route lengths or S bends.

Board 3 substitutes lit 00 only at occasional interior vent-00 positions,
leaving at least two unlit straight cells between each light and a corner.
No lit texture is used directly against a corner. These mixed-family transitions
are intentional inspection cases, not claims of interchangeable geometry.

## Static findings and remaining visual questions

Source-pixel comparisons were performed without executing Godot:

- The master corner's **north edge matches the correctly rotated vent-02 edge
  exactly in RGBA**. Its west edge has identical visible RGB (rows where either
  alpha is at least 128). Only one RGBA pixel differs: the topmost fringe has
  alpha 0 in the corner and 3/255 in the straight.
- Other vent phases have mean visible RGB edge differences of about 23–44/255
  against the corresponding openings; lit phases differ by about 48–65/255.
  Phase substitution is not safe to assume.
- The mixed vent-03→lit-00 and lit-00→vent-01 boundaries are not identical.
  Both silhouette and mechanical-detail changes need owner review. The existing
  vent sequence also has nonidentical internal boundaries, as documented in
  PR #215; its 03→00 wrap matches exactly.
- The approved corner has a sweeping rail and grille-free recessed bend; the
  straight vent art contains grilles. That detail change is intentional in the
  supplied art, but its visual abruptness remains an owner judgment.
- Baked highlights rotate with the texture. Geometry uses only rigid rotations;
  this does not prove consistent world-space lighting. Mipmap dark seams,
  filtering artifacts, apparent gaps and 1x readability require Godot viewing.

The intentionally mixed boundaries have the following source-pixel differences
(RGB uses rows with alpha >=128 on either side; channel values are 0–255):

| Boundary in texture direction | RGB mean / maximum | Maximum alpha difference |
| --- | --- | --- |
| vent 03 → lit 00 | 44.544 / 183 | 252 |
| lit 00 → vent 01 | 68.133 / 230 | 252 |

These are substantial silhouette/detail mismatches and may produce visible
steps or seams on board 3. They are reported without altering either artwork
family. This does not invalidate the separate vent-02 corner-edge matches.

Static validation covers PNG signature/chunk CRCs/dimensions/RGBA/source hash,
resource paths and node hierarchy, 32-unit grid registration, positive quarter
scales and four rotations, straight ordering, corner-neighbor phase/rotation,
machine reference transforms, unchanged existing files, Markdown links and Git
diff scope. Results are reported in the PR, without routine successful logs.

**No Godot editor, game, import, headless run or graphical verification was
performed.** Static inspection does not establish engine parsing, successful
loading, rendered seamlessness or owner acceptance. The
[execution policy](../../AGENTS.md#godot-execution-safety) is unchanged. This
experiment is outside the standing restricted test recipes.

## Exact owner F6 inspection

1. In the existing TLWH Godot project, open
   [conduit_corner_art_v1.tscn](conduit_corner_art_v1.tscn) and press **F6 / Run
   Current Scene**. F5 still opens the normal project startup scene.
2. The view starts on board 1 at **1x gameplay zoom**, using the 1280×720 logical
   viewport. Compare at the normal window size first; OS/window scaling may
   change physical screen pixels per world unit.
3. Inspect both openings of all four L routes on dirt and grass. Prioritize
   gaps, dark seams, rail/highlight continuity and the grille-to-bend transition.
4. Press **2** for the long unlit route, then **3** for the identical mixed route.
   Each number key centers its board and resets to 1x. Compare repetition and
   machine scale; scrutinize both sides of every lit straight cell.
5. **Middle-drag** pans. **Mouse wheel** uses the normal 0.5–1.5x exterior zoom
   range, 0.1 steps and 0.15-second easing. **Home** restores 1x at the current
   camera center.
6. After judging 1x, point at a connection and press **C** to center it at **4x**.
   Middle-drag remains available. C again returns to 1x at that center; the wheel
   leaves close-up and resumes gameplay zoom. Press **1/2/3** to restore a board.
7. **F8** stops. F6 restarts at board 1. Provide 1x screenshots and optional seam
   close-ups identifying board, terrain and corner orientation.

Owner F6 review must confirm scene loading, camera controls, both connection
edges, rotated shading and readability. Any required tiling correction should
be reported for explicit artwork authorization; the approved PNG remains intact.
Production promotion and bridge development require further authorization.
