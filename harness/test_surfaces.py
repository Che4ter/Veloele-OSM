import unittest
from surfaces import surface_class, parse_tags


class SurfaceClassTest(unittest.TestCase):
    def test_cobblestones(self):
        self.assertEqual(surface_class({'highway': 'residential', 'surface': 'cobblestone'}), 'cobble')
        self.assertEqual(surface_class({'highway': 'residential', 'surface': 'unhewn_cobblestone'}), 'cobble')

    def test_sett(self):
        self.assertEqual(surface_class({'highway': 'residential', 'surface': 'sett'}), 'sett')

    def test_paving_stones_are_not_rough(self):
        self.assertIsNone(surface_class({'highway': 'cycleway', 'surface': 'paving_stones'}))

    def test_easy_gravel(self):
        self.assertEqual(surface_class({'highway': 'track', 'surface': 'compacted'}), 'easy_gravel')
        self.assertEqual(surface_class({'highway': 'path', 'surface': 'fine_gravel'}), 'easy_gravel')
        self.assertEqual(surface_class({'highway': 'track', 'tracktype': 'grade2'}), 'easy_gravel')

    def test_tracktype_does_not_override_surface(self):
        self.assertIsNone(surface_class({'highway': 'track', 'tracktype': 'grade2', 'surface': 'asphalt'}))
        self.assertIsNone(surface_class({'highway': 'track', 'tracktype': 'grade2', 'surface': 'gravel'}))

    def test_parse_tags(self):
        self.assertEqual(parse_tags('highway=track surface=fine_gravel junk'),
                         {'highway': 'track', 'surface': 'fine_gravel'})


if __name__ == '__main__':
    unittest.main()
