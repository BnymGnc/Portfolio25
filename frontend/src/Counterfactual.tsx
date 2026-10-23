import {useEffect,useRef,useState} from 'react';
import type {CampusResponse} from './types';
import type {ScenarioEvaluation} from './aiTypes';
import {request,counterfactualScenario} from './api';
import {errorMessage,money,n} from './format';

export default function Counterfactual({data}:{data:CampusResponse}){
 const [building,setBuilding]=useState(data.campus.buildings[0]?.id??'');
 const [catalog,setCatalog]=useState<{id:string;label:string;status:string}[]>([]);
 useEffect(()=>{let alive=true;setCatalog([]);request('/api/buildings/'+building+'/catalog').then(r=>r.json()).then(v=>{if(alive){setCatalog(v);setKind(v.find((x:{status:string})=>x.status==='calculable')?.id??'')}}).catch(()=>{});return()=>{alive=false}},[building,data.context]);
 const [kind,setKind]=useState('heat_pump'),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [answer,setAnswer]=useState<{key:string;value:ScenarioEvaluation}|null>(null);
 const key=JSON.stringify([data.context,building,kind]);const latest=useRef(key);latest.current=key;
 async function run(){if(!data.context)return;const requested=key;setBusy(true);setError('');try{const value=await counterfactualScenario(data.context,building,kind);if(latest.current===requested)setAnswer({key:requested,value})}catch(e){if(latest.current===requested)setError(errorMessage(e))}finally{setBusy(false)}}
 const value=answer?.key===key?answer.value:null;
 return <details className="panel optional-ai counterfactual-panel"><summary>Bu müdahale seçilseydi?</summary><p>Aynı bütçe ve kapasite sınırlarıyla ayrı hesaplanır; ana plan ve girdiler değişmez. Fark, tek kesin seçim nedeni değildir; eşdeğer optimumlar olabilir.</p><div className="settings-fields"><label>Bina<select value={building} onChange={e=>setBuilding(e.target.value)}>{data.campus.buildings.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}</select></label><label>Zorunlu müdahale<select value={kind} onChange={e=>setKind(e.target.value)}>{catalog.filter(c=>c.status==='calculable').map(c=><option key={c.id} value={c.id}>{c.label}</option>)}</select></label></div><button className="button secondary" disabled={busy||!kind||!data.context?.calculation_id} onClick={()=>void run()}>{busy?'Hesaplanıyor…':'Alternatifi hesapla'}</button>{error&&<p role="alert">{error}</p>}{value&&<><p>{value.alternative.message}</p>{value.alternative.after&&value.baseline_plan?.after?<p>Ana plana göre yatırım farkı: {money((value.alternative.investment_try??0)-(value.baseline_plan.investment_try??0))}; yıllık enerji tasarrufu farkı: {n((value.alternative.energy_savings_kwh_year??0)-(value.baseline_plan.energy_savings_kwh_year??0))} kWh/yıl.</p>:<p>Uygun alternatif plan bulunamadı; fark hesaplanmadı. Bu durum tek başına hangi kısıtın belirleyici olduğunu kanıtlamaz.</p>}</>}</details>;
}
