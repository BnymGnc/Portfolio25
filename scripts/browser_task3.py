"""Task 3 UI acceptance using a temporary private QA account. No paid AI calls."""
import hashlib,json,secrets,shutil,sqlite3,time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/task3-ui';OUT.mkdir(parents=True,exist_ok=True)
report={'checks':[],'screenshots':[],'first_data_positions':[]};uid=None
email='qa-task3-'+secrets.token_hex(4)+'@example.test';password=secrets.token_urlsafe(18)
original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend/data').rglob('*.json')}
options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--disable-gpu');options.add_argument('--window-size=1440,1000');options.page_load_strategy='eager';options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
d=webdriver.Chrome(options=options);d.set_page_load_timeout(45);d.set_script_timeout(60)
wait=WebDriverWait(d,60,ignored_exceptions=(StaleElementReferenceException,))
def css(selector):return d.find_element(By.CSS_SELECTOR,selector)
def button(text):return wait.until(lambda _:next((e for e in d.find_elements(By.XPATH,f'//button[contains(.,"{text}")]') if e.is_displayed() and e.is_enabled()),None))
def click(text):
    element=button(text);d.execute_script("arguments[0].scrollIntoView({block:'center'})",element);element.click()
def page(label):
    element=d.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]');element.click();wait.until(lambda _:element.get_attribute('aria-current')=='page')
def ready():wait.until(lambda _:d.find_elements(By.ID,'project-select') and css('#project-select').is_enabled() and d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))
def viewport(width):d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
def shot(name,at=None):
    d.execute_script("window.scrollTo(0,0)") if at is None else d.execute_script("arguments[0].scrollIntoView({block:'start'})",css(at))
    time.sleep(.15);d.save_screenshot(str(OUT/(name+'.png')));report['screenshots'].append(name+'.png')
def check(text):report['checks'].append(text);print('PASS:',text,flush=True)
def geometry(label,selector):
    d.execute_script('window.scrollTo(0,0)');width=d.execute_script('return innerWidth');y=d.execute_script('return arguments[0].getBoundingClientRect().top',css(selector))
    if not d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1'):
        report['overflow']=d.execute_script("return [...document.querySelectorAll('body *')].filter(e=>{let r=e.getBoundingClientRect();return r.width&&r.right>innerWidth+1&&!e.closest('.table-scroll,.chart-scroll,pre')}).map(e=>({tag:e.tagName,cls:String(e.className),right:e.getBoundingClientRect().right})).slice(0,20)")
        raise AssertionError((label,width,'horizontal overflow',report['overflow']))
    limit=350 if width>=1000 else 450
    report['first_data_positions'].append({'page':label,'width':width,'top':round(y,1),'limit':limit})
    assert y<=limit,(label,width,y,limit)
def account_menu(open=True):
    element=css('.account-menu')
    if bool(element.get_attribute('open'))!=open:element.find_element(By.TAG_NAME,'summary').click()
def api(path,body=None):
    return d.execute_async_script("""const [path,body,done]=arguments;import('/src/api.ts').then(async a=>{const r=await fetch(a.API_BASE+path,{credentials:'include',method:body===null?'GET':'POST',headers:{'Content-Type':'application/json','X-CSRF-Token':a.getCSRF()},body:body===null?undefined:JSON.stringify(body)});done({status:r.status,body:await r.json()})}).catch(e=>done({error:String(e)}))""",path,body)
try:
    d.get('http://127.0.0.1:5173');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-card'))
    assert 'En az 12' not in css('.auth-card').text
    for width in (390,768,1440):
        viewport(width);shot('login-'+str(width));card=css('.auth-card').rect;assert card['width']<=440
        assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
    click('Kayıt olun');assert 'En az 12' in css('.auth-card').text
    css('#auth-email').send_keys(email);css('#auth-password').send_keys(password)
    css('button[aria-label="Parolayı göster"]').click();assert css('#auth-password').get_attribute('type')=='text';css('button[aria-label="Parolayı gizle"]').click();assert css('#auth-password').get_attribute('type')=='password'
    shot('register-1440');css('#auth-password').send_keys(Keys.ENTER)
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog.onboarding[open]'));uid=api('/api/auth/session')['body']['user']['id']
    assert not d.find_elements(By.ID,'project-select'),'Unloaded project should not be behind onboarding'
    shot('onboarding-1440');click('İleri');click('İleri');click('Geri');click('İleri');click('İleri');click('Projeyi aç');ready()
    check('Compact auth, registration, password toggle, Enter submission, onboarding without false 0-building background')
    projects=api('/api/projects')['body']['projects'];campus=next(p for p in projects if p['building_count']==4);housing=next(p for p in projects if p['building_count']==2);office=next(p for p in projects if p['name']=='Bağımsız ofis')
    def project(p):
        Select(css('#project-select')).select_by_value(p['id']);ready();wait.until(lambda _:css('#project-select').get_attribute('value')==p['id']);time.sleep(.15)
    project(campus)
    for width in (390,768,1440):viewport(width);geometry('overview','.metric-value');shot('overview-'+str(width))
    page('Bina detayları')
    for index in (0,1):
        select=Select(css('#building-select'));name=select.options[index].text;select.select_by_index(index);wait.until(lambda _:css('.page-heading h1').text==name);wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody tr'));shot('building-'+str(index+1)+'-1440')
    for width in (390,768,1440):
        viewport(width);geometry('building','.mini-metrics strong');shot('building-'+str(width));shot('floors-'+str(width),'.spatial-detail')
        click('Enerji Dağılımı');shot('end-use-'+str(width),'.spatial-detail');click('Katlar')
    viewport(1440)
    for theme in ('nature','night','earth'):
        account_menu();Select(css('#theme-select')).select_by_value(theme);account_menu(False);shot('theme-'+theme)
    d.refresh();ready();assert d.execute_script('return document.documentElement.dataset.theme')=='earth'
    check('Independent project/building context, first data positions and three themes persist on reload')
    project(housing);page('Bina detayları')
    for index in (0,1):
        select=Select(css('#building-select'));name=select.options[index].text;select.select_by_index(index);wait.until(lambda _:css('.page-heading h1').text==name)
    project(office);page('Bina detayları');assert d.find_elements(By.CSS_SELECTOR,'.single-building')
    # Recoverable read error: block only the QA browser's package requests.
    d.execute_cdp_cmd('Network.enable',{});d.execute_cdp_cmd('Network.setBlockedURLs',{'urls':['*api/buildings/B07/packages*']})
    page('Proje özeti');page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-panel .error-box'));shot('recoverable-package-error','.package-panel')
    d.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[]});click('Tekrar dene');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'))
    check('Housing A/B and single office; failed package request keeps application usable and retries')
    page('Senaryo girdileri')
    for width in (390,768,1440):viewport(width);geometry('scenario','input[name=budget_try]');shot('scenario-'+str(width))
    # Unsaved draft must survive attempted navigation and refresh.
    budget=css('input[name=budget_try]');initial=budget.get_attribute('value');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('2900000')
    d.find_element(By.XPATH,'//nav/button[contains(.,"Proje özeti")]').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open]'));click('Kal');assert budget.get_attribute('value')=='2900000'
    account_menu();click('Veriyi yenile');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open]'));click('Kal');account_menu(False);assert budget.get_attribute('value')=='2900000'
    click('Girdileri kaydet');wait.until(lambda _:not css('.scenario-panel form button').is_enabled());click('Yatırım planını hesapla')
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.result-metrics'));assert not d.find_elements(By.CSS_SELECTOR,'.inline-notice');assert not d.find_elements(By.CSS_SELECTOR,'.toast')
    assert not d.find_elements(By.CSS_SELECTOR,'.stale-panel');check('Draft retained by navigation/refresh guard; successful solve clears saved-input notice and stale state')
    for width in (390,768,1440):
        viewport(width);geometry('results','.decision-summary h2');shot('results-'+str(width));wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.chart-panel svg'));shot('load-chart-'+str(width),'.chart-panel');shot('investment-plan-'+str(width),'.selected-plan')
    viewport(1440);page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction select') and css('.synthetic-prediction button').is_enabled())
    select=Select(css('.synthetic-prediction select'));select.select_by_index(len(select.options)-1);click('ML ve fizik sonucunu karşılaştır')
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction>.table-scroll'));combined=css('.synthetic-prediction>.table-scroll').text
    assert 'Tahmin sunulmadı' not in combined;assert 'Göreli fark' in combined;assert d.find_elements(By.CSS_SELECTOR,'.ml-large-gap')
    for width in (390,768,1440):viewport(width);shot('ml-'+str(width),'.synthetic-prediction');assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
    viewport(1440);Select(css('.synthetic-prediction select')).select_by_index(0);click('ML ve fizik sonucunu karşılaştır');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction>.table-scroll') and css('.synthetic-prediction>.table-scroll').text!=combined)
    check('Actual ML changes with intervention; total-gas scope, large absolute/relative difference and limitation are visible')
    page('Senaryo girdileri');budget=css('input[name=budget_try]');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('0');target=css('input[name=savings_target_pct]');target.send_keys(Keys.CONTROL,'a');target.send_keys('100');css('input[name=mode][value=B]').click();click('Yatırım planını hesapla');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.no-solution'));shot('no-solution-1440');assert 'Çözüm bulunamadı' in css('.result-statusline').text
    check('Infeasible budget/target is displayed without a fabricated plan')
    account_menu();click('Kısa tanıtım');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog.onboarding[open]'));css('dialog.onboarding').send_keys(Keys.ESCAPE);ready()
    account_menu();click('Çıkış yap');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-card'));assert 'En az 12' not in css('.auth-card').text
    css('#auth-email').send_keys(Keys.CONTROL,'a');css('#auth-email').send_keys(email);css('#auth-password').send_keys('wrong-password-123');css('#auth-password').send_keys(Keys.ENTER);wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-error'));shot('login-error')
    css('#auth-password').send_keys(Keys.CONTROL,'a');css('#auth-password').send_keys(password);css('#auth-password').send_keys(Keys.ENTER);ready();assert not d.find_elements(By.CSS_SELECTOR,'dialog.onboarding')
    check('Replay/Escape, logout, useful login error and relogin without onboarding repeat')
    report['console_uncaught']=[e for e in d.get_log('browser') if 'Uncaught' in e['message']];assert not report['console_uncaught']
    report['completed']=True
finally:
    try:shot('last-state')
    except Exception:pass
    d.quit()
    if uid:
        db=sqlite3.connect(ROOT/'backend/data/accounts.sqlite3');row=db.execute('SELECT email FROM users WHERE id=?',(uid,)).fetchone()
        if row and row[0]==email:
            # The backend records the same timestamp for the email and IP attempt.
            # Remove only this QA identity's paired attempts, preserving other users.
            bucket='email:'+hashlib.sha256(email.encode()).hexdigest()
            moments=[r[0] for r in db.execute('SELECT moment FROM attempts WHERE bucket=?',(bucket,))]
            db.executemany('DELETE FROM attempts WHERE moment=? AND (bucket=? OR bucket=?)',[(moment,bucket,'ip:127.0.0.1') for moment in moments])
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,));db.execute('DELETE FROM users WHERE id=?',(uid,));db.commit()
            parent=(ROOT/'backend/data/users').resolve();target=(parent/uid).resolve();assert target.parent==parent and len(uid)==32
            if target.exists():shutil.copytree(target,OUT/'temporary-account-records',dirs_exist_ok=True);shutil.rmtree(target)
        db.close()
    report['original_records_preserved']=all(Path(p).exists() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original.items());assert report['original_records_preserved']
    (OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
