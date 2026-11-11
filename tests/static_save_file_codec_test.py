"""Offline format vectors and safety boundaries, not GDScript/runtime verification."""
import hashlib
from pathlib import Path
import re
import struct
import unittest

ROOT = Path(__file__).resolve().parents[1]
CODE = (ROOT / "persistence/save_file_codec.gd").read_text(encoding="utf-8")
RUNTIME = (ROOT / "tests/save_file_codec_test.gd").read_text(encoding="utf-8")
SPEC = (ROOT / "docs/SAVE_FILE_FORMAT.md").read_text(encoding="utf-8")


def body(name):
    return re.search(rf"^static func {name}\(.*?(?=^static func |\Z)",
                     CODE, re.M | re.S).group()


class SaveFileCodecStaticTests(unittest.TestCase):
    def test_independent_empty_file_vector(self):
        header = struct.pack("<8sHHIII", b"TLWHSAV1", 1, 0, 8, 8, 1)
        sections = struct.pack("<IIII", 27, 0, 27, 0)
        self.assertEqual(len(header), 24)
        golden = header + hashlib.sha256(header + sections).digest() + sections
        expected = re.search(r'const EMPTY_GOLDEN := "([0-9a-f]+)"', RUNTIME)[1]
        self.assertEqual(golden.hex(), expected)
        self.assertEqual(len(golden), 72)
        self.assertEqual(struct.unpack_from("<HHIII", golden, 8), (1, 0, 8, 8, 1))
        self.assertEqual(golden[56:64], struct.pack("<II", 27, 0))

    def test_digest_covers_all_other_bytes(self):
        golden = bytes.fromhex(re.search(r'const EMPTY_GOLDEN := "([0-9a-f]+)"', RUNTIME)[1])
        digest = lambda data: hashlib.sha256(data[:24] + data[56:]).digest()
        self.assertEqual(digest(golden), golden[24:56])
        for offset in list(range(24)) + list(range(56, len(golden))):
            changed = bytearray(golden)
            changed[offset] ^= 1
            self.assertNotEqual(digest(changed), golden[24:56], offset)
        self.assertNotEqual(hashlib.sha256(golden[:24] + bytes(32) + golden[56:]).digest(),
                            golden[24:56], "omission differs from zero filling")

    def test_native_decode_follows_integrity_and_bounded_wire_scan(self):
        decode = body("decode")
        self.assertLess(decode.index("validate_envelope(bytes)"), decode.index("_decode_section("))
        section = body("_decode_section")
        self.assertLess(section.index("_scan(bytes"), section.index("bytes_to_var(bytes)"))
        self.assertLess(section.index("bytes_to_var(bytes)"), section.index("_normalize(value"))
        executable = "\n".join(line.split("#")[0] for line in CODE.splitlines())
        self.assertEqual(executable.count("bytes_to_var("), 1)
        for forbidden in ("bytes_to_var_with_objects(", "str_to_var(", "load(",
                          "preload(", "get_tree(", "assert("):
            self.assertNotIn(forbidden, executable)
        for guard in ("MAX_DEPTH", "MAX_ELEMENTS", "MAX_COLLECTION_LENGTH", "MAX_STRING_BYTES",
                      "_valid_utf8", "previous < current", "TYPE_STRING", "flags"):
            self.assertIn(guard, body("_scan"))

    def test_low_level_io_checks_before_read_or_truncation(self):
        read = body("read_file")
        self.assertLess(read.index("size > MAX_FILE_BYTES"), read.index("get_buffer(size)"))
        write = body("write_file")
        self.assertLess(write.index("decode(bytes)"), write.index("FileAccess.open"))
        self.assertIn("file.flush()", write)
        self.assertIn("file.get_error()", write)
        self.assertNotIn("DirAccess", CODE)

    def test_format_and_limit_contract_is_explicit(self):
        for name, value in {"HEADER_SIZE": 56, "CHECKSUM_OFFSET": 24, "CHECKSUM_SIZE": 32,
                            "MAX_DEPTH": 32, "MAX_COLLECTION_LENGTH": 4096,
                            "MAX_STRING_BYTES": 65536, "MAX_ELEMENTS": 65536}.items():
            self.assertRegex(CODE, rf"const {name} := {value}\b")
        self.assertEqual(56 + 65536 + 8 * 1024 * 1024, 8454200)
        for term in ("8,454,200", "unsigned little endian", "not authenticate", "32 edges",
                     "no gameplay callers", "does not dispatch this codec suite"):
            self.assertIn(term, SPEC)
        for method in ("encode", "validate_envelope", "decode", "read_file", "write_file"):
            self.assertIn(f"static func {method}(", CODE)
        self.assertNotIn('"snapshot"', body("_error"))
        self.assertNotIn('"metadata"', body("_error"))


if __name__ == "__main__":
    unittest.main()
