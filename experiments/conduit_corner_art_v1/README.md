# Rounded conduit corner artwork experiment v1

Isolated experiment on open [PR #216](https://github.com/interneth3ro/the-long-way-home/pull/216),
pending merge. On 2026-11-17 the owner reported F6 visual acceptance of all four
corner orientations, long unlit routes and corner-to-straight connections at
normal gameplay zoom. The original illuminated straights had visible seams.
One localized cyan-recess correction is now available on board 4, **pending owner
F6 acceptance**. The approved corner remains unchanged. This does not
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
| [straight_vent_00_cyan_recess_v1.png](straight_vent_00_cyan_recess_v1.png) | One candidate derived from unlit phase 00, with cyan inside one grille recess |
| [straight_vent_00_cyan_recess_v1.png.import](straight_vent_00_cyan_recess_v1.png.import) | Authored lossless/mipmap settings for the candidate |
| [conduit_corner_art_v1.tscn](conduit_corner_art_v1.tscn) | Four static comparison boards, each repeated on dirt and grass |
| [inspection_camera.gd](inspection_camera.gd) | Inspection navigation only; extends the preserved straight experiment camera |
| [README.md](README.md) | Scope, provenance, phase choices and owner inspection instructions |

The approved corner PNG is **128×128, 8-bit RGBA**, 28,381 bytes. SHA-256:

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

The original source images remain unchanged. The new correction copies unlit
phase 00 and edits only the RGB values of 182 interior pixels; see the exact
scope below. No full-image regeneration, cropping or resampling was performed.
Rotations and display scaling are scene transforms only. New import
metadata was authored as text; this amendment generated no engine UID or cache.
Owner F6-generated local import/UID metadata is preserved and excluded from the
amendment. Import settings use lossless compression, mipmaps, alpha-border fixing, no
premultiplication and no size limit. Sprite filtering is linear with mipmaps,
matching the existing experiment. The new candidate's engine import/filtering
remains unverified by the agent.

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
Terrain starts below the header. Board origins are y=0, 768, 1536 and 2304.

| Key | Board | Contents per terrain |
| --- | --- | --- |
| 1 | Four orientations | Four separate L routes, each one corner plus four straight cells on each arm; machine references below |
| 2 | Long unlit | One open spiral, 53 unlit straights and four corners; machine references below |
| 3 | Original lit comparison | Same geometry as board 2; 11 interior phase-00 cells use the original lit artwork with owner-reported seams |
| 4 | Corrected lit comparison | Same geometry and lit positions as board 3; 11 interior phase-00 cells use the new cyan-recess candidate |

There are **414 conduit sprites: 382 straights and 32 corners** across the eight
terrain panels. Board 3 has 22 original lit straights; board 4 has 22 corrected
lit straights. All original terrain/route/machine nodes on boards 1–3 remain
unchanged; only the shared controls label gains board 4 navigation.
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
No lit texture is used directly against a corner. Board 4 uses exactly the same
positions and phase ordering with its unlit-derived candidate. Board 3 retains
the original mixed-family transitions for direct comparison.

## One illuminated-straight correction attempt

### Investigation and root cause

The original `straight_lit_00.png` is not merely unlit phase 00 with cyan added:
**16,330 of 16,384 RGBA pixels differ**, including **7,646 alpha values**.
Differences cover the upper and lower rails, housing, recess and both ends.
Of the 4,096 pixels in the two 16-pixel end strips, 4,079 differ. Substituting it
into the vent sequence therefore changes geometry/silhouette and mechanical
detail at the joins. Grid positions and phase order were already correct.

### Candidate and protected pixels

Source: unchanged
[straight_vent_00.png](../conduit_art_v1/supplied_no_connectors_v1/straight_vent_00.png),
SHA-256 `92b5587491daccf97c34312ab7ba37558ce908791e736cb1312e2e5e78d761b6`.
The candidate is **128×128, 8-bit RGBA**, 23,838 bytes, SHA-256:

```text
43544daa7d8b7ffd29aea583e7fe2d4486f202f93a5d92411b72f5b4d403d819
```

One pixel-level Aseprite edit adds a steady cyan core inside the existing dark
slot at **x=58–64, y=56–81 inclusive**, using top-left source-pixel coordinates.
Exactly **182 RGB pixels** change. A tapered additive light preserves the
underlying recess texture; the slot's metal ribs, bevels, housing and pipes
are untouched. There is no glow outside that slot and no new geometry.

The entire alpha channel is identical to unlit phase 00. Every RGBA pixel outside
the 7×26 illuminated rectangle is identical, including full-height **32-pixel
end guards** (x=0–31 and x=96–127), both rails and all mechanical detail outside
the illuminated recess. No original artwork, including the old illuminated set
or the approved corner's baked cyan accent, was edited. This is the sole artwork
correction attempt; no alternate candidates or redesign iterations were made.

### Boundary validation and acceptance boundary

Both candidate edge columns match unlit phase 00 **exactly in RGBA**. The
incoming vent-03→candidate join is exact RGBA equality. The outgoing
candidate→vent-01 join has exactly the same pixel differences as the accepted
unlit-00→unlit-01 join; those original phase boundaries are not all identical.
This correction introduces **zero additional boundary differences** and retains
the 00→01→02→03 sequence in every rotated straight run.

| Join | Corrected RGB mean / maximum | Maximum alpha difference |
| --- | --- | --- |
| vent 03 → corrected 00 | 0 / 0 | 0 |
| corrected 00 → vent 01 | 4.507 / 57 | 2 |

These compare adjacent source pixels, using rows where either alpha is >=128.
Static compatibility is not artistic acceptance: the owner must judge cyan
strength, 1x readability, texture filtering and both connections in Godot.
If this single treatment is rejected, use the **unlit-only fallback** instead
of further redesign: remove illuminated straight treatments from the active
corner scene while preserving the original PR #215 artwork and the approved
corner's cyan accent. The fallback has not been applied while this candidate
awaits review. No replacement animations or lighting effects are proposed.

## Static findings and remaining visual questions

Source-pixel comparisons were performed without executing Godot:

- The master corner's **north edge matches the correctly rotated vent-02 edge
  exactly in RGBA**. Its west edge has identical visible RGB (rows where either
  alpha is at least 128). Only one RGBA pixel differs: the topmost fringe has
  alpha 0 in the corner and 3/255 in the straight.
- Other vent phases have mean visible RGB edge differences of about 23–44/255
  against the corresponding openings; original lit phases differ by about 48–65/255.
  Phase substitution is not safe to assume.
- The mixed vent-03→lit-00 and lit-00→vent-01 boundaries are not identical.
  The owner confirmed visible discontinuities during initial F6 review. The existing
  vent sequence also has nonidentical internal boundaries, as documented in
  PR #215; its 03→00 wrap matches exactly.
- The approved corner has a sweeping rail and grille-free recessed bend; the
  straight vent art contains grilles. That detail change is intentional in the
  supplied art, and the owner accepted the corner connections at normal zoom.
- Baked highlights rotate with the texture. Geometry uses only rigid rotations;
  this does not prove consistent world-space lighting. Mipmap dark seams,
  filtering artifacts, apparent gaps and 1x readability require Godot viewing.

The intentionally mixed boundaries have the following source-pixel differences
(RGB uses rows with alpha >=128 on either side; channel values are 0–255):

| Boundary in texture direction | RGB mean / maximum | Maximum alpha difference |
| --- | --- | --- |
| vent 03 → lit 00 | 44.544 / 183 | 252 |
| lit 00 → vent 01 | 68.133 / 230 | 252 |

These substantial silhouette/detail mismatches produced owner-reported visible
seams on board 3. They are recorded without altering either original artwork
family. This does not invalidate the separate vent-02 corner-edge matches.

Static validation covers PNG signature/chunk CRCs/dimensions/RGBA/source hash,
resource paths and node hierarchy, 32-unit grid registration, positive quarter
scales and four rotations, straight ordering, corner-neighbor phase/rotation,
machine reference transforms, unchanged existing files, Markdown links and Git
diff scope. Results are reported in the PR, without routine successful logs.

**The agent performed no Godot editor/game, import, headless run or graphical
verification.** The initial F6 acceptance above is owner-reported and applies
to the original corners/unlit routes, not the new correction. Static inspection
does not establish candidate engine loading, filtering or artistic acceptance. The
[execution policy](../../AGENTS.md#godot-execution-safety) is unchanged. This
experiment is outside the standing restricted test recipes.

## Exact owner F6 inspection

1. In the existing TLWH Godot project, open
   [conduit_corner_art_v1.tscn](conduit_corner_art_v1.tscn) and press **F6 / Run
   Current Scene**. F5 still opens the normal project startup scene.
2. The view starts on board 1 at **1x gameplay zoom**, using the 1280×720 logical
   viewport. Compare at the normal window size first; OS/window scaling may
   change physical screen pixels per world unit.
3. Press **4** for the corrected cyan-recess board. Compare both sides of each
   illuminated cell on dirt and grass, checking gaps, dark seams, rail/highlight
   continuity and cyan strength at 1x.
4. Press **2** for the accepted unlit baseline or **3** for the original lit
   artwork with known seams; **1** retains the accepted corner orientations.
   Each number key centers its board and resets to 1x. Board 4 has the same
   route geometry and illuminated positions as board 3.
5. **Middle-drag** pans. **Mouse wheel** uses the normal 0.5–1.5x exterior zoom
   range, 0.1 steps and 0.15-second easing. **Home** restores 1x at the current
   camera center.
6. After judging 1x, point at a connection and press **C** to center it at **4x**.
   Middle-drag remains available. C again returns to 1x at that center; the wheel
   leaves close-up and resumes gameplay zoom. Press **1/2/3/4** to restore a board.
7. **F8** stops. F6 restarts at board 1. Provide 1x screenshots and optional seam
   close-ups identifying board, terrain and corner orientation.

Owner F6 review must confirm the new board loads, both connections remain
natural and its single recessed cyan accent reads well. Accept this treatment
or choose the unlit-only fallback; static PASS alone does not settle that choice.
Production promotion and bridge development require further authorization.
