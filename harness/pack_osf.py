#!/usr/bin/env python3
"""Zip profile/osf/ + profile/veloele.xml + profile/veloele.render.xml into dist/veloele.osf, then check it.
No settings are generated here: edit profile/osf/*.json directly."""
import pathlib, sys, zipfile
import check_osf

ROOT = pathlib.Path(__file__).resolve().parent.parent


def pack(root=ROOT, out=None):
    out = out or root / 'dist/veloele.osf'
    out.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(out, 'w', zipfile.ZIP_DEFLATED) as z:
        for p in sorted((root / 'profile/osf').iterdir()):
            if p.is_file() and p.suffix == '.json':
                z.write(p, p.name)
        z.write(root / 'profile/veloele.xml', 'routing/veloele.xml')
        z.write(root / 'profile/veloele.render.xml', 'rendering/veloele.render.xml')
    return out


if __name__ == '__main__':
    out = pack()
    print('wrote', out.relative_to(ROOT))
    sys.exit(check_osf.main(['check_osf.py', str(out), '--sources', str(ROOT)]))
