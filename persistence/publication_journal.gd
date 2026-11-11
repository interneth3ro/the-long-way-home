class_name PublicationJournal
extends RefCounted
## Pure byte foundation. No files, publication, gameplay, or execution permission.
## See docs/PUBLICATION_JOURNAL.md for result contracts and authority boundaries.
const Codec = preload("res://persistence/save_file_codec.gd")
const RECORD_MAGIC := "TLWHJRN1"
const COMMIT_MAGIC := "TLWHCMT1"
const MANIFEST_MAGIC := "TLWHMAN1"
const JOURNAL_VERSION := 1
const MANIFEST_VERSION := 1
const PREFIX_SIZE := 16
const FOOTER_SIZE := 56
const MANIFEST_SIZE := 100
const MAX_COUNTER := 9223372036854775807
const MIN_SNAPSHOT_BYTES := 72
const MAX_SNAPSHOT_BYTES := 8454200
const MIN_RECORD_BYTES := 144
const MAX_RECORD_BYTES := 8454272
const HISTORY_LIMIT := 5


static func _error(code: String, message: String) -> Dictionary:
	return {"ok": false, "error": code, "message": message}


static func _counter(value: Variant) -> bool:
	return typeof(value) == TYPE_INT and value >= 1 and value <= MAX_COUNTER


# Guard before addition; also independently testable without an enormous journal.
static func _next_sequence(value: int) -> Dictionary:
	if not _counter(value) or value == MAX_COUNTER:
		return _error("sequence", "Record sequence exhausted or invalid.")
	return {"ok": true, "value": value + 1}


static func _sha256(bytes: PackedByteArray) -> PackedByteArray:
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK or context.update(bytes) != OK:
		return PackedByteArray()
	return context.finish()


static func _header(magic: String, version: int, size: int) -> PackedByteArray:
	var bytes := PackedByteArray()
	bytes.resize(size)
	for i in 8:
		bytes[i] = magic.unicode_at(i)
	bytes.encode_u16(8, version)
	bytes.encode_u16(10, 0)
	return bytes


static func _snapshot(bytes: PackedByteArray) -> Dictionary:
	if bytes.size() < MIN_SNAPSHOT_BYTES or bytes.size() > MAX_SNAPSHOT_BYTES:
		return _error("invalid_input", "Snapshot size outside codec bounds.")
	var decoded := Codec.decode(bytes)
	if not decoded.ok:
		var code := "structural_corruption"
		if decoded.error in ["format_version", "compression", "snapshot_version"]:
			code = "unsupported_format"
		elif decoded.error in ["checksum", "hash"]:
			code = "integrity"
		return _error(code, "Codec %s: %s" % [decoded.error, decoded.message])
	# Do not keep decoded whole-world Dictionaries in journal history/results.
	return {"ok": true}


static func encode_record(snapshot_bytes: PackedByteArray, record_number: int) -> Dictionary:
	if not _counter(record_number):
		return _error("sequence", "Record number outside supported range.")
	var checked := _snapshot(snapshot_bytes)
	if not checked.ok:
		return checked
	var bytes := _header(RECORD_MAGIC, JOURNAL_VERSION, PREFIX_SIZE)
	bytes.encode_u32(12, snapshot_bytes.size())
	bytes.append_array(snapshot_bytes)
	var footer := _header(COMMIT_MAGIC, JOURNAL_VERSION, 24)
	footer.encode_u32(12, snapshot_bytes.size())
	footer.encode_u64(16, record_number)
	bytes.append_array(footer)
	var digest := _sha256(bytes)
	if digest.size() != 32:
		return _error("integrity", "Record SHA-256 calculation failed.")
	bytes.append_array(digest)
	return {"ok": true, "bytes": bytes}


# Compare all available fixed bytes, including partial version/reserved fields.
# A short prefix with already inconsistent framing is not an incomplete append.
static func _fixed_fields(bytes: PackedByteArray, offset: int, magic: String, version: int) -> Dictionary:
	var fixed := _header(magic, version, 12)
	for i in mini(12, bytes.size() - offset):
		if bytes[offset + i] != fixed[i]:
			if i in [8, 9]:
				return _error("unsupported_format", "Unsupported framing version.")
			return _error("structural_corruption", "Invalid magic or nonzero reserved field.")
	return {"ok": true}


static func _record_at(bytes: PackedByteArray, offset: int, expected: int) -> Dictionary:
	var fixed := _fixed_fields(bytes, offset, RECORD_MAGIC, JOURNAL_VERSION)
	if not fixed.ok:
		return fixed
	var remaining := bytes.size() - offset
	if remaining < PREFIX_SIZE:
		# Available low-order length bytes can already prove an oversized claim.
		var lower_bound := 0
		for i in maxi(0, remaining - 12):
			lower_bound |= int(bytes[offset + 12 + i]) << (8 * i)
		if lower_bound > MAX_SNAPSHOT_BYTES:
			return _error("structural_corruption", "Invalid partial snapshot length.")
		# With three bytes present, any nonzero fourth byte exceeds the cap.
		if remaining == 15 and lower_bound < MIN_SNAPSHOT_BYTES:
			return _error("structural_corruption", "Partial length has no legal completion.")
		return _error("incomplete_tail", "EOF inside record prefix.")
	var size := bytes.decode_u32(offset + 12)
	if size < MIN_SNAPSHOT_BYTES or size > MAX_SNAPSHOT_BYTES:
		return _error("structural_corruption", "Snapshot length outside codec bounds.")
	# Bounds precede slicing, hashing, and native codec decoding.
	if size > remaining - PREFIX_SIZE:
		return _error("incomplete_tail", "EOF inside snapshot bytes.")
	var footer_offset := offset + PREFIX_SIZE + size
	var footer_available := mini(FOOTER_SIZE, bytes.size() - footer_offset)
	fixed = _fixed_fields(bytes, footer_offset, COMMIT_MAGIC, JOURNAL_VERSION)
	if not fixed.ok:
		return fixed
	var footer := _header(COMMIT_MAGIC, JOURNAL_VERSION, 24)
	footer.encode_u32(12, size)
	footer.encode_u64(16, expected)
	for i in range(12, mini(24, footer_available)):
		if bytes[footer_offset + i] != footer[i]:
			if i >= 16:
				return _error("sequence", "Record number is not the next supported number.")
			return _error("structural_corruption", "Repeated snapshot length differs.")
	if footer_available >= 24:
		var digest := _sha256(bytes.slice(offset, footer_offset + 24))
		if digest.size() != 32:
			return _error("integrity", "Record SHA-256 calculation failed.")
		for i in footer_available - 24:
			if bytes[footer_offset + 24 + i] != digest[i]:
				return _error("integrity", "Record SHA-256 differs.")
	var snapshot_bytes := bytes.slice(offset + PREFIX_SIZE, footer_offset)
	var checked := _snapshot(snapshot_bytes)
	if not checked.ok:
		return checked
	if footer_available < FOOTER_SIZE:
		return _error("incomplete_tail", "EOF inside commit footer.")
	return {"ok": true, "next_offset": footer_offset + FOOTER_SIZE, "latest_bytes": snapshot_bytes}


## Never establishes manifest authority. Failure may include explicitly marked salvage.
static func recover_journal(bytes: PackedByteArray) -> Dictionary:
	var offset := 0
	var count := 0
	var expected := 1
	var latest := PackedByteArray()
	var terminal := _error("no_authority", "Journal has no committed records.")
	while offset < bytes.size():
		var record := _record_at(bytes, offset, expected)
		if not record.ok:
			terminal = record
			break
		offset = record.next_offset
		latest = record.latest_bytes
		count = expected
		if offset < bytes.size():
			var next := _next_sequence(expected)
			if not next.ok:
				terminal = next
				break
			expected = next.value
	var complete := count > 0 and offset == bytes.size()
	var result := {"ok": complete, "authoritative": false, "complete": complete,
		"record_count": count, "committed_length": offset, "has_snapshot": count > 0,
		"terminal": "complete" if complete else terminal.error}
	if count > 0:
		result.latest_bytes = latest
	if not complete:
		result.error = terminal.error
		result.message = terminal.message
	return result


## Validate all supplied history, even entries omitted by retention. Never mutate inputs.
static func build_generation(history: Array, new_snapshot: PackedByteArray) -> Dictionary:
	for entry in history:
		if typeof(entry) != TYPE_PACKED_BYTE_ARRAY:
			return _error("invalid_input", "History entries must be codec byte arrays.")
		var checked := _snapshot(entry)
		if not checked.ok:
			return checked
	var checked := _snapshot(new_snapshot)
	if not checked.ok:
		return checked
	var selected := history.slice(maxi(0, history.size() - (HISTORY_LIMIT - 1)))
	selected.append(new_snapshot)
	var bytes := PackedByteArray()
	for i in selected.size():
		var record := encode_record(selected[i], i + 1)
		if not record.ok:
			return record
		bytes.append_array(record.bytes)
	return {"ok": true, "bytes": bytes, "record_count": selected.size()}


static func encode_manifest(publication_sequence: int, generation: int, journal_bytes: PackedByteArray) -> Dictionary:
	if not _counter(publication_sequence) or not _counter(generation):
		return _error("invalid_input", "Manifest counters outside supported range.")
	var journal := recover_journal(journal_bytes)
	if not journal.ok:
		return _error(journal.error, "Cannot bind incomplete/invalid journal: " + journal.message)
	var digest := _sha256(journal_bytes)
	if digest.size() != 32:
		return _error("integrity", "Journal SHA-256 calculation failed.")
	var bytes := _header(MANIFEST_MAGIC, MANIFEST_VERSION, 36)
	bytes.encode_u64(12, publication_sequence)
	bytes.encode_u64(20, generation)
	bytes.encode_u64(28, journal_bytes.size())
	bytes.append_array(digest)
	var manifest_digest := _sha256(bytes)
	if manifest_digest.size() != 32:
		return _error("integrity", "Manifest SHA-256 calculation failed.")
	bytes.append_array(manifest_digest)
	return {"ok": true, "bytes": bytes}


static func decode_manifest(bytes: PackedByteArray) -> Dictionary:
	if bytes.size() != MANIFEST_SIZE:
		return _error("structural_corruption", "Manifest must be exactly 100 bytes.")
	var fixed := _fixed_fields(bytes, 0, MANIFEST_MAGIC, MANIFEST_VERSION)
	if not fixed.ok:
		return fixed
	# Reject unsigned high bits before decode/use in signed arithmetic.
	for offset in [12, 20, 28]:
		if (bytes[offset + 7] & 0x80) != 0:
			return _error("structural_corruption", "Manifest integer exceeds signed supported range.")
	var publication_sequence := bytes.decode_u64(12)
	var generation := bytes.decode_u64(20)
	var length := bytes.decode_u64(28)
	if not _counter(publication_sequence) or not _counter(generation) or length < MIN_RECORD_BYTES:
		return _error("structural_corruption", "Invalid manifest counter or journal length.")
	var digest := _sha256(bytes.slice(0, 68))
	if digest.size() != 32 or digest != bytes.slice(68):
		return _error("integrity", "Manifest SHA-256 differs.")
	return {"ok": true, "publication_sequence": publication_sequence, "generation": generation,
		"committed_length": length, "journal_digest": bytes.slice(36, 68)}


static func validate_generation(manifest_bytes: PackedByteArray, journal_bytes: PackedByteArray) -> Dictionary:
	var manifest := decode_manifest(manifest_bytes)
	if not manifest.ok:
		return manifest
	return _validate_generation(manifest, journal_bytes)


static func _validate_generation(manifest: Dictionary, journal_bytes: PackedByteArray) -> Dictionary:
	if manifest.committed_length != journal_bytes.size():
		return _error("structural_corruption", "Manifest length does not match complete generation.")
	var digest := _sha256(journal_bytes)
	if digest.size() != 32 or digest != manifest.journal_digest:
		return _error("integrity", "Manifest digest does not match complete generation.")
	var journal := recover_journal(journal_bytes)
	if not journal.ok:
		# Deliberately do not return partial history/latest_bytes through authority API.
		return _error(journal.error, "Generation is not wholly valid: " + journal.message)
	return {"ok": true, "authoritative": true, "publication_sequence": manifest.publication_sequence,
		"generation": manifest.generation, "committed_length": manifest.committed_length,
		"journal_digest": manifest.journal_digest, "record_count": journal.record_count,
		"latest_bytes": journal.latest_bytes}


## Slots are raw manifest bytes or null (absent); generations map integer IDs to bytes.
## Raw inputs are revalidated here; caller-authored 'ok' Dictionaries are never trusted.
static func select_authority(slot_a: Variant, slot_b: Variant, generations: Dictionary) -> Dictionary:
	var slots: Array = [slot_a, slot_b]
	var manifests: Array = []
	for slot in slots:
		if slot == null:
			manifests.append(_error("no_authority", "Manifest slot absent."))
		elif typeof(slot) != TYPE_PACKED_BYTE_ARRAY:
			return _error("invalid_input", "Manifest slots must be bytes or null.")
		else:
			manifests.append(decode_manifest(slot))
	# Conflict between self-valid authority records cannot be hidden by missing data.
	if manifests[0].ok and manifests[1].ok:
		if manifests[0].publication_sequence == manifests[1].publication_sequence and slots[0] != slots[1]:
			return _error("authority_conflict", "Equal publication sequences bind different authority records.")
	var diagnostics: Array = []
	var selected := _error("no_authority", "No manifest references a wholly valid generation.")
	for i in 2:
		var candidate: Dictionary = manifests[i]
		if candidate.ok:
			var generation: Variant = generations.get(candidate.generation)
			if generation == null:
				candidate = _error("missing_generation", "Referenced generation absent.")
			elif typeof(generation) != TYPE_PACKED_BYTE_ARRAY:
				return _error("invalid_input", "Referenced generation must be bytes.")
			else:
				candidate = _validate_generation(candidate, generation)
		diagnostics.append({"slot": i, "usable": candidate.ok,
			"error": candidate.get("error", ""), "message": candidate.get("message", "")})
		if candidate.ok and (not selected.ok or candidate.publication_sequence > selected.publication_sequence):
			selected = candidate
			selected.slot = i
	selected.diagnostics = diagnostics
	return selected
