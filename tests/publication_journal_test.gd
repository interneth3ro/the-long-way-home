extends SceneTree
## Authored synthetic assertions only. No execution grant or filesystem operations.
const Journal = preload("res://persistence/publication_journal.gd")
const Codec = preload("res://persistence/save_file_codec.gd")
const EMPTY_GOLDEN := "544c57485341563101000000080000000800000001000000b76647f5e2a23ff0059ef0a86012fc46e374924b8e7de93720dba0e2f68d03771b000000000000001b00000000000000"
const RECORD_GOLDEN := "544c57484a524e310100000048000000544c57485341563101000000080000000800000001000000b76647f5e2a23ff0059ef0a86012fc46e374924b8e7de93720dba0e2f68d03771b000000000000001b00000000000000544c5748434d54310100000048000000010000000000000038e252d41af189f28780432f11260022b624ba1a4cee6538ccf4ea8e08da7a6c"
const MANIFEST_GOLDEN := "544c57484d414e3101000000010000000000000001000000000000009000000000000000cfe23ff7a3e9d38ff365a223f5a0bb0e8d5c2b6eb43aa6090d320e2f180e0f4d0f1e902fad36cb67ba7ed798c84f4e7ecf3829175cd208af22fffc992c4d9733"
var _checks := 0
var _failures := 0


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


# Independent fixture framing, offsets and hashing; never use journal helpers.
func _hash(bytes: PackedByteArray) -> PackedByteArray:
	var context := HashingContext.new()
	_check(context.start(HashingContext.HASH_SHA256) == OK, "fixture hash start")
	_check(context.update(bytes) == OK, "fixture hash update")
	return context.finish()


func _record(snapshot: PackedByteArray, number: int = 1) -> PackedByteArray:
	var bytes := "TLWHJRN1".to_ascii_buffer()
	bytes.resize(16)
	bytes.encode_u16(8, 1)
	bytes.encode_u16(10, 0)
	bytes.encode_u32(12, snapshot.size())
	bytes.append_array(snapshot)
	var footer := "TLWHCMT1".to_ascii_buffer()
	footer.resize(24)
	footer.encode_u16(8, 1)
	footer.encode_u16(10, 0)
	footer.encode_u32(12, snapshot.size())
	footer.encode_u64(16, number)
	bytes.append_array(footer)
	bytes.append_array(_hash(bytes))
	return bytes


func _seal_record(bytes: PackedByteArray) -> PackedByteArray:
	var sealed := bytes.slice(0, bytes.size() - 32)
	sealed.append_array(_hash(sealed))
	return sealed


func _manifest(journal: PackedByteArray, sequence: int = 1, generation: int = 1) -> PackedByteArray:
	var bytes := "TLWHMAN1".to_ascii_buffer()
	bytes.resize(36)
	bytes.encode_u16(8, 1)
	bytes.encode_u16(10, 0)
	bytes.encode_u64(12, sequence)
	bytes.encode_u64(20, generation)
	bytes.encode_u64(28, journal.size())
	bytes.append_array(_hash(journal))
	bytes.append_array(_hash(bytes))
	return bytes


func _seal_manifest(bytes: PackedByteArray) -> PackedByteArray:
	var sealed := bytes.slice(0, 68)
	sealed.append_array(_hash(sealed))
	return sealed


func _reject(result: Dictionary, code: String, label: String) -> void:
	_check(not result.ok and result.get("error") == code, label)


func _goldens() -> void:
	var snapshot := EMPTY_GOLDEN.hex_decode()
	var record := RECORD_GOLDEN.hex_decode()
	var manifest := MANIFEST_GOLDEN.hex_decode()
	_check(_record(snapshot) == record, "independent record golden")
	_check(_manifest(record) == manifest, "independent manifest golden")
	var encoded := Journal.encode_record(snapshot, 1)
	_check(encoded.ok and encoded.bytes == record, "encoder record golden")
	encoded = Journal.encode_manifest(1, 1, record)
	_check(encoded.ok and encoded.bytes == manifest, "encoder manifest golden")
	var decoded := Journal.decode_manifest(manifest)
	_check(decoded.ok and decoded.committed_length == 144 and decoded.publication_sequence == 1 and decoded.generation == 1, "manifest field layout")
	var journal := Journal.recover_journal(record)
	_check(journal.ok and journal.complete and not journal.authoritative, "complete journal is not authority")
	_check(journal.record_count == 1 and journal.committed_length == 144 and journal.latest_bytes == snapshot, "minimum committed record")
	_check(Journal.validate_generation(manifest, record).authoritative, "whole generation authority")
	_check(Journal.MIN_RECORD_BYTES == 144 and Journal.MAX_RECORD_BYTES == 8454272, "record bounds")


func _framing_and_tails() -> void:
	var record := RECORD_GOLDEN.hex_decode()
	# Every proper nonempty truncation of this valid record has consistent framing.
	for cut in range(1, record.size()):
		var short := Journal.recover_journal(record.slice(0, cut))
		_reject(short, "incomplete_tail", "truncated record at %d" % cut)
		_check(not short.has_snapshot and short.committed_length == 0, "uncommitted bytes never exposed")
	_reject(Journal.recover_journal(PackedByteArray()), "no_authority", "empty journal")
	for fixture in [[0, 0, "structural_corruption"], [8, 2, "unsupported_format"],
		[9, 1, "unsupported_format"], [10, 1, "structural_corruption"],
		[11, 1, "structural_corruption"], [88, 0, "structural_corruption"],
		[96, 2, "unsupported_format"], [98, 1, "structural_corruption"], [99, 1, "structural_corruption"],
		[100, 73, "structural_corruption"], [104, 0, "sequence"],
		[111, 128, "sequence"], [143, 0, "integrity"]]:
		var damaged := record.duplicate()
		damaged[fixture[0]] = fixture[1]
		_reject(Journal.recover_journal(damaged), fixture[2], "malformed record offset %d" % fixture[0])
	# Maximum length is legal framing, but this small buffer is incomplete.
	for size in [0, 71, 72, 8454200, 8454201, 0xffffffff]:
		var prefix := record.slice(0, 16)
		prefix.encode_u32(12, size)
		var code := "incomplete_tail" if size in [72, 8454200] else "structural_corruption"
		_reject(Journal.recover_journal(prefix), code, "declared bound %d" % size)
	var bad_partial := record.slice(0, 15)
	bad_partial[12] = 255
	bad_partial[13] = 255
	bad_partial[14] = 255
	_reject(Journal.recover_journal(bad_partial), "structural_corruption", "partial length already oversized")
	bad_partial = record.slice(0, 15)
	bad_partial[12] = 0
	_reject(Journal.recover_journal(bad_partial), "structural_corruption", "partial length has no legal completion")
	for cut in [1, 9, 11, 89, 97, 99, 101, 105, 113]:
		var inconsistent := record.slice(0, cut)
		inconsistent[cut - 1] ^= 1
		_check(Journal.recover_journal(inconsistent).error != "incomplete_tail", "inconsistent partial framing/digest")
	var second := _record(EMPTY_GOLDEN.hex_decode(), 2)
	var joined := record.duplicate()
	joined.append_array(second)
	_check(Journal.recover_journal(joined).record_count == 2, "consecutive records")
	for number in [0, 1, 3, Journal.MAX_COUNTER]:
		var bad := record.duplicate()
		bad.append_array(_record(EMPTY_GOLDEN.hex_decode(), number))
		var salvage := Journal.recover_journal(bad)
		_reject(salvage, "sequence", "gap/duplicate/invalid sequence")
		_check(salvage.has_snapshot and salvage.record_count == 1 and salvage.committed_length == 144, "valid prefix salvage")
	var stopped := joined.slice(0, 200)
	stopped.append_array(record) # A later valid-looking boundary must not be scanned.
	var recovery := Journal.recover_journal(stopped)
	_check(not recovery.ok and recovery.record_count == 1 and recovery.latest_bytes == EMPTY_GOLDEN.hex_decode(), "stop at first damaged record")
	var trailing := record.duplicate()
	trailing.append(0)
	_reject(Journal.recover_journal(trailing), "structural_corruption", "arbitrary trailing byte")
	_check(Journal._next_sequence(Journal.MAX_COUNTER - 1).value == Journal.MAX_COUNTER, "last supported increment")
	_reject(Journal._next_sequence(Journal.MAX_COUNTER), "sequence", "overflow before addition")
	_reject(Journal.encode_record(EMPTY_GOLDEN.hex_decode(), 0), "sequence", "zero encode counter")
	_reject(Journal.encode_record(EMPTY_GOLDEN.hex_decode(), -1), "sequence", "negative encode counter")
	_check(Journal.encode_record(EMPTY_GOLDEN.hex_decode(), Journal.MAX_COUNTER).ok, "maximum encode counter")


func _nested_codec() -> void:
	var snapshot := EMPTY_GOLDEN.hex_decode()
	# Inner checksum is valid, but metadata root is a forbidden Object wire type.
	snapshot.encode_u32(56, 24)
	var covered := snapshot.slice(0, 24)
	covered.append_array(snapshot.slice(56))
	var digest := _hash(covered)
	for i in 32:
		snapshot[24 + i] = digest[i]
	_check(Codec.validate_envelope(snapshot).ok, "malformed nested fixture has valid envelope")
	_reject(Journal.recover_journal(_record(snapshot)), "structural_corruption", "full codec validation required")
	_reject(Journal.encode_record(snapshot, 1), "structural_corruption", "encoder rejects malformed nested codec")
	_reject(Journal.recover_journal(_record(snapshot).slice(0, 88)), "structural_corruption", "invalid complete snapshot with missing footer")
	var nested: PackedByteArray = Codec.encode({"x": 0}).bytes
	nested.encode_u32(nested.size() - 8, 24) # Object as a Dictionary value, not just an invalid root.
	covered = nested.slice(0, 24)
	covered.append_array(nested.slice(56))
	digest = _hash(covered)
	for i in 32:
		nested[24 + i] = digest[i]
	_check(Codec.validate_envelope(nested).ok, "nested Object fixture has valid codec checksum")
	_reject(Journal.recover_journal(_record(nested)), "structural_corruption", "nested Object rejected before native decoding")
	for field in [8, 10, 20]:
		var unsupported := EMPTY_GOLDEN.hex_decode()
		unsupported[field] = 2
		_reject(Journal.recover_journal(_record(unsupported)), "unsupported_format", "unsupported codec header")
	var damaged := RECORD_GOLDEN.hex_decode()
	damaged[72] ^= 1
	_reject(Journal.recover_journal(_seal_record(damaged)), "integrity", "inner integrity checked after outer reseal")
	_reject(Journal.encode_record(PackedByteArray(), 1), "invalid_input", "invalid snapshot input")


func _history() -> void:
	var history: Array = []
	for i in 7:
		history.append(Codec.encode({"n": i}).bytes)
	var before := history.duplicate(true)
	var newest: PackedByteArray = Codec.encode({"n": 7}).bytes
	var built := Journal.build_generation(history, newest)
	_check(built.ok and built.record_count == 5 and history == before, "five snapshots, immutable caller history")
	var expected := PackedByteArray()
	for i in range(3, 8):
		expected.append_array(_record(Codec.encode({"n": i}).bytes, i - 2))
	_check(built.bytes == expected, "latest four plus new; bytes preserved and renumbered")
	_check(Journal.build_generation(history, newest).bytes == expected, "deterministic compaction")
	_check(Journal.build_generation([], newest).record_count == 1, "initial generation")
	var corrupt := history.duplicate()
	corrupt[0] = PackedByteArray() # Omitted history must still be rejected.
	_reject(Journal.build_generation(corrupt, newest), "invalid_input", "reject invalid discarded history")
	_reject(Journal.build_generation([{}], newest), "invalid_input", "history entry type")
	_reject(Journal.build_generation(history, PackedByteArray()), "invalid_input", "reject invalid new snapshot")
	_check(Journal.recover_journal(expected).latest_bytes == newest, "latest compacted snapshot")


func _manifests_and_authority() -> void:
	var record := RECORD_GOLDEN.hex_decode()
	var manifest := MANIFEST_GOLDEN.hex_decode()
	for cut in [0, 1, 68, 99]:
		_reject(Journal.decode_manifest(manifest.slice(0, cut)), "structural_corruption", "short manifest")
	var trailing := manifest.duplicate()
	trailing.append(0)
	_reject(Journal.decode_manifest(trailing), "structural_corruption", "manifest trailing bytes")
	for fixture in [[0, 0, "structural_corruption"], [8, 2, "unsupported_format"],
		[10, 1, "structural_corruption"], [36, 0, "integrity"], [99, 0, "integrity"]]:
		var changed := manifest.duplicate()
		changed[fixture[0]] = fixture[1]
		_reject(Journal.decode_manifest(changed), fixture[2], "invalid manifest field")
	for offset in [12, 20, 28]:
		var high := manifest.duplicate()
		high[offset + 7] = 128
		_reject(Journal.decode_manifest(_seal_manifest(high)), "structural_corruption", "unsigned high bit")
		var zero := manifest.duplicate()
		zero.encode_u64(offset, 0)
		_reject(Journal.decode_manifest(_seal_manifest(zero)), "structural_corruption", "zero field")
	_check(Journal.encode_manifest(Journal.MAX_COUNTER, Journal.MAX_COUNTER, record).ok, "maximum manifest counters")
	_reject(Journal.encode_manifest(0, 1, record), "invalid_input", "invalid publication sequence")
	_reject(Journal.encode_manifest(1, -1, record), "invalid_input", "invalid generation")
	var newer := _manifest(record, 2, 2)
	var generations := {1: record, 2: record}
	_check(Journal.select_authority(manifest, null, generations).slot == 0, "one slot")
	_check(Journal.select_authority(null, manifest, generations).slot == 1, "other slot")
	_check(Journal.select_authority(manifest, newer, generations).publication_sequence == 2, "highest usable sequence")
	_check(Journal.select_authority(newer, manifest, generations).slot == 0, "independent of slot order")
	_check(Journal.select_authority(manifest, manifest, generations).ok, "identical equal-sequence authority")
	_reject(Journal.select_authority(manifest, _manifest(record, 1, 2), {}), "authority_conflict", "conflict before missing generation filtering")
	var fallback := Journal.select_authority(manifest, newer, {1: record})
	_check(fallback.ok and fallback.generation == 1 and fallback.diagnostics[1].error == "missing_generation", "missing newer generation fallback")
	var invalid := record.duplicate()
	invalid[143] ^= 1
	fallback = Journal.select_authority(manifest, newer, {1: record, 2: invalid})
	_check(fallback.ok and fallback.generation == 1 and fallback.diagnostics[1].error == "integrity", "invalid newer generation fallback")
	var unsupported := manifest.duplicate()
	unsupported[8] = 2
	fallback = Journal.select_authority(unsupported, manifest, generations)
	_check(fallback.ok and fallback.diagnostics[0].error == "unsupported_format", "unsupported slot diagnostic")
	var bad_digest := manifest.duplicate()
	bad_digest[99] ^= 1
	fallback = Journal.select_authority(bad_digest, manifest, generations)
	_check(fallback.ok and fallback.diagnostics[0].error == "integrity", "invalid slot digest diagnostic")
	_reject(Journal.select_authority(null, null, generations), "no_authority", "orphans never promoted")
	_reject(Journal.select_authority(manifest, null, {}), "no_authority", "no usable generation")
	_reject(Journal.select_authority({}, null, generations), "invalid_input", "untrusted caller result dictionary")
	_reject(Journal.select_authority(manifest, null, {1: "bad"}), "invalid_input", "generation input type")
	# Independently seal a manifest for a corrupt journal: checksum alone is insufficient.
	var damaged := record.duplicate()
	damaged.append_array(_record(EMPTY_GOLDEN.hex_decode(), 2).slice(0, 100))
	var salvage := Journal.recover_journal(damaged)
	_check(not salvage.ok and salvage.has_snapshot and salvage.committed_length == 144, "tail salvage available")
	var authority := Journal.validate_generation(_manifest(damaged), damaged)
	_reject(authority, "incomplete_tail", "bound damaged generation cannot authorize salvage")
	_check(not authority.has("latest_bytes") and not authority.has("authoritative"), "authority error never leaks salvage")
	_reject(Journal.validate_generation(manifest, damaged), "structural_corruption", "exact manifest length")
	_reject(Journal.validate_generation(manifest, invalid), "integrity", "complete journal digest binding")
	_reject(Journal.encode_manifest(1, 1, damaged), "incomplete_tail", "encoder cannot bind damaged generation")


func _initialize() -> void:
	_goldens()
	_framing_and_tails()
	_nested_codec()
	_history()
	_manifests_and_authority()
	print("PUBLICATION_JOURNAL: %s checks=%d failures=%d" % ["PASS" if _failures == 0 else "FAIL", _checks, _failures])
	quit(0 if _failures == 0 else 1)
