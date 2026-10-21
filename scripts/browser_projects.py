"""Chrome stage-5 flow. Writes only newly created QA project copies, never the default project.

Created projects are archived under artifacts/stage5, then deleted only if their bytes
still match this test's last snapshot. User edits during the test prevent cleanup.
"""
import hashlib
import json
import tempfile
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import urlopen

from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/stage5'


def read(path='/api/campus/snapshot',project='campus-demo-25'):
    with urlopen('http://127.0.0.1:8000'+path+'?'+urlencode({'project_id':project})) as response:return json.load(response)


def run():
    OUT.mkdir(parents=True,exist_ok=True)
    original=(ROOT/'backend/data/campus.json').read_bytes()
    baseline_ids={p['id'] for p in read('/api/projects')['projects']}
    owned={}
    options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--window-size=1536,1100')
    options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
    downloads=Path(tempfile.mkdtemp(prefix='project-downloads-',dir=OUT))
    options.add_experimental_option('prefs',{'download.default_directory':str(downloads)})
    try:
        with webdriver.Chrome(options=options) as driver:
            wait=WebDriverWait(driver,35)
            def page(label):driver.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]').click()
            def enter(field,value):field.send_keys(Keys.CONTROL,'a');field.send_keys(str(value))
            def snapshot():
                selected=Select(driver.find_element(By.CSS_SELECTOR,'.project-picker select')).first_selected_option.get_attribute('value')
                return read(project=selected)
            def capture(project):
                directory=(ROOT/'backend/data/projects').resolve()
                path=(directory/f'{project}.json').resolve()
                assert path.parent==directory and project not in baseline_ids
                if path.exists():owned[path]=path.read_bytes()
                result=path.with_name(path.stem+'.result.json')
                if result.exists():owned[result]=result.read_bytes()
            def choose_default():
                Select(driver.find_element(By.CSS_SELECTOR,'.project-picker select')).select_by_value('campus-demo-25')
                wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
            driver.get('http://127.0.0.1:5173')
            wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==8)
            for count in (1,2):
                driver.find_element(By.XPATH,'//button[text()="Yeni proje oluştur"]').click()
                form=driver.find_element(By.CSS_SELECTOR,'.new-project-form')
                enter(form.find_element(By.CSS_SELECTOR,'input:not([type="checkbox"])'),f'QA geçici {count} bina')
                for box in form.find_elements(By.CSS_SELECTOR,'input[type="checkbox"]')[:count]:box.click()
                form.find_element(By.CSS_SELECTOR,'button[type="submit"],button.primary').click()
                wait.until(lambda d:Select(d.find_element(By.CSS_SELECTOR,'.project-picker select')).first_selected_option.get_attribute('value')!='campus-demo-25')
                wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==count)
                current=snapshot();project=current['campus']['id'];capture(project)
                assert len(current['campus']['connection_groups'])==count
                assert len(driver.find_elements(By.CSS_SELECTOR,'.map-building'))==count
                page('Bina detayları')
                wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'))==4)
                driver.find_element(By.XPATH,'//button[contains(.,"Bilgileri düzenle")]').click()
                editor=driver.find_element(By.CSS_SELECTOR,'dialog form')
                enter(editor.find_element(By.NAME,'name'),f'QA düzenlenen {count}')
                editor.find_element(By.CSS_SELECTOR,'button.primary').click()
                wait.until(lambda d:not d.find_elements(By.CSS_SELECTOR,'dialog[open]'))
                page('Senaryo girdileri')
                driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
                wait.until(lambda d:len(d.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'))==count)
                wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.load-chart'))
                current=snapshot();capture(project)
                assert current['calculation']['decision_evidence'] and len(current['calculation']['sensitivity']['rows'])==9
                assert len(driver.find_elements(By.CSS_SELECTOR,'.decision-evidence tbody tr'))==3
                assert len(driver.find_elements(By.CSS_SELECTOR,'.sensitivity-results tbody tr'))==9
                groups=Select(driver.find_element(By.CSS_SELECTOR,'.chart-controls select[aria-label]'))
                assert len(groups.options)==count
                if count==2:
                    groups.select_by_index(1)
                    expected=current['campus']['connection_groups'][1]['capacity_kw']
                    label=driver.execute_script("return new Intl.NumberFormat('tr-TR',{maximumFractionDigits:1}).format(arguments[0])",expected)
                    assert label in driver.find_element(By.CSS_SELECTOR,'.chart-inspector').text
                    assert current['after']['capacity_utilization_pct']==max(100*c['peak_kw']/c['limit_kw'] for c in current['after']['capacity_checks'] if c['kind']=='group')
                Select(driver.find_element(By.CSS_SELECTOR,'.export-scope-label select')).select_by_value('result')
                driver.find_element(By.XPATH,'//div[@class="export-actions"]/button[contains(.,"JSON")]').click()
                exported=downloads/f'portfolio25-grid-{project}-result-r{current["campus"]["revision"]}-A.json'
                wait.until(lambda _:exported.exists())
                report=json.loads(exported.read_text(encoding='utf-8'))
                assert report['export_metadata']['project_id']==project and report['calculation']['decision_evidence']==current['calculation']['decision_evidence']
                driver.save_screenshot(str(OUT/f'{count}-building-results.png'))
                page('Senaryo girdileri')
                driver.find_element(By.CSS_SELECTOR,'.project-settings summary').click()
                field=driver.find_element(By.CSS_SELECTOR,'.project-settings input[aria-label="Mevsimsel SCOP düşük çarpan"]')
                enter(field,.8)
                page('Optimizasyon sonucu');assert driver.find_element(By.CSS_SELECTOR,'.stale-panel').is_displayed()
                page('Senaryo girdileri')
                driver.find_element(By.CSS_SELECTOR,'.project-settings button.primary').click()
                try:
                    wait.until(lambda _:snapshot()['campus']['sensitivity_settings']['scop']['low']==.8)
                except Exception:
                    driver.save_screenshot(str(OUT/'project-settings-failure.png'))
                    print('UI errors:',[e.text for e in driver.find_elements(By.CSS_SELECTOR,'.error-box')])
                    print('Invalid controls:',driver.execute_script("return [...document.querySelectorAll('.project-settings input:invalid')].map(x=>({label:x.getAttribute('aria-label'),value:x.value,reason:x.validationMessage}))"))
                    raise
                driver.find_element(By.CSS_SELECTOR,'.compute-button').click()
                wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.sensitivity-results'))
                current=snapshot();capture(project)
                row=current['calculation']['sensitivity']['rows'][0];assert row['multiplier']==.8
                for width in (390,500,768,1536):
                    driver.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':width<1000})
                    assert driver.execute_script('return document.documentElement.scrollWidth<=innerWidth'),(count,width)
                driver.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
                driver.refresh()
                wait.until(lambda d:d.find_elements(By.CSS_SELECTOR,'.project-picker select'))
                wait.until(lambda d:Select(d.find_element(By.CSS_SELECTOR,'.project-picker select')).first_selected_option.get_attribute('value')==project)
                assert snapshot()['campus']['buildings'][0]['name']==f'QA düzenlenen {count}'
                (OUT/f'{count}-building-snapshot.json').write_text(json.dumps(current,ensure_ascii=False,indent=2),encoding='utf-8')
                choose_default()
                print(f'PASS: {count}-building create/edit/persist/calculate/comparison/sensitivity/group chart/export/stale/width flow')
            assert not [e for e in driver.get_log('browser') if e['level']=='SEVERE']
        assert (ROOT/'backend/data/campus.json').read_bytes()==original
        print('PASS: default project inputs unchanged; no severe Chrome console errors')
    finally:
        directory=(ROOT/'backend/data/projects').resolve()
        for path,expected in owned.items():
            assert path.resolve().parent==directory
            if path.exists() and path.read_bytes()==expected:
                (OUT/path.name).write_bytes(expected)
                path.unlink()
            elif path.exists():print('Preserved concurrently modified QA project:',path.name)


if __name__=='__main__':run()
