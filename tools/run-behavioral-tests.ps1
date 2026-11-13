#requires -Version 7.0
[CmdletBinding()]
param()

# Definitions only: reuse the bounded process helper and fixed engine identity.
# Dot-sourcing does not dispatch the existing runner or create an external stage.
. "$PSScriptRoot/run-local-tests.ps1"

function Assert-BehavioralExecutionAuthorized {
    throw 'AUTHORIZATION_DENIED: local behavioral execution is inactive; separate owner approval and a reviewed activation amendment are required.'
}

function Get-BehavioralFailure($Result) {
    if ($Result.Status -cne 'PASS' -or $Result.ExitCode -ne 0 -or -not $Result.TerminationCertain) {
        return "Process failed: $($Result.Status); exit=$($Result.ExitCode); termination certain=$($Result.TerminationCertain)"
    }
    $bytes = [Text.Encoding]::UTF8.GetByteCount($Result.Stdout) + [Text.Encoding]::UTF8.GetByteCount($Result.Stderr)
    if ($Result.Bytes -gt 1048576 -or $bytes -gt 1048576) {
        return 'Output limit exceeded.'
    }
    $output = $Result.Stdout + "`n" + $Result.Stderr
    if ($output -match '(?im)\b(ERROR|SCRIPT ERROR|parse error|assertion failed|assertion failure)\b') {
        return 'Engine/script error reported, including with exit zero.'
    }
    if ($output -cmatch '(?m)^TLWH_BEHAVIORAL_GROUP_V1 [^\r\n]* FAIL\b') {
        return 'A test group reported failure.'
    }
    $records = [regex]::Matches($output, 'TLWH_BEHAVIORAL_V1[^\r\n]*')
    $lines = @($Result.Stdout -split '\r?\n' | Where-Object { -not [string]::IsNullOrWhiteSpace($_) })
    if ($records.Count -ne 1 -or $lines.Count -eq 0) {
        return 'Missing, failed, malformed, duplicate or misplaced completion record.'
    }
    $completion = [regex]::Match($lines[-1], '^TLWH_BEHAVIORAL_V1 PASS groups=([1-9][0-9]*) checks=([1-9][0-9]*) failures=0$')
    [long]$expectedGroups = 0
    [long]$expectedChecks = 0
    if (-not $completion.Success -or
        -not [long]::TryParse($completion.Groups[1].Value, [ref]$expectedGroups) -or
        -not [long]::TryParse($completion.Groups[2].Value, [ref]$expectedChecks)) {
        return 'Malformed completion counts.'
    }
    if ($Result.Stderr.Contains('TLWH_BEHAVIORAL_GROUP_V1')) {
        return 'Group records must be on stdout.'
    }
    $seen = [Collections.Generic.HashSet[string]]::new([StringComparer]::Ordinal)
    [long]$totalChecks = 0
    foreach ($line in $lines | Where-Object { $_.Contains('TLWH_BEHAVIORAL_GROUP_V1') }) {
        $group = [regex]::Match($line, '^TLWH_BEHAVIORAL_GROUP_V1 (\S+) PASS checks=([1-9][0-9]*)$')
        if (-not $group.Success -or -not $seen.Add($group.Groups[1].Value)) {
            return 'Malformed, duplicate or contradictory group record.'
        }
        [long]$checks = 0
        if (-not [long]::TryParse($group.Groups[2].Value, [ref]$checks) -or
            $checks -gt [long]::MaxValue - $totalChecks) {
            return 'Group check count exceeds the supported range.'
        }
        $totalChecks += $checks
    }
    if ($seen.Count -ne $expectedGroups -or $totalChecks -ne $expectedChecks) {
        return 'Completion counts disagree with group PASS records.'
    }
    return ''
}

function Invoke-BehavioralTests {
    try {
        Assert-BehavioralExecutionAuthorized
        $root = Split-Path $PSScriptRoot -Parent
        $identity = Get-StandardGodotIdentity
        Assert-PinnedEngine $identity.Path $identity.Sha256
    } catch {
        Write-Host 'Behavioral: NOT RUN'
        $message = $_.Exception.Message
        Write-Host $message.Substring(0, [Math]::Min(4096, $message.Length))
        return 1
    }
    try {
        # Exactly one process in the actual checkout. No import phase or retries.
        $result = Invoke-BoundedProcess $identity.Path @('--headless', '--path', $root,
            '--script', 'res://tests/behavioral/test_runner.gd') $root -Seconds 30 -MaxBytes 1048576 -ExcerptBytes 4096
        $failure = Get-BehavioralFailure $result
        if ($failure) {
            Write-Host "Behavioral: FAIL — $failure"
            Write-Host $result.Excerpt
            return 1
        }
        Write-Host 'Behavioral: PASS'
        Write-Host $result.Stdout.TrimEnd()
        return 0
    } catch {
        Write-Host 'Behavioral: FAIL — process attempt or result handling failed.'
        $message = $_.Exception.Message
        Write-Host $message.Substring(0, [Math]::Min(4096, $message.Length))
        return 1
    }
}

if ($MyInvocation.InvocationName -ne '.') {
    exit (Invoke-BehavioralTests)
}
