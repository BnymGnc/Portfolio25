"""Decision artefacts must use current physical results, never new/fabricated savings."""
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.testclient import TestClient

import main
from decision_brief import number
from exports import guarded_export
from pilot_kayseri import create_pilot


class DecisionBriefTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        for key, value in [('DATA_FILE', Path(temporary.name) / 'campus.json'), ('AUTH_REQUIRED', False)]:
            context = patch.object(main, key, value)
            context.start()
            self.addCleanup(context.stop)
        self.client = TestClient(main.app)
        self.addCleanup(self.client.close)
        self.campus = create_pilot()[2]
        main.write_campus(self.campus)

    def calculate(self, mode='A'):
        value = self.client.post('/api/calculate', json={'revision': 1, 'mode': mode, 'time_limit_s': 2})
        self.assertEqual(value.status_code, 200, value.text)
        return value.json()

    def export(self, result):
        return self.client.get('/api/export/html', params={'scope': 'result', 'revision': 1,
                                                         'expected_calculation_id': result['calculation_id']})

    def test_report_matches_current_api_values_and_never_mutates_records(self):
        result = self.calculate()
        before = (main.DATA_FILE.read_bytes(), main.result_path().read_bytes())
        response = self.export(result)
        self.assertEqual(response.status_code, 200, response.text)
        for value in [result['calculation_id'], result['engine_version'], result['input_hash'],
                      number(result['investment_try'], 0), number(result['after']['total_energy_kwh_year']),
                      number(result['net_savings_try_year'], 0), self.campus.name]:
            self.assertIn(value, response.text)
        self.assertIn('saha', response.text.lower())
        self.assertIn('CSV', response.text)
        self.assertIn('Content-Security-Policy', response.text)
        self.assertIn('attachment;', response.headers['content-disposition'])
        self.assertEqual(response.headers['cache-control'], 'no-store, private')
        self.assertEqual(before, (main.DATA_FILE.read_bytes(), main.result_path().read_bytes()))

    def test_unguarded_and_stale_report_requests_are_rejected(self):
        result = self.calculate()
        self.assertEqual(self.client.get('/api/export/html').status_code, 422)
        self.assertEqual(self.client.get('/api/export/html', params={'scope': 'inputs'}).status_code, 422)
        self.assertEqual(self.client.get('/api/export/html', params={'scope': 'result'}).status_code, 422)
        self.calculate()
        self.assertEqual(self.export(result).status_code, 409)

    def test_same_revision_foreign_project_changed_hash_and_engine_are_rejected(self):
        self.calculate()
        for change in ({'project_id': 'project-abcdefabcdef'}, {'engine_version': 'old-engine'}, {'input_hash': 'changed'}):
            snapshot = main.response(main.read_campus())
            snapshot.calculation = snapshot.calculation.model_copy(update=change)
            with self.assertRaises(HTTPException) as error:
                guarded_export(snapshot, 'result', 1, snapshot.calculation.calculation_id)
            self.assertEqual(error.exception.status_code, 409)

    def test_user_text_is_escaped_without_executable_markup(self):
        self.campus.name = '<script>alert(1)</script>'
        self.campus.buildings[0].name = '<img src=x onerror=alert(1)>'
        self.campus.scenario.price_basis.source = '</p><script>alert(2)</script>'
        main.write_campus(self.campus)
        response = self.export(self.calculate())
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('<script', response.text)
        self.assertNotIn('<img', response.text)
        self.assertIn('&lt;script&gt;', response.text)
        self.assertIn('&lt;img', response.text)

    def test_infeasible_plan_has_no_invented_after_or_investment(self):
        self.campus.scenario.budget_try = 0
        self.campus.scenario.savings_target_pct = 100
        main.write_campus(self.campus)
        result = self.calculate('B')
        self.assertEqual(result['status'], 'infeasible')
        response = self.export(result)
        self.assertEqual(response.status_code, 200)
        self.assertIn('Çözüm bulunamadı', response.text)
        self.assertIn('sonraki durum veya tasarruf üretilmedi', response.text)
        self.assertNotIn('yıllık nihai enerji farkı', response.text.lower())

    def test_report_stays_private(self):
        with patch.object(main, 'AUTH_REQUIRED', True):
            self.assertEqual(self.client.get('/api/export/html', params={'scope': 'result'}).status_code, 401)


if __name__ == '__main__':
    unittest.main()
