import {useEffect,useRef,useState} from 'react';
import type {CalculationContext} from './types';
import type {AIStatus,Explanation,Fact} from './aiTypes';
import {loadAIStatus,explainCalculation} from './api';
import {n} from './format';
import {aiErrorMessage} from './aiPresentation';

export function ContextLabel({context}:{context:CalculationContext}){return <details className="small-note"><summary>Teknik hesap bağlamı</summary><p>Proje {context.project_id} · r{context.input_revision} · motor {context.engine_version} · hesap {context.calculation_id?.slice(0,10)??'henüz yok'}</p></details>}
function Value({fact}:{fact:Fact}){return <dl className="ai-fact"><dt>{fact.label}</dt><dd>{typeof fact.value==='number'?n(fact.value,2):typeof fact.value==='boolean'?fact.value?'Evet':'Hayır':fact.value} {fact.unit}</dd></dl>}

export default function AIAssistant({context,scope,buildingId,disabled=false,onCalculate}:{context?:CalculationContext;scope:'plan'|'building';buildingId?:string;disabled?:boolean;onCalculate?:()=>void}){
 const [status,setStatus]=useState<AIStatus|null>(null),[answer,setAnswer]=useState<Explanation|null>(null),[question,setQuestion]=useState(''),[busy,setBusy]=useState(false),[error,setError]=useState('');
 const [answeredQuestion,setAnsweredQuestion]=useState('');
 const signature=JSON.stringify([context,buildingId,scope,question]);const latest=useRef(signature);latest.current=signature;
 useEffect(()=>{setBusy(false)},[signature]);
 useEffect(()=>{let alive=true;loadAIStatus().then(s=>{if(alive)setStatus(s)}).catch(()=>{});return()=>{alive=false}},[context?.project_id]);
 const needsPlan=scope==='plan'&&!context?.calculation_id;
 const current=!disabled&&answer&&answeredQuestion===question&&answer.scope===scope&&(answer.building_id??undefined)===buildingId&&JSON.stringify(answer.context)===JSON.stringify(context);
 const prompts=scope==='building'?['Bu binada hangi müdahaleleri değerlendirebilirim?','Karar vermeden önce hangi veriler eksik?','Isı pompası seçeneğinde nelere dikkat etmeliyim?']:['Seçilen yatırımlarda önce neyi incelemeliyim?','Bu planın en önemli varsayımları neler?','Hangi verileri sahada doğrulamalıyım?'];
 async function explain(){if(!context)return;const requested=signature;setBusy(true);setError('');try{const value=await explainCalculation(context,scope,buildingId,question.trim()||prompts[0]);if(latest.current===requested){if([...value.findings,...value.details].some(f=>!value.facts.some(v=>v.id===f.fact_id)))throw new Error('Açıklamanın kaynak alanı doğrulanamadı.');setAnswer(value);setAnsweredQuestion(question)}}catch(e){if(latest.current===requested)setError(aiErrorMessage(e))}finally{if(latest.current===requested)setBusy(false)}}
 return <section className="ai-panel ai-workflow">
 <p className="ai-intro">{scope==='plan'?'Yatırım kararınızı inceleyin. Asistan seçilen paketleri, maliyetleri ve dikkat edilmesi gereken varsayımları hesabınıza göre açıklar.':'Bu binanın uygun yatırım seçeneklerini ve karar için eksik bilgileri inceleyin.'}</p>
 {needsPlan?<div className="ai-empty"><h3>Önce bir yatırım planı oluşturun</h3><p>Asistanın yorumlayabilmesi için güncel bir hesap gerekli.</p>{onCalculate&&<button className="button primary" onClick={onCalculate}>Planımı oluştur</button>}</div>:<>
 {disabled&&<p className="stale-notice">Girdiler değişti. Güncel bir açıklama için kaydedip yeniden hesaplayın.</p>}
 <div className="prompt-choices">{prompts.map(text=><button className={`prompt-choice ${question===text?'selected':''}`} key={text} disabled={busy||disabled} onClick={()=>{setQuestion(text);setError('')}}>{text}</button>)}</div>
 <form onSubmit={e=>{e.preventDefault();void explain()}}><label>Sorunuz<textarea maxLength={1000} disabled={busy||disabled} placeholder={prompts[0]} value={question} onChange={e=>setQuestion(e.target.value)}/></label><button className="button primary explain-button" disabled={!context||status?.configured===false||disabled||busy}>{busy?'Yanıt hazırlanıyor…':'Asistana sor'}</button></form>
 {status?.configured===false&&<p className="ai-unavailable" role="status">AI asistanı şu anda kullanılamıyor. Yatırım seçeneklerini ve hesaplanan sonuçları incelemeye devam edebilirsiniz.</p>}
 {error&&<p className="error-box" role="alert">{error}</p>}
 {answer&&!current&&<p className="stale-notice">{answeredQuestion!==question?'Bu yanıt önceki soruya aittir. Yeni sorunuz için tekrar gönderin.':'Kaynak hesap değişti; yanıt güncel değil.'}</p>}
 {current&&answer&&<div className="ai-answer" aria-live="polite"><h3>Karar için öne çıkanlar</h3><ol>{answer.findings.map((finding,i)=><li key={i}><p>{finding.text}</p><Value fact={answer.facts.find(f=>f.id===finding.fact_id)!}/></li>)}</ol>{(answer.details.length>0||answer.limitations.length>0)&&<details><summary>Ayrıntılar ve dikkat edilecekler</summary>{answer.details.map((finding,i)=><div key={i}><p>{finding.text}</p><Value fact={answer.facts.find(f=>f.id===finding.fact_id)!}/></div>)}<ul>{answer.limitations.map(l=><li key={l}>{l}</li>)}</ul></details>}</div>}
 <p className="ai-privacy">Sorunuz ve bu projeye ait hesap özetleri AI hizmetine gönderilir. Sayısal değerler hesap motorundan alınır.</p>
 </>}
 </section>
}
