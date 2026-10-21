import unittest,tempfile,json
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import main
from pilot_kayseri import create_pilot
from spatial_models import InterventionDecision

class FinalIntegrity(unittest.TestCase):
    def setUp(self):
        t=tempfile.TemporaryDirectory();self.addCleanup(t.cleanup)
        for name,value in [('DATA_FILE',Path(t.name)/'campus.json'),('AUTH_REQUIRED',False)]:
            p=patch.object(main,name,value);p.start();self.addCleanup(p.stop)
        self.client=TestClient(main.app);self.addCleanup(self.client.close)
        self.c=create_pilot()[2];main.write_campus(self.c)
    def test_preview_draft_policy_matches_saved_engine_without_commit(self):
        b=self.c.buildings[0];selection=b.spatial_selection.model_dump();selection['lighting']=True
        decisions=[{'kind':'roof','state':'applied'},{'kind':'lighting','state':'mandatory'},{'kind':'heat_pump','state':'candidate'}]
        before=main.DATA_FILE.read_bytes()
        body={'revision':1,'selection':selection,'package':'heat_pump','spatial':b.spatial.model_dump(),'interventions':decisions}
        preview=self.client.post('/api/buildings/B07/spatial/evaluate',json=body)
        self.assertEqual(preview.status_code,200,preview.text);self.assertEqual(main.DATA_FILE.read_bytes(),before)
        b.interventions=[InterventionDecision(**d) for d in decisions];b.spatial_selection.lighting=True
        main.write_campus(self.c)
        packages=self.client.get('/api/buildings/B07/packages').json()['packages']
        match=next(p for p in packages if p['candidate_id']==preview.json()['after']['candidate_id'])
        for key in ('investment_try','electricity_kwh_year','heating_gas_kwh_year','energy_savings_kwh_year'):
            self.assertAlmostEqual(match[key],preview.json()['after'][key],places=6)
        self.assertEqual(match['intervention_costs']['roof'],0);self.assertGreater(match['intervention_costs']['lighting'],0)
    def test_new_decisions_excluded_preview_rejected(self):
        b=self.c.buildings[0]
        r=self.client.post('/api/buildings/B07/spatial/evaluate',json={'revision':1,'selection':{'lighting':True},'interventions':[{'kind':'lighting','state':'excluded'}]})
        self.assertEqual(r.status_code,422)
    def test_synthetic_group_integrity_real_inference_and_missing(self):
        import synthetic_ml
        from profiles import generate_profiles
        from interventions import candidates
        m=synthetic_ml.metadata();self.assertIsNotNone(m)
        groups=[set(m['groups'][name]) for name in ('train','validation','test')]
        self.assertTrue(all(not groups[i]&groups[j] for i in range(3) for j in range(i)))
        self.assertEqual(sum(map(len,groups)),m['building_count']);self.assertGreaterEqual(m['building_count'],200)
        self.assertFalse(any('after' in n or 'target' in n and n!='roof_target_u' for n in m['features']))
        context=self.client.get('/api/campus/snapshot').json()['context']
        b=self.c.buildings[0];options=candidates(b,generate_profiles(b,self.c.profile_settings),self.c.scenario)
        predictions=[]
        for option in options:
            r=self.client.post('/api/ml/synthetic/predict',json={'context':context,'building_id':b.id,'candidate_id':option.report.candidate_id})
            self.assertEqual(r.status_code,200,r.text);value=r.json();self.assertFalse(value['used_for_optimization']);self.assertFalse(value['capacity_inference'])
            if value['prediction']:predictions.append(value['prediction'])
        self.assertGreaterEqual(len(predictions),2,'Pilot is outside model domain: inspect bounds honestly')
        self.assertNotEqual(predictions[0],predictions[-1])
        with tempfile.TemporaryDirectory() as temp,patch.object(synthetic_ml,'ASSET_DIR',Path(temp)):
            r=synthetic_ml.predict(b,options[0],context,2025);self.assertEqual(r.status,'missing_model');self.assertIsNone(r.prediction)
        altered=b.model_copy(deep=True);altered.area_m2=1e6
        r=synthetic_ml.predict(altered,options[0],context,2025);self.assertEqual(r.status,'out_of_domain');self.assertIsNone(r.prediction)

if __name__=='__main__':unittest.main()
