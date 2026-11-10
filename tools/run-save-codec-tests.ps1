#requires -Version 7.0
[CmdletBinding()]
param([ValidateSet('Static', 'Run')][string]$Mode = 'Run')
Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
# Dot-sourcing the existing helper library must not replace our requested mode.
$codecInvocationMode = $Mode
. "$PSScriptRoot/run-local-tests.ps1"

function Assert-CodecAuthorization {
    throw 'AUTHORIZATION_DENIED: codec runner is inactive; separate owner approval and reviewed source activation required.'
}

function Get-CodecHash([byte[]]$Bytes) {
    $hasher = [Security.Cryptography.SHA256]::Create()
    try { [Convert]::ToHexString($hasher.ComputeHash($Bytes)) } finally { $hasher.Dispose() }
}

function Get-CodecDiagnostic([string]$Text) {
    $bytes = [Text.Encoding]::UTF8.GetBytes($Text)
    $length = [Math]::Min(4096, $bytes.Length)
    while ($true) {
        try { return [Text.UTF8Encoding]::new($false, $true).GetString($bytes, 0, $length) }
        catch [Text.DecoderFallbackException] { $length-- }
    }
}

function Get-CodecInputs {
    # Reviewed UTF-8/no-BOM/LF bytes: codec/test at PR #172; template in this PR.
    [pscustomobject]@{ Source = 'tests/fixtures/save_codec/project.godot'; Path = 'project.godot'; Sha256 = '37985F18F83537EC2265306776348FDB0FCAE41A08CD27908F107AED7BDB10F9' }
    [pscustomobject]@{ Source = 'persistence/save_file_codec.gd'; Path = 'persistence/save_file_codec.gd'; Sha256 = '0348779F7170346D4293823F2D118F56FFFFD44F2CC971134D79560A971F5253' }
    [pscustomobject]@{ Source = 'tests/save_file_codec_test.gd'; Path = 'tests/save_file_codec_test.gd'; Sha256 = 'D816238FF1C5046AEC4F3C5109F76CB6D75F8DDD67E3C82001555ACA0EDC7E41' }
}

function Get-CodecSourceBytes([string]$Path) {
    Assert-PlainPath $Path
    if (-not (Test-Path -LiteralPath $Path -PathType Leaf) -or (Get-Item -LiteralPath $Path).Length -gt 1048576) { throw 'Missing or oversized codec input.' }
    $raw = [IO.File]::ReadAllBytes($Path)
    $text = [Text.UTF8Encoding]::new($false, $true).GetString($raw).Replace("`r`n", "`n")
    [pscustomobject]@{ RawHash = (Get-CodecHash $raw); Bytes = [Text.Encoding]::UTF8.GetBytes($text) }
}

function Invoke-CodecGit([string]$Source, [string[]]$Arguments) {
    $git = @(Get-Command git -CommandType Application -ErrorAction Stop)[0].Source
    $result = Invoke-BoundedProcess $git $Arguments $Source -ExcerptBytes 1048576
    if ($result.Status -cne 'PASS' -or $result.ExitCode -cne 0 -or -not $result.TerminationCertain) { throw 'Codec Git preflight failed.' }
    $result.Stdout
}

function Get-CodecSnapshot([string]$Source) {
    $identity = Get-NativeSourceIdentity $Source
    $origin = (Invoke-CodecGit $Source @('remote', 'get-url', 'origin')).Trim()
    if ($origin -cnotin @('https://github.com/interneth3ro/the-long-way-home.git', 'git@github.com:interneth3ro/the-long-way-home.git')) { throw 'Unexpected repository identity.' }
    $null = Invoke-CodecGit $Source @('merge-base', '--is-ancestor', 'c048787628843719f693ae0116458242d41b0ead', $identity.Revision)
    $controls = @('tools', 'AGENTS.md', '.gitignore', '.gitattributes', 'docs/LOCAL_TESTING.md', 'docs/SAVE_CODEC_RUNNER.md', 'docs/SAVE_FILE_FORMAT.md',
        'tests/static_*test.py', 'tests/save_codec_runner_fixture_test.ps1', 'tests/fixtures/save_codec',
        'persistence/save_file_codec.gd', 'tests/save_file_codec_test.gd')
    $null = Invoke-CodecGit $Source (@('diff', '--quiet', $identity.Revision, '--') + $controls)
    foreach ($control in @('tools/run-save-codec-tests.ps1', 'tests/save_codec_runner_fixture_test.ps1',
        'tests/static_save_codec_runner_test.py', 'docs/SAVE_CODEC_RUNNER.md')) {
        if ($control -cnotin $identity.Tracked) { throw 'Runner controls must be committed and reviewed before execution.' }
    }
    foreach ($file in Get-ChildItem -LiteralPath (Join-Path $Source 'tests') -Filter 'static_*test.py' -File) {
        Assert-PlainPath $file.FullName
        $relative = [IO.Path]::GetRelativePath($Source, $file.FullName).Replace('\', '/')
        if ($relative -cnotin $identity.Tracked) { throw 'Untracked static test is not a reviewed control.' }
    }
    $inputs = @(foreach ($input in (Get-CodecInputs)) {
        if ($input.Source -cnotin $identity.Tracked) { throw 'Codec source input is not tracked.' }
        $bytes = Get-CodecSourceBytes (Join-Path $Source $input.Source)
        if ((Get-CodecHash $bytes.Bytes) -cne $input.Sha256) { throw 'Reviewed codec input hash changed.' }
        [pscustomobject]@{ Source = $input.Source; Path = $input.Path; Sha256 = $input.Sha256; RawHash = $bytes.RawHash }
    })
    [pscustomobject]@{ Identity = $identity; Inputs = $inputs }
}

function Assert-CodecSnapshot([string]$Source, $Snapshot) {
    if ((Get-CodecSnapshot $Source | ConvertTo-Json -Depth 8 -Compress) -cne ($Snapshot | ConvertTo-Json -Depth 8 -Compress)) { throw 'Source revision, status, index or inputs changed since static preflight.' }
}

function Assert-CodecIsolation([string]$Source, [string]$Parent, [string]$Directory) {
    foreach ($path in @($Source, $Parent, $Directory)) {
        if (-not [IO.Path]::IsPathFullyQualified($path)) { throw 'Absolute codec paths required.' }
        Assert-PlainPath $path
    }
    $sourcePath = [IO.Path]::GetFullPath($Source).TrimEnd('\', '/')
    $parentPath = [IO.Path]::GetFullPath($Parent).TrimEnd('\', '/')
    $stagePath = [IO.Path]::GetFullPath($Directory).TrimEnd('\', '/')
    $comparison = [StringComparison]::OrdinalIgnoreCase
    if ($sourcePath.Equals($parentPath, $comparison) -or $sourcePath.StartsWith($parentPath + '\', $comparison) -or
        $parentPath.StartsWith($sourcePath + '\', $comparison) -or
        -not [IO.Path]::GetDirectoryName($stagePath).Equals($parentPath, $comparison) -or
        [IO.Path]::GetFileName($stagePath) -cnotmatch '^tlwh-codec-[0-9a-f]{32}$') { throw 'Source/stage overlap or unsafe codec stage path.' }
}

function Get-CodecCommandPlan([string]$Source, [string]$Directory) {
    Assert-CodecIsolation $Source 'D:\GameDev\Godot\TLWH-NativeStages' $Directory
    # Data only. No process or directory creation and no executable/argument override.
    foreach ($phase in @('Import', 'Codec')) {
        $arguments = if ($phase -ceq 'Import') { @('--headless', '--editor', '--path', $Directory, '--quit') }
                     else { @('--headless', '--path', $Directory, '--script', 'res://tests/save_file_codec_test.gd') }
        [pscustomobject]@{ Phase = $phase; Executable = 'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe';
            Sha256 = 'AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424';
            Arguments = $arguments; Directory = $Directory; Seconds = $(if ($phase -ceq 'Import') { 60 } else { 30 }); MaxBytes = 1048576 }
    }
}

function New-CodecStage([string]$Source, $Snapshot) {
    Assert-CodecAuthorization # Also guards direct helper invocation before side effects.
    Assert-CodecSnapshot $Source $Snapshot
    $parent = 'D:\GameDev\Godot\TLWH-NativeStages'
    $id = [Guid]::NewGuid().ToString('N')
    $directory = Join-Path $parent ('tlwh-codec-' + $id)
    Assert-CodecIsolation $Source $parent $directory
    if (-not (Test-Path -LiteralPath $parent -PathType Container) -or (Test-Path -LiteralPath $directory)) { throw 'Stage parent missing or fresh stage already exists.' }
    $null = New-Item -ItemType Directory -Path $directory -ErrorAction Stop
    try {
    $inputs = @(foreach ($input in $Snapshot.Inputs) {
        $bytes = Get-CodecSourceBytes (Join-Path $Source $input.Source)
        if ($bytes.RawHash -cne $input.RawHash -or (Get-CodecHash $bytes.Bytes) -cne $input.Sha256) { throw 'Input changed before stage copy.' }
        $content = $bytes.Bytes
        if ($input.Path -ceq 'project.godot') {
            $content = [Text.Encoding]::UTF8.GetBytes([Text.Encoding]::UTF8.GetString($content).Replace('__STAGE_ID__', $id))
        }
        $path = Join-Path $directory $input.Path
        $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
        Assert-PlainPath $path
        $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
        try { $stream.Write($content, 0, $content.Length) } finally { $stream.Dispose() }
        [pscustomobject]@{ Path = $input.Path; Sha256 = (Get-CodecHash $content) }
    })
    $stage = [pscustomobject]@{ Source = $Source; Parent = $parent; Directory = $directory; Inputs = $inputs; Generated = @(); GeneratedCaptured = $false }
    Assert-CodecStage $stage $false
    Assert-CodecSnapshot $Source $Snapshot
    $stage
    } catch {
        $_.Exception.Data['CodecStageDirectory'] = $directory
        throw
    }
}

function Assert-CodecStage($Stage, [bool]$Imported) {
    Assert-CodecIsolation $Stage.Source $Stage.Parent $Stage.Directory
    $paths = @($Stage.Inputs.Path)
    if (@(Compare-Object -CaseSensitive $paths @('project.godot', 'persistence/save_file_codec.gd', 'tests/save_file_codec_test.gd')).Count) { throw 'Unexpected staged input inventory.' }
    foreach ($input in $Stage.Inputs) {
        $path = Join-Path $Stage.Directory $input.Path
        Assert-PlainPath $path
        if (-not (Test-Path -LiteralPath $path -PathType Leaf) -or (Get-FileHash -LiteralPath $path).Hash -cne $input.Sha256) { throw 'Staged input hash changed or file missing.' }
    }
    $generated = @()
    $queue = [Collections.Generic.Queue[string]]::new()
    $queue.Enqueue($Stage.Directory)
    while ($queue.Count) {
        foreach ($item in Get-ChildItem -Force -LiteralPath $queue.Dequeue()) {
            Assert-PlainPath $item.FullName # Check before entering a directory.
            $relative = [IO.Path]::GetRelativePath($Stage.Directory, $item.FullName).Replace('\', '/')
            if ($Imported -and ($relative -ceq '.godot' -or $relative.StartsWith('.godot/', [StringComparison]::Ordinal) -or
                $relative -ceq '.codec-profile' -or $relative.StartsWith('.codec-profile/', [StringComparison]::Ordinal))) {
                if ($item.PSIsContainer) { $queue.Enqueue($item.FullName) }
                continue
            }
            if ($Imported -and $relative -cin @('persistence/save_file_codec.gd.uid', 'tests/save_file_codec_test.gd.uid')) {
                if ($item.PSIsContainer -or $item.Length -gt 128 -or [IO.File]::ReadAllText($item.FullName) -cnotmatch '\Auid://[a-z0-9]{1,13}\r?\n?\z') { throw 'Invalid generated script UID.' }
                $generated += [pscustomobject]@{ Path = $relative; Sha256 = (Get-FileHash -LiteralPath $item.FullName).Hash }
                continue
            }
            if ($item.PSIsContainer) {
                if ($relative -cnotin @('persistence', 'tests')) { throw 'Unexpected staged directory.' }
                $queue.Enqueue($item.FullName)
            } elseif ($relative -cnotin $paths) { throw 'Unexpected staged file.' }
        }
    }
    $generated = @($generated | Sort-Object Path)
    if ($Stage.GeneratedCaptured -and ($generated | ConvertTo-Json -Compress) -cne ($Stage.Generated | ConvertTo-Json -Compress)) { throw 'Generated UID identity changed.' }
    if ($Imported) { $Stage.Generated = $generated; $Stage.GeneratedCaptured = $true }
}

function Get-CodecOutcome([ValidateSet('Static', 'Import', 'Codec')][string]$Phase, $Result) {
    $reason = 'OK'
    $output = $Result.Stdout + "`n" + $Result.Stderr
    if ($Result.Status -cne 'PASS') { $reason = $Result.Status }
    elseif (-not $Result.TerminationCertain) { $reason = 'UNCERTAIN_TERMINATION' }
    elseif ($Result.Bytes -lt 0 -or $Result.Bytes -gt 1048576 -or [Text.Encoding]::UTF8.GetByteCount($Result.Stdout + $Result.Stderr) -gt 1048576) { $reason = 'OUTPUT_LIMIT' }
    elseif ($Result.ExitCode -cne 0) { $reason = 'ABNORMAL_EXIT' }
    elseif ($output -match '(?im)\b(ERROR|SCRIPT ERROR|parse error|assertion fail(?:ed|ure)|crash|fatal)\b') { $reason = 'ENGINE_OR_PROCESS_ERROR' }
    elseif ($Phase -ceq 'Codec') {
        $records = @([regex]::Matches($output, 'SAVE_FILE_CODEC[^\r\n]*'))
        $last = @($Result.Stdout.TrimEnd().Split("`n"))[-1].TrimEnd("`r")
        if ($records.Count -ne 1 -or $records[0].Value -cnotmatch '\ASAVE_FILE_CODEC: PASS checks=[1-9][0-9]* failures=0\z' -or
            $last -cne $records[0].Value) { $reason = 'MISSING_OR_MALFORMED_COMPLETION' }
    }
    [pscustomobject]@{ Status = $(if ($reason -ceq 'OK') { 'PASS' } else { 'FAIL' }); Reason = $reason;
        Diagnostic = (Get-CodecDiagnostic $output) }
}

function Invoke-CodecStatic([string]$Source) {
    # Existing Native runner's 60-second static bound is deliberately unchanged.
    $pwsh = Join-Path $PSHOME 'pwsh.exe'
    $fixture = Invoke-BoundedProcess $pwsh @('-NoProfile', '-File', 'tests/save_codec_runner_fixture_test.ps1') $Source -Seconds 60
    $outcome = Get-CodecOutcome Static $fixture
    if ($outcome.Status -cne 'PASS' -or $fixture.Stdout -notmatch '(?m)^Codec runner fixtures: [1-9][0-9]* PASS, 0 FAIL\.\r?$') { throw 'Inert codec runner fixtures failed.' }
    $python = @(Get-Command python -CommandType Application -ErrorAction Stop)[0].Source
    $result = Invoke-BoundedProcess $python @('-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'static_*test.py') $Source -Seconds 600
    $outcome = Get-CodecOutcome Static $result
    Write-Host $result.Stdout.Trim()
    Write-Host $result.Stderr.Trim()
    if ($outcome.Status -cne 'PASS' -or $result.Stderr -notmatch '(?m)^Ran [1-9][0-9]* tests? in ' -or $result.Stderr -notmatch '(?m)^OK(?: \(skipped=[0-9]+\))?\r?$') { throw 'Actual Python static suite did not PASS.' }
}

function Invoke-CodecEnginePhase([ValidateSet('Import', 'Codec')][string]$Phase, $Stage, $Snapshot) {
    Assert-CodecAuthorization
    $source = Split-Path $PSScriptRoot -Parent
    if ($Stage.Parent -cne 'D:\GameDev\Godot\TLWH-NativeStages' -or $Stage.Source -cne $source) { throw 'Fixed codec source/stage parent required.' }
    Assert-CodecSnapshot $source $Snapshot
    Assert-CodecStage $Stage ($Phase -ceq 'Codec')
    $command = @(Get-CodecCommandPlan $source $Stage.Directory) | Where-Object Phase -CEQ $Phase
    # Fixed process-local profile paths protect the owner's Godot editor settings,
    # caches, user:// data and temp files. Never read these paths from environment.
    $previous = @{}
    $profilePaths = [ordered]@{ APPDATA = '.codec-profile/appdata'; LOCALAPPDATA = '.codec-profile/localappdata';
        TEMP = '.codec-profile/temp'; TMP = '.codec-profile/temp' }
    try {
        foreach ($name in $profilePaths.Keys) {
            $previous[$name] = [Environment]::GetEnvironmentVariable($name, 'Process')
            $path = Join-Path $Stage.Directory $profilePaths[$name]
            Assert-PlainPath $path
            $null = [IO.Directory]::CreateDirectory($path)
            [Environment]::SetEnvironmentVariable($name, $path, 'Process')
        }
        Assert-PinnedEngine $command.Executable $command.Sha256 # Immediately before each launch.
        Invoke-BoundedProcess $command.Executable $command.Arguments $command.Directory -Seconds $command.Seconds -MaxBytes 1048576 -ExcerptBytes 4096
    } finally {
        foreach ($name in $previous.Keys) { [Environment]::SetEnvironmentVariable($name, $previous[$name], 'Process') }
    }
}

function Save-CodecFailure([string]$Source, $Summary) {
    $directory = Join-Path $Source 'artifacts/logs'
    Assert-PlainPath $directory
    $path = Join-Path $directory ('codec-failure-' + [Guid]::NewGuid().ToString('N') + '.json')
    $null = Invoke-CodecGit $Source @('check-ignore', '--quiet', '--', $path)
    # Bounded provenance only: no complete status/index, file bodies or unbounded output.
    $record = [ordered]@{ Revision = $Summary.Revision; Stage = $Summary.Stage; Commands = $Summary.Commands;
        Static = $Summary.Static; Import = $Summary.Import; Codec = $Summary.Codec; Reason = $Summary.Reason;
        Diagnostic = (Get-CodecDiagnostic $Summary.Diagnostic); IdentitySha256 = $Summary.IdentitySha256 }
    $bytes = [Text.Encoding]::UTF8.GetBytes(($record | ConvertTo-Json -Depth 8))
    if ($bytes.Length -gt 65536) { throw 'Codec failure evidence exceeds 64 KiB.' }
    $null = [IO.Directory]::CreateDirectory($directory)
    Assert-PlainPath $directory
    $stream = [IO.File]::Open($path, [IO.FileMode]::CreateNew, [IO.FileAccess]::Write, [IO.FileShare]::None)
    try { $stream.Write($bytes, 0, $bytes.Length) } finally { $stream.Dispose() }
    $path
}

function Assert-CodecEvidenceDestination([string]$Source) {
    $directory = Join-Path $Source 'artifacts/logs'
    Assert-PlainPath $directory
    $null = Invoke-CodecGit $Source @('check-ignore', '--quiet', '--', (Join-Path $directory 'codec-failure-policy-check.json'))
}

function Invoke-CodecAuthorizedRun {
    Assert-CodecAuthorization # No snapshot, process or stage before this gate.
    $source = Split-Path $PSScriptRoot -Parent
    $summary = [ordered]@{ Static = 'NOT RUN'; Import = 'NOT RUN'; Codec = 'NOT RUN'; Reason = ''; Revision = '';
        Stage = ''; Commands = @(); Diagnostic = ''; IdentitySha256 = ''; Evidence = ''; EvidenceError = '' }
    try {
        if (-not $IsWindows) { throw 'Codec execution requires Windows PowerShell 7.' }
        $snapshot = Get-CodecSnapshot $source
        $summary.Revision = $snapshot.Identity.Revision
        $summary.IdentitySha256 = Get-CodecHash ([Text.Encoding]::UTF8.GetBytes(($snapshot | ConvertTo-Json -Depth 8 -Compress)))
        $pinned = Get-StandardGodotIdentity
        Assert-PinnedEngine $pinned.Path $pinned.Sha256
        $summary.Static = 'FAIL'
        Invoke-CodecStatic $source
        $summary.Static = 'PASS'
        Assert-CodecSnapshot $source $snapshot
        Assert-CodecEvidenceDestination $source
        $stage = New-CodecStage $source $snapshot
        $summary.Stage = $stage.Directory
        foreach ($command in @(Get-CodecCommandPlan $source $stage.Directory)) {
            $summary[$command.Phase] = 'FAIL'
            $summary.Commands += $command
            $result = Invoke-CodecEnginePhase $command.Phase $stage $snapshot
            $outcome = Get-CodecOutcome $command.Phase $result
            $summary.Reason = $outcome.Reason; $summary.Diagnostic = $outcome.Diagnostic
            if ($outcome.Status -cne 'PASS') { throw 'Codec engine phase failed; no retry.' }
            Assert-CodecSnapshot $source $snapshot
            Assert-CodecStage $stage $true
            Assert-PinnedEngine $pinned.Path $pinned.Sha256
            $summary[$command.Phase] = 'PASS'
        }
    } catch {
        if (-not $summary.Stage -and $_.Exception.Data.Contains('CodecStageDirectory')) { $summary.Stage = [string]$_.Exception.Data['CodecStageDirectory'] }
        if (-not $summary.Reason -or $summary.Reason -ceq 'OK') { $summary.Reason = 'PREFLIGHT_OR_IDENTITY_FAILURE' }
        if (-not $summary.Diagnostic) {
            $summary.Diagnostic = Get-CodecDiagnostic ([string]$_)
        }
        try { $summary.Evidence = Save-CodecFailure $source $summary } catch { $summary.EvidenceError = 'Bounded failure evidence could not be saved.' }
    }
    $summary
}

function Invoke-SaveCodecTests([ValidateSet('Static', 'Run')][string]$RequestedMode) {
    try {
        if ($RequestedMode -ieq 'Run') {
            Assert-CodecAuthorization
            $summary = Invoke-CodecAuthorizedRun
            Write-Host ($summary | ConvertTo-Json -Depth 8)
            if ($summary.Codec -cne 'PASS' -or $summary.EvidenceError) { return 1 }
        } else {
            Invoke-CodecStatic (Split-Path $PSScriptRoot -Parent)
            Write-Host 'Static: PASS. Godot import/runtime: NOT RUN — OWNER AUTHORIZATION REQUIRED.'
        }
        return 0
    } catch { Write-Host ([string]$_); return 1 }
}

if ($MyInvocation.InvocationName -ne '.') { exit (Invoke-SaveCodecTests $codecInvocationMode) }
