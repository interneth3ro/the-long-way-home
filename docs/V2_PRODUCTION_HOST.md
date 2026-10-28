# V2 production host — P1 through P8

P1 merged in PR #59; P2 Computer parity merged in PR #60; P3 stationary-machine
integration merged in PR #61 (`96f47e4`). P4 Extractor recovery merged in PR #62
(`bf18f09`). P5 Smelter recovery merged in PR #63 (`59275b0`).
P6 Fabricator recovery merged in PR #64; the verified post-P6 baseline is
`e14703e64aef961f18feba8a616acec00c4f069e`. The owner approved P7 after a
continuous six-phase rehearsal, **6/6 PASS (owner-reported)**. P8 is implemented
on `codex/p8-f5-production-cutover`, pending owner cutover acceptance and merge.

**F5 / Run Project** now starts V2 Primary through `scenes/main/main_v2.tscn`.
**F6 / Run Current Scene** with that scene open also starts V2. For the explicit
**legacy F6 fallback**, stop the game, open `scenes/main/main.tscn` and press F6.
F5 stays configured for V2. This is an editor workflow, with no startup selector.
Computer repair remains deferred. Agent validation is static only; no Godot
launch or P8 runtime acceptance is claimed.

**P7 Observation #1 remains nonblocking and unfixed.** See the
[observation and P8 scope](#p8-production-cutover-feature-branch-pending-merge)
for the deferred outside/Ferrite guidance correction.

Follow the [execution policy](../AGENTS.md#godot-execution-safety); this guide
does not authorize agent Godot execution. Main retains movement, camera zoom,
inventory and UI input. No harness HUD, C/H controls or failure probes are added.

## Architecture gate and ownership

The V2 production scene inherits Main; its [script](../scenes/main/main_v2.gd) extends
Main's script. In `_enter_tree`, it replaces only the inherited opening instance
under `Worlds`, before children enter/ready. The legacy opening never readies in
this host. No file or authored asset is removed. In `_ready`, it calls Main's
existing setup exactly once, then positions Dave at Initial, applies the room's
arrival-facing hook and resets camera smoothing/scroll.

Main's inherited `@onready` DialogueUI reference is captured before initialize
reparents Dave. Construction, MachineUI, DeveloperCoordinates and SceneTransitions
retain inherited exported player references. No binding uses a new Dave path
after reparenting. The coordinate display is disabled in the V2 production scene.
There is one inherited Dave/camera, PlaythroughState/planet/inventory,
ObjectiveController, tracker, musing UI, inventory UI, Construction, MachineUI and
SceneTransitionController. P4/P5/P6 reuse existing Extractor/Smelter/Fabricator
recovery transactions;
there is no second inventory owner or new progression state.

The production-owned wrappers inherit the approved reusable rooms:

- [production_ship_interior_v2.tscn](../scenes/world/production_ship_interior_v2.tscn)
  inherits `ship_interior_v2.tscn`.
- [production_maintenance_bay_v2.tscn](../scenes/world/production_maintenance_bay_v2.tscn)
  inherits `maintenance_bay_v2.tscn`.

Both roots scale art, collision, markers and triggers uniformly by 1.25. Each adds
`GroundObjects` at 0.8, so `1.25 * 0.8 = 1`. Existing transform-preserving
reparenting retains Dave's world scale, radius-10 feet collision, camera and
movement. The shared [arrival presenter](../scenes/world/v2_room_arrival.gd)
uses the nearest spawn marker's `metadata/facing` for idle facing through the
existing `prepare_for_arrival(player, planet)` hook. It owns no route/state.

Only production Primary disables the MaintenanceDoorBarrier shape. Its new
exterior trigger lies inside the retained exterior barrier. Reusable defaults,
closed-door artwork and the reserved upper Maintenance door remain unchanged.
P2 adds only the Computer interaction described below. P3 adds the stationary
presentation and initially dormant targets described below; P4 activates only
Extractor recovery; P5 activates Smelter recovery; P6 activates Fabricator recovery.
Approved machine
assets/transforms, legacy worlds,
exterior scene/script/simulation and PR #54's harness remain unchanged.

## Routes and arrival contracts

Destinations are actual PackedScene paths, never rewritten `scene_file_path` or
logical IDs. The controller caches these exact wrapper identities, including the
initial room. Cache, cancellation, rollback, fades, locks and teardown are unchanged.

| Source | Destination under `res://scenes/world/` | Arrival | Presentation |
| --- | --- | --- | --- |
| Primary Maintenance doorway | `production_maintenance_bay_v2.tscn` | `Spawns/FromInterior` | Existing QUICK_FADE (0.15s each way) |
| Maintenance Interior doorway | `production_ship_interior_v2.tscn` | `Spawns/FromMaintenance` | Existing QUICK_FADE |
| Primary Exterior doorway | `planet_exterior.tscn` | `Spawns/FromShip` | Existing FIRST_EXTERIOR_REVEAL |
| Exterior Hatch (E), V2 F5/F6 | `production_ship_interior_v2.tscn` | `Spawns/FromPlanet` | Existing IMMEDIATE |
| Exterior Hatch (E), legacy F6 | `ship_interior.tscn` | `Spawns/FromPlanet` | Existing IMMEDIATE |

The host listens only to `Worlds.child_entered_tree`. When the actual exterior
attaches, including cached revisits, it configures that instance's existing
`GroundObjects/Hatch.destination_scene` and `destination_spawn`, before arrival
and input unlock. Source identity and presentation stay unchanged. The legacy
host has no listener; the exterior's authored legacy return stays byte-preserved.
There is no alternate exterior scene, simulation or routing controller. The
existing PlaythroughState flag still controls first reveal and session reset.

| Marker | Room-local ground position | World at 1.25x | Facing |
| --- | --- | --- | --- |
| Primary Initial (provisional) | `(0, 80)` | `(0, 100)` | North, into room |
| Primary FromMaintenance (inherited) | `(-480, -31.5)` | `(-600, -39.375)` | East |
| Primary FromPlanet (provisional) | `(-13, 281)` | `(-16.25, 351.25)` | North |
| Maintenance FromInterior (inherited) | `(550, 41)` | `(687.5, 51.25)` | West |
| Exterior FromShip (unchanged) | `(-384, -64)` | `(-384, -64)` | Existing retained facing |

Initial and FromPlanet were provisional at P1. The owner later approved P7
after the 6/6 continuous rehearsal; P8 retains these positions for cutover checks.
Static feet-circle checks clear Primary walls, polygons
and capsule at all three Primary markers, and sample the exterior approach at
native x=-13, ground y=281..339. The exterior threshold center is `(-13, 323)`,
size `(170, 16)`. Initial/return markers are outside both Primary triggers.
Existing tests cover compartment arrivals and approach paths. Existing doorway
separation/rearm behavior remains. These checks do not establish navigation feel.

## P1 static verification and owner acceptance (historical)

```text
python -B tests/static_v2_production_host_test.py
python -B tests/static_v2_connection_test.py
python -B tests/static_automatic_transitions_test.py
python -B tests/static_port_console_geometry_test.py
git diff --check
```

All 29 static checks pass (5 new, 24 existing): transitive resource references,
declarations, no development dependency, routes/markers, composition/order,
scale, facing and geometric clearance. SHA-256 comparison checks baseline assets,
scenes/scripts, sidecars, construction, narrative, inventory, objectives, world
code and project settings; PNG bytes are exact, text uses Git CRLF normalization.
Markdown links and final scope are checked separately. No Godot or project code
was executed. Engine parsing, inherited overrides, startup signals, physics,
fades, camera continuity and gameplay remain unverified. No runtime, headless,
graphical or performance test was performed; no owner PASS is inferred.

Report **Test N: PASS/FAIL**, observations and errors one test at a time. Resolve
failures before proceeding. Merge approval is separate.

1. F6 the host. Accept/revise Initial spawn/facing; confirm Primary at 1.25x,
   camera and no errors.
2. Inspect Primary artwork/collision, Dave effective scale, movement and camera.
3. Travel Primary -> Maintenance automatically; verify fade, arrival, rearm and locks.
4. Travel Maintenance -> Primary; verify arrival, inward facing and controls.
5. Travel Primary -> exterior; verify first reveal and FromShip spawn.
6. E at exterior hatch -> Primary V2; accept/revise FromPlanet. Never legacy cabin.
7. Repeat room/exterior round trips; verify one Dave/camera, UI, safe arrivals,
   no duplication and no stuck locks.
8. Inspect cached-room lifecycle and supported cancellation/rollback with safe,
   focused owner checks; report unavailable cases. No stress/freeze probes.
9. Stop opt-in; F5 legacy. Verify original rooms, Computer, machine recovery/
   progression and original exterior return.

P1 stopped before Computer migration, stationary machine integration, progression
changes, save/load, eviction, F5 cutover or retirement. The opt-in host and wrappers
are later retirement-audit candidates; no deletion or cleanup is authorized here.

## P2 Computer interaction parity (merged PR #60)

The production wrapper alone adds `ProductionShipInteriorV2/ComputerInteraction`,
a nonblocking `Area2D` using the existing
[WorldInteractable](../scenes/interaction/world_interactable.gd) script directly.
It uses layer 1, mask 0, no monitoring, and a centered 64x8 local rectangle.
There is no new adapter script, visible console or solid footprint. The reusable
room, all previews, legacy Computer, approved art and collision remain unchanged.
`VisualContent/ComputerDamaged` stays visible; `ComputerRepairedInactive` stays
hidden. No repair transaction or overlay switching is implemented.

The **owner-accepted provisional** area position is room-local `(0, -214)`, world `(0, -267.5)`
at 1.25x, with `interaction_point = Vector2(0, 0)`. The solid base spans
x=-178..172, y=-277..-222 locally; the proxy spans x=-32..32, y=-218..-210.
It sits entirely in front of the base with a 4-local-unit gap. Dave's detector
and feet center are 10 world units above his ground origin. Along the central
approach, ground y=-111..-197 locally yields detector-to-point distances
118.75..11.25 world units, within the unchanged 120-unit search radius. The
45-unit amendment limits Computer eligibility to the closer part of that approach
(centerline ground y=-170 or closer). The sampled
approach from Initial clears permanent collision; the front ray reaches the
area before the base or wall. Area queries and rays already include areas,
and require the selected target to be the first hit on mask 1. The proxy does
not block Dave. The owner accepted the initial placement and interaction in the
seven initial tests; the amended 45-unit range still requires owner verification.

The optional `WorldInteractable.max_interaction_distance` is a cap in **world
units**, default 0 (retain existing detector behavior). Only this Computer sets
it to **45.0** in P2; P3's dormant machine targets also use that initial reference.
The detector retains its 120-world-unit search radius and compares
its existing `global_position.distance_squared_to(body.to_global(interaction_point))`
against `min(120 * 120, 45.0 * 45.0)`, with no extra room-scale multiplication.
Out-of-range candidates are skipped before nearest-target selection and the
unchanged line-of-sight ray. The same target refresh clears/reselects the target,
updates the prompt, and precedes queued E dispatch on each physics callback.
Thus prompt and activation share eligibility, including after movement or
repeated keypresses. Legacy Computer, other interactables and machine ranges
retain their previous behavior; no additional geometry or ray obstruction is added.

The prompt and fallback text match legacy. E opens the exact existing
[`dialogue/computer_opening.tres`](../dialogue/computer_opening.tres), ID
`computer_opening`. The inherited detector opens Dave's persistent DialogueUI;
finishing emits `conversation_completed` to Main's single existing
`_on_conversation_completed`, which calls
`ObjectiveController.activate_objective(&"restore_computer")`. The existing
state-change listener refreshes the tracker. Early dismissal emits only
`conversation_dismissed`, with no objective activation. There is no new listener,
objective, flag or local completion state. Interaction remains enabled after
dismissal/completion, and repeated activation cannot reset objective stage.
Main's exploration-first Ferrite activation and tracker precedence stay intact.

Startup binding/order, inherited UI ownership and P1 routing/cache remain as
described above. The area belongs to the cached production room; Dave's existing
detector/UI and Main's connection persist across room reentry.

All 31 static checks passed in the initial P2 run (7 host, 24 existing), along with
`git diff --check`. Static validation uses the four commands above. The host suite includes
Computer contract/signal-chain inspection and front-approach geometry. The
preservation check allows additive declarations only in the Primary production
wrapper while retaining all original nodes/resources. The amendment additionally
allows only the exact optional-cap additions in the two shared scripts; remaining
protected content still compares against `origin/main`. This is text/geometry evidence only, not
Godot parsing, physics, gameplay or graphical verification. Existing GDScript
tests were inspected but not executed under the headless restriction.

### P2 initial sequential owner acceptance — owner reported 7/7 PASS

The owner's 45-unit amendment reports all seven initial tests passed and accepts
the provisional placement. Individual observations are not supplied here. This
is owner-reported runtime evidence, separate from agent static validation. The
original sequence is retained below; the range amendment needs retests A-C.

Perform one test at a time and record **PASS/FAIL, observations and errors**.
Fix defects in this PR and retest affected scenarios before proceeding.

1. **Availability:** F6 `main_v2.tscn`; approach from accessible floor. Accept or
   revise the provisional front point; verify E prompt, distance, line of sight
   and no debugger errors.
2. **Completion:** Fresh V2 session; finish Computer dialogue. Verify
   `restore_computer` activation/tracker, existing dialogue and damaged overlay.
3. **Dismissal:** Separate fresh session; dismiss early. Verify no activation,
   unless independently activated by the existing Ferrite discovery path.
4. **Repeat:** Reopen after dismissal and completion. Check no duplicate UI,
   grants or objective anomalies.
5. **Transitions:** Interact, visit Maintenance and/or exterior, then return.
   Verify interaction, dialogue and objective state across cached-room reentry.
6. **Preservation:** Damaged screen stays visible, repaired stays hidden, console
   collision and room geometry remain intact; Dave navigates normally with no
   duplicate console or blocking proxy.
7. **Legacy:** F5; verify original Computer prompt/dialogue/objective, legacy
   routes/exterior return, machine recovery and production smoke paths.

### PR #60 range amendment — focused owner retests pending

The approved target is 45 world units for V2 Computer only. Static checks cover
the default-preserving cap, exclusive scene assignment, global distance/boundary
geometry, and shared prompt/E selection order. All 33 static checks passed after
the amendment (9 host, 24 existing); Markdown links and `git diff --check` passed.
No Godot execution or amended
runtime PASS is claimed. Record PASS/FAIL and observations one at a time:

A. **Distance:** F6 `main_v2.tscn`; check prompt absent and E inactive beyond 45
   world units, original conversation available within range, left/center/right
   approaches and debugger errors.
B. **Dialogue parity:** Complete to activate `restore_computer`; in a separate
   fresh session dismiss early without activation. Verify repeats and damaged overlay.
C. **Regression:** Leave/reenter Primary V2 and verify the cap persists; F5 legacy
   Computer and brief navigation/progression smoke check. Other interactions and
   the shared 120-unit search radius must retain their existing behavior.

The preceding range retest checklist records PR #60's historical validation scope;
its merge is confirmed by the P3 owner request, without inventing individual
retest observations. Computer repair and F5 cutover remain deferred.

## P3 stationary machines (merged PR #61)

The architecture inspection found compatible existing authority and interaction
contracts; no new progression state or recovery API was needed. Only the
production Maintenance wrapper gains `StationaryMachines`, containing independent
`Extractor`, `Smelter` and `Fabricator` assemblies. Each has an unchanged approved
`Visual` PackedScene, separate `Body/Shape`, dormant `Interaction/Shape`, and an
instance of [stationary_machine_presentation.gd](../scenes/world/stationary_machine_presentation.gd).
The reusable visual scenes and PNGs, inherited foundation/background art and
permanent `StaticCollision/MachineFoundations` are preserved.

### Coordinates, collision and depth

Machine anchors are room-native siblings of compensated `GroundObjects`, never
children of Dave's 0.8-scale container. Maintenance's production root now enables
Y-sorting; both organizational containers also enable it, joining their nested
children in one sorting context at default z=0. The machine roots are floor-contact
sort anchors, with unsorted visual children preserving the approved shadow/sprite
order. Dave retains effective scale 1; machines inherit 1.25. The inherited
Background has a production-only z=-1 override, keeping the complete room artwork
behind sorted actors even at negative Y. No new architectural overlay is invented;
permanent architecture retains its existing flattened background and collision.
Visual occlusion at accessible approaches requires owner review.

| Assembly | Room-native anchor | World anchor at 1.25x | Base center relative to anchor | Rectangle size (native) |
| --- | --- | --- | --- | --- |
| Extractor | `(-442, -156)` | `(-552.5, -195)` | `(0, -24)` | `152 x 44` |
| Smelter | `(435, -159)` | `(543.75, -198.75)` | `(0, -22)` | `136 x 40` |
| Fabricator | `(-451, 295)` | `(-563.75, 368.75)` | `(0, -22)` | `172 x 40` |

These initial rectangles follow the broad lower mounting bases seen in the PNGs,
excluding elevated machine bounds and their cast shadows. They use layer/mask 1.
They are independent of permanent foundation shapes and remain owner-tunable;
static geometry establishes clearance, not collision feel or final visual fit.
The Smelter rectangle is narrower to retain passage between its base and the
permanent raised side housing; a broader initial rectangle isolated rear floor
in the static clearance grid and was reduced before owner testing.

In the P3 baseline each machine uses `WorldInteractable` directly on a nonblocking
Area2D: layer 1, mask 0, monitoring off, local `(0, 8)`, rectangle `48 x 8`.
The target's rear edge is 6 native units beyond the machine collider's front.
Its origin is the interaction point. `max_interaction_distance = 45.0` is independently
editable per machine and measured in world units by the unchanged detector
(36 native units at 1.25x); its search radius remains 120. A feet/detector center
20 native units beyond the collider front is outside collision and within that cap.
The detector retains its existing first-hit ray test against architecture.
No prompt, response or conversation is configured and `interaction_enabled` stays
false in every P3 state. There is no player activation, grant, objective mutation
or recovery dialogue. Future P4-P6 work must wire intentional recovery behavior.

### Authoritative presentation and cached-room lifecycle

`PlaythroughState.extractor_recovered`, `smelter_recovered` and
`fabricator_recovered` exclusively determine removal. Highlighting requires
`ObjectiveController.get_active_objective()` to select `restore_computer` and
uses Main's existing tracker-stage precedence: Ferrite discovery selects Extractor;
ore acquisition selects Smelter; ingot acquisition selects Fabricator. Later
recovery/deployment/Plate stages suppress superseded highlights. There are no
new objective IDs, recovery flags or mutable presentation-stage stores.

| Derived state | Visual and contact shadow | Amber outline | Machine collider | Target shape / activation |
| --- | --- | --- | --- | --- |
| Normal | Visible | Off | Enabled | Present / disabled |
| Current recovery guidance | Visible | On | Enabled | Present / disabled |
| Recovered (takes precedence) | Hidden | Off | Disabled | Disabled / disabled |

The existing scene-local ShaderMaterial receives only `outline_enabled`; width
20, fixed amber `(0.65, 0.43, 0.19)`, opacity and all visual transforms stay exact.
The complete `Visual` subtree hides on recovery, including its contact shadow.
Shape disablement is deferred safely when state signals originate in physics.

Each presentation component binds once in `_ready` to Main's existing playthrough and sibling
ObjectiveController, then subscribes to its nine existing milestone signals and
`objective_state_changed`. It refreshes immediately on ready and after each
relevant event. `_enter_tree` schedules a refresh on every attach, including cached
return and quick-transition rollback, where `_ready` does not repeat. Detached
callbacks skip updates; reattachment reads current authority again before normal
play resumes. There is no per-frame polling or modification to the transition
controller, cache identities, arrival hook, cancellation or rollback semantics.

### P3 permitted verification and owner acceptance

```text
python -B -m unittest discover -s tests -p 'static_*test.py'
git diff --check
```

The static suites inspect resource graphs, scene declarations, approved anchors,
shared sorting context, local visual/material settings, dormant contracts,
world-distance geometry, state-source/precedence/signal/lifecycle wiring and
preservation of existing code/art. A conservative grid with 9-native-unit obstacle
clearance checks connected entry/front/side/rear approach samples for all machines,
including permanent geometry and new rectangles. Existing P1/P2, connection,
transition and console checks remain included. These are source/geometry checks;
they do not execute presentation state transitions or prove engine parsing,
inherited rendering, physics registration, signal delivery, deferred updates or
cached reattachment behavior. No Godot, headless, graphical, performance or
GDScript test execution is authorized/performed. Alternate states are unreachable
through P3's dormant recovery targets; no fake gameplay or debug state controls
are added to expose them.

All 37 static checks passed for P3, together with changed-document local link
validation and `git diff --check`. No runtime or owner PASS is inferred.

Owner tests, **one at a time**, reporting PASS/FAIL plus observations/errors:

1. F6 `main_v2.tscn`; enter Maintenance and inspect the three approved visuals,
   size, foundation placement, shadows and default outline state.
2. Navigate around Extractor and assess its floor-contact rectangle.
3. Navigate around Smelter and assess its floor-contact rectangle.
4. Navigate around Fabricator and assess its floor-contact rectangle.
5. Check Dave in front/behind machinery, shadows and permanent architectural
   occlusion from accessible approaches. Check camera zoom as needed.
6. Confirm no premature recovery E prompt or action. Target/range configuration
   has static evidence only; no active recovery interaction is claimed.
7. Leave and revisit Maintenance, including cached returns. Report alternate
   presentation states as unverified where normal P3 gameplay cannot reach them.
8. Stop F6; F5 retains legacy rooms/recovery/production, and F6 retains V2 routes.

This records P3's historical scope; P4 below extends Extractor activation only.
Smelter/Fabricator recovery was deferred to P5/P6 at that baseline. No Computer repair,
save/load, testing-framework expansion, CI or F5 cutover is included.

## P4 Extractor recovery (PR #62, merged)

The architecture inspection confirmed that the detector casts targets to
`WorldInteractable`, selects through overridden `can_interact()`, then dispatches
`interact() -> String` when no conversation is configured. The generic method
requires conversation/inspection content; enabling it alone cannot offer an
action. The new V2-only
[Extractor adapter](../scenes/interaction/v2_extractor_recovery.gd) overrides both
methods on the existing Area2D. The legacy rack script cannot be attached
unchanged because it expects `Module` and `Empty` children.

The adapter alone owns action eligibility: attached to the tree, interaction
enabled, valid PlaythroughState, `ferrite_discovered && !extractor_recovered`.
It reads current authority on selection and again on dispatch, independent of
Computer dialogue and tracker stage. No local flag, inventory listener or manager
is added. Its prompt is **E — Recover Extractor**. Existing detector safety gates
for tools, dialogue, machine UI, responses and transitions remain unchanged.

`interact()` calls only `PlaythroughState.recover_extractor()`. That transaction
guards synchronous inventory callbacks and repeated input, inserts exactly one
packaged Extractor, sets recovery state, then emits `extractor_recovery_completed`.
An insertion failure commits no recovery and returns the existing dismissible,
nonblocking response **Unable to recover the Extractor.** Success returns empty
text, so no success UI is added. Main's single existing completion listener shows
the existing musing and refreshes deployment guidance; `restore_computer` remains
active. Ferrite discovery already activates that objective for exploration before
Computer dialogue; later dialogue cannot reset its stage.

The [presentation component](../scenes/world/stationary_machine_presentation.gd)
no longer writes Extractor activation. It still owns visuals, outline, shadow and
deferred removable body/target shape disablement. The existing completion signal
immediately hides the complete Visual subtree and turns its outline off. Ready,
nine milestone signals, objective signals and deferred reattachment refresh retain
the P3 lifecycle contract. Cached rooms read the same authoritative recovered
state; no reconstruction, rollback of committed recovery or cache change is added.
At the P4 baseline, Smelter and Fabricator retained generic disabled targets.
P5 below activates Smelter only.

Extractor anchor `(-442, -156)`, room scale 1.25, base `152 x 44` at `(0, -24)`,
target `48 x 8` at `(0, 8)` and independently editable **45.0 world-unit** cap are
unchanged. The detector remains 120; Computer remains capped at 45. First-hit
occlusion and the same fresh range selection govern prompt and action. Approved
PNGs, visual scenes, materials, shadows, Y-sorting, permanent foundation artwork
and collision, legacy F5 and the F6 host are preserved.

### P4 validation and sequential owner acceptance

Use the static discovery command above and `git diff --check`. The existing suites
now check the Extractor action contract, failure-only response, transaction order,
Main's single musing connection and narrow presentation activation ownership.
P1/P2/P3 geometry, resources, lifecycle, later-machine dormancy and broad byte
preservation checks remain. These inspect text and geometry only. Godot parsing,
physics, UI dispatch, signal delivery, deferred collision updates, rendering,
cached reentry and gameplay remain unverified; no engine or project code was run.

The P4 implementation recorded **38 static checks passed** with
`python -B -m unittest discover -s tests -p 'static_*test.py'`; changed-document
local links and `git diff --check` also passed. A later audit on merged P4
reproduced 37 passes and one stale preservation-baseline failure, corrected in P5
below. No runtime or owner PASS is inferred.

Owner tests: perform **one at a time**, record **PASS/FAIL**, optional observations
and errors; resolve failures before proceeding. Merge approval is separate.

1. Before Ferrite discovery: Extractor visible, no recovery prompt/action.
2. After discovery: highlight and **E — Recover Extractor**; assess accessible
   front/side approaches, the 45-world-unit boundary and first-hit occlusion.
3. Recover once: one packaged Extractor, one existing musing, deployment guidance;
   visual/shadow/outline removed, removable collision gone, foundation retained.
4. Repeat E and deploy/remove equipment: no duplicate grant or musing.
5. Exit/return repeatedly to cached Maintenance: recovered machine stays absent
   and noninteractive.
6. Explore/recover before finishing Computer dialogue: later dialogue preserves
   state and guidance.
7. Inventory/UI focus and normal room transitions do not accidentally dispatch
   recovery. Do not force unsafe transition-cancellation scenarios.
8. Smelter/Fabricator remain dormant; P2 Computer interaction is unchanged.
9. F6 Extractor deployment/production smoke test, then separate F5 legacy
   recovery/Computer/navigation regression.

## P5 Smelter recovery (PR #63, merged)

Baseline: clean synchronized main at PR #62 merge
`bf18f09df74680372e1eb842929431915a409f9f`. The thin
[Smelter adapter](../scenes/interaction/v2_smelter_recovery.gd) follows P4's
WorldInteractable contract on `StationaryMachines/Smelter/Interaction`.
It checks attached-tree state, interaction activation and valid PlaythroughState,
then `ferrite_acquired && !smelter_recovered` on selection and again on dispatch.
Ore must have entered inventory once; production in an Extractor output buffer
alone does not qualify. Spending or transfer does not revoke eligibility.
Computer conversation, current quantity, Extractor deployment, objective stage
and highlight are not prerequisites.

The prompt is **E — Recover Smelter**. Dispatch calls only
`PlaythroughState.recover_smelter()`. Its existing reentry/duplicate guard inserts
exactly one packaged Smelter, commits recovery, then emits completion. Rejection
commits no recovery, removal, grant or completion and returns only **Unable to
recover the Smelter.** through existing nonblocking, dismissible response UI.
Retry stays eligible. Success/ineligibility return empty text. Main's one-time
Smelter-related musing remains at first ore acquisition. Recovery only refreshes
existing guidance, ordinarily **Deploy the Smelter near the Extractor.**, unless
superseded by later progression. It does not complete `restore_computer`.

At the P5 baseline, adapters exclusively own Extractor/Smelter eligibility;
presentation's dormancy guard applied only to Fabricator. Existing P3 ready, nine milestone signals,
objective signals and deferred cached reattachment synchronization remain.
Success immediately hides the entire Visual subtree (machine/shadow/outline),
defers safe disabling of removable body/target shapes, and makes interaction
ineligible immediately. Permanent foundation and raised housing art/collision
remain. Cached-room return and rollback read current session authority; they
never reset recovery. No disk persistence, new state or scene reconstruction.

Preserved: Smelter anchor `(435, -159)`, room scale 1.25 and GroundObjects/Dave
compensation, base `136 x 40` at `(0, -22)`, target `48 x 8` at `(0, 8)`, target
collision layer/mask/monitoring, independently editable **45.0 world-unit** cap
without another scale multiplier, 120-unit detector, Computer/Extractor caps,
first-hit occlusion, approved visual scene/PNG/shadow, 20-wide amber
`(0.65, 0.43, 0.19)` outline, material isolation and sorting. Legacy F5, P4 and
Fabricator dormancy remained unchanged in P5; P6 below activates it.

### P5 static validation and limitations

`python -B -m unittest discover -s tests -p 'static_*test.py'`: **39 tests pass**.
`git diff --check` and changed-document local Markdown links pass. Existing
resource graph/load-count checks include the new adapter and unique UID.
The P5 broad source/artwork/sidecar preservation check compared the actual
`origin/main` baseline, reversing only P5 binding/declaration and activation
changes when absent from that baseline. Merged P4 is protected rather than
normalized away. Focused assertions cover eligibility, dispatch, default grant
quantity, rejection/commit ordering and acquisition-only musing timing.

No Godot or project code was executed. Static checks do not establish engine
parsing, gameplay, physics, signal delivery, UI dispatch, rendering, deferred
collision removal or cached reattachment. Inventory rejection and unsafe
transition cancellation remain runtime-unverified unless a safe existing mechanism
is available to the owner. No debug gameplay or forced cancellation is added.

### P5 owner acceptance — ten sequential tests

This historical P5 checklist was for manual execution, **one test at a time**,
reporting **PASS/FAIL** and optional observations. Start with F6
[main_v2.tscn](../scenes/main/main_v2.tscn); test 10 uses legacy F5 separately.

1. **Before ore acquisition:** With Ferrite discovered but none acquired, Smelter
   has no prompt/action; ore only in an Extractor buffer does not qualify.
2. **First ore acquisition:** Collect ore; existing acquisition musing occurs once;
   guidance/highlight and **E — Recover Smelter** appear as appropriate. Check
   front/side approaches, 45-world-unit boundary and first-hit occlusion near
   raised housing. Do not recover yet.
3. **Successful recovery:** Press E once: exactly one packaged Smelter, deployment
   guidance, no recovery musing, visual/shadow/outline gone, removable collision
   and target disabled, permanent foundation/housing retained.
4. **Duplicate prevention:** Repeat E, then deploy/remove Smelter: no second
   starter grant or replay of acquisition musing.
5. **Cached-room persistence:** Repeated exits/returns leave Smelter absent and
   noninteractive. Where practical, confirm eligibility survives ore spending.
6. **Out-of-order exploration:** In a fresh session acquire ore/recover before
   finishing Computer dialogue; later dialogue preserves state and guidance.
7. **Input/transition safeguards:** Inventory, dialogue, machine UI, construction
   tools and normal transitions do not accidentally dispatch recovery. No forced
   cancellation or stress tests.
8. **Adjacent regression:** P4 Extractor unchanged, Fabricator dormant, P2
   Computer range and conversation unchanged.
9. **Deployment/production:** Deploy outside, transfer ore, produce/collect Ingot.
   Existing Fabricator guidance may appear; V2 Fabricator remains disabled.
10. **Legacy F5:** Legacy Smelter recovery, empty rack/collision, Computer,
    navigation and production remain unchanged; F6 routes still work.

## P6 Fabricator recovery (PR #64, merged; historical milestone)

The verified pre-P6 baseline is live main at PR #63 merge
`59275b0da9550ce9c2ec4aeeafd36037e0567e2a`. Architecture inspection confirmed
the existing transaction, response UI and guidance already satisfy P6. The thin
[Fabricator adapter](../scenes/interaction/v2_fabricator_recovery.gd) follows P4/P5
at `ProductionMaintenanceBayV2/StationaryMachines/Fabricator/Interaction`.
It checks attached-tree state, activation and valid PlaythroughState, then
`ferrite_ingot_acquired && !fabricator_recovered`, on selection and dispatch.
An ingot must have entered Dave's inventory once; Smelter output alone does not
qualify. Spending or transferring ingots does not revoke historical eligibility.
Current quantity, Computer conversation, objective stage, Smelter recovery or
deployment, recipes and material costs add no gates. Highlighting remains separate
and follows the existing higher-precedence guidance rules.

The prompt is **E — Recover Fabricator**. The adapter calls only
`PlaythroughState.recover_fabricator()`, whose existing duplicate/reentry guard
precedes insertion of exactly one packaged Fabricator. Recovery commits before
the completion signal. Rejection commits no recovery and returns exactly
**Unable to recover the Fabricator.** through existing nonblocking, dismissible
response UI; retry remains eligible. Success and ineligibility return empty text.
No flags, inventory, planet records or objectives are written by the adapter.

Both dormancy controls are removed narrowly: the Fabricator target replaces its
generic script with the adapter and its explicit disabled setting with the
prompt; presentation loses only its final Fabricator activation override.
The unused generic external declaration is replaced in place (`7_interaction`),
so the wrapper retains `load_steps=14`. All adapters now own eligibility.
Presentation retains its existing nine milestone subscriptions, objective signal,
ready refresh and deferred reattachment refresh. Completion hides the complete
Visual subtree including contact shadow, disables the amber outline, and defers
disabling removable body/interaction shapes. Permanent cabinet/foundation artwork
and `StaticCollision/MachineFoundations` remain. Cached returns read committed
authority; deploying or removing packaged equipment never resets shipboard recovery.

The existing **seven-second first-ingot acquisition musing** and resource content
are unchanged. Recovery adds no musing, dialogue, animation, cinematic or audio.
Main's completion listener refreshes guidance directly to **Craft a Ferrite Plate.**
with no Fabricator deployment objective. Deployment, Plate/Rod recipes, loading
and production remain as-is. A Plate in output alone does not clear guidance;
Dave acquiring a Plate does. Rod acquisition does not substitute, and
`restore_computer` stays active/incomplete. No new progression, transaction,
manager or save/load behavior is introduced.

Preserved exactly: Fabricator room-native anchor `(-451, 295)`, room scale 1.25
and Dave compensation, body `172 x 40` at `(0, -22)`, target `48 x 8` at `(0, 8)`,
layer 1/mask 0/monitoring off, **45.0 world-unit** cap without scale multiplication,
global 120-unit detector, first-hit occlusion, input/UI/transition safeguards,
Computer/Extractor/Smelter ranges, approved visual scenes/PNGs, scene-local
shader/material, outline width 20.0 and amber `(0.65, 0.43, 0.19)`, shadows,
transforms and Y-sorting. P4/P5 adapters, legacy F5 racks, Main, construction,
inventory, production and transitions are unchanged.

### P6 static validation and limitations

Baseline: **39/39** static tests passed. After P6:
`python -B -m unittest discover -s tests -p 'static_*test.py'`: **41/41 pass**.
`git diff --check` and changed-document local Markdown link/anchor validation pass.
The existing resource graph/load-count and unique UID checks include Fabricator.
P6 preservation pinned the verified pre-P6 SHA above instead of moving `origin/main`,
reversing only the exact P6 wrapper declaration/binding and presentation dormancy
removal. Merged P4/P5 and all existing protected code/art/sidecars remain protected.
Focused checks inspect historical eligibility, dispatch recheck, failure-only
response, one delegated transaction, grant/commit ordering, acquisition-only
musing, direct Plate guidance and Plate acquisition semantics.

These checks execute neither Godot nor project code. Engine parsing, physics,
signal delivery, UI behavior, rendering, deferred shape updates, room-return
correctness and gameplay remain runtime-unverified. Existing GDScript recovery,
deployment, recipe-switching and production suites were not executed. Exceptional
inventory rejection, synchronous reentry and engineered transition rollback remain
runtime-unverified; no debug controls or forced reproduction were added. No CI,
Actions, new test framework, performance probes, P7 rehearsal or F5 cutover.

### P6 owner acceptance — ten sequential tests (historical checklist)

This historical P6 checklist used **owner-run F6 gameplay**, **one at a time**,
with **PASS/FAIL** and optional observations/errors. No individual P6 result is
inferred from static checks or the later aggregate P7 report. Start with
[main_v2.tscn](../scenes/main/main_v2.tscn).

1. **Pre-ingot eligibility:** Fresh F6 progression: before first ingot enters
   inventory, no Fabricator recovery prompt/action. Smelter output alone must
   not unlock it.
2. **First ingot acquisition:** Collect an ingot; existing first-ingot musing plays
   once, Locate Fabricator guidance and amber highlight appear when appropriate.
   Check **E — Recover Fabricator** at accessible front/side approaches, the
   45-world-unit cap and cabinet occlusion. **Do not recover yet.**
3. **Successful recovery:** E once grants exactly one packaged Fabricator, with
   no recovery musing and direct **Craft a Ferrite Plate.** guidance. Machine,
   shadow and outline vanish; removable collision/target disable; permanent
   foundation/cabinet remain.
4. **Duplicate prevention:** Repeated E and subsequent deployment/planetary
   retrieval never grant another shipboard Fabricator or replay the ingot musing.
5. **Historical eligibility and cached returns:** Where normally achievable,
   spend ingots before recovery and verify eligibility persists. Repeated room
   exits/returns before/after recovery retain presentation without stale prompts.
   Separately, in a fresh session, ingots returned by deployed Smelter recovery
   may satisfy acquisition.
6. **Before Computer dialogue:** Acquire ingot and recover Fabricator before
   finishing the opening Computer conversation; later dialogue preserves state
   and the most advanced guidance.
7. **Input/transition safeguards:** Inventory, dialogue, machine panel,
   construction mode and normal doorway transitions do not accidentally dispatch
   recovery. No forced cancellation or stress tests.
8. **Adjacent regressions:** P4 Extractor recovery/musing, P5 Smelter recovery
   with acquisition-only musing, and P2 Computer range/conversation are unchanged.
9. **Existing Fabricator chain:** Deploy, select Plate recipe, load ingots,
   produce and collect a Plate. Output alone must not clear guidance; acquisition
   must. `restore_computer` stays active/incomplete. Recipe selection/loading
   add no musing; Rod acquisition must not substitute for Plate acquisition.
10. **Legacy F5:** Original Fabricator rack recovery retains its empty frame/rack
    and collision. Check Computer, navigation and existing production, then
    confirm opt-in F6 routes still work.

P6 merged in PR #64. P7 later passed 6/6 phases in the owner-reported continuous
rehearsal. Earlier P1-P6 checklists retain their historical F5/F6 expectations;
use the P8 checklist below for current launch acceptance.


## P8 production cutover (feature branch, pending merge)

The fixed verified live pre-P8 baseline is PR #64 merge
`e14703e64aef961f18feba8a616acec00c4f069e`. P8 changes only `run/main_scene`
in `project.godot` from `res://scenes/main/main.tscn` to
`res://scenes/main/main_v2.tscn`. All gameplay scripts, scenes, autoloads, authored
exterior hatch destination, scale, spawn positions, 45-unit interaction caps,
recovery adapters, authoritative progression and cached-room behavior are preserved.
The existing host configures its attached exterior instance's V2 return.
There is no new gameplay, narrative guidance, P7 replay or P9 stabilization.

### P7 Observation #1 - nonblocking and unfixed

**P7 Observation #1 (nonblocking missed implementation):** After the Computer's
opening conversation, the player is not explicitly directed outside to investigate
the Ferrite deposit. P7 owner rehearsal passed 6/6 phases despite this gap. A
separate, later approved narrative/objective-guidance correction is needed; it is
**excluded from P8** and remains unfixed.

No objective, dialogue, prompt or Ferrite discovery change is included, and no
issue is created by this cutover.

### P8 static verification and limits

Before P8, the permitted static suite passed **41/41**. After P8:
`python -B -m unittest discover -s tests -p 'static_*test.py'` passed **42/42**.
`git diff --check` and all **48 local links/anchors** in the three changed
documents passed. Six in-memory negative checks confirmed both preservation
tests reject duplicate startup assignments, unrelated project-setting changes
and reverting to legacy startup; no project files were mutated by these checks.
P8 pins production-host
preservation to the post-P6 SHA above, directly protecting Fabricator activation
and all three adapters, without reverse-P6 normalization. Both affected tests
require one exact V2 startup assignment, normalize only that assignment to the
fixed pre-P8 value, then compare the entire project file (existing CRLF
normalization only). All other source/artwork/sidecar protection remains.
A focused static check resolves F5 to the V2 host and checks independent legacy
Main's root, script and opening scene; the existing resource graph validates
references and declarations for both scenes.

No Godot, headless, graphical, GDScript gameplay or performance tests are run.
Static checks do not prove engine parsing, rendering, physics or gameplay.
All P8 runtime results below remain pending, separate from the P7 owner report.
Exceptional inventory rejection, synchronous reentry and engineered transition
rollback remain outside ordinary acceptance without a safe existing test mechanism.

### P8 owner acceptance - eight sequential tests (all PENDING)

After PR review, the **owner** runs these **one at a time**, reporting **PASS/FAIL**
and optional observations, resolving blocking defects before merge. Agents must
not execute these tests or infer passes from static validation.

1. **PENDING - Default F5 opening:** F5 launches V2 Primary at accepted spawn/facing;
   Dave movement/camera, Computer prompt and opening dialogue work. Legacy interior
   must not appear by default.
2. **PENDING - V2 routes and input:** Primary <-> Maintenance automatic doors,
   exterior departure and hatch return reach approved V2 rooms/markers; controls
   restore after dialogue/transitions.
3. **PENDING - Discovery and machine recovery:** Ferrite discovery and historical
   ore/ingot acquisition unlock Extractor, Smelter, Fabricator in order; no premature
   prompts, duplicate grants or extra recovery musings.
4. **PENDING - Representative production chain:** Recover/deploy equipment, acquire
   Ferrite Ore, acquire Ferrite Ingot, craft and **acquire** Ferrite Plate. Output
   alone does not advance acquisition guidance. `restore_computer` stays active/incomplete.
5. **PENDING - Cached-room persistence:** Repeated ordinary Maintenance returns
   retain recovered-machine absence, permanent foundations, disabled interactions
   and correct inventory grants.
6. **PENDING - Legacy F6 fallback:** Stop F5, open `scenes/main/main.tscn`, F6;
   verify original interior, navigation, Computer and representative legacy
   rack/empty-rack collision. Stop and confirm F5 still starts V2.
7. **PENDING - Runtime and resource health:** During ordinary tests check for
   startup/import/missing-resource errors, scene-loading failures, unexpected input
   locks and runtime errors. No forced cancellation, stress tests or benchmarks.
8. **PENDING - Documentation and static review:** F5/F6 instructions match observed
   behavior; required static suite, preservation checks, diff validation and changed
   document links pass; P7 Observation #1 remains nonblocking and unfixed.

### Merge gate and rollback

Require reviewed narrow diff, passing permitted static checks, owner-run acceptance,
no unresolved startup/routing blockers and **explicit owner merge approval**.
Do not merge automatically, retire branches, clean up, begin P9 or change F5 again.
If rollback is needed after a future merge, use a separate reviewed PR restoring
only the prior main-scene setting and corresponding test/current documentation
assumptions. Preserve history and V2. Ended sessions cannot be restored: disk
save/load is not implemented.
