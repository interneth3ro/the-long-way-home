"""Bounded C1 fixture authoring/reference model. No Godot or historical inputs.

--write creates missing outputs only; --check regenerates fields in memory.
--previews creates CPU approximations, never shader-rendered evidence.
"""
import argparse
from functools import lru_cache
import hashlib
import importlib.util
import json
import math
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / 'assets/experiments/terrain_c1'
SEED = 26026
RULE = 'c1_fields_v1'
ART = 'c1_materials_v1'
CHUNK = 2048
STEP = 16
GUTTER = 4
WIDTH = 137
PHASE_WIDTH = 7
COORDS = ((-1,-1),(0,-1),(-1,0),(0,0))
GUARD = math.sqrt(2)*STEP + .001


def helper(name, path):
    spec=importlib.util.spec_from_file_location(name,ROOT/path)
    obj=importlib.util.module_from_spec(spec)
    spec.loader.exec_module(obj)
    return obj


png=helper('c1_png','tools/bake-illustrated-terrain.py')
labels=helper('c1_labels','tools/ground-art-refinement.py')
LINEAR = tuple(png.to_linear(i) for i in range(256))


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def fixture():
    scene_path=ROOT/'scenes/world/planet_exterior.tscn'
    scene=scene_path.read_text()
    blocks=re.findall(r'\[node ([^\n]+)\]\n(.*?)(?=\n\[node |\Z)',scene,re.S)
    overlays=[]; anchors=[]
    for header,body in blocks:
        if 'parent="AuthoredCrashSite"' in header:
            values=[float(v) for v in re.search(r'polygon = PackedVector2Array\((.*?)\)',body).group(1).split(',')]
            color=[float(v) for v in re.search(r'color = Color\((.*?)\)',body).group(1).split(',')]
            overlays.append({'polygon':list(zip(values[::2],values[1::2])),'color':color,'feather':256})
        if 'type="StaticBody2D" parent="GroundObjects"' in header:
            match=re.search(r'position = Vector2\((.*?),(.*?)\)',body)
            anchors.append([float(match[1]),float(match[2])] if match else [0.,0.])
    protection=(ROOT/'scenes/world/crash_site_protection.gd').read_text()
    gameplay=[[float(a),float(b)] for a,b in re.findall(r'Vector2\((.*?),(.*?)\)',protection)]
    assert len(overlays)==4 and len(anchors)==4 and len(gameplay)==6
    paths=['scenes/world/planet_exterior.tscn','scenes/world/crash_site_protection.gd',
           'scenes/world/world_coordinates.gd','scenes/world/planet_generator.gd',
           'scenes/world/terrain_chunk.gd','tools/terrain-c1-author.py']
    return {'seed':SEED,'rule':RULE,'art':ART,'chunk_size':CHUNK,'field_step':STEP,
        'field_width':WIDTH,'gutter':GUTTER,'supported_chunks':COORDS,
        'coordinate_bounds':[-2048,2048],'overlays':overlays,'anchors':anchors,
        'gameplay':gameplay,'source_sha256_lf':{p:sha((ROOT/p).read_bytes().replace(b'\r\n',b'\n')) for p in paths}}


@lru_cache(maxsize=1)
def geometry():
    return fixture()


def segment_distance(p,a,b):
    dx,dy=b[0]-a[0],b[1]-a[1]
    t=max(0.,min(1.,((p[0]-a[0])*dx+(p[1]-a[1])*dy)/(dx*dx+dy*dy)))
    return math.hypot(p[0]-a[0]-t*dx,p[1]-a[1]-t*dy)


def polygon_distance(p,polygon):
    inside=False; distance=float('inf')
    for a,b in zip(polygon,polygon[1:]+polygon[:1]):
        distance=min(distance,segment_distance(p,a,b))
        if (a[1]>p[1]) != (b[1]>p[1]):
            if p[0] < (b[0]-a[0])*(p[1]-a[1])/(b[1]-a[1])+a[0]:
                inside=not inside
    return -distance if inside else distance


def strict_distance(p):
    f=geometry()
    distances=[polygon_distance(p,f['gameplay'])-48]
    distances.extend(polygon_distance(p,o['polygon'])-o['feather'] for o in f['overlays'])
    distances.extend(math.hypot(p[0]-a[0],p[1]-a[1])-160 for a in f['anchors'])
    return min(distances)


def random_at(x,y,channel,seed=SEED):
    v=seed%2147483647
    for add in ((x%2147483647)*69621,(y%2147483647)*907,channel*104729):
        v=(v*48271+add)%2147483647
    return ((v^(v>>13))*48271%2147483647)/2147483647


def smooth(v):
    v=max(0.,min(1.,v)); return v*v*(3-2*v)


def noise(x,y,scale,channel):
    x,y=x/scale,y/scale
    ix,iy=math.floor(x),math.floor(y); u,v=smooth(x-ix),smooth(y-iy)
    a=random_at(ix,iy,channel)*(1-u)+random_at(ix+1,iy,channel)*u
    b=random_at(ix,iy+1,channel)*(1-u)+random_at(ix+1,iy+1,channel)*u
    return a*(1-v)+b*v


def field_node(x,y):
    distance=strict_distance((x,y))
    recovery=120+300*noise(x,y,540,101)
    cover=smooth((distance-GUARD)/recovery)
    # Smooth field scales are independent of the color atlas and construction grid.
    macro=noise(x,y,1270,102)
    density=noise(x,y,370,103)
    return bytes((int(255*cover),round(255*macro),round(255*density)))


@lru_cache(maxsize=512)
def phase_node(x,y,seed=SEED):
    key=f'{RULE}:{ART}:{seed}:{x}:{y}:material'
    return hashlib.sha256(key.encode()).digest()[:3]


def fields(coord):
    x,y=coord
    pixels=b''.join(field_node(x*CHUNK+(i-GUTTER)*STEP,y*CHUNK+(j-GUTTER)*STEP)
        for j in range(WIDTH) for i in range(WIDTH))
    phases=b''.join(phase_node(x*4+i-1,y*4+j-1) for j in range(7) for i in range(7))
    return (WIDTH,WIDTH,pixels),(7,7,phases)


def bilinear(image,x,y):
    w,h,p=image
    assert -.00001<=x<=w-1+.00001 and -.00001<=y<=h-1+.00001
    x=max(0.,min(w-1.,x)); y=max(0.,min(h-1.,y))
    ix,iy=math.floor(x),math.floor(y); jx,jy=min(ix+1,w-1),min(iy+1,h-1)
    u,v=x-ix,y-iy
    return tuple(sum(p[(yy*w+xx)*3+c]*weight for xx,yy,weight in
        ((ix,iy,(1-u)*(1-v)),(jx,iy,u*(1-v)),(ix,jy,(1-u)*v),(jx,jy,u*v)))/255 for c in range(3))


def reconstruct(image,coord,p):
    return bilinear(image,(p[0]-coord[0]*CHUNK)/STEP+GUTTER,(p[1]-coord[1]*CHUNK)/STEP+GUTTER)


def select_chunk(p):
    # Clamp only for the baseline's one-cell halo, inside the stored 64-unit gutter.
    return tuple(max(-1,min(0,math.floor(v/CHUNK))) for v in p)


def outputs():
    result={}; records=[]
    for coord in COORDS:
        field,phase=fields(coord); stem=f'{coord[0]}_{coord[1]}'
        for kind,image in (('field',field),('phase',phase)):
            path=f'fields/{stem}_{kind}.png'; raw=png.encode_png(*image)
            result[path]=raw
        records.append({'coord':coord,'field':f'fields/{stem}_field.png','phase':f'fields/{stem}_phase.png',
            'field_sha256':sha(result[f'fields/{stem}_field.png']),'phase_sha256':sha(result[f'fields/{stem}_phase.png']),
            'identity':f'{RULE}:{ART}:{SEED}:{coord[0]}:{coord[1]}'})
    data=fixture(); data['regions']=records
    data['materials']={name:{'path':f'sources/{name}.png','sha256':sha((ASSETS/f'sources/{name}.png').read_bytes())} for name in ('earth','green')}
    result['fixture.json']=(json.dumps(data,indent=2)+'\n').encode()
    return result


def nearest(image,u,v):
    w,h,p=image; x=round(u*(w-1)); y=round(v*(h-1))
    assert 0<=x<w and 0<=y<h
    return p[(y*w+x)*3:(y*w+x)*3+3]


def material_pixel(sources,p):
    ix,iy=math.floor(p[0]/512),math.floor(p[1]/512)
    u,v=p[0]/512-ix,p[1]/512-iy
    u,v=smooth(u),smooth(v)
    out=[[0.,0.,0.],[0.,0.,0.]]
    for x,y,weight in ((ix,iy,(1-u)*(1-v)),(ix+1,iy,u*(1-v)),(ix,iy+1,(1-u)*v),(ix+1,iy+1,u*v)):
        phase=phase_node(x,y); scale=.8+.2*phase[2]/255
        su=.35+.3*phase[0]/255+(p[0]-x*512)/2048*scale
        sv=.35+.3*phase[1]/255+(p[1]-y*512)/2048*scale
        for k,source in enumerate(sources):
            sample=nearest(source,su,sv)
            for c in range(3): out[k][c]+=LINEAR[sample[c]]*weight
    return out


def previews():
    # Explicit CPU illustration: nearest material samples, no shader, mipmaps or runtime tint.
    sources=[png.decode_png((ASSETS/f'sources/{n}.png').read_bytes()) for n in ('earth','green')]
    cached={coord:png.decode_png((ASSETS/f'fields/{coord[0]}_{coord[1]}_field.png').read_bytes()) for coord in COORDS}
    mapping=json.loads((ROOT/'assets/experiments/native_terrain_47_96/baked_v2/mapping.json').read_text())
    atlas=png.decode_png((ROOT/'assets/environment/exterior/ground_refined_v1/baseline_94.png').read_bytes())
    interiors=png.decode_png((ROOT/'assets/environment/exterior/ground_refined_v1/interiors_bc.png').read_bytes())
    old={(tuple(e['signature']),0):labels.crop(atlas[2],atlas[0],*e['atlas']) for e in mapping['baseline']}
    old.update({(tuple(e['signature']),'ABC'.index(e['variant'])):labels.crop(interiors[2],interiors[0],*e['atlas']) for e in mapping['interiors']})
    def sample(p): return reconstruct(cached[select_chunk(p)],select_chunk(p),p)
    @lru_cache(maxsize=8192)
    def baseline_tile(tx,ty):
        g=[int(sample(((tx+dx+.5)*64,(ty+dy+.5)*64))[0]>=.5) for dx,dy in
            ((0,0),(-1,-1),(0,-1),(1,-1),(-1,0),(1,0),(-1,1),(0,1),(1,1))]
        c,nw,n,ne,w,e,sw,s,se=g
        sig=(c,c*nw*n*w,c*n,c*n*ne*e,c*w,c*e,c*w*sw*s,c*s,c*e*s*se)
        bucket=int(random_at(tx,ty,193)*2147483647)%100
        variant=(0 if bucket<60 else 1 if bucket<85 else 2) if len(set(sig))==1 else 0
        return old[sig,variant]
    result={}
    def view(name,origin,world_size,zoom):
        w,h=round(world_size[0]*zoom),round(world_size[1]*zoom)
        assert w*h<=400000
        candidate=bytearray(); baseline=bytearray()
        for yy in range(h):
            for xx in range(w):
                p=(origin[0]+(xx+.5)/zoom,origin[1]+(yy+.5)/zoom)
                coverage,macro,density=sample(p)
                earth,green=material_pixel(sources,p)
                green=[a*(1-(.45+.55*density))+b*(.45+.55*density) for a,b in zip((.10,.18,.025),green)]
                rgb=[(earth[c]*(1-coverage)+green[c]*coverage) for c in range(3)]
                brightness=.91+.18*macro
                green_hue=(.96+.08*density,1.,1.025-.05*density)
                candidate.extend(png.to_srgb(rgb[c]*brightness*(1-coverage+coverage*green_hue[c])) for c in range(3))
                tx,ty=math.floor(p[0]/64),math.floor(p[1]/64)
                tile=baseline_tile(tx,ty); sx=int((p[0]-tx*64)*2); sy=int((p[1]-ty*64)*2)
                baseline.extend(tile[(sy*128+sx)*3:(sy*128+sx)*3+3])
        board=labels.board(2*w+48,h+74)
        labels.text(board,'C1 CPU APPROXIMATION / '+name.replace('_',' '),16,10,1)
        labels.text(board,'BASELINE / NEUTRAL',16,32,1)
        labels.text(board,'CONTINUOUS / NEUTRAL',w+32,32,1)
        labels.paste(board,(w,h,baseline),16,54); labels.paste(board,(w,h,candidate),w+32,54)
        result[f'previews/{name}.png']=png.encode_png(*board)
    view('recovery_1x',(-1600,500),(768,512),1.)
    view('recovery_05x',(-1600,500),(768,512),.5)
    view('long_green_05x',(-2000,-1950),(4000,240),.5)
    view('junction_05x',(-256,-256),(512,512),.5)
    diagnostic=labels.board(528,566)
    labels.text(diagnostic,'C1 COVERAGE / MACRO / DENSITY',8,8,1)
    for y in range(512):
        for x in range(512):
            p=(-2048+(x+.5)*8,-2048+(y+.5)*8)
            value=sample(p); i=((y+32)*528+x+8)*3
            diagnostic[2][i:i+3]=bytes(round(v*255) for v in value)
    result['previews/fields_overview.png']=png.encode_png(*diagnostic)
    return result


def main():
    parser=argparse.ArgumentParser()
    group=parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--write',action='store_true'); group.add_argument('--check',action='store_true')
    group.add_argument('--previews',action='store_true')
    group.add_argument('--check-previews',action='store_true')
    args=parser.parse_args()
    data=previews() if args.previews or args.check_previews else outputs()
    for name,raw in data.items():
        path=ASSETS/name
        if args.check or args.check_previews:
            actual=path.read_bytes()
            if name.endswith('.json'): actual=actual.replace(b'\r\n',b'\n')
            assert actual==raw, 'Changed C1 output: '+name
        else:
            with path.open('xb') as stream: stream.write(raw)
    print(f'C1 offline PASS: {len(data)} '+('preview illustrations' if args.previews or args.check_previews else 'field/fixture outputs')+'; no Godot')


if __name__=='__main__': main()
