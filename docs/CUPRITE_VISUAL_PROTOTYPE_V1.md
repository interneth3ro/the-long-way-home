# Cuprite visual prototype v1

Implemented on `codex/cuprite-visual-prototype-v1`, pending merge in PR #180.
The owner reported final F5 **PASS** against visual configuration `ecdeb4b` and
artistically accepted the terrain blending, mineral coloration, footprint and
occupied appearance. Freeze this configuration as **Cuprite Deposit Visual
Prototype v1**: uniform scale `0.225`, `DepositArtwork` offset `(0, 16)`, prototype
location `(-96, 320)` and unchanged stationary Extractor reference. No further
artwork or scale adjustments are authorized in this PR. Future artwork variations
and functional resource generation are separate work.

## Artwork and placement

The owner supplied the standalone 1536 x 1024 RGBA PNG. The
[project copy](../assets/environment/exterior/cuprite/cuprite_prototype_v1.png)
preserves its original bytes, including alpha and painted margins. Source and
copy SHA-256: `6a3ed462b0da325b0dc334b0fb0f5d467242d7758dbd71bfe2aa46dff8b531fe`.
No regeneration, recoloring, cropping or baked scale change is involved.

The [prototype scene](../scenes/world/cuprite_visual_prototype.tscn) is instanced
under `GroundObjects` in the [existing exterior](../scenes/world/planet_exterior.tscn)
at world-local `(-96, 320)`, southeast of the ship exit and west of introductory
Ferrite. The centered sprite uses uniform `0.225` scale: its full canvas is
345.6 x 230.4 world units, bounded by x = -268.8 to 76.8 and
y = 220.8 to 451.2. `DepositArtwork.position = Vector2(0, 16)` places the canvas
center at `(-96, 336)`. The prototype root remains at `(-96, 320)` and the
stationary Extractor reference is unchanged. The deposit renders at z = -5, above terrain
and below ground objects, without terrain tint. Linear filtering supports the
reduced illustrated artwork.

Static geometry inspection places this canvas clear of the ship/hatch, arrival
spawn, rocks, introductory Ferrite artwork/footprint and its inspection trigger.
It remains inside the existing protected crash-site clearing; no protection,
generation or collision geometry is changed. It does not reserve construction
space: normal gameplay may place other objects over this visual during play.
Visual coverage and readability are covered by the owner's artistic acceptance.

The import sidecar follows existing Ferrite texture parameters: lossless
compression (`compress/mode=0`), no mipmaps, unchanged alpha channel mapping,
alpha-border correction, no premultiplied alpha and no size limit. The original
PNG remains untouched. Import settings are unchanged by the scale adjustment;
the owner reported successful F5 transparency and blending at the original scale.
The agent has not run Godot or independently verified texture import.

## Stationary Extractor scale reference

Open `planet_exterior.tscn` and expand
`GroundObjects/CupriteVisualPrototype/ExtractorReference`; Editable Children is
enabled for the prototype instance. Toggle **Visibility > Visible** in the
Inspector to show or hide the reference. It is hidden by default. Alternatively,
open the prototype scene and change the same node's visibility there. Save the
scene before an owner-performed F5 check. No agent engine launch is authorized.

The reference consists solely of Node2D and Sprite2D nodes reusing the existing
0-degree Extractor body, raised barrel and foreground textures, offsets and
display scale. Its 4x4 construction-cell guide corresponds to 128 x 128 world
units: world-local `(-160, 256)` to `(-32, 384)`. Its implied extraction point
and footprint center remain at the prototype root `(-96, 320)`, 16 world units
above the offset painted canvas center. The bottom-center art/sorting anchor
remains `(-96, 384)`.
It has no script, animation, collision, interaction, inventory, production or
simulation registration. It cannot be mined with, recovered or inspected as a
machine. The real Extractor implementation and artwork remain unchanged.

Static transform inspection confirmed the reference matches a normally deployed
0-degree Extractor in its raised pose. Read-only pixel analysis estimated the
Cuprite bright-mineral center approximately 4-6 world units above its original
canvas center, while the Extractor body's alpha-weighted center lies roughly
14 world units below its footprint center. These visual proxies indicate a
compositional imbalance, not a reference-registration error. Moving only the
deposit sprite down 16 world units is the owner-accepted visual correction that
preserves normal Extractor placement conventions, the root and all source bytes.

Cuprite has no ResourceDeposit registration, construction highlight, mining,
depletion, inventory item, recipe, research or progression. Existing Extractor
placement still requires compatible Ferrite ground; this reference does not
demonstrate functional Cuprite mining. Persistence and publication-journal code
are outside this change.

## Validation and owner F5 checklist

Final focused review confirmed the six-file PR scope, accepted scene properties,
unchanged reference registration, source PNG identity and all four protected UID
hashes. No gameplay, collision, generation, persistence or publication-journal
implementation files are part of the PR. Seven local playtest-modified files
remain preserved and outside the committed PR diff.

Owner-accepted, non-blocking historical test exception: the existing
`FerriteIntegrationStaticTest.test_other_exterior_nodes_and_resource_fields_are_unchanged`
passes against the committed `main` exterior but fails against the committed PR
exterior. Its historical node-set equality does not permit the added Cuprite
instance. This comparison was checked with only the scene input replaced by each
committed version in memory, preserving local playtest files. The full historical
suite was not run. The owner explicitly accepts this expected failure because
PR #180 intentionally introduces the Cuprite presentation node; it is not
considered a gameplay regression. The historical test, test runner and Ferrite
implementation must remain unchanged for this prototype. This exception is
limited to the identified failure and does not claim a full-suite PASS. With
the focused review checks and owner artistic acceptance recorded, no other known
merge blockers remain. Merge still requires explicit owner authorization.

Agent checks are static only: byte/hash and PNG structure checks, scene/resource
references and node types, registration arithmetic, import-parameter comparison,
changed-file scope, Markdown links and whitespace. Static checks do not establish
Godot parsing, successful texture import, gameplay or graphical correctness.
The four owner-exempted untracked persistence/test `.gd.uid` files are preserved
outside the change and checked against their preflight SHA-256 hashes.

Focused existing Python checks passed: all six Extractor animation source tests
plus the two Ferrite integration checks for extraction-point edge/rotation cases
and Extractor occupancy/shared geometry (8 tests total). Prototype-specific
console checks passed for PNG integrity/full alpha decode, exact source-copy
identity, scene references and static-only node types, reference registration,
import parameters, unchanged pre-existing exterior content, location clearance,
documentation links, changed-file scope and all four exempt UID hashes.
The full historical static suite was not run; its exact exterior snapshot guards
do not account for this new presentation instance. No snapshot pins or runner
controls were changed for this prototype.

For the 35% scale adjustment, focused static checks verify the exact scale-only
scene change, recalculated canvas/bounds and clearance, original PNG byte/hash
identity, unchanged reference/center, documentation links and whitespace. All four
protected UID hashes and the seven pre-existing playtest-modified files are checked
unchanged; those playtest edits are excluded from the adjustment commit.

For the artwork alignment adjustment, focused static checks verify that the only
scene change is `DepositArtwork.position = Vector2(0, 16)`, with unchanged `0.225`
scale, root, reference registration and source PNG. Recalculated bounds, clearance,
documentation links, whitespace, protected UID hashes and pre-existing local-edit
hashes are checked; local playtest edits remain outside the alignment commit.

No Godot editor, headless engine or game execution is included. The owner can:

1. Start the existing application with F5 and reach the exterior normally.
2. Locate Cuprite southeast of the exit, west of the introductory Ferrite.
3. Check transparency, painted rim/shadow, ground blending and accepted scale.
4. Enable the stationary reference in the Inspector, save and repeat F5; assess
   whether the Extractor covers most of the mineral core with useful visible edges
   and a better balance of exposed Cuprite above and below the machine.
5. Hide the reference and confirm the unobstructed artwork remains available.
6. Confirm arrival, hatch access, Ferrite discovery and normal Ferrite Extractor
   placement/production still behave as expected, with no new engine errors.

The owner reported final F5 PASS for the accepted configuration above. This records
overall artistic acceptance, not an itemized gameplay-regression result for every
historical checklist entry. Agent validation remains static only. Merge and engine
execution still require explicit owner authorization.
Reversal requires removing the single exterior instance/resource reference and
these prototype-specific scene/asset/document files; no simulation migration exists.
