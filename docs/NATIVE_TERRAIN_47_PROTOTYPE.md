# Issue #96: native 94-pattern two-material terrain laboratory

PR #98 is accepted by the owner as an isolated technical configuration prototype,
pending explicit owner merge authorization. The 47-pattern filenames and paths
remain stable for references and import UIDs. Production terrain and gameplay are
not integrated or changed. [Issue #96](https://github.com/interneth3ro/the-long-way-home/issues/96)
remains open; [PR #97](https://github.com/interneth3ro/the-long-way-home/pull/97) remains untouched.

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

These two peer-only overlaps are intentional, distinguished by center ID. Owner observations below establish limited editor painting acceptance, not an
exhaustive guarantee for every native Connect selection or brush order.

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

## Owner graphical acceptance and accepted limitation

The original 47-pattern commit `a5b2a2f` passed owner import/basic Green painting
but failed basic Earth painting with repeated Green centers. Those historical
results are separate from these owner-reported 94-pattern results in Godot 4.7.2;
none is agent graphical verification.

| Check | Owner result |
| --- | --- |
| Scene import | PASS |
| Solid Weathered Earth | PASS |
| Solid Low Green Cover | PASS |
| Single-cell Green island inside Earth | PASS |
| Single-cell Earth island inside Green | PASS |
| Initial horizontal boundary, both directions | PASS |
| Initial vertical boundary, both directions | **FAIL**: visible endpoint artifacts |
| Subsequent large-scale painting with overlapping rectangular strokes | PASS |
| Large irregular regions, narrow connections, interior pockets and repainting | PASS; accepted by owner |

Two inspected neighboring atlas tiles, `(8,1)` and `(5,1)`, had compatible shared
corner assignments. The diagnostic artwork produced abrupt narrowing at the
boundary endpoint. This supports a possible artwork/painting-technique explanation,
but the precise cause was **not conclusively established**. Later successful
painting does not turn either initial vertical test into PASS.

The owner accepts this limitation for the configuration-only technical prototype.
It must be revisited before production terrain integration. Exhaustive rotations,
diagonals/checkerboards, one-/two-cell variants and brush-order invariance are not
established by the reported observations. Final illustrated quality, procedural
chunk determinism, chunk-border continuity and production performance are not
accepted by this prototype.

Agent Godot, Native, game, graphical automation, profiling and benchmarking:
**NOT RUN**. Follow the [execution policy](../AGENTS.md#godot-execution-safety)
and [testing policy](LOCAL_TESTING.md); owner acceptance adds no execution permission.

## Static validation and preservation reconciliation

The independently reviewed corrections were published in
`1e5b5ee2a92d75b384ae8c9aa74b8a23a099a898`. This documentation follow-up changes
only README, this report and the [investigation](PR98_STATIC_TEST_INVESTIGATION.md).
Tests, terrain assets, mappings and execution/preservation controls are unchanged.

| Validation scope | Complete static suite | Focused terrain suite |
| --- | --- | --- |
| Clean isolated proposed PR including this documentation | 119/119 PASS; 0 failures/errors | 6/6 PASS |
| Isolated corrected PR overlaid with six exact owner resources | 119 run; 12 failure records across 10 methods; 0 errors: **FAIL** | 6/6 PASS |

Commands are `python -B -m unittest discover -s tests -p 'static_*test.py'` and
`python -B -m unittest discover -s tests -p 'static_native_terrain_47_test.py'`.
The owner-resource representation contains the corrected PR plus exact copies of
the six local production resources, with no cache/save/import overlays. It reproduces
the preserved working-resource discrepancies while leaving the attached main
checkout untouched; it is not the attached main branch's older suite.
The strict working-resource assertions are neither waived nor reported as passing.

Focused checks establish supplied hashes/Markdown agreement; reference transcription
and both remaps; exact 94/47/47 inventory and 752 peers; atlas/full-signature uniqueness;
two intentional peer-only overlaps; PNG CRC/dimensions/every sector pixel/transparent
gaps; lab references; and production isolation against main
`48cd9150d7aa2e029c7328229e7865cf00e83723`. Changed local Markdown links and Git
diff integrity checks pass. Static validation is not engine or runtime verification.

### Six preserved local resources

The owner approved preserving these resources in place, byte-for-byte, outside PR #98:
`assets/ui/b1_theme.tres`, `assets/ui/machine_actions.tres`,
`assets/ui/recipe_chooser.tres`, `dialogue/computer_opening.tres`,
`construction/recipes/ferrite_plate.tres` and `construction/recipes/ferrite_rod.tres`.
Their committed main and PR blobs are identical. Full hashes and the twelve-record
reconciliation are in the [investigation](PR98_STATIC_TEST_INVESTIGATION.md).

The forensic review found all 104 stored chooser properties unchanged. Other
resource differences match serialization/default omissions. All six resource
modification timestamps fall within approximately 107 milliseconds, followed by
matching editor-folding writes. Evidence strongly favors a shared Godot editor
resource-save event; the initiating action and why resources were marked edited
remain unknown. No meaningful resource-property defect was identified statically.
These are explained local preservation discrepancies, not PR changes. Preserve
associated evidence, imports, owner artwork, saves and ignored material unchanged.
No normalization, restoration, cleanup or owner-resource commit is authorized.

## Merge readiness and remaining Issue #96 work

**CLEAN for owner-controlled merge as an isolated technical prototype**, following
successful final static/preservation verification and explicit owner merge authorization.
The accepted vertical-boundary limitation and explained local byte discrepancies
do not block this limited acceptance. PR #98 remains draft until the owner chooses
its next review/merge action. No merge or cleanup is performed by this update.

Issue #96 is not completed or closed. Remaining work includes production-renderer
integration, original illustrated terrain quality and organic transitions,
reduced repetition, procedural chunk determinism/continuity across generation
orders and coordinates, and separately authorized production performance acceptance.
Revisit vertical endpoints and expanded transition/brush-order coverage before
integration. No new terrain features, artwork, runtime behavior or policies are
introduced by this documentation follow-up.
