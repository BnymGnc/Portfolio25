import {Component,useEffect,useState,type ReactNode} from 'react';
import App from './App';
import {API_BASE,setUserScope,loadProjects,setActiveProject,getActiveProject,setCSRF,getCSRF} from './api';
import {applyTheme,readTheme,type Theme} from './theme';

type User={id:string;email:string;onboarding_version:number};
export async function authRequest(path:string,body?:unknown){

 const response=await fetch(API_BASE+'/api/auth/'+path,{credentials:'include',method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(body===undefined?{}:{'X-CSRF-Token':getCSRF()})},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
 const value=await response.json();if(!response.ok)throw new Error(value.detail??'Oturum işlemi tamamlanamadı.');
 if(value.csrf)setCSRF(value.csrf);return value;
}

export class PanelBoundary extends Component<{children:ReactNode},{failed:boolean}>{
 state={failed:false};static getDerivedStateFromError(){return {failed:true}}
 render(){return this.state.failed?<section className="panel"><p role="alert">Bu bölüm gösterilemedi. Kayıtlarınız korunur.</p><button className="button secondary" onClick={()=>this.setState({failed:false})}>Bölümü yeniden dene</button></section>:this.props.children}
}

const steps=[
 ['Yatırım kararını hesaplarla inceleyin','Portfolio25-GRID bütçe, enerji ve elektrik bağlantı sınırlarını birlikte değerlendirir. Sonuçlar girilen fiziksel varsayımlara dayanır.'],
 ['Size ait sentetik pilot','Dört bağımsız proje ve sekiz bina hesabınıza kopyalanır. Kampüs, konut sitesi, ofis ve otelin bütçe ve bağlantıları birbirinden ayrıdır. Saha ölçümü değildir.'],
 ['İnceleyin, hesaplayın, karşılaştırın','Proje ve binayı seçin. Varsayımları gözden geçirin, girdileri kaydedin ve yatırım planını hesaplayın. Değişen girdiler önceki sonucu güncel olmaktan çıkarır.'],
 ['Fizik, ML ve LLM farklı işler yapar','Yatırım ve kapasite kararını fizik/MILP motoru verir. Deneysel ML yıllık tüketimi tahmin eder. İsteğe bağlı LLM yalnız hesapları açıklar; erişilemediğinde hesaplama çalışmaya devam eder.']
];
let bootstrap:ReturnType<typeof authRequest>|null=null;
export default function AuthGate(){
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[mode,setMode]=useState<'login'|'register'>('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[busy,setBusy]=useState(false),[step,setStep]=useState<number|null>(null),[theme,setTheme]=useState(readTheme());
 async function enter(value:{user:User|null}){
  setUserScope(value.user?.id??'');
  if(value.user){const list=await loadProjects();if(!list.projects.some(p=>p.id===getActiveProject())&&list.projects[0])setActiveProject(list.projects[0].id);setStep(value.user.onboarding_version<1?0:null)}
  setUser(value.user);
 }
 useEffect(()=>{let alive=true;(bootstrap??=authRequest('session')).then(async value=>{if(alive)await enter(value)}).catch(e=>{if(alive)setError(String(e.message))}).finally(()=>{if(alive)setLoading(false)});return()=>{alive=false}},[]);
 useEffect(()=>{const expired=()=>{setUser(null);setUserScope('');setError('Oturumunuz sona erdi; tekrar giriş yapın.')};window.addEventListener('portfolio25-session-expired',expired);return()=>window.removeEventListener('portfolio25-session-expired',expired)},[]);
 async function finish(){setBusy(true);try{await authRequest('onboarding',{});setStep(null)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 if(loading)return <main className="auth-shell"><p>Oturum kontrol ediliyor…</p></main>;
 if(!user)return <main className="auth-shell"><section className="panel auth-card"><span className="eyebrow">PORTFOLIO25-GRID · SENTETİK DEMO</span><h1>{mode==='login'?'Projenize giriş yapın':'Hesabınızı oluşturun'}</h1><p>Enerji yatırım seçeneklerini, bütçeyi ve modellenen elektrik kapasitesini karşılaştırın.</p><label>Tema<select value={theme} onChange={e=>{const t=e.target.value as Theme;setTheme(t);applyTheme(t)}}><option value="nature">Doğa</option><option value="night">Gece</option><option value="earth">Toprak</option></select></label><form onSubmit={async e=>{e.preventDefault();setBusy(true);setError('');try{const value=await authRequest(mode,{email,password});setPassword('');await enter(value)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}><label>E-posta<input type="email" required maxLength={254} autoComplete="email" value={email} onChange={e=>setEmail(e.target.value)}/></label><label>Parola<input type="password" required minLength={12} maxLength={128} autoComplete={mode==='login'?'current-password':'new-password'} value={password} onChange={e=>setPassword(e.target.value)}/><small>En az 12 karakter.</small></label><button className="button primary full" disabled={busy}>{busy?'İşlem sürüyor…':mode==='login'?'Giriş yap':'Kayıt ol ve pilotu aç'}</button></form>{error&&<p role="alert" className="error-box">{error}</p>}<button className="text-button" disabled={busy} onClick={()=>{setMode(mode==='login'?'register':'login');setError('')}}>{mode==='login'?'Hesabınız yok mu? Kayıt olun':'Hesabınız var mı? Giriş yapın'}</button><p className="small-note">E-posta doğrulama ve parola sıfırlama bu sürümde sunulmaz. Gerçek bina ölçümü içermeyen demo ile başlayın.</p></section></main>;
 return <><div className="account-bar"><span>{user.email}</span><button className="text-button" onClick={()=>setStep(0)}>Kısa tanıtım</button><button className="button secondary" onClick={()=>window.dispatchEvent(new CustomEvent('portfolio25-logout',{detail:async()=>{try{await authRequest('logout',{});setUserScope('');setUser(null);setStep(null)}catch(e){setError((e as Error).message)}}}))}>Çıkış yap</button></div>{error&&<p className="error-box" role="alert">{error}</p>}<PanelBoundary key={user.id}><App/></PanelBoundary>{step!==null&&<div className="modal-backdrop onboarding-backdrop"><section className="panel onboarding" role="dialog" aria-modal="true" aria-label="Kısa tanıtım" onKeyDown={e=>{if(e.key==='Escape')void finish();if(e.key==='Tab'){const nodes=Array.from(e.currentTarget.querySelectorAll<HTMLButtonElement>('button:not(:disabled)'));if(e.shiftKey&&document.activeElement===nodes[0]){e.preventDefault();nodes.at(-1)?.focus()}else if(!e.shiftKey&&document.activeElement===nodes.at(-1)){e.preventDefault();nodes[0]?.focus()}}}}><svg viewBox="0 0 240 80" aria-hidden="true"><path d="M12 65H228"/><rect x="25" y="22" width="38" height="43"/><rect x="83" y="8" width="44" height="57"/><rect x="147" y="30" width="52" height="35"/><path className="onboarding-flow" d="M12 75L65 45L110 55L165 20L225 12"/></svg><p>Adım {step+1} / 4</p><h2>{steps[step][0]}</h2><p>{steps[step][1]}</p><div className="dialog-actions"><button autoFocus className="button secondary" disabled={busy} onClick={()=>void finish()}>Atla</button>{step>0&&<button className="button secondary" onClick={()=>setStep(step-1)}>Geri</button>}<button className="button primary" disabled={busy} onClick={()=>step===3?void finish():setStep(step+1)}>{step===3?'Başla':'İleri'}</button></div></section></div>}</>;
}
