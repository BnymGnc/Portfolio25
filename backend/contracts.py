"""Typed public responses; engine objects remain backward compatible internally."""
from typing import Literal
from pydantic import Field
from models import Model,Baseline,PackageResult,CalculationResult,CampusResponse,SolverInfo,SensitivitySettings,CapacityCheck
from spatial_models import SpatialModel,SpatialSelection


class StorageStatus(Model):
    status:Literal['local','postgresql','unavailable','persistent_disk','ephemeral','unverified']
    required:bool
    message:str


class SessionUser(Model):
    id:str
    email:str
    onboarding_version:int


class AuthSession(Model):
    user:SessionUser|None
    csrf:str
    onboarding_version:int
    storage:StorageStatus


class Health(Model):
    status:Literal['ok','degraded']
    version:str
    optimization_status:Literal['not_checked']
    data_status:Literal['not_checked']
    storage:StorageStatus
    release_commit:str|None=None
    boot_id:str|None=None


class Context(Model):
    project_id:str
    input_revision:int
    input_hash:str
    engine_version:str
    calculation_id:str|None=None
    model_version:str|None=None


class PlanEvaluation(Model):
    after:Baseline
    investment_try:float
    budget_remaining_try:float
    budget_met:bool
    energy_savings_kwh_year:float
    energy_savings_pct:float|None
    net_savings_try_year:float
    target_met:bool
    capacity_met:bool
    capacity_violations:list[CapacityCheck]
    selected_packages:list[PackageResult]


class EvidenceMethod(Model):
    status:str
    message:str
    solver:SolverInfo|None
    evaluation:PlanEvaluation|None


class EvidenceMethods(Model):
    ratio:EvidenceMethod
    without_grid:EvidenceMethod
    grid:EvidenceMethod


class Evidence(Model):
    input_revision:int
    project_id:str
    mode:Literal['A','B']
    context:Context|None=None
    package_universe:dict[str,list[str]]
    ratio_definition:str
    scope:str
    methods:EvidenceMethods


class SensitivityRow(Model):
    parameter:Literal['scop','investment','insulation','roof']
    level:Literal['low','base','high']
    multiplier:float
    status:Literal['evaluated','invalid_assumptions']
    evaluation:PlanEvaluation|None
    message:str|None=None
    effective_assumptions:dict[str,dict[str,float]]|None=None


class Sensitivity(Model):
    input_revision:int
    project_id:str
    context:Context|None=None
    fixed_plan:bool
    reoptimized:bool
    method:str
    settings:SensitivitySettings
    rows:list[SensitivityRow]
    message:str|None=None


class Result(CalculationResult):
    decision_evidence:Evidence|None=None
    sensitivity:Sensitivity|None=None


class Snapshot(CampusResponse):
    context:Context
    calculation:Result|None=None


class LastResult(Model):
    current_revision:int
    is_current:bool
    calculation:Result|None
    calculation_id:str|None
    context:Context
    stale_reason:str|None


class GroupProfile(Model):
    id:str
    name:str
    capacity_kw:float
    before_kw:list[float]
    after_kw:list[float]|None


class ProjectProfiles(Model):
    context:Context
    calculation_id:str|None
    project_id:str
    input_revision:int
    result_input_revision:int|None
    result_mode:Literal['A','B']|None
    kind:Literal['synthetic']
    source:str
    timezone:str
    interval_hours:float
    timestamps:list[str]
    before_kw:list[float]
    after_kw:list[float]|None
    capacity_kw:float|None
    groups:list[GroupProfile]


class BuildingProfiles(Model):
    context:Context
    input_revision:int
    building_id:str
    package:str
    kind:Literal['synthetic']
    source:str
    timezone:str
    interval_hours:float
    timestamps:list[str]
    baseline_electricity_kw:list[float]
    electricity_kw:list[float]
    useful_heat_before_kw:list[float]
    useful_heat_after_kw:list[float]
    heat_pump_heat_kw:list[float]
    backup_boiler_heat_kw:list[float]
    summary:PackageResult


class ExcludedPackage(Model):
    package:str
    reason:str


class BuildingPackages(Model):
    context:Context
    input_revision:int
    building_id:str
    kind:Literal['synthetic']
    scope:str
    excluded_packages:list[ExcludedPackage]
    packages:list[PackageResult]


class EnergyTotals(Model):
    electricity_kwh_year:float
    fuel_kwh_year:float
    useful_heat_kwh_year:float


class AllocationRow(EnergyTotals):
    id:str
    name:str
    area_m2:float
    components:dict[str,float]


class ZoneRow(EnergyTotals):
    zone_id:str
    name:str
    floor_id:str
    floor_name:str
    use:str
    area_m2:float
    hp_heat_kwh_year:float
    components:dict[str,float]
    common_area:bool
    kind:Literal['modelled_allocation','assumption']
    source:str


class Allocation(Model):
    totals:EnergyTotals
    by_floor:list[AllocationRow]
    by_use:list[AllocationRow]
    zones:list[ZoneRow]
    reconciliation:dict[str,float]
    method:str
    residual_electricity_kwh_year:float
    comfort_modelled:Literal[False]


class AffectedZone(Model):
    floor_id:str
    zone_id:str
    name:str


class Effect(Model):
    electricity_savings_kwh_year:float
    fuel_savings_kwh_year:float
    investment_try:float
    net_savings_try_year:float
    energy_cost_savings_try_year:float
    capacity_met:bool
    building_peak_change_kw:float


class Recommendation(Model):
    id:str
    title:str
    status:Literal['calculated','calculated_review_required','review_only']
    finding:str
    affected:list[AffectedZone]
    effect:Effect|None
    conditions:str
    missing_information:list[str]


class SpatialAnalysis(Model):
    context:Context
    available:bool
    project_id:str
    input_revision:int
    building_id:str
    message:str|None=None
    spatial:SpatialModel|None=None
    selection:SpatialSelection|None=None
    baseline:Allocation|None=None
    recommendations:list[Recommendation]=Field(default_factory=list)
    weather:dict|None=None
    source:str|None=None


class SpatialPreview(Model):
    context:Context
    project_id:str
    input_revision:int
    building_id:str
    selection:SpatialSelection
    package:str
    before:PackageResult
    after:PackageResult
    electricity_savings_kwh_year:float
    fuel_savings_kwh_year:float
    investment_try:float
    energy_cost_savings_try_year:float
    net_savings_try_year:float
    simple_payback_years:float|None
    budget_met:bool
    capacity_checks:list[CapacityCheck]
    baseline_capacity_checks:list[CapacityCheck]
    capacity_met:bool
    capacity_context:str
    allocation_before:Allocation
    allocation_after:Allocation
    comfort_modelled:Literal[False]
    review_required:bool
    warnings:list[str]
