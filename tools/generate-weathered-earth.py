"""Reproduce four PROVISIONAL mathematical test textures, never concept crops.

Run with --check for read-only byte verification. No dependencies or Godot use.
Existing differing files are never overwritten.
"""
import argparse
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "assets/environment/exterior/weathered_earth_provisional"
NAMES = ("a_base_soil", "b_compacted_soil", "c_dusty_patches", "d_subtle_gravel")


def value(x, y, period):
    number = ((x % period) * 374761393 + (y % period) * 668265263 + 26026) & 0xffffffff
    number = ((number ^ (number >> 13)) * 1274126177) & 0xffffffff
    return (number ^ (number >> 16)) / 4294967295.0 - 0.5


def noise(x, y, period):
    px, py = x * period / 127, y * period / 127
    ix, iy = math.floor(px), math.floor(py)
    fx, fy = px - ix, py - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    north = value(ix, iy, period) * (1 - fx) + value(ix + 1, iy, period) * fx
    south = value(ix, iy + 1, period) * (1 - fx) + value(ix + 1, iy + 1, period) * fx
    return north * (1 - fy) + south * fy


def png_bytes(treatment):
    scan = bytearray()
    for y in range(128):
        scan.append(0)  # Unfiltered opaque RGB8 scanline.
        for x in range(128):
            common = sum(noise(x, y, p) * a for p, a in ((4, 5), (16, 7), (64, 9)))
            # Identical eight-pixel border strips for ALL treatments and both
            # opposing edges; interior differences fade in without a hard rim.
            distance = min(x, y, 127 - x, 127 - y)
            fade = max(0.0, min(1.0, (distance - 8) / 24))
            fade = fade * fade * (3 - 2 * fade)
            delta = (0, -4, 5, noise(x, y, 96) * 10)[treatment] * fade
            scan.extend(max(0, min(255, round(base + common + delta))) for base in (156, 141, 121))

    def chunk(kind, data):
        return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data))

    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 128, 128, 8, 2, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(bytes(scan), 9)) + chunk(b"IEND", b""))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true")
    args = parser.parse_args()
    for treatment, name in enumerate(NAMES):
        path = OUTPUT / (name + ".png")
        expected = png_bytes(treatment)
        if args.check or path.exists():
            if path.read_bytes() != expected:
                raise SystemExit(f"Texture differs; preserved existing bytes: {path}")
        else:
            OUTPUT.mkdir(parents=True, exist_ok=True)
            with path.open("xb") as stream:
                stream.write(expected)
        print(f"{'Verified' if args.check else 'Ready'} PROVISIONAL {name}: 128x128 opaque RGB")
