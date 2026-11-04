# Stage 3C — opt-in continuous exterior

Status: feature branch, pending merge and controlled gameplay validation.
The owner authorized this implementation after PR #142's isolated appearance
acceptance. No engine execution is authorized or reported here.

## Configuration and rollback

`PlanetExterior.terrain_renderer` adds `CONTINUOUS = 2`; `ILLUSTRATED = 1`
remains the script and production scene default. Select Continuous on a fresh
exterior instance before its first `prepare_for_arrival()` call. Selection is
locked for the instance lifetime. There is no player-facing renderer menu.
Rollback means stopping that playthrough and creating a fresh exterior with
Illustrated selected. Failures latch; no automatic fallback or mixed ground.
The separately approvable plan below changes only an external staged scene.

## Ownership and presentation

`PlanetExterior` still owns the sole neighborhood queue, revision, tokens,
retirement, cancellation, details, Ferrite, tint flushing and arrival receipts.
The sibling `ContinuousTerrainPresenter` is constructed only for explicit opt-in.
It has one caller-serviced job, no process callback, threads, disk cache or second
world generator. Each slice checks a 2,000 microsecond deadline after a unit and
has an absolute 32,768-unit cap. Publication/upload and the existing synchronous
`TerrainChunk.configure()` are outside that preparation deadline. This is a work
limit, not a measured time guarantee. Required queue entries are serviced before
advancing to the next chunk; pending preparation cannot drain the queue.

The generator's original 0–4 IDs are sampled from the existing generator into a
34×34 R8 halo and retained on CPU with world seed identity. GPU Candidate A and
four-window artwork sampling match the accepted lab core (`a=5/32`). Frozen C1
Earth and Green PNGs are unchanged. All Green subtypes use the same accepted
Green art. SHA-256 phase keys preserve `c1_fields_v1:c1_materials_v1:<seed>:<x>:<y>:material`.
C1 G/B shading is generated incrementally from the same coordinate noise and
quantization at absolute 16-unit nodes with four-node gutters; red protection is
absent. No replacement crash-site coverage mask is introduced.

Production presentation uses the existing `TerrainChunk` halo-averaged
`PlanetGenerator.sample_color()` → `_earth_tint()` → shared RGBAF tint atlas.
Thus world-state edits, ordered authored overlays and tint precedence use the
original code, with no classification/state changes. Tint multiplies the accepted
continuous artwork after its shading. Existing details remain above ground and
below authored objects/Ferrite. The authored scene geometry is unchanged.

A completed surface is attached and visible before presenter publication. Only
then does the exterior synchronously attach details, write/synchronize/flush tint
and record its revision receipt. Cancellation invalidates unfinished publication;
replacement retains previous pixels until a new surface attaches. Receipts still
require current state, seed, generator, revision, token and attached details.
Detachment hides publication; cached hatch returns reuse valid completed surfaces.
Failures preserve earlier visuals and block arrival, without retry loops.

## Bounds and known limitations

Owned chunks are limited to [-16,15] per axis. Halo samples extend beyond the
owned envelope; no coordinate clamping or wrapping is used. Requesting an
unsupported loading chunk fails closed, so exploration must remain inside this
envelope with room for the loading radius. Increasing the coordinate envelope
requires a separate certification decision.

One job retains 1,156 ID bytes + 56,307 shading bytes + 147 phase bytes. Each
published chunk retains these textures and 1,156 CPU ID bytes; there is no
unbounded field/phase memoization. At default radius 2 plus margin 1 there are at
most 49 retained chunks plus one replacement. This raw payload arithmetic excludes
engine/GPU allocation overhead, the shared artwork, tint atlas and details.
Retirement releases presenter references; queued frees complete at the engine's
normal boundary. Cancellation discards unfinished arrays and removes registrations
without retained surfaces. No historical evidence or owner files are deleted.

The architecture record's provisional performance targets remain measurement
criteria, **not achieved results**. In particular, initial arrival latency,
synchronous detail/tint cost, texture upload cost and GPU cost are unmeasured.
The preserved PNG import settings disable artwork mipmaps; distant filtering
quality remains a known limitation. Python float/model agreement cannot establish
Godot float32 noise quantization, shader compilation, GPU parity or actual visuals.
No runtime, graphical, gameplay or performance verification is claimed.

## Separately approvable gameplay execution plan

This section proposes exactly one cold import and one supervised playable session.
It grants no execution permission. Approval must identify the final commit and
this plan's manifest SHA-256. A reviewed activation/supervision amendment must be
prepared and approved before dispatch; the existing Native/MetadataSmoke runner
must not be repurposed or expanded by this PR. No real stage is created now.

The companion [input manifest](terrain_stage3c_gameplay_plan.json) enumerates
exact tracked input paths, byte lengths and SHA-256 hashes. Its fixed selection
includes production runtime roots (no experimental scenes), production assets,
shared shaders, and only frozen C1 Earth/Green PNGs and matching tracked sidecars
from experimental assets. Extra production resources are inert; no test harness,
executable, tool, evidence, cache, historical experiment or protected untracked
sidecar is an input. Review this intentionally conservative gameplay closure
before granting execution. The approved working-checkout serialization must match this table exactly.
For text inputs, verify LF-normalized content against the final Git blob; binary
inputs must match the blob byte for byte. Do not normalize staged copies.

Preconditions and stage preparation:

1. Capture HEAD, complete status/index identity and manifest/control hashes.
   Verify unchanged protected 15 sidecars, frozen C1/A1 references, preservation
   receipts, bundle and PR #141 negative experiment evidence against the existing
   preservation records. Require actual complete Python static-suite PASS.
2. Require no standard Godot process. Verify the exact standard executable
   `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`, SHA-256
   `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`.
   Rehash immediately before each launch. No executable/command substitutions.
3. Create one fresh unique `stage3c-<GUID>` under
   `D:\GameDev\Godot\TLWH-NativeStages`; reject any existing stage/reparse point.
   Copy exactly manifest inputs and independently verify hashes.
4. Apply only the manifest's two exact staged text transformations: opt in on the
   root `PlanetExterior` node; isolate this session's user-data directory. Check
   both source and staged hashes. Require the named isolated user directory to
   be absent; never reuse/delete owner settings or saves. Preserve the new stage
   and isolated user data after the run.

Exact proposed engine arguments (sequential, one process at a time):

```text
--headless --path <fresh-stage> --editor --import --quit
--path <fresh-stage> --resolution 1280x720 res://scenes/main/main_v2.tscn
```

Import deadline: 60 seconds. Playable-session deadline: 300 seconds, with the
owner closing normally before expiry. The latter is a specific proposed scope
for functional inspection, **not a benchmark or prolonged/stress run**. Both
phases need the existing bounded-process supervision: 1,048,576 combined output
bytes, 4,096-byte diagnostic excerpts, certain termination, exit 0, no engine,
script, parse, shader or assertion errors. Import must PASS before gameplay.
Use the established supervisor's stop/identity/output checks in the separately
reviewed activation amendment. Stop immediately on any error, responsiveness
symptom, timeout, overflow, source/stage/executable mutation or uncertain exit.
No automatic retry, repair-and-rerun, fallback, freeze reproduction or cleanup.

Generated output review may admit only `.godot/` cache, missing script/shader UID
sidecars and missing resource import sidecars corresponding to the enumerated
stage inputs. Existing input sidecars remain immutable. Validate generated
sidecar formats, reject unexpected paths/reparse points and preserve output
inventory/hashes for checking after gameplay. Do not bring generated files back
to the source checkout. Failure evidence remains bounded in ignored
`artifacts/logs/`; screenshots/permanent evidence require separate publication
approval. Source, stage and protected identities must be rechecked after each
phase and at final exit. Record observed checks without inventing coverage.

Owner-supervised acceptance, within the single session:

| Check | Expected observation |
|---|---|
| Fresh V2 exterior arrival | Complete ground before fade/input unlock; no holes or shader errors |
| Crash site | Accepted C1/Candidate A appearance with production tint and authored scar order; protected gameplay/objects unchanged |
| Exploration | Walk north/south/east/west across nearby positive and negative chunk boundaries; no visible seams, holes or displaced textures |
| Streaming and return | Move at least one chunk from arrival, then return; no stale ground or sustained unresponsiveness |
| Ferrite | Original deposit artwork, locations, interaction and construction highlight alignment |
| Construction and revisions | Place one available machine on valid ground, observe terrain/detail presentation and machine interaction; state change does not leave missing/stale ground |
| Hatch and warm return | Board through open hatch, return outside; safe fades/input and retained terrain |
| Responsiveness | Owner reports any visible stalls immediately; stop for severe symptoms, without attempting reproduction |

Start with the existing fresh-playthrough seed (26026); no seed/state/gameplay
changes are part of this plan. If prerequisite progression leaves insufficient
time for a check, mark it UNTESTED and stop normally. Do not extend/relaunch by
inference. Additional sessions, alternate seeds, artificial cancellation/failure
injection, envelope-edge travel, profiling and default activation need separate
approval. Static adversarial checks cover those contracts only as models/text.
Final owner gameplay acceptance and performance decisions remain separate.

## Static validation and preservation

The focused suite checks opt-in/default, exact accepted shader core, original IDs
and signed-seed seams, C1 field/phase identities, publication/cancellation guards,
production tint, bounded payload and exact feature scope. Existing preservation
suites continue checking frozen artwork, references and historical inputs.
PR #142's inventory test is anchored to its merge commit; Stage 3C checks its own
exact additions/modifications. Historical mathematical assertions and receipts
are unchanged. The final static results are recorded in the draft PR; no Godot
results should be inferred from them.
