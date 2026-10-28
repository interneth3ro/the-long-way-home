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
