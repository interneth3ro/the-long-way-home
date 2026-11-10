# Extractor directional artwork and barrel animation

Static artwork merged in PR #154 at `c5729c00f8d4055ac900e1b6221fe32a3e1ad5e6`,
after footprint PR #153 at `0a0003444be0ba4b67e7ab6c8fa678abbf740b34`.
The PR B handoff records the four directional treatments as owner-accepted.
Animation on `codex/extractor-barrel-animation` has final owner F5 acceptance:
**16/16 PASS, zero blocking defects**, reported 2026-11-04. PR #155 merged at
`461950a2c379ae3039b30d682b530180de645f72`. Earlier PR A/B verification below
retains its historical scope; it does not accept the new port-free body integration.

## Port-free runtime bodies v1 — feature branch, pending merge

Owner Decision 2A authorizes four exact fixed-crop derivatives of the artistically
accepted `TLWH_Extractor_PortFree_Artwork_v1.zip`. On
`codex/extractor-port-free-runtime-v1`, only the four active body PNGs are replaced.
All eight original barrel/foreground PNGs, all twelve import sidecars, presenter
scripts/scenes, registration, animation, footprint and gameplay remain unchanged.
Godot execution is **NOT RUN**; owner F5 acceptance of this integration is **PENDING**.

The [new derivative record](experiments/extractor_port_free_runtime_v1.json)
pins the ZIP (`35d8dc1d2e9c88ff7634c2403a864efa968e6a39829ced524dda76c5f27fe8d3`),
aggregate manifest, receipt, four approved full-canvas sources, exact output PNG
and decoded RGBA identities, original body identities and eight preserved layers.
External absolute source locations are not published. Original prototype archives,
acceptance records and the historical inventory below remain immutable.

The 1254x1254 approved bodies are cropped with the existing body rectangles in
the presentation table below. Exact RGBA row slices, including transparent RGB,
are encoded using Python 3.14.7 standard-library struct/zlib, zlib runtime
`1.3.1.zlib-ng`, filter 0 and compression level 9, with IHDR/IDAT/IEND only.
Every written PNG independently decodes to the exact approved crop. No nonzero
RGBA pixels lie outside those fixed rectangles. There is no alpha trimming,
resampling, recoloring, new crop geometry or registration adjustment.

Historical checks read original runtime bytes from fixed Git revision
`1a3d3dcc1b4503585a2e49f4bf5832d650f600de`; missing history fails explicitly.
The original package/master/pose comparisons keep their original expected hashes.
Active artifact checks use the new record; complete source reconstruction also
requires the frozen ZIP and receipt. The three Fabricator preservation guards
admit exactly the four body paths, plus this derivative JSON where needed, while
checking exact active identities. No directory-wide exception is introduced.

Read-only offline commands (no Godot, extraction, or image writes):

```powershell
python -B tests/extractor_artwork_offline.py --active
python -B tests/extractor_artwork_offline.py --freeze <port-free-ZIP> --receipt <port-free-receipt>
python -B tests/extractor_artwork_offline.py --packages <original-ZIP-directory> --motion
python -B -m unittest discover -s tests -p 'static_*test.py'
```

`--active` alone verifies committed artifact identities and explicitly reports
source reconstruction NOT RUN. It never substitutes local body bytes for missing
historical Git blobs. The frozen archive's retained 32-pose PASS remains historical
evidence; its embedded verifier is not executed by these commands. New derivative
identity/pixel checks do not establish Godot importing, filtering, fractional
animation rendering, performance, or graphical acceptance. The original 16/16
owner animation acceptance below remains evidence for that earlier milestone.

Stage 2 offline validation: **16/16 focused Extractor tests PASS** and the full
static suite **471 tests, OK (2 optional external Fabricator-package tests skipped)**
in 309.256 seconds. Active artifact identities, all four exact frozen-source crop
comparisons, and the original-package historical reconstruction/32 integer poses
PASS. The protected tracked-file audit and all twelve import byte identities PASS;
the three added/changed local Markdown links and `git diff --check` PASS.
These results do not establish engine or owner runtime acceptance.

### Owner F5 acceptance — all PENDING

1. Inspect construction ghosts in all four orientations.
2. Verify approved bodies, stable anchors and ghost transparency.
3. Deploy all four orientations and verify footprint alignment.
4. Confirm production animation completes its unchanged 1.6-second cycle.
5. Check barrel/foreground occlusion at raised, lowered and intermediate positions.
6. Verify inactive and output-full machines stop with the barrel raised.
7. Rotate ghosts and inspect deployed machines at different camera zoom levels.
8. Check continuous fractional-position motion for shimmer, seams, halos, clipping or drift.
9. Walk Dave around machines; inspect Y sorting and neighboring-machine overlap.
10. Verify extraction, ore collection, output capacity, recovery and redeployment.
11. Re-enter the exterior and verify presentation and animation lifecycle.
12. Check ordinary-play responsiveness, visual artifacts and debugger/import errors.

These checks are for the owner after PR review. No benchmark or prolonged runtime
test is included, and no owner result is inferred from static checks.

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
records the historical 12 PNG identities, source-layer hashes, crop sizes, offsets,
anchor, scale and output identities. At PR A the runtime PNGs were byte-identical copies, with
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

## Barrel animation (PR B)

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
a restrained smooth reversal without sharp impacts. Owner F5 acceptance covers
the observed implementation; timing and amplitude retain their provisional
presentation designation. This 1.6-second loop has no relationship to the one-second
ore cycle. Package checkpoints are 0/8/3/0 for 0 and 90, and 0/6/3/0 for 180 and
270, confirmed from the actual manifests; they are comparison poses, not timed
runtime keyframes. No sound, particles or new gameplay states are added.

`DeployedMachine` retains its exact existing `_process` status poll, including
the changed-status guard. Its new `_enter_tree` samples the authoritative record
before child readiness, skipping the entry sample if `configure()` has not yet
initialized both state and visual. This covers already-producing creation and
retained exterior re-entry, including a status change while detached. Scalar Extractor
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
| Full static suite (before entry-guard correction, `53df809`) | PASS: 406/406 in 292.214 seconds via `python -B -m unittest discover -s tests -p 'static_*test.py'` |
| Entry-guard correction | PASS: 12 Extractor, 9 Ferrite integration and 9 Stage 3C static tests; full suite not rerun for this two-line guard |
| Status-setter syntax correction | Added the missing property-declaration colon reported by the owner's debugger; new check fails before and passes after the fix. Of 13 focused Extractor tests, 12 pass; the unchanged metadata-preservation test reports five pre-existing local UID differences. All 12 local sidecars are preserved and excluded from the correction. Full suite not rerun; agent Godot verification remains NOT VERIFIED. |
| Documentation hygiene | PASS: 126 local Markdown targets, documentation-sync and `git diff --check` |
| Agent Godot import / parse / runtime / F5 / performance / actual filtering | NOT VERIFIED by the agent: no engine invocation performed; subsequent owner F5 results are recorded separately below |

PR B narrowly amends the PR A no-animation guard to permit Tween while retaining
resource/polling prohibitions. Its deployed-presenter byte guard moves to a new
test that allows exactly the documented `_enter_tree` block; the older footprint
guard removes only that block before its original comparison. New checks retain
all other presenter bytes, scene/import bytes, texture/offset declarations and
all existing unrelated preservation guards. The consumed Stage 3C plan reads
its original deployed presenter from Git, like its existing MachineVisual snapshot;
the historical plan/receipt bytes and hash pins remain unchanged. Execution
controls remain unchanged.

## Final owner F5 acceptance — 2026-11-04

The owner reports **16/16 PASS, zero blocking defects** for PR #155 after the
initialization-guard (`4483dd8`) and status-setter syntax (`7205599`) corrections.
These are owner-observed F5 results, separate from the agent's static validation.
No agent Godot execution or formal performance benchmark is claimed.

| Acceptance check | Owner result |
| --- | --- |
| 0-degree animation | PASS |
| 90-degree animation | PASS |
| 180-degree animation | PASS |
| 270-degree animation | PASS |
| Layer continuity | PASS |
| Producing state | PASS |
| Inactive state | PASS |
| Output-full transition | PASS |
| Placement ghost | PASS |
| Rotation | PASS |
| Recovery and redeployment | PASS |
| Exterior exit and re-entry | PASS |
| Zoom readability | PASS |
| Sorting and rendering | PASS |
| Performance | PASS |
| Gameplay regressions | PASS |

Animation is extremely subtle and barely perceptible at maximum zoom-out. The
owner explicitly accepts this as a **nonblocking visual limitation**. The owner
confirms animation functions, performance is unaffected in observed gameplay,
and no rendering or gameplay regressions were observed. The accepted
asset-production and integration process is considered successful. No measured
counts, timings or benchmark results were supplied. The prior nonblocking
270-degree socket-readability observation remains historical context, not a
request to edit frozen artwork. The 8/8/6/6-pixel strokes and 1.6-second loop stay
unchanged and provisional.

Additional output-full verification is **PASS**: the barrel stopped when the
buffer reached capacity, matching the machine information panel's state; it did
not restart while full, including after entering the ship and returning outside.
Restart after output collection was not separately documented and is not inferred
from this acceptance record.

## Owner-import sidecar audit — 2026-11-04

Read-only inspection used the existing owner-generated files against PR HEAD
`7205599`; no Godot launch, reimport, cache regeneration or metadata reconstruction
was performed. At preflight all 12 Extractor PNG sidecars were reported modified,
with no untracked nonignored files. Five have only the UID text changes below;
the other seven have only line-ending differences. No other tracked import
metadata had content changes. All twelve frozen PNG hashes match the unchanged
[provenance inventory](experiments/extractor_static_artwork.json).

| Included sidecar under `assets/machines/extractor/` | Previous UID text | Owner-generated canonical UID text |
| --- | --- | --- |
| `extractor_0_barrel.png.import` | `b9553028581b` | `ca553028581b` |
| `extractor_90_body.png.import` | `bb5dbe9b0a32` | `bb5dbfab0a32` |
| `extractor_90_barrel.png.import` | `b073c49412a2` | `b073c5a412a2` |
| `extractor_180_body.png.import` | `bb4e10e3493f` | `bb4e10e35a3f` |
| `extractor_180_foreground.png.import` | `bfd19198db79` | `bfd2a2a8db8a` |

For each pair, offline decoding confirms **the same numeric resource ID**, and
the new text is canonical under [Godot 4.7.2's ResourceUID encoding](https://github.com/godotengine/godot/blob/4.7.2-stable/core/io/resource_uid.cpp#L38-L102).
The five portable sidecars are included to preserve the owner's canonical import
metadata on another checkout and avoid repeated text rewrites. These are not new
resource identities. Every other normalized metadata byte matches the committed
version: source paths, generated cache paths, compression mode 0, mipmap generation,
alpha-border/premultiplication settings and all other parameters remain unchanged.
No filtering, transparency or performance-setting change requires acceptance.
Numeric IDs are unique across the twelve textures and do not collide with other
tracked resource declarations. The preservation test admits only these five exact
UID replacements and still compares every other metadata byte to PR A.

The seven excluded sidecars are 0 body/foreground, 90 foreground, 180 barrel,
and all three 270 layers. Their existing working bytes remain untouched; no
line-ending-only change is committed. All twelve current sidecar byte hashes
were captured and rechecked during closeout. Four relevant script UID files
(`extractor_visual`, `machine_visual`, `deployed_machine`, `construction_controller`)
and the shared scene match HEAD. Texture preloads and scene/script references
remain path-based and unchanged; no new UID files or scene/resource edits are
needed. There are no unexpected untracked or ignored sidecars in the Extractor
asset or construction directories.

The existing ignored `.godot/imported/` inventory contains 12 Extractor `.ctex`
and 12 matching `.md5` files. These and the rest of `.godot/` are local generated
cache, excluded from the PR and preserved. Inspection of existing metadata/cache
paths is not fresh engine-import verification.

Closeout validation: **13/13 PASS** via
`python -B -m unittest discover -s tests -p 'static_extractor*test.py'`;
**127 local Markdown targets PASS**, documentation-sync and `git diff --check`
PASS. The offline audit above also passed PNG identities, exact UID-only metadata
comparison, numeric-ID parity/uniqueness, tracked declaration collision checks,
and unchanged scene/script UID checks. These are static/read-only checks, not
engine import verification. The earlier full 406-test run belongs to
`53df809`; it was not rerun after the later guard or syntax corrections or this
documentation/UID-only closeout. Earlier archive/raster checks retain their
original scope. No animation, gameplay, source artwork or execution control is
changed by closeout. At that closeout PR #155 remained unmerged; no cleanup was included.
