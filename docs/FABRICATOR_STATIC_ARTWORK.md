# Fabricator four-orientation static artwork

Decision 36, Option A authorizes this static integration on
`codex/fabricator-four-orientation-static-artwork`, **pending owner normal-F5
acceptance and merge**. Clean local and remote `main` were both
`4b37fc97ff2bbdb24e1fee600245c2329055982d`, unchanged from Decision 35 preflight.
Decisions 33/34 retain authoritative machine rotation and the existing
`MachineVisual` architecture. No gameplay or artwork-production change is included.

## Frozen sources and preservation

All four November 9, 2026 owner-accepted packages remain external and immutable.
Historical proposed/unfrozen labels in payloads retain their original meaning;
the later freeze receipts and Decision 36 authorize these exact inputs. No private
absolute package paths, source masters, package tools, animation layers, receipts
or duplicate archives are published in this PR.

| View | Frozen package | Freeze manifest SHA-256 |
| --- | --- | --- |
| 0 | `fabricator_0_frozen_v1` | `c2f8441a7706169d62b96d9c4d3b6b0821765b65939f6fb9f0ef42cbf3d2d0df` |
| 90 | `fabricator_90_frozen_v1` | `32266dfdba5687571ab31b28aa305d6e24c7886ca1b6f79330df656df92db433` |
| 180 | `fabricator_180_frozen_v1` | `6a68b6ea0a2dad155259eb0f019c726b3403b3e238c1599af325b77ba62e6280` |
| 270 | `fabricator_270_frozen_v1` | `a4c405caaeca6331d2cacceb345b775fc29ccc64437af767d1cc9fe1c30f553d` |

All manifests are `freeze/manifest.json`. The front receipt is `freeze/receipt.md`;
the others are `freeze/acceptance_receipt.md`. They record acceptance Decisions
9, 12, 21 and 30. Before copying, all manifest pins, complete payload inventories
and wrapper checksums passed; receipts agree with their manifest identities.
The four PNGs passed CRC, RGBA8, complete decoding and dimensions checks.

| Destination under `assets/machines/fabricator/` | Frozen package-relative source | PNG SHA-256 (expected = actual) |
| --- | --- | --- |
| `fabricator_0_resting.png` | `payload/previews/fabricator_0_resting.png` | `8230ff568218379c754d409fdf1bf568d90d00c71ccc677feee435e11999dd7e` |
| `fabricator_90_body.png` | `accepted_prototype/runtime/fabricator_90_body.png` | `789a5600cc396b11b18579aa7ac7dd50d3abfe458733c8c980f4a91a74c30c0d` |
| `fabricator_180_body.png` | `accepted_prototype/runtime/fabricator_180_body.png` | `cb17fff5627c03ee5034a37ecac420d1ae4f8192ce5d8759feb4069f0256eca3` |
| `fabricator_270_body.png` | `accepted_prototype/runtime/fabricator_270_body.png` | `1344c9c217e197da11c7e74b4a626714f2424f5b6ea95b9b82a10860d33f64f0` |

The front is the accepted full-canvas resting composite, including its mechanism,
not the smaller cropped body. Exactly four PNGs were copied without editing,
resizing, cropping or re-encoding. The
[integration inventory](experiments/fabricator_static_artwork.json) records sizes,
decoded RGBA identities, receipt identities, registration and complete frozen-tree
fingerprints (81/40/29/33 files, 183 total). This is a new integration record;
historical freeze manifests and receipts are unchanged.

## Presenter and registration

[FabricatorVisual](../construction/fabricator_visual.gd) and its
[scene](../construction/fabricator_visual.tscn) contain a Node2D root and one
uncentered Body Sprite2D. Four preloaded textures are selected by
`posmod(quarter_turns, 4)`. Configuration before readiness is retained and applied
in `_ready`; repeated configuration with the same direction is inert. There is
no animation, per-frame processing, illumination layer, production input or
independent rotation authority.

| Turns / view | Source canvas | Ground anchor | Crop x,y,w,h / PNG dimensions | Exact scale | Body offset |
| --- | --- | --- | --- | --- | --- |
| 0 / front | 1254x1254 | (627,1080) | (0,0,1254,1254) / 1254x1254 | 8/65 | (-627,-1080) |
| 1 / right | 1536x1536 | (768,1370) | (109,326,1316,1075) / 1316x1075 | 32/305 | (-659,-1044) |
| 2 / rear | 1280x1280 | (640,1123) | (54,122,1171,1022) / 1171x1022 | 32/265 | (-586,-1001) |
| 3 / left | 1536x1536 | (768,1255) | (96,284,1339,993) / 1339x993 | 16/155 | (-672,-971) |

Rectangles have exclusive far boundaries. Root position is footprint-local
`(64,128)` and its scale is the selected ratio; Body retains unit scale and has
no rotation or mirroring. For full-canvas source point p and accepted anchor A:

`world(p) = footprint_top_left + (64,128) + scale * (p - A)`

Offsets already account for crop origin minus anchor. No second source translation
or scale is applied. Accepted apparent-height differences and left cylinder
proportions remain intact; artwork may overhang the logical footprint.

## Adapter, ghost, status and rendering

[MachineVisual](../construction/machine_visual.gd) adds the Fabricator scene,
container and status overlay. Its definition/turns/is_ghost/status/show_status
contract and property setters remain intact. It creates the presenter once,
forwards `turns`, and hides the subtree when another machine is selected.
The obsolete procedural Fabricator body is removed.

Deployed art uses a plain Node2D container. Ghost art uses a CanvasGroup with
`self_modulate` alpha 0.5 and white adapter modulation, matching the established
illustrated strategy. The construction grid, validity outline, cancellation,
rotation and ghost/deployed world transforms remain unchanged.

The deployed dot is a separate last sibling, outside the artwork scale and ghost
composite, shown only for `show_status` on a non-ghost Fabricator. Radius remains
3.5 world units. Producing green `(0.35,0.78,0.46)`, output-full amber
`(0.94,0.69,0.28)`, input-empty blue `(0.35,0.60,0.90)` and inactive gray
`(0.55,0.58,0.59)` remain. `rotated_point(size - (13,13), turns)` retains positions
`(115,115)`, `(13,115)`, `(13,13)`, `(115,13)`. Status comes from existing
deployed-machine polling; the presenter owns no simulation.

DeployedMachine remains bottom-center anchored under Y-sorted GroundObjects with
Dave. The artwork subtree retains default Z and local sibling order. The scene
uses local `LINEAR_WITH_MIPMAPS` (4). Four import sidecars were authored offline
with unique ResourceUIDs and resource-path-MD5 cache references: lossless
compression, mipmaps, no size limit, straight alpha, `premult_alpha=false`,
`fix_alpha_border=true`, and unchanged RGBA channel mapping. No shader, additive
blend, light node, global rendering change or generated cache is included.
Actual engine import behavior remains an owner F5 check.

## Gameplay and regression boundary

The 4x4 / 128x128 footprint, placement/collision, 96-unit center-based inspection
and transfers, accepted diagonal-corner limitation and 160-unit nearest-footprint
recovery remain unchanged. Initial placement configuration, recipes, switching,
capacities, production, transactions, objectives and state ownership remain
unchanged. The item icon and stationary maintenance-bay Fabricator are unchanged.

Extractor and Smelter presenter scripts, scenes, artwork and imports are unchanged.
Their adapter branches are compared with the baseline, including Extractor barrel
motion and Smelter thermal lifecycle. Existing Smelter status functions and the
color helper are unchanged. Only five suites' obsolete procedural/whole-adapter
assertions are amended; gameplay, geometry and historical checks remain protected.

## Offline validation

Commands use the existing Python static-test conventions and run no Godot or
project code. For external preservation, set `TLWH_FABRICATOR_FROZEN_ROOTS` to a
JSON array of the four local frozen package directories in 0/90/180/270 order.
The external test explicitly skips if roots are not supplied; repository checks
still run. The implementation runs supplied all four roots.

From the repository root:

```powershell
python -B -m unittest discover -s tests -p static_fabricator_artwork_test.py -v
Push-Location tests
python -B -m unittest -v static_fabricator_artwork_test static_extractor_artwork_test static_extractor_animation_test static_smelter_artwork_test static_smelter_footprint_test static_smelter_thermal_test static_fabricator_footprint_test static_fabricator_inspection_test static_ferrite_integration_test static_v2_stationary_machines_test static_current_preservation_test static_preservation_guards_test static_terrain_stage3c_test
Pop-Location
python -B -m unittest discover -s tests -p 'static_*test.py'
git diff --check
git diff --cached --check
```

On November 9, 2026, the new suite passed **10/10**, the focused regression set
passed **86/86**, and the established full suite passed **450/450**. All three
commands exited 0 with no skips. Post-implementation rehashing confirmed all
183 external frozen files unchanged and all four destination PNGs byte-identical.
Of 1,015 baseline tracked files, 1,007 retained exact working bytes; the eight
changed existing files are the adapter, five authorized tests, README and
GAME_VISION. Gameplay and all existing Extractor/Smelter assets/presenters remain
unchanged. Added local Markdown links, scene/resource bindings, historical README
preservation, publication-path review and `git diff --check` passed.

After staging all 22 files, the index-sensitive resource graph, UID inventory and
scope checks were revalidated with the following command from `tests/`:

```powershell
python -B -m unittest -v static_fabricator_artwork_test static_fabricator_footprint_test static_v2_production_host_test static_terrain_stage3d_test
```

Result: **37/37 PASS**, exit 0, no skips. `git diff --cached --check` also passed.

These checks validate source/resource contracts and independent registration
math. They do not parse or execute GDScript or certify rendering, gameplay or
engine imports.

No Godot graphical/headless launch, native harness, performance probe or benchmark
was run. Front animation, gantry/carriage/tool movement, timing/easing and any PR B
work remain deferred to separate authorization.

## Owner normal-F5 acceptance — pending

None of these runtime checks is claimed as passed by the agent.

1. Launch normal F5, `scenes/main/main_v2.tscn`; confirm no new parser, import or
   runtime errors.
2. Cycle the ghost repeatedly through front/right/rear/left; check mapping and
   unchanged rotation/cancellation controls.
3. Deploy all four orientations; compare ghost/deployed artwork, ground alignment
   and accepted visual scale/height differences.
4. Confirm the 4x4 footprint, placement validity, obstacle/Dave/occupied-cell
   rejection, exact-edge adjacency and unchanged collision.
5. Check deployed status-dot visibility, size, position and all operating colors;
   verify ghosts have no dot.
6. Walk Dave around each orientation and neighboring machines to inspect sorting;
   review transparency, filtering, overhang and clipping at normal zooms.
7. Inspect and transfer materials; verify recipe switching, production, output
   collection and accepted center-based reach limitations.
8. Recover and redeploy a populated Fabricator; verify exact material returns,
   objective progression and unchanged stationary-bay behavior.
9. Travel interior/exterior and check retained presentation/state; confirm
   Extractor barrel animation and Smelter thermal behavior still work.

Owner acceptance and PR review are the next gate. Merge, cleanup and the animation
milestone are separate decisions.
