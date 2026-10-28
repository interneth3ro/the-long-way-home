# Opt-in V2 production host — P1

Feature-branch integration, pending merge and owner acceptance. This is not the
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
No Computer interaction, stationary machine placement/highlights or recovery
adapters are installed. Approved machine assets/transforms, legacy worlds,
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

## Static verification and owner acceptance

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

Stop at P1: no Computer migration, stationary machine integration, progression
changes, save/load, eviction, F5 cutover or retirement. The opt-in host and wrappers
are later retirement-audit candidates; no deletion or cleanup is authorized here.
