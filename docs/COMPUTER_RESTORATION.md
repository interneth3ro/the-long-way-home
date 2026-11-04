# Computer restoration — implementation pending owner acceptance

Prepared on `codex/computer-restoration` from clean, synchronized main
`993ffc14c1fad1032227801870cd3a3fce50f7a5` (PRs #147 and #148 included).
This feature remains pending merge and owner normal-F5 acceptance.

## Approved content and requirements

The owner-supplied `TLWH_Computer_Restoration_Codex_Handoff.md` is the implementation
brief. Its section 6 reproduces the four locked scenes from
`TLWH_Computer_Restoration_Story_and_Decisions(1).md`, originally attached to
[issue #46](https://github.com/interneth3ro/the-long-way-home/issues/46).
The handoff reproduction supplies this implementation's narrative provenance;
the original canonical attachment was not independently retrieved or modified.
All 39 spoken lines, speakers, scene titles, order and stage directions are
preserved in [editable narrative content](../dialogue/computer_restoration.json).
A golden content digest in the [static checks](../tests/static_computer_restoration_test.py)
protects that script. The three inspection lines are also locked there.

The newer approved **4 Ferrite Plates + 4 Ferrite Rods** supersedes the historical
canonical **6 Plates + 8 Rods**. The dedicated compact repair panel supersedes
the historical dialogue-choice concept. Bearings are not required. Quantities
come exclusively from current Materials inventory, not machine storage or
lifetime production. Manufacturing upgrades and conduits remain future work.

## State and presentation

- `PlaythroughState` owns session-only opening/inspection completion, restoration
  and cinematic completion. No saving is introduced. Opening dismissal retries
  the original conversation; inspection dismissal retries its entire exchange.
  The opening conversation must complete before inspection, even after early
  outside progression. First Plate acquisition unlocks inspection. Before that,
  repeat completed-opening interactions use the existing damaged-system response.
- The dedicated [Computer presenter](../scenes/ui/computer_restoration.gd) routes
  only the existing Computer target. It uses existing B1 theme, B2 frame,
  scaling, focus, interaction distance and detector selection. Subsequent
  completed-inspection interactions open the panel. Counts refresh on inventory
  changes; confirmation is disabled until sufficient. Not yet/Esc consumes nothing.
  Leaving range closes the panel. Modal guards prevent competing inventory,
  hotbar/construction, interaction and hatch requests during repair presentation.
- `restore_computer()` validates both material definitions, identities and current
  quantities. The existing `InventoryState.remove_items(..., false)` stages both
  removals on private dictionary copies and commits only if the whole batch
  succeeds. The reentry guard and restored state precede every notification.
  Exactly one milestone and one inventory notification publish the committed
  transaction. Cancellation/failure cannot partially consume items.
- Main completes `restore_computer` on the committed restoration signal. Before
  repair, first Plate guidance uses live 4+4 readiness and reverses when materials
  are spent. Prior factory stages retain their precedence. The overarching
  objective remains active until repair succeeds.
- The presenter locks Dave's process mode and suspends/hides competing persistent
  presenters while preserving their prior visibility/process modes. A 0.35-second
  black fade covers the artwork switch, followed by a 0.35-second reveal. Existing
  V2 room-sized overlays retain their transforms and collision; the legacy F6
  sprite uses its existing repaired artwork. Arrival reapplies visuals from
  committed playthrough state. Old artwork is preserved.
- A separate instance of the existing dialogue scene shows full text immediately.
  Automatic entries reject Advance/Dismiss and hide those buttons. Ordinary
  conversations retain their manual controls and completion signals. Spoken
  duration is length/15 characters per second, clamped to 2.5–8 seconds. Scene
  gaps are 1.5 seconds. Stage directions are unspoken italic captions with
  1.5-second pauses, brief display flickers where directed, and a quiet generated
  electronic hum. There are no camera tracks or voice-over. This restrained
  presentation and its timing need owner acceptance.
- Only normal completion activates `restore_ship`, **Restore the Ship**, with
  `Investigate how to improve manufacturing capabilities for ship repairs.`
  The tracker is suppressed until activation is complete; its pin/hide preference
  survives. No research or machine upgrades unlock. Later Computer interaction
  supplies one concise operational response and cannot replay repair or the script.
- Completion or teardown kills presentation tweens, stops audio, removes playback,
  clears the fade and restores prior input/UI modes. Interrupted presentation
  never refunds or reverts the committed repair and does not falsely signal
  narrative completion. Ordinary travel is blocked during playback; externally
  removing the world/presenter aborts presentation without replay. A destroyed
  playthrough starts fresh as before. There is no persistent recovery/save system.

## Verification limits

Static checks inspect content, source order, scene references, overlay dimensions,
modal guards and cleanup wiring. They do not parse GDScript with Godot or prove
runtime input, audio, travel, layout or gameplay behavior.
[Transaction runtime regressions](../tests/computer_restoration_test.gd) cover
shortages, readiness reversal, opening/inspection gates, exact/surplus consumption,
reentry from both signal types, idempotent completion, rejected batches, definition
identity and second-ingredient failure. They remain **unexecuted** and outside
the authorized Native test inventory.

Native import/recipe-switching verification is **NOT TESTED**: new/changed static
checks require owner review under the [execution policy](LOCAL_TESTING.md#authorization-and-standing-scope)
before Native use. No runner, allowlist, native assertion, engine command or
execution permission was changed. Graphical/normal-F5 acceptance remains with
the owner. No agent graphical launch or performance probe was performed.

## Owner normal-F5 acceptance

All items currently **NOT TESTED**; no owner observations received yet. Record
PASS/FAIL and observations individually. Keep the PR draft until owner acceptance
and separate approval to mark ready/merge.

| # | Check | Result | Observations |
| --- | --- | --- | --- |
| 1 | Existing opening conversation and outside-investigation guidance intact | NOT TESTED | Pending owner F5 |
| 2 | First Plate unlocks exact inspection once; dismissal retries; later panel direct | NOT TESTED | Pending owner F5 |
| 3 | Before unlock, damaged feedback; correct range/prompt | NOT TESTED | Pending owner F5 |
| 4 | Panel style, scaling, focus, cancel and modal exclusivity | NOT TESTED | Pending owner F5 |
| 5 | Live Materials counts; insufficient confirmation disabled; spending reverses readiness/guidance | NOT TESTED | Pending owner F5 |
| 6 | Exact 4+4 consumed once; repeated confirmation cannot consume again | NOT TESTED | Pending owner F5 |
| 7 | Fade covers aligned repaired visual; persists after hatch travel | NOT TESTED | Pending owner F5 |
| 8 | Four canonical scenes, correct speakers/order, readable timing and scene gaps | NOT TESTED | Pending owner F5 |
| 9 | No movement, conflicting UI, travel or skip during playback; controls restored | NOT TESTED | Pending owner F5 |
| 10 | Restore Computer completes on repair; exact Restore the Ship follows cinematic | NOT TESTED | Pending owner F5 |
| 11 | Operational Computer dialogue; no repair/opening/cinematic replay | NOT TESTED | Pending owner F5 |
| 12 | Factory, inventory, camera, transitions, controls and gameplay unchanged outside feature | NOT TESTED | Pending owner F5 |
