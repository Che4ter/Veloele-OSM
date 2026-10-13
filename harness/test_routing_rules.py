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


if __name__ == '__main__':
    unittest.main()
