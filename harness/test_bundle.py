"""The real bundle packs and validates, and names with umlauts survive."""
import json, pathlib, tempfile, unittest, zipfile
import check_osf, pack_osf

ROOT = pathlib.Path(__file__).resolve().parent.parent


class BundleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.tmp = tempfile.TemporaryDirectory()
        cls.osf = pack_osf.pack(ROOT, pathlib.Path(cls.tmp.name) / 'veloele.osf')

    @classmethod
    def tearDownClass(cls):
        cls.tmp.cleanup()

    def test_packed_bundle_is_valid(self):
        self.assertEqual(check_osf.check(self.osf, check_osf.load_poi_types(), ROOT), [])

    def test_packed_bundle_keeps_umlauts(self):
        with zipfile.ZipFile(self.osf) as z:
            items = json.loads(z.read('items.json').decode('utf-8'))['items']
            filters = json.loads(z.read('poi_ui_filters.json').decode('utf-8'))['items']
        self.assertEqual([i['appMode']['userProfileName'] for i in items if i['type'] == 'PROFILE'], ['Velöle'])
        self.assertIn('Übernachten', [f['name'] for f in filters])

    def test_profile_has_spec_settings(self):
        with zipfile.ZipFile(self.osf) as z:
            p = json.loads(z.read('profile_veloele.json'))
        for k, v in {'renderer': 'veloele', 'voice_provider': 'de-tts', 'route_calculation_method': 'STANDARD_ONLY',
                     'disable_offroute_recalc': 'false', 'prouting_avoid_ferries': 'true',
                     'prouting_height_obstacles': 'true', 'nrenderer_hideIcons': 'true',
                     'daynight_mode': 'DAY', 'route_line_coloring_type': 'altitude', 'enable_3d_maps': 'false', 'selected_poi_filters_for_map': '',
                     # Task 1 outcome: explicit values that keep today's routes (24 km/h max changed 3/16 routes)
                     'max_speed': '5.5555556', 'default_speed': '5.0', 'min_speed': '1.3888888'}.items():
            self.assertEqual(p.get(k), v, k)


    def test_profile_icon_is_orange(self):
        with zipfile.ZipFile(self.osf) as z:
            items = json.loads(z.read('items.json').decode('utf-8'))['items']
        mode = next(i['appMode'] for i in items if i['type'] == 'PROFILE')
        self.assertEqual(mode.get('customIconColor'), -30720)  # 0xFFFF8800 as a signed ARGB int

    def test_no_battery_widget(self):
        with zipfile.ZipFile(self.osf) as z:
            p = json.loads(z.read('profile_veloele.json'))
        self.assertNotIn('battery', p['right_widget_panel_order'].split(','))
        self.assertNotIn('battery', p['map_info_controls'].split(';'))

if __name__ == '__main__':
    unittest.main()
