#!/usr/bin/env python3
"""Count turns (>60 deg direction change where the route switches way) per route.
usage: turns.py <results.json>..."""
import json, math, sys

def bearing(a, b):
    y = (b[1] - a[1]) * math.cos(math.radians(a[0]))
    return math.degrees(math.atan2(y, b[0] - a[0]))

def turns(segs):
    n = 0
    for p, q in zip(segs, segs[1:]):
        if p['id'] == q['id'] or len(p['p']) < 2 or len(q['p']) < 2:
            continue
        d = abs((bearing(q['p'][0], q['p'][1]) - bearing(p['p'][-2], p['p'][-1]) + 180) % 360 - 180)
        n += d > 60
    return n

runs = [{r['name']: r for r in json.load(open(f))} for f in sys.argv[1:]]
print(f"{'route':28}" + ''.join(f"{f.split('/')[-1][:22]:>24}" for f in sys.argv[1:]))
for name in runs[0]:
    cells = []
    for run in runs:
        r = run.get(name, {})
        if 'segs' not in r:
            cells.append(f"{'-':>24}")
            continue
        cyc = 100 * (r['cats']['cycleway'] + r['cats']['shared_path']) / r['dist']
        cells.append(f"{turns(r['segs']):3d}t {r['dist']/1000:6.2f}km {cyc:3.0f}%cyc".rjust(24))
    print(f"{name:28}" + ''.join(cells))
