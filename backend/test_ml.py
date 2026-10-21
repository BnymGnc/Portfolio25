import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import main,ml_service
from pilot_kayseri import create_pilot


class MLTests(unittest.TestCase):
    def test_group_split_features_and_real_inference(self):
        m=ml_service.metadata();self.assertIsNotNone(m)
        a,b,c=(set(m['split_groups'][k]) for k in ('train','validation','test'))
        self.assertFalse(a&b or a&c or b&c)
        self.assertGreater(m['building_groups'],100)
        self.assertFalse(any('after' in f or 'saving' in f or 'target' in f for f in m['features']))
        self.assertIn('ridge_reference',m['test_metrics']);self.assertIn('by_building_type',m['test_metrics'][m['selected_model']])
        with tempfile.TemporaryDirectory() as temp,patch.object(main,'DATA_FILE',Path(temp)/'campus.json'),TestClient(main.app) as client:
            main.write_campus(create_pilot()[2]);context=client.get('/api/campus/snapshot').json()['context'];before=main.DATA_FILE.read_bytes()
            value=client.post('/api/ml/predict',json={'context':context,'features':m['example']['features'],'country':'US'})
            self.assertEqual(value.status_code,200);self.assertEqual(value.json()['status'],'available');self.assertFalse(value.json()['capacity_inference'])
            self.assertGreaterEqual(value.json()['prediction']['electricity_kwh_year'],0)
            out=client.post('/api/ml/predict',json={'context':context,'features':m['example']['features'],'country':'TR'}).json()
            self.assertEqual(out['status'],'out_of_domain');self.assertIsNone(out['prediction'])
            local=client.post('/api/ml/project-predict',json={'context':context,'building_id':'B07'}).json();self.assertIsNotNone(local['physics_result']);self.assertIsNone(local['prediction'])
            with patch.object(ml_service,'ASSET_DIR',Path(temp)/'missing'):
                self.assertFalse(client.get('/api/ml/status').json()['available'])
                self.assertEqual(client.post('/api/ml/predict',json={'context':context,'features':m['example']['features']}).json()['status'],'missing_model')
            self.assertEqual(main.DATA_FILE.read_bytes(),before)


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
