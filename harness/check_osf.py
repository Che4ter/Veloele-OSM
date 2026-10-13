#!/usr/bin/env python3
"""Validate a Velöle .osf bundle (zip) before it goes onto a phone.

usage: check_osf.py <bundle.osf> [--sources <project root>]
Prints one line per problem and exits 1, or prints "ok".
With --sources, bundled routing/rendering files must equal profile/<name>.
"""
import json, pathlib, re, sys, zipfile
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent
JAR = ROOT / 'mapcreator/lib/OsmAnd-java-master-snapshot.jar'
# CI has no mapcreator jar and downloads poi_types.xml from OsmAnd-resources instead
POI_XML = ROOT / 'mapcreator/poi_types.xml'
FORBIDDEN = re.compile(r'^(last_known_|selected_gpx|osm_user|user_name|enabled_plugins|backup_|live_monitoring_url|drawer_)')
FILTER_ID = re.compile(r'^user_[a-z0-9_]+$')


def load_poi_types(jar=JAR, xml=POI_XML):
    """poi type name -> set of category names, from OsmAnd's poi_types.xml inside the jar (or next to it)"""
    if pathlib.Path(jar).exists():
        with zipfile.ZipFile(jar) as z:
            root = ET.fromstring(z.read('net/osmand/osm/poi_types.xml'))
    else:
        root = ET.parse(xml).getroot()
    types = {}
    for cat in root.iter('poi_category'):
        for t in cat.iter('poi_type'):
            types.setdefault(t.get('name'), set()).add(cat.get('name'))
    return types


def quick_action_filters(action):
    f = json.loads(action.get('params', '{}')).get('filters', '')
    return json.loads(f) if f.startswith('[') else [x for x in f.split(',') if x]


def check(osf, poi_types, sources=None):
    try:
        z = zipfile.ZipFile(osf)
    except (zipfile.BadZipFile, OSError) as e:
        return [f'not a zip: {e}']
    errors = []
    with z:
        names = set(z.namelist())
        try:
            items = json.loads(z.read('items.json'))['items']
        except (KeyError, ValueError) as e:
            return [f'items.json missing or broken: {e}']
        referenced, data = {'items.json'}, {}
        for it in items:
            f = it.get('file', '').lstrip('/')
            if it['type'] == 'GLOBAL':
                errors.append(f'GLOBAL item ({f}) must not be bundled')
            referenced.add(f)
            if f not in names:
                errors.append(f'{it["type"]}: {f} missing')
                continue
            raw = z.read(f)
            try:
                data[f] = (json.loads(raw) if f.endswith('.json') else
                           ET.fromstring(raw) if f.endswith('.xml') else raw)
            except (ValueError, ET.ParseError) as e:
                errors.append(f'{f}: does not parse: {e}')
            if sources and it['type'] == 'FILE':
                src = pathlib.Path(sources) / 'profile' / pathlib.Path(f).name
                if not src.exists() or src.read_bytes() != raw:
                    errors.append(f'{f} differs from profile/{src.name}')
        for f in sorted(names - referenced):
            errors.append(f'{f}: in zip but not in items.json')

        routing, styles, filters = {}, set(), set()
        for it in items:
            f = it.get('file', '').lstrip('/')
            d = data.get(f)
            if d is None:
                continue
            if it['type'] == 'FILE' and it.get('subtype') == 'routing_config':
                routing[pathlib.Path(f).name] = {p.get('name') for p in d.iter('routingProfile')}
            elif it['type'] == 'FILE' and it.get('subtype') == 'rendering_style':
                styles.add(d.get('name'))
            elif it['type'] == 'FILE':
                errors.append(f'{f}: unexpected file subtype {it.get("subtype")}')
            elif it['type'] == 'POI_UI_FILTERS':
                for flt in d['items']:
                    fid = flt.get('filterId', '')
                    if not FILTER_ID.match(fid):
                        errors.append(f'filter id {fid!r} is not user_[a-z0-9_]+')
                    filters.add(fid)
                    for cat, types in json.loads(flt['acceptedTypes']).items():
                        for t in types:
                            if cat not in poi_types.get(t, set()):
                                errors.append(f'filter {fid}: {cat}/{t} not in poi_types.xml')
        for it in items:
            d = data.get(it.get('file', '').lstrip('/'))
            if d is None:
                continue
            if it['type'] == 'QUICK_ACTIONS':
                for a in d['items']:
                    for fid in quick_action_filters(a):
                        if not fid.startswith('std_') and fid not in filters:
                            errors.append(f'quick action {a.get("name")}: unknown filter {fid}')
            elif it['type'] == 'PROFILE':
                rp = it['appMode'].get('routingProfile', '')
                file, _, prof = rp.partition('/')
                if prof not in routing.get(file, set()):
                    errors.append(f'profile routingProfile {rp} is not in a bundled routing_config')
                if d.get('renderer') not in styles:
                    errors.append(f'profile renderer {d.get("renderer")} is not a bundled style')
                for k in d:
                    if FORBIDDEN.match(k):
                        errors.append(f'profile key {k} is personal/forbidden')
    return errors


def main(argv):
    osf = argv[1]
    sources = pathlib.Path(argv[argv.index('--sources') + 1]) if '--sources' in argv else None
    errors = check(osf, load_poi_types(), sources)
    print('\n'.join(errors) if errors else 'ok')
    return 1 if errors else 0


if __name__ == '__main__':
    sys.exit(main(sys.argv))
