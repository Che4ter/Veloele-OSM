import json, pathlib, tempfile, unittest, zipfile
import check_osf

POI = {'drinking_water': {'man_made'}, 'toilets': {'service'}}
ROUTING = '<osmand_routing_config><routingProfile name="veloele"/></osmand_routing_config>'
STYLE = '<renderingStyle name="veloele" depends="default"/>'


def valid():
    """files dict (zip name -> content) and items list of a minimal valid bundle"""
    items = [
        {'type': 'FILE', 'file': '/routing/veloele.xml', 'subtype': 'routing_config'},
        {'type': 'FILE', 'file': '/rendering/veloele.render.xml', 'subtype': 'rendering_style'},
        {'type': 'POI_UI_FILTERS', 'file': 'poi_ui_filters.json'},
        {'type': 'QUICK_ACTIONS', 'file': 'quick_actions_1.json',
         'buttonState': {'id': 'quick_actions_1', 'enabled': True}},
        {'type': 'PROFILE', 'file': 'profile_veloele.json',
         'appMode': {'stringKey': 'veloele', 'parent': 'bicycle', 'userProfileName': 'Velöle',
                     'routingProfile': 'veloele.xml/veloele', 'routeService': 'OSMAND'}},
    ]
    files = {
        'routing/veloele.xml': ROUTING,
        'rendering/veloele.render.xml': STYLE,
        'poi_ui_filters.json': {'items': [{'name': 'Wasser', 'filterId': 'user_wasser',
                                           'acceptedTypes': json.dumps({'man_made': ['drinking_water']})}]},
        'quick_actions_1.json': {'items': [
            {'name': 'Wasser', 'actionType': 'poi.showhide', 'params': json.dumps({'filters': '["user_wasser"]'})},
            {'name': 'Toilette', 'actionType': 'poi.showhide', 'params': json.dumps({'filters': '["std_toilets"]'})}]},
        'profile_veloele.json': {'renderer': 'veloele', 'voice_provider': 'de-tts'},
    }
    return files, items


def write(tmp, files, items):
    p = pathlib.Path(tmp) / 'b.osf'
    with zipfile.ZipFile(p, 'w') as z:
        z.writestr('items.json', json.dumps({'version': 3, 'items': items}, ensure_ascii=False))
        for name, c in files.items():
            z.writestr(name, c if isinstance(c, str) else json.dumps(c, ensure_ascii=False))
    return p


class CheckOsfTest(unittest.TestCase):
    def run_check(self, files, items, sources=None):
        with tempfile.TemporaryDirectory() as tmp:
            return check_osf.check(write(tmp, files, items), POI, sources)

    def assertProblem(self, problems, fragment):
        self.assertTrue(any(fragment in p for p in problems), problems)

    def test_valid_bundle_passes(self):
        self.assertEqual(self.run_check(*valid()), [])

    def test_not_a_zip(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = pathlib.Path(tmp) / 'x.osf'
            p.write_text('hello')
            self.assertProblem(check_osf.check(p, POI), 'not a zip')

    def test_referenced_file_missing(self):
        files, items = valid()
        del files['poi_ui_filters.json']
        self.assertProblem(self.run_check(files, items), 'poi_ui_filters.json missing')

    def test_unreferenced_file(self):
        files, items = valid()
        files['general_settings.json'] = {}
        self.assertProblem(self.run_check(files, items), 'general_settings.json: in zip but not in items.json')

    def test_global_item_forbidden(self):
        files, items = valid()
        files['general_settings.json'] = {}
        items.append({'type': 'GLOBAL', 'file': 'general_settings.json'})
        self.assertProblem(self.run_check(files, items), 'GLOBAL')

    def test_bad_json(self):
        files, items = valid()
        files['profile_veloele.json'] = '{"renderer": '
        self.assertProblem(self.run_check(files, items), 'profile_veloele.json: does not parse')

    def test_bad_xml(self):
        files, items = valid()
        files['routing/veloele.xml'] = '<osmand_routing_config>'
        self.assertProblem(self.run_check(files, items), 'routing/veloele.xml: does not parse')

    def test_routing_profile_not_bundled(self):
        files, items = valid()
        items[-1]['appMode']['routingProfile'] = 'veloele.xml/bicycle_nl'
        self.assertProblem(self.run_check(files, items), 'veloele.xml/bicycle_nl')

    def test_renderer_not_bundled(self):
        files, items = valid()
        files['profile_veloele.json']['renderer'] = 'CycloRoute'
        self.assertProblem(self.run_check(files, items), 'renderer CycloRoute')

    def test_unknown_poi_type(self):
        files, items = valid()
        files['poi_ui_filters.json']['items'][0]['acceptedTypes'] = json.dumps({'man_made': ['water_tank']})
        self.assertProblem(self.run_check(files, items), 'water_tank')

    def test_poi_type_in_wrong_category(self):
        files, items = valid()
        files['poi_ui_filters.json']['items'][0]['acceptedTypes'] = json.dumps({'amenity': ['drinking_water']})
        self.assertProblem(self.run_check(files, items), 'drinking_water')

    def test_filter_id_must_be_ascii(self):
        files, items = valid()
        files['poi_ui_filters.json']['items'][0]['filterId'] = 'user_hiking_&_wasser'
        self.assertProblem(self.run_check(files, items), 'user_hiking_&_wasser')

    def test_quick_action_unknown_filter(self):
        files, items = valid()
        files['quick_actions_1.json']['items'][0]['params'] = json.dumps({'filters': '["user_ferien"]'})
        self.assertProblem(self.run_check(files, items), 'user_ferien')

    def test_forbidden_profile_key(self):
        files, items = valid()
        files['profile_veloele.json']['last_known_map_rotation'] = '115.8'
        self.assertProblem(self.run_check(files, items), 'last_known_map_rotation')

    def test_sources_mismatch_is_reported(self):
        files, items = valid()
        with tempfile.TemporaryDirectory() as src:
            (pathlib.Path(src) / 'profile').mkdir()
            (pathlib.Path(src) / 'profile/veloele.xml').write_text(ROUTING.replace('veloele"', 'veloele" x="1"'))
            (pathlib.Path(src) / 'profile/veloele.render.xml').write_text(STYLE)
            problems = self.run_check(files, items, sources=pathlib.Path(src))
        self.assertProblem(problems, 'routing/veloele.xml differs from profile/veloele.xml')
        self.assertFalse(any('render' in p for p in problems), problems)

    def test_text_file_is_not_parsed_as_xml(self):
        files, items = valid()
        files['color-palette/route_speed_default.txt'] = '# speed palette\n0,#ff0000\n'
        items.append({'type': 'FILE', 'file': '/color-palette/route_speed_default.txt', 'subtype': 'colors_palette'})
        problems = self.run_check(files, items)
        self.assertFalse(any('does not parse' in p for p in problems), problems)
        self.assertProblem(problems, 'unexpected file subtype colors_palette')

    @unittest.skipUnless(check_osf.JAR.exists(), 'OsmAnd MapCreator jars not present')
    def test_real_poi_types_load(self):
        types = check_osf.load_poi_types()
        self.assertIn('man_made', types['drinking_water'])
        self.assertIn('service', types['toilets'])


if __name__ == '__main__':
    unittest.main()
