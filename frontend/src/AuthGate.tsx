import {useEffect,useRef,useState} from 'react';
import App from './App';
import PanelBoundary from './PanelBoundary';
import {API_BASE,setUserScope,loadProjects,setActiveProject,getActiveProject,setCSRF,getCSRF} from './api';
import {applyTheme,readTheme,themes,type Theme} from './theme';

type User={id:string;email:string;onboarding_version:number};
export async function authRequest(path:string,body?:unknown){
 const response=await fetch(API_BASE+'/api/auth/'+path,{credentials:'include',method:body===undefined?'GET':'POST',headers:{'Content-Type':'application/json',...(body===undefined?{}:{'X-CSRF-Token':getCSRF()})},body:body===undefined?undefined:JSON.stringify(body),signal:AbortSignal.timeout(30000)});
 const value=await response.json();
 if(!response.ok)throw new Error(typeof value.detail==='string'?value.detail:'Oturum işlemi tamamlanamadı. Girdileri kontrol edin.');
 if(value.csrf)setCSRF(value.csrf);return value;
}
const steps=[
 ['Enerji yatırımını birlikte değerlendirin','Bütçe, enerji tasarrufu ve elektrik bağlantı sınırları aynı hesapta değerlendirilir.'],
 ['Dört proje, sekiz örnek bina','Kampüs, konut sitesi, ofis ve otelin size ait kopyaları hazır. Veriler sentetiktir; saha ölçümü değildir.'],
 ['İnceleyin, kaydedin, hesaplayın','Proje ve binayı seçin. Varsayımları düzenleyip yatırım planını hesaplayın; etkileri karşılaştırın.'],
 ['Hangi sonucu kim üretiyor?','Fizik ve optimizasyon yatırım planını hesaplar. Deneysel ML yıllık tüketimi tahmin eder. İsteğe bağlı LLM hesapları açıklar.']
];

function Onboarding({busy,error,onFinish}:{busy:boolean;error:string;onFinish:()=>void}){
 const [step,setStep]=useState(0);const dialog=useRef<HTMLDialogElement>(null);
 useEffect(()=>{dialog.current?.showModal();return()=>dialog.current?.close()},[]);
 return <main className="onboarding-stage"><div className="onboarding-welcome"><span className="auth-brand">Portfolio25<span>GRID</span></span><p>Projenizi tanımak için kısa bir başlangıç.</p></div><dialog ref={dialog} className="onboarding" aria-labelledby="tour-title" onCancel={e=>{e.preventDefault();if(!busy)onFinish()}}><svg viewBox="0 0 240 80" aria-hidden="true"><path d="M12 65H228"/><rect x="25" y="22" width="38" height="43"/><rect x="83" y="8" width="44" height="57"/><rect x="147" y="30" width="52" height="35"/><path className="onboarding-flow" d="M12 75L65 45L110 55L165 20L225 12"/></svg><p className="tour-progress" aria-live="polite">Adım {step+1} / {steps.length}</p><progress value={step+1} max={steps.length} aria-label="Tanıtım ilerlemesi"/><h1 id="tour-title">{steps[step][0]}</h1><p>{steps[step][1]}</p>{error&&<p className="error-box" role="alert">{error}</p>}<div className="dialog-actions"><button className="button secondary" disabled={busy} onClick={onFinish}>Tanıtımı atla</button>{step>0&&<button className="button secondary" disabled={busy} onClick={()=>setStep(step-1)}>Geri</button>}<button autoFocus className="button primary" disabled={busy} onClick={()=>step===steps.length-1?onFinish():setStep(step+1)}>{busy?'Kaydediliyor…':step===steps.length-1?'Projeyi aç':'İleri'}</button></div></dialog></main>;
}

let bootstrap:ReturnType<typeof authRequest>|null=null;
export default function AuthGate(){
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true),[error,setError]=useState(''),[mode,setMode]=useState<'login'|'register'>('login'),[email,setEmail]=useState(''),[password,setPassword]=useState(''),[visible,setVisible]=useState(false),[busy,setBusy]=useState(false),[tour,setTour]=useState(false),[theme,setTheme]=useState(readTheme());
 async function enter(value:{user:User|null}){
  setUserScope(value.user?.id??'');
  if(value.user){const list=await loadProjects();if(!list.projects.some(p=>p.id===getActiveProject())&&list.projects[0])setActiveProject(list.projects[0].id);setTour(value.user.onboarding_version<1)}
  setUser(value.user);
 }
 useEffect(()=>{let alive=true;(bootstrap??=authRequest('session')).then(async value=>{if(alive)await enter(value)}).catch(e=>{if(alive)setError((e as Error).message)}).finally(()=>{if(alive)setLoading(false)});return()=>{alive=false}},[]);
 useEffect(()=>{const expired=()=>{setUser(null);setUserScope('');setError('Oturumunuz sona erdi; tekrar giriş yapın.')};window.addEventListener('portfolio25-session-expired',expired);return()=>window.removeEventListener('portfolio25-session-expired',expired)},[]);
 async function finish(){setBusy(true);setError('');try{await authRequest('onboarding',{});setTour(false);setUser(u=>u?{...u,onboarding_version:1}:null)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}
 if(loading)return <main className="auth-shell"><p role="status">Oturum kontrol ediliyor…</p></main>;
 if(!user)return <main className="auth-shell"><section className="auth-card" aria-labelledby="auth-title"><div className="auth-card-top"><span className="auth-brand">Portfolio25<span>GRID</span></span><label className="auth-theme">Tema<select aria-label="Giriş teması" value={theme} onChange={e=>{const value=e.target.value as Theme;setTheme(value);applyTheme(value)}}>{themes.map(t=><option key={t.id} value={t.id}>{t.label}</option>)}</select></label></div><h1 id="auth-title">{mode==='login'?'Projenize giriş yapın':'Hesabınızı oluşturun'}</h1><p className="auth-value">Enerji yatırımını bütçe ve elektrik kapasitesiyle birlikte planlayın.</p><form onSubmit={async e=>{e.preventDefault();if(busy)return;setBusy(true);setError('');try{await authRequest('session');const value=await authRequest(mode,{email,password});setPassword('');setVisible(false);await enter(value)}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}><fieldset disabled={busy}><label htmlFor="auth-email">E-posta<input id="auth-email" type="email" required maxLength={254} autoComplete="email" autoCapitalize="none" value={email} onChange={e=>setEmail(e.target.value)}/></label><label htmlFor="auth-password">Parola<div className="password-field"><input id="auth-password" type={visible?'text':'password'} required minLength={mode==='register'?12:undefined} maxLength={128} autoComplete={mode==='login'?'current-password':'new-password'} aria-describedby={mode==='register'?'password-rule':undefined} value={password} onChange={e=>setPassword(e.target.value)}/><button className="password-toggle" type="button" aria-label={visible?'Parolayı gizle':'Parolayı göster'} aria-pressed={visible} onClick={()=>setVisible(!visible)}>{visible?'Gizle':'Göster'}</button></div>{mode==='register'&&<small id="password-rule">En az 12 karakter kullanın.</small>}</label>{error&&<p role="alert" className="auth-error">{error}</p>}<button className="button primary full" type="submit" aria-busy={busy}>{busy?'İşlem sürüyor…':mode==='login'?'Giriş yap':'Hesap oluştur'}</button></fieldset></form><button className="text-button auth-switch" disabled={busy} onClick={()=>{setMode(mode==='login'?'register':'login');setError('');setPassword('');setVisible(false)}}>{mode==='login'?'Hesabınız yok mu? Kayıt olun':'Hesabınız var mı? Giriş yapın'}</button><p className="auth-demo">Size ait sentetik pilotla deneyin; saha verisi gerekmez.</p><details className="auth-help"><summary>Yardım ve sürüm bilgisi</summary><p>Bu sürüm e-posta doğrulama ve parola sıfırlama sunmaz. Oturum hatasında bağlantınızı kontrol edip tekrar deneyin. Proje sonuçları sentetik varsayımlara dayanır.</p></details></section></main>;
 if(tour)return <Onboarding busy={busy} error={error} onFinish={()=>void finish()}/>;
 const account=<><p className="account-email">{user.email}</p><button className="text-button" onClick={()=>window.dispatchEvent(new CustomEvent('portfolio25-tour',{detail:()=>setTour(true)}))}>Kısa tanıtım</button><button className="button secondary" disabled={busy} onClick={()=>window.dispatchEvent(new CustomEvent('portfolio25-logout',{detail:async()=>{setBusy(true);setError('');try{await authRequest('logout',{});setUserScope('');setUser(null);setMode('login');setTour(false);setTheme(readTheme())}catch(e){setError((e as Error).message)}finally{setBusy(false)}}}))}>Çıkış yap</button>{error&&<p className="auth-error" role="alert">{error}</p>}</>;
 return <PanelBoundary key={user.id}><App accountMenu={account}/></PanelBoundary>;
}
