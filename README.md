# The Long Way Home

A story-driven science-fiction automation adventure. This fresh Godot project
has a player movement prototype with camera follow and mouse-wheel zoom, plus a
minimal ship-interior environment and collision foundation, plus data-driven
Computer dialogue, inspection and objective activation. Merged PR #26 adds an
authored exterior and reusable hatch transitions. Merged PR #27 adds seeded
chunk terrain. Merged PR #28 adds First Ferrite discovery, an internal musing
and Extractor guidance. Merged PR #30 adds a maintenance bay and provisional
inventory. Merged PR #32 adds Extractor deployment and recovery; merged PR #36
adds Ferrite Ore production and collection. Merged PR #38 adds Smelter recovery
and the Ferrite acquisition musing. Merged PR #39 adds Smelter deployment.
Merged PR #40 adds Ferrite Ingot production; merged PR #42 adds Fabricator rack
recovery. Merged PR #43 adds Fabricator deployment, initial recipe selection
and material loading; merged PR #44 adds in-place recipe switching. Merged PR #45
adds automatic Fabricator production and first Plate acquisition; owner acceptance
remains separate from agent static checks.
Its gameplay implementation is independent of FactoryGame; the approved Dave
migration below reuses only two legacy artwork sheets.

## Requirements and setup

Codex must follow the [Godot execution safety policy](AGENTS.md#godot-execution-safety)
before using the setup or launch instructions below. Graphical execution requires
explicit owner authorization; headless execution remains suspended following the
PR #5 incident, subject only to the separately authorized exact local-runner
exception in that policy.

- Godot **4.7.2 stable**, standard build. GDScript is the initial scripting language;
  no .NET SDK or third-party plugins are required.
- Git for cloning the repository.

```sh
git clone https://github.com/interneth3ro/the-long-way-home.git
cd the-long-way-home
godot --editor --path .
```

`godot` denotes your Godot executable; use its full path if it is not on `PATH`.
Alternatively, import `project.godot` through Godot's Project Manager.

## Launch and validation

The [local PowerShell test runner](docs/LOCAL_TESTING.md) runs the existing Python
static suite in this checkout. `-Mode NativePlan` copies tracked working inputs
for nonexecuting inspection using the fixed executable identity. On 2026-10-29,
the owner approved standing routine use of the restricted Native runner, replacing
the earlier one-invocation permission. Only the fixed import and recipe-switching
phases are covered; no automatic retries or unattended execution. The B1 change
adds only the three required IBM Plex Sans `.ttf` paths and their matching
`.ttf.import` metadata sidecars to asset staging.
See the guide for the fixed scope, limits and verification requirements.

**F5** starts production V2 (P8 merged in PR #65). F6 with
`scenes/main/main_v2.tscn` open also starts V2. For the legacy fallback, stop,
open `scenes/main/main.tscn` and press **F6**. F5 stays configured for V2.
From a terminal in the project root:

```sh
godot --path .
godot --headless --editor --path . --quit
godot --headless --path . --quit-after 60
```

The last two commands validate editor import and a bounded main-scene launch.
Headless checks do not verify graphical appearance. While execution is restricted,
use only nonexecuting checks under the policy above and report them as static
validation; runtime and engine verification remain unperformed.

## Extractor inspection visual pilot (feature branch, pending merge)

`codex/extractor-inspection-pilot` introduces an Extractor-only two-column
[inspection view](scenes/ui/extractor_inspection.tscn) inside the existing machine
presenter. The right-edge panel is vertically centered between a 24-unit top
clearance and the bottom hotbar/hint region. Its normal logical size is 640 x 510;
width is capped at 48% of the logical HUD, and logical heights below 740 use a
480-unit panel, tighter spacing and a smaller gauge. The owner has accepted the
overall layout, artwork, gauge, styling and proportions, including the divider/grid
refinements and portrait smoothing. The padding/header refinement below remains
pending owner screenshot review.

Extractor content now has 24-unit left/right and bottom padding, with 20 units at
the top. The private panel StyleBox changes only when switching presentation mode;
Smelter/Fabricator restore their original 16-unit sides and 14-unit top/bottom.
B2 offsets compensate for the active content margins, preserving its outer frame
rectangle and existing 24-unit nine-patch margins. Panel dimensions are unchanged.
The header displays `EXTRACTOR`, inheriting B1Title's IBM Plex Sans SemiBold and
copper-amber color, with a local 26-unit size override and Label vertical centering
within the existing container row. Close, its tooltip and Esc are unchanged.
The portrait remains flexible and production values wrap/scroll as before.

The unchanged [Extractor artwork](assets/environment/maintenance_bay_v2/machines/extractor_stationary.png)
uses aspect-preserving fit with native texture size excluded from layout minimums.
No portrait border, crop or new artwork is added. Output
identity, exact stored/capacity quantities and a utilization bar sit above Collect
All. The right column shows status, actual cycle percentage and definition-derived
nominal rate, duration and yield (currently 60.0 ore/min, 1.0 s and 1 Ferrite Ore).
The rate is nominal capacity, not measured throughput. A subdued header divider
spans the inner content width. The existing column separator uses an explicitly
vertical line style; both remain separate from the B2 frame. Production details
use compact label/value rows with right-aligned, wrapping values and a muted rule
beneath each row. Secondary details alone may scroll; Close and Collect All stay
outside that region.

Option A portrait minification changes only `mipmaps/generate=false` to `true` in
[the shared import sidecar](assets/environment/maintenance_bay_v2/machines/extractor_stationary.png.import)
and the UI Portrait's `texture_filter` from 2 (Linear) to 4 (Linear with Mipmaps).
Compression remains lossless (`compress/mode=0`); source size, alpha channel,
alpha-border fixing and premultiplication settings are unchanged. The original
PNG remains byte-identical. Godot will generate the mip chain on its next import;
no reimport or Godot launch was performed by the agent.

The same texture's stationary maintenance-bay sprite retains its explicit Linear
filter, which does not sample mipmaps; its shader, transform and original-resolution
sampling stay unchanged. The shared imported texture does gain roughly 33% memory
for the mip chain. UI minification should reduce edge aliasing, but may soften fine
mechanical detail or alpha fringes. The owner has accepted the smoothing; the agent
has not performed graphical validation. Anisotropic
filtering is not added for this flat, aspect-preserving portrait.

The 1319 x 1186 source fits the existing portrait rectangle proportionally. Its
physical source-to-screen scale is `min(rect_width / 1319, rect_height / 1186) *
P * sqrt(S)`, using logical rectangle dimensions and the unchanged hybrid formula.
At the 640-unit normal panel width, the nominal left-column width bounds local
scale to about 0.229, or 0.195 physical scale at 1280 x 720 / 85%; height fitting
can reduce this further. These are static bounds, not measured engine output.
Compare edges, bolts, pipes and alpha fringes at 75/85/100% and supported window
sizes; also compare the stationary machine at unchanged camera zoom. Reverting the
two settings restores the previous sampling configuration. No derivative artwork,
custom processing or new shader is introduced.

The reusable [cycle gauge](scenes/ui/cycle_gauge.gd) draws a subtle bezel, ticks,
track, status-colored arc and numeric percentage with CanvasItem drawing. It has
no independent animation or simulation. Producing is teal, Output Full amber and
Inactive gray. The opt-in [machine action theme](assets/ui/machine_actions.tres)
supplies primary/compact-close variations without changing global B1 styles.

All machine inspections temporarily suppress the objective tracker's expanded
panel and compact restore control, giving inspection priority. The tracker's
presentation preference and expanded flag are not modified by this override;
closing inspection removes it, including on transitions and teardown. Objective
progression continues. Smelter/Fabricator content layouts, recipe configuration,
pause leases, range guards, stored-output identity and transaction methods remain
unchanged. The 85% default and UIScaleRoot/hybrid formula are unchanged.

All 51 Python static checks pass. Agent validation remains static only; engine
parsing and input delivery are unverified by the agent. The owner reviewed the
overall graphical appearance, including the divider/grid refinement and portrait
smoothing. Padding/header changes need owner screenshot review. Proposed exact-file
preservation allowances in
`tests/static_v2_production_host_test.py` require owner review before Native use,
including the Option A import sidecar and updated machine presenter padding hash.
No Native or graphical Godot execution is authorized by this pilot's test changes.

Owner graphical acceptance, performed separately under the execution policy:

1. Inspect a deployed Extractor at 1280 x 720, 1024 x 576 and maximized, comparing
   75%, 85% and 100%. Check portrait fit, B2 edges, column proportions, gauge/text
   clarity and Close/Collect hit targets; confirm the 85% startup default. Check
   the header rule, vertical column rule, aligned production values and row rules,
   including wrapped Cycle Yield text and scrolling at compact sizes. For the new
   refinement, check side/bottom content clearance, unchanged outer B2 alignment,
   centered uppercase 26-unit title, and gauge/value/button fit without enlargement.
2. Watch real production progress; check teal Producing, amber Output Full and
   gray Inactive where reachable. Confirm definition values and storage/bar agree.
3. Collect empty, partial and full output; verify disabled empty state and exact
   inventory transfer. Leave range, reopen and close by both header and Esc.
4. Open/close inspection with the objective expanded, pinned, collapsed and hidden;
   verify the prior presentation returns, including after inventory/transition
   interruptions. Confirm the compact tracker never overlaps the panel.
5. Check unchanged Smelter inspection and Fabricator initial selection, switching,
   Back/errors, pause release, post-placement range feedback and old-product output.

## Hybrid UI scaling foundation (feature branch, pending merge)

`codex/hybrid-ui-scaling` adds a shared
[HUD-root behavior](scenes/ui/ui_scale_root.gd) to inventory, hotbar, machine
inspection (including its recipe chooser), objective tracker, dialogue,
interaction prompts/responses, musings and construction hints. Existing presenters,
CanvasLayers, node paths, child anchors, content sizes and visibility rules stay
in place. The transition curtain, world-space construction preview, world scale
and camera zoom are excluded. B1/B2 resources, fonts and artwork are unchanged.

For client size `W x H`, the existing 1280 x 720 reference and
`canvas_items` / `expand` stretch supply `S = min(W / 1280, H / 720)`.
The provisional balanced hybrid formula applies root multiplier
`U = P / sqrt(S)`, giving nominal physical UI multiplier `S * U = P * sqrt(S)`.
Each root uses the current logical viewport extent divided by `U`, with top-left
anchors/pivot, so bottom/right child anchors still reach the screen edges.
Viewport resizing recalculates the roots; a shared session preference updates
them immediately. No root Window content scale or camera compensation is added.
Godot rounds expanded logical viewport dimensions, so non-reference aspect ratios
can have subpixel differences from the nominal arithmetic.

The isolated [temporary selector](scenes/ui/ui_scale_preview.gd) offers
**75%, 85% and 100%**, with **85% as the owner-approved default**. The selector
reads the shared preference and shows 85% selected on startup. It appears
only when running the editor executable (`OS.has_feature("editor")`), including
the normal editor-launched game; exported games create no selector controls.
It stays outside the scaled roots at top center, uses default styling rather
than B1/B2 resources, consumes pointer/scroll input and adds no keybinding or disk
persistence. Restarting the game resets the preference to 85%. The owner reported
all six PR #84 functional acceptance tests PASS and approved 85% as the
general-purpose balance on 2026-10-29; 75% remains a valid personal preference.
At `S != 1`, even 100% uses the hybrid formula and therefore differs from the
old globally stretched presentation.

Inventory assignment and hotbar clearing menus remain children of their scaled
HUDs. Godot 4.7.2's
[PopupMenu setup](https://github.com/godotengine/godot/blob/4.7.2-stable/scene/gui/popup_menu.cpp)
explicitly derives Window content scale from the parent CanvasItem transform;
the helper does not apply a second multiplier. Attachment points use viewport
coordinates for embedded menus and screen coordinates for native windows.
Menus are bounded to their usable parent area; hotbar menus use the measured
popup height rather than a fixed offset. Resize/preference changes dismiss open
menus so they can reopen with fresh scale, bounds and attachment positions.

Built-in tooltips retain Godot's viewport-based text sizing and screen-edge
placement rather than being reduced with the HUD. This preserves the existing
tooltip presentation for comparison; tooltip/HUD size differences are a known
limitation of this foundation. Hover is re-evaluated after layout changes.
The [4.7.2 tooltip implementation](https://github.com/godotengine/godot/blob/4.7.2-stable/scene/main/viewport.cpp)
uses the tooltip Window's viewport scale, not the HUD Control transform.
Actual readability, pointer attachment and edge behavior require owner checks.

Known limits: rasterized IBM Plex fonts may soften under fractional Control
scaling; no MSDF/import changes are included. The provisional 1024 x 576 minimum
and the smallest preference can produce very small quantities/key labels.
At the scaling foundation milestone, machine panels remained content-driven with
no new whole-panel scroll region, and expanded objective/machine panels could
overlap at upper right. The Extractor pilot above adds bounded presentation and a
temporary tracker override. Percentage-width musings retain their
screen-relative width while text/padding scale. These remain useful review
considerations when changing window size or personal preference.

Validation: the original 46-test static suite initially rejected the intended
presentation edits through its preservation checks. The owner approved the exact
eleven-file normalized-byte allowance and rejection assertions in
`tests/static_v2_production_host_test.py` (file SHA-256
`115D9B737322606C1C5B232BDCDE5199130A68794DF027862AD3DB1079D74B33`).
The proposed suite passes **47 Python static tests**. Existing B1/hotbar/P8
historical comparisons remain behind those exact byte checks. The one authorized
Native attempt at `edaf334` passed static checks but stopped at cold import with
`ENGINE_ERROR`; the recipe test did not run. The retained 4,096-byte excerpt
contains startup output, so it does not identify the engine error. Static API
review found and corrected a call to engine-internal `Window.get_usable_parent_rect()`;
the helper now uses public viewport bounds / DisplayServer screen bounds.
After separate owner authorization for one fresh attempt, validation at
`d95c7f1` passed: **47 static tests, cold headless import and the existing recipe
switching regression (zero failures)**, with infrastructure/authorization checks
PASS. No automatic retry was performed. Failure evidence remains in ignored
`artifacts/logs/native-failure-f71e06401208402a83fea6aec24accd7.json`; both external
stages are preserved. No agent graphical execution occurred; the subsequent
six-test owner acceptance and 85% default decision are recorded above.
Runner, allowlists, execution policy and native test assertions are unchanged.

The approved 85% default follow-up at `18dcc40` also passed **47 static tests,
cold headless import and recipe switching (zero failures)** in one fresh
restricted Native run. No protected hash/assertion changes or retry were needed.
Static inspection confirms the unchanged selector derives its selected startup
button from the shared preference and retains all three comparison options.

Owner graphical checklist (further agent execution requires separate authorization):

1. In a separate game window at the normal maximized resolution, confirm 85%
   is selected on startup and compare the retained 75%, 85% and 100% options.
   Repeat in fullscreen if authorized.
2. Check inventory, ten hotbar slots and each machine/recipe state for alignment,
   click targets, clipping, font sharpness, icon clarity and B2 corners/edges.
3. Assign each hotbar destination, clear assignments and inspect tooltips near
   screen edges. Resize with a menu/tooltip open, then reopen it; verify scale,
   position, dismissal and complete access to all ten destinations.
4. Check expanded/restored objectives alongside machine inspection, dialogue,
   responses, prompts, musings and construction hints. Confirm existing hotbar
   visibility rules and identify any overlap that needs a separate layout change.
5. Resize through 1280 x 720 and 1024 x 576 and a wider/taller aspect ratio.
   Confirm the selector remains reachable and anchored panels stay on screen.
6. While placing/recovering, click selector buttons, inventory/hotbar controls and
   menus; none may place, recover or cancel a machine through UI input. Check
   hover regions after scale changes, including before moving the mouse.
7. Change UI preference at fixed camera zoom and verify unchanged world framing
   and mouse targeting. Check travel/fade coverage and retained UI preference.
   The owner-approved default remains 85%; comparisons do not persist.

## B1 UI foundation and desktop display (PR #77 merged)

The shared [B1 theme](assets/ui/b1_theme.tres) and
[panel StyleBox](assets/ui/b1_panel.tres) establish dark translucent panels,
muted teal progress/hover states, copper-amber titles/focus states and ivory text.
IBM Plex Sans Regular, Medium and SemiBold are bundled unmodified with their
[upstream source and SIL OFL 1.1 license](assets/fonts/ibm-plex-sans/README.md).
The machine HUD receives this theme; dynamically generated recipe buttons inherit
it. The inventory modernization below extends it to the inventory HUD. Extractor,
Smelter and Fabricator keep the same nodes, layout, transactions, recipes and
opening/closing behavior. Other HUDs retain their styles.

Reuse by assigning the theme to a Control root. PanelContainer, Button,
ProgressBar, Label, VBox/HBox defaults and B1Title, B1MutedLabel,
B1WarningLabel label variations are available. Body/buttons use 18-unit text,
titles 22, supporting text 16; containers use 10-unit gaps, panels 16 horizontal /
12 vertical padding, and buttons 12 horizontal / 7 vertical padding. Button normal,
hover, pressed, disabled and focus styles are defined; existing focus behavior is
unchanged. Inventory adds B1InventorySlot and B1InventoryDivider variations.

The project explicitly starts as a decorated resizable 1280 x 720 window, with
native maximize/restore available. The persistent
[display script](scenes/main/display_configuration.gd) sets the provisional
1024 x 576 client minimum through Window.min_size. canvas_items plus expand
uses available aspect-ratio area with automatic proportional scaling. Alt+Enter
toggles nonexclusive borderless fullscreen, restores session window geometry
(clamped to the current display work area), and returns maximized windows to
maximized mode. Window preferences are not saved. Use a separate native game
window for owner display testing; editor-embedded game behavior can differ.
The [Godot Window modes](https://docs.godotengine.org/en/stable/classes/class_window.html#enum-window-mode)
and [stretch settings](https://docs.godotengine.org/en/stable/classes/class_projectsettings.html#class-projectsettings-property-display-window-stretch-aspect)
define these APIs.

Camera zoom remains 0.75-1.5 and V2 room scale remains 1.25. Wider/taller views may
expose finite room-art boundaries. The foundation did not change camera clamping,
artwork or HUD placement, and did not add hotbar, settings or UI-scale options.
The inventory/Tab follow-up is described below. Headless checks cannot accept
the appearance or native window behavior. The known Alt+Enter issue is deferred.

Validation at `0f7070a`: 43 Python static checks PASS, 54 inert runner fixtures
PASS, and restricted Native cold import plus recipe-switching regression PASS.
The first B1 run at `4d741f1` stopped after import because generated font sidecars
were unexpected; the recipe test was NOT RUN. After separate owner authorization,
the exact three sidecars were tracked/allowlisted and one fresh-stage rerun passed.
The initial failure evidence remains in ignored artifacts/logs; both stages remain
preserved. No graphical Godot, window-mode acceptance or performance test was run.

Owner acceptance follow-up (PR #77): the owner reported six of seven tests
PASS: Smelter appearance/functionality, other machines, resizing, expanded world
view and basic regression. Alt+Enter produced no visible response. Source review
found the persistent display node enabled, no competing gameplay handler for this
chord, and a valid main Enter binding; actual event delivery/window behavior was
not observed. The shortcut now checks InputEventKey directly for Alt plus main
or keypad Enter, using logical or physical codes, ignoring release/echo and extra
Ctrl/Shift/Meta modifiers. The obsolete InputMap action is removed. Fullscreen
mode selection, geometry restoration, maximize handling and resize/aspect rules
are unchanged. This correction still requires owner graphical retesting in a
separate native game window; editor/OS interception cannot be excluded by static
inspection. No new graphical execution is authorized by this note.

Correction validation at `dee6050`: existing Python static suite 43 PASS;
restricted Native cold import and recipe-switching regression PASS after explicit
owner renewal of one invocation. Static inspection confirms press/echo/modifier
checks and unchanged window restoration/maximize code. These checks do not inject
real key events or verify fullscreen visually. The existing static preservation
helper now accepts editor omission of the three default-valued window flags while
rejecting nondefault changes. Those omissions were initially left uncommitted.
PR #78 now tracks Godot's normalized form: mode, resizable and borderless use the
engine defaults (0, true, false) without redundant entries. This prevents recurring
editor-save diffs while keeping all other project configuration changes visible.
The normalization passed the existing 43 static tests; no further Native run was
performed after the separately recorded successful attempt.

Owner acceptance checks, when the owner chooses to launch graphically:

1. Inspect a deployed Smelter: typography, panel transparency/border, button normal,
   hover, pressed and disabled states, progress and input/output counts. Verify
   Transfer All, Collect All and Close/Esc retain their behavior.
2. Inspect Extractor and Fabricator; verify recipe cards inherit the theme, recipe
   switching/pause/Back/errors and existing panel lifecycle remain intact.
3. Resize to the provisional minimum, maximize/restore, and inspect 16:9, 16:10 and
   ultrawide windows. Check readability, panel bounds and newly visible room edges.
4. Alt+Enter from a moved/resized window and from maximized mode; check return
   geometry, title-bar controls, Alt-Tab and multi-monitor/DPI behavior. Holding
   the shortcut should not repeatedly toggle.
5. Check wheel zoom extremes, unchanged world/player scale, inventory Tab,
   dialogue, prompts, musings and construction hints. Their broader responsive
   modernization remains future work.

## B1 inventory modernization (PR #78 merged)

The persistent left-side inventory uses the shared B1 theme and panel with a
24-position Materials grid (three rows of eight) and an eight-position Machines /
Equipment row (compact follow-up merged in PR #80). All empty positions remain visible and subdued; they have no
action or tooltip. Occupied positions show a 22-unit icon or 14-point symbol
and a 12-point quantity.
Hover shows the full name and exact total. Materials have no click action;
one left-click on a packaged machine requests deployment through the unchanged
construction controller. Unavailable/non-machine equipment is disabled and marked
not deployable in its tooltip. Context-dependent deployment rejection remains
with the controller. There is no selection step or Deploy button.

`ItemPresentation.ICONS`, also exposed as `InventoryUI.ITEM_ICONS`, is the shared
presentation-only lookup for inventory and hotbar: Plate/Rod reuse existing
recipe textures; ORE, BAR, EX, SM and FB are temporary distinguishing symbols for
Ore, Ingot, Extractor, Smelter and Fabricator. Each can be replaced by a Texture2D
in the lookup without changing storage or layout. Unknown future types use `?`
with their full identity in the tooltip. Quantities below 1,000 are exact on the
slot; larger values truncate to K/M/B/T/Qa/Qi, with exact int64 totals on hover.

Items sort by stable `item_id` within each section, independent of acquisition
order. Quantity-only updates do not reorder slots. New/removing types can shift
later IDs. Slots are built once; `InventoryState.changed` refreshes their contents.
The current catalog has four material and three machine types, but the aggregate
storage accepts more. Extra types appear in a bounded 64-unit scroll list below
the equipment row with section, name and exact total; overflow machines retain
direct deployment. This is a presentation fallback, with no storage capacity,
stack records, pagination, rearrangement or transaction changes.

Both grids use eight-column GridContainers, 42-unit slots and four-unit gaps.
The panel keeps its left/top placement (24, 100); B2 padding refinement makes
its width 396 units (364-unit grid plus 16-unit padding on each side), up from
PR #80's 380. A private copy of the shared panel style changes only padding:
16 horizontally and 14 vertically. B1 colors,
transparency, borders and corners remain unchanged; the hotbar and shared theme
are untouched. Section spacing is four units; the title is 18-point, section
headings/hint are 14-point, and the hint reads `Tab / Esc to close`. Deployment
and hotbar-assignment guidance remains in machine and overflow tooltips.

Height remains content-driven. Static font/spacing arithmetic estimates about
317 units without overflow, 385 with its existing 64-unit scroll area. These
are layout estimates, not measured Godot output. At 1024 x 576 the existing
0.8 scaling gives a 316.8-pixel-wide panel, 33.6-pixel slots,
17.6-pixel icons, 11.2-pixel symbols/headings and 9.6-pixel quantities. The panel
bounds fit both supported canvases by static inspection. IBM Plex Sans Regular
advance metrics put the widest quantity at about 36.5 of 38 available logical
units; its 15.6-unit line height fits the 18-unit quantity region. The owner
inspected the eight-column layout in Godot and approved it. Specific resolution
coverage and long-quantity readability were not separately recorded; these remain
useful acceptance checks rather than claims established by the static metrics.
No display settings or player UI-scale control changes are included.

B2 Balanced frame on `codex/b1-refined-industrial-inventory` (pending merge):
[the reusable NinePatchRect scene](scenes/ui/b2_panel_frame.tscn) uses the
[owner-supplied 96 x 96 RGBA texture](assets/ui/TLWH_B2_ninepatch_96.png), unchanged.
All four patch margins are 24; horizontal and vertical edges use TILE, with fixed
corners, linear filtering and center drawing disabled. The transparent center
preserves the existing B1 background. The procedural experiment has been removed.
The accompanying standard texture-import metadata uses lossless compression and
no mipmaps; no engine cache is tracked.

The accepted inventory integration instances this frame in a mouse-transparent Control wrapper.
PanelContainer fits the wrapper to its padded content rectangle with explicit
FILL size flags. Both the reusable frame and its inventory instance explicitly
use anchor layout mode and full-rect anchors. Instance offsets (-16, -14, +16, +14)
undo only the private 16/14 content padding: the resulting frame rectangle equals the
panel rectangle at every size, starting at (24, 100). No outward overhang or
texture-sized rectangle determines the frame size. The panel grows only to fit
the unchanged grid and new padding; content structure and placement stay unchanged. Both decorative nodes ignore mouse
input and inherit panel visibility. No additional script or input handler is
required; the shared theme and hotbar remain unchanged. To reuse later, instance the scene under a similar
wrapper and adjust its offsets for the host's padding. The machine follow-up below
uses that pattern; other panels are unchanged.

Owner testing found the first integration rendered a small upper-left decoration.
Its instance used position layout mode (0), which resets inherited anchors to
top-left. The earlier 46-test static PASS did not verify that layout behavior.
The correction explicitly uses anchor mode (1) before setting full-rect anchors.
The owner subsequently confirmed that the corrected frame surrounds the panel;
its placement and nine-patch scale are accepted. The final padding refinement
addresses the owner's heading/grid/hint clearance feedback: 16 horizontal and
14 vertical units. The 364-unit grid stays unchanged. Pixel inspection of the
unchanged asset finds faint corner alpha (up to 5/255) inside a 16/12 inset;
a 16/14 inset is fully transparent, including the corner and tiled-edge regions.
No individual labels or slots are offset. Vertical content spacing stays four.
The frame offsets change only to compensate for the new padding, keeping its
rectangle equal to the actual panel at normal and overflow heights.

Static padding/slot geometry, frame-to-panel rectangle equality, supported-canvas
bounds, asset clearance, documentation links and `git diff --check` PASS.
The owner approved the two exact inventory scene/script preservation hashes;
only those entries changed, in commit `dd9cbc3`. Historical comparisons,
runner controls and Native test assertions remain unchanged. One authorized
`pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Native` run at that revision
with the working framing/padding inputs passed: 46 Python static tests, cold
headless import and recipe-switching regression (zero failures). Infrastructure
and authorization checks PASS. The retained fresh stage is
`tlwh-native-plan-95889136ca83441083e6a0802db95d54`. No retry or graphical Godot
launch occurred. On 2026-10-29, after the padding correction and successful Native
run, the owner reported visual tests PASS and accepted the B2 inventory framing
and padding. Specific resolution/overflow coverage was not separately recorded.
Height estimates use font-table metrics and spacing arithmetic; the owner's
visual acceptance is separate from the agent's static and headless checks.


### B2 shared machine inspection framing (feature branch, pending merge)

On `codex/b2-machine-inspection-frame`, the shared
[machine scene](scenes/ui/machine_ui.tscn) instances the existing
[B2 frame](scenes/ui/b2_panel_frame.tscn) for Extractor, Smelter and Fabricator.
The artwork, 24-unit patch margins and shared frame scene are unchanged.
A mouse-transparent bounds Control is required because PanelContainer lays out
its direct Control children inside the content margins. As in inventory, FILL
flags, full-rect anchor layout and offsets (-16, -14, +16, +14) compensate for
those margins so the frame follows the actual outer panel at every content size.
The decoration precedes Content in sibling order, keeping controls above it.

The [machine presenter](scenes/ui/machine_ui.gd) duplicates the B1 panel StyleBox
locally, removes its four border widths and retains its translucent fill and
corner radii. Horizontal padding stays 16; top/bottom padding increases from 12
to 14 to match the accepted inventory clearance. This adds four units to the
content minimum height without imposing a fixed height or width. Existing
right/top placement and content-driven sizing remain. All content node paths,
signals, recipe controls, transfers, collection and production logic are unchanged.
Inventory, hotbar, shared theme and display scaling are unchanged.

On `codex/fabricator-range-hotbar-hover` (pending merge), post-placement
Fabricator inspection remains available outside interaction range. Change Recipe
and Collect are disabled there with `Move closer to interact` tooltips. Returning
within range restores availability subject to the existing recipe/output checks.
The existing visible-panel refresh updates distance feedback without rebuilding
controls; Transfer reuses the same range result. Action guards and transactions
are unchanged. Extractor/Smelter behavior is unchanged; opening either clears any
Fabricator-only Collect tooltip from the shared control.

Owner graphical acceptance for this refinement: with a selected Fabricator recipe
and stored output, move outside and back inside range during post-placement
inspection; check disabled buttons, tooltips, re-enabled actions, and empty-output
Collect remaining disabled. Compare active hotbar hover with normal and pressed
states, inactive teal hover, empty/depleted slots and right-click clearing at
1280 x 720 and 1024 x 576. Graphical checks require separate authorization.

The owner approved the two exact normalized-byte machine preservation hashes;
only those entries were added to the existing preservation table in `d65d32e`.
Runner controls and native test assertions are unchanged. On 2026-10-29, one
restricted `pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Native` run at
that revision with the working machine framing inputs passed all 46 Python static
tests, cold headless import and the existing recipe-switching regression (zero
failures). Infrastructure and authorization checks passed. The fresh retained
stage is `tlwh-native-plan-9d51301be6194c01b3cc8ed24624d587`.
Static inspection also verified original machine content nodes/signals and script
logic are unchanged, frame ordering/input/rectangle arithmetic, and local links;
`git diff --check` passed. No retry or graphical launch occurred. These checks do
not establish visual clearance, mouse interaction or owner graphical acceptance.

Owner graphical acceptance, after separately authorizing graphical execution:

- Inspect Extractor status/progress, output storage, Collect and Close clearance.
- Inspect Smelter input/output sections, Transfer, progress, Collect and Close.
- Inspect Fabricator initial recipe selection, selected recipe, multiple inputs,
  Change Recipe, paused/error/Back states, progress, Transfer and Collect.
- Across those content heights, confirm full-panel corners/edges, retained B1
  transparency, no doubled outer border, readable content and clickable controls.
  Check the supported 1280 x 720 and 1024 x 576 client sizes for clipping.


Tab replaces I in the inventory InputMap action. Inventory consumes Tab presses
and repeats in `_input`, before GUI focus navigation; only the initial press
toggles. Tab, Esc and the Inventory (Tab) button close the panel. Existing opening
signals still close machine inspection and cancel construction, and deployment
still closes inventory. Other keybindings remain unchanged.

Validation at `4f8195c`: 43 Python static checks PASS; resource wiring, icon
coverage, ordering/refresh/deployment/input paths and layout bounds inspected
statically; local Markdown file links and `git diff --check` PASS. The single
restricted Native attempt stopped after cold import: Godot rewrote the staged
IBM Plex Sans sidecars from CRLF to LF, violating required byte identity. The
runner reported Import FAIL / Infrastructure FAIL; recipe regression NOT RUN.
No retry or runner/sidecar amendment was made. The retained stage is
`tlwh-native-plan-b404eeab0c76478aae7378363e2e37fa`; bounded evidence is
`artifacts/logs/native-failure-5049f4c070854f8196e19e5e0dade7ce.json` (ignored).
Graphical layout, actual Tab events and deployment interaction remain unverified.
The static preservation update was separately owner-approved: it pins the exact
replacement inventory scene/script hashes and normalizes only inventory I to Tab.
Runner commands, tests, boundaries and executable identity remain unchanged.

PR #78 font metadata follow-up: all three tracked IBM Plex Sans sidecars
(Regular, Medium, SemiBold) had 36 CRLF endings in the checkout because Git's
`core.autocrlf=true` expanded their already-LF repository blobs. In the preserved
failed stage Godot changed only these line endings; every resulting byte matched
its committed blob. The checkout is now normalized to LF, with exact-path
`text eol=lf` attributes to prevent recurrence. No metadata fields, font binaries,
runner controls or inventory implementation changed. After explicit owner
approval for one fresh attempt, the unchanged restricted runner at `9fd87ef`
passed all 43 static tests, cold import and the recipe-switching regression
(zero failures), including infrastructure, authorization and byte-integrity checks.
The new retained stage is `tlwh-native-plan-1058befc971f4506b9abcd7a882f2e5e`.
The previous failed stage and evidence remain intact. Exactly one fresh attempt
was made; no further retry or graphical execution occurred. This confirms the
font staging correction, while graphical inventory acceptance remains pending.

Owner acceptance, when the owner chooses to launch graphically:

1. Open/close using Tab and the button in all three environments; verify I has
   no effect, held Tab toggles once, Esc closes, and Tab does not move GUI focus.
2. Inspect all 32 positions (24 Materials, eight Machines / Equipment), section divider, icons, exact hover totals and empty,
   occupied, hovered and disabled states at 1280 x 720 and 1024 x 576. Check the
   rightmost column, bottom hint and quantities for clipping at both zoom extremes.
3. Acquire materials, collect output, recover machines and spend quantities;
   verify totals refresh and quantity-only updates keep item ordering.
4. Single-click each recovered machine: verify immediate ghost entry, no placement
   from the slot click, R rotation, invalid placement feedback and right-click/Esc
   cancellation. Verify inventory cancels construction and closes inspection.
5. Travel between rooms/exterior and verify inventory quantities, machine panels
   and objectives continue normally. Overflow is a future-catalog safeguard;
   current gameplay cannot populate it without additional item definitions.

Compact inventory follow-up (pending merge): the owner approved the eight-column
layout and both exact-file preservation hash updates on 2026-10-29. The two
normalized hashes pin the complete final inventory scene and script; all other
preservation comparisons remain unchanged. No runner policy, hotbar code or native
assertions changed.

The single owner-authorized restricted Native run at `f4bc6e8` passed all 46 Python
static tests, cold headless import and the recipe-switching regression (zero
failures), plus infrastructure, authorization, executable and input identity
checks. The fresh retained stage is
`tlwh-native-plan-a2b1150e878749bfa8b672b6da8915c8`. No retries or agent graphical
execution occurred. The owner subsequently approved both layout and validation
results. These headless results establish import and existing recipe-test success;
they do not independently verify inventory/hotbar input or visual behavior.

The current catalog cannot populate overflow; code inspection confirms the same
scroll rows start at material index 24/equipment index 8, with deployment and
assignment connections preserved. The acceptance checklist above remains useful
for quantities including three digits and Qa suffixes at both display sizes,
tooltips, all empty slots, Tab/Esc, machine left/right-click and the unchanged
hotbar. When future catalog types populate overflow, also check scrolling both
sections and deploying/assigning overflow equipment.

## B1 hybrid hotbar (feature branch, pending merge)

`codex/b1-hybrid-hotbar` adds ten persistent 52-unit B1 slots centered at the
bottom, labeled **1-9, 0**, with six-unit gaps. This is an 18.75% reduction from
the original 64-unit hotbar slots. One dark backing panel surrounds the row,
reusing a private copy of the B1 panel style with 90% background opacity,
a thin border and four-unit padding. Its overall size is 582 x 60 units with
a 16-unit bottom margin. Icons/symbols, quantities and key labels fit the smaller
slots. Shared theme resources are unchanged. The separate compact inventory
follow-up on `codex/compact-20-slot-inventory` uses 24 material
and eight equipment positions without changing this hotbar.
Temporary machine symbols and integer-safe quantities share
`scenes/ui/item_presentation.gd` with inventory. Empty slots are subdued;
assigned zero-quantity slots retain their type, show zero and remain clearable.
The deploying type uses a steady copper-amber border. On
`codex/fabricator-range-hotbar-hover` (pending merge), active hover subtly brightens
the copper border and dark fill; inactive hover remains teal. A cached private
copy of the existing pressed StyleBox supplies active hover without changing
normal or pressed styles, dimensions, assignments or shortcuts.
Tooltips give machine identity, exact quantity and physical shortcut.

`Main/PlaythroughState` owns ten type references, per-slot customization flags
and per-type default-considered flags. First packaged possession (successful rack
recovery in current progression) considers Extractor/Smelter/Fabricator for
slots 1/2/3 exactly once. Occupied/customized slots and existing assignments of
that type prevent automatic insertion; there is no fallback or later restoration.
Manual replacement and deliberate clearing protect the chosen slot. Depletion,
placement/recovery and world transitions retain assignments; a fresh Main resets
them. Disk persistence and inventory transactions are unchanged.

Right-click a deployable inventory position, including a future overflow row,
for **Assign to Hotbar** and ten destinations showing their current contents.
Slot 10 displays shortcut 0. Left-click still requests immediate deployment.
Right-click an assigned hotbar slot for **Clear Assignment**, even at zero stock.
Assignment changes never consume inventory. Built-in PopupMenus use B1 styling
and own menu input; Tab also closes inventory from its menu. Travel dismisses menus.

Unmodified physical number keys (held-key repeats ignored), or left-clicking a
hotbar slot, call `ConstructionController.activate_hotbar`. The same type cancels;
a different available type uses `begin_deployment`, whose checks precede
cancellation. A rejected switch leaves the current tool intact and displays a
brief reason. Inventory, inspection, conversations/responses, transitions and
recovery block activation. Empty shortcuts do nothing. Existing preview/commit
validation, R rotation, successful-placement exit and Fabricator inspection remain.
Only successful placement consumes equipment. World right-click cancellation now
runs in `_unhandled_input`, allowing GUI context clicks to be consumed first;
Esc retains its existing input priority.

Interaction prompts move to offsets -128/-96, construction hints to -144/-92,
and musings up 64 units to -296/-160. Narrative content and completion/dismissal
semantics remain unchanged. The bar stays visible with inventory, inspection and
ambient musings; conversation/response panels and transitions temporarily hide it.

Previously owner-approved preservation assertions in
`tests/static_v2_production_host_test.py` pin the two inventory normalized hashes
and the extracted presentation helper.
Fourteen exact literal edits across six files are reversed before the unchanged
historical comparisons: session state, construction script/scene, Main and
interaction/musing scenes. Three added checks cover the shared helper hash,
restoration of entire pre-feature files at immutable
`92947fac8b9a7866c740ae5ee11b5cfd0b549ea4`, and rejection of modified/duplicated
allowances while unrelated changes remain detectable. The connection suite reuses
the same normalizer. No runner, execution policy or native test is changed.

The visual refinement requires **no preservation-test edits**. Its hotbar
script/scene were introduced after the immutable P8 historical baseline and are
not in its frozen-file inventory. Inventory/helper hashes, all fourteen exact
normalizations, historical comparisons and negative checks remain unchanged.
The existing static resource graph still follows and checks the refined scene.

Validation: the original implementation at `f7da479` passed all 46 static
checks, cold headless import and the allowlisted recipe-switching regression.
After owner approval, the refined working resources passed the same restricted
Native runner in one attempt: 46 static checks, cold import, recipe regression
(zero failures), infrastructure and authorization all PASS. The retained stage
is `tlwh-native-plan-44a633bb166e41e999277cbaafe23122`. No retry or graphical
execution occurred. Changed Markdown links and `git diff --check` PASS.
Text inspection confirms unchanged behavior methods, key mapping, assignment
state, construction and inventory files. Native success covers import and the
existing recipe regression; it does not establish hotbar interaction correctness
or visual acceptance. The owner approved the compact/backing-panel direction;
final in-game layout and interaction acceptance remain separate. The feature
is pending merge.

Owner acceptance, after the owner chooses to launch graphically:

1. Recover all three machines: defaults appear in 1/2/3 and all ten slots remain
   visible. Place/recover and travel through every environment; types persist at
   zero quantity while quantities follow inventory.
2. Replace destinations from inventory, including slot 10 / key 0; verify Current
   labels. Clear a zero-stock assignment and acquire/recover that type again: it
   must stay cleared. Customize a future default position before its machine
   arrives: the default must not overwrite it.
3. Verify key/click deployment, held-key suppression, same-type cancellation,
   immediate switching, rejected zero-stock switching, R, Esc and world
   right-click. Cancel/switch must not consume equipment; successful placement
   consumes exactly one and exits construction.
4. Right-click hotbar during placement: the clear menu must open without
   cancelling/confirming the ghost. Dismiss menus with Esc/outside clicks and
   close inventory with Tab; no click may reach placement or world interaction.
5. Verify numbers cannot deploy through inventory, inspection, conversations,
   responses, recovery or travel. Check bar, prompts, instructions, musings and
   feedback at 1280 x 720 and 1024 x 576; preserve narrative dismissal semantics.

## V2 production integration (P1-P6 merged, P7 approved, P8 pending merge)

P1-P6 merged in PRs #59-#64; the verified post-P6 baseline is
`e14703e64aef961f18feba8a616acec00c4f069e`. The owner approved P7 after a
continuous six-phase rehearsal, **6/6 PASS (owner-reported)**. P8 is implemented
on `codex/p8-f5-production-cutover`, pending owner cutover acceptance and merge.

**F5 / Run Project** now starts V2 Primary through `scenes/main/main_v2.tscn`.
**F6 / Run Current Scene** with that scene open also starts V2. For the explicit
**legacy F6 fallback**, stop the game, open `scenes/main/main.tscn` and press F6.
F5 stays configured for V2. This is an editor workflow, with no startup selector.
Computer repair remains deferred. Agent validation is static only; no Godot
launch or P8 runtime acceptance is claimed.

The inherited host connects production V2 rooms at 1.25x, reuses existing
player/controllers/UI and exterior, and configures exterior return to V2 Primary.
Legacy Main keeps its original exterior return. Computer and machine interaction
caps remain 45 world units. P4/P5/P6 enable Extractor/Smelter/Fabricator recovery
after discovery/ore acquisition/ingot acquisition, respectively. Acquisition
musings and direct **Craft a Ferrite Plate.** guidance remain unchanged.

**P7 Observation #1 remains nonblocking and unfixed:** after the Computer's opening
conversation, the player is not directed outside to investigate Ferrite. A later
approved narrative/objective-guidance correction is excluded from P8. See
[current status, observation and eight pending owner cutover tests](docs/V2_PRODUCTION_HOST.md#p8-production-cutover-feature-branch-pending-merge).

## Primary interior V2 development previews

**Retirement proposed in this PR (pending merge):** all 38 tracked `scenes/dev/`
files are removed after PR #66 migrated the static tests. The two preview
sections below are historical records; their controls and owner test plans apply
only to restored historical previews. They are not current launch instructions.
The four linked preview guides retain geometry, art provenance, design decisions
and owner findings. Their retired-source links point to the exact pre-retirement
commit, not missing checkout files.

Current **F5** runs production `scenes/main/main_v2.tscn`; **F6** with
`scenes/main/main.tscn` open runs the legacy fallback. Developer coordinates
(`scenes/ui/developer_coordinates.*`) remain an approved feature.

Tracked preview source is preserved at **`c6d236e5ad47d11e285287f93d69d87f8a5213dc`**
(the PR #66 merge). Inspect or restore from the repository root, after preserving
any local changes; restoration belongs on a separate feature branch:

```sh
git ls-tree -r --name-only c6d236e5ad47d11e285287f93d69d87f8a5213dc -- scenes/dev/
git show c6d236e5ad47d11e285287f93d69d87f8a5213dc:scenes/dev/v2_two_room_connection.tscn
git restore --source=c6d236e5ad47d11e285287f93d69d87f8a5213dc --worktree -- scenes/dev/
```

This restores exactly the 38 historical tracked files, without launching Godot.
It does not authorize engine execution or change the current production entry point.

An isolated development preview compares the approved room artwork at world
scales 1.0x, 1.25x and 1.5x using existing Dave and camera. These previews remain
isolated from production gameplay. The owner selected 1.25x following PR #47
review; PR #49's
separate collision/navigation preview is merged. PR #50 merged the isolated
automatic-transition preview; owner acceptance is separate. See the
[preview controls, provenance and ordered owner tests](docs/INTERIOR_V2_PREVIEW.md).
The [automatic-transition harness and eight owner tests](docs/INTERIOR_V2_TRANSITIONS.md)
cover development-only destinations and the separate 0.15-second quick fade.
Agent validation is static only under the Godot execution restriction.

PR #54 merged the separate [two-room V2 connection](docs/V2_TWO_ROOM_CONNECTION.md);
owner acceptance is separate. The historical F6 harness was `scenes/dev/v2_two_room_connection.tscn`
to start near Primary's left entrance and travel automatically to the actual
Maintenance Bay V2 and back. Both rooms are 1.25x; one is attached at a time,
with the existing detached-room cache retained. That historical slice preserved
F5 routes; P8 now selects the V2 host. See the guide's nine sequential owner tests.

## Maintenance bay V2 development previews

This feature branch adds an isolated stationary Smelter visual, pending merge
and final locked-file owner retests. The owner reports 9/9 initial tests PASS
and approved X=435.00, Y=-159.00, width=20.0, opacity=1.00; outline starts OFF.
Historical F6 scene: `scenes/dev/maintenance_bay_v2_smelter_preview.tscn`; O/V simulate objective
outline/removal, C/H toggle collision outlines/HUD, and movement/camera remain.
Temporary live-tuning controls and recording HUD are removed. See
[source, locked placement, controls and owner retests](docs/MAINTENANCE_BAY_V2_PREVIEW.md#stationary-smelter-visual-feature-branch-pending-merge).
Agent validation is static only; production and existing previews remain unchanged.

The feature branch adds an isolated stationary Extractor visual, pending merge
and owner acceptance. Historical F6 scene: `scenes/dev/maintenance_bay_v2_extractor_preview.tscn`;
O toggles its muted amber silhouette outline (default OFF), V simulates visual
removal/reappearance, and C/H retain collision-outline/HUD controls. See the
[placement and acceptance plan](docs/MAINTENANCE_BAY_V2_PREVIEW.md#stationary-extractor-visual-feature-branch-pending-merge).
Validation is static only; no recovery, objectives or production logic is added.

PR #51 added a separate machine-free maintenance-bay visual preview. Its historical
F6 scene was `scenes/dev/maintenance_bay_v2_scale_preview.tscn`: initial room
scale is 1.25x; 1/2/3 select 1.0x/1.25x/1.5x, 4-9 select comparison positions,
WASD/arrows move, wheel zooms and H toggles the HUD. Walking through artwork is
expected. Existing Dave/camera and all production environments/routes are unchanged.
See [art provenance, scope and sequential owner tests](docs/MAINTENANCE_BAY_V2_PREVIEW.md).
The owner selected **1.25x** for collision work. This feature branch adds static
room collision and a separate isolated playable preview, pending merge and owner
acceptance. The historical launch used `scenes/dev/maintenance_bay_v2_collision_preview.tscn` and
F6. WASD/arrows move, wheel zooms, C toggles actual collision outlines (initially
off), and H toggles the HUD. The right exit has a preview-only barrier; the upper
door remains solid. Stop and F6 the scale preview to return to visual comparison.
Agent validation is static only; engine loading and owner navigation remain unverified.

## Layout and development

- `project.godot`: engine settings and main-scene entry point.
- `scenes/main/main.tscn`: persistent playthrough root owning Dave, objectives,
  tracker, inventory UI, progression (including inventory state) and transitions;
  starts with the ship interior.
- `scenes/world/ship_interior.tscn`: preserved deck, perimeter and fixtures,
  plus departure and maintenance doorways with named return spawns.
- `scenes/world/maintenance_bay.tscn`: separate compact equipment room with
  three starter racks and a return doorway; provisional geometry only.
- `inventory/`: shared item definitions and quantities; Materials/Equipment
  are presentation metadata within one storage model.
- `scenes/ui/inventory_ui.tscn`: persistent, nonmodal Materials/Equipment panel.
- `scenes/world/planet_exterior.tscn`: editable crash-site overlay polygons, solid
  ship/hatch, rocks, Y-sorted objects and named exterior spawn. Its script manages
  disposable procedural terrain chunks; the temporary perimeter is removed.
- `scenes/player/dave.tscn`: reusable `CharacterBody2D`, a collision shape, a
  `Camera2D` child, and a separate `Visual` child containing one legacy pixel-art
  `Sprite2D` and the retained `AnimationPlayer` (PR #25, merged).
- `scenes/player/dave.gd`: movement through `_physics_process()` and
  `move_and_slide()`, with four-direction walk/idle presentation selection and
  presentation-only last-facing retention (PR #25, merged).
- `scenes/player/follow_camera.gd`: wheel input and bounded zoom transitions using
  a built-in Tween; following uses the child camera's built-in behavior.
- `scenes/player/interaction_detector.gd`: Dave's proximity selection, solid-body
  visibility check and interaction requests; attached to an `Area2D` child.
- `scenes/interaction/world_interactable.gd`: small `CollisionObject2D` interface
  for solid bodies and nonblocking areas, owning availability, prompt, optional
  conversation and fallback inspection text.
- `scenes/ui/interaction_ui.tscn` and `interaction_ui.gd`: screen-space prompt and
  dismissible response, instantiated under Dave as a `CanvasLayer`.
- `dialogue/`: Inspector-editable `DialogueConversation` and `DialogueEntry`
  Resources, with temporary opening content in `computer_opening.tres`.
- `scenes/ui/dialogue_ui.tscn` and `dialogue_ui.gd`: reusable screen-space
  dialogue presentation and active entry position, instantiated under Dave.
- `objectives/`: editable objective definitions, playthrough-local state controller,
  and provisional opening content in `restore_computer.tres`.
- `scenes/ui/objective_tracker.tscn` and `objective_tracker.gd`: screen-space
  objective data presentation with expand, pin, hide and restore controls.
- `scenes/main/main.gd`: playthrough-local dialogue completion, objective activation
  and tracker wiring.
- `docs/GAME_VISION.md`: approved direction and unresolved design questions.
- `AGENTS.md`: development conventions.

Use **WASD** or the **arrow keys** to move. The Input Map actions are `move_left`,
`move_right`, `move_up`, and `move_down`; WASD uses physical key positions.
`Input.get_vector()` limits direction length to one, keeping diagonal keyboard
movement at the same 240 pixels per second as cardinal movement. Dave's local
origin is his ground-contact position; artwork stays under `Visual`, aligned to
that origin without changing the controller or camera.

The following four Dave sections preserve historical artwork and calibration
records. The legacy migration section supersedes their active presentation and
playtest instructions (PR #25, merged).
All newer artwork remains preserved as inactive assets.

### Dave static sprite baseline (PR #21, merged)

The merged static replacement uses the approved
`assets/characters/dave/dave_static_approved_v2.png`: a 1184 × 1328, 8-bit RGBA
PNG copied byte-for-byte from the owner's local `dave v2.png`. The original
`dave_idle_angled_overhead_pilot.png` and its import metadata remain available
for comparison and rollback. Its prior transform was scale `(0.065, 0.065)`
and offset `(-324.5, -1431)`, with `centered = false`. Historical owner testing
at the earlier 0.045 scale passed nine of ten checks but found Dave too small;
the subsequent 0.065 refinement had no recorded gameplay verification. Those
results do not validate this replacement. The source PNGs are not edited or recompressed.
The new `.png.import` sidecar follows the existing lossless texture settings,
with a distinct UID, disabled mipmaps and no size limit. It was prepared as text;
Godot has not imported it. Generated `.godot/` data stays ignored.

Provisional tuning is local to `Visual/Sprite2D`: uniform
`scale = (0.0744, 0.0744)`, default position `(0, 0)`, `centered = false`, and
texture-pixel `offset = (-588.5, -1287)`. Linear texture filtering is retained.
At alpha >= 32, exclusive bounds are `(289, 58)`–`(888, 1287)` for the new art
and `(24, 24)`–`(624, 1431)` for the previous art. Matching visible height gives
`(1431 - 24) * 0.065 / (1287 - 58) = 0.074414…`, rounded to 0.0744.
The new visible extent is approximately 44.57 × 91.44 world units, versus
39.00 × 91.46 previously: essentially the same height, with a roughly 14% wider
silhouette. The offset centers the substantial horizontal bounds and maps the
lower boot edge to y = 0. Faint alpha extends beyond those bounds, including
below the boot; the canvas bottom is not the ground anchor. The full new canvas
spans about 88.09 × 98.80 world units. Preserve the source-pixel offset when
adjusting uniform scale to retain this anchor.

Dave's root and `Visual` origins, radius-10 collision circle at `(0, -10)`,
Y-sorting and Z settings are unchanged. Camera, movement, input, interaction,
dialogue, objectives, Computer artwork and project settings are unchanged.
There is no animation, shader or new gameplay behavior in this replacement.

Validation is static only: PNG decoding and transparency, source/copy SHA-256
identity, resource paths and import metadata, transform calculations, unchanged
nonvisual scene data and gameplay files, Markdown links and Git diff checks.
Neither graphical nor headless Godot execution was performed. Engine import,
rendering and gameplay behavior remain unverified for this replacement.

The owner must manually assess normal-zoom readability, proportions beside damaged
Computer and other objects, dark-background readability, boot contact, collision
and Y-sorting. Repeat visual checks at 0.75× and 1.5× zoom, check camera follow
and movement, then interactions, dialogue and objective progression. Inspect
transparency fringes, the source's faint halo, clipping and scaling artifacts.
Scale and alignment remain provisional until this playtest.

### Dave south-facing walk baseline (PR #22, merged)

PR #22 added south-facing walking presentation. The owner reports it was
validated and merged; the static-only results below record the original agent
validation. The north extension preserves its artwork, transforms and animation.
The original approved `assets/characters/dave/dave_walking.png` is preserved
byte-for-byte: 1983 x 793 RGBA, SHA-256
`02c9d474a90e7a6bd1f88bb2a954e88afb3df50c408f88dc1476596dcbf1a7a7`.
After inspection, the owner authorized removing only stray margin pixels in
derived frames. The derived `dave_walk_south_atlas.png` is 1920 x 784 RGBA,
containing four 480 x 784 cells in the original left-to-right order: left-foot
contact, opposite knee passing, right-foot contact, other knee passing.

Preparation uses integer translations only, with no resampling, repainting or
pose changes. Starting with source cells at x `[0,500)`, `[500,989)`,
`[989,1478)`, `[1478,1983)`, retain all pixels inside each alpha >= 32 bounding
box and all nonzero-alpha pixels 8-connected to the main silhouette. Remove
only detached pixels outside that box: 160, 46, 68 and 40 pixels respectively
(314 total, all alpha 1/255). Connected faint outlines remain. Crop transparent
margins and translate each retained image onto a transparent cell using these
source anchors; all bounds and baselines below are exclusive pixel edges.

| Frame | Retained source bounds (x0, y0, x1, y1) | Source anchor (x, y) | Cell anchor |
| --- | --- | --- | --- |
| 1 | (33, 20, 471, 779) | (254, 770) | (240, 770) |
| 2 | (528, 17, 967, 763) | (745, 755) | (240, 770) |
| 3 | (1013, 15, 1453, 779) | (1233, 770) | (240, 770) |
| 4 | (1500, 15, 1941, 764) | (1724, 755) | (240, 770) |

Horizontal anchors use rounded substantial silhouette centers; vertical anchors
use the substantial lower boot edge. This aligns ground contact, preserving the
poses' small torso bob (about 1.8 world units). `Visual/WalkSouthSprite` uses
`hframes = 4`, `centered = false`, offset `(-240, -770)` and uniform scale
`(0.1224, 0.1224)`. Contact poses are approximately 91.2-91.4 world units tall,
matching the static baseline's 91.44; the walking silhouette is wider, about
52.5 units versus 44.57. Both sprites retain linear filtering. Original artwork,
static sprite properties, body/Visual origins, collision and Y-sorting remain
unchanged. Both new PNG import sidecars use distinct UIDs and existing lossless,
no-mipmap, unlimited-size settings; they were written as text without engine import.

`Visual/AnimationPlayer` owns an editor-editable embedded AnimationLibrary in
`scenes/player/dave.tscn`. Its looping `walk_south` animation lasts 0.5 seconds:
discrete `WalkSouthSprite:frame` keys 0, 1, 2, 3 at 0, 0.125, 0.25, 0.375 seconds
give 8 FPS at the default playback speed of 1.0. `RESET` restores frame 0 for
editor preview. No animation track modifies transforms, collision or world position.

The controller checks the existing input vector after the unchanged movement
code: positive y and approximately zero x means straight south. Diagonals use
the static sprite. Entry starts the animation and applies its first frame
immediately; sustained south input does not restart it. Idle or another direction
stops playback, hides the walk sprite and shows the original static sprite with
its approved scale/offset. The trigger follows input, so pushing south against a
wall still animates. There are no other directional animations, speed modifiers,
sprinting, input-map changes or changes to camera, interactions, dialogue or objectives.

Validation is static only: decoded PNG dimensions/transparency and pixel identity
under the documented translations, original SHA-256, scene/resource references,
animation frame sequence/timing/loop configuration, explicit fallback, unchanged
existing scene nodes and movement statements, protected gameplay/settings files,
Markdown links and Git diff checks. Godot was not run graphically or headlessly;
engine import, playback, appearance and gameplay remain unverified.

Owner manual playtest: run the main scene and move straight south using S and
Down. Confirm all four poses in order at 8 FPS, including repeated stop/start;
assess gait, torso bob, foot sliding, halos and transitions at normal zoom and
0.75/1.5 zoom. Release movement and switch to every other direction, including
south diagonals: each must immediately restore the static sprite. Check collision,
Y-sorting, ground contact, camera follow/zoom, Computer interaction, dialogue and
objectives. Confirm Shift never changes speed. Foot sliding and the wider walking
silhouette require owner visual evaluation; no runtime result is claimed.

### Dave north-facing walk baseline (PR #23, merged)

PR #23 extended the baseline above with straight-north input. The owner reports
it was manually validated and merged; the checks below record agent static
validation of that baseline. Its historical idle behavior is superseded by the
directional idle feature below when merged.
The owner-approved `assets/characters/dave/dave_walk_north.png` is preserved
byte-for-byte: 1983 x 793, 8-bit RGBA, SHA-256
`17d8b3d999450e820ce368a905fbcdd548de62d7894197077430a75bf0aee39c`.
The derived `dave_walk_north_atlas.png` is 2176 x 832 RGBA: four uniform
544 x 832 cells in the original left-to-right order. No pixels are removed,
repainted or resampled; each complete source cell is translated by integer
pixels onto a transparent cell. Source and atlas import sidecars match the
baseline's lossless, no-mipmap, unlimited-size settings with distinct UIDs;
they are prepared as text without running an engine import.

| Frame | Source cell x range | Source anchor (x, y) | Atlas cell anchor |
| --- | --- | --- | --- |
| 1 | [0, 496) | (240, 769) | (272, 784) |
| 2 | [496, 992) | (744, 753) | (272, 784) |
| 3 | [992, 1488) | (1236, 769) | (272, 784) |
| 4 | [1488, 1983) | (1734, 753) | (272, 784) |

Anchors use rounded alpha >= 32 horizontal silhouette centers and exclusive
lower boot edges. `Visual/WalkNorthSprite` uses `centered = false`, `hframes = 4`,
offset `(-272, -784)` and the south sprite's uniform scale `(0.1224, 0.1224)`
and linear filtering. Substantial boot edges map to local y = 0 in every frame;
contact poses are about 91.07 world units tall, close to the existing baseline.
Larger cells preserve all faint margins without clipping or crossing cells.
Inspection found 846 detached nonzero-alpha pixels in total, all alpha <= 7/255;
these and the connected alpha fringe remain unchanged. Halos still need owner
visual assessment. There is no substantial cleanup or reconstruction.

The existing `Visual/AnimationPlayer` gains only `walk_north`: a 0.5-second loop
with discrete `WalkNorthSprite:frame` keys 0, 1, 2, 3 at 0, 0.125, 0.25 and
0.375 seconds (8 FPS at default playback speed 1.0). `walk_south` and `RESET`
remain unchanged. No animation modifies transforms or gameplay.

The presentation helper now selects north for negative y and south for positive
y, each with approximately zero x in the existing input vector. It starts on
entry or direction change and applies frame 0 immediately; sustained input does
not restart playback. Exactly one sprite is shown. Idle, east, west and all
diagonals stop playback and restore the approved static sprite. Directional idle
poses and other directional animations remain deferred. As before, input against
a wall still animates. Movement remains 240 pixels per second without sprinting;
input, collision, Y-sorting, camera, interaction, dialogue and objectives are unchanged.

Validation is static only: source SHA-256, complete source-cell pixel identity
under the documented translations, atlas dimensions and alignment, scene/resource
references and unique import UIDs, animation configuration, direction selection
and fallback review, unchanged south animation and existing scene nodes,
protected gameplay/settings files, Markdown links and Git diff checks. Godot
was not executed graphically or headlessly; import, playback, rendering and
gameplay verification remain for the owner.

Owner manual playtest: use W/Up for north and S/Down for south; check four frames
in order and continuous 8 FPS loops, repeated stop/start and north/south switching.
Confirm idle, east, west and diagonals restore static art. Inspect transparency,
clipping, halos, ground contact and foot sliding at normal zoom and both zoom
bounds. Verify collision, Y-sorting, camera follow/zoom, Computer interactions,
dialogue and objectives. Confirm Shift never changes speed. The south animation
must retain its previously approved appearance.

### Dave directional idle (feature branch, pending merge)

`codex/dave-directional-idle` adds static `Visual/IdleSouthSprite` and
`Visual/IdleNorthSprite` nodes using the exact owner-approved PNGs. No derived
images, pixel edits, resampling or new animations are needed. Original PNGs are
preserved byte-for-byte, including faint alpha fringes and margin pixels.

| Source PNG under `assets/characters/dave/` | Dimensions (RGBA) | SHA-256 |
| --- | --- | --- |
| `dave_idle_south.png` | 1279 x 1230 | `07f8353a3c225c4b547df055cd7e1d1620cdce9f5529eb4b24f399c3a733b99d` |
| `dave_idle_north.png` | 1145 x 1374 | `df2c97edcd7fcc38929b025ffb3a7c753647b086978df8c3db7b23112fc69e53` |

Both sprites use linear filtering and `centered = false`. Exclusive alpha >= 32
bounds are `(285, 106, 986, 1195)` south and `(188, 95, 952, 1301)` north.
Owner testing found the initial height-matched idle poses visibly larger than
walking. The first uniform reduction (south `0.075`, north `0.065`) resolved the
width mismatch according to the owner, but made idle noticeably shorter. This
second calibration preserves those approved X scales and independently restores
height using the owner's proposed Y scales. It remains pending owner playtesting.

| Direction | Previous X/Y scale | Revised X/Y scale | Width x height before / after (world units) | Walking contact-frame height |
| --- | --- | --- | --- | --- |
| South | (0.075, 0.075) | (0.075, 0.0835) | 52.58 x 81.68 / 52.58 x 90.93 | 91.19 / 91.43 |
| North | (0.065, 0.065) | (0.065, 0.0754) | 49.66 x 78.39 / 49.66 x 90.93 | 91.07 / 91.07 |

All extents use alpha >= 32 exclusive bounds. Walking contact frames are indices
0 and 2; their existing uniform scale is `0.1224`. South idle is 0.26-0.50 world
units shorter than those contacts; north is 0.13 shorter. Walking widths remain
52.14-52.51 south and 48.47-48.72 north across the four frames. Idle widths are
unchanged from the owner-approved width correction.

Verified source-pixel offsets remain `(-635.5, -1195)` south and `(-570, -1301)`
north: negative substantial horizontal midpoint and negative lower boot edge.
Componentwise scale times `(source point + offset)` maps both anchors to local
zero, including with separate X/Y scales. Root, collision and Visual origins
remain unchanged. All approved PNG pixels and faint alpha margins remain intact.

Nonuniform scaling increases vertical dimensions relative to the accepted uniform
revision by 11.33% south and 16.00% north, with horizontal dimensions unchanged.
Source inspection and transform calculations identify a real proportion tradeoff:
heads, torsos, limbs and boots become taller relative to their width; round armor
details can appear vertically oval. These transforms do not selectively correct
anatomy. No artwork edits or transformed preview images were made. Static checks
cannot establish whether the distortion is objectionable; owner comparison of
head, shoulders, torso, limbs and boot shapes during walk-to-idle transitions is
required. No graphical result or runtime acceptance is claimed.
The two import sidecars follow existing lossless, no-mipmap, unlimited-size
settings with distinct UIDs; they were prepared as text without engine import.

`last_facing` is presentation-only, initially `SOUTH`; the scene itself also
shows only south idle on spawn. Straight north/south input updates that value and
selects the existing walk animation. Sustained walking does not restart playback;
direction changes apply the first frame immediately. Zero input stops playback
and displays the remembered static idle. East/west and diagonal movement stop
playback and display the existing static fallback, leaving `last_facing`
unchanged. Stopping unsupported movement therefore returns to the last supported
north/south idle, or south if neither has occurred. Exactly one of the five
sprites is selected per state. `AnimationPlayer` remains the sole animation
controller; both walk animations, their 8 FPS timing and frame order are unchanged.
The input vector, 240 movement speed, `move_and_slide()`, collision, Y-sorting,
camera, interactions, dialogue, objectives and project settings are unchanged.

Validation is static only: PNG decode/integrity and SHA-256 preservation,
alpha/anchor calculations, scene and import references, animation and protected
scene-block comparison, presentation branch review, movement-statement identity,
Markdown links and Git diff checks. For this calibration, neither Godot nor
project code was executed.
Engine import, rendering, transition appearance and gameplay remain unverified;
faint fringes, revised proportions and ground alignment need owner assessment.

Owner manual playtest: confirm initial south idle, north/south walk-to-idle and
idle-to-walk transitions, repeated release and direct north/south switching.
Check all east/west and diagonal movement uses the original fallback and stopping
it retains the last north/south facing (including before any supported walk).
Confirm unchanged walk frame order and 8 FPS playback. Inspect size, boot contact,
clipping, transparency tearing and halos at normal zoom and 0.75/1.5 zoom. Check
collision, Y-sorting, camera follow/zoom, Computer interaction, dialogue and
objectives. Confirm Shift does not change speed and no new movement mechanics exist.

### Dave legacy directional animation migration (PR #25, merged)

The owner approved consistent helmeted pixel-art Dave, a scoped exception to the
illustrated visual direction. Only two PNGs are reused; no legacy controller or
gameplay systems are imported. The east/west artwork-generation effort is
abandoned. Existing newer Dave PNGs and import sidecars remain unchanged and
inactive. Source: `D:/GameDev/Godot/Projects/FactoryGame/Assets/Character/`.
Destination: `assets/characters/dave/`. Source and copy SHA-256 values match:

| Asset | SHA-256 |
| --- | --- |
| `character_walk.png` | `425b952b6168fd6e3d6291d71d5b3f16e3c54911074e18f1963de65a4b8b5ccf` |
| `character_idle.png` | `8cd4187072d894391d03165b798c3d6d90368624eb0256a0d11e1e0af369f21e` |

Both sheets are 384 x 192: eight columns and four rows of 48 x 48 cells.
Rows are south, north, west, east. One `Visual/Sprite2D` uses `hframes = 8`,
`vframes = 4` and nearest filtering. The existing `Visual/AnimationPlayer`
contains eight looping clips: `walk_{south,north,west,east}` uses eight frames
at 16 FPS (0.0625-second keys, 0.5-second cycle); corresponding `idle_*` clips
use eight frames at 1 / 0.18 = 5.555556 FPS (1.44-second cycle). Discrete tracks
select texture, frame and visual offset; `RESET` restores south idle frame 0.
Source frame order and pixels are unchanged. Import sidecars were authored as
text with lossless compression, no mipmaps and no size limit; Godot has not
imported them. Mining artwork, legacy SpriteFrames and scripts are excluded.

Every frame's nonzero-alpha bounds were measured. Exclusive horizontal bounds
are `[13,35)` south, `[12,35)` north, `[14,33)` west and `[15,34)` east;
visible heights range from 32 to 34 pixels. One uniform scale of
`91 / 34 = 2.676470588` makes the tallest poses 91 world units and the shortest
85.647 units. This measured result replaces the initial 2.8-3.0 estimate.

The sprite is uncentered. Source-pixel offsets use negative alpha midpoint X
and negative exclusive lower boot edge Y. X offsets for south/north/west/east
are `-24`, `-23.5`, `-23.5`, `-24.5`. Idle Y is always `-42`.
North/south walking Y follows `[-44,-43,-42,-43,-44,-43,-42,-43]`;
west/east walking Y is always `-43`. Discrete offset keys accompany each frame,
so `scale * (boot_edge + offset.y) = 0` and each silhouette stays horizontally
centered. This compensates small source baseline differences without editing
pixels. All occupied pixels fit inside their original cells. Root and Visual
origins, collision radius 10 at `(0,-10)` and interaction radius 120 at
`(0,-10)` are unchanged. No direction uses a different or nonuniform scale.

Facing follows the existing input's dominant axis, choosing horizontal on exact
ties. Moving selects walking and updates facing; stopping retains facing and
selects animated idle. The scene and `_ready()` initialize south idle. Animation
changes apply their first keys immediately; sustained input does not restart a
clip. Input against a wall still animates. Movement remains immediate at 240
units/second with unchanged `Input.get_vector()` and `move_and_slide()` code.
Camera/zoom, Y-sorting, UI paths, Computer interaction, dialogue and objective
wiring are unchanged. There are no new inputs, sprinting, acceleration or stamina.

Validation is static only: byte identity, dimensions, alpha bounds, frame/texture/
offset tracks, loop durations, resource paths, preserved movement and nonvisual
scene blocks, protected files, Markdown links and Git diff checks. Neither Godot
nor project code was executed. Engine import, playback and gameplay remain
unverified.

Owner manual playtest: verify initial south idle; eight frames in all four walk
clips at 16 FPS; four slower idle loops; last-facing retention; dominant-axis
diagonals and horizontal ties; repeated stop/start and direction changes without
flickering or missing frames. Inspect size, proportions, boot contact, sliding,
clipping and nearest-filter appearance at normal zoom and both zoom bounds.
Verify collision, Y-sorting, camera follow/zoom, Computer interaction, dialogue
completion and objective activation/tracker behavior. Check WASD and arrows,
and confirm Shift does not change speed. Pixel-art integration, pose-height
variation and per-frame anchor compensation require owner visual assessment.

### Existing environment and gameplay

The camera follows Dave's ground-contact origin independently of `Visual`.
**Mouse wheel up** zooms in; **mouse wheel down** zooms out, centered on Dave.
Zoom starts at 1.0, changes its target by 0.1 per wheel press, and is clamped to
0.75â€“1.5. These are provisional tuning values in `follow_camera.gd`. Each changed
target starts a 0.15-second eased Tween from the current zoom; rapid scrolling
retargets the transition, and repeated input at a bound leaves it running to
completion. No per-frame zoom callback runs when a transition is idle.

The test floor spans x = -2048 to 2048 and y = -1536 to 1536 (4096 Ã— 3072).
Dave spawns at (0, 0), clear of all collision footprints. Four 32-pixel-thick
`StaticBody2D` walls sit just outside the floor; their rectangular shapes meet at
the corners. Three obstacles sit at (-320, -180), (360, 40), and (0, 420), with
160 Ã— 48, 96 Ã— 64, and 160 Ã— 48 collision footprints respectively. All bodies use
the default collision layer/mask, matching Dave. Shapes and colored polygon
visuals are separate children; the console also has a small interaction script.
The Computer HD art pilot below replaces only the console's polygon visuals.

`GroundObjects` enables built-in Y-sorting for Dave and the obstacle roots at the
same default Z index. Each obstacle root is anchored at the bottom center of its
ground footprint, matching Dave's ground-contact origin. Its collision rectangle
extends upward from that anchor, while its taller visual extends above the
footprint to allow overlap when Dave stands behind it. Visual children stay
together as one sorted object. The floor and perimeter are outside this group.
There are no camera limits; floor edges can still become visible near the walls.
Existing movement, camera/zoom, display, rendering, and physics settings are
preserved.

The original ship visual pass used built-in `Polygon2D` and `Line2D` details.
`ShipDeck` covers x = -656 to 656 and y = -448 to 592, leaving the rest of the test
floor open. Sixteen inset panels, muted amber route guides and service markings
frame a clear central walking area. This is a deck section, not a new enclosed
room; the original distant perimeter remains the only boundary collision.
Blue-teal housings, pale metal edges and restrained amber/coral accents form a
temporary palette, not production artwork or a lighting system.

The existing `WestObstacle` depicts Computer, now using the HD pilot described
below instead of its temporary polygon console. `EastObstacle`
depicts a life-support filter unit with a faceted cap, filter window and service
pipe. `SouthObstacle` depicts a storage workbench with cabinet doors, a work mat,
loose cover and tool tray. The console supports temporary dialogue with
inspection fallback; the other fixtures remain noninteractive
placeholders.
These visual identities establish no new narrative state or objectives.
All fixture details remain under each existing `Visual` child, with no individual
Z overrides or nested Y-sorting. Computer's HD visual exceeds its original visual
bounds; the other fixtures retain theirs. The three body
positions, bottom-center anchors and collision shapes are unchanged. Flat deck
details are outside `GroundObjects`, drawn before it at the default Z index.

Validation for this feature is static only: scene/resource references, rectangle
placement, spawn clearance, Y-sorting hierarchy, unchanged scripts/settings,
documentation links, and Git diff checks. Godot has not been executed; engine
loading, collision response, and graphical layering remain unverified. Before
merging, the owner should manually check all four walls and corners, walk around
each obstacle from every direction, slide along its edges, and confirm Dave
appears behind its upper visual and in front below its anchor. Also verify camera
follow and mouse-wheel zoom throughout the area, including both zoom bounds.
For the ship visual pass, also assess the palette, fixture recognition, floor
marking readability and clear walking routes at the starting view and both zoom
bounds. Check that all fixture details occlude together as Dave walks behind and
in front, and that their visible bases agree with collision contact. No engine,
runtime or graphical verification was performed for this pass.

The interaction requires Dave's collision center to be **at most 120
world units from the interaction point**, measured as straight-line distance.
The detector's circle radius in `dave.tscn` supplies this single distance limit.
A direct physics shape query at Dave's current position finds candidate bodies;
the explicit point-distance check then rejects candidates beyond the limit.
Cached `Area2D` overlap monitoring is disabled. It selects the nearest available
point whose physics ray first hits that target's solid body, excluding Dave.
The console's point is the center of its existing 160 Ã— 48 footprint: its sides
and corners are reachable within the limit without changing collision geometry.
A solid obstacle between Dave and the target blocks the prompt and interaction.
All proximity, distance and obstruction checks run in the physics callback,
including before fulfilling an interaction request.

When available, a screen-space **E â€” Talk to Computer** prompt appears. Physical
**E** uses the existing `interact` action. The detector routes a valid conversation
to DialogueUI; an absent or invalid conversation falls back to inspection text.
An interactable is available when enabled and either content source is valid.
Inspection still closes with E, Esc or its Close button. Only one panel opens at
a time; new interactions and contextual prompts are suppressed during dialogue.

A fresh E press or **Next** advances entries in order. On the last entry,
**Finish** or E completes the conversation; **Dismiss** or Esc closes it without
completion. DialogueUI emits distinct completion and dismissal signals, clears
its active position on close and starts at the first entry on reinteraction.
No persistent state is recorded. Key echoes are ignored, and opening is deferred
to the physics callback so the opening key event cannot advance the first entry.
Leaving range does not close either panel. Movement and wheel zoom continue;
the screen-space UI does not pause the game or follow camera zoom.

Content ownership stays separate from presentation: `DialogueConversation` exports
a stable `conversation_id` and ordered `Array[DialogueEntry]`; each entry exports
`entry_id`, `speaker_id`, `speaker_display_name` and multiline `text`. Edit these
in `dialogue/computer_opening.tres`, assigned through the console's exported
`conversation` property in `main.tscn`. Keep IDs stable and entry IDs unique within
a conversation. Empty IDs, speakers/text, null entries and duplicate entry IDs
make a conversation invalid. The three opening lines are temporary content, not
finalized narrative canon. The console's existing inspection response is retained.
Main listens for completion of `computer_opening` to activate `restore_computer`;
DialogueUI remains independent of objectives. No choices, narrative flags, log or
save system are implemented.

Dialogue validation is static only: resource paths and UID sidecars, typed exports,
nonempty content and unique IDs, scene/UI wiring, input flow, completion versus
dismissal, inspection fallback and preserved range/obstruction logic. Movement,
camera, collision, rendering and project settings are unchanged. Godot was not
executed; engine loading, runtime input and graphical behavior remain unverified.
Before merging, the owner must manually check all three speakers/lines in order,
E and Next/Finish, Esc and Dismiss, held E without skipped entries or automatic
reopening, reinteraction starting at the first entry, and leaving range while
open. Check prompt suppression, movement and zoom during dialogue and readability
at both zoom bounds. Temporarily clear the console's conversation reference (and
separately assign invalid content) to verify inspection fallback, then restore it.
Also verify range boundaries, approach from all sides/corners, obstruction,
inspection dismissal and the other fixtures remaining noninteractive.

## Computer HD art pilot (feature branch, pending merge)

`codex/computer-hd-art-pilot` replaces only the artwork beneath
`GroundObjects/WestObstacle/Visual` in `scenes/main/main.tscn`. One `Sprite2D`
displays the approved damaged texture by default. Both source PNGs in
`assets/environment/computer/` are preserved byte-for-byte: 1086 Ã— 724, RGBA,
with transparent backgrounds. Both existing owner-generated `.png.import` sidecars
are retained unchanged in the PR, preserving their texture UIDs, lossless import
settings, disabled mipmaps and no size limit. The owner's local Dave sidecar
change remains untouched outside this commit. The agent ran no imports.
Generated `.godot/` caches stay ignored.

The provisional local sprite scale is `(0.24, 0.24)`, position `(0, 0)`,
`centered = false`, and offset `(-543, -718)` in source pixels. Source point
`(543, 718)` maps to the unchanged body ground/sort origin `(-320, -180)` in
world space. Both states share that transform and linear texture filtering.
At alpha greater than 16, inclusive image bounds are `(51, 15)`â€“`(1023, 711)`
for damaged and `(47, 14)`â€“`(1021, 717)` for repaired. Very faint pixels extend
to `(0, 13)`â€“`(1085, 713)` and `(1, 12)`â€“`(1053, 723)` respectively.
The common anchor sits just below both substantial bases; the six-pixel base
difference remains about 1.44 world units. No per-state alignment correction is
applied. Visible extents are approximately 234 Ã— 169 world units versus Dave's
roughly 93-unit height. The owner has manually confirmed that damaged Computer is
appropriately proportioned relative to Dave. The very minor perceived shift
between artwork states was explicitly accepted for this pilot; no correction is
applied.

The sprite directly references `computer_damaged_pilot.png` and has no attached
script. Temporary keyboard controls, their script and UID, and the scene's script
resource reference have been removed. No Inspector state tooling, input handler
or visual-state controller remains for this pilot. The repaired PNG and its import
metadata remain available for a future narrative-driven repair implementation;
there is no repair gameplay or objective completion path in this PR.

Static checks cover PNG decoding, chunk integrity, alpha bounds, source hashes,
resource paths, the shared transform, and comparison of
all non-Computer-visual scene data against `main`. Collision (160 Ã— 48 at local
`(0, -24)`), interaction point `(0, -24)`, dialogue, Y-sorting, Dave, other
fixtures, existing gameplay scripts and project settings are unchanged. Final
static checks cover complete removal of temporary switching functionality,
damaged texture assignment, preserved asset/sidecar hashes, resource counts and
references, unchanged scene configuration, documentation links and Git diff checks.

The owner reports all eight visual-state playtest checks passed: damaged
proportions relative to Dave, both artwork appearances, switching and visual
continuity, collision and interaction in both states, movement/dialogue/objective/
camera/zoom regressions, and system stability. The minor perceived shift is
accepted. These are owner-reported runtime results from before removal of the
temporary controls. Finalization was validated statically only; the agent did not
run Godot or perform post-removal runtime or graphical verification. Agent
execution remains subject to
[AGENTS.md](AGENTS.md#godot-execution-safety).

## Objectives and first narrative integration (feature branch, pending merge)

`ObjectiveDefinition` exports a stable `objective_id`, short `title` and multiline
`description`, editable through `.tres` resources. Treat definitions as read-only
content during play; activation and completion are never stored in Resources.
`ObjectiveController` owns one dictionary of runtime states: `INACTIVE`, `ACTIVE`
and `COMPLETED`. `activate_objective(id)` accepts only inactive objectives;
`complete_objective(id)` accepts only active objectives. Both return `true` only
for a transition and emit `objective_state_changed(id, state)` once. Unknown IDs,
repeated calls and invalid transitions return `false` without an emission.
`get_objective_state(id)` returns the state, or `-1` for an unknown/rejected ID.
Null/invalid definitions are ignored; duplicate valid IDs are rejected entirely.
Completed objectives cannot reactivate. State resets when Main is reloaded;
hatch travel preserves this controller.

The main scene wires the controller signal to `ObjectiveTracker.show_objective()`.
The first active definition in exported list order is shown; completing it reveals
the next active definition, if any. There is no separate current-objective state.
The tracker only reads supplied content and owns presentation preferences; it
never activates or completes objectives.

Main connects Dave's existing `DialogueUI.conversation_completed` signal to a
scene-local handler. Only `computer_opening` activates `restore_computer`;
dismissal has no activation connection, and unrelated conversation IDs are ignored.
Repeated completion is harmless: the controller rejects activation unless the
objective is inactive, without emitting another state change. DialogueUI, Dave's
movement controller and the interaction detector have no objective dependency.

The registered objective starts inactive. Its independently editable definition
in `objectives/restore_computer.tres` has title **Restore Computer** and description
**Investigate the damage to Computer and determine what is needed to restore its
systems.** This is provisional opening narrative content. No repair mechanics or
narrative completion path are implemented. The temporary J/K demo adapter, node,
script/UID and resource have been removed; no replacement debug controls exist.

The tracker occupies the top right of its own `CanvasLayer`, using the existing
ship UI palette. It is independent of camera zoom and is laid out above the bottom
dialogue and inspection region at the configured 1280 Ã— 720 viewport. When the
objective activates, only **Show Objective** appears. Clicking it expands the
contextual panel. **Pin** keeps the full panel visible; **Unpin** returns to
collapsed contextual mode. **Hide** conceals the full panel and leaves
**Show Objective** available; clicking it expands in contextual mode again.
With no active objective, neither panel nor button appears, even when pinned.
Presentation preferences remain local to Main and survive hatch travel; there
are no tracker timers or animations.

Validation for this integration is static only: resource references, script UID
sidecars, inactive-state initialization, completion ID guard, dismissal separation,
idempotent activation, scene/signal wiring, tracker transitions, UI anchors,
documentation links, preserved gameplay/settings and Git diff checks. Godot was
not executed; engine loading, runtime behavior, text wrapping and graphical
nonoverlap remain unverified.

Before merging, the owner must manually verify that no tracker appears initially;
Esc/Dismiss before finishing Computer's dialogue leaves it inactive; and E/Finish
on its last entry reveals Show Objective. Expand, Pin, Unpin, Hide and restore the
panel, then repeat the conversation and confirm it neither duplicates the objective
nor resets the chosen tracker presentation. Check the tracker with dialogue and
inspection open, readability and nonoverlap at both zoom bounds, and continued
movement, camera follow, wheel zoom and interaction behavior. Reloading the scene
must reset the objective to inactive. Unrelated conversation IDs and signal counts
require owner runtime verification; their paths were inspected statically.

Add feature directories and GDScript files when they have a concrete purpose.

On `codex/normalize-dave-import-uids` (pending merge), seven preserved Dave
texture sidecars use canonical numeric UID encodings instead of manually authored
readable strings. Each replacement represents the same numeric resource ID;
asset paths, pixels and import settings are unchanged. This records the repeated
editor-normalized values so cleanup does not keep restoring the old spellings.
Keep these normalized sidecars in version control. Validation is static only;
Godot was not run to verify reimport behavior.

Track approved source artwork, source-adjacent asset `.import` sidecars (import
settings and stable resource UIDs), and `.gd.uid` files. The `.import/` ignore rule
applies to cache directories, not these sidecar files. Keep generated `.godot/`
data, including its import cache, editor caches, generated thumbnails and temporary
logs out of source control. Preserve existing local data under the retention rules
in [AGENTS.md](AGENTS.md); being untracked does not authorize deletion.
Use feature branches and pull requests;
validate affected scenes and scripts before requesting review.

Keep authoritative documentation in `docs/` and generated evidence out of Git;
the artifact retention and ZIP policies are in [AGENTS.md](AGENTS.md).
Use [documentation-sync](.agents/skills/documentation-sync/SKILL.md) before PR
review. After an approved merge, separately request
[post-merge-cleanup](.agents/skills/post-merge-cleanup/SKILL.md) for that PR number
from a chat attached to a surviving checkout. Cleanup stops when preservation,
attachment or Windows lock safety cannot be verified.

## The First Step (PR #26, merged)

This milestone added exterior exploration and hatch transitions. The world
generation feature below extends its authored exterior. Mining, production,
electricity and construction remain deferred. Agent validation was static only;
Godot was not launched by the agent.

Main remains alive for the playthrough. Its transition controller accepts explicit
source/destination scene paths, a named spawn and a presentation enum. Environments
provide a Y-sorted GroundObjects node and named Marker2D children under Spawns. Dave is
reparented between those groups, retaining the same controller, facing, sprites,
camera/zoom and UI. The objective controller/tracker remain under Main. Cached
inactive environments are detached from the tree, preserving their state without
participating in physics; they are freed with the playthrough. Reload Main to
start fresh. Run Main/F5 for playtesting; environment scenes alone have no player.

The automatic-transition feature branch adds `QUICK_FADE` as enum value 2;
existing presentation values and production hatch callers are unchanged. Only
the isolated development harness selects it. Its synchronous input lock, separate
fade duration and cancellation/recovery contract are documented in the
[transition preview guide](docs/INTERIOR_V2_TRANSITIONS.md). The production
transition behavior described below continues to use the original modes.

The interior hatch is at (512, 512), southeast on the deck. E uses the existing
range/visibility detector to request travel. A busy guard accepts only one request,
and tree changes are deferred out of physics. The first departure locks Dave's
movement and interaction, fades out over 0.65 seconds, loads the exterior under
black, places Dave at FromShip (-384, -64), and fades in over 0.65 seconds.
Only after that reveal finishes does first_exterior_reveal_completed become true.
Controls then resume. Later exits and all returns have no deliberate fade or
timer, with one physics frame allowed for destination bodies to register.
The interior return marker is FromPlanet (512, 416). Spawns clear all solids;
travel requires a fresh interaction, never an arrival trigger. Invalid scenes or
spawn contracts leave the source intact, restore controls and do not complete
progression.

The first-exit flag belongs to the small PlaythroughState node, separate from
presentation. It survives hatch travel, but resets with a fresh Main/application.
There is no disk save/load system, serializer, save slot or new-game menu. Restart
persistence is NOT implemented. Future save/load must restore the flag alongside
player location, objectives and world state; it must default false in unrelated
new games. No owner save files or settings are read or written.

PR #26 added no musing UI or provisional dialogue. The controller's
first_exterior_reveal_completed signal fires after controls resume and is the
integration point for a future small, portrait-free, timed, nonpausing presenter.
It must not route internal thoughts through the regular dialogue panel.

### Exterior and coordinate conventions

PR #26 originally bounded the clearing at [-1024, 1024] on each axis. PR #27
removed that perimeter and samples AuthoredCrashSite
polygons into procedural terrain. GroundObjects contains the provisional ship,
hatch and two rocks, plus Dave during a visit. Spawns is placement metadata.
Ship and rock geometry is deliberately simple, with nearest filtering inherited
by the exterior. Existing Dave filtering and Computer artwork are preserved.
The open area east/south of the ship reserves room for Ferrite discovery,
reactor, machines and cable routes. First Ferrite below uses part of this area;
the machines, reactor and cables remain deferred.

World units equal unzoomed pixels: +X east/right, +Y south/down; Dave's origin
remains ground contact. Terrain cell = floor(world_position / 64) per component.
Chunk = floor(terrain_cell / 32), local terrain cell = terrain_cell -
chunk * 32. Construction cell = floor(world_position / 32), independently of
terrain. Use mathematical floor, including negatives: world x=-1 gives terrain
cell -1, chunk -1/local cell 31, and construction cell -1; x=-64 gives terrain
cell -1, x=-65 gives -2. Chunks span 2048 units, and cells use half-open bounds.
The authored site straddles four chunks about the origin. The world generation
feature below supplies coordinate helpers, chunk management and protection.

### Owner playtest (ordered, one item at a time)

1. Run Main/F5: Dave starts inside at the existing origin.
2. Check 240-unit movement, WASD/arrows, diagonals, all four walk/idle directions,
   last facing, camera following, wheel zoom, collision and Y-sorting.
3. Approach the southeast hatch: contextual E prompt respects range/obstruction.
4. Press E: first exit fades smoothly out/in; input is locked during the reveal.
5. Confirm safe exterior spawn below the visible hatch and no automatic return.
6. Explore the clearing, ship and rocks; check readability, camera,
   both zoom bounds, animation and Y-sorting.
7. Approach the exterior hatch and press E: immediate return to a clear interior
   spawn, with the chosen zoom/facing retained.
8. Exit again: immediate travel with no repeated first reveal.
9. Repeat round trips and press/hold E rapidly: no duplicate travel, stuck input,
   stale prompt or inspection panel. Each crossing requires a fresh press.
10. Confirm the first-exit flag survives round trips. No save/load workflow exists
    to test; restart Main/application and confirm a fresh first reveal. Durable
    restart persistence remains deferred.
11. Verify Computer dialogue completion/dismissal and objective activation still
    work. Activate the objective before travel; confirm state and tracker
    preferences survive return and repeated conversation does not duplicate it.

Engine loading, rendered appearance, fades, runtime physics/input and these
playtest items remain unverified. Static inspection covers references, named
spawns, collision clearances, flag lifecycle, lock/failure paths, preserved player
files, documentation links and Git patch integrity.

## World Generation Foundation (PR #27, merged)

This feature extends PR #26 without changing Dave, camera, interior, narrative,
objectives or input settings. Agent validation is static only: Godot parsing,
imports, rendering, runtime behavior and performance remain unverified.

`PlaythroughState.world_seed` configures a new playthrough (default **26026**).
Its `_ready()` creates `PlanetWorldState`, owning the seed and in-memory terrain
color overrides/removed-detail identities. Set the seed before starting Main;
changing the Inspector setting during an existing session does not reseed it.
Each natural detail is identified by its world terrain tile, with at most one
per tile. Revisions refresh presentations incrementally, retaining old visuals
until replacements are ready. These internal hooks have no player-facing editing
or harvesting mechanic. Restarting Main/application resets all state.
**There is no disk save/load or durable persistence.**

`WorldCoordinates` implements mathematical floor for 64-unit terrain tiles,
32-tile/2048-unit chunks, and an independent 32-unit construction grid. Negative
coordinates and half-open bounds follow the examples above. This uses Godot's
normal Vector2/Vector2i precision and range; it is a prototype for exploration
near the origin, with no claim of unlimited coordinate accuracy or infinite world.

`PlanetGenerator` samples smooth value noise in global terrain space and uses
bounded integer coordinate hashing for seeded detail choices and offsets. No
mutable random sequence or visitation history affects generation. Rock, soil,
weathered ground and sparse scrub colors vary between tile samples; 64-unit tile
edges remain provisional. Small rocks, shrubs and alien stalks are nonblocking
ground details drawn below Dave and authored Y-sorted objects. There are no
procedural physics bodies, finalized assets or ecological systems.

The original clearing, impact scar, north ridge and south shelf polygons/colors
remain editable in `planet_exterior.tscn`. Their parent is hidden because these
polygons are generation data rather than a second rectangular terrain layer.
The generator applies them in scene order, with full weight inside and a smooth
256-unit exterior feather. Their irregular outlines define the impact/recovery
transition; beyond the feather, normal rocky scrubland resumes. Authored interiors
remain seed-independent and override both baseline and stored colors. The old
rectangular background and temporary perimeter walls are removed. Ship, hatch,
spawn and both rock objects/collisions are preserved.

`PlanetExterior.protected_gameplay` separately reserves ship entrance, spawn,
main approach, factory clearing and Ferrite space. First Ferrite below adds the
introductory deposit within that existing protection.
A 48-unit clearance suppresses details around this polygon and the authored
geology polygons. Existing solid-object anchors also exclude details within
160 units, covering the two rocks; the larger ship is inside the clearing.
Details return sparsely through the recovery feather, with rejection probability
proportional to overlay weight. The largest detail extent is under 15 units. The protection
polygon can be edited independently of scar colors/outlines.

`planet_exterior.gd` owns only presentation lifecycle. Configure `loading_radius`
(default **2**), `retention_margin` (**1**) and `chunks_per_frame` (**2**) before
arrival. Required chunks form a Chebyshev square: `(2 * radius + 1)^2`, initially
**25** chunks. Crossing a chunk boundary replaces stale requests, prioritizes
nearby missing chunks, retains existing neighbors and removes nodes outside
radius + margin. At defaults at most **49** chunk nodes can remain, including
recently adjacent chunks; no indefinite cache accumulates. Stepping back across
a boundary reuses retained nodes. Nodes and requests stay cached while the exterior
is detached for ship visits and are freed with its playthrough.

First arrival fills the whole neighborhood in batches behind the existing black
curtain with input still locked. Later hatch arrivals reuse it without a new fade;
normal travel still allows the original physics registration frame. During walking,
missing outer chunks fill over subsequent frames, two per frame by default.
The two-chunk lookahead is intended to cover the viewport at existing zoom and
240-unit movement; stalls, visible coverage and tuning require owner testing.
This is a work-count budget, not a measured millisecond limit. No threads,
benchmarks or runtime performance claims are included.

Generation/presentation does **not** mark terrain explored or surveyed. No fog,
map or survey system exists yet. Future production simulation must live outside
disposable `TerrainChunk` nodes and continue when terrain visuals unload. No
factory simulation, building serialization, mining or logistics is implemented.

Owner review should follow the PR's ordered playtest checklist, one item at a
time: interior baseline, first reveal, crash-site preservation, travel beyond
old boundaries, continuous coverage, revisit determinism, unloading/retention,
seed variation, protected clearing, presentation/collision, transitions/objectives,
and finally extended exploration without debugger errors. Only the owner runs
these checks; agent static results do not establish gameplay acceptance.

## First Ferrite - Discovery (PR #28, merged)

One authored Ferrite deposit lies east/southeast of the hatch, centered near
(288, 256), approximately three seconds' direct walking distance from FromShip.
Provisional dark slate-gray ground and silver veins distinguish it from terrain.
The patch is broadly oval with modest edge variation. The introductory inspection
region has no artwork; the same mineral ground and veins remain visible before
and after discovery. The separate raised discovery formation is removed by this
refinement. Existing ship, hatch, spawn and rocks are unchanged. Protected gameplay
geometry suppresses procedural details over the patch and its approach for every
seed.

`PlanetWorldState` owns a read-only authored `ResourceDeposit` definition from
`scenes/world/introductory_ferrite.tres`: stable ID `crash_site_ferrite`, resource
type `ferrite`, and a mineral-bearing polygon in planet world coordinates. Its
bounds are (128, 144) to (448, 368). `get_deposit(id)` and
`deposit_at(world_point, resource_type)` query identity and mineral ground without
depending on artwork or disposable terrain chunks. Deposits are infinite,
uniform and nondepleting; no quantity, yield or extraction simulation exists.
Definitions are shared immutable content; discovery belongs to PlaythroughState.

The mineral area is separate from the decorative outline. Two future adjacent
64 x 64 footprints at (192, 192) and (256, 192) fit inside it. The introductory
invisible inspection region at (304, 280), radius 24, sits at the silver-vein
junction within mineral-bearing ground and occupies no construction cells.
The independent construction cell is 32 x 32; Extractors occupy 2 x 2 cells.
Only a designated extraction point
must overlap compatible mineral ground; the remaining footprint may extend off
the deposit. Edge-to-edge machines are allowed, overlapping footprints are not.
Every valid extraction point has equal richness. Construction validation,
compatible-deposit highlights and placement previews are added by the deployment
feature below.

Approach the silver-veined part of the deposit to see **E - Examine mineral
deposit** (an em dash is displayed in-game). The invisible Area2D reuses
WorldInteractable and the detector's normal 120-unit target-point range,
nearest-target selection and obstruction ray. No mouse targeting or exact
standing point is required. The detector includes areas as well as bodies and
supports standing directly inside the region. The area blocks neither movement
nor construction. Only a deliberate E inspection calls `discover_ferrite`;
proximity does not discover it. The state validates deposit identity, sets
`ferrite_discovered` before emitting one signal, and rejects repeated discovery.
Afterward targeting is disabled immediately and the detection shape is disabled
deferred to avoid physics-callback mutation. The prompt clears without a repeat
inspection response. Nothing visual changes during discovery. Initial
availability and subsequent updates read the existing playthrough discovery
flag; no additional persistent flag is added. Scene revisits and terrain-chunk
reloads preserve disabled interaction; a fresh playthrough restores it. Resource
deposits, interaction regions and genuine construction obstacles remain separate;
future permanent formations, trees or rocks may explicitly block construction.

Main routes discovery to reusable `MusingUI` and separately editable
`MusingDefinition` content in `dialogue/ferrite_discovery.tres`. Both approved
thoughts appear together in an 18-point, portrait-free lower-left panel, above
the interaction prompt and away from the upper-right objective tracker. It fades
in for 0.25 seconds, holds for 5 seconds and fades out for 0.35 seconds
(approximately 5.6 seconds total). Only this Ferrite content duration changed;
the approved text, other definitions and global timing default are preserved.
Controls ignore mouse input; it has no buttons, input handlers or gameplay lock.
A new musing cancels/replaces the old tween. Accepted hatch transitions dismiss
it immediately, including a transition that subsequently fails validation.
Main owns its lifetime, so fresh playthroughs cannot inherit stale UI.

Restore Computer remains the single registered overarching objective. A display
definition with the same ID/title changes its guidance to **Locate the Extractor
in the maintenance bay.** after discovery; no duplicate objective is registered
or completed. Existing tracker expand/pin/hide/restore preferences remain intact.
Computer's conversation still activates the original objective. If the player
explores before finishing it, discovery also activates that same objective so
guidance remains recoverable. Later Computer dialogue cannot revert the stage.

Discovery and world identity survive ship travel, terrain unloading/regeneration
and revisits. A fresh Main/application resets discovery and objective state.
**Persistence is session-only; there is no disk save/load.** Introductory machine
recovery will proceed strictly Extractor, then Smelter, then Fabricator. The later
recovery steps, mining, construction, recipes and power remain unimplemented. The pending Extractor milestone below adds the first recovery
step and inventory. Future research allows broader freedom.

The owner reports all 15 original PR #28 manual playtests passed before the
final timing and temporary coordinate HUD adjustments. Those adjustments remain
pending owner review. Agent validation is static only: scene/resource paths and UID
references, protected placement and two future footprints, unchanged original scene objects,
one-time state/signal ordering, objective idempotence, musing cancellation,
transition wiring, preserved movement/dialogue/settings and Markdown/diff checks.
No Godot editor, import, headless run, gameplay, rendering or performance test was
performed. Engine parsing, appearance, text wrapping, timing, interaction physics
and chunk travel require owner verification using the PR's ordered checklist,
one item at a time.

### Temporary developer coordinate display

`scenes/ui/developer_coordinates.tscn` is a standalone CanvasLayer under the
persistent Main scene. Its exported `player` reference points to the existing
Dave instance and survives his reparenting between worlds. Each frame it reads
Dave's `global_position` in the current scene's world coordinate system, rounds
each component to the nearest integer, and displays explicit signs, for example
`X: -2145   Y: +768`. It shows current position in both ship and exterior;
coordinates may jump when a hatch places Dave at the destination spawn.
It does not accumulate distance or alter movement, camera or world generation.

The small 16-point label sits at (24, 24) in screen space, matching the Objective
Tracker's 24-unit top offset and the HUD's horizontal margin. Muted text and a
subtle shadow follow existing UI conventions. All controls ignore mouse input.
Disable it through `Main/DeveloperCoordinates.display_enabled` in the Inspector;
there are no persistent settings or new player controls. Removing that Main
instance also removes the temporary display without changing gameplay scripts.

Static review covers the persistent player reference, direct position read,
signed integer formatting, scene/resource/UID wiring, mouse pass-through and
screen offsets. Godot was not run for these adjustments. The owner should verify
the approximately 5.6-second Ferrite musing and live signed coordinates while
walking in both worlds, hatch coordinate changes, layout alongside the tracker,
and the exported disable setting.

## Recover the Extractor (PR #30, merged)

The maintenance bay is a separate 640 x 448 world-unit room, revising the previous
same-scene equipment-room plan. In the cabin, approach the marked MAINTENANCE
doorway at (-520, -360) and press **E**. The bay's CABIN doorway returns
immediately. Both reuse `SceneTransitionController` and `scene_hatch.gd` with
named spawns (`FromCabin` and `FromMaintenance`); no controller changes, fade or
loading screen were added. Dave remains the same instance with his camera zoom
and facing. Arrival spawns clear the solids. Each transition requires a fresh E
press; holding E does not immediately send Dave back. The first exterior reveal
remains unchanged.

Placeholder damage, debris and industrial markings leave a clear walking aisle.
Three labeled storage racks hold intact packaged modules. In PR #30, Smelter and
Fabricator were secured static bodies without interactions. The Smelter recovery
milestone below extends only the Smelter; Fabricator remains noninteractive.
Extractor is visible but unavailable before Ferrite discovery. After discovery,
approach its rack and press **E - Recover Extractor** (in-game em dash).

**Tab** (physical key) or **Inventory (Tab)** toggles one nonmodal panel showing
**Materials** and **Machines / Equipment** together, initially empty slots. **Tab**,
**Esc**, or the button closes it. Movement and E interactions continue while it
is open; Esc closes inventory first when it is visible. It is available in all
three environments. Recovery displays Extractor with quantity 1 under Equipment.
That milestone has no drag/drop, deployment, capacity, weight or item splitting.
The deployment milestone below extends its Equipment actions.

`ItemDefinition` resources provide stable identity, display name and section
metadata. `InventoryState` keeps shared integer quantities by ID, with definitions
separately referenced for presentation. `add_item` supports quantities greater
than one; it rejects invalid definitions, nonpositive additions, conflicting
definitions for an existing ID and integer overflow, and reports success. Section
metadata does not affect insertion. Merging the UI sections later would not change
recovery or storage. There is no elaborate item database. UI reads authoritative
quantities rather than keeping a separate copy.

`Main/PlaythroughState` owns inventory and recovery state. `recover_extractor()`
checks Ferrite discovery and one-time/reentrant guards, then inserts the packaged
item. Only successful insertion records recovery and emits its completion signal.
Failure leaves the rack available and progression unchanged. The rack reads
that state on initialization and recovery, hiding its module and showing EMPTY.
Cached environments retain that presentation on revisits. A new Main instance
resets inventory, recovery, Ferrite discovery and objectives; there is **no disk
save/load**.

Main routes recovery to existing `MusingUI`, with independently editable content
in `dialogue/extractor_recovery.tres`. Dave's exact internal thoughts are:

> There you are. Still in one piece.
>
> Let's see if you survived the landing better than the rest of us.

Presentation fades in for 0.25 seconds, reads for 5 seconds and fades out for
0.35 seconds. Gameplay continues; transition start dismisses it. Ferrite's text,
timing and global musing presentation are unchanged.

Restore Computer keeps its single registered ID and remains active. Its staged
display definition reads **Deploy the Extractor on the Ferrite deposit.** after
recovery, taking precedence over the post-discovery stage. Later Computer dialogue
cannot revert it. Tracker pin/unpin, expand/collapse and hide/restore behavior is
unchanged. Starter recovery remains strictly Extractor, then Smelter, then
Fabricator; PR #30 implements only Extractor rack recovery. Deployed-machine
recovery and placement are added below; mining, production, power and later
starter rack recovery remain deferred.

Agent validation is static only: resource paths and node wiring, doorway spawn
clearance, item/quantity and recovery guards, musing content and timing, objective
staging, preservation of existing systems, Markdown links and Git whitespace.
No Godot, project code, import, headless, graphical, runtime or performance checks
were run. Engine parsing, input routing, text layout, interaction physics, travel
and gameplay remain for owner verification. The PR includes an ordered manual
checklist to conduct one item at a time.

## Deploy the Extractor (PR #32, merged)

Open inventory with **Tab**, then click the **Extractor** slot in Equipment to enter
construction immediately. There is no selected-equipment state or separate
Deploy button. Clicking a deployable packaged machine calls the existing public
construction entry point, closes inventory and starts a neutral translucent
machine ghost with a green valid or red invalid footprint and an invalid-placement
reason. Move the mouse
to position it; **R** rotates 90 degrees clockwise, **left-click** confirms,
and **right-click / Esc** cancels. A successful placement ends the mode.
Previewing indoors is allowed, but placement requires planetary ground.
Canceling or clicking an invalid location leaves inventory unchanged.

The footprint is **2 x 2 construction cells (64 x 64 world units)** on the
independent **32-unit grid**. Its top-left cell is authoritative; floor-based
snapping works across zero and negative coordinates. Rotation preserves that
cell, swaps asymmetric footprint dimensions on odd quarter turns, and rotates
the extraction point in the same coordinate convention. The Extractor's center
extraction point must fall inside compatible mineral-bearing ground; the rest
of its footprint may extend outside. Deposits never deplete; production is
described in the next milestone below.
`MachineDefinition` extends the existing packaged `ItemDefinition`; the Extractor
resource supplies Ferrite compatibility. Generic validation and highlighting
contain no Ferrite rule. Each deposit supplies its highlight color; compatible
polygons receive a restrained silver-blue overlay clipped to loaded terrain and
normal viewport visibility, below the ghost and validity footprint. This adds
no surveying, exploration state or offscreen deposit reveal.

Both preview and commit use `PlacementRules.rejection`, including inventory
availability, planetary ground, range, extraction-point compatibility, persistent
machine overlap and physical blockers. Machines may touch footprint edges.
Layer 3, **Construction blockers**, explicitly marks authored ship/hatch solids
and large rocks. The introductory inspection region is an invisible nonblocking area and
does not carry that property. Mineral-bearing ground and current decorative
details do not carry it either. Future trees or other plants can opt into blocking; vegetation is not universally exempt. Dave cannot
be enclosed in a new footprint. Deployed machines also have ordinary movement
collision. Their record footprints remain authoritative for machine overlap.

Hover a deployed machine within range to see the exact **Press B to recover**
prompt. **B** enters recovery mode, with a small bottom-screen instruction and
an amber eligible-target outline. **Left-click** an eligible machine to recover;
**right-click / Esc** cancels. One successful recovery automatically exits;
invalid or out-of-range clicks leave recovery mode active. Construction and
recovery ranges are independent Inspector exports on `Main/Construction`, both
initially **160 world units**, measured from Dave to the nearest point on the
footprint. There are no range upgrades, batch selection or remote recovery.

`ConstructionController.begin_deployment(definition)` is callable independently
of Equipment presentation. Confirm clicks are handled after GUI input and
queued for physics-time validation. One pending confirmation retains its original
tool mode, world instance and placement cell/rotation or recovery target; later
clicks cannot overwrite it. Execution rejects a changed mode/world and rechecks
the authoritative placement/recovery rules. Canceling, switching tools, opening
inventory or beginning a transition clears the pending request.

Inventory buttons and the panel consume mouse events through native Godot GUI
routing; informational HUD elements remain noninteractive. Open inventory,
dialogue and inspection responses explicitly block tool confirmation and B
activation. An active tool yields immediately when such a context opens, letting
the existing interface handle its keys. Otherwise rotation/cancel events belong
to the tool, E requests are suppressed, and ordinary E interaction resumes on
exit. Esc closes only the interface owning that event; opening inventory cancels
the tool without consuming equipment. B may enter recovery without a hovered
machine; R rotates only during construction. Movement and camera zoom remain
available. Tools neither add dialogue nor change approved internal musings.

`PlanetWorldState` owns machine IDs, definitions, cells and normalized quarter
turns. Synchronous guarded transactions remove exactly one packaged item before
inserting one machine record, or add exactly one item before removing a record.
Inventory transfer failure leaves world state unchanged. Inventory notifications
are deferred until both sides agree; the guard covers reentrant signal callbacks.
Canceling changes neither side. Exterior presenters synchronize by ID under
`GroundObjects`, independently of disposable terrain chunks, and retain physical
and visual representation on travel. Reattachment reconciles them from state.
The existing playthrough and cached-world ownership preserve machines through
cabin/bay visits and chunk unload/reload. A fresh playthrough resets everything;
there is no disk save/load or second machine inventory.

The first successful Extractor deployment permanently advances this playthrough's
**Restore Computer** guidance to **Produce Ferrite Ore with the Extractor.**
Recovery and redeployment do not revert it or repeat the milestone. Existing
Ferrite discovery, rack recovery, dialogue and tracker preferences are preserved.
The objective remains active. PR #32 left the machine unpowered and nonproducing;
the production milestone below adds provisional power-independent extraction.
Power, smelting, fabrication, logistics, manufacturing, hotbar support,
terrain/vegetation removal, additional machines/resources and final artwork are
deferred.

Validation for this feature is static only: standalone gdtoolkit 4.5 syntax
parsing of all 34 GDScript files, source/control-flow review, scene and resource
references, footprint/coordinate geometry, objective wiring,
protected-file comparison, Markdown links and Git diff checks. No Godot import,
headless execution, project code, graphical checks, gameplay tests or performance
probes were run. Engine parsing, input routing, physics contact, rendering/UI
layout and actual travel/persistence require owner playtesting. The feature PR
contains an ordered manual checklist, including repeated cancel/place/recover,
range limits, edge contact, GUI input, chunk travel and scene revisits.

## Produce Ferrite Ore (PR #36, merged)

The Extractor automatically produces **1 Ferrite Ore per 1.0-second cycle**
(provisional maximum **60/minute**) into its own **20-ore buffer**. Output item,
quantity per cycle, duration and capacity are exports on `MachineDefinition`,
configured by `inventory/extractor.tres`. Ferrite Ore uses the existing shared
quantity inventory with stable ID `ferrite_ore` and Materials presentation.
The compatible infinite Ferrite deposit and placement geometry are unchanged.
Electrical requirements are temporarily bypassed; there is no power simulation.

`PlanetWorldState` remains authoritative for each machine's identity, definition,
cell, rotation, elapsed cycle progress and whole-item output. Persistent
`PlaythroughState._process` advances all machines while Main is active, including
cabin/bay visits, transitions, open interfaces and chunk unloading.
Delayed updates complete multiple cycles up to available capacity. Reaching the
available-cycle time limit completes all affordable cycles directly, avoiding
division-rounding undercounts for configurable durations such as 0.7 seconds.
A machine pauses if another whole cycle cannot fit and resumes automatically
after withdrawal. Blocked updates preserve existing fractional progress and earn no
backlog; reaching capacity completes the final cycle. No visuals, animation,
panel or terrain node drives production. Fresh Main resets machines, inventory
and progression; there is no offline production, disk persistence or session
catch-up.

Approach a deployed machine and press **E** to inspect it through the existing
nearest-visible-target interaction detector. Machine inspection has a separate
**96-world-unit** range export on Dave's `InteractionDetector`, measured from
the interaction origin to the machine center, independent of the 160-unit
construction/recovery ranges. The compact nonpausing panel shows machine name,
Producing / Output Full / Inactive, live cycle percentage and output/capacity.
A small steady machine light reflects those authoritative states in green,
amber or neutral gray. Presenters initialize the light from authoritative state
before attachment, then poll status and request a redraw only when it changes.
The placement ghost has no operating light.

**Collect All** transfers completed output through the existing inventory API,
clears the buffer only after successful transfer, leaves the panel open and
preserves cycle progress. Empty collection is a no-op; the empty-buffer button
is disabled. Movement remains available. **Esc** or **Close** dismisses the panel;
walking out of range, opening inventory, entering construction/recovery, or
starting a scene transition closes it automatically. While the panel is open,
**B** cannot activate recovery and leaves the panel open; close it first. **R**
does not rotate a preview and **E** cannot trigger another world interaction.
Recovery activation checks `MachineUI.is_open()` before changing tool mode or
emitting `mode_started`, using the detector's existing panel reference. **Tab**
opens inventory and closes the panel. GUI clicks cannot also confirm
construction/recovery; dialogue, responses and tools keep input ownership.

The existing **B**, then **left-click** recovery now returns all completed solid
output and one packaged machine together, removes its persistent record and
discards incomplete cycle progress. Synchronous transaction guards prevent
collection, simulation and recovery from interleaving. Notifications occur only
after inventory and machine state agree. If either inventory addition fails,
recovery leaves inventory unchanged and retains the complete deployed record.
The smelting extension below replaces rollback with prevalidated batch additions.
No fluid/gas categories or generalized transfer framework are introduced.

The first successful Ferrite Ore acquisition in Materials, through either
collection or recovery, permanently advances **Restore Computer** guidance to
**Locate the Smelter in the maintenance bay.** Inventory notification drives
this one-time playthrough flag; production into a machine buffer does not.
Removing ore cannot revert it, and repeated collection cannot retrigger it.
Earlier milestones and approved dialogue are preserved. Smelter recovery is
extended below; smelting, fabrication, electricity and logistics remain deferred.
Future conduits and two outputs sharing this buffer are tracked in
[issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35);
no ports, routing or transport are implemented here.

Validation is static only: standalone gdtoolkit 4.5 grammar parsing, resource and
scene wiring inspection, production arithmetic and transaction/control-flow
review, protected-file comparison, Markdown links and Git whitespace checks.
No Godot, imports, project code, headless, graphical or performance checks were
run. Engine type checking, production timing, physics/input behavior, UI layout,
travel persistence and all gameplay acceptance require owner manual testing.
The feature PR provides the ordered playtest checklist.

## Smelter recovery (PR #38, merged)

The existing first-Ferrite-acquisition event now also presents Dave's exact musing
from `dialogue/ferrite_acquisition.tres`:

> Ore's no good to me like this. Need to refine it first.
>
> That smelter should do the job.

It uses the existing nonpausing MusingUI: 0.25-second fade in, 5-second reading
period and 0.35-second fade out, with transition dismissal and no confirmation.
Only successful acquisition into Materials through Collect All or recovery of an
ore-containing Extractor triggers it. Buffer production does not. The existing
`ferrite_acquired` flag owns the one-time event; additional ore, removal and scene
revisits do not repeat it. Main presents the musing and refreshes guidance in the
same event handler. Smelter recovery has no musing or inspection step.

The authored Smelter remains visible in its original bay location. Before first
ore acquisition, its rack cannot interact and offers no prompt. Afterward, approach
it and press **E â€” Recover Smelter**. `PlaythroughState.recover_smelter()` checks
acquisition, recovery and reentrant guards, adds exactly one packaged item, then
records recovery and emits completion. Failed insertion leaves recovery incomplete
and the rack available. Inventory possession alone cannot advance this milestone.

`inventory/smelter.tres` uses stable ID `smelter`, display name **Smelter** and the
Equipment section. PR #38 used `ItemDefinition` to display quantity text without
a deployment action. The deployment milestone below promotes this same resource
to `MachineDefinition`, preserving its identity and quantity storage.
Extractor retains its existing single-click deployment.

`smelter_rack.gd` follows the Extractor rack presentation pattern, hiding Module
and Secured and showing EMPTY after recovery. Rack, frame, sign, position and
collision remain. It initializes from persistent playthrough state, and cached
scene revisits retain the empty rack. Inventory and recovery reset only with a
fresh Main instance; there is no disk save/load. Restore Computer retains its
single objective ID and all earlier stages, with successful Smelter recovery
taking precedence to show **Deploy the Smelter near the Extractor.** Removing
items or revisiting Computer cannot revert this milestone. The deployment stage
below advances guidance further; "near" adds no placement rule.

Fabricator remains visible, secured, noninteractive and unavailable in inventory.
The maintenance bay remains provisional: future HD art should use varied mounting,
damaged infrastructure, access and environmental storytelling rather than three
evenly spaced machines. This milestone changes no layout, artwork or movement path.
Smelting, power, logistics, manufacturing and Fabricator progression remain deferred.

Validation is static only: source/control-flow inspection, resource and scene
references, preservation comparisons, Markdown links and Git whitespace checks.
No Godot, project code, engine import, headless or graphical checks were run.
Engine parsing, physics, input, UI readability, persistence during travel and
debugger output require owner manual playtesting. The feature PR supplies an
ordered checklist for testing one item at a time.

## Deploy the Smelter (PR #39, merged)

After rack recovery, click Smelter in Equipment to close inventory and enter
the existing construction mode immediately. The same `smelter` item is now a
`MachineDefinition` with a 2x2-cell (64x64-unit) footprint. Its empty
`compatible_resources` list already permits ordinary unobstructed planetary
ground and highlights no deposits. There is no Extractor proximity requirement.
Existing 32-unit snapping, clockwise R rotation, green/red footprint, neutral
translucent ghost, range, obstacle/occupancy checks, confirmation and cancellation
are reused without placement exceptions or controller changes.

`MachineVisual` draws a provisional cold furnace chamber, industrial housing,
side framing and directional top vent. In PR #39 deployed status stayed gray; the ghost
omits the status light. Presentation owns no simulation state.

In PR #39 the shared E inspection panel used `has_production()` to show **Inactive** and
**No production configured.**, hiding progress, output/capacity and Collect All.
Its Close button, movement, range closure and input/transition guards remain.
Opening an Extractor restores its existing production controls. That milestone gave
the Smelter no output item, cycle or capacity, so persistent production skipped it; no new
timer, buffer, ports, power, recipe or transport is introduced.

Existing atomic planet transactions consume one packaged item only on successful
placement and create one record with ID, definition, cell and rotation. B recovery
removes that record and returns one packaged item. Planet state owns machines
independently of terrain chunks and cached interior visits; there is no disk save.
The first committed Smelter deployment emits the existing planet deployment event;
`PlaythroughState` records `smelter_deployed` once and emits
`smelter_deployment_completed`. Main gives it guidance precedence within the same
Restore Computer objective: **Produce Ferrite Ingots with the Smelter.** This is
guidance implemented by the smelting extension below. Possession, failed/canceled
placement, recovery and redeployment cannot reset or repeat completion. A fresh
Main resets both planet and progression. Rack recovery, all existing musings and
Fabricator locks remain unchanged.

Validation is static only: source/control-flow review, resource references and
scene wiring, protected-file comparisons, Markdown destinations and Git whitespace
checks. No Godot, project code, imports, headless, graphical or performance checks
were run. Engine parsing/type checking, physics/input, layout, visual readability,
travel persistence and gameplay acceptance require owner manual testing. The
feature PR supplies the ordered playtest checklist.

## Produce Ferrite Ingots (PR #40, merged)

The deployed Smelter automatically converts **1 Ferrite Ore to 1 Ferrite Ingot**
per **2-second cycle** (provisional maximum **30/minute**), without power.
`inventory/smelter.tres` configures the fixed recipe through `MachineDefinition`
input/output exports: independent **20-ore input** and **20-ingot output** buffers.
The stable `ferrite_ingot` item uses Materials and existing quantity storage.
The Extractor retains its 60-ore/minute output-only recipe and no input record.

The existing **E** machine panel adds a vertical input section with **Transfer All**,
above the output section and **Collect All**. Transfer moves the smaller of available
ore and free input capacity; excess stays in inventory. Empty/full input disables
Transfer All. Collect withdraws only completed output, and is disabled when empty.
Both keep the panel open and retain fractional progress. Existing movement, range,
inventory, tool, GUI and transition guards remain. Extractor controls are unchanged.
The input heading is **Input** while empty and includes the configured material
name only while input is stored. Live refresh updates it after transfers and after
the last input is consumed; input-free machines keep the section hidden.

Persistent `PlanetWorldState.advance_production()` owns processing even during
ship visits and terrain unloading. Input remains stored during partial cycles;
completed cycles consume input and add output together without callbacks.
Elapsed productive time is bounded by both available input and output capacity,
discarding blocked time without a catch-up backlog. Blocked updates retain
fractional progress; the final affordable cycle ends at zero progress. The existing
capacity-boundary precision correction also applies to input-limited completion.
Status priority is Inactive, Output Full, Input Empty, then Producing. The existing
light uses gray, amber, blue and green respectively; the panel reads the same state.

**B** recovery prevalidates packaged equipment, stored input and completed output
with `InventoryState.add_items()`, using private dictionary copies. Any invalid
identity, quantity or integer overflow rejects the whole payload without mutation.
On success inventory is committed and the deployed record removed before either
inventory or world observers are notified. No published partial recovery or
rollback is used. Fractional progress is discarded; solid ore is returned intact.
The same batch path preserves Extractor recovery with stored ore.

First successful ingot acquisition through Collect All or recovery sets the
per-playthrough `ferrite_ingot_acquired` flag through inventory notification.
Buffer production alone cannot trigger it. It presents the exact musing:

> One step closer. Assuming that fabricator survived the crash.
>
> Guess there's only one way to find out.

The existing MusingUI uses its standard fades, a 7-second reading period and safe
transition dismissal. Guidance becomes **Locate the Fabricator in the maintenance
bay.** under the unchanged Restore Computer objective ID. Spending ingots,
recovery, redeployment and travel cannot revert or repeat completion. Fresh Main
resets session state; disk saves remain unimplemented. Fabricator rack, art,
collision and interaction locks are unchanged. Recipe switching
([issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37)), power
and logistics ([issue #35](https://github.com/interneth3ro/the-long-way-home/issues/35))
remain deferred; no ports, conduits or new production manager are added.

Validation is static only: standalone gdtoolkit 4.5 grammar parsing, source and
transaction review, resource/scene wiring, protected-file comparisons, Markdown
links and Git whitespace checks. Godot and project code were not run;
engine parsing/type checking, timing, input behavior, layout, travel persistence
and gameplay acceptance require the owner's manual testing. The PR contains an
ordered checklist, including acquisition by collection and by recovery in separate
fresh playthroughs.

## Recover the Fabricator (PR #42, merged)

After first Ferrite Ingot acquisition into Materials, approach the existing
maintenance-bay Fabricator and press **E - Recover Fabricator**. The permanent
`ferrite_ingot_acquired` milestone is reused unchanged: Smelter output alone does
not unlock recovery; collection or recovery of an ingot-containing Smelter does.
Spending ingots cannot relock it. No inspection, repair or material cost is added.

`PlaythroughState.recover_fabricator()` follows the Smelter rack transaction:
check acquisition, completion and reentrant guards, insert exactly one packaged
item, then record recovery and emit completion. Rejection leaves the rack and
objective unchanged and permits retry. Repeated input and synchronous inventory
callbacks cannot duplicate the item. PR #42 introduced `inventory/fabricator.tres`
as a plain Equipment `ItemDefinition` without deployment. The feature below
extends the same item identity into a deployable `MachineDefinition`.

`fabricator_rack.gd` uses the shared WorldInteractable interface and existing
input priority, refreshes on completion and initialization, hides Module/Secured
and shows EMPTY. Rack artwork, position, collision and frame remain intact.
Persistent Main owns recovery across cached or newly instantiated bay visits;
a fresh Main resets inventory, unlock and recovery. No disk saves are added.

Successful recovery refreshes Restore Computer guidance directly to **Craft a
Ferrite Plate.**, using the same objective ID with highest stage precedence.
There is no deployment objective, new dialogue, musing or special recovery panel.
The existing ingot musing and nonpausing presentation are unchanged. The crafting
objective remains incomplete: deployment, production, recipes (including
[recipe switching, issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37)),
power and logistics are outside this feature.

`tests/fabricator_recovery_test.gd` adds standalone regression checks without a
third-party framework. It covers locked/unlocked interaction, buffer-only ingots,
collection and Smelter recovery acquisition, spending, rejected insertion and
retry, synchronous reentry, exact quantity/category, empty rack, objective
precedence, cached/new bay instances and fresh playthrough reset. It exercises
bay detach/reattach rather than driving the asynchronous hatch transition.
These tests are **not executed** under the current Godot restriction; run them
only after explicit owner authorization lifts the relevant restriction.

Agent validation is static only: standalone gdtoolkit 4.5 grammar parsing of
changed/new scripts, scene/resource reference checks, protected-file comparisons,
Markdown links and `git diff --check`. No Godot, project code, imports, headless,
graphical or performance execution was performed. Godot type checking, regression
test execution, E input/physics, visual feedback and actual hatch travel require
owner verification. The feature PR provides an ordered manual checklist.

## Configure and load the Fabricator (PR #43, merged)

Deploy the recovered Fabricator by clicking it in Equipment. Existing preview,
R rotation, left-click placement, right-click/Esc cancellation, range, planetary
ground and collision checks apply. Its footprint is 2x2 cells (64x64 world units),
with provisional teal assembly-bed artwork shared by ghost and world machine.

After placement commits and construction exits, the shared panel opens for that
exact instance. `PlanetWorldState.deploy_machine_instance()` returns its committed
ID (zero on failure); the existing bool `deploy_machine()` remains available.
Construction emits `deployment_completed(machine_id)` after exiting its tool.
The consumed placement click cannot choose a card. Open panels block construction
and recovery input. Failed placements consume nothing and open no chooser.

The panel offers icon cards for Ferrite Plate (1 Ferrite Ingot -> 1 Ferrite Plate)
and Ferrite Rod (1 Ferrite Ingot -> 2 Ferrite Rods). Selection stays in the panel,
showing recipe requirements, expected product, stored inputs/capacity and Transfer
All. Nothing loads automatically. Dismissing an unconfigured machine leaves it
unconfigured; later in-range E opens the chooser directly. Configured machines
reopen inspection. PR #43 did not include recipe switching; the feature below
extends configured inspection.

Only the initial post-placement panel session bypasses inspection distance; it
remains open after selection. Transfer All still checks normal range, including
in that session. Closing or travelling ends the exception; later inspection uses
the existing 96-unit range.

`RecipeDefinition` and `RecipeIngredient` resources own recipe identity, required
items/quantities and output item/quantity, without production duration.
`MachineDefinition.recipes` lists available recipes and `input_capacity` sets
20 units per accepted material. `PlanetWorldState` owns `recipe_id` separately
from `inputs`, keyed by item identity. Machine snapshots deep-copy nested storage.
The Smelter retains its existing scalar input and production behavior.

Transfer All stages every ingredient removal with `InventoryState.remove_items()`
before publishing any change. Both starter recipes accept only Ferrite Ingots:
35 available loads 20 and leaves 15. Unaccepted materials stay with Dave. The
storage/transaction path also supports independent capacities for multiple
ingredients. Recovery atomically returns one packaged Fabricator and all inputs.
Insertion failure preserves the machine, recipe and inventory; success removes
the record. Redeployment gets a new ID, empty inputs and an unconfigured recipe.
Transaction guards cover synchronous callbacks to prevent reentrant duplication.

Persistent playthrough state survives chunk/presenter recreation, ship travel
and panel closure. Fresh playthroughs reset it; disk saves are not implemented.
Fabricators explicitly stay **Inactive**, with **Production not yet available**.
There is no progress display, output collection, consumption or manufacturing.
**Craft a Ferrite Plate.** remains incomplete; narrative content is unchanged.

`tests/fabricator_deployment_test.gd` adds standalone regression coverage for
placement identity/sequencing, overlap rejection, configuration, range, capacity,
reentry, recovery failure/conservation, redeployment reset, stale UI, presenter
recreation and world detach/revisit. A synthetic two-ingredient fixture exercises
independent capacities and atomic failure of a later ingredient. The rack test
now expects deployable Equipment. All tests remain **unexecuted** under the Godot
restriction. Fixtures do not establish actual mouse routing, streaming or hatch
travel; the PR provides an owner manual checklist.

Validation is static only: standalone gdtoolkit 4.5 grammar parsing, scene and
resource references, SVG XML, protected-source/UID comparisons, Markdown links
and Git diff checks. No Godot, project code, imports, headless, graphical or
performance execution was performed. Engine type checking, gameplay and visual
layout remain unverified.


The UI lifecycle amendment keeps configured Fabricator input controls continuously
visible across ordinary refreshes, rather than hiding/showing their parent each
frame. Regression assertions count visibility notifications across repeated
refreshes, check transfer eligibility after selection/reopening, hide controls
for unconfigured machines and check Extractor/Smelter section transitions.
These assertions remain unexecuted. Direct transaction calls do not establish
physical button behavior: owner playtesting must verify mouse-down, a hold across
multiple frames and mouse-up, then a 25-ingot transfer (20 stored, 5 retained).
The reported failure's runtime cause remains unconfirmed; no inventory, recipe,
range, production or recovery logic was changed by this amendment.


The output-label presentation amendment uses **Output** for empty production
buffers and **Output - material name** when nonempty (rendered with an em dash),
with quantity/capacity on the next line. Both Smelter and Extractor use the
configured output item name. Collection refreshes the heading when the buffer
empties. Fabricator output controls remain hidden. Added regression assertions
cover empty/nonempty/collected output, Extractor quantities and unchanged input
headings; these assertions are unexecuted under the Godot restriction.
The owner reports all ten prior functional playtests, including the Transfer All
lifecycle retest, passed before this label amendment. This amendment still needs
the owner's focused UI retest; agent validation remains static only.


## Switch deployed Fabricator recipes (PR #44, merged)

Implements the owner-approved recipe-switching decisions for
[issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37).
The issue's original design-needed status predates this specification; keep it
open until owner acceptance and merge. At PR #44, manufacturing remained deferred
and **Craft a Ferrite Plate.** stayed current; the production feature below extends it.

Configured Fabricators offer **Change Recipe** in the shared machine panel.
It reuses the Plate/Rod icon cards, marks the active recipe **Current**, and shows
**Back**, a subtle **Production Paused** label and cause-aware inline failures.
Selecting Current or Back returns to inspection unchanged; Esc closes the whole
panel. Different recipes apply immediately in the same open panel. Failure
retains the chooser and pause. Errors clear on success or exit. Initial placement
selection has no Back or pause and retains its one-time range exception; switching
always uses ordinary inspection range. No materials load automatically.

`PlanetWorldState.change_recipe()` validates the machine, both recipes and stored
input integrity, and returns a small `RecipeChangeResult` enum for UI feedback.
It retains compatible material IDs, stages all incompatible returns using the old
recipe's item definitions and `InventoryState.add_items(..., false)`, then commits
the recipe, retained inputs and zero incomplete progress before signals. Reentrant
machine mutations are rejected throughout notifications. Same-recipe selection is
a no-op. Failures preserve inventory, recipe, inputs, progress and completed output.
Plate <-> Rod keeps exactly the stored Ingots; no return is necessary today.

The panel acquires an instance-specific transient pause lease through
`begin_recipe_change()`, releases it through `end_recipe_change()`, and clears it
on Current, success, Back, Close/Esc, range exit, transitions, inventory/tools,
other responses, target replacement and panel teardown. Recovery clears the
removed machine's lease immediately; stale target callbacks close safely. Only
the matching lease can release its pause. Transfer is blocked during change mode.
`advance_production()` explicitly skips paused instances; future recipe production
must retain that gate. Opening/cancelling does not reset progress. Pauses never
enter machine snapshots and a fresh playthrough starts without them.

Recipe switching leaves completed-output fields untouched. Future manufacturing
must store product identity independently from recipe identity, preserve completed
products, and block new production while incompatible old output awaits collection.
This PR adds no Fabricator production, collection, timers, progress display or fake
products. Existing Extractor/Smelter production and scalar storage are retained.

Recipe cards rebuild only on entering a panel or change mode, never each frame.
Input, recipe summary and chooser controls receive their desired visibility once
per refresh, preserving the Transfer All lifecycle correction from PR #43.

Added `tests/fabricator_recipe_switching_test.gd` covers starter switches, exact
retention, same-recipe no-op, progress reset, storage rejection, snapshot isolation,
synthetic two-input retention/returns, later-item rollback, committed-state signal
observation, reentry guards, pause ownership and removal. Extended
`tests/fabricator_deployment_test.gd` covers switching controls/cards, Back/Esc,
inline errors, stable visibility, transfer after switching, range/interruption,
target replacement, teardown and recovery, plus existing objective and shared-panel
regressions. **Both scripts remain added/updated but unexecuted.** Synthetic fixtures
seed progress and output solely to test data preservation; they are not gameplay
or player-facing acceptance.

Static validation: standalone gdtoolkit 4.5 grammar parsing of the five affected
scripts, scene/resource paths and node/signal wiring, local Markdown links,
protected-file hashes and Git whitespace/scope checks. No Godot, project scripts,
imports, headless, graphical or performance tests were executed. Engine type
checking, real button interaction and layout remain unverified.

### Owner recipe-switching acceptance

Execute only after explicit owner authorization for graphical execution, **one
test at a time**, recording PASS/FAIL and optional observations before continuing.
Use a fresh playthrough with the existing Fabricator recovery progression.

1. Initial placement still opens both recipe cards. Select one; initial selection
   has no Back or Production Paused. Closing unconfigured and reopening still works.
2. Configured Fabricator inspection shows Change Recipe; open it with an ordinary
   mouse press, hold across several frames and release.
3. Both cards show correct icons, names, inputs and outputs. Current is marked.
   Hold/release a card normally; buttons remain usable across refreshes.
4. Select Current with loaded Ingots: return to the same inspection unchanged.
5. Back returns unchanged; open again and Esc closes the entire panel. Neither
   cancellation changes the recipe or stored materials.
6. With 15 Ingots loaded, switch Plate -> Rod -> Plate without recovery. Each
   change keeps exactly 15 Ingots in the same deployed Fabricator.
7. Production Paused appears subtly only while changing recipes. It does not
   prove live manufacturing pause, because manufacturing is not implemented.
8. Walk out of inspection range or travel through the hatch while the chooser is
   open. It closes safely; return and confirm configuration/materials persist.
9. After switching, hold/release Transfer All with 25 Ingots and an empty input:
   20 load and 5 remain. Existing partial buffers fill only to the 20-unit limit.
10. Recover and redeploy: inputs and equipment return once; new deployment starts
    unconfigured as before. Guidance remains Craft a Ferrite Plate.
11. Check Extractor/Smelter production, transfers, collection and recovery. Empty
    input/output headings remain generic; switching controls never appear there.

Defer player-facing tests for incompatible returns, two-material recipes, live
pause/resume, nonzero live production progress and completed Fabricator output.
Both available recipes use only Ferrite Ingots and manufacturing does not exist.
Synthetic regression fixtures do not satisfy these future gameplay checks.


## Fabricator production (PR #45, merged)

Configured, supplied Fabricators automatically turn 1 Ferrite Ingot into 1 Ferrite
Plate or 2 Ferrite Rods every **3 seconds**, configured in `RecipeDefinition` and
both recipe resources. There is no Start/Stop/Craft control. Each accepted input
still holds 20 units; the machine definition sets one shared 20-item output buffer.
No power, logistics, new recipes, disk saving or further Computer repair is added.
This extends [recipe switching](#switch-deployed-fabricator-recipes-pr-44-merged)
and its completed-output safeguard from [issue #37](https://github.com/interneth3ro/the-long-way-home/issues/37).
Dedicated testing infrastructure in [issue #41](https://github.com/interneth3ro/the-long-way-home/issues/41)
remains separate.

`PlanetWorldState.advance_production()` owns a focused recipe-machine path. It
bounds affordable cycles by every ingredient and whole output batches, consumes
all inputs at completion and creates the corresponding output before notifying.
Its transaction guard rejects synchronous machine reentry. Fractional work survives
missing inputs, insufficient output space, incompatible completed output and the
existing instance-specific chooser pause. Blocked elapsed time earns no backlog.
Large deltas perform bounded arithmetic per ingredient, without a per-cycle loop;
cycle boundaries follow the existing fixed-machine clamp convention.

Fabricator records add only `output_item_id`; fixed Extractor/Smelter scalar
buffers and timing stay in place. Nonempty output resolves through the machine's
recipe product definitions, independently of its selected recipe. Empty output
has zero quantity and empty identity. Different recipe selection resets only
incomplete progress. Plates left after selecting Rod block manufacture until
collected. Invalid output records stop production and reject collection/recovery
without deleting the record or relabeling items. Snapshots deep-copy buffer data.

The shared panel shows Producing, Input Empty, Output Full or Inactive and the
existing progress bar. Output names the actual stored product; after Collect All
it immediately returns to `Output` and `0 / 20`. Interactive sections retain stable
visibility across repeated refreshes. Collection enforces normal interaction range
and input priority, returns all stored products atomically, then clears quantity
and identity without changing inputs, recipe or partial work. Recovery stages one
packaged machine, every stored ingredient and the stored product in one inventory
transaction. Any failed insertion leaves all state unchanged. Redeployment starts
unconfigured with empty storage and zero work. Existing chooser controls, leases,
Current/Back/Esc and interruption cleanup remain in place.

`PlaythroughState.ferrite_plate_acquired` is an idempotent session milestone,
observed through the established successful inventory-change acquisition path.
Manufacturing alone cannot set it; successful Collect All, or recovery returning
completed Plates into Materials, can. Spending Plates never clears it. Main clears
the completed Craft a Ferrite Plate guidance without completing the overarching
`restore_computer` objective, which remains active/incomplete. There is no next
objective, dialogue, musing or transition.

Added `tests/fabricator_production_test.gd` covers recipe durations, boundaries,
partial/large deltas, whole batches, shortage/blockage backlog, pause, typed output,
snapshot isolation, both switching directions, collection/recovery rollback,
invalid identities, exact-once acquisition, notifications/reentry, isolated
multi-ingredient/nonbinary-duration fixtures and fixed-machine regressions.
Extended deployment and switching regressions cover active presentation, stable
output controls, live chooser pause, stored-product labels/collection and updated
recovery invariants. **All regression scripts remain unexecuted.** Static grammar,
resource/scene text and Git checks do not establish Godot type checking, runtime
behavior, layout or mouse interaction. No Godot, imports, project code, headless,
graphical or performance execution was performed. Owner acceptance is outstanding.

### Owner production acceptance

The owner performs **one test at a time**, reporting PASS/FAIL and observations
before the next. Stop and investigate any failure before proposing an amendment.
Agent graphical execution still requires separate explicit owner authorization.

1. **Configuration regression:** Deploy/configure Plate Fabricator and load Ingots;
   controls work.
2. **Plate manufacturing:** A 3-second automatic cycle creates one Plate and consumes
   one Ingot at completion.
3. **Collect All:** Collect Plates; stored quantity and generic empty label update.
4. **Milestone timing:** Manufacture alone leaves Craft a Ferrite Plate incomplete;
   collecting completes it. Restore Computer stays incomplete; no new guidance/dialogue.
5. **Rod manufacturing:** Switch to Rod; each 3-second cycle consumes one Ingot and
   produces two Rods; collect Rods.
6. **Output capacity:** Verify the 20-item limit, no partial two-Rod batch or overflow,
   and resumption after collection.
7. **Stored output across switching:** Produce Plates, switch to Rod, verify Plates
   remain collectible and block Rod production; collect Plates and observe Rod resumption.
8. **Pause and progress:** Open Change Recipe during a partial cycle; progress holds.
   Back/Current/Esc resume without reset; selecting a different recipe resets progress.
9. **Input/output blockage:** Where naturally reproducible, verify progress retention
   and no backlog while blocked.
10. **Recovery/redeployment:** Recover stored inputs and completed products; verify
    conservation and a fresh unconfigured redeployment.
11. **Extractor/Smelter regression:** Production, transfer, collection, recovery,
    statuses and generic empty labels remain correct.

Synthetic code fixtures are not owner playtesting. Do not add gameplay recipes for
multi-ingredient tests. Cases unavailable in ordinary gameplay (including a
19-Rod buffer with the current two-Rod batches) remain deferred/not manually verified,
even with regression code. No merge or post-merge cleanup is authorized here.
