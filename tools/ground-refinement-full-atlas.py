"""Offline full candidate atlas. Reuse the approved PR119 renderer unchanged.

--write exclusively creates a new fixed directory; --check is read-only.
No Godot, production writes, texture refinement or edge repair.
"""
import argparse
import csv
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT/'assets/experiments/native_terrain_47_96/ground_refinement_full_v1'
START = '5d4f502928ea964e9d8b8b71ded87c0888b5aaaf'
APPROVAL = 'docs/experiments/ground_art_approved_treatment.json'


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def protected_inputs():
    """Record actual working bytes, including all historical evidence and guards."""
    paths = subprocess.check_output(['git','ls-tree','-r','--name-only',START],cwd=ROOT).decode().splitlines()
    prefixes = ('assets/experiments/native_terrain_47_96/', 'artifacts/evidence/pr100',
                'scenes/world/', 'scenes/experiments/native_terrain_47_96/', 'tests/')
    exact = {APPROVAL, 'project.godot', 'tools/bake-illustrated-terrain.py',
             'tools/ground-art-refinement.py', 'tools/ground-transition-softness.py',
             'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv'}
    return {p:digest((ROOT/p).read_bytes()) for p in paths if p in exact or p.startswith(prefixes)}


def load_context():
    approval = json.loads((ROOT/APPROVAL).read_text())
    require(approval['selected']['feather_range'] == [.15,.85], 'Changed owner selection')
    recipe = ROOT/approval['recipe']['path']
    require(digest(recipe.read_bytes().replace(b'\r\n',b'\n')) == approval['recipe']['sha256_lf'],
            'Changed approved renderer')
    ref = approval['comparison_manifest']
    require(digest((ROOT/ref['path']).read_bytes().replace(b'\r\n',b'\n')) == ref['sha256_lf'],
            'Changed approved comparison')
    spec = importlib.util.spec_from_file_location('approved_softness',recipe)
    soft = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(soft)
    context = soft.load_context()
    study,bake,manifest,sources,baseline = context
    for name,expected in approval['refined_source_sha256'].items():
        require(digest((soft.INPUT/'sources'/name).read_bytes()) == expected, 'Changed refined source')
    mapping = json.loads((study.BASE/'baked_v2/mapping.json').read_text())
    with (ROOT/'docs/experiments/native_terrain_47_96/tlwh_94_pattern_mapping.csv').open(newline='') as stream:
        rows = list(csv.DictReader(stream))
    expected = {(int(r['atlas_x']),int(r['atlas_y'])):
                [int(r['tlwh_center']),*(int(r['tlwh_'+b]) for b in bake.BITS)] for r in rows}
    records = mapping['baseline']
    require(len(records) == len(expected) == len({tuple(e['signature']) for e in records}) == 94,
            'Changed baseline signature inventory')
    require({tuple(e['atlas']):e['signature'] for e in records} == expected, 'Changed mapping/CSV coordinates')
    require([sum(e['family'] == f for e in records) for f in ('earth','green')] == [47,47], 'Changed families')
    require([(e['atlas'],e['signature'],e['variant']) for e in mapping['interiors']] ==
            [([v-1,c],[c]*9,'ABC'[v]) for c in (0,1) for v in (1,2)], 'Changed interior inventory')
    # New local context only: imported modules and historical records are unchanged.
    full_manifest = dict(manifest,baseline=records)
    old_atlas = bake.decode_png((study.BASE/'baked_v2/baseline_94.png').read_bytes())[2]
    full_baseline = {(tuple(e['signature']),'A'):study.crop(old_atlas,1536,*e['atlas']) for e in records}
    full_baseline.update({k:p for k,p in baseline.items() if k[1] != 'A'})
    return soft,(study,bake,full_manifest,sources,full_baseline),approval,mapping


def saved_tiles(study, bake, mapping, files):
    """Decode encoded atlas bytes before validation and preview assembly."""
    atlas = bake.decode_png(files['baseline_94.png'])
    interiors = bake.decode_png(files['interiors_bc.png'])
    require(atlas[:2] == (1536,1024) and interiors[:2] == (256,256), 'Changed RGB atlas dimensions')
    tiles = {(tuple(e['signature']),'A'):study.crop(atlas[2],1536,*e['atlas']) for e in mapping['baseline']}
    tiles.update({(tuple(e['signature']),e['variant']):study.crop(interiors[2],256,*e['atlas'])
                  for e in mapping['interiors']})
    return tiles


def preview_image(soft, study, layout, model, name):
    if name != 'abc_repetition':
        return soft.assemble(study,layout,model)
    # Earth and Green are separate broad material samples, not an adjacency.
    image = study.board(len(layout[0])*128, len(layout)*128+24)
    study.paste(image,soft.assemble(study,layout[:2],model),0,0)
    study.paste(image,soft.assemble(study,layout[2:],model),0,2*128+24)
    return image


def build():
    before = protected_inputs()
    soft,context,approval,mapping = load_context()
    study,bake,manifest,sources,original = context
    tiles,masks,report = soft.render(context,*approval['selected']['feather_range'])
    accepted = json.loads((ROOT/approval['comparison_manifest']['path']).read_text())
    selected = next(t for t in accepted['treatments'] if t['label'] == 'CANDIDATE A')
    for e in selected['tile_pixel_sha256']:
        require(digest(tiles[tuple(e['signature']),e['variant']]) == e['sha256'], 'Approved subset no longer reproduced')
    atlas = bytearray(1536*1024*3)
    for e in mapping['baseline']:
        bake.copy_cell(atlas,1536,*e['atlas'],tiles[tuple(e['signature']),'A'])
    files = {'.gdignore':b'', '.gitattributes':b'* text eol=lf\n*.png binary\n',
             'baseline_94.png':bake.encode_png(1536,1024,atlas),
             'interiors_bc.png':(soft.INPUT/'interiors_bc.png').read_bytes()}
    saved = saved_tiles(study,bake,mapping,files)
    require(saved == tiles, 'Saved atlas changed generated pixels')
    report = soft.validate_tiles(context,saved,masks)
    # Independent directional totals, using all 98 records including variants.
    counts = {}
    for label,(_,_,ia,ib) in zip(('horizontal','vertical'),soft.RELATIONSHIPS):
        counts[label] = sum(tuple(a[i] for i in ia) == tuple(b[i] for i in ib)
                            for a,av in saved for b,bv in saved)
    require(sum(counts.values()) == report['compatible_ordered_edge_pairs'], 'Inconsistent pair count')
    report['ordered_edge_pairs_by_direction'] = counts
    layouts = dict(manifest['layouts'])
    for c,name in enumerate(('earth_interior','green_interior')):
        layouts[name] = [[dict(signature=[c]*9,variant='A') for x in range(4)] for y in range(2)]
    layouts['abc_repetition'] = [[dict(signature=[c]*9,variant='ABC'[(x+2*y)%3])
                                for x in range(6)] for c in (0,1) for y in range(2)]
    for name,layout in layouts.items():
        a,b = (preview_image(soft,study,layout,t,name) for t in (original,saved))
        image = study.pair(name.replace('_',' '),a,b)
        files['previews/'+name+'.png'] = bake.encode_png(*image)
    # A complete coordinate contact sheet covers every corner/link/endpoint and
    # isolated patch without claiming unrelated neighboring tiles are compatible.
    def contact(model):
        image = study.board(12*136,8*152)
        for e in mapping['baseline']:
            x,y = e['atlas']; px,py = x*136,y*152
            study.text(image,e['family']+' '+str(x)+':'+str(y),px,py,1)
            study.paste(image,(128,128,model[tuple(e['signature']),'A']),px,py+12)
        return image
    files['previews/all_transitions.png'] = bake.encode_png(*study.pair('ALL 94 SEPARATE TILES',contact(original),contact(saved)))
    records = [dict(e,variant='A',alternative_id=0,pixel_sha256=digest(saved[tuple(e['signature']),'A']))
               for e in mapping['baseline']]
    interiors = [dict(e,alternative_id=0,pixel_sha256=digest(saved[tuple(e['signature']),e['variant']]))
                 for e in mapping['interiors']]
    result = dict(status='isolated complete candidate; owner visual acceptance pending; production integration deferred',
                  starting_revision=START,approval=approval,recipe=dict(path='tools/ground-refinement-full-atlas.py',
                  sha256_lf=digest(Path(__file__).read_bytes().replace(b'\r\n',b'\n')),
                  method='unchanged approved render with expanded local inventory; saved B/C bytes'),
                  source_sha256=approval['refined_source_sha256'],
                  protected_working_input_sha256=before,
                  hash_convention='protected working inputs raw; explicit recipe/comparison sha256_lf normalized',
                  tile_size=[128,128],baseline_dimensions=[1536,1024],interior_dimensions=[256,256],
                  baseline_count=94,unique_signatures=94,configured_records=98,families=dict(earth=47,green=47),
                  unused_baseline_slots=[[x,y] for y in range(8) for x in range(12)
                                         if [x,y] not in [e['atlas'] for e in records]],
                  baseline=records,interiors=interiors,validation=report,layouts=layouts,
                  preview_note='offline PNG comparisons; original left, candidate right; 128 and 64 pixels per tile; no runtime shading',
                  output_sha256={name:digest(raw) for name,raw in sorted(files.items())})
    files['manifest.json'] = (json.dumps(result,indent=2)+'\n').encode()
    require(protected_inputs() == before, 'Protected working input changed during generation')
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.write and OUTPUT.exists():
        parser.error('Refusing existing candidate directory')
    files = build()
    if args.check:
        for name,raw in files.items():
            require((OUTPUT/name).read_bytes() == raw, 'Regeneration mismatch: '+name)
        print('PASS: byte-identical regeneration of',len(files),'outputs; read-only; 98 records / 94 signatures.')
    else:
        OUTPUT.mkdir(exist_ok=False)
        for name,raw in files.items():
            path = OUTPUT/name
            path.parent.mkdir(exist_ok=True)
            with path.open('xb') as stream:
                stream.write(raw)
        print('Created isolated candidate; 94 signatures / 98 records; no Godot or production integration.')
    print(json.loads(files['manifest.json'])['validation'])


if __name__ == '__main__':
    main()
