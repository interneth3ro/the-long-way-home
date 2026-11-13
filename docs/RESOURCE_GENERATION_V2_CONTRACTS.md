# Resource Generation v2 foundation contracts

Merged in PR #187. This foundation follows the owner-supplied November 11 design specification
(Decisions 1–6C) and subsequent approved Decisions 7A–7C: fixed anchors with later
placement assistance, controlled starting-area transition, and separate technical
and gameplay activation. The original implementation brief authorizes this scoped
work; the specification's planning boundary does not itself authorize execution.

The foundation supplies inert data interfaces only. No v2 generator, presenter, activation
switch, mining integration, inventory item, recipe, or persistence integration is
implemented. The existing Ferrite system and Cuprite visual prototype remain intact.

The separately scoped [ordinary-world generator](RESOURCE_GENERATION_V2_GENERATOR.md)
merged in PR #188. PR 3's [starting reservations and migration safeguards](RESOURCE_GENERATION_V2_STARTING.md)
merged in PR #189.
Both consume these unchanged interfaces without activating resources in gameplay.
PR 4's [shared presentation consumer](RESOURCE_GENERATION_V2_PRESENTATION.md)
and disabled standalone Cuprite inspection merged in PR #190. PR 5 adds
[isolated extractor anchor targeting and occupancy](RESOURCE_GENERATION_V2_PLACEMENT.md),
merged in PR #191. Milestone 6's [world-state integration](RESOURCE_GENERATION_V2_INTEGRATION.md)
is pending owner review and merge: separate token-checked v2 queries preserve
legacy Ferrite APIs. Foundation interfaces remain unchanged and no gameplay
activation is introduced.

## Native resource definition

[`WorldResourceDefinition`](../scenes/world/world_resource_definition.gd) extends
Godot `Resource` for native `.tres` authoring. It is separate from `ItemDefinition`,
`MachineDefinition`, and the legacy polygon-based `ResourceDeposit`.

| Field | Contract |
| --- | --- |
| `resource_id` | Nonempty canonical lowercase ASCII token `[a-z0-9_-]+`, held as `StringName`. |
| `abundance_weight` | Finite positive relative weight. Default zero is deliberately invalid/unconfigured. No production ratio is selected. |
| `geological_preferences` | Dictionary of caller-supported geology tokens to finite positive numeric preference weights. Empty means no configured preference. No sampling or hard geology gates. |
| `allowed_environments` | Unique caller-supported environment tokens; empty means no allowed-only restriction. |
| `restricted_environments` | Unique caller-supported environment tokens; must not intersect the allowed list. |
| `presentation_catalog` | Optional canonical `res://` reference ending in `.tres` or `.json`; no empty/dot/parent path components. Not loaded or interpreted here. |
| `anchor_cells` | Exactly `Vector2i(4, 4)` construction cells: 128×128 world units on the current 32-unit construction grid. |

`validation_error(supported_geology, supported_environments)` returns the first
actionable error, or an empty string. `definitions_error` validates an entire
nonempty list, rejecting null entries and duplicate resource IDs. These calls are
explicit admission checks: loading or editing a Resource does not validate it
automatically. A future generator must call them before consuming configuration.

The supported vocabularies are explicit call arguments. Empty vocabularies admit
only empty geology/environment configuration. This defines no new geology or biome
system, category names, or tuning. Future policy owners must supply stable supported
names and interpret preferences/restrictions. Syntax validation does not prove that
a referenced catalog exists or is compatible with a future presenter.

The [Cuprite `.tres` fixture](../tests/fixtures/resource_generation_v2/cuprite.tres)
is synthetic test data with neutral weight 1; it is not production tuning or
Cuprite activation. No production resource definitions are registered in this PR.

## Descriptor construction and ownership

[`ResourceGenerationDescriptors`](../scenes/world/resource_generation_descriptors.gd)
is a pure helper for complete location Dictionaries. `create_location` takes a
policy token, signed 64-bit world seed, `Vector2i` owner, nonnegative integer slot,
resource ID, 1–3 caller-supplied `Rect2i` anchors, and optional per-member presentation
Dictionaries. It returns either `{"ok": true, "location": ...}` or
`{"ok": false, "error": ...}`; failures never publish a partial group.

Every member has the same resource type. Array order is the stable member index;
the entire member array is the group membership, with no redundant group-size or
group-ID field. The location ID is also its group identity. An owner is supplied
by the future generator, never inferred from an anchor or artwork. Members may
cross owner boundaries. The foundation itself sets no region dimensions. The owner
locked the Decision 5E correction for the ordinary generator: **1,536 world units =
24 terrain cells at 64 units = 48 construction cells at 32 units**. The
specification's 48-terrain-cell equivalence is superseded; v2 uses no 3,072-unit region.

`location_error(data)` validates structural consistency without requiring a resource
catalog. `configured_location_error(data, definitions, supported_geology,
supported_environments)` additionally validates the definition set and rejects
unconfigured resource types. Future consumers must use configured admission before
generation/simulation use; structural validity alone does not activate a resource.

## Serialization: native Variant schema 1

The serialization representation is a native Godot Variant Dictionary, preserving
signed 64-bit integers, `Vector2i`, and `Rect2i` exactly. It is not JSON, a file
format, a save schema, or permission to use object deserialization. No encoder,
decoder, disk I/O, or save-codec changes are provided. A future persistence adapter
requires separate design; JSON number coercion would lose this contract.

Location Dictionaries require exactly these String keys:

| Key | Native Variant value |
| --- | --- |
| `schema_version` | Integer `1`; separate from generation-policy version. |
| `generation_policy` | Nonempty canonical String token, e.g. `v2`; chosen by caller. |
| `world_seed` | Signed 64-bit integer, including negative values. |
| `owner_region` | `Vector2i`, including negative coordinates. |
| `location_slot` | Nonnegative signed 64-bit integer. No slot budget chosen here. |
| `location_id` | Canonical String derived from the four identity inputs above. |
| `resource_type` | Canonical String resource token, compatible with existing `ferrite` spelling. |
| `deposits` | Complete ordered Array of 1–3 member Dictionaries. |

Member Dictionaries require exactly these String keys:

| Key | Native Variant value |
| --- | --- |
| `deposit_id` | Canonical String derived from parent identity inputs plus index. |
| `location_id` | Exact parent ID. |
| `member_index` | Integer equal to its zero-based position in the member array. |
| `resource_type` | Exact parent resource String. |
| `anchor_cells` | `Rect2i` with top-left construction-cell coordinates and size `(4,4)`. |
| `presentation` | Separate Dictionary, empty or containing optional String `catalog_ref` and/or canonical String token `variant_id`. Unknown keys and non-String values are rejected. |

All anchors use construction-cell coordinates, not terrain cells or world units.
Thus `Rect2i(-9,3,4,4)` is aligned: origins need not be multiples of four.
Floating-point rectangles are rejected, not rounded. Anchor ends must fit signed
32-bit cell coordinates, checked using 64-bit arithmetic before intersection.
Member anchors cannot overlap; edge contact is structurally accepted. Actual
within-group gaps, conservative visual clearance, authored protection, and
cross-location spacing remain later generation-policy checks.

Construction deep-copies presentation metadata. Returned Dictionaries are editable
values, not immutable snapshots; consumers must revalidate after edits or decoding.
No scene, Resource, texture, or authoritative placement value belongs in presentation.

## Identity strings

Exact formats, with ordinary signed decimal integers and no leading zero padding:

```text
resource-location:<policy>:<seed>:<owner_x>:<owner_y>:<slot>
resource:<policy>:<seed>:<owner_x>:<owner_y>:<slot>:<member_index>
```

For policy `v2`, seed `-9223372036854775807`, owner `(-2,-3)`, slot `7`, member `0`:

```text
resource-location:v2:-9223372036854775807:-2:-3:7
resource:v2:-9223372036854775807:-2:-3:7:0
```

Policy tokens cannot contain `:`. Resource type, anchors, presentation choices,
activation phase, and terrain chunks are excluded from identity. Locations use
their own prefix and omit the member index; deposit identities include it.
Changing generation semantics requires a new generation-policy version. This
contract does not establish deterministic procedural generation or saved-world
migration compatibility.

## Validation and preservation boundary

[Static tests](../tests/static_resource_generation_v2_test.py) inspect field and
validation contracts, exact identity formatting vectors, test-fixture wiring,
absence of I/O/generation dependencies, and preservation against baseline
`8430aacafa1e1cb08db1d7a5451d1ace66040e15` (merged PR #186).

[Pure-data GDScript assertions](../tests/resource_generation_v2_contract_test.gd)
cover definition failures, optional vocabulary admission, single/pair/triple
membership, negative coordinates, identity independence, malformed relationships,
overlap/overflow, and metadata isolation. They are authored but **not executed**:
no allowlisted runner dispatches them. Static checks do not establish Godot parser,
engine, headless runtime, graphical, mining, or generator-determinism PASS. This PR
changes no runner inventory, authorization, or safety control.

No existing Ferrite generation, `ResourceDeposit` caller, authoritative simulation,
machine definition, resource/item configuration, artwork, scene, save, or historical
evidence is modified. No new deposit becomes visible or mineable. Legacy Ferrite
migration and Cuprite/Carbite gameplay activation remain deferred. Starting
reservations and sampling are documented in their later milestones above;
PR 5 supplies inert snapping/occupancy contracts pending review. No default
resource ratio, geological category, spacing, density,
visual-envelope size, slot count, halo, or search budget is assumed here.
The ordinary generator's provisional policy values are recorded separately in its
[tuning register](RESOURCE_GENERATION_V2_GENERATOR.md#provisional-tuning-register).
