# Cuprite visual prototype v1

Implemented on `codex/cuprite-visual-prototype-v1`, pending merge. The owner
reported F5 PASS for overall artistic direction, transparency and terrain blending
at the original `1/6` scale, but found the deposit too small beneath the Extractor.
The owner requested a 35% uniform increase to `0.225`. This adjusted scale remains
provisional pending another owner F5 evaluation.

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
y = 204.8 to 435.2. The center remains `(-96, 320)` and the stationary Extractor
reference is unchanged. The deposit renders at z = -5, above terrain
and below ground objects, without terrain tint. Linear filtering supports the
reduced illustrated artwork.

Static geometry inspection places this canvas clear of the ship/hatch, arrival
spawn, rocks, introductory Ferrite artwork/footprint and its inspection trigger.
It remains inside the existing protected crash-site clearing; no protection,
generation or collision geometry is changed. It does not reserve construction
space: normal gameplay may place other objects over this visual during play.
Visual coverage and readability at the adjusted scale await owner F5 evaluation.

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
units, centered on the deposit: world-local `(-160, 256)` to `(-32, 384)`.
The bottom-center art/sorting anchor is `(-96, 384)`.
It has no script, animation, collision, interaction, inventory, production or
simulation registration. It cannot be mined with, recovered or inspected as a
machine. The real Extractor implementation and artwork remain unchanged.

Cuprite has no ResourceDeposit registration, construction highlight, mining,
depletion, inventory item, recipe, research or progression. Existing Extractor
placement still requires compatible Ferrite ground; this reference does not
demonstrate functional Cuprite mining. Persistence and publication-journal code
are outside this change.

## Validation and owner F5 checklist

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

No Godot editor, headless engine or game execution is included. The owner can:

1. Start the existing application with F5 and reach the exterior normally.
2. Locate Cuprite southeast of the exit, west of the introductory Ferrite.
3. Check transparency, painted rim/shadow, ground blending and provisional scale.
4. Enable the stationary reference in the Inspector, save and repeat F5; assess
   whether the Extractor covers most of the mineral core with useful visible edges.
5. Hide the reference and confirm the unobstructed artwork remains available.
6. Confirm arrival, hatch access, Ferrite discovery and normal Ferrite Extractor
   placement/production still behave as expected, with no new engine errors.

Overall artistic direction, transparency and blending passed the owner's original
F5 evaluation. Coverage and artistic acceptance at `0.225` remain pending the next
owner F5 evaluation; this is not final scale approval.
Reversal requires removing the single exterior instance/resource reference and
these prototype-specific scene/asset/document files; no simulation migration exists.
