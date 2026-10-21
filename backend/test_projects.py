import csv
import io
import itertools
import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import numpy as np
from fastapi.testclient import TestClient

import config
import main
from engine import prepare, solve_packages, calculate, summarize
from models import CalculationRequest, Campus, ConnectionGroup
from sample_data import create_sample_campus


class ProjectTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory()
        self.original=main.DATA_FILE
        main.DATA_FILE=Path(self.temp.name)/'campus.json'
        self.client=TestClient(main.app)

    def tearDown(self):
        self.client.close();main.DATA_FILE=self.original;self.temp.cleanup()

    def create(self, ids, connection='independent'):
        response=self.client.post('/api/projects',json={'name':'Sentetik test projesi','building_ids':ids,'connection_mode':connection})
        self.assertEqual(response.status_code,200,response.text)
        return {'project_id':response.json()['id']}

    def test_single_and_multi_project_full_flow_persistence_and_isolation(self):
        original=self.client.get('/api/campus').json()
        original_bytes=main.DATA_FILE.read_bytes()
        for ids in (['B03'],['B01','B03']):
            project=self.create(ids)
            current=self.client.get('/api/campus/snapshot',params=project).json()
            self.assertEqual(len(current['campus']['buildings']),len(ids))
            self.assertEqual(len(current['campus']['connection_groups']),len(ids))
            payload={k:current['campus'][k] for k in ('revision','name','buildings','scenario','connection_groups','sensitivity_settings')}
            payload['buildings'][0]['name']='Kalıcı proje binası'
            saved=self.client.put('/api/campus',params=project,json=payload)
            self.assertEqual(saved.status_code,200,saved.text)
            self.assertEqual(self.client.get('/api/campus',params=project).json()['campus']['buildings'][0]['name'],'Kalıcı proje binası')
            for mode in ('A','B'):
                computed=self.client.post('/api/calculate',params=project,json={'revision':2,'mode':mode})
                self.assertEqual(computed.status_code,200,computed.text)
                c=self.client.get('/api/campus/snapshot',params=project).json()
                self.assertEqual(c['calculation']['project_id'],project['project_id'])
                self.assertEqual(c['calculation']['decision_evidence']['input_revision'],2)
                exported=self.client.get('/api/export/json',params={**project,'scope':'result','revision':2,'expected_calculation_id':c['calculation_id']})
                self.assertEqual(exported.status_code,200)
                self.assertEqual(exported.json()['export_metadata']['project_id'],project['project_id'])
                self.assertIn('sensitivity',exported.json()['calculation'])
            p=self.client.get('/api/campus/profiles',params=project).json()
            self.assertEqual(len(p['groups']),len(ids))
            if len(ids)>1:self.assertIsNone(p['capacity_kw'])
            self.assertEqual(main.DATA_FILE.read_bytes(),original_bytes)
        self.assertEqual(len(self.client.get('/api/projects').json()['projects']),3)
        self.assertEqual(self.client.get('/api/campus').json(),original)

    def test_v2_migration_exact_backup_values_and_stale_result(self):
        raw=create_sample_campus().model_dump(mode='json')
        raw['schema_version']='2.0';raw['revision']=17
        for key in ('connection_groups','sensitivity_settings'):raw.pop(key)
        for b in raw['buildings']:
            for key in ('heating_system','heat_distribution','insulation_allowed','system_source'):b.pop(key)
        raw['buildings'][0]['name']='Kullanıcı verisi korunur'
        original=json.dumps(raw,ensure_ascii=False,indent=2).encode('utf-8')
        main.DATA_FILE.write_bytes(original)
        result=calculate(create_sample_campus(),CalculationRequest(revision=17))
        main.result_path().write_text(result.model_dump_json(),encoding='utf-8')
        response=self.client.get('/api/campus').json()
        c=response['campus']
        self.assertEqual(c['schema_version'],'3.0');self.assertEqual(c['revision'],18)
        self.assertEqual(c['buildings'][0]['name'],raw['buildings'][0]['name'])
        self.assertEqual(c['scenario'],raw['scenario'])
        self.assertEqual(c['connection_groups'][0]['capacity_kw'],raw['scenario']['electric_capacity_kw'])
        self.assertEqual(main.DATA_FILE.with_name('campus.v2-backup.json').read_bytes(),original)
        self.assertIsNone(response['calculation'])
        self.assertFalse(self.client.get('/api/calculations/last').json()['is_current'])
        self.assertEqual(self.client.get('/api/campus').json()['campus']['revision'],18)

    def test_partition_validation_legacy_alias_and_unknown_project(self):
        project=self.create(['B01','B02'])
        campus=self.client.get('/api/campus',params=project).json()['campus']
        payload={k:campus[k] for k in ('revision','buildings','scenario','connection_groups')}
        payload['connection_groups'][1]['building_ids']=['B01']
        self.assertEqual(self.client.put('/api/campus',params=project,json=payload).status_code,422)
        payload.pop('connection_groups')
        payload['scenario']['electric_capacity_kw']=1
        saved=self.client.put('/api/campus',params=project,json=payload)
        self.assertEqual(saved.status_code,200)
        # The obsolete aggregate field does not constrain independent buildings.
        computed=self.client.post('/api/calculate',params=project,json={'revision':2,'mode':'A'}).json()
        self.assertIsNotNone(computed['after'])
        campus=self.client.get('/api/campus').json()['campus']
        campus['scenario']['electric_capacity_kw']=1000
        saved=self.client.put('/api/campus',json={k:campus[k] for k in ('revision','buildings','scenario')}).json()
        self.assertEqual(saved['campus']['connection_groups'][0]['capacity_kw'],1000)
        self.assertEqual(self.client.get('/api/campus',params={'project_id':'../../secret'}).status_code,422)
        self.assertEqual(self.client.get('/api/campus',params={'project_id':'project-000000000000'}).status_code,404)

    def test_eligibility_filters_actual_optimization_and_profiles(self):
        project=self.create(['B01'])
        campus=self.client.get('/api/campus',params=project).json()['campus']
        campus['buildings'][0]['heat_distribution']='high_temperature_water'
        saved=self.client.put('/api/campus',params=project,json={k:campus[k] for k in ('revision','buildings','scenario')})
        self.assertEqual(saved.status_code,200)
        packages=self.client.get('/api/buildings/B01/packages',params=project).json()
        self.assertEqual([p['package'] for p in packages['packages']],['none','insulation'])
        self.assertEqual(len(packages['excluded_packages']),2)
        self.assertEqual(self.client.get('/api/buildings/B01/profiles',params={**project,'package':'heat_pump'}).status_code,422)
        result=self.client.post('/api/calculate',params=project,json={'revision':2}).json()
        self.assertTrue(all(p['package'] in ('none','insulation') for p in result['selected_packages']))
        self.assertEqual(result['decision_evidence']['package_universe']['B01'],['none','insulation'])
        campus=self.client.get('/api/campus',params=project).json()['campus']
        campus['buildings'][0]['heating_system']='electric_resistance'
        self.client.put('/api/campus',params=project,json={k:campus[k] for k in ('revision','buildings','scenario')})
        packages=self.client.get('/api/buildings/B01/packages',params=project).json()
        self.assertEqual([p['package'] for p in packages['packages']],['none'])

    def test_comparisons_enumeration_real_capacity_violations_and_no_forced_advantage(self):
        campus=create_sample_campus()
        campus.buildings=campus.buildings[:2]
        campus.scenario.budget_try=100_000_000
        campus.connection_groups=[ConnectionGroup(id=f'G{i+1:02d}',name=b.name,building_ids=[b.id],capacity_kw=10000) for i,b in enumerate(campus.buildings)]
        options,_=prepare(campus)
        for mode in ('A','B'):
            request=CalculationRequest(revision=1,mode=mode)
            unconstrained=solve_packages(campus.buildings,options,campus.scenario,request,campus.connection_groups,False)
            baseline=unconstrained.baseline.total_energy_kwh_year
            plans=list(itertools.product(*options))
            feasible=[p for p in plans if sum(x.report.investment_try for x in p)<=campus.scenario.budget_try and
                      (mode=='A' or sum(x.report.energy_savings_kwh_year for x in p)>=baseline*campus.scenario.savings_target_pct/100-.001)]
            expected=(max(sum(x.report.energy_savings_kwh_year for x in p) for p in feasible) if mode=='A' else
                      min(sum(x.report.investment_try for x in p) for p in feasible))
            self.assertAlmostEqual(unconstrained.energy_savings_kwh_year if mode=='A' else unconstrained.investment_try,expected)
        result=calculate(campus,CalculationRequest(revision=1))
        methods=result.decision_evidence['methods']
        self.assertTrue(methods['without_grid']['evaluation']['capacity_met'])
        self.assertAlmostEqual(methods['grid']['evaluation']['energy_savings_kwh_year'],methods['without_grid']['evaluation']['energy_savings_kwh_year'])
        self.assertLessEqual(methods['ratio']['evaluation']['investment_try'],campus.scenario.budget_try)
        campus.connection_groups[0].capacity_kw=190
        constrained=calculate(campus,CalculationRequest(revision=1))
        methods=constrained.decision_evidence['methods']
        self.assertFalse(methods['without_grid']['evaluation']['capacity_met'])
        self.assertTrue(methods['grid']['evaluation']['capacity_met'])
        self.assertGreater(methods['without_grid']['evaluation']['capacity_violations'][0]['violation_hours'],0)

    def test_sensitivity_fixed_plan_base_identity_repricing_and_invalid_range(self):
        campus=create_sample_campus();campus.buildings=campus.buildings[:1]
        campus.connection_groups=[ConnectionGroup(id='G01',name='Tek bağlantı',building_ids=['B01'],capacity_kw=10000)]
        result=calculate(campus,CalculationRequest(revision=1))
        self.assertEqual(len(result.sensitivity['rows']),9)
        self.assertFalse(result.sensitivity['reoptimized'])
        selected=[(p.building_id,p.package) for p in result.selected_packages]
        for row in result.sensitivity['rows']:
            e=row['evaluation']
            self.assertEqual([(p['building_id'],p['package']) for p in e['selected_packages']],selected)
            if row['level']=='base':
                self.assertAlmostEqual(e['energy_savings_kwh_year'],result.energy_savings_kwh_year)
                self.assertAlmostEqual(e['investment_try'],result.investment_try)
            if row['parameter']=='investment':
                self.assertAlmostEqual(e['investment_try'],result.investment_try*row['multiplier'])
        rows={r['level']:r['evaluation'] for r in result.sensitivity['rows'] if r['parameter']=='scop'}
        self.assertLess(rows['low']['energy_savings_kwh_year'],rows['high']['energy_savings_kwh_year'])
        campus.buildings[0].retrofit.insulation_reduction_fraction=.9
        campus.sensitivity_settings.insulation.high=2
        result=calculate(campus,CalculationRequest(revision=1))
        row=next(r for r in result.sensitivity['rows'] if r['parameter']=='insulation' and r['level']=='high')
        self.assertEqual(row['status'],'invalid_assumptions');self.assertIsNone(row['evaluation'])


class EnvironmentTests(unittest.TestCase):
    def test_explicit_backend_path_independent_of_cwd_without_overriding_process_environment(self):
        with tempfile.TemporaryDirectory() as directory:
            base=Path(directory);backend=base/'backend';backend.mkdir()
            (backend/'.env').write_text('GRID_CONFIG_TEST=from_file\nOPENAI_API_KEY=fake_unit_test_value\n',encoding='utf-8')
            cwd=Path.cwd()
            try:
                os.chdir(base)
                with patch.object(config,'BASE_DIR',backend),patch.dict(os.environ,{'OPENAI_API_KEY':'existing_test_value'},clear=True):
                    config.load_backend_env()
                    self.assertEqual(os.environ['GRID_CONFIG_TEST'],'from_file')
                    self.assertEqual(os.environ['OPENAI_API_KEY'],'existing_test_value')
            finally:os.chdir(cwd)

    def test_missing_key_does_not_disable_health_or_leak_settings(self):
        with patch.dict(os.environ,{'OPENAI_API_KEY':'','OPENAI_MODEL':'unused_test_model'}):
            with TestClient(main.app) as client:
                answer=client.get('/api/health')
                self.assertEqual(answer.status_code,200)
                self.assertNotIn('OPENAI',answer.text)


if __name__=='__main__':unittest.main()


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
