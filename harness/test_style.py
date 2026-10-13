"""The trimmed Velöle map style keeps exactly the spec's POI layer."""
import pathlib, unittest
import xml.etree.ElementTree as ET

STYLE = pathlib.Path(__file__).resolve().parent.parent / 'profile/veloele.render.xml'

KEEP = {
    ('amenity', 'toilets'), ('amenity', 'drinking_water'), ('natural', 'spring'), ('amenity', 'fountain'),
    ('shop', 'bicycle'), ('amenity', 'bicycle_repair_station'), ('amenity', 'compressed_air'),
    ('amenity', 'bicycle_rental'), ('barrier', 'cycle_barrier'),
    ('man_made', 'water_well'), ('man_made', 'water_tap'), ('amenity', 'shower'),
    ('landuse', 'cemetery'), ('amenity', 'grave_yard'), ('amenity', 'atm'),
    ('tourism', 'camp_site'), ('tourism', 'camp_pitch'), ('tourism', 'caravan_site'), ('amenity', 'shelter'),
    ('tourism', 'alpine_hut'), ('tourism', 'wilderness_hut'), ('tourism', 'cabin'),
    ('tourism', 'picnic_site'), ('leisure', 'picnic_table'),
    ('shop', 'bakery'), ('shop', 'butcher'), ('shop', 'cheese'), ('shop', 'supermarket'),
    ('shop', 'convenience'), ('shop', 'greengrocer'), ('shop', 'farm'), ('amenity', 'marketplace'),
    ('amenity', 'cafe'), ('amenity', 'restaurant'), ('amenity', 'biergarten'), ('amenity', 'pub'),
    ('amenity', 'ice_cream'), ('amenity', 'fast_food'),
}
REMOVED = {
    ('emergency', 'phone'), ('emergency', 'defibrillator'), ('amenity', 'police'), ('amenity', 'veterinary'),
    ('amenity', 'doctors'), ('amenity', 'clinic'), ('amenity', 'dentist'), ('emergency', 'ambulance_station'),
    ('highway', 'emergency_access_point'), ('amenity', 'social_facility'), ('emergency', 'rescue_box'),
    ('emergency', 'mountain_rescue'), ('emergency', 'lifeguard_base'), ('amenity', 'avalanche_transceiver'),
    ('amenity', 'health_post'), ('emergency', 'siren'), ('amenity', 'pharmacy'), ('shop', 'medical_supply'),
    ('tourism', 'hotel'), ('tourism', 'motel'), ('tourism', 'guest_house'), ('tourism', 'hostel'),
    ('tourism', 'apartment'), ('tourism', 'chalet'),
    ('amenity', 'payment_terminal'), ('amenity', 'payment_centre'), ('amenity', 'money_transfer'),
    ('shop', 'money_lender'), ('amenity', 'bank'), ('amenity', 'bureau_de_change'),
    ('amenity', 'mobile_money_agent'), ('amenity', 'ticket_validator'),
    ('shop', 'outdoor'), ('shop', 'sports'), ('shop', 'health_food'), ('shop', 'fishing'), ('shop', 'seafood'),
    ('shop', 'cannabis'), ('shop', 'tobacco'), ('shop', 'chocolate'),
    ('amenity', 'food_court'), ('amenity', 'bar'), ('amenity', 'hookah_lounge'),
    ('amenity', 'place_of_worship'), ('highway', 'trailhead'), ('tourism', 'information'),
}


@unittest.skipUnless(STYLE.exists(), 'private style profile/veloele.render.xml not present')
class StyleTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.root = ET.parse(STYLE).getroot()
        point = cls.root.find('point')
        cls.pairs = {(e.get('tag'), e.get('value')) for e in point.iter() if e.get('tag')}

    def test_identity(self):
        self.assertEqual(self.root.get('name'), 'veloele')
        self.assertEqual(self.root.get('depends'), 'default')

    def test_kept_pois(self):
        self.assertEqual(KEEP - self.pairs, set())

    def test_removed_pois(self):
        self.assertEqual(REMOVED & self.pairs, set())

    def test_bicycle_parking_is_suppressed(self):
        # user: no blue dots. Having no rule is not enough: the inherited default style
        # then draws them, so a top-level point rule must match them and draw nothing.
        point = self.root.find('point')
        for tag in ('amenity', 'osmand_amenity'):
            rules = [e for e in point if e.get('tag') == tag and e.get('value') == 'bicycle_parking']
            self.assertEqual(len(rules), 1, tag)
            for e in rules[0].iter():
                self.assertFalse(e.get('icon') or e.get('shield'), tag)
        self.assertEqual(len([e for e in point.iter() if e.get('value') == 'bicycle_parking']), 2)

    def test_no_healthcare_rules(self):
        self.assertEqual({p for p in self.pairs if p[0] == 'healthcare'}, set())

    def test_hide_icons_property_still_exists(self):
        attrs = {p.get('attr') for p in self.root.iter('renderingProperty')}
        self.assertLessEqual({'hideIcons', 'POIcyclotouring', 'showCycleRoutes'}, attrs)


if __name__ == '__main__':
    unittest.main()
