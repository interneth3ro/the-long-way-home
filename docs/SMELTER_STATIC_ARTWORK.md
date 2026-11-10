# Static directional Smelter artwork

## Port-free runtime bodies v1 (pending merge)

On November 10, 2026, the owner authorized the reviewed fourteen-path integration
on `codex/smelter-port-free-runtime-v1`, based on
`39ad7c09b0bbd5c01f63bede7d376c3e4baf170c`. Four independently accepted and frozen
port-free masters now supply the four active body PNGs through the original fixed
crop rectangles below. Every cropped RGBA byte, including transparent RGB, is
preserved. Encoding uses PNG RGBA8, no interlace, row filter 0 and zlib level 9;
there is no resize, rotation, repaint, premultiplication or alpha cleanup.

The [derivative provenance](experiments/smelter_port_free_runtime_v1.json) records
archive/receipt/manifest/master identities, original and active runtime hashes,
exact crop RGBA identities, measured alpha bounds and unchanged supporting layers.
The [read-only verifier](../tests/smelter_artwork_offline.py) checks active identities
and historical Git bodies; `--freeze-dir` additionally verifies all four preservation
formats, exact source crops, all 129 original-source files and the 270-degree
source aliases. It reads ZIP members without extracting or running package scripts.
Private source locations and raw receipts remain outside the repository.

All ten import sidecars, four illumination PNGs, 0-degree interior/foreground,
Smelter presenter/UID/scene and shared machine presenter remain unchanged. Original
registration, independent direction slots, ghost transparency, status dot,
footprint, collision, interaction ranges and all gameplay sources are preserved.
The accepted [thermal behavior](SMELTER_THERMAL_ILLUMINATION.md) continues unchanged.
The original inventory and acceptance records below describe historical artwork;
they do not certify the active port-free derivatives in Godot.

Offline composites at illumination opacity 0, 0.82 and 1 match full-master
compositions exactly. Static tests preserve the original idle reconstruction and
original four-edge alpha bounds, separately pin the new measured body bounds,
and compare the unchanged thermal contribution in every RGBA channel.

Run from the repository root:

```powershell
python -B tests/smelter_artwork_offline.py --active
python -B tests/smelter_artwork_offline.py --freeze-dir '<owner-local-freeze-directory>'
python -B -m unittest discover -s tests -p 'static_smelter*test.py'
python -B -m unittest discover -s tests -p 'static_*test.py'
```

Static results: Smelter 28/28, Extractor 16/16; Fabricator 34 passed and two
optional external-package checks skipped. Full suite: 473 tests, 471 passed, two
skipped, zero failures/errors. Both Smelter helper modes and the active Extractor
helper passed. Details are recorded in the derivative provenance. No Godot,
headless import, native runner, graphical interaction, benchmark or stress test
was executed. **Owner graphical acceptance remains pending.** Static PASS does
not establish engine parsing, imports, rendered filtering or runtime behavior.

### Owner F5 checklist for port-free v1

All items are pending owner review against this feature's implementation commit.

1. [ ] Start normally with F5; confirm imports and startup have no new errors.
2. [ ] Inspect all four orientations at zoom 0.5x, 1x and 1.5x.
3. [ ] Check registration, silhouettes, overhang, seams, sorting and clipping.
4. [ ] Cycle ghost orientations and machine types; confirm stable registration,
   composite transparency and hidden heat/status dot.
5. [ ] Check cold and inactive illumination, including immediate inactive hiding.
6. [ ] Check approximately 0.5-second warmup, 3.6-second pulse, 1-second cooldown
   and interrupted transitions restarting from current opacity.
7. [ ] Exercise input-empty and output-full transitions and resumed production.
8. [ ] Recover and redeploy; confirm cold presentation and exact material returns.
9. [ ] Travel exterior/interior/exterior; confirm state retention and nominal heat
   initialization from the current operating state.
10. [ ] Check independent mixed-orientation machines and 0-degree interior,
    illumination and foreground layering. Direction-change thermal continuity is
    source-contract-only unless the existing workflow permits changing direction
    on the same live heated presenter; ghost rotation/redeployment is not that test.
11. [ ] Check placement, occupancy, collision, rotation and existing interaction ranges.
12. [ ] Check production, input/output buffers and material transfers.
13. [ ] Recheck Extractor, Fabricator, terrain, Dave, stationary machinery and
    unrelated artwork during ordinary play.

## Historical static artwork milestone

Implemented on `codex/smelter-static-artwork`, **owner F5 accepted; merged in
PR #157** at `ca18cfa4c9f16ab934968aed4fa764f9c1e2b58d`, from PR #156 merge
`65564d5d95502fcc0368a2b5396d1855311c5806`.
This document preserves that milestone's static implementation and acceptance.
The subsequent [thermal illumination feature](SMELTER_THERMAL_ILLUMINATION.md)
extends the idle-only behavior under separate November 9 owner authorization;
its November 9 owner acceptance is recorded in that document. Historical results
below are unchanged.
The November 5, 2026 owner authorization approves static integration and decisions
1A/2A/3A: retain the operating-status dot, local linear filtering with mipmaps,
and accepted idle illumination in every production state. It authorizes no Godot
execution by the agent and no thermal animation.

## Frozen provenance

The four external owner-accepted packages are Stage 1B / 2B / 3B / 4B Prototype v1
for 0 / 90 / 180 / 270 degrees respectively. The owner's implementation handoff
pins all four manifest identities. Historical pending-review labels remain in the
external manifests; the later owner authorization records acceptance.

| Direction | Package folder | Manifest SHA-256 |
| --- | --- | --- |
| 0 | `smelter_0_prototype_v1` | `7138460485af27067d33b8f0fa562e904c9857829f08c26fb41a19dad741e7d0` |
| 90 | `smelter_90_stage2b_v1` | `fd1632155ab1fddca29e341697f2cb3261f4bcb419bd8abb42c6951a24c5d1c4` |
| 180 | `smelter_180_stage3b_v1` | `530847fd5413fd5cd3c12972068e9366a9e08ad8a16a5ab629ec313c6cb34166` |
| 270 | `smelter_270_stage4b_v1` | `67164aa4317d7a6551b96aeb51e74c6cabaa8e4ac53b29250ba07176bee64338` |

All four manifests and ten runtime PNG hashes were checked before copying. The
ten [runtime PNGs](../assets/machines/smelter/) are byte-identical to their frozen
inputs. All 129 external package files were rehashed after copying with no
changes. No source masters, Aseprite documents, previews or package tools were
copied or executed. No artwork was resized, regenerated, re-encoded or edited.

The [complete frozen inventory](experiments/smelter_static_artwork.json) records
all ten encoded PNG hashes, decoded RGBA hashes, dimensions, crops, offsets,
source-master identities and idle-preview identities. The read-only preflight
independently verified PNG chunk CRCs, decoding, exact crop-to-master pixels,
four-pixel transparent padding and pixel-exact idle reconstruction for all views.
The integration tests reconstruct those same idle pixel identities without
depending on the external package locations.

Import sidecars were authored offline using the existing Extractor texture
conventions: lossless `compress/mode=0`, mipmaps enabled, no size limit, straight
alpha and unchanged channel mapping. Their cache references use the resource-path
MD5 convention and unique canonical ResourceUID text. No imported `.ctex` cache
or engine-generated metadata was committed. Owner F5 acceptance reported no new
Godot import, parser or runtime errors; the agent did not run an import test.

## Presentation and registration

[SmelterVisual](../construction/smelter_visual.gd) and its
[scene](../construction/smelter_visual.tscn) use ten shared preloaded textures
and four fixed Sprite2D slots: Body, Interior, Illumination, Foreground. Missing
interior/foreground textures in the other three directions are null and hidden.
The illumination slot is always hidden, including after direction changes.
Visible children preserve source-over sibling order; no additive material or
global foreground Z is introduced.

`configure(quarter_turns)` normalizes with `posmod(quarter_turns,4)` and returns
early for an unchanged direction. Textures are never mechanically rotated or
mirrored. Nodes are instantiated once; there is no Smelter per-frame callback,
runtime file/JSON parsing, generated texture, animation or production-state input.

All sprites are uncentered. The root is footprint-local `(64,128)` and uniformly
scaled by `4/29` (scene value `0.13793103448275862`). All master canvases are
1254x1254. For footprint origin O, source pixel p and directional anchor A:

`world(p) = O + (64,128) + (p - A) * 4/29`

| Direction | Anchor A |
| --- | --- |
| 0 | `(608,1096)` |
| 90 | `(628,1158)` |
| 180 | `(634,1128)` |
| 270 | `(625,1172)` |

Offsets already subtract A. Never subtract it again or center crops separately.

| Direction | Layer | Crop x,y,w,h | Offset x,y | Order |
| --- | --- | --- | --- | --- |
| 0 | body | `37,97,1188,1008` | `-571,-999` | 0 |
| 0 | interior | `600,657,229,281` | `-8,-439` | 1 |
| 0 | illumination (hidden) | `208,109,621,829` | `-400,-987` | 2 |
| 0 | foreground | `536,636,353,315` | `-72,-460` | 3 |
| 90 | body | `161,14,934,1156` | `-467,-1144` | 0 |
| 90 | illumination (hidden) | `556,28,200,320` | `-72,-1130` | 1 |
| 180 | body | `38,89,1170,1048` | `-596,-1039` | 0 |
| 180 | illumination (hidden) | `890,107,172,104` | `256,-1021` | 1 |
| 270 | body | `162,72,925,1115` | `-463,-1100` | 0 |
| 270 | illumination (hidden) | `524,275,206,359` | `-101,-897` | 1 |

At 0 degrees the cold interior and foreground remain visible. Other directions
show body only. Fixed bronze highlights, orange paint and amber accents remain
unchanged; disabling illumination does not recolor the body or simulate power.
The 4x4 footprint and 32-unit construction grid remain unchanged. Artwork may
overhang the logical 128x128 rectangle; no clipping or occupancy expansion occurs.

## Shared adapter, ghost and sorting

[MachineVisual](../construction/machine_visual.gd) selects the scene only for the
existing `smelter` item identity. Both deployed and ghost machines use this same
presenter, offsets, calibration and idle visibility. The existing Extractor
creation/configuration/motion branch is preserved. Switching away hides the old
subtree and stops Extractor production motion as before; retained-world re-entry
keeps the existing readiness and authoritative status-resampling behavior.

Deployed art uses a plain Node2D container. Only the ghost uses a CanvasGroup
with `self_modulate` alpha 0.5, fading the completed composite. Parent modulation
stays white; overlapping sprites are not individually faded. No group backbuffer
mipmaps or new clipping settings are enabled. Existing placement validity
outlines, world transforms and construction-controller Z=10 overlay remain.

DeployedMachine stays bottom-center anchored under exterior `GroundObjects` with
Y-sorting enabled, alongside Dave. The art subtree is locally unsorted, with
default Z=0. The 0-degree foreground occludes its own interior but cannot jump
above other Y-sorted objects. Interaction, collision and recovery use existing
logical geometry, not alpha bounds. Overhang sorting with Dave and neighboring
machines passed the owner F5 checks recorded below.

## Status dot and filtering

The deployed-only Smelter dot is a last sibling in MachineVisual, outside the
scaled art root and any ghost CanvasGroup. It uses the existing status polling
and radius 3.5. Its footprint-local positions for turns 0/1/2/3 remain
`(115,115)`, `(13,115)`, `(13,13)`, `(115,13)`, computed through the unchanged
`rotated_point(size - (13,13), turns)` mapping.

Existing producing green `(0.35,0.78,0.46)`, output-full amber `(0.94,0.69,0.28)`,
input-empty blue `(0.35,0.60,0.90)` and inactive gray `(0.55,0.58,0.59)` remain.
Fabricator's existing procedural status drawing uses the same extracted color
helper; its geometry and semantics are preserved. Ghosts never create the
Smelter status dot. Inspection remains the detailed operational feedback route.

The scene uses local `LINEAR_WITH_MIPMAPS` (4), matching Extractor conventions.
Global rendering, camera and filtering are unchanged. The ten RGBA8 textures
contain 5,380,938 pixels: approximately 20.53 MiB base / 27.37 MiB with a full mip
chain, estimates rather than measured GPU allocation. Resources are shared across
instances; only the active ghost needs compositing. Texture edges, readability
and ordinary multiple-machine responsiveness passed owner F5 acceptance. No
runtime memory measurements, benchmark or stress-test results are claimed.

## Static validation and exclusions

Run the focused checks from the repository root:

```powershell
Push-Location tests
python -B -m unittest -v static_smelter_artwork_test static_smelter_footprint_test static_extractor_artwork_test static_extractor_animation_test static_ferrite_integration_test static_v2_stationary_machines_test static_current_preservation_test static_preservation_guards_test static_terrain_stage3c_test
Pop-Location
```

Implementation results: **55/55 PASS**: new Smelter artwork 8, footprint 5,
Extractor artwork 5, Extractor animation 6, Ferrite integration 9, stationary
machines 8, current preservation 4, preservation guards 1, Stage 3C 9.
These are Python source/resource contracts and offline pixel comparisons only.
They do not execute GDScript or certify engine parsing, rendering or gameplay.

Acceptance-update revalidation on November 9, 2026: the same focused command
passed **55/55** again. Preservation checks confirmed all ten PNG hashes and ten
import configurations match the accepted implementation, with no code, test,
manifest or historical-evidence changes. Documentation links, original README
historical-content preservation and `git diff --check` passed. Only this document,
GAME_VISION and README changed. The original implementation results above remain.

Only invalidated presentation assertions in the three authorized existing test
files were amended. Shared property setters/readiness, exact Extractor lifecycle,
Fabricator drawing and all existing gameplay preservation remain checked.
Historical hashes, execution manifests, tools, safety policy, production state,
inventory, collision, inspection, recovery and stationary presentation are unchanged.
The agent performed no Godot import, headless test, graphical launch or runtime
performance probe. Owner F5 observations are recorded separately below.
Thermal timers/tweens, production-driven illumination, particles,
shaders, physical material ports and conduits are excluded.

## Owner normal-F5 acceptance

The owner reported completion of all 15 gameplay and graphical checks on
**November 9, 2026**, against accepted implementation commit
`36a5214761ea66398dd78b5077f6062ed84e96d3`. Result: **15/15 PASS**. No
observations, defects or blocking concerns were reported. The owner also reported
no new Godot import, parser or runtime errors. These are owner-observed F5
results, separate from the original 55/55 agent static results above.

All checklist items below passed. The documentation-only acceptance update
preserves the accepted implementation, all ten frozen PNGs, all ten import
configurations, manifests and tests. The agent did not execute Godot. PR #157
may proceed to review; merging still requires explicit owner authorization.

1. [x] Recover/deploy the Smelter and inspect all four independent directional illustrations.
2. [x] Confirm stable bottom-center registration and 4x4 grid alignment in every direction.
3. [x] Rotate placement ghosts through repeated complete cycles, including negative-world cells.
4. [x] Compare ghost/deployed silhouettes and registration; check composite transparency and switching among all three machine types.
5. [x] Review scale beside Dave and readability at zoom 0.5, 1.0 and 1.5.
6. [x] Inspect transparent edges, seams and local mipmapped filtering on light/dark terrain.
7. [x] Check overhang remains visible while collision/placement retain the logical footprint and exact-edge adjacency.
8. [x] Walk Dave in front of/behind each direction; check sorting beside neighboring machines.
9. [x] Deploy several mixed-direction Smelters and check ordinary movement, camera, placement and UI responsiveness; no benchmark/stress test implied.
10. [x] Confirm the dot is visible above deployed art, hidden on ghosts, correctly positioned and correctly colored for input-empty/producing/output-full states.
11. [x] Confirm every production state retains idle illumination; 0-degree cold interior and foreground remain intact, with authored warm details unchanged.
12. [x] Inspect, transfer ore and collect ingots; check unchanged rates, capacities and 96-unit center-based reach, including accepted corner limitations.
13. [x] Use B recovery and redeploy; packaged machine and stored materials return exactly once, with unchanged nearest-footprint reach.
14. [x] Travel exterior -> interior -> exterior; confirm retained direction, status, buffers and artwork without duplicates.
15. [x] Recheck Extractor artwork/animation, Fabricator, Dave and stationary Smelter presentation/E recovery.
