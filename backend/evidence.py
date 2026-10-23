"""Deterministic decision evidence and one-at-a-time fixed-plan sensitivity."""
import math

from pydantic import ValidationError

from engine import calculate_package, solve_packages, summarize
from models import Campus
from profiles import generate_profiles


def evaluate(campus, chosen, baseline):
    after = summarize(campus.buildings, chosen, campus.scenario, campus.connection_groups)
    investment = sum(p.report.investment_try for p in chosen)
    savings = baseline.total_energy_kwh_year-after.total_energy_kwh_year
    return {'after':after.model_dump(mode='json'), 'investment_try':investment,
        'budget_remaining_try':campus.scenario.budget_try-investment,
        'budget_met':investment<=campus.scenario.budget_try+.01,
        'energy_savings_kwh_year':savings,
        'energy_savings_pct':100*savings/baseline.total_energy_kwh_year if baseline.total_energy_kwh_year>0 else None,
        'net_savings_try_year':baseline.operating_cost_try_year-after.operating_cost_try_year,
        'target_met':savings >= baseline.total_energy_kwh_year*campus.scenario.savings_target_pct/100-.001,
        'capacity_met':not any(c.violation_hours for c in after.capacity_checks),
        'capacity_violations':[c.model_dump() for c in after.capacity_checks if c.violation_hours],
        'selected_packages':[p.report.model_dump() for p in chosen]}


def from_result(campus, options, result):
    if not result.after:
        return {'status':result.status,'message':result.message,'solver':result.solver.model_dump(), 'evaluation':None}
    selections = {p.building_id:(p.candidate_id or p.package) for p in result.selected_packages}
    chosen = [next(p for p in group if (p.report.candidate_id or p.report.package)==selections[b.id]) for b,group in zip(campus.buildings,options)]
    return {'status':result.status,'message':result.message,'solver':result.solver.model_dump(),
            'evaluation':evaluate(campus,chosen,result.baseline)}


def ratio_plan(campus, options, baseline, mode="A"):
    # Global descending annual-final-kWh saved / initial TL. No upgrades after selection.
    chosen = {b.id:group[0] for b,group in zip(campus.buildings,options)}
    def incremental(p,field):return getattr(p.report,field)-getattr(chosen[p.report.building_id].report,field)
    candidates = [p for group in options for p in group if incremental(p,'energy_savings_kwh_year')>0]
    candidates.sort(key=lambda p:(-(incremental(p,'energy_savings_kwh_year')/incremental(p,'investment_try') if incremental(p,'investment_try')>0 else math.inf),
                                  p.report.building_id,p.report.candidate_id or p.report.package))
    remaining=campus.scenario.budget_try-sum(p.report.investment_try for p in chosen.values())
    assigned=set()
    for p in candidates:
        if mode=="B" and sum(v.report.energy_savings_kwh_year for v in chosen.values()) >= baseline.total_energy_kwh_year*campus.scenario.savings_target_pct/100-.001:
            break
        if p.report.building_id not in assigned and incremental(p,'investment_try')<=remaining+.001:
            cost=incremental(p,'investment_try')
            chosen[p.report.building_id]=p
            assigned.add(p.report.building_id)
            remaining-=cost
    return {'status':'heuristic','solver':None,'message':'Oran sezgiseli; optimum veya hedefe erişim kanıtı değildir.',
            'evaluation':evaluate(campus,[chosen[b.id] for b in campus.buildings],baseline)}


def decision_evidence(campus, options, request, grid_result):
    relaxed=solve_packages(campus.buildings,options,campus.scenario,request,campus.connection_groups,enforce_grid=False)
    return {'input_revision':campus.revision,'project_id':campus.id,'mode':request.mode,
        'package_universe':{b.id:[p.report.candidate_id or p.report.package for p in group] for b,group in zip(campus.buildings,options)},
        'ratio_definition':'Kaydedilmiş kat müdahaleleri sabit taban olarak bir kez bütçeden düşülür. Ek pozitif yıllık nihai enerji tasarrufu (kWh/yıl) / ek yatırım (TL), azalan sıra. Ücretsiz pozitif tasarruf önce; eşitlikte bina kimliği/paket adı. Bina başına ilk bütçeye sığan paket; yükseltme yok. Kapasite kullanılmaz. B modunda hedefe erişince durur; en düşük yatırım garantisi yoktur.',
        'scope':'Aynı girdiler, aynı uygun paket evreni, aynı fizik motoru ve bütçe. Kısıtsız optimizasyonda hem bina hem grup elektrik sınırları kaldırılır; uygunluk kuralları ve B hedefi korunur.',
        'methods':{'ratio':ratio_plan(campus,options,grid_result.baseline,request.mode),
                   'without_grid':from_result(campus,options,relaxed),'grid':from_result(campus,options,grid_result)}}


def sensitivity(campus, result):
    settings=campus.sensitivity_settings
    report={'input_revision':campus.revision,'project_id':campus.id,'fixed_plan':True,'reoptimized':False,
        'method':'Tek değişkenli düşük/temel/yüksek varsayım taraması; seçilen paketler ve pompa boyutları sabit. Çarpanlar bina bazındaki temel parametrelere uygulanır. Güven aralığı veya gerçekleşme olasılığı değildir.',
        'settings':settings.model_dump(mode='json'),'rows':[]}
    if not result.after:
        report['message']='Güncel uygun GRID planı yok; sabit plan duyarlılığı hesaplanmadı.'
        return report
    selection={p.building_id:p for p in result.selected_packages}
    profiles={b.id:generate_profiles(b,campus.profile_settings) for b in campus.buildings}
    parameters=['scop','investment','insulation']
    if any(d.kind=='roof' and d.state!='applied' for p in result.selected_packages for d in p.interventions):parameters.append('roof')
    for parameter in parameters:
        band=getattr(settings,parameter)
        for level,multiplier in [('low',band.low),('base',1.),('high',band.high)]:
            raw=campus.model_dump(mode='json')
            for building in raw['buildings']:
                a=building['retrofit']
                fields={'scop':['heat_pump_scop'],'investment':['insulation_cost_try_m2','heat_pump_cost_try_kw','heat_pump_fixed_cost_try'],
                        'insulation':['insulation_reduction_fraction'],'roof':[]}[parameter]
                for field in fields:
                    a[field]*=multiplier
                if parameter=='investment':
                    for quote in building.get('cost_quotes',{}).values():quote['amount_try']*=multiplier
                if parameter=='investment' and building.get('spatial'):
                    for field in ('roof_cost_try_m2','lighting_cost_try_m2','schedule_control_cost_try'):
                        building['spatial'][field]*=multiplier
                if parameter=='roof' and building.get('spatial'):
                    building['spatial']['roof_target_u_w_m2k']*=multiplier
            row={'parameter':parameter,'level':level,'multiplier':multiplier}
            try:
                variant=Campus.model_validate(raw)
                from interventions import selected_profile
                chosen=[selected_profile(b,profiles[b.id],variant.scenario,selection[b.id]) for b in variant.buildings]
                row.update(status='evaluated',evaluation=evaluate(variant,chosen,result.baseline),
                    effective_assumptions={b.id:{'scop':b.retrofit.heat_pump_scop,'insulation_reduction':b.retrofit.insulation_reduction_fraction,
                        'insulation_cost_try_m2':b.retrofit.insulation_cost_try_m2,'heat_pump_cost_try_kw':b.retrofit.heat_pump_cost_try_kw,
                        'heat_pump_fixed_cost_try':b.retrofit.heat_pump_fixed_cost_try,
                        **({'roof_target_u_w_m2k':b.spatial.roof_target_u_w_m2k} if b.spatial else {})} for b in variant.buildings})
            except (ValidationError,ValueError):
                row.update(status='invalid_assumptions',evaluation=None,message='Çarpan fiziksel parametre aralığını aşıyor; değer kırpılmadı, bu satır hesaplanmadı.')
            report['rows'].append(row)
    return report
