# Interior V2 automatic-transition preview

Feature-branch implementation, pending merge and owner acceptance. No test below
is premarked passed. Follow the [execution safety policy](../AGENTS.md#godot-execution-safety);
these owner-operated instructions do not authorize agent engine execution.

Open [ship_interior_v2_transition_preview.tscn](../scenes/dev/ship_interior_v2_transition_preview.tscn)
and press **F6 (Run Current Scene)**. Keep the project main scene unchanged.
This host instances production Dave, camera, PlaythroughState and the real
SceneTransitionController script. Progression is session-local; the preview
does not read or write saves. There are no factory objects, Computer interactions,
new objectives or narrative events in these minimal worlds.

The previous [scale and collision previews](INTERIOR_V2_PREVIEW.md) remain
available and unchanged. The approved V2 scene, its artwork, nine manifest
hashes and all its collision shapes remain unchanged. A new development-only
wrapper instances V2 at **1.25x** and supplies the transition contract at an
unscaled root. Dave remains at original scale, including radius-10 feet centered
at `(0,-10)`. Initial ground position is `(-110,28.75)`.

## Routes and controls

| Control | Action |
| --- | --- |
| WASD / arrows | Existing movement; walk into doorway thresholds without E |
| Mouse wheel | Existing camera zoom |
| C | Toggle actual physics outlines and orange trigger rectangle outlines |
| H | Toggle HUD (world filename, busy state, completion count, Dave position) |
| F7 | Request an intentionally absent test scene; expect warning and recovery |
| F8 | Request an absent spawn in the other test world; expect warning and recovery |
| X | Request cancellation before fade-in; HUD reports whether accepted |

F7/F8 do not change authored files, saves or production state. They intentionally
emit a rejection warning. No completion should be counted. Step out/reenter a
door after any interrupted entry. Failure probes retain Dave's source position.
X is accepted during fade-out/opaque preparation, restoring the source under
black. Fade-in commits the destination; X then returns false and normal completion
continues. The nominal 0.15-second window is short; owner testing can temporarily
adjust `SceneTransitions.quick_fade_seconds` in the Remote Inspector, then restart
to restore the authored value. No automated/prolonged runtime probe is provided.

| Source / entry threshold center | Destination | Safe arrival ground origin |
| --- | --- | --- |
| V2 wrapper maintenance `(-684,-50)`, rectangle 24x70 | Blue maintenance test world | `Spawns/FromInterior (0,100)` |
| Maintenance return `(0,210)`, rectangle 100x18 | V2 wrapper | `Spawns/FromMaintenance (-600,-45)`, facing east |
| V2 wrapper exterior `(-16,402)`, rectangle 100x18 | Brown exterior test world | `Spawns/FromInterior (0,100)` |
| Exterior return `(0,210)`, rectangle 100x18 | V2 wrapper | `Spawns/FromExterior (-16,340)`, facing north |

Both minimal destinations have closed rectangular collision boundaries and a
labeled floor with an orange return pad. All coordinates above are world units
in the new unscaled wrappers. The V2 maintenance barrier remains at x=-710 and
the exterior barrier at y=428.75. Narrow trigger strips sit on their accessible
side; no barrier is disabled or moved. C shows actual shapes; outlines are only
presentation. V2 retains the existing preview's above-art Dave presentation;
prop occlusion is still deferred. The wrapper GroundObjects intentionally does
not sort Dave among full-canvas overlays.

## Ownership and compatibility

[AutomaticDoorway](../scenes/interaction/automatic_doorway.gd) is a reusable
Area2D, layer 0/mask 1, outside the intentional-interaction interface. It filters
aggregated overlaps by identity against the controller's persistent Dave. Other
bodies/areas do not request travel. No E input or prompt is introduced. Production
Computer/machine interactions retain their existing E interface.

Each entry begins waiting for separation. Only a confirmed empty Dave overlap
arms it; the next overlap makes one request. Rejected entries require exit/reentry
and can never request every frame. Busy transitions reset arming. Reattachment
resets the component in `_enter_tree`, including cached worlds where `_ready`
does not repeat. Two physics callbacks allow overlap registration after reattach
or a locked teleport before observing separation. These are physics synchronization
steps, not a timed cooldown. Holding movement through unlock can resume naturally;
arriving overlapping an area still requires separation before reentry.

The controller appends **QUICK_FADE (2)**, retaining **IMMEDIATE (0)** and
**FIRST_EXTERIOR_REVEAL (1)**. Quick transitions synchronously clear interaction
requests and velocity, disable Dave's inherited processing/input, then defer
mutations. Fade out **0.15 seconds**, validate scene identity/GroundObjects/named
Marker2D, swap/reparent under opaque black, apply the existing arrival hook,
reset/force camera scroll and allow destination physics registration. Fade in
**0.15 seconds**, clear pending interaction/velocity again and restore Dave's
prior processing mode. Only successful quick travel emits transition_completed.

The source remains attached on missing scene/load/contract rejection. Newly
instantiated invalid worlds are freed; cached valid worlds remain cached.
Cancellation before reveal either keeps the source or rolls back under black;
controller teardown restores Dave's saved processing mode. No global pause or
synthetic key release is used. The quick path does not write progression flags.
The original transition body still owns immediate travel and the **0.65-second**
first-exterior cinematic, including its original progression update. Production
main, worlds, hatch scripts, Dave, project startup and scene references are
unchanged. No production scene points to these development destinations.

The initial cached world is the wrapper PackedScene's actual `scene_file_path`,
not the nested V2 art scene path. All reciprocal destinations use that same
wrapper path. This avoids initial-world identity mismatch and duplicate V2
instances on return. The host initializes the existing controller only after
its children are ready. It does not implement a second transition controller.
The wrapper's existing `prepare_for_arrival` hook sets V2 inward facing before
fade-in; production Dave's script and movement remain unchanged.

## Static evidence and limitations

Run `python -B tests/static_automatic_transitions_test.py` and
`python -B tests/static_port_console_geometry_test.py` from the repository root.
They read scene/script/resource text and hash assets; they do not execute Godot
or gameplay. The 11 new checks cover reference/load-step integrity, reciprocal
contracts, identity/host wiring, nine approved hashes, spawn separation, sampled
radius-10 route clearance, destination boundaries, overlap/rearm guards,
duplicate/input-lock ordering, fade isolation, failure and cancellation paths.
The seven existing console/container geometry checks remain applicable.

Control-flow string assertions are static regression tripwires. Sampled geometry
and code review do not establish engine parsing, collision response, event order,
held-input handling, cached-world behavior, cancellation, or gameplay success.
No Godot editor/import, headless, graphical, engine/type, playable-scene,
performance or runtime test was performed by the agent. Missing GroundObjects,
non-Node2D/load failures and cancellation rollback receive static review; F7/F8
exercise only missing-scene/spawn recovery when run by the owner.

## Sequential owner acceptance (one report at a time)

Report **Test N: PASS/FAIL**, observed behavior and any Godot errors after each
step. Wait for that report before proceeding; do not infer passes from static
checks. Start with Test 1. None of the following has been run by the agent.

1. **Isolated launch:** F6 the transition preview. Confirm unchanged V2 art,
   1.25x scale and collision, no Godot errors and no normal-game cutover.
2. **V2 to maintenance:** Walk into the left threshold without E. Confirm a
   quick fade and safe arrival in the labeled blue maintenance test environment.
3. **Maintenance to V2:** Deliberately approach its orange return pad. Confirm
   the east-facing inward V2 arrival, correct camera and no bounce-back.
4. **V2 to exterior:** Walk into the bottom threshold without E. Confirm a quick
   fade and safe arrival in the labeled brown exterior test environment.
5. **Exterior to V2:** Return deliberately. Confirm the north-facing safe V2
   spawn, correct camera and no trigger loop.
6. **Repeated travel and held input:** Cycle both routes, revisiting cached
   worlds. Hold movement and try E through fades. Confirm one completion per
   trip, no movement/interaction while locked, natural held movement after unlock,
   no duplicates, stuck controls or unintended reciprocal retriggers.
7. **Boundaries/failures:** With C outlines, approach solid doorway barriers
   without escaping. From clear floor use F7 then F8 separately: confirm warning,
   original world/position, transparent curtain, restored movement and no new
   completion. Try X during a subsequent fade-out; confirm source recovery and
   usable doorway after exit/reentry. V2 has no intentional object interactions;
   verify non-door E behavior in production during Test 8. Do not alter saves or
   production data to simulate failures.
8. **Production regression:** Stop preview; F5 normal game. Verify the original
   interior, real E hatch travel, Computer, inventory, objectives and factory
   gameplay. Verify the original special first-exterior reveal where testable.
   Report unavailable scenarios explicitly; do not premark them passed.
