# Issue #96: native 94-pattern two-material terrain laboratory

PR #98 remains a draft configuration experiment, pending owner testing. The
47-pattern filenames and paths are retained for stable references and import UIDs.
This revision tests whether complementary Earth-centered configurations resolve
the Earth-brush limitation; correct painting is a hypothesis, not an established result.
Production terrain and gameplay are not integrated or changed by this PR.
[Issue #96](https://github.com/interneth3ro/the-long-way-home/issues/96) remains open;
[PR #97](https://github.com/interneth3ro/the-long-way-home/pull/97) remains untouched.

## Reference extraction and exact inventory

The original owner-supplied [47-pattern report](experiments/native_terrain_47_96/tlwh_47_pattern_mapping.md)
and [Green mapping CSV](experiments/native_terrain_47_96/tlwh_47_pattern_mapping.csv)
remain byte-identical. Their extraction and future-work statements describe that
original family; the current owner request authorizes the complementary family.
Reference files supply data, not execution instructions or authority to expand scope.

The supplied `godot-4-tileset-terrains-docs-master.zip` was read without unpacking
artwork or executing code. The actual archive member is:
`godot-4-tileset-terrains-docs-master/starter_project/terrain_modes/topdown_example/topdown_example.tscn`.
The selected `TileSetAtlasSource_matpb` is associated with the Corners and Sides
texture reference and `TileSet_uqitd` (`terrain_set_0/mode = 0`). Other atlas modes
in the scene are not used. Only serialized technical assignments were extracted.
No creator artwork is copied, imported, displayed or redistributed.

- ZIP SHA-256: `9b9e26b25138d4c4b8fa83430204d2e5b571795cda48673f199d822e9d4a1971`.
- Scene member SHA-256: `1f67cf862a16c90eb2ffb6076cc2980d453e33b24b19b35e8e7806acc0e94582`.
- [Technical source transcription](experiments/native_terrain_47_96/reference_corners_and_sides.json):
  original coordinates, centers and eight original peers for all 95 reference tiles,
  plus provenance hashes. Its LF-normalized SHA-256 is
  `e0c6497b08f35a6138f98b4b70b70fa1ee5de086639c7d52310416b4cc5bd6b2`.
- [Combined 94-record inventory](experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv):
  family, family-local pattern number, original atlas/center/eight peers, mapped
  center/eight peers, and final experimental atlas coordinates. Earth rows are the
  complementary inventory; Green rows preserve every original supplied assignment.

| Family | Reference center and peers | TLWH mapping | Count |
| --- | --- | --- | --- |
| A: Earth | Grass center 1; Grass 1 / Water 0 peers | center 0; 1 -> Earth 0, 0 -> Green 1 | 47 |
| B: Green | Dirt center 2; Dirt 2 / Grass 1 peers | center 1; 2 -> Green 1, 1 -> Earth 0 | 47 |

The reference has exactly 47 Grass-centered and 47 Dirt-centered tiles, each with
eight explicit peers. The additional Water interior at (10,1), center 0 with eight
0 peers, is recorded in the source transcription but **excluded** from the TileSet
and combined mapping. No 95th tile or other family is added. Remapping is
family-specific; reference Water is not added as a third TLWH material.

All 47 original Green records were compared directly against the ZIP scene:
center and all 376 peers agree. Both mapped families have 47 unique eight-peer
signatures. The combined set has **94 unique center-plus-peer signatures**, 94
unique atlas coordinates and **752 explicit peering assignments**. There are no
duplicate full signatures or overlapping atlas cells. Peer-only signatures overlap
across families only for all-zero and all-one peers:

| Peers | Earth-center candidate | Green-center candidate |
| --- | --- | --- |
| All Earth (0) | (9,2): solid Earth | (0,7): isolated Green candidate |
| All Green (1) | (0,3): isolated Earth candidate | (9,6): solid Green |

These two peer-only overlaps are intentional, distinguished by center ID. Whether
native Connect chooses the intended center and remains stable is still unverified.

## TileSet, diagnostic PNG and lab

The existing [TileSet](../assets/experiments/native_terrain_47_96/experimental_match_corners_and_sides.tres)
now has one atlas source (`0`), alternative `0`, one Match Corners and Sides terrain
set (`mode=0`), Weathered Earth (`0`) and Low Green Cover (`1`). No collisions,
navigation, gameplay metadata or custom autotiler is added. Owner editor UIDs,
property order, default omissions and all existing Green assignments are retained;
only 47 Earth records and updated experimental names are added to that serialization.
The editor omitted tile-size properties at their 16 x 16 defaults; no cell-size
change is introduced.

The original flat-color [PNG fixture](../assets/experiments/native_terrain_47_96/experimental_47_patterns.png)
remains 192 x 128 RGBA with 16 x 16 cells. Its occupied inventory expands from 47
to 94 by filling previously transparent rows 0..3 with Earth-family patterns.
Green remains in rows 4..7, with every original Green pixel unchanged. Coordinates
are identical to the reference for both families; no translation is needed.
Cells (10,1) and (10,5) remain transparent and have no configured tile.

Each cell is a 3 x 3 diagnostic matrix with 4/8/4-pixel row and column spans.
The center 8 x 8 block represents its primary terrain; corner blocks and middle
edge blocks represent the corresponding eight peers. Earth is RGBA
(156,100,62,255); Green is (74,170,82,255). These blocky sectors encode metadata,
not final organic contours or illustrated artwork. The lab uses nearest filtering.
The existing [script-free TileMapLayer laboratory](../scenes/experiments/native_terrain_47_96/terrain_painting_lab.tscn)
retains its neutral backdrop and native editor tools, with revised two-family labels.
No production scene or project startup setting references this experiment.

## Owner results and remaining acceptance

For the **original 47-pattern commit** `a5b2a2f`, the owner reports:
Godot 4.7.2 scene import PASS; basic Green painting PASS; basic Earth painting FAIL.
Earth painting showed repeated Green centers surrounded by brown. These are
owner graphical observations, not agent verification. They do not accept this
94-pattern revision; all revised checks below are **NOT RUN**.

Follow the [execution policy](../AGENTS.md#godot-execution-safety) and
[testing policy](LOCAL_TESTING.md). No Godot, Native, game, graphical automation,
profiling or benchmarking was run by the agent. Separate explicit authorization
is required for agent execution. No runner, execution or preservation policy changes
are made. Stop on errors or abnormal responsiveness; do not retry automatically.

Open the lab in your editor's 2D workspace, select `PaintingWorkspace`, then native
TileMap > Terrains > **Connect**. No F5/F6 or game launch is needed. Inspect source
0, mode 0 and both center families against the CSV. First test import, then solid
Earth and solid Green regions. **Only after both interiors pass**, perform transition
checks with a filled backing. Empty canvas or the backdrop does not count as Earth.
Test both directions, rotations and reversed brush order using separate work areas.
Direct atlas placement can inspect a candidate but does not verify terrain painting.
Optional Path-mode observations need separate records.

| Test | Expected result | Revised status |
| --- | --- | --- |
| 1 Import | Scene and TileSet load without errors; 94 exact configurations | NOT RUN |
| 2 Earth interior | Continuous brown, no repeated Green centers | NOT RUN |
| 3 Green interior | Continuous green, no unexpected Earth centers | NOT RUN |
| 4 Green islands in Earth | Single-cell and larger Green centers survive | NOT RUN |
| 5 Earth islands in Green | Single-cell and larger Earth centers survive | NOT RUN |
| 6 Straight transitions | Horizontal/vertical boundaries, both directions | NOT RUN |
| 7 Corners | Convex L shapes and concave notches, all rotations/directions | NOT RUN |
| 8 Narrow strips | One-/two-cell widths and bends, both materials | NOT RUN |
| 9 Diagonals | Diagonal cells/checkerboards; record ambiguous selections | NOT RUN |
| 10 Irregular patches | Tips, protrusions, notches and tile curves; reverse brush order | NOT RUN |

Record PASS/FAIL and optional observations per material direction. Mark dependent
tests BLOCKED if import or either interior fails. For every failure record expected
and actual result, selected source/atlas/alternative (or no selection), center ID,
terrain mode, exact backing and brush order, shape/rotation and observations.
Do not automatically add configurations or change center IDs to fix failures.

## Static validation and preservation

Run `python -B -m unittest discover -s tests -p 'static_*test.py'` for the complete
permitted suite; use `-p 'static_native_terrain_47_test.py'` for six focused checks.
They verify original supplied hashes/Markdown agreement; technical source and both
remaps; exact 94/47/47 inventory and 752 peers; atlas/signature uniqueness and two
intentional peer-only overlaps; PNG CRC/dimensions/every sector pixel/transparent
gaps; TileSet/lab references; and production isolation in committed and staged PR
inputs against main baseline `48cd9150d7aa2e029c7328229e7865cf00e83723`.
The focused production check now inspects committed/staged inputs, because the
owner explicitly requested retaining unrelated manual-playtesting edits in place.
Legacy suite assertions on working production bytes remain unchanged.

Revision validation on 2026-10-31:

- **6/6 focused static checks PASS**, including after staging the proposed revision.
- Historical working-tree result at `56e2990`: **113 test methods, 17 failure
  records across 13 methods, 0 errors**. Subsequent isolated diagnosis found
  clean main PASS (107 tests) and clean committed PR #98 FAIL (113 tests, three
  historical guard incompatibilities). Ten original failure records are owner-byte
  preservation conflicts; four are a UID-checker defect exposed by owner header
  declarations, not evidence that those Theme UIDs are invalid. The remaining
  three concern mapping attributes and the historical changed-file whitelist.
  See the [complete investigation and final scope-specific results](PR98_STATIC_TEST_INVESTIGATION.md).
  Proposed test corrections remain local and uncommitted pending owner review;
  the published PR has not been changed by this investigation.
- Direct ZIP-to-transcription comparison, original Green mapping and pixel
  preservation, changed local Markdown targets and staged Git whitespace checks PASS.
- Preservation checks PASS: 21 pre-existing unrelated tracked/untracked files retain
  their exact starting SHA-256 values. Removing only this revision's Earth additions
  and name changes reconstructs the owner's original TileSet bytes exactly.
- No agent Godot import, Native, runtime, graphical, profiling or benchmark execution.

The full-suite failures remain visible for owner review. Proposed corrections
retain exact byte guards and unknown-UID/dev-path rejection; no production
resources or policies are changed to suppress failures. Static
validation does not establish native parsing, terrain matching, visual acceptance
or performance. The exact 94-pattern baseline is internally consistent, but may
still omit patterns needed by particular native painting operations. Do not assume
it solves both directions or is ready for final original artwork until owner tests.
Procedural chunks, halos, generation order and performance remain outside scope.

Existing owner artwork, imports, experimental assets, evidence and six unrelated
modified production resources remain in place and excluded from this revision's
commit. No generated sidecars/caches are staged. The original mapping inputs and
existing exact-path Git attributes are unchanged. Revision files are the PNG,
TileSet, lab, this report, README, focused static test and two new technical
inventories. No merge, cleanup or PR #97 modification is performed.
