# Quiet ground artwork study v1

Isolated prototype on a feature branch, pending owner visual acceptance and merge.
These are offline PNGs; the production renderer does not load this directory.
The `.gdignore` marker prevents Godot importing this study.

Start with the [meandering comparison](previews/meandering_boundary.png) and
[larger mixed comparison](previews/mixed_24x16.png). Original is left, refined is
right, with identical layouts and framing. The mixed comparison uses 64 pixels
per terrain tile; other boards include 128-pixel and 64-pixel views.

- [Earth interior](previews/earth_interior.png)
- [Green interior](previews/green_interior.png)
- [Earth and Green A/B/C repetition](previews/abc_repetition.png)
- [Representative transitions](previews/transitions.png)
- [Refined Earth source](sources/earth_refined.png)
- [Refined Green source](sources/green_refined.png)
- [Subset sheet at original atlas coordinates](baseline_subset.png)
- [Four B/C interiors at original coordinates](interiors_bc.png)
- [Mappings, parameters, layouts and hashes](manifest.json)

The subset sheet configures only 41 existing signatures; dark unused slots are
explicitly outside the inventory. There is no new TileSet or paintable scene.
See the [method, validation and limitations](../../../../docs/GROUND_ART_REFINEMENT_PROTOTYPE.md).
