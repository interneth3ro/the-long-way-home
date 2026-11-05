# Extractor directional artwork and barrel animation

Static artwork merged in PR #154 at `c5729c00f8d4055ac900e1b6221fe32a3e1ad5e6`,
after footprint PR #153 at `0a0003444be0ba4b67e7ab6c8fa678abbf740b34`.
The PR B handoff records the four directional treatments as owner-accepted.
Animation on `codex/extractor-barrel-animation` remains pending review, owner F5
acceptance and merge. Earlier PR A verification below retains its historical scope.

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
changes. There is no runtime manifest/ZIP parsing, texture creation or new
per-frame callback. PR B adds the status adapter and barrel-only motion described
below. The old procedural Extractor and its
status dot are replaced by neutral frozen artwork. The existing deployed status
polling remains unchanged; PR B forwards its status to presentation only.

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
python -B tests/extractor_artwork_offline.py --packages <directory-containing-the-four-ZIPs> --motion
python -B -m unittest discover -s tests -p 'static_extractor*test.py'
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
| Static barrel (historical PR A) | PASS at PR A: superseded only by the PR B animation below |
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

## Barrel animation (PR B, pending merge)

Only the Barrel Sprite2D receives tweened `position` values, from its unchanged
raised offset to that offset plus positive local Y. Positive Y is down in all
four accepted manifests. The parent already supplies the display scale; motion
does not apply it again. Body, foreground, root, anchor, scene geometry, texture
bytes, import settings, output mapping and the 4x4 footprint remain unchanged.

| Turns / direction | Maximum source-pixel travel | Approximate world travel |
| --- | --- | --- |
| 0 / 0 degrees | 8 | 0.9110 |
| 1 / 90 degrees | 8 | 0.9110 |
| 2 / 180 degrees | 6 | 0.6833 |
| 3 / 270 degrees | 6 | 0.6833 |

`STROKE_PX` is presentation-only and provisional. The provisional implementation
uses 0.8 seconds down and 0.8 seconds up, sine transition with in/out easing:
a restrained smooth reversal without sharp impacts. The owner has not approved
an exact playback rate. This 1.6-second loop has no relationship to the one-second
ore cycle. Package checkpoints are 0/8/3/0 for 0 and 90, and 0/6/3/0 for 180 and
270, confirmed from the actual manifests; they are comparison poses, not timed
runtime keyframes. No sound, particles or new gameplay states are added.

`DeployedMachine` retains its exact existing `_process` status poll, including
the changed-status guard. Its new `_enter_tree` samples the authoritative record
before child readiness. This covers already-producing creation and retained
exterior re-entry, including a status change while detached. Scalar Extractor
output-full transitions therefore do not depend on recipe notifications.
`MachineVisual.status` forwards changes through its existing presentation adapter:
only PRODUCING and non-ghost enables `set_producing(true)`. INACTIVE, OUTPUT_FULL,
INPUT_EMPTY and any other nonproducing value disable it. Ghosts remain raised
even if their status is producing. Smelter/Fabricator drawing is unchanged.

The visual owns at most one node-bound Tween. Repeated producing calls and
same-direction calls return without starting another. Stop kills and releases
the Tween before restoring the raised offset. Direction changes stop/reset,
select the existing textures/offsets, then resume only if producing. Switching
away from the Extractor definition stops the hidden subtree. Extractor tree exit
clears producing, kills motion and restores raised position, covering recovery,
free and exterior detach. Redeployment uses a fresh presenter and machine record.

Godot calls `_ready` once by default. The adapter therefore requests readiness
again on exit, then refreshes after children enter on re-entry. The refresh guard
requires both readiness and tree membership, so a parent's initial status sample
cannot animate a detached child. This is the narrow lifecycle reason for the
adapter change. See the official [Node lifecycle documentation](https://docs.godotengine.org/en/stable/classes/class_node.html#class-node-method-request-ready)
and [Tween binding documentation](https://docs.godotengine.org/en/stable/classes/class_tween.html#class-tween-method-bind-node).
There are no added per-frame callbacks, secondary status polls, deferred callbacks,
runtime resource loads, texture copies, or simulation/inventory mutations.

### PR B static and offline verification

The commands above run without Godot. The animation extension `--motion` reads
the implementation's existing configured layers and package poses, composites
all 32 integer positions (9/9/7/7), and rejects out-of-canvas clipping and any
formerly opaque pixel becoming fully transparent. All 32 passed with zero such
holes; the 12 raised/downstroke/return package comparisons have zero differing
RGBA pixels. These establish parity with the package occlusion/hidden-continuation
references, not artistic acceptance or fractional-pixel filtering behavior.

| Gate | PR B result / evidence |
| --- | --- |
| Baseline preservation | PASS: all four archive SHA-256 pins above, CRC, 12 PNG byte hashes, full layers and import metadata preserved |
| Architecture / amplitudes | PASS static: barrel-only Tween, unchanged offsets and scale, positive Y 8/8/6/6 |
| Status authority / initialization | PASS source contracts: existing poll and initial status retained, entry resample, producing-only forwarding, ghost exclusion |
| Transitions / lifecycle / idempotence | PASS source contracts: stop/reset, direction restart, tree exit, re-entry readiness; runtime NOT VERIFIED |
| No duplication / gameplay preservation | PASS static: one Tween creation site; no new process callback; simulation, placement, recovery, other machines and stationary art unchanged |
| Offline geometry | PASS: 32 bounded integer poses, zero new fully transparent holes, 12 exact package pose comparisons |
| Focused static checks | PASS: 12 tests via `python -B -m unittest discover -s tests -p 'static_extractor*test.py'` |
| Full static suite | PASS: 406/406 in 292.214 seconds via `python -B -m unittest discover -s tests -p 'static_*test.py'` |
| Documentation hygiene | PASS: 126 local Markdown targets, documentation-sync and `git diff --check` |
| Godot import / parse / runtime / F5 / performance / actual filtering | NOT VERIFIED: no engine invocation authorized or performed |

PR B narrowly amends the PR A no-animation guard to permit Tween while retaining
resource/polling prohibitions. Its deployed-presenter byte guard moves to a new
test that allows exactly the documented `_enter_tree` block; the older footprint
guard removes only that block before its original comparison. New checks retain
all other presenter bytes, scene/import bytes, texture/offset declarations and
all existing unrelated preservation guards. The consumed Stage 3C plan reads
its original deployed presenter from Git, like its existing MachineVisual snapshot;
the historical plan/receipt bytes and hash pins remain unchanged. Execution
controls remain unchanged.

## Owner F5 animation acceptance checklist

Every item is initially **NOT TESTED**; no F5 or performance run is authorized here.

- [ ] 0 degrees: clean producing motion; right-edge output identities preserved.
- [ ] 90 degrees: clean motion/occlusion; bottom-edge output identities preserved.
- [ ] 180 degrees: clean motion/occlusion; left-edge output identities preserved.
- [ ] 270 degrees: clean motion/occlusion; top-edge identities and socket readability.
- [ ] Raised/return: no seam, transparency hole, double collar, floating head or concealed continuation.
- [ ] Producing: starts correctly; extraction rate and output quantity unchanged.
- [ ] Inactive: raised and stationary.
- [ ] Output full: raised and stationary; collection restarts motion only when producing.
- [ ] Ghost: always raised/stationary; composite opacity and validity outline correct.
- [ ] Rotation: all four selections, correct offsets, no drift/spin or animation ghost artifacts.
- [ ] Recovery/redeployment: no stuck motion/orphan Tween; equipment and stored ore conserved.
- [ ] Exterior exit/re-entry: stop/reset; resume from authoritative state; production unchanged.
- [ ] Zoom 0.5/1.0/1.5: record whether provisional 6/8-pixel motion is perceptible.
- [ ] Sorting/rendering: Dave and adjacent machines; no mipmap shimmer, ghost halo or filtering artifacts.
- [ ] Performance: arrival, multiple active Extractors and repeated placement/recovery; record counts/conditions.
- [ ] Regression: Smelter, Fabricator, stationary Extractor, Ferrite production/collection, interaction and recovery.

Carry forward the nonblocking 270-degree socket-readability concern. Do not alter
frozen artwork preemptively. Record subtle motion as a usability observation;
do not silently increase provisional stroke amplitudes.
Merge and any engine execution require separate owner authorization. No cleanup
or changes to simulation, grid, definitions, Dave or stationary artwork are included.
