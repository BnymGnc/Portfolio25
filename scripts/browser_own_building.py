"""Own-building UI acceptance against local real backend; no external LLM calls.
Creates one isolated QA identity; never touches another account or reads .env.
"""
import json,secrets,time,os
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait,Select
BASE='http://127.0.0.1:5173';OUT=Path('artifacts/own-building-ui');OUT.mkdir(parents=True,exist_ok=True)
options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--disable-gpu');options.page_load_strategy='eager';options.add_argument('--window-size=1440,1000');options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
from selenium.webdriver.chrome.service import Service
d=webdriver.Chrome(service=Service(os.environ['SE_CHROMEDRIVER']),options=options);d.set_page_load_timeout(40);d.set_script_timeout(90);wait=WebDriverWait(d,60)
report={'completed':False,'llm_called':False,'checks':[]};creds={'email':'qa-own-ui-'+secrets.token_hex(7)+'@example.test','password':secrets.token_urlsafe(24)}
def call(path,body=None,method=None):
 return d.execute_async_script("""const [path,body,method,done]=arguments;fetch('/api/auth/session').then(r=>r.json()).then(s=>fetch(path,{method:method||(body?'POST':'GET'),credentials:'include',headers:{'Content-Type':'application/json','X-CSRF-Token':s.csrf},body:body?JSON.stringify(body):undefined})).then(async r=>done({status:r.status,body:await r.json()})).catch(e=>done({error:String(e)}))""",path,body,method)
def css(s):return d.find_element(By.CSS_SELECTOR,s)
def button(text):return wait.until(lambda _:next((x for x in d.find_elements(By.TAG_NAME,'button') if x.is_displayed() and x.is_enabled() and text in x.text),None))
def click(text):
 e=button(text);d.execute_script("arguments[0].scrollIntoView({block:'center'})",e);e.click()
def field(text,tag='input'):
 return next(e for e in d.find_elements(By.XPATH,'//label[contains(.,"'+text+'")]/'+tag) if e.is_displayed())
def fill(label,value):
 e=field(label);e.clear();e.send_keys(str(value))
def select(label,value):
 wait.until(lambda _:any(o.get_attribute('value')==str(value) for o in Select(field(label,'select')).options));Select(field(label,'select')).select_by_value(value)
def shot(name,width):
 d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False});time.sleep(.2)
 assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
 if name=='recommendations':d.execute_script("arguments[0].scrollIntoView({block:'start'})",css('.recommendation-grid'));time.sleep(.15)
 d.save_screenshot(str(OUT/(name+'-'+str(width)+'.png')))
def check(text):report['checks'].append(text);print('PASS:',text,flush=True)
try:
 print('Browser started',flush=True);d.get(BASE);print('Frontend opened',flush=True);result=call('/api/auth/register',creds);assert result['status']==200
 call('/api/auth/onboarding',{});d.refresh();wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.building-entry'))
 click('Kendi binamı ekle');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.own-building'))
 fill('Proje adı','QA own building');fill('Bina / daire adı','Actual input building');fill('Konum','Kayseri');fill('Brüt alan',1000)
 click('Taslağı kaydet');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.own-missing'))
 raw=call('/api/intakes')['body'][0]['draft'];assert raw['buildings'][0]['electricity']['value'] is None
 check('Manual wizard saves incomplete non-synthetic input without inventing consumption')
 for width in (390,1440):shot('building-input',width)
 # Complete the saved draft through the real API; inspect consumption and expert controls in UI.
 opts=call('/api/intakes/options')['body'];raw.update(budget_try=1000000,electricity_price=4,gas_price=1.5,tariff_source='QA bill 2025',profile_consent=True)
 b=raw['buildings'][0];b.update(year=2025,area_source='measured',heating_system='gas_boiler',system_scope='individual',heat_distribution='low_temperature_water',heating_gas_fraction=.8,heating_split_source='QA split assumption',connection_kw=200,connection_source='QA connection agreement',assumptions=opts['example_assumptions'],quotes={'insulation':{'amount_try':100000,'kind':'user_quote','source':'QA supplier quote','scope':'Whole building envelope','reference_date':'2026-10-23','currency':'TRY'}})
 b['electricity']['value']=100000;b['electricity']['source_kind']='measured';b['fuel']['value']=200000;b['fuel']['source_kind']='measured'
 result=call('/api/intakes/'+raw['id'],raw,'PUT');assert result['status']==200
 # Reopen from server to prove drafts are independent of local browser cache.
 css('dialog[open] .dialog-top .icon-button').click();click('Kendi binamı ekle');click('Sunucudaki kaydı aç');click('Tüketimler')
 wait.until(lambda _:field('Yıllık tüketim (kWh)').get_attribute('value')=='100000')
 for width in (390,1440):shot('consumption',width)
 click('Plan ve teklifler');click('Taslağı kaydet');wait.until(lambda _:button('Yatırım seçeneklerini aç').is_enabled())
 for width in (390,1440):shot('quotes-and-plan-input',width)
 click('Yatırım seçeneklerini aç');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.recommendation-card'))
 assert not d.find_elements(By.CSS_SELECTOR,'#detail-tab-floors');assert 'Actual input building' in css('h1').text
 for width in (390,1440):shot('recommendations',width)
 check('Saved own building publishes into real non-spatial project; eligible recommendation cards rendered at 390/1440')
 pid=call('/api/projects')['body']['projects'];pid=next(p['id'] for p in pid if p['name']=='QA own building')
 before=call('/api/campus/snapshot?project_id='+pid)['body'];assert before['campus']['provenance']['kind']!='synthetic'
 # Use actual visible plan flow and solver.
 nav=next(e for e in d.find_elements(By.CSS_SELECTOR,'nav button') if e.is_displayed() and 'Planım' in e.text);nav.click();click('Yatırım planını hesapla');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.result-metrics'))
 current=call('/api/campus/snapshot?project_id='+pid)['body'];assert current['calculation']['after']
 for width in (390,1440):shot('calculated-plan',width)
 # Real manual intervention preview and explicit evaluation, no AI provider call.
 context=current['context'];change={'field':'intervention','building_id':'B01','intervention':'insulation','value':'mandatory'}
 evaluated=call('/api/scenarios/evaluate?project_id='+pid,{'context':context,'changes':[change],'mode':'A'})
 assert evaluated['status']==200 and evaluated['body']['alternative']['after']
 assert call('/api/campus/snapshot?project_id='+pid)['body']==current
 check('Visible plan calculation and real transient intervention evaluation preserve main project; no LLM calls')
 report['completed']=True
except Exception:
 d.save_screenshot(str(OUT/'failure.png'));report['visible_error']=[x.text[:500] for x in d.find_elements(By.CSS_SELECTOR,'.error-box,.panel-error') if x.is_displayed()];raise
finally:
 try:report['uncaught_errors']=[x['message'][:200] for x in d.get_log('browser') if 'Uncaught' in x['message']]
 except Exception:report['uncaught_errors']=['Browser logs unavailable']
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');d.quit()
