#requires -Version 7.0
# Inert fixtures only. Never activate the source gate or invoke an engine.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../tools/run-save-codec-tests.ps1"
$passed = 0; $failed = 0
function Check([string]$Name, [scriptblock]$Body) {
    try { & $Body; $script:passed++; Write-Host "PASS $Name" }
    catch { $script:failed++; Write-Host "FAIL ${Name}: $_" }
}
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Reject([scriptblock]$Body, [string]$Pattern) {
    try { & $Body } catch { if ($_ -notmatch $Pattern) { throw "Unexpected rejection: $_" }; return }
    throw 'Expected rejection did not occur.'
}
function Result([string]$Stdout = '', [string]$Stderr = '', [string]$Status = 'PASS', $ExitCode = 0, [bool]$Certain = $true) {
    [pscustomobject]@{ Stdout = $Stdout; Stderr = $Stderr; Status = $Status; ExitCode = $ExitCode;
        TerminationCertain = $Certain; Bytes = [Text.Encoding]::UTF8.GetByteCount($Stdout + $Stderr) }
}
$repository = Split-Path $PSScriptRoot -Parent
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('tlwh-codec-fixture-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $fixture
$source = Join-Path $fixture 'source'
$parent = Join-Path $fixture 'stages'
$directory = Join-Path $parent ('tlwh-codec-' + [Guid]::NewGuid().ToString('N'))
foreach ($path in @($source, $parent, $directory)) { $null = New-Item -ItemType Directory -Path $path }
$inputs = @(Get-CodecInputs)
foreach ($input in $inputs) {
    $path = Join-Path $source $input.Source
    $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($path))
    [IO.File]::WriteAllBytes($path, [IO.File]::ReadAllBytes((Join-Path $repository $input.Source)))
    $target = Join-Path $directory $input.Path
    $null = [IO.Directory]::CreateDirectory([IO.Path]::GetDirectoryName($target))
    [IO.File]::WriteAllBytes($target, (Get-CodecSourceBytes $path).Bytes)
}
$stage = [pscustomobject]@{ Source = $source; Parent = $parent; Directory = $directory; Generated = @(); GeneratedCaptured = $false;
    Inputs = @($inputs | ForEach-Object { [pscustomobject]@{ Path = $_.Path; Sha256 = $_.Sha256 } }) }
$good = 'SAVE_FILE_CODEC: PASS checks=250 failures=0'

# Named, scoped doubles exercise future sequence control without opening its
# production gate. Any missed process interception throws, never dispatches.
function Invoke-CodecSequenceFixture([object[]]$Results, [string]$Mutation = '') {
    $calls = [Collections.Generic.List[string]]::new()
    $events = [Collections.Generic.List[string]]::new()
    function Assert-CodecAuthorization { $events.Add('gate-double') }
    function Invoke-BoundedProcess { throw 'Unexpected process in inert sequence' }
    function Get-CodecSnapshot { [pscustomobject]@{ Identity = [pscustomobject]@{ Revision = ('a' * 40) }; Inputs = @() } }
    function Assert-CodecSnapshot {
        $events.Add('source-check')
        if ($Mutation -eq 'identity' -and $calls.Count -gt 0) { throw 'Synthetic changed identity' }
    }
    function Assert-PinnedEngine { $events.Add('engine-hash-check') }
    function Invoke-CodecStatic { $events.Add('static-double'); if ($Mutation -eq 'static') { throw 'Synthetic static timeout' } }
    function Assert-CodecEvidenceDestination { $events.Add('ignored-evidence-check') }
    function New-CodecStage { $events.Add('stage-double'); [pscustomobject]@{ Directory = $directory } }
    function Get-CodecCommandPlan {
        [pscustomobject]@{ Phase = 'Import'; Executable = 'INERT'; Arguments = @(); Directory = $directory; Seconds = 60; MaxBytes = 1048576 }
        [pscustomobject]@{ Phase = 'Codec'; Executable = 'INERT'; Arguments = @(); Directory = $directory; Seconds = 30; MaxBytes = 1048576 }
    }
    function Invoke-CodecEnginePhase($Phase) { $calls.Add($Phase); $Results[$calls.Count - 1] }
    function Assert-CodecStage { $events.Add('stage-check') }
    function Save-CodecFailure { $events.Add('evidence-double'); 'inert-evidence' }
    $summary = Invoke-CodecAuthorizedRun
    [pscustomobject]@{ Summary = $summary; Calls = $calls; Events = $events }
}

try {
    Check 'PowerShell runner and fixture syntax parses without execution' {
        foreach ($path in @("$repository/tools/run-save-codec-tests.ps1", $PSCommandPath)) {
            $tokens = $null; $parseErrors = $null
            $null = [Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$parseErrors)
            Require ($parseErrors.Count -eq 0) 'PowerShell parse failure'
        }
    }
    Check 'public denial occurs before every process and staging helper' {
        $calls = [Collections.Generic.List[string]]::new()
        function Invoke-BoundedProcess { $calls.Add('process'); throw 'Unexpected process' }
        function Invoke-CodecAuthorizedRun { $calls.Add('dispatch'); throw 'Unexpected dispatch' }
        function New-CodecStage { $calls.Add('stage'); throw 'Unexpected stage' }
        foreach ($modeName in @('Run', 'run', 'RUN')) {
            Require ((Invoke-SaveCodecTests $modeName) -eq 1) 'Inactive gate returned success'
        }
        Require ($calls.Count -eq 0) 'Denied invocation reached a side effect'
    }
    Check 'direct dispatch, stage and engine helpers also deny first' {
        $calls = [Collections.Generic.List[string]]::new()
        function Get-CodecSnapshot { $calls.Add('snapshot'); throw 'Unexpected snapshot' }
        function Invoke-BoundedProcess { $calls.Add('process'); throw 'Unexpected process' }
        Reject { Invoke-CodecAuthorizedRun } 'AUTHORIZATION_DENIED'
        Reject { New-CodecStage $source $null } 'AUTHORIZATION_DENIED'
        Reject { Invoke-CodecEnginePhase Import $null $null } 'AUTHORIZATION_DENIED'
        Require ($calls.Count -eq 0) 'Direct helper bypassed gate'
    }
    Check 'real default and Run invocations deny without real stage creation' {
        $nativeParent = 'D:\GameDev\Godot\TLWH-NativeStages'
        $before = if (Test-Path -LiteralPath $nativeParent) { @(Get-ChildItem -Force -LiteralPath $nativeParent | Select-Object -ExpandProperty Name) } else { @() }
        foreach ($arguments in @(@('-NoProfile', '-File', 'tools/run-save-codec-tests.ps1'),
            @('-NoProfile', '-File', 'tools/run-save-codec-tests.ps1', '-Mode', 'Run'))) {
            # Harmless PowerShell child; the production gate stays unchanged.
            $result = Invoke-BoundedProcess (Join-Path $PSHOME 'pwsh.exe') $arguments $repository -Seconds 10
            Require ($result.ExitCode -eq 1 -and $result.TerminationCertain -and $result.Stdout -match 'AUTHORIZATION_DENIED') 'Real denied entry point failed'
        }
        $after = if (Test-Path -LiteralPath $nativeParent) { @(Get-ChildItem -Force -LiteralPath $nativeParent | Select-Object -ExpandProperty Name) } else { @() }
        Require (-not @(Compare-Object $before $after).Count) 'Denied entry created external stage'
    }
    Check 'fixed plan has exact executable, arguments, deadlines and output caps' {
        $planned = 'D:\GameDev\Godot\TLWH-NativeStages\tlwh-codec-' + ('a' * 32)
        $plan = @(Get-CodecCommandPlan $repository $planned)
        Require ($plan.Count -eq 2) 'Unexpected command count'
        Require (($plan[0].Arguments -join '|') -ceq "--headless|--editor|--path|$planned|--quit") 'Import arguments changed'
        Require (($plan[1].Arguments -join '|') -ceq "--headless|--path|$planned|--script|res://tests/save_file_codec_test.gd") 'Codec arguments changed'
        Require ($plan[0].Seconds -eq 60 -and $plan[1].Seconds -eq 30) 'Engine deadlines changed'
        foreach ($command in $plan) {
            Require ($command.Executable -ceq 'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe' -and $command.MaxBytes -eq 1048576) 'Identity or output cap changed'
            Require ($command.Sha256 -ceq 'AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424') 'Hash changed'
        }
        Reject { Get-CodecCommandPlan $repository $directory } 'overlap|unsafe'
    }
    Check 'fixed child profile environment isolated and restored on failure without an engine' {
        $before = @{}
        foreach ($name in @('APPDATA', 'LOCALAPPDATA', 'TEMP', 'TMP')) { $before[$name] = [Environment]::GetEnvironmentVariable($name, 'Process') }
        $seen = [Collections.Generic.List[string]]::new()
        function Assert-CodecAuthorization { }
        function Assert-CodecSnapshot { }
        function Assert-CodecStage { }
        function Assert-PinnedEngine { }
        function Get-CodecCommandPlan {
            [pscustomobject]@{ Phase = 'Import'; Executable = 'INERT-NEVER-LAUNCHED'; Sha256 = 'INERT'; Arguments = @(); Directory = $directory; Seconds = 60 }
        }
        function Invoke-BoundedProcess {
            foreach ($name in $before.Keys) {
                Require ([Environment]::GetEnvironmentVariable($name, 'Process').StartsWith($directory + '\', [StringComparison]::OrdinalIgnoreCase)) 'Profile environment escaped owned fixture'
                $seen.Add($name)
            }
            throw 'Synthetic process failure'
        }
        $inertStage = [pscustomobject]@{ Source = $repository; Parent = 'D:\GameDev\Godot\TLWH-NativeStages'; Directory = $directory }
        Reject { Invoke-CodecEnginePhase Import $inertStage $null } 'Synthetic process failure'
        Require ($seen.Count -eq 4) 'Profile environment not observed'
        foreach ($name in $before.Keys) { Require ([Environment]::GetEnvironmentVariable($name, 'Process') -ceq $before[$name]) 'Original process environment not restored' }
        $profile = Join-Path $directory '.codec-profile'
        $profileFullPath = [IO.Path]::GetFullPath($profile)
        Require ($profileFullPath -ceq ([IO.Path]::GetFullPath($directory).TrimEnd('\') + '\.codec-profile')) 'Unsafe owned profile cleanup'
        Assert-PlainPath $profileFullPath
        Remove-Item -LiteralPath $profileFullPath -Recurse -Force
    }
    Check 'source parent overlap, ancestor overlap and traversal rejected' {
        Assert-CodecIsolation $source $parent $directory
        Reject { Assert-CodecIsolation $source $source (Join-Path $source ('tlwh-codec-' + ('a' * 32))) } 'overlap'
        Reject { Assert-CodecIsolation $source $fixture (Join-Path $fixture ('tlwh-codec-' + ('a' * 32))) } 'overlap'
        Reject { Assert-CodecIsolation $source $parent (Join-Path $parent '../outside') } 'overlap|unsafe'
        Reject { Assert-CodecIsolation '.' $parent $directory } 'Absolute'
    }
    Check 'exact staged inventory and hashes accepted' { Assert-CodecStage $stage $false }
    Check 'unexpected staged files and directories rejected' {
        foreach ($relative in @('extra.txt', 'tests/extra.gd', 'owner-save.sav')) {
            $path = Join-Path $directory $relative
            [IO.File]::WriteAllText($path, 'inert')
            try { Reject { Assert-CodecStage $stage $false } 'Unexpected staged' } finally { Remove-Item -LiteralPath $path }
        }
        $path = Join-Path $directory 'assets'
        $null = New-Item -ItemType Directory -Path $path
        try { Reject { Assert-CodecStage $stage $false } 'Unexpected staged' } finally { Remove-Item -LiteralPath $path }
    }
    Check 'changed staged input hash rejected' {
        $path = Join-Path $directory 'project.godot'
        $bytes = [IO.File]::ReadAllBytes($path)
        [IO.File]::WriteAllText($path, 'changed inert input')
        try { Reject { Assert-CodecStage $stage $false } 'hash changed' } finally { [IO.File]::WriteAllBytes($path, $bytes) }
    }
    Check 'reparse point rejected before traversal using inert metadata double' {
        $target = Join-Path $directory 'persistence'
        $observed = [Collections.Generic.List[string]]::new()
        function Get-Item {
            param([switch]$Force, [string]$LiteralPath)
            if ($LiteralPath.Equals($target, [StringComparison]::OrdinalIgnoreCase)) {
                $observed.Add($LiteralPath)
                [pscustomobject]@{ Attributes = [IO.FileAttributes]::ReparsePoint }
            } else { Microsoft.PowerShell.Management\Get-Item -Force:$Force -LiteralPath $LiteralPath }
        }
        Reject { Assert-CodecStage $stage $false } 'Reparse point'
        Require ($observed.Count -gt 0) 'Reparse metadata double was not encountered'
    }
    Check 'generated cache and exact UID outputs allowed only after import and frozen' {
        $path = Join-Path $directory 'tests/save_file_codec_test.gd.uid'
        [IO.File]::WriteAllText($path, "uid://b12345`n")
        try {
            Reject { Assert-CodecStage $stage $false } 'Unexpected staged'
            Assert-CodecStage $stage $true
            [IO.File]::WriteAllText($path, "uid://b12346`n")
            Reject { Assert-CodecStage $stage $true } 'UID identity changed'
        } finally { Remove-Item -LiteralPath $path; $stage.Generated = @(); $stage.GeneratedCaptured = $false }
        Assert-CodecStage $stage $true
        [IO.File]::WriteAllText($path, "uid://b12345`n")
        try { Reject { Assert-CodecStage $stage $true } 'UID identity changed' }
        finally { Remove-Item -LiteralPath $path; $stage.GeneratedCaptured = $false }
        $cache = Join-Path $directory '.godot'
        $null = New-Item -ItemType Directory -Path $cache
        try {
            Reject { Assert-CodecStage $stage $false } 'Unexpected staged'
            Assert-CodecStage $stage $true
        } finally { Remove-Item -LiteralPath $cache; $stage.GeneratedCaptured = $false }
    }
    Check 'reviewed canonical source hashes and raw identity changes enforced' {
        function Get-NativeSourceIdentity {
            [pscustomobject]@{ Revision = ('a' * 40); Working = 'inert stable status'; Index = 'inert index';
                Tracked = @($inputs.Source) + @('tools/run-save-codec-tests.ps1', 'tests/save_codec_runner_fixture_test.ps1', 'tests/static_save_codec_runner_test.py', 'docs/SAVE_CODEC_RUNNER.md') }
        }
        function Invoke-CodecGit($Source, $Arguments) { if ($Arguments[0] -eq 'remote') { 'https://github.com/interneth3ro/the-long-way-home.git' } else { '' } }
        $snapshot = Get-CodecSnapshot $source
        Assert-CodecSnapshot $source $snapshot
        $unreviewed = Join-Path $source 'tests/static_unreviewed_test.py'
        [IO.File]::WriteAllText($unreviewed, '# inert; never executed')
        try { Reject { Get-CodecSnapshot $source } 'Untracked static test' } finally { Remove-Item -LiteralPath $unreviewed }
        $path = Join-Path $source 'persistence/save_file_codec.gd'
        $bytes = [IO.File]::ReadAllBytes($path)
        try {
            [IO.File]::WriteAllText($path, 'changed inert source')
            Reject { Get-CodecSnapshot $source } 'input hash changed'
            [IO.File]::WriteAllText($path, [Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n", "`n").Replace("`n", "`r`n"))
            Reject { Assert-CodecSnapshot $source $snapshot } 'changed since static'
        } finally { [IO.File]::WriteAllBytes($path, $bytes) }
    }
    Check 'valid synthetic completion accepted' { Require ((Get-CodecOutcome Codec (Result ($good + "`n"))).Status -ceq 'PASS') 'Valid completion rejected' }
    foreach ($text in @('', 'SAVE_FILE_CODEC: FAIL checks=250 failures=1', 'SAVE_FILE_CODEC: PASS checks=0 failures=0',
        'SAVE_FILE_CODEC: PASS checks=1 failures=1', 'SAVE_FILE_CODEC: PASS checks=x failures=0',
        ($good + "`n" + $good), ($good + "`nSAVE_FILE_CODEC: FAIL checks=1 failures=1"), ($good + "`ntrailing"), ('prefix ' + $good))) {
        $record = $text
        Check 'missing malformed duplicated contradictory or misplaced completion rejected' {
            Require ((Get-CodecOutcome Codec (Result $record)).Status -ceq 'FAIL') 'Bad completion accepted'
        }
    }
    Check 'completion on stderr or duplicated across streams rejected' {
        Require ((Get-CodecOutcome Codec (Result '' $good)).Status -ceq 'FAIL') 'Stderr completion accepted'
        Require ((Get-CodecOutcome Codec (Result $good $good)).Status -ceq 'FAIL') 'Cross-stream duplicate accepted'
    }
    foreach ($item in @((Result $good '' PASS 1), (Result $good '' TIMEOUT), (Result $good '' OUTPUT_LIMIT),
        (Result $good '' PASS 0 $false), (Result $good 'ERROR: inert'), (Result $good 'SCRIPT ERROR: inert'),
        (Result $good 'parse error'), (Result $good 'assertion failed'), (Result $good 'fatal crash'))) {
        $bad = $item
        Check 'nonzero timeout overflow uncertain termination and engine diagnostics fail' {
            Require ((Get-CodecOutcome Codec $bad).Status -ceq 'FAIL') 'Failure accepted'
            $sequence = Invoke-CodecSequenceFixture @($bad, (Result $good))
            Require ($sequence.Calls.Count -eq 1 -and $sequence.Summary.Codec -ceq 'NOT RUN') 'Import failure retried or continued'
        }
    }
    Check 'reported and actual excessive output fail with bounded diagnostics' {
        $bad = Result $good
        $bad.Bytes = 1048577
        Require ((Get-CodecOutcome Codec $bad).Status -ceq 'FAIL') 'Reported overflow accepted'
        $bad = Result ('x' * 1048577)
        $outcome = Get-CodecOutcome Codec $bad
        Require ($outcome.Status -ceq 'FAIL' -and [Text.Encoding]::UTF8.GetByteCount($outcome.Diagnostic) -le 4096) 'Output or diagnostic bound failed'
        $diagnostic = Get-CodecDiagnostic ('界' * 2000)
        Require ([Text.Encoding]::UTF8.GetByteCount($diagnostic) -le 4096 -and -not $diagnostic.Contains([char]0xfffd)) 'UTF-8 excerpt split a codepoint'
    }
    Check 'bounded unique ignored failure evidence preserves other files' {
        $seen = [Collections.Generic.List[string]]::new()
        function Invoke-CodecGit($Source, $Arguments) {
            Require ($Arguments[0] -ceq 'check-ignore') 'Unexpected evidence Git command'
            $seen.Add($Arguments[-1]); ''
        }
        $record = [pscustomobject]@{ Revision = ('a' * 40); Stage = 'inert'; Commands = @(); Static = 'PASS';
            Import = 'FAIL'; Codec = 'NOT RUN'; Reason = 'INERT_FAILURE'; Diagnostic = ('界' * 10000); IdentitySha256 = ('a' * 64) }
        $first = Save-CodecFailure $source $record
        $second = Save-CodecFailure $source $record
        Require ($first -cne $second -and $seen.Count -eq 2) 'Evidence name reused or ignore check skipped'
        $saved = [IO.File]::ReadAllText($first) | ConvertFrom-Json
        Require ((Get-Item -LiteralPath $first).Length -le 65536 -and [Text.Encoding]::UTF8.GetByteCount($saved.Diagnostic) -le 4096) 'Evidence limits failed'
        $before = (Get-FileHash -LiteralPath $first).Hash
        $record.Commands = @('x' * 70000)
        Reject { Save-CodecFailure $source $record } 'exceeds 64 KiB'
        Require ((Get-FileHash -LiteralPath $first).Hash -ceq $before) 'Prior evidence overwritten'
        function Invoke-CodecGit { throw 'Synthetic ignore rejection' }
        Reject { Save-CodecFailure $source $record } 'ignore rejection'
    }
    Check 'sequence is sequential with exactly two attempts and no retry' {
        $result = Invoke-CodecSequenceFixture @((Result), (Result $good))
        Require (($result.Calls -join '|') -ceq 'Import|Codec' -and $result.Summary.Codec -ceq 'PASS') 'Sequence failed'
        $result = Invoke-CodecSequenceFixture @((Result), (Result '' '' PASS 1))
        Require ($result.Calls.Count -eq 2 -and $result.Summary.Codec -ceq 'FAIL') 'Test failure retried'
        $result = Invoke-CodecSequenceFixture @((Result), (Result $good)) static
        Require ($result.Calls.Count -eq 0 -and $result.Events -notcontains 'stage-double') 'Static failure allowed stage'
        $result = Invoke-CodecSequenceFixture @((Result), (Result $good)) identity
        Require ($result.Calls.Count -eq 1 -and $result.Summary.Import -ceq 'FAIL') 'Changed identity allowed next phase'
    }
    Check 'common bounded process helper tested only with harmless PowerShell child' {
        $pwsh = Join-Path $PSHOME 'pwsh.exe'
        $result = Invoke-BoundedProcess $pwsh @('-NoProfile', '-Command', '[Console]::Write("inert")') $fixture -Seconds 10
        Require ($result.Status -ceq 'PASS' -and $result.TerminationCertain -and $result.Stdout -ceq 'inert') 'Harmless process did not complete'
    }
    Check 'production authorization gate remains inactive after scoped doubles' {
        Reject { Assert-CodecAuthorization } 'AUTHORIZATION_DENIED'
    }
} finally {
    # This exact fresh fixture is the only recursive removal target. No real stage.
    $resolved = [IO.Path]::GetFullPath($fixture)
    $expectedParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
    if ([IO.Path]::GetDirectoryName($resolved) -ne $expectedParent -or [IO.Path]::GetFileName($resolved) -cnotmatch '^tlwh-codec-fixture-[0-9a-f]{32}$') { throw 'Unsafe fixture cleanup target' }
    Assert-PlainPath $resolved
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
Write-Host "Codec runner fixtures: $passed PASS, $failed FAIL."
Write-Host 'Godot import/runtime: NOT RUN — OWNER AUTHORIZATION REQUIRED.'
if ($failed) { exit 1 }
