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
                ExitCode = $(if ($Arguments[0] -eq '-B') { 1 } else { 0 }); Bytes = $value.Length; Excerpt = $value }
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
            [pscustomobject]@{ Status = 'PASS'; ExitCode = 0; Bytes = $value.Length; Excerpt = $value }
        }
        Require ((Invoke-LocalTests $source 'NativePlan' $hostExe (Get-FileHash $hostExe).Hash) -eq 0) 'Plan failed'
    }
    $nativeStage = New-InputStage $source $fixture $tracked
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
    Check 'stage mutations and unexpected hidden directories refused' {
        [IO.File]::WriteAllText("$($nativeStage.Directory)/project.godot", 'changed stage')
        Reject { New-NativeCommandPlan $inertEngine $inertHash $nativeStage } 'changed'
        [IO.File]::Copy("$source/project.godot", "$($nativeStage.Directory)/project.godot", $true)
        $null = New-Item -ItemType Directory -Path "$($nativeStage.Directory)/.godot"
        Reject { New-NativeCommandPlan $inertEngine $inertHash $nativeStage } 'Unexpected staged directory'
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
