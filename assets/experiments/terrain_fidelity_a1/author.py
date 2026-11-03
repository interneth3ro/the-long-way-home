"""Bounded A1 offline authoring. No Godot, scene changes, or full atlas build.

python -B assets/experiments/terrain_fidelity_a1/author.py --write
python -B assets/experiments/terrain_fidelity_a1/author.py --check
Frozen imagegen sources are inputs; model generation is not reproducible.
"""
import argparse
import hashlib
import importlib.util
import json
import math
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]


def module(name, relative):
    spec = importlib.util.spec_from_file_location(name, ROOT / relative)
    obj = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


bake = module('a1_baker', 'tools/bake-illustrated-terrain.py')
study = module('a1_labels', 'tools/ground-art-refinement.py')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def box(image, size):
    """Integer box bins; deterministic offline preview filtering, not Godot."""
    w, h, p = image
    assert w == h and size <= w <= 2048
    out = bytearray()
    for y in range(size):
        y0, y1 = y*h//size, (y+1)*h//size
        for x in range(size):
            x0, x1 = x*w//size, (x+1)*w//size
            total = [0, 0, 0]
            for yy in range(y0, y1):
                for xx in range(x0, x1):
                    i = (yy*w+xx)*3
                    for c in range(3):
                        total[c] += p[i+c]
            count = (x1-x0)*(y1-y0)
            out.extend(round(v/count) for v in total)
    return bytes(out)


def periodic(p):
    """Eight-texel opposite-edge crossfade; disclose possible border softening."""
    out = bytearray(p)
    for axis in (0, 1):
        src = bytes(out)
        for d in range(8):
            t = .5 * (1 - d/8)**2
            for k in range(128):
                a, b = ((k*128+d)*3, (k*128+127-d)*3) if axis == 0 else ((d*128+k)*3, ((127-d)*128+k)*3)
                for c in range(3):
                    out[a+c] = round(src[a+c]*(1-t)+src[b+c]*t)
                    out[b+c] = round(src[b+c]*(1-t)+src[a+c]*t)
    return bytes(out)


def variants(p):
    result = [p]
    for dx, dy in ((37, 59), (79, 23)):
        out = bytearray()
        for y in range(128):
            for x in range(128):
                weight = .8 * math.sin(math.pi*x/127)**2 * math.sin(math.pi*y/127)**2
                if x in (0, 127) or y in (0, 127):
                    weight = 0
                i, j = (y*128+x)*3, (((y+dy)%127)*128+(x+dx)%127)*3
                out.extend(round(p[i+c]*(1-weight)+p[j+c]*weight) for c in range(3))
        result.append(bytes(out))
    return result


def material(x, y):
    # Fixed stress fixture, deliberately greener than current production. No generator edit.
    green = x > 5 + 2*math.sin(y*.48)
    if 8 <= y <= 10 and 1 <= x <= 3:
        green = True  # isolated cover
    if y == 5 and 1 <= x <= 6:
        green = True  # narrow connection
    if x == 12 and 2 <= y <= 4:
        green = False  # earth incision
    return int(green)


def signature(x, y):
    g = [material(x+dx, y+dy) for dx, dy in ((0,0),(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1))]
    c, nw, n, ne, w, e, sw, s, se = g
    return (c,c*nw*n*w,c*n,c*n*ne*e,c*w,c*e,c*w*sw*s,c*s,c*e*s*se)


def bucket(x, y):
    # Same independent presentation arithmetic, evaluated offline with fixed seed 26026.
    v = 26026
    for add in (x%2147483647*69621, y%2147483647*907, 193*104729):
        v = (v*48271+add)%2147483647
    v = ((v^(v>>13))*48271)%2147483647
    return 0 if v%100 < 60 else 1 if v%100 < 85 else 2


def build():
    files, inputs = {}, {}
    def read(path):
        raw = path.read_bytes()
        inputs[path.relative_to(ROOT).as_posix()] = digest(raw)
        return raw
    candidate = {}
    raw_edges = {}
    for family in ('earth', 'green'):
        image = bake.decode_png(read(HERE/'sources'/f'{family}_generated.png'))
        raw = box(image, 128)
        raw_edges[family] = max(abs(a-b) for side, other in (('left','right'),('top','bottom')) for a,b in zip(study.edge(raw,side),study.edge(raw,other)))
        p = periodic(raw)
        candidate[family] = variants(p)
        for index, tile in enumerate(candidate[family]):
            files[f'tiles/{family}_{"ABC"[index]}.png'] = bake.encode_png(128,128,tile)
    source_base = ROOT/'assets/environment/exterior/ground_refined_v1'
    baseline = bake.decode_png(read(source_base/'baseline_94.png'))
    interiors = bake.decode_png(read(source_base/'interiors_bc.png'))
    mapping = json.loads(read(ROOT/'assets/experiments/native_terrain_47_96/baked_v2/mapping.json'))
    old = {(tuple(e['signature']),0): study.crop(baseline[2],baseline[0],*e['atlas']) for e in mapping['baseline']}
    old.update({(tuple(e['signature']),'ABC'.index(e['variant'])):study.crop(interiors[2],interiors[0],*e['atlas']) for e in mapping['interiors']})
    cache = {}
    def tile(sig, variant):
        key = sig, variant
        if key not in cache:
            if len(set(sig)) == 1:
                p = candidate['green' if sig[0] else 'earth'][variant]
            else:
                mask = [bake.smooth((v-.15)/.70) for v in bake.mask(sig)]
                p = bytes(bake.to_srgb(bake.lerp(bake.to_linear(a),bake.to_linear(b),mask[i//3])) for i,(a,b) in enumerate(zip(candidate['earth'][0],candidate['green'][0])))
            cache[key] = p
        return cache[key]
    layouts = {
        'repeat': [[((1,)*9,0 if y < 3 else bucket(x,y)) for x in range(12)] for y in range(8)],
        'boundary': [[(signature(x,y),bucket(x,y) if len(set(signature(x,y))) == 1 else 0) for x in range(16)] for y in range(12)],
    }
    checks = {'self_and_variant_edges': 0, 'layout_adjacencies': 0}
    for family in candidate.values():
        for a in family:
            for b in family:
                for side, other in (('right','left'),('bottom','top')):
                    assert study.edge(a,side) == study.edge(b,other)
                    checks['self_and_variant_edges'] += 1
    for name, layout in layouts.items():
        for cell_size, scale_name in ((64,'1x'),(32,'05x')):
            cols, rows = len(layout[0]), len(layout)
            w, h = cols*cell_size, rows*cell_size
            panels = []
            for model in (old, None):
                panel = study.board(w,h)
                for y,row in enumerate(layout):
                    for x,(sig,variant) in enumerate(row):
                        p = model[sig,variant] if model is not None else tile(sig,variant)
                        small = box((128,128,p),cell_size)
                        study.paste(panel,(cell_size,cell_size,small),x*cell_size,y*cell_size)
                panels.append(panel)
            def sheet(grid=False):
                out = study.board(w*2+48,h+86)
                study.text(out,'A1 OFFLINE / '+name+' / '+str(cell_size)+' PX PER CELL',16,10,1)
                study.text(out,'BASELINE / NEUTRAL TINT',16,32,1)
                study.text(out,'CANDIDATE / SAME LAYOUT',w+32,32,1)
                for index,panel in enumerate(panels):
                    study.paste(out,panel,16+index*(w+16),56)
                    if grid:
                        for yy in range(h):
                            for xx in range(w):
                                if xx%cell_size == 0 or yy%cell_size == 0:
                                    i=((56+yy)*out[0]+16+index*(w+16)+xx)*3
                                    out[2][i:i+3]=bytes((190,220,225))
                return bake.encode_png(*out)
            files[f'previews/{name}_{scale_name}.png']=sheet()
            if cell_size == 64:
                files[f'previews/{name}_{scale_name}_grid.png']=sheet(True)
        for y,row in enumerate(layout):
            for x,(sig,v) in enumerate(row):
                for dx,dy,side,other in ((1,0,'right','left'),(0,1,'bottom','top')):
                    if y+dy < len(layout) and x+dx < len(row):
                        b,bv=layout[y+dy][x+dx]
                        assert study.edge(tile(sig,v),side)==study.edge(tile(b,bv),other)
                        checks['layout_adjacencies']+=1
    # One labeled native-size sample contact sheet; no additional full atlas.
    contact=study.board(6*144+16,190)
    for i,(family,v) in enumerate((f,v) for f in ('earth','green') for v in range(3)):
        study.text(contact,family+' '+'ABC'[v],16+i*144,10,1)
        study.paste(contact,(128,128,candidate[family][v]),16+i*144,32)
    files['previews/samples_128.png']=bake.encode_png(*contact)
    # Context grounds stay temporary; the composition script reads these after --write.
    context={}
    for name, model in (('baseline',old),('candidate',None)):
        panel=study.board(1408,1024)
        for y in range(16):
            for x in range(22):
                # Bare ship zone above, greener recovery below; fixture only.
                sig=(0,)*9 if y<8 else (1,)*9
                v=bucket(x,y)
                p=model[sig,v] if model is not None else tile(sig,v)
                study.paste(panel,(64,64,box((128,128,p),64)),x*64,y*64)
        context[name]=bake.encode_png(*panel)
    assert len({sig for sig,v in cache}) < 40, 'A1 must not build full transition inventory'
    manifest={'base_commit':'fa410ed9b329ffd28a927e142d2362971d54584a','seed':26026,
        'method':'Integer-bin box downsample; 8px opposite-edge crossfade; fixed-phase interior variants with .8 sine-squared envelope; current TLWH mask math for fixture concepts only',
        'native_sources':{f:bake.decode_png((HERE/'sources'/f'{f}_generated.png').read_bytes())[:2] for f in ('earth','green')},
        'input_sha256':inputs,'raw_128_opposite_edge_max_channel_difference':raw_edges,
        'candidate_edge_max_channel_difference':0,'checks':checks,
        'unique_fixture_signatures':len({sig for sig,v in cache}),
        'outputs':{name:{'sha256':digest(raw),'dimensions':bake.decode_png(raw)[:2]} for name,raw in files.items()},
        'limits':'Offline pixels only; exact edge equality is not perceptual seamlessness. No runtime tint, Godot filtering, motion, determinism or performance verification.'}
    files['manifest.json']=(json.dumps(manifest,indent=2)+'\n').encode()
    return files,context


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',action='store_true')
    group.add_argument('--check',action='store_true')
    args=parser.parse_args()
    files,context=build()
    for name,raw in files.items():
        path=HERE/name
        if args.check:
            assert path.read_bytes()==raw, 'Different output: '+name
        else:
            with path.open('xb') as stream:
                stream.write(raw)
    if args.write:
        tmp=ROOT/'artifacts/tmp/terrain_fidelity_a1'
        tmp.mkdir(parents=True,exist_ok=False)
        for name,raw in context.items():
            (tmp/(name+'.png')).write_bytes(raw)
    print('A1 PASS: '+str(len(files))+' deterministic outputs; edge and fixture checks passed. No Godot.')


if __name__=='__main__':
    main()
