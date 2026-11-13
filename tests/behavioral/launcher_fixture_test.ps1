#requires -Version 7.0
# Inert fixtures only: no Godot, engine lookup, staging, project execution or files.
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
$good = 'TLWH_BEHAVIORAL_V1 PASS groups=1 checks=4 failures=0'

Check 'launcher and fixture parse; launcher has no override parameters' {
    foreach ($path in @("$PSScriptRoot/../../tools/run-behavioral-tests.ps1", $PSCommandPath)) {
        $tokens = $null; $errors = $null
        $ast = [Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
        Require ($errors.Count -eq 0) 'PowerShell parse errors'
        if ($path -ne $PSCommandPath) { Require ($ast.ParamBlock.Parameters.Count -eq 0) 'Override parameter added' }
    }
}
Check 'inactive gate stops before engine identity or process operations' {
    function Get-StandardGodotIdentity { throw 'Unexpected engine identity lookup' }
    function Assert-PinnedEngine { throw 'Unexpected engine hash lookup' }
    function Invoke-BoundedProcess { throw 'Unexpected process launch' }
    $output = @(Invoke-BehavioralTests 6>&1)
    Require ($output[-1] -eq 1) 'Denied invocation returned success'
    Require (($output -join "`n") -match 'Behavioral: NOT RUN') 'NOT RUN missing'
    Require (($output -join "`n") -match 'AUTHORIZATION_DENIED') 'Gate did not deny first'
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
Check 'production gate remains inactive after scoped doubles' {
    try { Assert-BehavioralExecutionAuthorized; throw 'Gate unexpectedly returned' }
    catch { Require ($_ -match 'AUTHORIZATION_DENIED') 'Production gate changed' }
}
Write-Host "Behavioral launcher fixtures: $passed PASS, $failed FAIL. Godot: NOT RUN."
if ($failed) { exit 1 }
