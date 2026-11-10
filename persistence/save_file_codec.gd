class_name SaveFileCodec
extends RefCounted
## Standalone, storage-neutral codec. No gameplay capture or publication policy.
## See docs/SAVE_FILE_FORMAT.md for the byte contract and validation boundary.

const MAGIC := "TLWHSAV1"
const FORMAT_VERSION := 1
const SNAPSHOT_VERSION := 1
const COMPRESSION_NONE := 0
const HEADER_SIZE := 56
const CHECKSUM_OFFSET := 24
const CHECKSUM_SIZE := 32
const MAX_PAYLOAD_BYTES := 8 * 1024 * 1024
const MAX_METADATA_BYTES := 64 * 1024
const MAX_FILE_BYTES := HEADER_SIZE + MAX_METADATA_BYTES + MAX_PAYLOAD_BYTES
const MAX_COLLECTION_LENGTH := 4096
const MAX_DEPTH := 32
const MAX_STRING_BYTES := 65536
const MAX_ELEMENTS := 65536


static func _error(code: String, message: String) -> Dictionary:
	return {"ok": false, "error": code, "message": message}


static func _budget(limit: int) -> Dictionary:
	return {"elements": 0, "bytes": 0, "limit": limit, "error": ""}


# Validation and copying share one bounded walk. No caller-owned collection changes.
# Typed collections become untyped; unsupported values are never given to the serializer.
static func _normalize(value: Variant, depth: int, budget: Dictionary) -> Variant:
	budget.elements += 1
	budget.bytes += 4
	if depth > MAX_DEPTH or budget.elements > MAX_ELEMENTS:
		budget.error = "Structural limit exceeded."
		return null
	var result: Variant = value
	match typeof(value):
		TYPE_NIL:
			pass
		TYPE_BOOL, TYPE_INT, TYPE_FLOAT:
			if typeof(value) == TYPE_FLOAT and not is_finite(value):
				budget.error = "Only finite floats are supported."
			# Upper bound for native 32/64-bit numeric encoding.
			budget.bytes += 8
			if typeof(value) == TYPE_FLOAT and value == 0.0:
				result = 0.0 # Normalize negative zero.
		TYPE_STRING:
			if value.length() > MAX_STRING_BYTES:
				budget.error = "String limit exceeded or embedded NUL."
				return null
			var utf8: PackedByteArray = value.to_utf8_buffer()
			var length: int = utf8.size()
			if utf8.has(0):
				budget.error = "Embedded NUL is unsupported."
			if length > MAX_STRING_BYTES:
				budget.error = "UTF-8 string limit exceeded."
			budget.bytes += 4 + length + ((4 - length % 4) % 4)
		TYPE_ARRAY, TYPE_DICTIONARY:
			if value.size() > MAX_COLLECTION_LENGTH:
				budget.error = "Collection limit exceeded."
				return null
			budget.bytes += 4
			if typeof(value) == TYPE_ARRAY:
				result = []
				for child in value:
					result.append(_normalize(child, depth + 1, budget))
					if not budget.error.is_empty():
						return null
			else:
				result = {}
				var keys: Array = value.keys()
				for key in keys:
					if typeof(key) != TYPE_STRING:
						budget.error = "Dictionary keys must be Strings."
						return null
				keys.sort()
				for key in keys:
					_normalize(key, depth + 1, budget)
					if not budget.error.is_empty():
						return null
					result[key] = _normalize(value[key], depth + 1, budget)
					if not budget.error.is_empty():
						return null
		_:
			budget.error = "Unsupported Variant type: %s." % typeof(value)
	if budget.bytes > budget.limit:
		budget.error = "Serialized size budget exceeded."
	return result


static func encode(snapshot: Dictionary, metadata: Dictionary = {}) -> Dictionary:
	var payload_budget := _budget(MAX_PAYLOAD_BYTES)
	var normalized: Variant = _normalize(snapshot, 0, payload_budget)
	if not payload_budget.error.is_empty():
		return _error("snapshot", payload_budget.error)
	var metadata_budget := _budget(MAX_METADATA_BYTES)
	var normalized_metadata: Variant = _normalize(metadata, 0, metadata_budget)
	if not metadata_budget.error.is_empty():
		return _error("metadata", metadata_budget.error)
	# var_to_bytes never serializes full objects; the allowlist also rejects IDs.
	var payload := var_to_bytes(normalized)
	var meta := var_to_bytes(normalized_metadata)
	if payload.size() > MAX_PAYLOAD_BYTES or meta.size() > MAX_METADATA_BYTES:
		return _error("size", "Encoded section exceeds its limit.")
	var bytes := PackedByteArray()
	bytes.resize(HEADER_SIZE)
	for i in 8:
		bytes[i] = MAGIC.unicode_at(i)
	bytes.encode_u16(8, FORMAT_VERSION)
	bytes.encode_u16(10, COMPRESSION_NONE)
	bytes.encode_u32(12, meta.size())
	bytes.encode_u32(16, payload.size())
	bytes.encode_u32(20, SNAPSHOT_VERSION)
	bytes.append_array(meta)
	bytes.append_array(payload)
	var digest := _digest(bytes)
	if digest.size() != CHECKSUM_SIZE:
		return _error("hash", "SHA-256 calculation failed.")
	for i in CHECKSUM_SIZE:
		bytes[CHECKSUM_OFFSET + i] = digest[i]
	return {"ok": true, "bytes": bytes}


static func _digest(bytes: PackedByteArray) -> PackedByteArray:
	var context := HashingContext.new()
	if context.start(HashingContext.HASH_SHA256) != OK:
		return PackedByteArray()
	if context.update(bytes.slice(0, CHECKSUM_OFFSET)) != OK:
		return PackedByteArray()
	if context.update(bytes.slice(HEADER_SIZE)) != OK:
		return PackedByteArray()
	return context.finish()


## Framing and integrity only: success does not certify Variant or application schema.
static func validate_envelope(bytes: PackedByteArray) -> Dictionary:
	if bytes.size() < HEADER_SIZE or bytes.size() > MAX_FILE_BYTES:
		return _error("size", "File size outside allowed range.")
	for i in 8:
		if bytes[i] != MAGIC.unicode_at(i):
			return _error("magic", "Unrecognized save magic.")
	if bytes.decode_u16(8) != FORMAT_VERSION:
		return _error("format_version", "Unsupported envelope version.")
	if bytes.decode_u16(10) != COMPRESSION_NONE:
		return _error("compression", "Unsupported compression method.")
	if bytes.decode_u32(20) != SNAPSHOT_VERSION:
		return _error("snapshot_version", "Unsupported global snapshot version.")
	var metadata_size := bytes.decode_u32(12)
	var payload_size := bytes.decode_u32(16)
	if metadata_size < 8 or metadata_size > MAX_METADATA_BYTES or payload_size < 8 or payload_size > MAX_PAYLOAD_BYTES:
		return _error("length", "Declared section length outside allowed range.")
	if HEADER_SIZE + metadata_size + payload_size != bytes.size():
		return _error("length", "Declared lengths do not match the complete file.")
	var digest := _digest(bytes)
	if digest.size() != CHECKSUM_SIZE or digest != bytes.slice(CHECKSUM_OFFSET, HEADER_SIZE):
		return _error("checksum", "Whole-file SHA-256 mismatch.")
	return {"ok": true, "metadata_size": metadata_size, "payload_size": payload_size}


# Strict UTF-8 check before calling native string/Variant decoding. Reject NUL,
# overlong encodings, surrogates and code points beyond U+10FFFF.
static func _valid_utf8(bytes: PackedByteArray, start: int, length: int) -> bool:
	var pos := start
	var end := start + length
	while pos < end:
		var first: int = bytes[pos]
		pos += 1
		if first > 0 and first < 128:
			continue
		var count: int
		var code: int
		var minimum: int
		if first >= 0xc2 and first <= 0xdf:
			count = 1; code = first & 31; minimum = 128
		elif first >= 0xe0 and first <= 0xef:
			count = 2; code = first & 15; minimum = 2048
		elif first >= 0xf0 and first <= 0xf4:
			count = 3; code = first & 7; minimum = 65536
		else:
			return false
		if pos + count > end:
			return false
		for i in count:
			var next: int = bytes[pos]
			pos += 1
			if next < 128 or next > 191:
				return false
			code = (code << 6) | (next & 63)
		if code < minimum or code > 0x10ffff or (code >= 0xd800 and code <= 0xdfff):
			return false
	return true


# Bounded wire preflight prevents hostile count/depth/type fields reaching
# bytes_to_var. No arrays/dictionaries are allocated from external counts here.
static func _scan(bytes: PackedByteArray, state: Dictionary, depth: int, key: bool = false) -> void:
	state.elements += 1
	if depth > MAX_DEPTH or state.elements > MAX_ELEMENTS or state.pos + 4 > bytes.size():
		state.error = "Truncated Variant or structural limit exceeded."
		return
	var header := bytes.decode_u32(state.pos)
	state.pos += 4
	var type := header & 0xffff
	var flags := header >> 16
	if key and type != TYPE_STRING:
		state.error = "Wire dictionary key is not a String."
		return
	if flags != 0 and not (type in [TYPE_INT, TYPE_FLOAT] and flags == 1):
		state.error = "Unsupported Variant flags or typed wire collection."
		return
	match type:
		TYPE_NIL:
			pass
		TYPE_BOOL, TYPE_INT, TYPE_FLOAT:
			var size := 8 if flags == 1 else 4
			if state.pos + size > bytes.size():
				state.error = "Truncated number."
				return
			if type == TYPE_BOOL and bytes.decode_u32(state.pos) > 1:
				state.error = "Invalid Boolean."
			if type == TYPE_FLOAT:
				var number: float = bytes.decode_double(state.pos) if flags == 1 else bytes.decode_float(state.pos)
				if not is_finite(number):
					state.error = "Nonfinite wire float."
			state.pos += size
		TYPE_STRING:
			if state.pos + 4 > bytes.size():
				state.error = "Truncated String length."
				return
			var length := bytes.decode_u32(state.pos)
			state.pos += 4
			var padded := length + ((4 - length % 4) % 4)
			if length > MAX_STRING_BYTES or padded > bytes.size() - state.pos:
				state.error = "Invalid String length."
				return
			if not _valid_utf8(bytes, state.pos, length):
				state.error = "Invalid UTF-8 or embedded NUL."
				return
			for i in range(length, padded):
				if bytes[state.pos + i] != 0:
					state.error = "Nonzero String padding."
			if key:
				state.last_key = bytes.slice(state.pos, state.pos + length).get_string_from_utf8()
			state.pos += padded
		TYPE_ARRAY, TYPE_DICTIONARY:
			if state.pos + 4 > bytes.size():
				state.error = "Truncated collection length."
				return
			var count := bytes.decode_u32(state.pos)
			state.pos += 4
			var children := count * (2 if type == TYPE_DICTIONARY else 1)
			if count > MAX_COLLECTION_LENGTH or children > MAX_ELEMENTS - state.elements or children * 4 > bytes.size() - state.pos:
				state.error = "Collection count exceeds budget or remaining bytes."
				return
			var previous := ""
			for i in count:
				if type == TYPE_DICTIONARY:
					_scan(bytes, state, depth + 1, true)
					if not state.error.is_empty():
						return
					var current: String = state.last_key
					if i > 0 and not previous < current:
						state.error = "Dictionary keys must be unique and sorted."
						return
					previous = current
				_scan(bytes, state, depth + 1)
				if not state.error.is_empty():
					return
		_:
			state.error = "Non-allowlisted wire Variant type."


static func _decode_section(bytes: PackedByteArray, limit: int) -> Dictionary:
	if bytes.size() < 8 or bytes.decode_u32(0) != TYPE_DICTIONARY:
		return _error("variant", "Section root must be an untyped Dictionary.")
	var state := {"pos": 0, "elements": 0, "error": "", "last_key": ""}
	_scan(bytes, state, 0)
	if not state.error.is_empty() or state.pos != bytes.size():
		return _error("variant", "Invalid restricted Variant: " + state.error)
	# Intentionally use bytes_to_var, NEVER bytes_to_var_with_objects.
	var value: Variant = bytes_to_var(bytes)
	if typeof(value) != TYPE_DICTIONARY:
		return _error("variant", "Variant decoding did not return a Dictionary.")
	var budget := _budget(limit)
	var normalized: Variant = _normalize(value, 0, budget)
	if not budget.error.is_empty():
		return _error("variant", budget.error)
	return {"ok": true, "value": normalized}


static func decode(bytes: PackedByteArray) -> Dictionary:
	var envelope := validate_envelope(bytes)
	if not envelope.ok:
		return envelope
	var split: int = HEADER_SIZE + envelope.metadata_size
	var metadata := _decode_section(bytes.slice(HEADER_SIZE, split), MAX_METADATA_BYTES)
	if not metadata.ok:
		return metadata
	var snapshot := _decode_section(bytes.slice(split), MAX_PAYLOAD_BYTES)
	if not snapshot.ok:
		return snapshot
	return {"ok": true, "snapshot": snapshot.value, "metadata": metadata.value,
		"snapshot_version": SNAPSHOT_VERSION}


static func read_file(path: String) -> Dictionary:
	var file := FileAccess.open(path, FileAccess.READ)
	if file == null:
		return _error("read_open", "Cannot open file: %s." % FileAccess.get_open_error())
	var size := file.get_length()
	if size < HEADER_SIZE or size > MAX_FILE_BYTES:
		file.close()
		return _error("size", "File size outside allowed range.")
	var bytes := file.get_buffer(size)
	var read_error := file.get_error()
	var final_size := file.get_length()
	file.close()
	if read_error != OK or bytes.size() != size or final_size != size:
		return _error("read", "Incomplete or changed file while reading.")
	return {"ok": true, "bytes": bytes}


## Low-level write: the caller owns destination selection and publication.
## May truncate that destination. No atomicity/durability promise; no directory creation.
static func write_file(path: String, bytes: PackedByteArray) -> Dictionary:
	var checked := decode(bytes)
	if not checked.ok:
		return checked # Invalid input cannot truncate an existing destination.
	var file := FileAccess.open(path, FileAccess.WRITE)
	if file == null:
		return _error("write_open", "Cannot open destination: %s." % FileAccess.get_open_error())
	file.store_buffer(bytes)
	file.flush()
	var write_error := file.get_error()
	var size := file.get_length()
	file.close()
	if write_error != OK or size != bytes.size():
		return _error("write", "Incomplete file write: %s." % write_error)
	return {"ok": true}
