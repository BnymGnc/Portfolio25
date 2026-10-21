"""Small, bounded public metadata inspection. Never downloads annual bulk tables."""
import json,urllib.request,urllib.error,xml.etree.ElementTree as ET
from pathlib import Path
OUT=Path(__file__).resolve().parents[1]/'artifacts/improvements/comstock';OUT.mkdir(parents=True,exist_ok=True)
base='https://oedi-data-lake.s3.amazonaws.com/'
prefix='nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/comstock_amy2018_release_3/'
summary={'release':'2025/comstock_amy2018_release_3','scope':'İlk inceleme: sözlük ve müdahale eşlemesi; aday eğitim kapsamı en fazla 1000 ofis/okul/otel bina grubu, baz ve HP/kabuk müdahaleleri, yalnız yıllık elektrik/gaz. Saatlik veya tüm ulusal veri indirilmeyecek.','files':[]}
for name in ('data_dictionary.tsv','upgrades_lookup.json'):
 try:
  with urllib.request.urlopen(base+prefix+name,timeout=15) as r:data=r.read(2000001)
  if len(data)>2000000:raise ValueError('2 MB inceleme sınırı aşıldı')
  (OUT/name).write_bytes(data);summary['files'].append({'name':name,'bytes':len(data),'status':'downloaded'})
 except (urllib.error.URLError,ValueError) as e:summary['files'].append({'name':name,'status':'unavailable','reason':type(e).__name__})
try:
 url=base+'?list-type=2&max-keys=12&prefix='+urllib.parse.quote(prefix+'metadata_and_annual_results/')
 with urllib.request.urlopen(url,timeout=15) as r:data=r.read(100001)
 root=ET.fromstring(data);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
 summary['annual_candidates']=[{'key':n.find('s:Key',ns).text,'bytes':int(n.find('s:Size',ns).text)} for n in root.findall('s:Contents',ns)]
except (urllib.error.URLError,ET.ParseError):summary['annual_candidates']=[]
summary['decision']='Bu oturumda eşlenmiş bina/müdahale yıllık küçük eğitim alt kümesi hazırlanmadı. Sözlük/lookup erişim ve fizik özellik eşlemesi ayrıca doğrulanmalı; bulk veri indirilmedi. Deneysel sağlayıcı bağımsız sentetik simülasyonla etiketlenecek; ComStock ile eğitildiği iddia edilmeyecek.'
(OUT/'inspection.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps(summary,ensure_ascii=True))
