import json
import re
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pandas as pd
import app as site

# The tests use a fixed copy of the sample data, so they don't depend on
# whatever real data the pipeline last wrote to data/.
FIXTURES = Path(__file__).parent / 'fixtures'


class VesselDetailsTests(unittest.TestCase):
    def setUp(self):
        self.patcher = patch.object(site, 'DATA', FIXTURES)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        site.app.testing = True
        self.client = site.app.test_client()

    def config(self, response):
        html = response.get_data(as_text=True)
        return json.loads(re.search(
            r'<script id="vessel-map-config" type="application/json">(.*?)</script>',
            html, re.S).group(1))

    def test_all_vessels_in_both_languages(self):
        for prefix in ['', '/fr']:
            for vessel in site.load_alerts().to_dict('records'):
                with self.subTest(prefix=prefix, vessel=vessel['vessel_id']):
                    response = self.client.get(prefix + '/alert/' + vessel['vessel_id'])
                    self.assertEqual(response.status_code, 200)
                    config = self.config(response)
                    self.assertEqual(config['lat'], vessel['lat'])
                    self.assertEqual(config['lon'], vessel['lon'])
                    times = [e['time'] for e in config['events']]
                    self.assertEqual(times, sorted(times, reverse=True))
                    self.assertTrue(all(e['vessel_id'] == vessel['vessel_id'] for e in config['events']))

    def test_unknown_vessel_is_helpful_404(self):
        for prefix in ['', '/fr']:
            response = self.client.get(prefix + '/alert/DOES_NOT_EXIST')
            self.assertEqual(response.status_code, 404)
            self.assertIn((prefix + '/watch').encode(), response.data)
            self.assertNotIn(b'id="vessel-map"', response.data)

    def test_dark_contact_has_no_nan_identifier(self):
        response = self.client.get('/alert/V007')
        self.assertIn(b'Unidentified radar contact', response.data)
        self.assertIn(b'No AIS match', response.data)
        self.assertNotIn(b'>nan<', response.data)

    def test_empty_and_missing_events(self):
        with tempfile.TemporaryDirectory() as directory:
            data = Path(directory)
            pd.read_csv(FIXTURES / 'alerts.csv').to_csv(data / 'alerts.csv', index=False)
            with patch.object(site, 'DATA', data):
                for create_file in [False, True]:
                    if create_file:
                        (data / 'events.csv').write_text('vessel_id,event,time,lat,lon\n')
                    response = self.client.get('/alert/V014')
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(self.config(response)['events'], [])
                    self.assertIn(b'No activity events', response.data)


if __name__ == '__main__':
    unittest.main()
