extends SceneTree
## Synthetic only; no project scene, active session, resources or autoload required.
const Codec = preload("res://persistence/save_file_codec.gd")
const EMPTY_GOLDEN := "544c57485341563101000000080000000800000001000000b76647f5e2a23ff0059ef0a86012fc46e374924b8e7de93720dba0e2f68d03771b000000000000001b00000000000000"
var _failures := 0
var _checks := 0


func _check(condition: bool, label: String) -> void:
	_checks += 1
	if not condition:
		_failures += 1
		printerr("FAIL: " + label)


func _reject(bytes: PackedByteArray, label: String, error: String = "") -> void:
	var result := Codec.decode(bytes)
	_check(not result.ok and not result.has("snapshot") and not result.has("metadata"), label)
	if not error.is_empty():
		_check(result.get("error") == error, label + " error classification")


# Independent test framing and hashing; do not use codec encoder/digest for malformed fixtures.
func _seal(bytes: PackedByteArray) -> PackedByteArray:
	var covered := bytes.slice(0, 24)
	covered.append_array(bytes.slice(56))
	var hash := HashingContext.new()
	_check(hash.start(HashingContext.HASH_SHA256) == OK, "fixture hash start")
	_check(hash.update(covered) == OK, "fixture hash update")
	var digest := hash.finish()
	for i in 32:
		bytes[24 + i] = digest[i]
	return bytes


func _frame(payload: PackedByteArray, metadata: PackedByteArray = PackedByteArray([27, 0, 0, 0, 0, 0, 0, 0])) -> PackedByteArray:
	var bytes := PackedByteArray()
	bytes.resize(56)
	for i in 8:
		bytes[i] = "TLWHSAV1".unicode_at(i)
	bytes.encode_u16(8, 1)
	bytes.encode_u16(10, 0)
	bytes.encode_u32(12, metadata.size())
	bytes.encode_u32(16, payload.size())
	bytes.encode_u32(20, 1)
	bytes.append_array(metadata)
	bytes.append_array(payload)
	return _seal(bytes)


func _u32(value: int) -> PackedByteArray:
	var bytes := PackedByteArray()
	bytes.resize(4)
	bytes.encode_u32(0, value)
	return bytes


func _raw_value(value: PackedByteArray) -> PackedByteArray:
	# Dictionary containing exactly {"x": <raw value>}.
	var bytes := PackedByteArray([27, 0, 0, 0, 1, 0, 0, 0, 4, 0, 0, 0, 1, 0, 0, 0, 120, 0, 0, 0])
	bytes.append_array(value)
	return _frame(bytes)


func _round_trips() -> void:
	var fixtures: Array = [{}, {"empty": [[], {}]},
		{"primitives": [null, false, true, -2147483649, 9223372036854775807,
			-9223372036854775807 - 1, 0, 0.0, 1.25, 1.0e100, "", "Dave — 世界 🚀"]},
		{"sections": {"synthetic_inventory": {"version": 1, "data": []},
			"synthetic_world": {"version": 7, "data": {"seed": 26026}}}}]
	for fixture in fixtures:
		var encoded := Codec.encode(fixture, {"name": "synthetic"})
		_check(encoded.ok, "encode round-trip fixture")
		if not encoded.ok:
			continue
		var decoded := Codec.decode(encoded.bytes)
		_check(decoded.ok, "decode round-trip fixture")
		if decoded.ok:
			_check(decoded.snapshot == fixture, "snapshot values preserved")
			_check(decoded.metadata == {"name": "synthetic"}, "metadata preserved")
			_check(decoded.snapshot_version == 1, "global version exposed")
	var first := {"z": {"b": 2, "a": 1}, "a": [{"d": 4, "c": 3}, 9, 8]}
	var second := {"a": [{"c": 3, "d": 4}, 9, 8], "z": {"a": 1, "b": 2}}
	var before: Array = first.keys()
	var nested_before: Array = first.z.keys()
	var one := Codec.encode(first, {"z": 0, "a": 1})
	var two := Codec.encode(second, {"a": 1, "z": 0})
	_check(one.ok and two.ok and one.bytes == two.bytes, "nested and metadata determinism")
	_check(Codec.encode(first, {"z": 0, "a": 1}).bytes == one.bytes, "repeat encoding")
	_check(first.keys() == before and first.z.keys() == nested_before, "caller insertion order untouched")
	_check(Codec.decode(one.bytes).snapshot.a[1] == 9, "array order preserved")
	_check(Codec.encode({"a": [1, 2]}).bytes != Codec.encode({"a": [2, 1]}).bytes, "array order significant")
	_check(Codec.encode({"x": -0.0}).bytes == Codec.encode({"x": 0.0}).bytes, "signed zero normalized")
	var typed: Array[int] = [1, 2]
	_check(Codec.encode({"x": typed}).bytes == Codec.encode({"x": [1, 2]}).bytes, "typed input copied to untyped")
	# Layout lock uses raw fixture, not codec offsets or serializer.
	_check(Codec.encode({}).bytes == _frame(PackedByteArray([27, 0, 0, 0, 0, 0, 0, 0])), "empty file exact bytes")
	_check(TYPE_DICTIONARY == 27 and TYPE_ARRAY == 28, "native wire type identities")
	_check(Codec.encode({}).bytes.hex_encode() == EMPTY_GOLDEN, "independent Python SHA-256 golden")


func _integrity_and_framing() -> void:
	var bytes: PackedByteArray = Codec.encode({"x": 42}, {"a": "b"}).bytes
	_check(Codec.validate_envelope(bytes).ok, "envelope independently validates")
	for offset in [bytes.size() - 1, 56 + 16, 24]:
		var corrupt := bytes.duplicate()
		corrupt[offset] ^= 1
		_reject(corrupt, "covered byte corruption %s" % offset, "checksum")
	# Change framing while preserving total length: framing passes; digest must fail.
	var header_corrupt := bytes.duplicate()
	header_corrupt.encode_u32(12, bytes.decode_u32(12) + 4)
	header_corrupt.encode_u32(16, bytes.decode_u32(16) - 4)
	_reject(header_corrupt, "header lengths protected", "checksum")
	_reject(bytes.slice(0, bytes.size() - 1), "truncation", "length")
	var trailing := bytes.duplicate()
	trailing.append(0)
	_reject(trailing, "file trailing bytes", "length")
	_reject(PackedByteArray(), "empty file", "size")
	_reject(bytes.slice(0, 55), "short header", "size")
	for fixture in [[0, 0, "magic"], [8, 2, "format_version"], [10, 1, "compression"], [20, 2, "snapshot_version"]]:
		var changed := bytes.duplicate()
		changed[fixture[0]] = fixture[1]
		_reject(_seal(changed), "unsupported header " + fixture[2], fixture[2])
	for field in [12, 16]:
		for length in [0, 7, 0xffffffff]:
			var changed := bytes.duplicate()
			changed.encode_u32(field, length)
			_reject(_seal(changed), "unsafe declared length", "length")
	var too_big := PackedByteArray()
	too_big.resize(Codec.MAX_FILE_BYTES + 1)
	_reject(too_big, "file size limit", "size")
	# Exact payload/metadata caps are rejected without allocating their declared sizes.
	for fixture in [[12, Codec.MAX_METADATA_BYTES + 1], [16, Codec.MAX_PAYLOAD_BYTES + 1]]:
		var changed := bytes.duplicate()
		changed.encode_u32(fixture[0], fixture[1])
		_reject(_seal(changed), "section size cap", "length")


func _malformed_variants() -> void:
	for raw in [PackedByteArray([255, 0, 0, 0]), _u32(TYPE_OBJECT),
		_u32(TYPE_OBJECT | (1 << 16)), _u32(TYPE_CALLABLE), _u32(TYPE_SIGNAL),
		_u32(TYPE_PACKED_BYTE_ARRAY), _u32(TYPE_VECTOR2), _u32(TYPE_STRING_NAME),
		_u32(TYPE_ARRAY | (1 << 16)), _u32(TYPE_DICTIONARY | (1 << 18)),
		PackedByteArray([1, 0, 0, 0, 2, 0, 0, 0]),
		PackedByteArray([3, 0, 0, 0, 0, 0, 128, 127]),
		PackedByteArray([4, 0, 0, 0, 255, 255, 255, 127]),
		PackedByteArray([28, 0, 0, 0, 255, 255, 255, 127]),
		PackedByteArray([4, 0, 0, 0, 1, 0, 0, 0, 255, 0, 0, 0]),
		PackedByteArray([4, 0, 0, 0, 1, 0, 0, 0, 0, 0, 0, 0]),
		PackedByteArray([4, 0, 0, 0, 1, 0, 0, 0, 120, 1, 0, 0])]:
		_reject(_raw_value(raw), "malformed/unsupported raw Variant", "variant")
	var incomplete := PackedByteArray([27, 0, 0, 0, 1, 0, 0, 0])
	_reject(_frame(incomplete), "missing dictionary pair", "variant")
	var trailing := var_to_bytes({})
	trailing.append_array(_u32(TYPE_NIL))
	_reject(_frame(trailing), "Variant trailing bytes", "variant")
	_reject(_frame(var_to_bytes({1: "bad"})), "nonstring wire keys", "variant")
	_reject(_frame(var_to_bytes({"z": 1, "a": 2})), "unsorted wire dictionary", "variant")
	var duplicate := var_to_bytes({"a": 1, "b": 2})
	duplicate[36] = 97 # Second string key bytes begin at 36.
	_reject(_frame(duplicate), "duplicate wire keys", "variant")
	_reject(_frame(var_to_bytes({}), var_to_bytes([])), "invalid metadata root", "variant")
	var nested := _u32(TYPE_NIL)
	for i in Codec.MAX_DEPTH + 1:
		var parent := PackedByteArray([28, 0, 0, 0, 1, 0, 0, 0])
		parent.append_array(nested)
		nested = parent
	_reject(_raw_value(nested), "wire depth cap", "variant")
	var oversized := PackedByteArray([28, 0, 0, 0])
	oversized.append_array(_u32(Codec.MAX_COLLECTION_LENGTH + 1))
	_reject(_raw_value(oversized), "wire collection cap", "variant")
	var huge_string := PackedByteArray([4, 0, 0, 0])
	huge_string.append_array(_u32(Codec.MAX_STRING_BYTES + 1))
	_reject(_raw_value(huge_string), "wire string cap", "variant")
	for utf8 in [PackedByteArray([0xc0, 0x80]), PackedByteArray([0xed, 0xa0, 0x80]),
		PackedByteArray([0xf4, 0x90, 0x80, 0x80]), PackedByteArray([0xe2, 0x82])]:
		var raw := _u32(TYPE_STRING)
		raw.append_array(_u32(utf8.size()))
		raw.append_array(utf8)
		while raw.size() % 4 != 0:
			raw.append(0)
		_reject(_raw_value(raw), "strict UTF-8 rejection", "variant")


func _encoder_limits() -> void:
	var node := Node.new()
	var unsupported: Array = [node, Resource.new(), RefCounted.new(), Callable(self, "_check"),
		Signal(self, "process_frame"), Vector2.ZERO, PackedByteArray([1]), &"string_name", INF, NAN]
	for value in unsupported:
		var result := Codec.encode({"x": value})
		_check(not result.ok and not result.has("bytes"), "encoder rejects unsupported type")
		node.set_meta("untouched", true)
	_check(node.get_meta("untouched"), "rejected object remains usable")
	node.free()
	_check(not Codec.encode({1: "invalid"}).ok, "encoder nonstring key")
	_check(not Codec.encode({}, {"x": Vector2.ZERO}).ok, "metadata same allowlist")
	_check(not Codec.encode({"x": "a".repeat(Codec.MAX_STRING_BYTES + 1)}).ok, "encoder string cap")
	_check(not Codec.encode({"x": "界".repeat(21846)}).ok, "UTF-8 byte cap")
	_check(Codec.encode({"x": "a".repeat(Codec.MAX_STRING_BYTES)}).ok, "string boundary accepted")
	var collection: Array = []
	collection.resize(Codec.MAX_COLLECTION_LENGTH)
	_check(Codec.encode({"x": collection}).ok, "collection boundary accepted")
	collection.append(null)
	_check(not Codec.encode({"x": collection}).ok, "encoder collection cap")
	var depth: Variant = null
	for i in Codec.MAX_DEPTH - 1:
		depth = [depth]
	_check(Codec.encode({"x": depth}).ok, "depth boundary accepted")
	depth = [depth]
	_check(not Codec.encode({"x": depth}).ok, "encoder depth cap")
	var cycle: Array = []
	cycle.append(cycle)
	_check(not Codec.encode({"x": cycle}).ok, "cycle bounded by depth cap")
	cycle.clear() # Release this fixture's self reference.
	var wide: Array = []
	var row: Array = []
	row.resize(Codec.MAX_COLLECTION_LENGTH)
	for i in 16:
		wide.append(row)
	_check(not Codec.encode({"x": wide}).ok, "total element cap with modest fixture")
	_reject(_raw_value(var_to_bytes(wide)), "wire total element cap", "variant")
	var large: Array = []
	for i in 129:
		large.append("a".repeat(Codec.MAX_STRING_BYTES))
	_check(not Codec.encode({"x": large}).ok, "encoder payload byte budget")
	_check(not Codec.encode({}, {"x": "a".repeat(Codec.MAX_METADATA_BYTES)}).ok, "encoder metadata byte budget")


func _files() -> void:
	# Unique directory only; never touch existing owner files or remove unknown paths.
	var directory := "user://codec-synthetic-" + str(Time.get_ticks_usec())
	_check(not DirAccess.dir_exists_absolute(directory), "test directory does not already exist")
	if DirAccess.dir_exists_absolute(directory):
		return
	_check(DirAccess.make_dir_absolute(directory) == OK, "create unique fixture directory")
	var path := directory.path_join("candidate.sav")
	var unrelated := directory.path_join("unrelated.txt")
	var sentinel := FileAccess.open(unrelated, FileAccess.WRITE)
	if sentinel == null:
		_check(false, "create sentinel")
		return
	sentinel.store_string("preserve synthetic sentinel")
	sentinel.close()
	var encoded := Codec.encode({"sections": {"demo": {"version": 3, "data": [1, 2]}}})
	_check(Codec.write_file(path, encoded.bytes).ok, "write candidate")
	var reopened := Codec.read_file(path)
	_check(reopened.ok, "independently reopen candidate")
	if reopened.ok:
		_check(reopened.bytes == encoded.bytes, "disk bytes match")
		_check(Codec.validate_envelope(reopened.bytes).ok, "independent integrity validation")
		_check(Codec.decode(reopened.bytes).ok, "independent decode")
	_check(not Codec.write_file(directory.path_join("absent/failed.sav"), encoded.bytes).ok, "controlled failed write")
	_check(not Codec.read_file(directory.path_join("missing.sav")).ok, "controlled missing file")
	_check(not Codec.write_file(unrelated, PackedByteArray()).ok, "invalid bytes rejected before opening target")
	_check(FileAccess.get_file_as_string(unrelated) == "preserve synthetic sentinel", "unrelated file preserved")
	# Only exact files created above are eligible for fixture cleanup.
	_check(DirAccess.remove_absolute(path) == OK, "remove owned candidate")
	_check(DirAccess.remove_absolute(unrelated) == OK, "remove owned sentinel")
	_check(DirAccess.remove_absolute(directory) == OK, "remove empty owned directory")


func _initialize() -> void:
	_round_trips()
	_integrity_and_framing()
	_malformed_variants()
	_encoder_limits()
	_files()
	print("SAVE_FILE_CODEC: %s checks=%d failures=%d" % ["PASS" if _failures == 0 else "FAIL", _checks, _failures])
	quit(0 if _failures == 0 else 1)
