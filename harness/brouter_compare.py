"""Run harness/routes.txt through BRouter with several profiles and compare them.

usage: brouter_compare.py <brouter.jar> <segmentdir> <profiledir> <workdir> <profile[:k=v,...]>...
e.g.   brouter_compare.py brouter-all.jar segments prof /tmp/out trekking veloele veloele:surface_mode=2
(set ROUTES=<file> to use another routes file)
"""
import json, math, os, subprocess, sys, pathlib
from concurrent.futures import ThreadPoolExecutor

sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent))
from surfaces import surface_class, parse_tags

jar, segdir, profdir, work = sys.argv[1:5]
variants = sys.argv[5:]
work = pathlib.Path(work); work.mkdir(parents=True, exist_ok=True)
root = pathlib.Path(__file__).resolve().parent.parent
routes = []
for line in pathlib.Path(os.environ.get('ROUTES', root / 'harness/routes.txt')).read_text().splitlines():
    if line.strip() and not line.startswith('#'):
        name, a, b = line.split(';')
        (la1, lo1), (la2, lo2) = a.split(','), b.split(',')
        routes.append((name, f'{lo1},{la1}|{lo2},{la2}'))

def run(ri, v):
    prof, _, params = v.partition(':')
    q = f'lonlats={routes[ri][1]}&profile={prof}&format=geojson&alternativeidx=0'
    for kv in filter(None, params.split(',')):
        q += '&profile:' + kv
    out = work / f'{v.replace(":", "_").replace("=", "")}-{ri}'
    subprocess.run(['java', '-cp', jar, 'btools.server.BRouter', segdir, profdir, q, str(out)],
                   capture_output=True, timeout=600)
    f = pathlib.Path(str(out) + '0.geojson')
    return json.loads(f.read_text())['features'][0] if f.exists() else None

def dist(a, b):
    dx = (b[0] - a[0]) * 111320 * math.cos(math.radians(a[1])); dy = (b[1] - a[1]) * 110540
    return math.hypot(dx, dy), math.degrees(math.atan2(dx, dy))

def turns(coords, step=12):
    pts = [coords[0]]
    for c in coords[1:]:
        if dist(pts[-1], c)[0] >= step: pts.append(c)
    n = 0
    for a, b, c in zip(pts, pts[1:], pts[2:]):
        d = abs((dist(b, c)[1] - dist(a, b)[1] + 180) % 360 - 180)
        n += d > 60
    return n

def infra(tags):
    t = dict(x.split('=', 1) for x in tags.split() if '=' in x)
    hw = t.get('highway', '')
    if hw == 'cycleway' or t.get('bicycle') == 'designated' or t.get('cyclestreet') == 'yes' \
            or t.get('bicycle_road') == 'yes' or t.get('cycleway') in ('track', 'opposite_track') \
            or 'track' in (t.get('cycleway:both'), t.get('cycleway:left'), t.get('cycleway:right')):
        return 'bike'
    if hw in ('primary', 'secondary', 'tertiary', 'primary_link', 'secondary_link', 'tertiary_link', 'trunk') \
            and 'lane' not in (t.get('cycleway'), t.get('cycleway:both'), t.get('cycleway:left'), t.get('cycleway:right')):
        return 'main'
    if t.get('surface') in ('gravel', 'compacted', 'fine_gravel', 'unpaved', 'ground', 'dirt', 'earth', 'grass', 'sand', 'pebblestone') \
            or (hw == 'track' and t.get('tracktype', 'grade2') != 'grade1' and 'surface' not in t):
        return 'unpaved'
    return 'other'

jobs = [(ri, v) for ri in range(len(routes)) for v in variants]
with ThreadPoolExecutor(4) as ex:
    res = dict(zip(jobs, ex.map(lambda j: run(*j), jobs)))

W = 52
print(f'{"route":28}' + ''.join(f'{v[:W-2]:>{W}}' for v in variants))
print(f'{"":28}' + ''.join(f'{"km bike% rte% main% unp% turns asc cob% set% grv%":>{W}}' for v in variants))
for ri, (name, _) in enumerate(routes):
    row = f'{name[:28]:28}'
    for v in variants:
        f = res[(ri, v)]
        if not f: row += f'{"FAIL":>{W}}'; continue
        msgs = f['properties']['messages']
        cat = {}
        for m in msgs[1:]:
            k = infra(m[9]); cat[k] = cat.get(k, 0) + int(m[3])
            if 'route_bicycle_' in m[9]: cat['route'] = cat.get('route', 0) + int(m[3])
            sc = surface_class(parse_tags(m[9]))
            if sc: cat['s_' + sc] = cat.get('s_' + sc, 0) + int(m[3])
        tot = sum(v for k, v in cat.items() if k != 'route' and not k.startswith('s_')) or 1
        row += '{:>{w}}'.format('%5.1f %4.0f %4.0f %4.0f %4.0f %4d %4s %4.1f %4.1f %4.1f' % (
            int(f['properties']['track-length']) / 1000, 100 * cat.get('bike', 0) / tot,
            100 * cat.get('route', 0) / tot,
            100 * cat.get('main', 0) / tot, 100 * cat.get('unpaved', 0) / tot,
            turns(f['geometry']['coordinates']), f['properties']['filtered ascend'],
            100 * cat.get('s_cobble', 0) / tot, 100 * cat.get('s_sett', 0) / tot,
            100 * cat.get('s_easy_gravel', 0) / tot), w=W)
    print(row)
