"""Real browser acceptance with a temporary new account; no existing project edits."""
import json,time,secrets,sqlite3,shutil,hashlib
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait,Select
from selenium.common.exceptions import StaleElementReferenceException
ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/final-delivery';OUT.mkdir(parents=True,exist_ok=True)
report={'checks':[],'screenshots':[]};uid=None
email='qa-'+secrets.token_hex(5)+'@example.test';password=secrets.token_urlsafe(20)
original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend/data').rglob('*.json')}
options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--disable-gpu');options.add_argument('--window-size=1536,1100');options.set_capability('goog:loggingPrefs',{'browser':'ALL'});options.page_load_strategy='eager'
driver=webdriver.Chrome(options=options);driver.set_page_load_timeout(45);driver.set_script_timeout(45);wait=WebDriverWait(driver,45,ignored_exceptions=(StaleElementReferenceException,));d=driver
def css(s):return d.find_element(By.CSS_SELECTOR,s)
def click_text(text):
    element=wait.until(lambda _:next((e for e in d.find_elements(By.XPATH,f'//button[contains(.,"{text}")]') if e.is_displayed() and e.is_enabled()),None));d.execute_script("arguments[0].scrollIntoView({block:'center'})",element);element.click()
def check(label):report['checks'].append(label);print('PASS',label,flush=True)
def ready():wait.until(lambda _:d.find_elements(By.ID,'project-select') and css('#project-select').is_enabled() and d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))
def shot(name,selector=None):
    if selector:d.execute_script("arguments[0].scrollIntoView({block:'start'})",css(selector));css(selector).screenshot(str(OUT/(name+'.png')))
    else:d.execute_script('window.scrollTo(0,0)');d.save_screenshot(str(OUT/(name+'.png')))
    report['screenshots'].append(name+'.png')
def viewport(width):d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
def page(text):
    button=wait.until(lambda _:d.find_element(By.XPATH,f'//nav/button[contains(.,"{text}")]'));d.execute_script("arguments[0].scrollIntoView({block:'center'})",button);button.click();wait.until(lambda _:button.get_attribute('aria-current')=='page')
def api(path,body=None):
    return d.execute_async_script("""const [path,body,done]=arguments;import('/src/api.ts').then(async a=>{const r=await fetch(a.API_BASE+path,{method:body===null?'GET':'POST',credentials:'include',headers:{'Content-Type':'application/json','X-CSRF-Token':a.getCSRF()},body:body===null?undefined:JSON.stringify(body)});done({status:r.status,body:await r.json()})}).catch(e=>done({error:String(e)}));""",path,body)
try:
    print('Opening frontend',flush=True);d.get('http://127.0.0.1:5173');print('Page loaded',flush=True);wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-card'));print('Login visible',flush=True);shot('login')
    click_text('Kayıt olun');css('input[type=email]').send_keys(email);css('input[type=password]').send_keys(password);click_text('Kayıt ol ve pilotu aç')
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.onboarding'));uid=api('/api/auth/session')['body']['user']['id'];shot('onboarding')
    for _ in range(3):click_text('İleri')
    click_text('Başla');ready();uid=api('/api/auth/session')['body']['user']['id'];check('UI registration, four-step onboarding and authenticated pilot')
    projects=api('/api/projects')['body']['projects'];assert len(projects)==4 and sum(p['building_count'] for p in projects)==8
    campus=next(p for p in projects if p['building_count']==4);housing=next(p for p in projects if p['building_count']==2);office=next(p for p in projects if 'ofis' in p['name'].lower())
    def select_project(p):
        Select(css('#project-select')).select_by_value(p['id']);wait.until(lambda _:css('#project-select').is_enabled() and css('#project-select').get_attribute('value')==p['id']);time.sleep(.4)
    select_project(campus);page('Bina detayları')
    for i in range(2):
        select=Select(css('#building-select'));option=select.options[i];name=option.text;select.select_by_index(i);wait.until(lambda _:css('.detail-header h2').text==name);wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'));shot('building-'+str(i+1));check('Building context '+name)
    for theme in ('nature','night','earth'):
        Select(css('#theme-select')).select_by_value(theme);time.sleep(.3);shot('desktop-'+theme)
    d.refresh();ready();assert d.execute_script('return document.documentElement.dataset.theme')=='earth';check('Three themes and persisted preference')
    select_project(housing);page('Bina detayları')
    for i in range(2):
        select=Select(css('#building-select'));name=select.options[i].text;select.select_by_index(i);wait.until(lambda _:css('.detail-header h2').text==name)
    check('Housing independent block navigation')
    for width in (390,768,1280,1536):
        viewport(width);time.sleep(.2);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth'),width
        if width==390:shot('mobile-building')
    check('No document overflow at 390 / 768 / 1280 / 1536')
    select_project(office);page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.single-building'));check('Single-building office')
    click_text('Müdahale Senaryoları');click_text('Düzenlenebilir sentetik varsayımlar') if False else None
    # A blank numeric input is preserved and rejected, not converted to zero.
    details=css('.spatial-controls details');d.execute_script('arguments[0].open=true',details)
    numeric=css('input[aria-label="Çatı hedef U (W/m²K)"]');numeric.send_keys(Keys.CONTROL,'a');numeric.send_keys(Keys.BACKSPACE)
    click_text('Önce / sonra etkisini hesapla');assert numeric.get_attribute('value')=='';wait.until(lambda _:'Sayısal alanları' in css('.spatial-detail').text)
    numeric.send_keys('0.35');click_text('Portföy kararlarını ve varsayımları kaydet');wait.until(lambda _:not css('.spatial-controls').get_attribute('disabled') and not css('.spatial-save').is_enabled());time.sleep(.2);check('Blank numeric rejected and recoverable save')
    page('Senaryo girdileri');shot('scenario');click_text('Yatırım planını hesapla');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.solver-banner'));shot('results');check('Real optimization and result rendering')
    page('Senaryo girdileri')
    details=css('.alternative-scenario details');d.execute_script('arguments[0].open=true',details)
    budget=css('.alternative-scenario input[type=number]');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('3100000');click_text('Manuel taslak oluştur');click_text('Kaydetmeden hesapla')
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.apply-alternative') and css('.apply-alternative').is_enabled());click_text('Bu senaryoyu uygula')
    wait.until(lambda _:css('input[name="budget_try"]').get_attribute('value')=='3100000');check('Temporary scenario applies and synchronizes main form')
    page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction select') and css('.synthetic-prediction button').is_enabled())
    click_text('ML ve fizik sonucunu karşılaştır');wait.until(lambda _:css('.synthetic-prediction select').is_enabled() and d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction > .table-scroll'))
    before=css('.synthetic-prediction > .table-scroll').text;assert 'Tahmin sunulmadı' not in before
    selector=Select(css('.synthetic-prediction select'));selector.select_by_index(len(selector.options)-1)
    click_text('ML ve fizik sonucunu karşılaştır');wait.until(lambda _:css('.synthetic-prediction select').is_enabled() and d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction > .table-scroll') and css('.synthetic-prediction > .table-scroll').text!=before)
    shot('ml-comparison','.synthetic-prediction');check('Intervention changes real synthetic inference and physical result')
    # Logout and login must not repeat onboarding or change project revisions.
    click_text('Çıkış yap');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-card'))
    css('input[type=email]').send_keys(Keys.CONTROL,'a');css('input[type=email]').send_keys(email);css('input[type=password]').send_keys(password);click_text('Giriş yap');ready();assert not d.find_elements(By.CSS_SELECTOR,'.onboarding');check('Logout/relogin and onboarding persistence')
    report['console_errors']=[entry for entry in d.get_log('browser') if entry['level']=='SEVERE']
    assert not [e for e in report['console_errors'] if 'Uncaught' in e['message']],report['console_errors']
finally:
    try:shot('last-state')
    except Exception:pass
    d.quit()
    if uid:
        # Remove only the account created by this run. Never traverse another user's directory.
        db=sqlite3.connect(ROOT/'backend/data/accounts.sqlite3')
        row=db.execute('SELECT email FROM users WHERE id=?',(uid,)).fetchone()
        if row and row[0]==email:
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,));db.execute('DELETE FROM users WHERE id=?',(uid,));db.commit()
            parent=(ROOT/'backend/data/users').resolve();target=(parent/uid).resolve()
            assert target.parent==parent and len(uid)==32
            if target.exists():shutil.copytree(target,OUT/'temporary-account-records',dirs_exist_ok=True);shutil.rmtree(target)
        db.close()
    assert all(Path(p).exists() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original.items()),'Existing user JSON changed'
    report['existing_records_preserved']=True
    (OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
