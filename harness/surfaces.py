"""Surface classes for the touring-tuning reports (OsmAnd harness JSON and BRouter messages)."""


def parse_tags(s):
    return dict(x.split('=', 1) for x in s.split() if '=' in x)


def surface_class(tags):
    s = tags.get('surface', '')
    if s in ('cobblestone', 'unhewn_cobblestone'):
        return 'cobble'
    if s == 'sett':
        return 'sett'
    if s in ('compacted', 'fine_gravel'):
        return 'easy_gravel'
    if not s and tags.get('highway') == 'track' and tags.get('tracktype') in ('grade1', 'grade2'):
        return 'easy_gravel'
    return None
