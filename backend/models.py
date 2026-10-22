from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator
from spatial_models import SpatialModel, SpatialSelection,InterventionDecision


class Model(BaseModel):
    model_config = ConfigDict(extra="forbid", allow_inf_nan=False)


class Provenance(Model):
    kind: Literal["measured", "external_simulation", "synthetic"]
    source: str = Field(min_length=1, max_length=500)
    seed: int | None = None


SourceKind = Literal["measured", "user_estimate", "default", "synthetic", "unspecified"]


class Reference(Model):
    kind: SourceKind = "unspecified"
    reference_date: date = date(2026, 10, 19)
    source: str = Field(default="Düzenlenebilir sentetik örnek varsayımı; resmî güncel değer değildir.", min_length=1, max_length=500)


class RetrofitAssumptions(Reference):
    boiler_efficiency: float = Field(default=0.9, gt=0, le=1)
    insulation_relevant_heat_fraction: float = Field(default=0.9, ge=0, le=1)
    insulation_reduction_fraction: float = Field(default=0.3, ge=0, le=1)
    heat_pump_scop: float = Field(default=3.2, ge=1, le=10)
    heat_pump_coverage_fraction: float = Field(default=0.9, ge=0, le=1)
    heat_pump_capacity_kw_thermal: float = Field(default=200, ge=0, le=1_000_000)
    insulation_cost_try_m2: float = Field(default=350, ge=0, le=100_000)
    heat_pump_cost_try_kw: float = Field(default=5000, ge=0, le=1_000_000)
    heat_pump_fixed_cost_try: float = Field(default=100_000, ge=0, le=1_000_000_000)
    annual_maintenance_fraction: float = Field(default=0.015, ge=0, le=1)


class ProfileSettings(Model):
    year: int = Field(default=2025, ge=2020, le=2100)
    timezone: Literal["Europe/Istanbul"] = "Europe/Istanbul"
    seed: int = Field(default=25, ge=0, le=2**32 - 1)
    kind: Literal["synthetic"] = "synthetic"
    source: str = "Yıllık enerjiye normalize edilen sentetik profil v1; ölçülmüş yük veya hava verisi değildir."


class Building(Model):
    field_sources: dict[str, SourceKind] = Field(default_factory=dict, max_length=30)
    interventions:list[InterventionDecision]|None=None
    id: str = Field(pattern=r"^B[0-9]{2}$")
    name: str = Field(min_length=1, max_length=100, pattern=r"\S")
    use_type: Literal["Eğitim", "Araştırma", "İdari", "Sosyal", "Konaklama", 'Konut', 'Ofis', 'Otel']
    area_m2: float = Field(gt=0, le=1_000_000)
    year_built: int = Field(ge=1800, le=2100)
    electricity_kwh_year: float = Field(ge=0, le=1_000_000_000)
    heating_kwh_year: float = Field(ge=0, le=1_000_000_000)
    non_heating_gas_kwh_year: float = Field(default=0, ge=0, le=1_000_000_000)
    peak_electric_kw: float = Field(ge=0, le=1_000_000)
    connection_limit_kw: float = Field(default=500, gt=0, le=1_000_000)
    retrofit: RetrofitAssumptions = Field(default_factory=RetrofitAssumptions)
    provenance: Provenance
    heating_system: Literal['gas_boiler', 'electric_resistance', 'existing_heat_pump', 'other'] = 'gas_boiler'
    heat_distribution: Literal['hydronic_assumed', 'low_temperature_water', 'high_temperature_water', 'none', 'unknown'] = 'hydronic_assumed'
    insulation_allowed: bool = True
    system_source: str = Field(default='Sentetik varsayım: gaz kazanı ve ısı pompasına uygun sulu dağıtım; yerinde doğrulanmadı.', min_length=1, max_length=500)
    spatial: SpatialModel | None = None
    spatial_selection: SpatialSelection = Field(default_factory=SpatialSelection)

    @model_validator(mode='after')
    def spatial_consistency(self):
        if self.interventions is not None and len({d.kind for d in self.interventions})!=len(self.interventions):
            raise ValueError('Her müdahale için tek karar durumu olmalı.')
        if self.spatial:
            if abs(sum(f.area_m2 for f in self.spatial.floors)-self.area_m2)>1e-6:
                raise ValueError('Kat alanları bina alanıyla uzlaşmalı.')
            if self.spatial.dhw_gas_kwh_year>self.non_heating_gas_kwh_year:
                raise ValueError('Sıcak su gazı, ısıtma dışı gazın içinde olmalı; ek enerji değildir.')
        elif any((self.spatial_selection.roof,self.spatial_selection.lighting,self.spatial_selection.schedule)):
            raise ValueError('Kat modeli olmayan binaya kat müdahalesi kaydedilemez.')
        return self


class ConnectionGroup(Model):
    id: str = Field(pattern=r'^G[0-9]{2}$')
    name: str = Field(min_length=1, max_length=100, pattern=r'\S')
    building_ids: list[str] = Field(min_length=1, max_length=50)
    capacity_kw: float = Field(gt=0, le=10_000_000)
    source: str = Field(default='Düzenlenebilir sentetik bağlantı varsayımı; gerçek sözleşme doğrulanmadı.', min_length=1, max_length=500)


class SensitivityBand(Model):
    low: float = Field(default=.8, ge=.1, le=3)
    high: float = Field(default=1.2, ge=.1, le=3)

    @model_validator(mode='after')
    def ordered(self):
        if not self.low <= 1 <= self.high:
            raise ValueError('Düşük çarpan ≤ 1 ≤ yüksek çarpan olmalıdır; temel her zaman 1.')
        return self


class SensitivitySettings(Reference):
    roof:SensitivityBand=Field(default_factory=lambda:SensitivityBand(low=.8,high=1.2))
    scop: SensitivityBand = Field(default_factory=lambda: SensitivityBand(low=.85, high=1.15))
    investment: SensitivityBand = Field(default_factory=SensitivityBand)
    insulation: SensitivityBand = Field(default_factory=lambda: SensitivityBand(low=.75, high=1.25))


class Scenario(Model):
    budget_try: float = Field(ge=0, le=1_000_000_000_000)
    savings_target_pct: float = Field(ge=0, le=100)
    electric_capacity_kw: float = Field(gt=0, le=10_000_000)
    electricity_price_try_kwh: float = Field(ge=0, le=1_000)
    heating_price_try_kwh: float = Field(ge=0, le=1_000)
    price_basis: Reference = Field(default_factory=Reference)
    electricity_emission_kg_kwh: float = Field(default=0.4, ge=0, le=10)
    gas_emission_kg_kwh: float = Field(default=0.2, ge=0, le=10)
    emission_basis: Reference = Field(default_factory=Reference)


class CampusUpdate(Model):
    revision: int = Field(ge=1)
    buildings: list[Building] = Field(min_length=1, max_length=50)
    scenario: Scenario
    profile_settings: ProfileSettings = Field(default_factory=ProfileSettings)
    connection_groups: list[ConnectionGroup] | None = None
    sensitivity_settings: SensitivitySettings = Field(default_factory=SensitivitySettings)
    name: str = Field(default='Örnek Kampüs', min_length=1, max_length=100, pattern=r'\S')

    @model_validator(mode="after")
    def validate_buildings(self):
        if len({b.id for b in self.buildings}) != len(self.buildings):
            raise ValueError('Bina kimlikleri benzersiz olmalıdır.')
        for building in self.buildings:
            if building.provenance.kind != "synthetic" or building.provenance.seed != 25:
                raise ValueError("Örnek kampüsün sentetik veri kaynağı korunmalıdır.")
        if self.connection_groups is not None:
            ids = [g.id for g in self.connection_groups]
            members = [b for g in self.connection_groups for b in g.building_ids]
            if len(set(ids)) != len(ids) or len(set(members)) != len(members) or set(members) != {b.id for b in self.buildings}:
                raise ValueError('Her bina tam bir bağlantı grubunda olmalı; gruplar boş, yinelenen veya bilinmeyen üyeli olamaz.')
        return self


class Campus(CampusUpdate):
    schema_version: Literal['3.0'] = '3.0'
    id: str = Field(default='campus-demo-25', pattern=r'^(campus-demo-25|project-[a-f0-9]{12})$')
    name: str = "Örnek Kampüs"
    provenance: Provenance
    optimization_status: Literal["ready"] = "ready"
    migration_notes: list[str] = Field(default_factory=list)
    pilot: dict | None = None

    @model_validator(mode='after')
    def default_connections(self):
        if self.connection_groups is None:
            self.connection_groups = [ConnectionGroup(id='G01', name='Örnek kampüs ortak beslemesi',
                building_ids=[b.id for b in self.buildings], capacity_kw=self.scenario.electric_capacity_kw)]
        for b in self.buildings:
            if b.spatial:
                from spatial_energy import validate_inputs
                validate_inputs(b,self.profile_settings.year)
        return self


class ProjectCreate(Model):
    name: str = Field(min_length=1, max_length=100, pattern=r'\S')
    building_ids: list[str] = Field(min_length=1, max_length=50)
    connection_mode: Literal['independent', 'shared'] = 'independent'


class CapacityCheck(Model):
    kind: Literal['building', 'group']
    id: str
    name: str
    peak_kw: float
    peak_timestamp: str
    limit_kw: float
    max_excess_kw: float
    violation_hours: int


class Baseline(Model):
    area_m2: float
    electricity_kwh_year: float
    heating_kwh_year: float
    non_heating_gas_kwh_year: float
    total_gas_kwh_year: float
    total_energy_kwh_year: float
    intensity_kwh_m2_year: float
    operating_cost_try_year: float
    energy_cost_try_year: float
    maintenance_cost_try_year: float
    emissions_kg_year: float
    electric_peak_kw: float
    electric_peak_timestamp: str
    electric_peak_sum_kw: float
    capacity_utilization_pct: float
    capacity_checks: list[CapacityCheck] = Field(default_factory=list)


class ProfileAuditRow(Model):
    building_id: str
    annual_electricity_kwh: float
    integrated_electricity_kwh: float
    electricity_error_kwh: float
    annual_useful_heat_kwh: float
    integrated_useful_heat_kwh: float
    heat_error_kwh: float
    electric_peak_kw: float
    connection_limit_kw: float
    consistent: bool


class ProfileAudit(Model):
    kind: Literal["synthetic"] = "synthetic"
    source: str
    timezone: str
    start: str
    end_exclusive: str
    interval_hours: float = 1
    hour_count: int
    all_consistent: bool
    buildings: list[ProfileAuditRow]


PackageName = Literal["none", "insulation", "heat_pump", "combined"]


class PackageResult(Model):
    candidate_id:str|None=None
    interventions:list[InterventionDecision]=Field(default_factory=list)
    intervention_costs:dict[str,float]=Field(default_factory=dict)
    building_id: str
    building_name: str
    package: PackageName
    investment_try: float
    electricity_kwh_year: float
    heating_gas_kwh_year: float
    non_heating_gas_kwh_year: float
    useful_heat_before_kwh_year: float
    useful_heat_after_kwh_year: float
    heat_pump_heat_kwh_year: float
    heat_pump_electricity_kwh_year: float
    backup_boiler_heat_kwh_year: float
    unmet_heat_kwh_year: float = 0
    energy_savings_kwh_year: float
    net_savings_try_year: float
    maintenance_cost_try_year: float
    electric_peak_kw: float
    connection_limit_kw: float
    simple_payback_years: float | None
    spatial_investment_try: float = 0
    spatial_interventions: list[str] = Field(default_factory=list)


class SolverInfo(Model):
    name: str = "scipy.optimize.milp / HiGHS"
    status_code: int
    message: str
    time_limit_s: float
    solve_seconds: float
    total_seconds: float
    mip_gap: float | None
    mip_node_count: int | None
    objective_bound: float | None
    objective_unit: str
    optimality_proven: bool


class CalculationRequest(Model):
    revision: int = Field(ge=1)
    mode: Literal["A", "B"] = "A"
    time_limit_s: float = Field(default=10, ge=0.01, le=60)


class CalculationResult(Model):
    calculation_id: str | None = None
    input_hash: str | None = None
    engine_version: str | None = None
    model_version: str | None = None
    project_id: str = 'campus-demo-25'
    input_revision: int
    mode: Literal["A", "B"]
    status: Literal["optimal", "feasible_limit", "limit_no_solution", "infeasible", "failed"]
    message: str
    solver: SolverInfo
    baseline: Baseline
    after: Baseline | None = None
    selected_packages: list[PackageResult] = Field(default_factory=list)
    investment_try: float | None = None
    energy_savings_kwh_year: float | None = None
    energy_savings_pct: float | None = None
    net_savings_try_year: float | None = None
    emissions_savings_kg_year: float | None = None
    simple_payback_years: float | None = None
    target_met: bool | None = None
    warnings: list[str] = Field(default_factory=list)
    grid_constraints_applied: bool = True
    decision_evidence: dict | None = None
    sensitivity: dict | None = None


class CampusResponse(Model):
    baseline_packages:list[PackageResult]=Field(default_factory=list)
    calculation_id: str | None = None
    result_stale_reason: str | None = None
    context: dict | None = None
    campus: Campus
    baseline: Baseline
    profile_audit: ProfileAudit
    calculation: CalculationResult | None = None
    after: Baseline | None = None
    investment_plan: list[PackageResult] | None = None
