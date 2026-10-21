"""Experimental surrogate of the local simulator, never a capacity/plan authority."""
import hashlib,json
from pathlib import Path
from pydantic import Field
from models import Model,PackageResult
from contracts import Context
from ml_service import AnnualPrediction
from typing import Literal
from spatial_energy import zones,annual_hours,can_schedule

ASSET_DIR=Path(__file__).parent/'ml_assets'/'synthetic-annual'
VERSION='synthetic-annual-1.1'
FEATURE_VERSION='spatial-inputs-1.0'
KINDS=('roof','insulation','lighting','schedule','heat_pump')
USES=('Eğitim','Araştırma','İdari','Konut','Ofis','Otel')
NAMES=['area','electricity','heating_gas','other_gas','boiler_efficiency','scop','hp_capacity','insulation_fraction','insulation_coverage','cooling','common_electricity','lighting_annual','lighting_reduction','device_annual','roof_area','roof_u','roof_target_u','wall_u','window_u','air_changes','service_hours','occupied_hours','schedule_eligible_area']+[f'use_{u}' for u in USES]+[f'action_{k}' for k in KINDS]
_loaded=None

def features(b,actions,year):
    zs=[z for _,z in zones(b)];a=b.area_m2
    avg=lambda fn:sum(z.area_m2*fn(z) for z in zs)/a
    roof=[z for z in zs if z.roof_contact];roof_area=sum(z.area_m2 for z in roof)
    rt=b.retrofit
    values=[a,b.electricity_kwh_year,b.heating_kwh_year,b.non_heating_gas_kwh_year,rt.boiler_efficiency,rt.heat_pump_scop,rt.heat_pump_capacity_kw_thermal,
        rt.insulation_reduction_fraction,rt.insulation_relevant_heat_fraction,b.spatial.cooling_electricity_kwh_year,b.spatial.common_system_electricity_kwh_year,
        sum(z.area_m2*z.lighting_w_m2*annual_hours(z,year)*z.program.lighting_use_fraction/1000 for z in zs),
        sum(z.area_m2*max(0,z.lighting_w_m2-z.target_lighting_w_m2)*annual_hours(z,year)*z.program.lighting_use_fraction/1000 for z in zs),
        sum(z.area_m2*z.device_w_m2*annual_hours(z,year)*z.program.device_use_fraction/1000 for z in zs),roof_area,
        sum(z.area_m2*z.roof_u_w_m2k for z in roof)/roof_area if roof_area else 0,b.spatial.roof_target_u_w_m2k,
        avg(lambda z:z.wall_u_w_m2k),avg(lambda z:z.window_u_w_m2k),avg(lambda z:z.air_changes_hour),
        avg(lambda z:z.program.service_end-z.program.service_start),avg(lambda z:z.program.occupied_end-z.program.occupied_start),sum(z.area_m2 for z in zs if can_schedule(z))]
    return values+[int(b.use_type==u) for u in USES]+[int(k in actions) for k in KINDS]

class PredictRequest(Model):
    context:Context
    building_id:str=Field(max_length=100)
    candidate_id:str=Field(max_length=150)

class Prediction(Model):
    year:int
    input_features:dict[str,float]|None=None
    base_context:Context
    building_id:str
    candidate_id:str
    model_version:str|None=None
    model_context:Context|None=None
    source_kind:Literal['synthetic_simulation']='synthetic_simulation'
    status:Literal['available','missing_model','out_of_domain','unavailable']
    prediction:AnnualPrediction|None=None
    physics_result:PackageResult|None=None
    difference:AnnualPrediction|None=None
    messages:list[str]
    used_for_optimization:Literal[False]=False
    capacity_inference:Literal[False]=False

def metadata():
    p=ASSET_DIR/'metadata.json'
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else None

def status():
    m=metadata()
    return {'available':bool(m and (ASSET_DIR/'model.joblib').exists()),'source_kind':'synthetic_simulation','metadata':m}

def predict(b,profile,current,year):
    global _loaded
    m=metadata();cid=profile.report.candidate_id or profile.report.package
    base=dict(year=year,base_context=current,building_id=b.id,candidate_id=cid,physics_result=profile.report,model_version=m['model_version'] if m else None,
              model_context={**current,'model_version':m['model_version']} if m else None)
    if not m or not (ASSET_DIR/'model.joblib').exists():return Prediction(**base,status='missing_model',messages=['Sentetik model dosyası bulunamadı; fizik sonucu korunur.'])
    actions={d.kind for d in profile.report.interventions}
    if not actions:
        from interventions import heating_package
        actions=({'insulation'} if profile.report.package in ('insulation','combined') else set())|({'heat_pump'} if profile.report.package in ('heat_pump','combined') else set())
        actions|={k for k in ('roof','lighting','schedule') if getattr(b.spatial_selection,k)}
    if not b.spatial or b.use_type not in USES or b.spatial_selection.zone_ids or year!=2025 or b.heating_system!='gas_boiler' or b.heat_distribution!='low_temperature_water' or abs(b.retrofit.heat_pump_coverage_fraction-.9)>1e-9:
        return Prediction(**base,status='out_of_domain',messages=['Eğitim kapsamı: 2025 sentetik hava, gaz kazanı ve düşük sıcaklıklı sulu dağıtım, bütün bina zon şablonu. Bu girdi kapsam dışında.'])
    x=features(b,actions,year)
    base['input_features']=dict(zip(NAMES,x))
    violations=[NAMES[i] for i,v in enumerate(x) if v<m['feature_bounds'][i][0]-1e-6 or v>m['feature_bounds'][i][1]+1e-6]
    if violations:return Prediction(**base,status='out_of_domain',messages=['Eğitim aralığı dışındaki girdiler: '+', '.join(violations)+'. Tahmin zorlanmadı.'])
    path=ASSET_DIR/'model.joblib';digest=hashlib.sha256(path.read_bytes()).hexdigest()
    if digest!=m['model_sha256']:return Prediction(**base,status='unavailable',messages=['Model dosyasının özeti doğrulanamadı.'])
    import joblib
    from threadpoolctl import threadpool_limits
    if not _loaded or _loaded[0]!=digest:_loaded=(digest,joblib.load(path))
    with threadpool_limits(limits=2):y=_loaded[1].predict([x])[0]
    if any(v<0 for v in y):return Prediction(**base,status='unavailable',messages=['Negatif tahmin fiziksel olarak geçersiz; gösterilmedi. Fizik sonucu kullanılabilir.'])
    predicted=AnnualPrediction(electricity_kwh_year=float(y[0]),gas_kwh_year=float(y[1]))
    actual=profile.report
    return Prediction(**base,status='available',prediction=predicted,
        difference=AnnualPrediction(electricity_kwh_year=predicted.electricity_kwh_year-actual.electricity_kwh_year,
            gas_kwh_year=predicted.gas_kwh_year-actual.heating_gas_kwh_year-actual.non_heating_gas_kwh_year),
        messages=['Kendi sentetik simülatörünün deneysel yaklaşımı; saha doğruluğu veya saatlik kapasite kanıtı değildir.','Plan kararı fizik/MILP motorundan gelir.'])
