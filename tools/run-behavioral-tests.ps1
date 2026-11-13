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
    if ($records.Count -ne 1 -or $lines.Count -eq 0 -or
        $lines[-1] -cnotmatch '^TLWH_BEHAVIORAL_V1 PASS groups=[1-9][0-9]* checks=[1-9][0-9]* failures=0$') {
        return 'Missing, failed, malformed, duplicate or misplaced completion record.'
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
