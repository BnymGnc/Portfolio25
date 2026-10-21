"""Bounded matched annual subset: CO/NY/TX, first 3 counties, 4 upgrades.

Maximum 8 MB compressed downloads, never national files or timeseries. All matching
uses bldg_id; weighted TBtu gas is converted back using its own row's weight.
"""
import csv,gzip,hashlib,io,json,tarfile,urllib.request,urllib.parse,xml.etree.ElementTree as ET
from pathlib import Path
BASE='https://oedi-data-lake.s3.amazonaws.com/'
PREFIX='nrel-pds-building-stock/end-use-load-profiles-for-us-building-stock/2025/comstock_amy2018_release_3/'
OUT=Path(__file__).resolve().parents[1]/'backend/ml_assets/comstock-small';OUT.mkdir(parents=True,exist_ok=True)
TYPES={'PrimarySchool','SecondarySchool','SmallOffice','MediumOffice','LargeOffice','SmallHotel','LargeHotel'}
report={'release':'2025/comstock_amy2018_release_3','source_kind':'external_simulation','weather':'AMY2018, United States','states':['CO','NY','TX'],'max_compressed_bytes':8000000,'downloaded_compressed_bytes':0,'files':[],'upgrades':{'0':'Baseline','16':'HP Boiler, Gas Backup','43':'LED Lighting','49':'Roof Insulation'},'targets':['electricity_kwh_year','gas_kwh_year'],'gas_conversion':'calc.weighted.natural_gas.total.energy_consumption..tbtu × 293071070.1722222 / weight','electricity':'out.electricity.purchased.energy_consumption..kwh; selected upgrades have no PV','license_source':'https://natlabrockies.github.io/ComStock.github.io/docs/citation.html','documentation':'https://natlabrockies.github.io/ComStock.github.io/docs/data.html'}
def fetch(key,maxsize=1000000):
 with urllib.request.urlopen(BASE+key,timeout=15) as r:data=r.read(maxsize+1)
 if len(data)>maxsize:raise ValueError('Single file inspection budget exceeded')
 return data
def rows(key):
 data=fetch(key);report['downloaded_compressed_bytes']+=len(data)
 if report['downloaded_compressed_bytes']>8000000:raise ValueError('Download budget exceeded')
 report['files'].append({'key':key,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()})
 plain=gzip.decompress(data)
 if len(plain)>20000000:raise ValueError('Expanded file too large')
 if plain[257:262]==b'ustar':
  with tarfile.open(fileobj=io.BytesIO(plain),mode='r:') as tar:
   member=next(m for m in tar if m.isfile() and m.name.endswith('.csv'));plain=tar.extractfile(member).read()
 return list(csv.DictReader(io.StringIO(plain.decode('utf-8-sig'))))
def num(row,key):return float(row[key])
def energy(row):return [num(row,'out.electricity.purchased.energy_consumption..kwh'),num(row,'calc.weighted.natural_gas.total.energy_consumption..tbtu')*293071070.1722222/num(row,'weight')]
result=[]
for state in report['states']:
 prefix=PREFIX+'metadata_and_annual_results/by_state_and_county/basic/csv/state='+state+'/'
 xml=fetch('?list-type=2&delimiter=/&max-keys=3&prefix='+urllib.parse.quote(prefix),50000)
 tree=ET.fromstring(xml);ns={'s':'http://s3.amazonaws.com/doc/2006-03-01/'}
 counties=[n.find('s:Prefix',ns).text for n in tree.findall('s:CommonPrefixes',ns)]
 for folder in counties:
  county=folder.rstrip('/').split('=')[-1]
  def key(upgrade):return folder+f'{state}_{county}_upgrade{upgrade}_basic.csv.gz'
  try:
   baseline={r['bldg_id']:r for r in rows(key(0)) if r['in.comstock_building_type'] in TYPES}
   for upgrade in (0,16,43,49):
    variants=list(baseline.values()) if upgrade==0 else rows(key(upgrade))
    for row in variants:
     old=baseline.get(row['bldg_id'])
     if not old or (upgrade and row.get('applicability','').lower() not in ('true','1','1.0')):continue
     try:
      old_e,old_g=energy(old);new_e,new_g=energy(row);area=num(old,'in.sqft..ft2')*.09290304
      if min(old_e,old_g,new_e,new_g)<0 or area<=0:continue
      result.append({'building_id':old['bldg_id'],'features':{'area_m2':area,'year_built':int(float(old['in.year_built'])),'building_type':old['in.comstock_building_type'],'climate_zone':old['in.as_simulated_ashrae_iecc_climate_zone_2006'],'hvac_system':old['in.hvac_system_type'],'baseline_electricity_kwh_year':old_e,'baseline_gas_kwh_year':old_g,'upgrade':str(upgrade)},'targets':[new_e,new_g]})
     except (ValueError,KeyError,ZeroDivisionError):continue
  except Exception as error:
   report.setdefault('skipped',[]).append({'county':county,'reason':type(error).__name__})
report['rows']=len(result);report['building_groups']=len({r['building_id'] for r in result});report['building_types']=sorted({r['features']['building_type'] for r in result})
data=''.join(json.dumps(r,ensure_ascii=False)+'\n' for r in result)
(OUT/'data.jsonl').write_text(data,encoding='utf-8');report['dataset_sha256']=hashlib.sha256(data.encode()).hexdigest()
(OUT/'source.json').write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({k:report[k] for k in ('rows','building_groups','downloaded_compressed_bytes','building_types')},ensure_ascii=True))
