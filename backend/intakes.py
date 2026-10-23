"""Private nullable building drafts; PostgreSQL retains them across application restarts.

Publishing is transactional and never fills unknown measurements silently.
"""
from datetime import date
from typing import Literal
from uuid import uuid4
import json,os,csv,io,calendar
from fastapi import HTTPException
from pydantic import Field,model_validator
from psycopg.types.json import Jsonb
from models import Model,CostQuote,RetrofitAssumptions,Campus,Building,Scenario,Provenance,Reference,ConnectionGroup,ProfileSettings
from auth import user_context

class Consumption(Model):
    mode: Literal['annual','monthly']='annual'
    value: float|None=Field(default=None,ge=0,le=1e9)
    months: list[float|None]=Field(default_factory=lambda:[None]*12,min_length=12,max_length=12)
    unit: Literal['kWh','m3']='kWh'
    source_kind: Literal['measured','user_estimate','unspecified']='unspecified'
    source: str=Field(default='',max_length=500)
    conversion_kwh_m3: float|None=Field(default=None,gt=0,le=30)
    conversion_source: str=Field(default='',max_length=500)
    @model_validator(mode='after')
    def valid_months(self):
        if any(v is not None and (v<0 or v>1e9) for v in self.months):raise ValueError('Aylık tüketimler 0–1 milyar aralığında olmalı.')
        return self
    def annual(self):
        total=self.value if self.mode=='annual' else sum(self.months) if all(v is not None for v in self.months) else None
        if total is None:return None
        if self.unit=='m3':return total*self.conversion_kwh_m3 if self.conversion_kwh_m3 is not None and self.conversion_source.strip() else None
        return total

class BuildingInput(Model):
    name: str=Field(default='Yeni binam',min_length=1,max_length=100)
    scope: Literal['apartment','building','portfolio']='building'
    location: str=Field(default='',max_length=200)
    use_type: Literal['Eğitim','Araştırma','İdari','Sosyal','Konaklama','Konut','Ofis','Otel']='Konut'
    area_m2: float|None=Field(default=None,gt=0,le=1e6)
    area_source: Literal['measured','user_estimate','unspecified']='unspecified'
    year: int|None=Field(default=None,ge=2020,le=2100)
    heating_system: Literal['unknown','gas_boiler','electric_resistance','existing_heat_pump','coal','lpg','district','other']='unknown'
    system_scope: Literal['unknown','individual','central']='unknown'
    heat_distribution: Literal['unknown','low_temperature_water','high_temperature_water','none']='unknown'
    insulation_known: Literal['unknown','yes','no']='unknown'
    electricity: Consumption=Field(default_factory=Consumption)
    fuel: Consumption=Field(default_factory=Consumption)
    heating_gas_fraction: float|None=Field(default=None,ge=0,le=1)
    heating_split_source: str=Field(default='',max_length=500)
    connection_kw: float|None=Field(default=None,gt=0,le=1e6)
    connection_source: str=Field(default='',max_length=500)
    assumptions: RetrofitAssumptions|None=None
    quotes: dict[Literal['insulation','heat_pump','roof','lighting','schedule'],CostQuote]=Field(default_factory=dict)
    @model_validator(mode='after')
    def electric_unit(self):
        if self.electricity.unit!='kWh':raise ValueError('Elektrik birimi kWh olmalı.')
        return self

class Intake(Model):
    id: str=Field(default_factory=lambda:'intake-'+uuid4().hex[:12],pattern=r'^intake-[a-f0-9]{12}$')
    revision: int=Field(default=1,ge=1)
    name: str=Field(default='Bina değerlendirmem',min_length=1,max_length=100)
    buildings: list[BuildingInput]=Field(default_factory=lambda:[BuildingInput()],min_length=1,max_length=20)
    budget_try: float|None=Field(default=None,ge=0,le=1e12)
    electricity_price: float|None=Field(default=None,ge=0,le=1000)
    gas_price: float|None=Field(default=None,ge=0,le=1000)
    tariff_source: str=Field(default='',max_length=500)
    target_pct: float=Field(default=25,ge=0,le=100)
    profile_consent: bool=False
    project_id: str|None=Field(default=None,pattern=r'^project-[a-f0-9]{12}$')

class ReadinessIssue(Model):
    field: str
    message: str

class Readiness(Model):
    status: Literal['unsupported','data_required','calculable']
    missing: list[ReadinessIssue]
    unsupported: list[ReadinessIssue]
    technical_review: list[str]
    capacity_statement: str

class IntakeView(Model):
    draft: Intake
    readiness: Readiness

CATALOG_VERSION='grid-catalog-1.0'

def readiness(d):
    missing=[];technical=[];unsupported=[]
    for i,b in enumerate(d.buildings):
        prefix=f'buildings.{i}.'
        for key,value in [('area_m2',b.area_m2),('year',b.year),('electricity',b.electricity.annual()),('fuel',b.fuel.annual()),('connection_kw',b.connection_kw),('assumptions',b.assumptions),('heating_gas_fraction',b.heating_gas_fraction)]:
            if value is None:missing.append({'field':prefix+key,'message':{'electricity':'Tam yıllık elektrik veya 12 ay; eksik aylar yıllık sayılmaz.','fuel':'Tam yıllık yakıt; m³ için kaynaklı kWh dönüşümü gerekli.','assumptions':'Kaynaklı uzman varsayımlarını tanımlayın.'}.get(key,'Hesap için bu bilgi gerekli.')})
        for key,value in [('heating_split_source',b.heating_split_source),('connection_source',b.connection_source)]:
            if not value.strip():missing.append({'field':prefix+key,'message':'Bilginin kaynağını belirtin.'})
        if b.heating_system not in ('unknown','gas_boiler'):unsupported.append({'field':prefix+'heating_system','message':'Bu yakıt/sistemin ısı dönüşümü mevcut motorda desteklenmiyor; gaz kazanı olarak hesaplanmaz.'})
        elif b.heating_system=='unknown':missing.append({'field':prefix+'heating_system','message':'Mevcut ısıtma sistemini belirleyin.'})
        if b.heat_distribution in ('unknown','high_temperature_water') or b.system_scope=='unknown':technical.append('Isı pompası için dağıtım sıcaklığı ve hizmet alanı uzman tarafından doğrulanmalı.')
    if len({b.year for b in d.buildings if b.year is not None})>1:missing.append({'field':'buildings.year','message':'Portföy binaları aynı yıllık dönemi kullanmalı.'})
    for key in ('budget_try','electricity_price','gas_price'):
        if getattr(d,key) is None:missing.append({'field':key,'message':'Plan için değer gerekli; bilinmeyen sıfır kabul edilmez.'})
    if not d.tariff_source.strip():missing.append({'field':'tariff_source','message':'Tarifelerin kaynak ve dönemini belirtin.'})
    if not d.profile_consent:missing.append({'field':'profile_consent','message':'Ölçülmüş saatlik veri yok; yıllık tüketimden modellenen profilin sınırlarını kabul edin.'})
    return {'status':'unsupported' if unsupported else 'data_required' if missing else 'calculable','missing':missing,'unsupported':unsupported,'technical_review':technical,'capacity_statement':'Kapasite yalnız modellenen profile göre değerlendirilir; ölçülmüş bağlantı uygunluğu değildir.'}

def compile_project(d,pid):
    state=readiness(d)
    if state['status']!='calculable':raise HTTPException(422,{'code':'building_not_ready','message':'Eksik veya desteklenmeyen girdiler var.','fields':state['missing']+state['unsupported']})
    buildings=[];groups=[]
    for i,b in enumerate(d.buildings,1):
        bid=f'B{i:02d}';gas=b.fuel.annual();share=b.heating_gas_fraction
        interventions=[{'kind':'insulation','state':'candidate' if 'insulation' in b.quotes and b.scope!='apartment' else 'excluded'},{'kind':'heat_pump','state':'candidate' if 'heat_pump' in b.quotes and b.heat_distribution=='low_temperature_water' and (b.scope!='apartment' or b.system_scope=='individual') else 'excluded'}]
        buildings.append(Building(id=bid,name=b.name,use_type=b.use_type,area_m2=b.area_m2,year_built=None,electricity_kwh_year=b.electricity.annual(),heating_kwh_year=gas*share,non_heating_gas_kwh_year=gas*(1-share),peak_electric_kw=None,connection_limit_kw=b.connection_kw,
            retrofit=b.assumptions,provenance=Provenance(kind='user_estimate',source='Kullanıcı girişi; ölçüm kaynakları alan bazında ayrı saklanır.'),heating_system='gas_boiler',heat_distribution=b.heat_distribution,system_source=b.heating_split_source,insulation_allowed=b.scope!='apartment',interventions=interventions,cost_quotes=b.quotes,
            field_sources={'area_m2':b.area_source,'electricity_kwh_year':b.electricity.source_kind,'heating_kwh_year':'user_estimate' if b.fuel.source_kind!='unspecified' else 'unspecified','non_heating_gas_kwh_year':'user_estimate' if b.fuel.source_kind!='unspecified' else 'unspecified'},
            input_metadata={**b.model_dump(mode='json'),'intake_id':d.id,'intake_revision':d.revision,'profile_source':'modelled_from_annual','construction_year':'unspecified'}))
        groups.append(ConnectionGroup(id=f'G{i:02d}',name=b.name+' bağımsız bağlantısı',building_ids=[bid],capacity_kw=b.connection_kw,source=b.connection_source))
    campus=Campus(id=pid,name=d.name,revision=1,buildings=buildings,provenance=Provenance(kind='user_estimate',source='Kullanıcı tarafından oluşturulan bina projesi; sentetik pilot değildir.'),
        scenario=Scenario(budget_try=d.budget_try,savings_target_pct=d.target_pct,electric_capacity_kw=groups[0].capacity_kw,electricity_price_try_kwh=d.electricity_price,heating_price_try_kwh=d.gas_price,price_basis=Reference(kind='user_estimate',reference_date=date.today(),source=d.tariff_source)),connection_groups=groups,
        profile_settings=ProfileSettings(year=d.buildings[0].year,source='Yıllık kullanıcı tüketimlerine normalize edilmiş modellenmiş saatlik profil; ölçülmüş sayaç yükü veya yerel hava ölçümü değildir.'))
    from engine import prepare
    prepare(campus)
    return campus

def rows(main):
    uid=user_context.get();store=main.get_store()
    if store:
        with store.connection() as db:return [Intake.model_validate(r['document']) for r in db.execute('SELECT document FROM portfolio25.building_intakes WHERE owner_id=%s ORDER BY intake_id',(uid,))]
    with main.accounts.db() as db:
        db.execute('CREATE TABLE IF NOT EXISTS building_intakes(owner_id TEXT NOT NULL,intake_id TEXT NOT NULL,revision INTEGER NOT NULL,document TEXT NOT NULL,PRIMARY KEY(owner_id,intake_id))')
        return [Intake.model_validate_json(r[0]) for r in db.execute('SELECT document FROM building_intakes WHERE owner_id=? ORDER BY intake_id',(uid,))]

def save(main,d,*,create=False,publish=False):
    uid=user_context.get();store=main.get_store();rows(main)
    project=None
    if publish:
        if d.project_id:raise HTTPException(409,'Taslak zaten projeye aktarıldı; mevcut projeyi düzenleyin.')
        project=compile_project(d,'project-'+uuid4().hex[:12])
    stored=d.model_copy(deep=True);stored.revision=1 if create else d.revision+1
    if project:stored.project_id=project.id
    if store:
        with store.connection() as db:
            if create:
                if d.project_id:raise HTTPException(422,'Yeni taslak mevcut projeye atanamaz.')
                db.execute('INSERT INTO portfolio25.building_intakes VALUES(%s,%s,%s,%s)',(uid,d.id,stored.revision,Jsonb(stored.model_dump(mode='json'))))
            else:
                existing=db.execute('SELECT document FROM portfolio25.building_intakes WHERE owner_id=%s AND intake_id=%s FOR UPDATE',(uid,d.id)).fetchone()
                if not existing:raise HTTPException(404,'Taslak bulunamadı.')
                old=Intake.model_validate(existing['document'])
                if old.revision!=d.revision or old.project_id!=d.project_id:raise HTTPException(409,'Taslak revizyonu veya proje bağlantısı değişti.')
                if old.project_id:raise HTTPException(409,'Projeye aktarılmış taslak değiştirilemez; proje ekranını kullanın.')
                db.execute('UPDATE portfolio25.building_intakes SET revision=%s,document=%s WHERE owner_id=%s AND intake_id=%s',(stored.revision,Jsonb(stored.model_dump(mode='json')),uid,d.id))
            if project:db.execute('INSERT INTO portfolio25.projects(owner_id,project_id,revision,document) VALUES(%s,%s,%s,%s)',(uid,project.id,1,Jsonb(project.model_dump(mode='json'))))
    else:
        with main.accounts.db() as db:
            if create:
                if d.project_id:raise HTTPException(422,'Yeni taslak mevcut projeye atanamaz.')
                db.execute('INSERT INTO building_intakes VALUES(?,?,?,?)',(uid,d.id,stored.revision,stored.model_dump_json()))
            else:
                old=db.execute('SELECT document FROM building_intakes WHERE owner_id=? AND intake_id=?',(uid,d.id)).fetchone()
                if not old:raise HTTPException(404,'Taslak bulunamadı.')
                old=Intake.model_validate_json(old[0])
                if old.revision!=d.revision or old.project_id!=d.project_id:raise HTTPException(409,'Taslak değişti; yeniden yükleyin.')
                if old.project_id:raise HTTPException(409,'Projeye aktarılmış taslak değiştirilemez.')
                db.execute('UPDATE building_intakes SET revision=?,document=? WHERE owner_id=? AND intake_id=?',(stored.revision,stored.model_dump_json(),uid,d.id))
            if project:
                folder=main.data_root()/'projects';folder.mkdir(parents=True,exist_ok=True)
                target=folder/(project.id+'.json');temp=target.with_suffix('.tmp');temp.write_text(project.model_dump_json(),encoding='utf-8');os.replace(temp,target)
    return IntakeView(draft=stored,readiness=readiness(stored))

def install(main):
    app=main.app
    @app.get('/api/intakes',response_model=list[IntakeView])
    def list_intakes():return [IntakeView(draft=d,readiness=readiness(d)) for d in rows(main)]
    @app.post('/api/intakes',response_model=IntakeView)
    def create_intake(d:Intake):
        with main.lock:return save(main,d,create=True)
    @app.put('/api/intakes/{intake_id}',response_model=IntakeView)
    def update_intake(intake_id:str,d:Intake):
        if intake_id!=d.id:raise HTTPException(422,'Taslak kimliği eşleşmiyor.')
        with main.lock:return save(main,d)
    @app.post('/api/intakes/{intake_id}/publish',response_model=IntakeView)
    def publish_intake(intake_id:str,d:Intake):
        if intake_id!=d.id:raise HTTPException(422,'Taslak kimliği eşleşmiyor.')
        with main.lock:return save(main,d,publish=True)

CSV_HEADER=['name','scope','use_type','location','area_m2','year','electricity_kwh','gas_kwh','heating_gas_fraction','heating_split_source','heating_system','system_scope','heat_distribution','connection_kw','connection_source']
class CSVBody(Model):
    text:str=Field(max_length=100000)

def csv_preview(body):
    errors=[];buildings=[]
    try:
        reader=csv.DictReader(io.StringIO(body.text.lstrip('\ufeff')),strict=True)
        if reader.fieldnames!=CSV_HEADER:raise ValueError('Şablon sütunları ve sırası eşleşmeli.')
        records=list(reader)
        if not 1<=len(records)<=20:raise ValueError('1–20 bina satırı gerekir.')
        for line,row in enumerate(records,2):
            try:
                data={k:v for k,v in row.items() if v not in ('',None)}
                for key in ('electricity_kwh','gas_kwh'):
                    value=data.pop(key,None)
                    data['electricity' if key=='electricity_kwh' else 'fuel']={'value':value,'source_kind':'user_estimate','source':'Kullanıcı CSV girişi; ölçüm doğrulanmadı.'}
                buildings.append(BuildingInput.model_validate(data))
            except Exception:errors.append({'row':line,'field':'row','message':'Birim, sayı, kapsam veya sistem geçerli değil; şablondaki kWh/m²/yıl birimlerini kontrol edin.'})
    except (ValueError,csv.Error):errors.append({'row':1,'field':'header','message':'Geçerli UTF-8 CSV ve verilen şablon sütunları gerekli.'})
    return {'buildings':[b.model_dump(mode='json') for b in buildings],'errors':errors,'units':{'area_m2':'m²','year':'tam takvim yılı','electricity_kwh':'kWh/yıl','gas_kwh':'enerji içeriği kWh/yıl','connection_kw':'kW'}}
