"""Offline previews from saved Stage 2 atlas pixels, not runtime rendering."""
import csv,hashlib,importlib.util,json,math
from pathlib import Path
OUT=Path(__file__).resolve().parent
ROOT=OUT.parents[2]
spec=importlib.util.spec_from_file_location('bake',ROOT/'tools/bake-illustrated-terrain.py')
bake=importlib.util.module_from_spec(spec);spec.loader.exec_module(bake)
asset=ROOT/'assets/experiments/native_terrain_47_96/baked_v2'
mapping=json.loads((asset/'mapping.json').read_text())
lookup={tuple(e['signature']):e for e in mapping['baseline']}
width,height,baseline=bake.decode_png((asset/'baseline_94.png').read_bytes())
_,_,interiors=bake.decode_png((asset/'interiors_bc.png').read_bytes())
def cell(pixels,width,x,y):
    return b''.join(pixels[((y*128+dy)*width+x*128)*3:((y*128+dy)*width+(x+1)*128)*3] for dy in range(128))
base_cells={s:cell(baseline,width,*e['atlas']) for s,e in lookup.items()}
variant_cells={(e['signature'][0],'ABC'.index(e['variant'])):cell(interiors,256,*e['atlas']) for e in mapping['interiors']}

def solve_layout(layout, invert):
    # Offline shared-edge constraint assignment, NOT a Godot Connect replica.
    # Pick actual inventory signatures with fixed authored centers, preferring
    # shared anchors close to a soft, continuous field of those center labels.
    width, height = len(layout[0]), len(layout)
    signatures = list(lookup)
    edge = ((1,2,3),(3,5,8),(6,7,8),(1,4,6))
    opposite = (2,3,0,1)
    compatible = [[set() for _ in range(4)] for _ in signatures]
    for i,a in enumerate(signatures):
        for j,b in enumerate(signatures):
            for direction in range(4):
                if tuple(a[k] for k in edge[direction]) == tuple(b[k] for k in edge[opposite[direction]]):
                    compatible[i][direction].add(j)
    at = lambda x,y: int(layout[min(height-1,max(0,y))][min(width-1,max(0,x))]) ^ invert
    anchors = ((.5,.5),(0,0),(.5,0),(1,0),(0,.5),(1,.5),(0,1),(.5,1),(1,1))
    domains, costs, neighbors = [], [], []
    for y in range(height):
        for x in range(width):
            center = at(x,y)
            uniform = all(at(x+dx,y+dy)==center for dx in (-1,0,1) for dy in (-1,0,1))
            domain = {i for i,sig in enumerate(signatures) if sig[0]==center and (not uniform or sig==(center,)*9)}
            domains.append(domain)
            targets=[]
            for ax,ay in anchors:
                total,weight=0.0,0.0
                for yy in range(y-2,y+3):
                    for xx in range(x-2,x+3):
                        d2=(xx+.5-x-ax)**2+(yy+.5-y-ay)**2
                        w=math.exp(-d2/(2*.57**2))
                        total+=w*at(xx,yy);weight+=w
                targets.append(total/weight)
            costs.append({i:sum((signatures[i][k]-targets[k])**2 for k in range(1,9)) for i in domain})
            links=[]
            for direction,(dx,dy) in enumerate(((0,-1),(1,0),(0,1),(-1,0))):
                if 0<=x+dx<width and 0<=y+dy<height:
                    links.append((direction,(y+dy)*width+x+dx))
            neighbors.append(links)
    def propagate(state,queue):
        while queue:
            cell=queue.pop()
            for direction,neighbor in neighbors[cell]:
                allowed=set()
                for i in state[cell]:allowed.update(compatible[i][direction])
                narrowed=state[neighbor] & allowed
                if not narrowed:return False
                if narrowed!=state[neighbor]:
                    state[neighbor]=narrowed;queue.append(neighbor)
        return True
    visited=0
    def search(state):
        nonlocal visited
        visited+=1
        assert visited<20000, 'Offline layout search bound reached.'
        unresolved=[i for i,d in enumerate(state) if len(d)>1]
        if not unresolved:return state
        cell=min(unresolved,key=lambda i:(len(state[i]),min(costs[i][v] for v in state[i])))
        for choice in sorted(state[cell],key=lambda v:(costs[cell][v],v)):
            trial=state.copy();trial[cell]={choice}
            if propagate(trial,[cell]):
                result=search(trial)
                if result is not None:return result
        return None
    assert propagate(domains,list(range(len(domains))))
    result=search(domains)
    assert result is not None
    return [[signatures[next(iter(result[y*width+x]))] for x in range(width)] for y in range(height)]


def assemble(name,cells):
    height,width=len(cells),len(cells[0])
    pixels=bytearray(width*height*128*128*3)
    records=[]
    seams=0
    for y,row in enumerate(cells):
        record=[]
        for x,signature in enumerate(row):
            assert signature in lookup
            variant=((x*73856093 ^ y*19349663 ^ 0x72bf)%3) if signature==(signature[0],)*9 else 0
            data=base_cells[signature] if variant==0 else variant_cells[signature[0],variant]
            for yy in range(128):
                offset=((y*128+yy)*width*128+x*128)*3
                pixels[offset:offset+384]=data[yy*384:(yy+1)*384]
            record.append(dict(signature=signature,variant='ABC'[variant],
                               baseline_atlas=lookup[signature]['atlas']))
        records.append(record)
    def pixel(x,y):
        offset=(y*width*128+x)*3
        return pixels[offset:offset+3]
    for y,row in enumerate(cells):
        for x,sig in enumerate(row):
            if x+1<width:
                assert tuple(sig[i] for i in (3,5,8))==tuple(row[x+1][i] for i in (1,4,6))
                for yy in range(y*128,(y+1)*128):assert pixel(x*128+127,yy)==pixel(x*128+128,yy)
                seams+=1
            if y+1<height:
                assert tuple(sig[i] for i in (6,7,8))==tuple(cells[y+1][x][i] for i in (1,2,3))
                for xx in range(x*128,(x+1)*128):assert pixel(xx,y*128+127)==pixel(xx,y*128+128)
                seams+=1
    raw=bake.encode_png(width*128,height*128,pixels)
    with (OUT/(name+'.png')).open('xb') as stream:stream.write(raw)
    return dict(name=name,width=width*128,height=height*128,cells=records,
                matched_boundaries=seams,maximum_channel_difference=0,sha256=hashlib.sha256(raw).hexdigest())


records=[]
proof=json.loads((ROOT/'artifacts/evidence/pr100-terrain-proof-stage1-v3/manifest.json').read_text())
for name in ('green_patch_varied','earth_patch_varied','meandering_boundary_varied'):
    layout=next(p['cells'] for p in proof['previews'] if p['name']==name)
    records.append(assemble(name,[[tuple(c['signature']) for c in row] for row in layout]))
vertical=['0000000000','0000011110','0000011110','0000011110',
          '0000011110','0000011110','0000011110','0000000000']
narrow=['0000000000','0000010000','0000010000','0000010000',
        '0000010000','0000010000','0000010000','0000000000']
isolated=['0000000','0000000','0000000','0001000','0000000','0000000','0000000']
for name,layout,invert in (('vertical_earth_left',vertical,0),('vertical_green_left',vertical,1),
                           ('vertical_narrow_endpoints',narrow,0),('isolated_green',isolated,0),
                           ('isolated_earth',isolated,1)):
    records.append(assemble(name,solve_layout(layout,invert)))
with (OUT/'previews.json').open('x',encoding='utf-8') as stream:
    json.dump(dict(source='Saved baseline_94.png + interiors_bc.png. Offline valid assignments, not Godot Connect.',
                   baseline_sha256=mapping['output_sha256']['baseline_94.png'],
                   interiors_sha256=mapping['output_sha256']['interiors_bc.png'],previews=records),stream,indent=2)
    stream.write('\n')
print('Created',len(records),'saved-atlas offline previews;',sum(r['matched_boundaries'] for r in records),
      'shared boundaries match exactly; transitions use A and only solid interiors use A/B/C.')
