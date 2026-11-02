# Ground artwork refinement prototype v1

## Follow-up transition softness review

The owner reviewed the quieter ground as a substantial visual improvement and
requested slightly smoother transitions. The approved refined Earth/Green
sources and the current 0.20-0.80 prototype remain unchanged. An additive
[three-way softness comparison](../assets/experiments/native_terrain_47_96/ground_softness_comparison_v1/README.md)
shows Current 0.20-0.80, Candidate A 0.15-0.85 and Candidate B 0.10-0.90 on the
same saved meandering/mixed layouts at approximate gameplay scale and native
detail scale. It validates all compatible edges of the same 41-signature subset
for every treatment. No replacement atlas, new TileSet or runtime change is
introduced. The feathering choice remains pending owner visual acceptance.

The original prototype method and validation record follow unchanged.

This additive artwork study is pending owner visual acceptance and merge. It
implements the approved quieter direction using transformed original source
textures. Production integration and a full 94-signature replacement remain
outside scope. No gameplay, procedural generation, tint shader, scene, resolver,
TileSet, weighting or production import settings change.

## Review package

The [prototype README](../assets/experiments/native_terrain_47_96/ground_refinement_v1/README.md)
links all six comparison PNGs and the new artwork. Compare the assembled
meandering and mixed environments first, then interiors and transition shapes.
Every board is labeled **OFFLINE STUDY**. Original is left, refined is right;
framing, tile assignments and variants are identical. Original panels use saved
production atlas pixels, including their original B/C interiors.

The 128-pixel views show artwork resolution. The additional 64-pixel views use
nearest-neighbor reduction to approximate 128-pixel art occupying 64 world units
at a one-screen-pixel-per-world-unit view. They omit camera zoom, production tint,
lighting, objects and runtime rendering. They are not Godot captures.

## Provenance and deterministic transformation

The verified starting `main` and remote HEAD were
`ec95accbab05dd580dc15a3176b8e76457861d2f`, with a clean working tree.
The [new offline tool](../tools/ground-art-refinement.py) checks original sources,
production resources, the 94-record inventory and the historical baker against
their existing identities before processing. PNG/CSV hashes use raw bytes;
text hashes normalize CRLF to LF, matching existing preservation guards.
No external dependency or engine is required.

Inputs are the approved `earth_solid.png` and `green_solid.png` under
`assets/experiments/native_terrain_47_96/illustrated_v1/originals/`.
Each new source is a 128x128, 8-bit RGB PNG. No independently generated material,
uncontrolled noise or new palette is introduced.

For each linear-RGB channel, operate on the unique 127x127 periodic texels; the
last row/column duplicate the first, as in the existing source sampling contract.
Compute separable periodic box averages with radii **2, 7 and 18**. With `F`, `M`
and `L` denoting those averages, source `S` and mean `mu`, the refined value is:

```text
mu + 0.14*(L-mu) + 0.06*(M-L) + 0.025*(F-M) + 0.008*(S-F)
```

Correct floating-point mean drift before sRGB encoding. This compresses separate
frequency bands while retaining faint source-derived texture. It deliberately
compresses the color spread; it preserves approximate mean color and material
identity, not the original contrast histogram. No heavy Gaussian blur is used.

B/C retain the historical offsets/rotations and sine-squared interior envelope,
with **0.45** mixture strength instead of the original **0.80**. All boundary
pixels remain equal to the refined A interior. No brightness tint is added.

## Transition treatment and coverage

Import the historical baker read-only; never call its writer or change its
globals. Reuse its existing signature masks, including the Coons interpolation,
center bubble and periodic contour perturbation. Apply:

```text
new_weight = smoothstep((old_weight - 0.20) / 0.60)
```

Here `smoothstep(t)` clamps `t` to 0..1 and evaluates `t*t*(3-2*t)`.
The monotonic mapping preserves the 0.5 contour, binary anchors and shared-edge
relationships. Across this subset, partially blended texels decrease from
**152,887 to 64,986** (about 57.5%). Width is a mask-space parameter, not a fixed
number of pixels or world units. Narrow links and endpoint centers retain their
original pure-material anchors.

The subset has **41 existing baseline signatures plus four solid B/C records**.
It includes twenty named representatives: both solids, four straight directions,
convex/concave corners, endpoints, narrow links and isolated patches for both
materials. Remaining signatures support the assembled previews. No new signature
or peering value is introduced. Coordinates stay identical to the existing CSV
and production mapping. `baseline_subset.png` keeps the original 12x8 grid and
128-pixel cells; unused dark slots have no configured records. `interiors_bc.png`
keeps Earth B/C at (0,0)/(1,0), Green B/C at (0,1)/(1,1). No TileSet is created.

Three small layouts are copied exactly, including variants, from the immutable
Stage 2 `previews.json`: Green patch, Earth patch and meandering boundary. The
meandering board is exported for comparison; all three are retained in the new
manifest for repeatability. The larger 24x16 study uses a documented sinusoidal
binary field and the existing rule-1 shared-side/corner classification; it is an
offline illustration, not a new world-generation implementation. Its fixed
coordinate variant buckets use 60/25/15 thresholds; the production resolver is
untouched. The A/B/C repetition board deliberately cycles A/B/C equally to expose
art differences, rather than claiming to model their production distribution.

## Reproduction and checks

```powershell
python -B tools/ground-art-refinement.py --check
python -B -m unittest discover -s tests -p 'static_ground_refinement_test.py' -v
python -B -m unittest discover -s tests -p 'static_baked_terrain_test.py' -v
python -B -m unittest discover -s tests -p 'static_terrain_resolver_test.py' -v
```

`--check` regenerates all twelve generated outputs in memory and compares exact
bytes, including the manifest. `--write` creates only the fixed prototype output
directory and refuses an existing directory. Documentation is manually authored
and is not overwritten or regenerated. Do not delete the study to rerun it;
use `--check` against the tracked results. The study's local `.gitattributes`
keeps its generated JSON manifest at LF for exact regeneration after checkout;
no existing attributes or historical files change.

The focused subset checks cover RGB dimensions, saved raster hashes, immutable
CSV/native mappings, every compatible ordered horizontal/vertical edge pair of
the generated records, all nine transition anchors, A/B/C boundary equality,
absence of black/magenta configured pixels, retained nonzero texture and reduced
contrast, approximate channel means, unchanged contour classification, all saved
preview adjacencies and exact historical layouts. Regeneration invokes only the
new offline artwork tool and read-only historical math, never Godot.

## Preservation and review limits

On 2026-11-02, the finalized staged prototype passed **9/9 focused offline
checks**, including exact in-memory byte regeneration and **836** compatible
ordered right/bottom edge pairs across its 45 records. The unchanged production
baked suite passed **6/6** and resolver static suite passed **8/8**: **23/23
focused checks total**. Both new documents' local links and staged Git whitespace
checks passed. All **696** preflight-snapshotted files (existing tracked inputs
plus existing PR #100 evidence files) retained their exact raw working bytes.
The full repository static suite was not run; these results are scoped to the
artwork study, saved production atlas and resolver.

Production PNGs, TileSet, mapping, original artwork, historical baker, peering
inventory, gameplay scripts, scene integration, all historical guards/goldens,
receipts and existing PR #100 evidence remain unchanged. The new manifest records
input/output hashes without replacing historical expectations. Existing historical
resources and their hash pins remain authoritative for their original versions.

This is subset validation, not validation of a refined 94-signature atlas. The
saved production atlas continues to be checked separately with its unchanged
existing tests. Runtime performance, graphics and shading equivalence are
unverified; no Godot execution is authorized or performed for this study.

The concept image itself was not supplied to this chat; this candidate follows
the written approved direction. The new surfaces intentionally approach uniform
color, and subtle A/B/C differences may be difficult to see at gameplay scale.
Less texture exposes existing rounded stepping and corner pockets. Narrower
feathering makes boundaries crisper; visual acceptance of that tradeoff and small
features remains the owner's decision. Existing runtime tint may also change the
perceived balance. Stop at the draft PR for owner visual acceptance before any
further implementation or production replacement.
