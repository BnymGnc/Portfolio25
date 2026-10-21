"""Optional experimental inference; never used by the physics or MILP engine."""
import hashlib,json
from pathlib import Path
from typing import Literal
from pydantic import Field
from models import Model,PackageResult
from contracts import Context
from ml_features import encode

ASSET_DIR=Path(__file__).resolve().parent/'ml_assets/comstock-small'
_loaded=None


class Features(Model):
    area_m2:float=Field(gt=0,le=1e6)
    year_built:int=Field(ge=1800,le=2100)
    building_type:str=Field(min_length=1,max_length=80)
    climate_zone:str=Field(min_length=1,max_length=20)
    hvac_system:str=Field(min_length=1,max_length=150)
    baseline_electricity_kwh_year:float=Field(ge=0,le=1e9)
    baseline_gas_kwh_year:float=Field(ge=0,le=1e9)
    upgrade:Literal['0','16','43','49']


class PredictRequest(Model):
    context:Context
    features:Features
    country:str=Field(default='US',min_length=2,max_length=2)


class ProjectPredictRequest(Model):
    context:Context
    building_id:str


class AnnualPrediction(Model):
    electricity_kwh_year:float
    gas_kwh_year:float


class Prediction(Model):
    base_context:Context
    model_context:Context|None=None
    status:Literal['available','missing_model','out_of_domain','unavailable']
    source_kind:Literal['external_simulation']='external_simulation'
    model_version:str|None=None
    prediction:AnnualPrediction|None=None
    physics_result:PackageResult|None=None
    messages:list[str]
    used_for_optimization:Literal[False]=False
    capacity_inference:Literal[False]=False
    clipped_negative_outputs:bool=False


class ModelStatus(Model):
    available:bool
    model_version:str|None=None
    feature_schema:str|None=None
    selected_model:str|None=None
    training_rows:int=0
    validation_rows:int=0
    test_rows:int=0
    building_groups:int=0
    source_kind:Literal['external_simulation']='external_simulation'
    metrics:dict[str,dict]=Field(default_factory=dict)
    validation_metrics:dict[str,dict[str,float]]=Field(default_factory=dict)
    timing:dict[str,dict[str,float]]=Field(default_factory=dict)
    limitations:list[str]
    domain:dict|None=None
    example:dict|None=None
    source:dict|None=None
    feature_names:list[str]=Field(default_factory=list)
    model_sha256:str|None=None


def metadata():
    file=ASSET_DIR/'metadata.json'
    if not file.exists() or not (ASSET_DIR/'model.joblib').exists():return None
    return json.loads(file.read_text(encoding='utf-8'))


def status():
    m=metadata()
    if not m:return ModelStatus(available=False,limitations=['Eğitilmiş model dosyası bulunamadı; fizik motoru çalışmaya devam eder.'])
    return ModelStatus(available=True,model_version=m['model_version'],feature_schema=m['feature_schema'],selected_model=m['selected_model'],training_rows=m['training_rows'],validation_rows=m['validation_rows'],test_rows=m['test_rows'],building_groups=m['building_groups'],metrics=m['test_metrics'],validation_metrics=m['validation_metrics'],timing=m['timing'],limitations=m['limitations'],domain=m['domain'],example=m['example'],source=m['source'],feature_names=m['features'],model_sha256=m['model_sha256'])


def predict(features,country,base_context):
    m=metadata()
    if not m:return Prediction(base_context=base_context,status='missing_model',messages=['Model bulunamadı; tahmin üretilmedi.'])
    ctx={**base_context,'model_version':m['model_version']};raw=features.model_dump();problems=[]
    if country!=m['domain']['country']:problems.append('Coğrafya eğitim kapsamı dışında: model ABD ticari simülasyonlarıyla eğitildi; Kayseri/Türkiye tahmini doğrulanmadı.')
    for key,band in m['domain']['numeric'].items():
        if not band['min']<=raw[key]<=band['max']:problems.append(key+' eğitim sayısal aralığı dışında.')
    for key,allowed in m['domain']['categorical'].items():
        if raw[key] not in allowed:problems.append(key+' eğitim kategorilerinde yok.')
    if problems:return Prediction(base_context=base_context,model_context=ctx,model_version=m['model_version'],status='out_of_domain',messages=problems)
    try:
        import joblib
        from threadpoolctl import threadpool_limits
        global _loaded
        data=(ASSET_DIR/'model.joblib').read_bytes();digest=hashlib.sha256(data).hexdigest()
        if digest!=m['model_sha256']:return Prediction(base_context=base_context,status='unavailable',messages=['Model dosyası bütünlük kontrolünü geçemedi.'])
        if not _loaded or _loaded[0]!=digest:_loaded=(digest,joblib.load(ASSET_DIR/'model.joblib'))
        with threadpool_limits(limits=2):values=_loaded[1].predict([encode(raw)])[0]*raw['area_m2']
        return Prediction(base_context=base_context,model_context=ctx,model_version=m['model_version'],status='available',
            prediction=AnnualPrediction(electricity_kwh_year=max(0,float(values[0])),gas_kwh_year=max(0,float(values[1]))),clipped_negative_outputs=bool(min(values)<0),
            messages=['Deneysel yıllık simülasyon tahmini; saatlik pik veya bağlantı uygunluğu için kullanılamaz.','Aynı bina grubunun varyantları eğitim ve test arasında ayrıldı; bağımsız saha doğrulaması yok.'])
    except (ImportError,ValueError,OSError):return Prediction(base_context=base_context,status='unavailable',messages=['Model bağımlılığı/dosyası yüklenemedi; fizik motoru etkilenmedi.'])
