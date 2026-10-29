#requires -Version 7.0
[CmdletBinding()]
param(
    [ValidateSet('Static', 'NativePlan', 'Native')][string]$Mode = 'Static',
    [string]$GodotPath,
    [string]$GodotSha256
)
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'

# Generic bounded subprocess helper. Public modes never dispatch Godot.
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
    $capture = @([IO.MemoryStream]::new(), [IO.MemoryStream]::new())
    $captured = 0; $terminationCertain = $false
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
                    $retain = [Math]::Min($count, $MaxBytes - $captured)
                    if ($retain -gt 0) {
                        $capture[$i].Write($buffers[$i], 0, $retain)
                        $captured += $retain
                    }
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
                $terminationCertain = $true
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
        # Timeout/overflow cannot certify descendant termination, even if the root exits.
        if ($started -and -not $terminationCertain) {
            Write-Warning 'Termination uncertain; process-tree kill is best effort. Stop further engine execution.'
        }
        $process.Dispose()
    }
    $diagnostic = [Text.Encoding]::UTF8.GetString($excerpt.ToArray())
    $excerpt.Dispose()
    $stdout = [Text.Encoding]::UTF8.GetString($capture[0].ToArray())
    $stderr = [Text.Encoding]::UTF8.GetString($capture[1].ToArray())
    foreach ($stream in $capture) { $stream.Dispose() }
    [pscustomobject]@{ Status = $status; ExitCode = $code; Bytes = $total; Excerpt = $diagnostic;
        Stdout = $stdout; Stderr = $stderr; TerminationCertain = $terminationCertain }
}

function Assert-PinnedEngine {
    param([string]$Engine, [string]$EngineHash)
    if (-not $Engine -or -not [IO.Path]::IsPathFullyQualified($Engine) -or
        $EngineHash -notmatch '^[0-9a-fA-F]{64}$') {
        throw 'NativePlan requires absolute GodotPath and exact GodotSha256.'
    }
    Assert-PlainPath $Engine
    if (-not (Test-Path -LiteralPath $Engine -PathType Leaf) -or
        (Get-FileHash -LiteralPath $Engine).Hash -ne $EngineHash) {
        throw 'Pinned executable missing or SHA-256 mismatch.'
    }
}

# Data only: callers cannot supply flags, scripts, scenes, deadlines or extra arguments.
function New-NativeCommandPlan {
    [CmdletBinding()]
    param([string]$Engine, [string]$EngineHash, $Stage)
    Assert-PinnedEngine $Engine $EngineHash
    Assert-PlainPath $Stage.Directory
    $directory = [IO.Path]::GetFullPath($Stage.Directory)
    $source = [IO.Path]::GetFullPath($Stage.Source).TrimEnd('\', '/')
    if (-not [IO.Path]::IsPathFullyQualified($Stage.Directory) -or
        $directory.Equals($source, [StringComparison]::OrdinalIgnoreCase) -or
        $directory.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        [IO.Path]::GetFileName($directory) -notmatch '^tlwh-native-plan-[0-9a-f]{32}$') {
        throw 'Only a fresh external input stage is permitted.'
    }
    $expected = @($Stage.Inputs.Path)
    if ('project.godot' -cnotin $expected -or 'tests/fabricator_recipe_switching_test.gd' -cnotin $expected) {
        throw 'Required project/test input missing.'
    }
    foreach ($entry in $Stage.Inputs) {
        if (-not (Test-ApprovedInput $entry.Path)) { throw 'Unapproved staged input.' }
        $path = Join-Path $directory $entry.Path
        Assert-PlainPath $path
        if ((Get-FileHash -LiteralPath $path).Hash -ne $entry.Sha256) { throw 'Staged input changed.' }
    }
    # Inspect links before recursing into each directory; never traverse a linked tree.
    $pendingDirectories = [Collections.Generic.Queue[string]]::new()
    $pendingDirectories.Enqueue($directory)
    $found = 0
    while ($pendingDirectories.Count) {
        foreach ($item in Get-ChildItem -Force -LiteralPath $pendingDirectories.Dequeue()) {
            Assert-PlainPath $item.FullName
            $relative = [IO.Path]::GetRelativePath($directory, $item.FullName).Replace('\', '/')
            if ($item.PSIsContainer) {
                if (-not @($expected | Where-Object { $_.StartsWith($relative + '/', [StringComparison]::Ordinal) }).Count) {
                    throw 'Unexpected staged directory.'
                }
                $pendingDirectories.Enqueue($item.FullName)
            } else {
                if ($relative -cnotin $expected) { throw 'Unexpected staged file.' }
                $found++
            }
        }
    }
    if ($found -ne $expected.Count) { throw 'Ambiguous staged inventory.' }
    foreach ($phase in @('Import', 'Native')) {
        $arguments = if ($phase -eq 'Import') {
            @('--headless', '--editor', '--path', $directory, '--quit')
        } else {
            @('--headless', '--path', $directory, '--script', 'res://tests/fabricator_recipe_switching_test.gd')
        }
        [pscustomobject]@{ Phase = $phase; Executable = $Engine; Sha256 = $EngineHash;
            Arguments = $arguments; Directory = $directory;
            Seconds = $(if ($phase -eq 'Import') { 60 } else { 30 }); MaxBytes = 1048576 }
    }
}

# Internal Stage A implementation: deliberately has NO public entry-point caller.
# Tests replace named helpers in child scope; no executable/callback injection API.
function Get-NativeSourceIdentity {
    param([string]$Source)
    Assert-PlainPath $Source
    $git = @(Get-Command git -CommandType Application -ErrorAction Stop)[0].Source
    $values = @{}
    foreach ($key in @('Root', 'Revision', 'Working', 'Index')) {
        $arguments = switch ($key) {
            Root { @('rev-parse', '--show-toplevel') }
            Revision { @('rev-parse', 'HEAD') }
            Working { @('status', '--porcelain=v1', '--untracked-files=normal') }
            Index { @('ls-files', '--stage', '-z') }
        }
        $r = Invoke-BoundedProcess $git $arguments $Source -ExcerptBytes 1048576
        if ($r.Status -ne 'PASS' -or -not $r.TerminationCertain -or $r.ExitCode -ne 0) {
            throw "Source identity unavailable: $key"
        }
        $values[$key] = $r.Stdout
    }
    if (-not ([IO.Path]::GetFullPath($values.Root.Trim())).Equals(
        [IO.Path]::GetFullPath($Source), [StringComparison]::OrdinalIgnoreCase) -or
        $values.Revision.Trim() -notmatch '^([0-9a-f]{40}|[0-9a-f]{64})$') { throw 'Invalid source identity.' }
    $tracked = @(foreach ($record in $values.Index.Split([char]0, [StringSplitOptions]::RemoveEmptyEntries)) {
        if ($record -notmatch '^100(644|755) [0-9a-f]+ 0\t(.+)$') { throw 'Unsafe or unresolved source index.' }
        $Matches[2]
    })
    [pscustomobject]@{ Revision = $values.Revision.Trim(); Working = $values.Working;
        Index = $values.Index; Tracked = $tracked }
}

function Assert-NativeDispatchInputs {
    param($Stage, $Identity, [bool]$Imported)
    if (-not [IO.Path]::IsPathFullyQualified($Stage.Directory) -or
        -not [IO.Path]::IsPathFullyQualified($Stage.Source)) { throw 'Stage paths must be absolute.' }
    $directory = [IO.Path]::GetFullPath($Stage.Directory).TrimEnd('\', '/')
    $source = [IO.Path]::GetFullPath($Stage.Source).TrimEnd('\', '/')
    if ([IO.Path]::GetFileName($directory) -notmatch '^tlwh-native-plan-[0-9a-f]{32}$' -or
        $directory.Equals($source, [StringComparison]::OrdinalIgnoreCase) -or
        $directory.StartsWith($source + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase) -or
        $source.StartsWith($directory + [IO.Path]::DirectorySeparatorChar, [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Stage identity or source separation invalid.'
    }
    $current = Get-NativeSourceIdentity $Stage.Source
    foreach ($key in @('Revision', 'Working', 'Index')) {
        if ($current.$key -cne $Identity.$key) { throw "Source changed: $key" }
    }
    $approved = @($current.Tracked | Where-Object { Test-ApprovedInput $_ })
    if ($approved.Count -ne $Stage.Inputs.Count -or
        @($approved | Select-Object -Unique).Count -ne $approved.Count) { throw 'Source inventory changed.' }
    foreach ($entry in $Stage.Inputs) {
        if ($entry.Path -cnotin $approved) { throw 'Unapproved source input.' }
        foreach ($root in @($Stage.Source, $Stage.Directory)) {
            $path = Join-Path $root $entry.Path
            Assert-PlainPath $path
            if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash -cne $entry.Sha256) {
                throw "Source or staged input changed: $($entry.Path)"
            }
        }
    }
    # Import may create .godot only. Traverse it with the same no-link rule;
    # never delete it or allow additions elsewhere. Original inputs stay immutable.
    Assert-PlainPath $Stage.Directory
    $queue = [Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($Stage.Directory)
    while ($queue.Count) {
        foreach ($item in Get-ChildItem -Force -LiteralPath $queue.Dequeue()) {
            Assert-PlainPath $item.FullName
            $relative = [IO.Path]::GetRelativePath($Stage.Directory, $item.FullName).Replace('\', '/')
            if ($Imported -and ($relative -ceq '.godot' -or $relative.StartsWith('.godot/', [StringComparison]::Ordinal))) {
                if ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
                continue
            }
            if ($item.PSIsContainer) {
                if (-not @($approved | Where-Object { $_.StartsWith($relative + '/', [StringComparison]::Ordinal) }).Count) {
                    throw 'Unexpected staged directory.'
                }
                $queue.Enqueue($item.FullName)
            } elseif ($relative -cnotin $approved) { throw 'Unexpected staged file.' }
        }
    }
}

function Save-NativeFailureEvidence {
    param([string]$Source, $Summary)
    $directory = Join-Path $Source 'artifacts/logs'
    Assert-PlainPath $directory
    $path = Join-Path $directory ('native-failure-' + [Guid]::NewGuid().ToString('N') + '.json')
    $git = @(Get-Command git -CommandType Application -ErrorAction Stop)[0].Source
    $ignored = Invoke-BoundedProcess $git @('check-ignore', '--quiet', '--', $path) $Source
    if ($ignored.Status -ne 'PASS' -or $ignored.ExitCode -ne 0 -or -not $ignored.TerminationCertain) {
        throw 'Failure evidence destination is not confirmed ignored.'
    }
    # Inventory is reported to the caller; evidence retains bounded diagnostics
    # and provenance, never an unbounded copy of the complete working-status text.
    $record = [ordered]@{}
    foreach ($key in @('Static', 'Import', 'Native', 'Reason', 'Revision', 'Executable', 'Sha256',
        'StageDirectory', 'Commands', 'Diagnostic')) { $record[$key] = $Summary.$key }
    $hasher = [Security.Cryptography.SHA256]::Create()
    try {
        $record.WorkingSha256 = [BitConverter]::ToString($hasher.ComputeHash(
            [Text.Encoding]::UTF8.GetBytes($Summary.Working))).Replace('-', '')
        $record.InputsSha256 = [BitConverter]::ToString($hasher.ComputeHash(
            [Text.Encoding]::UTF8.GetBytes((ConvertTo-Json -InputObject @($Summary.Inputs) -Depth 4 -Compress)))).Replace('-', '')
    } finally { $hasher.Dispose() }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Depth 8))
    if ($bytes.Length -gt 65536) { throw 'Failure evidence exceeds 64 KiB.' }
    $null = [IO.Directory]::CreateDirectory($directory)
    Assert-PlainPath $directory
    $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
    return $path
}

function Invoke-RestrictedNativeDispatch {
    [CmdletBinding()]
    param([string]$Source, [string]$Engine, [string]$EngineHash,
          [ValidateSet('PASS', 'FAIL', 'NOT RUN')][string]$StaticStatus)
    $summary = [pscustomobject]@{ Static = $StaticStatus; Import = 'NOT RUN'; Native = 'NOT RUN';
        Reason = 'STATIC_NOT_PASS'; Revision = ''; Working = ''; Executable = $Engine; Sha256 = $EngineHash;
        StageDirectory = ''; Inputs = @(); Commands = @(); Diagnostic = ''; Evidence = ''; EvidenceError = '' }
    if ($StaticStatus -ne 'PASS') { return $summary }
    $phase = 'Import'
    try {
        Assert-PinnedEngine $Engine $EngineHash
        $identity = Get-NativeSourceIdentity $Source
        $summary.Revision = $identity.Revision; $summary.Working = $identity.Working
        $stage = New-InputStage $Source ([IO.Path]::GetTempPath()) $identity.Tracked
        $summary.StageDirectory = $stage.Directory; $summary.Inputs = $stage.Inputs
        $commands = @(New-NativeCommandPlan $Engine $EngineHash $stage)
        foreach ($command in $commands) {
            $phase = $command.Phase
            $summary.Commands += $command
            $summary.$phase = 'FAIL'
            Assert-NativeDispatchInputs $stage $identity ($phase -eq 'Native')
            # Last check before the one synchronous bounded launch. No retries.
            Assert-PinnedEngine $Engine $EngineHash
            $result = Invoke-BoundedProcess $command.Executable $command.Arguments $command.Directory `
                -Seconds $command.Seconds -MaxBytes $command.MaxBytes -ExcerptBytes 4096
            $outcome = Get-NativeOutcome $phase $result
            $summary.$phase = $outcome.Status; $summary.Reason = $outcome.Reason
            $summary.Diagnostic = $outcome.Diagnostic
            if ($outcome.Status -ne 'PASS') { break }
        }
    } catch {
        $summary.$phase = 'FAIL'; $summary.Reason = 'DISPATCH_VALIDATION_OR_PROCESS_FAILURE'
        $message = [Text.Encoding]::UTF8.GetBytes([string]$_)
        $summary.Diagnostic = [Text.Encoding]::UTF8.GetString($message, 0, [Math]::Min(4096, $message.Length))
    }
    if ($summary.Import -eq 'FAIL' -or $summary.Native -eq 'FAIL') {
        try { $summary.Evidence = Save-NativeFailureEvidence $Source $summary }
        catch { $summary.EvidenceError = 'Failure evidence could not be saved; inspect returned bounded diagnostic.' }
    }
    return $summary
}

function Get-NativeOutcome {
    param([ValidateSet('Import', 'Native')][string]$Phase, $Result)
    $reason = 'OK'
    $output = $Result.Stdout + "`n" + $Result.Stderr
    if ($Result.Status -ne 'PASS') { $reason = $Result.Status }
    elseif (-not $Result.TerminationCertain) { $reason = 'UNCERTAIN_TERMINATION' }
    elseif ($Result.Bytes -gt 1048576 -or
        [Text.Encoding]::UTF8.GetByteCount($Result.Stdout + $Result.Stderr) -gt 1048576) { $reason = 'OUTPUT_LIMIT' }
    elseif ($Result.ExitCode -cne 0) { $reason = 'ABNORMAL_EXIT' }
    elseif ($output -match '(?im)\b(ERROR|SCRIPT ERROR|parse error|assertion failed|assertion failure)\b') { $reason = 'ENGINE_ERROR' }
    elseif ($Phase -eq 'Native') {
        $prefix = 'Fabricator recipe switching regression failures:'
        $records = @([regex]::Matches($output, '(?m)^Fabricator recipe switching regression failures:.*$'))
        $lines = @($Result.Stdout.TrimEnd().Split("`n"))
        if ($records.Count -ne 1 -or $records[0].Value.TrimEnd("`r") -cne "$prefix 0" -or
            $lines[-1].TrimEnd("`r") -cne "$prefix 0") {
            $reason = if ($records.Count -eq 1 -and $records[0].Value -match ': [1-9][0-9]*\r?$') {
                'ASSERTION_FAILURE'
            } else { 'MISSING_OR_MALFORMED_COMPLETION' }
        }
    }
    $diagnosticBytes = [Text.Encoding]::UTF8.GetBytes($output)
    $diagnostic = [Text.Encoding]::UTF8.GetString($diagnosticBytes, 0, [Math]::Min(4096, $diagnosticBytes.Length))
    [pscustomobject]@{ Status = $(if ($reason -eq 'OK') { 'PASS' } else { 'FAIL' });
        Reason = $reason; Diagnostic = $diagnostic }
}

# Inert dispatcher: consumes synthetic result records, never calls a process helper.
# There is deliberately no executor callback or real-execution switch.
function Invoke-SyntheticNativeSequence {
    [CmdletBinding()]
    param([string]$Engine, [string]$EngineHash, $Stage,
          [ValidateSet('PASS', 'FAIL', 'NOT RUN')][string]$StaticStatus, [object[]]$Results = @())
    $summary = [pscustomobject]@{ Static = $StaticStatus; Import = 'NOT RUN'; Native = 'NOT RUN';
        Reason = 'STATIC_NOT_PASS'; Commands = @(); Synthetic = $true; Diagnostic = '';
        Executable = $Engine; Sha256 = $EngineHash; StageDirectory = $Stage.Directory }
    if ($StaticStatus -ne 'PASS') { return $summary }
    $commands = @(New-NativeCommandPlan $Engine $EngineHash $Stage)
    foreach ($command in $commands) {
        # Recheck bytes at each simulated dispatch, without invoking the executable.
        Assert-PinnedEngine $Engine $EngineHash
        $index = $summary.Commands.Count
        $summary.Commands += $command
        $summary.($command.Phase) = 'FAIL'
        if ($index -ge $Results.Count) { $summary.Reason = 'MISSING_RESULT'; break }
        try { $outcome = Get-NativeOutcome $command.Phase $Results[$index] }
        catch { $summary.Reason = 'MALFORMED_RESULT'; break }
        $summary.($command.Phase) = $outcome.Status
        $summary.Reason = $outcome.Reason
        $summary.Diagnostic = $outcome.Diagnostic
        if ($outcome.Status -ne 'PASS') { break }
    }
    return $summary
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
    [pscustomobject]@{ Directory = $stage; Source = $Source; Inputs = @($inputs) }
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
            Assert-PinnedEngine $Engine $EngineHash
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
            $commands = @(New-NativeCommandPlan $Engine $EngineHash $stage)
            $plan = 'PASS'
            Write-Host "Retained dry-run stage: $($stage.Directory)"
            foreach ($entry in $stage.Inputs) { Write-Host "$($entry.Sha256) $($entry.Path)" }
            foreach ($command in $commands) {
                Write-Host "PROPOSED ONLY ($($command.Phase), sequential after prior PASS): executable=$($command.Executable | ConvertTo-Json -Compress) arguments=$($command.Arguments | ConvertTo-Json -Compress) ($($command.Seconds)s, $($command.MaxBytes) bytes)"
            }
        }
        $exitCode = 0
    } catch { Write-Host "FAIL (configuration/infrastructure or earlier phase): $_" }
    Write-Host "Summary: static=$static; staging plan=$plan; native import=NOT RUN; recipe test=NOT RUN; overall=$(if ($exitCode -eq 0) { 'PASS' } else { 'FAIL' })"
    return $exitCode
}

# Dot-sourcing is used by non-Godot fixtures; it does not authorize dispatch.
if ($MyInvocation.InvocationName -ne '.') {
    exit (Invoke-LocalTests (Split-Path $PSScriptRoot -Parent) $Mode $GodotPath $GodotSha256)
}
