#requires -Version 7.0
# Non-Godot fixtures only. No engine lookup, invocation, project imports or edits.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../tools/run-local-tests.ps1"
$passed = 0; $failed = 0
function Check([string]$Name, [scriptblock]$Body) {
    try { & $Body; $script:passed++; Write-Host "PASS $Name" }
    catch { $script:failed++; Write-Host "FAIL ${Name}: $_" }
}
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Reject([scriptblock]$Body, [string]$Pattern) {
    try { & $Body } catch {
        if ($_ -notmatch $Pattern) { throw "Unexpected rejection: $_" }
        return
    }
    throw 'Expected rejection did not occur.'
}
$hostExe = Join-Path $PSHOME 'pwsh.exe'
$fixture = Join-Path ([IO.Path]::GetTempPath()) ('tlwh-runner-fixture-' + [Guid]::NewGuid().ToString('N'))
$null = New-Item -ItemType Directory -Path $fixture
$source = Join-Path $fixture 'source'
$null = New-Item -ItemType Directory -Path "$source/tests", "$source/assets", "$source/saves", "$source/.godot"
[IO.File]::WriteAllText("$source/project.godot", '; synthetic fixture only')
[IO.File]::WriteAllText("$source/tests/fabricator_recipe_switching_test.gd", '# inert fixture')
[IO.File]::WriteAllText("$source/tests/static_fixture_test.py", '# inert fixture; never executed')
[IO.File]::WriteAllBytes("$source/assets/sample.png", [byte[]]@(0, 255, 10, 13, 128))
[IO.File]::WriteAllText("$source/assets/sample.png.import", 'synthetic sidecar')
[IO.File]::WriteAllText("$source/tests/fabricator_recipe_switching_test.gd.uid", 'uid://synthetic')
[IO.File]::WriteAllText("$source/saves/private.json", 'protected fixture')
[IO.File]::WriteAllText("$source/.godot/cache", 'ignored fixture')
[IO.File]::WriteAllText("$source/assets/untracked.png", 'untracked fixture')
$tracked = @('project.godot', 'tests/fabricator_recipe_switching_test.gd',
    'tests/fabricator_recipe_switching_test.gd.uid', 'assets/sample.png', 'assets/sample.png.import',
    'saves/private.json', '.godot/cache')
$null = New-Item -ItemType Directory -Path "$source/tools"
[IO.File]::WriteAllText("$source/tools/run-local-tests.ps1", '# inert runner identity')
[IO.File]::WriteAllText("$source/AGENTS.md", 'inert policy identity')
$tracked += @('tools/run-local-tests.ps1', 'AGENTS.md')
# This pinned identity is inert text, never an executable or a Godot installation.
$inertEngine = Join-Path $fixture 'pinned-engine.txt'
[IO.File]::WriteAllText($inertEngine, 'inert identity fixture')
$inertHash = (Get-FileHash -LiteralPath $inertEngine).Hash
$completion = 'Fabricator recipe switching regression failures: 0'
function NativeResult([string]$Stdout = '', [string]$Stderr = '',
                      [string]$Status = 'PASS', $ExitCode = 0, [bool]$Certain = $true) {
    [pscustomobject]@{ Status = $Status; ExitCode = $ExitCode; Stdout = $Stdout; Stderr = $Stderr;
        Bytes = [Text.Encoding]::UTF8.GetByteCount($Stdout + $Stderr); TerminationCertain = $Certain }
}
# Exercise the real dispatcher with scoped, named non-Godot doubles only.
# The production API has no injection parameters. Unexpected process calls throw.
function Invoke-DispatchFixture([object[]]$Results, [string]$Mutation = '') {
    $calls = [Collections.Generic.List[object]]::new()
    $state = @{ IdentityReads = 0; Stage = $null; ApprovalChecks = 0 }
    $stageFunction = (Get-Command New-InputStage).ScriptBlock
    function Assert-ReviewedNativeRunner { }
    function Assert-NativeExecutionAuthorization {
        $state.ApprovalChecks++
        if ($Mutation -eq 'revoked' -and $state.ApprovalChecks -eq 4) { throw 'Synthetic revoked owner approval' }
    }
    function Get-NativeSourceIdentity {
        param($Source)
        $state.IdentityReads++
        [pscustomobject]@{ Revision = ('a' * 40); Working = ' M project.godot';
            Index = $(if ($Mutation -eq 'source' -and $calls.Count -gt 0) { 'changed' } else { 'inert-index' });
            Tracked = $tracked }
    }
    function New-InputStage {
        param($Source, $Parent, $Tracked)
        $state.Stage = & $stageFunction $Source $fixture $Tracked
        return $state.Stage
    }
    function Invoke-BoundedProcess {
        param($Executable, $Arguments, $Directory, $Seconds, $MaxBytes, $ExcerptBytes)
        if ($Arguments[0] -eq 'check-ignore') { return NativeResult }
        Require ($Executable -ceq $inertEngine -and $Arguments[0] -ceq '--headless') 'Unexpected process'
        Require (Test-Path -LiteralPath $reviewScope.ReceiptPath -PathType Leaf) 'Engine reached before consumption'
        Require ($MaxBytes -eq 1048576 -and $ExcerptBytes -eq 4096) 'Wrong dispatch limits'
        $calls.Add([pscustomobject]@{ Arguments = $Arguments; Seconds = $Seconds })
        if ($calls.Count -eq 1) {
            switch ($Mutation) {
                cache { $null = New-Item -ItemType Directory -Path "$Directory/.godot" }
                stage { [IO.File]::WriteAllText("$Directory/project.godot", 'tampered') }
                extra { [IO.File]::WriteAllText("$Directory/unexpected.txt", 'tampered') }
                engine { [IO.File]::WriteAllText($inertEngine, 'tampered') }
            }
        }
        if ($calls.Count -gt $Results.Count) { throw 'Unexpected retry' }
        return $Results[$calls.Count - 1]
    }
    $preparedStage = New-InputStage $source $fixture $tracked
    $snapshot = [pscustomobject]@{ Identity = (Get-NativeSourceIdentity $source); Inputs = $preparedStage.Inputs }
    $reviewScope = New-FirstRunReviewScope $inertEngine $inertHash $preparedStage $snapshot
    # Receipt is real, in a fresh synthetic source evidence directory; each helper
    # invocation represents an independently approved fixture-only scope.
    $receiptDirectory = Join-Path $fixture ([Guid]::NewGuid().ToString('N'))
    $null = New-Item -ItemType Directory -Path $receiptDirectory
    $reviewScope.ReceiptPath = Join-Path $receiptDirectory 'first-run-attempt.receipt'
    $reviewScope.EvidenceDirectory = $receiptDirectory
    function Get-ApprovedFirstRunContext { [pscustomobject]@{ Stage = $preparedStage; Scope = $reviewScope } }
    # Bind using the actual review builder; only redirect fixture evidence paths.
    $scopeBuilder = (Get-Command New-FirstRunReviewScope).ScriptBlock
    function New-FirstRunReviewScope {
        param($Engine, $EngineHash, $Stage, $StaticSnapshot, [switch]$Imported)
        $scope = & $scopeBuilder $Engine $EngineHash $Stage $StaticSnapshot -Imported:$Imported
        $scope.EvidenceDirectory = $receiptDirectory
        $scope.ReceiptPath = Join-Path $receiptDirectory 'first-run-attempt.receipt'
        $scope
    }
    try {
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS $snapshot
        [pscustomobject]@{ Summary = $r; Calls = $calls; Reads = $state.IdentityReads; ApprovalChecks = $state.ApprovalChecks; Receipt = $reviewScope.ReceiptPath; Scope = $reviewScope }
    } finally { [IO.File]::WriteAllText($inertEngine, 'inert identity fixture') }
}
try {
    Check 'bounded process success' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command', "[Console]::Write('fixture-ok')") $fixture
        Require ($r.Status -eq 'PASS' -and $r.ExitCode -eq 0 -and $r.Excerpt -eq 'fixture-ok') 'Wrong success result'
    }
    Check 'abnormal process exit' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command', 'exit 7') $fixture
        Require ($r.Status -eq 'NONZERO_EXIT' -and $r.ExitCode -eq 7) 'Abnormal exit accepted'
    }
    Check 'static failure propagation and later phases skipped' {
        # Replace only the subprocess helper in this child scope. No project command runs.
        function Invoke-BoundedProcess {
            param($Executable, $Arguments, $Directory)
            $value = switch ($Arguments[0]) {
                'rev-parse' { if ($Arguments[1] -eq '--show-toplevel') { $Directory } else { 'synthetic-revision' } }
                'status' { '' }
                '-B' { 'synthetic assertion failure' }
                default { throw 'Unexpected later phase' }
            }
            [pscustomobject]@{ Status = $(if ($Arguments[0] -eq '-B') { 'NONZERO_EXIT' } else { 'PASS' });
                ExitCode = $(if ($Arguments[0] -eq '-B') { 1 } else { 0 }); Bytes = $value.Length; Excerpt = $value; TerminationCertain = $true }
        }
        Require ((Invoke-LocalTests $source 'Static' '' '') -eq 1) 'Static failure accepted'
    }
    Check 'missing executable' {
        Reject { Invoke-BoundedProcess "$fixture/missing.exe" @() $fixture } 'cannot find|No such|specified'
    }
    Check 'timeout' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command', 'Start-Sleep -Seconds 5') $fixture -Seconds 1
        Require ($r.Status -eq 'TIMEOUT' -and $null -eq $r.ExitCode) 'Timeout accepted'
    }
    Check 'combined stdout/stderr output cap and bounded excerpt' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command',
            "[Console]::Out.Write(('x' * 600000)); [Console]::Error.Write(('y' * 600000))") $fixture
        Require ($r.Status -eq 'OUTPUT_LIMIT' -and $r.Bytes -gt 1048576 -and $r.Excerpt.Length -le 4096) 'Overflow accepted'
    }
    Check 'unsafe traversal rejected before stage creation' {
        Reject { New-InputStage $source $fixture ($tracked + '../escape.gd') } 'Unsafe input'
    }
    Check 'Windows aliases, ADS and rooted paths rejected' {
        foreach ($path in @('assets/.. /escape.gd', 'assets/CON.png', 'assets/a.png:secret', '/assets/a.png', 'assets//a.png')) {
            Reject { New-InputStage $source $fixture ($tracked + $path) } 'Unsafe'
        }
    }
    Check 'source-contained staging rejected' {
        Reject { New-InputStage $source "$source/stage" $tracked } 'outside the source'
    }
    Check 'byte-preserving tracked working inputs and exclusions' {
        $stage = New-InputStage $source $fixture $tracked
        Require ($stage.Inputs.Count -eq 5) 'Incorrect inventory'
        foreach ($entry in $stage.Inputs) {
            Require ((Get-FileHash -LiteralPath (Join-Path $stage.Directory $entry.Path)).Hash -eq $entry.Sha256) 'Byte mismatch'
        }
        Require (-not (Test-Path "$($stage.Directory)/saves")) 'Save copied'
        Require (-not (Test-Path "$($stage.Directory)/.godot")) 'Cache copied'
        Require (-not (Test-Path "$($stage.Directory)/assets/untracked.png")) 'Untracked copied'
        [IO.File]::WriteAllText("$source/project.godot", '; changed working bytes')
        $second = New-InputStage $source $fixture $tracked
        Require ($second.Directory -ne $stage.Directory) 'Stage reused'
        Require ((Get-Content -Raw "$($second.Directory)/project.godot") -eq '; changed working bytes') 'Tested old commit'
    }
    Check 'missing tracked input rejected' {
        Reject { New-InputStage $source $fixture ($tracked + 'assets/missing.png') } 'Missing tracked input'
    }
    Check 'prohibited native invocation fails before prerequisites' {
        Require ((Invoke-LocalTests "$fixture/nonexistent" 'Native' $hostExe ('0' * 64)) -eq 1) 'Native execution gate bypassed'
    }
    Check 'missing native configuration fails closed' {
        Require ((Invoke-LocalTests (Split-Path $PSScriptRoot -Parent) 'NativePlan' '' '') -eq 1) 'Missing configuration accepted'
    }
    Check 'mismatched native identity fails closed without invocation' {
        Require ((Invoke-LocalTests (Split-Path $PSScriptRoot -Parent) 'NativePlan' $hostExe ('0' * 64)) -eq 1) 'Identity mismatch accepted'
    }
    Check 'full synthetic NativePlan succeeds without invoking pinned binary' {
        $stageFunction = (Get-Command New-InputStage).ScriptBlock
        function New-InputStage {
            param($Source, $Parent, $Tracked)
            & $stageFunction $Source $fixture $Tracked
        }
        function Get-NativeSourceIdentity {
            [pscustomobject]@{ Revision = ('a' * 40); Working = ' M project.godot';
                Index = 'inert-index'; Tracked = $tracked }
        }
        function Invoke-BoundedProcess {
            param($Executable, $Arguments, $Directory, $ExcerptBytes)
            Require ($Executable -ne $hostExe) 'Pinned binary was invoked'
            $value = switch ($Arguments[0]) {
                'rev-parse' { if ($Arguments[1] -eq '--show-toplevel') { $Directory } else { 'synthetic-revision' } }
                'status' { ' M project.godot' }
                '-B' { 'synthetic static suite success' }
                'ls-files' { ($tracked | ForEach-Object { "100644 $('a' * 40) 0`t$_" }) -join [char]0 }
                default { throw 'Unexpected subprocess' }
            }
            [pscustomobject]@{ Status = 'PASS'; ExitCode = 0; Bytes = $value.Length; Excerpt = $value; TerminationCertain = $true }
        }
        Require ((Invoke-LocalTests $source 'NativePlan' $hostExe (Get-FileHash $hostExe).Hash) -eq 0) 'Plan failed'
    }
    $nativeStage = New-InputStage $source $fixture $tracked
    Check 'first-run review scope binds identities without authorizing execution' {
        function Get-NativeSourceIdentity {
            [pscustomobject]@{ Revision = ('a' * 40); Working = ' M project.godot';
                Index = 'inert-index'; Tracked = $tracked }
        }
        function Invoke-BoundedProcess { throw 'Review scope attempted a process' }
        $snapshot = [pscustomobject]@{ Identity = (Get-NativeSourceIdentity); Inputs = $nativeStage.Inputs }
        $scope = New-FirstRunReviewScope $inertEngine $inertHash $nativeStage $snapshot
        Require ($scope.Authorization -ceq 'INACTIVE' -and $scope.Routine -ceq 'INACTIVE') 'Scope grants permission'
        Require ($scope.Revision -ceq ('a' * 40) -and $scope.Source -ceq $source -and
            $scope.StageDirectory -ceq $nativeStage.Directory -and $scope.Inputs.Count -eq 5) 'Source/stage identity missing'
        Require ($scope.RunnerPath -ceq (Join-Path $source 'tools/run-local-tests.ps1') -and
            $scope.Controls[0].Sha256 -ceq (Get-FileHash "$source/tools/run-local-tests.ps1").Hash -and
            $scope.IndexSha256 -match '^[A-F0-9]{64}$') 'Runner/control/index identity missing'
        Require ($scope.Commands.Count -eq 2 -and $scope.Commands[0].Executable -ceq $inertEngine -and
            $scope.Commands[1].Sha256 -ceq $inertHash -and $scope.MaxAttemptsPerPhase -eq 1 -and
            $scope.MaxConcurrentProcesses -eq 1 -and $scope.EvidenceDirectory -ceq (Join-Path $source 'artifacts/logs')) 'Review limits missing'
        Reject { Assert-NativeExecutionAuthorization } 'inactive'
        # Repeated successful planning cannot consume or unlock permission.
        $null = New-FirstRunReviewScope $inertEngine $inertHash $nativeStage $snapshot
        Reject { Assert-NativeExecutionAuthorization } 'inactive'
        Reject { Assert-NativeExecutionAuthorization -Scope $scope } 'parameter'
    }
    Check 'first-run review rejects changed static snapshot identity and bytes' {
        $reviewIdentity = [pscustomobject]@{ Revision = ('a' * 40); Working = ''; Index = 'inert-index'; Tracked = $tracked }
        function Get-NativeSourceIdentity { return $reviewIdentity }
        function Invoke-BoundedProcess { throw 'Review scope attempted a process' }
        Reject { New-FirstRunReviewScope $inertEngine $inertHash $nativeStage $null } 'snapshot required'
        foreach ($key in @('Revision', 'Working', 'Index')) {
            $old = $reviewIdentity.PSObject.Copy(); $old.$key = 'changed'
            $snapshot = [pscustomobject]@{ Identity = $old; Inputs = $nativeStage.Inputs }
            Reject { New-FirstRunReviewScope $inertEngine $inertHash $nativeStage $snapshot } 'Source changed'
        }
        $snapshot = [pscustomobject]@{ Identity = $reviewIdentity; Inputs = @() }
        Reject { New-FirstRunReviewScope $inertEngine $inertHash $nativeStage $snapshot } 'Working inputs changed'
    }
    Check 'first-run review rejects tampered stage engine and missing control identity' {
        $identity = [pscustomobject]@{ Revision = ('a' * 40); Working = ''; Index = 'inert-index'; Tracked = $tracked }
        function Get-NativeSourceIdentity { return $identity }
        function Invoke-BoundedProcess { throw 'Review scope attempted a process' }
        $stage = New-InputStage $source $fixture $tracked
        $snapshot = [pscustomobject]@{ Identity = $identity; Inputs = $stage.Inputs }
        Reject { New-FirstRunReviewScope $inertEngine ('0' * 64) $stage $snapshot } 'mismatch'
        [IO.File]::WriteAllText("$($stage.Directory)/project.godot", 'tampered')
        Reject { New-FirstRunReviewScope $inertEngine $inertHash $stage $snapshot } 'input changed'
        [IO.File]::Copy("$source/project.godot", "$($stage.Directory)/project.godot", $true)
        $identity.Tracked = @($tracked | Where-Object { $_ -cne 'AGENTS.md' })
        Reject { New-FirstRunReviewScope $inertEngine $inertHash $stage $snapshot } 'review identity missing'
    }
    Check 'fixed command allowlist, limits and no arbitrary flags' {
        $commands = @(New-NativeCommandPlan $inertEngine $inertHash $nativeStage)
        Require ($commands.Count -eq 2) 'Wrong command count'
        Require (($commands[0].Arguments -join '|') -ceq "--headless|--editor|--path|$($nativeStage.Directory)|--quit") 'Import arguments changed'
        Require (($commands[1].Arguments -join '|') -ceq "--headless|--path|$($nativeStage.Directory)|--script|res://tests/fabricator_recipe_switching_test.gd") 'Test arguments changed'
        Require ($commands[0].Seconds -eq 60 -and $commands[1].Seconds -eq 30) 'Wrong deadlines'
        foreach ($command in $commands) {
            Require ($command.MaxBytes -eq 1048576 -and $command.Executable -ceq $inertEngine -and $command.Sha256 -ceq $inertHash) 'Identity/limit changed'
        }
        Reject { New-NativeCommandPlan $inertEngine $inertHash $nativeStage -Arguments @('--help') } 'parameter'
        Reject { Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS -Executor {} } 'parameter'
    }
    Check 'synthetic dispatcher success, ordering, no process execution' {
        function Invoke-BoundedProcess { throw 'Synthetic dispatcher attempted a process' }
        $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @((NativeResult), (NativeResult $completion))
        Require ($r.Synthetic -and $r.Static -eq 'PASS' -and $r.Import -eq 'PASS' -and $r.Native -eq 'PASS') 'Wrong phases'
        Require (($r.Commands.Phase -join ',') -ceq 'Import,Native') 'Wrong order or retries'
    }
    Check 'synthetic static failure skips both commands' {
        $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage FAIL @()
        Require ($r.Commands.Count -eq 0 -and $r.Import -eq 'NOT RUN' -and $r.Native -eq 'NOT RUN') 'Static stop failed'
    }
    Check 'each import failure stops test, no retries' {
        $badImports = @((NativeResult '' 'ERROR: import failed'), (NativeResult '' '' 'NONZERO_EXIT' 7),
            (NativeResult '' '' 'TIMEOUT' $null $false), (NativeResult '' '' 'OUTPUT_LIMIT' $null $false),
            (NativeResult '' '' 'PASS' 0 $false), (NativeResult '' '' 'PASS' 9))
        foreach ($bad in $badImports) {
            $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @($bad, (NativeResult $completion))
            Require ($r.Import -eq 'FAIL' -and $r.Native -eq 'NOT RUN' -and $r.Commands.Count -eq 1) 'Import failure continued'
        }
    }
    Check 'test failure preserves successful import and fails native' {
        $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @((NativeResult), (NativeResult 'Fabricator recipe switching regression failures: 3'))
        Require ($r.Import -eq 'PASS' -and $r.Native -eq 'FAIL' -and $r.Reason -eq 'ASSERTION_FAILURE' -and $r.Commands.Count -eq 2) 'Assertion accepted'
    }
    Check 'completion required, exact, unique, final and on stdout' {
        foreach ($text in @('', 'Fabricator recipe switching regression failures: nope',
            'Fabricator recipe switching regression failures: 00', "$completion`n$completion", "$completion`nmore output")) {
            Require ((Get-NativeOutcome Native (NativeResult $text)).Reason -eq 'MISSING_OR_MALFORMED_COMPLETION') 'Bad completion accepted'
        }
        Require ((Get-NativeOutcome Native (NativeResult '' $completion)).Status -eq 'FAIL') 'stderr completion accepted'
        Require ((Get-NativeOutcome Native (NativeResult "Godot synthetic banner`r`n$completion`r`n")).Status -eq 'PASS') 'CRLF completion rejected'
    }
    Check 'zero exit with engine errors on either stream fails' {
        foreach ($errorText in @('ERROR: resource failed', 'SCRIPT ERROR: invalid call', 'Parse Error: invalid syntax', 'Assertion failed')) {
            Require ((Get-NativeOutcome Import (NativeResult $errorText)).Status -eq 'FAIL') 'Import error accepted'
            Require ((Get-NativeOutcome Native (NativeResult $completion $errorText)).Status -eq 'FAIL') 'Test error accepted'
        }
    }
    Check 'errors after diagnostic excerpt and split byte reads remain visible' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command',
            "[Console]::Out.Write(('x' * 5000)); [Console]::Error.Write('SCRIPT '); [Console]::Error.Flush(); Start-Sleep -Milliseconds 100; [Console]::Error.Write('ERROR: late failure')") $fixture
        Require ($r.Excerpt.Length -le 4096 -and $r.Stderr -ceq 'SCRIPT ERROR: late failure') 'Full bounded capture missing'
        Require ((Get-NativeOutcome Import $r).Status -eq 'FAIL') 'Late error accepted'
    }
    Check 'exact combined byte boundary and Unicode raw-byte accounting' {
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-Command',
            "[Console]::OutputEncoding = [Text.Encoding]::UTF8; [Console]::Out.Write(([string][char]0x00e9 * 524288))") $fixture
        Require ($r.Status -eq 'PASS' -and $r.Bytes -eq 1048576) 'Exact byte boundary failed'
        Require ([Text.Encoding]::UTF8.GetByteCount($r.Stdout + $r.Stderr) -eq 1048576) 'UTF-8 capture corrupted'
    }
    Check 'timeout and overflow records fail and termination remains uncertain' {
        foreach ($arguments in @(
            @('-NoProfile', '-Command', 'Start-Sleep -Seconds 5'),
            @('-NoProfile', '-Command', "[Console]::Out.Write(('x' * 1100000))"))) {
            $r = Invoke-BoundedProcess $hostExe $arguments $fixture -Seconds 1
            Require ($r.Status -in @('TIMEOUT', 'OUTPUT_LIMIT') -and -not $r.TerminationCertain) 'Unsafe termination claim'
            Require ((Get-NativeOutcome Import $r).Status -eq 'FAIL') 'Limit failure accepted'
            Require ([Text.Encoding]::UTF8.GetByteCount($r.Stdout + $r.Stderr) -le 1048576) 'Unbounded retained output'
        }
    }
    Check 'missing and malformed synthetic results fail closed' {
        $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @()
        Require ($r.Import -eq 'FAIL' -and $r.Native -eq 'NOT RUN' -and $r.Reason -eq 'MISSING_RESULT') 'Missing result accepted'
        $r = Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @([pscustomobject]@{ ExitCode = 0 })
        Require ($r.Import -eq 'FAIL' -and $r.Native -eq 'NOT RUN' -and $r.Reason -eq 'MALFORMED_RESULT') 'Malformed result accepted'
    }
    Check 'missing, relative, wildcard and malformed executable identity refused' {
        Reject { New-NativeCommandPlan '' '' $nativeStage } 'absolute'
        Reject { New-NativeCommandPlan 'relative.exe' $inertHash $nativeStage } 'absolute'
        Reject { New-NativeCommandPlan "$fixture/*.txt" $inertHash $nativeStage } 'missing|mismatch'
        Reject { New-NativeCommandPlan "$fixture/missing.exe" $inertHash $nativeStage } 'missing|mismatch'
        Reject { New-NativeCommandPlan $inertEngine 'bad' $nativeStage } 'SHA256'
    }
    Check 'changed executable identity refused before simulated dispatch' {
        [IO.File]::WriteAllText($inertEngine, 'changed identity')
        Reject { Invoke-SyntheticNativeSequence $inertEngine $inertHash $nativeStage PASS @((NativeResult)) } 'mismatch'
        [IO.File]::WriteAllText($inertEngine, 'inert identity fixture')
    }
    Check 'real dispatch wiring uses only fixed sequential commands, no retries' {
        $r = Invoke-DispatchFixture @((NativeResult), (NativeResult $completion)) cache
        Require ($r.Summary.Import -eq 'PASS' -and $r.Summary.Native -eq 'PASS') 'Dispatch failed'
        Require ($r.Calls.Count -eq 2 -and $r.Reads -ge 5) 'Missing per-phase validation or wrong launch count'
        Require ($r.ApprovalChecks -eq 4) 'Missing per-launch approval validation'
        Require ($r.Calls[0].Seconds -eq 60 -and $r.Calls[1].Seconds -eq 30) 'Wrong launch deadlines'
        Require (($r.Calls[0].Arguments -join '|') -ceq "--headless|--editor|--path|$($r.Summary.StageDirectory)|--quit") 'Wrong import'
        Require (($r.Calls[1].Arguments -join '|') -ceq "--headless|--path|$($r.Summary.StageDirectory)|--script|res://tests/fabricator_recipe_switching_test.gd") 'Wrong script'
        Require ($r.Summary.Evidence -eq '' -and $r.Summary.Working -eq ' M project.godot') 'Success log or missing provenance'
    }
    Check 'source identity reads actual revision working status and regular tracked index without project execution' {
        $identity = Get-NativeSourceIdentity (Split-Path $PSScriptRoot -Parent)
        Require ($identity.Revision -match '^[0-9a-f]{40}$' -and
            'project.godot' -cin $identity.Tracked -and $identity.Index.Length -gt 0) 'Incomplete source identity'
        Require ($identity.Working -is [string]) 'Working status omitted'
    }
    Check 'synthetic generated reparse point and stage source overlap rejected' {
        $stage = New-InputStage $source $fixture $tracked
        $identity = [pscustomobject]@{ Revision = 'fixture'; Working = ''; Index = ''; Tracked = $tracked }
        function Get-NativeSourceIdentity { return $identity }
        $cache = Join-Path $stage.Directory '.godot'
        $null = New-Item -ItemType Directory -Path $cache
        $link = Join-Path $cache 'external'
        $null = New-Item -ItemType Directory -Path $link
        # No junction privilege needed: expose synthetic link metadata to the
        # real path validator; it must reject before enumerating the child.
        function Get-Item {
            param([switch]$Force, [string]$LiteralPath)
            if ($LiteralPath -ceq $link) {
                return [pscustomobject]@{ Attributes = [IO.FileAttributes]::ReparsePoint }
            }
            Microsoft.PowerShell.Management\Get-Item -Force:$Force -LiteralPath $LiteralPath
        }
        Reject { Assert-NativeDispatchInputs $stage $identity $true } 'Reparse point'
        $stage.Directory = $source
        Reject { Assert-NativeDispatchInputs $stage $identity $false } 'identity|separation'
    }
    Check 'real dispatch stops every failed import and retains bounded unique evidence' {
        foreach ($bad in @((NativeResult '' 'SCRIPT ERROR: failure'), (NativeResult '' '' TIMEOUT $null $false),
            (NativeResult '' '' OUTPUT_LIMIT $null $false), (NativeResult '' '' PASS 0 $false),
            (NativeResult '' '' NONZERO_EXIT 7))) {
            $r = Invoke-DispatchFixture @($bad)
            Require ($r.Calls.Count -eq 1 -and $r.Summary.Import -eq 'FAIL' -and $r.Summary.Native -eq 'NOT RUN') 'Continued after import failure'
            Require ((Get-Item -LiteralPath $r.Summary.Evidence).Length -le 65536) 'Unbounded or missing evidence'
            Require (Test-Path -LiteralPath $r.Receipt) 'Failed attempt receipt lost'
            Reject { New-FirstRunAttemptReceipt $r.Scope } 'exists'
            $saved = Get-Content -Raw -LiteralPath $r.Summary.Evidence | ConvertFrom-Json
            Require ($saved.Revision -ceq ('a' * 40) -and $saved.Commands.Count -eq 1) 'Evidence missing provenance'
        }
        Require (@(Get-ChildItem "$source/artifacts/logs").Count -eq 5) 'Evidence overwritten'
    }
    Check 'real dispatch native failure preserves import and does not retry' {
        $r = Invoke-DispatchFixture @((NativeResult), (NativeResult 'Fabricator recipe switching regression failures: 2'))
        Require ($r.Summary.Import -eq 'PASS' -and $r.Summary.Native -eq 'FAIL' -and $r.Calls.Count -eq 2) 'Wrong native failure'
    }
    Check 'source stage inventory and engine changes between phases stop dispatch' {
        foreach ($mutation in @('source', 'stage', 'extra', 'engine', 'revoked')) {
            $r = Invoke-DispatchFixture @((NativeResult), (NativeResult $completion)) $mutation
            Require ($r.Calls.Count -eq 1 -and $r.Summary.Import -eq 'PASS' -and $r.Summary.Native -eq 'FAIL') "Mutation accepted: $mutation"
            if ($mutation -eq 'revoked') { Require ($r.Summary.Authorization -eq 'FAIL') 'Revocation outcome missing' }
        }
    }
    Check 'real dispatch static gate has no side effects' {
        function Assert-PinnedEngine { throw 'Static gate reached identity checks' }
        function New-InputStage { throw 'Static gate created stage' }
        function Invoke-BoundedProcess { throw 'Static gate launched process' }
        foreach ($status in @('FAIL', 'NOT RUN')) {
            $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash $status
            Require ($r.Import -eq 'NOT RUN' -and $r.Native -eq 'NOT RUN' -and $r.Commands.Count -eq 0) 'Static gate failed'
        }
    }
    Check 'evidence requires ignored plain path and preserves existing owner file' {
        $ownerFile = "$source/artifacts/logs/owner.txt"
        [IO.File]::WriteAllText($ownerFile, 'preserve me')
        function Invoke-BoundedProcess { NativeResult '' '' NONZERO_EXIT 1 }
        $r = (Invoke-DispatchFixture @((NativeResult '' 'ERROR: failure'))).Summary
        Reject { Save-NativeFailureEvidence $source $r } 'not confirmed ignored'
        Require ((Get-Content -Raw $ownerFile) -ceq 'preserve me') 'Owner evidence changed'
    }
    Check 'dispatcher reports source-identity and evidence failures without continuing' {
        function Get-NativeSourceIdentity { throw 'synthetic source failure' }
        function Save-NativeFailureEvidence { throw 'synthetic disk failure' }
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS
        Require ($r.Import -eq 'NOT RUN' -and $r.Native -eq 'NOT RUN' -and $r.Infrastructure -eq 'FAIL' -and $r.EvidenceError -ne '') 'Infrastructure failure lost'
    }
    Check 'production public call graph has exactly one guarded dispatch caller' {
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile("$PSScriptRoot/../tools/run-local-tests.ps1", [ref]$tokens, [ref]$errors)
        Require ($errors.Count -eq 0) 'Runner syntax errors'
        $calls = @($ast.FindAll({ param($node)
            $node -is [Management.Automation.Language.CommandAst] -and
            $node.GetCommandName() -eq 'Invoke-RestrictedNativeDispatch'
        }, $true))
        Require ($calls.Count -eq 1) 'Unexpected dispatcher call paths'
        Require ($calls[0].Extent.Text -match '\$static \$snapshot') 'Actual static outcome/snapshot omitted'
        Reject { Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS -Executor {} } 'parameter'
    }
    Check 'stage mutations and unexpected hidden directories refused' {
        [IO.File]::WriteAllText("$($nativeStage.Directory)/project.godot", 'changed stage')
        Reject { New-NativeCommandPlan $inertEngine $inertHash $nativeStage } 'changed'
        [IO.File]::Copy("$source/project.godot", "$($nativeStage.Directory)/project.godot", $true)
        $null = New-Item -ItemType Directory -Path "$($nativeStage.Directory)/.godot"
        Reject { New-NativeCommandPlan $inertEngine $inertHash $nativeStage } 'Unexpected staged directory'
    }
    Check 'inactive authorization gate rejects direct dispatch without engine execution' {
        $stage = New-InputStage $source $fixture $tracked
        function Get-NativeSourceIdentity {
            [pscustomobject]@{ Revision = ('a' * 40); Working = ''; Index = 'fixture'; Tracked = $tracked }
        }
        function New-InputStage { return $stage }
        function Invoke-BoundedProcess {
            param($Executable, $Arguments)
            Require ($Arguments[0] -eq 'check-ignore') 'Inactive gate reached engine'
            NativeResult
        }
        function Save-NativeFailureEvidence { return 'synthetic evidence destination' }
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS
        Require ($r.Commands.Count -eq 0 -and $r.Import -eq 'NOT RUN' -and $r.Native -eq 'NOT RUN' -and
            $r.Authorization -eq 'FAIL' -and $r.Infrastructure -eq 'FAIL') 'Inactive dispatch gate failed'
    }
    Check 'first-run approval and routine policy remain separate inactive stages' {
        Reject { Assert-NativeExecutionAuthorization } 'exact first run.*successful first-run validation.*separately owner-approved repository execution policy'
        foreach ($attempt in @(
            { Assert-NativeExecutionAuthorization -FirstRunApproved },
            { Assert-NativeExecutionAuthorization -Routine },
            { Assert-NativeExecutionAuthorization -ApprovalFile 'anything.json' })) {
            Reject $attempt 'parameter'
        }
    }
    Check 'runner has no online approval, expiration or approval-file input' {
        $text = Get-Content -Raw -LiteralPath "$PSScriptRoot/../tools/run-local-tests.ps1"
        Require ($text -notmatch 'Get-NativeApprovalApi|Get-Command gh|issuecomment|Read-Host|DateTimeOffset|approval\.json') 'Removed authorization machinery remains'
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseInput($text, [ref]$tokens, [ref]$errors)
        Require ($errors.Count -eq 0) 'Runner parse failed'
        Require (($ast.ParamBlock.Parameters.Name.VariablePath.UserPath -join ',') -ceq 'Mode,GodotPath,GodotSha256') 'Unexpected activation parameter'
    }
    Check 'offline reviewed-runner checks retain source and control-file protection' {
        $review = @{ ChangedRevision = $false; Dirty = $false }
        function Invoke-BoundedProcess {
            param($Executable, $Arguments)
            if ($Arguments[0] -ceq 'rev-parse') {
                return NativeResult $(if ($review.ChangedRevision) { 'b' * 40 } else { 'a' * 40 })
            }
            Require (($Arguments -join '|') -ceq "diff|--quiet|$('a' * 40)|--|tools|AGENTS.md|tests/static_*test.py") 'Reviewed controls changed'
            NativeResult '' '' $(if ($review.Dirty) { 'NONZERO_EXIT' } else { 'PASS' }) $(if ($review.Dirty) { 1 } else { 0 })
        }
        $root = Split-Path $PSScriptRoot -Parent
        Assert-ReviewedNativeRunner $root ('a' * 40)
        $review.ChangedRevision = $true
        Reject { Assert-ReviewedNativeRunner $root ('a' * 40) } 'revision changed'
        $review.ChangedRevision = $false; $review.Dirty = $true
        Reject { Assert-ReviewedNativeRunner $root ('a' * 40) } 'working changes'
        $review.Dirty = $false
        Reject { Assert-ReviewedNativeRunner $source ('a' * 40) } 'reviewed checkout runner'
    }
    $approvalIdentity = [pscustomobject]@{ Revision = ('a' * 40); Working = ''; Index = 'fixture'; Tracked = $tracked }
    $approvalStage = New-InputStage $source $fixture $tracked
    Check 'source changes since static-suite start deny even before approval' {
        function Get-ApprovedFirstRunContext { [pscustomobject]@{ Stage = $approvalStage } }
        function Get-NativeSourceIdentity { return $approvalIdentity }
        function New-InputStage { return $approvalStage }
        function Assert-NativeExecutionAuthorization { }
        function Save-NativeFailureEvidence { return 'synthetic evidence destination' }
        $oldIdentity = [pscustomobject]@{ Revision = ('b' * 40); Working = ''; Index = 'old' }
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS ([pscustomobject]@{ Identity = $oldIdentity; Inputs = @() })
        Require ($r.Commands.Count -eq 0 -and $r.Reason -eq 'DISPATCH_VALIDATION_OR_PROCESS_FAILURE' -and $r.Diagnostic -match 'since static-suite') 'Static source mutation accepted'
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS ([pscustomobject]@{ Identity = $approvalIdentity; Inputs = @() })
        Require ($r.Commands.Count -eq 0 -and $r.Diagnostic -match 'Working inputs changed since static-suite') 'Static working-byte mutation accepted'
    }
    Check 'public Native static failure prevents dispatch and approval' {
        function Assert-NativeExecutionAuthorization { }
        function Assert-PinnedEngine { }
        function Get-NativeSourceIdentity { return $approvalIdentity }
        function Invoke-RestrictedNativeDispatch { throw 'Failed static suite reached dispatch' }
        function Invoke-BoundedProcess {
            param($Executable, $Arguments, $Directory)
            $value = if ($Arguments[0] -eq 'rev-parse' -and $Arguments[1] -eq '--show-toplevel') { $Directory } else { '' }
            [pscustomobject]@{ Status = $(if ($Arguments[0] -eq '-B') { 'NONZERO_EXIT' } else { 'PASS' });
                ExitCode = $(if ($Arguments[0] -eq '-B') { 1 } else { 0 }); Bytes = 0; Excerpt = $value; TerminationCertain = $true }
        }
        Require ((Invoke-LocalTests $source Native $inertEngine $inertHash) -eq 1) 'Static failure accepted'
    }
    Check 'public Native passes actual static PASS and captured source snapshot to dispatch' {
        $state = @{ Dispatched = $false }
        function Assert-NativeExecutionAuthorization { }
        function Assert-PinnedEngine { }
        function Get-NativeSourceIdentity { return $approvalIdentity }
        function Invoke-BoundedProcess {
            param($Executable, $Arguments, $Directory)
            $value = if ($Arguments[0] -eq 'rev-parse' -and $Arguments[1] -eq '--show-toplevel') { $Directory } else { '' }
            [pscustomobject]@{ Status = 'PASS'; ExitCode = 0; Bytes = 0; Excerpt = $value; TerminationCertain = $true }
        }
        function Invoke-RestrictedNativeDispatch {
            param($Source, $Engine, $EngineHash, $StaticStatus, $StaticSnapshot)
            Require ($StaticStatus -ceq 'PASS' -and $StaticSnapshot.Identity.Revision -ceq $approvalIdentity.Revision -and $StaticSnapshot.Inputs.Count -eq 5) 'Static proof omitted'
            $state.Dispatched = $true
            [pscustomobject]@{ Import = 'PASS'; Native = 'PASS'; Reason = 'OK'; Evidence = ''; EvidenceError = '' }
        }
        Require ((Invoke-LocalTests $source Native $inertEngine $inertHash) -eq 0 -and $state.Dispatched) 'Static PASS not connected'
    }
    Check 'public Native mode cannot reach prerequisites, staging or execution' {
        $gateCalls = [Collections.Generic.List[string]]::new()
        function Assert-PlainPath { $gateCalls.Add('prerequisite'); throw 'Gate reached prerequisites' }
        function New-InputStage { $gateCalls.Add('stage'); throw 'Gate created a stage' }
        function Invoke-BoundedProcess { $gateCalls.Add('process'); throw 'Gate started a process' }
        $previous = [Environment]::GetEnvironmentVariable('TLWH_ALLOW_NATIVE')
        $env:TLWH_ALLOW_NATIVE = '1'
        try {
            Require ((Invoke-LocalTests $source Native $inertEngine $inertHash) -eq 1) 'Native gate bypassed'
            Require ($gateCalls.Count -eq 0) 'Gate had prohibited side effects'
        } finally { [Environment]::SetEnvironmentVariable('TLWH_ALLOW_NATIVE', $previous) }
    }
    Check 'context provider denies direct use and cannot load approval data' {
        Reject { Get-ApprovedFirstRunContext } 'inactive'
        Reject { Get-ApprovedFirstRunContext -ApprovalFile 'anything' } 'parameter'
        function Assert-NativeExecutionAuthorization { }
        function Assert-PinnedEngine { throw 'Inactive provider reached engine identity' }
        function Save-NativeFailureEvidence { 'synthetic evidence' }
        $r = Invoke-RestrictedNativeDispatch $source $inertEngine $inertHash PASS
        Require ($r.Diagnostic -match 'context inactive' -and $r.Commands.Count -eq 0 -and
            $r.Import -eq 'NOT RUN' -and $r.Native -eq 'NOT RUN') 'Provider bypassed'
    }
    Check 'exact scope binding rejects substitutions and changed controls' {
        $stage = New-InputStage $source $fixture $tracked
        $identity = [pscustomobject]@{ Revision = ('a' * 40); Working = ''; Index = 'fixture'; Tracked = $tracked }
        function Get-NativeSourceIdentity { $identity }
        $snapshot = [pscustomobject]@{ Identity = $identity; Inputs = $stage.Inputs }
        $scope = New-FirstRunReviewScope $inertEngine $inertHash $stage $snapshot
        $context = [pscustomobject]@{ Scope = $scope; Stage = $stage }
        Assert-FirstRunBinding $context $inertEngine $inertHash $stage $snapshot
        foreach ($field in @('Revision', 'Working', 'IndexSha256', 'RunnerPath', 'Source',
            'StageDirectory', 'EvidenceDirectory', 'ReceiptPath', 'StopConditions', 'RoutineAfterPass')) {
            $context.Scope = $scope | ConvertTo-Json -Depth 12 | ConvertFrom-Json
            $context.Scope.$field = 'substitution'
            Reject { Assert-FirstRunBinding $context $inertEngine $inertHash $stage $snapshot } 'scope changed'
        }
        $context.Scope = $scope | ConvertTo-Json -Depth 12 | ConvertFrom-Json
        $context.Scope.Commands[0].Seconds = 61
        Reject { Assert-FirstRunBinding $context $inertEngine $inertHash $stage $snapshot } 'scope changed'
        $context.Scope = $scope
        $otherStage = New-InputStage $source $fixture $tracked
        Reject { Assert-FirstRunBinding $context $inertEngine $inertHash $otherStage $snapshot } 'scope changed'
        $control = "$source/AGENTS.md"
        $original = [IO.File]::ReadAllBytes($control)
        try {
            [IO.File]::WriteAllText($control, 'changed control')
            Reject { Assert-FirstRunBinding $context $inertEngine $inertHash $stage $snapshot } 'scope changed'
        } finally { [IO.File]::WriteAllBytes($control, $original) }
    }
    Check 'exclusive consumption survives restart and preserves incomplete owner receipt' {
        $directory = Join-Path $fixture 'receipt-restart'
        $null = New-Item -ItemType Directory -Path $directory
        $scope = [pscustomobject]@{ EvidenceDirectory = $directory; ReceiptPath = (Join-Path $directory 'first-run-attempt.receipt') }
        New-FirstRunAttemptReceipt $scope
        $original = [IO.File]::ReadAllText($scope.ReceiptPath)
        Reject { New-FirstRunAttemptReceipt $scope } 'exists'
        $runner = (Resolve-Path "$PSScriptRoot/../tools/run-local-tests.ps1").Path.Replace("'", "''")
        $json = ($scope | ConvertTo-Json -Compress).Replace("'", "''")
        $code = ". '$runner'; try { New-FirstRunAttemptReceipt (ConvertFrom-Json '$json'); exit 7 } catch { exit 0 }"
        $encoded = [Convert]::ToBase64String([Text.Encoding]::Unicode.GetBytes($code))
        $r = Invoke-BoundedProcess $hostExe @('-NoProfile', '-EncodedCommand', $encoded) $fixture -Seconds 15
        Require ($r.Status -eq 'PASS' -and $r.ExitCode -eq 0) 'Restart replay accepted'
        Require ([IO.File]::ReadAllText($scope.ReceiptPath) -ceq $original) 'Receipt overwritten'
        $partial = Join-Path $fixture 'receipt-partial'
        $null = New-Item -ItemType Directory -Path $partial
        $scope.EvidenceDirectory = $partial; $scope.ReceiptPath = Join-Path $partial 'first-run-attempt.receipt'
        [IO.File]::WriteAllText($scope.ReceiptPath, '')
        Reject { New-FirstRunAttemptReceipt $scope } 'exists'
        Require ((Get-Item $scope.ReceiptPath).Length -eq 0) 'Uncertain receipt replaced'
        $scope.ReceiptPath = Join-Path $partial 'replacement.receipt'
        Reject { New-FirstRunAttemptReceipt $scope } 'Invalid'
    }
    Check 'concurrent separate processes consume exactly once' {
        $directory = Join-Path $fixture 'receipt-concurrent'
        $null = New-Item -ItemType Directory -Path $directory
        $scope = [pscustomobject]@{ EvidenceDirectory = $directory; ReceiptPath = (Join-Path $directory 'first-run-attempt.receipt') }
        $runner = (Resolve-Path "$PSScriptRoot/../tools/run-local-tests.ps1").Path
        $jobs = @(1..3 | ForEach-Object {
            Start-Job -ScriptBlock {
                param($Runner, $Scope)
                . $Runner
                try { New-FirstRunAttemptReceipt $Scope; 'CONSUMED' } catch { 'DENIED' }
            } -ArgumentList $runner, $scope
        })
        try {
            $done = @($jobs | Wait-Job -Timeout 20)
            Require ($done.Count -eq 3) 'Concurrent fixture did not terminate'
            $results = @($jobs | Receive-Job -ErrorAction Stop)
            Require (@($results | Where-Object { $_ -ceq 'CONSUMED' }).Count -eq 1 -and
                @($results | Where-Object { $_ -ceq 'DENIED' }).Count -eq 2) 'Concurrent replay permitted'
        } finally { $jobs | Stop-Job; $jobs | Remove-Job }
    }
} finally {
    # Only this freshly created, inert fixture tree. No project files or prior temp files.
    $resolved = [IO.Path]::GetFullPath($fixture)
    $expectedParent = [IO.Path]::GetFullPath([IO.Path]::GetTempPath()).TrimEnd('\', '/')
    if ([IO.Path]::GetDirectoryName($resolved) -ne $expectedParent -or
        [IO.Path]::GetFileName($resolved) -notmatch '^tlwh-runner-fixture-[0-9a-f]{32}$') { throw 'Unsafe fixture cleanup target' }
    Assert-PlainPath $resolved
    Remove-Item -LiteralPath $resolved -Recurse -Force
}
Write-Host "Fixtures: $passed PASS, $failed FAIL. Godot import/test: NOT RUN."
if ($failed) { exit 1 }
