#requires -Version 7.0
# Inert fixtures only: no Godot, executable access, staging or file writes.
$ErrorActionPreference = 'Stop'
. "$PSScriptRoot/../../tools/run-behavioral-tests.ps1"
$passed = 0
$failed = 0
function Check([string]$Name, [scriptblock]$Body) {
    try { & $Body; $script:passed++; Write-Host "PASS $Name" }
    catch { $script:failed++; Write-Host "FAIL ${Name}: $_" }
}
function Require($Condition, [string]$Message) { if (-not $Condition) { throw $Message } }
function Result([string]$Stdout = '', [string]$Stderr = '', [string]$Status = 'PASS',
                $ExitCode = 0, [bool]$Certain = $true) {
    [pscustomobject]@{ Stdout = $Stdout; Stderr = $Stderr; Status = $Status;
        ExitCode = $ExitCode; TerminationCertain = $Certain; Excerpt = 'inert diagnostic';
        Bytes = [Text.Encoding]::UTF8.GetByteCount($Stdout + $Stderr) }
}
$completion = 'TLWH_BEHAVIORAL_V1 PASS groups=1 checks=4 failures=0'
$group = 'TLWH_BEHAVIORAL_GROUP_V1 world_coordinates PASS checks=4'
$good = "$group`n$completion"

Check 'launcher and fixture parse; launcher has no override parameters' {
    foreach ($path in @("$PSScriptRoot/../../tools/run-behavioral-tests.ps1", $PSCommandPath)) {
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
        Require ($errors.Count -eq 0) 'PowerShell parse errors'
        if ($path -ne $PSCommandPath) { Require ($ast.ParamBlock.Parameters.Count -eq 0) 'Override parameter added' }
    }
}
Check 'denied authorization stops before engine identity or process operations' {
    function Assert-BehavioralExecutionAuthorized { throw 'AUTHORIZATION_DENIED: inert withdrawal' }
    function Get-StandardGodotIdentity { throw 'Unexpected engine identity lookup' }
    function Assert-PinnedEngine { throw 'Unexpected engine hash lookup' }
    function Invoke-BoundedProcess { throw 'Unexpected process launch' }
    $output = @(Invoke-BehavioralTests 6>&1)
    Require ($output[-1] -eq 1) 'Denied invocation returned success'
    Require (($output -join "`n") -match 'Behavioral: NOT RUN') 'NOT RUN missing'
    Require (($output -join "`n") -match 'AUTHORIZATION_DENIED') 'Gate did not deny first'
}
Check 'fixed identity remains the reviewed executable and SHA-256 without executable access' {
    $identity = Get-StandardGodotIdentity
    Require ($identity.Path -ceq 'D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe') 'Pinned path changed'
    Require ($identity.Sha256 -ceq 'AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424') 'Pinned hash changed'
}
Check 'production gate is a single denial or reviewed standing return' {
    $gate = [scriptblock]::Create((Get-Command Assert-BehavioralExecutionAuthorized).ScriptBlock.ToString()).Ast
    Require ($gate.EndBlock.Statements.Count -eq 1) 'Gate gained executable statements'
    $statement = $gate.EndBlock.Statements[0]
    Require (($statement -is [Management.Automation.Language.ThrowStatementAst] -and
        $statement.Extent.Text -ceq "throw 'AUTHORIZATION_DENIED: local behavioral execution is inactive; separate owner approval and a reviewed activation amendment are required.'") -or
        ($statement -is [Management.Automation.Language.ReturnStatementAst] -and
        $statement.Extent.Text -ceq 'return')) 'Unexpected authorization mechanism'
    # Shape validation is not owner approval. Both forms remain inert in fixtures.
}
Check 'proposed two-group manifest is explicit; approved four coordinate checks stay unchanged' {
    # Small scope guard only, not a GDScript parser or proof of assertion behavior.
    # Changes to the manifest/assertions still require separate review and authorization.
    $dispatcher = Get-Content -LiteralPath "$PSScriptRoot/test_runner.gd" -Raw
    $smoke = Get-Content -LiteralPath "$PSScriptRoot/smoke_test.gd" -Raw
    $manifest = [regex]::Match($dispatcher, '(?s)const\s+GROUPS\s*:=\s*\[(.*?)\]')
    $expectedManifest = @(
        '{"name":"world_coordinates","script":preload("res://tests/behavioral/smoke_test.gd")},'
        '{"name":"resource_generation_v2","script":preload("res://tests/behavioral/resource_generation_v2_test.gd")},'
    ) -join ''
    Require ($manifest.Success -and ($manifest.Groups[1].Value -replace '\s', '') -ceq $expectedManifest) 'Proposed two-entry manifest changed'
    # Recognizing the proposal is not approval to execute the expanded manifest.

    $cases = [regex]::Match($smoke, '(?s)var\s+cases\s*:=\s*\[(.*?)\]')
    $expectedCases = @(
        '{"point":Vector2(-0.01,-32.01),"expected":Vector2i(-1,-2)},'
        '{"point":Vector2(-32,-64),"expected":Vector2i(-1,-2)},'
        '{"point":Vector2(31.99,32),"expected":Vector2i(0,1)},'
        '{"point":Vector2(32,64),"expected":Vector2i(1,2)},'
    ) -join ''
    Require ($cases.Success -and ($cases.Groups[1].Value -replace '\s', '') -ceq $expectedCases) 'Approved four boundary cases changed'
    Require ($smoke -match 'const\s+Coordinates\s*=\s*preload\("res://scenes/world/world_coordinates\.gd"\)') 'Production coordinate dependency changed'
    Require ($smoke -match 'Coordinates\.world_to_construction\(vector\.point\)') 'Production coordinate call missing'
}
Check 'valid completion accepts LF CRLF and harmless engine banner' {
    foreach ($stdout in @($good, "$good`n", "Godot inert banner`r`n$good`r`n")) {
        Require ((Get-BehavioralFailure (Result $stdout)) -ceq '') 'Valid completion rejected'
    }
}
Check 'completion is required unique final on stdout and zero-failure' {
    foreach ($stdout in @('', 'TLWH_BEHAVIORAL_V1 FAIL groups=0 checks=4 failures=1',
            'TLWH_BEHAVIORAL_V1 PASS groups=0 checks=4 failures=0',
            'TLWH_BEHAVIORAL_V1 PASS groups=1 checks=0 failures=0',
            'TLWH_BEHAVIORAL_V1 PASS groups=1 checks=4 failures=1',
            "$good`n$good", "$good`ntrailing", "prefix $good")) {
        Require ((Get-BehavioralFailure (Result $stdout)) -ne '') 'Invalid completion accepted'
    }
    Require ((Get-BehavioralFailure (Result '' $good)) -ne '') 'Stderr-only completion accepted'
    Require ((Get-BehavioralFailure (Result $good $good)) -ne '') 'Cross-stream duplicate accepted'
    Require ((Get-BehavioralFailure (Result "TLWH_BEHAVIORAL_GROUP_V1 world_coordinates FAIL`n$good")) -ne '') 'Contradictory group failure accepted'
}
Check 'completion reconciles exact group count and total checks' {
    $other = 'TLWH_BEHAVIORAL_GROUP_V1 synthetic_second PASS checks=3'
    $twoGroups = "$group`n$other`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=7 failures=0"
    Require ((Get-BehavioralFailure (Result $twoGroups)) -ceq '') 'Valid synthetic group sum rejected'
    foreach ($stdout in @($completion,
            "$group`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=4 failures=0",
            "$group`nTLWH_BEHAVIORAL_V1 PASS groups=1 checks=5 failures=0",
            "$group`n$other`nTLWH_BEHAVIORAL_V1 PASS groups=1 checks=7 failures=0",
            "$group`n$other`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=6 failures=0")) {
        Require ((Get-BehavioralFailure (Result $stdout)) -ne '') 'Mismatched group/check counts accepted'
    }
}
Check 'duplicate contradictory and malformed group records cannot produce PASS' {
    foreach ($stdout in @("$group`n$good",
            "$group`n$group`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=8 failures=0",
            "$group`nTLWH_BEHAVIORAL_GROUP_V1 world_coordinates PASS checks=3`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=7 failures=0",
            "prefix $good", "$group extra`n$completion",
            "TLWH_BEHAVIORAL_GROUP_V1 world_coordinates PASS checks=0`n$completion",
            "$group`nTLWH_BEHAVIORAL_GROUP_V1 world_coordinates FAIL`n$completion")) {
        Require ((Get-BehavioralFailure (Result $stdout)) -ne '') 'Invalid or repeated group accepted'
    }
    Require ((Get-BehavioralFailure (Result $good $group)) -ne '') 'Cross-stream group duplicate accepted'
    Require ((Get-BehavioralFailure (Result $completion $group)) -ne '') 'Stderr group substituted for stdout group'
}
Check 'completion and group totals reject out-of-range counts without overflow' {
    foreach ($stdout in @("$group`nTLWH_BEHAVIORAL_V1 PASS groups=9223372036854775808 checks=4 failures=0",
            "$group`nTLWH_BEHAVIORAL_V1 PASS groups=1 checks=9223372036854775808 failures=0",
            "TLWH_BEHAVIORAL_GROUP_V1 huge PASS checks=9223372036854775808`n$completion",
            "TLWH_BEHAVIORAL_GROUP_V1 huge PASS checks=9223372036854775807`n$group`nTLWH_BEHAVIORAL_V1 PASS groups=2 checks=4 failures=0")) {
        Require ((Get-BehavioralFailure (Result $stdout)) -ne '') 'Out-of-range count accepted'
    }
}
Check 'exit-zero engine errors and every process failure remain failures' {
    foreach ($result in @((Result $good 'SCRIPT ERROR: inert'), (Result $good 'Parse Error: inert'),
            (Result $good 'ERROR: inert'), (Result $good 'Assertion failed'),
            (Result $good '' PASS 1), (Result $good '' NONZERO_EXIT 7),
            (Result $good '' TIMEOUT $null $false), (Result $good '' OUTPUT_LIMIT $null $false),
            (Result $good '' PASS 0 $false))) {
        Require ((Get-BehavioralFailure $result) -ne '') 'Process failure accepted'
    }
    $over = Result $good
    $over.Bytes = 1048577
    Require ((Get-BehavioralFailure $over) -ne '') 'Reported output overflow accepted'
    Require ((Get-BehavioralFailure (Result ('x' * 1048576) $good)) -ne '') 'Actual output overflow accepted'
}
Check 'proposed path checks identity then dispatches one fixed bounded command' {
    $events = [Collections.Generic.List[string]]::new()
    function Assert-BehavioralExecutionAuthorized { $events.Add('gate-double') }
    function Get-StandardGodotIdentity {
        $events.Add('identity-double')
        [pscustomobject]@{ Path = 'INERT-NEVER-LAUNCHED'; Sha256 = 'inert' }
    }
    function Assert-PinnedEngine($Engine, $EngineHash) {
        Require ($Engine -ceq 'INERT-NEVER-LAUNCHED' -and $EngineHash -ceq 'inert') 'Identity changed'
        $events.Add('pin-double')
    }
    function Invoke-BoundedProcess($Executable, $Arguments, $Directory, $Seconds, $MaxBytes, $ExcerptBytes) {
        $events.Add('process-double')
        Require ($Executable -ceq 'INERT-NEVER-LAUNCHED') 'Unexpected executable'
        Require ($Directory -ceq (Split-Path (Split-Path $PSScriptRoot -Parent) -Parent)) 'Not actual checkout'
        Require (($Arguments -join '|') -ceq "--headless|--path|$Directory|--script|res://tests/behavioral/test_runner.gd") 'Command override or extra phase'
        Require ($Seconds -eq 30 -and $MaxBytes -eq 1048576 -and $ExcerptBytes -eq 4096) 'Bounds changed'
        Result $good
    }
    Require ((Invoke-BehavioralTests) -eq 0) 'Synthetic success failed'
    Require (($events -join '|') -ceq 'gate-double|identity-double|pin-double|process-double') 'Wrong order or retry'
    $events.Clear()
    function Invoke-BoundedProcess { $events.Add('process-double'); Result $good '' NONZERO_EXIT 7 }
    Require ((Invoke-BehavioralTests) -eq 1) 'Synthetic failure accepted'
    Require (@($events | Where-Object { $_ -ceq 'process-double' }).Count -eq 1) 'Failure retried'
}
Check 'standing return permits routine calls; failures never retry; withdrawal stops dispatch' {
    $productionGate = (Get-Command Assert-BehavioralExecutionAuthorized).ScriptBlock.ToString()
    & {
        # In-memory future activation only; all engine operations remain doubles.
        function Assert-BehavioralExecutionAuthorized { return }
        function Get-StandardGodotIdentity { [pscustomobject]@{ Path = 'INERT'; Sha256 = 'inert' } }
        function Assert-PinnedEngine { }
        $attempts = [Collections.Generic.List[string]]::new()
        function Invoke-BoundedProcess {
            $attempts.Add('inert')
            if ($outcome -ceq 'EXCEPTION') { throw 'inert process exception' }
            if ($outcome -ceq 'PASS') { return (Result $good) }
            Result $good '' $outcome 1 ($outcome -ceq 'NONZERO_EXIT')
        }
        # Separate routine calls do not consume a one-use grant.
        $outcome = 'PASS'
        foreach ($invocation in 1..2) {
            $output = @(Invoke-BehavioralTests 6>&1)
            Require ($output[-1] -eq 0 -and $attempts.Count -eq $invocation) 'Routine invocation denied or retried'
        }
        foreach ($outcome in @('NONZERO_EXIT', 'TIMEOUT', 'OUTPUT_LIMIT', 'EXCEPTION')) {
            $attempts.Clear()
            $output = @(Invoke-BehavioralTests 6>&1)
            Require ($output[-1] -eq 1 -and $attempts.Count -eq 1) 'Failure accepted or retried'
        }
        function Assert-BehavioralExecutionAuthorized { throw 'AUTHORIZATION_DENIED: inert withdrawal' }
        $attempts.Clear()
        $output = @(Invoke-BehavioralTests 6>&1)
        Require ($output[-1] -eq 1 -and ($output -join "`n") -match 'AUTHORIZATION_DENIED') 'Withdrawal ignored'
        Require ($attempts.Count -eq 0) 'Withdrawn authorization dispatched'
    }
    Require ((Get-Command Assert-BehavioralExecutionAuthorized).ScriptBlock.ToString() -ceq $productionGate) 'Scoped doubles changed production gate'
}
Write-Host "Behavioral launcher fixtures: $passed PASS, $failed FAIL. Godot: NOT RUN."
if ($failed) { exit 1 }
