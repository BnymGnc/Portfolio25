import copy,json
from test_accounts import AccountTests
from pilot_kayseri import create_pilot
from intakes import Intake,BuildingInput,Consumption,CSVBody,csv_preview,CSV_HEADER
from engine import calculate
from models import CalculationRequest

class IntakeTests(AccountTests):
    def ready(self,client):
        assumptions=client.get('/api/intakes/options').json()['example_assumptions']
        return Intake(name='Private actual building',budget_try=1e6,electricity_price=4,gas_price=1.5,tariff_source='User bill 2025',profile_consent=True,buildings=[BuildingInput(name='My building',location='Kayseri',area_m2=1000,year=2025,heating_system='gas_boiler',system_scope='individual',heat_distribution='low_temperature_water',electricity=Consumption(value=100000,source_kind='measured'),fuel=Consumption(value=200000,source_kind='measured'),heating_gas_fraction=.8,heating_split_source='User heating/DHW split estimate',connection_kw=200,connection_source='User agreement',assumptions=assumptions,quotes={'insulation':{'amount_try':100000,'kind':'user_quote','source':'Supplier offer','reference_date':'2026-10-23','scope':'Whole envelope, explicit quote; not inferred from floor area'}})])
    def test_nullable_draft_owner_and_physical_publish(self):
        a,_=self.account('own-a');b,_=self.account('own-b')
        empty=Intake().model_dump(mode='json');saved=a.post('/api/intakes',json=empty)
        self.assertEqual(saved.status_code,200,saved.text);raw=saved.json()['draft'];self.assertIsNone(raw['buildings'][0]['area_m2'])
        self.assertEqual(b.get('/api/intakes').json(),[])
        self.assertEqual(a.post('/api/intakes/'+raw['id']+'/publish',json=raw).status_code,422)
        self.assertEqual(b.put('/api/intakes/'+raw['id'],json=raw).status_code,404)
        d=self.ready(a).model_dump(mode='json');saved=a.post('/api/intakes',json=d).json()['draft']
        published=a.post('/api/intakes/'+saved['id']+'/publish',json=saved)
        self.assertEqual(published.status_code,200,published.text);pid=published.json()['draft']['project_id'];params={'project_id':pid}
        snap=a.get('/api/campus/snapshot',params=params);self.assertEqual(snap.status_code,200,snap.text)
        campus=snap.json()['campus'];self.assertEqual(campus['buildings'][0]['heating_kwh_year'],160000);self.assertAlmostEqual(campus['buildings'][0]['non_heating_gas_kwh_year'],40000)
        self.assertIsNone(campus['buildings'][0]['spatial']);self.assertIsNone(campus['buildings'][0]['year_built']);self.assertNotEqual(campus['provenance']['kind'],'synthetic')
        self.assertEqual(b.get('/api/campus/snapshot',params=params).status_code,404)
        result=a.post('/api/calculate',params=params,json={'revision':1,'mode':'A'});self.assertEqual(result.status_code,200,result.text)
        self.assertGreater(result.json()['energy_savings_kwh_year'],0)
        body=a.get('/api/buildings/B01/packages',params=params).json();options=body['packages']
        for option in options:self.assertAlmostEqual(body['group_impacts'][option['candidate_id']][0]['peak_kw'],option['electric_peak_kw'])
        p=next(p for p in options if p['candidate_id']=='insulation');self.assertEqual(p['investment_try'],100000)
        edit={k:campus[k] for k in __import__('main').CampusUpdate.model_fields};edit['buildings'][0]['cost_quotes']['insulation']['amount_try']=200000
        self.assertEqual(a.put('/api/campus',params=params,json=edit).status_code,200)
        after=a.get('/api/buildings/B01/packages',params=params).json()['packages'];q=next(p for p in after if p['candidate_id']=='insulation')
        self.assertEqual(q['investment_try'],200000);self.assertNotEqual(q['simple_payback_years'],p['simple_payback_years'])
        self.assertAlmostEqual(p['net_savings_try_year']-q['net_savings_try_year'],1500)
        self.assertEqual(q['energy_savings_kwh_year'],p['energy_savings_kwh_year'])
        run=a.post('/api/calculate',params=params,json={'revision':2,'mode':'A'}).json()
        investment_rows=[row for row in run['sensitivity']['rows'] if row['parameter']=='investment']
        low=next(row for row in investment_rows if row['level']=='low');high=next(row for row in investment_rows if row['level']=='high')
        self.assertLess(low['evaluation']['investment_try'],high['evaluation']['investment_try'])
        self.assertEqual(a.get('/api/export/html',params={**params,'scope':'result','revision':2,'expected_calculation_id':run['calculation_id']}).status_code,200)
        self.assertEqual(a.post('/api/intakes/'+saved['id']+'/publish',json=published.json()['draft']).status_code,409)
    def test_unknown_fuel_months_units_and_apartment_scope(self):
        a,_=self.account('scope')
        d=self.ready(a);d.buildings[0].heating_system='coal'
        raw=a.post('/api/intakes',json=d.model_dump(mode='json')).json();self.assertEqual(raw['readiness']['status'],'unsupported')
        self.assertEqual(a.post('/api/intakes/'+d.id+'/publish',json=d.model_dump(mode='json')).status_code,422)
        self.assertIsNone(Consumption(mode='monthly',months=[10]*11+[None]).annual())
        self.assertIsNone(Consumption(value=100,unit='m3').annual())
        self.assertEqual(Consumption(value=100,unit='m3',conversion_kwh_m3=10.4,conversion_source='Bill calorific content').annual(),1040)
        self.assertEqual(Consumption(mode='monthly',months=[10]*12).annual(),120)
        invalid=d.model_dump(mode='json');invalid['buildings'][0]['electricity']['unit']='m3';self.assertEqual(a.post('/api/intakes',json=invalid).status_code,422)
        d=self.ready(a);d.buildings[0].scope='apartment'
        from intakes import compile_project
        c=compile_project(d,'project-0123456789ab');r=calculate(c,CalculationRequest(revision=1))
        self.assertEqual(r.investment_try,0)
    def test_simple_csv_preview(self):
        header=','.join(CSV_HEADER)
        good='House,building,Konut,Kayseri,1000,2025,100000,200000,.8,User estimate,gas_boiler,individual,low_temperature_water,200,Agreement'
        result=csv_preview(CSVBody(text=header+'\n'+good+'\n'+good.replace('1000,2025','bad,2025')))
        self.assertEqual(len(result['buildings']),1);self.assertEqual(result['errors'][0]['row'],3)
