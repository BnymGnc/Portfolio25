import csv
import io
import os
import threading
from pathlib import Path
from contextvars import ContextVar
from uuid import uuid4
import re

from config import load_backend_env
from fastapi import FastAPI, HTTPException, Request
from auth import Accounts, Credentials, user_context
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response

from models import Campus, CampusResponse, CampusUpdate, CalculationRequest, CalculationResult, PackageName, ProjectCreate, ConnectionGroup
from sample_data import create_sample_campus
from migrations import migrate_v1, migrate_v2
from engine import PACKAGES, calculate, calculate_package, summarize
from profiles import audit_profiles, generate_profiles
from exports import calculation_id, guarded_export
from typing import Literal
import numpy as np
import contracts
from eligibility import exclusion_reason
from spatial_models import SpatialPreviewRequest
from calculation_context import context,stale_reason
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from fastapi.exceptions import ResponseValidationError
from storage import storage_status, check_storage
from postgres_store import get_store, DatabaseUnavailable
import psycopg
from starlette.concurrency import run_in_threadpool

BASE_DIR = Path(__file__).resolve().parent
BOOT_ID = uuid4().hex  # Public process nonce; contains no host/account/secret data.
load_backend_env()
configured_path = Path(os.getenv("DATA_FILE", "data/campus.json"))
DATA_FILE = configured_path if configured_path.is_absolute() else BASE_DIR / configured_path
lock = threading.RLock()
compute_lock = threading.Lock()
project_context = ContextVar('project_id', default='campus-demo-25')


AUTH_REQUIRED = True
accounts = Accounts(lambda: DATA_FILE.parent/'accounts.sqlite3', secure=os.getenv('COOKIE_SECURE','false').lower()=='true',
                    storage_guard=lambda: check_storage(DATA_FILE),
                    db_provider=lambda: get_store().auth_connection if get_store() is not None else None)
ORIGINS = {s.strip() for s in os.getenv('FRONTEND_ORIGINS','http://127.0.0.1:5173,http://localhost:5173').split(',') if s.strip()}

def data_root():
    uid=user_context.get()
    return DATA_FILE.parent/'users'/uid if uid else DATA_FILE.parent

def pilot_samples():
    from pilot_kayseri import create_pilot
    import hashlib
    samples=create_pilot()
    if user_context.get():
        for sample in samples: sample.id='project-'+hashlib.sha256((user_context.get()+sample.id).encode()).hexdigest()[:12]
    return samples

def data_file():
    project_id=project_context.get()
    return (data_root()/'campus.json' if user_context.get() else DATA_FILE) if project_id=='campus-demo-25' else data_root()/'projects'/f'{project_id}.json'


def project_exists():
    store=get_store()
    return store.project(user_context.get(),project_context.get()) is not None if store else data_file().exists()

app = FastAPI(title="Portfolio25-GRID API", version="0.2.0", description="Sentetik kampüs paket hesaplama ve MILP prototipi.")


def error_response(status,message,code=None,fields=None):
    return JSONResponse(status_code=status,headers={'Cache-Control':'private, no-store'},content={'detail':message,'error':{
        'code':code or {422:'invalid_input',409:'context_conflict',404:'not_found',503:'unavailable'}.get(status,'request_failed'),
        'message':message,'fields':fields or []}})


@app.exception_handler(StarletteHTTPException)
async def http_error(request,error):
    if isinstance(error.detail,dict):return error_response(error.status_code,error.detail.get('message','Girdileri kontrol edin.'),error.detail.get('code'),error.detail.get('fields'))
    return error_response(error.status_code,str(error.detail),getattr(error,'code',None))


@app.exception_handler(psycopg.Error)
async def database_error(request,error):
    safe=DatabaseUnavailable()
    return error_response(503,str(safe.detail),safe.code)


@app.exception_handler(RequestValidationError)
async def validation_error(request,error):
    fields=[{'field':'.'.join(map(str,e['loc'])),'message':e['msg']} for e in error.errors()]
    return error_response(422,'Girdileri kontrol edin: '+'; '.join(f['field']+': '+f['message'] for f in fields),'invalid_input',fields)


@app.exception_handler(ValueError)
async def physical_error(request,error):
    return error_response(422,str(error),'physical_validation',[{'field':'buildings','message':str(error)}])


@app.exception_handler(ResponseValidationError)
async def response_error(request,error):
    return error_response(500,'Yanıt sözleşmesi doğrulanamadı; işlem sonucu güncel kayıtla yeniden kontrol edilmeli.','response_validation')
app.add_middleware(
    CORSMiddleware,
    allow_origins=[origin.strip() for origin in os.getenv(
        "FRONTEND_ORIGINS", "http://127.0.0.1:5173,http://localhost:5173"
    ).split(",") if origin.strip()],
    allow_methods=["GET", "PUT", "POST"], allow_headers=["Content-Type", "X-CSRF-Token"], allow_credentials=True,
)


@app.middleware('http')
async def select_project(request, call_next):
    public=request.url.path in ('/api/health','/openapi.json','/docs','/docs/oauth2-redirect','/redoc')
    auth_route=request.url.path.startswith('/api/auth/')
    try:
        if AUTH_REQUIRED and not public and request.method!='OPTIONS':check_storage(DATA_FILE)
        session=await run_in_threadpool(accounts.session,request) if AUTH_REQUIRED and not public and request.method!='OPTIONS' else None
    except HTTPException as error:
        return error_response(error.status_code,str(error.detail),getattr(error,'code',None))
    uid=session['user_id'] if session else None
    if AUTH_REQUIRED and not public and request.method!='OPTIONS':
        if not auth_route and not uid:return error_response(401,'Devam etmek için giriş yapın.','authentication_required')
        if request.method not in ('GET','HEAD'):
            try:accounts.check_csrf(request,session,ORIGINS)
            except HTTPException as error:return error_response(error.status_code,str(error.detail),'csrf_failed')
    user_token=user_context.set(uid)
    project_id=request.query_params.get('project_id','campus-demo-25')
    if not re.fullmatch(r'campus-demo-25|project-[a-f0-9]{12}',project_id):
        user_context.reset(user_token)
        return error_response(422,'Geçersiz proje kimliği.')
    token=project_context.set(project_id)
    try:
        global_route=public or auth_route or request.url.path.startswith('/api/intakes') or request.url.path in ('/api/projects','/api/examples/kayseri','/api/examples/kayseri/load')
        try:
            if not global_route and request.method!='OPTIONS' and not await run_in_threadpool(project_exists) and (uid or project_id!='campus-demo-25'):
                return error_response(404,'Proje bulunamadı veya bu hesaba ait değil.')
        except DatabaseUnavailable as error:
            return error_response(503,str(error.detail),error.code)
        result=await call_next(request)
        result.headers['Cache-Control']='no-store, private'
        result.headers['Vary']='Cookie, Origin'
        return result
    finally:
        project_context.reset(token)
        user_context.reset(user_token)


def session_reply(value):
    return {**value,'storage':storage_status(DATA_FILE)}


@app.get('/api/auth/session',response_model=contracts.AuthSession)
def auth_session(request:Request,response:Response):
    session=accounts.session(request)
    if not session:return session_reply(accounts.issue(response))
    return {'user':accounts.public_user(session['user_id']),'csrf':session['csrf'],'onboarding_version':1,
            'storage':storage_status(DATA_FILE)}


def authenticated_response(uid,request,response):
    token=user_context.set(uid)
    try:load_kayseri()  # Idempotent: only missing private templates are created.
    finally:user_context.reset(token)
    return session_reply(accounts.issue(response,uid,accounts.session(request)))


@app.post('/api/auth/register',response_model=contracts.AuthSession)
def register(request:Request,response:Response,credentials:Credentials):
    accounts.limit(request,credentials.email)
    return authenticated_response(accounts.register(credentials),request,response)


@app.post('/api/auth/login',response_model=contracts.AuthSession)
def login(request:Request,response:Response,credentials:Credentials):
    accounts.limit(request,credentials.email)
    return authenticated_response(accounts.login(credentials),request,response)


@app.post('/api/auth/logout',response_model=contracts.AuthSession)
def logout(request:Request,response:Response):
    session=accounts.session(request)
    return session_reply(accounts.issue(response,None,session))


@app.post('/api/auth/onboarding')
def onboarding():
    uid=user_context.get()
    if not uid:raise HTTPException(401,'Giriş yapın.')
    with accounts.db() as db:db.execute('UPDATE users SET onboarding_version=1 WHERE id=?',(uid,))
    return {'completed':True,'version':1}


def write_campus(campus: Campus, expected_revision=None) -> None:
    store=get_store()
    if store:
        store.save_project(user_context.get(),campus,expected_revision)
        return
    path=data_file()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_suffix(".tmp")
    temporary.write_text(campus.model_dump_json(indent=2), encoding="utf-8")
    temporary.replace(path)


def read_campus() -> Campus:
    store=get_store()
    if store:
        raw=store.project(user_context.get(),project_context.get())
        if raw is None:raise HTTPException(404,'Proje bulunamadı veya bu hesaba ait değil.')
        return Campus.model_validate(raw)
    path=data_file()
    if not path.exists():
        write_campus(create_sample_campus())
    raw_text = path.read_text(encoding="utf-8-sig")
    import json
    raw = json.loads(raw_text)
    if raw.get("schema_version", "1.0") == "1.0":
        migrated = migrate_v1(raw)
        backup = path.with_name(path.stem + ".v1-backup.json")
        if not backup.exists():
            with backup.open('xb') as file:
                file.write(path.read_bytes())
        write_campus(migrated)
        return migrated
    if raw.get('schema_version')=='2.0':
        migrated=migrate_v2(raw)
        backup=path.with_name(path.stem+'.v2-backup.json')
        if not backup.exists():
            with backup.open('xb') as file:
                file.write(path.read_bytes())
        write_campus(migrated)
        return migrated
    return Campus.model_validate(raw)


def result_path() -> Path:
    path=data_file()
    return path.with_name(path.stem + ".result.json")


def read_result(campus: Campus) -> CalculationResult | None:
    result=read_historical_result()
    return result if result and not stale_reason(campus,result) else None


def read_historical_result() -> CalculationResult | None:
    store=get_store()
    if store:return store.last_result(user_context.get(),project_context.get())
    path = result_path()
    if not path.exists():
        return None
    return CalculationResult.model_validate_json(path.read_text(encoding="utf-8"))


def response(campus: Campus) -> CampusResponse:
    profiles = [generate_profiles(b, campus.profile_settings) for b in campus.buildings]
    audit = audit_profiles(campus, profiles)
    from interventions import baseline_profile
    baseline = summarize(campus.buildings, [baseline_profile(b,p,campus.scenario)
                                           for b, p in zip(campus.buildings, profiles, strict=True)], campus.scenario, campus.connection_groups)
    result = read_result(campus)
    old=read_historical_result()
    return CampusResponse(campus=campus, baseline=baseline, profile_audit=audit, calculation=result,
                          baseline_packages=[baseline_profile(b,p,campus.scenario).report for b,p in zip(campus.buildings,profiles,strict=True)],
                          calculation_id=calculation_id(result),context=context(campus,result),result_stale_reason=stale_reason(campus,old),
                          after=result.after if result else None,
                          investment_plan=result.selected_packages if result and result.after else None)


@app.get("/api/health",response_model=contracts.Health)
def health(response:Response):
    storage=storage_status(DATA_FILE)
    unavailable=storage['status']=='unavailable'
    response.status_code=503 if unavailable else 200
    commit=os.getenv('RENDER_GIT_COMMIT','')
    return {"status": "degraded" if unavailable else "ok", "version": "0.4.0", "optimization_status": "not_checked",'data_status':'not_checked',
            'storage':storage,'release_commit':commit if re.fullmatch(r'[a-fA-F0-9]{40}',commit) else None,'boot_id':BOOT_ID}


@app.get('/api/calculations/current/evidence',response_model=contracts.Evidence)
def current_evidence(expected_calculation_id:str):
    with lock:
        campus=read_campus();result=read_result(campus)
        if not result or result.calculation_id!=expected_calculation_id:raise HTTPException(409,'Güncel hesap bağlamı değişti; yeniden hesaplayın.')
        return result.decision_evidence


@app.get('/api/examples/kayseri')
def kayseri_status():
    from pilot_kayseri import create_pilot,TITLE,DATASET
    with lock:
        projects=[]
        for sample in pilot_samples():
            path=data_root()/'projects'/f'{sample.id}.json'
            store=get_store()
            raw=store.project(user_context.get(),sample.id) if store else None
            current=Campus.model_validate(raw) if raw is not None else (Campus.model_validate_json(path.read_bytes()) if not store and path.exists() else None)
            p=current or sample
            projects.append({'id':p.id,'name':p.name,'building_count':len(p.buildings),'budget_try':p.scenario.budget_try,
                'connection_group_count':len(p.connection_groups),'loaded':current is not None})
        return {'dataset':DATASET,'title':TITLE,'projects':projects,'building_count':sum(p['building_count'] for p in projects)}


@app.post('/api/examples/kayseri/load')
def load_kayseri():
    from pilot_kayseri import create_pilot,DATASET
    with lock:
        samples=pilot_samples();created=[];preserved=[]
        store=get_store()
        if store:
            created,preserved=store.seed_pilot(user_context.get(),samples,DATASET)
            return {**kayseri_status(),'created':created,'preserved':preserved}
        # Validate every occupied identity before writing any sample. Never overwrite.
        for p in samples:
            path=data_root()/'projects'/f'{p.id}.json'
            if path.exists():
                current=Campus.model_validate_json(path.read_bytes())
                if not current.pilot or current.pilot.get('dataset')!=DATASET:
                    raise HTTPException(409,'Pilot kimliği mevcut başka bir kayda ait; hiçbir kayıt değiştirilmedi.')
                preserved.append(p.id)
        for p in samples:
            if p.id not in preserved:
                token=project_context.set(p.id)
                try:write_campus(p);created.append(p.id)
                finally:project_context.reset(token)
        return {**kayseri_status(),'created':created,'preserved':preserved}


@app.get('/api/projects')
def list_projects():
    with lock:
        store=get_store()
        if store:
            projects=[Campus.model_validate(p) for p in store.projects(user_context.get())]
            return {'projects':[{'id':p.id,'name':p.name,'building_count':len(p.buildings),
                'project_type':'single_building' if len(p.buildings)==1 else 'multi_building','revision':p.revision} for p in projects]}
        default_token=project_context.set('campus-demo-25')
        try:
            projects=[read_campus()] if not user_context.get() or data_file().exists() else []
            for path in sorted((data_root()/'projects').glob('project-*.json')):
                if not re.fullmatch(r'project-[a-f0-9]{12}',path.stem):
                    continue
                projects.append(Campus.model_validate_json(path.read_text(encoding='utf-8')))
            return {'projects':[{'id':p.id,'name':p.name,'building_count':len(p.buildings),
                'project_type':'single_building' if len(p.buildings)==1 else 'multi_building','revision':p.revision} for p in projects]}
        finally:
            project_context.reset(default_token)


@app.post('/api/projects')
def create_project(request: ProjectCreate):
    with lock:
        source=read_campus()
        if len(set(request.building_ids))!=len(request.building_ids) or not set(request.building_ids)<={b.id for b in source.buildings}:
            raise HTTPException(422,'Kaynak projeden benzersiz mevcut bina kimlikleri seçin.')
        buildings=[b.model_copy(deep=True) for b in source.buildings if b.id in request.building_ids]
        groups=([ConnectionGroup(id=f'G{i:02d}',name=f'{b.name} bağımsız bağlantısı',building_ids=[b.id],capacity_kw=b.connection_limit_kw)
                 for i,b in enumerate(buildings,1)] if request.connection_mode=='independent' else
                [ConnectionGroup(id='G01',name='Tanımlanan ortak bağlantı',building_ids=[b.id for b in buildings],capacity_kw=source.scenario.electric_capacity_kw)])
        raw=source.model_dump(mode='json')
        raw['pilot']=None
        raw.update(id='project-'+uuid4().hex[:12],name=request.name,revision=1,buildings=[b.model_dump(mode='json') for b in buildings],
                   connection_groups=[g.model_dump() for g in groups],migration_notes=[f'{source.id} r{source.revision} sentetik girdilerinin bağımsız kopyası. Bütçe kopyalandı; bağlantı varsayımlarını inceleyin.'])
        if len(groups)==1:
            raw['scenario']['electric_capacity_kw']=groups[0].capacity_kw
        project=Campus.model_validate(raw)
        token=project_context.set(project.id)
        try:
            write_campus(project)
        finally:
            project_context.reset(token)
        return {'id':project.id,'name':project.name,'building_count':len(project.buildings)}


@app.get("/api/campus", response_model=contracts.Snapshot)
def get_campus():
    with lock:
        return response(read_campus())


@app.put("/api/campus", response_model=contracts.Snapshot)
def update_campus(update: CampusUpdate):
    with lock:
        current = read_campus()
        if update.revision != current.revision:
            raise HTTPException(409, "Veri başka bir oturumda değişti. Sayfayı yenileyip tekrar deneyin.")
        for building in update.buildings:
            original = next((b for b in current.buildings if b.id == building.id),None)
            if original is None:
                raise HTTPException(422,'Bu kayıt işlemi mevcut proje binalarını düzenler; yeni proje oluşturmayı kullanın.')
            if building.provenance != original.provenance:
                raise HTTPException(422, "Sentetik örneklerin kaynak bilgisi değiştirilemez.")
        # Merge only explicitly supplied fields, including nested assumptions. Old clients
        # must not reset v2 fields when saving a v1-shaped payload.
        def merge(base, patch):
            result = dict(base)
            for key, value in patch.items():
                result[key] = merge(result[key], value) if isinstance(value, dict) and isinstance(result.get(key), dict) else value
            return result
        patch = update.model_dump(exclude_unset=True)
        patch["buildings"] = [merge(next(b.model_dump() for b in current.buildings if b.id == item["id"]), item)
                              for item in patch["buildings"]]
        merged=merge(current.model_dump(), {**patch, 'revision':current.revision+1})
        if merged['connection_groups'] is None:
            raise HTTPException(422,'Bağlantı grupları boş bırakılamaz.')
        if len(merged['connection_groups'])==1:
            group=merged['connection_groups'][0]
            old_cap=current.connection_groups[0].capacity_kw if len(current.connection_groups)==1 else None
            group_changed=old_cap!=group['capacity_kw']
            scenario_changed=merged['scenario']['electric_capacity_kw']!=current.scenario.electric_capacity_kw
            if group_changed and scenario_changed and group['capacity_kw']!=merged['scenario']['electric_capacity_kw']:
                raise HTTPException(422,'Tek bağlantının kapasitesi ve eski ortak kapasite alanı çelişiyor.')
            if scenario_changed and not group_changed:
                group['capacity_kw']=merged['scenario']['electric_capacity_kw']
            else:
                merged['scenario']['electric_capacity_kw']=group['capacity_kw']
        from pydantic import ValidationError
        try:
            updated=Campus.model_validate(merged)
        except ValidationError as error:
            errors=error.errors(include_input=False)
            return error_response(422,'Girdiler tutarsız: '+'; '.join(e['msg'] for e in errors),'invalid_input',
                [{'field':'.'.join(map(str,e['loc'])) or 'buildings','message':e['msg']} for e in errors])
        # Validate the entire candidate's physical calculations before committing any byte.
        from engine import prepare
        prepare(updated)
        candidate_response=contracts.Snapshot.model_validate(response(updated).model_dump(mode='json'))
        write_campus(updated,expected_revision=current.revision)
        return candidate_response


@app.get('/api/campus/snapshot',response_model=contracts.Snapshot)
def get_campus_snapshot():
    with lock:
        snapshot = response(read_campus())
        return {**snapshot.model_dump(mode='json'), 'calculation_id': calculation_id(snapshot.calculation)}


@app.post("/api/calculate", response_model=contracts.Result)
def calculate_plan(request: CalculationRequest):
    if not compute_lock.acquire(blocking=False):
        raise HTTPException(409, "Başka bir hesaplama sürüyor; tamamlanmasını bekleyin.")
    try:
        with lock:
            campus = read_campus()
            if campus.revision != request.revision:
                raise HTTPException(409, "Girdiler değişti; güncel kaydı yükleyin.")
        result = calculate(campus, request)
        # Persist the same normalized public result that clients receive.
        result=CalculationResult.model_validate(contracts.Result.model_validate(result.model_dump()).model_dump(mode='json'))
        with lock:
            if stale_reason(read_campus(),result) is not None:
                raise HTTPException(409, "Hesaplama sırasında girdiler değişti; sonucu yeniden hesaplayın.")
            store=get_store()
            if store:
                store.save_result(user_context.get(),campus,result)
                return result
            path = result_path()
            if path.exists():
                import hashlib
                previous=path.read_bytes()
                history=data_root()/'history'/campus.id
                history.mkdir(parents=True,exist_ok=True)
                archive=history/(hashlib.sha256(previous).hexdigest()+'.json')
                if not archive.exists():
                    with archive.open('xb') as file:file.write(previous)
            temporary = path.with_suffix(".tmp")
            temporary.write_text(result.model_dump_json(indent=2), encoding="utf-8")
            temporary.replace(path)
        return result
    finally:
        compute_lock.release()


@app.get('/api/buildings/{building_id}/spatial',response_model=contracts.SpatialAnalysis)
def get_spatial(building_id:str):
    with lock:
        campus=read_campus()
    building=next((b for b in campus.buildings if b.id==building_id),None)
    if not building:raise HTTPException(404,'Bina bulunamadı.')
    if not building.spatial:return {'context':context(campus,read_result(campus)),'project_id':campus.id,'input_revision':campus.revision,'building_id':building.id,'available':False,
        'message':'Bu eski kayıtta kat/zon verisi yok; dağılım uydurulmadı. Ayrı Kayseri sentetik pilotunu açık yükleme eylemiyle deneyebilirsiniz.'}
    from spatial_service import analysis
    return {'context':context(campus,read_result(campus)),'available':True,**analysis(campus,building)}


@app.post('/api/buildings/{building_id}/spatial/evaluate',response_model=contracts.SpatialPreview)
def preview_spatial(building_id:str,request:SpatialPreviewRequest):
    with lock:campus=read_campus()
    if campus.revision!=request.revision:raise HTTPException(409,'Girdiler değişti; yeniden yükleyip hesaplayın.')
    building=next((b for b in campus.buildings if b.id==building_id),None)
    if not building:raise HTTPException(404,'Bina bulunamadı.')
    if not building.spatial:raise HTTPException(422,'Bu binada kat/zon modeli yok.')
    from spatial_service import evaluate
    try:result=evaluate(campus,building,request.selection,request.package,request.spatial,request.interventions)
    except ValueError as error:raise HTTPException(422,str(error))
    with lock:
        if read_campus().revision!=request.revision:raise HTTPException(409,'Hesap sırasında girdiler değişti; yeniden hesaplayın.')
    return {**result,'context':context(campus,read_result(campus))}


@app.get("/api/buildings/{building_id}/profiles",response_model=contracts.BuildingProfiles)
def get_building_profiles(building_id: str, package: PackageName = "none",candidate_id:str|None=None,expected_calculation_id:str|None=None):
    with lock:
        campus = read_campus()
    building = next((b for b in campus.buildings if b.id == building_id), None)
    if building is None:
        raise HTTPException(404, "Bina bulunamadı.")
    profile = generate_profiles(building, campus.profile_settings)
    from interventions import candidates,baseline_profile
    result=read_result(campus)
    if expected_calculation_id and calculation_id(result)!=expected_calculation_id:raise HTTPException(409,'Profilin kaynak hesabı değişti.')
    baseline=baseline_profile(building,profile,campus.scenario)
    if candidate_id is not None:
        computed=next((p for p in candidates(building,profile,campus.scenario) if p.report.candidate_id==candidate_id),None)
        if not computed:raise HTTPException(422,'Bu bina için uygun aday kimliği bulunamadı.')
    elif building.interventions is not None:
        if package!='none':raise HTTPException(422,'Açık karar durumlarında tam kombinasyon için candidate_id gönderin.')
        computed=baseline
    else:
        if reason:=exclusion_reason(building,package):raise HTTPException(422,reason)
        computed=calculate_package(building,profile,campus.scenario,package)
    return {'context':context(campus,read_result(campus)),"input_revision": campus.revision, "building_id": building_id, "package": package,
            "kind": "synthetic", "source": campus.profile_settings.source,
            "timezone": campus.profile_settings.timezone, "interval_hours": 1,
            "timestamps": profile.timestamps, "baseline_electricity_kw": baseline.electricity_kw.tolist(),
            "electricity_kw": computed.electricity_kw.tolist(), "useful_heat_before_kw": baseline.useful_heat_kw.tolist(),
            "useful_heat_after_kw": computed.useful_heat_kw.tolist(),
            "heat_pump_heat_kw": computed.heat_pump_heat_kw.tolist(), "backup_boiler_heat_kw": computed.backup_heat_kw.tolist(),
            "summary": computed.report}


@app.get("/api/buildings/{building_id}/packages",response_model=contracts.BuildingPackages)
def get_building_packages(building_id: str):
    with lock:
        campus = read_campus()
    building = next((b for b in campus.buildings if b.id == building_id), None)
    if building is None:
        raise HTTPException(404, "Bina bulunamadı.")
    profile = generate_profiles(building, campus.profile_settings)
    from interventions import candidates,baseline_profile
    from engine import capacity_checks
    options=candidates(building,profile,campus.scenario)
    base=[baseline_profile(b,generate_profiles(b,campus.profile_settings),campus.scenario) for b in campus.buildings]
    index=next(i for i,b in enumerate(campus.buildings) if b.id==building_id)
    impacts={}
    relevant={g.id for g in campus.connection_groups if building_id in g.building_ids}
    for option in options:
        trial=base.copy();trial[index]=option
        impacts[option.report.candidate_id or option.report.package]=[c for c in capacity_checks(campus.buildings,trial,campus.scenario,campus.connection_groups) if c.kind=='group' and c.id in relevant]
    exclusion_building=building.model_copy(deep=True)
    if building.interventions is not None:exclusion_building.spatial_selection.roof=False
    return {'context':context(campus,read_result(campus)),"input_revision": campus.revision, "building_id": building_id, "kind": "synthetic",
            'scope':'bounded_intervention_templates' if building.interventions is not None else 'heating_only', 'excluded_packages':[{'package':name,'reason':exclusion_reason(exclusion_building,name)} for name in PACKAGES if exclusion_reason(exclusion_building,name)],
            "packages": [p.report for p in options],"group_impacts":impacts}


@app.get("/api/calculations/last",response_model=contracts.LastResult)
def get_last_calculation():
    # Historical data is deliberately separate from the current-result contract/export.
    with lock:
        campus = read_campus()
        result = read_historical_result()
        return {"current_revision": campus.revision, "is_current": bool(result and not stale_reason(campus,result)),
                "calculation": result, "calculation_id": calculation_id(result),'context':context(campus,read_result(campus)),
                'stale_reason':stale_reason(campus,result)}


@app.get("/api/campus/profiles",response_model=contracts.ProjectProfiles)
def get_campus_profiles(expected_calculation_id:str|None=None):
    with lock:
        campus = read_campus()
        result = read_result(campus)
        if expected_calculation_id and calculation_id(result)!=expected_calculation_id:
            raise HTTPException(409,'Grafik hesabı değişti; sonuçları yenileyin.')
    profiles = [generate_profiles(b, campus.profile_settings) for b in campus.buildings]
    audit = audit_profiles(campus, profiles)
    if not audit.all_consistent:
        raise HTTPException(422, "Saatlik profil eksik veya yıllık enerjiyle tutarsız; grafik üretilemedi.")
    from interventions import baseline_profile,selected_profile
    baseline_profiles=[baseline_profile(b,p,campus.scenario) for b,p in zip(campus.buildings,profiles,strict=True)]
    before = np.sum([p.electricity_kw for p in baseline_profiles], axis=0)
    after = None
    if result and result.after:
        selected = {p.building_id: p for p in result.selected_packages}
        if set(selected) != {b.id for b in campus.buildings}:
            raise HTTPException(422, "Hesaplanmış planda eksik bina var; yeniden hesaplayın.")
        after = np.sum([selected_profile(b, p, campus.scenario, selected[b.id]).electricity_kw
                        for b, p in zip(campus.buildings, profiles, strict=True)], axis=0)
    group_profiles=[]
    for group in campus.connection_groups:
        members=[i for i,b in enumerate(campus.buildings) if b.id in group.building_ids]
        before_group=np.sum([baseline_profiles[i].electricity_kw for i in members],axis=0)
        after_group=np.sum([selected_profile(campus.buildings[i],profiles[i],campus.scenario,selected[campus.buildings[i].id]).electricity_kw for i in members],axis=0) if after is not None else None
        group_profiles.append({'id':group.id,'name':group.name,'capacity_kw':group.capacity_kw,'before_kw':before_group.tolist(),
                               'after_kw':after_group.tolist() if after_group is not None else None})
    return {'context':context(campus,result),'calculation_id':calculation_id(result),'project_id':campus.id,"input_revision": campus.revision, "result_input_revision": result.input_revision if result and result.after else None,
            "result_mode": result.mode if result and result.after else None,
            "kind": "synthetic", "source": campus.profile_settings.source,
            "timezone": campus.profile_settings.timezone, "interval_hours": 1,
            "timestamps": profiles[0].timestamps, "before_kw": before.tolist(),
            "after_kw": after.tolist() if after is not None else None,
            "capacity_kw": campus.connection_groups[0].capacity_kw if len(campus.connection_groups)==1 else None, 'groups':group_profiles}


@app.get("/api/export/{file_format}")
def export_campus(file_format: str, scope: Literal['auto','inputs','result'] = 'auto',
                  revision: int | None = None, expected_calculation_id: str | None = None):
    if file_format == 'html' and scope != 'result':
        raise HTTPException(422, 'Karar özeti yalnız güncel hesaplanmış sonuç için indirilebilir.')
    with lock:
        campus = read_campus()
        snapshot = response(campus)
        snapshot, metadata = guarded_export(snapshot, scope, revision, expected_calculation_id)
    suffix = '' if scope == 'auto' else f'-{scope}-r{campus.revision}' + (f'-{snapshot.calculation.mode}' if snapshot.calculation else '')
    prefix='portfolio25-grid' if campus.id=='campus-demo-25' else f'portfolio25-grid-{campus.id}'
    filename = f'{prefix}{suffix}.{file_format}'
    if file_format == 'html':
        from decision_brief import render_brief
        return Response(render_brief(snapshot, metadata), media_type='text/html',
                        headers={'Content-Disposition': f'attachment; filename="{filename}"',
                                 'X-Content-Type-Options': 'nosniff'})
    if file_format == "json":
        import json
        body = snapshot.model_dump(mode='json')
        if scope != 'auto':
            body['export_metadata'] = metadata
        return Response(json.dumps(body,ensure_ascii=False,indent=2), media_type="application/json",
                        headers={"Content-Disposition": f'attachment; filename="{filename}"'})
    if file_format != "csv":
        raise HTTPException(404, "Desteklenen biçimler: csv, json, html (karar özeti)")
    output = io.StringIO(newline="")
    writer = csv.writer(output)
    writer.writerow(["id", "name", "use_type", "area_m2", "year_built", "electricity_kwh_year",
                     "heating_kwh_year", "peak_electric_kw", "data_kind", "source", "seed",
                     "budget_try", "savings_target_pct", "electric_capacity_kw",
                     "electricity_price_try_kwh", "heating_price_try_kwh", "revision", "optimization_status",
                     "non_heating_gas_kwh_year", "connection_limit_kw", "retrofit_assumptions_json",
                     "valuation_assumptions_json", "profile_settings_json", "selected_package", "investment_try",
                     "after_electricity_kwh_year", "after_heating_gas_kwh_year", "energy_savings_kwh_year",
                     "net_savings_try_year", "simple_payback_years", "solver_status", "solver_gap", "optimality_proven",
                     "export_kind", "calculation_revision", "calculation_id", "calculation_mode", "exported_at_utc",
                     "campus_before_json", "campus_after_json", "solver_json", "selected_package_json", "data_provenance_json",
                     'project_json','system_assumptions_json','decision_evidence_json','sensitivity_json','spatial_model_json','spatial_selection_json','interventions_json','context_json'])
    for b in campus.buildings:
        # Neutralize spreadsheet formulas in user-editable names.
        safe_name = "'" + b.name if b.name.lstrip().startswith(("=", "+", "-", "@")) else b.name
        plan = next((p for p in (snapshot.investment_plan or []) if p.building_id == b.id), None)
        calc = snapshot.calculation
        writer.writerow([b.id, safe_name, b.use_type, b.area_m2, b.year_built, b.electricity_kwh_year,
                         b.heating_kwh_year, b.peak_electric_kw, b.provenance.kind, b.provenance.source,
                         b.provenance.seed, campus.scenario.budget_try, campus.scenario.savings_target_pct,
                         campus.scenario.electric_capacity_kw, campus.scenario.electricity_price_try_kwh,
                         campus.scenario.heating_price_try_kwh, campus.revision, campus.optimization_status,
                         b.non_heating_gas_kwh_year, b.connection_limit_kw, b.retrofit.model_dump_json(),
                         campus.scenario.model_dump_json(), campus.profile_settings.model_dump_json(),
                         *([plan.package, plan.investment_try, plan.electricity_kwh_year, plan.heating_gas_kwh_year,
                            plan.energy_savings_kwh_year, plan.net_savings_try_year, plan.simple_payback_years] if plan else [""] * 7),
                         calc.status if calc else "not_calculated", calc.solver.mip_gap if calc else "",
                         calc.solver.optimality_proven if calc else "",
                         scope, metadata['calculation_revision'], metadata['calculation_id'], metadata['calculation_mode'],
                         metadata['exported_at_utc'], snapshot.baseline.model_dump_json(),
                         snapshot.after.model_dump_json() if snapshot.after else '', calc.solver.model_dump_json() if calc else '',
                         plan.model_dump_json() if plan else '', b.provenance.model_dump_json(),
                         __import__('json').dumps({'id':campus.id,'name':campus.name,'pilot':campus.pilot,'connection_groups':[g.model_dump() for g in campus.connection_groups],
                            'sensitivity_settings':campus.sensitivity_settings.model_dump(mode='json')},ensure_ascii=False),
                         __import__('json').dumps({key:getattr(b,key) for key in ('heating_system','heat_distribution','insulation_allowed','system_source','field_sources')},ensure_ascii=False),
                         __import__('json').dumps(calc.decision_evidence,ensure_ascii=False) if calc else '',
                         __import__('json').dumps(calc.sensitivity,ensure_ascii=False) if calc else '',
                         b.spatial.model_dump_json() if b.spatial else '',b.spatial_selection.model_dump_json(),
                         __import__('json').dumps([d.model_dump() for d in b.interventions]) if b.interventions is not None else '',
                         __import__('json').dumps(snapshot.context,ensure_ascii=False)])
    return Response("\ufeff" + output.getvalue(), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": f'attachment; filename="{filename}"'})


from ai_models import ExplainRequest,Explanation,ScenarioDraftRequest,ScenarioDraft,ScenarioRun,ScenarioEvaluation,AIStatus,CounterfactualRequest
import ai_service


def require_context(expected,require_plan=False):
    with lock:
        campus=read_campus();result=read_result(campus);current=context(campus,result)
        if expected.model_dump()!=current:raise HTTPException(409,'Proje/girdi/hesap/motor bağlamı değişti; ekranı yenileyin.')
        if require_plan and not result:raise HTTPException(409,'Önce güncel ana yatırım planını hesaplayın.')
        return campus,result,current


@app.get('/api/ai/status',response_model=AIStatus)
def ai_status():
    return AIStatus(configured=ai_service.configured(),model=ai_service.model(),prompt_version=ai_service.PROMPT_VERSION,explanation_available=ai_service.configured(),**ai_service.service_status())


@app.post('/api/ai/explain',response_model=Explanation)
def explain_plan(request:ExplainRequest):
    campus,result,current=require_context(request.context,request.scope=='plan')
    explanation=ai_service.explain(campus,result,request,current)
    require_context(request.context,request.scope=='plan')
    return explanation


@app.post('/api/ai/scenario-draft',response_model=ScenarioDraft)
def scenario_draft(request:ScenarioDraftRequest):
    campus,result,current=require_context(request.context,True)
    proposed=ai_service.draft(campus,request,current)
    require_context(request.context,True)
    return proposed


@app.post('/api/scenarios/evaluate',response_model=ScenarioEvaluation)
def scenario_evaluate(request:ScenarioRun):
    campus,result,current=require_context(request.context,True)
    alternative=ai_service.changed_campus(campus,request.changes)
    if not compute_lock.acquire(blocking=False):raise HTTPException(409,'Başka bir hesap sürüyor; tamamlanmasını bekleyin.')
    try:calculated=calculate(alternative,CalculationRequest(revision=campus.revision,mode=request.mode,time_limit_s=request.time_limit_s))
    finally:compute_lock.release()
    require_context(request.context,True)
    return ScenarioEvaluation(base_context=current,changes=request.changes,baseline_plan=result.model_dump() if result else None,alternative=calculated.model_dump())


@app.post('/api/scenarios/apply',response_model=contracts.Snapshot)
def scenario_apply(request:ScenarioRun):
    with lock:
        campus,result,_=require_context(request.context,True)
        alternative=ai_service.changed_campus(campus,request.changes)
        return update_campus(CampusUpdate.model_validate({k:alternative.model_dump()[k] for k in CampusUpdate.model_fields}))


@app.post('/api/scenarios/counterfactual',response_model=ScenarioEvaluation)
def counterfactual(request:CounterfactualRequest):
    campus,result,current=require_context(request.context,True)
    alternative=campus.model_copy(deep=True)
    building=next((b for b in alternative.buildings if b.id==request.building_id),None)
    if not building:raise HTTPException(404,'Bina bulunamadı.')
    from interventions import policy
    from spatial_models import InterventionDecision
    decisions=policy(building)
    if decisions.get(request.intervention)=='applied':raise HTTPException(422,'Müdahale zaten uygulanmış fiziksel başlangıçta; yeni zorunlu yatırım olarak sayılmaz.')
    decisions[request.intervention]='mandatory'
    building.interventions=[InterventionDecision(kind=k,state=v) for k,v in decisions.items()]
    if not compute_lock.acquire(blocking=False):raise HTTPException(409,'Başka bir hesap sürüyor.')
    try:calculated=calculate(alternative,CalculationRequest(revision=campus.revision,mode=result.mode,time_limit_s=5))
    finally:compute_lock.release()
    require_context(request.context,True)
    return ScenarioEvaluation(base_context=current,changes=[],baseline_plan=result.model_dump(),alternative=calculated.model_dump(),building_id=building.id,forced_intervention=InterventionDecision(kind=request.intervention,state='mandatory'))


import ml_service


@app.get('/api/ml/status',response_model=ml_service.ModelStatus)
def model_status():return ml_service.status()


@app.post('/api/ml/predict',response_model=ml_service.Prediction)
def model_predict(request:ml_service.PredictRequest):
    _,_,current=require_context(request.context)
    prediction=ml_service.predict(request.features,request.country,current)
    require_context(request.context)
    return prediction


@app.post('/api/ml/project-predict',response_model=ml_service.Prediction)
def model_project_predict(request:ml_service.ProjectPredictRequest):
    campus,result,current=require_context(request.context)
    building=next((b for b in campus.buildings if b.id==request.building_id),None)
    if not building:raise HTTPException(404,'Bina bulunamadı.')
    selected=next((p for p in result.selected_packages if p.building_id==building.id),None) if result else None
    if selected is None:
        from interventions import baseline_profile
        selected=baseline_profile(building,generate_profiles(building,campus.profile_settings),campus.scenario).report
    m=ml_service.metadata()
    prediction=ml_service.Prediction(base_context=current,status='out_of_domain' if m else 'missing_model',model_version=m['model_version'] if m else None,
        model_context={**current,'model_version':m['model_version']} if m else None,physics_result=selected,
        messages=['Seçili proje sentetik Türkiye örneğidir. ABD ComStock müdahale/iklim alanları doğrulanmadı; ML sonucu uydurulmadı.','Fizik motoru sonucu ayrı gösterilir; optimizasyon ML kullanmaz.'])
    require_context(request.context)
    return prediction


from openapi_contract import install as install_openapi
import synthetic_ml

@app.get('/api/ml/synthetic/status')
def synthetic_status():
    return synthetic_ml.status()

@app.post('/api/ml/synthetic/predict',response_model=synthetic_ml.Prediction)
def synthetic_predict(request:synthetic_ml.PredictRequest):
    campus,_,current=require_context(request.context)
    building=next((b for b in campus.buildings if b.id==request.building_id),None)
    if not building:raise HTTPException(404,'Bina bulunamadı.')
    from interventions import candidates
    options=candidates(building,generate_profiles(building,campus.profile_settings),campus.scenario)
    selected=next((p for p in options if (p.report.candidate_id or p.report.package)==request.candidate_id),None)
    if selected is None:raise HTTPException(422,'Bu girdilerde uygun aday paket bulunamadı.')
    result=synthetic_ml.predict(building,selected,current,campus.profile_settings.year)
    require_context(request.context)
    return result

install_openapi(app)

import named_scenarios
import sys
named_scenarios.install(app, sys.modules[__name__])


import intakes
intakes.install(sys.modules[__name__])
from catalog import catalogue,CatalogItem

@app.get('/api/buildings/{building_id}/catalog',response_model=list[CatalogItem])
def building_catalog(building_id:str):
    b=next((b for b in read_campus().buildings if b.id==building_id),None)
    if not b:raise HTTPException(404,'Bina bulunamadı.')
    return catalogue(b)

@app.get('/api/intakes/csv/template')
def intake_template():
    text=io.StringIO();writer=csv.writer(text);writer.writerow(intakes.CSV_HEADER)
    writer.writerow(['Binam','building','Konut','', '',2025,'','','','','gas_boiler','unknown','unknown','',''])
    return Response(text.getvalue(),media_type='text/csv',headers={'Content-Disposition':'attachment; filename="building-input-template.csv"'})

@app.post('/api/intakes/csv/preview')
def intake_csv_preview(body:intakes.CSVBody):return intakes.csv_preview(body)


@app.get('/api/intakes/options')
def intake_options():
    from models import RetrofitAssumptions
    return {'catalog_version':intakes.CATALOG_VERSION,'heating_systems':[{'id':k,'status':'calculable' if k=='gas_boiler' else 'data_required' if k=='unknown' else 'unsupported','label':v} for k,v in {'unknown':'Bilmiyorum','gas_boiler':'Doğalgaz kazanı','electric_resistance':'Elektrik dirençli ısıtma','existing_heat_pump':'Mevcut ısı pompası','coal':'Kömür','lpg':'LPG','district':'Bölgesel ısıtma','other':'Diğer'}.items()],
        'example_assumptions':RetrofitAssumptions(kind='default',source='Proje uzman varsayımları v1; yerinde doğrulanmadı, resmî performans değeri değildir.').model_dump(mode='json')}
