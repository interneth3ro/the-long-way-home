# Stage 3B — visible continuous terrain laboratory

**2026-11-03; feature branch, pending merge and owner visual acceptance.**
Implementation authority comes from the owner's Stage 3B handoff; execution
authority does not. See the dated [architecture amendment](terrain_stage3_architecture_decisions.md#owner-amendment--2026-11-03-isolated-visible-stage-3b-laboratory).

The standalone [scene](../../scenes/experiments/terrain_stage3b/lab.tscn) calls the
real `ContinuousTerrainMetadata.prepare()` for seed **26026**, once per frame for
exactly `(-1,-1), (0,-1), (-1,0), (0,0)`. It retains the original 34×34 byte
material payload per chunk, including Green IDs 1–4. There is no production
presenter, world state, streaming, save mutation or runtime disk write. All four
surfaces stay behind a curtain until preparation succeeds; a detected failure
latches, hides surfaces and stops preparation. Missing scripts, parse errors and
GPU failures still require the supervising operator to stop the process.

## Reconstruction and presentation

The shader fetches four binary Earth/Green labels from the original IDs. For local
pixel `p`, `q=(p-32)/64`, `cell=floor(q)`, `f=fract(q)` and
`w=f*f*(3-2*f)`. Bilinear interpolation with weights `w` produces `v`; coverage is
`smoothstep(5/32,27/32,v)`. There is **no protection multiplier P** or replacement
crash-site mask. Exact original center endpoints are the mathematical design
objective, not a claim of GPU parity. Original generator exclusions remain intact.

Each numerical image is created in memory as **34×34 R8 without mipmaps**.
Unmodified IDs 0–4 occupy normalized red values `id/255`; level-zero
`texelFetch(cell+1)` and `round(red*255)` recover them before testing `id>0`.
There is no `source_color` hint, color conversion or texture interpolation on ID
fetches. At owned pixel 0, the supporting centers are local -1/0; at 2048 they
are 31/32. Neighboring chunks therefore fetch the same absolute centers. Halo
samples may lie beyond the owned `[-16,15]` study envelope; the unchanged builder
supports that contract. This lab selects only four owned chunks within it.

Frozen C1 Earth/Green PNGs, fixture, phase textures and field textures are read
unchanged. The four overlapping 512-unit windows use C1's scale/offset formula,
absolute-coordinate SHA-256 phase identities and explicit artwork gradients.
The phase texels also use exact level-zero fetches; the frozen C1 identity string
is `c1_fields_v1:c1_materials_v1:26026:X:Y:material`. No floating-point hash is
used. The existing field's G/B macro/detail channels retain C1 shading; its red
coverage channel is unused. Artwork uses imported linear filtering with **no
runtime mipmap generation**. C1's former runtime-generated artwork mipmaps are
absent; compare minification at 0.5× explicitly before accepting this difference.

**Absent production behavior:** neutral production tint; no terrain state edits,
ordered production color overlays, ship/contact shadow, Ferrite, decorations,
player, collision or gameplay. Classification still receives the original
authored polygons, feathers and anchors from the preserved C1 fixture. This is
a ground-only crash-area view. Production tint/overlay precedence is unchanged
in production and is not validated or represented by the C1 G/B shading.

Preparation is capped at four jobs of 1,156 center samples each, one job/frame,
with four retained dictionaries/surfaces, four 1,156-byte ID texture payloads,
four 7×7 phase textures, four 137×137 C1 fields and two shared 1254×1254 sources.
No eviction/rebuild loop exists. These are inventory bounds, not measured frame
time or engine/GPU memory. Per-chunk metadata preparation is synchronous and
unprofiled; the production slice/performance targets remain unverified.

## Proposed owner visual run — requires separate explicit approval

The lab code is ready to submit for an authorized visual run. **No stage was
created and no Godot process was launched.** Neither `Native` nor inactive
`MetadataSmoke` can dispatch this scene. Do not change either runner to do so.
Approve a reviewed one-time staging/execution amendment for the final commit,
the exact inventory and commands below before proceeding. An operator or reviewed
bounded supervisor must enforce the limits; the commands alone do not enforce
timeouts/output caps. No additional runner subsystem is included in this PR.

1. Require the full Python static suite to pass and recheck the exact seven-file
   PR scope, source/index/status hashes, protected sidecars and frozen assets.
   Verify the standard executable SHA-256 is
   `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.
2. After approval only, create a fresh unique directory
   `D:\GameDev\Godot\TLWH-NativeStages\stage3b-<unique-id>` outside the checkout.
   Copy only the **52** tracked inputs defined below, preserving relative paths
   except the two existing metadata-fixture mappings. Recheck source/stage hashes
   before each launch; never reuse a stage or run in the checkout.
3. Run exactly one cold import (60 seconds maximum), sequentially, with clean
   completion required before the visual launch. This imports only ten frozen
   C1 PNGs and the listed resources. Godot may create `.godot/` data and new UID
   sidecars for the new lab script/shader **in the disposable stage only**; retain
   them there and never copy generated data back. Existing imported PNG sidecar
   bytes must remain unchanged; stop if the engine rewrites them.
4. Rehash the pinned executable. Run exactly one graphical session, 1280×720,
   capped at **180 seconds** for the comparisons below. No performance probe,
   benchmark, automation interaction, screenshot generation or gameplay run is
   included. Stop immediately on responsiveness symptoms, shader/parse errors,
   missing assets, failed preparation, changed identity or uncertain termination.
   No automatic retry. A second session requires a new grant.
5. Each process has a **1,048,576-byte combined output cap**; bounded diagnostic
   excerpts are at most **4,096 bytes**. Enforce termination on timeout/overflow;
   preserve bounded failure evidence in ignored `artifacts/logs/` and preserve the
   stage. Do not proceed after failure. Generated source UID sidecars are the
   only new file types proposed; no new executable types or engine tests.

Exact proposed engine commands (replace only `$stage3bPath` with the newly
verified approved stage; **do not execute before approval**):

```powershell
& 'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe' --headless --path $stage3bPath --editor --import --quit
& 'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe' --path $stage3bPath --resolution 1280x720 res://scenes/experiments/terrain_stage3b/lab.tscn
```

Exact staging input definition (52 unique source/destination pairs):

- Start with the 32 paths in
  [metadata inputs](../../tests/fixtures/metadata_smoke/inputs.json), excluding
  `tests/metadata_smoke_test.gd`, its `.uid`,
  `tests/fixtures/metadata_smoke/geometry.json`, and
  `tests/fixtures/terrain_stage2_classification_vectors.json` (28 remain).
  Map `tests/fixtures/metadata_smoke/project.godot` to `project.godot` and
  `tests/fixtures/metadata_smoke/builder.gd.uid` to
  `scenes/world/continuous_terrain_metadata.gd.uid`, exactly as the existing
  metadata recipe does. This minimal GL Compatibility project has no autoloads
  or main scene. Its name remains "TLWH Metadata Smoke"; the explicit scene
  argument launches this lab, without running a smoke script.
- Add the three files under `scenes/experiments/terrain_stage3b/`.
- Add `assets/experiments/terrain_c1/fixture.json`.
- Add `assets/experiments/terrain_c1/sources/{earth,green}.png` and their two
  matching `.png.import` files.
- Add `assets/experiments/terrain_c1/fields/{-1_-1,-1_0,0_-1,0_0}_{field,phase}.png`
  and their eight matching `.png.import` files.

The unchanged metadata class dependency closure includes production state and
Ferrite class *definitions*. The lab never constructs those classes or invokes
their initialization, so no Ferrite catalog/artwork or gameplay system is staged
or run. Runtime import must confirm that dormant dependencies remain dormant.

## Visual acceptance checklist

After the curtain clears and status shows `ready true`, use:

| Control | Comparison |
|---|---|
| 1 | Natural transition near `(-1100,750)`; grass/soil character and blend shape |
| 2 | Crash-area ground near `(-384,-192)`; classified Earth with organic boundary blending, no strict visual mask |
| 3 | Negative-coordinate chunk seam near `(0,-1700)`; no line or phase jump across x=0 |
| 4 / 5 / 6 | 1.0× / 0.5× / 1.5×; camera clamps inside fixed prepared area |
| F | Cycle artwork → continuous coverage grayscale → original ID colors (red=id/4, green=nonzero) |
| Esc | Exit |

Compare C1's preserved visual direction and prior owner observations; old C1
coverage is intentionally different. Check center plateaus, transition shape,
subtype IDs, negative seam continuity and artwork minification. Inspect all three
views at 1×/0.5×. Report backend, errors, controls tested and owner visual result.
No visual acceptance is claimed until actual authorized on-screen review.

## Validation and remaining limits

Focused command: `python -B -m unittest discover -s tests -p static_terrain_stage3b_test.py -v`.
Full static command: `python -B -m unittest discover -s tests -p 'static_*test.py'`.
These run independent offline Python models and source/resource text checks;
they do not parse or execute GDScript, compile shaders, import assets or establish
GPU parity. The tests cover all 16 patterns, endpoint algebra, signed seeds,
negative ownership/seams, halo encoding, fixed inventory, failure source contracts
and unchanged frozen art/production scope. The PR #139 inventory guard is anchored
to its immutable merge; the new test checks the exact current seven-file scope.
No historical math/golden/assertion or runner control is relaxed.

Runtime must still validate parsing, dependency/import closure, R8 normalized
round-trip, numerical color handling, raster orientation, shader precision,
sampling windows/gradients, seams and visual quality. No timings, numerical
certification, production arrival proof or acceptance is inferred from static
PASS. No integration or Dave sprite work is included. After owner visual review,
make only evidence-driven adjustments before planning narrow opt-in integration.
