import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import main
from pilot_kayseri import create_pilot


class IntegrityTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.patch=patch.object(main,'DATA_FILE',Path(self.temp.name)/'campus.json');self.patch.start()
        self.client=TestClient(main.app);self.campus=create_pilot()[2];main.write_campus(self.campus)
    def tearDown(self):self.client.close();self.patch.stop();self.temp.cleanup()
    def test_invalid_physics_never_commits(self):
        before=main.DATA_FILE.read_bytes();raw=self.campus.model_dump(mode='json')
        for f in raw['buildings'][0]['spatial']['floors']:
            for z in f['zones']:z['cooling_system_id']=None
        result=self.client.put('/api/campus',json={k:raw[k] for k in ('revision','buildings','scenario')})
        self.assertEqual(result.status_code,422);self.assertIn('soğutma',result.json()['error']['message'])
        self.assertTrue(result.json()['error']['fields']);self.assertEqual(main.DATA_FILE.read_bytes(),before)
        self.assertEqual(self.client.get('/api/campus').status_code,200)
    def test_context_identity_and_engine_changes(self):
        result=self.client.post('/api/calculate',json={'revision':1}).json()
        self.assertTrue(result['calculation_id']);self.assertTrue(result['input_hash']);self.assertTrue(result['engine_version'])
        snapshot=self.client.get('/api/campus/snapshot').json()
        profiles=self.client.get('/api/campus/profiles',params={'expected_calculation_id':result['calculation_id']}).json()
        self.assertEqual(profiles['context'],snapshot['context'])
        self.assertEqual(self.client.get('/api/campus/profiles?expected_calculation_id=wrong').status_code,409)
        with patch('calculation_context.ENGINE_VERSION','future'):
            self.assertIsNone(self.client.get('/api/campus/snapshot').json()['calculation'])
            last=self.client.get('/api/calculations/last').json();self.assertFalse(last['is_current']);self.assertIn('sürümü',last['stale_reason'])
        old=json.loads(main.result_path().read_text(encoding='utf-8'));old['project_id']='project-000000000000'
        main.result_path().write_text(json.dumps(old),encoding='utf-8')
        self.assertFalse(self.client.get('/api/calculations/last').json()['is_current'])
        self.assertIsNone(self.client.get('/api/campus/snapshot').json()['calculation'])
    def test_input_digest_and_readiness(self):
        self.client.post('/api/calculate',json={'revision':1})
        c=self.campus.model_copy(deep=True);c.scenario.budget_try+=1;main.write_campus(c)
        self.assertFalse(self.client.get('/api/calculations/last').json()['is_current'])
        self.assertEqual(self.client.get('/api/health').json()['optimization_status'],'not_checked')

    def test_same_revision_change_during_solve_never_persists_result(self):
        self.assertEqual(self.client.post('/api/calculate',json={'revision':1}).status_code,200)
        original_result=main.result_path().read_bytes()
        actual_calculate=main.calculate
        def change_input(campus,request):
            result=actual_calculate(campus,request)
            edited=campus.model_copy(deep=True);edited.name+=' external edit'
            main.write_campus(edited)  # Simulate a direct file edit without a revision bump.
            return result
        with patch.object(main,'calculate',side_effect=change_input):
            response=self.client.post('/api/calculate',json={'revision':1})
        self.assertEqual(response.status_code,409)
        self.assertEqual(main.result_path().read_bytes(),original_result)
        self.assertFalse(self.client.get('/api/calculations/last').json()['is_current'])


class InterventionTests(unittest.TestCase):
    def test_optional_mandatory_applied_and_enumeration(self):
        from spatial_models import InterventionDecision,SpatialSelection
        from engine import prepare,calculate,solve_packages
        from models import CalculationRequest
        from itertools import product
        p=create_pilot()[2];b=p.buildings[0]
        b.spatial_selection=SpatialSelection(schedule_review_ack=True)
        b.interventions=[InterventionDecision(kind=k,state='candidate') for k in ('roof','insulation','lighting','schedule','heat_pump')]
        options,_=prepare(p);self.assertLessEqual(len(options[0]),32)
        self.assertTrue(any(o.report.candidate_id=='none' and o.report.investment_try==0 for o in options[0]))
        self.assertTrue(any(o.report.candidate_id=='lighting' for o in options[0]))
        self.assertFalse(any({'roof','insulation'}<={d.kind for d in o.report.interventions} for o in options[0]))
        p.scenario.budget_try=1_000_000
        for mode in ('A','B'):
            feasible=[]
            for combo in product(*options):
                cost=sum(o.report.investment_try for o in combo);saving=sum(o.report.energy_savings_kwh_year for o in combo)
                if cost>p.scenario.budget_try or any(o.electricity_kw.max()>b.connection_limit_kw for o in combo):continue
                if sum((o.electricity_kw for o in combo)).max()>p.connection_groups[0].capacity_kw:continue
                if mode=='B' and saving<combo[0].baseline.report.electricity_kwh_year*.0+(combo[0].baseline.report.electricity_kwh_year+combo[0].baseline.report.heating_gas_kwh_year+b.non_heating_gas_kwh_year)*p.scenario.savings_target_pct/100:continue
                feasible.append((cost,saving))
            result=solve_packages(p.buildings,options,p.scenario,CalculationRequest(revision=1,mode=mode),p.connection_groups)
            self.assertEqual(result.status,'optimal')
            self.assertAlmostEqual(result.energy_savings_kwh_year,max(x[1] for x in feasible)) if mode=='A' else self.assertAlmostEqual(result.investment_try,min(x[0] for x in feasible))
        b.interventions=[InterventionDecision(kind='lighting',state='applied'),InterventionDecision(kind='roof',state='mandatory')]
        options,_=prepare(p)
        for o in options[0]:
            self.assertEqual(o.report.intervention_costs['lighting'],0)
            self.assertEqual(o.report.investment_try,700*b.spatial.roof_cost_try_m2)
            self.assertEqual(o.baseline.report.investment_try,0)
            self.assertLess(o.baseline.report.electricity_kwh_year,b.electricity_kwh_year)
        result=calculate(p,CalculationRequest(revision=1))
        roof=[r for r in result.sensitivity['rows'] if r['parameter']=='roof']
        self.assertEqual(len(roof),3)
        self.assertGreater(roof[0]['evaluation']['energy_savings_kwh_year'],roof[-1]['evaluation']['energy_savings_kwh_year'])


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
