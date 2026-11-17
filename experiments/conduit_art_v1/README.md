# Straight conduit artwork comparison v1

Isolated artwork experiment on [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215),
pending merge and owner visual review. The existing Salvaged Sci-Fi v2 sprites
remain the baseline. Experimental alternatives include the Codex-generated
Heavy Industrial v2 sprites, original owner-supplied ChatGPT sequences, and new
supplied connector-free sequences.
**Neither this comparison nor static validation marks the artwork
owner-approved or promotes it into production.**

## Decision 105 and current comparison scope

[Issue #214, Decision 105 Option A](https://github.com/interneth3ro/the-long-way-home/issues/214)
removes individual transported-item sprites from conduit presentation. The
recess is an industrial visual feature with no item-readability target. D105
leaves logical transport, inspection and recovery rules intact; this experiment
implements none of those systems and does not modify the issue.

The owner's Heavy Industrial v2 Refined sheet (`conduits2.png`) is the artistic
target for the three existing Codex treatments: **A Vent Grille**, **B Access Panel**, and
**C Illuminated Section**. All use the existing width and 32x32 logical cell.
Dark weathered metal, recessed inserts, restrained orange wear and steady cyan
replace neither the baseline nor any production art. There are no items,
orange hazard collars, prominent orange caps, animated lights, corners, adapters
or bridges.

The two baseline PNGs remain byte-for-byte identical to `0918c91`. The earlier
temporary item-readability board and wire placeholder remain removed. The
connector-free amendment preserves all four earlier boards and all 13 earlier PNGs,
their local import metadata, machines, rulers and camera controls. Only two HUD
text values are updated to describe the additional comparison areas.

## Owner F6 inspection

1. Open [conduit_art_v1.tscn](conduit_art_v1.tscn) in the TLWH Godot project.
2. Press **F6 / Run Current Scene**. F5 retains the normal project startup scene.
3. The scene starts at **gameplay 1x**, in the original baseline board, using the
   normal 1280x720 logical viewport.
4. **Middle-drag upward to pan down** through the preserved boards to the new
   **CONNECTOR-FREE / UNLIT COMPARISON** at y=3072 and **CONNECTOR-FREE /
   ILLUMINATED COMPARISON** at y=3840. Several shorter drags work. Earlier
   boards remain at y=0 (baseline), 768 (Codex), 1536 (original supplied unlit)
   and 2304 (original supplied illuminated). These are world-unit offsets.
5. Each connector-free board compares three horizontal 12-cell rows:
   **Baseline**, **Original supplied**, and **Connector-free**. The vertical
   columns are **Base**, **Orig**, and **Free**. Earth and green panels repeat
   the layout with unchanged machine-scale references.
6. Both supplied sets repeat **00, 01, 02, 03** three times. Read phases left to
   right horizontally and top to bottom vertically. The four bottom swatches
   identify the new connector-free phases at 0.25 scale. Unlit boards use the
   vent sequences; illuminated boards use the lit sequences. Baseline illuminated
   references retain their occasional one-in-four accents.
7. Mouse wheel keeps the existing exterior camera's **0.5-1.5x** range,
   0.1 steps and 0.15-second easing. Compare at 1x first, then other gameplay
   zooms. Middle-drag pans freely; **F8** stops and **F6 again** resets the view.
8. Review retouched rail texture, internal joins, four-cell repetition, apparent
   width against machines, cyan coverage/brightness and rotated shading. Provide
   a screenshot and choose a treatment or request revisions. Owner-supplied does not mean owner-accepted;
   no corner-art work or final approval follows automatically.

These are owner launch instructions. No Godot editor/game, headless import or
scene-load test was run for this amendment. The
[execution policy](../../AGENTS.md#godot-execution-safety) remains unchanged:
the standing restricted recipes do not authorize loading this experiment.
No engine verification or owner graphical acceptance is claimed.

## Contents and unchanged scale

The original board retains eight 12-cell runs: horizontal unlit/mixed and
vertical unlit/mixed on both earth and green terrain (**96 segments**).

The Codex Heavy v2 board adds seven 12-cell runs per terrain (**168 segments**):
horizontal baseline unlit, Heavy unlit, baseline mixed, Heavy mixed; vertical
baseline mixed, Heavy unlit and Heavy mixed. Its Heavy unlit sequence is
`A A B A B A A B A B A B`. In each mixed run, cells **3, 7 and 11** use the
illuminated variant. Baseline and Heavy share this one-in-four accent frequency
for a direct brightness comparison on that board.

The two original supplied-art boards each add six 12-cell runs per terrain: horizontal
and vertical baseline, Codex, and supplied sequences. That adds **288 segments**,
including **96 original supplied-art segments**, and 16 phase swatches.

The new connector-free boards add another **288 segments**: 96 connector-free,
96 original supplied and 96 baseline reference cells, across horizontal/vertical
runs on both terrain materials. They add 16 connector-free phase swatches.
The complete six-board scene has **840 run segments** plus **38 swatches**.

All conduit sprites are **128x128 RGBA**, scaled **0.25**, with centers exactly
32 world units apart. The three Codex Heavy variants use the baseline alpha mask,
retaining its visible housing width (approximately 23 world units), margins
and cell registration. Codex Heavy variants have identical outer rails, frame and
recess geometry; only their central insert pixels differ. Vertical samples
rotate the same sprites 90 degrees clockwise. The supplied tiles retain their
own alpha masks and visibly fill more of the cell; see the measurements below.

Existing Extractor and Smelter layer textures are referenced without behavior,
animation or copies of source art. Their production scales, child offsets and
128x128 four-by-four-cell footprint outlines are retained on all six boards.
The only scene script is [inspection_camera.gd](inspection_camera.gd), unchanged
and limited to viewing controls inherited from the existing camera.

## Files and imports

All 45 tracked experiment files remain in this directory and the
supplied_heavy_v2 and supplied_no_connectors_v1 subdirectories. Root files:

| File | Role |
| --- | --- |
| [conduit_art_v1.tscn](conduit_art_v1.tscn) | Preserved boards plus original/connector-free comparisons |
| [inspection_camera.gd](inspection_camera.gd) | Unchanged viewing controls |
| [straight_unlit.png](straight_unlit.png) | Unchanged Salvaged Sci-Fi baseline |
| [straight_lit.png](straight_lit.png) | Unchanged baseline with lower-rail cyan |
| [straight_unlit.png.import](straight_unlit.png.import) | Existing baseline import settings |
| [straight_lit.png.import](straight_lit.png.import) | Existing baseline import settings |
| [heavy_v2_vent.png](heavy_v2_vent.png) | Preserved Codex A: recessed vent grille |
| [heavy_v2_access.png](heavy_v2_access.png) | Preserved Codex B: bolted access plate |
| [heavy_v2_lit.png](heavy_v2_lit.png) | Preserved Codex C: grille with restrained cyan inset |
| [heavy_v2_vent.png.import](heavy_v2_vent.png.import) | Matching lossless/mipmap configuration |
| [heavy_v2_access.png.import](heavy_v2_access.png.import) | Matching lossless/mipmap configuration |
| [heavy_v2_lit.png.import](heavy_v2_lit.png.import) | Matching lossless/mipmap configuration |
| [README.md](README.md) | Scope, instructions, limitations and artwork provenance |

The earlier supplied-art amendment added these eight unchanged PNGs and eight
matching import sidecars under [supplied_heavy_v2](supplied_heavy_v2/):

| Phase | Unlit sequence | Illuminated sequence |
| --- | --- | --- |
| 00 | [straight_vent_00.png](supplied_heavy_v2/straight_vent_00.png) / [import](supplied_heavy_v2/straight_vent_00.png.import) | [straight_lit_00.png](supplied_heavy_v2/straight_lit_00.png) / [import](supplied_heavy_v2/straight_lit_00.png.import) |
| 01 | [straight_vent_01.png](supplied_heavy_v2/straight_vent_01.png) / [import](supplied_heavy_v2/straight_vent_01.png.import) | [straight_lit_01.png](supplied_heavy_v2/straight_lit_01.png) / [import](supplied_heavy_v2/straight_lit_01.png.import) |
| 02 | [straight_vent_02.png](supplied_heavy_v2/straight_vent_02.png) / [import](supplied_heavy_v2/straight_vent_02.png.import) | [straight_lit_02.png](supplied_heavy_v2/straight_lit_02.png) / [import](supplied_heavy_v2/straight_lit_02.png.import) |
| 03 | [straight_vent_03.png](supplied_heavy_v2/straight_vent_03.png) / [import](supplied_heavy_v2/straight_vent_03.png.import) | [straight_lit_03.png](supplied_heavy_v2/straight_lit_03.png) / [import](supplied_heavy_v2/straight_lit_03.png.import) |

The connector-free amendment adds eight PNGs and eight matching import sidecars
under [supplied_no_connectors_v1](supplied_no_connectors_v1/):

| Phase | Connector-free vent | Connector-free illuminated |
| --- | --- | --- |
| 00 | [straight_vent_00.png](supplied_no_connectors_v1/straight_vent_00.png) / [import](supplied_no_connectors_v1/straight_vent_00.png.import) | [straight_lit_00.png](supplied_no_connectors_v1/straight_lit_00.png) / [import](supplied_no_connectors_v1/straight_lit_00.png.import) |
| 01 | [straight_vent_01.png](supplied_no_connectors_v1/straight_vent_01.png) / [import](supplied_no_connectors_v1/straight_vent_01.png.import) | [straight_lit_01.png](supplied_no_connectors_v1/straight_lit_01.png) / [import](supplied_no_connectors_v1/straight_lit_01.png.import) |
| 02 | [straight_vent_02.png](supplied_no_connectors_v1/straight_vent_02.png) / [import](supplied_no_connectors_v1/straight_vent_02.png.import) | [straight_lit_02.png](supplied_no_connectors_v1/straight_lit_02.png) / [import](supplied_no_connectors_v1/straight_lit_02.png.import) |
| 03 | [straight_vent_03.png](supplied_no_connectors_v1/straight_vent_03.png) / [import](supplied_no_connectors_v1/straight_vent_03.png.import) | [straight_lit_03.png](supplied_no_connectors_v1/straight_lit_03.png) / [import](supplied_no_connectors_v1/straight_lit_03.png.import) |

New import sidecars follow the tracked baseline configuration: lossless
(`compress/mode=0`), mipmaps enabled, alpha-border fixing enabled,
premultiplication disabled, no size limit. Paths use their own texture path
hashes. No engine UID or cache was generated. Conduits/machines keep linear
filtering with mipmaps (`texture_filter=4`). Existing local engine-added
metadata for all earlier candidate sets is preserved and excluded from this
amendment.

Shared project resources remain referenced in place:

- Terrain: `assets/experiments/terrain_c1/sources/{earth,green}.png`, the live
  continuous-renderer sources. All boards use the same fixed center crop and
  nominal phase scale 0.9: `2048 / (1254 x 0.9)` world units per source pixel,
  with linear filtering.
- Machines: front-facing layers under `assets/machines/{extractor,smelter}/`,
  retaining production scales/offsets.
- UI: IBM Plex Sans Regular; shared zoom behavior in
  `scenes/player/follow_camera.gd`.

## Static validation and limitations

Checks cover PNG dimensions/color type/transparency, exact common alpha masks,
all nine ordered Codex Heavy variant boundary pairs and the ordered sequence
joins of both supplied sets (horizontal and clockwise rotation), unchanged source bytes, existing
candidate hashes, 12-cell run lengths and exact 00-03 sequence ordering,
spacing/scale/rotation, illumination frequency, valid resource paths,
parent/load-step consistency, imports, Markdown links and Git diff scope.
The applicable preservation test suite and final results are reported in the PR;
routine successful check output is not committed.

For the existing Codex candidates, offline inspection of the packed sprites and 32-pixel tiled composites shows a
meaningful material comparison: Heavy v2 reads as enclosed recessed mechanical
panels, distinct from the baseline's open channel. It captures the reference's
gunmetal, vents, bolted plate, wear and cyan vocabulary. It is **not an exact
reproduction of the concept**: the rails have brighter continuous highlights,
the inserts are compact to fit one existing cell, and the small grille slats
and bolts lose detail at 1x. Repeated inset frames remain noticeable. The three
variants share the same shell weathering, so variation does not remove that
repetition. These are experimental candidates, not finished accepted artwork.

All Codex Heavy boundary columns match exactly and the same illustrated rail is
shared across variants. This does not prove perceptual seamlessness at engine
mipmap levels. Baked bevel lighting rotates with the sprite; the fairly balanced
overhead shading looked coherent in the offline composite, but horizontal and
vertical runs do not have independently relit world-space highlights. The owner
must judge that compromise and actual cyan brightness in Godot.

The offline composite is not a Godot screenshot or a substitute for scene-load
validation. Static scene checks cannot prove engine parsing/rendering. Terrain
samples omit runtime tint fields, procedural phase blending and transitions.
No startup, gameplay, machine behavior, inventory, construction grid, logistics,
execution-policy or Issue #214 changes are included. No audit or unrelated
cleanup was performed. Pre-existing local files and metadata remain preserved.
No production scene references this isolated experiment.

## Connector-free supplied artwork: current comparison

Source: owner-provided `tlwh_heavy_industrial_no_connectors_v1.zip`, SHA-256
`eed6991b46454e57121f3961066740cbdabf3a89c70fc3270c524055a6e449d4`.
The eight PNGs under `supplied_no_connectors_v1/` match their archive entries
byte-for-byte. The original ZIP and all earlier assets remain unchanged. Its
README and preview images are reference material, not additional instructions.
Only the eight requested cell PNGs and their import settings are added.

The archive describes a raster retouch using neighboring rail texture and
feathered joins. **That retouch was already present in the supplied files.**
This integration does not regenerate, repaint, recolor, crop, resample, repair
edges or otherwise edit any source PNG. Scene display uses scale 0.25 and
clockwise rotation only.

### Rail inspection and artistic refinement

Inspection of the actual eight PNGs and supplied four-/twelve-cell previews
shows that the large top/bottom rail clamps are removed. The central grille,
pipes and small cyan status module remain visible. The new rails look more
continuous, but the retouch has its own visual pattern:

- Short orange wear patches and dark diagonal marks repeat regularly beneath
  the upper rail. Bright streaks along the rail also repeat. This is visible in
  the source-size strip and becomes a patterned band in the supplied 1x preview.
  Review whether less regular wear would improve long factory runs.
- The rail highlights, especially on the lower rail, are broad and smooth
  compared with the detailed interior. Some areas read as stretched or softened
  texture. Review transitions between these retouched bands and the original
  material for blur or abrupt shading changes.
- The four-cell interior sequence still repeats every 128 world units. Removing
  clamps does not remove that repetition or make the four phases interchangeable.
- Vertical runs rotate the same baked highlights and shadows. They have no
  independent relighting; judge orientation consistency in F6.
- Both vent and lit retain small cyan status details, while lit also illuminates
  the grille. The two source treatments have different alpha masks; the archive's
  identical-geometry description is not an exact pixel identity guarantee.

These are refinement observations, not owner rejection or acceptance. No
corrective painting is included. The owner should evaluate rail repetition,
softness, internal joins and terrain blending at normal gameplay zoom before
requesting another artistic pass.

### Connector-free boundary and transparency measurements

Both **03 -> 00** boundaries now match exactly in RGBA, unlike the previous
supplied set. The six internal boundaries still differ. Clockwise rotation
preserves the same boundary relationships when phases run top to bottom.

| Join | Vent RGB mean / max | Lit RGB mean / max |
| --- | --- | --- |
| 00 -> 01 | 4.507 / 57 | 8.129 / 70 |
| 01 -> 02 | 7.481 / 64 | 6.209 / 53 |
| 02 -> 03 | 7.029 / 53 | 9.410 / 68 |
| 03 -> 00 | 0 / 0 | 0 / 0 |

RGB differences use rows with alpha >=128 on either side, in 0-255 channel
units. Maximum alpha differences at internal joins are 10/255 for vent and
4/255 for lit. The 01-to-02 differences are lower than the earlier supplied
version; other internal transitions still need review. Nonidentical adjacent
texture pixels do not by themselves prove visible gaps, and an exact wrap does
not certify perceptual seamlessness under Godot mipmaps.

All eight files are 128x128, 8-bit RGBA, with valid PNG chunk CRCs. Vent has
108-128 fully transparent pixels per tile; lit has 248-381. Median per-column
width covered by alpha >=128 at scale 0.25 is 31.25-31.75 world units for vent
and 30.25 for lit. This remains approximately the earlier supplied silhouette
and wider than the old baseline/Codex silhouettes (22.5 world units by that
measure). All samples still occupy the unchanged 32x32 logical construction
cell. No final width recommendation or approval is implied.

Source alpha values differ from the earlier supplied images and between vent
and lit. Separate unlit and illuminated boards make those source differences
reviewable; mixed same-phase substitution is not being certified. Godot import,
scene loading, mipmap seams and rendered visual acceptance remain unverified
under the existing execution policy.

## Original supplied ChatGPT artwork: provenance and limitations

Source: owner-provided `tlwh_heavy_industrial_straight_v2.zip`, SHA-256
`d17f8e4c0bc70168c51a84068f24ddfb2502c268cfa7e1e0223c41f0f7a94c20`.
Only the eight requested cell PNGs were extracted into the experiment. Each
matches its archive entry byte-for-byte, including the muted metal rail
connectors. The original ZIP remains unchanged. Its README and four preview
PNGs remain in the archive as reference material; they are not scene assets
or additional task instructions.

There was **no redesign, regeneration, recoloring, masking, cropping, resampling,
edge repair or connector edit** to these PNGs. The archive README describes them
as concept-image crops/resampling; that is supplied provenance, not a newly
performed authoring step. They are 128x128, 8-bit RGBA. PNG chunk checks found
only IHDR, IDAT and IEND, and verified their CRCs.

These are consecutive sections of two four-cell strips, **not interchangeable
single-cell variants**. Runs repeat 00-01-02-03, with centers 32 units apart and
scale 0.25. Clockwise 90-degree sprite rotation and top-to-bottom phase ordering
are equivalent to rotating the assembled horizontal strip. The source images
are never rotated or rewritten on disk.

### Boundary measurements

The supplied boundaries are **not pixel-exact**, including the repeating
03-to-00 boundary, despite the archive README's claim of matching outer pixels.
The table reports mean/max RGB component differences at each adjoining column,
using rows with alpha at least 128 on either side (0-255 channel units).
The same differences apply to the rotated joins.

| Join | Vent mean / max | Lit mean / max |
| --- | --- | --- |
| 00 -> 01 | 3.499 / 57 | 7.730 / 70 |
| 01 -> 02 | 14.722 / 112 | 15.402 / 119 |
| 02 -> 03 | 6.253 / 40 | 8.601 / 104 |
| 03 -> 00 | 4.997 / 20 | 1.353 / 12 |

Alpha boundary differences are small (maximum 10/255 for vent and 5/255 for lit).
Adjacent illustrated columns can differ naturally; these measurements flag
joins for F6 inspection rather than proving a visible gap or seamlessness.
The larger 01-to-02 transition and four-cell wrap deserve particular attention.
No source pixels were changed to force a PASS.

### Visual review points

- **Apparent width:** at scale 0.25, the median per-column span of pixels with
  alpha >=128 is 31.25-31.75 world units for vent and 30.25-30.5 for lit, versus
  22.5 for both existing candidate sets. This is a source-silhouette difference;
  all samples still use the same 32x32 logical cell. No dimensions are being
  recommended or accepted.
- **Transparency:** each supplied tile has genuine transparent pixels, but far
  fewer than the existing sprites: 108-128 fully transparent pixels for vent
  and 228-405 for lit, versus 4,532. The narrow, slightly irregular margins and
  partially transparent edge pixels may affect terrain blending.
- **Unlit/lit geometry:** corresponding phases have different alpha values and
  slightly different silhouettes/shading. The two supplied sequences are shown
  separately; this experiment does not establish seamless phase-matched
  unlit/lit substitution.
- **Connectors:** the substantial muted metal connector remains exactly as
  supplied and repeats every four cells (128 world units). It is visually
  prominent; acceptance of that repetition remains with the owner.
- **Cyan:** the supplied vent sequence already contains small cyan status
  details; its label follows the archive naming. The lit strip illuminates
  broader grille areas. Its cyan coverage is not normalized to the older
  candidates' one-in-four accent treatment.
- **Rotated shading:** all baked highlights/shadows rotate with the strip.
  There is no independently relit vertical asset. Horizontal/vertical consistency,
  perceptual seams and Godot mipmap/filter behavior remain for F6 review.

## Codex Heavy Industrial v2 provenance and preparation

The built-in **imagegen** tool generated A from the supplied Heavy Industrial
concept as its artistic reference and the unchanged baseline sprite as a
geometry guide. Separate imagegen edits of A produced B and C. No CLI/API
fallback, flat procedural placeholder art, historical-project assets or
replacement item art was used.

The three generated working canvases are 1774x887. For final packing, their
illustrated horizontal band at `(0,160)`, size `1774x564`, was bicubically
resampled into `(0,18)`, size `128x92`, on a 128x128 canvas. This compresses
the long generated insert to the existing single-cell length; it does not
widen the conduit. The baseline alpha mask fixes the established silhouette
and transparent margins for every new variant.

A smooth eight-column edge blend brings the vent sprite's left/right columns
to their shared mean RGBA profile. B/C retain that exact shell and alpha, with
only an interior patch at `x=32..95, y=47..81`, feathered over three pixels,
taken from their corresponding generated edits. This makes the variants
interchangeable without relying on the generator to preserve exact pixels.
System.Drawing performed only this deterministic packing, downsampling,
masking and edge/insert compositing; the illustrated details came from imagegen.

Only the final three new PNGs and import settings are committed. The owner
reference and full generated canvases remain at their original local paths;
none was overwritten or deleted. The exact Heavy prompt set follows.

### A. Vent Grille

```text
Use case: stylized-concept / reference-derived game sprite.
Asset: ONE Heavy Industrial v2 straight conduit tile, variant A Vent Grille, true transparent PNG. Image 1 is the owner's Heavy Industrial v2 refined artistic target: match its dark layered metal, beveled gunmetal highlights, subtle bolts, weathering and recessed narrow-slot grille. Image 2 is ONLY the existing sprite's exact geometry/width/margin guide, not its material design. Keep image 2's horizontal silhouette, uninterrupted side rails and recessed interior proportions. Square canvas, horizontal conduit continues through both left and right boundaries. Occupied band begins near 14% and ends near 86% canvas height; transparent above/below. No perspective convergence. No visible ends.
Create richly illustrated mechanical detail like the lower-left vent swatch of image 1: one shallow recessed dark vent grille in the center with slim closely spaced vertical slats, substantial armored metal housing and layered framing. Grille lies wholly between the two continuous side rails. Very few small fasteners, sparse subtle orange paint chips, dark weathered steel. No large transverse collars, no orange corner caps, no hazard stripes, no items, no cyan anywhere, no text, no ground, no frame.
Tile compatibility: absolutely straight parallel external rails, identical rail cross-sections at x=0 and x=last; a quiet dark continuation zone near both side edges, no seam/end fitting. Keep the central insert within the middle 60% of length and the existing recessed channel width. All illustration and texture should have convincing depth, not flat shapes or basic gradients.
Lighting: soft neutral overhead ambient with nearly symmetric top/bottom bevel illumination, very short local recess shadows, no lateral light gradient or long cast shadows. It must remain convincing when rotated 90 degrees. The result is a high-fidelity candidate to be downsampled to 128x128 and displayed in a 32x32 cell. Preserve generous detail but avoid noisy high-contrast grunge. Deliver only this one transparent tile.
```

### B. Access Panel

```text
Use case: precise-object-edit. Edit target: supplied Heavy Industrial vent conduit sprite. Create variant B Access Panel. Change ONLY the central grille insert between the two continuous rails. Replace its slatted opening with a recessed armored gunmetal access plate, subtle layered bevels, six small inset bolts, fine machined seams and restrained orange chips, matching the owner's Heavy Industrial reference. No lettering or symbols. Keep the outer frame, both rails, material weathering outside the insert, alpha silhouette, image dimensions and boundary profiles EXACTLY the same. Keep the insert's surrounding rectangular mounting frame. No new outer fittings or end caps, no hazard stripes, no cyan, no transported items. Same soft neutral overhead lighting; no new directional shadows. Detailed illustrated metal, never flat placeholder shapes. Preserve transparent background. Output only this one matching sprite.
```

### C. Illuminated Section

```text
Use case: precise-object-edit. Edit target: the supplied Heavy Industrial vent conduit sprite. Create variant C Illuminated Section. Change ONLY the central grille insert between the two continuous rails. Keep a dark recessed mechanical inset with fine grille detail, but add one narrow steady cyan luminous bar across its center, occupying about one quarter of the full tile length. Subtle turquoise glass, a modest bright cyan core, very tight subdued local glow. No bloom outside the insert, no white-hot flare, no traveling light. All other materials stay neutral gunmetal. Keep the outer frame, both rails, weathering outside the insert, alpha silhouette, image dimensions and boundary profiles EXACTLY the same. Keep the insert's rectangular mounting frame and its two small side fasteners. No new end fittings, hazard stripes, orange caps, text or transported items. Same detailed illustrated weathered metal and soft neutral overhead lighting. Preserve the transparent background. Output only this one matching sprite.
```

## Salvaged Sci-Fi v2 provenance (unchanged baseline)

Built-in imagegen produced the candidate artwork using the supplied
`conduit_tiling.png` as a visual reference. These are newly generated derivatives,
not lossless extractions of the concept swatches and not placeholder geometry.

The generated square canvases were 1254×1254. A centered 768×768 region at
(243, 243) was downsampled to 128×128. An eight-pixel blend at each horizontal
edge brings both boundary columns to their shared mean profile. The illuminated
candidate retains the exact unlit base and alpha, with only a feathered lower-rail
patch inside x=43..84, y=92..105 taken from the final generated illuminated
variant. This preserves geometry and mixed-variant joins.

Only the final two PNGs are committed. The owner's original sheet and generated
working canvases remain outside the experiment; no existing artwork was
overwritten. The exact generation prompts follow.

### 1. Unlit candidate

```text
Use case: stylized-concept. Asset type: transparent seamless horizontal straight item conduit sprite for the 2D game The Long Way Home. Reference image: owner-approved concept sheet; use ONLY the Standard (Unlit) swatch on the right as the material/geometry target, no other sheet elements. Create ONE square tile (prefer 128 x 128; if higher resolution maintain exact square layout), genuine transparent background. Horizontal run from left image boundary to right image boundary, no end fittings or end caps; both rails and recessed channel continue perfectly straight off BOTH side boundaries and repeat seamlessly. Top-down/angled-overhead illustrated weathered gunmetal, wide empty recessed dark open central trough, two parallel continuous gray side rails with subtle sparse orange paint wear. No orange corner caps, no vertical cross-straps, no heavy end panels, no transverse seams. Occupy the full image width; total conduit width across y about 72% of square, centered vertically with transparent margins top and bottom. Central channel at least 45% of square height, rails relatively narrow. Uniform soft neutral overhead lighting without a left-to-right brightness gradient. All profiles/shading at x=0 must match x=last pixel. No transported items, no cyan anywhere, no illumination, no ground, no shadow outside silhouette, no grid, no text, no board, no frame. This is a production-style candidate sprite, not a mockup or diagram.
```

### 2. Illuminated edit

```text
Use case: precise-object-edit. Edit target: the supplied unlit conduit sprite. Produce the illuminated variant of this exact sprite. Change ONLY a small central portion of the LOWER rail: inset one restrained horizontal cyan status light, approximately 14% of image width and 1.2% image height, with a dark gunmetal bezel and very localized subtle glow confined to the rail. Keep ALL other pixels, geometry, rails, recess, orange wear, dimensions, transparency and left/right edges unchanged. No other cyan, no bloom across channel, no extra fittings, no perspective changes, no text. Preserve genuine transparency. The variant must tile with the original seamlessly in any sequence.
```

### 3. Illumination refinement

```text
Use case: precise-object-edit. Edit target: this exact illuminated conduit texture. Change ONLY the cyan light on the lower rail. Keep its horizontal center at x=627 and vertical center at y=830 in this 1254x1254 image. Make its cyan luminous core about 160 pixels wide and 32 pixels tall, with rounded ends and a subtle dark metal bezel. This must survive downsampling to a 128x128 sprite and display at 32x32 world pixels. Restrained cyan, not white, no wide bloom. Keep every other part of the image unchanged: exact rail/channel geometry, weathering, transparent margins, left/right edges, framing and image size. No other objects, no text.
```
