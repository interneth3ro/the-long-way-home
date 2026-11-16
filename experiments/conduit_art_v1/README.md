# Straight conduit artwork tiling experiment v1

Feature-branch experiment, pending merge and owner visual acceptance. These are
**candidate illustrations, not approved production assets**. The owner-supplied
Salvaged Sci-Fi v2 concept sheet is the visual reference; the written task limits
this experiment to straight segments. Its depicted adapters, corners, bridges and
machine connections are not implemented.

The canonical design remains [Issue #214](https://github.com/interneth3ro/the-long-way-home/issues/214),
especially D10 (one 32Ã—32 cell; narrower artwork allowed), D87/D90 (visible items
and an unresolved item envelope), and D91 (future foreground layering).
The issue is unchanged.

## Launch for owner inspection

1. In the TLWH Godot project, open
   [conduit_art_v1.tscn](conduit_art_v1.tscn).
2. Use **F6 / Run Current Scene**, not F5 / Run Project.
3. The initial camera is **1Ã—**, in the normal 1280Ã—720 logical viewport.
   Mouse wheel uses the existing exterior camera's 0.5â€“1.5Ã— limits, 0.1 steps and
   0.15-second easing. Middle-drag pans this inspection camera.
4. Use **F8** to stop; rerun F6 to restore the initial view.

These are owner launch instructions, not a record of agent execution. No editor,
engine import, scene-load run, headless test or graphical Godot launch was
performed. The standing restricted recipes do not cover loading this experiment.
The [execution policy](../../AGENTS.md#godot-execution-safety) remains unchanged.
First owner import may create ordinary local engine caches/UID metadata; none is
included in this PR.

## Scene contents and scale

The two panels show the same arrangement over the current exterior renderer's
existing earth and green source artwork. Each has:

- A horizontal unlit run and a horizontal mixed run, each 12 cells long.
- A vertical unlit run and a vertical mixed run, each 12 cells long.
- Three illuminated cells per mixed run (positions 3, 7 and 11).
- Static Extractor and Smelter layers at their existing production transforms,
  with 128Ã—128 outlines for their four-by-four-cell logical footprints.
- A separate four-cell item-fit strip using existing Ferrite Ore/Ingot icons in
  provisional **10Ã—10-unit maximum envelopes**, and a 32-unit ruler.

There are 96 clean comparison segments plus eight segments in the separate fit
strips. Segment centers sit on the construction grid's cell centers, 32 units
apart. A 128-pixel conduit texture is scaled by 0.25, giving a full 32Ã—32 logical
cell; the visible housing is approximately 23 units wide and the open recess
approximately 12 units wide. These are artwork measurements, not simulation
dimensions or approved item sizes.

The vertical runs rotate the same sprite 90 degrees. Their straight edges align
exactly; the baked rail shading also rotates. Judge whether that shading is
acceptable or dedicated vertical artwork is needed.

The scene contains static sprites, labels, rulers, and a camera. Its only local
script adds middle-drag panning and enables the existing exterior zoom range.
No machine, player, terrain streaming, inventory, production, construction,
recovery or logistics simulation is instantiated.

## Files and import settings

All seven added files are inside this directory:

| File | Purpose |
| --- | --- |
| [conduit_art_v1.tscn](conduit_art_v1.tscn) | Isolated comparison scene |
| [inspection_camera.gd](inspection_camera.gd) | Viewing controls extending the existing camera |
| [straight_unlit.png](straight_unlit.png) | 128Ã—128 RGBA candidate, no cyan |
| [straight_lit.png](straight_lit.png) | 128Ã—128 RGBA candidate, localized steady cyan inset |
| [straight_unlit.png.import](straight_unlit.png.import) | Authored texture import settings |
| [straight_lit.png.import](straight_lit.png.import) | Matching authored texture import settings |
| [README.md](README.md) | Launch instructions, provenance and review boundaries |

Both PNGs have genuine alpha. Import settings are lossless compression
(`compress/mode=0`), mipmaps enabled, alpha-border fixing enabled, no
premultiplication and no size limit. Conduit and machine sprites use **linear
filtering with mipmaps** (`texture_filter=4`), matching the production machine
visuals. No lights, emission shader, pulse or animation is used.

Existing assets are referenced in place and remain unchanged:

- Terrain: `assets/experiments/terrain_c1/sources/{earth,green}.png`, the artwork
  loaded by the current `ContinuousTerrainPresenter`.
  Fixed center crops use nominal shader phase scale 0.9:
  `2048 / (1254 Ã— 0.9)` world units per source pixel, with linear filtering.
  This falls within the live renderer's 0.8â€“1.0 phase-scale range.
- Machines: front-facing layers under `assets/machines/{extractor,smelter}/`;
  scales and offsets copied as values from their current visual definitions.
  Machine scripts and animation are deliberately absent.
- Items: `assets/items/{ferrite_ore,ferrite_ingot}.png`.
- UI: existing IBM Plex Sans Regular. Zoom behavior:
  `scenes/player/follow_camera.gd`.

## Owner review

Inspect each material at 1Ã— first, then compare near 0.5Ã— and 1.5Ã—:

- Do adjacent copies read as a continuous conduit? Are join lines, repeated
  scratches or rail highlights distracting?
- Is housing width appropriate beside the existing machines?
- Does the open channel leave enough room for recognizable item silhouettes?
  The separate static fit strip tests one provisional envelope only.
- Do unlit and illuminated cells share geometry and materials?
- Is cyan visible but restrained? Does one light every four cells look repetitive?
- Does rotating the art work visually in vertical runs?
- Are the conduit and item silhouettes readable on both dirt and grass?

Approval remains the owner's decision. No visual acceptance is claimed.

## Validation and limitations

Static structure checks cover resource paths, parent ordering, load-step count,
eight 12-segment runs, three lit cells per mixed run, exact 32-unit spacing,
0.25 scaling and 90-degree rotation. Pixel checks cover PNG size, real
transparency, equal alpha masks, no cyan in the unlit variant, differences
confined to the illuminated inset, and **identical RGBA left/right boundary
columns across both variants**. Matching edges do not establish perceptual
seamlessness or eliminate repeated texture patterns.

An offline raster layout inspection was used to check spacing and scale. It is
not a Godot screenshot and does not validate engine filtering, shader output,
scene parsing or runtime controls. Repository static-suite results are reported
in the PR.

The terrain panels use current source artwork at representative live scale,
without procedural phase blending, terrain transitions or runtime tint fields.
They are material/scale comparisons, not a recreation of a generated world.
Item fit probes are stationary, and the conduit PNGs are flattened illustrations;
future D91 foreground-rail occlusion and moving-item readability are untested.
Cyan is intentionally small; its visibility at distant zoom needs owner review.

The normal startup scene, all existing gameplay files, camera behavior in the
game, machine footprints and Issue #214 remain unchanged. No test-runner scope
or execution permission is changed. No third-party plugin is added.

This directory is the entire experiment: nothing outside it references the scene
or these PNGs. Removing it later would remove the experiment, subject to the
owner's preservation requirements; this task performs no cleanup.

## Artwork provenance and preparation

Built-in imagegen produced the candidate artwork using the supplied
`conduit_tiling.png` as a visual reference. These are newly generated derivatives,
not lossless extractions of the concept swatches and not placeholder geometry.

The generated square canvases were 1254Ã—1254. A centered 768Ã—768 region at
(243, 243) was downsampled to 128Ã—128. An eight-pixel blend at each horizontal
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
