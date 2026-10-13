#!/usr/bin/env python3
"""Metres on cobblestone / sett / easy gravel per route, for one or more harness result files.
usage: surface_share.py <results.json>..."""
import json, math, sys
from surfaces import surface_class, parse_tags


def seg_len(p):
    d = 0
    for (la1, lo1), (la2, lo2) in zip(p, p[1:]):
        dx = (lo2 - lo1) * 111320 * math.cos(math.radians(la1))
        dy = (la2 - la1) * 110540
        d += math.hypot(dx, dy)
    return d


runs = [{r['name']: r for r in json.load(open(f))} for f in sys.argv[1:]]
print(f"{'route':28}" + ''.join(f"{f.split('/')[-1][:26]:>28}" for f in sys.argv[1:]))
print(f"{'':28}" + ''.join(f"{'km  cob_m sett_m grv_m':>28}" for _ in sys.argv[1:]))
for name in runs[0]:
    cells = []
    for run in runs:
        r = run.get(name, {})
        if 'segs' not in r:
            cells.append(f"{'-':>28}")
            continue
        m = {'cobble': 0, 'sett': 0, 'easy_gravel': 0}
        for s in r['segs']:
            c = surface_class(parse_tags(s['t']))
            if c:
                m[c] += seg_len(s['p'])
        cells.append(f"{r['dist']/1000:6.2f} {m['cobble']:6.0f} {m['sett']:6.0f} {m['easy_gravel']:5.0f}".rjust(28))
    print(f"{name[:28]:28}" + ''.join(cells))
