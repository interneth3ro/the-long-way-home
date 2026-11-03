# Ferrite Milestone 2: deterministic region data

Owner-accepted local-development Milestone 2 merged in PR #126.
Runtime acceptance is recorded below for reviewed commit `366378a`.
Uses the ten
accepted variants from merged PR #125's [catalog](FERRITE_SHAPE_CATALOG_V1.md).
Milestone 3A presentation/highlighting merged in PR #127 with owner
graphical/gameplay acceptance (8/8 PASS). Milestone 3B hybrid preparation is
implemented on the feature branch, pending merge and owner acceptance; see below.
Generated deposits have no discovery interactions. The introductory deposit, progression,
machine calculations and terrain generation remain unchanged.

## Ownership and reconstruction

[PlanetWorldState](../scenes/world/planet_world_state.gd) owns one
[FerriteRegionGenerator](../scenes/world/ferrite_region_generator.gd) per session.
The helper reads geometry JSON once and computes deposits without loading images,
instantiating scenes or consuming global RNG. The session seed is fixed at
construction. Terrain chunks and exterior nodes own no resource data. Persistent
machine production uses its existing designated extraction-point query indoors
and outdoors. No depletion, quantity, yield variation or machine algorithm is added.

Regions are 48×48 terrain cells (3,072×3,072 world units). Coordinates use floor
division, X east and Y south: world `(-1,-1)` belongs to region `(-1,-1)`.
Origins lie at integer 64-unit terrain cells inside their owner region. Geometry
may cross chunk/region boundaries without changing ownership or identity.

Generation `v1`, size policy `size_v1` and catalog `faceted_ferrite_catalog_v1`
are separate version identities. IDs are
`ferrite:v1:<signed_seed>:<signed_region_x>:<signed_region_y>:<slot>`.
The seed scopes IDs to world generation; sessions with the same seed intentionally
reconstruct the same IDs. A future save/world namespace may distinguish sessions
externally. Slots 0–5 exist before eligibility or rejection; survivors are never
renumbered. The authored `crash_site_ferrite` ID cannot collide with this namespace.

Channels hash UTF-8 text `v1:<seed>:<region_x>:<region_y>:<slot>:<channel>` with
SHA-256, reading the first seven hex digits as a nonnegative integer. Modulo
selects finite ranges with negligible integer modulo bias, not exact frequencies.
Channels are `richness` (slot -1), `position_x`, `position_y`, `size_v1`, `shape`,
`variant` and `priority`. Priority ties use lexical full-ID order. Variant choice
uses sorted explicit IDs, independent of catalog array order.

A future save must retain seed, generation-policy version, size-policy version
and catalog identity. These identify the fixed configuration. Changes to channels,
placement, protection, weights, spacing or identity require a new generation
version or explicit migration; never silently reinterpret saved worlds under
changed `v1` rules. Released catalog geometry, masks, registration and IDs must
remain reconstructible. No save format or migration system is added here.

## Catalog initialization and failure handling

The focused PR #126 correction hardens the startup dependency without changing
generation policy. Godot 4.7 supports FileAccess text reads and JSON parsing;
an expected JSON object becomes a Dictionary, arrays remain Arrays and JSON
numbers may be floats. The original typed assignment from `JSON.parse_string()`
was valid only for the expected object. A failed parse returns null, and other
top-level JSON types do not satisfy that assignment. Missing/wrong fields could
also fail later indexing or selection. Debug assertions did not safely handle
these failures and are omitted from release builds. See the official
[JSON API](https://docs.godotengine.org/en/4.7/classes/class_json.html),
[FileAccess API](https://docs.godotengine.org/en/stable/classes/class_fileaccess.html)
and [assert reference](https://docs.godotengine.org/en/4.7/classes/class_%40gdscript.html).

Initialization now explicitly opens/reads/closes the file, checks I/O status and
empty content, and uses `JSON.parse()` with line/error diagnostics. Before typed
assignment it checks the top-level object and catalog version, then the ten-entry
collection, unique nonempty IDs, known size/family strings, coverage of all three
sizes, finite integral dimensions/reach, fixed scale/registration, matching padded
image dimensions, and numeric grid-aligned polygon vertices within logical bounds.
Only consumed fields are checked; mask topology/artwork admission stays with the
existing offline catalog compiler and tests. This is not a replacement authoring
validator or a test of Godot's JSON parser through Python.

Both variant collections publish only after complete validation and protection
setup. Valid numeric values and polygon ordering are retained without conversion;
selection, hashes, identities, geometry and tuning stay unchanged. There is no
retry or alternate catalog. `FerriteRegionGenerator.is_ready()` and
`initialization_error()` expose status. A failure logs the exact catalog path and
reason with a correction/restart instruction. Region, ID, area and resource
reconstruction cannot consume failed/unpublished state. Empty results on those
paths do not mean successful generation: readiness remains false and the error
remains available. Existing authored-only access is retained for inspection.

World state forwards status through `is_resource_generation_ready()` and
`resource_generation_error()`. Deployment is rejected, machine status is inactive,
and production does not advance when the generator is unavailable. Successful
production rules/calculations are unchanged. Main checks readiness before session
transition initialization, logs a startup-blocked error and pauses the scene tree.
The V2 override returns after the parent check before accessing the current world
or preparing arrival. Thus there is no playable authored-only fallback. Existing
arrival hooks do not return a general initialization result; blocking at startup
avoids adding a loading/error framework or changing transition behavior. Recovery
requires correcting the input/package and restarting; there is no new error UI.

The raw FileAccess input is
`res://assets/environment/exterior/ferrite/catalog_v1/catalog.json`.
No `export_presets.cfg` or catalog `.json.import`/Keep override is present in the
reviewed checkout, and `project.godot` supplies no raw-catalog export inclusion.
The raw FileAccess path is not automatically a ResourceLoader dependency merely
because a script names it. Exported availability is therefore **not established**.
**Before the first exported-build acceptance, ensure the Ferrite catalog JSON is
included in every applicable export preset and verify successful catalog
initialization in an actual exported build.** This is a deferred export-readiness
requirement, not a blocker for the accepted local-development milestone.
The owner should approve adding the exact non-resource include
filter `assets/environment/exterior/ferrite/catalog_v1/catalog.json` to each
applicable export preset, then verify its raw availability and successful startup
in the actual export. Godot documents non-resource JSON inclusion in its
[export resource options](https://docs.godotengine.org/en/4.7/tutorials/export/exporting_projects.html#resource-options).
No export setting, import metadata, dependency or artwork was changed here.
Missing packaged input will block startup with an actionable error rather than
silently changing procedural results. The owner has confirmed successful local
Godot parsing/startup in the acceptance below. Injected initialization failures,
release failure handling, scene-tree pause behavior on failure and export
packaging remain unverified and require separately authorized engine execution.

## Initial tuning and bounded conflict policy

These are conservative, provisional **engineering defaults**, not owner-approved
numeric abundance targets or measured density/performance results. They remain
subject to future distribution and performance tuning:

| Parameter | Initial value and purpose |
| --- | --- |
| Rich-region selection | 20% channel threshold, independent of distance |
| Ordinary candidates | Slots 0–2 |
| Rich candidates | Slots 0–5, more opportunities without merging |
| Position | Uniform cell-origin samples inside canonical owner region |
| Logical reach | At most 12 cells east/south from origin, checked against catalog |
| Image registration | 32-unit padding on all sides; full image rectangle reserved |
| Visible separation | More than 128 units along at least one axis between image envelopes |
| Conflict neighborhood | Owner plus eight neighbors, halo 1 |
| Region computation | 54 raw slot evaluations on cache miss; at most 324 priority/envelope comparisons |
| Cache | 32 accepted region arrays, FIFO eviction; no ever-explored list |
| Area query | At most 64 owner regions including conservative lookup halo |

The maximum padded envelope is 832 units wide/high. Its reach plus spacing
cannot bridge the 3,072-unit separation to an owner two regions away, so a
one-region halo suffices. Candidate construction never requests accepted regions.
A candidate survives only if no eligible raw neighbor with a preceding
`(priority, ID)` overlaps its gap-expanded image rectangle. Even a neighbor that
loses elsewhere can suppress it. This nonrecursive local-minima policy is
query-order independent but may leave vacancies a greedy refill could occupy.
There are no retries or density guarantees. Rich regions offer twice as many
slots, not a guaranteed twofold accepted count; larger fields and crowded
neighborhoods may suffer more rejection. Later tuning needs owner-authorized
measurements if qualitative abundance needs adjustment.

Full image rectangles include logical polygons and every painted margin. The
unchanged authoritative [crash-site gameplay polygon](../scenes/world/crash_site_protection.gd)
is now shared with the exterior's default protection. Its enclosing rectangle
plus the gap excludes generated deposits around all protected gameplay space.
The introductory deposit's authoritative footprint is independently reserved with
its 32-unit artwork apron plus the gap. Whole-rectangle rejection includes boundary
touch and containment, avoiding concave intersection gaps; it intentionally
reserves extra ground near polygon corners. Authored terrain overlays are not
changed. Future scene overrides/moves of protection must reconcile simulation
protection and generation version.

## Selection and logical geometry

The isolated `size_v1` policy uses 10/50/40 small/medium/large thresholds and no
distance input. Shape selection renormalizes the approved 20/20/25/35 weights over
families available **within the chosen size**, then selects uniformly among sorted
IDs in that size/family. Small is solely rectangle; medium has all four families;
large lacks rectangle and uses 25% L, 31.25% stepped and 43.75% organic conditional
probabilities. With ideal independent size draws these happen to recover the
overall 20/20/25/35 family targets for this catalog. They are not per-size targets,
quotas or guarantees about realized worlds. Finite draws, modulo bias, protection
and conflict rejection alter realized proportions. All ten variants are available.
Distance-based large-deposit progression and catalog expansion remain deferred.

Descriptors contain seed, canonical owner/slot/ID, variant ID, terrain-cell origin,
three version identities, full illustrated envelope and priority. Descriptor
dictionaries and cached arrays are read-only; their fields are value types.
Each ResourceDeposit reconstruction translates the authoritative local polygon
by `origin_cell * 64`. Concave notches stay empty; no convex hull, mask rewrite,
clipping, union or resource merging occurs. Rendering metadata stays in descriptors.
Generated resources are fresh objects: caller edits cannot alter cached geometry
or future lookup. Compare `deposit_id`, not Resource object identity. Membership
still uses `Geometry2D.is_point_in_polygon` and the existing extraction-point rule.

## Lookup API

| World-state API | Semantics |
| --- | --- |
| `get_deposits()` | Existing authored-only list; no generated enumeration. Spatial presentation/highlights use bounded area APIs. |
| `get_deposit(id)` | Authored identity first, then strict current-seed/version generated reconstruction. Unknown, rejected or noncanonical IDs return null. |
| `deposit_at(point, type)` | Authored membership first, then bounded generated Ferrite lookup and logical polygon membership; independent of exterior/chunk existence. |
| `get_deposit_region(owner)` | Immutable generated descriptors for this canonical owner only, including its cross-boundary deposits. Lazy preparation hook. |
| `query_deposit_descriptors(area)` | Generated-only broad phase: illustrated envelopes intersecting the inclusive area, row-major owner then slot order. |
| `get_deposit_variant(variant_id)` | Deep copy of validated catalog metadata, or empty for unknown/unready input; forwards `FerriteRegionGenerator.variant_metadata`. No image loading in simulation. |
| `get_deposits_in_area(area)` | Authored resources whose footprint bounds intersect plus generated resources from the illustrated-envelope broad phase. Precise clipping/membership is the caller's responsibility. |

Areas must be finite, with nonnegative size; point rectangles are allowed. The
owner scan starts at `floor((area.position - (832,832))/3072)` and ends at
`floor((area.end + (64,64))/3072)`, inclusive. This covers origins left/north whose
artwork reaches forward and origins right/south whose padding reaches backward.
Each owner is queried once, avoiding duplicate IDs within a call. Invalid areas
return empty. Requests over 64 owners emit an error and return empty **in full**,
including the authored-resource API; callers must explicitly page larger requests.
The budget includes owner scans, not their temporary conflict halos; one query
performs at most 3,456 raw slot evaluations before cache reuse. Temporary neighbor
arrays never become persistent entries. Eviction discards only reconstructible
descriptors, never machines, discovery or exploration state.

Milestone 3A uses bounded spatial queries for artwork/highlights rather than
multiplying all explored deposits by loaded chunks. Coordinates retain Godot's
finite Vector2/Vector2i representation; lazy
unbounded-world generation does not provide arbitrary-precision coordinates.
Direct owner requests beyond ±44,739,240 return empty to avoid terrain-cell
integer overflow. Area queries also reject coordinates outside the corresponding
safe interior and reject huge extents before integer conversion/count products.
Floating-point precision still limits useful gameplay positions well before that
integer bound; no large-coordinate precision or floating-origin feature is claimed.

## Validation and deferred acceptance

`python -B -m unittest discover -s tests -p 'static_ferrite*test.py'` covers the
catalog, introductory integration and offline region specification oracle. The
oracle uses actual masks/polygons and shared protection inputs, with source
contracts binding arithmetic, channels and integration. Checks cover shuffled
region/query order, FIFO eviction/reconstruction, IDs, negative coordinates,
chunk/region/corner crossings, translated occupied/empty centers, full-envelope
exclusion, spacing, bounded work and family availability. Existing production,
discovery, extraction and terrain regressions run in the full static suite.
These are offline models and source inspection, **not GDScript execution**.
Initialization checks additionally model missing/empty/malformed input, wrong
top-level/version/types, missing consumed fields, duplicate IDs, size coverage,
registration and numeric constraints, plus source checks for atomic publication,
readiness guards and blocked startup. Python's parser is not a Godot parser test.

The agent ran no Godot editor, game, headless process, import, benchmark or
profiling. The owner's separate runtime smoke-test results are recorded below.
Exhaustive runtime determinism, reconstruction/cache behavior, boundary
membership, concave Geometry2D clipping, exported JSON availability and performance
benchmarks remain unverified. Further engine/graphical checks require explicit
owner authorization.
Catalog variety remains ten. Milestone 3A's presentation/highlight implementation
and final owner acceptance are described below. Deliberate preloading,
lookahead/loading behavior and performance optimization belong to 3B; loading
screens, world maps and distance-based size progression are not added here.

## Milestone 3A presentation and highlighting — feature branch, pending merge

This section records the accepted PR #127 implementation. Its synchronous query
and refresh mechanics are superseded by the pending 3B section below; the dated
owner acceptance remains historical evidence for 3A only.

[FerriteDepositPresenter](../scenes/world/ferrite_deposit_presenter.gd) is a small
disposable Node2D owned by the exterior. It queries generated descriptors only,
deduplicates stable IDs across pages, and keeps one uncentered Sprite2D per nearby
deposit. The authored introductory sprite/scene and discovery remain separate
and unchanged. No resource or machine state belongs to this helper.

The retention square is planet-local: `(center_chunk - radius) * 2048`, with side
`(2 * radius + 1) * 2048`, where radius is loading radius plus retention margin.
The helper's `refresh(state, area)` runs only after the existing neighborhood
center/revision gate, including arrival, rather than on every process frame.
Cached exterior reattachment retains the helper, sprites and shared textures.
The query includes a deposit whenever its **complete padded image rectangle**
intersects retention, including edge contact, even when its owner region or
terrain chunk is absent. Only departure of that full envelope retires its sprite;
returning reconstructs the same identity without changing simulation.

`query_areas(area)` divides that square into pages of at most 8,192 world units
per side (four chunks). At maximum exported settings (radius six), there are at
most 16 pages. Each page's owner lookup plus halo stays below the existing
64-owner query cap. Negative positions retain floor-based chunk/region semantics.
Queries enumerate nearby owners, never all previously explored deposits.

The existing validated catalog is the registration source; there is no second
variant map or JSON parser. Initialization now also rejects missing/noncanonical
`png_path` metadata. A sprite's planet-local canvas origin is
`origin_cell * 64 - logical_origin_source_pixels * display_scale`.
All accepted variants use `(64,64)` source registration and uniform 0.5 scale,
so the canvas begins 32 world units before the logical origin. The helper loads
a Texture2D only on first nearby use of its variant, validates image dimensions
and the descriptor envelope, and caches at most the ten shared catalog textures
for the exterior lifetime. It never composes, stretches, rotates, mirrors or
tints images. Layer order is terrain at −11/−10, Ferrite at −5, construction
highlights at −4, then Dave and deployed machines above.

Readiness errors propagate from the existing generator contract. Missing texture,
wrong dimensions, unknown variant or inconsistent registration returns an explicit
failure before node mutation. The exterior records the failure, logs the reason
and pauses the tree; correcting the input/package and restarting is required.
There is no alternate texture or playable authored-only fallback on failure.
The deferred **raw catalog JSON export inclusion and exported-build verification**
requirement above remains in force; 3A adds no export preset.

Construction refresh first clears old nodes, queries `get_deposits_in_area` through
the same retention pages, and deduplicates deposit IDs. Compatible deposits visit
only chunk coordinates overlapped by their logical footprint bounds, skipping
chunks absent from the retained terrain dictionary. Each loaded chunk rectangle
clips the **actual footprint** using all results from
[`Geometry2D.intersect_polygons`](https://docs.godotengine.org/en/stable/classes/class_geometry2d.html#class-geometry2d-method-intersect-polygons).
Concave notches are not filled with bounds/convex hulls; separate returned pieces
each receive a Polygon2D with the existing resource highlight color. Accepted
catalog masks have simple contours without holes. Construction-mode changes,
neighborhood retirement and chunk completion refresh/clear normally; no offscreen
highlight registry is retained. Point-based extraction and infinite uniform
resource production remain unchanged.

Focused offline checks now cover catalog PNG registration/integrity, bounded
paging and identity lifecycle, padded-envelope retention, signed boundaries,
mask-cell clipping coverage and a synthetic U-shaped multi-piece clipping
contract. These are Python models and source checks, **not execution of GDScript
or Geometry2D**. They do not establish Godot parsing/import, runtime clipping,
gameplay, appearance, memory use or performance. No Godot process was launched
by the agent. The owner's separate graphical/gameplay results are recorded below.

Region queries still compute synchronously on cache miss, and the first nearby
use of each texture loads synchronously. The bounded region FIFO can churn while
paging large retention areas; construction refresh can repeat nearby queries
while terrain completes. Shared textures remain cached after sprite retirement.
These costs and memory impact require later owner observation and 3B
hybrid preparation/lookahead/scheduling work. There is no stutter-free claim,
performance probe or loading-screen implementation in 3A. Known repeated silver
highlights/grain and regular concave rims remain nonblocking artistic limitations.

## Milestone 3B hybrid preparation — feature branch, pending merge

The owner authorized all four implementation slices with static-only agent
validation. **Godot NOT RUN / OWNER ACCEPTANCE PENDING.** The PR #127 observation
of modest initial-discovery stutter remains unexplained; no runtime improvement,
memory measurement or frame-time guarantee is claimed.

### Nearby snapshot and geometry reuse

`FerriteRegionGenerator.query_owners(area)` exposes the existing bounded owner
enumeration without generating regions. Existing `query()` uses that same helper.
The presenter pages the presentation area and its one-chunk lookahead, unions
owner coordinates before generation, and retains accepted immutable region arrays
only within the current lookahead owner set. Page overlap no longer repeats region
generation within a logical request. Overlapping completed owners survive movement;
terrain revision, world identity or seed changes invalidate the snapshot.

The reconstruction FIFO remains **32 regions** with unchanged eviction/generation
policy. The separate active working set is spatially bounded, not a history of
explored deposits: at maximum exported radius six, a 15x15-chunk lookahead covers
at most 144 owner regions including the asymmetric lookup reach. Each owner holds
at most six descriptors. Required/future descriptor lists and queues share this
bound. At default arrival the required union covers 36 owners, rather than 64
paged region visits. These are source-derived counts, not runtime measurements.

Stable IDs are deduplicated before footprint reconstruction. Construction reads
the presenter's exterior-only geometry view, with one cached resource per required
ID. Mining still reconstructs authoritative geometry independently through state.
Catalog metadata is copied privately once per encountered variant per world/seed;
the generator's mutable catalog collections never escape. At most ten shared
textures remain cached. No artwork/catalog/distribution inputs change.

### Arrival and exploration scheduling

`request(state, area)` replaces pending work and returns a generation token.
`step(state, token, required_only)` services one owner generation, descriptor
registration (possibly one synchronous texture load), or sprite registration per
call. Bounded snapshot assembly and final readiness publication are separate steps.
All required owners finish before required descriptor validation; all required
registrations validate before new sprites are created. Required work always
precedes speculative work. Only encountered variants whose complete illustrated
envelopes intersect the required area are loaded during arrival; the ten textures
are not eagerly preloaded.

`prepare_for_arrival()` drains required Ferrite work and the existing terrain queue,
yielding between iterations. The transition controller continues awaiting this
hook before restoring input. The first arrival uses the existing opaque fade;
later transition presentation rules remain unchanged. Once playable, `_process()`
services the queue even if the neighborhood center/revision gate returns early.
Lookahead extends exactly one chunk beyond presentation on every side and prepares
metadata and required textures, never speculative sprites. Owners sort by distance,
signed y/x coordinates; descriptor work sorts by stable ID. These orders do not
change deterministic deposit generation or conflict resolution.

The focused PR #128 safety correction makes preparation completion explicit:
the exterior returns a readiness receipt bound to its arrival generation,
Ferrite request, world state/seed/revision and player. The controller revalidates
that receipt after preparation, physics registration and reveal/fade waits, before
restoring input or reporting success. A failed/incomplete required arrival blocks
opaquely with input locked and an error, independently of whether tree pause
prevents an awaited callback from resuming. There is no authored-only fallback.
Legacy synchronous interior facing hooks still return void.

Quick cancellation before attachment returns to the ready source; cancellation
during preparation rolls back while opaque and re-prepares a cached exterior
source. Only successful source readiness permits unlocking; cancelled travel emits
no destination success. A real asset/terrain failure remains blocking even when
cancellation is requested. Controller generations bind deferred dispatch and all
await continuations to the accepted request; exterior generations reject old
preparations before they can clear a newer preparation's flags. A stale presenter
step ends preparation as incomplete rather than spinning indefinitely. These are
source contracts, not engine-verified cancellation/pause behavior.

New requests discard stale pending tasks. Tokens, world/seed/revision checks,
exterior detachment and explicit quick-transition cancellation prevent stale work
from registering sprites. Completed bounded region/texture data may survive cached
world reattachment. Sprites retire only when their full padded illustrated envelope
leaves the normal presentation area, with inclusive signed-boundary semantics.

Highlight requests from neighborhood changes, snapshot readiness and terrain batches
set a dirty flag; the exterior rebuilds once at the end of that frame's work when
the required snapshot is ready. Construction switching/cancellation clears existing
nodes immediately. Inactive construction performs no highlight deposit queries.
Actual concave polygon clipping, all returned pieces and loaded-chunk filtering
are preserved.

### Validation limits and owner comparison

Focused checks: `python -B -m unittest discover -s tests -p 'static_ferrite*test.py'`.
Transition safety: `python -B -m unittest discover -s tests -p 'static_transition_safety_test.py'`.
Full non-engine suite: `pwsh -NoProfile -File tools/run-local-tests.ps1 -Mode Static`.
The 3B tests compare membership with the accepted generation oracle, exercise
signed boundaries, work priority/draining, bounded owner retention, reversals and
cancelled/superseded schedules, and bind those models to source contracts. They
do not execute GDScript, ResourceLoader, Geometry2D or a renderer.

One region generation, texture load/upload, terrain chunk, snapshot assembly or
highlight rebuild may still block a frame. The one-unit cap is a work cap only.
Additional active descriptor/footprint memory and a potentially longer opaque
arrival wait are explicit tradeoffs. No threads, loading-screen UI, cache tuning,
export changes or simulation dependency on presentation are introduced.

Owner comparison uses accepted baseline `ca83742507dadd499d338eb2a07740692cb90573`
and the draft PR's exact candidate commit, on the same machine, renderer,
resolution, seed **26026** and recorded route. A fresh application session is not
necessarily a cold filesystem/GPU cache. Agent execution remains prohibited.

1. First arrival: record fade/preparation delay, complete nearby artwork, and no
   control before readiness; confirm normal input restoration.
2. Starter `(128,128)..(768,512)`: unchanged discovery, musing, objectives and story.
3. Approach unseen deposits: record stutter and late/missing artwork separately.
4. Cross positive/negative 2048-unit chunk and 3072-unit region boundaries and
   corners; reverse and revisit without shifting, duplicate or missing fields.
5. Check small table; medium crown/elbow/offset/slab/terraces; large
   basin/elbow/sprawl/stair. Unencountered variants remain **untested**.
6. Enter/switch/cancel construction: exact concave notches, empty decorative rims,
   multi-piece highlights and chunk-spanning placement.
7. Valid/invalid extraction points, mining, collection, recovery and multiple
   Extractors on a field retain behavior.
8. Leave machines producing offscreen, travel indoors and return; verify continued
   production and stable presentation.
9. Reenter in the same session: check fade/input/artwork/duplicates and cancellation
   where practical. Check early quick cancellation and rollback during preparation
   where reachable: source readiness must precede input restoration, with no
   destination completion/reveal progression. Any separately owner-controlled
   failed-preparation check must keep input locked and emit no success; static
   checks do not authorize fault injection or engine execution.
10. Stop on severe freezes or instability; do not deliberately reproduce them.

```text
Baseline/candidate commit | fresh session/return | seed | renderer/resolution
Route/coordinates | encountered variant | construction state | action
Stutter: none/slight/obvious/severe | late/missing artwork: yes/no
Arrival delay observation | gameplay result | other notes
```

Keep separate acceptance judgments for **stutter reduction**, **artwork appearing
on time**, and **arrival-transition cost**. Subjective reports are not quantitative
timing; only actual owner measurements support numeric performance claims.

### Original owner acceptance checklist — 3A

1. Open/run the project locally; confirm no parser, import, catalog or texture
   errors, and normal interior/exterior arrival and hatch return.
2. Confirm the introductory field at `(128,128)..(768,512)`, its artwork,
   discovery and guidance remain unchanged.
3. Explore nearby generated fields: varied approved shapes/sizes, correct half
   scale, shallow edges/terrain separation, no tint, stretching or duplicates.
   Confirm Dave and machines draw above Ferrite.
4. Enter Extractor construction: highlights follow concave logical footprints,
   leave empty notches unhighlighted and stop on cancellation. Check pieces on
   both sides of chunk edges; no decorative rim/shadow is highlighted.
5. Check valid/invalid extraction-point placement and multiple Extractors on
   one field. Verify output collection and recovery retain normal behavior.
6. Traverse positive/negative chunk boundaries, 3,072-unit region boundaries and
   their corners. Fields must stay whole until their entire image leaves
   retention, with no duplicate shadows, flashes or identity changes on return.
7. Leave/return repeatedly, including interior travel; check no missing/duplicate
   deposits and that production continues independently of sprite lifetime.
8. Observe ordinary movement and first encounters with each variant for new
   noticeable stutter. Record qualitative observations only; no formal benchmark
   or memory/performance acceptance is claimed by static PASS.

### Final PR #127 owner graphical/gameplay acceptance — 2026-11-02

The owner completed Godot graphical and gameplay testing of reviewed commit
`7a2dd6e448777f3dba4cd2d6195c6e1f67db7e2f` on 2026-11-02
(America/Chicago). **All eight acceptance checks PASSED; zero functional failures
reported. Owner graphical and gameplay acceptance: APPROVED.**

1. Godot startup, resource imports, exterior arrival and hatch return: PASS.
2. Introductory Ferrite artwork, discovery and progression preservation: PASS.
3. Generated Ferrite appearance, scale, variety and rendering layers: PASS.
4. Exact construction highlighting, including concave notches: PASS.
5. Extractor placement, production, collection and recovery: PASS.
6. Cross-chunk/region presentation, including negative coordinates: PASS.
7. Stable deposits across departure, return and indoor travel; production
   independent of sprite lifetime: PASS.
8. General stability without severe freezes or gameplay blockers: PASS.

**Accepted nonblocking performance observation — investigate in Milestone 3B.**
The owner observed slightly more noticeable stuttering during initial exterior
discovery than before PR #127. The increase was modest and did not prevent normal
gameplay. Milestone 3B must investigate this observation. Synchronous region
generation, first-use texture loading and repeated presentation/highlight queries
are potential contributors only: these are hypotheses, not established causes.
No performance optimization, measured performance or stutter-free operation has
been verified. Memory use and formal performance measurements remain unverified.

These owner-reported results are separate from the previously completed agent
static suite (**258/258 PASS**), focused Ferrite checks (**40/40 PASS**) and offline
PNG checks. They do not establish exhaustive clipping/determinism, injected
failure handling or exported-build compatibility. The deferred raw catalog JSON
packaging and exported-build verification requirement above remains in force.

This acceptance follow-up changes documentation only, preserving the reviewed
implementation, generation/distribution, artwork/catalog, mining calculations
and terrain. The agent did not launch Godot or run benchmarks. PR #127 is prepared
for owner review and a normal **merge commit** through GitHub; no automatic merge
is authorized or performed. Post-merge cleanup belongs in a separate conversation.

## Final owner runtime acceptance — 2026-11-02

The owner reports **6/6 acceptance checks PASS, zero failures** for reviewed
implementation `366378a5090d2fb4b34a1d9d28ab32430b948a04` on 2026-11-02
(America/Chicago). The owner accepts Milestone 2's deterministic region-generation
architecture and corrected catalog initialization behavior.

1. Godot project opens without GDScript parser errors.
2. Session startup succeeds without Ferrite catalog initialization errors.
3. Ship interior and exterior transitions work normally.
4. Introductory Ferrite and discovery remain functional.
5. Extractor placement and mining remain functional.
6. No obvious startup delay or gameplay stutter was observed.

These are owner-reported runtime results, separate from the previously completed
agent static suite (**246/246 PASS**), focused Ferrite checks (**28/28 PASS**) and
corrective code review (**PASS**). The acceptance documentation update preserves
the reviewed implementation and all generation policy values.

The absence of observed delay/stutter is a smoke-test observation, not a benchmark
or measured performance guarantee. This acceptance does not establish procedural
deposit graphical presentation, exhaustive runtime determinism or exported-build
compatibility. The export-readiness requirement above remains deferred; no export
preset is created or changed by this PR. Engineering defaults remain provisional.

PR #126 is prepared for owner review and a normal **merge commit** through GitHub.
No automatic merge is authorized. Post-merge cleanup belongs in the separate
cleanup conversation and is not part of this acceptance update.
