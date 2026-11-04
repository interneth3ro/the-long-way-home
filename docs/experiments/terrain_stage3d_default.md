# Stage 3D — continuous terrain production default

Status: feature branch, pending merge. Owner authorized this narrow default
change on 2026-11-04 after PR #143 merged at
`e5db8040d38bfd6b1ddb584d636af01052806b7c` and cleanup completed.
Validation is static only; no Godot process, import, gameplay session or timing
measurement is authorized or performed by this implementation.

## Selection and rollback

`PlanetExterior.terrain_renderer` defaults to `TerrainRenderer.CONTINUOUS`.
The production `planet_exterior.tscn` root has no serialized renderer override,
so it inherits that default; no scene edit is necessary. The script initializer
is the only production change. The enum stays
`LEGACY = 0`, `ILLUSTRATED = 1`, `CONTINUOUS = 2`.

To roll back an individual exterior, stop the playthrough, select Illustrated
(`terrain_renderer = 1`) on a fresh exterior instance before its first
`prepare_for_arrival()` call, then start a new playthrough under separate execution
approval. To restore the production default in a follow-up feature PR, change
the script initializer to `TerrainRenderer.ILLUSTRATED`; update the
default-selection assertions/docs and run static checks. The unchanged production
scene will inherit it. An explicitly serialized per-instance selection always
overrides the script initializer. No renderer hot switching, automatic fallback,
artwork replacement or shader change is needed.

The accepted [Stage 3C implementation and limits](terrain_stage3c_exterior.md)
remain unchanged: original generation/material IDs, Candidate A, frozen C1 art,
shaders, tint/overlays, chunk lifecycle, fail-closed arrival readiness, Ferrite,
construction and gameplay. The 15 protected untracked sidecars, historical
evidence and preservation references remain protected. Stage 3C's consumed
manifest/procedure and acceptance record remain historical, not permission for
another run. Its estimated 10–15 second first exterior wait was **not measured**;
loading feedback/investigation remains deferred in
[Issue #144](https://github.com/interneth3ro/the-long-way-home/issues/144).

## Static checks

`python -B -m unittest discover -s tests -p 'static_*test.py'` checks source,
resource text, independent models and preservation without executing Godot or
GDScript. The focused Stage 3D test requires the exact feature inventory and
reconstructs the sole allowed production change from merged PR #143 and requires
the unchanged production scene to inherit it. Existing default assertions now
expect Continuous; historical scene/geometry guards remain unchanged. Stage 3C's
inventory and consumed input-manifest checks use its immutable merged source
for the changed script, retaining the
original CRLF serialization and hashes. No historical manifest or receipt changes.
Final test counts/results are recorded in the draft PR. Static PASS establishes
neither engine parsing, shader compilation, actual readiness nor visual quality.

## Final gameplay and transition timing plan — inactive, separate approval

This plan requests no execution now. A separate owner approval must name the
final reviewed commit, this guide's SHA-256 and a reviewed activation/supervision
amendment with exact commands, inputs and transforms. No stage, new runner or
activation amendment is created in Stage 3D. Existing Native/MetadataSmoke modes
must not be repurposed. The Stage 3C grant is consumed.

Proposed bounded scope: one cold import followed only on PASS by one supervised
fresh V2 playthrough at seed 26026, 1280×720, using the production default without
any staged renderer override. Measure natural loading/transitions during this
functional session; no profiling, stress loop, optimization or freeze reproduction.

Preparation to review before execution:

1. Require complete Python static-suite PASS, clean tracked/index state and only
   the exact 15 protected untracked sidecars. Capture revision, status/index,
   source/input hashes and controls. Recheck the existing preservation receipt,
   C1 artwork/metadata, A1 branch, all annotated tag objects/targets, backup bundle,
   both Stage 2B-2 manifests/ten PNGs and PR #141 branch/six diagnostics.
2. Use the 346 paths in the immutable
   [Stage 3C manifest](terrain_stage3c_gameplay_plan.json) as the proposed input
   closure, excluding protected untracked sidecars, caches, tools, tests and
   evidence. Its raw SHA-256 remains
   `a567d3b6abb39fdf28cc0b019f7280ad971a771d610db41f2e5c9f692997a7c8`.
   Verify the other 345 source records unchanged. Replace only this source
   identity in the new reviewed activation record (approved CRLF serialization;
   text must also match the final Git blob after LF normalization):

   | Input | Bytes | SHA-256 |
   |---|---:|---|
   | `scenes/world/planet_exterior.gd` | 22845 | `f5b3d0a30834623db05a8ed6b03e906df01a8df0ecb87d70264c1cfe5f0f9ad7` |

3. Verify no standard Godot process. Pin the exact standard executable
   `D:\GameDev\Godot\Standard\Godot_v4.7.2-stable_win64.exe`, SHA-256
   `AB1824F85BFD8E0E4128182C000C4003A3E042245B2967848D089B2A04B22424`,
   immediately before each launch. Use a fresh unique `stage3d-<GUID>` under
   `D:\GameDev\Godot\TLWH-NativeStages`, never the source checkout or an old stage.
   Reject links/reparse points and existing destinations. Copy and independently
   verify the exact inputs. The only proposed staged transformation is isolated
   custom user data in `project.godot`: a new absent `TLWH-Stage3D-<GUID>` name,
   with exact replacement bytes and staged hash fixed by the activation amendment.
   Do not reuse Stage 3C's user data or apply its scene opt-in transformation.

Exact proposed command shapes, sequential, one engine process at a time:

```text
--headless --path <fresh-stage> --editor --import --quit
--path <fresh-stage> --resolution 1280x720 res://scenes/main/main_v2.tscn
```

Use reviewed bounded supervision: 60 seconds for import, 300 seconds for gameplay,
1,048,576 combined output bytes per process, 4,096-byte diagnostic excerpts,
normal exit 0 and certain termination. Stop on engine/script/parse/shader errors,
failure, timeout, overflow, identity drift, unexpected generated files or uncertain
termination. Stop immediately for severe responsiveness symptoms; do not attempt
reproduction. No retry, repair-and-rerun or extension. Preserve stage and isolated
user data. Review only the established generated inventory: `.godot/` cache,
15 missing PNG import sidecars and three missing script/shader UID sidecars;
validate their formats/destinations and pin their inventory/hashes after import.
Recheck all source/stage/executable/protected identities after each phase and at
exit. No generated files return to source. Publication of permanent evidence or
screenshots requires separate approval; no routine successful logs are required.

Owner-supervised sequence within that single session:

| Check | Expected result |
|---|---|
| Fresh first exterior transition | Continuous appears through the production scene default; complete terrain before fade/input unlock, no holes or shader errors |
| Local exploration | Accepted terrain/tint/scar order; nearby positive/negative chunk crossings and return show no seams, displaced textures or stale ground |
| Ferrite/construction | Existing artwork, deposit interaction, placement highlights and one available machine's placement/interaction remain correct |
| Two natural hatch round trips | Automatic boarding, audio/fades/input lock and retained exterior are correct; no stale terrain on either return |
| Responsiveness | Record ordinary waits/stalls and owner observations; stop for severe symptoms |

Use one external monotonic stopwatch operated by the observer; no production
instrumentation or code edits. Record elapsed seconds to the stopwatch's displayed
precision, noting human start/stop uncertainty. Start each interval at the hatch
transition trigger (interaction accepted for exterior departure; crossing the
boarding threshold for inward travel), and stop when the destination fade is
complete and movement input is accepted. This measures the player's total wait,
including fades/readiness, not isolated generation or GPU time. Record the first
exterior interval separately from process startup and import. Use the same method
for all later transitions; note direction and retained/new exterior state.

| Interval, in order | Measured seconds | Result/observations |
|---|---|---|
| First interior → exterior (fresh instance) | NOT RUN | Pending approval |
| Exterior → interior, round trip 1 | NOT RUN | Pending approval |
| Interior → exterior, round trip 1 (retained exterior) | NOT RUN | Pending approval |
| Exterior → interior, round trip 2 | NOT RUN | Pending approval |
| Interior → exterior, round trip 2 (retained exterior) | NOT RUN | Pending approval |

Record PASS/FAIL/UNTESTED for each check, actual timings, machine/backend and any
stalls/errors. If progression or the deadline prevents a check, mark UNTESTED and
close normally; do not relaunch. Do not infer improvement from Stage 3C's estimate
or declare a performance budget achieved from this session. No comparative
Illustrated session, alternate seeds, envelope-edge exploration, injected failure,
benchmark, freeze reproduction, merge or cleanup is included. Owner acceptance
of this final default path remains pending after review of the measured results.
