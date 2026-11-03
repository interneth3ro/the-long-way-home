# Ferrite Milestone 2: deterministic region data

Owner-accepted local-development milestone, pending final documentation review
and merge. Runtime acceptance is recorded below for reviewed commit `366378a`.
Uses the ten
accepted variants from merged PR #125's [catalog](FERRITE_SHAPE_CATALOG_V1.md).
Procedural deposits have data and lookup; they have no production artwork nodes,
discovery interactions or highlights yet. The introductory deposit, progression,
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
| `get_deposits()` | Existing authored-only list; no generated enumeration. Current highlights retain their existing scope. |
| `get_deposit(id)` | Authored identity first, then strict current-seed/version generated reconstruction. Unknown, rejected or noncanonical IDs return null. |
| `deposit_at(point, type)` | Authored membership first, then bounded generated Ferrite lookup and logical polygon membership; independent of exterior/chunk existence. |
| `get_deposit_region(owner)` | Immutable generated descriptors for this canonical owner only, including its cross-boundary deposits. Lazy preparation hook. |
| `query_deposit_descriptors(area)` | Generated-only broad phase: illustrated envelopes intersecting the inclusive area, row-major owner then slot order. |
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

No per-frame enumeration or preparation is added. Milestone 3 should use spatial
queries for highlights rather than multiplying all explored deposits by loaded
chunks. Coordinates retain Godot's finite Vector2/Vector2i representation; lazy
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
Catalog variety remains ten. Presentation/highlights, visual retirement,
preloading/loading screens, world maps and distance-based size progression remain
deferred.

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
