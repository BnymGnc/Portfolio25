"""Explicit UI load and read-only pilot exploration; edits only a new QA copy.

Keeps original projects and pilot inputs intact. QA copy is archived and removed
only when its last captured bytes still match, including its own history files.
"""
import argparse
import hashlib
import json
from pathlib import Path
from urllib.request import urlopen,Request
from urllib.parse import urlencode
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select,WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException
from uuid import uuid4

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/pilot';OUT.mkdir(parents=True,exist_ok=True)


def api(path='/api/campus/snapshot',project='campus-demo-25',body=None):
    request=Request('http://127.0.0.1:8000'+path+'?'+urlencode({'project_id':project}),
                    data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with urlopen(request) as response:return json.load(response)


def run():
    original={p:p.read_bytes() for p in (ROOT/'backend/data').rglob('*.json')}
    status=api('/api/examples/kayseri');initial_ids={p['id'] for p in api('/api/projects')['projects']};owned={}
    options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--window-size=1536,1100')
    options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
    try:
        with webdriver.Chrome(options=options) as d:
            wait=WebDriverWait(d,35,ignored_exceptions=(StaleElementReferenceException,))
            def page(label):
                wait.until(lambda _:d.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]').is_enabled())
                wait.until(lambda _:d.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]').click() is None)
            def management():
                details=d.find_element(By.CSS_SELECTOR,'.project-management')
                if not details.get_attribute('open'):details.find_element(By.TAG_NAME,'summary').click()
            def pick(id,count):
                management()
                Select(d.find_element(By.CSS_SELECTOR,'#project-select')).select_by_value(id)
                wait.until(lambda _:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==count)
            def tab(text):d.find_element(By.XPATH,f'//div[@class="spatial-tabs"]/button[text()="{text}"]').click()
            def number(input,value):input.send_keys(Keys.CONTROL,'a');input.send_keys(str(value))
            def capture(id):
                directory=(ROOT/'backend/data/projects').resolve()
                path=(directory/f'{id}.json').resolve();assert path.parent==directory and id not in initial_ids
                for p in (path,path.with_suffix('.result.json')):
                    if p.exists():owned[p]=p.read_bytes()
                history=(ROOT/'backend/data/history'/id).resolve()
                assert history.parent==(ROOT/'backend/data/history').resolve()
                for p in history.glob('*.json'):owned[p]=p.read_bytes()
            original_count=len(api()['campus']['buildings'])
            d.get('http://127.0.0.1:5173');wait.until(lambda _:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==original_count)
            management()
            d.find_element(By.CSS_SELECTOR,'.pilot-loader summary').click()
            d.find_element(By.CSS_SELECTOR,'.install-pilot').click()
            campus_id=status['projects'][0]['id']
            wait.until(lambda _:Select(d.find_element(By.CSS_SELECTOR,'#project-select')).first_selected_option.get_attribute('value')==campus_id)
            wait.until(lambda _:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==4)
            assert 'Kayseri için hazırlanmış sentetik pilot senaryo — saha ölçümü değildir.' in d.find_element(By.CSS_SELECTOR,'.synthetic-banner').text
            assert len(api('/api/projects')['projects'])==len(initial_ids)+sum(not p['loaded'] for p in status['projects'])
            print('PASS: explicit four-project/eight-building load; original project retained')
            page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
            Select(d.find_element(By.CSS_SELECTOR,'.energy-filter select')).select_by_value('fuel_kwh_year')
            campus=api(project=campus_id)['campus'];b=campus['buildings'][0]
            actual=sum(float(e.get_attribute('data-energy')) for e in d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody [data-energy]'))
            expected_allocation=api('/api/buildings/'+b['id']+'/spatial',campus_id)['baseline']
            assert abs(actual-expected_allocation['totals']['fuel_kwh_year'])<1e-5
            tab('Enerji Dağılımı');assert d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody tr')
            tab('Müdahale Senaryoları')
            d.find_element(By.NAME,'spatial.roof').click();d.find_element(By.NAME,'spatial.lighting').click()
            Select(d.find_element(By.CSS_SELECTOR,'select[aria-label="Kat senaryosu ısıtma paketi"]')).select_by_value('heat_pump')
            d.find_element(By.CSS_SELECTOR,'.spatial-calculate').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-preview'))
            preview=d.find_element(By.CSS_SELECTOR,'.spatial-preview')
            expected=api('/api/buildings/'+b['id']+'/spatial/evaluate',campus_id,{'revision':campus['revision'],'selection':{'roof':True,'lighting':True},'package':'heat_pump'})
            assert abs(float(preview.get_attribute('data-electricity-after'))-expected['after']['electricity_kwh_year'])<1e-6
            assert abs(float(preview.get_attribute('data-investment'))-expected['investment_try'])<1e-6
            d.execute_script("arguments[0].scrollIntoView({block:'start'})",preview);d.save_screenshot(str(OUT/'combined-preview.png'))
            d.find_element(By.CSS_SELECTOR,'.spatial-controls details summary').click()
            target=d.find_element(By.CSS_SELECTOR,'input[aria-label="Z001 hedef aydınlatma (W/m²)"]');number(target,3)
            assert d.find_element(By.CSS_SELECTOR,'.spatial-stale').is_displayed()
            assert all(not x.is_enabled() for x in d.find_elements(By.CSS_SELECTOR,'.export-actions button')[-2:])
            d.find_element(By.XPATH,'//button[contains(.,"Veriyi yenile")]').click()
            wait.until(lambda _:d.find_elements(By.XPATH,'//h2[text()="Kaydedilmemiş değişiklikler"]'))
            d.find_element(By.XPATH,'//button[normalize-space()="Kal"]').click()
            assert target.get_attribute('value')=='3'
            d.find_element(By.XPATH,'//button[contains(.,"Veriyi yenile")]').click()
            wait.until(lambda _:d.find_elements(By.XPATH,'//button[normalize-space()="Vazgeç ve devam et"]'))
            d.find_element(By.XPATH,'//button[normalize-space()="Vazgeç ve devam et"]').click()
            wait.until(lambda _:not d.find_elements(By.CSS_SELECTOR,'.spatial-preview'))
            wait.until(lambda _:d.find_element(By.CSS_SELECTOR,'#project-select').is_enabled())
            print('PASS: floor/use fuel reconciliation; combined preview matches API; changed assumptions invalidate preview/export')
            for index,count in ((1,2),(2,1),(3,1)):
                project=status['projects'][index]['id'];pick(project,count);page('Bina detayları')
                wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
                tab('Müdahale Senaryoları')
                if index in (1,3):
                    card=d.find_element(By.XPATH,'//article[contains(@class,"recommendation")][.//h3[text()="HVAC çalışma programı"]]')
                    assert 'Yalnız inceleme adayı' in card.text and not card.find_elements(By.TAG_NAME,'button')
                    assert not d.find_element(By.NAME,'spatial.schedule').is_enabled()
                assert len(api(project=project)['campus']['connection_groups'])==count
            print('PASS: four-project navigation; independent housing connections; protected housing/hotel schedule rejected')
            # Make a separate office QA copy; do not save edits to any original pilot.
            office=status['projects'][2]['id'];pick(office,1)
            management()
            d.find_element(By.XPATH,'//button[text()="Yeni proje oluştur"]').click()
            qa_name='QA kat '+uuid4().hex[:8]
            form=d.find_element(By.CSS_SELECTOR,'.new-project-form');number(form.find_element(By.CSS_SELECTOR,'input:not([type="checkbox"])'),qa_name)
            form.find_element(By.CSS_SELECTOR,'input[type="checkbox"]').click();form.find_element(By.CSS_SELECTOR,'button.primary').click()
            created=wait.until(lambda _:next((p for p in api('/api/projects')['projects'] if p['name']==qa_name),None))
            qa=created['id'];capture(qa)
            wait.until(lambda _:Select(d.find_element(By.CSS_SELECTOR,'#project-select')).first_selected_option.get_attribute('value')==qa)
            page('Senaryo girdileri');d.find_element(By.CSS_SELECTOR,'.compute-button').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'));capture(qa)
            page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'));tab('Müdahale Senaryoları')
            Select(d.find_element(By.CSS_SELECTOR,'select[aria-label="Müdahale alanı"]')).select_by_value('Z001')
            d.find_element(By.NAME,'spatial.lighting').click();d.find_element(By.CSS_SELECTOR,'.spatial-calculate').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-preview'))
            qa_before=api(project=qa)['campus'];qa_building=qa_before['buildings'][0]
            expected_cost=qa_building['spatial']['floors'][0]['zones'][0]['area_m2']*qa_building['spatial']['lighting_cost_try_m2']
            assert abs(float(d.find_element(By.CSS_SELECTOR,'.spatial-preview').get_attribute('data-investment'))-expected_cost)<1e-6
            d.find_element(By.CSS_SELECTOR,'.spatial-save').click();wait.until(lambda _:api(project=qa)['campus']['revision']==qa_before['revision']+1);capture(qa)
            wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.stale-notice'))
            page('Optimizasyon sonucu');assert d.find_element(By.CSS_SELECTOR,'.stale-panel').is_displayed()
            page('Senaryo girdileri');d.find_element(By.CSS_SELECTOR,'.compute-button').click();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.decision-evidence'));capture(qa)
            current=api(project=qa);assert current['calculation']['selected_packages'][0]['spatial_investment_try']==expected_cost
            assert all(any(row['parameter']==p for row in current['calculation']['sensitivity']['rows']) for p in ('scop','investment','insulation'))
            page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
            for label in ('Katlar','Enerji Dağılımı','Müdahale Senaryoları'):
                tab(label)
                for width in (390,500,768,1536):
                    d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':width<1000})
                    assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth'),(label,width)
                d.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
            tab('Katlar');d.find_element(By.CSS_SELECTOR,'.spatial-detail').screenshot(str(OUT/'floor-view.png'))
            d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':390,'height':1000,'deviceScaleFactor':1,'mobile':True});d.save_screenshot(str(OUT/'mobile-pilot.png'));d.execute_cdp_cmd('Emulation.clearDeviceMetricsOverride',{})
            pick('campus-demo-25',original_count)
            logs=d.get_log('browser');(OUT/'browser-console.json').write_text(json.dumps(logs,indent=2),encoding='utf-8')
            assert not [e for e in logs if e['level']=='SEVERE']
            print('PASS: QA scope saved once into portfolio; old result blocked; comparison/sensitivity work; 3 views at 4 widths; no severe console error')
        assert all(path.read_bytes()==data for path,data in original.items())
        print('PASS: all pre-existing JSON inputs, results and backups byte-for-byte preserved')
    finally:
        for path,expected in owned.items():
            assert path.resolve().is_relative_to((ROOT/'backend/data').resolve())
            if path.exists() and path.read_bytes()==expected:
                destination=OUT/'qa-archive'/path.relative_to(ROOT/'backend/data');destination.parent.mkdir(parents=True,exist_ok=True);destination.write_bytes(expected);path.unlink()
            elif path.exists():print('Preserved concurrently changed QA file:',path.name)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',help='Use a separate evidence folder; preserve earlier screenshots and logs.')
    args=parser.parse_args()
    if args.output_dir:OUT=Path(args.output_dir);OUT.mkdir(parents=True,exist_ok=True)
    run()
