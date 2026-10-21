"""Run real PostgreSQL integration tests in an isolated local Docker container.

No production credentials, .env, unrelated containers, training or LLM calls.
The random database password is never printed; temporary files are removed.
"""
import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import subprocess
import sys
import tempfile
import time
import unittest
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def docker(*args):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Docker QA operation failed; check Docker Desktop and the postgres:16-alpine image.')
    return result.stdout.strip()


def deployment_smoke(image, database_container, password, api_port, directory):
    """Real CMD/PORT/configuration, without replacing the app's storage provider."""
    name='portfolio25-api-pg-qa-'+secrets.token_hex(5)
    origin='https://buildingportfolio25.vercel.app'
    base=f'http://127.0.0.1:{api_port}'
    cookie='';csrf='';created=False
    envfile=Path(directory)/'api-qa.env'
    with envfile.open('x',encoding='utf-8') as stream:
        envfile.chmod(0o600)
        stream.write(f'DATABASE_URL=postgresql://qa:{password}@127.0.0.1:5432/portfolio25qa?sslmode=disable\n')

    def request(path,body=None,method=None,*,use_cookie=None):
        nonlocal cookie,csrf
        headers={'Origin':origin,'Content-Type':'application/json'}
        if cookie or use_cookie:headers['Cookie']=cookie if use_cookie is None else use_cookie
        if csrf:headers['X-CSRF-Token']=csrf
        req=Request(base+path,data=None if body is None else json.dumps(body).encode(),headers=headers,method=method)
        try:response=urlopen(req,timeout=45)
        except HTTPError as error:response=error
        with response:
            value=json.load(response)
            received=response.headers.get('set-cookie')
            if received:
                assert all(flag in received for flag in ('HttpOnly','Secure','SameSite=lax','Path=/'))
                assert 'Domain=' not in received
                cookie=received.split(';',1)[0]
            if value.get('csrf'):csrf=value['csrf']
            assert 'no-store' in response.headers.get('cache-control','')
            return response.status,value

    def launch():
        nonlocal created
        # Shared QA network namespace allows loopback-only non-TLS PostgreSQL.
        # This is not a claim that Neon TLS/PgBouncer was exercised.
        docker('run','--detach','--name',name,'--memory','768m',
               '--network','container:'+database_container,'--env-file',str(envfile),
               '-e','PORT=18463','-e','RENDER=true','-e','STORAGE_BACKEND=postgres',
               '-e','COOKIE_SECURE=true','-e','FRONTEND_ORIGINS='+origin,image)
        created=True
        deadline=time.monotonic()+90
        while True:
            try:
                status,health=request('/api/health')
                if status==200 and health['storage']['status']=='postgresql':return health
            except (URLError,TimeoutError,ConnectionError):pass
            if time.monotonic()>deadline:raise RuntimeError('Docker PostgreSQL application startup/health did not become ready')
            time.sleep(1)

    try:
        first_boot=launch()  # Empty DB: serve.py itself must apply the first migration.
        assert request('/api/auth/session')[0]==200
        credentials={'email':'qa-container-'+secrets.token_hex(6)+'@example.test','password':secrets.token_urlsafe(24)}
        status,registered=request('/api/auth/register',credentials)
        assert status==200,'Docker PostgreSQL registration failed'
        uid=registered['user']['id']
        assert request('/api/auth/onboarding',{})[0]==200
        status,listing=request('/api/projects')
        assert status==200 and len(listing['projects'])==4 and sum(p['building_count'] for p in listing['projects'])==8
        pid=next(p['id'] for p in listing['projects'] if p['name']=='Bağımsız ofis')
        query='?'+urlencode({'project_id':pid})
        status,snapshot=request('/api/campus/snapshot'+query);assert status==200
        campus=snapshot['campus']
        status,saved=request('/api/campus'+query,{'revision':campus['revision'],'buildings':campus['buildings'],
            'scenario':campus['scenario'],'name':'Container PostgreSQL private QA'},method='PUT')
        assert status==200 and saved['campus']['revision']==campus['revision']+1
        status,result=request('/api/calculate'+query,{'revision':saved['campus']['revision'],'mode':'A','time_limit_s':5})
        assert status==200 and result['after'],'Docker PostgreSQL calculation failed'
        export_query='?'+urlencode({'project_id':pid,'scope':'result','revision':saved['campus']['revision'],'expected_calculation_id':result['calculation_id']})
        status,exported=request('/api/export/json'+export_query)
        assert status==200 and exported['calculation']['calculation_id']==result['calculation_id']
        inspection=docker('exec',name,'python','-c',
            "from pathlib import Path; p=Path('/app/backend'); assert not (p/'data').exists(); assert not (p/'.env').exists(); "
            "assert not list(p.rglob('*.sqlite3*')); assert (p/'db_migrations/001_initial.sql').is_file(); "
            "assert all((p/'ml_assets'/n/'model.joblib').is_file() for n in ('comstock-small','synthetic-annual')); print('verified')")
        assert inspection=='verified'
        docker('stop','--time','5',name);docker('rm','--volumes',name);created=False
        next_boot=launch()  # New process/container, same DATABASE_URL, no data volume.
        assert first_boot['boot_id']!=next_boot['boot_id'],'API process was not replaced'
        status,session=request('/api/auth/session')
        assert status==200 and session['user']['id']==uid and session['user']['onboarding_version']==1
        status,restored=request('/api/campus/snapshot'+query)
        assert status==200 and restored['campus']==saved['campus'] and restored['calculation_id']==result['calculation_id']
        old_cookie=cookie
        assert request('/api/auth/logout',{})[0]==200
        assert request('/api/projects',use_cookie=old_cookie)[0]==401
        assert request('/api/auth/login',{**credentials,'password':'incorrect-test-password'})[0]==401
        status,logged_in=request('/api/auth/login',credentials)
        assert status==200 and logged_in['user']['id']==uid
        return {'completed':True,'startup_migration_on_empty_database':True,'custom_port':True,
            'registration_login_logout_revocation':True,'four_projects_eight_buildings':True,
            'input_revision_calculation_export_preserved_across_new_container':True,
            'different_process_boot_verified':True,
            'no_user_data_volume_or_local_sqlite_json':True,'live_neon_tls_tested':False}
    finally:
        if created:docker('rm','--force','--volumes',name)


if __name__ == '__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--docker-api',metavar='IMAGE',help='Also exercise the actual Docker CMD/PORT and restart against PostgreSQL')
    args=parser.parse_args()
    container = 'portfolio25-pg-qa-' + secrets.token_hex(5)
    password = secrets.token_urlsafe(28)
    report = {'database':'real PostgreSQL in isolated Docker', 'production_tested':False,
              'llm_called':False,'model_trained':False,'completed':False}
    created = False
    try:
        with tempfile.TemporaryDirectory() as temp:
            envfile = Path(temp) / 'qa.env'
            with envfile.open('x', encoding='utf-8') as stream:
                envfile.chmod(0o600)
                stream.write(f'POSTGRES_USER=qa\nPOSTGRES_PASSWORD={password}\nPOSTGRES_DB=portfolio25qa\n')
            # Docker can allocate a different random published port on stop/start.
            # Reserve an available loopback port and explicitly bind it so outage
            # tests really reconnect to the same service address.
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0))
                port=probe.getsockname()[1]
            with socket.socket() as probe:
                probe.bind(('127.0.0.1',0))
                api_port=probe.getsockname()[1]
            publications=['--publish',f'127.0.0.1:{port}:5432']
            if args.docker_api:publications+=['--publish',f'127.0.0.1:{api_port}:18463']
            docker('run','--detach','--name',container,'--memory','384m',
                   *publications,'--env-file',str(envfile),'postgres:16-alpine')
            created = True
            binding = docker('port',container,'5432/tcp')
            port = int(binding.rsplit(':',1)[1])
            deadline=time.monotonic()+60
            while subprocess.run(['docker','exec',container,'pg_isready','-U','qa'],capture_output=True).returncode:
                if time.monotonic()>deadline:raise RuntimeError('PostgreSQL QA startup timed out')
                time.sleep(1)
            if args.docker_api:
                report['docker_application']=deployment_smoke(args.docker_api,container,password,api_port,temp)
            os.environ['TEST_DATABASE_URL']=f'postgresql://qa:{password}@127.0.0.1:{port}/portfolio25qa?sslmode=disable'
            os.environ['TEST_POSTGRES_CONTAINER']=container
            # Do not import production storage selection from a local .env.
            os.environ['STORAGE_BACKEND']='sqlite'
            os.environ['DATABASE_URL']=''
            suite=unittest.defaultTestLoader.discover(str(ROOT/'backend'),pattern='test_postgres.py')
            result=unittest.TextTestRunner(verbosity=2).run(suite)
            report.update(tests_run=result.testsRun,failures=len(result.failures),errors=len(result.errors),completed=result.wasSuccessful())
            report['version']=docker('exec',container,'psql','-U','qa','-d','portfolio25qa','-Atc','SELECT version()')
    finally:
        if created:
            # Only this uniquely named, isolated QA container/anonymous volume.
            docker('rm','--force','--volumes',container)
        output=ROOT/'artifacts/postgres-acceptance'
        output.mkdir(parents=True,exist_ok=True)
        (output/'report.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
        print(json.dumps(report),flush=True)
    raise SystemExit(0 if report['completed'] else 1)
