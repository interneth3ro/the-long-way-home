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
The concrete one-time procedure at the end of this document replaces direct
invocation of the illustrative engine commands below. Preparation approval is
not execution approval; the procedure remains **unexecuted**.

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

## PR #142 one-time supervision amendment — proposed, inactive

Owner review of `b3686b6cf553d52a635dd785aa9702ab3c721947` provisionally accepts
the lab for controlled evaluation. This amendment requests exactly one execution
of the following procedure from the separately approved documentation-preparation
commit. Only this document changes after that laboratory revision. It adds no
runner mode, reusable launcher, authorization file or standing permission.

Reuse the unchanged reviewed runner by **dot-sourcing definitions only**. Its
`Invoke-BoundedProcess` starts the executable directly (`UseShellExecute=false`),
owns its process handle, asynchronously drains both redirected pipes, enforces
the stopwatch and combined output cap, and calls `Kill(true)` plus a bounded
2-second wait on an unfinished process. A graphical process is supervised by the
same handle; supervision does not depend on a console window or blocking shell
command. Do not use `Start-Process`, `--editor` for the visual phase, a console
executable substitute, a background/detached job or `-Wait` as the timeout.

**Termination limitation:** forced termination is deliberately reported uncertain
by the reviewed helper. A deadline/overflow is a failed run, never a successful
180-second viewing completion; no subsequent engine launch or retry is permitted.
Do not claim the helper proves descendant termination or survives a system-wide
freeze. The owner must be present, leave the supervising PowerShell running and
use Esc/window close to end the lab normally before 180 seconds. Closing the
supervisor is not an approved stop mechanism. On visible failure or responsiveness
symptoms, close the lab immediately; the retained process handle still supplies
the deadline backstop. Engine-error scanning occurs when the bounded call returns,
as in the reviewed runner; this procedure adds no live error/identity watcher.
Source/status/index, input/control/evidence hashes and stage identity are checked
at phase boundaries; no concurrent editing is permitted. No actual Godot GUI
process/termination test has been performed under this preparation-only request.

The exact 52-input pin below hashes raw working bytes, not normalized Git blobs:
sort ASCII/ordinal `destination|source|lowercase-sha256` rows, join with LF and
include one terminal LF. Pin:
`a8c2d4de036764757e885b0f3bac94d8c7f8106624ad42f575e7880eaa954750`.
This preserves the approved aliases and minimal project bytes; a line-ending
change requires review, not repinning automatically. Frozen Earth and Green
remain respectively `1ab148b0f431cec954299ed4c85cc541df8b72abc7789d9ea1b00532e31eec3d`
and `9a464eb3afa8795c366a9e1af7cd7939cd19e06d76da1169d7ad93df5ad70a79`.

After separate explicit approval, open one fresh interactive PowerShell 7 in the
primary checkout. Set `$reviewedRevision` to the exact **40-character preparation
commit approved by the owner**, then execute this entire fixed block once. The
revision is the only review input; there are no path, inventory, executable,
scene, command, duration or cap overrides. Do not execute isolated lines. The
block is documented source for review, not an instruction to run it now.

```powershell
# INACTIVE: execute once only after separate owner approval of this exact procedure.
$ErrorActionPreference = 'Stop'
Set-StrictMode -Version Latest
if (-not $IsWindows -or $PSVersionTable.PSVersion.Major -lt 7 -or
    $reviewedRevision -cnotmatch '^[0-9a-f]{40}$') { throw 'Reviewed Windows/PowerShell/revision required.' }
$source = 'D:\GameDev\Godot\Projects\TLWH'
$runner = Join-Path $source 'tools/run-local-tests.ps1'
function Hash-File([string]$p) { (Get-FileHash -LiteralPath $p -Algorithm SHA256).Hash.ToLowerInvariant() }
function Hash-Text([string]$s) {
    [Convert]::ToHexString([Security.Cryptography.SHA256]::HashData([Text.Encoding]::UTF8.GetBytes($s))).ToLowerInvariant()
}
if ((Hash-File $runner) -cne '51528fdabfb14d2b0d0dbd6c8b9bfc181acdccbcd594eebe2de0a8c874f8fea1') { throw 'Runner changed.' }
. $runner # Definitions only: does not invoke Invoke-LocalTests or either dispatcher.
Assert-PlainPath $source
Assert-PlainPath $runner
$identity = Get-NativeSourceIdentity $source
if ($identity.Revision -cne $reviewedRevision) { throw 'Unreviewed HEAD.' }
$git = @(Get-Command git -CommandType Application)[0].Source
function Git-Read([string[]]$a) {
    $r = Invoke-BoundedProcess $git $a $source
    if ($r.Status -ne 'PASS' -or $r.ExitCode -ne 0 -or -not $r.TerminationCertain) { throw 'Git verification failed.' }
    $r.Stdout
}
$labRevision = 'b3686b6cf553d52a635dd785aa9702ab3c721947'
$null = Git-Read @('merge-base','--is-ancestor',$labRevision,'HEAD')
$delta = (Git-Read @('diff','--name-only',$labRevision,'HEAD','--')).Trim()
if ($delta -cne 'docs/experiments/terrain_stage3b_visible_lab.md') { throw 'Preparation must change only the existing lab document.' }
$receiptPath = Join-Path $source 'artifacts/logs/terrain-preservation-2026-11-03.json'
if ((Hash-File $receiptPath) -cne '8eb39435fef15561e7024bdc0cc340a309acacbcf58e870f1e0eff0ea3a521a7') { throw 'Preservation receipt changed.' }
$receipt = Get-Content -Raw -LiteralPath $receiptPath | ConvertFrom-Json
$sidecars = @($receipt.protected_sidecars.PSObject.Properties.Name)
$status = @($identity.Working -split "`n" | Where-Object { $_.TrimEnd("`r") })
if ($sidecars.Count -ne 15 -or $status.Count -ne 15 -or
    @($status | Where-Object { -not $_.StartsWith('?? ') }).Count -or
    (Compare-Object -CaseSensitive $sidecars @($status | ForEach-Object { $_.Substring(3).TrimEnd("`r") }))) { throw 'Unexpected checkout changes.' }

$exclude = @('tests/metadata_smoke_test.gd','tests/metadata_smoke_test.gd.uid',
    'tests/fixtures/metadata_smoke/geometry.json','tests/fixtures/terrain_stage2_classification_vectors.json')
$paths = @(Get-MetadataStagePaths | Where-Object { $_ -cnotin $exclude })
$paths += @('scenes/experiments/terrain_stage3b/lab.gd','scenes/experiments/terrain_stage3b/lab.tscn',
    'scenes/experiments/terrain_stage3b/continuous.gdshader','assets/experiments/terrain_c1/fixture.json')
$images = @('sources/earth','sources/green')
foreach ($c in @('-1_-1','-1_0','0_-1','0_0')) { foreach ($kind in @('field','phase')) { $images += "fields/${c}_${kind}" } }
foreach ($image in $images) { $paths += "assets/experiments/terrain_c1/$image.png", "assets/experiments/terrain_c1/$image.png.import" }
if ($paths.Count -ne 52 -or @($paths | Select-Object -Unique).Count -ne 52) { throw 'Inventory mismatch.' }
$inputs = @(foreach ($p in $paths) {
    $original = Get-InputSourcePath $p -Metadata
    if ($original -cnotin $identity.Tracked) { throw 'Untracked input.' }
    Assert-PlainPath (Join-Path $source $original)
    [pscustomobject]@{ Path=$p; Source=$original; Sha256=(Hash-File (Join-Path $source $original)) }
})
$rows = [string[]]@($inputs | ForEach-Object { "$($_.Path)|$($_.Source)|$($_.Sha256)" })
[Array]::Sort($rows,[StringComparer]::Ordinal)
if ((Hash-Text (($rows -join "`n")+"`n")) -cne 'a8c2d4de036764757e885b0f3bac94d8c7f8106624ad42f575e7880eaa954750') { throw 'Reviewed input bytes changed.' }

# Capture controls and protected evidence before static validation. No saved success report.
$guard = @($receiptPath)
$guard += @($identity.Tracked | Where-Object { $_ -cmatch '^(tools/|tests/|AGENTS\.md$|docs/LOCAL_TESTING\.md$|docs/experiments/terrain_stage3b_visible_lab\.md$)' } | ForEach-Object { Join-Path $source $_ })
foreach ($p in $sidecars) {
    $f = Join-Path $source $p
    if ((Hash-File $f) -cne $receipt.protected_sidecars.$p.sha256) { throw 'Protected sidecar changed.' }
    $guard += $f
}
if ((Get-Item -LiteralPath $receipt.bundle.path).Length -ne $receipt.bundle.size -or
    (Hash-File $receipt.bundle.path) -cne $receipt.bundle.sha256) { throw 'Backup identity changed.' }
$guard += $receipt.bundle.path
foreach ($record in @(
    @('artifacts/tmp/stage2b2-20261103-132958/manifest.json','a24340c1b006283270d04c7c43aa1fe4b1b1ca85019b43af2fd56817107ac2f7'),
    @('artifacts/tmp/stage2b2-readable-v1-20261103-134527/manifest.json','332fa252dca79d2112dc071831c28e86f28bd3d88c0470e292335620180e8063'))) {
    $manifest = Join-Path $source $record[0]
    if ((Hash-File $manifest) -cne $record[1]) { throw 'Historical manifest changed.' }
    $guard += $manifest
    foreach ($output in (Get-Content -Raw -LiteralPath $manifest | ConvertFrom-Json).outputs) {
        $f = Join-Path (Split-Path $manifest) $output.file
        if ((Get-Item -LiteralPath $f).Length -ne $output.bytes -or (Hash-File $f) -cne $output.sha256) { throw 'Historical PNG changed.' }
        $guard += $f
    }
}
$adaptive = Join-Path $source 'artifacts/tmp/adaptive-cpu-1c4ee892573242e1818fdd2ff3eb866e'
Assert-PlainPath $adaptive
$files = @(Get-ChildItem -LiteralPath $adaptive -Force -File)
$arows = [string[]]@($files | ForEach-Object { $_.Name + (Hash-File $_.FullName) })
[Array]::Sort($arows,[StringComparer]::Ordinal)
if ($files.Count -ne 6 -or (Hash-Text ($arows -join '')) -cne '5a1a713347c03361ea27f47bc0b9f82370551acc0db33408a2a4ffee994999b8') { throw 'PR141 evidence changed.' }
$guard += @($files.FullName)
$guards = @(foreach ($p in ($guard | Select-Object -Unique)) { Assert-PlainPath $p; [pscustomobject]@{ Path=$p; Sha256=(Hash-File $p) } })
$refs = @{}
foreach ($tag in $receipt.tags.PSObject.Properties) {
    if ((Git-Read @('cat-file','-t',$tag.Name)).Trim() -cne 'tag') { throw 'Annotated tag missing.' }
    $refs[$tag.Name] = $receipt.remote_refs.('refs/tags/'+$tag.Name)
    $refs[($tag.Name+'^{}')] = $tag.Value
}
$refs['codex/terrain-fidelity-a1-artwork'] = $receipt.commits.a1.commit
$refs['codex/terrain-adaptive-cpu-prototype'] = '9a75949181349dbecc475bb12328cef69636ce92'
$stage3bPath = $null
$generated = @{}
function Assert-LabSnapshot([bool]$imported) {
    $now = Get-NativeSourceIdentity $source
    foreach ($key in @('Revision','Working','Index')) { if ($now.$key -cne $identity.$key) { throw "Source changed: $key" } }
    foreach ($ref in $refs.Keys) { if ((Git-Read @('rev-parse',$ref)).Trim() -cne $refs[$ref]) { throw 'Preservation ref changed.' } }
    foreach ($g in $guards) { Assert-PlainPath $g.Path; if ((Hash-File $g.Path) -cne $g.Sha256) { throw 'Control/evidence changed.' } }
    foreach ($entry in $inputs) {
        $f = Join-Path $source $entry.Source
        Assert-PlainPath $f
        if ((Hash-File $f) -cne $entry.Sha256) { throw 'Source input changed.' }
        if ($stage3bPath) {
            $f = Join-Path $stage3bPath $entry.Path
            Assert-PlainPath $f
            if ((Hash-File $f) -cne $entry.Sha256) { throw 'Staged input changed.' }
        }
    }
    if (-not $stage3bPath) { return }
    Assert-PlainPath $stage3bPath
    $queue = [Collections.Generic.Queue[string]]::new(); $queue.Enqueue($stage3bPath)
    while ($queue.Count) {
        foreach ($item in Get-ChildItem -Force -LiteralPath $queue.Dequeue()) {
            Assert-PlainPath $item.FullName # Check before descending; never follow links.
            $relative = [IO.Path]::GetRelativePath($stage3bPath,$item.FullName).Replace('\','/')
            if ($item.PSIsContainer) {
                if (-not ($imported -and ($relative -ceq '.godot' -or $relative.StartsWith('.godot/'))) -and
                    -not @($paths | Where-Object { $_.StartsWith($relative+'/') }).Count) { throw 'Unexpected stage directory.' }
                $queue.Enqueue($item.FullName)
            } elseif ($relative -cnotin $paths -and -not ($imported -and $relative.StartsWith('.godot/'))) {
                if (-not $imported -or $relative -cnotin @('scenes/experiments/terrain_stage3b/lab.gd.uid','scenes/experiments/terrain_stage3b/continuous.gdshader.uid') -or
                    $item.Length -gt 128 -or (Get-Content -Raw -LiteralPath $item.FullName).Trim() -cnotmatch '^uid://[a-z0-9]+$') { throw 'Unexpected stage output.' }
                $hash = Hash-File $item.FullName
                if ($generated.ContainsKey($relative) -and $generated[$relative] -cne $hash) { throw 'Generated UID changed.' }
                $generated[$relative] = $hash
            }
        }
    }
    foreach ($p in $generated.Keys) { if (-not (Test-Path -LiteralPath (Join-Path $stage3bPath $p) -PathType Leaf)) { throw 'Generated UID disappeared.' } }
}

$pinned = Get-StandardGodotIdentity
$summary = [pscustomobject]@{ Static='NOT RUN'; Import='NOT RUN'; Native='VISUAL NOT RUN'; Infrastructure='PASS';
    Authorization='ONE-TIME OWNER GRANT REQUIRED'; Reason=''; Revision=$identity.Revision; Working=$identity.Working;
    Executable=$pinned.Path; Sha256=$pinned.Sha256; StageDirectory=''; Inputs=$inputs; Commands=@(); Diagnostic='' }
try {
    Assert-LabSnapshot $false
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    $python = @(Get-Command python -CommandType Application)[0].Source
    $r = Invoke-BoundedProcess $python @('-B','-m','unittest','discover','-s','tests','-p','static_*test.py') $source -Seconds 360
    $summary.Diagnostic = $r.Excerpt
    if ($r.Status -ne 'PASS' -or $r.ExitCode -ne 0 -or -not $r.TerminationCertain -or
        ($r.Stdout+"`n"+$r.Stderr) -notmatch '(?m)^OK\r?$') { throw 'Static suite failed; no staging or engine launch.' }
    $summary.Static = 'PASS'
    Assert-LabSnapshot $false
    $parent = Get-NativeStageParent $source
    $stage3bPath = Join-Path $parent ('stage3b-'+[Guid]::NewGuid().ToString('N'))
    if (Test-Path -LiteralPath $stage3bPath) { throw 'Stage exists; no reuse.' }
    $null = New-Item -ItemType Directory -Path $stage3bPath
    $summary.StageDirectory = $stage3bPath
    foreach ($entry in $inputs) {
        $destination = Join-Path $stage3bPath $entry.Path
        Assert-PlainPath (Join-Path $source $entry.Source)
        Assert-PlainPath $destination
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        Assert-PlainPath $destination
        [IO.File]::Copy((Join-Path $source $entry.Source),$destination,$false)
    }
    Write-Host "Retained stage: $stage3bPath"
    $importArgs = @('--headless','--path',$stage3bPath,'--editor','--import','--quit')
    $visualArgs = @('--path',$stage3bPath,'--resolution','1280x720','res://scenes/experiments/terrain_stage3b/lab.tscn')
    $summary.Commands = @($importArgs,$visualArgs)
    Assert-LabSnapshot $false
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    $summary.Import = 'FAIL'
    $r = Invoke-BoundedProcess $pinned.Path $importArgs $stage3bPath -Seconds 60 -MaxBytes 1048576 -ExcerptBytes 4096
    $summary.Diagnostic = $r.Excerpt
    $outcome = Get-NativeOutcome Import $r # Health/error checks only, no smoke dispatch.
    if ($outcome.Status -ne 'PASS') { throw "Preparation failed: $($outcome.Reason)" }
    Assert-LabSnapshot $true
    $summary.Import = 'PASS'
    Assert-PinnedEngine $pinned.Path $pinned.Sha256
    Write-Host 'One visual session: owner inspect ready true, views 1/2/3, zoom 4/5/6, F diagnostics; Esc/close BEFORE 180s.'
    $summary.Native = 'VISUAL FAIL'
    $r = Invoke-BoundedProcess $pinned.Path $visualArgs $stage3bPath -Seconds 180 -MaxBytes 1048576 -ExcerptBytes 4096
    $summary.Diagnostic = $r.Excerpt
    $outcome = Get-NativeOutcome Import $r # Same exit/error checks; no invented visual completion marker.
    if ($outcome.Status -ne 'PASS') { throw "Visual process failed: $($outcome.Reason)" }
    Assert-LabSnapshot $true
    $summary.Native = 'VISUAL PROCESS PASS; OWNER ACCEPTANCE SEPARATE'
    Write-Host 'Process checks passed. Record actual owner observations separately; no automatic acceptance, retry or cleanup.'
} catch {
    $summary.Infrastructure = 'FAIL'
    $summary.Reason = [string]$_
    try { $evidence = Save-NativeFailureEvidence $source $summary; Write-Host "Retained bounded failure evidence: $evidence" }
    catch { Write-Warning 'Failure evidence could not be written; preserve stage and stop.' }
    throw # No subsequent phase, automatic retry, rerun, deletion or cleanup.
}
```

The 360-second static deadline reuses the reviewed metadata recipe's static-suite
budget; it does not change Native's deadline or authorize metadata execution.
Only the two explicit engine calls above consume the proposed one-time grant.
The existing failure writer retains at most 64 KiB in ignored `artifacts/logs/`
with a 4,096-byte diagnostic and hashed working/input provenance. Its legacy
`Native` field holds the visual process status here; it does not run Native.
There is no source stage, import, real-stage creation or Godot execution during
preparation/review. Any failure consumes the attempt; no fix-and-retry is implied.

Preparation validation (non-Godot): the complete procedure parses as PowerShell;
AST inspection finds only four bounded-process call sites (Git verification,
Python static suite, import and visual session). Synthetic PowerShell children
passed normal stdout/stderr completion, a one-second timeout and a reduced-cap
overflow check. Both forced-stop roots were confirmed absent; the helper still
reported termination uncertain, as required. These checks create no stage and
do not establish Godot GUI behavior, descendant containment or visual acceptance.
