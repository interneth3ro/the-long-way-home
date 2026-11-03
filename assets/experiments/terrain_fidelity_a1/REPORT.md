# Terrain Visual Fidelity 2.0 — A1 artwork feasibility

Experimental artwork, pending owner review. Recommendation: **needs one bounded
art revision**. The new treatment adds visible material structure, but this candidate
does not yet demonstrate convincingly natural repetition at the 128-pixel footprint.
This finding does not establish that the renderer must be replaced.

## Scope and provenance

- Base: `fa410ed9b329ffd28a927e142d2362971d54584a`, synchronized `main`.
- Branch: `codex/terrain-fidelity-a1-artwork`. The exact review HEAD is the PR head
  containing this report; use `git rev-parse HEAD` or the PR commit list. A commit
  cannot contain its own final hash; the final chat records that hash explicitly.
- The supplied `grassland.png` concept board was visually examined. Its layered
  greens, short grass/leaf cover, quiet areas, warm earth and irregular recovery
  informed the prompts. No board pixels, layout, labels or props were copied.
- Built-in image_gen produced two original 1254x1254 RGB sources. Their full prompts,
  provider-byte hashes and packaged hashes are in [prompts.json](prompts.json).
  Ancillary PNG metadata was stripped without changing compressed pixel data;
  provider originals remain outside the checkout. No historical FactoryGame input
  was read or reused during A1. Model generation is not deterministically repeatable.
- Existing production atlas pixels were read for baseline comparison only. Ship,
  contact-shadow and introductory Ferrite pixels were reused only in the labeled
  offline context image. Production files remain unchanged.
- Preflight found no tracked edits and 15 pre-existing untracked environment PNG
  import sidecars. They remain untracked and were hash-checked for preservation.
  Ignored owner files were not cleaned, moved or repurposed.
- All additions are inside this `.gdignore`-protected directory. There are no scene,
  TileSet or production-resource references to these candidates.

## Method and artistic rationale

One Green treatment combines short painterly grass with interwoven leaf cover;
Earth uses compacted warm soil, restrained cracks and tiny embedded fragments.
Green is intentionally dominant in the boundary fixture, independently of current
world distribution. Neither distribution nor crash-site masks were changed.

`author.py` uses current TLWH PNG helpers and label drawing without invoking their
writers. Integer-bin box reduction creates 128x128 samples from the generated
sources. An eight-texel opposite-edge crossfade then makes opposite boundary pixels
equal. This is an offline seam treatment, not proof that the generated sources were
seamless. Raw reduced edge mismatches were Earth **43/255** and Green **29/255**.

Each material has A/B/C-like candidates. B/C use fixed phase shifts `(37,59)` and
`(79,23)` with an interior-only sine-squared envelope of strength 0.8. Edges remain
identical; no lighting rotations are introduced. These are correlated variations
of one source, not independently painted materials. A fixed seed 26026 uses the
current resolver's 60/25/15 arithmetic offline. Runtime determinism is untested.

Only **15 unique fixture signatures** are evaluated in memory. Transition concepts
reuse the current TLWH mask math and selected 0.15–0.85 remap, blending in linear
light. No complete 94-signature atlas, native resource or transition integration
was built. The narrow connection, curved boundary, incision, corners and isolated
patch are fixtures, not a new terrain-generation algorithm.

## Evidence and findings

| Evidence | What to inspect |
| --- | --- |
| [128-pixel samples](previews/samples_128.png) | Earth and Green A/B/C candidates; source-art scale, not gameplay scale |
| [Green repeats, 1.0x](previews/repeat_1x.png) / [0.5x](previews/repeat_05x.png) | Same baseline/candidate arrangement; first three rows deliberately repeat A, remaining rows use weighted variation |
| [Repeat grid diagnostic](previews/repeat_1x_grid.png) | Tile alignment, separately from clean views |
| [Boundary concepts, 1.0x](previews/boundary_1x.png) / [0.5x](previews/boundary_05x.png) | Broad interiors, curved/straight segments, corners, narrow connection, island and earth incision |
| [Boundary grid diagnostic](previews/boundary_1x_grid.png) | Whether material rhythm follows cell boundaries |
| [Ship/Ferrite context, 0.5x](previews/context_05x.png) | Clearly illustrative composite at matched object scales; simple split background, not the authored crash site |

All paired grounds are neutral-tint comparisons with identical layouts and pixel
scales. Cells occupy 64 pixels at 1.0x and 32 at 0.5x, before viewer scaling.
Integer-bin box reduction is an offline display approximation, not Godot filtering.
The viewer may shrink large sheets; inspect at native image size where practical.

**Observed subjective findings:**

- At 1.0x, Green has substantially more surface structure, but recurring diagonal
  grass strokes form a wallpaper rhythm. Weighted B/C reduce exact duplication
  without eliminating it. Quiet/dense variation is weaker than the reference board.
- At 0.5x, small foliage merges into granular directional texture. The intended
  lushness is less legible and the diagonal rhythm remains. This is not a successful
  substitute for the board's layered vegetation at gameplay scale.
- Earth reads as warmer, more articulated soil, but light specks and patches recur.
  Further fine grain would likely increase busyness rather than solve repetition.
- No hard RGB discontinuity occurs on the tested candidate edges. The edge
  crossfade can nevertheless soften a repeated border band. Matching edge bytes
  cannot certify natural-looking borders or derivatives after display filtering.
- Transition shapes remain visibly cell-constrained and scalloped in the stress
  fixture. More detailed materials do not hide repeated boundary geometry. These
  are limited concepts, not an accepted vegetation-to-soil recovery treatment.
- The context composition retains clear ship/Ferrite silhouettes. Ground detail
  helps bridge material richness but remains much finer than Ferrite's broad facets.
  This is a subjective compositing observation, not gameplay readability acceptance.

The context image uses existing ship/shadow scale 0.70 and Ferrite scale 0.50,
then 0.5x view reduction. [Context provenance](context-provenance.json) records
dimensions, hashes and composition method. It omits runtime tint and authored
lighting; its simple Earth/Green split is intentionally illustrative. The detailed
maintenance-bay stationary Extractor is not composited here and must not be confused
with exterior deployed machines, whose current drawings are provisional.

## Checks and reproduction

Focused checks performed:

- **36** self/variant opposite-edge comparisons: exact RGB equality.
- **528** candidate layout adjacencies: exact RGB equality at source resolution.
- Regeneration check of **14** author outputs, including manifest: byte-identical.
- Context source/output hash check, changed-file scope, Markdown links and
  `git diff --check`; pre-existing sidecar preservation.

These checks cover only saved samples and the two layouts, not every compatible
signature, diagonal combination, native filtering or possible world arrangement.
No Godot, editor, import, game, full static suite, benchmark or profiler was run.
No claim is made about motion shimmer, runtime determinism, responsiveness, frame
rate, memory, streaming or native TileSet correctness.

```powershell
python -B assets/experiments/terrain_fidelity_a1/author.py --check
pwsh -NoProfile -File assets/experiments/terrain_fidelity_a1/compose-context.ps1 -Check
```

Creation uses `author.py --write`, which refuses existing outputs. Reproduction of
creation requires a fresh task-owned copy containing the sources and recipes;
preserve the reviewed directory. `--write` also creates two ignored intermediate
grounds under `artifacts/tmp/terrain_fidelity_a1/` for context composition. They are
not PR assets. `--check` regenerates evidence in memory and does not write files.
Context reproduction needs those grounds and Windows System.Drawing/Arial; GDI/font
differences may affect encoded output across hosts. No additional dependency/plugin
was installed. Original provider sources and the concept board are not required
for offline regeneration of the saved samples.

## Exact changed-file inventory

All 23 tracked additions are under `assets/experiments/terrain_fidelity_a1/`:

```text
.gdignore
REPORT.md
author.py
compose-context.ps1
context-provenance.json
manifest.json
prompts.json
sources/earth_generated.png
sources/green_generated.png
tiles/earth_A.png
tiles/earth_B.png
tiles/earth_C.png
tiles/green_A.png
tiles/green_B.png
tiles/green_C.png
previews/samples_128.png
previews/repeat_1x.png
previews/repeat_05x.png
previews/repeat_1x_grid.png
previews/boundary_1x.png
previews/boundary_05x.png
previews/boundary_1x_grid.png
previews/context_05x.png
```

[manifest.json](manifest.json) records generated tile/preview dimensions and hashes,
source input hashes, parameters and edge-check totals. Sources are original frozen
AI rasters; six tiles are repeatable edge-equal candidates; all previews are derived
offline evidence. None is an accepted production asset or perceptually certified
seamless material. Text, filenames and packaged metadata were reviewed for private
paths/secrets before publication. Production documentation was reconciled without
changing its current-behavior claims; this report supplies the A1 evidence gap.

## Owner review and next decision

Recommendation: **needs one bounded art revision**, not Stage A2 yet. Revise medium
motif scale and density: fewer aligned blade strokes, more low-salience interwoven
cover and quieter irregular areas. Keep the same repeat tests and footprint so the
revision answers an art question rather than hiding it with a larger unique scene.
This is a recommendation only; no further revision or architecture work is started.

Owner visual-acceptance questions:

1. Does the Green palette move toward the supplied board, despite the failed
   repetition treatment, or should it be less yellow/olive?
2. At native 1.0x and 0.5x, is the diagonal rhythm as conspicuous as reported?
3. Is Earth detail appropriate beside ship/Ferrite, or too granular and orange?
4. Approve one bounded art revision, or request architectural exploration based
   on these limitations? Neither decision is implied by this draft PR.

Stop at A1 review. No full atlas, production integration, distribution tuning,
historical reuse, Godot execution or Stage A2 is authorized by these outputs.
