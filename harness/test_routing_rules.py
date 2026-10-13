"""Rule placement in the routing profiles that the harness route sets do not pin."""
import pathlib, re, unittest
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parent.parent


def _guarded_by_track(node, inside_track=False, inside_param=False):
    """Yield (select, inside_track) for every grade1/grade2 speed select outside a param block."""
    for child in node:
        track = inside_track or (child.tag == 'if' and child.get('t') == 'highway' and child.get('v') == 'track')
        param = inside_param or child.get('param') is not None
        if child.tag == 'select' and child.get('t') == 'tracktype' and child.get('v') in ('grade1', 'grade2') and not param:
            yield child, track
        yield from _guarded_by_track(child, track, param)


def _osmand_priority():
    return ET.parse(ROOT / 'profile/veloele.xml').find('.//way[@attribute="priority"]')


def _highway_value(prio, highway, tag, value):
    """Value of the select for tag=value inside a highway=<highway> block."""
    for block in prio.iter('if'):
        if block.get('t') == 'highway' and block.get('v') == highway:
            sel = block.find(f'.//select[@t="{tag}"][@v="{value}"]')
            if sel is not None:
                return sel.get('value')
    return None


def _highway_value_nested(prio, highway, tag):
    """Value of the bare select inside an <if t=tag> within a highway=<highway> block."""
    for block in prio.iter('if'):
        if block.get('t') == 'highway' and block.get('v') == highway:
            for cond in block.iter('if'):
                if cond.get('t') == tag and cond.get('v') is None:
                    sel = next((s for s in cond.iter('select') if s.get('t') is None), None)
                    if sel is not None:
                        return sel.get('value')
    return None


class GoodTrackSpeedTest(unittest.TestCase):
    """grade1/2 = 15 km/h is for tracks; an asphalt road that also carries tracktype keeps 18."""

    def test_osmand_grade_speed_only_on_tracks(self):
        speed = ET.parse(ROOT / 'profile/veloele.xml').find('.//way[@attribute="speed"]')
        found = list(_guarded_by_track(speed))
        self.assertEqual(len(found), 2)
        for sel, track in found:
            self.assertTrue(track, sel.get('v'))

    def test_brouter_grade_speed_only_on_tracks(self):
        brf = (ROOT / 'profile/veloele.brf').read_text(encoding='utf-8')
        lines = [l for l in brf.splitlines() if re.search(r'tracktype=grade1\|grade2\s+\)?\s*then 15\b', l)]
        self.assertEqual(len(lines), 1)
        self.assertIn('highway=track', lines[0])


class SidewalkBicycleTest(unittest.TestCase):
    """A road whose sidewalk allows bicycles is ridden on that sidewalk: minor-road
    priority and no traffic penalty. BRouter only; OsmAnd drops the tag."""

    def test_brouter_sidewalk_bicycle(self):
        brf = (ROOT / 'profile/veloele.brf').read_text(encoding='utf-8')
        self.assertRegex(brf, r'assign sidewalk_bike = or sidewalk:bicycle=yes\|designated\s+'
                              r'or sidewalk:left:bicycle=yes\|designated\s+sidewalk:right:bicycle=yes\|designated')
        self.assertIn('assign priority = if sidewalk_bike then max priority 0.75 else priority', brf)
        facility = re.search(r'assign has_bike_facility = (.*?)\n\n', brf, re.S).group(1)
        self.assertIn('sidewalk_bike', facility)



class SharedLaneTest(unittest.TestCase):
    """Sharrows and bus lanes open to bikes count on any side, not only as plain cycleway=."""

    def test_brouter_shared_lane_any_side(self):
        brf = (ROOT / 'profile/veloele.brf').read_text(encoding='utf-8')
        for value in ('shared_lane', 'share_busway'):
            block = brf.split(f'assign has_{value} =', 1)[1].split('\nassign ', 1)[0]
            for key in ('cycleway', 'cycleway:both', 'cycleway:left', 'cycleway:right'):
                self.assertIn(f' {key}={value}', block)
        self.assertNotIn('cycleway=shared_lane then', brf)
        self.assertNotIn('cycleway=shared_lane|share_busway then', brf)

    def test_osmand_shared_lane_both(self):
        # one-sided values reach the OsmAnd router as plain cycleway=, cycleway:both= stays
        prio = _osmand_priority()
        self.assertEqual(_highway_value(prio, 'unclassified', 'cycleway:both', 'shared_lane'), '0.8')
        for value in ('shared_lane', 'share_busway'):
            self.assertEqual(_highway_value(prio, 'tertiary', 'cycleway:both', value), '0.6')


class OneSidedLaneTest(unittest.TestCase):
    """A lane on one side only gets half the gain of lanes on both sides."""
    HALF = {'residential': '0.81', 'unclassified': '0.775', 'tertiary': '0.575', 'tertiary_link': '0.575',
            'secondary': '0.45', 'secondary_link': '0.45', 'primary': '0.35', 'primary_link': '0.35'}

    def test_brouter_one_lane(self):
        brf = (ROOT / 'profile/veloele.brf').read_text(encoding='utf-8')
        self.assertIn('assign has_lane = or cycleway=lane or cycleway:both=lane '
                      'and cycleway:left=lane cycleway:right=lane', brf)
        self.assertIn('assign one_lane = and not has_lane or cycleway:left=lane cycleway:right=lane', brf)
        for value in set(self.HALF.values()):
            self.assertRegex(brf, rf'one_lane then {re.escape(value)}\b')

    def test_osmand_one_lane(self):
        # OsmAnd merges cycleway:left/right=lane into cycleway=lane; the side shows in
        # cycleway:<other>=no or in lane details on one side only
        prio = _osmand_priority()
        found = {}
        for block in prio.iter('if'):
            if block.get('t') != 'cycleway' or block.get('v') != 'lane':
                continue
            for sel in block.iter('select'):
                found.setdefault(sel.get('v') if sel.get('t') == 'highway' else None, set()).add(sel.get('value'))
        for highway in ('tertiary', 'tertiary_link', 'secondary', 'secondary_link', 'primary', 'primary_link'):
            self.assertEqual(found.get(highway), {self.HALF[highway]}, highway)
        for highway in ('residential', 'unclassified'):
            self.assertEqual(_highway_value(prio, highway, 'cycleway:left', 'no'), self.HALF[highway])
            self.assertEqual(_highway_value_nested(prio, highway, 'cycleway:right:lane'), self.HALF[highway])


if __name__ == '__main__':
    unittest.main()
