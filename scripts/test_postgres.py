"""Run real PostgreSQL integration tests in an isolated local Docker container.

No production credentials, .env, unrelated containers, training or LLM calls.
The random database password is never printed; temporary files are removed.
"""
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

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'backend'))


def docker(*args):
    result = subprocess.run(['docker', *args], capture_output=True, text=True, timeout=120)
    if result.returncode:
        raise RuntimeError('Docker QA operation failed; check Docker Desktop and the postgres:16-alpine image.')
    return result.stdout.strip()


if __name__ == '__main__':
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
            docker('run','--detach','--name',container,'--memory','384m',
                   '--publish',f'127.0.0.1:{port}:5432','--env-file',str(envfile),'postgres:16-alpine')
            created = True
            binding = docker('port',container,'5432/tcp')
            port = int(binding.rsplit(':',1)[1])
            deadline=time.monotonic()+60
            while subprocess.run(['docker','exec',container,'pg_isready','-U','qa'],capture_output=True).returncode:
                if time.monotonic()>deadline:raise RuntimeError('PostgreSQL QA startup timed out')
                time.sleep(1)
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
