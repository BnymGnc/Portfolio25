import os,tempfile,unittest
from pathlib import Path
from unittest.mock import patch
from fastapi.testclient import TestClient
import main
from auth import Accounts
from serve import platform_port,serve

class DeploymentTests(unittest.TestCase):
    def test_public_health_has_safe_release_and_process_identity(self):
        with tempfile.TemporaryDirectory() as temp,patch.object(main,'DATA_FILE',Path(temp)/'campus.json'),patch.dict(os.environ,{
                'STORAGE_BACKEND':'sqlite','RENDER':'false','DATABASE_URL':'','RENDER_GIT_COMMIT':'a'*40}),TestClient(main.app) as client:
            first=client.get('/api/health').json()
            self.assertEqual(first['release_commit'],'a'*40)
            self.assertRegex(first['boot_id'],r'^[a-f0-9]{32}$')
            self.assertEqual(client.get('/api/health').json()['boot_id'],first['boot_id'])
            with patch.dict(os.environ,{'RENDER_GIT_COMMIT':'invalid-value-must-not-be-exposed'}):
                self.assertIsNone(client.get('/api/health').json()['release_commit'])
            self.assertEqual(list(Path(temp).iterdir()),[])

    def test_platform_port_and_all_interface_single_worker(self):
        with patch.dict(os.environ,{'PORT':'12345','BACKEND_PORT':'8000','BACKEND_HOST':'127.0.0.1'}):
            self.assertEqual(platform_port(),12345)
            with patch('serve.uvicorn.run') as run:
                serve();run.assert_called_once_with('main:app',host='0.0.0.0',port=12345,workers=1)
        for value in ('','not-a-port','0','65536'):
            with patch.dict(os.environ,{'PORT':value}),self.assertRaises(ValueError):platform_port()

    def test_https_session_cookie_csrf_persistence_and_public_health(self):
        origin='https://buildingportfolio25.vercel.app'
        with tempfile.TemporaryDirectory() as temp,patch.object(main,'DATA_FILE',Path(temp)/'campus.json'),patch.object(main,'AUTH_REQUIRED',True),patch.object(main,'ORIGINS',{origin}),patch.object(main.accounts,'secure',True):
            with TestClient(main.app,base_url=origin) as client:
                # Render probes require neither auth nor a working data/solver check.
                response=client.get('/api/health');self.assertEqual(response.status_code,200)
                self.assertEqual(response.json()['data_status'],'not_checked');self.assertEqual(list(Path(temp).iterdir()),[])
                boot=client.get('/api/auth/session');cookie=boot.headers['set-cookie']
                for flag in ('HttpOnly','Secure','SameSite=lax','Path=/'):self.assertIn(flag,cookie)
                self.assertNotIn('Domain=',cookie)
                csrf=boot.json()['csrf'];client.headers.update({'Origin':origin,'X-CSRF-Token':csrf})
                registered=client.post('/api/auth/register',json={'email':'deploy@example.test','password':'temporary-test-password-123'})
                self.assertEqual(registered.status_code,200,registered.text);uid=registered.json()['user']['id']
                client.headers['X-CSRF-Token']=registered.json()['csrf']
                self.assertIn('no-store',registered.headers['cache-control']);self.assertIn('Cookie',registered.headers['vary'])
                self.assertEqual(client.post('/api/auth/onboarding',json={}).status_code,200)
                self.assertEqual(client.post('/api/auth/onboarding',headers={'Origin':'https://evil.invalid'},json={}).status_code,403)
                self.assertEqual(client.post('/api/auth/onboarding',headers={'X-CSRF-Token':'wrong'},json={}).status_code,403)
                projects=client.get('/api/projects').json()['projects'];self.assertEqual(len(projects),4)
                pid=projects[0]['id'];snapshot=client.get('/api/campus/snapshot',params={'project_id':pid});self.assertEqual(snapshot.status_code,200)
                # Reopen the store with the same persistent path and existing cookie.
                with patch.object(main,'accounts',Accounts(lambda:Path(temp)/'accounts.sqlite3',secure=True)):
                    self.assertEqual(client.get('/api/auth/session').json()['user']['id'],uid)
                    self.assertEqual(client.get('/api/auth/session').json()['user']['onboarding_version'],1)
                    self.assertEqual(client.get('/api/campus/snapshot',params={'project_id':pid}).json()['campus'],snapshot.json()['campus'])
                old=client.cookies.get('portfolio25_session')
                self.assertEqual(client.post('/api/auth/logout',json={}).status_code,200)
                with TestClient(main.app,base_url=origin) as other:
                    other.cookies.set('portfolio25_session',old)
                    self.assertEqual(other.get('/api/projects').status_code,401)

if __name__=='__main__':unittest.main()
