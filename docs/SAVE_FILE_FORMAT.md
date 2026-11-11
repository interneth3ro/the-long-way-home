# TLWH serialized save-file foundation

Milestone 5 foundation for issue [#165](https://github.com/interneth3ro/the-long-way-home/issues/165),
implemented on `codex/m5-sav-codec`, pending owner review and merge.
The supplied implementation approval M5-30–38 supersedes the earlier SQLite-first
investigation: that evaluation is closed. This module has no gameplay callers,
snapshot capture, SaveCoordinator, restoration, publication journal or save UI.
It introduces no database or extension dependency.

## Envelope version 1

All integers are **unsigned little endian**, with no alignment gaps. Offsets are
zero based. `M` and `P` below are byte lengths, excluding the header.

| Offset | Bytes | Meaning |
| --- | --- | --- |
| 0 | 8 | ASCII magic `TLWHSAV1` (`544c574853415631`) |
| 8 | 2 | Envelope version, exactly `1` |
| 10 | 2 | Compression method, exactly `0` = NONE |
| 12 | 4 | Metadata length `M` |
| 16 | 4 | Stored payload length `P`; also decoded byte length with NONE |
| 20 | 4 | Global snapshot version, exactly `1` |
| 24 | 32 | Raw SHA-256 digest, not hexadecimal text |
| 56 | M | One restricted Variant Dictionary: metadata |
| 56 + M | P | One restricted Variant Dictionary: snapshot |

The complete file length must equal `56 + M + P`; trailing data is invalid.
SHA-256 is calculated over the concatenation of bytes `[0,24)` and `[56,EOF)`.
The fixed digest field is **omitted**, not zero-filled. This covers all header
fields, metadata and stored payload. Basic framing, versions and safe lengths
are checked first, then integrity, then the restricted wire structure, then
native Variant decoding and recursive value validation. No section is returned
on failure, including metadata when payload validation fails.

SHA-256 detects corruption; it does not authenticate a save. An attacker can
recompute it. The strict structural preflight therefore applies even to files
with valid checksums. Unsupported envelope/global versions and compression fail
without migrations. Subsystem schema compatibility belongs to future callers.

## Metadata, snapshot and native Variant subset

Both sections use Godot's native `var_to_bytes` binary encoding; decoding uses
`bytes_to_var`, which does not enable full object reconstruction. The codec
never uses the object-enabled API. Both roots are Dictionaries. Metadata may be
empty; this foundation assigns no gameplay meaning or required metadata keys.
Future metadata schemas must be explicitly agreed before integration.

Values allowed recursively: null, Boolean, signed 64-bit integer, finite float,
String, Array and Dictionary. **Keys must be Strings** (not StringNames).
All other Variant types are rejected, including object IDs, objects, Nodes,
Resources, Callable, Signal, RID, vectors and packed arrays. Encoder input typed
collections are copied into untyped collections after checking their values.
Typed collection descriptors on disk are rejected before decoding: they can
carry class/script information and are unnecessary for storage-neutral data.

The native subset is explicitly constrained as follows, independently of any
future changes to the engine's broader serializer:

- Each value starts with a little-endian uint32 type header: 0=null, 1=bool,
  2=int, 3=float, 4=String, 27=Dictionary, 28=Array.
- All header bits outside these exact values are zero, except bit 16 may be set
  for int/float to select 64-bit rather than 32-bit storage.
- Null has no body. Bool has uint32 body 0 or 1. Integers have signed int32/int64
  bodies; floats have IEEE-754 binary32/binary64 bodies and must be finite.
- A String has a uint32 UTF-8 byte length, then those bytes and zero padding to
  a multiple of four bytes. Reject embedded NUL, invalid UTF-8, overlong forms,
  surrogate code points, values above U+10FFFF and nonzero padding.
- Untyped Array has a uint32 element count followed by values in sequence.
  Dictionary has a uint32 pair count followed by key/value pairs. No shared or
  typed collection flags are accepted. Keys on disk must be unique and strictly
  ascending under Godot String lexicographic (Unicode code point) comparison.
- Exactly one value consumes each section, with no trailing bytes.

Godot's [binary API documentation](https://docs.godotengine.org/en/stable/tutorials/io/binary_serialization_api.html)
describes the general representation but contains historical type IDs. This
contract and the runtime type-identity/layout fixtures lock the selected Godot 4
subset; do not derive current IDs from that older table. The encoder remains
native Godot, not a replacement Variant serializer.

The global version is in the header, independent of subsystem versions. A
synthetic payload may contain `{"sections": {"demo": {"version": 7, "data": []}}}`.
The codec preserves this data without interpreting or approving version 7. A
future subsystem must validate its own versions before restoration. There is no
approved production snapshot schema implemented here.

## Limits and deterministic encoding

| Limit | Value |
| --- | --- |
| Metadata bytes | 65,536 (64 KiB), minimum 8 |
| Stored payload bytes | 8,388,608 (8 MiB), minimum 8 |
| Complete file bytes | 8,454,200 (56 + metadata cap + payload cap) |
| Entries per collection | 4,096 array elements or dictionary pairs |
| Nesting depth | 32 edges from section root (root depth 0) |
| UTF-8 bytes per String, including keys | 65,536 |
| Total values per section | 65,536, counting root, containers, keys and values |

File size is checked before reading its buffer. Framing limits precede section
slicing. The wire scanner enforces lengths, types, UTF-8, counts, depth and total
values before native decoding. It allocates no collections from wire counts;
dictionary comparison holds only the previous/current bounded key. Recursion is
bounded at depth 32. The decoded value is checked and copied before exposure.

Encoder validation bounds work before calling the native serializer. It counts
an upper bound of 12 bytes per Boolean/int/float (some encode to 8), and exact
other value sizes. Consequently a numerically dense snapshot close to its byte
cap can be rejected even when its actual encoded size would fit. Decode applies
the same budget after the wire scan. These deliberately conservative limits are
foundation constraints, not promises of future whole-world capacity or a general
memory budget. Shared subcollections are expanded as values, counted each time;
cycles fail at the depth limit. No enormous fixture is needed to test counts or
declared length rejection.

Dictionary keys are sorted recursively, including metadata; arrays retain order.
Caller-owned values are never mutated. Negative floating zero is normalized to
positive zero. Typed and untyped input containers with equivalent supported
values encode identically. Determinism applies to the same Variant types/values
under the approved native encoding: int 1 and float 1.0 are different, Unicode
normalization is not applied, and timestamps/IDs are not generated. No guarantee
is made across future native encoding changes or engine versions. The reader
accepts both valid numeric widths; it does not promise byte-for-byte canonical
re-encoding of externally supplied numeric representations.

## API and failures

[`SaveFileCodec`](../persistence/save_file_codec.gd) is a standalone RefCounted
module with static methods; no autoload, scene or active session is required.

| Method | Success fields besides `ok: true` |
| --- | --- |
| `encode(snapshot: Dictionary, metadata: Dictionary = {})` | `bytes` |
| `validate_envelope(bytes)` | `metadata_size`, `payload_size` |
| `decode(bytes)` | `snapshot`, `metadata`, `snapshot_version` |
| `read_file(path)` | `bytes` |
| `write_file(path, bytes)` | none |

Every failure returns only `ok: false`, `error` (stable category String) and
`message` (diagnostic String). Categories are `snapshot`, `metadata`, `size`,
`hash`, `magic`, `format_version`, `compression`, `snapshot_version`, `length`,
`checksum`, `variant`, `read_open`, `read`, `write_open`, `write`. Defenses use
controlled results, not assertions. No gameplay state is accessed or changed.

`read_file` reads bounded raw bytes; it does not certify validity. Independently
reopen using `read_file`, then call `validate_envelope` for framing/integrity or
`decode` for complete format validation. Envelope-only success deliberately says
nothing about restricted payload validity or application-level schema.

`write_file` first fully decodes/validates bytes before opening the destination,
then reports open, buffer/flush and length errors. It creates no directories and
touches only the caller-selected destination. Opening a valid destination for
WRITE may truncate it; this is a low-level operation with **no overwrite policy,
atomic publication, rollback or guaranteed power-loss durability**. Flush does
not provide that guarantee. Future publication must choose a unique candidate,
independently reopen/validate it, and implement its separately approved journal.
The caller must avoid concurrent modifications while encoding/reading/writing;
the codec detects short reads and changed file length, not all same-size races.

## Validation and execution boundary

M5-39 Option A prepares a [dedicated isolated runner](SAVE_CODEC_RUNNER.md) on
`codex/m5-codec-runner-preparation`, dependent on this codec branch. Its execution
gate is inactive; runner preparation and static PASS grant no Godot permission.
The codec and runtime assertions are unchanged by that preparation.

[`save_file_codec_test.gd`](../tests/save_file_codec_test.gd) is an automated
standalone SceneTree suite of synthetic round trips, canonical ordering, fixed
layout, direct malformed envelopes, corruption, limits and isolated file I/O.
Fixture framing/hashing is independent of codec helpers. It tests object wire
rejection before native decode, never enables reconstruction or loads a resource.
The runtime suite creates only a unique test-owned `user://codec-synthetic-*`
directory, a candidate and a sentinel, and removes those exact fixture files on
normal completion. No saves, active playthroughs or gameplay scenes are used.

The Python `static_save_file_codec_test.py` suite independently checks the binary
specification vectors and source safety/API boundaries. It does not execute
GDScript or establish engine parse/runtime success.

The existing local runner remains unchanged. Its standing Native permission is
for recipe-switching only and **does not dispatch this codec suite**. No engine
run, metadata smoke, graphical check or benchmark is implied by static PASS.
Before codec runtime execution, the owner must review and approve a narrow
runner activation amendment specifying:

1. Exact tracked codec/test inputs and isolated minimal `project.godot` staging
   manifest, with no gameplay scene or autoload; fresh unique external stage
   under `D:\GameDev\Godot\TLWH-NativeStages`.
2. The pinned standard 4.7.2 executable/hash from AGENTS.md, source/status/index
   and input hash capture before actual static-suite PASS, and identity checks
   throughout; no command/script/executable overrides.
3. At most one cold import (60 seconds) and, only on clean PASS, one fixed
   `--headless --path <fresh-stage> --script res://tests/save_file_codec_test.gd`
   invocation (30 seconds), sequentially, with no automatic retry.
4. Existing 1,048,576-byte output and 4,096-byte diagnostic limits, unique isolated
   test data, required `SAVE_FILE_CODEC: PASS` completion with zero failures,
   fail-closed error/termination handling and retained bounded failure evidence.

This checklist is a proposed review scope, **not an active runner recipe or
execution grant**. Until reviewed activation, codec engine parsing, automated
runtime assertions and independent file reopening remain unexecuted. Owner
acceptance must review those results and the file contract before integration.
