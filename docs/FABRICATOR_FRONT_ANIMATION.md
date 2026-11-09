# Fabricator 0° front mechanical animation

Decision 62, Option A authorizes Decisions 38–61 and the six accepted preflight
proposals. Implementation is on `codex/fabricator-front-animation`, **pending owner
normal-F5 acceptance and merge**. Hybrid Precision combines deliberate gantry
positioning, brisk carriage travel, decisive engagements and inspection holds.
It is independent of recipe completion.

The clean, fetched local and remote `main` baseline was
`fd1f3347ad14a3735f5ffcc22b05730421b16212` (1,029 tracked paths). The owner reports
PR #161 merged, cleaned up and accepted across all seven graphical acceptance
groups. That static-art acceptance does not establish animation acceptance.

Only four existing production files change: `construction/fabricator_visual.gd`,
its scene, `construction/machine_visual.gd` and `construction/deployed_machine.gd`.
The last file adds exactly `visual.presentation_machine_id = machine_id` before
tree attachment. Gameplay, identity allocation, production, inventory, recipes,
recovery, placement, objectives and the Extractor/Smelter presenters are preserved.

## Frozen inputs and registration

The external `fabricator_0_frozen_v1` package remains immutable: all 81 files,
its payload inventory and checksums are verified. Freeze manifest SHA-256:
`c2f8441a7706169d62b96d9c4d3b6b0821765b65939f6fb9f0ef42cbf3d2d0df`.
The accepted resting composite remains unchanged:
`8230ff568218379c754d409fdf1bf568d90d00c71ccc677feee435e11999dd7e`.
The frozen [static inventory](experiments/fabricator_static_artwork.json) is
unchanged. Historical package labels and receipts retain their original meaning.

Exactly five PNGs are copied byte-for-byte from `payload/runtime/` into
`assets/machines/fabricator/`. No source masters, previews or package code are
copied or executed. No artwork is generated, re-encoded, resized or retouched.

| File | Dimensions | Offset | Encoded SHA-256 |
| --- | --- | --- | --- |
| `fabricator_0_body.png` | 1120×983 | (−559,−957) | `659c3e4f67ab5da4b331e76f6a5027fcd4411a38f5c9eeeec9b7be2524a80b53` |
| `fabricator_0_gantry.png` | 422×78 | (−211,−514) | `ba0c6f46b257fc6674a97afbc4e443c41426dba4850c85eb26b75961c4adbbb3` |
| `fabricator_0_tool.png` | 68×259 | (−34,−512) | `bae53754b821dde684578f909eb6eca7cc68620f7df50d970c59106caabfc2b6` |
| `fabricator_0_carriage.png` | 134×161 | (−67,−546) | `47cb483f5b31d78ebf3acbfcab375ed61ffff4e921ab3c453fb9f6de329b30ac` |
| `fabricator_0_foreground.png` | 501×224 | (−250,−312) | `63714016278479350165651585b6d93e6286e8acaca0549214d698b96d0e207d` |

The 1254×1254 registered canvas uses ground anchor (627,1080), one uniform
root scale of 8/65, and root position (64,128). Construction remains 4×4 cells,
128×128 world units. Sprite offsets already subtract the ground anchor.

```text
FabricatorVisual
├── Body
└── FrontAssembly
    ├── BodyLayer
    ├── GantryY
    │   ├── Gantry
    │   └── CarriageX
    │       ├── ToolZ
    │       │   └── Tool
    │       └── Carriage
    └── Foreground
```

Transform groups begin at identity. All sprites are uncentered, with unit scale
and zero rotation. Only GantryY.y, CarriageX.x and ToolZ.y move. In source pixels:

| Layer | Final position |
| --- | --- |
| Body | (−559,−957) |
| Gantry | (−211,−514+Y) |
| Tool | (−34+X,−512+Y+Z) |
| Carriage | (−67+X,−546+Y) |
| Foreground | (−250,−312) |

Scene order draws body → gantry → tool → carriage → foreground. Tool stays behind
carriage; foreground occludes the assembly. There is no local Y-sorting, global
Z-index override, rotation, mirroring, deformation or extra illumination.

Deployed 0° uses the layers in every production state, including rest. Construction
ghosts use the unchanged resting composite with completed-composite alpha 0.5.
90°/180°/270° retain their static PNGs and independent registrations. The existing
unscaled status dot responds immediately to authoritative status.

Five authored import sidecars follow existing lossless, mipmapped, straight-alpha
settings, with distinct canonical UIDs. Local filtering remains
`LINEAR_WITH_MIPMAPS`. No imports or engine launches are performed. Source-pixel
reconstruction exactly matches the resting composite and all 17 frozen pose
previews. Independent mipmap filtering may still differ in engine rendering.
**If F5 reveals a visible resting mismatch, stop for review; do not change frozen
pixels or add rendering effects.**

## Exact choreography

Each pattern is 5.00 seconds including its outgoing handoff. Sequence:
P1 → P2 → P3 → P1. Approved envelopes are X −70…+70, Y −28…+32 and Z −6…+20,
inside frozen maxima X ±90, Y −36…+42 and Z −8…+24. Rest is (0,0,0).
Tool depth stays fixed during continuous passes. X/Y remain stationary during
engagement/retraction; major positioning occurs only with Z=−6.

### P1 — Material Pass

| Phase | Seconds | Start XYZ | End XYZ |
| --- | --- | --- | --- |
| Deep engagement | 0.00–0.18 | (−65,−20,−6) | (−65,−20,20) |
| Long material pass | 0.18–1.98 | (−65,−20,20) | (65,−20,20) |
| Retract | 1.98–2.16 | (65,−20,20) | (65,−20,−6) |
| Coordinate second position | 2.16–2.86 | (65,−20,−6) | (45,18,−6) |
| Deep engagement | 2.86–3.04 | (45,18,−6) | (45,18,20) |
| Short return pass | 3.04–4.19 | (45,18,20) | (−35,18,20) |
| Retract | 4.19–4.37 | (−35,18,20) | (−35,18,−6) |
| Handoff to P2 | 4.37–5.00 | (−35,18,−6) | (−40,−8,−6) |

### P2 — Precision Work

| Phase | Seconds | Start XYZ | End XYZ |
| --- | --- | --- | --- |
| Shallow engagement 1 | 0.00–0.16 | (−40,−8,−6) | (−40,−8,10) |
| Local pass 1 | 0.16–1.06 | (−40,−8,10) | (−28,−8,10) |
| Retract | 1.06–1.22 | (−28,−8,10) | (−28,−8,−6) |
| Coordinate center | 1.22–1.62 | (−28,−8,−6) | (0,12,−6) |
| Settle | 1.62–1.72 | (0,12,−6) | (0,12,−6) |
| Shallow engagement 2 | 1.72–1.88 | (0,12,−6) | (0,12,10) |
| Local pass 2 | 1.88–2.78 | (0,12,10) | (12,12,10) |
| Retract | 2.78–2.94 | (12,12,10) | (12,12,−6) |
| Coordinate right | 2.94–3.34 | (12,12,−6) | (40,−8,−6) |
| Shallow engagement 3 | 3.34–3.50 | (40,−8,−6) | (40,−8,10) |
| Local pass 3 | 3.50–4.40 | (40,−8,10) | (28,−8,10) |
| Retract | 4.40–4.56 | (28,−8,10) | (28,−8,−6) |
| Handoff to P3 | 4.56–5.00 | (28,−8,−6) | (55,26,−6) |

### P3 — Finishing Pass

| Phase | Seconds | Start XYZ | End XYZ |
| --- | --- | --- | --- |
| Deep engagement | 0.00–0.18 | (55,26,−6) | (55,26,20) |
| Finishing traverse | 0.18–3.18 | (55,26,20) | (−55,26,20) |
| Retract | 3.18–3.36 | (−55,26,20) | (−55,26,−6) |
| Inspection hold | 3.36–3.76 | (−55,26,−6) | (−55,26,−6) |
| Handoff to P1 | 3.76–5.00 | (−55,26,−6) | (−65,−20,−6) |

Boundary tables own every interval endpoint: no gaps, duplicated handoffs or
endpoint discontinuities. Holds use Tween intervals without transform writes;
P3's inspection hold is exactly 0.40 s.

## Easing

For normalized phase time u, carriage X uses a=0.12, b=0.18 and v=20/17:

```text
fX(u) = v*u*u/(2*a)                  for 0 <= u < a
        v*(u-a/2)                   for a <= u <= 1-b
        1-v*(1-u)*(1-u)/(2*b)       for 1-b < u <= 1
fY(u) = (1-cos(pi*u))/2
fZ(u) = 4*u^3                       for u < 0.5
        1-(-2*u+2)^3/2              otherwise
```

The Fabricator-local helper gives X 12% acceleration, 70% steady velocity and
18% deceleration for passes and coordinated positioning. Y uses sine in/out;
Z uses cubic in/out. All are monotonic without overshoot; endpoints are assigned
exactly. No shared animation framework is introduced.

## Startup, shutdown, interruption and lifecycle

Private visual states are REST, INITIALIZING, FABRICATING and SHUTTING_DOWN.
REST is exact (0,0,0), without an active Tween. These states never enter gameplay
records. `PlanetWorldState` remains authoritative; the existing deployed presenter
forwards status through `MachineVisual`.

Startup captures displayed (x0,y0,z0), retracts to −6 in `0.15*(z0+6)/26` seconds,
then coordinates X/Y to the selected entry over 0.45 s. Normal startup is
approximately 0.484615 s; already raised startup is 0.45 s. Production is not delayed.

Shutdown interrupts the current pass, captures its displayed pose, retracts to −6
in `0.18*(z0+6)/26` seconds, coordinates X/Y home over 0.70 s, then parks Z at zero
over 0.12 s. Total duration is 1.00 s from deep engagement, approximately 0.930769 s
from shallow engagement and 0.82 s when already raised. Zero-duration retraction
is omitted without moving the pose.

One Tween reference, generation counter, effective production intent and temporary
pattern cursor own the animation. Redirects capture before invalidating callbacks
and killing/clearing the old Tween. Completion guards check generation, expected
state, initialization, tree membership, effective visibility, deployed enablement,
front orientation and current production intent.

Initialization reserves an attempt. A producing-to-stopped edge advances its
cursor once, including during initialization or outgoing handoff, then shuts down.
Input Empty/Output Full/Inactive changes cannot restart shutdown or advance again.
Normal pattern completion advances once. Resuming during shutdown cancels the
obsolete return-home path; the displayed pose retracts if necessary and redirects
to the next entry without teleporting. Repeated status delivery is idempotent at
all three presentation layers. The status dot does not wait for shutdown.

`presentation_machine_id` is assigned before tree attachment and forwarded before
status-driven initialization. Starting index is `(machine_id-1) mod 3` for positive
IDs: 1/4/7 → P1, 2/5/8 → P2, 3/6/9 → P3. Missing/zero IDs use P1. No randomness
or animation phase/cursor is saved. Recovery/redeployment may allocate a new ID
under unchanged gameplay rules.

Effective ancestor hiding cancels motion, invalidates initialization and restores
rest immediately. Showing initializes from the latest intent and stable ID.
Switching away from 0° resets the front and shows the accepted static body;
switching back begins at rest. Exit cancels ownership, restores rest, clears intent
and requests readiness again. Parent entry resamples status and the adapter
resupplies it after child readiness. Recovery frees the presenter; stale callbacks
cannot restart it. No previous phase resumes across scene visits.

## Offline validation and limits

`tests/static_fabricator_animation_test.py` checks PNG identities/decoding/alpha,
source-pixel reconstruction, hierarchy and motion, exact keyframes, rational
timeline continuity, envelopes, easing, transition math, lifecycle guards,
identity forwarding and preservation. It does not execute or parse GDScript.
Seven existing suites admit only the approved presentation amendments. The deployed
source remains byte-equivalent after removing the exact identity line. Historical
baselines and gameplay protections are retained.

Set `TLWH_FABRICATOR_FRONT_FROZEN_ROOT` to the external front package directory.
Set `TLWH_FABRICATOR_FROZEN_ROOTS` to a JSON array of the four external package
directories in 0/90/180/270 order. These enable read-only inventory and byte
comparisons; they grant no engine execution authority. Absolute owner paths are
intentionally not published here.

From the repository root:

```powershell
python -B -m unittest discover -s tests -p 'static_fabricator*test.py' -v
python -B -m unittest discover -s tests -p 'static_extractor*test.py' -v
python -B -m unittest discover -s tests -p 'static_smelter*test.py' -v
python -B -m unittest discover -s tests -p 'static_*test.py'
git diff --check
git diff --cached --check
```

From `tests/`:

```powershell
python -B -m unittest -v static_ferrite_integration_test static_v2_stationary_machines_test static_current_preservation_test static_preservation_guards_test
```

Final results on November 9, 2026, all exit 0:

| Command group above | Result | Skips / failures |
| --- | --- | --- |
| Fabricator discovery, both frozen-root variables set, complete staged inventory | 36/36 PASS (18 new animation checks) | 0 / 0 |
| Extractor discovery | 13/13 PASS | 0 / 0 |
| Smelter discovery | 26/26 PASS | 0 / 0 |
| Focused Ferrite/stationary/current-preservation/guard modules | 22/22 PASS | 0 / 0 |
| Full static discovery, both frozen-root variables set, complete staged inventory | 468/468 PASS | 0 / 0 |
| Working and staged diff formatting | PASS | None |

The first Fabricator discovery run omitted the four-root variable and skipped
that optional external inventory check (35 passed, one skipped, exit 0). The final
staged run above supplied both variables and passed all 36; the full suite also
verified all four external packages without skips. No failing test was disabled.

Post-implementation rehashing preserved all 81 front-package files and all existing
artwork/import metadata. The static package checks also verified the complete
183-file four-package inventory. All five copied/staged PNGs match their accepted
encoded identities. Of 1,029 baseline tracked files, 1,016 retain exact working
bytes; the 13 changed existing files are the four production files, seven tests,
README and the static-artwork document. Removing the exact ID assignment restores
the deployed source's original byte hash. Historical README bytes likewise remain
exact outside its current-status edits. No frozen inventory or receipt changed.

The complete 25-file scope, all 26 documented choreography phases, local Markdown
links, private-path publication review and source/scene bindings passed review.
The index contains no caches, source masters, pose previews or temporary artifacts.
Documentation sync updates only the new animation document, README and the static
artwork document, preserving design/narrative canon and historical records.

No Godot graphical/headless launch, imports, native harness, performance probe or
benchmark is authorized or run. Python checks do not establish GDScript parser
correctness, Tween scheduling, rendering, gameplay success or runtime acceptance.

## Owner normal-F5 acceptance — PENDING

None of these checks has been performed or marked passed by the agent.

1. Launch the normal Godot F5 entry scene.
2. Confirm no new parser, import or runtime errors.
3. Verify the deployed 0° resting appearance matches the accepted composite.
4. Verify all four orientation mappings.
5. Confirm ghosts remain static and correctly translucent.
6. Confirm three distinct fabrication patterns.
7. Observe smooth gantry movement and brisk carriage passes.
8. Confirm shallow and deep tool engagement.
9. Confirm no tool bobbing during continuous passes.
10. Confirm tool remains behind carriage and foreground occludes correctly.
11. Verify no visible rail/support alignment problems.
12. Stop production during every major motion phase, including initialization and handoffs.
13. Confirm controlled tool retraction and return home.
14. Resume production during shutdown and verify smooth redirection.
15. Confirm repeated status updates do not restart motion.
16. Verify deterministic variation across several Fabricators.
17. Leave and re-enter the exterior.
18. Confirm scene re-entry begins from rest and reinitializes correctly.
19. Recover and redeploy a Fabricator.
20. Confirm all static orientations remain unchanged.
21. Verify status-dot position, visibility and colors.
22. Verify recipe selection, switching, input, output, production and recovery.
23. Verify Extractor barrel animation remains correct.
24. Verify Smelter thermal behavior remains correct.
25. Inspect texture clarity and ordinary performance at normal gameplay zoom.

Gates A–J cover frozen identity, preservation, hierarchy, choreography, offline
safety/lifecycle contracts, static/ghost preservation, gameplay, other presenters
and static/documentation validation. Gate K remains **PENDING — owner normal-F5
acceptance required**. The draft PR stops here for owner review. Merge, cleanup
and another milestone remain separate authorizations.
