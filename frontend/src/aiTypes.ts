import type {CalculationContext,CalculationResult} from './types';
export interface AIStatus{last_call_status:string;last_success_at:number|null;service_reachable:boolean|null;configured:boolean;model:string;prompt_version:string;rag:false}
export interface Fact{id:string;label:string;value:number|string|boolean;unit:string;source_path:string}
export interface Explanation{scope:"plan"|"building";building_id?:string|null;context:CalculationContext;model:string;prompt_version:string;cached:boolean;findings:{fact_id:string;text:string}[];details:{fact_id:string;text:string}[];facts:Fact[];limitations:string[]}
export interface ScenarioChange{field:'budget_try'|'savings_target_pct'|'electricity_price_try_kwh'|'heating_price_try_kwh'|'intervention';value:number|'candidate'|'mandatory'|'excluded';building_id?:string|null;intervention?:string|null}
export interface ScenarioDraft{clarification?:string|null;context:CalculationContext;model:string;prompt_version:string;changes:ScenarioChange[];explanation:string;cached:boolean}
export interface ScenarioEvaluation{base_context:CalculationContext;transient:true;persisted:false;changes:ScenarioChange[];baseline_plan:CalculationResult|null;alternative:CalculationResult;forced_intervention?:{kind:string;state:string}|null;building_id?:string}
