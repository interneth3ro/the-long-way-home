# Straight conduit final visual acceptance candidate v1

Isolated artwork experiment on [PR #215](https://github.com/interneth3ro/the-long-way-home/pull/215),
pending owner final visual acceptance and merge. **The candidate sprites are not
marked owner-approved or promoted into production.**

## Decision 105: recessed conduit presentation

[Issue #214, Decision 105 Option A](https://github.com/interneth3ro/the-long-way-home/issues/214)
removes individual transported-item sprites from conduit presentation. Preserve
the Salvaged Sci-Fi v2 weathered gunmetal housing, continuous rails, dark recessed
channel, subtle orange wear, transparent background and sparse steady cyan.
The recess remains part of the visual design; it has no item-readability target.
D105 supersedes earlier visible-item presentation requirements while leaving
logical transport, inspection and recovery rules intact. This experiment
implements none of those systems and does not modify the issue.

The existing two conduit PNGs are retained byte-for-byte from `0918c91`.
No regeneration, redesign, widening, recoloring or new lighting treatment was
needed for this candidate. The temporary readability board, original item-fit
strips, item texture references, navigation hint and temporary wire SVG/import
sidecar have been removed. Existing inventory artwork remains untouched.

## Final F6 inspection

1. Open [conduit_art_v1.tscn](conduit_art_v1.tscn) in the TLWH Godot project.
2. Press **F6 / Run Current Scene**. F5 retains the normal project startup scene.
3. Inspect the initial **1x** view in the normal 1280x720 logical viewport. All
   comparisons are on this board; there is no lower item-readability board.
4. Mouse wheel uses the existing exterior camera's 0.5-1.5x range, 0.1 steps and
   0.15-second easing. Middle-drag pans. Use F8 to stop and F6 again to reset.
5. Review both terrain materials and both orientations for:
   - Seam visibility and continuity between neighboring cells.
   - Distracting repeated scratches, rail highlights or texture patterns.
   - Current conduit width beside the existing machines and 32-unit ruler.
   - Cyan frequency and brightness, including unlit-to-lit transitions.
   - Horizontal/vertical consistency, including the rotated baked shading.
6. Explicitly approve the final candidate or request revisions. Corner artwork
   remains a later task after this review; no final visual acceptance is inferred.

These are owner launch instructions. The agent has not imported or loaded the
scene with Godot, run a headless scene test, or launched the editor/game
graphically. The [execution policy](../../AGENTS.md#godot-execution-safety)
remains unchanged; the standing restricted recipes do not authorize loading
this experiment. No engine validation or graphical acceptance is claimed.

## Comparison contents and unchanged scale

Dirt and grass each retain four separate 12-cell runs: horizontal unlit,
horizontal mixed, vertical unlit and vertical mixed. There are **96 conduit
segments total**, with three illuminated cells in each mixed run (positions
3, 7 and 11; one accent every four cells). Unlit is the default appearance.
No individual items, end fittings, adapters, corners or bridges are displayed.

Each 128x128 conduit sprite uses scale 0.25 and occupies one **32x32 logical
cell**. Centers are exactly 32 world units apart. Width, transparent margins,
source geometry and grid registration are unchanged. Vertical runs rotate the
same sprite 90 degrees; there is no independent vertical redesign.

Existing Extractor and Smelter front-facing layers keep their production
transforms and 128x128 four-by-four-cell footprint outlines. Terrain, machine
positions, rulers and viewing controls are unchanged. The only scene script is
[inspection_camera.gd](inspection_camera.gd), which adds middle-drag viewing to
the existing camera zoom behavior. There are no gameplay, machine behavior,
item, inventory, construction, recovery or logistics systems in this scene.

## Files and import settings

The PR's seven remaining files are isolated in this directory:

| File | Purpose |
| --- | --- |
| [conduit_art_v1.tscn](conduit_art_v1.tscn) | Simplified straight-conduit comparison scene |
| [inspection_camera.gd](inspection_camera.gd) | Unchanged experiment viewing controls |
| [straight_unlit.png](straight_unlit.png) | Unchanged 128x128 RGBA default candidate, no illumination |
| [straight_lit.png](straight_lit.png) | Unchanged matching candidate with localized steady cyan |
| [straight_unlit.png.import](straight_unlit.png.import) | Unchanged tracked texture import configuration |
| [straight_lit.png.import](straight_lit.png.import) | Matching unchanged tracked import configuration |
| [README.md](README.md) | Current D105 scope, launch instructions and provenance |

Both PNGs are **128x128, 8-bit RGBA**, with genuine transparency and identical
alpha masks. Both horizontal boundary columns match exactly across both
variants, so the same boundary match holds when the sprite is rotated vertically.
Their differences are confined to the cyan inset; there are no animated lights,
pulses, traveling lights or emission shaders.

Import settings remain lossless (`compress/mode=0`), mipmaps enabled,
alpha-border fixing enabled, premultiplication disabled and no size limit.
Conduit/machine sprites use linear filtering with mipmaps (`texture_filter=4`),
as in the existing machine visuals. Local engine-added metadata is preserved;
this amendment does not change the tracked conduit import settings.

Existing project resources are referenced in place:

- Terrain: `assets/experiments/terrain_c1/sources/{earth,green}.png`, used by the
  current continuous renderer. Fixed center samples retain nominal phase scale
  0.9, or `2048 / (1254 x 0.9)` world units per source pixel, with linear filtering.
- Machines: front-facing layers under `assets/machines/{extractor,smelter}/`,
  retaining their existing scales and offsets without animation or machine scripts.
- UI: IBM Plex Sans Regular. Shared zoom behavior:
  `scenes/player/follow_camera.gd`.

## Validation and remaining limitations

Current static checks cover PNG dimensions/color type/transparency, exact
boundary and alpha-mask matches, localized cyan, unchanged candidate hashes,
eight 12-cell runs, illumination counts, grid centers, spacing, rotations,
resource paths, parent/load-step consistency, import settings, removal of item
resources, local Markdown links and Git diff scope. Applicable preservation
test results are reported in the PR. Routine check output is not committed.

Exact pixel matches do not establish perceptual seamlessness: repeated details,
real engine mipmap/filter output, cyan brightness and rotated shading still need
the owner's rendered F6 inspection. The terrain samples omit procedural phase
blending, transitions and runtime tint fields. They provide an artwork/scale
comparison, not a generated-world recreation. No Godot scene-load or graphical
verification was performed for this amendment.

Normal startup, gameplay, machine footprints, construction grid, source artwork,
execution policy and Issue #214 remain unchanged. No repository audit or unrelated
cleanup is included. Only the obsolete experiment wire source and its matching
sidecar were deleted; existing caches, UID files, owner metadata, historical
evidence and unrelated files remain preserved.

No production scene references this experiment. The directory remains removable
under the owner's preservation rules. The following original authoring prompts
are historical provenance; final review follows D105 and the checklist above.

## Artwork provenance and preparation

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
