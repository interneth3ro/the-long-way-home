# Issue #96: native 47-pattern terrain laboratory

Feature branch experiment, pending merge and owner testing. This standalone,
configuration-only candidate does not implement the production visual refinements
tracked by [Issue #96](https://github.com/interneth3ro/the-long-way-home/issues/96).
[PR #97](https://github.com/interneth3ro/the-long-way-home/pull/97) remains a separate,
unmodified 16-corner experiment; none of its assets or code is reused here.

## Configuration provenance and inventory

The owner's [mapping report](experiments/native_terrain_47_96/tlwh_47_pattern_mapping.md)
and [exact CSV inventory](experiments/native_terrain_47_96/tlwh_47_pattern_mapping.csv)
are preserved byte for byte. Their 47 records agree; each has eight explicit
binary peering bits, and coordinates and signatures are unique. The report
identifies the community example scene and atlas; the original ZIP/reference
scene was not supplied to this implementation session, so extraction from that
scene has not been independently repeated. No creator artwork is included.
Instructions in that mapping report are reference context; implementation scope
and execution authorization come from the owner's assignment and repository policy.

Two exact-path `-text` attributes preserve the supplied mapping bytes across Git
checkouts rather than applying automatic newline conversion; the CSV's original
CRLF terminators are recognized as such by its exact-path whitespace attribute.
Existing font rules
are unchanged; no import or execution permission is expanded.

| Reference | TLWH | Use |
| --- | --- | --- |
| Grass (1) | Weathered Earth (0) | Peering values only |
| Dirt (2) | Low Green Cover (1) | All 47 centers and Green peering values |

Only these two terrains exist. Reference Water and the separate Grass-to-Water
family are excluded. The sole terrain set uses Match Corners and Sides (`mode=0`);
there is one atlas source (`0`), alternative `0`, and exactly 47 tiles. No physics,
navigation or gameplay metadata is added.

The [TileSet](../assets/experiments/native_terrain_47_96/experimental_match_corners_and_sides.tres)
uses the CSV coordinates unchanged: x=0..11, y=4..7, omitting (10,5).
The [original diagnostic PNG](../assets/experiments/native_terrain_47_96/experimental_47_patterns.png)
is 192 x 128 RGBA, with 16 x 16 cells. Rows 0..3 and (10,5) are transparent and
have no TileSet tile. Transparent padding is not an empty terrain configuration.

Each occupied cell is a flat 3 x 3 diagnostic matrix. Column/row spans are 4, 8,
4 pixels: corners occupy four 4 x 4 blocks, sides occupy the middle edge blocks,
and the 8 x 8 center is Green. Earth is RGBA (156,100,62,255); Green is
(74,170,82,255). Every sector encodes the corresponding CSV bit. These deliberately
blocky sectors make side/corner assignments inspectable; they are not final
transition contours or a candidate for artistic acceptance. Nearest filtering is
set on the lab root. No generated import sidecar or engine cache is committed.

## Known limitations before editor testing

There are **no Earth-centered configurations**. Pattern #33 at (9,6) is fully
Green. Pattern #36 at (0,7) has eight Earth peers but a **Green center**; it is
an isolated Green-center candidate, not a solid Earth tile. No Earth-center island
candidate or solid Earth backing exists. Defining Earth in the terrain set does
not establish that the native Earth brush has paintable candidates.

The supplied family is internally consistent but cannot represent arbitrary
independent binary center/peer assignments. Static completeness of the 47 supplied
records does not establish sufficiency for both material directions. Additional
Earth-centered configurations would be needed to represent Earth-centered cells;
the exact minimal expansion for native painting remains unresolved and is outside
this PR. No configurations, center substitutions, empty-terrain (`-1`) values or
custom autotiler are added to hide missing coverage.

Native brush availability, matching/selection, island survival, boundary stability,
empty-space behavior and painting-order dependence are **NOT RUN**. No 4.7.2 import,
parse, runtime or graphical compatibility is claimed. This may provide a useful
configuration reference for original illustrated work only after owner testing;
it is not yet an accepted terrain-art foundation. Chunk integration, neighbor halos,
generation order, performance, production 64-unit terrain/construction dimensions,
streaming and the provisional per-chunk TileMapLayer architecture remain outside scope.

## Owner-controlled editor checks

Follow the [execution policy](../AGENTS.md#godot-execution-safety) and
[testing policy](LOCAL_TESTING.md). Agent Godot execution requires separate explicit
owner authorization for this assignment, including Native. No runner changes are
made. Stop on import/parse errors or abnormal responsiveness; do not automatically
retry, profile, benchmark or reproduce a freeze.

1. In your editor, open the [laboratory](../scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn)
   in 2D. No game launch or F5/F6 is needed. Select `PaintingWorkspace`, open the
   native TileMap panel's Terrains tab and use **Connect**. Editor labels and a
   neutral backdrop provide instructions; the layer starts empty.
2. Inspect terrain set 0 and source 0 in the TileSet editor. Confirm both terrain
   definitions, mode, center and all eight peering bits against the CSV. Select
   each Earth/Green brush if available; record a missing/disabled Earth brush.
3. Use independent small work areas. Attempt an Earth backing then Green marks,
   and a Green backing then Earth marks. If a backing/brush cannot be made, mark
   that direction FAIL with the missing candidate, or BLOCKED if no attempt can
   be performed. Do not count empty canvas, the neutral backdrop, or pattern #36
   as Earth. Direct atlas placement can inspect tiles but does not prove terrain painting.
4. Keep results tied to Connect and exact brush order. Repeat with materials and
   order reversed, including rotated shapes. Optional Path tests require separate
   records. Inspect actual selected source/atlas/alternative and primary terrain
   in the editor; compare to the inventory. Preserve test edits and useful evidence
   separately under the repository preservation policy.

All result fields start **NOT RUN**. Use PASS/FAIL (or BLOCKED with reason) and
optional observations independently for each direction; no unchecked row is a PASS.

| Test | Expected check | Green into Earth | Earth into Green |
| --- | --- | --- | --- |
| 1 Import/configuration | Scene/TileSet load; 47 exact assignments; both brush availability | NOT RUN | NOT RUN |
| 2 Large regions | Continuous interiors and correctly matched boundaries | NOT RUN | NOT RUN |
| 3 Single-cell islands | Intended isolated center survives; record actual center ID | NOT RUN | NOT RUN |
| 4 Straight boundaries | Horizontal/vertical edges remain continuous | NOT RUN | NOT RUN |
| 5 Corners | Convex L shapes and concave notches, all rotations | NOT RUN | NOT RUN |
| 6 Narrow strips | One-/two-cell widths, bends and rotated strips survive | NOT RUN | NOT RUN |
| 7 Diagonals | Diagonal cells/checkerboards; record ambiguous or missing selections | NOT RUN | NOT RUN |
| 8 Irregular patches | Notches, protrusions, isolated tips and tile curves; reverse order | NOT RUN | NOT RUN |

For every failure record: test/direction; expected result; actual result;
source/atlas/alternative coordinates (or no selection); primary terrain ID;
terrain painting mode; backing, exact brush order and shape/rotation; optional
observations. Missing Earth centers are a known data limitation, not a reason to
invent extra tiles during testing. If import fails, dependent checks are BLOCKED.

## Static verification and scope

Run `python -B -m unittest discover -s tests -p 'static_*test.py'` for the complete
nonexecuting Python suite, or use `-p 'static_native_terrain_47_test.py'` for the
five focused tests. They check supplied-file SHA-256 and Markdown/CSV agreement,
exact inventory/IDs/peering assignments, unique signatures/coordinates, PNG chunk
CRC/dimensions/every sector pixel/transparent gaps, resource and lab references,
known center gaps and byte preservation of all tracked production inputs and
execution controls against baseline `48cd9150d7aa2e029c7328229e7865cf00e83723`.
Git diff review checks the remaining changed-file scope. Static assertions inspect
text and bytes; they do not run Godot, gameplay or a simulated terrain solver.

Implementation validation on 2026-10-31: **112/112 complete static tests PASS**,
including **5/5 focused prototype tests**. Changed local Markdown targets and
Git whitespace checks PASS. All 13 pre-existing untracked files retain their
original SHA-256 values. Godot import, Native, runtime, graphical, profiling and
benchmark checks are NOT RUN.

The deliverables are the PNG and TileSet above, the script-free lab, both unchanged
mapping inputs, this report/checklist and the focused static test. The README links
this report. Existing owner artwork, import sidecars, ignored data and the PR #97
branch remain preserved. No production assets, rendering, project settings,
narrative canon, gameplay, tests for Native, or execution policy are changed.

Godot API references: [TileSet terrain modes](https://docs.godotengine.org/en/4.5/classes/class_tileset.html)
and [terrain setup](https://docs.godotengine.org/en/latest/tutorials/2d/using_tilesets.html).
These describe the configuration model, not verification of this resource in 4.7.2.
