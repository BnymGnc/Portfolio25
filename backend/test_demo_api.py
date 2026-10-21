import tempfile
import unittest
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

import main
from models import CalculationRequest
from engine import calculate_package
from profiles import generate_profiles


class DemoReadApiTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.original_path = main.DATA_FILE
        main.DATA_FILE = Path(self.temp.name) / 'campus.json'
        self.client = TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.DATA_FILE = self.original_path
        self.temp.cleanup()

    def test_package_endpoint_reuses_engine_and_does_not_change_revision(self):
        before = self.client.get('/api/campus').json()
        answer = self.client.get('/api/buildings/B01/packages').json()
        campus = main.read_campus()
        b = campus.buildings[0]
        profile = generate_profiles(b, campus.profile_settings)
        self.assertEqual(len(answer['packages']), 4)
        for p in answer['packages']:
            self.assertEqual(p, calculate_package(b, profile, campus.scenario, p['package']).report.model_dump())
        self.assertEqual(answer['input_revision'], before['campus']['revision'])
        self.assertEqual(self.client.get('/api/buildings/B99/packages').status_code, 404)

    def test_hourly_campus_matches_actual_annual_result_and_aligned_peak(self):
        current = self.client.get('/api/campus').json()
        self.assertIsNone(self.client.get('/api/campus/profiles').json()['after_kw'])
        r = self.client.post('/api/calculate', json={'revision':current['campus']['revision']}).json()
        p = self.client.get('/api/campus/profiles').json()
        self.assertEqual(len(p['timestamps']), 8760)
        self.assertAlmostEqual(sum(p['before_kw']), r['baseline']['electricity_kwh_year'], places=5)
        self.assertAlmostEqual(sum(p['after_kw']), r['after']['electricity_kwh_year'], places=5)
        self.assertAlmostEqual(max(p['after_kw']), r['after']['electric_peak_kw'])
        self.assertEqual(p['result_input_revision'], r['input_revision'])
        self.assertTrue(np.all(np.array(p['after_kw']) <= p['capacity_kw'] + 1e-6))

    def test_history_is_explicitly_stale_and_never_exported_as_current(self):
        current = self.client.get('/api/campus').json()['campus']
        self.assertIsNone(self.client.get('/api/calculations/last').json()['calculation'])
        result = self.client.post('/api/calculate', json={'revision':current['revision']}).json()
        self.assertTrue(self.client.get('/api/calculations/last').json()['is_current'])
        current['scenario']['budget_try'] += 1
        self.client.put('/api/campus',json={key:current[key] for key in ('revision','buildings','scenario')})
        history = self.client.get('/api/calculations/last').json()
        self.assertFalse(history['is_current'])
        self.assertEqual(history['calculation'],result)
        self.assertIsNone(self.client.get('/api/campus').json()['calculation'])
        self.assertIsNone(self.client.get('/api/export/json').json()['calculation'])
        self.assertIsNone(self.client.get('/api/campus/profiles').json()['after_kw'])


if __name__ == '__main__':
    unittest.main()


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
