"""Offline Ferrite v1 geometry compiler. Standard library only; never runs Godot."""
import argparse
from collections import deque
import json
from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
ASSET = Path('assets/environment/exterior/ferrite/catalog_v1')
CELL = 64
SOURCE_CELL = 128
PAD = 64
VERSION = 'faceted_ferrite_catalog_v1'
RANGES = {'small': (3, 3, 5, 4), 'medium': (6, 4, 8, 6), 'large': (9, 6, 12, 8)}
FAMILIES = {'rectangle', 'l_shape', 'stepped', 'organic'}


def require(condition, message):
    if not condition:
        raise ValueError(message)


def reachable(cells):
    if not cells:
        return set()
    seen = {min(cells)}
    queue = deque(seen)
    while queue:
        x, y = queue.popleft()
        for point in ((x-1, y), (x+1, y), (x, y-1), (x, y+1)):
            if point in cells and point not in seen:
                seen.add(point)
                queue.append(point)
    return seen


def geometry(rows):
    """Validate broad hole-free polyomino; return clockwise grid boundary."""
    require(rows and rows[0], 'Empty mask')
    width, height = len(rows[0]), len(rows)
    require(all(len(row) == width and set(row) <= {'#', '.'} for row in rows),
            'Malformed mask rows')
    cells = {(x, y) for y, row in enumerate(rows) for x, token in enumerate(row) if token == '#'}
    require(cells and reachable(cells) == cells, 'Disconnected mask')
    require(min(x for x, y in cells) == 0 and max(x for x, y in cells) == width-1
            and min(y for x, y in cells) == 0 and max(y for x, y in cells) == height-1,
            'Unused outer rows/columns')
    outside = {(x, y) for y in range(-1, height+1) for x in range(-1, width+1)} - cells
    require(reachable(outside) == outside, 'Hole in mask')
    # Every occupied cell must belong to a solid 2x2 block. This deliberately
    # excludes one-cell tips/arms, even though an Extractor needs only one cell.
    for x, y in cells:
        require(any({(a, b), (a+1, b), (a, b+1), (a+1, b+1)} <= cells
                    for a in (x-1, x) for b in (y-1, y)), 'Thin tip or neck')
    require(all(reachable(cells - {point}) == cells - {point} for point in cells),
            'Single-cell articulation/neck')
    edges = {}
    for x, y in sorted(cells):
        for neighbor, start, end in (
                ((x, y-1), (x, y), (x+1, y)),
                ((x+1, y), (x+1, y), (x+1, y+1)),
                ((x, y+1), (x+1, y+1), (x, y+1)),
                ((x-1, y), (x, y+1), (x, y))):
            if neighbor not in cells:
                require(start not in edges, 'Diagonal boundary contact')
                edges[start] = end
    start = min(edges, key=lambda p: (p[1], p[0]))
    contour, current = [], start
    while True:
        require(current in edges and current not in contour, 'Non-simple contour')
        contour.append(current)
        current = edges[current]
        if current == start:
            break
    require(len(contour) == len(edges), 'Multiple contours')
    polygon = []
    for i, b in enumerate(contour):
        a, c = contour[i-1], contour[(i+1) % len(contour)]
        if (b[0]-a[0])*(c[1]-b[1]) != (b[1]-a[1])*(c[0]-b[0]):
            polygon.append([b[0]*CELL, b[1]*CELL])
    return cells, polygon


def contains(point, polygon):
    x, y = point
    inside = False
    for a, b in zip(polygon, polygon[1:] + polygon[:1]):
        if (a[1] > y) != (b[1] > y) and x < (b[0]-a[0])*(y-a[1])/(b[1]-a[1])+a[0]:
            inside = not inside
    return inside


def compile_catalog():
    source = json.loads((ROOT/ASSET/'shapes.json').read_text(encoding='utf-8'))
    require(source['catalog_version'] == VERSION, 'Unsupported catalog version')
    variants, ids, silhouettes = [], set(), set()
    require(8 <= len(source['variants']) <= 12, 'Expected 8-12 variants')
    for item in source['variants']:
        identity = item['id']
        require(re.fullmatch(r'ferrite_v1_[a-z0-9_]+', identity) and identity not in ids,
                'Invalid/duplicate ID')
        ids.add(identity)
        require(item['size_class'] in RANGES and item['shape_family'] in FAMILIES,
                'Unknown size/family')
        mask_path = ASSET/'masks'/f'{identity}.txt'
        rows = (ROOT/mask_path).read_text(encoding='utf-8').splitlines()
        cells, polygon = geometry(rows)
        signature = tuple(rows)
        require(signature not in silhouettes, 'Duplicate silhouette')
        silhouettes.add(signature)
        width, height = len(rows[0]), len(rows)
        min_w, min_h, max_w, max_h = RANGES[item['size_class']]
        require(min_w <= width <= max_w and min_h <= height <= max_h, 'Size outside class')
        if item['shape_family'] == 'rectangle':
            require(len(cells) == width*height and len(polygon) == 4, 'Nonrectangular rectangle')
        else:
            require(len(cells) < width*height and len(polygon) >= 6, 'Missing shape variation')
        # Polygon truth must agree at cell centers, both locally and after
        # translating into a negative world quadrant; no truncating division.
        for ox, oy in ((0, 0), (-2048, -4096)):
            translated = [[x+ox, y+oy] for x, y in polygon]
            for y in range(-1, height+1):
                for x in range(-1, width+1):
                    require(contains((ox+(x+0.5)*CELL, oy+(y+0.5)*CELL), translated)
                            == ((x, y) in cells), 'Polygon/cell mismatch')
        variants.append({
            **item, 'catalog_version': VERSION, 'mask_path': mask_path.as_posix(),
            'width_cells': width, 'height_cells': height, 'occupied_cells': len(cells),
            'logical_polygon_world_units': polygon,
            'png_path': (ASSET/f'{identity}.png').as_posix(),
            'logical_origin_source_pixels': [PAD, PAD],
            'image_size_pixels': [width*SOURCE_CELL+2*PAD, height*SOURCE_CELL+2*PAD],
            'display_scale': 0.5,
        })
    require({v['shape_family'] for v in variants} == FAMILIES, 'Missing family')
    require({v['size_class'] for v in variants} == set(RANGES), 'Missing size class')
    return {'catalog_version': VERSION, 'terrain_cell_world_units': CELL,
            'source_pixels_per_cell': SOURCE_CELL,
            'future_selection_targets': source['future_selection_targets'], 'variants': variants}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='Compare derived JSON; write nothing')
    args = parser.parse_args()
    catalog = compile_catalog()
    encoded = (json.dumps(catalog, indent=2) + '\n').encode('utf-8')
    target = ROOT/ASSET/'catalog.json'
    if args.check:
        # Git's Windows text checkout may use CRLF. Canonical JSON content is
        # reproducible independently of that checkout setting; PNGs are byte-exact.
        require(target.read_text(encoding='utf-8').encode('utf-8') == encoded,
                'Stale derived catalog; rebuild')
    else:
        target.write_bytes(encoded)
    print(f"{'CHECK' if args.check else 'BUILD'} PASS: {len(catalog['variants'])} catalog geometries")


if __name__ == '__main__':
    main()
