import {useEffect,useRef,useState} from 'react';
import {loadPilotStatus,installPilot} from './api';
import type {PilotStatus} from './spatialTypes';
import {errorMessage,money} from './format';

export default function PilotLoader({disabled,onOpen}:{disabled:boolean;onOpen:(id:string)=>Promise<void>}){
  const [data,setData]=useState<PilotStatus|null>(null),[error,setError]=useState(''),[busy,setBusy]=useState(false);
  const details=useRef<HTMLDetailsElement>(null);
  useEffect(()=>{let alive=true;loadPilotStatus().then(v=>{if(alive)setData(v)}).catch(e=>{if(alive)setError(errorMessage(e))});return()=>{alive=false}},[]);
  async function open(id:string){await onOpen(id);if(details.current)details.current.open=false;}
  async function load(){setBusy(true);setError('');try{const value=await installPilot();setData(value);await open(value.projects[0].id);}catch(e){setError(errorMessage(e));}finally{setBusy(false)}}
  return <section className="panel pilot-loader"><details ref={details}><summary>Kayseri sentetik pilotu · 4 bağımsız proje / 8 bina</summary><p className="pilot-title">Kayseri için hazırlanmış sentetik pilot senaryo — saha ölçümü değildir.</p><p>Mevcut proje ve hesaplar değiştirilmez. Yükleme yalnız aşağıdaki ayrı örnek projeleri ekler; tekrar yükleme düzenlediğiniz pilot kayıtlarını sıfırlamaz.</p>{error&&<p className="error-box" role="alert">{error}</p>}{data&&<div className="pilot-projects">{data.projects.map(p=><article key={p.id}><strong>{p.name}</strong><span>{p.building_count} bina · {p.connection_group_count} elektrik grubu</span><span>{money(p.budget_try)} · yalnız bu projenin bütçesi</span>{p.loaded&&<button className="text-button" disabled={disabled||busy} onClick={()=>void open(p.id)}>Projeyi aç →</button>}</article>)}</div>}<p className="small-note">Aynı 2025/+03:00 zaman ekseni ve sentetik hava senaryosu kullanılır. Konut bloklarının kazanları bağımsızdır; sıcak su müdahalesi modellenmez. Dört proje ortak trafoya veya ortak bütçeye bağlanmaz.</p><button className="button primary install-pilot" disabled={disabled||busy} onClick={()=>void load()}>{busy?'Yükleniyor…':'Ayrı pilot projelerini yükle ve aç'}</button></details></section>;
}
