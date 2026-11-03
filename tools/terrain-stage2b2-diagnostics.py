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


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--generate', action='store_true', required=True)
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
    check()
    counts = {}
    for pattern in SUITES:
        suite = unittest.defaultTestLoader.discover(str(ROOT/'tests'), pattern=pattern)
        result = unittest.TextTestRunner(verbosity=2).run(suite)
        counts[pattern] = result.testsRun
        if not result.wasSuccessful():
            raise SystemExit('STOP: proof/regression gate failed; no diagnostics')
        check()
    if identities() != before:
        raise RuntimeError('Inputs changed during proof gate')
    spec = importlib.util.spec_from_file_location('stage2b2_labels', ROOT/'tools/ground-art-refinement.py')
    labels = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(labels)
    geometry = reference.classification.load_geometry()
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
