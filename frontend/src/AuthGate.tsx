import {t} from './i18n';
import {useEffect,useRef,useState} from 'react';
import App from './App';
import PanelBoundary from './PanelBoundary';
import DemoGuide from './DemoGuide';
import {API_BASE,setUserScope,loadProjects,setActiveProject,getActiveProject,setCSRF,getCSRF} from './api';
import {applyTheme,readTheme} from './theme';
import {requestAuth,LoginRejectedError,type AuthPath,type AuthReply,type User,type StorageStatus} from './authClient';
import {safeError,ServiceError} from './http';
import {PRODUCTION_ORIGIN,requiresProductionOrigin,OriginRejectedError} from './deployment';
import {useLocale} from './Locale';
import Settings from './Settings';
import {Icon} from './visuals';

export async function authRequest(path:AuthPath,body?:unknown){
 const value=await requestAuth(API_BASE,path,body,getCSRF());
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
 return <main className="onboarding-stage"><div className="onboarding-welcome"><span className="auth-brand">Portfolio25<span>GRID</span></span><p>Projenizi tanımak için kısa bir başlangıç.</p></div><dialog ref={dialog} className="onboarding" aria-labelledby="tour-title" onCancel={e=>{e.preventDefault();if(!busy)onFinish()}}><svg viewBox="0 0 240 80" aria-hidden="true"><path d="M12 65H228"/><rect x="25" y="22" width="38" height="43"/><rect x="83" y="8" width="44" height="57"/><rect x="147" y="30" width="52" height="35"/><path className="onboarding-flow" d="M12 75L65 45L110 55L165 20L225 12"/></svg><p className="tour-progress" aria-live="polite">Adım {step+1} / {steps.length}</p><progress value={step+1} max={steps.length} aria-label="Tanıtım ilerlemesi"/><h1 id="tour-title">{steps[step][0]}</h1><p>{steps[step][1]}</p>{error&&<p className="error-box" role="alert">{error}</p>}<div className="dialog-actions"><button className="button secondary" disabled={busy} onClick={onFinish}>{t("Tanıtımı atla")}</button>{step>0&&<button className="button secondary" disabled={busy} onClick={()=>setStep(step-1)}>{t("Geri")}</button>}<button autoFocus className="button primary" disabled={busy} onClick={()=>step===steps.length-1?onFinish():setStep(step+1)}>{busy?t("Kaydediliyor…"):step===steps.length-1?t("Projeyi aç"):t("İleri")}</button></div></dialog></main>;
}

let bootstrap:Promise<AuthReply>|null=null;
function ColdStartNote(){
 return <p className="auth-server-note">{t("Ücretsiz demo sunucusu kullanılmadığında uykuya geçebilir. İlk bağlantıda uyanması yaklaşık bir dakika, bazen daha uzun sürebilir.")}</p>;
}

export default function AuthGate(){
 const {preferences,setPreferences}=useLocale();
 const [settings,setSettings]=useState(false);
 const useProduction=requiresProductionOrigin(window.location.origin);
 const [user,setUser]=useState<User|null>(null),[loading,setLoading]=useState(true);
 const [error,setError]=useState(''),[connectionError,setConnectionError]=useState(false);
 const [storage,setStorage]=useState<StorageStatus>(),[loginRejected,setLoginRejected]=useState(false);
 const [originRejected,setOriginRejected]=useState(false);
 const [mode,setMode]=useState<'login'|'register'>('login'),[email,setEmail]=useState(''),[password,setPassword]=useState('');
 const [visible,setVisible]=useState(false),[busy,setBusy]=useState(false),[tour,setTour]=useState(false),[theme,setTheme]=useState(readTheme());
 useEffect(()=>{applyTheme(theme)},[theme]);

 function reportError(cause:unknown){setError(safeError(cause));setConnectionError(cause instanceof ServiceError);setOriginRejected(cause instanceof OriginRejectedError);setLoginRejected(cause instanceof LoginRejectedError)}
 async function enter(value:AuthReply){
  setStorage(value.storage);
  const nextUser=value.user??null;
  setUserScope(nextUser?.id??'');
  if(nextUser){
   const list=await loadProjects();
   if(!list.projects.some(p=>p.id===getActiveProject())&&list.projects[0])setActiveProject(list.projects[0].id);
   setTour(nextUser.onboarding_version<1);
  }
  setUser(nextUser);
 }
 useEffect(()=>{
  if(useProduction){setLoading(false);return;}
  let alive=true;
  (bootstrap??=authRequest('session')).then(async value=>{if(alive)await enter(value)})
   .catch(cause=>{bootstrap=null;if(alive)reportError(cause)})
   .finally(()=>{if(alive)setLoading(false)});
  return()=>{alive=false};
 },[]);
 useEffect(()=>{
  const expired=()=>{setUser(null);setUserScope('');setMode('login');setPassword('');setVisible(false);setConnectionError(false);setError('Oturumunuz sona erdi; tekrar giriş yapın.')};
  window.addEventListener('portfolio25-session-expired',expired);
  return()=>window.removeEventListener('portfolio25-session-expired',expired);
 },[]);

 async function reconnect(){
  if(busy)return;
  setBusy(true);setError('');setConnectionError(false);setLoginRejected(false);
  try{await enter(await authRequest('session'))}catch(cause){reportError(cause)}finally{setBusy(false)}
 }
 async function finish(){
  setBusy(true);setError('');
  try{await authRequest('onboarding',{});setTour(false);setUser(u=>u?{...u,onboarding_version:1}:null)}
  catch(cause){reportError(cause)}finally{setBusy(false)}
 }
 async function submit(){
  if(busy)return;
  setBusy(true);setError('');setConnectionError(false);setLoginRejected(false);
  try{
   const session=await authRequest('session');setStorage(session.storage);
   const value=await authRequest(mode,{email,password});
   setPassword('');setVisible(false);await enter(value);
  }catch(cause){reportError(cause)}finally{setBusy(false)}
 }

 if(useProduction)return <main className="auth-shell"><section className="auth-card auth-loading"><span className="auth-brand">Portfolio25<span>GRID</span></span><h1>{t("Demoyu üretim adresinde açın")}</h1><p className="auth-value">Bu dağıtıma özel bağlantı üzerinden giriş yapılmaz. Kayıt ve projeler için sabit adresi kullanın.</p><a className="button primary full production-link" href={PRODUCTION_ORIGIN}>{t("Üretim demosunu aç")}</a><p className="auth-demo">{PRODUCTION_ORIGIN}</p></section></main>;
 if(loading)return <main className="auth-shell"><section className="auth-card auth-loading"><span className="auth-brand">Portfolio25<span>GRID</span></span><h1>{t("Sunucuya bağlanılıyor")}</h1><p role="status">{t("Oturum kontrol ediliyor…")}</p><ColdStartNote/></section></main>;
 if(!user)return <main className="auth-shell"><section className="auth-card" aria-labelledby="auth-title">
  <div className="auth-card-top"><span className="auth-brand">Portfolio25<span>GRID</span></span><span className="auth-product-label">{t('Elektrifikasyon planlama')}</span></div>
  <h1 id="auth-title">{mode==='login'?t("Projenize giriş yapın"):t("Hesabınızı oluşturun")}</h1>
  <p className="auth-value">{t("Enerji yatırımını bütçe ve elektrik kapasitesiyle birlikte planlayın.")}</p>
  {storage?.status==='ephemeral'&&<p className="auth-storage-note" role="status">{t("Kalıcı saklama doğrulanmadı. Bu demo sunucusundaki hesaplar ve projeler yeniden başlatma veya yayın sırasında kaybolabilir.")}</p>}
  <form onSubmit={e=>{e.preventDefault();void submit()}}><fieldset disabled={busy}>
   <label htmlFor="auth-email">{t("E-posta")}<input id="auth-email" type="email" required maxLength={254} autoComplete="email" autoCapitalize="none" value={email} onChange={e=>setEmail(e.target.value)}/></label>
   <label htmlFor="auth-password">{t("Parola")}<div className="password-field"><input id="auth-password" type={visible?'text':'password'} required minLength={mode==='register'?12:undefined} maxLength={128} autoComplete={mode==='login'?'current-password':'new-password'} aria-describedby={mode==='register'?'password-rule':undefined} value={password} onChange={e=>setPassword(e.target.value)}/><button className="password-toggle" type="button" aria-label={visible?t("Parolayı gizle"):t("Parolayı göster")} aria-pressed={visible} onClick={()=>setVisible(!visible)}>{visible?t("Gizle"):t("Göster")}</button></div>{mode==='register'&&<small id="password-rule">{t("En az 12 karakter kullanın.")}</small>}</label>
   {error&&<p role="alert" className="auth-error">{t(error)}</p>}
   {loginRejected&&<details className="auth-login-help"><summary>{t('Giriş yapamıyor musunuz?')}</summary><p>{t("Aynı e-posta adresini, klavye dilini ve Caps Lock durumunu kontrol edin. Parolayı göstererek yazımı inceleyebilirsiniz.")}</p><p>{t("Bu hata, yanlış parola ile sunucuda artık bulunmayan hesabı ayırt etmez. Yeni hesap açmak eski projeleri geri getirmez; eski kayıtlar için yönetici yedeği gerekir.")}</p></details>}
   <button className="button primary full" type="submit" aria-busy={busy}>{busy?t("İşlem sürüyor…"):mode==='login'?t("Giriş yap"):t("Hesap oluştur")}</button>
  </fieldset></form>
  {originRejected&&<a className="button secondary full production-link" href={PRODUCTION_ORIGIN}>{t("Üretim adresinde giriş yap")}</a>}
  {connectionError&&<button className="button secondary full auth-reconnect" disabled={busy} onClick={()=>void reconnect()}>{t("Bağlantıyı yeniden dene")}</button>}
  <button className="text-button auth-switch" disabled={busy} onClick={()=>{setMode(mode==='login'?'register':'login');setError('');setConnectionError(false);setLoginRejected(false);setPassword('');setVisible(false)}}>{mode==='login'?t("Hesabınız yok mu? Kayıt olun"):t("Hesabınız var mı? Giriş yapın")}</button>
  <p className="auth-demo">{t("Size ait sentetik pilotla deneyin; saha verisi gerekmez.")}</p>
  <ColdStartNote/>
  <div className="auth-footer"><details className="auth-help"><summary>{t("Demo rehberi ve sınırlar")}</summary><DemoGuide/><p>{t("E-posta doğrulama ve parola sıfırlama bu sürümde bulunmaz.")}</p></details><button className="text-button" onClick={()=>setSettings(true)}><Icon name="sliders" size={15}/>{t('Ayarlar')}</button></div>
 </section>{settings&&<Settings theme={theme} onTheme={setTheme} preferences={preferences} onPreferences={setPreferences} onClose={()=>setSettings(false)}/>}</main>;
 if(tour)return <Onboarding busy={busy} error={error} onFinish={()=>void finish()}/>;
 const account=<>
  <p className="account-email">{user.email}</p>
  <button className="text-button" onClick={()=>window.dispatchEvent(new CustomEvent('portfolio25-tour',{detail:()=>setTour(true)}))}>{t("Kısa tanıtım")}</button>
  <button className="button secondary" disabled={busy} onClick={()=>window.dispatchEvent(new CustomEvent('portfolio25-logout',{detail:async()=>{
   setBusy(true);setError('');
   try{await authRequest('logout',{});setUserScope('');setUser(null);setMode('login');setTour(false);setTheme(readTheme())}
   catch(cause){reportError(cause)}finally{setBusy(false)}
  }}))}>{t("Çıkış yap")}</button>
  {error&&<p className="auth-error" role="alert">{error}</p>}
 </>;
 return <PanelBoundary key={user.id}><App accountMenu={account}/></PanelBoundary>;
}
