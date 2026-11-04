"""Explicit bounded offline candidate diagnostics. No engine or writes on import."""
import argparse
from fractions import Fraction as F
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import time
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'tests'))
import terrain_adaptive_cpu_reference as candidate
import terrain_stage2_reference as ids
import terrain_stage2b2_reconstruction_reference as baseline


def load(name, path):
    spec = importlib.util.spec_from_file_location(name, ROOT/path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, text=True).strip()


def preservation():
    receipt = json.loads((ROOT/'artifacts/logs/terrain-preservation-2026-11-03.json').read_text())
    sidecars = {p:e for p,e in receipt['protected_sidecars'].items() if p.startswith('assets/environment/exterior/')}
    assert len(sidecars) == 15
    for p,e in receipt['protected_sidecars'].items():
        assert sha(ROOT/p) == e['sha256']
    for tag, target in receipt['tags'].items():
        assert git('cat-file','-t',tag) == 'tag' and git('rev-parse',tag+'^{}') == target
    assert git('rev-parse','refs/heads/codex/terrain-fidelity-a1-artwork') == receipt['commits']['a1']['commit']
    bundle = receipt['bundle']
    assert Path(bundle['path']).stat().st_size == bundle['size'] and sha(bundle['path']) == bundle['sha256']
    for p,h in receipt['commits']['c1']['sha256'].items():
        if p.endswith(('/sources/earth.png','/sources/green.png')):
            assert sha(ROOT/p) == h
    evidence = {}
    for name in ('stage2b2-20261103-132958','stage2b2-readable-v1-20261103-134527'):
        directory = ROOT/'artifacts/tmp'/name
        manifest = json.loads((directory/'manifest.json').read_text())
        evidence[name+'/manifest.json'] = sha(directory/'manifest.json')
        for row in manifest['outputs']:
            assert sha(directory/row['file']) == row['sha256']
            assert (directory/row['file']).stat().st_size == row['bytes']
            evidence[name+'/'+row['file']] = row['sha256']
    return evidence


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--generate', action='store_true', required=True)
    parser.parse_args()
    preserved = preservation()
    paths = set(git('ls-files').splitlines()) | {
        'tests/terrain_adaptive_cpu_reference.py', 'tests/static_terrain_adaptive_cpu_test.py',
        'tools/terrain-adaptive-cpu-diagnostics.py'}
    before = {p:sha(ROOT/p) for p in sorted(paths)}
    state = (git('rev-parse','HEAD'), git('status','--porcelain'), git('diff','--cached'))
    utility = load('old_diagnostic_utilities', 'tools/terrain-stage2b2-diagnostics.py')
    labels = load('old_diagnostic_labels', 'tools/ground-art-refinement.py')
    start = time.monotonic()
    def check():
        if time.monotonic()-start > 120 or utility.memory_bytes() > 512*1024**2:
            raise RuntimeError('Diagnostic resource limit exceeded; stop without retry')
    check()
    cover = candidate.Cover(ids.load_geometry())
    prepared = time.monotonic()-start
    field = candidate.Field(cover, 26026)
    old = baseline.Protection(26026, cover.authored)
    reconstruction = baseline.Reconstruction(lambda cell: old.center_record(cell)[0], 26026, old)
    payload = json.dumps(cover.payload(), separators=(',', ':')).encode()
    destination = ROOT/'artifacts/tmp'/('adaptive-cpu-'+uuid.uuid4().hex)
    assert not destination.exists()
    assert subprocess.run(['git','check-ignore','-q',str(destination/'manifest.json')],cwd=ROOT).returncode == 0
    destination.mkdir()
    outputs, costs = [], []
    crops = [('minimum-clearance',(604,-548,612,-540),33,33,6),
             ('crash-site',(480,-672,736,-416),65,65,4),
             ('natural',(2496,2496,3008,2752),65,33,4),
             ('seam-patches',(-64,-1344,64,-1216),33,33,6)]
    for name, rect, nx, ny, scale in crops:
        panels = [bytearray(),bytearray(),bytearray()]
        deltas, blocked, query_boxes = [], 0, []
        begin = time.monotonic()
        for y in range(ny):
            check()
            for x in range(nx):
                p = (F(rect[0])+F(rect[2]-rect[0])*x/(nx-1),
                     F(rect[1])+F(rect[3]-rect[1])*y/(ny-1))
                original = reconstruction.values(p)
                original = original[1]*original[3]
                a, value = field.values(p)
                value = float(value)
                if ids.exclusion_reason(p,cover.authored) is not None:
                    if value != 0:
                        raise RuntimeError('BLOCKED: positive protected diagnostic sample')
                    blocked += 1
                delta = abs(original-value)
                deltas.append(delta)
                query_boxes.append(len(cover.buckets.get(tuple(int(v//64) for v in p),())))
                for target, shade in zip(panels,(original,value,delta)):
                    c = round(255*shade)
                    target.extend((c,c,c))
        width, height = 3*(nx*scale+16), ny*scale+70
        canvas = (width,height,bytearray(bytes((32,32,32))*width*height))
        labels.text(canvas,'OFFLINE CONDITIONAL PROTOTYPE / '+name.upper(),8,8,1)
        for i, title in enumerate(('ACCEPTED A MODEL','ADAPTIVE BOX MODEL','ABS DIFFERENCE')):
            labels.text(canvas,title,8+i*(nx*scale+16),28,1)
            labels.paste(canvas,(nx,ny,panels[i]),8+i*(nx*scale+16),50,scale)
        data = utility.png(width,height,canvas[2])
        filename = name+'.png'
        (destination/filename).write_bytes(data)
        outputs.append(dict(file=filename,bytes=len(data),sha256=hashlib.sha256(data).hexdigest(),rect=rect,grid=[nx,ny]))
        costs.append(dict(crop=name,samples=nx*ny,seconds=time.monotonic()-begin,
                          max_abs_difference=max(deltas),mean_abs_difference=sum(deltas)/len(deltas),
                          protected_samples=blocked,max_query_boxes=max(query_boxes)))
    check()
    # Separate query timing: bounded fixed samples, no engine/performance claim.
    queries = [(F(604)+F(x,4),F(-548)+F(y,4)) for y in range(33) for x in range(33)]
    begin = time.monotonic()
    for p in queries:
        field.values(p)
    query_seconds = time.monotonic()-begin
    check()
    assert {p:sha(ROOT/p) for p in before} == before
    assert preservation() == preserved
    assert state == (git('rev-parse','HEAD'),git('status','--porcelain'),git('diff','--cached'))
    minimum = cover.distance_surrogate((608,-544))
    record = dict(label='OFFLINE CONDITIONAL PROTOTYPE: not Godot/GPU evidence',
                  head=state[0],geometry_sha256=candidate.IDENTITY,source_sha256=before,
                  preservation=preserved,preparation_seconds=prepared,
                  peak_process_memory_bytes=utility.memory_bytes(),nodes=cover.nodes,
                  leaves=len(cover.leaves),blocked_boxes=len(cover.boxes),
                  uncertain=sum(s=='uncertain' for _,s in cover.leaves),
                  smallest_box_side=str(min(b[2]-b[0] for b in cover.boxes)),
                  canonical_box_json_bytes=len(payload),index_buckets=len(cover.buckets),
                  index_references=sum(map(len,cover.buckets.values())),
                  index_max_bucket=max(map(len,cover.buckets.values())),
                  minimum_center_box_distance_squared=str(minimum*32),
                  cached_centers=len(field.centers),query_samples=len(queries),query_seconds=query_seconds,
                  total_seconds=time.monotonic()-start,crops=costs,outputs=outputs)
    (destination/'boxes.json').write_bytes(payload)
    (destination/'manifest.json').write_text(json.dumps(record,indent=2)+'\n')
    print(json.dumps({k:v for k,v in record.items() if k not in ('source_sha256','preservation')},indent=2))
    print('OUTPUT',destination.relative_to(ROOT).as_posix())


if __name__ == '__main__':
    main()
