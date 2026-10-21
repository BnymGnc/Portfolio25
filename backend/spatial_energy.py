"""Auditable end-use allocation, NOT thermal dynamics or calibrated Kayseri weather."""
import calendar
from functools import lru_cache
import numpy as np
from spatial_models import SpatialSelection


def zones(b):
    return [(f,z) for f in b.spatial.floors for z in f.zones]


def annual_hours(z,year):
    days=sum(calendar.weekday(year,m,d) in z.program.days for m in range(1,13) for d in range(1,calendar.monthrange(year,m)[1]+1))
    return days*(z.program.occupied_end-z.program.occupied_start)


def known_electricity(b,year):
    return sum(z.area_m2*annual_hours(z,year)*(z.lighting_w_m2*z.program.lighting_use_fraction+z.device_w_m2*z.program.device_use_fraction)/1000
               for _,z in zones(b))+b.spatial.cooling_electricity_kwh_year+b.spatial.common_system_electricity_kwh_year


def can_schedule(z):
    p=z.program
    return p.schedule_change_allowed and not p.critical_service and (p.service_start<max(0,p.occupied_start-p.required_margin_hours) or p.service_end>min(24,p.occupied_end+p.required_margin_hours))


def validate_selection(b,selection,package='none'):
    all_zones=zones(b);ids=[z.id for _,z in all_zones]
    if len(set(selection.zone_ids))!=len(selection.zone_ids) or not set(selection.zone_ids)<=set(ids):raise ValueError('Müdahale zon kimlikleri mevcut binada ve benzersiz olmalı.')
    targets=[z for _,z in all_zones if not selection.zone_ids or z.id in selection.zone_ids]
    if (selection.roof or selection.schedule) and b.heating_system!='gas_boiler':raise ValueError('Bu ısıtma sistemi için çatı/program dönüşüm fiziği desteklenmiyor; yalnız inceleme adayı.')
    if selection.roof:
        if package in ('insulation','combined'):raise ValueError('Çatı ve çatı dahil kabuk paketi birlikte seçilemez; aynı çatının yatırımını iki kez saymayın.')
        if not b.insulation_allowed or not any(z.roof_contact and z.roof_u_w_m2k>b.spatial.roof_target_u_w_m2k for _,z in all_zones):raise ValueError('Çatı yalıtımı için uygun yüzey veya azaltım bulunmuyor.')
    if selection.lighting and not any(z.lighting_upgrade_allowed and z.target_lighting_w_m2<z.lighting_w_m2 for z in targets):raise ValueError('Seçilen alanlarda hesaplanabilir aydınlatma iyileştirmesi yok.')
    if selection.schedule:
        if b.use_type in ('Araştırma','Konut','Otel'):raise ValueError('Laboratuvar, konut ve otelin gerekli/sürekli hizmeti bu pilotta azaltılamaz; yalnız uzman inceleme adayıdır.')
        if not selection.schedule_review_ack:raise ValueError('Program değişikliği konfor doğrulaması değildir; uzman incelemesi senaryosu olduğunu onaylayın.')
        if not any(can_schedule(z) for z in targets):raise ValueError('Seçilen alanlarda hizmet gereksinimini azaltmadan program değişikliği tanımlanamadı; inceleme adayıdır.')


def validate_inputs(b,year):
    if b.spatial.cooling_electricity_kwh_year>0 and not any(z.cooling_system_id for _,z in zones(b)):
        raise ValueError('spatial.cooling_electricity_kwh_year: Pozitif soğutma enerjisi için hizmet verilen en az bir uygun zon gereklidir.')
    if known_electricity(b,year)>b.electricity_kwh_year+1e-6:raise ValueError('Tanımlı aydınlatma/cihaz/soğutma/ortak tüketim bina elektriğini aşıyor. Girdileri uzlaştırın; artık sıfırlanmadı.')
    if b.spatial.dhw_gas_kwh_year and not sum(z.dhw_weight for _,z in zones(b)):raise ValueError('Sıcak suyu dağıtmak için kullanım ağırlığı eksik.')
    validate_selection(b,b.spatial_selection)


@lru_cache(maxsize=8)
def weather(year,timezone):
    from profiles import time_axis
    axis=time_axis(year,timezone)
    hour=np.array([t.hour for t in axis]);day=np.array([t.timetuple().tm_yday for t in axis]);weekday=np.array([t.weekday() for t in axis])
    temperature=10+15*np.cos(2*np.pi*(day-200)/365.25)+5*np.sin(2*np.pi*(hour-8)/24)
    return tuple(t.isoformat() for t in axis),hour,weekday,np.maximum(18-temperature,0),np.maximum(temperature-22,0)


def scale(shape,total):
    if total==0:return np.zeros_like(shape,dtype=float)
    if float(shape.sum())<=0:raise ValueError('Pozitif yıllık enerjinin saatlik dağıtımı için desteklenen program yok.')
    return shape*(total/float(shape.sum()))


def build_components(b,settings,selection=None):
    selection=selection or SpatialSelection()
    validate_inputs(b,settings.year);validate_selection(b,selection)
    timestamps,hour,weekday,hdd,cdd=weather(settings.year,settings.timezone)
    records=[];total_heat_weight=0.;total_cooling_weight=0.
    for f,z in zones(b):
        p=z.program;day=np.isin(weekday,p.days)
        occupied=day&(hour>=p.occupied_start)&(hour<p.occupied_end)
        service=day&(hour>=p.service_start)&(hour<p.service_end)
        targeted=not selection.zone_ids or z.id in selection.zone_ids
        change_schedule=selection.schedule and targeted and can_schedule(z)
        new_service=(day&(hour>=max(p.service_start,p.occupied_start-p.required_margin_hours))&(hour<min(p.service_end,p.occupied_end+p.required_margin_hours))) if change_schedule else service
        wall=(z.facade_m2-z.window_m2)*z.wall_u_w_m2k+z.window_m2*z.window_u_w_m2k
        roof=z.area_m2*z.roof_u_w_m2k if z.roof_contact else 0.
        other=(z.area_m2*z.ground_u_w_m2k if z.ground_contact else 0.)+.33*z.air_changes_hour*z.area_m2*z.height_m
        after_roof=z.area_m2*min(z.roof_u_w_m2k,b.spatial.roof_target_u_w_m2k) if z.roof_contact and selection.roof else roof
        # Setback weight is an explicit allocation assumption, not indoor temperature.
        heat_weight=(wall+roof+other)*hdd*(.45+.55*service)
        after_weight=(wall+after_roof+other)*hdd*(.45+.55*new_service)
        exposure={'K':.8,'G':1.2,'D':1.,'B':1.1}[z.orientation]
        cool_weight=(z.area_m2*.1+z.window_m2*exposure)*cdd*(.15+.85*service) if z.cooling_system_id else np.zeros_like(cdd)
        after_cool_weight=(z.area_m2*.1+z.window_m2*exposure)*cdd*(.15+.85*new_service) if z.cooling_system_id else np.zeros_like(cdd)
        lighting=occupied*z.area_m2*z.lighting_w_m2*p.lighting_use_fraction/1000
        light_after=occupied*z.area_m2*(min(z.lighting_w_m2,z.target_lighting_w_m2) if selection.lighting and targeted and z.lighting_upgrade_allowed else z.lighting_w_m2)*p.lighting_use_fraction/1000
        devices=occupied*z.area_m2*z.device_w_m2*p.device_use_fraction/1000
        records.append({'floor':f,'zone':z,'heat_weight':heat_weight,'after_weight':after_weight,'cool_weight':cool_weight,'after_cool_weight':after_cool_weight,
            'lighting':lighting,'light_after':light_after,'devices':devices,'schedule_changed':change_schedule})
        total_heat_weight+=float(heat_weight.sum());total_cooling_weight+=float(cool_weight.sum())
    if b.heating_kwh_year>0 and total_heat_weight<=0:raise ValueError('Isı ihtiyacı dağıtımı için kabuk/program bilgisi eksik.')
    heat_scale=b.heating_kwh_year*b.retrofit.boiler_efficiency/total_heat_weight if total_heat_weight else 0
    cool_scale=b.spatial.cooling_electricity_kwh_year/total_cooling_weight if total_cooling_weight else 0
    if b.spatial.cooling_electricity_kwh_year and total_cooling_weight<=0:raise ValueError('Soğutma enerjisi için hizmet alanı eksik.')
    residual=max(0.,b.electricity_kwh_year-known_electricity(b,settings.year))
    dhw_total=sum(z.dhw_weight for _,z in zones(b))
    for r in records:
        z=r['zone'];area_fraction=z.area_m2/b.area_m2
        r.update(heat=r['heat_weight']*heat_scale,heat_after=r['after_weight']*heat_scale,
            cooling=r['cool_weight']*cool_scale,cooling_after=r['after_cool_weight']*cool_scale,
            unseparated=np.full(len(hour),residual*area_fraction/len(hour)),
            dhw_gas=b.spatial.dhw_gas_kwh_year*z.dhw_weight/dhw_total if dhw_total else 0.,
            other_gas=(b.non_heating_gas_kwh_year-b.spatial.dhw_gas_kwh_year)*area_fraction)
        r['electricity']=r['lighting']+r['devices']+r['cooling']+r['unseparated']
        r['electricity_after']=r['light_after']+r['devices']+r['cooling_after']+r['unseparated']
    common=np.full(len(hour),b.spatial.common_system_electricity_kwh_year/len(hour))
    electricity=np.sum([r['electricity'] for r in records],axis=0)+common
    electricity_after=np.sum([r['electricity_after'] for r in records],axis=0)+common
    heat=np.sum([r['heat'] for r in records],axis=0);heat_after=np.sum([r['heat_after'] for r in records],axis=0)
    roof_area=sum(z.area_m2 for _,z in zones(b) if z.roof_contact)
    light_area=sum(r['zone'].area_m2 for r in records if selection.lighting and (not selection.zone_ids or r['zone'].id in selection.zone_ids) and r['zone'].lighting_upgrade_allowed and r['zone'].target_lighting_w_m2<r['zone'].lighting_w_m2)
    cost=(roof_area*b.spatial.roof_cost_try_m2 if selection.roof else 0)+light_area*b.spatial.lighting_cost_try_m2+(b.spatial.schedule_control_cost_try if selection.schedule else 0)
    return {'timestamps':timestamps,'records':records,'common_kw':common,'electricity':electricity,'electricity_after':electricity_after,
            'heat':heat,'heat_after':heat_after,'investment_try':cost,'residual_electricity_kwh_year':residual,'roof_area_m2':roof_area}


def profile_inputs(b,settings):
    c=build_components(b,settings)
    from profiles import AnnualProfiles
    return AnnualProfiles(c['timestamps'],c['electricity'],c['heat'])


def transformed_inputs(b,profile):
    from models import ProfileSettings
    settings=ProfileSettings(year=int(profile.timestamps[0][:4]))
    c=build_components(b,settings,b.spatial_selection)
    return c['electricity_after'],c['heat_after'],c['investment_try']


def allocation(b,settings,package_profile=None):
    if package_profile and b.interventions is not None:
        # Partition the actual full combination, including the applied physical baseline.
        b=b.model_copy(deep=True)
        active={d.kind for d in package_profile.report.interventions}
        b.spatial_selection=SpatialSelection(**{k:k in active for k in ('roof','lighting','schedule')},zone_ids=b.spatial_selection.zone_ids,schedule_review_ack=b.spatial_selection.schedule_review_ack)
    c=build_components(b,settings,b.spatial_selection if package_profile else SpatialSelection())
    records=c['records'];rows=[]
    for r in records:
        z=r['zone'];q=r['heat_after'] if package_profile else r['heat']
        if package_profile:
            total=c['heat_after'];fraction=np.divide(q,total,out=np.zeros_like(q),where=total>0)
            heat=float((package_profile.useful_heat_kw*fraction).sum())
            hp=float((package_profile.heat_pump_heat_kw*fraction).sum())
            hp_el=hp/b.retrofit.heat_pump_scop
            gas=float((package_profile.backup_heat_kw*fraction).sum())/b.retrofit.boiler_efficiency
        else:heat=float(q.sum());hp=0.;hp_el=0.;gas=heat/b.retrofit.boiler_efficiency
        e=float((r['electricity_after'] if package_profile else r['electricity']).sum())+hp_el
        parts={'heating_electricity':hp_el,'cooling':float((r['cooling_after'] if package_profile else r['cooling']).sum()),
            'lighting':float((r['light_after'] if package_profile else r['lighting']).sum()),'devices':float(r['devices'].sum()),
            'unseparated_electricity':float(r['unseparated'].sum()),'heating_fuel':gas,'hot_water_fuel':r['dhw_gas'],'unseparated_fuel':r['other_gas'],'common_systems':0.}
        rows.append({'zone_id':z.id,'name':z.name,'floor_id':r['floor'].id,'floor_name':r['floor'].name,'use':z.use,'area_m2':z.area_m2,
            'electricity_kwh_year':e,'fuel_kwh_year':gas+r['dhw_gas']+r['other_gas'],'useful_heat_kwh_year':heat,'hp_heat_kwh_year':hp,
            'components':parts,'common_area':z.common_area,'kind':'modelled_allocation','source':z.source})
    common=float(c['common_kw'].sum())
    rows.append({'zone_id':'SHARED','name':'Merkezî sistemlerin ortak elektriği','floor_id':'SHARED','floor_name':'Katlara dağıtılmamış ortak sistemler',
        'use':'Ortak sistemler','area_m2':0,'electricity_kwh_year':common,'fuel_kwh_year':0.,'useful_heat_kwh_year':0.,'hp_heat_kwh_year':0.,'common_area':True,
        'kind':'assumption','source':'Ayrı tanımlı pompalar/asansör/ortak ekipman elektriği; kat/zon satırlarına tekrar eklenmez.',
        'components':{key:common if key=='common_systems' else 0. for key in rows[0]['components']}})
    def aggregate(key,name_key):
        result={}
        for row in rows:
            id=row[key]
            if id not in result:result[id]={'id':id,'name':row[name_key],'area_m2':0.,'electricity_kwh_year':0.,'fuel_kwh_year':0.,'useful_heat_kwh_year':0.,'components':{k:0. for k in row['components']}}
            for field in ('area_m2','electricity_kwh_year','fuel_kwh_year','useful_heat_kwh_year'):result[id][field]+=row[field]
            for field,value in row['components'].items():result[id]['components'][field]+=value
        return list(result.values())
    totals={key:sum(row[key] for row in rows) for key in ('electricity_kwh_year','fuel_kwh_year','useful_heat_kwh_year')}
    expected_e=package_profile.report.electricity_kwh_year if package_profile else b.electricity_kwh_year
    expected_f=(package_profile.report.heating_gas_kwh_year if package_profile else b.heating_kwh_year)+b.non_heating_gas_kwh_year
    errors={'electricity_kwh':totals['electricity_kwh_year']-expected_e,'fuel_kwh':totals['fuel_kwh_year']-expected_f}
    if any(abs(v)>1e-5 for v in errors.values()):raise ValueError('Kat/zon enerji uzlaştırması başarısız; sonuç gösterilmedi.')
    return {'totals':totals,'by_floor':aggregate('floor_id','floor_name'),'by_use':aggregate('use','use'),'zones':rows,'reconciliation':errors,
        'method':'Aydınlatma/cihaz: alan × kurulu W/m² × kullanım saatleri × kullanım katsayısı. Isı: U×yüzey + 0,33×hava değişimi×hacim, sentetik derece-saat ve hizmet programına göre normalize edilir. Artık elektrik alanla dağıtılır; ortak sistem elektriği ayrı satırdır. Aynı toplamın iki kırılımı birbirine eklenmez.',
        'residual_electricity_kwh_year':c['residual_electricity_kwh_year'],'comfort_modelled':False}
