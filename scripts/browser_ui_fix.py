"""Real Chrome UI acceptance. Writes only a temporary QA project, then archives it.

Run with system Python (installed Selenium). Existing records and env are untouched.
Screenshots, served-source/process evidence and data hashes go to artifacts/ui-fix.
"""
import hashlib
import json
import time
from pathlib import Path
from urllib.request import urlopen, Request
from urllib.parse import urlencode
from uuid import uuid4
import psutil
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import Select, WebDriverWait
from selenium.common.exceptions import StaleElementReferenceException

ROOT=Path(__file__).resolve().parents[1]
OUT=ROOT/'artifacts/ui-fix'
OUT.mkdir(parents=True,exist_ok=True)
BASE='http://127.0.0.1:5173'
API='http://127.0.0.1:8000'

def api(path='/api/campus/snapshot',project='campus-demo-25',body=None):
    req=Request(API+path+'?'+urlencode({'project_id':project}),data=json.dumps(body).encode() if body is not None else None,headers={'Content-Type':'application/json'})
    with urlopen(req,timeout=80) as response:return json.load(response)

def run():
    original={p:p.read_bytes() for p in (ROOT/'backend/data').rglob('*.json')}
    owned={};initial_ids={p['id'] for p in api('/api/projects')['projects']}
    report={'url':BASE,'api_url':API,'checks':[],'screenshots':[]}
    def check(name,detail=True):
        report['checks'].append({'name':name,'detail':detail});print('PASS:',name,flush=True)
    def capture_owned(id):
        assert id not in initial_ids
        directory=(ROOT/'backend/data/projects').resolve()
        path=(directory/f'{id}.json').resolve();assert path.parent==directory
        for p in (path,path.with_suffix('.result.json')):
            if p.exists():owned[p]=p.read_bytes()
        history=(ROOT/'backend/data/history'/id).resolve()
        assert history.parent==(ROOT/'backend/data/history').resolve()
        for p in history.glob('*.json'):owned[p]=p.read_bytes()
    try:
        listeners=[]
        for connection in psutil.net_connections(kind='tcp'):
            if connection.status=='LISTEN' and connection.laddr.port in (5173,8000):
                process=psutil.Process(connection.pid)
                listeners.append({'port':connection.laddr.port,'pid':connection.pid,'cwd':process.cwd(),'command':process.cmdline()})
        report['processes']=listeners
        assert len(listeners)==2
        assert all(Path(p['cwd']).resolve() in (ROOT,ROOT/'frontend') for p in listeners)
        with urlopen(BASE+'/src/App.tsx') as response:
            served=response.read().decode();report['frontend_headers']=dict(response.headers)
        assert 'ContextBar' in served and 'v0.3' not in served
        with urlopen(BASE) as response:assert '/@vite/client' in response.read().decode()
        report['health']=api('/api/health')
        check('Correct process folders; live Vite source (not stale dist); backend health',listeners)
        pilot=api('/api/examples/kayseri')
        assert all(p['loaded'] for p in pilot['projects']), 'Pilot must already be loaded; this test does not install user data.'
        campus_id,housing_id,office_id,hotel_id=[p['id'] for p in pilot['projects']]
        project_data={id:api(project=id)['campus'] for id in (campus_id,housing_id,office_id,hotel_id)}
        options=webdriver.ChromeOptions()
        options.add_argument('--headless=new');options.add_argument('--window-size=1536,1100')
        downloads=(OUT/'downloads'/uuid4().hex[:8]);downloads.mkdir(parents=True)
        options.add_experimental_option('prefs',{'download.default_directory':str(downloads.resolve()),'download.prompt_for_download':False})
        options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
        with webdriver.Chrome(options=options) as d:
            wait=WebDriverWait(d,45,ignored_exceptions=(StaleElementReferenceException,))
            def css(selector):return d.find_element(By.CSS_SELECTOR,selector)
            def ready():wait.until(lambda _:d.find_elements(By.ID,'project-select') and css('#project-select').is_enabled())
            def page(label):
                button=wait.until(lambda _:d.find_element(By.XPATH,f'//nav/button[contains(.,"{label}")]'))
                button.click()
                wait.until(lambda _:button.get_attribute('aria-current')=='page')
            def project(id,count):
                ready();Select(css('#project-select')).select_by_value(id)
                wait.until(lambda _:len(d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))==count and css('#project-select').is_enabled() and css('#project-select').get_attribute('value')==id)
            def building(id,name):
                ready();page('Bina detayları');Select(css('#building-select')).select_by_value(id)
                wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.detail-header h2') and css('.detail-header h2').text==name)
                wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.package-table tbody tr'))
            def theme(value):
                Select(css('#theme-select')).select_by_value(value)
                wait.until(lambda _:d.execute_script('return document.documentElement.dataset.theme')==value)
            def viewport(width):
                d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1100 if width>=1000 else 1000,'deviceScaleFactor':1,'mobile':False})
            def shot(name,selector=None):
                if selector:
                    element=css(selector)
                    d.execute_script("arguments[0].scrollIntoView({block:'start'})",element)
                    element.screenshot(str(OUT/(name+'.png')))
                else:
                    d.execute_script('window.scrollTo(0,0)')
                    d.save_screenshot(str(OUT/(name+'.png')))
                report['screenshots'].append({'file':name+'.png','project':css('#project-select').get_attribute('value'),'building':css('#building-select').get_attribute('value') if d.find_elements(By.ID,'building-select') else css('.single-building').text,'theme':css('#theme-select').get_attribute('value'),'width':d.execute_script('return innerWidth')})
            def no_overflow(label):
                issues=d.execute_script("""
                  const width=innerWidth;
                  return [...document.querySelectorAll('body *')].filter(e=>{
                    const r=e.getBoundingClientRect();if(!r.width||!r.height)return false;
                    if(e.closest('.table-scroll,.chart-scroll,pre,.sr-only'))return false;
                    return r.right>width+1||r.left< -1;
                  }).map(e=>({tag:e.tagName,cls:e.className,right:e.getBoundingClientRect().right})).slice(0,15);
                """)
                assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth'),(label,issues)
                assert not issues,(label,issues)
            d.get(BASE);ready()
            viewport(1536)
            project(campus_id,4)
            for t in ('nature','night','earth'):
                theme(t);d.refresh();ready()
                assert css('#theme-select').get_attribute('value')==t
                shot('desktop-'+t)
                assert not d.find_elements(By.XPATH,'//*[text()="v0.3 · kullanıcı hesabı içermez"]')
                # Actual computed contrast in common text and primary controls.
                contrasts=d.execute_script("""
                  const luminance=c=>{const v=c.match(/[\\d.]+/g).slice(0,3).map(Number).map(v=>v/255).map(v=>v<=.04045?v/12.92:((v+.055)/1.055)**2.4);return v[0]*.2126+v[1]*.7152+v[2]*.0722};
                  return ['h1','.page-heading p','.context-bar label','.metric-title','.button.primary','.nav-item.active','.synthetic-banner','.text-button'].map(s=>{
                    const e=document.querySelector(s),a=getComputedStyle(e);
                    let p=e,b=a.backgroundColor;
                    while(b==='rgba(0, 0, 0, 0)'&&p.parentElement){p=p.parentElement;b=getComputedStyle(p).backgroundColor}
                    const x=luminance(a.color),y=luminance(b);return {selector:s,ratio:(Math.max(x,y)+.05)/(Math.min(x,y)+.05)};
                  })
                """)
                assert all(c['ratio']>=4.5 for c in contrasts),(t,contrasts)
                check('Theme persists and common text contrast ≥4.5: '+t,contrasts)
            theme('nature')
            # The older campus remains a separate project with its own eight buildings.
            project('campus-demo-25',8)
            assert 'Önceki örnek kampüs' in Select(css('#project-select')).first_selected_option.text
            project(campus_id,4)
            for b in project_data[campus_id]['buildings'][:2]:
                building(b['id'],b['name'])
                assert b['name']==Select(css('#building-select')).first_selected_option.text
                wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
                shot('detail-'+b['id'])
                shot('floors-'+b['id'],'.spatial-detail')
            # Deliberately delay the old building's requests, then change building.
            d.execute_script("""
              window.originalFetch=window.fetch;
              window.fetch=async (...args)=>{
                const response=await window.originalFetch(...args);
                if(String(args[0]).includes('/buildings/B01/'))await new Promise(r=>setTimeout(r,1600));
                return response;
              }
            """)
            Select(css('#building-select')).select_by_value('B01')
            Select(css('#building-select')).select_by_value('B02')
            wait.until(lambda _:css('.detail-header h2').text==project_data[campus_id]['buildings'][1]['name'])
            time.sleep(2)
            assert css('.detail-header h2').text==project_data[campus_id]['buildings'][1]['name']
            assert 'B02' in css('.detail-header .eyebrow').text
            wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody [data-energy]'))
            total=sum(float(e.get_attribute('data-energy')) for e in d.find_elements(By.CSS_SELECTOR,'.distribution-table tbody [data-energy]'))
            expected=api('/api/buildings/B02/spatial',campus_id)['baseline']['totals']['electricity_kwh_year']
            assert abs(total-expected)<1e-5,(total,expected)
            d.execute_script('window.fetch=window.originalFetch')
            check('Two campus buildings; delayed old-building requests cannot replace new context')
            d.find_element(By.XPATH,'//div[@class="spatial-tabs"]/button[text()="Müdahale Senaryoları"]').click()
            css('input[name="spatial.lighting"]').click()
            Select(css('#building-select')).select_by_value('B01')
            wait.until(lambda _:d.find_elements(By.XPATH,'//button[text()="Kal"]')).pop().click()
            assert css('#building-select').get_attribute('value')=='B02'
            Select(css('#building-select')).select_by_value('B01')
            d.find_element(By.XPATH,'//button[text()="Vazgeç ve devam et"]').click()
            wait.until(lambda _:css('.detail-header h2').text==project_data[campus_id]['buildings'][0]['name'])
            check('Building switch offers stay/discard for unsaved spatial draft; no original record saved')
            project(housing_id,2)
            for b in project_data[housing_id]['buildings']:
                building(b['id'],b['name'])
                wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
                assert css('.detail-header h2').text==b['name']
            viewport(390);shot('mobile-building-selection')
            check('Housing project and A/B block selection')
            project(office_id,1);assert not d.find_elements(By.ID,'building-select')
            assert 'tek binalı proje' in css('.building-context').text
            page('Bina detayları');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
            assert css('.detail-header h2').text==project_data[office_id]['buildings'][0]['name']
            page('Senaryo girdileri')
            assert not d.find_elements(By.XPATH,'//h1[contains(.,"Kampüs")]')
            check('Single-building office has explicit static name; no ineffective building selector')
            # A separate QA project is the only record written by the acceptance flow.
            qa=api('/api/projects',office_id,{'name':'UI doğrulama · ofis '+uuid4().hex[:6],'building_ids':['B07'],'connection_mode':'independent'})['id']
            capture_owned(qa)
            d.refresh();ready();project(qa,1);page('Senaryo girdileri')
            css('.compute-button').click()
            wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.plan-table tbody tr'));capture_owned(qa)
            wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.load-chart'))
            snapshot=api(project=qa)
            css('.export-menu summary').click()
            Select(css('select[aria-label="Dışa aktarım türü"]')).select_by_value('result')
            d.find_element(By.XPATH,'//div[@class="export-menu-content"]/button[text()="JSON"]').click()
            exported=wait.until(lambda _:list(downloads.glob('*.json')))
            export=json.loads(exported[0].read_text(encoding='utf-8-sig'))
            assert export['calculation_id']==snapshot['calculation_id']
            assert export['campus']['id']==qa
            css('.export-menu summary').click()
            check('Actual JSON download matches displayed calculation/project',{'calculation_id':snapshot['calculation_id'],'file':str(exported[0].relative_to(OUT))})
            for t in ('nature','night','earth'):
                theme(t)
                for label in ('Bina detayları','Senaryo girdileri','Optimizasyon sonucu','Model ve veri'):
                    page(label)
                    if label=='Bina detayları':
                        wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.spatial-tabs'))
                        for tab in ('Katlar','Enerji Dağılımı','Müdahale Senaryoları'):
                            d.find_element(By.XPATH,f'//div[@class="spatial-tabs"]/button[text()="{tab}"]').click()
                            for w in (390,768,1280,1536):
                                viewport(w);no_overflow((t,tab,w))
                        if t=='night':shot('interventions-night','.spatial-detail')
                    if label=='Optimizasyon sonucu':wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.load-chart'))
                    for width in (390,500,768,1280,1536):
                        viewport(width);no_overflow((t,label,width))
                        if t=='nature' and width in (768,1280) and label in ('Bina detayları','Senaryo girdileri','Optimizasyon sonucu'):
                            shot(f'{label.split()[0]}-{width}')
                    if label=='Senaryo girdileri':
                        viewport(390);css('.export-menu summary').click()
                        no_overflow((t,'open export menu',390))
                        css('.export-menu summary').click()
                page('Optimizasyon sonucu');shot('results-'+t)
                shot('chart-'+t,'.chart-panel')
            check('All three themes; details/scenario/results/model at 390,500,768,1280,1536; no page overflow')
            theme('nature');viewport(1536)
            page('Senaryo girdileri');shot('scenario');shot('scenario-form','.scenario-layout')
            # Pending form guard: stay, reload restore, discard; only QA save.
            budget=css('input[name="budget_try"]')
            old=budget.get_attribute('value')
            budget.send_keys(Keys.CONTROL,'a');budget.send_keys('1234567')
            Select(css('#project-select')).select_by_value(campus_id)
            wait.until(lambda _:d.find_elements(By.XPATH,'//h2[text()="Kaydedilmemiş değişiklikler"]'))
            d.find_element(By.XPATH,'//button[text()="Kal"]').click()
            assert css('#project-select').get_attribute('value')==qa
            assert css('input[name="budget_try"]').get_attribute('value')=='1234567'
            d.find_element(By.XPATH,'//button[text()="Veriyi yenile"]').click()
            wait.until(lambda _:d.find_elements(By.XPATH,'//button[text()="Kal"]')).pop().click()
            assert css('input[name="budget_try"]').get_attribute('value')=='1234567'
            d.refresh();ready();page('Senaryo girdileri')
            assert css('input[name="budget_try"]').get_attribute('value')=='1234567'
            Select(css('#project-select')).select_by_value(campus_id)
            d.find_element(By.XPATH,'//button[text()="Vazgeç ve devam et"]').click()
            wait.until(lambda _:css('#project-select').get_attribute('value')==campus_id and css('#project-select').is_enabled())
            project(qa,1);page('Senaryo girdileri')
            assert css('input[name="budget_try"]').get_attribute('value')==old
            budget=css('input[name="budget_try"]');budget.send_keys(Keys.CONTROL,'a');budget.send_keys('1234567')
            Select(css('#project-select')).select_by_value(campus_id)
            d.find_element(By.XPATH,'//button[text()="Kaydet ve devam et"]').click()
            wait.until(lambda _:css('#project-select').get_attribute('value')==campus_id and css('#project-select').is_enabled())
            capture_owned(qa);assert api(project=qa)['campus']['scenario']['budget_try']==1234567
            project(qa,1);page('Optimizasyon sonucu')
            assert css('.stale-panel').is_displayed()
            css('.export-menu summary').click()
            Select(css('select[aria-label="Dışa aktarım türü"]')).select_by_value('result')
            assert all(not e.is_enabled() for e in d.find_elements(By.CSS_SELECTOR,'.export-menu-content button'))
            css('.export-menu summary').click()
            check('Save/discard/stay for project switch; refresh guard; reload draft restore; old result stale')
            # No AI button is invoked: panels/status only, no paid provider calls.
            project(campus_id,4);building('B01',project_data[campus_id]['buildings'][0]['name'])
            viewport(390);shot('mobile-detail')
            viewport(1536);d.execute_script('window.scrollTo(0,0)')
            css('#theme-select').send_keys(Keys.TAB)
            focused=d.execute_script('return {tag:document.activeElement.tagName,outline:getComputedStyle(document.activeElement).outlineStyle}')
            assert focused['outline']!='none',focused
            d.find_element(By.XPATH,'//header//button[text()="Uygulama hakkında"]').click()
            assert 'Kullanıcı hesabı' in css('dialog').text
            shot('about-modal','dialog')
            css('dialog button[aria-label="Pencereyi kapat"]').click()
            # Simulate an absent pilot listing without changing any server record.
            d.execute_script("""
              const realFetch=window.fetch;
              window.fetch=async (...args)=>{
                const response=await realFetch(...args);
                if(String(args[0]).includes('/api/examples/kayseri?')){
                  const body=await response.json();body.projects.forEach(p=>p.loaded=false);
                  return new Response(JSON.stringify(body),{status:200,headers:{'Content-Type':'application/json'}});
                }return response;
              };
            """)
            d.find_element(By.XPATH,'//button[text()="Veriyi yenile"]').click();ready()
            wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.pilot-missing'))
            css('.pilot-missing button').click()
            assert css('.install-pilot').is_displayed()
            check('Missing-pilot explanation opens the existing explicit loader (response stub, no data install)')
            d.refresh();ready()
            check('Keyboard focus visible and account/version details in About dialog')
            report['console']=d.get_log('browser')
            assert not [e for e in report['console'] if e['level']=='SEVERE'],report['console']
            check('No severe browser console errors')
        assert all(path.exists() and path.read_bytes()==value for path,value in original.items())
        check('Every original JSON input/result/history byte-for-byte preserved',len(original))
    finally:
        for path,value in owned.items():
            assert path.resolve().is_relative_to((ROOT/'backend/data').resolve())
            if path.exists() and path.read_bytes()==value:
                target=OUT/'qa-archive'/path.relative_to(ROOT/'backend/data')
                target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(value);path.unlink()
            elif path.exists():print('Preserved concurrently changed QA file:',path.name)
        report['original_hashes']={str(p.relative_to(ROOT)):hashlib.sha256(value).hexdigest() for p,value in original.items()}
        report['originals_unchanged']=all(p.exists() and p.read_bytes()==v for p,v in original.items())
        (OUT/'browser-report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')

if __name__=='__main__':run()
