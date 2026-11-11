# Publication journal byte foundation

Issue [#165](https://github.com/interneth3ro/the-long-way-home/issues/165), PR 1,
implemented on `codex/publication-journal-bytes`, **pending merge**.
[PublicationJournal](../persistence/publication_journal.gd) is a standalone
RefCounted module of pure static byte operations. It preserves the
[codec envelope](SAVE_FILE_FORMAT.md) unchanged inside each record. It has no
filesystem calls, gameplay callers, SaveCoordinator, scheduling, save UI, or
restoration. This is not working gameplay saving or filesystem publication.

## Record version 1

All multibyte integers are unsigned little endian; offsets are zero based, with
no alignment gaps. Journal, manifest, codec, and future gameplay schema versions
are independent. Only journal version 1 and manifest version 1 are supported.
No migration or forward scanning through damaged bytes is implemented.

Prefix (16 bytes):

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 8 | ASCII `TLWHJRN1` (`544c57484a524e31`) |
| 8 | 2 | Journal version = 1 |
| 10 | 2 | Reserved = 0 |
| 12 | 4 | Complete codec snapshot length `S` |

The next `S` bytes are exactly one complete `TLWHSAV1` snapshot, with its own
independent codec checksum. `S` is 72 through 8,454,200 inclusive.

Commit footer (56 bytes), relative to the end of the snapshot:

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 8 | ASCII `TLWHCMT1` (`544c5748434d5431`) |
| 8 | 2 | Journal version = 1 |
| 10 | 2 | Reserved = 0 |
| 12 | 4 | Repeated snapshot length `S` |
| 16 | 8 | Consecutive record number |
| 24 | 32 | Raw SHA-256 digest |

The record digest covers the complete prefix, complete snapshot and footer
bytes `[0,24)`. The final digest field is excluded, not zero-filled. Complete
record size is `16 + S + 56`: **144 through 8,454,272 bytes**.

The first record number is 1, followed by strictly consecutive numbers.
Supported record, generation and publication counters are `1..2^63-1` despite
unsigned wire storage. High-bit values are rejected; incrementing the maximum
record number fails before addition. Numbers are not floats and do not wrap.
Record numbering restarts in each generation. Publication sequence advancement
belongs to the future publisher; this module accepts explicit validated values.

## Manifest version 1

Exactly **100 bytes**, with no trailing bytes or implicit padding:

| Offset | Bytes | Field |
| --- | --- | --- |
| 0 | 8 | ASCII `TLWHMAN1` (`544c57484d414e31`) |
| 8 | 2 | Manifest version = 1 |
| 10 | 2 | Reserved = 0 |
| 12 | 8 | Publication sequence |
| 20 | 8 | Generation number |
| 28 | 8 | Committed journal byte length |
| 36 | 32 | Raw SHA-256 of the complete journal |
| 68 | 32 | Raw SHA-256 of manifest bytes `[0,68)` |

The manifest checksum excludes its own field. The journal digest includes
every record, including every footer checksum. Length must be at least 144
and at most `2^63-1`; authority validation requires exact actual byte length.
The parser does not allocate based on this declared length. This is not a
promise that such large byte arrays can be represented or processed in Godot.
There are no paths, filenames, timestamps, or gameplay identities in the manifest.
SHA-256 detects corruption; it does not authenticate saves or prevent deliberate
recomputation. No byte contract promises crash or power-loss durability.

## Recovery and authority

`recover_journal` walks from offset zero. It checks available fixed framing,
size bounds, repeated length, consecutive numbering, record digest and the
codec's full `decode()` for each complete snapshot. Envelope-only validation is
insufficient. Decoded Dictionaries are released after each record validation;
the result exposes only the latest validated snapshot's codec bytes.

Recovery stops at the first invalid record. It never scans for later magic,
changes bytes, truncates, repairs or certifies filesystem authority. A complete
nonempty journal returns `ok: true`, `complete: true`, `authoritative: false`,
`terminal: "complete"`, `record_count`, `committed_length`, `has_snapshot: true`
and `latest_bytes`.

On damage, `ok` and `complete` are false; `error`, `message` and `terminal`
describe the first failure. `committed_length` and `record_count` describe only
the validated prefix. `has_snapshot` is true and `latest_bytes` is present only
if a prior record was fully committed and validated. This is explicit salvage,
never authoritative success. An empty journal returns `no_authority`, zero
count/boundary and no snapshot. A zero-byte append is indistinguishable from
no append and does not make an otherwise complete journal incomplete.

EOF inside consistent framing is `incomplete_tail`. Available malformed magic,
version, reserved, length, sequence or digest bytes are rejected even if short.
A partial length whose available low bytes already exceed the cap, or cannot
be completed to any supported length, is invalid.
A partial snapshot is not decoded or certified; once the snapshot is complete,
its codec validity is checked even when the footer is short. This classification
does not prove an interrupted write caused the missing bytes.

`validate_generation` requires a self-valid manifest, exact whole-journal length
and digest, and completely successful journal recovery. On failure it returns
only `ok: false`, `error` and `message`; it never exposes salvage. On success it
returns `authoritative: true`, publication/generation identifiers, committed
length, journal digest, record count and latest codec bytes. This certifies only
the supplied byte relationship, not that those bytes were durably published.

`select_authority` accepts two raw manifest slots (byte arrays or null for an
absent slot) and a Dictionary mapping integer generation IDs to raw journal byte
arrays. It validates the bytes itself; caller-provided validation-result
Dictionaries are not trusted. It compares self-valid equal-sequence manifests
before checking referenced generations: differing records are an explicit
`authority_conflict`, even if one generation is missing. Identical records are
accepted, with slot 0 winning the tie. Different sequences select the highest
usable one, including fallback when a higher sequence references missing or
invalid data. Unsupported or corrupt slots are unusable; their errors remain
visible in diagnostics. An unreferenced generation is never promoted.

The selector adds `slot` (0 or 1) to successful authority results and
`diagnostics` entries containing `slot`, `usable`, `error` and `message` for each
slot on normal selection/no-authority results. Invalid API inputs and authority
conflicts return ordinary errors immediately. Missing referenced generation data
is a candidate-level `missing_generation`; no usable candidates produce
`no_authority`. Unreferenced Dictionary entries are not examined or selected.
Callers must report degraded/fallback recovery, not interpret it as a publication
or silently use it to authorize repair of stored data.

## In-memory construction and API

| Static API | Success fields besides `ok: true` |
| --- | --- |
| `encode_record(snapshot_bytes, record_number)` | `bytes` |
| `recover_journal(bytes)` | Recovery fields described above; never authoritative |
| `build_generation(history, new_snapshot)` | `bytes`, `record_count` |
| `encode_manifest(publication_sequence, generation, journal_bytes)` | `bytes` |
| `decode_manifest(bytes)` | `publication_sequence`, `generation`, `committed_length`, `journal_digest` |
| `validate_generation(manifest_bytes, journal_bytes)` | Whole-generation authority fields described above |
| `select_authority(slot_a, slot_b, generations)` | Selected authority, slot and diagnostics described above |

`build_generation` takes chronological codec byte arrays, validates every supplied
history entry (including entries outside retention), retains the latest four,
and adds the new validated snapshot. It preserves codec bytes unchanged, assigns
record numbers from 1 and recomputes record digests. Caller inputs are not
mutated. Invalid entries are rejected rather than silently skipped. Manifest
encoding also refuses to bind an incomplete/invalid journal.

Five is the initial generation history policy, independent of the five rotating
autosave slots approved in Issue #165. Five maximum records total **42,271,360
bytes** (about 40.31 MiB). Recovery validates supplied journals sequentially and
does not impose a five-record compatibility limit; construction emits at most
five. The input byte array already resides in memory; hashing, slicing, encoding
and codec normalization need additional memory. This is not a whole-world memory
budget or performance certification. Callers must provide stable input bytes
and collections, without concurrent mutation; this pure module has no writer lock.

Ordinary errors return only `ok: false`, `error` and `message`:

| Category | Meaning |
| --- | --- |
| `invalid_input` | Invalid construction size/counters, history types or selector argument content |
| `unsupported_format` | Unsupported journal/manifest version or codec version/compression |
| `structural_corruption` | Invalid framing, reserved fields, lengths, supported ranges or nested codec structure |
| `integrity` | Journal, codec or manifest checksum mismatch/calculation failure |
| `sequence` | Invalid record number, gap, duplicate or exhausted increment |
| `incomplete_tail` | EOF before a full record with otherwise consistent available framing |
| `authority_conflict` | Self-valid equal-sequence manifests bind different records |
| `missing_generation` | A selector candidate references absent generation bytes |
| `no_authority` | Empty journal or no usable manifest/generation pair |

Salvage and selector diagnostics are the explicit exceptions to the ordinary
error shape. GDScript's typed method signatures enforce top-level byte/Array/
Dictionary/int argument types; callers must respect them. No decoded gameplay
schema is interpreted. Internal `_` helpers are not publisher interfaces.

## Validation and deferred publication

[Python static tests](../tests/static_publication_journal_test.py) independently
construct codec/record/manifest golden vectors with `struct` and `hashlib`, check
byte coverage/layout and inspect source safety boundaries. The existing command
is `python -B -m unittest discover -s tests -p 'static_*test.py'`. It invokes no
Godot or GDScript. Static success does not establish parsing, type checking or
runtime behavior.

[Synthetic GDScript assertions](../tests/publication_journal_test.gd) are authored
but **not executed**. They cover truncation, malformed framing/codec values,
sequence limits, salvage, compaction and manifest authority. They use independent
fixture framing/hashing and no filesystem I/O. No runner dispatch, stage or
authorization mechanism was added or changed. Historical codec checks and their
consumed grant remain documented in [SAVE_CODEC_RUNNER.md](SAVE_CODEC_RUNNER.md).
Any engine import, parsing or runtime invocation requires fresh owner approval
and a separately reviewed isolated execution scope; no command here grants it.

A future separately authorized PR must define directory boundaries, generation
filename derivation/allocation, exclusive writer ownership, path-redirection and
collision handling, immutable generation writes, flushing/closing, independent
reopening, inactive-slot publication, final verification, initial-store and
orphan handling, and failed/uncertain outcomes without automatic retries.
No filesystem publication, slot writes, repair, deletion, gameplay integration,
or crash/power-loss guarantee is implemented here. Retaining historical
generations without deletion leaves total disk growth unbounded.
