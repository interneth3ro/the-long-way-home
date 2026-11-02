# Ferrite artwork prototype v1

Offline artwork candidate on the feature branch, pending merge and owner visual
acceptance. No production integration or Godot execution.

## Review package

- [Contact sheet](../assets/experiments/ferrite_artwork_v1/previews/contact_sheet.png):
  components, both sizes, surface/edge close-ups and scale reference.
- [Medium transparent PNG](../assets/experiments/ferrite_artwork_v1/previews/medium_6x4.png).
- [Large transparent PNG](../assets/experiments/ferrite_artwork_v1/previews/large_10x6.png).
- [Large with terrain grid and Extractor footprint](../assets/experiments/ferrite_artwork_v1/previews/large_10x6_scale.png).

The overlay is a reference rectangle, not new Extractor artwork. Checkerboards
appear only on the contact sheet. The package's `.gdignore` prevents engine import.

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
```

The execution-policy option applies only to that process, not persistent policy.
Build writes only 15 fixed derived PNGs in this package's `components/` and
`previews/`. Check regenerates in memory and compares exact PNG bytes without
writing outputs. Source dimensions, outside transparency and fully opaque safe
interior pixels are checked, including component joins. Cross-platform/font-version
byte equality is not promised for the contact sheet.

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

The contact sheet uses a neutral backdrop. Refined-ground compatibility, normal
gameplay scale, machine readability and engine appearance need later owner
acceptance. No graphical, gameplay or performance PASS is claimed. Production
terrain, resource geometry, clearing, simulation, Extractor and placement are
unchanged. Preserve a rejected prototype for comparison; no automatic redesign
or cleanup follows rejection.
