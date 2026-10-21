import type { Campus, CampusResponse, CalculationResult, BuildingPackages, CampusProfiles, LastCalculation, ProjectSummary } from './types';
import type {PilotStatus,SpatialAnalysis,SpatialModel,SpatialSelection,SpatialPreview} from './spatialTypes';
import type {PackageName,InterventionDecision} from './types';
import type {CalculationContext} from './types';
import type {AIStatus,Explanation,ScenarioDraft,ScenarioChange,ScenarioEvaluation} from './aiTypes';
import type {ModelStatus,Prediction} from './ModelData';
import type {SyntheticStatus,SyntheticResult} from './SyntheticPrediction';

// Production always uses the Vercel same-origin /api rewrite, including auth.
export const API_BASE = import.meta.env.PROD ? '' : (import.meta.env.VITE_API_BASE_URL || '').replace(/\/$/, '');
let userScope='';let csrf='';let sessionGeneration=0;
export function setCSRF(value:string){csrf=value}
export function getCSRF(){return csrf}
export function getUserScope(){return userScope}
export function setUserScope(id:string){sessionGeneration++;userScope=id;activeProject=localStorage.getItem('portfolio25-project:'+id)||'campus-demo-25'}
let activeProject='campus-demo-25';
export function setActiveProject(id:string) {activeProject=id;localStorage.setItem('portfolio25-project:'+userScope,id);}
export function getActiveProject() {return activeProject;}
export async function modelStatus():Promise<ModelStatus>{return (await request('/api/ml/status')).json()}
export async function syntheticStatus():Promise<SyntheticStatus>{return (await request('/api/ml/synthetic/status')).json()}
export async function predictSynthetic(context:CalculationContext,building_id:string,candidate_id:string):Promise<SyntheticResult>{return (await request('/api/ml/synthetic/predict',jsonBody({context,building_id,candidate_id}),30000)).json()}
export async function predictModel(context:CalculationContext,features:Record<string,unknown>,country:string):Promise<Prediction>{return (await request('/api/ml/predict',jsonBody({context,features,country}),30000)).json()}
export async function predictProject(context:CalculationContext,building_id:string):Promise<Prediction>{return (await request('/api/ml/project-predict',jsonBody({context,building_id}),30000)).json()}
export async function counterfactualScenario(context:CalculationContext,building_id:string,intervention:string):Promise<ScenarioEvaluation>{return (await request('/api/scenarios/counterfactual',jsonBody({context,building_id,intervention}),60000)).json()}
const jsonBody=(body:unknown)=>({method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(body)});
export async function loadAIStatus():Promise<AIStatus>{return (await request('/api/ai/status')).json()}
export async function explainCalculation(context:CalculationContext,scope:'plan'|'building',building_id:string|undefined,question:string):Promise<Explanation>{return (await request('/api/ai/explain',jsonBody({context,scope,building_id,question}),35000)).json()}
export async function proposeScenario(context:CalculationContext,question:string):Promise<ScenarioDraft>{return (await request('/api/ai/scenario-draft',jsonBody({context,question}),35000)).json()}
export async function evaluateScenario(context:CalculationContext,changes:ScenarioChange[],mode:'A'|'B'):Promise<ScenarioEvaluation>{return (await request('/api/scenarios/evaluate',jsonBody({context,changes,mode,time_limit_s:5}),60000)).json()}
export async function applyScenario(context:CalculationContext,changes:ScenarioChange[],mode:'A'|'B'):Promise<CampusResponse>{return (await request('/api/scenarios/apply',jsonBody({context,changes,mode}))).json()}

export async function loadPilotStatus():Promise<PilotStatus>{return (await request('/api/examples/kayseri',{},30000)).json();}
export async function installPilot():Promise<PilotStatus>{return (await request('/api/examples/kayseri/load',{method:'POST'},30000)).json();}
export async function loadSpatial(id:string):Promise<SpatialAnalysis>{return (await request(`/api/buildings/${encodeURIComponent(id)}/spatial`,{},30000)).json();}
export async function previewSpatial(id:string,revision:number,selection:SpatialSelection,spatial:SpatialModel,packageName:PackageName,interventions:InterventionDecision[]|null):Promise<SpatialPreview>{return (await request(`/api/buildings/${encodeURIComponent(id)}/spatial/evaluate`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({revision,selection,spatial,package:packageName,interventions})},30000)).json();}

async function request(path: string, options: RequestInit = {}, timeout = 30000, projectId=activeProject) {
  const requestedGeneration=sessionGeneration;
  let response: Response;
  try {
    const divider=path.includes('?')?'&':'?';
    response = await fetch(`${API_BASE}${path}${divider}project_id=${encodeURIComponent(projectId)}`, { ...options, credentials:'include', headers:{...options.headers,...(options.method&&options.method!=='GET'?{'X-CSRF-Token':csrf}:{})}, signal: AbortSignal.timeout(timeout) });
  } catch {
    throw new Error(`API yanıtı alınamadı (${API_BASE||'/api'}). Bağlantı kesilmiş veya süre sınırı aşılmış olabilir; kayıt durumunu yenileyip tekrar deneyin.`);
  }
  if(requestedGeneration!==sessionGeneration)throw new Error('Oturum değişti; önceki oturuma ait yanıt uygulanmadı.');
  if (!response.ok) {
    if(response.status===401)window.dispatchEvent(new Event('portfolio25-session-expired'));
    const body = await response.json().catch(() => null);
    const labels: Record<string, string> = { area_m2: 'Bina alanı', year_built: 'Yapım yılı', electricity_kwh_year: 'Elektrik tüketimi', heating_kwh_year: 'Isıtma gazı', non_heating_gas_kwh_year: 'Diğer gaz', connection_limit_kw: 'Bina bağlantı sınırı', budget_try: 'Bütçe', savings_target_pct: 'Tasarruf hedefi', electric_capacity_kw: 'Ortak kapasite', source: 'Kaynak', reference_date: 'Varsayım tarihi', boiler_efficiency: 'Kazan verimi', heat_pump_scop: 'SCOP', time_limit_s: 'Süre sınırı' };
    const detail = typeof body?.detail === 'string' ? body.detail : Array.isArray(body?.detail) ? body.detail.map((e: {loc?: (string | number)[]}) => `${labels[String(e.loc?.at(-1))] ?? 'Girdi'}: değer veya biçim geçerli değil; formdaki sınırları kontrol edin.`).join(' · ') : 'Girilen değerleri kontrol edin.';
    throw new Error(`İşlem tamamlanamadı (${response.status}). ${detail}`);
  }
  if((path!=='/api/projects'||options.method==='POST')&&projectId!==activeProject)throw new Error('Proje değişti; geç gelen yanıt uygulanmadı.');
  return response;
}

export async function loadProjects():Promise<{projects:ProjectSummary[]}> {return (await request('/api/projects',{},30000,'campus-demo-25')).json();}
export async function createProject(name:string,building_ids:string[],connection_mode:'independent'|'shared') :Promise<Pick<ProjectSummary,'id'|'name'|'building_count'>> {
  return (await request('/api/projects',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({name,building_ids,connection_mode})})).json();
}

export async function loadPackages(id: string): Promise<BuildingPackages> {
  return (await request(`/api/buildings/${encodeURIComponent(id)}/packages`)).json();
}
export async function loadProfiles(calculationId?:string|null): Promise<CampusProfiles> {
  return (await request('/api/campus/profiles'+(calculationId?'?expected_calculation_id='+encodeURIComponent(calculationId):''))).json();
}
export async function loadLastCalculation(): Promise<LastCalculation> {
  return (await request('/api/calculations/last')).json();
}

export async function loadCampus(): Promise<CampusResponse> {
  return (await request('/api/campus/snapshot')).json();
}

export async function saveCampus(campus: Campus): Promise<CampusResponse> {
  return (await request('/api/campus', {
    method: 'PUT',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ revision: campus.revision, buildings: campus.buildings, scenario: campus.scenario, profile_settings: campus.profile_settings,
      name:campus.name,connection_groups:campus.connection_groups,sensitivity_settings:campus.sensitivity_settings }),
  })).json();
}

export async function calculateCampus(revision: number, mode: 'A' | 'B', time_limit_s: number): Promise<CalculationResult> {
  return (await request('/api/calculate', { method: 'POST', headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ revision, mode, time_limit_s }) }, Math.max(90000,2*time_limit_s*1000+30000))).json();
}

export async function downloadCampus(format: 'csv' | 'json', scope: 'inputs' | 'result', revision: number, calculationId?: string | null, mode?: 'A' | 'B') {
  const params = new URLSearchParams({scope, revision: String(revision)});
  if (calculationId) params.set('expected_calculation_id', calculationId);
  const blob = await (await request(`/api/export/${format}?${params}`)).blob();
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement('a');
  anchor.href = url;
  const prefix=activeProject==='campus-demo-25'?'portfolio25-grid':`portfolio25-grid-${activeProject}`;
  anchor.download = `${prefix}-${scope}-r${revision}${scope === 'result' && mode ? `-${mode}` : ''}.${format}`;
  document.body.append(anchor);
  anchor.click();
  anchor.remove();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
}
