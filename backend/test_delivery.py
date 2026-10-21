import csv
import io
import tempfile
import unittest
from pathlib import Path

from fastapi.testclient import TestClient
import main
from engine import calculate, prepare, summarize
from models import CalculationRequest
from sample_data import create_sample_campus
import numpy as np


class DeliveryExportTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.original=main.DATA_FILE
        main.DATA_FILE=Path(self.temp.name)/'campus.json'
        self.client=TestClient(main.app)

    def tearDown(self):
        self.client.close()
        main.DATA_FILE=self.original
        self.temp.cleanup()

    def calculated(self,mode='A'):
        c=self.client.get('/api/campus/snapshot').json()
        self.client.post('/api/calculate',json={'revision':c['campus']['revision'],'mode':mode})
        return self.client.get('/api/campus/snapshot').json()

    def test_explicit_inputs_never_include_plan_even_after_calculation(self):
        c=self.calculated()
        result=self.client.get('/api/export/json',params={'scope':'inputs','revision':c['campus']['revision']})
        self.assertEqual(result.status_code,200)
        body=result.json()
        self.assertIsNone(body['calculation'])
        self.assertIsNone(body['investment_plan'])
        self.assertIsNone(body['after'])
        self.assertEqual(body['export_metadata']['kind'],'inputs')
        self.assertIn('inputs-r1',result.headers['content-disposition'])

    def test_result_contains_same_revision_plan_solver_assumptions_and_source(self):
        c=self.calculated()
        params={'scope':'result','revision':1,'expected_calculation_id':c['calculation_id']}
        result=self.client.get('/api/export/json',params=params)
        body=result.json()
        self.assertEqual(result.status_code,200)
        self.assertEqual(body['calculation'],c['calculation'])
        self.assertEqual(len(body['investment_plan']),8)
        self.assertEqual(body['export_metadata']['calculation_revision'],1)
        self.assertEqual(body['export_metadata']['calculation_id'],c['calculation_id'])
        self.assertEqual(body['campus']['provenance']['kind'],'synthetic')
        self.assertIn('source',body['campus']['scenario']['price_basis'])
        exported=self.client.get('/api/export/csv',params=params)
        rows=list(csv.DictReader(io.StringIO(exported.text.lstrip('\ufeff'))))
        self.assertEqual({r['revision'] for r in rows},{'1'})
        self.assertEqual({r['calculation_id'] for r in rows},{c['calculation_id']})
        self.assertTrue(all(r['campus_after_json'] and r['solver_json'] and r['selected_package_json'] for r in rows))

    def test_revision_race_and_same_revision_recalculation_rejected(self):
        a=self.calculated('A')
        params={'scope':'result','revision':1,'expected_calculation_id':a['calculation_id']}
        b=self.calculated('B')
        self.assertNotEqual(a['calculation_id'],b['calculation_id'])
        self.assertEqual(self.client.get('/api/export/json',params=params).status_code,409)
        c=b['campus'];c['scenario']['budget_try']+=1
        self.client.put('/api/campus',json={k:c[k] for k in ('revision','buildings','scenario')})
        self.assertEqual(self.client.get('/api/export/json',params={'scope':'inputs','revision':1}).status_code,409)
        self.assertEqual(self.client.get('/api/export/json',params={'scope':'result','revision':2,'expected_calculation_id':b['calculation_id']}).status_code,409)
        self.assertEqual(self.client.get('/api/export/json',params={'scope':'result'}).status_code,422)

    def test_actual_campus_heat_balance_and_both_mode_capacity_checks(self):
        campus=create_sample_campus()
        groups,_=prepare(campus)
        for building,group in zip(campus.buildings,groups):
            for p in group:
                report=p.report
                self.assertAlmostEqual(report.heat_pump_heat_kwh_year+report.backup_boiler_heat_kwh_year,
                                       report.useful_heat_after_kwh_year,places=6)
                self.assertAlmostEqual(report.heating_gas_kwh_year*building.retrofit.boiler_efficiency,
                                       report.backup_boiler_heat_kwh_year,places=6)
                self.assertAlmostEqual(report.electricity_kwh_year,
                                       building.electricity_kwh_year+report.heat_pump_electricity_kwh_year,places=6)
                self.assertEqual(report.non_heating_gas_kwh_year,building.non_heating_gas_kwh_year)
        for mode in ('A','B'):
            result=calculate(campus,CalculationRequest(revision=1,mode=mode))
            self.assertIsNotNone(result.after)
            selected={p.building_id:p.package for p in result.selected_packages}
            profiles=[next(p for p in group if p.report.package==selected[b.id]) for b,group in zip(campus.buildings,groups)]
            load=np.sum([p.electricity_kw for p in profiles],axis=0)
            self.assertTrue(np.all(load<=campus.scenario.electric_capacity_kw+1e-6))
            self.assertTrue(all(np.max(p.electricity_kw)<=b.connection_limit_kw+1e-6 for b,p in zip(campus.buildings,profiles)))
            self.assertAlmostEqual(float(load.max()),result.after.electric_peak_kw)
            self.assertLessEqual(result.investment_try,campus.scenario.budget_try+.01)

    def test_zero_budget_impossible_target_and_initial_overload(self):
        campus=create_sample_campus()
        campus.scenario.budget_try=0
        result=calculate(campus,CalculationRequest(revision=1,mode='A'))
        self.assertEqual(result.status,'optimal')
        self.assertEqual(result.investment_try,0)
        self.assertTrue(all(p.package=='none' for p in result.selected_packages))
        self.assertAlmostEqual(result.energy_savings_kwh_year,0)
        campus.scenario.budget_try=1e12
        campus.scenario.electric_capacity_kw=5000
        campus.scenario.savings_target_pct=100
        result=calculate(campus,CalculationRequest(revision=1,mode='B'))
        self.assertEqual(result.status,'infeasible')
        campus.scenario.electric_capacity_kw=50
        campus.connection_groups[0].capacity_kw=50
        for mode in ('A','B'):
            result=calculate(campus,CalculationRequest(revision=1,mode=mode))
            self.assertGreater(result.baseline.electric_peak_kw,50)
            self.assertEqual(result.status,'infeasible')
            self.assertIsNone(result.after)


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
