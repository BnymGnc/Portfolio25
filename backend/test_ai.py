import json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
from fastapi import HTTPException
import main,ai_service
from pilot_kayseri import create_pilot


class AITests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.p=patch.object(main,'DATA_FILE',Path(self.temp.name)/'campus.json');self.p.start()
        main.write_campus(create_pilot()[2]);self.client=TestClient(main.app)
        self.client.post('/api/calculate',json={'revision':1,'mode':'A'})
        self.ctx=self.client.get('/api/campus/snapshot').json()['context'];ai_service._cache.clear();ai_service._requests.clear()
    def tearDown(self):self.client.close();self.p.stop();self.temp.cleanup()
    def test_explanation_bound_cache_and_invalid_claim(self):
        answer={'findings':[{'fact_id':k,'text':'Bu alan hesap motorunun varsayımlı sonucudur.'} for k in ('investment_try','energy_savings_kwh_year','target_met')],'details':[]}
        response={'status':'completed','output':[{'type':'message','content':[{'type':'output_text','text':json.dumps(answer)}]}]}
        with patch('ai_service.provider_call',return_value=response) as call:
            a=self.client.post('/api/ai/explain',json={'context':self.ctx}).json();b=self.client.post('/api/ai/explain',json={'context':self.ctx}).json()
            self.assertEqual(a['context'],self.ctx);self.assertEqual(len(a['findings']),3);self.assertTrue(b['cached']);self.assertEqual(call.call_count,1)
        ai_service._cache.clear();answer['findings'][0]['text']='Kesin 100 TL tasarruf.';response['output'][0]['content'][0]['text']=json.dumps(answer)
        with patch('ai_service.provider_call',return_value=response):self.assertEqual(self.client.post('/api/ai/explain',json={'context':self.ctx}).status_code,503)
        old=main.result_path().read_bytes()
        with patch('ai_service.provider_call',side_effect=HTTPException(503,'Sahte servis kesintisi')):
            self.assertEqual(self.client.post('/api/ai/explain',json={'context':self.ctx}).status_code,503)
        self.assertEqual(main.result_path().read_bytes(),old)
        self.assertEqual(self.client.post('/api/calculate',json={'revision':1}).status_code,200)
        self.assertEqual(self.client.post('/api/ai/explain',json={'context':self.ctx}).status_code,409)
    def test_scenario_function_only_and_no_main_write(self):
        reply={'status':'completed','output':[{'type':'function_call','name':'propose_scenario','arguments':json.dumps({'changes':[{'field':'budget_try','value':3080000}],'explanation':'Bütçe değişikliği taslağı.'})}]}
        with patch('ai_service.provider_call',return_value=reply) as call:
            draft=self.client.post('/api/ai/scenario-draft',json={'context':self.ctx,'question':'Bütçe yüzde on artsa?'}).json()
            self.assertEqual(call.call_args.args[0]['tools'][0]['name'],'propose_scenario');self.assertEqual(draft['changes'][0]['value'],3080000)
        data=main.DATA_FILE.read_bytes();saved=main.result_path().read_bytes()
        body={'context':self.ctx,'changes':draft['changes'],'mode':'A'}
        run=self.client.post('/api/scenarios/evaluate',json=body)
        self.assertEqual(run.status_code,200);self.assertFalse(run.json()['persisted']);self.assertNotEqual(run.json()['alternative']['input_hash'],self.ctx['input_hash'])
        self.assertEqual(main.DATA_FILE.read_bytes(),data);self.assertEqual(main.result_path().read_bytes(),saved)
        forced=self.client.post('/api/scenarios/counterfactual',json={'context':self.ctx,'building_id':'B07','intervention':'roof'})
        self.assertEqual(forced.status_code,200);self.assertEqual(forced.json()['forced_intervention']['kind'],'roof')
        self.assertEqual(main.DATA_FILE.read_bytes(),data);self.assertEqual(main.result_path().read_bytes(),saved)
        self.assertEqual(self.client.post('/api/scenarios/evaluate',json={**body,'changes':[{'field':'path','value':1}]}).status_code,422)
        self.assertEqual(self.client.post('/api/scenarios/apply',json=body).json()['campus']['revision'],2)
    def test_named_local_snapshot_remains_immutable(self):
        body={'name':'Baseline','context':self.ctx}
        saved=self.client.post('/api/scenarios/saved',json=body)
        self.assertEqual(saved.status_code,200,saved.text)
        value=saved.json();before=main.DATA_FILE.read_bytes()
        self.assertEqual(self.client.get('/api/scenarios/saved/'+value['id']).json(),value)
        self.assertEqual(main.DATA_FILE.read_bytes(),before)
        self.assertEqual(value['calculation']['calculation_id'],self.ctx['calculation_id'])
        self.assertEqual(len(self.client.get('/api/scenarios/saved').json()),1)

    def test_missing_key_status_and_openapi(self):
        with patch.dict('os.environ',{'OPENAI_API_KEY':''}):
            self.assertFalse(self.client.get('/api/ai/status').json()['configured'])
            self.assertEqual(self.client.post('/api/ai/explain',json={'context':self.ctx}).status_code,503)
        schema=self.client.get('/openapi.json').json()
        self.assertTrue(any(p['name']=='project_id' for p in schema['paths']['/api/calculate']['post']['parameters']))
        self.assertEqual(schema['paths']['/api/ai/explain']['post']['responses']['200']['content']['application/json']['schema']['$ref'],'#/components/schemas/Explanation')


def setUpModule():
    global _auth_patch
    from unittest.mock import patch
    _auth_patch=patch.object(main,'AUTH_REQUIRED',False)
    _auth_patch.start()

def tearDownModule():
    _auth_patch.stop()
