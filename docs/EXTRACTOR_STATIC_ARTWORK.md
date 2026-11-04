# Extractor static directional artwork (PR A, pending merge)

Implemented on `codex/extractor-static-artwork`, based on merged PR #153 at
`0a0003444be0ba4b67e7ab6c8fa678abbf740b34`. This draft integrates the owner's
four frozen directional packages for deployed Extractors and placement ghosts.
Owner F5 acceptance remains pending. No animation or operating-state artwork is
implemented; the barrel remains raised in every state. PR B is separate work.

## Provenance and immutable inputs

The owner supplied all four `TLWH_Extractor_{direction}_Prototype_v1.zip` files.
0 and 270 identities are pinned by the integration handoff. The hash-pinned
270 manifest's `baseline_90` and `baseline_180` records supply the other two
trusted identities, corroborated by its `previews/preservation_validation.json`.
Historical package `awaiting_owner_review` metadata is preserved; the later
integration handoff records owner acceptance of all four. No archive is edited,
executed, copied into the repository or regenerated.

| Direction | Archive SHA-256 |
| --- | --- |
| 0 | `59fd666a3206641172fb934766a9717e148333143468be5ffabbb57c617e81ef` |
| 90 | `db8e1302e8696ee13dcf7f8d61f0c5d0920cea74a1b43ecaf08baa78cf62ad05` |
| 180 | `cb71fd45fbcf103e93853333fb740e4f0a93b932434896dae139439c92dc0647` |
| 270 | `021286d810d25fe5cd91d749cfa05d3440b7f61ccfb484aeb391d1923486f467` |

The [complete SHA-256 and manifest inventory](experiments/extractor_static_artwork.json)
records all 12 PNG identities, source-layer hashes, crop sizes, offsets, anchor,
scale and output identities. The runtime PNGs are byte-identical copies, with
lossless mipmapped `.png.import` metadata authored offline using existing texture
import conventions. No engine-generated cache is included. Import behavior has
not been verified by Godot.

## Presentation contract

`MachineVisual` selects [ExtractorVisual](../construction/extractor_visual.tscn)
only for `item_id == extractor`. Its [controller](../construction/extractor_visual.gd)
has 12 shared preloaded textures, three Sprite2Ds, explicit per-direction offsets
and `posmod(turns,4)` selection. Definition/direction setters refresh only on
changes. There is no runtime manifest/ZIP parsing, texture creation, animation,
new per-frame callback or status wiring. The old procedural Extractor and its
status dot are replaced by neutral frozen artwork. The existing deployed status
polling remains unchanged; it cannot move or recolor this art.

Within the existing bottom-center Y-sorted deployed-machine subtree, the sprites
stay in sibling order body, raised barrel, foreground. All have local Z=0 and
`centered=false`; the foreground has no global Z override. The art root is at
footprint-local `(64,128)` with uniform scale `0.11387900355871886`. For footprint
origin O and master pixel p, `world(p)=O+(64,128)+s*(p-(632,1139))`.
Offsets below already subtract the master anchor. Narrow 90/270 silhouettes are
not stretched. Raster coordinates do not certify physical conduit attachments.

| Direction | Layer | Crop x,y,w,h | Anchor-relative offset x,y |
| --- | --- | --- | --- |
| 0 | body | `66,37,1132,1107` | `-566,-1102` |
| 0 | barrel | `320,274,173,418` | `-312,-865` |
| 0 | foreground | `296,266,238,462` | `-336,-873` |
| 90 | body | `149,15,966,1128` | `-483,-1124` |
| 90 | barrel | `588,265,185,224` | `-44,-874` |
| 90 | foreground | `276,256,706,734` | `-356,-883` |
| 180 | body | `69,21,1127,1122` | `-563,-1118` |
| 180 | barrel | `763,253,179,425` | `131,-886` |
| 180 | foreground | `741,241,223,463` | `109,-898` |
| 270 | body | `107,15,1050,1128` | `-525,-1124` |
| 270 | barrel | `534,268,206,431` | `-98,-871` |
| 270 | foreground | `436,236,368,503` | `-196,-903` |

| Turns | Artwork | Output edge | Output 1 | Output 2 |
| --- | --- | --- | --- | --- |
| 0 | 0 degrees | Right | Upper | Lower |
| 1 | 90 degrees clockwise | Bottom | Right | Left |
| 2 | 180 degrees clockwise | Left | Lower | Upper |
| 3 | 270 degrees clockwise | Top | Left | Right |

Directions select textures; no sprite rotation or reflection occurs. Output
identities are artwork only; no separate port inventory or coordinates are added.

The same scene and transforms serve deployed and ghost Extractors. Only the ghost
creates one CanvasGroup, using `self_modulate` alpha 0.5 on the completed composite,
as specified by [Godot's CanvasGroup documentation](https://docs.godotengine.org/en/stable/classes/class_canvasgroup.html).
Children remain opaque during compositing, hiding the barrel continuation.
Switching to another machine hides the Extractor subtree and restores the previous
procedural ghost opacity. Existing validity outline, GUI suppression, cancellation,
placement transforms and ghost overlay ordering are unchanged. Deployed Extractors
use a plain Node2D container. CanvasGroup backbuffer mipmaps stay disabled;
Extractor-local texture filtering uses LINEAR_WITH_MIPMAPS (4), independent of
project defaults and stationary art. Actual filtering and composite appearance
require later owner review.

The 12 RGBA8 images total 5,986,794 source pixels: approximately 22.84 MiB base,
30.45 MiB with a theoretical full mip chain. These are estimates, not measured
GPU allocation or performance. Texture resources are shared across instances.
Compositing is bounded to the single placement ghost. Exterior loading, initial
rotation and deployed-count responsiveness remain unverified.

## Validation and limits

Nonexecuting commands:

```powershell
python -B -m unittest discover -s tests -p static_extractor_artwork_test.py
python -B tests/extractor_artwork_offline.py --packages <directory-containing-the-four-ZIPs>
python -B -m unittest discover -s tests -p 'static_*test.py'
git diff --check
```

The offline verifier uses only Python stdlib. It reads configured texture paths
and offsets from the implementation, decodes RGBA8 PNGs with chunk CRC checks,
compares reconstructed full layers byte-for-byte, and composites in source-pixel
space using integer straight-alpha source-over rounding matching the documented
package raster convention. It compares both the independently retained cleaned
master and raised preview for every direction. It never executes archive scripts
or writes images. This verifies assembly, not Godot filtering or artistic fidelity
to the original concept studies.

| Gate | Result / scope |
| --- | --- |
| Archive provenance and 12 exact PNGs | PASS: four trusted identities, CRC and byte equality |
| Manifest fidelity | PASS: all 12 sizes/offsets, anchor, scale, layer order and references |
| Direction mapping | PASS: static selection and package output identities; visual readability pending |
| Anchor arithmetic | PASS: root (64,128), one anchor subtraction, 128x128 guide |
| Raised reconstruction | PASS: zero differing RGBA pixels in all four masters and all four raised previews; all 12 full layers exact |
| Ghost/deployed parity | PASS: shared scene and transforms; composite appearance unverified |
| Static barrel | PASS: no added motion, status wiring or per-frame processing |
| Local sorting | PASS: source hierarchy and sibling order; graphical occlusion unverified |
| Gameplay preservation | PASS: baseline checks protect production, definition, collision, recovery and interaction |
| Other machines | PASS: Smelter/Fabricator draw functions and stationary scene/art unchanged |
| Hygiene | PASS: 401/401 static tests (289.227 seconds); 7 changed local Markdown links; diff check |
| Engine / F5 / runtime performance | NOT VERIFIED: none run or authorized by this task |

The prior footprint and computer-restoration preservation tests allow exactly the ghost-opacity flag
replacement in `ConstructionController`; a new baseline comparison protects every
other controller byte. The consumed Stage 3C plan still checks its original MachineVisual and pre-PR-153 Extractor resource
from Git;
its immutable receipt is unchanged. Native runner, execution controls, native test
assertions and staging inventory remain unchanged. Static success grants no
engine permission. See [execution policy](../AGENTS.md#godot-execution-safety) and
[local testing](LOCAL_TESTING.md).

## Later owner F5 checklist

Every item is initially **NOT TESTED**; no F5 or performance run is authorized here.

- [ ] 0 degrees: right-edge outputs; ghost and deployed match raised artwork.
- [ ] 90 degrees: bottom-edge outputs; ghost and deployed match.
- [ ] 180 degrees: left-edge outputs; ghost and deployed match.
- [ ] 270 degrees: top-edge outputs; ghost and deployed match.
- [ ] R rotation: four correct selections, no spin/mirror, anchor drift or preview mismatch.
- [ ] Scale/placement: 4x4 alignment, ground contact and unchanged Dave-relative scale.
- [ ] Layer occlusion: barrel/foreground overlap, no doubled edges, holes, seams or halos.
- [ ] Ghost opacity: whole-composite fade, concealed continuation, validity outline and cancellation.
- [ ] Zoom/filtering: inspect 0.5, 1.0 and 1.5 where available for aliasing, shimmer or blur.
- [ ] Y sorting: Dave in front/behind and adjacent machines.
- [ ] Placement: snapping, Ferrite eligibility, obstacles, collision and adjacency.
- [ ] Gameplay: inspection, collection, B recovery/redeployment, extraction and output-full.
- [ ] Other machines: Smelter/Fabricator and stationary maintenance-bay Extractor.
- [ ] Performance: exterior entry, first rotation, ghost movement and representative counts; record conditions.
- [ ] No animation: raised barrel remains motionless in every state.

Carry forward the nonblocking 270-degree socket-readability concern. Do not alter
frozen artwork preemptively. Shallow-motion readability belongs to later PR B.
Merge and any engine execution require separate owner authorization. No cleanup
or changes to simulation, grid, definitions, Dave or stationary artwork are included.
