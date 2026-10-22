"""Task 3 UI acceptance using a temporary private QA account. No paid AI calls."""
import argparse,hashlib,json,secrets,shutil,sqlite3,time
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

ROOT=Path(__file__).resolve().parents[1]
parser=argparse.ArgumentParser(description=__doc__)
parser.add_argument('--data-dir',type=Path,default=ROOT/'backend/data',help='Must match the local test server DATA_FILE parent; never a production store.')
args=parser.parse_args();DATA=args.data_dir.resolve()
assert DATA.is_relative_to(ROOT.resolve()),'QA cleanup must stay inside this workspace'
OUT=ROOT/'artifacts/ui-review/acceptance';OUT.mkdir(parents=True,exist_ok=True)
DOWNLOADS=OUT/'downloads';DOWNLOADS.mkdir(exist_ok=True)
WIDTHS=(320,390,500,768,1280,1536)
report={'checks':[],'screenshots':[],'first_data_positions':[]};uid=None
email='qa-task3-'+secrets.token_hex(4)+'@example.test';password=secrets.token_urlsafe(18)
original={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in DATA.rglob('*.json')}
options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--disable-gpu');options.add_argument('--window-size=1440,1000');options.page_load_strategy='eager';options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
options.add_experimental_option('prefs',{'download.default_directory':str(DOWNLOADS),'download.prompt_for_download':False})
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
    if name not in {'login-390','login-1536','overview-390','overview-1536','building-1-1440','building-2-1440','floors-390','end-use-390','theme-nature','theme-night','theme-earth','scenario-390','scenario-1536','results-390','results-1536','load-chart-390','investment-plan-1536','settings-tr','ml-1440','no-solution-1440','last-state'}:return
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
    if not open:
        dialogs=d.find_elements(By.CSS_SELECTOR,'dialog[open] .dialog-top .icon-button')
        if dialogs:dialogs[0].click()
        return
    if css('.mobile-tools').is_displayed():click('Menü')
    click('Hesap')

def open_settings():
    if css('.mobile-tools').is_displayed():click('Menü')
    button('Settings' if d.execute_script('return document.documentElement.lang')=='en' else 'Ayarlar').click()

def change_language(value):
    open_settings();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.settings-dialog[open]'))
    Select(css('.settings-dialog select[aria-label="TR / EN"]')).select_by_value(value)
    css('.settings-dialog .icon-button').click()

def api(path,body=None):
    return d.execute_async_script("""const [path,body,done]=arguments;import('/src/api.ts').then(async a=>{const project=document.querySelector('#project-select')?.value||'campus-demo-25';const scoped=path+(path.includes('?')?'&':'?')+'project_id='+encodeURIComponent(project);const session=body===null?null:await(await fetch(a.API_BASE+'/api/auth/session',{credentials:'include'})).json();const r=await fetch(a.API_BASE+scoped,{credentials:'include',method:body===null?'GET':'POST',headers:{'Content-Type':'application/json',...(session?{'X-CSRF-Token':session.csrf}:{})},body:body===null?undefined:JSON.stringify(body)});done({status:r.status,body:await r.json()})}).catch(e=>done({error:String(e)}))""",path,body)
try:
    d.get('http://127.0.0.1:5173');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-card'))
    assert not d.find_elements(By.CSS_SELECTOR,'.auth-card select')
    assert 'En az 12' not in css('.auth-card').text
    for width in WIDTHS:
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
    for width in WIDTHS:viewport(width);geometry('overview','.metric-value');shot('overview-'+str(width))
    page('Bina detayları')
    for index in (0,1):
        select=Select(css('#building-select'));name=select.options[index].text;select.select_by_index(index);wait.until(lambda _:css('.page-heading h1').text==name);wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody tr'));shot('building-'+str(index+1)+'-1440')
    for width in WIDTHS:
        viewport(width);geometry('building','.mini-metrics strong');shot('building-'+str(width));shot('floors-'+str(width),'.spatial-detail')
        click('Enerji Dağılımı');shot('end-use-'+str(width),'.spatial-detail');d.find_element(By.XPATH,'//div[@aria-label="Kat analizi görünümü"]/button[normalize-space(.)="Katlar"]').click()
    viewport(1440)
    # Hiding a panel must preserve its live draft and the navigation guard.
    click('Müdahaleler');css('.spatial-assumptions>summary').click()
    roof=css('.spatial-assumptions input');original_roof=roof.get_attribute('value')
    roof.send_keys(Keys.CONTROL,'a');roof.send_keys(str(float(original_roof)+.01))
    click('Yatırım seçenekleri');assert css('#detail-view-packages').is_displayed() and not css('#detail-view-floors').is_displayed()
    click('Katlar ve kullanım');assert css('.spatial-assumptions input').get_attribute('value')==str(float(original_roof)+.01)
    d.find_element(By.XPATH,'//nav/button[@aria-label="Proje özeti"]').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open]'));click('Kal')
    assert css('.spatial-assumptions input').get_attribute('value')==str(float(original_roof)+.01)
    d.find_element(By.XPATH,'//nav/button[@aria-label="Proje özeti"]').click();click('Vazgeç ve devam et');ready();page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody tr'))
    check('Building tabs show one view, preserve spatial drafts, and retain save/discard/stay protection')
    for theme in ('nature','night','earth'):
        open_settings();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.settings-dialog[open]'))
        Select(css('.settings-dialog select[aria-label="Ayarlar teması"]')).select_by_value(theme)
        css('.settings-dialog .icon-button').click();shot('theme-'+theme)
    d.refresh();ready();assert d.execute_script('return document.documentElement.dataset.theme')=='earth'
    check('Independent project/building context, first data positions and three themes persist on reload')
    # Preferences must not remount forms or modify the calculation context.
    assert not d.find_elements(By.CSS_SELECTOR,'.topbar #project-select,.topbar .demo-badge')
    assert d.find_elements(By.CSS_SELECTOR,'.project-workspace #project-select')
    context_before=api('/api/campus/snapshot')['body']['context']
    page('Senaryo girdileri');draft_budget=css('input[name=budget_try]');saved_budget=draft_budget.get_attribute('value')
    draft_budget.send_keys(Keys.CONTROL,'a');draft_budget.send_keys(str(int(saved_budget)+1))
    open_settings();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.settings-dialog[open]'))
    css('.settings-dialog input[type=checkbox]').click();assert d.execute_script('return document.documentElement.dataset.reduceMotion')=='true'
    Select(css('.settings-dialog select[aria-label="TR / EN"]')).select_by_value('en')
    wait.until(lambda _:css('#settings-title').text=='Settings');assert css('input[name=budget_try]').get_attribute('value')==str(int(saved_budget)+1)
    css('.settings-dialog .icon-button').click()
    assert 'Scenario inputs' in css('.page-heading h1').text and not d.find_elements(By.CSS_SELECTOR,'.topbar select')
    draft_budget=css('input[name=budget_try]');draft_budget.send_keys(Keys.CONTROL,'a');draft_budget.send_keys(saved_budget)
    wait.until(lambda _:not css('.scenario-panel form button').is_enabled())
    d.refresh();ready();assert d.execute_script('return document.documentElement.lang')=='en';assert d.execute_script('return document.documentElement.dataset.reduceMotion')=='true'
    for index,label in ((0,'overview'),(1,'building'),(2,'scenario'),(3,'results'),(4,'model')):
        element=d.find_elements(By.CSS_SELECTOR,'.sidebar nav button')[index];element.click();wait.until(lambda _:element.get_attribute('aria-current')=='page')
        if index==1:
            click('Edit information');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open] select[name=use_type]'))
            assert css('select[name=use_type]').get_attribute('value')=='Eğitim'
            assert Select(css('select[name=use_type]')).first_selected_option.text=='Education'
            css('dialog[open] .icon-button').click()
        for width in (390,768,1536):
            viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1');shot('english-'+label+'-'+str(width))
    viewport(1440);click('Settings');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.settings-dialog[open]'));shot('settings-en')
    click('Open project settings');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.project-settings details[open]'))
    assert css('.project-settings').is_displayed()
    change_language('tr')
    context_after=api('/api/campus/snapshot')['body']['context'];assert context_before==context_after
    open_settings();shot('settings-tr');css('.settings-dialog .icon-button').click()
    check('Project selectors moved into workspace; Settings and TR/EN work, preferences persist, drafts and API context remain unchanged')
    project(housing);page('Bina detayları')
    for index in (0,1):
        select=Select(css('#building-select'));name=select.options[index].text;select.select_by_index(index);wait.until(lambda _:css('.page-heading h1').text==name)
    project(office);page('Bina detayları');assert d.find_elements(By.CSS_SELECTOR,'.single-building')
    # Recoverable read error: block only the QA browser's package requests.
    d.execute_cdp_cmd('Network.enable',{});d.execute_cdp_cmd('Network.setBlockedURLs',{'urls':['*api/buildings/B07/packages*']})
    page('Proje özeti');page('Bina detayları');click('Yatırım seçenekleri');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-panel .error-box'));shot('recoverable-package-error','.package-panel')
    d.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[]});click('Tekrar dene');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'))
    check('Housing A/B and single office; failed package request keeps application usable and retries')
    page('Senaryo girdileri')
    for width in WIDTHS:viewport(width);geometry('scenario','input[name=budget_try]');shot('scenario-'+str(width))
    # Unsaved draft must survive attempted navigation and refresh.
    budget=css('input[name=budget_try]');initial=budget.get_attribute('value');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('2900000')
    d.find_element(By.XPATH,'//nav/button[contains(.,"Proje özeti")]').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open]'));click('Kal');assert budget.get_attribute('value')=='2900000'

    if css('.mobile-tools').is_displayed():click('Menü')
    click('Yardım');css('.utility-content>details').click();click('Veriyi yenile');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog[open]'));click('Kal');account_menu(False);assert budget.get_attribute('value')=='2900000'
    click('Girdileri kaydet');wait.until(lambda _:not css('.scenario-panel form button').is_enabled());click('Yatırım planını hesapla')
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.result-metrics'));assert not d.find_elements(By.CSS_SELECTOR,'.inline-notice');assert not d.find_elements(By.CSS_SELECTOR,'.toast')
    assert not d.find_elements(By.CSS_SELECTOR,'.stale-panel');check('Draft retained by navigation/refresh guard; successful solve clears saved-input notice and stale state')
    for width in WIDTHS:
        viewport(width);geometry('results','.decision-summary h2');shot('results-'+str(width));wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.chart-panel svg'));shot('load-chart-'+str(width),'.chart-panel');shot('investment-plan-'+str(width),'.selected-plan')
    viewport(1440)
    snapshot_reply=api('/api/campus/snapshot');assert snapshot_reply['status']==200,snapshot_reply.get('body',{}).get('detail')
    current=snapshot_reply['body'];existing_downloads=set(DOWNLOADS.glob('*.html'))
    baseline=current['calculation']['baseline'];after=current['calculation']['after']
    expected={'electricity':after['electricity_kwh_year']-baseline['electricity_kwh_year'],
              'gas':after['heating_kwh_year']+after['non_heating_gas_kwh_year']-baseline['heating_kwh_year']-baseline['non_heating_gas_kwh_year'],
              'carbon':after['emissions_kg_year']-baseline['emissions_kg_year']}
    for metric,value in expected.items():assert abs(float(css(f'dd[data-metric="{metric}"]').get_attribute('data-value'))-value)<1e-6
    change_language('en')
    for width in (390,1536):
        viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1');shot('english-calculated-results-'+str(width));shot('electrification-en-'+str(width),'.electrification-impact')
    change_language('tr');viewport(1440)
    check('Electrification electricity/gas/carbon deltas equal API values; English forms retain canonical enum values and current results')
    evidence=css('.result-evidence>summary');d.execute_script("arguments[0].scrollIntoView({block:'center'})",evidence);evidence.click()
    assert len(d.find_elements(By.CSS_SELECTOR,'.decision-evidence tbody tr'))==3
    assert d.find_elements(By.CSS_SELECTOR,'.sensitivity-results tbody tr')
    for width in (390,768,1536):viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
    css('.result-evidence>summary').click();viewport(1440)
    click('Paketleri gör');wait.until(lambda _:css('#detail-view-packages').is_displayed());assert not css('#detail-view-floors').is_displayed()
    page('Proje özeti');summary=css('.scenario-map-disclosure>summary');d.execute_script("arguments[0].scrollIntoView({block:'center'})",summary);summary.click()
    css('.model-toggle button[data-mode=after]').click()
    selected=current['calculation']['selected_packages'][0]
    assert float(css('[data-testid=map-investment]').get_attribute('data-value'))==selected['investment_try']
    assert float(css('[data-testid=map-savings]').get_attribute('data-value'))==selected['energy_savings_kwh_year']
    for width in (390,768,1536):viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
    viewport(1440);click('Paketleri karşılaştır');wait.until(lambda _:css('#detail-view-packages').is_displayed())
    page('Optimizasyon sonucu')
    check('Collapsed comparison/sensitivity retain real tables; after-map values match API; result/map links open the investment tab')
    click('Karar özeti indir')
    report_file=wait.until(lambda _:next((p for p in DOWNLOADS.glob('*.html') if p not in existing_downloads),None))
    content=report_file.read_text(encoding='utf-8');assert current['calculation_id'] in content and current['campus']['name'] in content
    original_window=d.current_window_handle;d.switch_to.new_window('tab');d.get(report_file.as_uri());wait.until(lambda _:d.find_elements(By.TAG_NAME,'h1'))
    for width in (390,1440):
        viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1');shot('decision-brief-'+str(width))
    d.close();d.switch_to.window(original_window);viewport(1440)
    page('Senaryo girdileri');budget=css('input[name=budget_try]');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('2900001');click('Girdileri kaydet')
    wait.until(lambda _:css('.scenario-panel form button').text.startswith('Girdiler kayıtlı'))
    wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.stale-notice'));page('Optimizasyon sonucu');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.stale-panel'))
    assert not d.find_elements(By.CSS_SELECTOR,'.decision-brief-download')
    rejected=api('/api/export/html?scope=result&revision='+str(current['campus']['revision'])+'&expected_calculation_id='+current['calculation_id'])
    assert rejected['status']==409
    page('Senaryo girdileri');click('Yatırım planını hesapla');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.result-metrics'))
    assert not d.find_elements(By.CSS_SELECTOR,'.stale-panel') and api('/api/campus/snapshot')['body']['calculation_id']!=current['calculation_id']
    check('Actual decision-brief download matches API context; stale UI removes download, backend rejects old context, recalculation restores current plan')
    page('Model ve veri');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction select'))
    for width in WIDTHS:viewport(width);assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1');shot('model-'+str(width))
    viewport(1440);page('Bina detayları');click('ML / fizik karşılaştırması');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.synthetic-prediction select option') and css('.synthetic-prediction button').is_enabled())
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
        db=sqlite3.connect(DATA/'accounts.sqlite3');row=db.execute('SELECT email FROM users WHERE id=?',(uid,)).fetchone()
        if row and row[0]==email:
            # The backend records the same timestamp for the email and IP attempt.
            # Remove only this QA identity's paired attempts, preserving other users.
            bucket='email:'+hashlib.sha256(email.encode()).hexdigest()
            moments=[r[0] for r in db.execute('SELECT moment FROM attempts WHERE bucket=?',(bucket,))]
            db.executemany('DELETE FROM attempts WHERE moment=? AND (bucket=? OR bucket=?)',[(moment,bucket,'ip:127.0.0.1') for moment in moments])
            db.execute('DELETE FROM sessions WHERE user_id=?',(uid,));db.execute('DELETE FROM users WHERE id=?',(uid,));db.commit()
            parent=(DATA/'users').resolve();target=(parent/uid).resolve();assert target.parent==parent and len(uid)==32
            if target.exists():shutil.rmtree(target)
        db.close()
    report['original_records_preserved']=all(Path(p).exists() and hashlib.sha256(Path(p).read_bytes()).hexdigest()==h for p,h in original.items());assert report['original_records_preserved']
    (OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
