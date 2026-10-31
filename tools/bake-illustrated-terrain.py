"""Offline authoring recipe for the owner-approved Stage 1 terrain treatment.

No Godot, runtime shader, procedural world integration or external dependencies.
Importing reads only the fixed inventory/source PNGs. Running as a script writes
new files exclusively to a NEW output directory; existing art is never replaced.
"""
import csv
import hashlib
import json
import math
from pathlib import Path
import struct
import zlib

ROOT = Path(__file__).resolve().parents[1]
ASSET = ROOT / 'assets/experiments/native_terrain_47_96/illustrated_v1'
INVENTORY = ROOT / 'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv'
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


def smooth(t):
    t = min(1.0, max(0.0, t))
    return t*t*(3-2*t)


def lerp(a, b, t):
    return a+(b-a)*t


def to_linear(value):
    value /= 255
    return value/12.92 if value <= .04045 else ((value+.055)/1.055)**2.4


def to_srgb(value):
    value = max(0.0, min(1.0, value))
    value = value*12.92 if value <= .0031308 else 1.055*value**(1/2.4)-.055
    return round(value*255)


with INVENTORY.open(newline='') as stream:
    rows = list(csv.DictReader(stream))
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
        nu, nv = (0 if x == 127 else u), (0 if y == 127 else v)
        noise = (.60*math.sin(2*math.pi*nu+.45)*math.sin(2*math.pi*nv+1.2)
                 + .25*math.sin(2*math.pi*(3*nu+2*nv)+1.1)
                 + .15*math.sin(2*math.pi*(7*nu-5*nv)+.3))
        geometry.append((u, v, noise))

mask_cache, tile_cache = {}, {}


def mask(signature):
    if signature in mask_cache:
        return mask_cache[signature]
    c,nw,n,ne,w,e,sw,s,se = signature
    result = []
    def edge(t, values):
        # Linear interpolation through three actual peers. Shared edges use
        # exactly the same one-dimensional boundary function on either tile.
        if t <= .5:
            return lerp(values[0], values[1], 2*t)
        return lerp(values[1], values[2], 2*t-1)
    # Coons transfinite surface interpolates four complete boundary curves.
    # A smooth interior bubble enforces the actual center without editing edges.
    middle = .5*(n+s+w+e) - .25*(nw+ne+sw+se)
    for u,v,noise in geometry:
        top, bottom = edge(u,(nw,n,ne)), edge(u,(sw,s,se))
        left, right = edge(v,(nw,w,sw)), edge(v,(ne,e,se))
        corners = lerp(lerp(nw,ne,u),lerp(sw,se,u),v)
        field = lerp(top,bottom,v)+lerp(left,right,u)-corners
        bubble = 16*u*(1-u)*v*(1-v)
        field += bubble*(c-middle)
        field = max(0.0,min(1.0,field))
        field += .16 * 4*field*(1-field) * noise
        result.append(smooth((field-.30)/.40))
    for px,py,index in ((64,64,0),(0,0,1),(64,0,2),(127,0,3),
                        (0,64,4),(127,64,5),(0,127,6),(64,127,7),(127,127,8)):
        assert round(result[py*128+px]*255) == signature[index]*255
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


def signature(row):
    return (int(row['tlwh_center']), *(int(row['tlwh_'+bit]) for bit in BITS))


def copy_cell(atlas, width, x, y, pixels):
    for yy in range(128):
        offset = ((y*128+yy)*width+x*128)*3
        atlas[offset:offset+384] = pixels[yy*384:(yy+1)*384]


def tile_properties(x, y, sig):
    prefix = f'{x}:{y}/0'
    return [prefix+' = 0', prefix+'/terrain_set = 0', prefix+'/terrain = '+str(sig[0]),
            *(prefix+'/terrains_peering_bit/'+bit+' = '+str(value) for bit,value in zip(BITS,sig[1:]))]


def build(destination):
    """Write 94 baseline tiles and exactly four approved solid alternatives."""
    destination = Path(destination)
    destination.mkdir(parents=False, exist_ok=False)
    baseline = bytearray(1536*1024*3)
    records = []
    for row in rows:
        sig = signature(row)
        x,y = int(row['atlas_x']),int(row['atlas_y'])
        pixels = tile(sig,0)
        copy_cell(baseline,1536,x,y,pixels)
        records.append(dict(family=row['family'],pattern=int(row['pattern']),atlas=[x,y],
                            signature=sig,pixel_sha256=hashlib.sha256(pixels).hexdigest()))
    interiors = bytearray(256*256*3)
    variants = []
    for center in (0,1):
        for variant in (1,2):
            sig = (center,)*9
            pixels = tile(sig,variant)
            x,y = variant-1,center
            copy_cell(interiors,256,x,y,pixels)
            variants.append(dict(atlas=[x,y],signature=sig,variant=('A','B','C')[variant],
                                 pixel_sha256=hashlib.sha256(pixels).hexdigest()))
    files = {'baseline_94.png':encode_png(1536,1024,baseline),
             'interiors_bc.png':encode_png(256,256,interiors)}
    path = 'res://assets/experiments/native_terrain_47_96/baked_v2/'
    resource = ['[gd_resource type="TileSet" format=3]','',
                f'[ext_resource type="Texture2D" path="{path}baseline_94.png" id="1_baseline"]',
                f'[ext_resource type="Texture2D" path="{path}interiors_bc.png" id="2_interiors"]','',
                '[sub_resource type="TileSetAtlasSource" id="Baseline"]',
                'resource_name = "BAKED - 94 original signatures / variant A"',
                'texture = ExtResource("1_baseline")','texture_region_size = Vector2i(128, 128)']
    for entry in records:
        resource.extend(tile_properties(*entry['atlas'],entry['signature']))
    resource.extend(['','[sub_resource type="TileSetAtlasSource" id="Interiors"]',
                     'resource_name = "BAKED - approved B/C solid interiors only"',
                     'texture = ExtResource("2_interiors")','texture_region_size = Vector2i(128, 128)'])
    for entry in variants:
        resource.extend(tile_properties(*entry['atlas'],entry['signature']))
    resource.extend(['','[resource]','resource_name = "EXPERIMENTAL baked Earth/Green - full 94 baseline"',
                     'tile_size = Vector2i(128, 128)','terrain_set_0/mode = 0',
                     'terrain_set_0/terrain_0/name = "Weathered Earth"',
                     'terrain_set_0/terrain_0/color = Color(0.61, 0.39, 0.24, 1)',
                     'terrain_set_0/terrain_1/name = "Low Green Cover"',
                     'terrain_set_0/terrain_1/color = Color(0.29, 0.67, 0.32, 1)',
                     'sources/0 = SubResource("Baseline")','sources/1 = SubResource("Interiors")',''])
    files['baked_terrain.tres'] = '\n'.join(resource).encode('utf-8')
    mapping = dict(method='Approved Stage 1 v3 Coons / center bubble / periodic perturbation / linear-light blend',
                   stage=2,baseline_count=94,baseline_peers=752,interior_alternatives=4,
                   source_sha256={name:hashlib.sha256((ASSET/'originals'/name).read_bytes()).hexdigest()
                                  for name in ('earth_solid.png','green_solid.png')},
                   inventory_sha256=hashlib.sha256(INVENTORY.read_bytes()).hexdigest(),
                   approved_proof=APPROVED_PROOF,baseline=records,interiors=variants,
                   output_sha256={name:hashlib.sha256(raw).hexdigest() for name,raw in files.items()})
    files['mapping.json'] = (json.dumps(mapping,indent=2)+'\n').encode('utf-8')
    for name,raw in files.items():
        with (destination/name).open('xb') as stream:
            stream.write(raw)
    print('Baked 94 baseline configurations (752 peers) and four B/C solid alternatives. No engine run.')



APPROVED_PROOF = {'approved_date': '2026-10-31',
 'proof_recipe_sha256': 'd4c1ba5baa436dca7b96abd3920c06832f06d7df6385114b7108166fead10cd7',
 'approved_image_sha256': {'previews/meandering_boundary_varied.png': '1ca4eec259de89e40e8276920e03f5f7602f986ad26c255c0f4ed6a6761ae67c',
                           'previews/green_patch_varied.png': '006843cbc82aed0a982f3f49afe4ba539545d78704c7facaa9355823feb8156e',
                           'previews/earth_patch_varied.png': '812b05969d4b20ca02942f12e6da1efa93f89b7230b896ba92be369ce440849c',
                           'variations.png': 'd4875b71660b8480e4c2ade8ee5a14e511e04df60d21494073e307767e543bbb',
                           'representatives.png': '656f3301712add48877ef13e22422c9cc4fd4f39f78641ee7edba86de5293f7d'},
 'representative_png_sha256': {'earth_solid_9_2.png': '7ce29cc5a6c0753da600799fc88056c9875bcd465e356f956d328e357f5c1460',
                               'earth_convex_nw_8_0.png': 'ac962ee22e5d41ce3c7b1b0f6efeb4a94ce22c306383b3c01b42c63d97988020',
                               'earth_concave_nw_5_1.png': 'e87e4e5d3356d0ec2dfb9010f8322802bbeab07ed6249899b0a74066f0f75848',
                               'earth_endpoint_south_0_0.png': 'df539662801112ed963538af78830503a00f19d60c99c0c9477d486af1c02d10',
                               'earth_narrow_ns_0_1.png': '7a0fc720e86396dee3d62590ddf9da0e48514f2aafc53a23814b757aaba53620',
                               'earth_isolated_0_3.png': '8e2485714688e3bd74eb670b934f3c750f6d0c8261cb08a6fe060f8b536aaad6',
                               'earth_north_10_0.png': '07ecf9acd5388f4172758edf29f93df430632772c8381a17fd67d76badf38fb0',
                               'earth_south_9_3.png': '3b6553124c60f25950ecfcd4aabe56fcb39d04efb4daec4eefc4e0e6283c043b',
                               'earth_west_8_1.png': 'f3b45f7d3429482130748d06d8526758a340096337ffe0cb78f1ceb9513bb259',
                               'earth_east_11_2.png': 'dc13b8ab4b1713faa570c0e9e0fef4e021317f1604e72de9ada4a54f6a0aaf15',
                               'green_solid_9_6.png': '8b0036d4ff7e90a2658667cf416daf2a1e7cd6e46e29ba2b67049ecf7a575158',
                               'green_convex_nw_8_4.png': '0b062cbbb3b801cea94cc95520b351474beaab253107bcb9d8b5292124b91888',
                               'green_concave_nw_5_5.png': '4efb1537e29df2269d148777603a1cf6705894f6ae3cce16669749cfe0576a21',
                               'green_endpoint_south_0_4.png': 'ef0b7d889cb4f618bec5b0f6db9be2bd5edb6bdc595305e32b50357d0ba27823',
                               'green_narrow_ns_0_5.png': '835f9a1fdf1eef1705c9643b88a345520e4a6965ad8239171f08eea83aa6a632',
                               'green_isolated_0_7.png': 'db6b7324c51256c24ca8e67ebd372cf581760b5682f8291a8e25ab50b1672693',
                               'green_north_10_4.png': 'd1074892232f7dd332279fe202b8cab9ee6eabb0330b1c3295535ddcff03e00b',
                               'green_south_9_7.png': '47bd8181c5db95f1afe0690af06ff8feca50509b7d8da4b3dc73c8dcabbf3fdd',
                               'green_west_8_5.png': '52a1d6069ae1272acba8c597218bd8086f9e1261388e7622ddfda4223d3bf21b',
                               'green_east_11_6.png': 'e779358dd65857a568de90f631d563c23cc5ec402852e3d807d396bbd1f5895b'}}

APPROVED_PROOF["variant_png_sha256"] = {'earth_1.png': 'e1951b82e85cb12b3b588b34573dc0814ce82ca3624b0db1ce2547f3a0eb6144', 'earth_2.png': 'f9f48001f8fe0cda14516782feafba5f3b7fcadc7e59943fed257d5b70520c50', 'green_1.png': 'e010ef9c4ce81bbbc053eb2aaf6bef65b7239f8539af0ef52ec5d2d6c7faa3a0', 'green_2.png': '36342ca6910ae89d85e5c50cf242dcadd3ba4b505508f391ce5159b5f8eb769b'}


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('destination', help='New output directory; existing directories are rejected.')
    build(parser.parse_args().destination)
