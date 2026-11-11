"""Independent byte vectors and source boundaries; never executes GDScript/Godot."""
import hashlib
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = (ROOT / "persistence/publication_journal.gd").read_text(encoding="utf-8")
RUNTIME = (ROOT / "tests/publication_journal_test.gd").read_text(encoding="utf-8")
SPEC = (ROOT / "docs/PUBLICATION_JOURNAL.md").read_text(encoding="utf-8")


def body(name):
    return re.search(rf"^static func {name}\(.*?(?=^static func |\Z)",
                     CODE, re.M | re.S).group()


def golden(name):
    return bytes.fromhex(re.search(rf'const {name} := "([0-9a-f]+)"', RUNTIME)[1])


def record(snapshot, sequence=1):
    prefix = struct.pack("<8sHHI", b"TLWHJRN1", 1, 0, len(snapshot))
    footer = struct.pack("<8sHHIQ", b"TLWHCMT1", 1, 0, len(snapshot), sequence)
    covered = prefix + snapshot + footer
    return covered + hashlib.sha256(covered).digest()


def manifest(journal, sequence=1, generation=1):
    fields = struct.pack("<8sHHQQQ", b"TLWHMAN1", 1, 0, sequence,
                         generation, len(journal)) + hashlib.sha256(journal).digest()
    return fields + hashlib.sha256(fields).digest()


class PublicationJournalStaticTests(unittest.TestCase):
    def test_independent_nested_codec_vector(self):
        fields = struct.pack("<8sHHIII", b"TLWHSAV1", 1, 0, 8, 8, 1)
        dictionaries = struct.pack("<IIII", 27, 0, 27, 0)
        snapshot = fields + hashlib.sha256(fields + dictionaries).digest() + dictionaries
        self.assertEqual(snapshot, golden("EMPTY_GOLDEN"))
        self.assertEqual(len(snapshot), 72)

    def test_independent_record_golden(self):
        encoded = record(golden("EMPTY_GOLDEN"))
        self.assertEqual(encoded, golden("RECORD_GOLDEN"))
        self.assertEqual(len(encoded), 144)
        self.assertEqual(struct.unpack_from("<8sHHI", encoded), (b"TLWHJRN1", 1, 0, 72))
        self.assertEqual(encoded[16:88], golden("EMPTY_GOLDEN"))
        self.assertEqual(struct.unpack_from("<8sHHIQ", encoded, 88),
                         (b"TLWHCMT1", 1, 0, 72, 1))

    def test_independent_manifest_golden(self):
        encoded = manifest(golden("RECORD_GOLDEN"))
        self.assertEqual(encoded, golden("MANIFEST_GOLDEN"))
        self.assertEqual(len(encoded), 100)
        self.assertEqual(struct.unpack_from("<8sHHQQQ", encoded),
                         (b"TLWHMAN1", 1, 0, 1, 1, 144))
        self.assertEqual(encoded[36:68], hashlib.sha256(golden("RECORD_GOLDEN")).digest())
        self.assertEqual(encoded[68:], hashlib.sha256(encoded[:68]).digest())

    def test_record_digest_covers_every_framing_and_snapshot_byte(self):
        encoded = golden("RECORD_GOLDEN")
        for offset in range(112):
            changed = bytearray(encoded)
            changed[offset] ^= 1
            self.assertNotEqual(hashlib.sha256(changed[:112]).digest(), encoded[112:], offset)
        self.assertNotEqual(hashlib.sha256(encoded[:112] + bytes(32)).digest(), encoded[112:])
        self.assertEqual(hashlib.sha256(encoded[:112]).digest(), encoded[112:])

    def test_manifest_digest_covers_every_field_and_journal_digest_byte(self):
        encoded = golden("MANIFEST_GOLDEN")
        for offset in range(68):
            changed = bytearray(encoded)
            changed[offset] ^= 1
            self.assertNotEqual(hashlib.sha256(changed[:68]).digest(), encoded[68:], offset)
        self.assertNotEqual(hashlib.sha256(encoded[:68] + bytes(32)).digest(), encoded[68:])

    def test_manifest_binds_history_not_just_latest_record(self):
        snapshot = golden("EMPTY_GOLDEN")
        full = record(snapshot) + record(snapshot, 2)
        self.assertNotEqual(manifest(full)[36:68], manifest(record(snapshot, 2))[36:68])
        self.assertEqual(manifest(full)[36:68], hashlib.sha256(full).digest())

    def test_unsigned_layout_and_signed_supported_counter_boundary(self):
        maximum = (1 << 63) - 1
        self.assertEqual(struct.unpack_from("<Q", record(golden("EMPTY_GOLDEN"), maximum), 104)[0], maximum)
        self.assertEqual(struct.pack("<Q", maximum), b"\xff" * 7 + b"\x7f")
        self.assertEqual(struct.pack("<Q", 1 << 63)[7], 128)
        increment = body("_next_sequence")
        self.assertLess(increment.index("value == MAX_COUNTER"), increment.index("value + 1"))
        decode = body("decode_manifest")
        self.assertLess(decode.index("& 0x80"), decode.index("decode_u64"))
        self.assertIn("[12, 20, 28]", decode)

    def test_framing_and_history_limits(self):
        self.assertEqual(16 + 72 + 56, 144)
        self.assertEqual(16 + 8454200 + 56, 8454272)
        self.assertEqual(5 * 8454272, 42271360)
        for name, value in {"PREFIX_SIZE": 16, "FOOTER_SIZE": 56, "MANIFEST_SIZE": 100,
                            "MIN_SNAPSHOT_BYTES": 72, "MAX_SNAPSHOT_BYTES": 8454200,
                            "MIN_RECORD_BYTES": 144, "MAX_RECORD_BYTES": 8454272,
                            "HISTORY_LIMIT": 5, "MAX_COUNTER": (1 << 63) - 1}.items():
            self.assertRegex(CODE, rf"const {name} := {value}\b")
        self.assertIn('size < MIN_SNAPSHOT_BYTES or size > MAX_SNAPSHOT_BYTES', body("_record_at"))

    def test_record_validation_is_bounded_and_complete(self):
        scan = body("_record_at")
        self.assertLess(scan.index("size > MAX_SNAPSHOT_BYTES"), scan.index("bytes.slice("))
        self.assertLess(scan.index("size > remaining - PREFIX_SIZE"), scan.index("_snapshot(snapshot_bytes)"))
        self.assertIn("Codec.decode(bytes)", body("_snapshot"))
        self.assertNotIn("validate_envelope(", CODE)
        self.assertIn("footer_offset + 24", scan)
        self.assertIn("digest[i]", scan)
        self.assertIn("footer_available < FOOTER_SIZE", scan)
        self.assertIn("lower_bound > MAX_SNAPSHOT_BYTES", scan)
        self.assertIn("remaining == 15 and lower_bound < MIN_SNAPSHOT_BYTES", scan)

    def test_recovery_stops_on_first_bad_record_and_marks_salvage(self):
        recovery = body("recover_journal")
        self.assertRegex(recovery, r"if not record.ok:\s+terminal = record\s+break")
        self.assertIn('"authoritative": false', recovery)
        self.assertIn('"committed_length": offset', recovery)
        self.assertIn('"has_snapshot": count > 0', recovery)
        self.assertIn("_next_sequence(expected)", recovery)
        self.assertNotRegex(recovery, r"\.(find|rfind)\(")

    def test_generation_revalidates_even_discarded_history(self):
        build = body("build_generation")
        self.assertLess(build.index("_snapshot(entry)"), build.index("history.slice("))
        self.assertIn("HISTORY_LIMIT - 1", build)
        self.assertIn("selected.append(new_snapshot)", build)
        self.assertIn("encode_record(selected[i], i + 1)", build)
        self.assertNotIn("history.append(", build)
        self.assertNotIn("history.pop", build)

    def test_authority_cannot_accept_salvage_or_forged_validation_result(self):
        validate = body("_validate_generation")
        self.assertLess(validate.index("manifest.committed_length != journal_bytes.size()"),
                        validate.index("recover_journal(journal_bytes)"))
        self.assertLess(validate.index("digest != manifest.journal_digest"),
                        validate.index("recover_journal(journal_bytes)"))
        self.assertRegex(validate, r'if not journal.ok:\s+#[^\n]+\s+return _error\(')
        self.assertIn("decode_manifest(manifest_bytes)", body("validate_generation"))
        select = body("select_authority")
        self.assertIn("decode_manifest(slot)", select)
        self.assertLess(select.index('"authority_conflict"'), select.index("generations.get("))
        self.assertIn("candidate.publication_sequence > selected.publication_sequence", select)
        self.assertIn('"missing_generation"', select)
        self.assertIn("selected.diagnostics = diagnostics", select)

    def test_pure_module_and_synthetic_suite_have_no_io_or_gameplay_calls(self):
        for text in (CODE, RUNTIME):
            executable = "\n".join(line.split("#")[0] for line in text.splitlines())
            for forbidden in ("FileAccess", "DirAccess", "OS.", "Thread.", "user://", "get_tree(",
                              "write_file(", "read_file(", "bytes_to_var(", "load(", "assert("):
                # preload is restricted to exact standalone modules below.
                self.assertNotIn(forbidden, executable.replace("preload(", "PRELOAD("))
            preloads = re.findall(r'preload\("([^"]+)"\)', executable)
            self.assertTrue(set(preloads) <= {"res://persistence/save_file_codec.gd",
                                            "res://persistence/publication_journal.gd"})
        self.assertIn("extends RefCounted", CODE)
        self.assertIn("extends SceneTree", RUNTIME)

    def test_runtime_assertions_are_independent_and_not_runner_dispatched(self):
        fixture_code = RUNTIME[RUNTIME.index("func _hash("):RUNTIME.index("func _reject(")]
        self.assertNotIn("Journal.", fixture_code)
        for label in ("truncated record at", "partial length already oversized", "overflow before addition",
                      "full codec validation required", "reject invalid discarded history",
                      "conflict before missing generation filtering", "orphans never promoted",
                      "bound damaged generation cannot authorize salvage"):
            self.assertIn(label, RUNTIME)
        runner = (ROOT / "tools/run-save-codec-tests.ps1").read_text(encoding="utf-8")
        self.assertIn("return 'PREPARED'", runner)
        self.assertNotIn("publication_journal", runner)

    def test_documented_contract_and_validation_limits(self):
        for method in ("encode_record", "recover_journal", "build_generation", "encode_manifest",
                       "decode_manifest", "validate_generation", "select_authority"):
            self.assertIn(f"static func {method}(", CODE)
            self.assertIn(f"`{method}", SPEC)
        for term in ("TLWHJRN1", "TLWHCMT1", "TLWHMAN1", "[0,68)", "8,454,272",
                     "42,271,360", "2^63", "incomplete_tail", "authority_conflict",
                     "no_authority", "not executed", "not authenticate", "pending merge"):
            self.assertIn(term, SPEC)


if __name__ == "__main__":
    unittest.main()
