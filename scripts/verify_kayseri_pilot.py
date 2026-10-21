"""Reproduce pilot reports via the real API, using only temporary storage."""
import argparse
import json
import sys
import tempfile
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
import main
from fastapi.testclient import TestClient


def run(output_dir=None):
    previous=main.DATA_FILE;out=Path(output_dir) if output_dir else ROOT/'artifacts/pilot/reports';out.mkdir(parents=True,exist_ok=True);manifest=[]
    try:
        with tempfile.TemporaryDirectory() as directory:
            main.DATA_FILE=Path(directory)/'campus.json'
            with TestClient(main.app) as client:
                loaded=client.post('/api/examples/kayseri/load').json()
                for project in loaded['projects']:
                    params={'project_id':project['id']}
                    c=client.get('/api/campus',params=params).json()['campus'];items=[]
                    for b in c['buildings']:
                        analysis=client.get(f'/api/buildings/{b["id"]}/spatial',params=params);analysis.raise_for_status()
                        (out/f'{b["id"]}-analysis.json').write_text(json.dumps(analysis.json(),ensure_ascii=False,indent=2),encoding='utf-8')
                        payload={'revision':c['revision'],'selection':{'roof':True,'lighting':True},'package':'heat_pump'}
                        if b['use_type'] in ('Eğitim','İdari','Ofis'):payload['selection'].update(schedule=True,schedule_review_ack=True)
                        preview=client.post(f'/api/buildings/{b["id"]}/spatial/evaluate',params=params,json=payload);preview.raise_for_status()
                        value=preview.json();(out/f'{b["id"]}-combined.json').write_text(json.dumps(value,ensure_ascii=False,indent=2),encoding='utf-8')
                        items.append({'id':b['id'],'name':b['name'],'recommendations':{r['id']:r['status'] for r in analysis.json()['recommendations']},
                            'preview':{k:value[k] for k in ('electricity_savings_kwh_year','fuel_savings_kwh_year','investment_try','net_savings_try_year','capacity_met','review_required')}})
                    plans={}
                    for mode in ('A','B'):
                        response=client.post('/api/calculate',params=params,json={'revision':1,'mode':mode});response.raise_for_status()
                        r=response.json();snapshot=client.get('/api/campus/snapshot',params=params).json()
                        exported=client.get('/api/export/json',params={**params,'scope':'result','revision':1,'expected_calculation_id':snapshot['calculation_id']});exported.raise_for_status()
                        (out/f'{c["pilot"]["project_key"]}-{mode}-result.json').write_bytes(exported.content)
                        plans[mode]={k:r[k] for k in ('status','investment_try','energy_savings_kwh_year','energy_savings_pct','target_met')}
                        if r['after']:assert all(check['violation_hours']==0 for check in r['after']['capacity_checks'])
                    manifest.append({'project':project,'buildings':items,'plans':plans})
    finally:main.DATA_FILE=previous
    (out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps([{p['project']['name']:p['plans']} for p in manifest],ensure_ascii=True,indent=2))


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir',help='Write a new evidence folder without replacing earlier reports.')
    run(parser.parse_args().output_dir)
