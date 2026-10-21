"""Exercise the built Linux image with isolated bind-mounted data, never user records.

Run after: docker build -t portfolio25-api:deploy-check .
The HTTPS Origin models the frontend; local container transport is HTTP. This is
not a claim that a live Render/Vercel HTTPS deployment has been tested.
"""
import hashlib
import json
import subprocess
import tempfile
import time
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from uuid import uuid4

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'artifacts' / 'docker-deployment'
OUT.mkdir(parents=True, exist_ok=True)
IMAGE = 'portfolio25-api:deploy-check'
ORIGIN = 'https://frontend.example.test'


def docker(*args):
    return subprocess.check_output(['docker', *args], text=True, encoding='utf-8').strip()


def main():
    name = 'portfolio25-deploy-qa-' + uuid4().hex[:12]
    data = Path(tempfile.mkdtemp(prefix='data-', dir=OUT)).resolve()
    report = {'image': IMAGE, 'checks': [], 'live_cloud_verified': False}
    cookie = ''; csrf = ''; base = ''

    def check(message):
        report['checks'].append(message)
        print('PASS:', message, flush=True)

    def launch():
        nonlocal base
        docker('run', '-d', '--name', name, '--memory', '768m', '--cpus', '2',
               '--mount', f'type=bind,source={data},target=/var/data',
               '-e', 'PORT=18463', '-e', f'FRONTEND_ORIGINS={ORIGIN}',
               '-p', '127.0.0.1::18463', IMAGE)
        port = docker('port', name, '18463/tcp').rsplit(':', 1)[1]
        base = 'http://127.0.0.1:' + port
        for _ in range(60):
            try:
                with urlopen(base + '/api/health', timeout=2) as r:
                    assert r.status == 200
                    return
            except (URLError, TimeoutError, ConnectionError):
                time.sleep(.5)
        raise RuntimeError('QA container did not become healthy.')

    def request(path, body=None, method=None, origin=ORIGIN, token=None):
        nonlocal cookie, csrf
        headers = {'Origin': origin, 'Content-Type': 'application/json'}
        if cookie: headers['Cookie'] = cookie
        if csrf or token: headers['X-CSRF-Token'] = csrf if token is None else token
        req = Request(base + path, data=json.dumps(body).encode() if body is not None else None,
                      method=method, headers=headers)
        try: response = urlopen(req, timeout=90)
        except HTTPError as error: response = error
        with response:
            value = json.load(response)
            received = response.headers.get('set-cookie')
            if received:
                assert all(flag in received for flag in ('HttpOnly', 'Secure', 'SameSite=lax', 'Path=/'))
                assert 'Domain=' not in received
                cookie = received.split(';', 1)[0]
            if value.get('csrf'): csrf = value['csrf']
            assert 'no-store' in response.headers.get('cache-control', '')
            return response.status, value

    try:
        launch()
        assert not list(data.iterdir()), 'Health created user/data files'
        check('Linux image binds 0.0.0.0 on custom PORT; unauthenticated health does not initialize data')
        inspection = docker('exec', name, 'python', '-c',
            "from pathlib import Path; import json; p=Path('/app/backend'); "
            "assert not (p/'.env').exists(); assert not (p/'data').exists(); "
            "assert not list(p.rglob('*.sqlite3*')); assert not list(p.glob('test*.py')); "
            "assert not Path('/app/artifacts').exists(); "
            "assert all((p/'ml_assets'/s/'model.joblib').exists() for s in ('comstock-small','synthetic-annual')); "
            "print('Runtime files and both trained models verified')")
        check(inspection)
        assert request('/api/projects')[0] == 401
        assert request('/api/auth/session')[0] == 200
        status, value = request('/api/auth/register', {'email':'container-qa@example.test',
                                                      'password':'temporary-container-test-password'})
        assert status == 200, (status, value)
        uid = value['user']['id']
        assert request('/api/auth/onboarding', {}, origin='https://wrong.invalid')[0] == 403
        assert request('/api/auth/onboarding', {}, token='wrong')[0] == 403
        assert request('/api/auth/onboarding', {})[0] == 200
        check('Secure host-only HttpOnly cookie, authentication, exact Origin and CSRF checks work in container')
        status, listing = request('/api/projects')
        assert status == 200 and len(listing['projects']) == 4
        assert sum(p['building_count'] for p in listing['projects']) == 8
        pid = next(p['id'] for p in listing['projects'] if p['name'] == 'Bağımsız ofis')
        query = '?project_id=' + pid
        status, snapshot = request('/api/campus/snapshot' + query)
        assert status == 200
        status, result = request('/api/calculate' + query, {'revision':snapshot['campus']['revision'], 'mode':'A', 'time_limit_s':5})
        assert status == 200 and result['after'], (status, result.get('detail'))
        check('Private four-project/eight-building pilot and real Linux SciPy optimization run')
        status, snapshot = request('/api/campus/snapshot' + query)
        bid = snapshot['campus']['buildings'][0]['id']
        status, packages = request('/api/buildings/' + bid + '/packages' + query)
        status, prediction = request('/api/ml/synthetic/predict' + query, {
            'context':snapshot['context'], 'building_id':bid,
            'candidate_id':packages['packages'][-1]['candidate_id']})
        assert status == 200 and prediction['prediction'], (status, prediction.get('messages'))
        assert request('/api/ml/status' + query)[1]['available']
        check('Packaged synthetic model performs real Linux inference; ComStock artifact remains available; no training or LLM call')
        result_id = result['calculation_id']
        before = {str(p.relative_to(data)):hashlib.sha256(p.read_bytes()).hexdigest()
                  for p in data.rglob('*.json')}
        docker('rm', '-f', name)
        launch()
        status, session = request('/api/auth/session')
        assert status == 200 and session['user']['id'] == uid and session['user']['onboarding_version'] == 1
        status, restored = request('/api/campus/snapshot' + query)
        assert status == 200 and restored['calculation_id'] == result_id
        assert all(hashlib.sha256((data/path).read_bytes()).hexdigest() == digest for path,digest in before.items())
        check('New container with the same mounted directory retains users, session, onboarding, projects and calculation without JSON mutation')
        old_cookie = cookie
        assert request('/api/auth/logout', {})[0] == 200
        cookie = old_cookie
        assert request('/api/projects')[0] == 401
        check('Revoked session remains invalid after logout')
    finally:
        # Only the uniquely named container created by this script is removed.
        subprocess.run(['docker','rm','-f',name], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        (OUT/'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')


if __name__ == '__main__':main()
