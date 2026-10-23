"""Bounded action templates: at most 32 combinations per building, one zone scope.

Annual inputs are the immutable synthetic reference. Applied actions form the physical
baseline; their historical CAPEX is never charged to the new plan.
"""
from itertools import product
from spatial_models import SpatialSelection,InterventionDecision

KINDS=('roof','insulation','lighting','schedule','heat_pump')


def policy(building):
    if building.interventions is not None:return {d.kind:d.state for d in building.interventions}
    # Legacy selections retain exactly their fixed, new-investment semantics.
    return {**{k:'mandatory' for k in ('roof','lighting','schedule') if getattr(building.spatial_selection,k)},
        'insulation':'candidate','heat_pump':'candidate'}


def heating_package(actions):
    return 'combined' if {'insulation','heat_pump'}<=actions else 'insulation' if 'insulation' in actions else 'heat_pump' if 'heat_pump' in actions else 'none'


def raw_combination(b,profile,scenario,actions):
    from engine import calculate_package
    from eligibility import exclusion_reason
    candidate=b.model_copy(deep=True);candidate.interventions=None
    candidate.spatial_selection=SpatialSelection(**{k:k in actions for k in ('roof','lighting','schedule')},
        zone_ids=b.spatial_selection.zone_ids,schedule_review_ack=b.spatial_selection.schedule_review_ack)
    if actions & {'roof','lighting','schedule'} and not b.spatial:raise ValueError('Kat müdahalesi için kat/zon modeli gerekiyor.')
    package=heating_package(actions)
    if reason:=exclusion_reason(candidate,package):raise ValueError(reason)
    result=calculate_package(candidate,profile,scenario,package)
    costs={}
    if 'insulation' in actions:costs['insulation']=b.area_m2*b.retrofit.insulation_cost_try_m2
    if 'heat_pump' in actions:costs['heat_pump']=b.retrofit.heat_pump_capacity_kw_thermal*b.retrofit.heat_pump_cost_try_kw+b.retrofit.heat_pump_fixed_cost_try
    if b.spatial and actions & {'roof','lighting','schedule'}:
        from spatial_energy import build_components
        from models import ProfileSettings
        settings=ProfileSettings(year=int(profile.timestamps[0][:4]))
        for action in ('roof','lighting','schedule'):
            if action in actions:
                single=candidate.model_copy(deep=True);single.spatial_selection=SpatialSelection(**{action:True},zone_ids=b.spatial_selection.zone_ids,schedule_review_ack=b.spatial_selection.schedule_review_ack)
                costs[action]=build_components(single,settings,single.spatial_selection)['investment_try']
    costs={k:b.cost_quotes[k].amount_try if k in b.cost_quotes else v for k,v in costs.items()}
    return result,costs


def baseline_profile(b,profile,scenario):
    from engine import calculate_package
    if b.interventions is None:return calculate_package(b,profile,scenario,'none',apply_spatial=False)
    applied={k for k,s in policy(b).items() if s=='applied'}
    base,_=raw_combination(b,profile,scenario,applied)
    r=base.report;r.investment_try=0;r.spatial_investment_try=0;r.maintenance_cost_try_year=0
    r.energy_savings_kwh_year=0;r.net_savings_try_year=0;r.simple_payback_years=None;r.candidate_id='none';r.emissions_change_kg_year=0
    r.interventions=[InterventionDecision(kind=k,state='applied') for k in KINDS if k in applied]
    r.intervention_costs={k:0. for k in applied}
    return base


def evaluate_combination(b,profile,scenario,actions,base=None):
    from engine import payback
    base=base or baseline_profile(b,profile,scenario)
    states=policy(b);applied={k for k,s in states.items() if s=='applied'}
    result,costs=raw_combination(b,profile,scenario,actions|applied)
    r=result.report
    new=actions-applied
    costs={k:v for k,v in costs.items() if k in new}
    r.investment_try=sum(costs.values());r.spatial_investment_try=sum(v for k,v in costs.items() if k in ('roof','lighting','schedule'))
    r.maintenance_cost_try_year=r.investment_try*b.retrofit.annual_maintenance_fraction
    old=base.report
    r.energy_savings_kwh_year=old.electricity_kwh_year+old.heating_gas_kwh_year-r.electricity_kwh_year-r.heating_gas_kwh_year
    r.net_savings_try_year=(old.electricity_kwh_year-r.electricity_kwh_year)*scenario.electricity_price_try_kwh+(old.heating_gas_kwh_year-r.heating_gas_kwh_year)*scenario.heating_price_try_kwh-r.maintenance_cost_try_year
    r.emissions_change_kg_year=(r.electricity_kwh_year-old.electricity_kwh_year)*scenario.electricity_emission_kg_kwh+(r.heating_gas_kwh_year-old.heating_gas_kwh_year)*scenario.gas_emission_kg_kwh
    r.simple_payback_years=payback(r.investment_try,r.net_savings_try_year)
    r.useful_heat_before_kwh_year=old.useful_heat_after_kwh_year
    r.candidate_id='+'.join(k for k in KINDS if k in new) or 'none'
    r.interventions=[InterventionDecision(kind=k,state=states.get(k,'candidate')) for k in KINDS if k in actions|applied]
    r.intervention_costs={**{k:0. for k in applied},**costs}
    result.baseline=base
    return result


def candidates(b,profile,scenario):
    from engine import PACKAGES,calculate_package
    from eligibility import exclusion_reason
    if b.interventions is None:
        result=[calculate_package(b,profile,scenario,p) for p in PACKAGES if not exclusion_reason(b,p)]
        base=baseline_profile(b,profile,scenario)
        for p in result:
            actions=set(p.report.spatial_interventions)|({'insulation'} if p.report.package in ('insulation','combined') else set())|({'heat_pump'} if p.report.package in ('heat_pump','combined') else set())
            p.report.candidate_id=p.report.package
            p.report.interventions=[InterventionDecision(kind=k,state='mandatory' if k in p.report.spatial_interventions else 'candidate') for k in KINDS if k in actions]
            p.baseline=base
        return result
    states=policy(b);base=baseline_profile(b,profile,scenario)
    mandatory={k for k,s in states.items() if s=='mandatory'};optional=[k for k in KINDS if states.get(k)=='candidate']
    # A mandatory/applied conflict is an invalid request, not a silently omitted decision.
    evaluate_combination(b,profile,scenario,mandatory,base)
    result=[]
    for bits in product((False,True),repeat=len(optional)):
        actions=mandatory|{k for k,yes in zip(optional,bits) if yes}
        try:result.append(evaluate_combination(b,profile,scenario,actions,base))
        except ValueError:continue
    if not result:raise ValueError('Uygun müdahale kombinasyonu yok; zorunlu kararları inceleyin.')
    return sorted(result,key=lambda p:(p.report.investment_try,p.report.candidate_id))


def selected_profile(b,profile,scenario,report):
    if b.interventions is None:
        from engine import calculate_package
        return calculate_package(b,profile,scenario,report.package)
    return evaluate_combination(b,profile,scenario,{d.kind for d in report.interventions})
