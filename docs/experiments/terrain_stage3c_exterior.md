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


## PR #143 final one-time execution procedure — proposed, inactive

The owner provisionally accepted implementation `0600be54ebec217e20cea923e117a465fcddff2d`
for controlled gameplay validation and requested this preparation only. This
amendment changes **only this guide**. The 346-input manifest remains byte-for-byte
unchanged, SHA-256 `a567d3b6abb39fdf28cc0b019f7280ad971a771d610db41f2e5c9f692997a7c8`.
Both staged transformations, their mixed/newline bytes and resulting hashes are
used exactly as committed; the source scene and illustrated default are untouched.
Native and inactive MetadataSmoke modes, policies and assertions are unchanged.

This is a fixed documented procedure, not a reusable launcher or new runner mode.
It dot-sources only the unchanged reviewed runner's definitions, reusing
`Invoke-BoundedProcess`, `Get-NativeSourceIdentity`, `Assert-PlainPath`,
`Get-NativeStageParent`, `Assert-PinnedEngine`, `Get-NativeOutcome` and
`Save-NativeFailureEvidence`. No dispatcher, NativePlan, Native or MetadataSmoke
invocation occurs. The only engine calls are the two explicit calls below.

**Not authorized yet.** Final approval must name the exact documentation-preparation
commit and the unchanged manifest hash above. After that approval only, set
`$reviewedRevision` to that approved 40-character commit in a **fresh interactive
PowerShell 7 on Windows**, in the primary checkout, and execute this entire block
once. That revision is the only review input: no executable, path, input, scene,
command, transformation, duration or output-limit override is supported. Do not
execute isolated lines or invoke the procedure to validate its preparation.
A failure stops the attempt; no repair/retry or unattended continuation is granted.
The owner must remain present and close the game normally before 300 seconds.

The reviewed helper starts the standard Windows executable directly, keeps its
process handle, asynchronously drains both redirected pipes, and enforces the
stopwatch/output caps. It does not depend on a visible terminal window or a
blocking `Start-Process -Wait`. Timeout/overflow calls its existing best-effort
`Kill(true)` and bounded two-second wait; **termination remains uncertain** on
forced-stop paths. No later launch is permitted. This does not certify descendant
containment or protection against system-wide freezes. Do not close the supervisor
to end gameplay. On visible errors or responsiveness symptoms, close the game
immediately; do not attempt to reproduce them.

Error scanning and source/stage/control/evidence identity checks occur at phase
boundaries, as in the reviewed supervision. There is no new live error/identity
watcher. No concurrent source/stage editing is permitted. Normal exit 0 and clean
process checks are not gameplay acceptance: report actual checklist observations,
including UNTESTED checks, separately. No gameplay completion marker is invented.

The isolated user-data directory is the manifest's fixed custom name directly
under Windows application data, per [Godot's custom user-data path contract](https://docs.godotengine.org/en/stable/tutorials/io/data_paths.html#accessing-persistent-user-data-user).
It must be absent before the attempt, may be created by import/gameplay, and is
preserved afterward. Existing saves/settings are neither staged nor reused.

```powershell
# INACTIVE: separate explicit owner approval of this exact procedure is required.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows -or $PSVersionTable.PSVersion.Major -lt 7 -or
    -not (Test-Path variable:reviewedRevision) -or
    $reviewedRevision -cnotmatch '^[0-9a-f]{40}$') { throw 'Approved Windows/PowerShell/revision required.' }
$source = 'D:\GameDev\Godot\Projects\TLWH'
$runner = Join-Path $source 'tools/run-local-tests.ps1'
function Hash-File([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Hash-Text([string]$s) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($s))).ToLowerInvariant()
}
# Refuse to load unreviewed definitions. No engine command, including --version.
if ((Hash-File $runner) -cne '51528fdabfb14d2b0d0dbd6c8b9bfc181acdccbcd594eebe2de0a8c874f8fea1') { throw 'Reviewed supervisor changed.' }
. $runner # Definitions only; the runner's dot-source gate prevents dispatch.
$summary = [pscustomobject]@{ Static='NOT RUN'; Import='NOT RUN'; Native='GAMEPLAY NOT RUN';
    Infrastructure='PASS'; Authorization='SEPARATE ONE-TIME OWNER GRANT REQUIRED'; Reason='';
    Revision=''; Working=''; Executable=''; Sha256=''; StageDirectory=''; Inputs=@(); Commands=@(); Diagnostic='' }
$stage3cPath = $null
$git = @(Get-Command git -CommandType Application)[0].Source
function Git-Read([string[]]$a) {
    $r = Invoke-BoundedProcess $git $a $source
    if ($r.Status -ne 'PASS' -or $r.ExitCode -ne 0 -or -not $r.TerminationCertain) { throw 'Git verification failed.' }
    $r.Stdout
}
function Assert-NoGodot {
    if (@(Get-Process -Name 'Godot*' -ErrorAction SilentlyContinue).Count) { throw 'An existing Godot process blocks this attempt; do not stop owner processes.' }
}
try {
    Assert-PlainPath $source
    Assert-PlainPath $runner
    $identity = Get-NativeSourceIdentity $source
    $summary.Revision = $identity.Revision; $summary.Working = $identity.Working
    if ($identity.Revision -cne $reviewedRevision) { throw 'HEAD is not the final owner-approved preparation commit.' }
    $implementation = '0600be54ebec217e20cea923e117a465fcddff2d'
    $guide = 'docs/experiments/terrain_stage3c_exterior.md'
    $null = Git-Read @('merge-base','--is-ancestor',$implementation,'HEAD')
    if ((Git-Read @('diff','--name-status',$implementation,'HEAD','--')).Trim() -cne "M`t$guide") {
        throw 'Preparation must modify only the existing Stage 3C guide.'
    }
    $receiptPath = Join-Path $source 'artifacts/logs/terrain-preservation-2026-11-03.json'
    if ((Hash-File $receiptPath) -cne '8eb39435fef15561e7024bdc0cc340a309acacbcf58e870f1e0eff0ea3a521a7') { throw 'Preservation receipt changed.' }
    $receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
    $sidecars = @($receipt.protected_sidecars.PSObject.Properties.Name)
    $status = @($identity.Working -split "`n" | Where-Object { $_.TrimEnd("`r") })
    if ($sidecars.Count -ne 15 -or $status.Count -ne 15 -or
        @($status | Where-Object { -not $_.StartsWith('?? ') }).Count -or
        (Compare-Object -CaseSensitive $sidecars @($status | ForEach-Object { $_.Substring(3).TrimEnd("`r") }))) {
        throw 'Tracked/index state must be clean; only the exact protected untracked sidecars may remain.'
    }
    $manifestPath = Join-Path $source 'docs/experiments/terrain_stage3c_gameplay_plan.json'
    if ((Hash-File $manifestPath) -cne 'a567d3b6abb39fdf28cc0b019f7280ad971a771d610db41f2e5c9f692997a7c8') { throw 'Approved manifest changed; no repinning.' }
    $plan = Get-Content -Raw -LiteralPath $manifestPath | ConvertFrom-Json
    $inputs = @($plan.inputs)
    $summary.Inputs = $inputs
    $paths = [string[]]@($inputs | ForEach-Object { $_.path })
    $unique = [Collections.Generic.HashSet[string]]::new([StringComparer]::OrdinalIgnoreCase)
    if ($inputs.Count -ne 346 -or $plan.input_count -ne 346) { throw 'Exact 346-input inventory required.' }
    foreach ($p in $paths) {
        if ($p -cnotmatch '^[A-Za-z0-9_./-]+$' -or $p.StartsWith('/') -or
            @($p.Split('/') | Where-Object { $_ -in @('', '.', '..') }).Count -or
            -not $unique.Add($p) -or $p -cnotin $identity.Tracked) { throw 'Unsafe, duplicate or untracked manifest input.' }
    }
    $transformed = @($inputs | Where-Object { $_.PSObject.Properties.Name -contains 'transform' })
    if ($transformed.Count -ne 2 -or (Compare-Object -CaseSensitive @('project.godot','scenes/world/planet_exterior.tscn') @($transformed.path))) {
        throw 'Only the two pinned staged transformations are permitted.'
    }
    $userName = 'TLWH-Stage3C-8fe7fe8c0e594933b02e9581b8b51b11'
    if ($plan.user_directory_must_be_absent -cne $userName) { throw 'Unexpected user-data identity.' }
    $appData = [Environment]::GetFolderPath([Environment+SpecialFolder]::ApplicationData)
    if (-not $appData -or -not [IO.Path]::IsPathFullyQualified($appData) -or
        -not $env:APPDATA -or -not ([IO.Path]::GetFullPath($env:APPDATA)).Equals(
            [IO.Path]::GetFullPath($appData), [StringComparison]::OrdinalIgnoreCase)) { throw 'Uncertain Windows application-data root.' }
    $userDirectory = Join-Path $appData $userName
    Assert-PlainPath $userDirectory
    if (Test-Path -LiteralPath $userDirectory) { throw 'Isolated user directory already exists; preserve it and stop.' }

    # Bound the only possible generated non-cache outputs to this fixed inventory.
    $generatedAllowed = @{}
    foreach ($p in $paths) {
        if ($p.EndsWith('.gd') -or $p.EndsWith('.gdshader')) {
            if (($p+'.uid') -cnotin $paths) { $generatedAllowed[$p+'.uid'] = $p }
        } elseif ($p.EndsWith('.png') -and ($p+'.import') -cnotin $paths) {
            $generatedAllowed[$p+'.import'] = $p
        }
    }
    if ($generatedAllowed.Count -ne 18 -or
        @($generatedAllowed.Keys | Where-Object { $_.EndsWith('.import') }).Count -ne 15 -or
        @($generatedAllowed.Keys | Where-Object { $_.EndsWith('.uid') }).Count -ne 3) { throw 'Unexpected generated-sidecar scope.' }
    $generated = @{}
    # Capture unchanged controls and historical evidence before static validation.
    $guard = @($receiptPath,$manifestPath)
    $guard += @($identity.Tracked | Where-Object {
        $_ -cmatch '^(tools/|tests/|AGENTS\.md$|docs/LOCAL_TESTING\.md$|docs/experiments/terrain_stage3[bc][^/]*\.md$|assets/experiments/terrain_c1/)'
    } | ForEach-Object { Join-Path $source $_ })
    $guard += (Join-Path $source $guide)
    foreach ($p in $sidecars) {
        $f = Join-Path $source $p
        Assert-PlainPath $f
        if ((Hash-File $f) -cne $receipt.protected_sidecars.$p.sha256) { throw 'Protected source sidecar changed.' }
        $guard += $f
    }
    foreach ($entry in $receipt.commits.c1.sha256.PSObject.Properties) {
        if ($entry.Name.EndsWith('.png') -or $entry.Name.EndsWith('/fixture.json')) {
            $f = Join-Path $source $entry.Name
            Assert-PlainPath $f
            if ((Hash-File $f) -cne $entry.Value) { throw 'Frozen C1 artwork/field/fixture changed.' }
            $guard += $f
        }
    }
    foreach ($entry in $receipt.metadata.PSObject.Properties) {
        $f = Join-Path $source $entry.Name
        Assert-PlainPath $f
        if ((Hash-File $f) -cne $entry.Value.sha256) { throw 'Preserved C1 import/UID metadata changed.' }
        $guard += $f
    }
    Assert-PlainPath $receipt.bundle.path
    if ((Get-Item -LiteralPath $receipt.bundle.path).Length -ne $receipt.bundle.size -or
        (Hash-File $receipt.bundle.path) -cne $receipt.bundle.sha256) { throw 'Preservation bundle changed.' }
    $guard += $receipt.bundle.path
    foreach ($record in @(
        @('artifacts/tmp/stage2b2-20261103-132958/manifest.json','a24340c1b006283270d04c7c43aa1fe4b1b1ca85019b43af2fd56817107ac2f7'),
        @('artifacts/tmp/stage2b2-readable-v1-20261103-134527/manifest.json','332fa252dca79d2112dc071831c28e86f28bd3d88c0470e292335620180e8063'))) {
        $historical = Join-Path $source $record[0]
        Assert-PlainPath $historical
        if ((Hash-File $historical) -cne $record[1]) { throw 'Historical diagnostic manifest changed.' }
        $guard += $historical
        foreach ($output in (Get-Content -Raw -LiteralPath $historical | ConvertFrom-Json).outputs) {
            $f = Join-Path (Split-Path $historical) $output.file
            Assert-PlainPath $f
            if ((Get-Item -LiteralPath $f).Length -ne $output.bytes -or (Hash-File $f) -cne $output.sha256) { throw 'Historical diagnostic PNG changed.' }
            $guard += $f
        }
    }
    $adaptive = Join-Path $source 'artifacts/tmp/adaptive-cpu-1c4ee892573242e1818fdd2ff3eb866e'
    Assert-PlainPath $adaptive
    $files = @(Get-ChildItem -LiteralPath $adaptive -Force)
    if ($files.Count -ne 6 -or @($files | Where-Object { $_.PSIsContainer }).Count) { throw 'PR #141 evidence inventory changed.' }
    $arows = [string[]]@(foreach ($f in $files) { Assert-PlainPath $f.FullName; $f.Name + (Hash-File $f.FullName) })
    [Array]::Sort($arows,[StringComparer]::Ordinal)
    if ((Hash-Text ($arows -join '')) -cne '5a1a713347c03361ea27f47bc0b9f82370551acc0db33408a2a4ffee994999b8') { throw 'PR #141 diagnostics changed.' }
    $guard += @($files.FullName)
    $guards = @(foreach ($p in ($guard | Select-Object -Unique)) { Assert-PlainPath $p; [pscustomobject]@{ Path=$p; Sha256=(Hash-File $p) } })
    $refs = @{}
    foreach ($tag in $receipt.tags.PSObject.Properties) {
        if ((Git-Read @('cat-file','-t',$tag.Name)).Trim() -cne 'tag') { throw 'Annotated preservation tag missing.' }
        $refs[$tag.Name] = $receipt.remote_refs.('refs/tags/'+$tag.Name)
        $refs[($tag.Name+'^{}')] = $tag.Value
    }
    $refs['codex/terrain-fidelity-a1-artwork'] = $receipt.commits.a1.commit
    $refs['codex/terrain-adaptive-cpu-prototype'] = '9a75949181349dbecc475bb12328cef69636ce92'

    function Assert-Stage3CSnapshot([ValidateSet('Before','Imported','Final')][string]$phase) {
        $now = Get-NativeSourceIdentity $source
        foreach ($key in @('Revision','Working','Index')) { if ($now.$key -cne $identity.$key) { throw "Source identity changed: $key" } }
        foreach ($ref in $refs.Keys) { if ((Git-Read @('rev-parse',$ref)).Trim() -cne $refs[$ref]) { throw 'Preservation reference changed.' } }
        foreach ($g in $guards) { Assert-PlainPath $g.Path; if ((Hash-File $g.Path) -cne $g.Sha256) { throw 'Reviewed control/evidence changed.' } }
        foreach ($entry in $inputs) {
            $f = Join-Path $source $entry.path
            Assert-PlainPath $f
            if ((Get-Item -LiteralPath $f).Length -ne $entry.bytes -or (Hash-File $f) -cne $entry.sha256) { throw 'Source input changed.' }
            if ($stage3cPath) {
                $f = Join-Path $stage3cPath $entry.path
                Assert-PlainPath $f
                $size = $entry.bytes; $hash = $entry.sha256
                if ($entry.PSObject.Properties.Name -contains 'transform') { $size=$entry.staged_bytes; $hash=$entry.staged_sha256 }
                if ((Get-Item -LiteralPath $f).Length -ne $size -or (Hash-File $f) -cne $hash) { throw 'Staged input changed.' }
            }
        }
        Assert-PlainPath $userDirectory
        if ($phase -ceq 'Before' -and (Test-Path -LiteralPath $userDirectory)) { throw 'Isolated user data appeared before import.' }
        if (-not $stage3cPath) { return }
        Assert-PlainPath $stage3cPath
        $queue = [Collections.Generic.Queue[string]]::new(); $queue.Enqueue($stage3cPath)
        while ($queue.Count) {
            foreach ($item in Get-ChildItem -Force -LiteralPath $queue.Dequeue()) {
                Assert-PlainPath $item.FullName # Never follow links, including cache links.
                $relative = [IO.Path]::GetRelativePath($stage3cPath,$item.FullName).Replace('\','/')
                $cache = $relative -ceq '.godot' -or $relative.StartsWith('.godot/',[StringComparison]::Ordinal)
                if ($relative -ceq '.godot' -and -not $item.PSIsContainer) { throw 'Cache root must be a directory.' }
                if ($item.PSIsContainer) {
                    if (-not ($phase -cne 'Before' -and $cache) -and
                        -not @($paths | Where-Object { $_.StartsWith($relative+'/',[StringComparison]::Ordinal) }).Count) { throw 'Unexpected staged directory.' }
                    $queue.Enqueue($item.FullName)
                } elseif ($relative -cnotin $paths -and -not ($phase -cne 'Before' -and $cache)) {
                    if ($phase -ceq 'Before' -or -not $generatedAllowed.ContainsKey($relative)) { throw 'Unexpected staged output.' }
                    if ($phase -ceq 'Final' -and -not $generated.ContainsKey($relative)) { throw 'New non-cache output after import review.' }
                    $limit = if ($relative.EndsWith('.uid')) { 128 } else { 65536 }
                    if ($item.Length -gt $limit) { throw 'Generated sidecar exceeds its fixed read limit.' }
                    $text = [Text.UTF8Encoding]::new($false,$true).GetString([IO.File]::ReadAllBytes($item.FullName)).Replace("`r`n","`n")
                    if ($relative.EndsWith('.uid')) {
                        if ($item.Length -gt 128 -or $text.Trim() -cnotmatch '^uid://[a-z0-9]+$') { throw 'Malformed generated UID.' }
                    } else {
                        $original = $generatedAllowed[$relative]
                        $sections = @([regex]::Matches($text,'(?m)^\[([^]\r\n]+)\]$') | ForEach-Object { $_.Groups[1].Value })
                        if ($item.Length -gt 65536 -or ($sections -join ',') -cne 'remap,deps,params' -or
                            [regex]::Matches($text,'(?m)^importer="texture"$').Count -ne 1 -or
                            [regex]::Matches($text,'(?m)^type="CompressedTexture2D"$').Count -ne 1 -or
                            [regex]::Matches($text,'(?m)^uid="uid://[a-z0-9]+"$').Count -ne 1 -or
                            [regex]::Matches($text,'(?m)^source_file="'+[regex]::Escape('res://'+$original)+'"$').Count -ne 1) { throw 'Malformed generated PNG import metadata.' }
                        $remap = [regex]::Matches($text,'(?m)^path="(res://\.godot/imported/[A-Za-z0-9_.-]+\.ctex)"$')
                        if ($remap.Count -ne 1 -or [regex]::Matches($text,'(?m)^dest_files=\["'+[regex]::Escape($remap[0].Groups[1].Value)+'"\]$').Count -ne 1 -or
                            -not (Test-Path -LiteralPath (Join-Path $stage3cPath $remap[0].Groups[1].Value.Substring(6)) -PathType Leaf)) { throw 'Invalid generated import destination.' }
                    }
                    $hash = Hash-File $item.FullName
                    if ($generated.ContainsKey($relative) -and $generated[$relative] -cne $hash) { throw 'Generated sidecar changed after import review.' }
                    $generated[$relative] = $hash
                }
            }
        }
        foreach ($p in $generated.Keys) { if (-not (Test-Path -LiteralPath (Join-Path $stage3cPath $p) -PathType Leaf)) { throw 'Generated sidecar disappeared.' } }
    }
    $pinned = Get-StandardGodotIdentity
    $summary.Executable = $pinned.Path; $summary.Sha256 = $pinned.Sha256
    Assert-NoGodot
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    Assert-Stage3CSnapshot Before
    $python = @(Get-Command python -CommandType Application)[0].Source
    $r = Invoke-BoundedProcess $python @('-B','-m','unittest','discover','-s','tests','-p','static_*test.py') $source -Seconds 360 -MaxBytes 1048576 -ExcerptBytes 4096
    $summary.Diagnostic = $r.Excerpt
    $staticOutput = $r.Stdout+"`n"+$r.Stderr
    if ($r.Status -ne 'PASS' -or $r.ExitCode -ne 0 -or -not $r.TerminationCertain -or
        $staticOutput -notmatch '(?m)^OK\r?$' -or $staticOutput -notmatch '(?m)^Ran 367 tests in ') { throw 'Complete static suite did not PASS; no stage or launch.' }
    $summary.Static = 'PASS'
    Assert-Stage3CSnapshot Before
    Assert-NoGodot
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    $parent = Get-NativeStageParent $source
    $stage3cPath = Join-Path $parent ('stage3c-'+[Guid]::NewGuid().ToString('N'))
    if (Test-Path -LiteralPath $stage3cPath) { throw 'Stage exists; no reuse.' }
    $null = New-Item -ItemType Directory -Path $stage3cPath
    $summary.StageDirectory = $stage3cPath
    foreach ($entry in $inputs) {
        $original = Join-Path $source $entry.path
        $destination = Join-Path $stage3cPath $entry.path
        Assert-PlainPath $original; Assert-PlainPath $destination
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        Assert-PlainPath $destination
        $bytes = [IO.File]::ReadAllBytes($original)
        if ($entry.PSObject.Properties.Name -contains 'transform') {
            $utf8 = [Text.UTF8Encoding]::new($false,$true)
            $text = $utf8.GetString($bytes)
            $find = [string]$entry.transform.find
            if ([regex]::Matches($text,[regex]::Escape($find)).Count -ne 1) { throw 'Staged transformation match is not unique.' }
            $bytes = $utf8.GetBytes($text.Replace($find,[string]$entry.transform.replace))
        }
        $stream = [IO.File]::Open($destination,[IO.FileMode]::CreateNew,[IO.FileAccess]::Write,[IO.FileShare]::None)
        try { $stream.Write($bytes,0,$bytes.Length) } finally { $stream.Dispose() }
    }
    Write-Host "Retained stage: $stage3cPath"
    Write-Host "Isolated user data (preserve): $userDirectory"
    $importArgs = @('--headless','--path',$stage3cPath,'--editor','--import','--quit')
    $gameplayArgs = @('--path',$stage3cPath,'--resolution','1280x720','res://scenes/main/main_v2.tscn')
    $summary.Commands = @($importArgs,$gameplayArgs)
    Assert-Stage3CSnapshot Before
    Assert-NoGodot
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    $summary.Import = 'FAIL'
    $r = Invoke-BoundedProcess $pinned.Path $importArgs $stage3cPath -Seconds 60 -MaxBytes 1048576 -ExcerptBytes 4096
    $summary.Diagnostic = $r.Excerpt
    $outcome = Get-NativeOutcome Import $r # Exit/error health checks only, no test dispatch.
    if ($outcome.Status -ne 'PASS' -or ($r.Stdout+"`n"+$r.Stderr) -match '(?im)shader compilation failed|shader error|assertion failed') { throw "Cold import failed: $($outcome.Reason)" }
    Assert-Stage3CSnapshot Imported
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    Assert-NoGodot
    $summary.Import = 'PASS'
    # Freeze the non-cache generated sidecar inventory; .godot remains engine-owned.
    $generatedRows = [string[]]@($generated.Keys | ForEach-Object { $_+'|'+$generated[$_] })
    [Array]::Sort($generatedRows,[StringComparer]::Ordinal)
    Write-Host ('Reviewed generated sidecars: '+$generated.Count+'; inventory SHA256 '+(Hash-Text (($generatedRows -join "`n")+"`n")))
    Assert-Stage3CSnapshot Final
    Assert-NoGodot
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    Write-Host 'ONE supervised gameplay session, 1280x720; follow the eight guide checks; close normally BEFORE 300 seconds. Stop on visible errors/stalls. No retry.'
    $summary.Native = 'GAMEPLAY FAIL'
    $r = Invoke-BoundedProcess $pinned.Path $gameplayArgs $stage3cPath -Seconds 300 -MaxBytes 1048576 -ExcerptBytes 4096
    $summary.Diagnostic = $r.Excerpt
    $outcome = Get-NativeOutcome Import $r # No invented gameplay completion marker.
    if ($outcome.Status -ne 'PASS' -or ($r.Stdout+"`n"+$r.Stderr) -match '(?im)shader compilation failed|shader error|assertion failed') { throw "Gameplay process failed: $($outcome.Reason)" }
    Assert-Stage3CSnapshot Final
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    Assert-NoGodot
    $summary.Native = 'GAMEPLAY PROCESS PASS; OWNER CHECKLIST/ACCEPTANCE SEPARATE'
    Write-Host 'Process checks passed. Record actual owner observations and UNTESTED items separately; no default activation, retry, merge or cleanup.'
} catch {
    $summary.Infrastructure = 'FAIL'
    $summary.Reason = [string]$_
    try { $evidence = Save-NativeFailureEvidence $source $summary; Write-Host "Retained bounded failure evidence: $evidence" }
    catch { Write-Warning 'Failure evidence could not be written; preserve all files/stages and report this failure.' }
    throw # No subsequent launch, automatic retry, fix-and-rerun or deletion.
}
```

The full static suite has the reviewed 360-second supervision budget; engine
phases remain exactly 60 and 300 seconds. All three calls use the existing
1,048,576-byte combined cap and 4,096-byte diagnostic excerpts. The legacy
failure record's `Native` field holds **gameplay process status**, not a Native
mode invocation. `Save-NativeFailureEvidence` enforces its existing 64 KiB limit
and ignored `artifacts/logs/` destination. A pre-load supervisor identity failure
stops before any trusted helper is available; preserve its console diagnostic.
Success prints provenance and retains the final process result in memory; no
routine successful-output log or screenshot is saved. Stage and isolated user
data remain preserved. Only the exact 18 possible new non-cache sidecar paths
are admissible during import; any actually generated sidecars are validated and
hash-pinned before gameplay. They cannot appear, disappear or change afterward.
Cache contents may change during gameplay but every cache entry is traversed
without following reparse points. Existing staged inputs/sidecars never change.

Preparation validation and the final approved documentation commit are recorded
in the PR update. Preparation performs no source import, real-stage creation,
Godot execution, graphics, gameplay, profiling, merge or cleanup. After approval,
one attempted run consumes the one-time grant even on failure. The owner checklist
above remains the acceptance scope; elapsed time is not acceptance or approval.
