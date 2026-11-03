"""Explicit bounded offline grayscale diagnostics. No output on import.

Run --generate once. Runs the required gate first; any failure stops generation.
Only a fresh ignored artifacts/tmp child can receive output. No engine commands.
"""
import argparse
import ctypes
from ctypes import wintypes
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import struct
import subprocess
import sys
import threading
import time
import unittest
import zlib

ROOT = Path(__file__).resolve().parents[1]
MANIFEST = ROOT / 'tests/fixtures/terrain_stage2b2_cases.json'
SUITES = ('static_terrain_stage2b2_reconstruction_test.py',
          'static_terrain_stage2_coverage_test.py', 'static_terrain_stage2b_compatibility_test.py',
          'static_ground_rejection_test.py', 'static_low_green_ground_test.py',
          'static_ground_publication_test.py', 'static_transition_safety_test.py')


def png(width, height, pixels):
    def chunk(kind, body):
        return struct.pack('>I', len(body))+kind+body+struct.pack('>I', zlib.crc32(kind+body))
    scan = b''.join(b'\0'+pixels[y*width*3:(y+1)*width*3] for y in range(height))
    return (b'\x89PNG\r\n\x1a\n'+chunk(b'IHDR', struct.pack('>IIBBBBB', width, height, 8, 2, 0, 0, 0))
            +chunk(b'IDAT', zlib.compress(scan, 6))+chunk(b'IEND', b''))


def memory_bytes():
    class Counters(ctypes.Structure):
        _fields_ = [('cb', wintypes.DWORD), ('PageFaultCount', wintypes.DWORD)] + [
            (name, ctypes.c_size_t) for name in ('PeakWorkingSetSize','WorkingSetSize',
            'QuotaPeakPagedPoolUsage','QuotaPagedPoolUsage','QuotaPeakNonPagedPoolUsage',
            'QuotaNonPagedPoolUsage','PagefileUsage','PeakPagefileUsage','PrivateUsage')]
    counters = Counters()
    counters.cb = ctypes.sizeof(counters)
    kernel = ctypes.WinDLL('kernel32', use_last_error=True)
    kernel.GetCurrentProcess.restype = wintypes.HANDLE
    psapi = ctypes.WinDLL('psapi', use_last_error=True)
    psapi.GetProcessMemoryInfo.argtypes = [wintypes.HANDLE, ctypes.c_void_p, wintypes.DWORD]
    if not psapi.GetProcessMemoryInfo(kernel.GetCurrentProcess(), ctypes.byref(counters), counters.cb):
        raise RuntimeError('Cannot enforce working-memory observation')
    return max(counters.PeakWorkingSetSize, counters.PrivateUsage)


def synthetic(case):
    kind = case['kind']
    def material(cell):
        x, y = cell
        if kind == 'pattern':
            ox, oy = case.get('origin', (0, 0))
            bit = ((0, 1), (3, 2))[(y-oy) % 2][(x-ox) % 2]
            return int(bool(case['pattern'] & (1 << bit)))
        return int({'island': (x,y)==(0,0), 'hole': (x,y)!=(0,0),
                    'horizontal': y>=0, 'vertical': x>=0, 'diagonal': x+y>=0,
                    'corner': x>=0 and y>=0, 't-junction': y>=0 or x==0,
                    'four-way': x==0 or y==0}[kind])
    return material


def identities():
    paths = subprocess.check_output(['git','ls-files'], cwd=ROOT, text=True).splitlines()
    paths += ['docs/experiments/terrain_stage2b2_reconstruction.md',
              'tests/terrain_stage2b2_reconstruction_reference.py',
              'tests/static_terrain_stage2b2_reconstruction_test.py',
              'tests/fixtures/terrain_stage2b2_cases.json', 'tools/terrain-stage2b2-diagnostics.py']
    # Hash only numerical/source-scope inputs; full tracked preservation is tested.
    relevant = [p for p in set(paths) if p.startswith(('tests/', 'tools/')) and p.endswith(('.py','.json'))]
    relevant += ['scenes/world/planet_exterior.tscn','scenes/world/planet_generator.gd',
                 'scenes/world/crash_site_protection.gd','scenes/world/world_coordinates.gd']
    return {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sorted(set(relevant))}


def readable_preflight(manifest, reference):
    """Validate the authorized profile and preserve the original study exactly."""
    reviewed = '5761715e74e4ec274e579b681f4a97ac0973843c'
    original = json.loads(subprocess.check_output(
        ['git','show',reviewed+':tests/fixtures/terrain_stage2b2_cases.json'],cwd=ROOT))
    if {k:v for k,v in manifest.items() if k!='readable_profile'} != original:
        raise RuntimeError('Original manifest/cases/limits changed')
    allowed = {'tools/terrain-stage2b2-diagnostics.py', 'tests/fixtures/terrain_stage2b2_cases.json',
               'docs/experiments/terrain_stage2b2_reconstruction.md'}
    changes = set(subprocess.check_output(['git','diff','--name-only',reviewed,'--'],cwd=ROOT,text=True).splitlines())
    if not changes <= allowed:
        raise RuntimeError('Readable refinement exceeds three-file authorization')
    profile = manifest['readable_profile']
    expected = [('natural',[2496,2496,3008,2752],[129,65],4,4),
                ('crash',[480,-672,736,-416],[65,65],4,8),
                ('inset',[604,-548,612,-540],[33,33],0.25,8)]
    if (profile['version']!='readable-v1' or profile['output_count']!=3
            or profile['canvases']!={'natural':[1152,384],'crash':[1152,944]}
            or profile['panels']!={'left_x':24,'right_x':600,'main_y':64,'inset_y':640}
            or len(profile['cases'])!=3
            or profile['original_directory']!='artifacts/tmp/stage2b2-20261103-132958'):
        raise RuntimeError('Unsupported readable layout')
    for case, (name,rect,grid,spacing,scale) in zip(profile['cases'],expected):
        if (case['id'],case['rect'],case['grid'],case['spacing'],case['display_scale'])!=(name,rect,grid,spacing,scale):
            raise RuntimeError('Readable case drift')
        if case['seed']!=26026 or case['gutter']!=1 or case['phase']!='endpoints-inclusive':
            raise RuntimeError('Unsupported sample identity')
        for axis in (0,1):
            if reference.F(rect[axis+2]-rect[axis])/(grid[axis]-1)!=spacing:
                raise RuntimeError('Anisotropic or incorrect sampling')
        if (tuple(case['source_centers_a'])!=reference.source_bounds(rect,1)
                or tuple(case['source_squares_b'])!=reference.source_bounds(rect,1,16)):
            raise RuntimeError('Unproved source halo')
        size=profile['canvases']['natural' if name=='natural' else 'crash']
        top=640 if name=='inset' else 64
        if 600+grid[0]*scale>size[0] or top+grid[1]*scale>size[1]:
            raise RuntimeError('Panel does not fit canvas')
    original_dir=ROOT/profile['original_directory']
    raw=(original_dir/'manifest.json').read_bytes()
    evidence=json.loads(raw)
    preserved={'manifest.json':hashlib.sha256(raw).hexdigest()}
    if len(evidence['outputs'])!=7:
        raise RuntimeError('Original seven-output inventory changed')
    for row in evidence['outputs']:
        payload=(original_dir/row['file']).read_bytes()
        if len(payload)!=row['bytes'] or hashlib.sha256(payload).hexdigest()!=row['sha256']:
            raise RuntimeError('Original diagnostic preservation failure')
        preserved[row['file']]=row['sha256']
    # Tests and both mathematical references must remain byte-identical to the
    # original generation, independent of Git's line-ending normalization.
    for path,digest in evidence['source_sha256'].items():
        if path.startswith('tests/') and path.endswith('.py'):
            if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=digest:
                raise RuntimeError('Mathematical reference or existing test bytes changed')
    receipt=json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
    for path,entry in receipt['protected_sidecars'].items():
        if hashlib.sha256((ROOT/path).read_bytes()).hexdigest()!=entry['sha256']:
            raise RuntimeError('Protected sidecar changed')
    for tag,sha in receipt['tags'].items():
        if (subprocess.check_output(['git','rev-parse',tag+'^{}'],cwd=ROOT,text=True).strip()!=sha
                or subprocess.check_output(['git','cat-file','-t',tag],cwd=ROOT,text=True).strip()!='tag'):
            raise RuntimeError('Preservation tag changed')
    if subprocess.check_output(['git','rev-parse','refs/heads/codex/terrain-fidelity-a1-artwork'],cwd=ROOT,text=True).strip()!=receipt['commits']['a1']['commit']:
        raise RuntimeError('Original A1 branch changed')
    bundle=Path(receipt['bundle']['path'])
    with bundle.open('rb') as stream:
        digest=hashlib.file_digest(stream,'sha256').hexdigest()
    if bundle.stat().st_size!=receipt['bundle']['size'] or digest!=receipt['bundle']['sha256']:
        raise RuntimeError('Preservation bundle changed')
    return preserved


def readable_generate(manifest, reference, labels, geometry, before, counts, timings, start, preserved):
    """Three PNGs from one sample pass; presentation only, no algorithm changes."""
    profile=manifest['readable_profile']; limits=manifest['limits']
    evaluations=0; total_bytes=0; predicate_calls=0
    def check():
        if (time.monotonic()-start>=120 or memory_bytes()>limits['memory_bytes']
                or evaluations>limits['evaluations'] or total_bytes>limits['bytes']):
            raise RuntimeError('Readable diagnostic limit breached; no retry')
    check()
    sampled={}
    protection=reference.Protection(26026,geometry)
    model=reference.Reconstruction(lambda cell:protection.center_record(cell)[0],26026,protection)
    for case in profile['cases']:
        nx,ny=case['grid']; x0,y0,x1,y1=map(reference.F,case['rect'])
        raw=[[],[]]; final=[[],[]]; excluded=[]; centers=[]
        for y in range(ny):
            check()
            for x in range(nx):
                point=(x0+(x1-x0)*x/(nx-1),y0+(y1-y0)*y/(ny-1))
                values=model.values(point); evaluations+=3
                for target,source in enumerate((1,2)):
                    raw[target].append(values[source]); final[target].append(values[source]*values[3])
                # Natural clean output needs no exclusion overlay calculation.
                excluded.append(reference.classification.exclusion_reason(point,geometry) is not None if case['id']!='natural' else False)
                predicate_calls+=int(case['id']!='natural')
                centers.append(all((v-32)%64==0 for v in point))
        sampled[case['id']]=(case,raw,final,excluded,centers)
    check()
    destination=ROOT/'artifacts/tmp'/('stage2b2-readable-v1-'+time.strftime('%Y%m%d-%H%M%S'))
    if destination.exists() or destination.parent.resolve()!=(ROOT/'artifacts/tmp').resolve():
        raise RuntimeError('Fresh ignored destination required')
    if subprocess.run(['git','check-ignore','-q',str(destination/'manifest.json')],cwd=ROOT).returncode!=0:
        raise RuntimeError('Readable destination is not ignored')
    destination.mkdir()
    def caption(canvas,text,x,y,size=2):
        if x+len(text)*6*size>canvas[0] or y+7*size>canvas[1]:
            raise RuntimeError('Label does not fit readable layout')
        labels.text(canvas,text,x,y,size)
    def panel(canvas,kind,candidate,origin,overlay):
        case,raw,final,excluded,centers=sampled[kind]
        nx,ny=case['grid']; scale=case['display_scale']
        pixels=bytearray()
        for value in final[candidate]:
            shade=round(255*reference.clamp(value)) if not overlay else 0
            pixels.extend((shade,shade,shade))
        labels.paste(canvas,(nx,ny,pixels),*origin,scale)
        if not overlay: return
        # Separate line map: solid final .5, long-dash pre .5, dotted exclusion.
        # Draw on the enlarged display, with line styles in display pixels.
        def dot(x,y):
            if 0<=x<nx*scale and 0<=y<ny*scale:
                offset=((origin[1]+y)*canvas[0]+origin[0]+x)*3
                canvas[2][offset:offset+3]=b'\xff\xff\xff'
        fields=((excluded,'dotted'),([v>=.5 for v in raw[candidate]],'dashed'),
                ([v>=.5 for v in final[candidate]],'solid'))
        for field,style in fields:
            for y in range(ny):
                for x in range(nx):
                    i=y*nx+x
                    for neighbor,vertical in ((i-1,True),(i-nx,False)):
                        if (vertical and x==0) or (not vertical and y==0): continue
                        if field[i]==field[neighbor]: continue
                        for k in range(scale):
                            xx=x*scale if vertical else x*scale+k
                            yy=y*scale+k if vertical else y*scale
                            phase=yy if vertical else xx
                            if style=='solid' or (phase%12<7 if style=='dashed' else phase%6<2): dot(xx,yy)
        for i,is_center in enumerate(centers):
            if is_center:
                cx=(i%nx)*scale+scale//2; cy=(i//nx)*scale+scale//2
                for d in range(-3,4): dot(cx+d,cy); dot(cx,cy+d)
    outputs=[]
    for kind,overlay in (('natural',False),('crash',False),('crash',True)):
        check()
        width,height=profile['canvases'][kind]
        if width>limits['width'] or height>limits['height']: raise RuntimeError('Image bounds')
        canvas=(width,height,bytearray(bytes((32,32,32))*width*height))
        caption(canvas,'SEED 26026 / '+kind.upper()+(' / LINE MAP ONLY' if overlay else ' / CLEAN COVERAGE'),24,12)
        caption(canvas,'A / SHARPENED 5/32',24,40)
        caption(canvas,'B / MIDPOINT W16',600,40)
        for candidate,x in enumerate((24,600)): panel(canvas,kind,candidate,(x,64),overlay)
        if kind=='natural':
            caption(canvas,'WORLD X 2496 TO 3008 / Y 2496 TO 2752',24,336,1)
            caption(canvas,'129 BY 65 SAMPLES / STEP 4 / DISPLAY 4X NEAREST',24,352,1)
            caption(canvas,'BLACK 0 EARTH / WHITE 1 GREEN / GRAY PARTIAL / NO OVERLAYS',24,368,1)
        else:
            caption(canvas,'WORLD X 480 TO 736 / Y -672 TO -416 / STEP 4 / DISPLAY 8X',24,600,1)
            caption(canvas,'DETAIL X 604 TO 612 / Y -548 TO -540 / STEP 0.25 / DISPLAY 8X',24,620,1)
            for candidate,x in enumerate((24,600)): panel(canvas,'inset',candidate,(x,640),overlay)
            caption(canvas,'SOLID FINAL .5 / DASH PRE .5 / DOT STRICT EXCLUSION / PLUS CENTER' if overlay
                    else 'BLACK 0 EARTH / WHITE 1 GREEN / GRAY PARTIAL / CLEAN SAMPLES',24,916,1)
            caption(canvas,'SAMPLED LINE MAP / OVERLAPPING LINES CAN COINCIDE' if overlay
                    else 'NEAREST DISPLAY ENLARGEMENT ADDS NO ANALYTIC DETAIL / NOT GODOT ZOOM',24,932,1)
        for i in range(0,len(canvas[2]),3):
            canvas[2][i:i+3]=bytes((canvas[2][i],))*3
        data=png(width,height,canvas[2]); total_bytes+=len(data); check()
        name=('stage2b2-r2-seed26026-'+kind+'-a5of32-vs-w16-step4'
              +('-inset025' if kind=='crash' else '')+('-overlay.png' if overlay else '-clean.png'))
        with (destination/name).open('xb') as stream: stream.write(data)
        outputs.append(dict(file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),width=width,height=height))
    if len(outputs)!=3 or identities()!=before or readable_preflight(manifest,reference)!=preserved:
        raise RuntimeError('Final count/input/preservation failure')
    record=dict(status='complete',profile=profile,source_sha256=before,
                head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                geometry_sha256=reference.classification.geometry_identity(geometry),gate_counts=counts,
                gate_seconds=timings,seconds=time.monotonic()-start,peak_memory_observed=memory_bytes(),
                sampled_positions=evaluations//3,candidate_evaluations=evaluations,
                shared_protection_calls=evaluations//3,extra_exclusion_predicate_calls=predicate_calls,
                overlay_reconstruction_calls=0,outputs=outputs,original_output_sha256=preserved,
                arithmetic='unchanged conditional Python enclosure and exact-rational protection',
                display='nearest enlargement; equal world spacing; line map uses sampled crossings, not exact curves')
    data=(json.dumps(record,indent=2)+'\n').encode(); total_bytes+=len(data); check()
    with (destination/'manifest.json').open('xb') as stream: stream.write(data)
    print(json.dumps(dict(destination=str(destination),bytes=total_bytes,**record)))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', required=True)
    parser.add_argument('--profile', choices=('original','readable-v1'), default='original')
    args = parser.parse_args()
    if os.name != 'nt':
        raise SystemExit('Bounded generator requires the reviewed Windows memory check')
    start = time.monotonic()
    def timeout():
        print('STOP: 120-second command limit; no automatic retry', file=sys.stderr, flush=True)
        os._exit(124)
    watchdog = threading.Timer(120, timeout)
    watchdog.daemon = True
    watchdog.start()
    sys.path.insert(0, str(ROOT/'tests'))
    import terrain_stage2b2_reconstruction_reference as reference
    manifest = json.loads(MANIFEST.read_text())
    limits = manifest['limits']
    evaluations, total_bytes = 0, 0
    def check():
        if (time.monotonic()-start >= limits['seconds'] or memory_bytes() > limits['memory_bytes']
                or evaluations > limits['evaluations'] or total_bytes > limits['bytes']):
            raise RuntimeError('Diagnostic resource limit: stop without retry')
    before = identities()
    preserved=readable_preflight(manifest,reference) if args.profile=='readable-v1' else None
    check()
    counts = {}
    timings = {}
    for pattern in SUITES:
        suite_start=time.monotonic()
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=pattern)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        counts[pattern] = result.testsRun
        timings[pattern]=time.monotonic()-suite_start
        if not result.wasSuccessful():
            raise SystemExit('STOP: proof/regression gate failed; no diagnostics')
        check()
    if identities() != before:
        raise RuntimeError('Inputs changed during proof gate')
    spec = importlib.util.spec_from_file_location('stage2b2_labels', ROOT/'tools/ground-art-refinement.py')
    labels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(labels)
    geometry = reference.classification.load_geometry()
    if args.profile=='readable-v1':
        readable_generate(manifest,reference,labels,geometry,before,counts,timings,start,preserved)
        watchdog.cancel()
        return
    destination = ROOT/'artifacts/tmp'/('stage2b2-'+time.strftime('%Y%m%d-%H%M%S'))
    if destination.exists() or destination.parent.resolve() != (ROOT/'artifacts/tmp').resolve():
        raise RuntimeError('Fresh task-owned destination required')
    if subprocess.run(['git','check-ignore','-q',str(destination/'manifest.json')],cwd=ROOT).returncode != 0:
        raise RuntimeError('Destination must be ignored')
    destination.mkdir()
    groups = {}
    for case in manifest['cases']:
        groups.setdefault(case['group'], []).append(case)
    outputs = []
    for group, cases in groups.items():
        check()
        # One row per case; identical grids and scales across all three candidates.
        width, row_height = 1536, 70
        height = 40 + row_height*len(cases)
        if width > limits['width'] or height > limits['height']:
            raise RuntimeError('Image dimension budget')
        canvas = (width,height,bytearray(bytes((32,32,32))*width*height))
        labels.text(canvas, 'OFFLINE '+group.upper()+' / CONTROL A B / CLEAN THEN OVERLAY / SCALES .5 1 1.5', 4,4,1)
        for index, case in enumerate(cases):
            check()
            seed = case['seed']
            protection = reference.Protection(seed, geometry) if case['kind']=='production' else None
            material = ((lambda cell: protection.center_record(cell)[0]) if protection else synthetic(case))
            model = reference.Reconstruction(material, seed, protection)
            nx, ny = case['grid']
            x0,y0,x1,y1 = map(reference.F,case['rect'])
            raw = [[] for _ in range(3)]
            final = [[] for _ in range(3)]
            geometry_mask = []
            centers = []
            for y in range(ny):
                check()
                for x in range(nx):
                    p=(x0+(x1-x0)*x/(nx-1), y0+(y1-y0)*y/(ny-1))
                    values=model.values(p)
                    evaluations += 3
                    for c in range(3):
                        raw[c].append(values[c]); final[c].append(values[c]*values[3])
                    geometry_mask.append(reference.classification.exclusion_reason(p,geometry) is not None if protection else False)
                    centers.append(all((v-32)%64==0 for v in p))
            ybase=30+index*row_height
            labels.text(canvas,case['id'],4,ybase,1)
            xpos=210
            for c in range(3):
                for scale in case['scales']:
                    for overlay in (False,True):
                        pixels=bytearray()
                        for i,value in enumerate(final[c]):
                            shade=round(255*reference.clamp(value))
                            if overlay:
                                x,y=i%nx,i//nx
                                adjacent=[i-1] if x else []
                                if y: adjacent.append(i-nx)
                                # All overlays grayscale: center white, computed zero
                                # exclusion edge 96, pre .5 160, final .5 224.
                                if any(geometry_mask[j]!=geometry_mask[i] for j in adjacent): shade=96
                                if any((raw[c][j]>=.5)!=(raw[c][i]>=.5) for j in adjacent): shade=160
                                if any((final[c][j]>=.5)!=(value>=.5) for j in adjacent): shade=224
                                if centers[i]: shade=255
                            pixels.extend((shade,shade,shade))
                        labels.paste(canvas,(nx,ny,pixels),xpos,ybase,scale)
                        xpos += round(nx*scale)+4
            check()
        # Label helper uses pale green lettering; normalize all output to grayscale.
        for i in range(0,len(canvas[2]),3):
            shade=canvas[2][i]
            canvas[2][i:i+3]=bytes((shade,shade,shade))
        data=png(width,height,canvas[2])
        total_bytes+=len(data)
        check()
        name=f'{reference.RULE}-seeds-mixed-{group}-a5of32-w16-scales05-1-15.png'
        with (destination/name).open('xb') as stream: stream.write(data)
        outputs.append(dict(file=name,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),width=width,height=height))
    if len(outputs)>limits['images'] or identities()!=before:
        raise RuntimeError('Output count or source identity changed')
    record=dict(status='complete',baseline=reference.BASE,head=subprocess.check_output(['git','rev-parse','HEAD'],cwd=ROOT,text=True).strip(),
                source_sha256=before,geometry_sha256=reference.classification.geometry_identity(geometry),
                gate_counts=counts,manifest=manifest,outputs=outputs,evaluations=evaluations,
                seconds=time.monotonic()-start,peak_memory_observed=memory_bytes(),
                guard='conditional Python enclosure; exact rational protection; no engine parity',
                overlay='sampled original strict-exclusion edge 96; pre .5 160; final .5 224; exact sampled centers 255')
    data=(json.dumps(record,indent=2)+'\n').encode()
    total_bytes+=len(data)
    check()
    with (destination/'manifest.json').open('xb') as stream: stream.write(data)
    watchdog.cancel()
    print(json.dumps(dict(destination=str(destination),evaluations=evaluations,bytes=total_bytes,outputs=outputs)))


if __name__=='__main__':
    main()
