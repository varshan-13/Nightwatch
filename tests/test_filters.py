import html
import re
import unittest
from urllib.parse import urlparse, parse_qs

import app as site


class FilterTests(unittest.TestCase):
    def setUp(self):
        site.app.testing = True
        self.client = site.app.test_client()
        self.alerts = site.load_alerts()

    def ids(self, path):
        response = self.client.get(path)
        self.assertEqual(response.status_code, 200)
        return re.findall(r'<tr data-vessel-id="([^"]+)"', response.get_data(as_text=True))

    def test_risk_bands_and_clear_in_both_languages(self):
        for prefix in ['', '/fr']:
            for low, high in [(0, 100), (70, 100), (40, 69), (0, 39)]:
                actual = self.ids(f'{prefix}/watch?min_risk={low}&max_risk={high}')
                expected = set(self.alerts[self.alerts.risk.between(low, high)].vessel_id)
                self.assertEqual(set(actual), expected)

    def test_combined_search_dark_and_risk_filters(self):
        expected = self.alerts[self.alerts.risk.between(40, 69) & self.alerts.dark]
        self.assertEqual(set(self.ids('/watch?min_risk=40&max_risk=69&dark=1')), set(expected.vessel_id))
        vessel = self.alerts.iloc[0]
        self.assertEqual(self.ids('/watch?min_risk=0&q=' + vessel.vessel_id), [vessel.vessel_id])
        self.assertEqual(self.ids('/watch?min_risk=0&q=NO_SUCH_VESSEL_98765'), [])

    def test_clamped_and_invalid_ranges(self):
        self.assertEqual(set(self.ids('/watch?min_risk=-5&max_risk=999')), set(self.alerts.vessel_id))
        self.assertEqual(self.ids('/watch?min_risk=70&max_risk=20'), self.ids('/watch?min_risk=70&max_risk=70'))
        self.assertEqual(self.ids('/watch?min_risk=invalid'), self.ids('/watch'))

    def test_detail_return_and_language_switch_keep_filters(self):
        self.client.get('/watch?min_risk=40&max_risk=69&dark=1&q=abc')
        vessel_id = self.alerts.iloc[0].vessel_id
        response = self.client.get('/alert/' + vessel_id)
        href = html.unescape(re.search(r'class="detail-back mono" href="([^"]+)"', response.get_data(as_text=True)).group(1))
        query = parse_qs(urlparse(href).query)
        self.assertEqual(query, {'min_risk': ['40'], 'max_risk': ['69'], 'dark': ['1'], 'q': ['abc']})
        response = self.client.get('/watch?min_risk=40&max_risk=69&dark=1&q=abc')
        target = html.unescape(re.search(r'href="([^"]+)" lang="fr"', response.get_data(as_text=True)).group(1))
        self.assertEqual(urlparse(target).path, '/fr/watch')
        self.assertEqual(parse_qs(urlparse(target).query), query)
