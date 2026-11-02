$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Drawing
$proofRoot = $PSScriptRoot
$manifest = Get-Content -LiteralPath (Join-Path $proofRoot 'manifest.json') -Raw | ConvertFrom-Json
$script:proofFont = [System.Drawing.Font]::new('Segoe UI', 11)
$script:proofBold = [System.Drawing.Font]::new('Segoe UI', 12, [System.Drawing.FontStyle]::Bold)
$script:proofTitle = [System.Drawing.Font]::new('Segoe UI', 25, [System.Drawing.FontStyle]::Bold)
$script:proofMono = [System.Drawing.Font]::new('Consolas', 10)
$script:white = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(235,239,237))
$script:muted = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(172,186,180))
$script:panel = [System.Drawing.SolidBrush]::new([System.Drawing.Color]::FromArgb(35,44,41))

function New-Board([int]$width, [int]$height) {
    $script:board = [System.Drawing.Bitmap]::new($width,$height)
    $script:draw = [System.Drawing.Graphics]::FromImage($script:board)
    $script:draw.Clear([System.Drawing.Color]::FromArgb(19,26,23))
    $script:draw.TextRenderingHint = [System.Drawing.Text.TextRenderingHint]::AntiAliasGridFit
    $script:draw.InterpolationMode = [System.Drawing.Drawing2D.InterpolationMode]::HighQualityBicubic
    $script:draw.PixelOffsetMode = [System.Drawing.Drawing2D.PixelOffsetMode]::HighQuality
}
function Text([string]$text,[single]$x,[single]$y,[string]$style='normal') {
    $font = switch ($style) { 'title' {$script:proofTitle} 'bold' {$script:proofBold} 'mono' {$script:proofMono} default {$script:proofFont} }
    $brush = if ($style -eq 'muted') {$script:muted} else {$script:white}
    $script:draw.DrawString($text,$font,$brush,$x,$y)
}
function Picture([string]$relative,[single]$x,[single]$y,[single]$width,[single]$height) {
    $inputImage = [System.Drawing.Image]::FromFile((Join-Path $proofRoot $relative))
    try {
        $scale = [Math]::Min($width/$inputImage.Width,$height/$inputImage.Height)
        $rectangle = [System.Drawing.RectangleF]::new($x,$y,($inputImage.Width*$scale),($inputImage.Height*$scale))
        $script:draw.DrawImage($inputImage,$rectangle)
    } finally { $inputImage.Dispose() }
}
function Save-Board([string]$name) {
    $destination = Join-Path $proofRoot $name
    if (Test-Path -LiteralPath $destination) { throw "Preserve existing board: $destination" }
    $script:board.Save($destination,[System.Drawing.Imaging.ImageFormat]::Png)
    $script:draw.Dispose()
    $script:board.Dispose()
}

try {
    New-Board 1320 1370
    Text 'TLWH / native terrain artwork proof' 26 16 'title'
    Text 'Stage 1 only | 20 representative 128px tiles | 40 of 94 signatures exercised | no engine integration' 28 62 'muted'
    Text 'WEATHERED EARTH CENTER (0)' 28 94 'bold'
    Text 'LOW GREEN COVER CENTER (1)' 688 94 'bold'
    for ($index=0; $index -lt 20; $index++) {
        $family = [Math]::Floor($index/10)
        $local = $index%10
        $column = ($local%2)+2*$family
        $row = [Math]::Floor($local/2)
        $x = 20+$column*330
        $y = 128+$row*238
        $entry = $manifest.representatives[$index]
        $script:draw.FillRectangle($script:panel,[int]$x,[int]$y,310,220)
        Text (($entry.name -replace '_',' / ')) ($x+12) ($y+9) 'bold'
        Picture $entry.image ($x+12) ($y+40) 128 128
        Picture $entry.mask ($x+166) ($y+56) 96 96
        Text 'ART 128px' ($x+22) ($y+171) 'muted'
        Text 'MASK' ($x+192) ($y+158) 'muted'
        $signature = @($entry.signature)
        $peers = ($signature[1..8] -join '')
        Text ('C='+$signature[0]+'  peers='+$peers+'  cell=('+($entry.original_atlas -join ',')+')') ($x+10) ($y+198) 'mono'
    }
    Text 'Mask: black=Earth, white=Green. Peer order: NW,N,NE,W,E,SW,S,SE. Original inventory coordinates.' 28 1332 'muted'
    Save-Board 'representatives.png'

    New-Board 1640 970
    Text 'Approved study / native-signature proof' 26 16 'title'
    Text 'Same approved texture sources; different illustrative layouts. Reference geometry is not a verified native terrain mapping.' 28 62 'muted'
    Text 'APPROVED PACKAGE PREVIEW (REFERENCE)' 28 98 'bold'
    Text 'OFFLINE COONS-SURFACE PROOF (PROPOSED)' 846 98 'bold'
    Picture 'references/assembled_12x10_preview.png' 28 132 760 634
    Picture 'previews/meandering_boundary_varied.png' 846 132 760 634
    Text 'Original supplied neighborhood-mask study, unchanged.' 28 776 'muted'
    Text 'Actual native signatures; soft contour mask; A/B/C texture alternatives.' 846 656 'muted'
    Text 'Remaining limits: visible source repetition, grid influence and occasional small corner pockets.' 846 686 'muted'
    Picture 'representatives/earth_solid_9_2.png' 28 820 128 128
    Picture 'representatives/green_solid_9_6.png' 176 820 128 128
    Text 'Source materials preserved.' 332 827 'bold'
    Text 'No palette replacement, machinery, vegetation or overlays conceal the ground.' 332 860 'muted'
    Text 'All compositing is baked into PNG files. TileSets, scenes and production rendering are untouched.' 332 890 'muted'
    Text 'Visual approval is pending; exact edge pixels do not establish contour quality or Godot behavior.' 332 920 'muted'
    Save-Board 'comparison.png'

    New-Board 1600 754
    Text 'Interior repetition / three seam-compatible alternatives' 24 14 'title'
    Text 'A = original. B/C = source-derived interior mixtures; edge pixels remain unchanged. No color tint or new painted material.' 26 60 'muted'
    Text 'EARTH / ORIGINAL A REPEATED' 24 96 'bold'
    Text 'EARTH / MIXED A, B, C' 820 96 'bold'
    Picture 'previews/earth_repeat_a.png' 24 128 768 256
    Picture 'previews/earth_repeat_abc.png' 820 128 768 256
    Text 'GREEN / ORIGINAL A REPEATED' 24 406 'bold'
    Text 'GREEN / MIXED A, B, C' 820 406 'bold'
    Picture 'previews/green_repeat_a.png' 24 438 768 256
    Picture 'previews/green_repeat_abc.png' 820 438 768 256
    Text 'Result: motifs are less identical, but large-scale repetition remains visible. B/C can slightly soften texture contrast.' 26 714 'muted'
    Save-Board 'variations.png'
} finally {
    $script:proofFont.Dispose(); $script:proofBold.Dispose(); $script:proofTitle.Dispose(); $script:proofMono.Dispose()
    $script:white.Dispose(); $script:muted.Dispose(); $script:panel.Dispose()
}
Write-Output 'Created representative sheet, approved-study comparison and repetition comparison.'
