"""Additive PR119 feather comparison. No source refinement, engine or integration.

--write exclusively creates a new fixed evidence directory; --check regenerates
in memory. The saved v1 prototype, sources and all old tools remain read-only.
"""
import argparse
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
INPUT = ROOT/'assets/experiments/native_terrain_47_96/ground_refinement_v1'
OUTPUT = INPUT.parent/'ground_softness_comparison_v1'
BASE_REVISION = '9b558cceef13d2ab37563f89d96a5401236d1ec0'
PINS = {
    'tools/ground-art-refinement.py': '68223b5144221f67276bffffa311d72771d933dd9304b4b2dfc0f6f155437578',
    'assets/experiments/native_terrain_47_96/ground_refinement_v1/manifest.json':
        '0cfbc9453cae2bcca8e0654500c5098436edba01adbf995a3da3d61f1d4034fc',
}
TREATMENTS = (('CURRENT', .20, .80), ('CANDIDATE A', .15, .85), ('CANDIDATE B', .10, .90))
ANCHORS = ((64,64,0),(0,0,1),(64,0,2),(127,0,3),(0,64,4),
           (127,64,5),(64,127,7),(0,127,6),(127,127,8))
RELATIONSHIPS = (('right','left',(3,5,8),(1,4,6)),
                 ('bottom','top',(6,7,8),(1,2,3)))
LAYOUTS = ('meandering_boundary_varied', 'mixed_24x16')


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def require(condition, message):
    if not condition:
        raise ValueError(message)


def load_context():
    for name, expected in PINS.items():
        require(digest((ROOT/name).read_bytes().replace(b'\r\n', b'\n')) == expected, 'Changed pinned input: '+name)
    spec = importlib.util.spec_from_file_location('readonly_ground_study', ROOT/'tools/ground-art-refinement.py')
    study = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(study)
    bake = study.load_baker()
    manifest = json.loads((INPUT/'manifest.json').read_text())
    # Validate every saved prototype output, including all old preview images.
    for name, expected in manifest['output_sha256'].items():
        require(digest((INPUT/name).read_bytes()) == expected, 'Changed saved prototype: '+name)
    sources = [bake.decode_png((INPUT/'sources'/name).read_bytes())
               for name in ('earth_refined.png', 'green_refined.png')]
    require(all(p[:2] == (128,128) for p in sources), 'Unexpected refined source size')
    sources = [p[2] for p in sources]
    atlas = bake.decode_png((INPUT/'baseline_subset.png').read_bytes())[2]
    interiors = bake.decode_png((INPUT/'interiors_bc.png').read_bytes())[2]
    baseline = {(tuple(e['signature']), 'A'): study.crop(atlas, 1536, *e['atlas']) for e in manifest['baseline']}
    for entry in manifest['interiors']:
        baseline[tuple(entry['signature']), entry['variant']] = study.crop(interiors, 256, *entry['atlas'])
    inventory = json.loads((study.BASE/'baked_v2/mapping.json').read_text())
    expected = {tuple(e['atlas']): tuple(e['signature']) for e in inventory['baseline']}
    for entry in manifest['baseline']:
        require(expected[tuple(entry['atlas'])] == tuple(entry['signature']), 'Changed signature/coordinate')
    return study, bake, manifest, sources, baseline


def validate_tiles(context, tiles, masks):
    study, bake, manifest, sources, baseline = context
    require(set(tiles) == set(baseline), 'Changed subset inventory')
    anchors = comparisons = 0
    for (signature, variant), pixels in tiles.items():
        require(len(pixels) == 128*128*3, 'Unexpected tile size')
        require(not any(pixels[i:i+3] in (b'\x00\x00\x00',b'\xff\x00\xff')
                        for i in range(0,len(pixels),3)), 'Placeholder pixel')
        if variant != 'A':
            require(pixels == baseline[signature, variant], 'Changed B/C interior')
            continue
        old_mask = bake.mask(signature)
        mask = masks[signature]
        require(all((a >= .5) == (b >= .5) for a,b in zip(old_mask,mask)), 'Moved contour centerline')
        for x,y,k in ANCHORS:
            offset = (y*128+x)*3
            require(mask[y*128+x] == signature[k], 'Changed mask anchor')
            require(pixels[offset:offset+3] == sources[signature[k]][offset:offset+3], 'Changed raster anchor')
            anchors += 1
    for (a,av), ap in tiles.items():
        for (b,bv), bp in tiles.items():
            for side, opposite, ia, ib in RELATIONSHIPS:
                if tuple(a[i] for i in ia) == tuple(b[i] for i in ib):
                    require(study.edge(ap,side) == study.edge(bp,opposite), 'Incompatible saved edges')
                    comparisons += 1
    for center in (0,1):
        require(tiles[(center,)*9,'A'] == sources[center], 'Changed solid source')
        for side in ('top','bottom','left','right'):
            require(len({study.edge(tiles[(center,)*9,v],side) for v in 'ABC'}) == 1, 'Changed interior edge')
    adjacencies = 0
    for name in LAYOUTS:
        layout = manifest['layouts'][name]
        for y,row in enumerate(layout):
            for x,entry in enumerate(row):
                sig = tuple(entry['signature'])
                require(sig == (sig[0],)*9 or entry['variant'] == 'A', 'Variant on boundary')
                for dx,dy,side,opposite,ia,ib in ((1,0,*RELATIONSHIPS[0]),(0,1,*RELATIONSHIPS[1])):
                    if x+dx < len(row) and y+dy < len(layout):
                        neighbor = layout[y+dy][x+dx]
                        ns = tuple(neighbor['signature'])
                        require(tuple(sig[i] for i in ia) == tuple(ns[i] for i in ib), 'Invalid preview relationship')
                        require(study.edge(tiles[sig,entry['variant']],side) ==
                                study.edge(tiles[ns,neighbor['variant']],opposite), 'Preview seam mismatch')
                        adjacencies += 1
    return dict(configured_records=len(tiles), baseline_signatures=len(manifest['baseline']),
                anchors=anchors, compatible_ordered_edge_pairs=comparisons,
                assembled_adjacencies=adjacencies,
                partially_blended_texels=sum(sum(0 < v < 1 for v in mask) for mask in masks.values()),
                maximum_shared_edge_channel_difference=0)


def render(context, lo, hi):
    study, bake, manifest, sources, baseline = context
    linear = [[bake.to_linear(v) for v in source] for source in sources]
    tiles, masks = {}, {}
    for entry in manifest['baseline']:
        sig = tuple(entry['signature'])
        mask = [bake.smooth((v-lo)/(hi-lo)) for v in bake.mask(sig)]
        masks[sig] = mask
        # Same per-channel arithmetic as saved v1, with only feather endpoints
        # varied. Source images and interior variations are never regenerated.
        tiles[sig,'A'] = bytes(bake.to_srgb(bake.lerp(linear[0][i],linear[1][i],mask[i//3]))
                               for i in range(128*128*3))
    for key,pixels in baseline.items():
        if key[1] != 'A':
            tiles[key] = pixels
    report = validate_tiles(context, tiles, masks)
    if (lo,hi) == (.20,.80):
        require(tiles == baseline, 'Current treatment does not reproduce saved v1 pixels')
    return tiles, masks, report


def assemble(study, layout, tiles):
    image = study.board(len(layout[0])*128, len(layout)*128)
    for y,row in enumerate(layout):
        for x,entry in enumerate(row):
            study.paste(image, (128,128,tiles[tuple(entry['signature']),entry['variant']]), x*128,y*128)
    return image


def comparison(context, models, name):
    study, bake, manifest, _, _ = context
    layout = manifest['layouts'][name]
    w, h = len(layout[0])*64, len(layout)*64
    # A same-coordinate 8x6 detail window below the entire 64px/tile layout.
    # Detail positions are fixed across all treatments; no filtering of masks.
    cx, cy = (2,1) if name == 'meandering_boundary_varied' else (12,4)
    detail = [row[cx:cx+8] for row in layout[cy:cy+6]]
    panel_width = max(w,1024)
    image = study.board(panel_width*3+64, h+768+168)
    title = 'MEANDERING BOUNDARY' if name == 'meandering_boundary_varied' else 'MIXED TERRAIN 24 X 16'
    study.text(image, 'OFFLINE SOFTNESS COMPARISON / '+title, 16,12)
    study.text(image, 'FULL IDENTICAL LAYOUT / 64 PX PER TILE / APPROXIMATE GAMEPLAY SCALE / NO RUNTIME SHADING', 16,36)
    for i,((label,lo,hi), model) in enumerate(zip(TREATMENTS,models)):
        tiles, _, _ = model
        x = 16+i*(panel_width+16)
        study.text(image, label+' / '+format(lo,'.2f')+' - '+format(hi,'.2f'),x,64)
        study.paste(image, assemble(study,layout,tiles),x,88,.5)
        study.text(image, 'SAME DETAIL / 128 PX PER TILE / CELL '+str(cx)+':'+str(cy),x,h+108)
        study.paste(image, assemble(study,detail,tiles),x,h+136)
    return bake.encode_png(*image)


def build():
    context = load_context()
    study, bake, manifest, sources, baseline = context
    models = [render(context,lo,hi) for _,lo,hi in TREATMENTS]
    files = {'.gdignore': b'', '.gitattributes': b'manifest.json text eol=lf\n'}
    for name in LAYOUTS:
        files[name+'_comparison.png'] = comparison(context,models,name)
    report = dict(status='comparison only; no feathering value selected', base_revision=BASE_REVISION,
                  pinned_inputs=PINS, source_sha256={name:digest((INPUT/'sources'/name).read_bytes())
                                                    for name in ('earth_refined.png','green_refined.png')},
                  layout_sha256={name:digest(json.dumps(manifest['layouts'][name],sort_keys=True,separators=(',',':')).encode())
                                 for name in LAYOUTS},
                  baseline=[dict(atlas=e['atlas'],signature=e['signature']) for e in manifest['baseline']],
                  interiors=manifest['interiors'],
                  treatments=[dict(label=label,range=[lo,hi],validation=model[2],
                                   tile_pixel_sha256=[dict(signature=list(sig),variant=v,sha256=digest(pixels))
                                                      for (sig,v),pixels in sorted(model[0].items())])
                              for (label,lo,hi),model in zip(TREATMENTS,models)],
                  output_sha256={name:digest(raw) for name,raw in files.items()})
    files['manifest.json'] = (json.dumps(report,indent=2)+'\n').encode()
    study.checked_inputs()
    return files


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument('--write',action='store_true')
    mode.add_argument('--check',action='store_true')
    args = parser.parse_args()
    if args.write and OUTPUT.exists():
        parser.error('Refusing existing comparison directory')
    files = build()
    if args.check:
        for name,raw in files.items():
            require((OUTPUT/name).read_bytes() == raw, 'Regeneration mismatch: '+name)
        print('PASS: all comparison outputs regenerate exactly in memory; no writes.')
    else:
        OUTPUT.mkdir(exist_ok=False)
        for name,raw in files.items():
            with (OUTPUT/name).open('xb') as stream:
                stream.write(raw)
        print('Created two three-way comparison PNGs and isolated provenance. No current artwork changed.')


if __name__ == '__main__':
    main()
