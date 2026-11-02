# Sanitized historical source derivative; not independently reproducible.
# Provenance: docs/experiments/repository_housekeeping_stage2c.json
"""Owner-authorized OFFLINE Stage 1 proof. No engine or repository resource edits.

Standard-library-only PNG decoding/baking. Intentionally renders a representative
subset, not the complete 94-tile atlas. See manifest.json for exact signatures.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import subprocess
import zipfile
import zlib

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
ASSET = ROOT / 'assets/experiments/native_terrain_47_96/illustrated_v1'
INVENTORY = ROOT / 'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv'
PACKAGE = Path('<HISTORICAL_REFERENCE_PACKAGE_ZIP>')
BITS = ('top_left_corner', 'top_side', 'top_right_corner', 'left_side',
        'right_side', 'bottom_left_corner', 'bottom_side', 'bottom_right_corner')
SIZE = 128


def decode_png(raw):
    assert raw[:8] == b'\x89PNG\r\n\x1a\n'
    pos, packed = 8, bytearray()
    while pos < len(raw):
        n = struct.unpack_from('>I', raw, pos)[0]
        kind, data = raw[pos+4:pos+8], raw[pos+8:pos+8+n]
        assert zlib.crc32(kind+data) == struct.unpack_from('>I', raw, pos+8+n)[0]
        if kind == b'IHDR':
            width, height, *mode = struct.unpack('>IIBBBBB', data)
            assert mode == [8, 2, 0, 0, 0]
        if kind == b'IDAT':
            packed.extend(data)
        pos += n+12
    assert pos == len(raw)
    scan = zlib.decompress(packed)
    stride = width*3
    assert len(scan) == height*(stride+1)
    previous, result = bytearray(stride), bytearray()
    for y in range(height):
        offset = y*(stride+1)
        filtering = scan[offset]
        assert filtering in range(5)
        row = bytearray(scan[offset+1:offset+1+stride])
        for x in range(stride):
            a = row[x-3] if x >= 3 else 0
            b = previous[x]
            c = previous[x-3] if x >= 3 else 0
            p = a+b-c
            distances = (abs(p-a), abs(p-b), abs(p-c))
            paeth = (a, b, c)[distances.index(min(distances))]
            row[x] = (row[x]+(0, a, b, (a+b)//2, paeth)[filtering]) % 256
        result.extend(row)
        previous = row
    return width, height, bytes(result)


def encode_png(width, height, pixels):
    def chunk(kind, data):
        return struct.pack('>I', len(data))+kind+data+struct.pack('>I', zlib.crc32(kind+data))
    assert len(pixels) == width*height*3
    scan = b''.join(b'\0'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            + chunk(b'IDAT', zlib.compress(scan, 9)) + chunk(b'IEND', b''))


def save_png(path, width, height, pixels):
    with (OUT/path).open('xb') as stream:
        stream.write(encode_png(width, height, pixels))


def digest(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t*t*(3-2*t)


def smoother(t):
    return t*t*t*(t*(6*t-15)+10)


def lerp(a, b, t):
    return a+(b-a)*t


def to_linear(value):
    value /= 255
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4


def to_srgb(value):
    value = max(0.0, min(1.0, value))
    value = value*12.92 if value <= .0031308 else 1.055*value**(1/2.4)-.055
    return round(value*255)


rows = list(csv.DictReader(INVENTORY.open(newline='')))
lookup = {(int(r['tlwh_center']), *(int(r['tlwh_'+b]) for b in BITS)): r for r in rows}
assert len(rows) == len(lookup) == 94
originals = [decode_png((ASSET/'originals'/name).read_bytes())
             for name in ('earth_solid.png', 'green_solid.png')]
assert all(item[:2] == (SIZE, SIZE) for item in originals)
sources = [item[2] for item in originals]
for source in sources:
    assert source[:SIZE*3] == source[-SIZE*3:]
    assert all(source[y*SIZE*3:y*SIZE*3+3] == source[(y*SIZE+127)*3:(y*SIZE+128)*3]
               for y in range(SIZE))

# Three source-derived material alternatives. No palette change, new painting,
# random brightness or variation on edges. Blend in linear light.
material = {}
for terrain, source in enumerate(sources):
    for variant in range(3):
        pixels = []
        for y in range(SIZE):
            for x in range(SIZE):
                index = (y*SIZE+x)*3
                base = tuple(to_linear(c) for c in source[index:index+3])
                if variant == 0 or x in (0,127) or y in (0,127):
                    pixels.append(base)
                    continue
                u, v = x/127, y/127
                envelope = math.sin(math.pi*u)**2 * math.sin(math.pi*v)**2
                if variant == 1:
                    sx, sy = (127-x+37) % 128, (127-y+59) % 128
                else:
                    sx, sy = (y+79) % 128, (127-x+23) % 128
                shifted_index = (sy*SIZE+sx)*3
                shifted = tuple(to_linear(c) for c in source[shifted_index:shifted_index+3])
                pixels.append(tuple(lerp(a, b, .80*envelope) for a,b in zip(base, shifted)))
        material[terrain,variant] = pixels

# A single globally periodic perturbation is used on shared edges. It vanishes
# at binary anchors through 4*f*(1-f). No per-signature seam-repair strip.
geometry = []
for y in range(SIZE):
    for x in range(SIZE):
        u, v = x/127, y/127
        qx, qy = min(1, int(u*2)), min(1, int(v*2))
        tx, ty = smoother(u*2-qx), smoother(v*2-qy)
        nu, nv = (0 if x == 127 else u), (0 if y == 127 else v)
        noise = (.60*math.sin(2*math.pi*nu+.45)*math.sin(2*math.pi*nv+1.2)
                 + .25*math.sin(2*math.pi*(3*nu+2*nv)+1.1)
                 + .15*math.sin(2*math.pi*(7*nu-5*nv)+.3))
        geometry.append((qx, qy, tx, ty, noise))

mask_cache, tile_cache = {}, {}


def mask(signature):
    if signature in mask_cache:
        return mask_cache[signature]
    c,nw,n,ne,w,e,sw,s,se = signature
    grid = ((nw,n,ne), (w,c,e), (sw,s,se))
    result = []
    for qx,qy,tx,ty,noise in geometry:
        field = lerp(lerp(grid[qy][qx], grid[qy][qx+1], tx),
                     lerp(grid[qy+1][qx], grid[qy+1][qx+1], tx), ty)
        field += .16 * 4*field*(1-field) * noise
        result.append(smooth((field-.26)/.48))
    for px,py,index in ((64,64,0),(0,0,1),(64,0,2),(127,0,3),
                        (0,64,4),(127,64,5),(0,127,6),(64,127,7),(127,127,8)):
        assert round(result[py*128+px]) == signature[index]
    mask_cache[signature] = result
    return result


def tile(signature, variant):
    key = signature, variant
    if key not in tile_cache:
        weights = mask(signature)
        earth, green = material[0,variant], material[1,variant]
        tile_cache[key] = bytes(to_srgb(lerp(a,b,t)) for t,ep,gp in zip(weights,earth,green)
                                for a,b in zip(ep,gp))
    return tile_cache[key]


for folder in ('representatives','masks','variants','previews','references'):
    (OUT/folder).mkdir()

representatives = []
for c in (0,1):
    o = 1-c
    specs = [('solid', [c]*8), ('convex_nw', [o,o,o,o,c,o,c,c]),
             ('concave_nw', [o,c,c,c,c,c,c,c]), ('endpoint_south', [o,o,o,o,o,o,c,o]),
             ('narrow_ns', [o,c,o,o,o,o,c,o]), ('isolated', [o]*8)]
    for name,indices in [('north',(0,1,2)),('south',(5,6,7)),('west',(0,3,5)),('east',(2,4,7))]:
        peers = [c]*8
        for index in indices:
            peers[index] = o
        specs.append((name, peers))
    for name,peers in specs:
        signature = (c,*peers)
        row = lookup[signature]
        family = ('earth','green')[c]
        stem = f'{family}_{name}_{row["atlas_x"]}_{row["atlas_y"]}'
        image_path, mask_path = 'representatives/'+stem+'.png', 'masks/'+stem+'.png'
        save_png(image_path, 128,128,tile(signature,0))
        save_png(mask_path,128,128,bytes(round(v*255) for v in mask(signature) for _ in range(3)))
        representatives.append(dict(name=family+' '+name, image=image_path, mask=mask_path,
                                    signature=signature, original_atlas=[int(row['atlas_x']),int(row['atlas_y'])]))
    for variant in (1,2):
        save_png(f'variants/{family}_{variant}.png',128,128,tile((c,)*9,variant))

PATCH = ['000000000000','000111100000','001111111000','001110111100',
         '000110011000','000111111000','000001100000','000000000000']
COAST = ['000000111111','000001111111','000111111111','000011111111',
         '000001111111','000011111111','001111111111','001111111111']
GROUPS = [[(-1,-1),(0,-1),(-1,0),(0,0)],[(0,-1),(0,0)],
          [(0,-1),(1,-1),(0,0),(1,0)],[(-1,0),(0,0)],[(0,0),(1,0)],
          [(-1,0),(0,0),(-1,1),(0,1)],[(0,0),(0,1)],[(0,0),(1,0),(0,1),(1,1)]]
preview_records = []


def assemble(name, layout, invert, vary):
    width, height = len(layout[0]), len(layout)
    at = lambda x,y: int(layout[min(height-1,max(0,y))][min(width-1,max(0,x))])
    result = bytearray(width*height*SIZE*SIZE*3)
    cells = []
    for y in range(height):
        line = []
        for x in range(width):
            # OR chooses a shared Green-owned boundary before role inversion.
            # This is one valid illustrative layout, not a Godot Connect replica.
            signature = tuple(v^invert for v in [at(x,y),*[max(at(x+dx,y+dy)
                                 for dx,dy in group) for group in GROUPS]])
            assert signature in lookup
            variant = ((x*73856093 ^ y*19349663 ^ 0x72bf) % 3) if vary else 0
            data = tile(signature,variant)
            line.append(dict(signature=signature,variant=variant))
            for yy in range(SIZE):
                offset = ((y*SIZE+yy)*width*SIZE+x*SIZE)*3
                result[offset:offset+SIZE*3] = data[yy*SIZE*3:(yy+1)*SIZE*3]
        cells.append(line)
    image = f'previews/{name}.png'
    save_png(image,width*SIZE,height*SIZE,result)
    preview_records.append(dict(name=name,image=image,layout=layout,invert=invert,vary=vary,cells=cells))


assemble('green_patch_baseline', PATCH,0,False)
assemble('green_patch_varied', PATCH,0,True)
assemble('earth_patch_varied', PATCH,1,True)
assemble('meandering_boundary_varied', COAST,0,True)

# Simple repeat tests: unmodified A compared with A/B/C, with the same texture
# scale and no props, tint, fog, grid or other means of hiding repetition.
for terrain in (0,1):
    for vary in (False,True):
        pixels = bytearray(768*256*3)
        for y in range(2):
            for x in range(6):
                variant = ((x*73856093 ^ y*19349663 ^ 0x72bf)%3) if vary else 0
                data = tile((terrain,)*9,variant)
                for yy in range(128):
                    offset = ((y*128+yy)*768+x*128)*3
                    pixels[offset:offset+384] = data[yy*384:(yy+1)*384]
        save_png(f'previews/{("earth","green")[terrain]}_repeat_{("a","abc")[vary]}.png',768,256,pixels)

# Exact shared-edge test for ALL compatible pairs in the generated subset and
# all nine A/B/C variant pairings. No engine and no timing/performance probe.
generated = sorted(mask_cache)
assert len(generated) == 37 and len(generated) < 94
edge_indices = {'top':(1,2,3),'bottom':(6,7,8),'left':(1,4,6),'right':(3,5,8)}
def edge_pixels(data,side):
    if side == 'top': return data[:384]
    if side == 'bottom': return data[-384:]
    x = 0 if side == 'left' else 127
    return bytes(value for y in range(128) for value in data[(y*128+x)*3:(y*128+x)*3+3])
comparisons = 0
for a in generated:
    for b in generated:
        for side,opposite in (('right','left'),('bottom','top')):
            if tuple(a[i] for i in edge_indices[side]) != tuple(b[i] for i in edge_indices[opposite]):
                continue
            for va in range(3):
                for vb in range(3):
                    assert edge_pixels(tile(a,va),side) == edge_pixels(tile(b,vb),opposite), (a,b,side,va,vb)
                    comparisons += 1

with zipfile.ZipFile(PACKAGE) as package:
    for name in ('assembled_12x10_preview.png','transition_contact_sheet.png'):
        raw = package.read(name)
        assert decode_png(raw)[:2] in ((1536,1280),(1040,660))
        with (OUT/'references'/name).open('xb') as stream:
            stream.write(raw)

snapshot = json.loads((OUT/'source_snapshot.json').read_text())
for path, expected in snapshot['files'].items():
    assert digest(ROOT/path) == expected, path
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT).decode().strip() == snapshot['head']
manifest = dict(stage='1 - offline proof only',head=snapshot['head'],generated_signatures=len(generated),
                inventory_sha256=digest(INVENTORY),package_sha256=digest(PACKAGE),
                source_sha256={name:digest(ASSET/'originals'/name)
                               for name in ('earth_solid.png','green_solid.png')},
                representative_png_count=len(representatives),representatives=representatives,
                subset=[dict(signature=s,original_atlas=[int(lookup[s]['atlas_x']),int(lookup[s]['atlas_y'])])
                        for s in generated],previews=preview_records,
                validation=dict(exact_compatible_edge_comparisons=comparisons,maximum_channel_difference=0,
                                protected_source_files_unchanged=len(snapshot['files']),godot='NOT RUN'),
                outputs={str(p.relative_to(OUT)).replace('\\','/'):digest(p) for p in OUT.rglob('*.png')})
with (OUT/'manifest.json').open('x',encoding='utf-8') as stream:
    json.dump(manifest,stream,indent=2)
    stream.write('\n')
print(json.dumps({'generated_signatures':len(generated),'representative_pngs':len(representatives),
                  'compatible_edge_checks':comparisons,'max_channel_difference':0,
                  'preserved_working_files':len(snapshot['files'])}))
