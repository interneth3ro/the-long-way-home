TLWH transition prototypes v1 — VISUAL / ALGORITHMIC PROTOTYPE ONLY

Source: approved 128x128 Weathered Earth and Low Green Cover prototypes.
Files are 128x128 RGB PNGs. 3x3 binary pattern string is row-major NW N NE / W C E / SW S SE, where 0=Earth, 1=Green.
These strings are demonstration neighborhood states, NOT Godot terrain peering-bit IDs or verified matches to the 94 configured signatures.
The transition mask is formed from shared-neighbor control points, bilinear interpolation and border-zeroed low-frequency perturbation.
Exact edge pixel continuity was tested in the assembled 12x10 map; maximum channel difference = 0.
Exact edge equality does not guarantee visually pleasing transitions or Godot matching correctness.
No Godot run, repository change, or performance claim. Full 94-tile mapping remains Codex scope after owner visual review.

earth_solid.png : 000000000
green_solid.png : 111111111
horizontal_earth_above.png : 000000111
horizontal_green_above.png : 111111000
vertical_earth_left.png : 001001001
vertical_green_left.png : 110110110
outer_green_corner.png : 000001011
outer_earth_corner.png : 111110100
inner_green_corner.png : 000010011
inner_earth_corner.png : 111101100
narrow_green_connection.png : 010010010
narrow_earth_connection.png : 101101101
isolated_green.png : 000010000
isolated_earth.png : 111101111
