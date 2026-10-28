# Opt-in V2 production host — P1 and P2

P1 merged in PR #59; P2 Computer parity is on its feature branch, pending merge
and owner acceptance. This is not the
F5 cutover. Follow the [execution policy](../AGENTS.md#godot-execution-safety);
this guide does not authorize agent Godot execution.

For owner testing, open [main_v2.tscn](../scenes/main/main_v2.tscn) and press
**F6 (Run Current Scene)**. F5 still launches `scenes/main/main.tscn` and the
legacy opening. Main retains movement, camera zoom, inventory and UI input.
No harness HUD, C/H controls or failure probes are added.

## Architecture gate and ownership

The opt-in scene inherits Main; its [script](../scenes/main/main_v2.gd) extends
Main's script. In `_enter_tree`, it replaces only the inherited opening instance
under `Worlds`, before children enter/ready. The legacy opening never readies in
this host. No file or authored asset is removed. In `_ready`, it calls Main's
existing setup exactly once, then positions Dave at Initial, applies the room's
arrival-facing hook and resets camera smoothing/scroll.

Main's inherited `@onready` DialogueUI reference is captured before initialize
reparents Dave. Construction, MachineUI, DeveloperCoordinates and SceneTransitions
retain inherited exported player references. No binding uses a new Dave path
after reparenting. The coordinate display is disabled in the opt-in scene.
There is one inherited Dave/camera, PlaythroughState/planet/inventory,
ObjectiveController, tracker, musing UI, inventory UI, Construction, MachineUI and
SceneTransitionController. There are no inventory grants or new progression.

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
P2 adds only the Computer interaction described below. No stationary machine
placement/highlights or recovery adapters are installed. Approved machine assets/transforms, legacy worlds,
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
| Exterior Hatch (E), opt-in | `production_ship_interior_v2.tscn` | `Spawns/FromPlanet` | Existing IMMEDIATE |
| Exterior Hatch (E), legacy F5 | `ship_interior.tscn` | `Spawns/FromPlanet` | Existing IMMEDIATE |

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

Initial and FromPlanet require owner visual acceptance; these coordinates were
not previously approved. Static feet-circle checks clear Primary walls, polygons
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

## P2 Computer interaction parity (feature branch, pending merge)

The production wrapper alone adds `ProductionShipInteriorV2/ComputerInteraction`,
a nonblocking `Area2D` using the existing
[WorldInteractable](../scenes/interaction/world_interactable.gd) script directly.
It uses layer 1, mask 0, no monitoring, and a centered 64x8 local rectangle.
There is no new adapter script, visible console or solid footprint. The reusable
room, all previews, legacy Computer, approved art and collision remain unchanged.
`VisualContent/ComputerDamaged` stays visible; `ComputerRepairedInactive` stays
hidden. No repair transaction or overlay switching is implemented.

The **provisional** area position is room-local `(0, -214)`, world `(0, -267.5)`
at 1.25x, with `interaction_point = Vector2(0, 0)`. The solid base spans
x=-178..172, y=-277..-222 locally; the proxy spans x=-32..32, y=-218..-210.
It sits entirely in front of the base with a 4-local-unit gap. Dave's detector
and feet center are 10 world units above his ground origin. Along the central
approach, ground y=-111..-197 locally yields detector-to-point distances
118.75..11.25 world units, within the unchanged 120-unit limit. The sampled
approach from Initial clears permanent collision; the front ray reaches the
area before the base or wall. Area queries and rays already include areas,
and require the selected target to be the first hit on mask 1. The proxy does
not block Dave. Position, prompt feel and actual physics selection still require
owner verification; these coordinates are not accepted placement.

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

All 31 static checks passed in the P2 run (7 host, 24 existing), along with
`git diff --check`. Static validation uses the four commands above. The host suite includes
Computer contract/signal-chain inspection and front-approach geometry. The
preservation check allows additive declarations only in the Primary production
wrapper while retaining all original nodes/resources; all other protected files
still compare against `origin/main`. This is text/geometry evidence only, not
Godot parsing, physics, gameplay or graphical verification. Existing GDScript
tests were inspected but not executed under the headless restriction.

### P2 sequential owner acceptance — pending, no PASS/FAIL recorded

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

Stop after P2 PR creation. All seven owner tests are required before merge
approval; merge and specific post-merge cleanup require separate owner requests.
Computer repair, stationary machines, P3 and F5 cutover remain deferred.
