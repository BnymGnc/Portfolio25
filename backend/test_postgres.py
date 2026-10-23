"""Real PostgreSQL only. Run scripts/test_postgres.py; never a SQLite substitute."""
from concurrent.futures import ThreadPoolExecutor
from contextlib import ExitStack
import hashlib
import json
import os
from pathlib import Path
import secrets
import subprocess
import tempfile
import time
import unittest
from unittest.mock import patch

from fastapi import HTTPException
from fastapi.responses import Response
from fastapi.testclient import TestClient

import main
from postgres_store import PostgresStore
from auth import Accounts, Credentials, COOKIE
from import_postgres import import_archive
from models import CalculationRequest
from engine import calculate
from pilot_kayseri import create_pilot
from storage_admin import backup

ORIGIN='https://buildingportfolio25.vercel.app'


@unittest.skipUnless(os.getenv('TEST_DATABASE_URL'), 'Requires real isolated PostgreSQL; use scripts/test_postgres.py')
class PostgresTests(unittest.TestCase):
    index=0

    def setUp(self):
        self.stack=ExitStack();self.addCleanup(self.stack.close)
        self.temp=self.stack.enter_context(tempfile.TemporaryDirectory())
        self.store=PostgresStore(os.environ['TEST_DATABASE_URL'],timeout=8,connect_timeout=5)
        self.addCleanup(self.store.close)
        self.store.migrate()
        self.stack.enter_context(patch.object(main,'DATA_FILE',Path(self.temp)/'should-stay-empty'/'campus.json'))
        self.stack.enter_context(patch.object(main,'get_store',lambda:self.store))
        self.stack.enter_context(patch('storage.get_store',lambda:self.store))
        self.stack.enter_context(patch.object(main,'ORIGINS',{ORIGIN}))
        self.stack.enter_context(patch.object(main.accounts,'secure',True))
        self.stack.enter_context(patch.object(main,'AUTH_REQUIRED',True))
        self.clients=[]

    def client(self):
        PostgresTests.index+=1
        client=TestClient(main.app,base_url=ORIGIN,client=(f'192.0.2.{PostgresTests.index}',5000))
        self.addCleanup(client.close)
        boot=client.get('/api/auth/session')
        self.assertEqual(boot.status_code,200,boot.text)
        self.assertEqual(boot.json()['storage']['status'],'postgresql')
        client.headers.update({'Origin':ORIGIN,'X-CSRF-Token':boot.json()['csrf']})
        self.clients.append(client)
        return client

    def account(self):
        client=self.client()
        credentials={'email':'qa-pg-'+secrets.token_hex(8)+'@example.test','password':secrets.token_urlsafe(24)}
        registered=client.post('/api/auth/register',json=credentials)
        self.assertEqual(registered.status_code,200,registered.text)
        for flag in ('Secure','HttpOnly','SameSite=lax'):
            self.assertIn(flag,registered.headers['set-cookie'])
        client.headers['X-CSRF-Token']=registered.json()['csrf']
        return client,credentials,registered.json()['user']['id']

    def office(self,client):
        projects=client.get('/api/projects').json()['projects']
        self.assertEqual(len(projects),4)
        selected=next(p for p in projects if p['building_count']==1 and 'ofis' in p['name'].lower())
        params={'project_id':selected['id']}
        snapshot=client.get('/api/campus/snapshot',params=params)
        self.assertEqual(snapshot.status_code,200,snapshot.text)
        return params,snapshot.json()

    def assert_no_files(self):
        self.assertFalse(main.DATA_FILE.parent.exists(),'PostgreSQL production must not write local accounts/projects/results')

    def test_real_building_draft_publish_quotes_survive_reopen(self):
        from test_intakes import IntakeTests
        client,_,uid=self.account();other,_,_=self.account()
        draft=IntakeTests.ready(self,client).model_dump(mode='json')
        saved=client.post('/api/intakes',json=draft)
        self.assertEqual(saved.status_code,200,saved.text);draft=saved.json()['draft']
        self.assertEqual(other.get('/api/intakes').json(),[])
        published=client.post('/api/intakes/'+draft['id']+'/publish',json=draft)
        self.assertEqual(published.status_code,200,published.text);value=published.json()['draft']
        params={'project_id':value['project_id']}
        run=client.post('/api/calculate',params=params,json={'revision':1,'mode':'A','time_limit_s':3})
        self.assertEqual(run.status_code,200,run.text)
        self.assertGreater(run.json()['energy_savings_kwh_year'],0)
        before=client.get('/api/campus/snapshot',params=params).json()
        self.store.close();self.store=PostgresStore(os.environ['TEST_DATABASE_URL']);self.addCleanup(self.store.close)
        self.store.migrate();self.store.migrate()
        self.assertEqual(client.get('/api/intakes').json()[0]['draft'],value)
        self.assertEqual(client.get('/api/campus/snapshot',params=params).json(),before)
        self.assertEqual(other.get('/api/campus/snapshot',params=params).status_code,404)
        self.assert_no_files()

    def test_named_scenario_immutable_owner_isolation_restart(self):
        a,_,uid=self.account();b,_,_=self.account()
        params,snapshot=self.office(a)
        result=a.post('/api/calculate',params=params,json={'revision':1,'mode':'A','time_limit_s':3})
        self.assertEqual(result.status_code,200)
        snapshot=a.get('/api/campus/snapshot',params=params).json()
        saved=a.post('/api/scenarios/saved',params=params,json={'name':'Baseline QA','context':snapshot['context']})
        self.assertEqual(saved.status_code,200,saved.text);saved=saved.json()
        path='/api/scenarios/saved/'+saved['id']
        self.assertEqual(b.get(path,params=params).status_code,404)
        other,_=self.office(b)
        self.assertEqual(b.get(path,params=other).status_code,404)
        original=snapshot['campus']
        edit={'revision':1,'buildings':original['buildings'],'scenario':{**original['scenario'],'budget_try':1}}
        self.assertEqual(a.put('/api/campus',params=params,json=edit).status_code,200)
        self.assertEqual(a.post('/api/scenarios/saved',params=params,json={'name':'Stale','context':snapshot['context']}).status_code,409)
        self.store.close();self.store=PostgresStore(os.environ['TEST_DATABASE_URL']);self.addCleanup(self.store.close)
        self.store.migrate();self.store.migrate()
        self.assertEqual(a.get(path,params=params).json(),saved)
        self.assertEqual(saved['inputs'],original)
        self.assertEqual(saved['calculation']['calculation_id'],result.json()['calculation_id'])
        self.assertEqual(len(a.get('/api/scenarios/saved',params=params).json()),1)
        current=a.get('/api/campus/snapshot',params=params).json()
        self.assertEqual(current['campus']['scenario']['budget_try'],1)
        self.assertIsNone(current['calculation'])
        self.assert_no_files()

    def test_auth_argon2_csrf_logout_revocation_and_owner_isolation(self):
        a,credentials,uid=self.account();b,_,_=self.account()
        params,snapshot=self.office(a)
        self.assertEqual(b.get('/api/campus/snapshot',params=params).status_code,404)
        self.assertEqual(b.get('/api/export/json',params=params).status_code,404)
        self.assertEqual(b.post('/api/calculate',params=params,json={'revision':1,'mode':'A','time_limit_s':3}).status_code,404)
        self.assertEqual(a.post('/api/auth/logout',headers={'Origin':'https://evil.invalid'},json={}).status_code,403)
        self.assertEqual(a.post('/api/auth/logout',headers={'X-CSRF-Token':'wrong'},json={}).status_code,403)
        cookie=a.cookies.get(COOKIE)
        logged_out=a.post('/api/auth/logout',json={});self.assertEqual(logged_out.status_code,200)
        a.headers['X-CSRF-Token']=logged_out.json()['csrf']
        with TestClient(main.app,base_url=ORIGIN) as stolen:
            stolen.cookies.set(COOKIE,cookie)
            self.assertEqual(stolen.get('/api/projects').status_code,401)
        wrong=a.post('/api/auth/login',json={**credentials,'password':'definitely-wrong-password'})
        self.assertEqual(wrong.status_code,401)
        correct=a.post('/api/auth/login',json=credentials)
        self.assertEqual(correct.status_code,200,correct.text)
        self.assertEqual(correct.json()['user']['id'],uid)
        self.assertEqual(a.get('/api/campus/snapshot',params=params).json()['campus'],snapshot['campus'])
        with self.store.connection() as db:
            stored=db.execute('SELECT password_hash FROM portfolio25.users WHERE id=%s',(uid,)).fetchone()['password_hash']
            self.assertTrue(stored.startswith('$argon2id$'))
            self.assertNotIn(credentials['password'],stored)
        self.assert_no_files()

    def test_edit_invalid_input_revision_calculation_export_ml_and_application_restart(self):
        client,credentials,uid=self.account()
        params,snapshot=self.office(client)
        original=snapshot['campus']
        update={'revision':original['revision'],'name':'QA PostgreSQL private office',
                'buildings':original['buildings'],'scenario':original['scenario']}
        invalid=json.loads(json.dumps(update));invalid['buildings'][0]['area_m2']=0
        self.assertEqual(client.put('/api/campus',params=params,json=invalid).status_code,422)
        self.assertEqual(client.get('/api/campus/snapshot',params=params).json()['campus'],original)
        invalid_physics=json.loads(json.dumps(update))
        for floor in invalid_physics['buildings'][0]['spatial']['floors']:
            for zone in floor['zones']:zone['cooling_system_id']=None
        rejected=client.put('/api/campus',params=params,json=invalid_physics)
        self.assertEqual(rejected.status_code,422)
        self.assertIn('soğutma',rejected.json()['error']['message'])
        self.assertEqual(client.get('/api/campus/snapshot',params=params).json()['campus'],original)
        saved=client.put('/api/campus',params=params,json=update)
        self.assertEqual(saved.status_code,200,saved.text)
        current=saved.json()['campus'];self.assertEqual(current['revision'],original['revision']+1)
        self.assertEqual(client.put('/api/campus',params=params,json=update).status_code,409)
        result=client.post('/api/calculate',params=params,json={'revision':current['revision'],'mode':'A','time_limit_s':5})
        self.assertEqual(result.status_code,200,result.text)
        result=result.json();self.assertEqual(result['status'],'optimal')
        immutable=main.CalculationResult.model_validate(result)
        immutable.message='Changed document with the same calculation identity'
        with self.assertRaises(HTTPException) as conflict:
            self.store.save_result(uid,main.Campus.model_validate(current),immutable)
        self.assertEqual(conflict.exception.status_code,409)
        exported=client.get('/api/export/json',params={**params,'scope':'result','revision':current['revision'],'expected_calculation_id':result['calculation_id']})
        self.assertEqual(exported.status_code,200,exported.text)
        self.assertEqual(exported.json()['calculation']['calculation_id'],result['calculation_id'])
        self.assertEqual(client.get('/api/export/csv',params={**params,'scope':'inputs','revision':current['revision']}).status_code,200)
        campus=client.get('/api/campus/snapshot',params=params).json()
        candidate=client.get(f"/api/buildings/{current['buildings'][0]['id']}/packages",params=params).json()['packages'][0]
        prediction=client.post('/api/ml/synthetic/predict',params=params,json={'context':campus['context'],'building_id':current['buildings'][0]['id'],'candidate_id':candidate['candidate_id']})
        self.assertEqual(prediction.status_code,200,prediction.text)
        self.assertEqual(prediction.json()['status'],'available')
        # A completely new pool/application store against the same actual database.
        self.store.close()
        self.store=PostgresStore(os.environ['TEST_DATABASE_URL'],timeout=8,connect_timeout=5);self.addCleanup(self.store.close)
        self.store.migrate()
        self.assertEqual(client.get('/api/auth/session').json()['user']['id'],uid)
        self.assertEqual(client.get('/api/campus/snapshot',params=params).json()['campus'],current)
        self.assertEqual(client.get('/api/calculations/last',params=params).json()['calculation']['calculation_id'],result['calculation_id'])
        # Marking old calculations stale keeps the actual historical result.
        update['revision']=current['revision'];update['name']='QA revision after calculation'
        changed=client.put('/api/campus',params=params,json=update);self.assertEqual(changed.status_code,200)
        last=client.get('/api/calculations/last',params=params).json()
        self.assertFalse(last['is_current']);self.assertEqual(last['calculation']['calculation_id'],result['calculation_id'])
        self.assertEqual(client.get('/api/export/json',params={**params,'scope':'result','revision':current['revision']+1,'expected_calculation_id':result['calculation_id']}).status_code,409)
        recalculated=client.post('/api/calculate',params=params,json={'revision':current['revision']+1,'mode':'A','time_limit_s':5})
        self.assertEqual(recalculated.status_code,200,recalculated.text)
        self.assertNotEqual(recalculated.json()['calculation_id'],result['calculation_id'])
        with self.store.connection() as db:
            history=db.execute('SELECT calculation_id FROM portfolio25.calculations WHERE owner_id=%s AND project_id=%s',(uid,current['id'])).fetchall()
            self.assertEqual({r['calculation_id'] for r in history},{result['calculation_id'],recalculated.json()['calculation_id']})
        self.assert_no_files()

    def test_concurrent_revision_updates_and_idempotent_migrations_and_pilot(self):
        client,_,uid=self.account();params,snapshot=self.office(client)
        campus=main.Campus.model_validate(snapshot['campus'])
        with self.store.connection() as db:
            checksum=db.execute('SELECT * FROM portfolio25.schema_migrations').fetchall()
        self.store.migrate();self.store.migrate()
        with self.store.connection() as db:
            self.assertEqual(db.execute('SELECT * FROM portfolio25.schema_migrations').fetchall(),checksum)
        before=self.store.projects(uid)
        for _ in range(2):
            loaded=client.post('/api/examples/kayseri/load',json={})
            self.assertEqual(loaded.status_code,200);self.assertEqual(loaded.json()['created'],[])
        self.assertEqual(self.store.projects(uid),before)
        variants=[campus.model_copy(deep=True),campus.model_copy(deep=True)]
        for i,variant in enumerate(variants):variant.revision+=1;variant.name=f'Concurrent QA {i}'
        def save(variant):
            try:self.store.save_project(uid,variant,expected_revision=campus.revision);return 200
            except HTTPException as error:return error.status_code
        with ThreadPoolExecutor(max_workers=2) as pool:
            self.assertEqual(sorted(pool.map(save,variants)),[200,409])
        self.assertEqual(self.store.project(uid,campus.id)['revision'],campus.revision+1)
        stale=calculate(campus,CalculationRequest(revision=campus.revision,mode='A',time_limit_s=3))
        with self.assertRaises(HTTPException) as stale_conflict:self.store.save_result(uid,campus,stale)
        self.assertEqual(stale_conflict.exception.status_code,409)
        self.assertIsNone(self.store.last_result(uid,campus.id))
        self.assert_no_files()

    def test_legacy_backup_import_is_atomic_idempotent_preserves_hash_session_and_owners(self):
        data=Path(self.temp)/'legacy';accounts=Accounts(lambda:data/'accounts.sqlite3')
        credentials=Credentials(email='qa-pg-legacy-'+secrets.token_hex(6)+'@example.test',password=secrets.token_urlsafe(24))
        uid=accounts.register(credentials)
        response=Response();reply=accounts.issue(response,uid)
        from http.cookies import SimpleCookie
        cookie=SimpleCookie();cookie.load(response.headers['set-cookie']);token=cookie[COOKIE].value
        with accounts.db() as db:original_hash=db.execute('SELECT password_hash FROM users WHERE id=?',(uid,)).fetchone()[0]
        campus=create_pilot()[2];campus.id='project-'+secrets.token_hex(6)
        project=data/'users'/uid/'projects'/f'{campus.id}.json';project.parent.mkdir(parents=True)
        project.write_text(campus.model_dump_json(),encoding='utf-8')
        result=calculate(campus,CalculationRequest(revision=campus.revision,mode='A',time_limit_s=3))
        project.with_name(project.stem+'.result.json').write_text(result.model_dump_json(),encoding='utf-8')
        # A shared legacy campus is backed up, but never assigned to this owner.
        (data/'campus.json').write_text(create_pilot()[0].model_dump_json(),encoding='utf-8')
        from intakes import Intake
        own_draft=Intake(name='Legacy private draft')
        with accounts.db() as db:
            db.execute('CREATE TABLE building_intakes(owner_id TEXT,intake_id TEXT,revision INTEGER,document TEXT)')
            db.execute('INSERT INTO building_intakes VALUES(?,?,?,?)',(uid,own_draft.id,1,own_draft.model_dump_json()))
        source_hash=hashlib.sha256(project.read_bytes()).hexdigest()
        archive=backup(data,Path(self.temp)/'legacy.portfolio25-backup.zip')
        self.assertEqual(import_archive(self.store,archive)['status'],'validated_only')
        self.assertEqual(import_archive(self.store,archive,apply=True)['status'],'imported')
        self.assertEqual(import_archive(self.store,archive,apply=True)['status'],'already_imported')
        self.assertEqual(len(self.store.projects(uid)),1)
        self.assertEqual(self.store.project(uid,campus.id),campus.model_dump(mode='json'))
        with self.store.connection() as db:
            self.assertTrue(db.execute('SELECT password_hash FROM portfolio25.users WHERE id=%s',(uid,)).fetchone()['password_hash']==original_hash,'Original password hash must be retained')
        client=self.client();client.cookies.set(COOKIE,token)
        self.assertEqual(client.get('/api/auth/session').json()['user']['id'],uid)
        self.assertEqual(client.get('/api/intakes').json()[0]['draft'],own_draft.model_dump(mode='json'))
        self.assertEqual(client.get('/api/calculations/last',params={'project_id':campus.id}).json()['calculation']['calculation_id'],result.calculation_id)
        self.assertEqual(hashlib.sha256(project.read_bytes()).hexdigest(),source_hash)
        self.assert_no_files()

    def test_import_conflict_rolls_back_all_earlier_inserts(self):
        data=Path(self.temp)/'legacy-conflict';accounts=Accounts(lambda:data/'accounts.sqlite3')
        first=Credentials(email='qa-pg-before-'+secrets.token_hex(6)+'@example.test',password=secrets.token_urlsafe(24))
        first_uid=accounts.register(first)
        second=Credentials(email='qa-pg-conflict-'+secrets.token_hex(6)+'@example.test',password=secrets.token_urlsafe(24))
        second_uid=accounts.register(second)
        archive=backup(data,Path(self.temp)/'conflict.portfolio25-backup.zip')
        # Existing target identity at the same email must never be reassigned.
        other_uid=secrets.token_hex(16)
        with self.store.connection() as db:
            db.execute('INSERT INTO portfolio25.users(id,email,password_hash) VALUES(%s,%s,%s)',(other_uid,second.email,'test-conflict-value'))
        with self.assertRaises(ValueError):import_archive(self.store,archive,apply=True)
        with self.store.connection() as db:
            self.assertIsNone(db.execute('SELECT id FROM portfolio25.users WHERE id IN (%s,%s)',(first_uid,second_uid)).fetchone())
            self.assertEqual(db.execute('SELECT id FROM portfolio25.users WHERE email=%s',(second.email,)).fetchone()['id'],other_uid)
        self.assert_no_files()

    def test_real_database_outage_is_503_no_fallback_and_recovers(self):
        container=os.getenv('TEST_POSTGRES_CONTAINER')
        if not container:self.skipTest('Docker-managed outage test requires scripts/test_postgres.py')
        client,credentials,uid=self.account();params,snapshot=self.office(client)
        stopped=False
        try:
            subprocess.run(['docker','stop','--time','1',container],check=True,capture_output=True);stopped=True
            for method,url,body in [('get','/api/health',None),('get','/api/auth/session',None),('post','/api/auth/login',credentials)]:
                response=getattr(client,method)(url,**({'json':body} if body else {}))
                self.assertEqual(response.status_code,503,response.text)
                self.assertFalse(credentials['password'] in response.text,'Password must not leak')
                self.assertFalse(os.environ['TEST_DATABASE_URL'] in response.text,'DSN must not leak')
                if url!='/api/health':self.assertEqual(response.json()['error']['code'],'database_unavailable')
            self.assert_no_files()
        finally:
            if stopped:subprocess.run(['docker','start',container],check=True,capture_output=True)
            from urllib.parse import urlsplit
            binding=subprocess.run(['docker','port',container,'5432/tcp'],capture_output=True,text=True,check=True).stdout.strip()
            self.assertEqual(int(binding.rsplit(':',1)[1]),urlsplit(os.environ['TEST_DATABASE_URL']).port,'QA service address changed, not a database reconnect failure')
            deadline=time.monotonic()+45
            while subprocess.run(['docker','exec',container,'pg_isready','-U','qa'],capture_output=True).returncode:
                if time.monotonic()>deadline:self.fail('QA PostgreSQL did not recover')
                time.sleep(1)
        # Reuse the same pool after a real DB stop/start; checkout checking and
        # reconnection must recover without restarting the application.
        deadline=time.monotonic()+30
        while True:
            recovered=client.get('/api/auth/session')
            if recovered.status_code==200:break
            if time.monotonic()>deadline:self.fail('Existing pool did not reconnect after DB recovery')
            time.sleep(1)
        self.assertEqual(recovered.json()['user']['id'],uid)
        self.assertEqual(client.get('/api/campus/snapshot',params=params).json()['campus'],snapshot['campus'])


if __name__=='__main__':unittest.main()
