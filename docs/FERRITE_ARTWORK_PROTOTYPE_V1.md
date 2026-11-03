# Ferrite artwork prototype v1

Owner-accepted offline artwork prototype, merged in PR #123 at `87ca973`.
The prototype itself involved no production integration or Godot execution.
All images, including their earlier pending-acceptance captions, are preserved
unchanged; the record below
supersedes those status captions.

## Owner acceptance: 2026-11-02

The owner explicitly approved the delivered prototype and irregular assembly proof
at commit `1662a616346f33718fe4dbaee7989b2c70f7aa40`, then requested that PR #123
and its documentation record acceptance. This accepts the Faceted Ferrite artwork
and the demonstrated reusable architecture: rectangular examples plus connected
L-shaped, stepped and organic grid-cluster assemblies, overlays, corner treatments
and close-ups, with the documented limitations retained.

This is owner visual/architecture acceptance of the isolated offline prototype.
It does not claim in-game verification, authorize production integration or
procedural distribution, or request a merge. PR #123 subsequently merged.
The prior offline validation results at the reviewed commit remain the technical
evidence; this documentation-only acceptance update does not rerun generation or
Godot checks.

## Review package

- [Contact sheet](../assets/experiments/ferrite_artwork_v1/previews/contact_sheet.png):
  components, both sizes, surface/edge close-ups and scale reference.
- [Medium transparent PNG](../assets/experiments/ferrite_artwork_v1/previews/medium_6x4.png).
- [Large transparent PNG](../assets/experiments/ferrite_artwork_v1/previews/large_10x6.png).
- [Large with terrain grid and Extractor footprint](../assets/experiments/ferrite_artwork_v1/previews/large_10x6_scale.png).

The overlay is a reference rectangle, not new Extractor artwork. Checkerboards
appear only on the contact sheet. The package's `.gdignore` prevents engine import.

## Irregular assembly proof

- [Three-shape comparison](../assets/experiments/ferrite_artwork_v1/previews/irregular_contact_sheet.png).
- L-shaped: [clean](../assets/experiments/ferrite_artwork_v1/previews/irregular_l_shape.png)
  / [logical mask overlay](../assets/experiments/ferrite_artwork_v1/previews/irregular_l_shape_mask.png).
- Stepped: [clean](../assets/experiments/ferrite_artwork_v1/previews/irregular_stepped.png)
  / [logical mask overlay](../assets/experiments/ferrite_artwork_v1/previews/irregular_stepped_mask.png).
- Organic grid cluster: [clean](../assets/experiments/ferrite_artwork_v1/previews/irregular_organic.png)
  / [logical mask overlay](../assets/experiments/ferrite_artwork_v1/previews/irregular_organic_mask.png).
- Close-ups: [concave turn](../assets/experiments/ferrite_artwork_v1/previews/irregular_concave_closeup.png)
  / [stepped perimeter](../assets/experiments/ferrite_artwork_v1/previews/irregular_step_closeup.png).

### Reproducible occupancy masks

`#` means an occupied 64-world-unit terrain cell; `.` means empty. Rows run north
to south, columns west to east. All three masks were authored with broad connected
regions; none was changed after the first proof build. These are demonstrations,
not procedural generation rules or changes to production resource geometry.

Shape A, [l_shape.txt](../assets/experiments/ferrite_artwork_v1/masks/l_shape.txt):
8x6 bounding cells, 36 occupied, 5 convex / 1 concave turn.

```text
####....
####....
####....
########
########
########
```

Shape B, [stepped.txt](../assets/experiments/ferrite_artwork_v1/masks/stepped.txt):
10x7 bounding cells, 50 occupied, 8 convex / 4 concave turns.

```text
..######..
..######..
########..
########..
..########
..########
....######
```

Shape C, [organic.txt](../assets/experiments/ferrite_artwork_v1/masks/organic.txt):
10x8 bounding cells, 56 occupied, 14 convex / 10 concave turns.

```text
...####...
.#######..
.########.
#########.
.#########
.#########
...######.
....####..
```

| Shape | Logical source bounds | Clean/overlay PNG canvas | World bounds |
| --- | --- | --- | --- |
| A | 1024x768 | 1152x896 | 512x384 |
| B | 1280x896 | 1408x1024 | 640x448 |
| C | 1280x1024 | 1408x1152 | 640x512 |

All logical origins remain `(64,64)` source pixels. The contact sheet displays
the three clean assemblies at exactly 0.5 source scale, overlays at 0.25, the
concave crop at 1.0, and the stepped crop at 0.8. Standalone crops retain native
pixels: 384x384 and 640x512 respectively. No complete deposit is stretched.

### Architecture extension and corner treatment

The original nine-slice system cannot represent concave footprints. It remains
unchanged for the preserved rectangles. The new `irregular.ps1` adds a separate,
bounded offline contour compositor using **the same existing interior and four
directional painted edge strips**, without generating new artwork.

1. Cancel cell-internal boundaries and trace one clockwise exterior contour.
   Classify convex and concave vertices from the turn direction.
2. Round both types of corner with a 24-source-pixel quadratic turn. Straight
   spans receive at most five pixels of deterministic contour variation; this
   changes geometry only, not the mineral material.
3. Sample one continuous, native-density interior in deposit coordinates.
   A 96-pixel overlap blends repeated source intervals. Cell boundaries never
   reset texture coordinates, so adjoining regions share the same facets.
4. Follow the entire contour with the original painted perimeter strips.
   Register samples to each strip's actual opaque painted rim, preserving useful
   edge paint instead of stretching transparent fringe RGB. Blend world-facing
   strip samples through rounded turns; do not rotate or mirror lighting.
   Feather painted edge material into the shared interior over 24..104 pixels.
5. Retain shallow orientation-dependent sidewalls (2..12 source pixels) and add
   a low-opacity contact-shadow skirt, ending within 36 pixels of the contour.
   This includes recesses and short step spans, not only the outer bounding box.

The eight new `components/irregular_convex_*.png` and
`components/irregular_concave_*.png` files expose canonical 192x192 corner
treatments. Convex suffixes identify the occupied quadrant; concave suffixes the
missing quadrant. **These are inspection exports of the shared corner sampler,
not finished corner sprites pasted into the assemblies.** All eight exports and
all three shapes execute the same contour/paint mapping rule. Material color
comes from the original illustration, not flat polygon fills or noise.

This is not overlapping finished deposits or hard-cutting a rectangular preview:
the interior and directional edge assets are sampled independently, and the
perimeter is rebuilt around every convex/concave transition. There are no
shape-specific paint edits or retouched final images, and no 94-signature system.

### Supported shapes and honest assessment

Demonstrated support: connected, hole-free, orthogonal occupancy masks with broad
regions, re-entrant corners, multiple width changes and short protrusions/recesses.
The sampler can repeat material beyond the rectangular compositor's splice-size
limits, with increasing visible repetition. Arbitrary topology is not claimed:
disconnected masks, holes/multiple loops, malformed rows and diagonal-only boundary
contacts fail explicitly. Thin necks and long one-cell tendrils are not artistically
validated; opposite edge bands would compete for their limited interior space.

At 0.5 source scale the three proofs retain the same mineral identity and continuous
interior. They are nevertheless **less naturally varied than the rectangular
artwork**: similar highlights recur at exposed north edges; the predominantly
diagonal grain repeats vertically; some rounded turns expose converging texture
or softened fractures. The cluster remains visibly grid-conforming, rather than
an unconstrained natural silhouette. Concave edges are thinner and more regular
than the source's best hand-painted outer corners. The owner accepted the delivered
proof with these documented limitations. Acceptance does not imply equal artistic
polish across all shapes or an unrestricted production library. Further refinement
remains separately scoped; the approved material is not redesigned by this record.

## Dimensions and assembly

128 source pixels represent one 64-world-unit terrain cell, displayed at 0.5
scale. Both axes retain the same density. PNGs include 64 source pixels of
transparent/shadow margin on each side (32 world units).

| Example | Logical source rectangle | PNG canvas | World footprint |
| --- | --- | --- | --- |
| Medium, 6x4 terrain cells | 768x512 | 896x640 | 384x256 |
| Large, 10x6 terrain cells | 1280x768 | 1408x896 | 640x384 |

The logical rectangle starts at pixel `(64,64)` in each preview. The cyan
Extractor reference is exactly 128x128 source pixels: 64x64 world units / 2x2
construction cells. Terrain-grid spacing is 128 pixels. Visual edges may
overhang/recede modestly around the logical rectangle.

The untouched [master](../assets/experiments/ferrite_artwork_v1/source/ferrite_master.png)
is a 1619x972 AI-generated illustration. Its requested canvas geometry was not
honored. The compositor uses the logical rectangle `(96,160)..(1536,832)` and
crops a 64-pixel margin around it; it never stretches the complete illustration.

| Component group | Source dimensions | Relationship |
| --- | --- | --- |
| Four corners | 192x192 each | Fixed size, includes padding and 128px of logical corner |
| North/south | 1184x192 each | Fixed height; overlap-spliced center length |
| West/east | 192x416 each | Fixed width; overlap-spliced center length |
| Interior | 1184x416 | Continuous painted source; overlap-spliced on both axes |
| Silver/quiet samples | 256x256 each | Material-review crops, not seamless drop-in overlays |

The same nine components supply both sizes with coherent light direction.
No rotated tiles, per-cell random patches, ground recoloring or polygon-painted
substitute textures are used. A changed middle-strip length retains endpoints
and joins two native-size intervals through a 96-pixel smoothstep overlap.
Shortening removes central material; lengthening repeats overlapping material.
Adjacent components use the same coordinate mapping, keeping joins registered.
No source texel is spatially stretched. Blend RGB is alpha-weighted.

This is a compact continuous-composition prototype, **not an infinitely seamless
texture library**. Delivered dimensions are supported; arbitrary dimensions are
not promised. Unsupported splice dimensions fail explicitly. Assembly uses no
RNG; the saved source defines the illustration.

The generator left faint outside alpha residue and scattered pinholes inside.
Derived components zero alpha <=8, seal alpha >=240, and seal the safe interior
24px inside the logical rectangle. Intermediate edge alpha and painted
sidewall/contact shading remain. The source master is never modified.

## Reproduce and validate offline

Requires existing Windows PowerShell 5.1 / .NET Framework System.Drawing and
Segoe UI. No packages, Godot or external services are required for assembly.
From the repository root:

```powershell
powershell.exe -NoProfile -ExecutionPolicy Bypass -File assets/experiments/ferrite_artwork_v1/build.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File assets/experiments/ferrite_artwork_v1/build.ps1 -Check
powershell.exe -NoProfile -ExecutionPolicy Bypass -File assets/experiments/ferrite_artwork_v1/irregular.ps1
powershell.exe -NoProfile -ExecutionPolicy Bypass -File assets/experiments/ferrite_artwork_v1/irregular.ps1 -Check
```

The execution-policy option applies only to that process, not persistent policy.
Build writes only 15 fixed derived PNGs in this package's `components/` and
`previews/`. Check regenerates in memory and compares exact PNG bytes without
writing outputs. Source dimensions, outside transparency and fully opaque safe
interior pixels are checked, including component joins. Cross-platform/font-version
byte equality is not promised for the contact sheet.

The irregular build reads the existing component family and the three text masks.
It writes only 17 fixed `irregular_*` PNGs (six clean/overlay assemblies, eight
corner-treatment exports, two close-ups, one contact sheet). Its `-Check` mode
regenerates and compares exact PNG bytes without writing. Validation covers
four-neighbor logical connectivity, single-contour topology, turn counts,
occupied/empty cell-center agreement, opaque contour interiors and transparent
exterior beyond the shadow skirt. Flood fills at alpha thresholds 1 and 128 check
both all visible pixels and the solid mineral body for disconnected islands.
Run the original `build.ps1 -Check` as the rectangular/component regression.
These are focused offline checks, not Godot or artistic acceptance tests.

Source artwork was made using built-in imagegen with the owner-supplied Ferrite
size/shape study as a visual reference, not a pixel source. No previous-game ore
assets were used. The [authoring prompt](../assets/experiments/ferrite_artwork_v1/source/PROMPT.md)
records the request. AI regeneration is not bitwise reproducible; the delivered
components and previews are reproducible from the saved master.

## Artistic assessment and limits

Broad cool metallic facets, shallow fractures, restrained oxidation and a thin
painted edge read as one surface in both offline assemblies. The painting
provides the material detail; the compositor only assembles it.

Both sizes share recognizable highlights. Overlap blending can soften/ghost
fractures near central joins, particularly in the enlarged vertical interior.
The bright northwest facet and mostly diagonal grain are more uniform than the
reference's varied layered facets. Sample crops do not solve variation across
many deposits; no autonomous per-deposit variation is implemented. This is not
claimed as a final seam-free production library.

The contact sheet uses a neutral backdrop. Offline visual/architecture acceptance
is recorded above. Refined-ground compatibility in-game, normal gameplay scale,
machine readability and engine appearance still require later integration and
owner verification. No engine, gameplay or performance PASS is claimed. Production
terrain, resource geometry, clearing, simulation, Extractor and placement are
unchanged. Retain the source and previews for comparison; acceptance does not
request redesign or cleanup.

## Production integration (feature branch, pending merge)

The production exterior uses one static Sprite2D below `FerriteGround` (Z -5),
above terrain (Z -11/-10), below construction highlights (Z -4), Dave and machines.
It has no terrain tint shader or modulation. The four polygon/line placeholder
nodes are removed. The original prototype, components, masks and authoring tools
remain unchanged behind their `.gdignore`.

The sole production asset is a byte-for-byte copy of the approved
[large preview](../assets/experiments/ferrite_artwork_v1/previews/large_10x6.png) at
[faceted_ferrite_10x6.png](../assets/environment/exterior/ferrite/faceted_ferrite_10x6.png).
SHA-256: `82442d7e11eaf4483202ff22b22060efa4c2f638e66f30694d8b527dd1961c75`.
The preview remains the authoring source of truth; future approved revisions must
update the production copy explicitly. No regeneration, repainting or recoloring
was performed. Keeping only this final PNG outside the ignored package makes it
importable without exposing the experimental tools and review images to Godot.

| Registration | Value |
| --- | --- |
| Logical bounds in exterior world units | `(128,128)..(768,512)` |
| Terrain cells | X 2..11, Y 2..7: exactly 10x6 |
| Logical dimensions | 640x384 world units, 20x12 construction cells |
| PNG canvas | 1408x896 RGBA source pixels |
| Logical source origin and size | `(64,64)`, 1280x768 pixels |
| Sprite canvas origin | `(96,96)`, `centered = false` |
| Uniform display scale | 0.5; 128 source pixels per 64-unit terrain cell |
| Displayed canvas bounds, including margins | `(96,96)..(800,544)` |
| Inspection | unchanged `(304,280)`, radius 24, ID `crash_site_ferrite` |

The expanded field stays east/southeast of the ship, retains the original western
inspection approach from spawn `(-384,-64)` and leaves the hatch `(-384,-176)`
clear. Its full canvas and a 64-unit logical access apron fit inside the existing
protected gameplay polygon. Both authored rocks are remote from the field.
Procedural details there are already suppressed; generated details elsewhere are
decorative and noncolliding. No clearing, gradients, terrain assets, resolver,
shading, streaming, navigation or environmental collisions change.

`introductory_ferrite.tres` retains `crash_site_ferrite`, type `ferrite` and its
highlight color. Its axis-aligned rectangle alone controls membership and the
existing chunk-clipped compatible-resource highlights. Decorative alpha may
recede within or overhang the rectangle; it never controls mining. Discovery,
objective progression and interaction scripts are unchanged. Extractors remain
2x2 construction cells with the existing designated extraction-point rule,
rotations, overlap/solid/range checks and all production behavior. Full containment
is not required. Adjacent nonoverlapping Extractors can share this deposit.

Offline checks inspect exact geometry, image identity/header, registration,
resource reachability, protected coverage, representative extraction-point cases,
unchanged gameplay contracts and the scoped diff. They do not execute GDScript or
establish Godot import success, physics, visual quality or performance. No Godot
execution is authorized for this milestone. Procedural distribution remains a
future milestone requiring varied connected irregular grid-conforming deposits;
no runtime compositor or procedural ore generator is introduced here.

### Owner acceptance checklist (pending)

- Exterior loads and imports the new texture successfully.
- Approved artwork appears at the intended location with no old placeholder.
- Surface, shallow edges and contact shading suit Weathered Earth and Low Green Cover.
- Dave and Extractors render correctly above the mineral surface.
- Construction highlights match the rectangular mineable area.
- Valid interior/edge extraction points work; outside points are rejected.
- Multiple adjacent Extractors work; overlap and obstacle rejection remain intact.
- Discovery remains accessible and advances the opening objective normally.
- Mining, production, ship access and nearby walking remain normal.
- No obvious performance regression during ordinary play.

Owner graphical/gameplay acceptance and explicit merge approval remain required.
