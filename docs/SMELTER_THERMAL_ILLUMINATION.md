# Smelter thermal illumination

Implemented on `codex/smelter-thermal-illumination`, **pending merge and owner
F5 acceptance**, from PR #157 merge `ca18cfa4c9f16ab934968aed4fa764f9c1e2b58d`.
The November 9, 2026 owner authorization approves Thermal Decisions 1A–10A.
This is presentation only: no gameplay temperature, production delay or saved heat.
The [PR #157 static artwork acceptance](SMELTER_STATIC_ARTWORK.md#owner-normal-f5-acceptance)
remains historical evidence and does not establish thermal graphical acceptance.

## Approved behavior

| Operating state | Thermal presentation |
| --- | --- |
| INACTIVE | Cancel animation and immediately set opacity to zero. |
| INPUT_EMPTY | Stop pulse; fade existing opacity to zero over 1.0 second. |
| PRODUCING | Cold start: warm from zero to 0.82 over 0.5 seconds, then pulse. |
| OUTPUT_FULL | Stop pulse; fade existing opacity to zero over 1.0 second, without a hold. |

All four directions use sine in/out easing. A producing pulse is a 1.8-second
rise from 0.82 to 1.00 plus a 1.8-second fall, repeated without dwell. Its
3.6-second period is independent of two-second production. Gameplay never waits
for the artwork; the dot reports authoritative status immediately. Residual
cooling after blockage creates no completed products.

Transitions start at displayed opacity. Below 0.82, resumed warm-up takes
`0.5 * (0.82 - opacity) / 0.82` seconds. At or above 0.82, resumption rises to
1.00 using the remaining pulse-rise fraction capped at 0.5 seconds, then starts
a full falling/rising pulse. This avoids lowering already-hot illumination or
jumping to an endpoint. Identical status refreshes never restart animation.
Opacity stays within 0–1; the producing loop stays within 0.82–1.00. Completed
cooling hides the sprite and releases the tween.

## Ownership and lifecycle

The existing path remains `PlaythroughState._process` →
`PlanetWorldState.advance_production` → `DeployedMachine._process` →
`MachineVisual.status` → `_refresh_presentation`. No new simulation polling,
signal or world-state field is introduced.

[MachineVisual](../construction/machine_visual.gd) adds only two Smelter calls:
forward status with thermal enabled only outside ghosts, and hard-reset before
hiding a deactivated Smelter subtree. [SmelterVisual](../construction/smelter_visual.gd)
owns one tween and transient status/initialization/generation fields. Genuine
transitions cancel the old tween first. Finite tweens hand off through their
finished signal; callbacks check generation, initialization, tree membership and
status. No script frame callback, runtime texture or shader is introduced.

Ghosts reset directly to zero without cooling, preserving CanvasGroup composite
alpha 0.5 and no status dot. Switching machine types cannot leave hidden Smelter
animation running; Extractor's motion branch is unchanged. Tree exit invalidates
callbacks, cancels animation and clears initialization, covering recovery and
world detachment. The adapter's next ready refresh initializes producing at 0.82
and pulses; all other states initialize cold, even when status is unchanged.
Persistent production continues indoors; unknown offscreen heat is never replayed.
Fresh attachment to an already-producing record uses the same nominal policy.
Normal new deployment is empty/cold and later production uses cold-start warm-up.

Direction configuration changes textures/offsets and nonthermal visibility only;
heat opacity, visibility, phase and tween stay intact. Each Smelter owns independent
animation. Recovery destroys that presenter; redeployment starts fresh.

## Preservation

All ten PNGs and ten import sidecars, the [frozen inventory](experiments/smelter_static_artwork.json),
root `(64,128)`, scale `4/29`, directional anchors/offsets, uncentered sprites,
local mipmapped linear filtering and Body/Interior/Illumination/Foreground
source-over order remain unchanged. No scene, material, global lighting, camera
or Y-sort changes are made. The deployed-only dot retains radius 3.5, four colors,
directional positions and foreground sibling ownership. Production, definitions,
capacities, inventory, inspection/transfers, collision/placement, recovery/travel,
Extractor, Fabricator, Dave and stationary Smelter remain unchanged.

## Static validation and limits

From the repository root:

```powershell
Push-Location tests
python -B -m unittest -v static_smelter_thermal_test static_smelter_artwork_test static_smelter_footprint_test static_extractor_artwork_test static_extractor_animation_test static_ferrite_integration_test static_v2_stationary_machines_test static_current_preservation_test static_preservation_guards_test static_terrain_stage3c_test
Pop-Location
```

Implementation validation: **68/68 PASS** (thermal 13, artwork 8, footprint 5,
Extractor artwork 5, Extractor animation 6, Ferrite integration 9, stationary
machines 8, current preservation 4, preservation guards 1, Stage 3C 9).
The pre-implementation artwork suite also passed **8/8**. Tests inspect source
contracts and independent offline easing examples; they do not execute
GDScript or certify actual tween behavior. Existing checks preserve PNG/RGBA
identities, imports, frozen idle reconstruction, geometry, status dot and gameplay.
Text comparisons use existing LF/CRLF normalization; PNGs remain exact bytes.
Only superseded artwork-test assertions are amended; Extractor animation tests
remain unchanged. No Godot import, headless/graphical execution, benchmark or
performance probe was performed. Parsing, rendered transitions and lifecycle
behavior require owner F5 acceptance. Expected incremental cost is one existing
heat sprite and one tween per active/cooling machine; performance is unmeasured.

## Owner normal-F5 acceptance — pending

Run ordinary owner F5 against the feature commit. Report observations and any new
import, parser or runtime errors. Items remain unchecked until actual owner
results are supplied; keep the PR draft until acceptance.

1. [ ] Deploy cold Smelters in all four directions; verify registration.
2. [ ] Transfer ore and inspect 0.5-second cold warm-up in every direction.
3. [ ] Review smooth 3.6-second full pulse, intensity and no endpoint dwell.
4. [ ] Check readability at zoom 0.5×, 1.0× and 1.5×.
5. [ ] Deplete input: immediate blue dot, 1.0-second cooldown to cold.
6. [ ] Fill output: immediate amber dot, 1.0-second cooldown, no warm hold.
7. [ ] Collect with input remaining: immediate production and smooth heat resumption.
8. [ ] Collect without input: input-empty status and cold/cooling illumination.
9. [ ] Interrupt warm-up/cooling repeatedly, including resumption above/below 0.82: no flash, jump or stale restart.
10. [ ] B-recover while illuminated: exact item returns, cold redeployment, no stale heat.
11. [ ] Travel exterior → interior → exterior while producing: nominal heat on return, no warm-up replay or duplicates.
12. [ ] Become input-empty or output-full indoors: return immediately cold with correct status.
13. [ ] Observe mixed-direction Smelters with independent statuses during ordinary play.
14. [ ] Rotate/switch ghosts among all three machines: no ghost heat/dot, unchanged composite transparency and no hidden animation.
15. [ ] Check dot colors, radius, visibility and directional positions.
16. [ ] Check 0° foreground, Dave/neighbour sorting, overhang and unchanged collision/placement.
17. [ ] Confirm one ore → one ingot per two seconds, capacities 20/20, inspection, transfers, collection and recovery.
18. [ ] Recheck Extractor animation/artwork, Fabricator, Dave and stationary Smelter/E recovery.
19. [ ] Confirm no new Godot import, parser or runtime errors.
