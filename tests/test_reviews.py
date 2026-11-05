import re
import shutil
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import app as site

FIXTURES = Path(__file__).parent / 'fixtures'  # fixed sample data for tests


class ReviewsTests(unittest.TestCase):
    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        data = Path(self.directory.name)
        shutil.copy(FIXTURES / 'alerts.csv', data / 'alerts.csv')
        self.patcher = patch.object(site, 'DATA', data)
        self.patcher.start()
        self.addCleanup(self.patcher.stop)
        site.app.testing = True
        self.client = site.app.test_client()

    def submit(self, vessel, label, note='', prefix=''):
        self.client.get(prefix + '/alert/' + vessel)
        with self.client.session_transaction() as session:
            token = session['review_token']
        return self.client.post(prefix + '/alert/' + vessel,
                                data={'token': token, 'label': label, 'note': note})

    def awaiting(self):
        html = self.client.get('/watch?min_risk=0').get_data(as_text=True)
        return int(re.findall(r'class="counter-value">(\d+)', html)[3])

    def test_save_reload_lists_and_undo_in_both_languages(self):
        for prefix in ['', '/fr']:
            with self.subTest(prefix=prefix):
                self.assertEqual(self.awaiting(), 60)
                note = 'Checked, needs follow-up.\n<script>alert(1)</script>'
                response = self.submit('V014', 'confirmed', note, prefix)
                self.assertEqual(response.status_code, 303)
                self.assertIn(prefix + '/alert/V014', response.location)
                feedback = site.load_feedback()
                self.assertEqual(feedback.iloc[0]['note'], note)
                self.assertTrue(feedback.iloc[0]['time'].endswith('+00:00'))
                self.assertEqual(self.awaiting(), 59)
                for status, contains in [('pending', False), ('reviewed', True), ('all', True)]:
                    response = self.client.get(prefix + '/alerts?status=' + status)
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual((prefix + '/alert/V014').encode() in response.data, contains)
                other = site.app.test_client()
                html = other.get(prefix + '/alert/V014').get_data(as_text=True)
                self.assertIn('&lt;script&gt;', html)
                self.assertNotIn('<script>alert(1)</script>', html)
                self.assertEqual(self.submit('V014', 'undo', prefix=prefix).status_code, 303)
                self.assertEqual(self.awaiting(), 60)
                self.assertTrue(site.load_feedback().empty)

    def test_replace_does_not_duplicate_or_erase_other_decisions(self):
        self.submit('V014', 'confirmed')
        self.submit('V007', 'false_alarm')
        self.submit('V014', 'false_alarm', 'Updated')
        feedback = site.load_feedback().set_index('vessel_id')
        self.assertEqual(len(feedback), 2)
        self.assertEqual(feedback.loc['V014', 'label'], 'false_alarm')
        self.assertEqual(feedback.loc['V007', 'label'], 'false_alarm')
        self.submit('V014', 'undo')
        self.assertEqual(site.reviewed_ids(), {'V007'})

    def test_invalid_submissions_do_not_write(self):
        self.assertEqual(self.client.post('/alert/V014', data={'label': 'confirmed'}).status_code, 400)
        self.assertEqual(self.submit('V014', 'bad_label').status_code, 400)
        self.assertEqual(self.submit('V014', 'confirmed', 'x' * 2001).status_code, 400)
        self.assertEqual(self.client.post('/alert/UNKNOWN').status_code, 404)
        self.assertFalse((site.DATA / 'feedback.csv').exists())

    def test_alerts_navigation_and_empty_reviewed_view(self):
        for prefix in ['', '/fr']:
            response = self.client.get(prefix + '/alerts?status=reviewed')
            self.assertEqual(response.status_code, 200)
            self.assertNotIn(b'<tbody>', response.data)
            self.assertIn(('href="' + prefix + '/alerts"').encode(), response.data)
            self.assertEqual(self.client.get(prefix + '/alerts?status=unknown').status_code, 200)


if __name__ == '__main__':
    unittest.main()
