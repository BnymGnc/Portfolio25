export type SourceKind='measured'|'user_estimate'|'default'|'synthetic'|'unspecified';
import type {SpatialModel,SpatialSelection} from './spatialTypes';
export interface Provenance {
  kind: 'measured' | 'external_simulation' | 'synthetic';
  source: string;
  seed: number | null;
}

export interface Building {
  field_sources?:Record<string,SourceKind>;
  interventions?:InterventionDecision[]|null;
  id: string;
  name: string;
  use_type: 'Eğitim' | 'Araştırma' | 'İdari' | 'Sosyal' | 'Konaklama' | 'Konut' | 'Ofis' | 'Otel';
  area_m2: number;
  year_built: number;
  electricity_kwh_year: number;
  heating_kwh_year: number;
  non_heating_gas_kwh_year: number;
  peak_electric_kw: number;
  connection_limit_kw: number;
  retrofit: RetrofitAssumptions;
  provenance: Provenance;
  heating_system: 'gas_boiler' | 'electric_resistance' | 'existing_heat_pump' | 'other';
  heat_distribution: 'hydronic_assumed' | 'low_temperature_water' | 'high_temperature_water' | 'none' | 'unknown';
  insulation_allowed: boolean;
  system_source: string;
  spatial: SpatialModel | null;
  spatial_selection: SpatialSelection;
}

export interface Reference {
  kind?:SourceKind;
  reference_date: string;
  source: string;
}

export interface RetrofitAssumptions extends Reference {
  boiler_efficiency: number;
  insulation_relevant_heat_fraction: number;
  insulation_reduction_fraction: number;
  heat_pump_scop: number;
  heat_pump_coverage_fraction: number;
  heat_pump_capacity_kw_thermal: number;
  insulation_cost_try_m2: number;
  heat_pump_cost_try_kw: number;
  heat_pump_fixed_cost_try: number;
  annual_maintenance_fraction: number;
}

export interface ProfileSettings {
  year: number;
  timezone: string;
  seed: number;
  kind: 'synthetic';
  source: string;
}

export interface Scenario {
  budget_try: number;
  savings_target_pct: number;
  electric_capacity_kw: number;
  electricity_price_try_kwh: number;
  heating_price_try_kwh: number;
  price_basis: Reference;
  electricity_emission_kg_kwh: number;
  gas_emission_kg_kwh: number;
  emission_basis: Reference;
}

export interface Campus {
  pilot?:{dataset:string;title:string;heating_independence:string;weather:Record<string,unknown>}|null;
  schema_version: '2.0' | '3.0';
  id: string;
  name: string;
  revision: number;
  provenance: Provenance;
  buildings: Building[];
  scenario: Scenario;
  optimization_status: 'ready';
  profile_settings: ProfileSettings;
  migration_notes: string[];
  connection_groups: ConnectionGroup[];
  sensitivity_settings: SensitivitySettings;
}

export interface ConnectionGroup { id: string; name: string; building_ids: string[]; capacity_kw: number; source: string }
export interface SensitivitySettings extends Reference { scop: {low:number;high:number}; investment: {low:number;high:number}; insulation: {low:number;high:number}; roof:{low:number;high:number} }
export interface CapacityCheck { kind:'building'|'group';id:string;name:string;peak_kw:number;peak_timestamp:string;limit_kw:number;max_excess_kw:number;violation_hours:number }
export interface ProjectSummary {id:string;name:string;building_count:number;project_type:'single_building'|'multi_building';revision:number}

export interface Baseline {
  area_m2: number;
  electricity_kwh_year: number;
  heating_kwh_year: number;
  non_heating_gas_kwh_year: number;
  total_gas_kwh_year: number;
  total_energy_kwh_year: number;
  intensity_kwh_m2_year: number;
  operating_cost_try_year: number;
  energy_cost_try_year: number;
  maintenance_cost_try_year: number;
  emissions_kg_year: number;
  electric_peak_kw: number;
  electric_peak_timestamp: string;
  electric_peak_sum_kw: number;
  capacity_utilization_pct: number;
  capacity_checks: CapacityCheck[];
}

export interface CampusResponse {
  baseline_packages?:PackageResult[];
  context?:CalculationContext;
  result_stale_reason?:string|null;
  calculation_id?: string | null;
  campus: Campus;
  baseline: Baseline;
  profile_audit: ProfileAudit;
  calculation: CalculationResult | null;
  after: Baseline | null;
  investment_plan: PackageResult[] | null;
}

export interface ProfileAudit {
  kind: 'synthetic'; source: string; timezone: string; start: string; end_exclusive: string;
  interval_hours: number; hour_count: number; all_consistent: boolean;
  buildings: { building_id: string; annual_electricity_kwh: number; integrated_electricity_kwh: number;
    electricity_error_kwh: number; annual_useful_heat_kwh: number; integrated_useful_heat_kwh: number;
    heat_error_kwh: number; electric_peak_kw: number; connection_limit_kw: number; consistent: boolean }[];
}

export type PackageName = 'none' | 'insulation' | 'heat_pump' | 'combined';
export interface PackageResult {
  candidate_id?:string|null;interventions?:InterventionDecision[];intervention_costs?:Record<string,number>;
  spatial_investment_try:number;spatial_interventions:string[];
  building_id: string; building_name: string; package: PackageName; investment_try: number;
  electricity_kwh_year: number; heating_gas_kwh_year: number; non_heating_gas_kwh_year: number;
  useful_heat_before_kwh_year: number; useful_heat_after_kwh_year: number;
  heat_pump_heat_kwh_year: number; heat_pump_electricity_kwh_year: number;
  backup_boiler_heat_kwh_year: number; unmet_heat_kwh_year: number; energy_savings_kwh_year: number;
  net_savings_try_year: number; maintenance_cost_try_year: number;
  electric_peak_kw: number; connection_limit_kw: number; simple_payback_years: number | null;
}

export interface CalculationResult {
  calculation_id?:string|null;input_hash?:string|null;engine_version?:string|null;model_version?:string|null;
  project_id: string;
  grid_constraints_applied: boolean;
  decision_evidence: {input_revision:number;project_id:string;mode:'A'|'B';ratio_definition:string;scope:string;methods:Record<'ratio'|'without_grid'|'grid',EvidenceMethod>} | null;
  sensitivity: {input_revision:number;project_id:string;fixed_plan:boolean;reoptimized:boolean;method:string;message?:string;settings:SensitivitySettings;rows:SensitivityRow[]} | null;
  input_revision: number; mode: 'A' | 'B';
  status: 'optimal' | 'feasible_limit' | 'limit_no_solution' | 'infeasible' | 'failed';
  message: string;
  solver: { name: string; status_code: number; message: string; time_limit_s: number;
    solve_seconds: number; total_seconds: number; mip_gap: number | null; mip_node_count: number | null;
    objective_bound: number | null; objective_unit: string; optimality_proven: boolean };
  baseline: Baseline; after: Baseline | null; selected_packages: PackageResult[];
  investment_try: number | null; energy_savings_kwh_year: number | null; energy_savings_pct: number | null;
  net_savings_try_year: number | null; emissions_savings_kg_year: number | null;
  simple_payback_years: number | null; target_met: boolean | null; warnings: string[];
}

export interface CampusProfiles {
  context?:CalculationContext;calculation_id?:string|null;
  project_id?:string;
  input_revision: number;
  result_input_revision: number | null;
  result_mode: 'A' | 'B' | null;
  kind: 'synthetic';
  source: string;
  timezone: string;
  interval_hours: number;
  timestamps: string[];
  before_kw: number[];
  after_kw: number[] | null;
  capacity_kw: number | null;
  groups?: {id:string;name:string;capacity_kw:number;before_kw:number[];after_kw:number[]|null}[];
}

export interface BuildingPackages {
  input_revision: number; building_id: string; kind: 'synthetic'; packages: PackageResult[];
  excluded_packages: {package:PackageName;reason:string}[];
  scope:'heating_only';
}

export interface PlanEvaluation {after:Baseline;investment_try:number;budget_remaining_try:number;budget_met:boolean;energy_savings_kwh_year:number;energy_savings_pct:number|null;net_savings_try_year:number;target_met:boolean;capacity_met:boolean;capacity_violations:CapacityCheck[];selected_packages:PackageResult[]}
export interface EvidenceMethod {status:string;message:string;solver:CalculationResult['solver']|null;evaluation:PlanEvaluation|null}
export interface SensitivityRow {parameter:'scop'|'investment'|'insulation'|'roof';level:'low'|'base'|'high';multiplier:number;status:'evaluated'|'invalid_assumptions';message?:string;evaluation:PlanEvaluation|null;effective_assumptions?:Record<string,Record<string,number>>}

export interface LastCalculation {
  context?:CalculationContext;stale_reason?:string|null;
  calculation_id?: string | null;
  current_revision: number; is_current: boolean; calculation: CalculationResult | null;
}
export interface CalculationContext {project_id:string;input_revision:number;input_hash:string;engine_version:string;calculation_id:string|null;model_version:string|null}
export interface InterventionDecision {kind:'roof'|'insulation'|'lighting'|'schedule'|'heat_pump';state:'candidate'|'mandatory'|'applied'|'excluded'}
