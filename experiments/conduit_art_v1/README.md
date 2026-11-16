# Straight conduit artwork comparison v1

Isolated artwork experiment on [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215),
pending merge and owner visual review. The existing Salvaged Sci-Fi v2 sprites
remain the baseline; the new Heavy Industrial v2 sprites are experimental
alternatives. **Neither this comparison nor static validation marks the artwork
owner-approved or promotes it into production.**

## Decision 105 and current comparison scope

[Issue #214, Decision 105 Option A](https://github.com/interneth3ro/the-long-way-home/issues/214)
removes individual transported-item sprites from conduit presentation. The
recess is an industrial visual feature with no item-readability target. D105
leaves logical transport, inspection and recovery rules intact; this experiment
implements none of those systems and does not modify the issue.

The owner's Heavy Industrial v2 Refined sheet (`conduits2.png`) is the artistic
target for three new treatments: **A Vent Grille**, **B Access Panel**, and
**C Illuminated Section**. All use the existing width and 32x32 logical cell.
Dark weathered metal, recessed inserts, restrained orange wear and steady cyan
replace neither the baseline nor any production art. There are no items,
orange hazard collars, prominent orange caps, animated lights, corners, adapters
or bridges.

The two baseline PNGs remain byte-for-byte identical to `0918c91`. The earlier
temporary item-readability board and wire placeholder remain removed. This
amendment adds a comparison area without moving or changing the original
terrain, conduit runs, machines, rulers or camera controls. Only the shared HUD
status text changes, with an added navigation hint.

## Owner F6 inspection

1. Open [conduit_art_v1.tscn](conduit_art_v1.tscn) in the TLWH Godot project.
2. Press **F6 / Run Current Scene**. F5 retains the normal project startup scene.
3. The scene starts at **gameplay 1x**, in the original baseline board, using the
   normal 1280x720 logical viewport.
4. **Middle-drag upward to pan down** to the clearly labeled **HEAVY INDUSTRIAL
   v2 / BASELINE COMPARISON** board, positioned 768 world units below the
   original. Several shorter drags work. The new board repeats the baseline
   beside Heavy v2, so both can be compared in one view at the same zoom.
5. Each terrain panel has paired horizontal baseline/Heavy rows, first unlit and
   then mixed cyan. The three vertical columns are **Base** (baseline mixed),
   **HI U** (Heavy unlit), and **HI C** (Heavy mixed). A/B/C swatches identify the
   three new treatments at the same gameplay scale.
6. Mouse wheel keeps the existing exterior camera's **0.5-1.5x** range,
   0.1 steps and 0.15-second easing. Compare at 1x first, then other gameplay
   zooms. Middle-drag pans freely; **F8** stops and **F6 again** resets the view.
7. Review seams, repeated panel/texture patterns, current width against machines,
   cyan frequency/brightness, and horizontal/vertical consistency. Provide a
   screenshot and choose a treatment or request revisions. No corner-art work
   or final approval follows automatically.

These are owner launch instructions. No Godot editor/game, headless import or
scene-load test was run for this amendment. The
[execution policy](../../AGENTS.md#godot-execution-safety) remains unchanged:
the standing restricted recipes do not authorize loading this experiment.
No engine verification or owner graphical acceptance is claimed.

## Contents and unchanged scale

The original board retains eight 12-cell runs: horizontal unlit/mixed and
vertical unlit/mixed on both earth and green terrain (**96 segments**).

The new board adds seven 12-cell runs per terrain (**168 segments**):
horizontal baseline unlit, Heavy unlit, baseline mixed, Heavy mixed; vertical
baseline mixed, Heavy unlit and Heavy mixed. Its Heavy unlit sequence is
`A A B A B A A B A B A B`. In each mixed run, cells **3, 7 and 11** use the
illuminated variant. Baseline and Heavy share this one-in-four accent frequency
for a direct brightness comparison. The full scene has **264 run segments**
plus six individual A/B/C swatches.

All conduit sprites are **128x128 RGBA**, scaled **0.25**, with centers exactly
32 world units apart. The three Heavy variants use the baseline alpha mask,
retaining its visible housing width (approximately 23 world units), margins
and cell registration. Heavy variants have identical outer rails, frame and
recess geometry; only their central insert pixels differ. Vertical samples
rotate the same sprites 90 degrees.

Existing Extractor and Smelter layer textures are referenced without behavior,
animation or copies of source art. Their production scales, child offsets and
128x128 four-by-four-cell footprint outlines are retained on both boards.
The only scene script is [inspection_camera.gd](inspection_camera.gd), unchanged
and limited to viewing controls inherited from the existing camera.

## Files and imports

All 13 tracked experiment files remain in this directory:

| File | Role |
| --- | --- |
| [conduit_art_v1.tscn](conduit_art_v1.tscn) | Original baseline board plus Heavy comparison below it |
| [inspection_camera.gd](inspection_camera.gd) | Unchanged viewing controls |
| [straight_unlit.png](straight_unlit.png) | Unchanged Salvaged Sci-Fi baseline |
| [straight_lit.png](straight_lit.png) | Unchanged baseline with lower-rail cyan |
| [straight_unlit.png.import](straight_unlit.png.import) | Existing baseline import settings |
| [straight_lit.png.import](straight_lit.png.import) | Existing baseline import settings |
| [heavy_v2_vent.png](heavy_v2_vent.png) | New A: recessed vent grille |
| [heavy_v2_access.png](heavy_v2_access.png) | New B: bolted access plate |
| [heavy_v2_lit.png](heavy_v2_lit.png) | New C: grille with restrained cyan inset |
| [heavy_v2_vent.png.import](heavy_v2_vent.png.import) | Matching lossless/mipmap configuration |
| [heavy_v2_access.png.import](heavy_v2_access.png.import) | Matching lossless/mipmap configuration |
| [heavy_v2_lit.png.import](heavy_v2_lit.png.import) | Matching lossless/mipmap configuration |
| [README.md](README.md) | Scope, instructions, limitations and artwork provenance |

New import sidecars follow the tracked baseline configuration: lossless
(`compress/mode=0`), mipmaps enabled, alpha-border fixing enabled,
premultiplication disabled, no size limit. Paths use their own texture path
hashes. No engine UID or cache was generated. Conduits/machines keep linear
filtering with mipmaps (`texture_filter=4`). Existing local engine-added
baseline metadata is preserved and excluded from this amendment.

Shared project resources remain referenced in place:

- Terrain: `assets/experiments/terrain_c1/sources/{earth,green}.png`, the live
  continuous-renderer sources. Both boards use the same fixed center crop and
  nominal phase scale 0.9: `2048 / (1254 x 0.9)` world units per source pixel,
  with linear filtering.
- Machines: front-facing layers under `assets/machines/{extractor,smelter}/`,
  retaining production scales/offsets.
- UI: IBM Plex Sans Regular; shared zoom behavior in
  `scenes/player/follow_camera.gd`.

## Static validation and limitations

Checks cover PNG dimensions/color type/transparency, exact common alpha masks,
all nine ordered Heavy variant boundary pairs (horizontal and 90-degree
rotation), unchanged outer-shell pixels, baseline hashes, 12-cell run lengths,
spacing/scale/rotation, illumination frequency, valid resource paths,
parent/load-step consistency, imports, Markdown links and Git diff scope.
The applicable preservation test suite and final results are reported in the PR;
routine successful check output is not committed.

Offline inspection of the packed sprites and 32-pixel tiled composites shows a
meaningful material comparison: Heavy v2 reads as enclosed recessed mechanical
panels, distinct from the baseline's open channel. It captures the reference's
gunmetal, vents, bolted plate, wear and cyan vocabulary. It is **not an exact
reproduction of the concept**: the rails have brighter continuous highlights,
the inserts are compact to fit one existing cell, and the small grille slats
and bolts lose detail at 1x. Repeated inset frames remain noticeable. The three
variants share the same shell weathering, so variation does not remove that
repetition. These are experimental candidates, not finished accepted artwork.

All Heavy boundary columns match exactly and the same illustrated rail is
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

## Heavy Industrial v2 provenance and preparation

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
