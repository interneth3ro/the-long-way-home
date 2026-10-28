# V2 two-room development connection

> **Archived workflow; retirement proposed in this PR (pending merge).** The
> preview files described below are removed from this checkout. All launch steps,
> controls, pending tests and implementation-status statements below are historical
> records of their original slices, not current instructions or new acceptance.
> Retired-source links open immutable Git history. Geometry, art provenance,
> decisions and owner findings are retained as recorded.
>
> Current F5 starts production `scenes/main/main_v2.tscn`; F6 with
> `scenes/main/main.tscn` open runs the legacy fallback. See the
> [retirement and restoration record](../README.md#primary-interior-v2-development-previews)
> for exact commands to restore the 38 files from
> `c6d236e5ad47d11e285287f93d69d87f8a5213dc` (PR #66).
> Godot execution restrictions still apply; this record authorizes no execution.

Implementation merged in PR #54; owner acceptance is tracked separately. Follow the
[execution policy](../AGENTS.md#godot-execution-safety). This guide does not
authorize agent Godot execution. No owner acceptance result is recorded yet.

Historical launch (retired): open [v2_two_room_connection.tscn](https://github.com/interneth3ro/the-long-way-home/blob/c6d236e5ad47d11e285287f93d69d87f8a5213dc/scenes/dev/v2_two_room_connection.tscn)
in Godot and press **F6 (Run Current Scene)**. Keep the project main scene
unchanged. Start near Primary Interior V2's left entrance, facing left. Walk left
into its threshold to enter Maintenance Bay V2 through the right entrance, facing
left. Enter that right threshold to return to Primary, facing right. Travel is
automatic, without E. WASD/arrows move; wheel zooms; **C** toggles actual collision
and orange threshold outlines; **H** toggles the HUD. Relaunch resets the isolated
session. F5 remains the original production game.

## Architecture gate and ownership

The original gate stopped before editing: the real controller caches detached
rooms and has no unload option. The owner authorized revised Decision 5, **B2**:
one attached/active V2 room, retaining PR #50's detached cache. This supersedes
only the free/unload requirement. No controller or AutomaticDoorway implementation
changes are made. Bounded memory, persistent machine/story/room state and later
production consolidation remain separate future work.

The actual reusable [Primary room](../scenes/world/ship_interior_v2.tscn) and
[Maintenance room](../scenes/world/maintenance_bay_v2.tscn) own their Doorways
component, shallow rectangle and Spawns arrival Marker2D. They contain no
development paths, routing values, controller, Dave, camera or HUD. Doorways has
`process_mode = 4` (disabled) by default; AutomaticDoorway children inherit it.
This also prevents duplicate requests inside the older transition preview, which
already has a controller, and preserves collision-disabled visual previews.
AutomaticDoorway also safely returns when no controller exists.

Development-only inherited instances
[v2_connection_interior.tscn](https://github.com/interneth3ro/the-long-way-home/blob/c6d236e5ad47d11e285287f93d69d87f8a5213dc/scenes/dev/v2_connection_interior.tscn) and
[v2_connection_maintenance.tscn](https://github.com/interneth3ro/the-long-way-home/blob/c6d236e5ad47d11e285287f93d69d87f8a5213dc/scenes/dev/v2_connection_maintenance.tscn)
reuse the real rooms without copying art, collision or marker coordinates. They
enable Doorways, supply reciprocal destinations, and attach a small
[presentation adapter](https://github.com/interneth3ro/the-long-way-home/blob/c6d236e5ad47d11e285287f93d69d87f8a5213dc/scenes/dev/v2_connection_world.gd) using the existing
`prepare_for_arrival` hook. Routing belongs to these development configurations.
There is no replacement controller or permanent development dependency in rooms.

Each inherited root is uniformly 1.25x, carrying art, collision, triggers and
markers together. Its development-only GroundObjects child is 0.8x:
`1.25 * 0.8 = 1`. The existing controller reparents the same production Dave
preserving global transforms. Dave/camera retain original world scale, feet
collision and movement. GroundObjects renders above the art, as in older
previews; prop occlusion remains deferred.

The host initially instances only Primary. The real controller caches its actual
development PackedScene `scene_file_path`; reciprocal routes use that same path,
preventing a duplicate initial room on return. It detaches the source before
attaching the destination. Detached cached rooms do not process or participate
in physics. Persistent Dave/camera, session-local PlaythroughState and one real
controller retain their existing lifecycle. This adds no saves, factory content,
story events, production routes or future persistence guarantees.

The established quick path retains approximately 0.15 seconds of fade each way,
synchronous interaction/movement locks, deferred tree mutation, destination
validation, camera reset, physics registration, cancellation rollback and failure
recovery. Entry waits for separation and makes one request per entry. New fixed
arrivals are outside the triggers. These behaviors are reused, not proven by
static tests. Existing F7/F8/X probes remain in the old transition preview;
the new harness adds no failure-probe controls.

## Geometry and barrier configuration

Both approved images are 1536x1024. Source pixel `(768,512)` maps to local origin;
world position is `(source - (768,512)) * 1.25` at these unrotated roots. Dave's
radius-10 circle is centered 10 world units above his ground origin: native
radius and vertical offset are both 8 pixels. Markers denote ground origins.

| Element | Source pixel | Room local | World at 1.25x |
| --- | --- | --- | --- |
| Primary threshold center | (216,472.5) | (-552,-39.5) | (-690,-49.375) |
| Primary arrival, face right | (288,480.5) | (-480,-31.5) | (-600,-39.375) |
| Initial Dave, face left | (258,480.5) | (-510,-31.5) | (-637.5,-39.375) |
| Maintenance threshold center | (1374,545) | (606,33) | (757.5,41.25) |
| Maintenance arrival, face left | (1318,553) | (550,41) | (687.5,51.25) |

Primary's actual left boundary is local x=-568, y=-102..23 (source x=200,
y=410..535). Its 16x105 native trigger spans x=-560..-544, y=-92..13,
leaving 10 native pixels to either opening endpoint; world size is 20x131.25.
Only the connected instance disables
`CollisionContent/MaintenanceDoorBarrier/Shape`. The reusable barrier resource,
exterior barrier and unrelated collision remain unchanged. Approved closed door
art stays unchanged; no door animation is added.

Maintenance's right opening is local x=622, y=-47..113 (source x=1390,
y=465..625). Its 16x140 trigger spans x=598..614, y=-37..103, leaving
10 native pixels at each endpoint; world size is 20x175.
`PreviewOnlyRightDoorBarrier` stays exclusively in the original collision preview.
The reserved upper door, local y=-242 and x=67..172, stays solid with no trigger
or destination.

Primary arrival feet-circle clearance from its trigger is 70 world units; initial
Dave clearance is 32.5. Maintenance arrival clearance is 50. Horizontal feet-center
routes from each arrival through its threshold to the opening clear all enabled
walls/props by more than native radius 8, sampled at intervals no greater than
one native pixel. This is geometry evidence, not simulated movement acceptance.

## Static checks and limitations

Run from the repository root:

```text
python -B tests/static_v2_connection_test.py
python -B tests/static_automatic_transitions_test.py
python -B tests/static_port_console_geometry_test.py
git diff --check
```

Six new checks cover references/load counts/UID uniqueness, room ownership,
disabled defaults, unchanged original geometry, reciprocal routes and identity,
scale compensation, facing, spawn separation, sampled feet clearance and
preservation. Eleven existing transition checks and seven console checks remain
applicable. All nine Primary hashes and Maintenance's documented SHA-256 are
checked. PR #52 collision refinements and original preview files are unchanged.

These checks read text/assets and invoke neither Godot nor gameplay code. Engine
parsing, inherited override application, physics ordering, camera continuity,
fades, held input, cache reattachment and navigation feel need owner verification.
No editor/import, headless, graphical, runtime or performance test was run.
No owner PASS is inferred.

## Sequential owner acceptance: one report at a time

Report **Test N: PASS/FAIL**, observations and errors after each test. Wait for
that report before advancing; investigate failures before a focused amendment.
Do not merge until all tests pass; merging and cleanup require owner direction.

1. **Harness launch:** F6 the connected harness. Confirm actual Primary V2 at
   1.25x, Dave near the left entrance facing left, correct art/collision, no errors
   and no spontaneous transition.
2. **Primary-to-Maintenance:** Deliberately enter the shallow left threshold.
   Confirm the existing quick fade starts automatically without E.
3. **Maintenance arrival:** Confirm approved art/scale, fixed safe arrival inside
   the right door, Dave facing left and no immediate return.
4. **Maintenance-to-Primary:** Enter the right threshold. Confirm fade, safe
   arrival inside Primary's left entrance and Dave facing right.
5. **Repeated reciprocal travel:** Make several round trips. Check for loops,
   duplicate triggers, stuck movement, broken camera and input locks. Try held
   movement and E through fades to verify inherited locking and recovery.
6. **Doorway precision:** Walk nearby without entering; deliberate entry should
   work from reasonable angles. Inspect C outlines and clearance. Reserved upper
   Maintenance door must remain solid/inactive.
7. **Scene lifecycle/resilience:** Inspect Remote tree: one attached room,
   persistent Dave/camera and one controller. Prior rooms may stay detached/cached;
   check for inactive-room collision/processing. Validate failure recovery only
   through safe supported owner checks without modifying production; report
   unavailable checks explicitly.
8. **Existing V2 previews:** Separately F6 original scale, collision and PR #50
   transition previews. Verify controls, C/H where applicable, walk-through
   visual previews, intended barriers and old routes.
9. **Production regression:** Stop preview, F5 original game. Verify original
   ship/routes, Dave interactions, Computer/Marvin and existing factory/story
   progression, including Extractor/Smelter/Fabricator where available. No V2
   cutover or save changes; report unavailable scenarios explicitly.
