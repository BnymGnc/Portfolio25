"""Live Vercel -> Render acceptance with one isolated QA account.

Uses real HTTPS and Chrome. No .env reads, training, LLM calls or existing
project updates. The QA account remains because there is no account-delete API.
Credentials/session/CSRF are kept in memory and never printed or saved.
Requires Selenium and Chrome; run from repo root with system Python.
"""
import argparse
import json
import math
import secrets
import time
from datetime import datetime, timezone
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode, urlparse
from urllib.request import Request, urlopen

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

ORIGIN = 'https://buildingportfolio25.vercel.app'
BACKEND = 'https://portfolio25-api.onrender.com'
parser = argparse.ArgumentParser(description=__doc__)
parser.add_argument('--expected-asset', help='Wait for this built JS asset path in live HTML before registering QA')
args = parser.parse_args()
OUT = Path(__file__).resolve().parents[1] / 'artifacts/live-deployment'
OUT.mkdir(parents=True, exist_ok=True)
report = {'started_at': datetime.now(timezone.utc).isoformat(), 'origin': ORIGIN,
          'backend': BACKEND, 'checks': [], 'completed': False,
          'llm_called': False, 'training_started': False}


def check(message):
    report['checks'].append(message)
    print('PASS:', message, flush=True)


def http(path, *, base=ORIGIN, method='GET', body=None, headers=None):
    request = Request(base + path, method=method, headers=headers or {},
                      data=None if body is None else json.dumps(body).encode())
    try:
        response = urlopen(request, timeout=30)
    except HTTPError as error:
        response = error
    with response:
        raw = response.read()
        try:
            value = json.loads(raw)
        except (ValueError, UnicodeDecodeError):
            value = None
        return response.status, response.headers, value


driver = None
try:
    status, _, health = http('/api/health', base=BACKEND)
    assert status == 200 and health['status'] == 'ok'
    report['backend_health'] = health
    check('Render public /api/health is JSON 200; readiness remains explicitly not_checked')

    # A first push can still be building. Poll health without registering users.
    deadline = time.monotonic() + 600
    last = None
    while True:
        try:
            status, headers, health = http('/api/health?qa=' + secrets.token_hex(4))
            last = status
            if status == 200 and isinstance(health, dict) and health.get('status') == 'ok':
                if args.expected_asset:
                    with urlopen(ORIGIN + '/?qa=' + secrets.token_hex(4), timeout=30) as page:
                        asset_ready = args.expected_asset in page.read().decode('utf-8')
                    if asset_ready:
                        break
                    last = 'waiting-for-new-frontend-asset'
                else:
                    break
        except (URLError, TimeoutError):
            last = 'unreachable'
        if time.monotonic() >= deadline:
            raise AssertionError('Vercel rewrite did not become healthy within 10 minutes; last=' + str(last))
        print('Waiting for Vercel API deployment; health status:', last, flush=True)
        time.sleep(10)
    report['frontend_health'] = health
    assert 'application/json' in headers.get('content-type', '')
    assert 'no-store' in headers.get('cache-control', '')
    check('Vercel same-origin /api/health reaches backend JSON with no-store')
    status, headers, body = http('/api/not-a-real-route')
    assert status in (401, 404) and isinstance(body, dict)
    assert 'application/json' in headers.get('content-type', '')
    status, headers, _ = http('/scenario')
    assert status == 200 and 'text/html' in headers.get('content-type', '')
    check('API failure is JSON, not SPA HTML; /scenario still receives SPA HTML')

    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1440,1000')
    options.set_capability('goog:loggingPrefs', {'browser': 'ALL', 'performance': 'ALL'})
    driver = webdriver.Chrome(options=options)
    driver.set_page_load_timeout(60)
    driver.set_script_timeout(100)
    wait = WebDriverWait(driver, 120)
    csrf = ''
    email = 'qa-live-' + secrets.token_hex(6) + '@example.test'
    password = secrets.token_urlsafe(24)

    def css(selector):
        return driver.find_element(By.CSS_SELECTOR, selector)

    def click(label):
        element = wait.until(lambda _: next((e for e in driver.find_elements(By.TAG_NAME, 'button')
                                            if label in e.text and e.is_displayed() and e.is_enabled()), None))
        driver.execute_script("arguments[0].scrollIntoView({block:'center'})", element)
        element.click()

    def browser_request(path, body=None, token=None):
        return driver.execute_async_script("""
          const [path,body,token,done]=arguments;
          fetch(path,{method:body===null?'GET':'POST',credentials:'include',
            headers:{'Content-Type':'application/json','X-CSRF-Token':token},
            body:body===null?undefined:JSON.stringify(body),signal:AbortSignal.timeout(90000)})
          .then(async r=>{
            let value;try{value=await r.json()}catch{done({status:r.status,error:'non_json_response'});return}
            done({status:r.status,type:r.headers.get('content-type'),cache:r.headers.get('cache-control'),body:value})
          })
          .catch(e=>done({error:e.name==='TimeoutError'?'request_timeout':'browser_request_failed'}));
        """, path, body, csrf if token is None else token)

    def api(path, body=None, token=None):
        response = browser_request(path, body, token)
        # Only read requests may retry once; never repeat registrations/calculations.
        if body is None and (response.get('error') or response.get('status') in (502, 503, 504)):
            failure = {'path': urlparse(path).path, 'status': response.get('status'), 'error': response.get('error')}
            report.setdefault('transient_read_failures', []).append(failure)
            print('Transient read failure:', failure, flush=True)
            time.sleep(2)
            response = browser_request(path)
        if response.get('error'):
            report['last_request_error'] = {'path': urlparse(path).path, 'status': response.get('status'), 'error': response['error']}
        return response

    driver.get(ORIGIN)
    wait.until(lambda _: driver.find_elements(By.CSS_SELECTOR, '.auth-card'))
    click('Kayıt olun')
    css('#auth-email').send_keys(email)
    css('#auth-password').send_keys(password, Keys.ENTER)
    wait.until(lambda _: driver.find_elements(By.CSS_SELECTOR, 'dialog.onboarding[open]')
               or driver.find_elements(By.CSS_SELECTOR, '.auth-error'))
    assert not driver.find_elements(By.CSS_SELECTOR, '.auth-error'), 'Live registration rejected; check allowed Origin/CSRF/configuration'
    report['qa_account_created'] = True
    click('Tanıtımı atla')
    wait.until(lambda _: driver.find_elements(By.ID, 'project-select') and css('#project-select').is_enabled())
    boot = api('/api/auth/session')
    assert boot['status'] == 200 and boot['body']['user']
    csrf = boot['body']['csrf']
    user_id = boot['body']['user']['id']
    cookie = driver.get_cookie('portfolio25_session')
    assert cookie and cookie['secure'] and cookie['httpOnly']
    assert cookie['sameSite'].lower() == 'lax' and cookie['path'] == '/'
    assert cookie['domain'] == urlparse(ORIGIN).hostname
    report['cookie_flags'] = {key: cookie[key] for key in ('secure', 'httpOnly', 'sameSite', 'path', 'domain')}
    check('Real browser registration and onboarding succeed through Vercel; Secure/HttpOnly/Lax host-only cookie is retained')
    assert api('/api/auth/onboarding', {}, token='deliberately-wrong')['status'] == 403
    bad_status, _, _ = http('/api/auth/onboarding', method='POST', body={}, headers={
        'Origin': 'https://not-allowed.example', 'Content-Type': 'application/json',
        'Cookie': 'portfolio25_session=' + cookie['value'], 'X-CSRF-Token': csrf})
    assert bad_status == 403
    check('Wrong CSRF and wrong Origin are rejected with 403; valid Vercel Origin works')

    projects_response = api('/api/projects')
    assert projects_response['status'] == 200 and 'no-store' in projects_response['cache']
    projects = projects_response['body']['projects']
    assert len(projects) == 4 and sum(p['building_count'] for p in projects) == 8
    office = next(p for p in projects if p['building_count'] == 1 and 'ofis' in p['name'].lower())
    project_id = office['id']
    query = '?' + urlencode({'project_id': project_id})
    snapshot = api('/api/campus/snapshot' + query)
    assert snapshot['status'] == 200 and snapshot['body']['campus']['id'] == project_id
    report['project_count'] = len(projects)
    report['building_count'] = sum(p['building_count'] for p in projects)
    check('Four private projects/eight buildings load; project_id query reaches the correct office snapshot')

    Select(css('#project-select')).select_by_value(project_id)
    wait.until(lambda _: css('#project-select').is_enabled() and driver.find_elements(By.CSS_SELECTOR, '.inventory-panel tbody tr'))
    click('Senaryo girdileri')
    click('Yatırım planını hesapla')
    wait.until(lambda _: driver.find_elements(By.CSS_SELECTOR, '.result-metrics')
               or driver.find_elements(By.CSS_SELECTOR, '.no-solution')
               or driver.find_elements(By.CSS_SELECTOR, 'main>.error-box'))
    assert driver.find_elements(By.CSS_SELECTOR, '.result-metrics'), 'No feasible live result rendered'
    snapshot = api('/api/campus/snapshot' + query)
    assert snapshot['status'] == 200
    snapshot = snapshot['body']
    result = snapshot['calculation']
    assert result['status'] in ('optimal', 'feasible_limit') and result['after']
    assert result['project_id'] == project_id
    assert result['calculation_id'] == snapshot['calculation_id']
    assert result['input_revision'] == snapshot['campus']['revision']
    report['calculation'] = {k: result[k] for k in ('status', 'investment_try', 'energy_savings_kwh_year', 'net_savings_try_year', 'engine_version')}
    driver.save_screenshot(str(OUT / 'live-result.png'))
    check('Live browser computes a real office MILP and renders a revision/calculation-matched result')
    profile_query = '?' + urlencode({'project_id': project_id, 'expected_calculation_id': result['calculation_id']})
    profiles = api('/api/campus/profiles' + profile_query)
    assert profiles['status'] == 200
    assert profiles['body']['calculation_id'] == result['calculation_id']
    assert len(profiles['body']['timestamps']) == 8760
    assert profiles['body']['after_kw'] is not None
    check('Hourly profiles retain project and expected_calculation_id query parameters and 8760 aligned hours')

    building_id = snapshot['campus']['buildings'][0]['id']
    packages = api('/api/buildings/' + building_id + '/packages' + query)
    assert packages['status'] == 200
    candidate = next(p for p in packages['body']['packages'] if p['package'] == 'combined')
    ml = api('/api/ml/synthetic/predict' + query, {'context': snapshot['context'],
              'building_id': building_id, 'candidate_id': candidate.get('candidate_id') or candidate['package']})
    assert ml['status'] == 200 and ml['body']['status'] == 'available'
    prediction = ml['body']
    assert prediction['base_context'] == snapshot['context']
    assert all(math.isfinite(prediction['prediction'][k]) for k in ('electricity_kwh_year', 'gas_kwh_year'))
    report['ml'] = {k: prediction[k] for k in ('status', 'model_version', 'prediction')}
    check('Deployed model performs actual synthetic annual inference through same-origin /api; physics context matches')

    api_requests = [json.loads(item['message'])['message'] for item in driver.get_log('performance')]
    api_urls = [item['params']['request']['url'] for item in api_requests
                if item['method'] == 'Network.requestWillBeSent'
                and '/api/' in item['params']['request']['url']]
    assert api_urls and all(urlparse(url).netloc == urlparse(ORIGIN).netloc for url in api_urls)
    report['browser_api_paths'] = sorted(set(urlparse(url).path for url in api_urls))
    check('All observed browser API requests stay on the Vercel origin, without a direct Render request')

    css('.account-menu>summary').click()
    click('Çıkış yap')
    wait.until(lambda _: driver.find_elements(By.CSS_SELECTOR, '.auth-card'))
    wait.until(lambda _: css('#auth-title').text == 'Projenize giriş yapın')
    status, _, _ = http('/api/projects', headers={'Cookie': 'portfolio25_session=' + cookie['value']})
    assert status == 401
    check('Browser logout clears access; old session cookie is rejected with 401')
    css('#auth-email').send_keys(Keys.CONTROL, 'a')
    css('#auth-email').send_keys(email)
    css('#auth-password').send_keys(password, Keys.ENTER)
    wait.until(lambda _: driver.find_elements(By.ID, 'project-select') and css('#project-select').is_enabled()
               or driver.find_elements(By.CSS_SELECTOR, '.auth-error'))
    assert not driver.find_elements(By.CSS_SELECTOR, '.auth-error'), 'Live login rejected'
    session = api('/api/auth/session')
    assert session['body']['user']['id'] == user_id
    csrf = session['body']['csrf']
    again = api('/api/campus/snapshot' + query)
    assert again['status'] == 200 and again['body']['calculation_id'] == result['calculation_id']
    assert session['body']['user']['onboarding_version'] == 1
    check('Real browser login restores the same private project/result and completed onboarding')
    assert api('/api/auth/logout', {})['status'] == 200
    errors = [entry for entry in driver.get_log('browser') if 'Uncaught' in entry['message']]
    report['uncaught_browser_error_count'] = len(errors)
    assert not errors
    report['completed'] = True
except Exception as error:
    # Never dump driver page source, credential payloads or auth headers.
    report['failure_type'] = type(error).__name__
    print('FAIL:', type(error).__name__, 'See the last completed check in the report.', flush=True)
    raise
finally:
    if driver:
        try:
            driver.save_screenshot(str(OUT / 'last-state.png'))
        except Exception:
            report['final_screenshot_available'] = False
        finally:
            try:
                driver.quit()
            except Exception:
                report['browser_close_failed'] = True
    report['finished_at'] = datetime.now(timezone.utc).isoformat()
    report['qa_account_retained'] = report.get('qa_account_created', False)
    (OUT / 'report.json').write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
