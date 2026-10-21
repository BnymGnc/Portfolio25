"""Exercise cold-start/proxy errors and recovery in Chrome, on local QA data only.

No paid API calls. An isolated temporary account is removed after the test;
existing JSON records are compared by SHA-256. Never prints credential/token values.
"""
import hashlib,json,secrets,shutil,sqlite3
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

ROOT=Path(__file__).resolve().parents[1];OUT=ROOT/'artifacts/auth-recovery';OUT.mkdir(parents=True,exist_ok=True)
original={p:hashlib.sha256(p.read_bytes()).hexdigest() for p in (ROOT/'backend/data').rglob('*.json')}
email='qa-recovery-'+secrets.token_hex(6)+'@example.test';password=secrets.token_urlsafe(24);uid=None
options=webdriver.ChromeOptions();options.add_argument('--headless=new');options.add_argument('--disable-gpu');options.add_argument('--window-size=1440,1000');options.set_capability('goog:loggingPrefs',{'browser':'ALL'})
d=webdriver.Chrome(options=options);wait=WebDriverWait(d,60);report={'checks':[],'completed':False}
d.execute_cdp_cmd('Page.addScriptToEvaluateOnNewDocument',{'source':"""
 const fetchOriginal=window.fetch.bind(window);let sessionFailure=true,registerFailure=true;
 window.authQa={registerCalls:0};
 window.fetch=(url,options={})=>{
  if(String(url).includes('/api/auth/session')&&sessionFailure){sessionFailure=false;return Promise.resolve(new Response('An error occurred with this application',{status:502,headers:{'Content-Type':'text/plain'}}))}
  if(String(url).includes('/api/auth/register')){
   window.authQa.registerCalls++;
   if(registerFailure){registerFailure=false;return Promise.resolve(new Response('<html>Proxy unavailable</html>',{status:503,headers:{'Content-Type':'text/html'}}))}
  }
  return fetchOriginal(url,options);
 };
"""})
def css(s):return d.find_element(By.CSS_SELECTOR,s)
def click(label):
 e=wait.until(lambda _:next((x for x in d.find_elements(By.TAG_NAME,'button') if label in x.text and x.is_displayed() and x.is_enabled()),None));e.click()
try:
 d.get('http://127.0.0.1:5173/');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-error'))
 assert 'Sunucu' in css('.auth-error').text and 'Unexpected' not in css('.auth-error').text
 assert 'Ücretsiz demo sunucusu' in css('.auth-server-note').text
 click('Kayıt olun');css('#auth-email').send_keys(email);css('#auth-password').send_keys(password,Keys.ENTER)
 wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.auth-error'))
 assert '503' in css('.auth-error').text and '<html>' not in css('.auth-error').text
 assert d.execute_script('return window.authQa.registerCalls')==1
 assert css('#auth-password').get_attribute('value')==password
 for width in (390,1440):
  d.execute_cdp_cmd('Emulation.setDeviceMetricsOverride',{'width':width,'height':1000,'deviceScaleFactor':1,'mobile':False})
  assert d.execute_script('return document.documentElement.scrollWidth<=innerWidth+1')
  d.save_screenshot(str(OUT/f'friendly-error-{width}.png'))
 click('Bağlantıyı yeniden dene');wait.until(lambda _:not d.find_elements(By.CSS_SELECTOR,'.auth-error') and css('#auth-email').is_enabled())
 assert css('#auth-email').get_attribute('value')==email and css('#auth-password').get_attribute('value')==password
 assert d.execute_script('return window.authQa.registerCalls')==1
 report['checks'].append('Initial text 502 and registration HTML 503 show safe Turkish errors; manual GET recovery retains both inputs without retrying registration')
 click('Hesap oluştur');wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'dialog.onboarding[open]'));click('Tanıtımı atla')
 wait.until(lambda _:d.find_elements(By.CSS_SELECTOR,'.inventory-panel tbody tr'))
 with sqlite3.connect(ROOT/'backend/data/accounts.sqlite3') as db:uid=db.execute('SELECT id FROM users WHERE email=?',(email,)).fetchone()[0]
 assert d.execute_script('return window.authQa.registerCalls')==2
 assert not d.find_elements(By.CSS_SELECTOR,'.pilot-card,.sidebar-footer,.flow-steps')
 d.save_screenshot(str(OUT/'compact-overview.png'))
 report['checks'].append('A second explicit submit registers successfully and loads real private pilot; duplicate sidebar content is absent')
 report['uncaught_errors']=sum('Uncaught' in e['message'] for e in d.get_log('browser'));assert report['uncaught_errors']==0
 report['completed']=True
finally:
 d.quit()
 if uid:
  with sqlite3.connect(ROOT/'backend/data/accounts.sqlite3') as db:
   assert db.execute('SELECT email FROM users WHERE id=?',(uid,)).fetchone()[0]==email
   bucket='email:'+hashlib.sha256(email.encode()).hexdigest();moments=[r[0] for r in db.execute('SELECT moment FROM attempts WHERE bucket=?',(bucket,))]
   db.executemany('DELETE FROM attempts WHERE moment=? AND (bucket=? OR bucket=?)',[(m,bucket,'ip:127.0.0.1') for m in moments])
   db.execute('DELETE FROM sessions WHERE user_id=?',(uid,));db.execute('DELETE FROM users WHERE id=?',(uid,))
  parent=(ROOT/'backend/data/users').resolve();target=(parent/uid).resolve();assert target.parent==parent and len(uid)==32
  if target.exists():shutil.copytree(target,OUT/'qa-records',dirs_exist_ok=True);shutil.rmtree(target)
 report['original_json_unchanged']=all(p.exists() and hashlib.sha256(p.read_bytes()).hexdigest()==h for p,h in original.items());assert report['original_json_unchanged']
 (OUT/'report.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8');print(json.dumps(report),flush=True)
