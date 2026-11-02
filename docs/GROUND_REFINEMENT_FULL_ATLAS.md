# Complete approved ground refinement atlas

PR #120 merged the owner-approved complete atlas. The production integration
below is prepared on a feature branch, pending technical review and owner
gameplay acceptance. The offline candidate and its historical records remain unchanged.

## Sources and generation

The [approval record](experiments/ground_art_approved_treatment.json) is
authoritative. Warm ochre-brown Weathered Earth and muted natural Low Green Cover
retain their faint natural texture, subtle uniform color variation and existing
complementary A/B/C treatment. The saved 128x128 RGB refined sources under
`assets/experiments/native_terrain_47_96/ground_refinement_v1/sources/` are read
verbatim, not regenerated. Their SHA-256 identities are:

- Earth: `43f587282190b7046d7a36f395c38a52beed64e95c84037c1e12ee68d81c6e1f`
- Green: `09327f27b2ac2be87fd17586fc9626d1c52bc00f4d1491651a35912c78a94202`

The [small offline wrapper](../tools/ground-refinement-full-atlas.py) imports the
unchanged approved renderer and supplies a new local context containing the full
production inventory. No imported globals or historical recipe files change.
Mask construction, organic contour centerlines, nine anchors and linear-light
blending are inherited unchanged. Only the approved remap is applied:

```text
new_weight = smoothstep((old_weight - 0.15) / 0.70)
```

The range is a mask-weight interval, not a fixed pixel distance. No edge repair,
new texture parameters, resolver logic or procedural world behavior is introduced.
B/C atlas bytes are copied directly from the approved saved prototype.

## Inventory and saved outputs

All new artwork, evidence and the manifest are under
[ground_refinement_full_v1](../assets/experiments/native_terrain_47_96/ground_refinement_full_v1/README.md).
The directory has a local `.gdignore`; production scenes and resources do not
reference it. It contains no new TileSet resource.

| Atlas | RGB dimensions | Tile size | Records |
| --- | --- | --- | ---: |
| `baseline_94.png` | 1536x1024 | 128x128 | 94 |
| `interiors_bc.png` | 256x256 | 128x128 | 4 |

The baseline preserves all 94 coordinate/signature assignments in the production
mapping and immutable historical CSV: **47 Earth and 47 Green**, each with nine
signature values. The 12x8 layout retains unconfigured black slots (10,1) and
(10,5); these are excluded from configured tiles and previews. No signatures,
peering assignments, priority rules, source IDs or alternative IDs are added.
Candidate manifest records retain alternative ID 0, as in production.

Earth A remains at (9,2); Green A at (9,6). In the B/C atlas, Earth B/C remain
(0,0)/(1,0), Green B/C (0,1)/(1,1). There are **98 configured records representing
94 unique signatures**. All three interiors for each material are distinct and
share identical edge pixels. The new manifest records every coordinate,
signature, variant, tile-pixel hash, input identity and output hash.

## Reproduction and validation

From the repository root, using Python's standard library only:

```powershell
python -B tools/ground-refinement-full-atlas.py --write
python -B -m unittest discover -s tests -p 'static_ground_full_atlas_test.py' -v
python -B -m unittest discover -s tests -p 'static_ground_*_test.py' -v
python -B -m unittest discover -s tests -p 'static_baked_terrain_test.py' -v
python -B -m unittest discover -s tests -p 'static_terrain_resolver_test.py' -v
python -B -m unittest discover -s tests -p 'static_*_test.py'
```

`--write` creates only a new fixed output directory and refuses an existing one.
The original tool remains an immutable historical authoring input. Its standalone
`--check` also reproduces checkout audit metadata and requires the historical
checkout. Use the focused static suite above for current-checkout reproduction;
it regenerates artwork and compares semantic manifest fields while leaving the
saved historical input inventory untouched. Do not delete the saved candidate. Working-input hashes record
raw checkout bytes, including historical text line endings; use the same checkout
line-ending convention for byte-identical manifest reproduction. Explicit
`sha256_lf` identities use the repository's LF normalization convention.

The validator checks all 98 saved tile records after decoding the actual encoded
atlas bytes. It checks every ordered pair whose three edge signature values
match: **1,394 horizontal + 1,394 vertical = 2,788 compatible edge pairs**, each
with exact pixel equality and maximum channel difference **0**. This count includes
A/B/C variants and self-pairs, with right-to-left and bottom-to-top directions
counted once each, following the existing signature rules. It exceeds the PR #119
subset's 836 comparisons.

All **846 baseline mask/raster anchors** match their signature values. Every
baseline texel preserves its original >=0.5 contour classification; 232,204 texels
are partially blended. Configured tiles contain no black or magenta placeholders.
Tests also check compatible diagonal corner pixels, assembled layout adjacencies,
missing-record rejection, damaged anchors/edges/contours, exact inventory, saved
Candidate A subset reproduction, source/B/C identity and deterministic outputs.

## Offline comparisons

The [preview index](../assets/experiments/native_terrain_47_96/ground_refinement_full_v1/README.md)
links broad Earth/Green interiors, A/B/C repetition, large material patches,
meandering boundaries, mixed terrain, and a complete coordinate contact sheet.
The contact sheet includes every horizontal/vertical boundary, convex/concave
corner, narrow link, endpoint, isolated patch and remaining configuration.
Separated contact-sheet neighbors are not asserted to be compatible terrain.

Assembled terrain reuses the exact saved PR #119 layouts, including its offline
mixed field, and PR #100 patch/meander assignments. No new world-generation
algorithm is used. Both sides are assembled from decoded saved atlas pixels with
identical layouts and variants. Every board includes native artwork scale and
approximate half-scale display (128-pixel art at 64 world units), labeled offline.

## Preservation and limits

Starting main: `5d4f502928ea964e9d8b8b71ded87c0888b5aaaf` (merged PR #119).
Preflight verified a clean checkout and zero divergence after fetching origin.
The original approval reproduction suite passed 4/4 before implementation.
The saved manifest retains the original 343-file checkout inventory as historical
provenance. On the Balanced Simplification feature branch, it no longer freezes
current source, tests or documentation. Focused tests retain exact approved
artwork, true authoring inputs, mapping, raster anchors, edges and output identities.
No historical receipt or artwork hash is rebaselined.

No Godot invocation, engine import, gameplay, graphical, rendering or performance
validation is performed. Exact shared-edge equality proves raster compatibility
under the signature rules; owner visual review is still required for appearance.
Offline previews omit camera zoom, runtime shading and color overrides. Existing
rounded contour stepping remains unchanged. These candidate images are not
paintable in a new scene and are not loaded by production.

Future production integration requires owner acceptance of the full candidate,
a separately authorized integration PR retaining the existing resolver/TileSet
contract, preservation review and separately authorized engine/graphical checks.
No historical acceptance record is rewritten by this candidate.


## Historical validation compatibility (superseded by Balanced Simplification)

PR #120's [37-file admission record](experiments/ground_art_validation_admission.json)
remains immutable history. Its saved artwork and recipe identities are checked;
its five validation-amendment entries no longer admit or freeze current tests.
The predecessor helpers, broad changed-file prohibitions and helper self-pins
have been retired on the pending maintenance branch. Unrelated additions do not
need historical admission. Ordinary source revisions remain in Git.

The two exact historical checkout portability contracts remain: the PR #119
comparison `.gitattributes` and Stage 2E audit. Original PNGs, receipts, historical
stage manifests, inert payloads and recovery evidence retain their identities.
Active terrain checks retain the current lookup resource path, complete TileSet
structure, peering inventory and approved atlas pixels. Resolver arithmetic,
chunk ownership, determinism and relevant gameplay-source contracts remain.

Run current static regression coverage from the repository root:

```powershell
python -B -m unittest discover -s tests -p 'static_*test.py'
```

This maintenance changes validation only. It grants no Godot execution permission.

## Consolidated static validation results (2026-11-02)

Historical PR #120 results below describe that implementation, not a new run
of the simplified suite:

| Command/check | Result |
| --- | --- |
| `python -B -m unittest discover -s tests -p 'static_*_test.py'` | 282/282 PASS; zero failures/errors |
| Focused command below (from `tests/`) | 66/66 PASS; zero failures/errors |
| `python -B tools/ground-refinement-full-atlas.py --check` | All 13 generated outputs byte-identical; read-only |

```powershell
python -B -m unittest -v static_ground_admission_test static_ground_portability_test static_housekeeping_test static_ground_full_atlas_test static_baked_terrain_test static_terrain_resolver_test static_ground_approval_test static_ground_refinement_test static_ground_softness_test
```

The focused 66 checks comprise admission/corruption 17, portability 4, original
Stage 2A self-tests 5, full-atlas 7, baked terrain 6, resolver 8, PR #119 approval 4,
prototype 9 and softness 6. Full discovery additionally covers all other existing
preservation, scene/resource-source and gameplay-source static regressions. There
are no remaining static failures. No Godot import, engine, graphical, runtime,
rendering or performance acceptance is claimed.

All ten candidate PNGs retain their pre-remediation bytes. The two owner-pinned
atlas SHA-256 values remain:

- Baseline: `36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0`
- B/C: `d8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694`

The complete inventory remains 94 signatures / 98 records, with 2,788 exact
compatible ordered edge pairs and 846 anchors. Production assets, mapping,
TileSet, resolver, shading, PR #100 evidence, original PR #119 artifacts, historical
receipts, old hash pins and execution controls remain unchanged. The five named
validation amendments are the only modifications to files that existed at the
starting revision. Candidate metadata records their authorized current identities;
it does not replace any historical receipt. Owner technical and full-atlas visual
acceptance remain required before merge consideration or production integration.

## Production integration (feature branch, pending merge)

Starting main: `da3d2d53b90f6a311d47bf1ab43f2a45437577b5`.
The active presenter still loads `TerrainAssignmentLookup.TILESET_PATH`; only that
constant changes from
`res://assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres` to
`res://assets/environment/exterior/ground_refined_v1/terrain.tres`.
The mapping remains `baked_v2/mapping.json` at its original path.

The [active TileSet](../assets/environment/exterior/ground_refined_v1/terrain.tres)
is the historical native TileSet with exactly two texture path substitutions:

| Texture | Previous prefix | Active prefix | SHA-256 of approved active PNG |
| --- | --- | --- | --- |
| `baseline_94.png` | `assets/experiments/native_terrain_47_96/baked_v2/` | `assets/environment/exterior/ground_refined_v1/` | `36595f982ecadffc75ea2f7ca3498e6d44cbf9f3a7fe298f28268730161056e0` |
| `interiors_bc.png` | `assets/experiments/native_terrain_47_96/baked_v2/` | `assets/environment/exterior/ground_refined_v1/` | `d8c76f080226c93229be7b3947983776543d14f454a475d69700af3f7849c694` |

Both PNGs are byte-for-byte copies of PR #120. No original atlas, mapping,
TileSet, offline `.gdignore`, preview, manifest or acceptance receipt changes.
All 94 signatures, 98 records, 752 baseline peering assignments, four B/C records,
source IDs 0/1, atlas coordinates, alternatives and 128-pixel dimensions remain
identical. The half-scale TileMap, resolver rules, generation, chunk handling,
shading, crash-site gradients/masks/overrides, collisions and gameplay authority
remain unchanged. There is no additional rendering layer or texture pass.

The new directory has no ignored ancestor. Path-based texture references permit
normal Godot texture import; no import metadata is copied or invented. The
historical TileSet has no top-level resource UID, and neither does its derivative.
Internal subresource IDs are retained and scoped to their resource. Fresh PNG
import metadata must be generated by the owner's engine import. Static path
inspection establishes the intended import arrangement, not successful import.

Balanced Simplification replaces the forward predecessor layer with focused
resource validation. The lookup path is checked independently of script bytes;
the TileSet structure, peering, approved atlas pixels and missing-resource
failures remain covered. Current test and documentation bytes have no admission
requirement. The saved historical manifests and original artwork pins remain intact.

Validation is static only. Godot, Native, profiling and benchmarks have not been
run. Owner import, gameplay appearance and responsiveness remain unverified.
Static results and exact file inventory are recorded in the draft PR.

### Owner gameplay acceptance checklist

Use the ordinary owner-controlled gameplay workflow. Record pass/fail/untested
for each item; no item below has been claimed as passed by the agent.

1. Initial exterior spawn: terrain imports and loads without resource errors.
2. Weathered Earth is warm ochre-brown; Low Green Cover is muted natural green.
3. Organic transitions appear soft and continuous at normal gameplay scale.
4. Inspect large areas for subtle A/B/C repetition and uniform faint texture.
5. Check crash-site clearing, shading, masks and feathering.
6. Confirm Ferrite deposits remain readable.
7. Confirm construction-grid readability.
8. Confirm machinery and vegetation contrast against both ground families.
9. Move across chunk boundaries and inspect continuity.
10. Leave previously visited areas and return; compare terrain appearance.
11. Confirm regeneration consistency for the same seed and coordinates.
12. Observe ordinary gameplay responsiveness and any significant new stutter.

Owner graphical and performance acceptance is required before merge authorization.
Issue #96 remains open. No merge or engine execution is authorized by static PASS.
