"""Deterministic package physics and a binary MILP over precomputed hourly loads."""
from dataclasses import dataclass
from time import perf_counter

import numpy as np
from scipy.optimize import Bounds, LinearConstraint, milp
from scipy.sparse import csc_array

from models import (Baseline, Building, CalculationRequest, CalculationResult, Campus,
                    PackageName, PackageResult, Scenario, SolverInfo)
from profiles import AnnualProfiles, audit_profiles, generate_profiles
from models import CapacityCheck, ConnectionGroup
from eligibility import exclusion_reason
from spatial_models import InterventionDecision

PACKAGES: tuple[PackageName, ...] = ("none", "insulation", "heat_pump", "combined")


@dataclass
class PackageProfile:
    report: PackageResult
    timestamps: tuple[str, ...]
    electricity_kw: np.ndarray
    useful_heat_kw: np.ndarray
    heat_pump_heat_kw: np.ndarray
    backup_heat_kw: np.ndarray
    baseline: 'PackageProfile | None' = None


def payback(investment: float, net_savings: float) -> float | None:
    return investment / net_savings if net_savings > 0 else None


def calculate_package(b: Building, profile: AnnualProfiles, s: Scenario, package: PackageName, apply_spatial=True) -> PackageProfile:
    a = b.retrofit
    insulated = package in ("insulation", "combined")
    pump = package in ("heat_pump", "combined")
    # The explicitly related share alone receives the insulation reduction.
    electricity_base=profile.electricity_kw;heat_base=profile.useful_heat_kw;spatial_cost=0.;actions=[]
    if b.spatial and apply_spatial:
        from spatial_energy import transformed_inputs,validate_selection
        validate_selection(b,b.spatial_selection,package)
        electricity_base,heat_base,spatial_cost=transformed_inputs(b,profile)
        actions=[key for key in ('roof','lighting','schedule') if getattr(b.spatial_selection,key)]
    heat = heat_base * (1 - a.insulation_relevant_heat_fraction * a.insulation_reduction_fraction if insulated else 1)
    hp_heat = np.minimum(heat * a.heat_pump_coverage_fraction, a.heat_pump_capacity_kw_thermal) if pump else np.zeros_like(heat)
    # Constant seasonal-equivalent electrical allocation, NOT a temperature-based hourly COP.
    hp_electricity = hp_heat / a.heat_pump_scop
    backup = heat - hp_heat
    heating_gas = float(backup.sum()) / a.boiler_efficiency
    electricity = electricity_base + hp_electricity
    annual_electricity = float(electricity.sum()) if pump or (b.spatial and apply_spatial) else b.electricity_kwh_year
    if package == "none" and not actions:
        heating_gas = b.heating_kwh_year
    investment = (b.area_m2 * a.insulation_cost_try_m2 if insulated else 0) + (
        a.heat_pump_capacity_kw_thermal * a.heat_pump_cost_try_kw + a.heat_pump_fixed_cost_try if pump else 0)
    investment+=spatial_cost
    maintenance = investment * a.annual_maintenance_fraction
    before_energy = b.electricity_kwh_year + b.heating_kwh_year + b.non_heating_gas_kwh_year
    after_energy = annual_electricity + heating_gas + b.non_heating_gas_kwh_year
    before_cost = b.electricity_kwh_year * s.electricity_price_try_kwh + (b.heating_kwh_year + b.non_heating_gas_kwh_year) * s.heating_price_try_kwh
    after_cost = annual_electricity * s.electricity_price_try_kwh + (heating_gas + b.non_heating_gas_kwh_year) * s.heating_price_try_kwh + maintenance
    net = before_cost - after_cost
    report = PackageResult(
        candidate_id=package,
        interventions=[InterventionDecision(kind=k,state='mandatory' if k in actions else 'candidate') for k in ('roof','insulation','lighting','schedule','heat_pump') if k in set(actions)|({'insulation'} if insulated else set())|({'heat_pump'} if pump else set())],
        building_id=b.id, building_name=b.name, package=package, investment_try=investment,
        electricity_kwh_year=annual_electricity, heating_gas_kwh_year=heating_gas,
        non_heating_gas_kwh_year=b.non_heating_gas_kwh_year,
        useful_heat_before_kwh_year=float(profile.useful_heat_kw.sum()), useful_heat_after_kwh_year=float(heat.sum()),
        heat_pump_heat_kwh_year=float(hp_heat.sum()), heat_pump_electricity_kwh_year=float(hp_electricity.sum()),
        backup_boiler_heat_kwh_year=float(backup.sum()), energy_savings_kwh_year=before_energy - after_energy,
        net_savings_try_year=net, maintenance_cost_try_year=maintenance,
        electric_peak_kw=float(electricity.max()), connection_limit_kw=b.connection_limit_kw,
        simple_payback_years=payback(investment, net),
        spatial_investment_try=spatial_cost,spatial_interventions=actions,
    )
    return PackageProfile(report, profile.timestamps, electricity, heat, hp_heat, backup)


def groups_for(buildings, scenario, connection_groups=None):
    return connection_groups if connection_groups is not None else [ConnectionGroup(id='G01', name='Ortak besleme',
        building_ids=[b.id for b in buildings], capacity_kw=scenario.electric_capacity_kw)]


def capacity_checks(buildings, packages, scenario, connection_groups=None):
    loads = {b.id: p.electricity_kw for b, p in zip(buildings, packages, strict=True)}
    definitions = [('building', b.id, b.name, loads[b.id], b.connection_limit_kw) for b in buildings]
    definitions += [('group', g.id, g.name, np.sum([loads[i] for i in g.building_ids], axis=0), g.capacity_kw)
                    for g in groups_for(buildings, scenario, connection_groups)]
    return [CapacityCheck(kind=kind, id=id, name=name, peak_kw=float(load.max()),
        peak_timestamp=packages[0].timestamps[int(load.argmax())], limit_kw=limit,
        max_excess_kw=max(0.,float(load.max())-limit), violation_hours=int(np.count_nonzero(load > limit+1e-6)))
        for kind, id, name, load, limit in definitions]


def summarize(buildings: list[Building], packages: list[PackageProfile], scenario: Scenario, connection_groups=None) -> Baseline:
    if not packages or any(p.timestamps != packages[0].timestamps for p in packages):
        raise ValueError("Saatlik profiller aynı zaman damgalarını ve dönemi kullanmalıdır.")
    load = np.sum([p.electricity_kw for p in packages], axis=0)
    electricity = float(load.sum())
    heating = sum(p.report.heating_gas_kwh_year for p in packages)
    other_gas = sum(p.report.non_heating_gas_kwh_year for p in packages)
    maintenance = sum(p.report.maintenance_cost_try_year for p in packages)
    area = sum(b.area_m2 for b in buildings)
    peak = float(load.max())
    checks = capacity_checks(buildings, packages, scenario, connection_groups)
    energy_cost = electricity * scenario.electricity_price_try_kwh + (heating + other_gas) * scenario.heating_price_try_kwh
    return Baseline(
        area_m2=area, electricity_kwh_year=electricity, heating_kwh_year=heating,
        non_heating_gas_kwh_year=other_gas, total_gas_kwh_year=heating + other_gas,
        total_energy_kwh_year=electricity + heating + other_gas,
        intensity_kwh_m2_year=(electricity + heating + other_gas) / area,
        energy_cost_try_year=energy_cost, maintenance_cost_try_year=maintenance,
        operating_cost_try_year=energy_cost + maintenance,
        emissions_kg_year=electricity * scenario.electricity_emission_kg_kwh + (heating + other_gas) * scenario.gas_emission_kg_kwh,
        electric_peak_kw=peak, electric_peak_timestamp=packages[0].timestamps[int(load.argmax())],
        electric_peak_sum_kw=sum(p.report.electric_peak_kw for p in packages),
        capacity_utilization_pct=max(100 * c.peak_kw/c.limit_kw for c in checks if c.kind=='group'), capacity_checks=checks,
    )


def prepare(campus: Campus):
    profiles = [generate_profiles(b, campus.profile_settings) for b in campus.buildings]
    audit = audit_profiles(campus, profiles)
    if not audit.all_consistent:
        raise ValueError("Saatlik profillerin yıllık enerji kontrolü başarısız; hesaplama durduruldu.")
    from interventions import candidates
    packages=[candidates(b,p,campus.scenario) for b,p in zip(campus.buildings,profiles,strict=True)]
    return packages, audit


def finite_or_none(value):
    return float(value) if value is not None and np.isfinite(value) else None


def solve_packages(buildings: list[Building], options: list[list[PackageProfile]], scenario: Scenario,
                   request: CalculationRequest, connection_groups=None, enforce_grid=True) -> CalculationResult:
    """Accepts smaller examples as well as the eight-building API dataset."""
    started = perf_counter()
    baseline = summarize(buildings, [group[0].baseline or group[0] for group in options], scenario, connection_groups)
    flat = [p for group in options for p in group]
    count = len(flat)
    offsets = np.cumsum([0] + [len(group) for group in options])
    choice_rows = np.zeros((len(buildings), count))
    for i in range(len(buildings)):
        choice_rows[i, offsets[i]:offsets[i + 1]] = 1
    costs = np.array([p.report.investment_try for p in flat])
    savings = np.array([p.report.energy_savings_kwh_year for p in flat])
    # Every row is the campus load at one aligned hour; no sum of independent peaks.
    hourly_rows = np.column_stack([p.electricity_kw for p in flat])
    rows = [choice_rows, costs[None, :] / 1000]
    lower = [np.ones(len(buildings)), np.array([-np.inf])]
    upper = [np.ones(len(buildings)), np.array([scenario.budget_try / 1000])]
    if enforce_grid:
        for group in groups_for(buildings, scenario, connection_groups):
            mask = np.array([p.report.building_id in group.building_ids for p in flat])
            rows.append(hourly_rows * mask)
            lower.append(np.full(hourly_rows.shape[0], -np.inf))
            upper.append(np.full(hourly_rows.shape[0], group.capacity_kw))
    target_kwh = baseline.total_energy_kwh_year * scenario.savings_target_pct / 100
    if request.mode == "B":
        rows.append(savings[None, :] / 1000)
        lower.append(np.array([target_kwh / 1000]))
        upper.append(np.array([np.inf]))
    allowed = np.array([float(not enforce_grid or p.report.electric_peak_kw <= b.connection_limit_kw + 1e-9)
                        for b, group in zip(buildings, options, strict=True) for p in group])
    c = (-savings if request.mode == "A" else costs) / 1_000_000
    solve_start = perf_counter()
    solved = milp(c, integrality=np.ones(count), bounds=Bounds(np.zeros(count), allowed),
                  constraints=LinearConstraint(csc_array(np.vstack(rows)), np.concatenate(lower), np.concatenate(upper)),
                  options={"time_limit": request.time_limit_s, "mip_rel_gap": 0.0, "presolve": True})
    solve_seconds = perf_counter() - solve_start
    gap = finite_or_none(getattr(solved, "mip_gap", None))
    bound = finite_or_none(getattr(solved, "mip_dual_bound", None))
    if bound is not None:
        bound *= -1_000_000 if request.mode == "A" else 1_000_000
    info = SolverInfo(status_code=int(solved.status), message=str(solved.message), time_limit_s=request.time_limit_s,
                      solve_seconds=solve_seconds, total_seconds=perf_counter() - started, mip_gap=gap,
                      mip_node_count=getattr(solved, "mip_node_count", None), objective_bound=bound,
                      objective_unit="kWh/year" if request.mode == "A" else "TRY",
                      optimality_proven=False)
    warnings = [
        "Bütün saatlik yükler sentetiktir; kapasite sonucu ölçülmüş şebeke uygunluğu değildir.",
        "SCOP sabit mevsimsel eşdeğer olarak dağıtılır; sıcaklığa bağlı saatlik COP modeli kullanılmaz.",
        "Pompanın karşılamadığı ısı, kapasitesi sınırsız varsayılan mevcut doğalgaz kazanına aktarılır.",
        "Basit geri ödeme: yatırım / (enerji maliyeti tasarrufu − ek yıllık bakım); iskonto, ömür, vergi ve tarife değişimi içermez.",
    ]
    if any(c.violation_hours for c in baseline.capacity_checks):
        warnings.append("Mevcut durum kampüs besleme sınırını aşıyor; seçilecek planın da bütün saatlerde uygun olması zorunludur.")
    result = CalculationResult(input_revision=request.revision, mode=request.mode, status="failed",
                               message="Çözücü geçerli bir plan döndürmedi.", solver=info, baseline=baseline, warnings=warnings,
                               grid_constraints_applied=enforce_grid)
    if solved.status == 2:
        result.status = "infeasible"
        result.message = ("Tasarruf hedefine bütçe, bina bağlantı ve kampüs besleme sınırları içinde ulaşılamıyor."
                          if request.mode == "B" else "Bütçe, bina bağlantı ve kampüs besleme sınırları altında uygun plan bulunamadı.")
        return result
    if solved.status not in (0, 1) or solved.x is None:
        if solved.status == 1:
            result.status = "limit_no_solution"
            result.message = "Süre/arama sınırında uygun plan bulunamadı; bu durum hedefin imkânsız olduğunu kanıtlamaz."
        return result
    x = np.asarray(solved.x)
    if x.shape != (count,) or not np.all(np.isfinite(x)) or np.max(np.abs(x - np.rint(x))) > 1e-5:
        result.message = "Çözücünün tamsayılı aday planı doğrulanamadı."
        return result
    chosen = []
    for i, group in enumerate(options):
        picked = [p for p, value in zip(group, x[offsets[i]:offsets[i + 1]], strict=True) if value > 0.5]
        if len(picked) != 1:
            result.message = "Her bina için tam bir paket seçilmesi doğrulanamadı."
            return result
        chosen.append(picked[0])
    after = summarize(buildings, chosen, scenario, connection_groups)
    investment = sum(p.report.investment_try for p in chosen)
    saving = baseline.total_energy_kwh_year - after.total_energy_kwh_year
    # Independent post-checks use original units, not the solver's scaled rows.
    if (investment > scenario.budget_try + 0.01 or (enforce_grid and any(c.violation_hours for c in after.capacity_checks))
            or (request.mode == "B" and saving < target_kwh - 0.001)):
        result.message = "Aday plan bağımsız bütçe/kapasite/hedef kontrolünü geçemedi."
        return result
    proven = solved.status == 0 and (gap is None or gap <= 1e-8)
    result.status = "optimal" if proven else "feasible_limit"
    result.message = "Optimum çözücü tarafından kanıtlandı (sayısal toleranslar dahilinde)." if proven else "Uygun plan bulundu; optimum olduğu kanıtlanmadı."
    result.solver.optimality_proven = proven
    result.after = after
    result.selected_packages = [p.report for p in chosen]
    result.investment_try = investment
    result.energy_savings_kwh_year = saving
    result.energy_savings_pct = 100 * saving / baseline.total_energy_kwh_year if baseline.total_energy_kwh_year > 0 else None
    result.net_savings_try_year = baseline.operating_cost_try_year - after.operating_cost_try_year
    result.emissions_savings_kg_year = baseline.emissions_kg_year - after.emissions_kg_year
    result.simple_payback_years = payback(investment, result.net_savings_try_year)
    result.target_met = saving >= target_kwh - 0.001
    result.solver.total_seconds = perf_counter() - started
    return result


def calculate(campus: Campus, request: CalculationRequest) -> CalculationResult:
    start = perf_counter()
    packages, _ = prepare(campus)
    result = solve_packages(campus.buildings, packages, campus.scenario, request, campus.connection_groups)
    result.project_id = campus.id
    from evidence import decision_evidence, sensitivity
    result.decision_evidence = decision_evidence(campus, packages, request, result)
    result.sensitivity = sensitivity(campus, result)
    result.warnings.append('Isıtma paketleri yanında seçili kat aydınlatma/program etkileri hesaplanır. Sıcak su korunur; konfor ve genel konut modeli doğrulanmış değildir.')
    result.solver.total_seconds = perf_counter() - start
    from calculation_context import stamp
    return stamp(campus,result)
