"""Isolated offline artwork study. No engine, production writes or dependencies.

--write creates only a new, fixed prototype directory. --check regenerates in
memory and compares saved bytes. Historical baker is imported read-only; its
build function is never called and its globals are never changed.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / 'assets/experiments/native_terrain_47_96'
OUTPUT = BASE / 'ground_refinement_v1'
BASE_REVISION = 'ec95accbab05dd580dc15a3176b8e76457861d2f'
PARAMETERS = dict(period=127, box_radii=[2, 7, 18], low_gain=.14,
                  middle_gain=.06, fine_gain=.025, residual_gain=.008,
                  variant_strength=.45, feather_remap=[.20, .80],
                  working_color_space='linear RGB; sRGB encoding',
                  preview_variant_rule='fixed coordinate buckets 60/25/15; offline only')
INPUT_SHA256 = {
    'assets/experiments/native_terrain_47_96/baked_v2/baseline_94.png':
        '5a3d448774fc2dc816f02827b75ecca1f1a57678e5023f383525cb811aff1977',
    'assets/experiments/native_terrain_47_96/baked_v2/interiors_bc.png':
        '01de466fcec2e7ed8e8cadf9813a57d3783eb57b50ec56408a9ba0346357efc8',
    'assets/experiments/native_terrain_47_96/baked_v2/baked_terrain.tres':
        'e70237fe02222ccd3b9da8e96a27320d642a7244605e258012f44f4f666f3256',
    'assets/experiments/native_terrain_47_96/baked_v2/mapping.json':
        '7702325b9d235ee7edc7f5ab0e6bdaa23db6f2ee8293f297a5d90449bb98d867',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/earth_solid.png':
        '1e530bdcefa9ba29575b8bd2c61a15ec26c04567b928ffebfb4b460336d4ff3f',
    'assets/experiments/native_terrain_47_96/illustrated_v1/originals/green_solid.png':
        'bc64176fde0d899dfd8c56d42a62fc81525e780c3b22687b982bde31244270e2',
    'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv':
        '678c107702c1b933510a36101f77f04e4f7277cfab7c86ced25a1ed086100e4c',
    'tools/bake-illustrated-terrain.py':
        '2227fe4b280dd3538ed435ace64af5540b7061be3dbe396633df8cd931d6acdf',
}


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def checked_inputs():
    """Match the repository's existing LF-normalized text identity convention."""
    raw_hashes = {}
    for name, expected in INPUT_SHA256.items():
        raw = (ROOT / name).read_bytes()
        raw_hashes[name] = digest(raw)
        canonical = raw if name.endswith(('.png', '.csv')) else raw.replace(b'\r\n', b'\n')
        if digest(canonical) != expected:
            raise ValueError('Unexpected protected input: ' + name)
    return raw_hashes


def load_baker():
    checked_inputs()
    spec = importlib.util.spec_from_file_location('historical_terrain_baker', ROOT / 'tools/bake-illustrated-terrain.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def periodic_box(values, radius):
    """Separable periodic box on the unique 127x127 texels, not clamped blur."""
    n = 127
    length = 2 * radius + 1
    horizontal = [0.0] * (n*n)
    result = [0.0] * (n*n)
    for y in range(n):
        total = sum(values[y*n + (x % n)] for x in range(-radius, radius+1))
        for x in range(n):
            horizontal[y*n+x] = total / length
            total += values[y*n+(x+radius+1) % n] - values[y*n+(x-radius) % n]
    for x in range(n):
        total = sum(horizontal[(y % n)*n+x] for y in range(-radius, radius+1))
        for y in range(n):
            result[y*n+x] = total / length
            total += horizontal[((y+radius+1) % n)*n+x] - horizontal[((y-radius) % n)*n+x]
    return result


def refine(source, bake):
    # Preserve each channel's linear mean. Compress separate spatial bands;
    # retain faint fine texture rather than replacing the source with a flat fill.
    channels = []
    for c in range(3):
        original = [bake.to_linear(source[(y*128+x)*3+c]) for y in range(127) for x in range(127)]
        fine, middle, low = [periodic_box(original, r) for r in PARAMETERS['box_radii']]
        mean = sum(original) / len(original)
        values = [mean + PARAMETERS['low_gain']*(lo-mean) + PARAMETERS['middle_gain']*(mi-lo)
                  + PARAMETERS['fine_gain']*(fi-mi) + PARAMETERS['residual_gain']*(o-fi)
                  for o, fi, mi, lo in zip(original, fine, middle, low)]
        correction = mean - sum(values)/len(values)
        channels.append([bake.to_srgb(v+correction) for v in values])
    # Copy first row/column to final row/column exactly, matching saved art's
    # duplicate-endpoint sampling contract. No per-tile edge repair.
    return bytes(channels[c][(y % 127)*127+(x % 127)]
                 for y in range(128) for x in range(128) for c in range(3))


def variants(source, bake):
    linear = [tuple(bake.to_linear(c) for c in source[i:i+3]) for i in range(0, len(source), 3)]
    result = [source]
    for variant in (1, 2):
        pixels = bytearray()
        for y in range(128):
            for x in range(128):
                sx, sy = ((127-x+37) % 128, (127-y+59) % 128) if variant == 1 else ((y+79) % 128, (127-x+23) % 128)
                strength = 0 if x in (0, 127) or y in (0, 127) else PARAMETERS['variant_strength']*math.sin(math.pi*x/127)**2*math.sin(math.pi*y/127)**2
                pixels.extend(bake.to_srgb(a+(b-a)*strength) for a, b in zip(linear[y*128+x], linear[sy*128+sx]))
        result.append(bytes(pixels))
    return result


def crop(pixels, width, x, y):
    return b''.join(pixels[((y*128+dy)*width+x*128)*3:((y*128+dy)*width+(x+1)*128)*3] for dy in range(128))


def edge(pixels, side):
    if side == 'top':
        return pixels[:384]
    if side == 'bottom':
        return pixels[-384:]
    x = 0 if side == 'left' else 127
    return b''.join(pixels[(y*128+x)*3:(y*128+x)*3+3] for y in range(128))


def board(width, height):
    return (width, height, bytearray(bytes((23, 30, 28))*width*height))


def paste(canvas, image, x, y, scale=1):
    width, height, pixels = image
    target_width = round(width*scale)
    target_height = round(height*scale)
    assert x >= 0 and y >= 0 and x+target_width <= canvas[0] and y+target_height <= canvas[1]
    for yy in range(target_height):
        sy = min(height-1, int(yy/scale))
        row = bytearray()
        for xx in range(target_width):
            sx = min(width-1, int(xx/scale))
            offset = (sy*width+sx)*3
            row.extend(pixels[offset:offset+3])
        offset = ((y+yy)*canvas[0]+x)*3
        canvas[2][offset:offset+len(row)] = row


# Tiny fixed bitmap labels keep generation independent of installed fonts/apps.
GLYPHS = dict(zip('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 /:.-', [
    '01110100011000111111100011000110001','11110100011000111110100011000111110',
    '01111100001000010000100001000001111','11110100011000110001100011000111110',
    '11111100001000011110100001000011111','11111100001000011110100001000010000',
    '01111100001000010111100011000101111','10001100011000111111100011000110001',
    '11111001000010000100001000010011111','00111000100001000010100101001001100',
    '10001100101010011000101001001010001','10000100001000010000100001000011111',
    '10001110111010110101100011000110001','10001110011010110011100011000110001',
    '01110100011000110001100011000101110','11110100011000111110100001000010000',
    '01110100011000110001101011001001101','11110100011000111110101001001010001',
    '01111100001000001110000010000111110','11111001000010000100001000010000100',
    '10001100011000110001100011000101110','10001100011000110001100010101000100',
    '10001100011000110101101011101110001','10001100010101000100010101000110001',
    '10001100010101000100001000010000100','11111000010001000100010001000011111',
    '01110100011001110101110011000101110','00100011000010000100001000010001110',
    '01110100010000100010001000100011111','11110000010000101110000010000111110',
    '00010001100101010010111110001000010','11111100001000011110000010000111110',
    '01110100001000011110100011000101110','11111000010001000100010000100001000',
    '01110100011000101110100011000101110','01110100011000101111000010000101110',
    '00000000000000000000000000000000000','00001000100001000100010000100010000',
    '00000001000010000000001000010000000','00000000000000000000000000010000100',
    '00000000000000011111000000000000000']))


def text(canvas, label, x, y, size=2):
    for char in label.upper():
        bits = GLYPHS[char]
        for yy in range(7):
            for xx in range(5):
                if bits[yy*5+xx] == '1':
                    for dy in range(size):
                        offset = ((y+yy*size+dy)*canvas[0]+x+xx*size)*3
                        canvas[2][offset:offset+3*size] = bytes((224, 232, 224))*size
        x += 6*size


def pair(title, original, refined, gameplay_only=False):
    width, height = original[:2]
    scale = .5 if gameplay_only else 1
    w, h = round(width*scale), round(height*scale)
    result = board(2*w+48, h+112+(round(height*.5)+44 if not gameplay_only else 0))
    text(result, 'OFFLINE STUDY / '+title, 16, 12)
    text(result, 'ORIGINAL / '+('64' if gameplay_only else '128')+' PX PER TILE', 16, 42)
    text(result, 'REFINED / SAME LAYOUT', w+32, 42)
    paste(result, original, 16, 70, scale)
    paste(result, refined, w+32, 70, scale)
    if not gameplay_only:
        text(result, 'APPROXIMATE GAMEPLAY SCALE / 64 PX PER TILE / NO RUNTIME SHADING', 16, h+88)
        paste(result, original, 16, h+116, .5)
        paste(result, refined, w+32, h+116, .5)
    return result


def build():
    """Return all generated bytes in memory. No writes, temp files or engine."""
    checked_inputs()
    bake = load_baker()
    mapping = json.loads((BASE/'baked_v2/mapping.json').read_text())
    entries = {tuple(e['signature']): e for e in mapping['baseline']}
    # Exact historical input, never execute or rewrite the evidence's renderer.
    preview_path = ROOT/'artifacts/evidence/pr100-stage2-baked-v2/previews.json'
    preview_raw = preview_path.read_bytes()
    historical = json.loads(preview_raw)
    originals = [bake.sources[c] for c in (0, 1)]
    refined = [refine(p, bake) for p in originals]
    materials = [variants(p, bake) for p in refined]
    source_atlas = bake.decode_png((BASE/'baked_v2/baseline_94.png').read_bytes())[2]
    source_interiors = bake.decode_png((BASE/'baked_v2/interiors_bc.png').read_bytes())[2]
    old = {(sig, 0): crop(source_atlas, 1536, *e['atlas']) for sig, e in entries.items()}
    for e in mapping['interiors']:
        old[tuple(e['signature']), 'ABC'.index(e['variant'])] = crop(source_interiors, 256, *e['atlas'])
    layouts = {}
    for name in ('green_patch_varied', 'earth_patch_varied', 'meandering_boundary_varied'):
        record = next(p for p in historical['previews'] if p['name'] == name)
        layouts[name] = [[(tuple(c['signature']), 'ABC'.index(c['variant'])) for c in row] for row in record['cells']]
    # Larger authored mathematical study field; this is neither world generation
    # nor a production resolver change. Classify peers with existing rule-1 ANDs.
    def sample(x, y):
        return int(math.sin(x*.43) + .62*math.cos(y*.54) + .28*math.sin((x+y)*.71) > .25)
    mixed = []
    for y in range(16):
        row = []
        for x in range(24):
            c = sample(x, y)
            nw, n, ne, w, e, sw, s, se = [sample(x+dx, y+dy) for dx, dy in
                                         ((-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1))]
            sig = (c, c*n*w*nw, c*n, c*n*e*ne, c*w, c*e, c*s*w*sw, c*s, c*s*e*se)
            bucket = (x*37+y*61+19) % 100
            variant = (0 if bucket < 60 else 1 if bucket < 85 else 2) if sig == (c,)*9 else 0
            assert sig in entries
            row.append((sig, variant))
        mixed.append(row)
    layouts['mixed_24x16'] = mixed
    representative_coords = [(9,2),(8,0),(5,1),(0,0),(0,1),(0,3),(10,0),(9,3),(8,1),(11,2),
                             (9,6),(8,4),(5,5),(0,4),(0,5),(0,7),(10,4),(9,7),(8,5),(11,6)]
    by_coord = {tuple(e['atlas']): sig for sig, e in entries.items()}
    representatives = [by_coord[p] for p in representative_coords]
    subset = set(representatives)
    for layout in layouts.values():
        subset.update(sig for row in layout for sig, _ in row)
    assert len(subset) < 94
    current, masks = {}, {}
    feather_counts = [0, 0]
    for sig in sorted(subset):
        original_mask = bake.mask(sig)
        lo, hi = PARAMETERS['feather_remap']
        mask = [bake.smooth((v-lo)/(hi-lo)) for v in original_mask]
        masks[sig] = mask
        feather_counts[0] += sum(0 < v < 1 for v in original_mask)
        feather_counts[1] += sum(0 < v < 1 for v in mask)
        earth, green = materials[0][0], materials[1][0]
        pixels = bytearray()
        for i, weight in enumerate(mask):
            pixels.extend(bake.to_srgb(bake.lerp(bake.to_linear(a), bake.to_linear(b), weight))
                          for a, b in zip(earth[i*3:i*3+3], green[i*3:i*3+3]))
        current[sig, 0] = bytes(pixels)
    for c in (0, 1):
        for variant in (1, 2):
            current[(c,)*9, variant] = materials[c][variant]
    files = {'.gdignore': b''}
    for c, name in enumerate(('earth', 'green')):
        files['sources/'+name+'_refined.png'] = bake.encode_png(128, 128, refined[c])
    atlas = bytearray(bytes((23, 30, 28))*1536*1024)
    records = []
    for sig in sorted(subset):
        e = entries[sig]
        bake.copy_cell(atlas, 1536, *e['atlas'], current[sig, 0])
        records.append(dict(atlas=e['atlas'], signature=sig, variant='A', family=e['family'],
                            pattern=e['pattern'], pixel_sha256=digest(current[sig, 0])))
    files['baseline_subset.png'] = bake.encode_png(1536, 1024, atlas)
    interiors = bytearray(256*256*3)
    for c in (0, 1):
        for v in (1, 2):
            bake.copy_cell(interiors, 256, v-1, c, current[(c,)*9, v])
    files['interiors_bc.png'] = bake.encode_png(256, 256, interiors)

    def assemble(layout, tiles):
        image = board(len(layout[0])*128, len(layout)*128)
        for y, row in enumerate(layout):
            for x, key in enumerate(row):
                paste(image, (128, 128, tiles[key]), x*128, y*128)
        return image

    def save_pair(name, title, layout, gameplay_only=False):
        image = pair(title, assemble(layout, old), assemble(layout, current), gameplay_only)
        files['previews/'+name+'.png'] = bake.encode_png(*image)

    for c, name in enumerate(('earth', 'green')):
        layout = [[((c,)*9, 0)]*4 for _ in range(2)]
        save_pair(name+'_interior', name+' INTERIOR A', layout)
    repeat = [[((c,)*9, (x+2*y) % 3) for x in range(6)] for c in (0, 1) for y in range(2)]
    save_pair('abc_repetition', 'EARTH THEN GREEN / A B C REPEATED', repeat)
    # Separate unrelated samples with gutters: this board is a contact sheet,
    # not a claim that arbitrary neighboring representative tiles join.
    def contact(tiles):
        result = board(5*136, 4*152)
        names = ('SOLID','CONVEX','CONCAVE','ENDPOINT','LINK',
                 'ISLAND','NORTH','SOUTH','WEST','EAST')
        for i, (sig, coords) in enumerate(zip(representatives, representative_coords)):
            x, y = (i % 5)*136, (i // 5)*152
            text(result, names[i % 10]+' '+str(coords[0])+':'+str(coords[1]), x, y, 1)
            paste(result, (128,128,tiles[sig,0]), x, y+12)
        return result
    image = pair('SEPARATE TILES / EARTH THEN GREEN', contact(old), contact(current))
    files['previews/transitions.png'] = bake.encode_png(*image)
    save_pair('meandering_boundary', 'MEANDERING BOUNDARY', layouts['meandering_boundary_varied'])
    save_pair('mixed_24x16', 'MIXED 24 X 16 / OFFLINE FIELD', mixed, True)
    manifest = dict(status='isolated artwork prototype; owner visual acceptance pending',
                    base_revision=BASE_REVISION, parameters=PARAMETERS,
                    input_hash_convention='PNGs and CSV raw; text CRLF normalized to LF',
                    input_sha256=INPUT_SHA256, historical_preview_sha256=digest(preview_raw.replace(b'\r\n', b'\n')),
                    baseline_count=len(records), baseline=records,
                    interiors=[dict(atlas=[v-1,c], signature=[c]*9, variant='ABC'[v], pixel_sha256=digest(current[(c,)*9,v]))
                               for c in (0,1) for v in (1,2)],
                    representative_order=representative_coords,
                    feather_nonpure_texels=dict(original=feather_counts[0], refined=feather_counts[1]),
                    layouts={name: [[dict(signature=sig, variant='ABC'[v], baseline_atlas=entries[sig]['atlas'])
                                      for sig,v in row] for row in layout] for name,layout in layouts.items()},
                    output_sha256={name: digest(raw) for name, raw in sorted(files.items())})
    files['manifest.json'] = (json.dumps(manifest, indent=2)+'\n').encode()
    checked_inputs()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write', action='store_true')
    mode.add_argument('--check', action='store_true')
    args = parser.parse_args()
    if args.write and OUTPUT.exists():
        parser.error('Refusing existing prototype directory: '+str(OUTPUT))
    files = build()
    if args.check:
        for name, raw in files.items():
            if (OUTPUT/name).read_bytes() != raw:
                raise ValueError('Regeneration mismatch: '+name)
        print('PASS: deterministic byte regeneration of', len(files), 'prototype outputs; no writes.')
    else:
        OUTPUT.mkdir(exist_ok=False)
        for name, raw in files.items():
            path = OUTPUT/name
            path.parent.mkdir(exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
        print('Created', len(files), 'isolated files. No engine or production integration.')


if __name__ == '__main__':
    main()
