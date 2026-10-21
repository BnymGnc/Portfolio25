import hashlib
import csv
import io
import json
import tempfile
import unittest
from pathlib import Path

import numpy as np
from fastapi.testclient import TestClient

import main
from engine import calculate,calculate_package,prepare
from models import CalculationRequest,Campus,ProfileSettings
from pilot_kayseri import create_pilot,DATASET
from profiles import generate_profiles
from spatial_energy import allocation,known_electricity
from spatial_models import Floor,Zone,SpatialModel,SharedSystem,SpatialSelection,UseProgram
from spatial_service import evaluate,recommendations
from test_engine import toy_building,toy_scenario


class PilotPhysicsTests(unittest.TestCase):
    def test_four_projects_eight_buildings_reproducible_weather_and_systems(self):
        a,b=create_pilot(),create_pilot()
        self.assertEqual(a,b);self.assertEqual([len(p.buildings) for p in a],[4,2,1,1])
        self.assertEqual(len({z.id for p in a for z in p.buildings}),8)
        self.assertEqual([len(p.connection_groups) for p in a],[1,2,1,1])
        axes=[]
        for project in a:
            self.assertEqual(project.pilot['weather']['kind'],'synthetic')
            for building in project.buildings:
                p=generate_profiles(building,project.profile_settings);axes.append(p.timestamps)
                self.assertAlmostEqual(float(p.electricity_kw.sum()),building.electricity_kwh_year,places=6)
                self.assertAlmostEqual(float(p.useful_heat_kw.sum()),building.heating_kwh_year*building.retrofit.boiler_efficiency,places=6)
                ids={z.id for f in building.spatial.floors for z in f.zones}
                self.assertEqual(set(building.spatial.systems[0].served_zone_ids),ids)
                self.assertGreater(len(building.spatial.floors),1)
        self.assertTrue(all(axis==axes[0] for axis in axes))

    def test_all_allocations_common_areas_and_use_views_reconcile(self):
        for p in create_pilot():
            for b in p.buildings:
                a=allocation(b,p.profile_settings)
                for rows in (a['zones'],a['by_floor'],a['by_use']):
                    self.assertAlmostEqual(sum(r['electricity_kwh_year'] for r in rows),b.electricity_kwh_year,places=6)
                    self.assertAlmostEqual(sum(r['fuel_kwh_year'] for r in rows),b.heating_kwh_year+b.non_heating_gas_kwh_year,places=6)
                    self.assertAlmostEqual(sum(r['useful_heat_kwh_year'] for r in rows),b.heating_kwh_year*b.retrofit.boiler_efficiency,places=6)
                self.assertGreater(sum(r['electricity_kwh_year'] for r in a['zones'] if r['common_area']),0)
                self.assertAlmostEqual(sum(r['components']['hot_water_fuel'] for r in a['zones']),b.spatial.dhw_gas_kwh_year,places=6)

    def test_hand_calculation_lighting_roof_hp_combination_and_unique_cost(self):
        b=toy_building();b.retrofit.heat_pump_capacity_kw_thermal=100
        z=Zone(id='Z001',name='Elle kontrol alanı',use='Ofis',area_m2=100,facade_m2=100,window_m2=10,
            roof_contact=True,heating_system_id='H',lighting_w_m2=10,target_lighting_w_m2=5,device_w_m2=0,
            program=UseProgram(lighting_use_fraction=1),dhw_weight=100)
        b.spatial=SpatialModel(floors=[Floor(id='F00',name='Zemin',area_m2=100,zones=[z])],
            systems=[SharedSystem(id='H',name='Tek ortak sistem',kind='heating',served_zone_ids=['Z001'])],dhw_gas_kwh_year=50)
        b.electricity_kwh_year=known_electricity(b,2025)+100
        profile=generate_profiles(b,ProfileSettings())
        before=calculate_package(b,profile,toy_scenario(),'none',False)
        b.spatial_selection=SpatialSelection(roof=True,lighting=True)
        after=calculate_package(b,profile,toy_scenario(),'heat_pump')
        light_before=b.electricity_kwh_year-100
        ua=90*1.1+10*2.5+100*1.2+.33*.5*100*3
        remaining=800*(1-(100*1.2-100*.35)/ua)
        hp_heat=remaining*.75
        expected_e=b.electricity_kwh_year-light_before*.5+hp_heat/4
        expected_gas=(remaining-hp_heat)/.8
        self.assertAlmostEqual(after.report.electricity_kwh_year,expected_e,places=6)
        self.assertAlmostEqual(after.report.heating_gas_kwh_year,expected_gas,places=6)
        self.assertEqual(after.report.spatial_investment_try,100*650+100*180)
        self.assertEqual(after.report.investment_try,100*650+100*180+100*20+100)
        self.assertEqual(after.report.non_heating_gas_kwh_year,100)
        a=allocation(b,ProfileSettings(),after)
        self.assertAlmostEqual(a['totals']['electricity_kwh_year'],expected_e,places=6)
        # Useful heat is reported separately, never added to final electrical/fuel input.
        self.assertAlmostEqual(after.report.energy_savings_kwh_year,
            before.report.electricity_kwh_year+1100-expected_e-expected_gas-100,places=6)

    def test_protected_services_and_roof_overlap_never_suggested_as_savings(self):
        projects=create_pilot()
        for p,b in [(projects[0],projects[0].buildings[2]),(projects[1],projects[1].buildings[0]),(projects[3],projects[3].buildings[0])]:
            r=next(r for r in recommendations(p,b) if r['id']=='schedule')
            self.assertEqual(r['status'],'review_only');self.assertIsNone(r['effect'])
            with self.assertRaises(ValueError):evaluate(p,b,SpatialSelection(schedule=True,schedule_review_ack=True))
        p=projects[2];b=p.buildings[0]
        with self.assertRaises(ValueError):evaluate(p,b,SpatialSelection(roof=True),'combined')
        with self.assertRaises(ValueError):evaluate(p,b,SpatialSelection(schedule=True))
        r=evaluate(p,b,SpatialSelection(schedule=True,schedule_review_ack=True))
        self.assertFalse(r['comfort_modelled']);self.assertTrue(r['review_required'])

    def test_hotel_hot_water_and_other_gas_preserved_after_all_supported_actions(self):
        p=create_pilot()[3];b=p.buildings[0]
        result=evaluate(p,b,SpatialSelection(roof=True,lighting=True),'heat_pump')
        self.assertEqual(result['before']['non_heating_gas_kwh_year'],result['after']['non_heating_gas_kwh_year'])
        for side in ('allocation_before','allocation_after'):
            self.assertAlmostEqual(sum(r['components']['hot_water_fuel'] for r in result[side]['zones']),b.spatial.dhw_gas_kwh_year,places=6)

    def test_saved_floor_selection_enters_portfolio_once_and_baseline_stays_original(self):
        p=create_pilot()[2];b=p.buildings[0];original=b.electricity_kwh_year+b.heating_kwh_year+b.non_heating_gas_kwh_year
        b.spatial_selection=SpatialSelection(roof=True,lighting=True)
        options,_=prepare(p);fixed=options[0][0].report.spatial_investment_try
        self.assertEqual(fixed,700*650+2100*180)
        result=calculate(p,CalculationRequest(revision=1))
        self.assertAlmostEqual(result.baseline.total_energy_kwh_year,original)
        self.assertEqual(result.selected_packages[0].spatial_investment_try,fixed)
        self.assertAlmostEqual(result.investment_try,sum(r.investment_try for r in result.selected_packages))
        for method in result.decision_evidence['methods'].values():
            if method['evaluation']:
                self.assertLessEqual(method['evaluation']['investment_try'],p.scenario.budget_try+.01)
                self.assertEqual(method['evaluation']['selected_packages'][0]['spatial_investment_try'],fixed)
        for row in result.sensitivity['rows']:
            if row['status']=='evaluated' and row['parameter']=='investment':
                self.assertAlmostEqual(row['evaluation']['selected_packages'][0]['spatial_investment_try'],fixed*row['multiplier'])
        p.scenario.budget_try=0
        self.assertEqual(calculate(p,CalculationRequest(revision=1)).status,'infeasible')


class PilotApiTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.previous=main.DATA_FILE;main.DATA_FILE=Path(self.temp.name)/'campus.json';self.client=TestClient(main.app)
    def tearDown(self):
        self.client.close();main.DATA_FILE=self.previous;self.temp.cleanup()

    def test_explicit_idempotent_load_preserves_existing_project_and_pilot_edits(self):
        self.client.get('/api/campus');original=main.DATA_FILE.read_bytes()
        initial=self.client.get('/api/examples/kayseri').json()
        self.assertTrue(all(not p['loaded'] for p in initial['projects']))
        self.assertEqual(len(self.client.get('/api/projects').json()['projects']),1)
        loaded=self.client.post('/api/examples/kayseri/load').json();self.assertEqual(len(loaded['created']),4)
        project=loaded['projects'][1]['id'];params={'project_id':project}
        c=self.client.get('/api/campus',params=params).json()['campus'];c['scenario']['budget_try']=1234567
        self.assertEqual(self.client.put('/api/campus',params=params,json={k:c[k] for k in ('revision','buildings','scenario')}).status_code,200)
        path=main.DATA_FILE.parent/'projects'/f'{project}.json';saved=path.read_bytes()
        again=self.client.post('/api/examples/kayseri/load').json()
        self.assertEqual(len(again['created']),0);self.assertEqual(len(again['preserved']),4)
        self.assertEqual(path.read_bytes(),saved);self.assertEqual(main.DATA_FILE.read_bytes(),original)
        self.assertEqual(sum(p['building_count'] for p in again['projects']),8)
        exported=self.client.get('/api/export/csv',params={**params,'scope':'inputs','revision':2})
        self.assertEqual(exported.status_code,200)
        rows=list(csv.DictReader(io.StringIO(exported.content.decode('utf-8-sig'))))
        self.assertEqual(json.loads(rows[0]['project_json'])['pilot']['dataset'],DATASET)
        self.assertEqual(json.loads(rows[0]['spatial_model_json'])['schema_version'],'1.0')

    def test_preview_readonly_save_invalidates_result_and_history_kept(self):
        loaded=self.client.post('/api/examples/kayseri/load').json();pid=loaded['projects'][2]['id'];params={'project_id':pid}
        self.client.post('/api/calculate',params=params,json={'revision':1})
        c=self.client.get('/api/campus/snapshot',params=params).json();campus=c['campus'];bid=campus['buildings'][0]['id']
        data_path=main.DATA_FILE.parent/'projects'/f'{pid}.json';before=data_path.read_bytes();old_result=data_path.with_suffix('.result.json').read_bytes()
        preview=self.client.post(f'/api/buildings/{bid}/spatial/evaluate',params=params,json={'revision':1,'selection':{'lighting':True,'roof':True},'package':'heat_pump'})
        self.assertEqual(preview.status_code,200,preview.text);self.assertEqual(data_path.read_bytes(),before)
        campus['buildings'][0]['spatial_selection']['lighting']=True
        saved=self.client.put('/api/campus',params=params,json={k:campus[k] for k in ('revision','buildings','scenario')})
        self.assertEqual(saved.status_code,200);self.assertIsNone(saved.json()['calculation'])
        rejected=self.client.get('/api/export/json',params={**params,'scope':'result','revision':1,'expected_calculation_id':c['calculation_id']})
        self.assertEqual(rejected.status_code,409)
        self.client.post('/api/calculate',params=params,json={'revision':2})
        archive=main.DATA_FILE.parent/'history'/pid/(hashlib.sha256(old_result).hexdigest()+'.json')
        self.assertEqual(archive.read_bytes(),old_result)
        result=self.client.get('/api/campus',params=params).json()
        self.assertAlmostEqual(result['baseline']['electricity_kwh_year'],campus['buildings'][0]['electricity_kwh_year'])

    def test_geometry_and_unreconciled_inputs_rejected_without_loss(self):
        loaded=self.client.post('/api/examples/kayseri/load').json();pid=loaded['projects'][0]['id'];params={'project_id':pid}
        c=self.client.get('/api/campus',params=params).json()['campus']
        path=main.DATA_FILE.parent/'projects'/f'{pid}.json';original=path.read_bytes()
        c['buildings'][0]['spatial']['floors'][0]['zones'][0]['area_m2']+=1
        self.assertEqual(self.client.put('/api/campus',params=params,json={k:c[k] for k in ('revision','buildings','scenario')}).status_code,422)
        self.assertEqual(path.read_bytes(),original)
        c=self.client.get('/api/campus',params=params).json()['campus'];c['buildings'][0]['electricity_kwh_year']=1
        self.assertEqual(self.client.put('/api/campus',params=params,json={k:c[k] for k in ('revision','buildings','scenario')}).status_code,422)
        self.assertEqual(path.read_bytes(),original)

    def test_old_records_missing_floor_data_are_not_fabricated(self):
        c=self.client.get('/api/campus').json()
        answer=self.client.get('/api/buildings/B01/spatial').json()
        self.assertFalse(answer['available']);self.assertIsNone(c['campus']['buildings'][0]['spatial'])


if __name__=='__main__':unittest.main()


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
