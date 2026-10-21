from engine import calculate_package,capacity_checks,payback
from profiles import generate_profiles
from spatial_models import SpatialSelection
from spatial_energy import allocation,zones,can_schedule,validate_selection,validate_inputs
from eligibility import exclusion_reason


def evaluate(campus,building,selection,package='none',spatial=None,interventions=None):
    raw=building.model_dump(mode='json');raw['spatial_selection']=selection.model_dump()
    if spatial is not None:raw['spatial']=spatial.model_dump()
    if interventions is not None:raw['interventions']=[d.model_dump() for d in interventions]
    from models import Building
    target=Building.model_validate(raw)
    validate_inputs(target,campus.profile_settings.year);validate_selection(target,selection,package)
    if reason:=exclusion_reason(target,package):raise ValueError(reason)
    profile=generate_profiles(target,campus.profile_settings)
    from interventions import baseline_profile,evaluate_combination
    before=baseline_profile(target,profile,campus.scenario)
    actions={k for k in ('roof','lighting','schedule') if getattr(selection,k)}|({'insulation'} if package in ('insulation','combined') else set())|({'heat_pump'} if package in ('heat_pump','combined') else set())
    if target.interventions is not None:
        from interventions import policy
        decisions=policy(target)
        forbidden={a for a in actions if decisions.get(a,'excluded')=='excluded'}
        if forbidden:raise ValueError('Önizlemede dışlanmış müdahale seçildi: '+', '.join(sorted(forbidden)))
        actions|={a for a,state in decisions.items() if state in ('applied','mandatory')}
    after=evaluate_combination(target,profile,campus.scenario,actions,before) if target.interventions is not None else calculate_package(target,profile,campus.scenario,package)
    chosen=[];baseline=[]
    for b in campus.buildings:
        if b.id==target.id:b=target
        p=generate_profiles(b,campus.profile_settings)
        old=baseline_profile(b,p,campus.scenario)
        baseline.append(old);chosen.append(after if b.id==target.id else old)
    checks=capacity_checks(campus.buildings,chosen,campus.scenario,campus.connection_groups)
    oldchecks=capacity_checks(campus.buildings,baseline,campus.scenario,campus.connection_groups)
    return {'project_id':campus.id,'input_revision':campus.revision,'building_id':building.id,'selection':selection.model_dump(),'package':package,
        'before':before.report.model_dump(),'after':after.report.model_dump(),
        'electricity_savings_kwh_year':before.report.electricity_kwh_year-after.report.electricity_kwh_year,
        'fuel_savings_kwh_year':before.report.heating_gas_kwh_year-after.report.heating_gas_kwh_year,
        'investment_try':after.report.investment_try,'energy_cost_savings_try_year':after.report.net_savings_try_year+after.report.maintenance_cost_try_year,
        'net_savings_try_year':after.report.net_savings_try_year,'simple_payback_years':payback(after.report.investment_try,after.report.net_savings_try_year),
        'budget_met':after.report.investment_try<=campus.scenario.budget_try+.01,
        'capacity_checks':checks,'baseline_capacity_checks':oldchecks,'capacity_met':not any(c.violation_hours for c in checks),
        'capacity_context':'Diğer proje binaları müdahalesiz mevcut durumdadır; bu bir portföy optimizasyonu değildir. Kaydedilen kat müdahaleleri sonraki portföy hesabına bir kez katılır.',
        'allocation_before':allocation(target,campus.profile_settings,before) if target.interventions is not None else allocation(target,campus.profile_settings),'allocation_after':allocation(target,campus.profile_settings,after),
        'comfort_modelled':False,'review_required':selection.schedule,
        'warnings':['Kat/zon enerji dağılımı açıklanabilir normalize paylaştırmadır; ayrıntılı termal simülasyon değildir.',
                    'Sıcak su ve diğer gaz korunur; sıcak su müdahale etkisi hesaplanmadı.',
                    'Sıcaklık dinamiği yok; konfor korundu sonucu üretilmez. Program değişikliği uzman incelemesi gerektirir.']}


def recommendations(campus,building):
    result=[]
    candidates=[('roof','Çatı yalıtımı',SpatialSelection(roof=True),'none'),
                ('lighting','Aydınlatma iyileştirmesi',SpatialSelection(lighting=True),'none'),
                ('schedule','HVAC çalışma programı',SpatialSelection(schedule=True,schedule_review_ack=True),'none'),
                ('insulation','Kabuk yalıtımı',SpatialSelection(),'insulation'),
                ('heat_pump','Isı pompası dönüşümü',SpatialSelection(),'heat_pump')]
    for id,title,selection,package in candidates:
        affected=[{'floor_id':f.id,'zone_id':z.id,'name':z.name} for f,z in zones(building) if
                  (id=='roof' and z.roof_contact) or (id=='lighting' and z.lighting_upgrade_allowed and z.lighting_w_m2>z.target_lighting_w_m2) or
                  (id=='schedule' and can_schedule(z)) or id in ('insulation','heat_pump')]
        finding=({'roof':f'Çatıya temas eden {sum(z.area_m2 for _,z in zones(building) if z.roof_contact):g} m² yüzey; U hedefi {building.spatial.roof_target_u_w_m2k:g} W/m²K.',
                  'lighting':'Kurulu ve hedef W/m² farkı, kullanım saatleri ve kullanım katsayısıyla hesaplanır; yüksek tüketim payı tek başına verimsizlik kanıtı değildir.',
                  'schedule':'Mevcut hizmet penceresinin kullanım saati + gerekli hazırlık payını aştığı, kritik olmayan alanlar tarandı.',
                  'insulation':'Mevcut motorun yalnız ilgili faydalı ısı payını azaltan kabuk paketi.',
                  'heat_pump':'Mevcut gaz kazanı, sulu dağıtım, SCOP, termal boyut ve kazan yedeği varsayımları.'})[id]
        try:
            preview=evaluate(campus,building,selection,package)
            effect={key:preview[key] for key in ('electricity_savings_kwh_year','fuel_savings_kwh_year','investment_try','net_savings_try_year','energy_cost_savings_try_year','capacity_met')}
            effect['building_peak_change_kw']=preview['after']['electric_peak_kw']-preview['before']['electric_peak_kw']
            result.append({'id':id,'title':title,'status':'calculated_review_required' if id=='schedule' else 'calculated',
                'finding':finding,'affected':affected,'effect':effect,'conditions':'Sentetik fizik/kullanım/maliyet varsayımlarıyla senaryo; yerinde sistem, hizmet ve teklif doğrulaması gerekir.',
                'missing_information':sorted({note for _,z in zones(building) for note in z.missing_information})})
        except ValueError as error:
            result.append({'id':id,'title':title,'status':'review_only','finding':finding,'affected':affected,'effect':None,
                'conditions':str(error),'missing_information':['Uygulanabilirlik veya korunacak hizmet koşulu sağlanmadı; tasarruf iddiası yok.']})
    return result


def analysis(campus,building):
    from interventions import baseline_profile
    base=baseline_profile(building,generate_profiles(building,campus.profile_settings),campus.scenario)
    return {'project_id':campus.id,'input_revision':campus.revision,'building_id':building.id,
        'spatial':building.spatial.model_dump(),'selection':building.spatial_selection.model_dump(),
        'baseline':allocation(building,campus.profile_settings,base) if building.interventions is not None else allocation(building,campus.profile_settings),'recommendations':recommendations(campus,building),
        'weather':campus.pilot.get('weather') if campus.pilot else None,'source':'Sentetik varsayımlar üzerinden modellenmiş dağılım; ölçülmüş kat verisi değildir.'}
