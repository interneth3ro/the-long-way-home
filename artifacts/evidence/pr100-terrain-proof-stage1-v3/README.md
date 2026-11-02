# PR #100 / Stage 1 offline artwork proof

Status: **owner visual approval pending**. This is an ignored evidence bundle,
not an integrated asset update. PR #100 remains draft and blocked for graphical
acceptance. No complete 94-tile atlas has been generated or integrated.

## Review images

- [Representative tiles and exact masks](representatives.png): twenty individual
  128x128 PNGs covering both center terrains, four straight directions, convex and
  concave corners, endpoints, narrow connections and isolated patches.
- [Approved package / new method comparison](comparison.png): original supplied
  preview on the left, new native-signature proof on the right. The layouts differ;
  this is a visual treatment comparison, not a pixel-identical reconstruction.
- [Interior A/B/C repetition comparison](variations.png): original repeated source
  versus three seam-compatible source-derived alternatives, at equal scale.
- [Green patch with varied interiors](previews/green_patch_varied.png).
- [Earth patch with varied interiors](previews/earth_patch_varied.png).
- [Meandering common boundary](previews/meandering_boundary_varied.png).
- [Green patch with unmodified repeating interiors](previews/green_patch_baseline.png).

Actual tile PNGs are in `representatives/`; corresponding grayscale masks are in
`masks/`. The four additional B/C interior PNGs are in `variants/`. Original A
interiors appear among the representatives. Black mask values mean Earth; white
means Green. Intermediate values blend the two approved source materials.

## Inputs and scope

Source materials are the exact approved `earth_solid.png` and `green_solid.png`
from `assets/experiments/native_terrain_47_96/illustrated_v1/originals/`.
No new texture painting, palette replacement, brightness tint or generative image
editing is used. The owner explicitly authorized deterministic image-processing
code for this proof.

The immutable 94-record CSV is the authority for all signatures. The filename
of a source example is not used to infer native metadata. Every representative
and every assembled cell resolves to an actual center-plus-eight-peer record.
`manifest.json` records original inventory cells, all forty exercised signatures,
all preview-cell assignments/variants and input/output SHA-256 hashes.

Twenty signatures have separately exported art/mask PNGs. Twenty more are used
only while assembling the previews. There is no atlas sheet, no invented terrain
signature and no approximation of an unmatched corner example. The original four
corner PNGs and all other approved source assets remain unchanged.

## Mask-generation method

1. Place the actual native values in a 3x3 control grid: NW,N,NE / W,C,E / SW,S,SE.
   Earth is 0; Green is 1. These are shared peering values, not neighboring cells'
   terrain labels.
2. Interpolate each complete tile edge through its two corner values and side
   midpoint. Adjacent tiles with the same three shared peers therefore get the
   same boundary function.
3. Interpolate a continuous surface between those four edge curves using a Coons
   patch (sum of opposite-edge blends minus the duplicated corner blend).
4. Add an interior bubble `16*u*(1-u)*v*(1-v)` multiplied by the correction needed
   to reach the actual center value. The bubble vanishes on all four edges, so
   fixing the center never changes a shared edge.
5. Add a modest periodic perturbation, multiplied by `4*f*(1-f)`. This leaves binary
   control anchors unchanged and adds uneven contours where materials meet.
   The perturbation is identical on matching edges and does not use per-tile
   random edge values. Pixel 127 uses the same periodic phase as pixel 0.
6. Feather the field through smoothstep from 0.30 to 0.70. Blend the two approved
   RGB textures in linear light, then encode back to sRGB PNG. There is no outline
   color, extra border strip, magenta placeholder or runtime shader in this bake.

All nine control samples are checked against their actual signature after
quantization. The original solid textures also have equal opposite border pixels.
Common mask functions plus those source pixels give exact compatible tile edges.

This does not claim correct native configuration from a visual label: both the
input record and raster control values are checked directly.

## Assembled examples and interior variation

The previews use authored coarse region layouts. A bounded offline constraint
assignment chooses existing signatures with those center terrains, enforces all
three shared peers on adjacent sides, and prefers anchors near a smooth field of
the authored region. Deep interiors use the solid signature.

This is an offline artwork assembly device, **not a simulation or replacement of
Godot Connect**. Godot may choose different valid signatures or brush-order results.
No layout solver, mask generator or image-processing code is added to the game.

Alternative A is the original material. B/C blend shifted/rotated samples of that
same material into its interior. A smooth sine-squared envelope makes the blend
exactly zero on every edge, with no change in edge pixels. The blend takes place
in linear light. The same three material alternatives work with every tested mask.
Variants are selected deterministically in the previews; their indices are saved.

The method reduces identical central motifs modestly without introducing a new
art style. It does not eliminate repeated edge structures or all broad repetition.

## Checks and preservation

- Forty of ninety-four actual signatures exercised; twenty exported representatives.
- 5,535 compatible horizontal/vertical edge comparisons, covering all nine A/B/C
  pairings for each compatible signature pair: **maximum channel difference 0**.
- Both center terrains and all nine control samples checked for each generated mask.
- Generated PNG dimensions, chunk CRCs and complete compressed scanlines checked.
- All 371 pre-existing tracked/untracked working-file hashes match the snapshot,
  including the protected resources, PR #100 scenes/resources and approved artwork.
- HEAD remains `e8a722e50de4c89442a579584ae1228aef483ff6`.
- No existing TileSet, scene, 94-record inventory, shader, testing control or production
  renderer is modified. No project file is staged or committed for Stage 1.
- Godot, Native, graphical interaction, profiling and benchmarks: **NOT RUN**.

`proof.py` is a standard-library offline bake recipe; `boards.ps1` adds labels and
comparison layouts using Windows System.Drawing. Both are evidence-only files.
They create outputs exclusively and intentionally refuse to overwrite existing
PNGs. Reproduction requires a fresh evidence directory at the same directory depth.
`source_snapshot.json` retains the pre-proof working-file hashes; `manifest.json`
records the meaningful output checks. No successful routine test log is retained.

## Visual evaluation and limitations

The magenta interruptions and flat diagnostic sectors are absent. Boundaries now
have a continuous feathered treatment inside the tile, rather than an eight-pixel
edge repair. Corners, endpoints and isolated patches use the same mask language.

The proof is **not yet accepted terrain artwork**:

- Grid influence remains in the region shape. Exact binary native anchors constrain
  the contour; the current mask can still show rounded steps and scalloping.
- Some combinations create small corner pockets or lobes. Their peer assignments
  are valid, but their visual effect still needs owner judgment.
- A/B/C alternatives reduce repetition only moderately. The two original textures
  share strong repeated edge/motif structure; blends may soften interior contrast.
- Equal boundary pixels do not establish smooth derivatives or absence of a visible
  texture band across the join. The repetition board exposes this limitation.
- These are 128px offline images. Downscaled gameplay appearance, imported texture
  filtering, native brush selection and performance have not been verified.
- Only forty signatures were exercised. The remaining fifty-four configurations
  are deliberately ungenerated and unreviewed in this stage.

The earlier `../pr100-terrain-proof-stage1-v1/` and `../pr100-terrain-proof-stage1-v2/`
folders preserve the preceding method trials. v1's tensor interpolation looked too
square; v2 improved the surface but assigned every interface to one terrain family.
v3 is the selected review candidate and uses both families in assembled regions.
These trials are not new project asset versions or full atlases.

Owner decision requested: approve this contour/material method for Stage 2, or
specify changes to softness, rounded steps/corner pockets and repetition first.
Approval of Stage 1 deliverables alone does not authorize generating/integrating
the complete atlas, launching Godot or changing the production renderer.
