"""Four independent projects, eight synthetic buildings; deterministic optional sample."""
import hashlib
import random
from models import Building,Campus,ConnectionGroup,ProfileSettings,Provenance,RetrofitAssumptions,Scenario
from spatial_models import Floor,Zone,SharedSystem,SpatialModel,UseProgram
from spatial_energy import known_electricity

TITLE='Kayseri için hazırlanmış sentetik pilot senaryo — saha ölçümü değildir.'
DATASET='kayseri-synthetic-v1'


def project_id(key):return 'project-'+hashlib.sha256((DATASET+'-'+key).encode()).hexdigest()[:12]


def make_building(index,name,use,area,floor_count,heat_intensity,dhw_intensity,detailed=False):
    rng=random.Random(25+index)
    continuous=use in ('Konut','Otel','Araştırma')
    p=UseProgram(days=list(range(7)) if continuous or name=='Kütüphane' else list(range(5)),
        occupied_start=0 if continuous else 8,occupied_end=24 if continuous else 22 if name=='Kütüphane' else 18,
        service_start=0 if continuous else 6,service_end=24 if continuous or name=='Kütüphane' else 22,
        lighting_use_fraction=.18 if use=='Konut' else .35 if use=='Otel' else .65 if use=='Araştırma' else .8,
        device_use_fraction=.35 if use=='Konut' else .45 if use=='Otel' else .8 if use=='Araştırma' else .65,
        people_per_100m2=3 if use in ('Konut','Otel') else 12 if use=='Eğitim' else 5,
        critical_service=continuous,schedule_change_allowed=not continuous)
    footprint=area/floor_count;perimeter=4*footprint**.5
    if detailed:
        layout=([('Derslik','Eğitim',.55),('Bilgisayar alanı','Bilgisayar',.25),('Dolaşım','Ortak alan',.2)] if use=='Eğitim' else
                [('Yaşam alanı','Konut yaşam',.55),('Yatak odaları','Konut yatak',.25),('Merdiven ve dolaşım','Ortak alan',.2)] if use=='Konut' else
                [('Açık ofis','Ofis',.6),('Toplantı','Toplantı',.2),('Dolaşım','Ortak alan',.2)])
    else:layout=[('Ana kullanım alanı',use,.82),('Ortak alan','Ortak alan',.18)]
    floors=[];number=0
    for i in range(floor_count):
        floor_zones=[]
        for label,purpose,fraction in layout:
            number+=1;common=purpose=='Ortak alan';zarea=footprint*fraction;height=3.5 if use in ('Eğitim','Araştırma') else 3.
            facade=perimeter*height*fraction
            floor_zones.append(Zone(id=f'Z{number:03d}',name=label,use=purpose,area_m2=zarea,height_m=height,
                program=p.model_copy(update={'people_per_100m2':1 if common else p.people_per_100m2},deep=True),
                facade_m2=facade,window_m2=facade*(.15 if common else .32 if use=='Ofis' else .25),orientation=('G','D','K')[number%3],
                roof_contact=i==floor_count-1,ground_contact=i==0,wall_u_w_m2k=round(rng.uniform(.9,1.4),2),
                roof_u_w_m2k=1.25,air_changes_hour=2 if use=='Araştırma' else .5,
                lighting_w_m2=5 if common else 10 if use=='Ofis' else 9,
                target_lighting_w_m2=3 if common else 4.5,device_w_m2=1 if common else 35 if use=='Araştırma' else 12 if use=='Ofis' else 7,
                heating_system_id='HEAT-1',cooling_system_id=None if common else 'COOL-1',
                dhw_weight=0 if common else zarea,common_area=common,
                missing_information=['Zon sayaçları, gerçek pencere/cephe ve konfor verisi yok.']+([] if detailed else ['Kaba ana kullanım/ortak alan ayrımı; oda düzeyi model yok.'])))
        floors.append(Floor(id=f'F{i:02d}',name='Zemin kat' if i==0 else f'{i}. kat',area_m2=footprint,zones=floor_zones))
    ids=[z.id for f in floors for z in f.zones];cooled=[z.id for f in floors for z in f.zones if z.cooling_system_id]
    spatial=SpatialModel(floors=floors,detailed_zones=detailed,systems=[
        SharedSystem(id='HEAT-1',name='Bina merkezî ısıtma sistemi',kind='heating',served_zone_ids=ids),
        SharedSystem(id='COOL-1',name='Birden çok kata hizmet veren soğutma sistemi',kind='cooling',served_zone_ids=cooled),
        SharedSystem(id='DHW-1',name='Ayrı sıcak su sistemi · müdahale yok',kind='domestic_hot_water',served_zone_ids=ids)],
        cooling_electricity_kwh_year=area*(28 if use=='Araştırma' else 25 if use=='Otel' else 18 if use=='Ofis' else 8 if use=='Konut' else 14),
        common_system_electricity_kwh_year=area*(10 if use=='Otel' else 7 if use=='Konut' else 5),dhw_gas_kwh_year=area*dhw_intensity)
    b=Building(id=f'B{index:02d}',name=name,use_type=use,area_m2=area,year_built=1995+index*2,
        electricity_kwh_year=1e8,heating_kwh_year=area*(heat_intensity+rng.randint(-8,8)),
        non_heating_gas_kwh_year=area*(dhw_intensity+(15 if use=='Otel' else 8)),peak_electric_kw=0,
        connection_limit_kw=round(area*.14,2),provenance=Provenance(kind='synthetic',seed=25,source=TITLE+' Sabit seed=25; kurum/işletme temsili değildir.'),
        heat_distribution='low_temperature_water',system_source='Sentetik düşük sıcaklıklı sulu dağıtım/gaz kazanı varsayımı; saha doğrulaması yok.',
        retrofit=RetrofitAssumptions(heat_pump_capacity_kw_thermal=area*.045),spatial=spatial)
    b.electricity_kwh_year=round(known_electricity(b,2025)+area*10,2)
    return b


def create_pilot():
    buildings=[make_building(*args) for args in [
        (1,'Eğitim binası','Eğitim',4800,4,155,3,True),(2,'Kütüphane','Eğitim',3600,3,145,3,False),
        (3,'Araştırma laboratuvarı','Araştırma',2400,2,195,4,False),(4,'İdari bina','İdari',1800,3,140,3,False),
        (5,'A blok','Konut',3000,5,160,55,True),(6,'B blok','Konut',3300,5,150,55,False),
        (7,'Bağımsız ofis','Ofis',2100,3,140,4,True),(8,'Küçük otel','Otel',2800,4,155,85,False)]]
    groups=[('campus','Temsilî kampüs',buildings[:4],12_000_000,True,1100),('housing','Temsilî konut sitesi',buildings[4:6],7_000_000,False,None),
            ('office','Bağımsız ofis',buildings[6:7],2_800_000,False,None),('hotel','Küçük otel',buildings[7:],4_000_000,False,None)]
    result=[]
    for key,name,bs,budget,shared,capacity in groups:
        connections=[ConnectionGroup(id='G01',name='Sentetik kampüs ortak elektrik bağlantısı',building_ids=[b.id for b in bs],capacity_kw=capacity)] if shared else [ConnectionGroup(id=f'G{i:02d}',name=b.name+' bağımsız elektrik bağlantısı',building_ids=[b.id],capacity_kw=b.connection_limit_kw) for i,b in enumerate(bs,1)]
        result.append(Campus(id=project_id(key),name=name,revision=1,buildings=bs,provenance=bs[0].provenance,
            profile_settings=ProfileSettings(seed=25,year=2025,source='Ortak kayseri-synthetic-v1 saatlik hava senaryosu; saha/hava ölçümü değil. Europe/Istanbul, 2025, 1 saat.'),
            scenario=Scenario(budget_try=budget,savings_target_pct=25,electric_capacity_kw=connections[0].capacity_kw,electricity_price_try_kwh=4.5,heating_price_try_kwh=1.5),connection_groups=connections,
            pilot={'dataset':DATASET,'title':TITLE,'seed':25,'project_key':key,'weather':{'kind':'synthetic','year':2025,'resolution_hours':1,'timezone':'Europe/Istanbul','source':'Proje içinde üretilmiş ortak sentetik eğri; Kayseri ölçümü veya doğrulanmış yerel iklim modeli değildir.','license':'Harici hava dosyası/lisansı yok; proje içi sentetik varsayım.'},
                'heating_independence':'Her binanın ısıtma sistemi bağımsızdır; bloklar arası ortak kazan/ekipman yok. Elektrik grubu paylaşımı ısıtma sistemi paylaşımı anlamına gelmez.'}))
    return result
