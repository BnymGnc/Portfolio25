import io,json,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from urllib.error import HTTPError
from fastapi.testclient import TestClient
import main,ai_service

ORIGIN='http://127.0.0.1:5173'
class AccountTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory();self.addCleanup(self.temp.cleanup)
        p=patch.object(main,'DATA_FILE',Path(self.temp.name)/'campus.json');p.start();self.addCleanup(p.stop)
        p=patch.object(main,'AUTH_REQUIRED',True);p.start();self.addCleanup(p.stop)
        self.clients=[]
    def account(self,name):
        c=TestClient(main.app);self.addCleanup(c.close)
        csrf=c.get('/api/auth/session').json()['csrf'];c.headers.update({'Origin':ORIGIN,'X-CSRF-Token':csrf})
        r=c.post('/api/auth/register',json={'email':name+'@example.test','password':'test-only-password-123'})
        self.assertEqual(r.status_code,200,r.text);c.headers['X-CSRF-Token']=r.json()['csrf'];return c,r.json()['user']
    def test_private_pilot_sessions_and_ownership(self):
        legacy=b'{"private":"legacy untouched"}';main.DATA_FILE.write_bytes(legacy)
        a,ua=self.account('alice');b,ub=self.account('bob')
        pa=a.get('/api/projects').json()['projects'];pb=b.get('/api/projects').json()['projects']
        self.assertEqual(len(pa),4);self.assertEqual(sum(p['building_count'] for p in pa),8)
        self.assertFalse({p['id'] for p in pa}&{p['id'] for p in pb})
        pid=pa[0]['id']
        for path in ('/api/campus/snapshot','/api/campus/profiles','/api/export/json','/api/calculations/last','/api/buildings/B01/spatial','/api/ai/status','/api/ml/status'):
            self.assertEqual(b.get(path,params={'project_id':pid}).status_code,404,path)
        for path in ('/api/calculate','/api/ai/explain','/api/ml/project-predict','/api/scenarios/evaluate','/api/scenarios/apply','/api/buildings/B01/spatial/evaluate'):
            self.assertEqual(b.post(path,params={'project_id':pid},json={}).status_code,404,path)
        self.assertEqual(b.put('/api/campus',params={'project_id':pid},json={}).status_code,404)
        a.post('/api/auth/onboarding',json={});self.assertEqual(a.get('/api/auth/session').json()['user']['onboarding_version'],1)
        self.assertEqual(a.post('/api/auth/logout',json={}).status_code,200)
        self.assertEqual(a.get('/api/projects').status_code,401)
        csrf=a.get('/api/auth/session').json()['csrf'];a.headers['X-CSRF-Token']=csrf
        login=a.post('/api/auth/login',json={'email':'alice@example.test','password':'test-only-password-123'});self.assertEqual(login.status_code,200)
        self.assertEqual(login.json()['user']['id'],ua['id']);self.assertEqual(len(a.get('/api/projects').json()['projects']),4)
        self.assertEqual(main.DATA_FILE.read_bytes(),legacy)
        raw=(Path(self.temp.name)/'accounts.sqlite3').read_bytes();self.assertNotIn(b'test-only-password-123',raw)
        # Reopen database using a new store: onboarding and identity survive restart.
        from auth import Accounts
        self.assertEqual(Accounts(lambda:Path(self.temp.name)/'accounts.sqlite3').public_user(ua['id'])['onboarding_version'],1)
    def test_two_accounts_share_versioned_pilot_values_but_never_edits(self):
        from copy import deepcopy
        from pilot_kayseri import create_pilot, DATASET
        a,_=self.account('pilot-a');b,_=self.account('pilot-b')
        def snapshots(client):
            projects=client.get('/api/projects').json()['projects']
            return {value['campus']['pilot']['project_key']:value for value in
                    [client.get('/api/campus/snapshot',params={'project_id':p['id']}).json() for p in projects]}
        def canonical(document):
            value=deepcopy(document);value.pop('id');return value
        aa,bb=snapshots(a),snapshots(b)
        expected={p.pilot['project_key']:p.model_dump(mode='json') for p in create_pilot()}
        self.assertEqual(set(aa),set(expected));self.assertEqual(sum(len(x['campus']['buildings']) for x in aa.values()),8)
        for key in expected:
            self.assertEqual(aa[key]['campus']['pilot']['dataset'],DATASET)
            self.assertEqual(canonical(aa[key]['campus']),canonical(expected[key]))
            self.assertEqual(canonical(aa[key]['campus']),canonical(bb[key]['campus']))
            self.assertEqual(aa[key]['baseline'],bb[key]['baseline'])
            self.assertEqual(aa[key]['profile_audit'],bb[key]['profile_audit'])
            self.assertNotEqual(aa[key]['campus']['id'],bb[key]['campus']['id'])
        original_b=deepcopy(bb)
        edit=deepcopy(aa['campus']['campus']);pid=edit['id']
        edit['scenario']['budget_try']+=12345
        edit['buildings'][0]['name']='Only account A edit'
        saved=a.put('/api/campus',params={'project_id':pid},json={k:edit[k] for k in main.CampusUpdate.model_fields})
        self.assertEqual(saved.status_code,200,saved.text)
        own=a.get('/api/campus/snapshot',params={'project_id':pid}).json()['campus']
        self.assertEqual(own['revision'],2)
        self.assertEqual(snapshots(b),original_b)
        self.assertEqual(b.get('/api/campus/snapshot',params={'project_id':pid}).status_code,404)
        reloaded=a.post('/api/examples/kayseri/load',json={})
        self.assertEqual(reloaded.status_code,200,reloaded.text)
        self.assertEqual(reloaded.json()['created'],[])
        a.headers['X-CSRF-Token']=a.post('/api/auth/logout',json={}).json()['csrf']
        login=a.post('/api/auth/login',json={'email':'pilot-a@example.test','password':'test-only-password-123'})
        self.assertEqual(login.status_code,200)
        self.assertEqual(a.get('/api/campus/snapshot',params={'project_id':pid}).json()['campus'],own)
        self.assertEqual(canonical(create_pilot()[0].model_dump(mode='json')),canonical(expected['campus']))

    def test_csrf_cookie_and_revocation(self):
        c,user=self.account('csrf');token=c.cookies.get('portfolio25_session')
        response=c.get('/api/projects');self.assertIn('no-store',response.headers['cache-control'])
        self.assertEqual(c.post('/api/auth/logout',headers={'Origin':'https://evil.invalid'},json={}).status_code,403)
        self.assertEqual(c.post('/api/auth/logout',headers={'X-CSRF-Token':'wrong'},json={}).status_code,403)
        self.assertEqual(c.post('/api/auth/logout',json={}).status_code,200)
        attacker=TestClient(main.app);self.addCleanup(attacker.close);attacker.cookies.set('portfolio25_session',token)
        self.assertEqual(attacker.get('/api/projects').status_code,401)
    def test_quota_and_rate_are_not_retried(self):
        for code,state in [('insufficient_quota','quota_exhausted'),('rate_limit_exceeded','rate_limited')]:
            err=HTTPError('https://api.openai.com',429,'rate',{},io.BytesIO(json.dumps({'error':{'code':code}}).encode()))
            with patch.dict('os.environ',{'OPENAI_API_KEY':'fake-test-key'}),patch('ai_service.urlopen',side_effect=err) as provider:
                with self.assertRaises(main.HTTPException):ai_service.provider_call({'input':'test'})
                self.assertEqual(provider.call_count,1);self.assertEqual(ai_service.service_status()['last_call_status'],state)

if __name__=='__main__':unittest.main()
