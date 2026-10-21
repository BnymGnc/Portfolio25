"""Delivery browser flow: does not PUT or reset saved user inputs.

Only recomputes the already selected mode against the current saved revision.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.request import urlopen

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT=Path(__file__).resolve().parents[1]
API='http://127.0.0.1:8000'

def read(path='/api/campus/snapshot'):
    with urlopen(API+path) as response:
        return json.load(response)


def run():
    artifacts=ROOT/'artifacts/delivery'
    artifacts.mkdir(exist_ok=True)
    downloads=Path(tempfile.mkdtemp(prefix='downloads-',dir=artifacts))
    input_file=ROOT/'backend/data/campus.json'
    original_hash=hashlib.sha256(input_file.read_bytes()).hexdigest()
    original=read()
    options=webdriver.ChromeOptions()
    options.add_argument('--headless=new')
    options.add_argument('--window-size=1536,1100')
    options.add_experimental_option('prefs',{'download.default_directory':str(downloads),'download.prompt_for_download':False})
    options.set_capability('goog:loggingPrefs',{'browser':'ALL','performance':'ALL'})
    with webdriver.Chrome(options=options) as driver:
        wait=WebDriverWait(driver,25)
        def page(label):
            driver.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]').click()
        driver.get('http://127.0.0.1:5173')
        wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
        wait.until(lambda d:'API bağlantısı kuruldu' in d.find_element(By.CSS_SELECTOR,'.connection').text)
        assert 'Sentetik örnek kampüs' in driver.find_element(By.TAG_NAME,'body').text
        print('PASS: live frontend/API and eight saved buildings')
        driver.find_element(By.CSS_SELECTOR,'.main-plan-action').click()
        driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'))
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.load-chart'))
        latest=read()
        requests=[json.loads(e['message'])['message'] for e in driver.get_log('performance')]
        calls=[e['params']['request'] for e in requests if e['method']=='Network.requestWillBeSent' and '/api/calculate' in e['params']['request']['url']]
        assert calls and json.loads(calls[-1]['postData'])['revision']==original['campus']['revision']
        assert latest['calculation']['input_revision']==latest['campus']['revision']
        print('PASS: compute request and displayed result use the same saved revision')
        for kind in ('inputs','result'):
            Select(driver.find_element(By.CSS_SELECTOR,'.export-scope-label select')).select_by_value(kind)
            for extension in ('csv','json'):
                driver.find_element(By.XPATH,f'//div[@class="export-actions"]/button[contains(.,"{extension.upper()}")]').click()
                suffix=f'-{latest["calculation"]["mode"]}' if kind=='result' else ''
                file=downloads/f'portfolio25-grid-{kind}-r{latest["campus"]["revision"]}{suffix}.{extension}'
                wait.until(lambda _:file.exists())
                if extension=='json':
                    body=json.loads(file.read_text(encoding='utf-8'))
                    assert body['export_metadata']['input_revision']==latest['campus']['revision']
                    assert (body['calculation'] is not None)==(kind=='result')
                    if kind=='result':
                        assert body['export_metadata']['calculation_id']==latest['calculation_id']
                        assert len(body['investment_plan'])==8 and body['after']
        print('PASS: explicitly separated input/result CSV/JSON with matching revision and calculation ID')
        page('Senaryo girdileri')
        field=driver.find_element(By.NAME,'budget_try');field.send_keys(Keys.CONTROL,'a');field.send_keys(str(original['campus']['scenario']['budget_try']+1))
        page('Optimizasyon sonucu')
        assert driver.find_element(By.CSS_SELECTOR,'.stale-panel').is_displayed()
        assert all(not b.is_enabled() for b in driver.find_elements(By.CSS_SELECTOR,'.export-actions button')[-2:])
        driver.find_element(By.XPATH,'//button[contains(.,"Veriyi yenile")]').click()
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'))
        print('PASS: unsaved input invalidates displayed result; refresh restores saved values without PUT')
        for label in ('Kampüs özeti','Bina detayları','Senaryo girdileri','Optimizasyon sonucu'):
            page(label)
            for width in (390,500,768,1536):
                driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':width<1000})
                assert driver.execute_script('return document.documentElement.scrollWidth<=innerWidth'),(label,width)
                if width==390:
                    assert driver.execute_script("return document.querySelector('.main-shell').getBoundingClientRect().left===0"),'Mobile menu steals content width'
            driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
        print('PASS: four screens at 390/500/768/1536px; full-width mobile content')
        page('Kampüs özeti')
        if driver.find_elements(By.CSS_SELECTOR,'.scenario-model'):
            model=driver.find_element(By.CSS_SELECTOR,'.scenario-model')
            driver.execute_script("arguments[0].scrollIntoView({block:'start'})",model)
            driver.find_element(By.CSS_SELECTOR,'.scenario-model button[data-mode="after"]').click()
            building=driver.find_element(By.CSS_SELECTOR,'.scenario-model .map-building')
            building.click()
            wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.model-building-detail'))
            first=latest['calculation']['selected_packages'][0]
            detail=driver.find_element(By.CSS_SELECTOR,'.model-building-detail').text
            assert latest['campus']['buildings'][0]['name'] in detail
            assert driver.find_elements(By.CSS_SELECTOR,'.model-legend')
            baseline_peak=latest['profile_audit']['buildings'][0]['electric_peak_kw']
            expected={'map-investment':first['investment_try'],'map-savings':first['energy_savings_kwh_year'],
                      'map-peak-delta':first['electric_peak_kw']-baseline_peak}
            for test_id,value in expected.items():
                actual=float(driver.find_element(By.CSS_SELECTOR,f'[data-testid="{test_id}"]').get_attribute('data-value'))
                assert abs(actual-value)<1e-7,(test_id,actual,value)
            model.screenshot(str(artifacts/'campus-scenario-model.png'))
            print('PASS: before/after map, package colors and real API building effects')
        driver.execute_script('window.scrollTo(0,0)')
        driver.save_screenshot(str(artifacts/'desktop.png'))
        page('Optimizasyon sonucu')
        driver.execute_script('window.scrollTo(0,0)')
        driver.save_screenshot(str(artifacts/'results.png'))
        driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':390,'height':1000,'deviceScaleFactor':1,'mobile':True})
        driver.save_screenshot(str(artifacts/'mobile.png'))
        driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
        page('Kampüs özeti')
        invalid=downloads/'invalid.csv';invalid.write_text('id;name\nB01;broken',encoding='utf-8')
        driver.find_element(By.CSS_SELECTOR,'input[type="file"]').send_keys(str(invalid))
        wait.until(lambda d:'CSV yüklenemedi' in d.find_element(By.CSS_SELECTOR,'.inventory-panel .error-box').text)
        valid=downloads/f'portfolio25-grid-result-r{latest["campus"]["revision"]}-{latest["calculation"]["mode"]}.csv'
        driver.find_element(By.CSS_SELECTOR,'input[type="file"]').send_keys(str(valid))
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.csv-preview'))
        driver.find_element(By.XPATH,'//div[@class="csv-preview"]/button[contains(.,"Vazgeç")]').click()
        print('PASS: invalid CSV rejected; current result CSV previews and cancels without saving')
        driver.execute_script("window.deliveryFetch=window.fetch;window.fetch=async (...args)=>{const r=await window.deliveryFetch(...args);if(String(args[0]).split('?')[0].endsWith('/api/campus/profiles')){const p=await r.json();p.before_kw.pop();return new Response(JSON.stringify(p),{status:200,headers:{'Content-Type':'application/json'}});}return r;};")
        page('Optimizasyon sonucu')
        wait.until(lambda d:'Saatlik profil eksik' in d.find_element(By.CSS_SELECTOR,'.chart-panel').text)
        assert not driver.find_elements(By.CSS_SELECTOR,'.load-chart')
        driver.execute_script('window.fetch=window.deliveryFetch')
        driver.find_element(By.XPATH,'//button[contains(.,"Profili yeniden yükle")]').click()
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.load-chart'))
        print('PASS: deliberately missing hour produces explicit error; retry recovers real profile')
        driver.execute_cdp_cmd('Network.enable',{})
        driver.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[API+'/api/*']})
        driver.refresh()
        wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.error-box'))
        assert not driver.find_elements(By.CSS_SELECTOR,'.metric-card')
        driver.execute_cdp_cmd('Network.setBlockedURLs',{'urls':[]})
        driver.find_element(By.XPATH,'//button[contains(.,"Tekrar dene")]').click()
        wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
        assert not [e for e in driver.get_log('browser') if e['level']=='SEVERE' and 'ERR_BLOCKED_BY_CLIENT' not in e['message']]
        print('PASS: controlled API outage has a readable error; retry reconnects')
    assert hashlib.sha256(input_file.read_bytes()).hexdigest()==original_hash,'Saved input file changed'
    print('PASS: saved input file byte-for-byte unchanged')


if __name__=='__main__':
    run()
