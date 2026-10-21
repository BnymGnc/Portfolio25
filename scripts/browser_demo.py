"""Stage 3 integration QA. Requires running local servers, Chrome and Selenium.

Uses real API results. Temporarily edits inputs and restores them in finally.
Revisions increase. If a calculation existed, its original mode is recalculated
after input restoration. Screenshots/downloads live in ignored artifacts/.
"""
import base64
import json
import os
import tempfile
from pathlib import Path
from urllib.request import Request, urlopen

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT = Path(__file__).resolve().parents[1]
FRONTEND = os.getenv('SMOKE_FRONTEND_URL', 'http://127.0.0.1:5173')
API = os.getenv('SMOKE_API_URL', 'http://127.0.0.1:8000')


def api(path='/api/campus', method='GET', body=None):
    request = Request(API + path, method=method, headers={'Content-Type':'application/json'},
                      data=json.dumps(body).encode() if body is not None else None)
    with urlopen(request, timeout=90) as response:
        return json.load(response)


def run():
    output = ROOT / 'artifacts'
    output.mkdir(exist_ok=True)
    downloads = Path(tempfile.mkdtemp(prefix='demo-',dir=output))
    original = api()
    options = webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1536,1100')
    options.add_experimental_option('prefs',{'download.default_directory':str(downloads),'download.prompt_for_download':False})
    options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
    driver = webdriver.Chrome(options=options)
    redirect_from = os.getenv('SMOKE_REDIRECT_API_FROM')
    if redirect_from:
        # Isolated QA API; production input files must not be edited by browser tests.
        driver.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument', {'source':
            f"const realFetch=window.fetch; window.fetch=(url,options)=>realFetch(typeof url==='string'?url.replace({json.dumps(redirect_from)},{json.dumps(API)}):url,options);"})
    wait = WebDriverWait(driver, 25)
    modified = False
    def page(text):
        driver.find_element(By.XPATH, f'//nav/button[contains(., "{text}")]').click()
    def enter(name, value):
        field = driver.find_element(By.NAME,name)
        field.send_keys(Keys.CONTROL,'a');field.send_keys(str(value))
    try:
        driver.get(FRONTEND)
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
        assert 'Sentetik örnek kampüs' in driver.find_element(By.TAG_NAME,'body').text
        driver.save_screenshot(str(output/'stage3-overview.png'))
        print('PASS: eight real API buildings, provenance and campus overview')

        driver.find_elements(By.CSS_SELECTOR,'.edit-button')[0].click()
        wait.until(EC.visibility_of_element_located((By.TAG_NAME,'dialog')))
        enter('name','QA Demo Bina')
        modified=True
        driver.find_element(By.CSS_SELECTOR,'dialog button.primary').click()
        wait.until(EC.invisibility_of_element_located((By.TAG_NAME,'dialog')))
        assert api()['campus']['buildings'][0]['name']=='QA Demo Bina'
        driver.refresh()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.inventory-panel'),'QA Demo Bina'))
        page('Bina detayları')
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'))==4)
        print('PASS: building edit persists and four packages come from API')

        page('Senaryo girdileri')
        enter('budget_try',original['campus']['scenario']['budget_try']+100000)
        driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.plan-table tbody tr')))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.load-chart')))
        result=api()['calculation']
        assert result['solver']['optimality_proven']
        assert len(driver.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'))==8
        assert 'Optimum çözüm bulundu' in driver.find_element(By.CSS_SELECTOR,'.solver-banner').text
        Select(driver.find_element(By.CSS_SELECTOR,'.chart-controls select')).select_by_value('1')
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.chart-legend'),'24 /'))
        driver.find_element(By.XPATH,'//button[contains(., "Pik haftasını göster")]').click()
        assert driver.find_element(By.CSS_SELECTOR,'.chart-controls input').get_attribute('value')==result['after']['electric_peak_timestamp'][:10]
        driver.save_screenshot(str(output/'stage3-results.png'))
        print('PASS: save/calculate, actual investment/plan, aligned annual chart and period controls')

        page('Senaryo girdileri')
        enter('savings_target_pct',original['campus']['scenario']['savings_target_pct']+1)
        page('Optimizasyon sonucu')
        assert 'Girdiler değişti; yeniden hesaplayın' in driver.find_element(By.CSS_SELECTOR,'.stale-panel').text
        assert all(not b.is_enabled() for b in driver.find_elements(By.CSS_SELECTOR,'.export-actions button')[1:])
        page('Senaryo girdileri')
        driver.find_element(By.CSS_SELECTOR,'.scenario-panel button.primary').click()
        wait.until(lambda d:'Girdiler kayıtlı' in d.find_element(By.CSS_SELECTOR,'.scenario-panel button.primary').text)
        driver.refresh()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.inventory-panel')))
        page('Optimizasyon sonucu')
        assert driver.find_element(By.CSS_SELECTOR,'.stale-panel').is_displayed()
        assert api('/api/export/json')['calculation'] is None
        print('PASS: pending/saved/reloaded edits mark history stale; exports cannot contain old plan')

        page('Senaryo girdileri')
        driver.find_element(By.CSS_SELECTOR,'input[name="mode"][value="B"]').click()
        driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.plan-table tbody tr')))
        assert api()['calculation']['mode']=='B'
        assert api()['calculation']['target_met']
        export_revision=api()['campus']['revision']
        for ext in ('CSV','JSON'):
            driver.find_element(By.XPATH,f'//div[@class="export-actions"]/button[contains(.,"{ext}")]').click()
            wait.until(lambda _: (downloads/f'portfolio25-grid-result-r{export_revision}-B.{ext.lower()}').exists())
        exported=json.loads((downloads/f'portfolio25-grid-result-r{export_revision}-B.json').read_text(encoding='utf-8'))
        assert len(exported['investment_plan'])==8
        print('PASS: mode B reaches target, CSV/JSON include actual current plan')

        page('Kampüs özeti')
        invalid=downloads/'invalid.csv';invalid.write_text('id;name\nB01;broken',encoding='utf-8')
        before_revision=api()['campus']['revision']
        driver.find_element(By.CSS_SELECTOR,'input[type="file"]').send_keys(str(invalid))
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.inventory-panel .error-box'),'CSV yüklenemedi'))
        assert api()['campus']['revision']==before_revision
        driver.find_element(By.CSS_SELECTOR,'input[type="file"]').send_keys(str(downloads/f'portfolio25-grid-result-r{export_revision}-B.csv'))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.csv-preview')))
        driver.find_element(By.XPATH,'//div[@class="csv-preview"]/button[contains(., "Vazgeç")]').click()
        assert api()['campus']['revision']==before_revision
        driver.find_element(By.CSS_SELECTOR,'input[type="file"]').send_keys(str(downloads/f'portfolio25-grid-result-r{export_revision}-B.csv'))
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.csv-preview')))
        driver.find_element(By.XPATH,'//div[@class="csv-preview"]/button[contains(., "8 binayı uygula")]').click()
        wait.until(EC.invisibility_of_element_located((By.CSS_SELECTOR,'.csv-preview')))
        assert api()['campus']['revision']==before_revision+1
        assert api()['calculation'] is None
        page('Senaryo girdileri')
        driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.load-chart')))
        page('Kampüs özeti')
        print('PASS: invalid CSV has no mutation; valid export previews, applies and invalidates old result')

        # Deliberate transport fault: remove one hour from the real API response.
        driver.execute_script("window.demoFetch=window.fetch; window.fetch=async (...args)=>{const r=await window.demoFetch(...args);if(String(args[0]).endsWith('/api/campus/profiles')){const p=await r.json();p.before_kw.pop();return new Response(JSON.stringify(p),{status:200,headers:{'Content-Type':'application/json'}});}return r;};")
        page('Optimizasyon sonucu')
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.chart-panel'),'Saatlik profil eksik'))
        assert not driver.find_elements(By.CSS_SELECTOR,'.load-chart')
        driver.execute_script('window.fetch=window.demoFetch')
        driver.find_element(By.XPATH,'//button[contains(.,"Profili yeniden yükle")]').click()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.load-chart')))
        print('PASS: missing hour gives explicit profile error and retry recovers')

        page('Senaryo girdileri')
        enter('budget_try',0);enter('savings_target_pct',100)
        driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
        wait.until(EC.text_to_be_present_in_element((By.CSS_SELECTOR,'.solver-banner'),'Çözüm bulunamadı'))
        assert not driver.find_elements(By.CSS_SELECTOR,'.result-metrics')
        print('PASS: infeasible scenario has no invented KPI values')

        driver.find_element(By.XPATH,'//div[@class="export-actions"]/button[contains(.,"Varsayımlar")]').click()
        wait.until(EC.visibility_of_element_located((By.CSS_SELECTOR,'.assumptions-dialog')))
        assert 'SCOP' in driver.find_element(By.CSS_SELECTOR,'.assumptions-dialog').text
        driver.find_element(By.CSS_SELECTOR,'.assumptions-dialog .icon-button').click()
        for label in ('Kampüs özeti','Bina detayları','Senaryo girdileri','Optimizasyon sonucu'):
            page(label)
            for width in (390,500,768,1536):
                driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':900,'deviceScaleFactor':1,'mobile':True})
                assert driver.execute_script('return document.documentElement.scrollWidth<=innerWidth'),(label,width)
            driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
        print('PASS: assumptions accessible; four screens at 390/500/768/1536px have no page overflow')

        driver.execute_cdp_cmd('Network.enable',{})
        driver.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[API+'/api/*']})
        driver.refresh()
        wait.until(EC.presence_of_element_located((By.CSS_SELECTOR,'.error-box')))
        assert not driver.find_elements(By.CSS_SELECTOR,'.metric-card')
        driver.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[]})
        driver.find_element(By.XPATH,'//button[contains(.,"Tekrar dene")]').click()
        wait.until(lambda d: len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
        unexpected=[e for e in driver.get_log('browser') if e['level']=='SEVERE' and 'ERR_BLOCKED_BY_CLIENT' not in e['message'] and 'favicon' not in e['message']]
        assert not unexpected,unexpected
        print('PASS: API failure/retry and browser console')
    finally:
        if modified:
            latest=api()['campus']
            api(method='PUT',body={**{k:original['campus'][k] for k in ('buildings','scenario','profile_settings')},'revision':latest['revision']})
            if original['calculation']:
                api('/api/calculate','POST',{'revision':api()['campus']['revision'],'mode':original['calculation']['mode'],'time_limit_s':10})
        driver.quit()


if __name__=='__main__':
    run()
