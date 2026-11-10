"""Read-only Smelter PNG/provenance checks; no package scripts or Godot execution.

--active checks repository artifacts and historical Git bodies.
--freeze-dir additionally checks all four archives, receipts, original packages,
full source layers and exact accepted-master crop pixels (including hidden RGB).
"""
import argparse
import hashlib
import json
from pathlib import Path, PurePosixPath
import stat
import subprocess
import zipfile

from extractor_artwork_offline import decode_png, place

ROOT = Path(__file__).resolve().parents[1]
INVENTORY = ROOT / "docs/experiments/smelter_static_artwork.json"
ACTIVE_INVENTORY = ROOT / "docs/experiments/smelter_port_free_runtime_v1.json"
HISTORICAL_REF = "39ad7c09b0bbd5c01f63bede7d376c3e4baf170c"
BODY_PATHS = tuple(f"assets/machines/smelter/smelter_{d}_body.png" for d in (0, 90, 180, 270))
CROPS = ((37, 97, 1188, 1008), (161, 14, 934, 1156),
         (38, 89, 1170, 1048), (162, 72, 925, 1115))
# Encoded output, independently decoded fixed-crop RGBA, measured exclusive bounds.
ACTIVE_IDENTITIES = (
    ("25f6bafda4129913180be164ae92548f6c57492f34757408e25095656ed81c8e",
     "a4abd7aaa90a34dd7c1a0aedf38a960da0fa0f59a4b0411870691d29c1c1cde5", [12, 4, 1175, 1004]),
    ("a2cde3e730c17c72fecc64d22710449436bccc51120aaca3ba488c8832ee17f0",
     "f0fc63ae28b77187b43c0348dd75e6c5f090810b5914313d1f3fb4b059b870e3", [4, 4, 930, 1145]),
    ("7361280fb4b78f7719ea1dd2692070205d2fb73d2a1b8640a88282f930104aad",
     "ac90fe20b1d71471426bcabe3a828abd55fa879a3026a04dc5888e7ef241bc1c", [14, 4, 1156, 1044]),
    ("c363971c6e5e8309b144d17a6eb73633243e86cc8880ee7ea27f504d6e41a9c0",
     "4280cdcf3a5af163022c7a3dc0c7fb71f6f6ee6f2853ab9bf44bd67597436952", [4, 4, 921, 1104]),
)
PRESENTATION_PATHS = (
    "construction/smelter_visual.gd", "construction/smelter_visual.gd.uid",
    "construction/smelter_visual.tscn", "construction/machine_visual.gd",
    "docs/experiments/smelter_static_artwork.json",
)
# Independent freeze pins, not inferred from mutable provenance or preview labels.
# direction, ZIP, receipt, manifest, accepted master, manifest member, master member
FREEZES = (
    (0, "1cae74ab0dce259bcacb4d53ede293a1a9d53172fffe218fb4c4db41f429bd3a",
     "200c903433c1298c8beb62cd905e98201a84dc280399525e484362185fc48a8e",
     "09708d2f5d8eb6b40d7895757eb931158ac3028c594e958d7681ac371d98471f",
     "67b0635894398db3d38ddc0e5fb781e0f92800748f8fa506ac523270181c48d9",
     "preservation_manifest.json", "accepted_prototype/source/smelter_0_body_port_free_master.png"),
    (90, "1dd773744ce28af1da57141e3890c43d7a105644da69a99e0932734263228bea",
     "ef9f17cf3dc4619dcb498c67d0b447e8ddf21823eabd14b27c8ed503fe42ea84",
     "1d7d16a814329b41e6c9809abd1b85850d8447f840e336fafebce298af82c873",
     "ffa369c3c55357498e7c30df5052095e62f6dec872dd4c8b8bb2e02918d7a1ea",
     "preservation_manifest.json", "accepted_prototype/source/smelter_90_body_port_free_master.png"),
    (180, "b35916eef53a06bc0df55bb61584441028d55bb90da2c88bab938b5899cc81d1",
     "3e0d02d59a35fe137e091e975bb2e2a54c89ea885ca995e0b4437334098061cb",
     "8d70208386cd31118523a0d4a9f2ec18ce944d25d510c0683d25b826968704fb",
     "d7d5c7bb2bd7824146ef5fec957032a9b95ad9bd0697b92ebc5cc44b585c8b23",
     "preservation/aggregate_manifest.json", "accepted_derivative/artwork/smelter_180_port_free_body_master.png"),
    (270, "72553e1c602e0a7924ef16983c66dbe2095e56e94181fefedff23b4a4b35d671",
     "9366f0749f350059b1c745e064b4f83eec9eae7f9183eaf86e7d0b8eab0a02e3",
     "a74a73ae169e3a0fdf1dfbd6223a44a9ed55f55bc8f56b5176a2ab472c95176a",
     "a66b6c25bd9412f89a5a541256fb99367a7fed54ef83bf010a333e5e16a242c2",
     "preservation/aggregate_manifest.json", "artwork/smelter_270_body_port_free_master.png"),
)


def sha(data):
    return hashlib.sha256(data).hexdigest()


def historical_bytes(path):
    """Missing history is a failure, never a fallback to the active derivative."""
    return subprocess.check_output(["git", "show", f"{HISTORICAL_REF}:{path}"], cwd=ROOT)


def alpha_bounds(w, h, rgba):
    points = [i for i, a in enumerate(rgba[3::4]) if a]
    assert points, "empty artwork"
    return [min(i % w for i in points), min(i // w for i in points),
            max(i % w for i in points) + 1, max(i // w for i in points) + 1]


def crop_pixels(raw, rect):
    w, h, pixels = decode_png(raw)  # Independently checks CRC, RGBA8 and filters.
    assert (w, h) == (1254, 1254)
    x, y, cw, ch = rect
    assert 0 <= x < x + cw <= w and 0 <= y < y + ch <= h
    for row in range(h):
        data = pixels[row * w * 4:(row + 1) * w * 4]
        outside = data if row < y or row >= y + ch else data[:x * 4] + data[(x + cw) * 4:]
        assert not any(outside), "discarded pixels must be zero RGBA"
    return b"".join(pixels[((y + row) * w + x) * 4:((y + row) * w + x + cw) * 4]
                    for row in range(ch))


def safe_member(name):
    path = PurePosixPath(name)
    assert name and not path.is_absolute() and "\\" not in name and ":" not in name
    assert all(part not in ("", ".", "..") for part in name.split("/"))
    return name


def frozen_inputs(directory):
    """Verify all inputs before callers derive anything; only read frozen files.

    Original package locations are consumed privately from hash-pinned metadata;
    they are never printed or copied into repository provenance.
    """
    records = json.loads(INVENTORY.read_text())["directions"]
    verified = []
    for index, (pin, old) in enumerate(zip(FREEZES, records)):
        d, archive_sha, receipt_sha, manifest_sha, master_sha, manifest_member, master_member = pin
        name = f"TLWH_Smelter_{d}_PortFree_Artwork_v1"
        archive, receipt_path = directory / (name + ".zip"), directory / (name + ".receipt.json")
        assert sha(archive.read_bytes()) == archive_sha, f"{d}: archive identity"
        receipt_raw = receipt_path.read_bytes()
        assert sha(receipt_raw) == receipt_sha, f"{d}: receipt identity"
        receipt = json.loads(receipt_raw)
        prefix = name + "/"
        with zipfile.ZipFile(archive) as z:
            names = z.namelist()
            assert len(names) == len(set(names))
            for info in z.infolist():
                safe_member(info.filename)
                assert info.filename.startswith(prefix) and not info.is_dir()
                assert not stat.S_ISLNK(info.external_attr >> 16)
                assert info.file_size <= 100_000_000 and not info.flag_bits & 1
            raw = z.read(prefix + manifest_member)
            assert sha(raw) == manifest_sha
            manifest = json.loads(raw)
            if d == 0:
                members = {prefix + k: v for k, v in manifest["members"].items()}
                assert set(names) == set(manifest["expected_members"])
            elif d == 180:
                members = {r["archive_member"]: r for r in manifest["protected_members"]}
            else:
                members = {prefix + r["path"]: r for r in manifest["protected_members"]}
            assert set(names) == set(members) | {prefix + manifest_member}
            for member, identity in members.items():
                payload = z.read(member)  # ZipFile checks each CRC on full read.
                size = identity.get("bytes", identity.get("size", identity.get("size_bytes")))
                assert (len(payload), sha(payload)) == (size, identity["sha256"]), member
            if d == 0:
                source_root = Path(receipt["source_packages"]["original"])
                mapping = {n.removeprefix(prefix + "original_source/"): n for n in names
                           if n.startswith(prefix + "original_source/")}
            elif d == 90:
                snapshot = manifest["source_snapshots"]["original_90"]
                source_root = Path(snapshot["source_directory"])
                mapping = {r["path"]: prefix + "original_90/" + r["path"] for r in snapshot["inventory"]}
            elif d == 180:
                snapshot = manifest["source_packages"]["original_stage3b"]
                source_root = Path(snapshot["root"])
                mapping = {p: prefix + "original_source/" + p for p in snapshot["files"]}
            else:
                snapshots = json.loads(z.read(prefix + manifest["source_snapshots"]["mapping"]))
                snapshot = snapshots["packages"]["original"]
                source_root = Path(snapshot["source_root"])
                mapping = {r["path"]: prefix + r["member"] for r in snapshot["files"]}
                # Verify both logical inventories, including all deduplicated aliases.
                for package in snapshots["packages"].values():
                    for r in package["files"]:
                        payload = z.read(prefix + safe_member(r["member"]))
                        assert (len(payload), sha(payload)) == (r["bytes"], r["sha256"])
            assert len(mapping) == (31, 27, 31, 40)[index]
            assert {p.relative_to(source_root).as_posix() for p in source_root.rglob("*") if p.is_file()} == set(mapping)
            for logical, member in mapping.items():
                safe_member(logical)
                local = source_root / logical
                assert local.resolve().is_relative_to(source_root.resolve())
                assert local.read_bytes() == z.read(member), f"{d}: original source {logical}"
            original_manifest_raw = z.read(mapping[old["manifest"]])
            assert sha(original_manifest_raw) == old["manifest_sha256"]
            original_manifest = json.loads(original_manifest_raw)
            original_full = {}
            for asset, layer in zip(old["assets"], original_manifest["layers"]):
                assert asset["role"] == layer["id"]
                runtime = z.read(mapping[layer["runtime"]])
                assert runtime == historical_bytes(asset["path"])
                assert sha(runtime) == asset["sha256"]
                source = z.read(mapping[layer["source"]])
                assert sha(source) == asset["source_master_sha256"]
                assert crop_pixels(source, asset["crop_rect_px"]) == decode_png(runtime)[2]
                original_full[asset["role"]] = source
            master = z.read(prefix + master_member)
            assert sha(master) == master_sha
            crop = crop_pixels(master, CROPS[index])
            verified.append((master, crop, original_full, {
                "archive": archive.name, "bytes": archive.stat().st_size,
                "entry_count": len(names), "sha256": archive_sha,
                "receipt": receipt_path.name, "receipt_sha256": receipt_sha,
                "manifest_entry": prefix + manifest_member, "manifest_sha256": manifest_sha,
                "original_manifest_entry": mapping[old["manifest"]],
                "original_manifest_sha256": old["manifest_sha256"],
                "original_source_files": len(mapping),
            }))
        assert sha(archive.read_bytes()) == archive_sha
        assert sha(receipt_path.read_bytes()) == receipt_sha
        print(f"{d} degrees: archive/receipt/manifest/master and {len(mapping)} original source files PASS")
    return verified


def composite(record, body_rgba, opacity):
    """Integer source-over reference, not Godot filtering or artistic acceptance."""
    out = bytearray(1254 * 1254 * 4)
    for asset in record["assets"]:
        w, h, pixels = decode_png((ROOT / asset["path"]).read_bytes())
        if asset["role"] == "body":
            pixels = bytearray(body_rgba)
        elif asset["role"] == "illumination":
            pixels[3::4] = bytes(round(a * opacity) for a in pixels[3::4])
        place(pixels, w, h, tuple(asset["crop_rect_px"][:2]), out)
    return out


def verify_active_artifacts():
    active = json.loads(ACTIVE_INVENTORY.read_text())
    records = json.loads(INVENTORY.read_text())["directions"]
    assert active["historical_git_revision"] == HISTORICAL_REF
    assert tuple(b["path"] for b in active["bodies"]) == BODY_PATHS
    preserved = []
    for index, (body, old, pin) in enumerate(zip(active["bodies"], records, FREEZES)):
        asset = old["assets"][0]
        assert body["direction"] == old["direction"] == pin[0]
        assert body["source_sha256"] == pin[4]
        assert body["source_path"] == f"TLWH_Smelter_{pin[0]}_PortFree_Artwork_v1/" + pin[6]
        assert body["canvas_px"] == old["master_size_px"] == [1254, 1254]
        assert body["crop_rect_px"] == asset["crop_rect_px"] == list(CROPS[index])
        assert body["dimensions_px"] == asset["size_px"] == list(CROPS[index][2:])
        assert body["offset_px"] == asset["anchor_relative_offset_px"]
        assert body["original_runtime_sha256"] == asset["sha256"] == sha(historical_bytes(asset["path"]))
        assert body["original_source_sha256"] == asset["source_master_sha256"]
        png_hash, rgba_hash, expected_bounds = ACTIVE_IDENTITIES[index]
        assert (body["png_sha256"], body["rgba_sha256"], body["alpha_bounds_px"]) == (png_hash, rgba_hash, expected_bounds)
        raw = (ROOT / body["path"]).read_bytes()
        assert (len(raw), sha(raw)) == (body["bytes"], body["png_sha256"])
        w, h, rgba = decode_png(raw)
        assert [w, h] == body["dimensions_px"]
        assert sha(rgba) == body["rgba_sha256"] == body["source_crop_rgba_sha256"]
        reconstructed = bytearray(1254 * 1254 * 4)
        x, y, _, _ = CROPS[index]
        for row in range(h):
            start = ((y + row) * 1254 + x) * 4
            reconstructed[start:start + w * 4] = rgba[row * w * 4:(row + 1) * w * 4]
        assert sha(reconstructed) == body["source_rgba_sha256"]
        bounds = alpha_bounds(w, h, rgba)
        assert bounds == body["alpha_bounds_px"]
        assert bounds[0] >= 4 and bounds[1] >= 4 and bounds[2] <= w - 4 and bounds[3] <= h - 4
        for layer in old["assets"]:
            if layer["role"] != "body":
                assert sha((ROOT / layer["path"]).read_bytes()) == layer["sha256"]
                preserved.append({"path": layer["path"], "sha256": layer["sha256"]})
        freeze = body["freeze"]
        assert (freeze["sha256"], freeze["receipt_sha256"], freeze["manifest_sha256"]) == pin[1:4]
    assert active["preserved_supporting_layers"] == preserved
    expected_imports = [a["path"] + ".import" for r in records for a in r["assets"]]
    assert [r["path"] for r in active["preserved_imports"]] == expected_imports
    assert tuple(r["path"] for r in active["preserved_presentation"]) == PRESENTATION_PATHS
    for item in active["preserved_imports"] + active["preserved_presentation"]:
        raw = (ROOT / item["path"]).read_bytes()
        # Repository text follows platform LF/CRLF checkout conventions.
        assert raw.replace(b"\r\n", b"\n") == historical_bytes(item["path"]).replace(b"\r\n", b"\n")
        assert sha(raw.replace(b"\r\n", b"\n")) == item["lf_sha256"]
    return active


def verify_active_source(directory):
    active = verify_active_artifacts()
    for body, (master, crop, _, freeze) in zip(active["bodies"], frozen_inputs(directory)):
        assert body["freeze"] == freeze
        assert sha(decode_png(master)[2]) == body["source_rgba_sha256"]
        assert crop == decode_png((ROOT / body["path"]).read_bytes())[2]
        assert sha(crop) == body["source_crop_rgba_sha256"]
        print(f'{body["direction"]} degrees: exact accepted-master crop RGBA equality PASS')


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--active", action="store_true")
    parser.add_argument("--freeze-dir", type=Path)
    args = parser.parse_args()
    if not args.active and args.freeze_dir is None:
        parser.error("supply --active and/or --freeze-dir")
    if args.active:
        verify_active_artifacts()
        print("Active Smelter identities, historical bodies, supporting layers, imports and presentation PASS")
    if args.freeze_dir is not None:
        verify_active_source(args.freeze_dir)
