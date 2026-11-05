import csv
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as site
from pipeline.validate import build_validation, match_vessel, write_validation


class ValidationTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.data = Path(self.temporary.name)
        self.alerts = [{'vessel_id': f'V{i:02}', 'name': f'Vessel {i}',
                        'mmsi': str(123456780 + i), 'risk': 99 - i} for i in range(30)]
        self.write('alerts.csv', self.alerts)
        self.write('raw/profiles.csv', [{'vessel_id': 'V00', 'imo': '7826233'}])
        self.write('iotc_iuu.csv', [
            {'iotc_id': 'A', 'name': 'Old name', 'imo': '7826233', 'mmsi': ''},
            {'iotc_id': 'B', 'name': 'Another name', 'imo': '', 'mmsi': '123456781'},
            {'iotc_id': 'C', 'name': 'Vessel-2', 'imo': '', 'mmsi': ''},
        ])

    def write(self, name, rows):
        path = self.data / name
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('w', newline='') as stream:
            writer = csv.DictWriter(stream, fieldnames=list(rows[0]))
            writer.writeheader()
            writer.writerows(rows)

    def test_priority_and_top20_counts(self):
        result = build_validation(self.data)
        self.assertEqual(result['top20_hits'], 3)
        self.assertEqual([r['match_method'] for r in result['top20'][:3]], ['imo', 'mmsi', 'name'])
        self.assertEqual(len(result['top20']), 20)
        self.assertEqual(result['imo_vessels'], 1)
        self.assertEqual(result['top20'][0]['iotc_id'], 'A')

    def test_baseline_repeatable_even_if_input_order_changes(self):
        first = build_validation(self.data)
        self.write('alerts.csv', list(reversed(self.alerts)))
        second = build_validation(self.data)
        self.assertEqual(first['baseline_ids'], second['baseline_ids'])
        self.assertEqual(first['random_hits'], second['random_hits'])
        self.assertEqual(len(set(first['baseline_ids'])), 20)

    def test_latest_feedback_and_current_dataset_only(self):
        self.write('feedback.csv', [
            {'vessel_id': 'V00', 'label': 'confirmed', 'note': '', 'time': 'a'},
            {'vessel_id': 'V00', 'label': 'false_alarm', 'note': '', 'time': 'b'},
            {'vessel_id': 'V01', 'label': 'confirmed', 'note': '', 'time': 'c'},
            {'vessel_id': 'NOT_CURRENT', 'label': 'false_alarm', 'note': '', 'time': 'd'},
        ])
        result = build_validation(self.data)
        self.assertEqual(result['reviewed_count'], 2)
        self.assertEqual(result['false_alarm_rate'], 0.5)
        self.assertEqual(result['top20'][0]['decision'], 'false_alarm')

    def test_missing_list_feedback_and_profiles_are_not_zero_results(self):
        (self.data / 'iotc_iuu.csv').unlink()
        (self.data / 'raw/profiles.csv').unlink()
        result = build_validation(self.data)
        self.assertIsNone(result['top20_hits'])
        self.assertIsNone(result['random_hits'])
        self.assertIsNone(result['false_alarm_rate'])
        self.assertIsNone(result['top20'][0]['on_iotc'])
        self.assertFalse(result['imo_profiles_available'])

    def test_small_dataset_uses_actual_denominator(self):
        self.write('alerts.csv', self.alerts[:2])
        result = build_validation(self.data)
        self.assertEqual(result['sample_size'], 2)
        self.assertEqual(result['top20_hits'], 2)
        self.assertEqual(result['random_hits'], 2)

    def test_no_blank_ambiguous_or_conflicting_name_matches(self):
        entries = [{'iotc_id': 'a', 'name': 'SAME', 'imo': '7826233'},
                   {'iotc_id': 'b', 'name': 'SAME', 'imo': '7322897'}]
        self.assertEqual(match_vessel({'name': 'Same'}, '', entries)['match_method'], 'ambiguous')
        self.assertEqual(match_vessel({'name': 'Same'}, '9042001', entries[:1])['match_method'], 'conflict')
        self.assertFalse(match_vessel({'name': 'Unknown', 'mmsi': ''}, '', [{'name': 'Unknown'}])['on_iotc'])
        self.assertTrue(match_vessel({'name': 'Océan-Lion'}, '', [{'iotc_id': 'a', 'name': 'XING HAI FENG', 'aliases': 'OCEAN LION'}])['on_iotc'])

    def test_pages_and_snapshot_refresh_after_feedback_changes(self):
        site.app.testing = True
        with patch.object(site, 'DATA', self.data):
            client = site.app.test_client()
            for prefix in ['', '/fr']:
                response = client.get(prefix + '/validation')
                self.assertEqual(response.status_code, 200)
                self.assertNotIn(b'[X]', response.data)
                self.assertIn(b'3 / 20', response.data)
            original = json.loads((self.data / 'validation.json').read_text())
            self.assertIsNone(original['false_alarm_rate'])
            self.write('feedback.csv', [{'vessel_id': 'V00', 'label': 'false_alarm', 'note': '', 'time': '2026-11-05'}])
            response = client.get('/validation')
            self.assertIn(b'100.0%', response.data)
            updated = json.loads((self.data / 'validation.json').read_text())
            self.assertEqual(updated['false_alarm_rate'], 1)
            self.assertEqual(updated['top20'][0]['decision'], 'false_alarm')

    def test_snapshot_valid_json_and_zero_hit_distinct_from_missing(self):
        self.write('iotc_iuu.csv', [{'name': 'No matching vessel', 'imo': '', 'mmsi': ''}])
        result = write_validation(self.data)
        self.assertEqual(result['top20_hits'], 0)
        self.assertEqual(json.loads((self.data / 'validation.json').read_text())['top20_hits'], 0)
