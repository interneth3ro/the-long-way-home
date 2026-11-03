param([switch]$Check)
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$studyRoot = $PSScriptRoot
$projectRoot = (Resolve-Path (Join-Path $studyRoot '../../..')).Path
$outputPath = Join-Path $studyRoot 'previews/context_05x.png'
$receiptPath = Join-Path $studyRoot 'context-provenance.json'
if (-not $Check -and ((Test-Path -LiteralPath $outputPath) -or (Test-Path -LiteralPath $receiptPath))) { throw 'Context output exists; preserve it.' }
$paths = @{
    baseline = 'artifacts/tmp/terrain_fidelity_a1/baseline.png'
    candidate = 'artifacts/tmp/terrain_fidelity_a1/candidate.png'
    ship = 'assets/environment/exterior/crashed_exploration_ship_approved.png'
    shadow = 'assets/environment/exterior/crashed_ship_contact_shadow_prototype.png'
    ferrite = 'assets/environment/exterior/ferrite/faceted_ferrite_10x6.png'
}
$loaded = @{}
$records = @{}
try {
    foreach ($name in $paths.Keys) {
        $path = Join-Path $projectRoot $paths[$name]
        $loaded[$name] = [System.Drawing.Bitmap]::FromFile($path)
        $records[$name] = @{ path=$paths[$name]; sha256=(Get-FileHash -LiteralPath $path).Hash.ToLowerInvariant(); width=$loaded[$name].Width; height=$loaded[$name].Height }
    }
    if ($Check) {
        $saved = Get-Content -LiteralPath $receiptPath -Raw | ConvertFrom-Json
        foreach ($name in $paths.Keys) {
            if ($saved.inputs.$name.sha256 -ne $records[$name].sha256) { throw "Changed context input: $name" }
        }
        if ($saved.output_sha256 -ne (Get-FileHash -LiteralPath $outputPath).Hash.ToLowerInvariant()) { throw 'Changed context output' }
        Write-Output 'Context input/output hashes PASS; no Godot.'
    } else {
        $canvas = New-Object System.Drawing.Bitmap(1456, 602)
        $graphics = [System.Drawing.Graphics]::FromImage($canvas)
        $font = New-Object System.Drawing.Font('Arial', 10)
        try {
            $graphics.Clear([System.Drawing.Color]::FromArgb(23,30,28))
            $graphics.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBilinear
            $graphics.DrawString('A1 OFFLINE ILLUSTRATIVE COMPOSITE / 0.5x / NEUTRAL TINT / NOT A RUNTIME SCREENSHOT', $font, [System.Drawing.Brushes]::White, 16, 8)
            $graphics.DrawString('BASELINE', $font, [System.Drawing.Brushes]::White, 16, 30)
            $graphics.DrawString('CANDIDATE / IDENTICAL OBJECT SCALES', $font, [System.Drawing.Brushes]::White, 736, 30)
            $panelIndex = 0
            foreach ($name in @('baseline','candidate')) {
                $panelX = 16 + $panelIndex*720
                $graphics.DrawImage($loaded[$name], [System.Drawing.RectangleF]::new($panelX,56,704,512))
                # Documented source-to-world scales, then 0.5 gameplay-equivalent zoom.
                $graphics.DrawImage($loaded.shadow, [System.Drawing.RectangleF]::new($panelX,56,$loaded.shadow.Width*.35,$loaded.shadow.Height*.35))
                $graphics.DrawImage($loaded.ship, [System.Drawing.RectangleF]::new($panelX+16,62,$loaded.ship.Width*.35,$loaded.ship.Height*.35))
                $graphics.DrawImage($loaded.ferrite, [System.Drawing.RectangleF]::new($panelX+336,330,$loaded.ferrite.Width*.25,$loaded.ferrite.Height*.25))
                $panelIndex++
            }
            $graphics.DrawString('Fixtures use a simple Earth/Green split. No authored crash-site tint, lighting, collision or gameplay is reproduced.', $font, [System.Drawing.Brushes]::White, 16, 578)
            $canvas.Save($outputPath, [System.Drawing.Imaging.ImageFormat]::Png)
        } finally { $font.Dispose(); $graphics.Dispose(); $canvas.Dispose() }
        $receipt = @{ inputs=$records; output_sha256=(Get-FileHash -LiteralPath $outputPath).Hash.ToLowerInvariant(); dimensions=@(1456,602); world_scales=@{ship=.70; shadow=.70; ferrite=.50}; zoom=.50; method='System.Drawing offline composition, bilinear resizing; documented object scales; no runtime tint'; reproduction='Run author.py --write in a fresh output copy to recreate temporary grounds, then run this script. Fonts/GDI may affect encoded output across hosts.' }
        $receipt | ConvertTo-Json -Depth 6 | Set-Content -LiteralPath $receiptPath -Encoding utf8
        Write-Output 'Offline context composite created; no Godot.'
    }
} finally { foreach ($item in $loaded.Values) { $item.Dispose() } }
