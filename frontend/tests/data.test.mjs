import test from 'node:test';
import assert from 'node:assert/strict';
import { readFileSync } from 'node:fs';
import { campusFromCSV, parseCSV } from '../src/csv.ts';
import { validateProfiles } from '../src/profileData.ts';
import { solverLabel } from '../src/format.ts';
import {periodIndices} from '../src/chartSelection.ts';

const example = JSON.parse(readFileSync(new URL('../../docs/sample-campus.json', import.meta.url), 'utf8'));

test('Full-year selection includes the entire axis regardless of the selected start date',()=>{
 const stamps=Array.from({length:8760},(_,i)=>new Date(Date.parse('2025-01-01T00:00:00+03:00')+i*3600000).toISOString());
 assert.equal(periodIndices(stamps,'2025-06-01',366).length,8760);
 assert.equal(periodIndices(stamps,'2025-06-01',7).length,168);
});
const campus = example.campus;
const headers = ['id','name','use_type','area_m2','year_built','electricity_kwh_year','heating_kwh_year','peak_electric_kw','data_kind','source','seed','budget_try','savings_target_pct','electric_capacity_kw','electricity_price_try_kwh','heating_price_try_kwh'];
const quote = value => `"${String(value).replaceAll('"','""')}"`;
function fixture(change = () => {}) {
  const rows = campus.buildings.map(b => ({...b,...campus.scenario,data_kind:b.provenance.kind,source:b.provenance.source,seed:b.provenance.seed}));
  change(rows);
  return '\ufeff' + headers.join(',') + '\r\n' + rows.map(row=>headers.map(h=>quote(row[h])).join(',')).join('\r\n');
}
test('CSV roundtrip preserves eight buildings and handles quoted commas/newlines', () => {
  const c = campusFromCSV(fixture(rows => rows[0].name = 'Örnek, "Bina"\nKat 1'),campus);
  assert.equal(c.buildings.length,8);
  assert.equal(c.buildings[0].name,'Örnek, "Bina"\nKat 1');
  assert.equal(c.buildings[0].non_heating_gas_kwh_year,campus.buildings[0].non_heating_gas_kwh_year);
  assert.deepEqual(c.scenario,campus.scenario);
});
test('Invalid CSVs reject malformed quoting, fields, ids and numbers without mutation', () => {
  const original=JSON.stringify(campus);
  for(const content of ['id;name\nB01;X','"unclosed',fixture(r=>r.pop()),fixture(r=>r[1].id='B01'),fixture(r=>r[0].area_m2=0),fixture(r=>r[0].electricity_kwh_year='NaN'),fixture(r=>r[0].budget_try=2)]) {
    assert.throws(()=>campusFromCSV(content,campus));
  }
  assert.equal(JSON.stringify(campus),original);
  assert.throws(()=>parseCSV('a\n"x"bad'));
});
test('CSV cannot relabel synthetic provenance',()=>assert.throws(()=>campusFromCSV(fixture(r=>r[0].data_kind='measured'),campus),/sentetik/));
test('Malformed nested assumption JSON rejects before applying',()=>{
  const text=fixture().split('\r\n').map((line,i)=>line+','+(i===0?'retrofit_assumptions_json':quote('{bad'))).join('\r\n');
  assert.throws(()=>campusFromCSV(text,campus),/JSON/);
});
function profileFixture() {
  const data=structuredClone(example); data.profile_audit={...data.profile_audit,hour_count:2,start:'2025-01-01T00:00:00+03:00'};
  const result={input_revision:campus.revision,mode:'A',baseline:{electricity_kwh_year:30},after:{electricity_kwh_year:40}};
  const profile={input_revision:campus.revision,result_input_revision:campus.revision,result_mode:'A',kind:'synthetic',timezone:'Europe/Istanbul',interval_hours:1,capacity_kw:campus.scenario.electric_capacity_kw,timestamps:['2025-01-01T00:00:00+03:00','2025-01-01T01:00:00+03:00'],before_kw:[10,20],after_kw:[15,25]};
  return {data,result,profile};
}
test('Chart accepts aligned API totals and rejects missing hours, shifted times, NaN, stale revisions',()=>{
  const {data,result,profile}=profileFixture();
  assert.equal(validateProfiles(profile,data,result),profile);
  for(const mutate of [p=>p.after_kw.pop(),p=>p.timestamps[1]='2025-01-01T02:00:00+03:00',p=>p.before_kw[0]=NaN,p=>p.before_kw[0]=12,p=>p.result_input_revision++,p=>p.result_mode='B']) {
    const candidate=structuredClone(profile);mutate(candidate);assert.throws(()=>validateProfiles(candidate,data,result));
  }
});

test('Chart rejects another calculation or engine even when revision, mode and annual totals match',()=>{
 const {data,result,profile}=profileFixture();result.calculation_id='first';result.input_hash='inputs';result.engine_version='4.0.0';
 profile.calculation_id='first';profile.context={input_hash:'inputs',engine_version:'4.0.0'};
 assert.equal(validateProfiles(profile,data,result),profile);
 for(const change of [p=>p.calculation_id='second',p=>p.context.engine_version='future',p=>p.context.input_hash='changed']){
  const candidate=structuredClone(profile);change(candidate);assert.throws(()=>validateProfiles(candidate,data,result));
 }
});
test('Solver labels never promote limited or failed results to optimum',()=>{
  assert.equal(solverLabel({status:'optimal',solver:{optimality_proven:true}}),'Optimum çözüm bulundu');
  assert.equal(solverLabel({status:'feasible_limit',solver:{status_code:1,optimality_proven:false}}),'Süre sınırında uygun çözüm bulundu');
  assert.equal(solverLabel({status:'infeasible',solver:{}}),'Çözüm bulunamadı');
  assert.equal(solverLabel({status:'limit_no_solution',solver:{}}),'Süre sınırında çözüm bulunamadı');
  assert.notEqual(solverLabel({status:'optimal',solver:{optimality_proven:false}}),'Optimum çözüm bulundu');
});

test('Single-building CSV roundtrip and project identity protection',()=>{
  const single=structuredClone(campus);single.buildings=single.buildings.slice(0,1);
  const csv=fixture(rows=>rows.splice(1));
  assert.equal(campusFromCSV(csv,single).buildings.length,1);
  const other=csv.split('\r\n').map((line,i)=>line+','+(i===0?'project_json':quote(JSON.stringify({id:'project-000000000000'})))).join('\r\n');
  assert.throws(()=>campusFromCSV(other,single),/projeye/);
  assert.throws(()=>campusFromCSV(fixture(),single));
});

test('Independent connection profiles retain physical boundaries and reject cross-project data',()=>{
  const {data,result,profile}=profileFixture();
  data.campus.buildings=data.campus.buildings.slice(0,2);
  data.campus.buildings[0].electricity_kwh_year=10;data.campus.buildings[1].electricity_kwh_year=20;
  data.campus.connection_groups=[{id:'G01',building_ids:['B01'],capacity_kw:12},{id:'G02',building_ids:['B02'],capacity_kw:18}];
  result.selected_packages=[{building_id:'B01',electricity_kwh_year:15},{building_id:'B02',electricity_kwh_year:25}];
  profile.capacity_kw=null;
  profile.groups=[{id:'G01',capacity_kw:12,before_kw:[4,6],after_kw:[5,10]},{id:'G02',capacity_kw:18,before_kw:[6,14],after_kw:[10,15]}];
  assert.equal(validateProfiles(profile,data,result),profile);
  for(const mutate of [p=>p.groups[0].after_kw.pop(),p=>p.groups[0].capacity_kw=500,p=>p.groups[1].before_kw[0]=8,p=>p.project_id='project-000000000000']){
    const invalid=structuredClone(profile);mutate(invalid);assert.throws(()=>validateProfiles(invalid,data,result));
  }
});

test('Pilot CSV retains spatial selection and central system identity without applying result columns',()=>{
  const single=structuredClone(campus);single.buildings=single.buildings.slice(0,1);
  const spatial={schema_version:'1.0',floors:[{id:'F00',name:'Sentetik kat',zones:[{id:'Z001',heating_system_id:'H1'}]}],systems:[{id:'H1',served_zone_ids:['Z001']}]};
  const selection={roof:false,lighting:true,schedule:false,zone_ids:['Z001'],schedule_review_ack:false};
  const base=fixture(rows=>{rows.splice(1);rows[0].use_type='Ofis'});
  const csv=base.split('\r\n').map((line,i)=>line+','+(i===0?'spatial_model_json,spatial_selection_json':quote(JSON.stringify(spatial))+','+quote(JSON.stringify(selection)))).join('\r\n');
  const parsed=campusFromCSV(csv,single);
  assert.equal(parsed.buildings[0].use_type,'Ofis');
  assert.deepEqual(parsed.buildings[0].spatial,spatial);
  assert.deepEqual(parsed.buildings[0].spatial_selection,selection);
});
