param([switch]$Check)
$ErrorActionPreference = 'Stop'
$root = Split-Path $PSScriptRoot -Parent
$geometryArgs = @('-B', (Join-Path $PSScriptRoot 'ferrite-catalog.py'))
if ($Check) { $geometryArgs += '--check' }
& python @geometryArgs
if ($LASTEXITCODE -ne 0) { throw 'Catalog geometry validation failed.' }

Add-Type -AssemblyName System.Drawing
# Compile declarations only; the prototype entry point would rebuild old outputs.
$path = Join-Path $root 'assets/experiments/ferrite_artwork_v1/irregular.ps1'
$tokens = $null
$errors = $null
$ast = [System.Management.Automation.Language.Parser]::ParseFile($path, [ref]$tokens, [ref]$errors)
if ($errors.Count -ne 0) { throw 'Invalid prototype source.' }
$definitions = @($ast.FindAll({ param($node)
    $node -is [System.Management.Automation.Language.StringConstantExpressionAst] -and
    $node.StringConstantType -eq 'SingleQuotedHereString' -and
    $node.Value.Contains('public static class FerriteIrregularProof')
}, $true))
if ($definitions.Count -ne 1) { throw 'Expected one embedded contour compositor.' }
Add-Type -ReferencedAssemblies System.Drawing -TypeDefinition $definitions[0].Value
Add-Type -ReferencedAssemblies System.Drawing -Path (Join-Path $PSScriptRoot 'ferrite-catalog-renderer.cs')
[FerriteCatalogRenderer]::Initialize([FerriteIrregularProof], $root)
$catalogPath = Join-Path $root 'assets/environment/exterior/ferrite/catalog_v1/catalog.json'
$catalog = Get-Content -Raw -LiteralPath $catalogPath | ConvertFrom-Json
$variants = @($catalog.variants)
$images = New-Object 'System.Collections.Generic.List[System.Drawing.Bitmap]'
try {
    foreach ($entry in $variants) {
        $mask = [System.IO.File]::ReadAllLines((Join-Path $root $entry.mask_path))
        $image = [FerriteCatalogRenderer]::Render($mask)
        $images.Add($image)
        [FerriteCatalogRenderer]::Save((Join-Path $root $entry.png_path), $image, [bool]$Check)
        Write-Output ("PASS: {0}; {1}x{2} cells; {3} occupied; {4}x{5}px" -f
            $entry.id, $entry.width_cells, $entry.height_cells, $entry.occupied_cells, $image.Width, $image.Height)
    }
    $review = Join-Path $root 'assets/experiments/ferrite_catalog_v1'
    [FerriteCatalogRenderer]::ContactSheet($images.ToArray(), [string[]]@($variants.id),
        [string[]]@($variants.size_class), [string[]]@($variants.shape_family), $review, [bool]$Check)
    # One full-resolution mask/Extractor overlay per size. Clean individual
    # previews are the production-candidate PNGs themselves, without duplicate copies.
    foreach ($identity in @('ferrite_v1_small_table', 'ferrite_v1_medium_elbow', 'ferrite_v1_large_sprawl')) {
        $index = [array]::IndexOf([string[]]@($variants.id), $identity)
        $mask = [System.IO.File]::ReadAllLines((Join-Path $root $variants[$index].mask_path))
        [FerriteCatalogRenderer]::Overlay($images[$index], $mask,
            (Join-Path $review ($identity + '_overlay.png')), [bool]$Check)
    }
} finally {
    foreach ($image in $images) { $image.Dispose() }
}
Write-Output 'PASS: 10 candidate PNGs, contact sheet and 3 overlays; no Godot; artistic acceptance pending.'
