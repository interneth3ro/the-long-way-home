"""Offline PNG reconstruction only. Never imports project code or invokes Godot.

Optional archive gate: python -B tests/extractor_artwork_offline.py --packages DIR
No archive scripts are executed and no files are extracted or changed.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import struct
import zipfile
import zlib

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/experiments/extractor_static_artwork.json"


def decode_png(data):
    """Decode the frozen noninterlaced RGBA8 PNG format using only stdlib."""
    assert data[:8] == b"\x89PNG\r\n\x1a\n"
    cursor, compressed = 8, bytearray()
    while cursor < len(data):
        length = struct.unpack_from(">I", data, cursor)[0]
        kind = data[cursor + 4:cursor + 8]
        payload = data[cursor + 8:cursor + 8 + length]
        crc = struct.unpack_from(">I", data, cursor + 8 + length)[0]
        assert zlib.crc32(kind + payload) & 0xffffffff == crc
        if kind == b"IHDR":
            w, h, bits, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
            assert (bits, color, compression, filtering, interlace) == (8, 6, 0, 0, 0)
        elif kind == b"IDAT":
            compressed.extend(payload)
        cursor += length + 12
        if kind == b"IEND":
            break
    assert cursor == len(data)
    raw = zlib.decompress(compressed)
    stride = w * 4
    assert len(raw) == h * (stride + 1)
    out, previous = bytearray(), bytearray(stride)
    for y in range(h):
        start = y * (stride + 1)
        mode = raw[start]
        assert mode in range(5)
        row = bytearray(raw[start + 1:start + 1 + stride])
        if mode:
            for x in range(stride):
                left = row[x - 4] if x >= 4 else 0
                up = previous[x]
                upper_left = previous[x - 4] if x >= 4 else 0
                if mode == 1:
                    predictor = left
                elif mode == 2:
                    predictor = up
                elif mode == 3:
                    predictor = (left + up) // 2
                else:
                    prediction = left + up - upper_left
                    distances = [abs(prediction - v) for v in (left, up, upper_left)]
                    predictor = (left, up, upper_left)[distances.index(min(distances))]
                row[x] = (row[x] + predictor) & 255
        out.extend(row)
        previous = row
    return w, h, out


def configured_layers():
    script = (ROOT / "construction/extractor_visual.gd").read_text()
    paths = re.findall(r'preload\("res://([^"\n]+\.png)"\)', script)
    section = script.split("const OFFSETS := [", 1)[1].split("@onready", 1)[0]
    offsets = [tuple(map(int, p)) for p in re.findall(r"Vector2\((-?\d+), (-?\d+)\)", section)]
    assert len(paths) == len(offsets) == 12
    return list(zip(paths, offsets))


def place(pixels, w, h, offset, composite):
    x, y = offset
    assert 0 <= x and 0 <= y and x + w <= 1254 and y + h <= 1254
    for sy in range(h):
        for sx in range(w):
            source = (sy * w + sx) * 4
            dest = ((sy + y) * 1254 + sx + x) * 4
            sa, da = pixels[source + 3], composite[dest + 3]
            if sa == 0:
                continue
            if sa == 255 or da == 0:
                composite[dest:dest + 4] = pixels[source:source + 4]
                continue
            alpha = sa * 255 + da * (255 - sa)
            for channel in range(3):
                composite[dest + channel] = (pixels[source + channel] * sa * 255
                    + composite[dest + channel] * da * (255 - sa) + alpha // 2) // alpha
            composite[dest + 3] = (alpha + 127) // 255


def different(a, b):
    assert len(a) == len(b)
    return sum(a[i:i + 4] != b[i:i + 4] for i in range(0, len(a), 4))


def verify_archives(directory, motion=False):
    records = json.loads(INVENTORY.read_text())["directions"]
    configured = configured_layers()
    for direction_index, record in enumerate(records):
        archive = directory / record["archive"]
        before = hashlib.sha256(archive.read_bytes()).hexdigest()
        assert before == record["archive_sha256"]
        with zipfile.ZipFile(archive) as z:
            assert z.testzip() is None
            manifest = json.loads(z.read(record["manifest"]).decode("utf-8-sig"))
            prefix = record["manifest"].rsplit("/", 1)[0] + "/"
            assert manifest["assets"] == record["assets"]
            assert manifest["master"] == record["master"]
            assert manifest["calibration"]["world_units_per_source_pixel"] == record["scale"]
            assert manifest["output_ports"] == record["output_ports"]
            reconstructed = bytearray(1254 * 1254 * 4)
            for index, asset in enumerate(manifest["assets"]):
                path, offset = configured[direction_index * 3 + index]
                data = (ROOT / path).read_bytes()
                assert data == z.read(prefix + asset["path"])
                assert hashlib.sha256(data).hexdigest() == asset["sha256"]
                assert list(offset) == asset["anchor_relative_offset_px"]
                w, h, pixels = decode_png(data)
                assert [w, h] == asset["exported_size_px"] == asset["crop_rect_px"][2:]
                master_offset = (offset[0] + 632, offset[1] + 1139)
                assert list(master_offset) == asset["crop_rect_px"][:2]
                fw, fh, full = decode_png(z.read(prefix + asset["source_path"]))
                assert (fw, fh) == (1254, 1254)
                # Raw copy also checks transparent RGB and pixels outside the crop.
                layer = bytearray(1254 * 1254 * 4)
                x, y = master_offset
                for row in range(h):
                    dest = ((y + row) * 1254 + x) * 4
                    layer[dest:dest + w * 4] = pixels[row * w * 4:(row + 1) * w * 4]
                assert different(layer, full) == 0, path
                place(pixels, w, h, master_offset, reconstructed)
            for reference in (manifest["master"]["source"], "previews/reconstructed_raised.png"):
                rw, rh, expected = decode_png(z.read(prefix + reference))
                assert (rw, rh) == (1254, 1254)
                count = different(reconstructed, expected)
                print(f'{record["direction"]} degrees / {reference}: {count} differing RGBA pixels')
                assert count == 0
            if motion:
                verify_motion(z, prefix, manifest, configured[direction_index * 3:direction_index * 3 + 3])
        assert hashlib.sha256(archive.read_bytes()).hexdigest() == before
        print(f'{record["direction"]} degrees: archive CRC, identity, 3 byte-identical PNGs and full layers PASS')


def verify_motion(archive, prefix, manifest, layers):
    """Integer source-space poses, not filtered rendering or artistic acceptance."""
    direction = manifest["output_ports"][0]["orientation"]
    maximum = 8 if direction in (0, 90) else 6
    assert manifest["motion"]["axis"] == "master_positive_y_is_down"
    poses = manifest["motion"]["representative_positions"]
    assert [(p["name"], p["y_offset_px"]) for p in poses] == [
        ("raised", 0), ("downstroke", maximum), ("return", 3)]
    decoded = [(decode_png((ROOT / path).read_bytes()), offset) for path, offset in layers]
    raised_alpha = None
    for stroke in range(maximum + 1):
        composite = bytearray(1254 * 1254 * 4)
        for index, ((w, h, pixels), (x, y)) in enumerate(decoded):
            # place() rejects canvas clipping; fixed body/foreground never move.
            place(pixels, w, h, (x + 632, y + 1139 + (stroke if index == 1 else 0)), composite)
        alpha = composite[3::4]
        if raised_alpha is None:
            raised_alpha = alpha
        holes = sum(a == 255 and b == 0 for a, b in zip(raised_alpha, alpha))
        print(f'{direction} degrees / stroke {stroke}: {holes} formerly opaque pixels now transparent')
        assert holes == 0, "new fully transparent hole relative to raised silhouette"
        for pose in poses:
            if pose["y_offset_px"] != stroke:
                continue
            w, h, expected = decode_png(archive.read(prefix + f'previews/reconstructed_{pose["name"]}.png'))
            assert (w, h) == (1254, 1254)
            count = different(composite, expected)
            print(f'{direction} degrees / {pose["name"]}: {count} differing RGBA pixels')
            assert count == 0, "pose differs from accepted reference (including concealed continuation)"


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--packages", type=Path, required=True)
    parser.add_argument("--motion", action="store_true", help="also check integer barrel strokes and package pose references")
    args = parser.parse_args()
    verify_archives(args.packages, args.motion)
