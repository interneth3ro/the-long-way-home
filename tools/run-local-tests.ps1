#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Static', 'NativePlan', 'Native')][string]$Mode = 'Static',
    [string]$GodotPath,
    [string]$GodotSha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Generic bounded subprocess helper. Native execution has no call site in this PR.
function Invoke-BoundedProcess {
    param([string]$Executable, [string[]]$Arguments, [string]$Directory,
          [int]$Seconds = 60, [int]$MaxBytes = 1048576, [int]$ExcerptBytes = 4096)
    if ($Seconds -lt 1 -or $MaxBytes -lt 1 -or $ExcerptBytes -lt 1 -or $ExcerptBytes -gt $MaxBytes) { throw 'Invalid process limits.' }
    $info = [Diagnostics.ProcessStartInfo]::new()
    $info.FileName = $Executable
    $info.WorkingDirectory = $Directory
    $info.UseShellExecute = $false
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    $info.Environment['PYTHONDONTWRITEBYTECODE'] = '1'
    foreach ($argument in $Arguments) { $info.ArgumentList.Add($argument) }
    $process = [Diagnostics.Process]::new()
    $process.StartInfo = $info
    $status = 'PASS'; $code = $null; $total = 0; $started = $false
    $excerpt = [IO.MemoryStream]::new()
    $watch = [Diagnostics.Stopwatch]::StartNew()
    try {
        if (-not $process.Start()) { throw 'Process did not start.' }
        $started = $true
        $streams = @($process.StandardOutput.BaseStream, $process.StandardError.BaseStream)
        $buffers = @([byte[]]::new(4096), [byte[]]::new(4096))
        $pending = @($streams[0].ReadAsync($buffers[0], 0, 4096),
                     $streams[1].ReadAsync($buffers[1], 0, 4096))
        while ($true) {
            for ($i = 0; $i -lt 2; $i++) {
                if ($null -ne $pending[$i] -and $pending[$i].IsCompleted) {
                    $count = $pending[$i].GetAwaiter().GetResult()
                    $total += $count
                    $keep = [Math]::Min($count, $ExcerptBytes - [int]$excerpt.Length)
                    if ($keep -gt 0) { $excerpt.Write($buffers[$i], 0, $keep) }
                    $pending[$i] = if ($count -gt 0) {
                        $streams[$i].ReadAsync($buffers[$i], 0, 4096)
                    } else { $null }
                }
            }
            if ($total -gt $MaxBytes) { $status = 'OUTPUT_LIMIT'; break }
            if ($watch.Elapsed.TotalSeconds -ge $Seconds) { $status = 'TIMEOUT'; break }
            if ($process.HasExited -and $null -eq $pending[0] -and $null -eq $pending[1]) {
                $code = $process.ExitCode
                if ($code -ne 0) { $status = 'NONZERO_EXIT' }
                break
            }
            Start-Sleep -Milliseconds 10
        }
    } finally {
        if ($started -and -not $process.HasExited) {
            # Best effort only; bounded wait, no PID-name search or automatic retry.
            try { $process.Kill($true); $null = $process.WaitForExit(2000) }
            catch { Write-Warning "Process-tree cleanup failed: $_" }
        }
        $process.Dispose()
    }
    $diagnostic = [Text.Encoding]::UTF8.GetString($excerpt.ToArray())
    $excerpt.Dispose()
    [pscustomobject]@{ Status = $status; ExitCode = $code; Bytes = $total; Excerpt = $diagnostic }
}

function Assert-PlainPath {
    param([string]$Path)
    $current = [IO.Path]::GetFullPath($Path)
    while ($current) {
        if (Test-Path -LiteralPath $current) {
            if ((Get-Item -Force -LiteralPath $current).Attributes -band [IO.FileAttributes]::ReparsePoint) {
                throw "Reparse point prohibited: $current"
            }
        }
        $current = [IO.Path]::GetDirectoryName($current)
    }
}

function Test-ApprovedInput {
    param([string]$Relative)
    if ($Relative -match '(^/|\\|:|[\x00-\x1f]|(^|/)\.{1,2}(/|$))') {
        throw "Unsafe input path: $Relative"
    }
    foreach ($segment in $Relative.Split('/')) {
        if ($segment -notmatch '^[A-Za-z0-9_. -]+$' -or $segment -match '[. ]$' -or
            $segment -match '^(?i:CON|PRN|AUX|NUL|COM[0-9]|LPT[0-9])(\.|$)') {
            throw "Unsafe Windows path segment: $Relative"
        }
    }
    if ($Relative -match '(?i)(^|/)(\.[^/]+|artifacts|saves?|settings|credentials?)([./]|$)' -or
        $Relative -match '(?i)(secret|credential|\.env|export_presets)') { return $false }
    if ($Relative -ceq 'project.godot') { return $true }
    if ($Relative -cmatch '^tests/fabricator_recipe_switching_test\.gd(\.uid)?$') { return $true }
    # Narrow tracked resource inventory; expanding this list requires review.
    return $Relative -cmatch '^(assets|construction|dialogue|inventory|objectives|scenes|shaders)/.+\.(gd|gd\.uid|tscn|tres|gdshader|gdshader\.uid|png|svg|png\.import|svg\.import|json)$'
}

function New-InputStage {
    param([string]$Source, [string]$Parent, [string[]]$Tracked)
    $Source = [IO.Path]::GetFullPath($Source).TrimEnd('\', '/')
    $Parent = [IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    Assert-PlainPath $Source
    Assert-PlainPath $Parent
    if ($Parent.Equals($Source, [StringComparison]::OrdinalIgnoreCase) -or
        $Parent.StartsWith($Source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Staging must be outside the source checkout.'
    }
    if (-not (Test-Path -LiteralPath $Parent -PathType Container)) { throw 'Stage parent must exist.' }
    # Validate the complete list before creating any output.
    $inputs = foreach ($relative in $Tracked) {
        if (Test-ApprovedInput $relative) {
            $path = Join-Path $Source $relative
            Assert-PlainPath $path
            if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { throw "Missing tracked input: $relative" }
            [pscustomobject]@{ Path = $relative; Sha256 = (Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash }
        }
    }
    if ('project.godot' -cnotin @($inputs.Path) -or
        'tests/fabricator_recipe_switching_test.gd' -cnotin @($inputs.Path)) { throw 'Required project/test input missing.' }
    $stage = Join-Path $Parent ('tlwh-native-plan-' + [Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $stage
    Write-Host "Stage created (retained even on failure): $stage"
    foreach ($entry in $inputs) {
        $sourcePath = Join-Path $Source $entry.Path
        Assert-PlainPath $sourcePath
        $destination = Join-Path $stage $entry.Path
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($destination))
        [IO.File]::Copy($sourcePath, $destination, $false)
        if ((Get-FileHash -LiteralPath $destination).Hash -ne $entry.Sha256 -or
            (Get-FileHash -LiteralPath $sourcePath).Hash -ne $entry.Sha256) {
            throw "Input changed during staging: $($entry.Path); inspect retained stage $stage"
        }
    }
    [pscustomobject]@{ Directory = $stage; Inputs = @($inputs) }
}

function Invoke-LocalTests {
    param([string]$Root, [string]$RequestedMode, [string]$Engine, [string]$EngineHash)
    $static = 'NOT RUN'; $plan = 'NOT RUN'; $exitCode = 1
    try {
        # Deliberately unconditional: no environment variable, token or switch unlocks execution.
        if ($RequestedMode -eq 'Native') { throw 'Native execution prohibited by current policy; use NativePlan.' }
        if (-not $IsWindows) { throw 'This entry point supports Windows PowerShell 7 only.' }
        Assert-PlainPath $Root
        $git = @(Get-Command git -CommandType Application -ErrorAction Stop)[0].Source
        $python = @(Get-Command python -CommandType Application -ErrorAction Stop)[0].Source
        $checkout = Invoke-BoundedProcess $git @('rev-parse', '--show-toplevel') $Root
        if ($checkout.Status -ne 'PASS' -or
            -not ([IO.Path]::GetFullPath($checkout.Excerpt.Trim())).Equals(
                [IO.Path]::GetFullPath($Root), [StringComparison]::OrdinalIgnoreCase)) { throw 'Runner must reside in the actual checkout.' }
        $revision = Invoke-BoundedProcess $git @('rev-parse', 'HEAD') $Root
        $changes = Invoke-BoundedProcess $git @('status', '--short', '--untracked-files=normal') $Root
        if ($revision.Status -ne 'PASS' -or $changes.Status -ne 'PASS' -or $changes.Bytes -gt 4096) {
            throw 'Cannot report complete revision/working input status.'
        }
        Write-Host "Source revision: $($revision.Excerpt.Trim())"
        Write-Host "Working status (untracked files are excluded from staging):`n$($changes.Excerpt.Trim())"
        # Configuration is checked without invoking the pinned binary, even for --version.
        if ($RequestedMode -eq 'NativePlan') {
            if (-not $Engine -or -not [IO.Path]::IsPathFullyQualified($Engine) -or
                $EngineHash -notmatch '^[0-9a-fA-F]{64}$') { throw 'NativePlan requires absolute GodotPath and exact GodotSha256.' }
            Assert-PlainPath $Engine
            if (-not (Test-Path -LiteralPath $Engine -PathType Leaf) -or
                (Get-FileHash -LiteralPath $Engine).Hash -ne $EngineHash) { throw 'Pinned executable missing or SHA-256 mismatch.' }
            Write-Host "Pinned executable (not invoked): $Engine SHA256=$EngineHash"
        } elseif ($Engine -or $EngineHash) { throw 'Engine configuration requires NativePlan.' }
        $suite = @(Get-ChildItem -LiteralPath (Join-Path $Root 'tests') -Filter 'static_*test.py' -File)
        if ($suite.Count -eq 0) { throw 'Static suite is missing.' }
        foreach ($file in $suite) { Assert-PlainPath $file.FullName }
        $static = 'FAIL'
        $result = Invoke-BoundedProcess $python @('-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'static_*test.py') $Root
        $static = if ($result.Status -eq 'PASS') { 'PASS' } else { 'FAIL' }
        Write-Host "Static: $static ($($result.Status), exit=$($result.ExitCode), bytes=$($result.Bytes))"
        Write-Host $result.Excerpt.Trim()
        if ($static -ne 'PASS') { throw 'Static suite failed; no subsequent phase permitted.' }
        if ($RequestedMode -eq 'NativePlan') {
            $plan = 'FAIL'
            $listing = Invoke-BoundedProcess $git @('ls-files', '--stage', '-z') $Root -ExcerptBytes 1048576
            if ($listing.Status -ne 'PASS') { throw 'Tracked inventory unavailable.' }
            $tracked = foreach ($record in $listing.Excerpt.Split([char]0, [StringSplitOptions]::RemoveEmptyEntries)) {
                if ($record -notmatch '^100644 [0-9a-f]+ 0\t(.+)$' -and
                    $record -notmatch '^100755 [0-9a-f]+ 0\t(.+)$') {
                    throw 'Only regular, resolved Git index files may be staged.'
                }
                $Matches[1]
            }
            $stage = New-InputStage $Root ([IO.Path]::GetTempPath()) $tracked
            $plan = 'PASS'
            Write-Host "Retained dry-run stage: $($stage.Directory)"
            foreach ($entry in $stage.Inputs) { Write-Host "$($entry.Sha256) $($entry.Path)" }
            Write-Host "PROPOSED ONLY: `"$Engine`" --headless --editor --path `"$($stage.Directory)`" --quit (60s, 1048576 bytes)"
            Write-Host "THEN ONLY IF IMPORT PASSES: `"$Engine`" --headless --path `"$($stage.Directory)`" --script res://tests/fabricator_recipe_switching_test.gd (30s, 1048576 bytes)"
        }
        $exitCode = 0
    } catch { Write-Host "FAIL (configuration/infrastructure or earlier phase): $_" }
    Write-Host "Summary: static=$static; staging plan=$plan; native import=NOT RUN; recipe test=NOT RUN; overall=$(if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' })"
    return $exitCode
}

# Dot-sourcing exposes only helpers for harmless synthetic fixtures.
if ($MyInvocation.InvocationName -ne '.') {
    exit (Invoke-LocalTests (Split-Path $PSScriptRoot -Parent) $Mode $GodotPath $GodotSha256)
}
