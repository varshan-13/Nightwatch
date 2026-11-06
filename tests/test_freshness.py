import tempfile
import unittest
from datetime import date
from pathlib import Path
from unittest.mock import patch

import app as site


class FreshnessTests(unittest.TestCase):
    def test_record_dates_not_file_age(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            (data / 'alerts.csv').write_text('last_seen\n2025-06-20 12:00\n2025-06-18 09:00\ninvalid\n')
            (data / 'events.csv').write_text('time\n2024-06-01 10:00\n2025-06-19 09:00\n')
            with patch.object(site, 'DATA', data):
                self.assertEqual(site.data_freshness(), {'latest': date(2025, 6, 20), 'start': date(2024, 6, 1), 'end': date(2025, 6, 20)})

    def test_missing_and_empty_records(self):
        with tempfile.TemporaryDirectory() as folder:
            data = Path(folder)
            with patch.object(site, 'DATA', data):
                self.assertEqual(site.data_freshness(), {'latest': None, 'start': None, 'end': None})
                (data / 'alerts.csv').write_text('last_seen\ninvalid\n')
                (data / 'events.csv').write_text('time\n')
                self.assertIsNone(site.data_freshness()['latest'])

    def test_bilingual_pages_and_filters_keep_dataset_dates(self):
        site.app.testing = True
        with site.app.test_client() as client:
            latest = site.data_freshness()['latest'].isoformat()
            for prefix in ['', '/fr']:
                for path in ['/watch', '/watch?q=NO_SUCH_VESSEL_987', '/alerts', '/validation']:
                    response = client.get(prefix + path)
                    self.assertEqual(response.status_code, 200)
                    self.assertIn(('datetime="' + latest + '"').encode(), response.data)
                    self.assertNotIn(b'Last 12 months', response.data)
