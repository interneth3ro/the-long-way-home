#requires -Version 7.0
# Inert fixtures only. Never activate the source gate or invoke an engine.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../tools/run-save-codec-tests.ps1"
# Future activated-source validation is permitted only inside/already after the
# consumed attempt. Never let an inert default-entry probe claim a real grant.
if ((Get-CodecGrantTransition) -cne 'PREPARED') {
    $consumedPath = Get-CodecConsumptionPath (Get-CodecGrantedRevision)
    Assert-PlainPath $consumedPath
    if (-not (Test-Path -LiteralPath $consumedPath)) { throw 'Inert fixtures refuse an unconsumed activated source; restore PREPARED before standalone review tests.' }
}
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
    function Complete-CodecAuthorizationPhase { $events.Add('phase-authorization-double') }
    function Save-CodecFailure { $events.Add('evidence-double'); 'inert-evidence' }
    $summary = Invoke-CodecAuthorizedRun
    [pscustomobject]@{ Summary = $summary; Calls = $calls; Events = $events }
}

# Synthetic grant data and temp-only tombstones; never activate tracked source,
# write a real grant record, or call the activated production Run entry point.
function Invoke-CodecGrantFixture([scriptblock]$Body) {
    $grantDirectory = Join-Path $fixture ('grant-' + [Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $grantDirectory
    $receipt = Join-Path $grantDirectory 'synthetic-consumed.json'
    $model = @{ Reviewed = ('b' * 40); Activation = ('c' * 40); Identity = ('d' * 64); State = 'AUTHORIZED_ONCE:' + ('b' * 40) }
    function Get-CodecGrantTransition { $model.State }
    function Get-CodecConsumptionPath { $receipt }
    function Get-CodecGrantBinding {
        [pscustomobject]@{ ReviewedRevision = $model.Reviewed; ActivationRevision = $model.Activation; IdentitySha256 = $model.Identity }
    }
    function Invoke-BoundedProcess { throw 'Unexpected process in synthetic grant fixture' }
    function New-CodecStage { throw 'Unexpected stage in synthetic grant fixture' }
    function Invoke-CodecEnginePhase { throw 'Unexpected engine in synthetic grant fixture' }
    try { & $Body $receipt $model } finally { Close-CodecInvocation }
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
        function Get-CodecGrantTransition { 'PREPARED' }
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
        function Get-CodecGrantTransition { 'PREPARED' }
        $calls = [Collections.Generic.List[string]]::new()
        function Get-CodecSnapshot { $calls.Add('snapshot'); throw 'Unexpected snapshot' }
        function Invoke-BoundedProcess { $calls.Add('process'); throw 'Unexpected process' }
        Reject { Start-CodecInvocation } 'AUTHORIZATION_DENIED'
        Reject { Invoke-CodecAuthorizedRun } 'AUTHORIZATION_DENIED'
        Reject { New-CodecStage $source $null } 'AUTHORIZATION_DENIED'
        Reject { Invoke-CodecEnginePhase Import $null $null } 'AUTHORIZATION_DENIED'
        Require ($calls.Count -eq 0) 'Direct helper bypassed gate'
    }
    Check 'real default and Run invocations deny without real stage creation' {
        if ((Get-CodecGrantTransition) -cne 'PREPARED') {
            Write-Host 'Prepared-only real CLI denial probes are not invoked on activated source.'
            return
        }
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
    Check 'command-line grant arguments cannot activate an invocation' {
        $result = Invoke-BoundedProcess (Join-Path $PSHOME 'pwsh.exe') @('-NoProfile', '-File',
            'tools/run-save-codec-tests.ps1', '-Mode', 'Run', '-Grant', ('AUTHORIZED_ONCE:' + ('b' * 40))) $repository -Seconds 10
        Require ($result.ExitCode -ne 0 -and $result.TerminationCertain -and $result.Stderr -match 'parameter') 'CLI grant accepted'
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
    foreach ($initialEnding in @('LF', 'CRLF')) {
        Check "reviewed canonical source hashes and raw identity changes enforced ($initialEnding initial)" {
            $tracked = @($inputs.Source) + @('tools/run-save-codec-tests.ps1', 'tests/save_codec_runner_fixture_test.ps1', 'tests/static_save_codec_runner_test.py', 'docs/SAVE_CODEC_RUNNER.md')
            function Get-NativeSourceIdentity {
                [pscustomobject]@{ Revision = ('a' * 40); Working = 'inert stable status'; Index = 'inert index';
                    Tracked = $tracked }
            }
            function Invoke-CodecGit($Source, $Arguments) { if ($Arguments[0] -eq 'remote') { 'https://github.com/interneth3ro/the-long-way-home.git' } else { '' } }
            # Scoped copies let negative controls change synthetic expectations only.
            $fixtureInputs = @($inputs | ForEach-Object { [pscustomobject]@{ Source = $_.Source; Path = $_.Path; Sha256 = $_.Sha256 } })
            function Get-CodecInputs { $fixtureInputs }
            $codecInput = @($fixtureInputs | Where-Object Source -CEQ 'persistence/save_file_codec.gd')[0]
            $reviewedHash = $codecInput.Sha256
            $path = Join-Path $source 'persistence/save_file_codec.gd'
            $bytes = [IO.File]::ReadAllBytes($path)
            try {
                $lfBytes = [Text.Encoding]::UTF8.GetBytes([Text.Encoding]::UTF8.GetString($bytes).Replace("`r`n", "`n"))
                $crlfBytes = [Text.Encoding]::UTF8.GetBytes([Text.Encoding]::UTF8.GetString($lfBytes).Replace("`n", "`r`n"))
                [byte[]]$initialBytes = if ($initialEnding -ceq 'LF') { $lfBytes } else { $crlfBytes }
                [IO.File]::WriteAllBytes($path, $initialBytes)
                $initial = Get-CodecSourceBytes $path
                Require ($initial.RawHash -ceq (Get-CodecHash $initialBytes)) 'Initial synthetic representation not established'
                Require ((Get-CodecHash $initial.Bytes) -ceq $reviewedHash) 'Initial canonical reviewed hash differs'
                # Capture a known LF baseline regardless of checkout/initial endings.
                [IO.File]::WriteAllBytes($path, $lfBytes)
                $snapshot = Get-CodecSnapshot $source
                Assert-CodecSnapshot $source $snapshot
                $baselineInput = @($snapshot.Inputs | Where-Object Source -CEQ $codecInput.Source)[0]
                Require ($baselineInput.RawHash -ceq (Get-CodecHash $lfBytes)) 'LF raw baseline not established'
                Require ($baselineInput.Sha256 -ceq $reviewedHash) 'LF canonical reviewed hash differs'
                $unreviewed = Join-Path $source 'tests/static_unreviewed_test.py'
                [IO.File]::WriteAllText($unreviewed, '# inert; never executed')
                try { Reject { Get-CodecSnapshot $source } 'Untracked static test' } finally { Remove-Item -LiteralPath $unreviewed }
                [IO.File]::WriteAllText($path, 'changed inert source')
                Reject { Get-CodecSnapshot $source } 'input hash changed'
                [IO.File]::WriteAllBytes($path, $lfBytes)
                foreach ($badHash in @(('0' * 64), $null)) {
                    try {
                        $codecInput.Sha256 = $badHash
                        Reject { Get-CodecSnapshot $source } 'input hash changed'
                    } finally { $codecInput.Sha256 = $reviewedHash }
                }
                $reviewedTracked = $tracked
                try {
                    $tracked = @($tracked | Where-Object { $_ -cne $codecInput.Source })
                    Reject { Get-CodecSnapshot $source } 'Codec source input is not tracked'
                } finally { $tracked = $reviewedTracked }
                [IO.File]::WriteAllBytes($path, $crlfBytes)
                $changed = Get-CodecSourceBytes $path
                Require ($lfBytes.Length -ne $crlfBytes.Length -and $changed.RawHash -cne $baselineInput.RawHash) 'Synthetic raw bytes did not actually change'
                Require ((Get-CodecHash $changed.Bytes) -ceq $reviewedHash) 'CRLF canonical reviewed content changed'
                $freshSnapshot = Get-CodecSnapshot $source
                Require (($freshSnapshot.Identity | ConvertTo-Json -Depth 8 -Compress) -ceq ($snapshot.Identity | ConvertTo-Json -Depth 8 -Compress)) 'Unrelated source identity changed'
                Reject { Assert-CodecSnapshot $source $snapshot } 'changed since static'
                # CRLF itself remains valid; changing raw identity after capture does not.
                Assert-CodecSnapshot $source $freshSnapshot
            } finally { [IO.File]::WriteAllBytes($path, $bytes) }
        }
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
        Require ((Get-CodecGrantTransition) -ceq 'PREPARED' -or (Test-Path -LiteralPath (Get-CodecConsumptionPath (Get-CodecGrantedRevision)))) 'Source is neither prepared nor already consumed'
    }
    Check 'one-line source binding rejects unrelated commits and changes' {
        $reviewed = 'b' * 40; $activation = 'c' * 40
        $prepared = [IO.File]::ReadAllText("$repository/tools/run-save-codec-tests.ps1").Replace("`r`n", "`n")
        $prepared = [regex]::Replace($prepared, "(?m)^    return '(?:PREPARED|AUTHORIZED_ONCE:[0-9a-f]{40})'$", "    return 'PREPARED'")
        # Synthetic text only, not an activated script file or executable entry.
        $active = [regex]::Replace($prepared, "(?m)^    return 'PREPARED'$", "    return 'AUTHORIZED_ONCE:$reviewed'")
        $model = @{ Parents = "$activation $reviewed"; Changed = 'tools/run-save-codec-tests.ps1'; Current = $active }
        function Get-CodecGrantTransition { "AUTHORIZED_ONCE:$reviewed" }
        function Get-CodecSnapshot { [pscustomobject]@{ Identity = [pscustomobject]@{ Revision = $activation }; Inputs = @('inert') } }
        function Get-CodecSourceBytes { [pscustomobject]@{ Bytes = [Text.Encoding]::UTF8.GetBytes($model.Current) } }
        function Invoke-CodecGit($Source, $Arguments) {
            switch ($Arguments[0]) { 'rev-list' { $model.Parents }; 'diff' { $model.Changed }; 'show' { $prepared }; default { throw 'Unexpected binding command' } }
        }
        Require ((Get-CodecGrantBinding $reviewed).ActivationRevision -ceq $activation) 'Exact synthetic binding rejected'
        $model.Parents = "$activation $reviewed $reviewed"
        Reject { Get-CodecGrantBinding $reviewed } 'single direct child'
        $model.Parents = "$activation " + ('e' * 40)
        Reject { Get-CodecGrantBinding $reviewed } 'single direct child'
        $model.Parents = "$activation $reviewed"
        $model.Changed += "`ntests/extra.gd"
        Reject { Get-CodecGrantBinding $reviewed } 'changed more than'
        $model.Changed = 'tools/run-save-codec-tests.ps1'
        $model.Current = $active + "`n# unreviewed alteration"
        Reject { Get-CodecGrantBinding $reviewed } 'beyond one transition line'
    }
    Check 'synthetic consumption is exclusive and survives closing its owner' {
        Invoke-CodecGrantFixture {
            param($receipt, $model)
            Start-CodecInvocation
            Require ((Test-Path -LiteralPath $receipt) -and $script:CodecGrantContext.NextStep -ceq 'Dispatch') 'Consumption not recorded before dispatch'
            Reject { Start-CodecInvocation } 'already owns'
            Close-CodecInvocation
            $saved = [IO.File]::ReadAllText($receipt) | ConvertFrom-Json
            Require ($saved.State -ceq 'CONSUMED' -and $saved.ReviewedRevision -ceq $model.Reviewed) 'Wrong tombstone identity'
            Reject { Start-CodecInvocation } 'already consumed'
        }
    }
    Check 'synthetic phase permissions cannot repeat or skip a failed import' {
        Invoke-CodecGrantFixture {
            Start-CodecInvocation
            Assert-CodecAuthorization -Step Dispatch
            Reject { Assert-CodecAuthorization -Step Dispatch } 'out of order'
            Reject { Assert-CodecAuthorization -Step Import } 'out of order'
            Assert-CodecAuthorization -Step Stage
            Reject { Assert-CodecAuthorization -Step Stage } 'out of order'
            Assert-CodecAuthorization -Step Import
            Reject { Assert-CodecAuthorization -Step Import } 'out of order'
            Reject { Assert-CodecAuthorization -Step Codec } 'out of order'
            Complete-CodecAuthorizationPhase Import
            Assert-CodecAuthorization -Step Codec
            Complete-CodecAuthorizationPhase Codec
            Reject { Assert-CodecAuthorization -Step Codec } 'out of order'
            Close-CodecInvocation
            Reject { Start-CodecInvocation } 'already consumed'
        }
    }
    foreach ($failure in @('static failure', 'partial staging', 'failed import', 'codec failure', 'timeout', 'uncertain termination')) {
        $failureLabel = $failure
        Check "synthetic $failureLabel consumes the grant without retry" {
            Invoke-CodecGrantFixture {
                Start-CodecInvocation
                try { throw 'Synthetic failed attempt' } catch { } finally { Close-CodecInvocation }
                Reject { Start-CodecInvocation } 'already consumed'
            }
        }
    }
    Check 'empty malformed and partial tombstones deny without reading approval data' {
        foreach ($content in @('', '{partial', '{"State":"AUTHORIZED"}')) {
            $recordContent = $content
            Invoke-CodecGrantFixture {
                param($receipt)
                [IO.File]::WriteAllText($receipt, $recordContent)
                Reject { Start-CodecInvocation } 'already consumed'
                Require ($null -eq $script:CodecGrantContext) 'Existing record became an approval'
            }
        }
    }
    Check 'consumption creation failure denies all helpers without an invocation context' {
        Invoke-CodecGrantFixture {
            param($receipt)
            $unavailable = Join-Path ([IO.Path]::GetDirectoryName($receipt)) 'missing/record.json'
            function Get-CodecConsumptionPath { $unavailable }
            Reject { Start-CodecInvocation } 'consumption parent unavailable'
            Reject { Assert-CodecAuthorization -Step Dispatch } 'no live consumed'
            Require ($null -eq $script:CodecGrantContext) 'Failed record created context'
        }
    }
    Check 'record write verification failure leaves a denying tombstone' {
        Invoke-CodecGrantFixture {
            param($receipt)
            function Get-CodecHash { throw 'Synthetic write verification failure' }
            Reject { Start-CodecInvocation } 'could not be recorded'
            Require ((Test-Path -LiteralPath $receipt) -and $null -eq $script:CodecGrantContext) 'Partial record or denial missing'
            Reject { Start-CodecInvocation } 'already consumed'
        }
    }
    Check 'binding preflight failure consumes an empty claim before any workflow step' {
        Invoke-CodecGrantFixture {
            param($receipt)
            function Get-CodecGrantBinding { throw 'Synthetic binding failure' }
            Reject { Start-CodecInvocation } 'could not be recorded'
            Require ((Test-Path -LiteralPath $receipt) -and (Get-Item -LiteralPath $receipt).Length -eq 0) 'Failed binding left no claim'
            Reject { Start-CodecInvocation } 'already consumed'
        }
    }
    Check 'changed binding and restored source revoke a live synthetic invocation' {
        Invoke-CodecGrantFixture {
            param($receipt, $model)
            Start-CodecInvocation
            $model.Identity = 'e' * 64
            Reject { Assert-CodecAuthorization } 'identity changed'
            $model.State = 'PREPARED'
            Reject { Assert-CodecAuthorization } 'AUTHORIZATION_DENIED'
            Reject { Start-CodecInvocation } 'AUTHORIZATION_DENIED'
            Require (Test-Path -LiteralPath $receipt) 'Restoration deleted consumption'
        }
    }
    Check 'inert process interruption leaves consumption and a second process denies' {
        $receipt = Join-Path $fixture 'synthetic-interrupted.json'
        $child = Join-Path $fixture 'synthetic-grant-child.ps1'
        $runnerLiteral = (Join-Path $repository 'tools/run-save-codec-tests.ps1').Replace("'", "''")
        $receiptLiteral = $receipt.Replace("'", "''")
        $childText = @'
param([switch]$Interrupt)
$ErrorActionPreference = 'Stop'
. '__RUNNER__'
function Get-CodecGrantTransition { 'AUTHORIZED_ONCE:bbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbbb' }
function Get-CodecConsumptionPath { '__RECEIPT__' }
function Get-CodecGrantBinding { [pscustomobject]@{ ReviewedRevision = ('b' * 40); ActivationRevision = ('c' * 40); IdentitySha256 = ('d' * 64) } }
function Invoke-BoundedProcess { throw 'Unexpected process in synthetic child' }
function New-CodecStage { throw 'Unexpected stage in synthetic child' }
function Invoke-CodecEnginePhase { throw 'Unexpected engine in synthetic child' }
try {
    Start-CodecInvocation
    if ($Interrupt) { [Environment]::Exit(17) }
    exit 99
} catch {
    if ($_ -match 'already consumed') { exit 0 }
    throw
}
'@
        [IO.File]::WriteAllText($child, $childText.Replace('__RUNNER__', $runnerLiteral).Replace('__RECEIPT__', $receiptLiteral))
        $pwsh = Join-Path $PSHOME 'pwsh.exe'
        $first = Invoke-BoundedProcess $pwsh @('-NoProfile', '-File', $child, '-Interrupt') $fixture -Seconds 10
        Require ($first.ExitCode -eq 17 -and $first.TerminationCertain -and (Test-Path -LiteralPath $receipt)) 'Synthetic interruption did not consume'
        $second = Invoke-BoundedProcess $pwsh @('-NoProfile', '-File', $child) $fixture -Seconds 10
        Require ($second.ExitCode -eq 0 -and $second.TerminationCertain) 'Second synthetic process reused grant'
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
