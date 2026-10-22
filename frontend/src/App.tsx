import NamedScenarios from './NamedScenarios';
import {t,tr} from './i18n';
import PanelBoundary from './PanelBoundary';
import { useEffect, useRef, useState, type ReactNode } from 'react';
import { API_BASE, calculateCampus, downloadCampus, loadCampus, loadLastCalculation, saveCampus, loadProjects, setActiveProject } from './api';
import type { Building, Campus, CampusResponse, CalculationResult, Scenario, ProjectSummary } from './types';
import { BuildingEditor, ScenarioForm } from './forms';
import { Icon } from './visuals';
import { errorMessage, n } from './format';
import { campusFromCSV } from './csv';
import BuildingDetail from './BuildingDetail';
import Results from './Results';
import ScenarioModel from './ScenarioModel';
import {ProjectPicker,ProjectSettings} from './Projects';
import PilotLoader from './PilotLoader';
import AlternativeScenario from './AlternativeScenario';
import ModelData from './ModelData';
import {clearProjectDrafts,hasDrafts,readDraft} from './drafts';
import {getActiveProject} from './api';
import {loadPilotStatus} from './api';
import type {PilotStatus} from './spatialTypes';
import ContextBar from './ContextBar';
import DemoGuide from './DemoGuide';
import ProjectReadiness from './ProjectReadiness';
import {useLocale} from './Locale';
import Settings from './Settings';
import {applyTheme, readTheme} from './theme';
import {noticeVisible,type Notice} from './viewState';

type Page = 'overview' | 'building' | 'scenario' | 'results' | 'model';
const pages = [{ id: 'overview', title: 'Proje özeti', icon: 'grid', }, { id: 'building', title: 'Bina detayları', icon: 'building', }, { id: 'scenario', title: 'Senaryo girdileri', icon: 'sliders', }, { id: 'results', title: 'Optimizasyon sonucu', icon: 'leaf', },{id:'model',title:'Model ve veri',icon:'info',}] as const;

function Modal({ title, onClose, children }: { title: string; onClose: () => void; children: ReactNode }) {
  const ref = useRef<HTMLDialogElement>(null);
  useEffect(() => { ref.current?.showModal(); }, []);
  return <dialog ref={ref} className="assumptions-dialog" onCancel={onClose} aria-labelledby="modal-title"><div className="dialog-top"><h2 id="modal-title">{title}</h2><button className="icon-button" aria-label={t("Pencereyi kapat")} onClick={onClose}><Icon name="close" /></button></div>{children}</dialog>;
}

export default function App({accountMenu}:{accountMenu?:ReactNode}) {
  const {preferences,setPreferences}=useLocale();
  const [settings,setSettings]=useState(false);
  const [utility,setUtility]=useState<'account'|'help'|'menu'|null>(null);
  const [theme,setTheme] = useState(readTheme);
  const [about,setAbout] = useState(false);
  const [pilot,setPilot] = useState<PilotStatus|null>(null);
  const managementRef = useRef<HTMLDetailsElement>(null);
  useEffect(()=>{applyTheme(theme)},[theme]);
  const [data, setData] = useState<CampusResponse | null>(null);
  const [previous, setPrevious] = useState<CalculationResult | null>(null);
  const [page, setPage] = useState<Page>('overview');
  const [chosen, setChosen] = useState('B01');
  const [buildingView,setBuildingView]=useState<'floors'|'packages'|'ml'>('floors');
  const refreshSequence=useRef(0);
  const [navigation,setNavigation]=useState<null|(()=>void)>(null);
  const [savingNavigation,setSavingNavigation]=useState(false);
  const dispatchedSave=useRef('');
  const [navigationAttempt,setNavigationAttempt]=useState(0);
  const [editing, setEditing] = useState<Building | null>(null);
  const [editorDirty, setEditorDirty] = useState(false);
  const [scenarioDirty, setScenarioDirty] = useState(false);
  const [projectDirty,setProjectDirty]=useState(false);
  const [spatialDirty,setSpatialDirty]=useState(false);
  const [projects,setProjects]=useState<ProjectSummary[]>([]);
  const [draft, setDraft] = useState<Scenario | null>(null);
  const [formKey, setFormKey] = useState(0);
  const [exportScope, setExportScope] = useState<'inputs' | 'result'>('inputs');
  const [mode, setMode] = useState<'A' | 'B'>('A');
  const [seconds, setSeconds] = useState('10');
  const [loading, setLoading] = useState(true);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [notice, setNotice] = useState<Notice|null>(null);
  const [query, setQuery] = useState('');
  const [assumptions, setAssumptions] = useState(false);
  const [csvError, setCsvError] = useState('');
  const [csvPreview, setCsvPreview] = useState<Campus | null>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const scenarioContainer = useRef<HTMLDivElement>(null);
  const campus = data?.campus;
  const result = data?.calculation ?? previous;
  const pending = scenarioDirty || projectDirty || spatialDirty || editorDirty || !!csvPreview;
  const stale = !!result && (!data?.calculation || result.calculation_id!==data.calculation_id || result.project_id!==campus?.id || result.input_revision !== campus?.revision || pending || result.mode !== mode);
  const active = result && !stale ? result : null;
  const canExport = !!data && !pending && !busy && !loading && (exportScope === 'inputs' || (!stale && !!data.calculation && !!data.calculation_id));
  const selectedBuilding = campus?.buildings.find(b => b.id === chosen) ?? campus?.buildings[0];
  function guard(action:()=>void){if(pending){setNavigation(()=>action);setSavingNavigation(false);dispatchedSave.current='';}else action();}
  function goPage(next:Page){if(next===page)return;const action=()=>{setPage(next);window.scrollTo({top:0,behavior:'instant'})};if(next==='scenario'&&!editorDirty&&!spatialDirty&&!csvPreview)action();else guard(action)}
  useEffect(()=>{const handler=(event:BeforeUnloadEvent)=>{if(pending||hasDrafts()){event.preventDefault();event.returnValue='';}};window.addEventListener('beforeunload',handler);return()=>window.removeEventListener('beforeunload',handler)},[pending]);
  useEffect(()=>{
    if(!navigation||!savingNavigation||busy)return;
    if(!pending){const action=navigation;setNavigation(null);setSavingNavigation(false);action();return;}
    const kind=editorDirty?'editor':spatialDirty?'spatial':scenarioDirty?'scenario':projectDirty?'project':'csv';
    if(dispatchedSave.current===kind)return;dispatchedSave.current=kind;
    if(kind==='spatial')(document.querySelector('.spatial-save') as HTMLButtonElement|null)?.click();
    else {const selector=kind==='editor'?'dialog:not(.draft-guard) form':kind==='scenario'?'.scenario-panel form':'.project-settings form';(document.querySelector(selector) as HTMLFormElement|null)?.requestSubmit();}
  },[navigation,navigationAttempt,savingNavigation,pending,busy,editorDirty,spatialDirty,scenarioDirty,projectDirty]);
  useEffect(()=>{const listener=(event:Event)=>guard((event as CustomEvent).detail);window.addEventListener('portfolio25-logout',listener);window.addEventListener('portfolio25-tour',listener);return()=>{window.removeEventListener('portfolio25-logout',listener);window.removeEventListener('portfolio25-tour',listener)}},[pending,busy]);
  async function refresh() {
    const requestedProject=getActiveProject();const sequence=++refreshSequence.current;
    setLoading(true); setError('');setNotice(null);
    try {
      const list=await loadProjects();
      if(requestedProject!==getActiveProject()||sequence!==refreshSequence.current)return;
      setProjects(list.projects);
      const pilotStatus=await loadPilotStatus().catch(()=>null);
      if(requestedProject!==getActiveProject()||sequence!==refreshSequence.current)return;
      setPilot(pilotStatus);
      const value = await loadCampus(); if(requestedProject!==getActiveProject()||sequence!==refreshSequence.current)return; setData(value);
      const last = await loadLastCalculation();if(requestedProject!==getActiveProject()||sequence!==refreshSequence.current)return;
      if (last.current_revision !== value.campus.revision) throw new Error('Kayıt başka bir oturumda değişti. Veriyi tekrar yenileyin.');
      if (value.calculation && last.calculation_id !== value.calculation_id) throw new Error('Hesap iki okuma arasında değişti; veriyi yenileyin.');
      setExportScope(value.calculation ? 'result' : 'inputs');
      setPrevious(last.calculation); setMode(value.calculation?.mode ?? last.calculation?.mode ?? 'A');
      setFormKey(k => k + 1); setScenarioDirty(false); setDraft(value.campus.scenario); setCsvPreview(null);
    } catch (e) { if(requestedProject===getActiveProject()&&sequence===refreshSequence.current)setError(errorMessage(e)); }
    finally { if(sequence===refreshSequence.current)setLoading(false); }
  }
  useEffect(() => { void refresh(); }, []);
  useEffect(() => { if (!notice) return; const timer = setTimeout(() => setNotice(null), 6000); return () => clearTimeout(timer); }, [notice]);
  function accept(value: CampusResponse) { setData(value); if (value.calculation) setPrevious(value.calculation); }
  async function selectProject(id:string) {
    setNotice(null);setActiveProject(id);setData(null);setPrevious(null);setScenarioDirty(false);setProjectDirty(false);setSpatialDirty(false);setEditorDirty(false);setEditing(null);setDraft(null);setChosen('B01');setPage('overview');setQuery('');
    if(managementRef.current)managementRef.current.open=false;
    await refresh();
  }
  async function commit(value: Campus) {
    setBusy(true); setError('');
    try { const saved = await saveCampus(value); accept(saved); setNotice({message:'Girdiler kaydedildi.',projectId:saved.campus.id,revision:saved.campus.revision,calculationId:null,kind:'saved'}); return saved; }
    finally { setBusy(false); }
  }
  async function compute() {
    if (!data || busy || csvPreview || editorDirty) return;
    if(spatialDirty){setError('Kat varsayımları/seçimleri değişti; önce bina detayında kaydedin.');return;}
    if(projectDirty){setError('Proje ve bağlantı/duyarlılık değişikliklerini önce kaydedin.');return;}
    if (!Number.isFinite(Number(seconds)) || Number(seconds) < .01 || Number(seconds) > 60) { setError('Çözücü süresi 0,01–60 saniye aralığında olmalı.'); return; }
    const form = scenarioContainer.current?.querySelector<HTMLFormElement>('.scenario-panel form');
    if (form && !form.reportValidity()) return;
    setBusy(true); setError('');setNotice(null);
    try {
      let current = data;
      if (scenarioDirty && draft) { current = await saveCampus({ ...data.campus, scenario: draft }); accept(current); }
      const calculated = await calculateCampus(current.campus.revision, mode, Number(seconds));
      const verified = await loadCampus();
      if (verified.campus.revision !== calculated.input_revision || !verified.calculation || verified.calculation.mode !== calculated.mode || verified.calculation_id !== calculated.calculation_id) { accept(verified); throw new Error('Hesap veya girdiler başka bir oturumda değişti. Yenileyip tekrar hesaplayın.'); }
      accept(verified); setExportScope('result');setNotice(null);setDraft(verified.campus.scenario);setScenarioDirty(false);
      setPrevious(calculated); setPage('results'); window.scrollTo({ top: 0, behavior: 'instant' });
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function exportData(format: 'csv' | 'json' | 'html', kind: 'inputs' | 'result' = exportScope) {
    if (!data || pending || busy || loading || (kind === 'result' && (!active || !data.calculation_id))) return;
    setBusy(true); setError('');
    try {
      await downloadCampus(format, kind, campus!.revision, data?.calculation_id, active?.mode);
      setNotice({message:`${kind === 'inputs' ? 'Başlangıç verisi' : 'Hesaplanmış sonuç'} indirildi.`,projectId:campus!.id,revision:campus!.revision,calculationId:data.calculation_id??null,kind:'export'});
    } catch (e) { setError(errorMessage(e)); }
    finally { setBusy(false); }
  }
  async function readCSV(file: File | undefined) {
    if (!file || !campus) return;
    setCsvError(''); setCsvPreview(null);
    try {
      if (!file.name.toLowerCase().endsWith('.csv')) throw new Error('Lütfen .csv uzantılı bir dosya seçin.');
      if (file.size > 2 * 1024 * 1024) throw new Error('CSV dosyası 2 MB sınırını aşıyor.');
      setCsvPreview(campusFromCSV(await file.text(), campus));
    } catch (e) { setCsvError(errorMessage(e)); }
    if (fileInput.current) fileInput.current.value = '';
  }
  function openBuilding(id:string,view:'floors'|'packages'|'ml'='floors'){guard(()=>{setChosen(id);setBuildingView(view);setPage('building');window.scrollTo({top:0,behavior:'instant'})})}
  return <div className="app-shell">
    <a className="skip-link" href="#main">{t("İçeriğe geç")}</a>
    <aside className="sidebar"><a className="brand" href="#main" onClick={() => goPage('overview')}><span className="brand-symbol"><Icon name="grid" size={27} /></span><span>Portfolio25<span className="brand-sub">GRID</span></span></a><p className="workspace-label">{t('Elektrifikasyon planlama')}</p><nav aria-label={t("Ana menü")}>{pages.map(item => <button key={item.id} className={`nav-item ${page === item.id ? 'active' : ''}`} aria-label={t(item.title)} aria-current={page === item.id ? 'page' : undefined} onClick={() => goPage(item.id)}><Icon name={item.icon} size={19} /><span className="nav-label-full">{t(item.title)}</span><span className="nav-label-short" aria-hidden="true">{({overview:t("Özet"),building:t("Binalar"),scenario:t("Senaryo"),results:t("Sonuç"),model:t("Model")} as const)[item.id]}</span></button>)}</nav><div className="sidebar-utilities" aria-label={tr('Workspace tools','Çalışma alanı araçları')}><button onClick={()=>setUtility('account')}><span className="utility-avatar" aria-hidden="true">P</span>{t('Hesap')}</button><button className="settings-button" onClick={()=>setSettings(true)}><Icon name="sliders" size={18}/>{t('Ayarlar')}</button><button onClick={()=>setUtility('help')}><Icon name="info" size={18}/>{tr('Help','Yardım')}</button></div></aside>
    <div className="main-shell" data-page={page}><header className="topbar">
      <div className="workspace-identity"><strong className="mobile-brand">Portfolio25<span>GRID</span></strong><span className="workspace-section">{t(pages.find(p=>p.id===page)?.title??'Proje özeti')}</span></div>
      <button className="button secondary mobile-tools" onClick={()=>setUtility('menu')} aria-label={tr('Account, settings and help','Hesap, ayarlar ve yardım')}><Icon name="sliders" size={17}/>{tr('Menu','Menü')}</button>
    </header>
      <main id="main"><div className="page-heading"><div><h1>{page==='building'?selectedBuilding?.name??t("Bina yükleniyor…"):page==='overview'?campus?.name??t("Proje yükleniyor…"):page==='results'?t("Yatırım planı"):t(pages.find(p=>p.id===page)?.title??'')}</h1><p>{page==='building'&&selectedBuilding?`${campus?.name} · ${t(selectedBuilding.use_type)} · ${n(selectedBuilding.area_m2,0)} m² · ${selectedBuilding.year_built}`:page==='overview'?`${campus?campus.buildings.length+' '+tr('buildings','bina')+' · ':''}${t('Enerji görünümü')}`:page==='scenario'?`${campus?.name??t("Proje")} · ${tr('Budget, target and investment plan','Bütçe, hedef ve yatırım planı')}`:page==='results'?tr('Selected investments and their effects','Seçilen yatırımlar ve etkileri'):tr('Experimental predictions and data sources','Deneysel tahmin ve veri kaynakları')}</p></div><div className="export-actions">{page==='building'&&selectedBuilding&&<button className="button secondary" disabled={busy} onClick={()=>setEditing(selectedBuilding)}>{t("Bilgileri düzenle")}</button>}{page==='overview'&&<button className="button primary main-plan-action" disabled={busy||!data} onClick={()=>goPage('scenario')}>{t("Yatırım planını hazırla")}<Icon name="arrow" size={16}/></button>}{page==='scenario'&&<button className="button primary compute-button" disabled={busy || !data || !!csvPreview || !Number.isFinite(Number(seconds)) || Number(seconds) < .01 || Number(seconds) > 60} onClick={() => void compute()}>{busy?t("Hesaplanıyor…"):t("Yatırım planını hesapla")}<Icon name="arrow" size={17} /></button>}<details className="export-menu"><summary>{t("Dışa aktar")}</summary><div className="export-menu-content"><label>{t("Dışa aktarım türü")}<select aria-label={t("Dışa aktarım türü")} value={exportScope} onChange={e=>setExportScope(e.target.value as 'inputs'|'result')}><option value="inputs">{t("Başlangıç verisi")}</option><option value="result">{t("Hesaplanmış sonuç")}</option></select></label><button className="button secondary" disabled={!canExport} onClick={()=>void exportData('csv')}>{t("CSV indir")}</button><button className="button secondary" disabled={!canExport} onClick={()=>void exportData('json')}>{t("JSON indir")}</button></div></details></div></div>
        <section className="project-workspace" aria-label="Proje çalışma alanı"><ContextBar campus={campus} building={selectedBuilding} projects={projects} pilot={pilot} disabled={busy||loading} onProject={id=>guard(()=>void selectProject(id))} onBuilding={openBuilding}/><span className="source-tag">{campus?.provenance.kind==='synthetic'?t("Sentetik örnek · saha ölçümü değil"):t("Kaynak ve varsayımlarla modellenir")}</span></section>{pilot?.projects.some(p=>!p.loaded)&&<div className="pilot-missing"><span>{t("Kayseri pilotunun bazı projeleri henüz yüklenmedi. Kampüs, konut sitesi, ofis ve otel seçenekleri yükleyince görünür.")}</span><button className="text-button" onClick={()=>{if(managementRef.current){managementRef.current.open=true;const details=managementRef.current.querySelector('.pilot-loader details');details?.setAttribute('open','');managementRef.current.scrollIntoView({block:'start'})}}}>{t("Pilot yükleme seçeneklerini aç")}</button></div>}
        {error && <div className="error-box" role="alert"><span>{error}</span><button className="button secondary" disabled={busy || loading} onClick={() => guard(()=>void refresh())}>{t("Tekrar dene")}</button></div>}
        {stale && page !== 'results' && <div className="stale-notice" role="status"><Icon name="info" size={18} /><span><strong>{t("Girdiler değişti; yeniden hesaplayın.")}</strong>{" "+t("Sonuç dışa aktarımı yeniden hesaplanana kadar kapalı.")}</span><button className="text-button" onClick={() => goPage('results')}>{t("Önceki hesabı gör")}</button></div>}
        {noticeVisible(notice,campus?.id,campus?.revision,data?.calculation_id)&&<div className="inline-notice" role="status"><Icon name="check" size={18}/>{notice!.message}</div>}
        {loading && !data && <div className="loading-state" role="status"><span className="spinner" />{t("Örnek proje API’den yükleniyor…")}</div>}
        {data && campus && <>
          {page === 'overview' && <>
            <div className="stats-grid"><Metric title={t("Yıllık nihai enerji")} value={n(data.baseline.total_energy_kwh_year / 1e6, 2)} unit="GWh/yıl" note={t("Elektrik + tüm doğalgaz")} icon="bolt" /><Metric title={t("Enerji yoğunluğu")} value={n(data.baseline.intensity_kwh_m2_year)} unit="kWh/m²-yıl" note={`${n(data.baseline.area_m2, 0)} m² ${tr("total gross area","toplam brüt alan")}`} icon="building" /><Metric title={t("Yıllık enerji maliyeti")} value={n(data.baseline.energy_cost_try_year / 1e6, 2)} unit="milyon TL" note={t("Kaynak/tarihli varsayımsal tarifeler")} icon="sliders" /><Metric title={campus.connection_groups.length===1?t("Eşzamanlı elektrik piki"):t("Proje toplam piki (tanısal)")} value={n(data.baseline.electric_peak_kw)} unit="kW" note={`${n(data.baseline.capacity_utilization_pct)}% ${tr("maximum group utilization","en yüksek grup kullanımı")} · ${campus.connection_groups.length} ${tr("groups","grup")}`} icon="grid" /></div>
            <section className="panel inventory-panel"><div className="section-heading"><div><span className="eyebrow">{t("BİNA ENVANTERİ")}</span><h2>{t("Binalar ve başlangıç tüketimleri")}</h2></div><div className="inventory-tools"><input className="search-input" aria-label={t("Bina ara")} placeholder={t("Bina adı veya kodu ara…")} value={query} onChange={e => setQuery(e.target.value)} /><button className="button secondary" disabled={busy || pending} onClick={() => fileInput.current?.click()}>{t("CSV ile güncelle")}</button><input ref={fileInput} type="file" accept=".csv,text/csv" aria-label={t("Sentetik proje CSV dosyası")} className="sr-only" onChange={e => void readCSV(e.target.files?.[0])} /></div></div>
              {csvError && <div className="error-box" role="alert"><strong>{t("CSV yüklenemedi.")}</strong><span>{csvError}</span><button className="text-button" onClick={() => setCsvError('')}>{t("Kapat")}</button></div>}
              {csvPreview && <div className="csv-preview"><div><strong>{csvPreview.buildings.length} bina için CSV doğrulaması tamamlandı</strong><p>{t("İsim, tüketim ve senaryo değişiklikleri API doğrulamasından sonra birlikte kaydedilecek. Dosyadaki eski sonuç sütunları içe alınmaz.")}</p></div><button className="button secondary" onClick={() => setCsvPreview(null)} disabled={busy}>{t("Vazgeç")}</button><button className="button primary" disabled={busy} onClick={async () => { try { const next = await commit(csvPreview); setCsvPreview(null); setDraft(next.campus.scenario); setFormKey(k => k + 1); } catch (e) { setCsvError(errorMessage(e)); } }}>{csvPreview.buildings.length} binayı uygula</button></div>}
              <div className="table-scroll"><table><thead><tr><th>{t("Bina / kullanım")}</th><th>{t("Alan")}</th><th>{t("Elektrik")}</th><th>{t("Toplam doğalgaz")}</th><th>{t("Profil piki / bağlantı")}</th><th>{t("İşlem")}</th></tr></thead><tbody>{campus.buildings.filter(b => `${b.name} ${b.id}`.toLocaleLowerCase('tr').includes(query.toLocaleLowerCase('tr'))).map(b => <tr key={b.id}><td><button className="building-cell" onClick={() => openBuilding(b.id)}><span className="building-code">{b.id}</span><span><strong>{b.name}</strong><small>{t(b.use_type)} · {b.year_built} · {tr("Synthetic","Sentetik")}</small></span></button></td><td>{n(b.area_m2, 0)}<small>m²</small></td><td>{n(b.electricity_kwh_year / 1000)}<small>{t("MWh/yıl")}</small></td><td>{n((b.heating_kwh_year + b.non_heating_gas_kwh_year) / 1000)}<small>{t("MWh/yıl")}</small></td><td>{n(data.profile_audit.buildings.find(r => r.building_id === b.id)?.electric_peak_kw)} / {n(b.connection_limit_kw)}<small>kW</small></td><td><button className="icon-button edit-button" aria-label={`${b.name} düzenle`} disabled={busy} onClick={() => setEditing(b)}><Icon name="edit" size={17} /></button></td></tr>)}</tbody></table>{!campus.buildings.some(b => `${b.name} ${b.id}`.toLocaleLowerCase('tr').includes(query.toLocaleLowerCase('tr'))) && <p className="empty-search">{t("Bu aramayla eşleşen bina bulunamadı.")}</p>}</div><div className="table-footer"><button className="text-button" onClick={()=>setAssumptions(true)}>{t("Kaynak ve varsayımlar")}</button><span>{t("CSV yalnız bu uygulamanın sentetik dışa aktarma şablonunu kabul eder.")}</span></div></section>
            <div className="overview-grid"><ProjectReadiness data={data} onBuilding={id=>guard(()=>setEditing(campus.buildings.find(b=>b.id===id)??null))} onScenario={()=>goPage("scenario")} onAssumptions={()=>setAssumptions(true)}/><details className="panel scenario-map-disclosure"><summary>{t('Şematik proje görünümü')}<span>{t('Önce / sonra bina etkileri')}</span></summary><ScenarioModel selectedId={selectedBuilding?.id} onSelect={id=>guard(()=>setChosen(id))} data={data} result={active} onBuilding={id=>openBuilding(id,'packages')}/></details></div>
          </>}
          {page === 'building' && selectedBuilding && <BuildingDetail disabled={pending||busy} context={data.context} key={`${campus.id}-${formKey}`} initialTab={buildingView} building={selectedBuilding} revision={campus.revision} result={active} onSpatialDirty={setSpatialDirty} onSpatialSave={async building=>{await commit({...campus,buildings:campus.buildings.map(b=>b.id===building.id?building:b)});}} onEdit={() => { if (!busy) setEditing(selectedBuilding); }} />}
          <div hidden={page !== 'scenario'} className="scenario-layout" ref={scenarioContainer}><div className="scenario-forms"><ScenarioForm key={formKey} campus={campus} disabled={busy} onDirtyChange={setScenarioDirty} onDraftChange={setDraft} onSave={async scenario => { await commit({ ...campus, scenario }); }} /><details className="panel scenario-expert"><summary>{t("Bağlantılar ve gelişmiş varsayımlar")}</summary><ProjectSettings key={`${campus.id}-${formKey}`} campus={campus} disabled={busy} onDirty={setProjectDirty} onSave={async value=>{if(scenarioDirty)throw new Error("Önce senaryo girdilerini kaydedin; proje taslağınız korunur.");return commit(value);}}/><PanelBoundary><AlternativeScenario key={campus.id} data={data} disabled={pending||busy} onApplied={value=>{accept(value);setDraft(value.campus.scenario);setScenarioDirty(false);setProjectDirty(false);setFormKey(k=>k+1);setNotice({message:"Senaryo girdileri kaydedildi.",projectId:value.campus.id,revision:value.campus.revision,calculationId:null,kind:"saved"})}}/></PanelBoundary></details></div><div className="scenario-side"><section className="panel mode-panel"><span className="eyebrow">{t("OPTİMİZASYON HEDEFİ")}</span><h2>{t("Planın hedefini seçin")}</h2><p className="compute-context">{campus.name} · {campus.buildings.length} bina hesaplanacak</p><label className={`mode-option ${mode === 'A' ? 'selected' : ''}`}><input type="radio" name="mode" value="A" checked={mode === 'A'} disabled={busy} onChange={() => setMode('A')} /><span><strong>{t("Mod A · En yüksek enerji tasarrufu")}</strong><small>{t("Bütçe ve kapasite sınırları altında yıllık nihai enerji tasarrufunu en yüksek yapar. Hedef bilgi amaçlıdır.")}</small></span></label><label className={`mode-option ${mode === 'B' ? 'selected' : ''}`}><input type="radio" name="mode" value="B" checked={mode === 'B'} disabled={busy} onChange={() => setMode('B')} /><span><strong>{t("Mod B · Hedefe en düşük yatırımla ulaş")}</strong><small>{t("Enerji hedefine bütçe ve kapasite sınırlarını koruyarak ulaşır. Sağlanamayan hedef açıkça bildirilir.")}</small></span></label><details className="solver-options"><summary>{t("Gelişmiş hesap ayarı")}</summary><label className="time-limit">{t("Çözücü süre sınırı (sn)")}<input type="number" aria-label={t("Çözücü süre sınırı")} min="0.01" max="60" step="0.01" value={seconds} disabled={busy} onChange={e => setSeconds(e.target.value)} /></label></details><p className="small-note">{t("Her bina için tam bir paket seçilir. Bina bağlantı ve bağlantı grubu sınırları iki modda da zorunludur.")}</p></section><button className="text-button scenario-sources-link" onClick={()=>setAssumptions(true)}><Icon name="info" size={16}/>{t('Kaynak ve varsayımlar')}</button></div></div>
          {page==='model'&&<PanelBoundary><ModelData key={campus.id} data={data} buildingId={selectedBuilding!.id} disabled={pending||busy}/></PanelBoundary>}
          {page === 'results' && <Results data={data} result={result} stale={stale} busy={busy} onBrief={()=>void exportData('html','result')} onScenario={() => goPage('scenario')} onBuilding={id=>openBuilding(id,'packages')} onAssumptions={() => setAssumptions(true)} onExport={() => void exportData('csv', 'result')} />}
          <NamedScenarios key={campus.id} data={data} disabled={pending||busy||loading}/><details ref={managementRef} className="project-management"><summary>{t("Proje ve örnek veri yönetimi")}</summary><ProjectPicker showSelector={false} campus={campus??null} projects={projects} disabled={busy||loading} onSelect={async id=>guard(()=>void selectProject(id))}/><PilotLoader disabled={busy||loading||pending} onOpen={async id=>guard(()=>void selectProject(id))}/></details><footer className="main-footer"><span>Portfolio25-GRID</span><button className="text-button" onClick={()=>setAbout(true)}>{t("Uygulama hakkında")}</button></footer>
        </>}
      </main></div>
    {utility&&<Modal title={utility==='account'?t('Hesap'):utility==='help'?tr('Help','Yardım'):tr('Menu','Menü')} onClose={()=>setUtility(null)}>
      {utility==='account'?<div className="utility-content"><p className="utility-description">{tr('Manage your current session. Signing out keeps your saved projects.','Mevcut oturumunuzu yönetin. Çıkış yapmak kaydedilmiş projelerinizi silmez.')}</p>{accountMenu}</div>:utility==='help'?<div className="utility-content"><DemoGuide/><div className="utility-links"><button className="button secondary" onClick={()=>{setUtility(null);setAssumptions(true)}}>{t('Kaynak ve varsayımlar')}</button><button className="text-button" onClick={()=>{setUtility(null);setAbout(true)}}>{t('Uygulama hakkında')}</button></div><details><summary>{tr('Data refresh','Veriyi yenileme')}</summary><p>{tr('Reload saved inputs. You will be asked to save or discard unsaved changes.','Kaydedilmiş girdileri yeniden yükleyin. Kaydedilmemiş değişiklikler için kaydetme veya vazgeçme seçeneği sunulur.')}</p><button className="button secondary" disabled={busy||loading} onClick={()=>{setUtility(null);guard(()=>void refresh())}}>{t('Veriyi yenile')}</button></details></div>:<div className="utility-menu"><button onClick={()=>setUtility('account')}>{t('Hesap')}</button><button onClick={()=>{setUtility(null);setSettings(true)}}>{t('Ayarlar')}</button><button onClick={()=>setUtility('help')}>{tr('Help','Yardım')}</button></div>}
    </Modal>}
    {settings&&<Settings theme={theme} onTheme={setTheme} preferences={preferences} onPreferences={setPreferences} onClose={()=>setSettings(false)} onProjectSettings={()=>{setSettings(false);goPage('scenario');setTimeout(()=>{document.querySelector('.scenario-expert')?.setAttribute('open','');document.querySelector('.project-settings>details')?.setAttribute('open','');document.querySelector('.project-settings')?.scrollIntoView({block:'start'})},0)}} onSources={()=>{setSettings(false);setAssumptions(true)}} onAbout={()=>{setSettings(false);setAbout(true)}}/>}
    {about&&<Modal title={t("Uygulama hakkında")} onClose={()=>setAbout(false)}><p>Portfolio25-GRID · Sentetik verilerle enerji yatırımı karar desteği. Kullanıcıya özel projeler ve kalıcı oturum yetkilendirmesi içerir. E-posta doğrulama/parola sıfırlama sunulmaz.</p>{campus&&<dl className="technical-context"><dt>{t("Proje")}</dt><dd>{campus.name} · {campus.id}</dd><dt>Veri / kayıt / dönem</dt><dd>Şema {campus.schema_version} · kayıt r{campus.revision} · {campus.profile_settings.year}</dd><dt>Motor</dt><dd>{data?.context?.engine_version}</dd><dt>Güncel hesap</dt><dd>{data?.calculation_id??'Güncel hesap yok'}</dd><dt>API</dt><dd>{API_BASE||'/api'}</dd></dl>}<p>Proje verileri, varsayımlar ve hesap geçmişi backend tarafından saklanır. Eski motor veya girdilere ait sonuç güncel plan olarak kullanılmaz.</p></Modal>}
    {navigation&&<Modal title={t("Kaydedilmemiş değişiklikler")} onClose={()=>{setNavigation(null);setSavingNavigation(false)}}><p>{t("Taslağınız bu tarayıcıda korunur. Devam etmeden önce seçin.")}</p><div className="dialog-actions"><button className="button secondary" onClick={()=>setNavigation(null)}>{t("Kal")}</button><button className="button secondary" onClick={()=>{const action=navigation;clearProjectDrafts();setScenarioDirty(false);setProjectDirty(false);setSpatialDirty(false);setEditorDirty(false);setCsvPreview(null);setEditing(null);setFormKey(k=>k+1);setNavigation(null);setTimeout(action,0)}}>{t("Vazgeç ve devam et")}</button><button className="button primary" disabled={busy||!!csvPreview} onClick={()=>{dispatchedSave.current='';setSavingNavigation(true);setNavigationAttempt(x=>x+1)}}>{t("Kaydet ve devam et")}</button></div><p className="small-note">Kayıt doğrulaması başarısızsa Kal ile formu düzeltin. CSV önizlemesini önce uygulayın veya vazgeçin.</p></Modal>}
    {editing && campus && <BuildingEditor building={editing} onDirtyChange={setEditorDirty} onClose={() => {const close=()=>{setEditing(null);setEditorDirty(false)};if(editorDirty&&Object.keys(readDraft('editor:'+editing.id,{})).length)guard(close);else close();}} onSave={async b => { await commit({ ...campus, buildings: campus.buildings.map(old => old.id === b.id ? b : old) }); }} />}
    {assumptions && <Modal title="Varsayımlar ve veri kaynağı" onClose={() => setAssumptions(false)}>{campus && data ? <><p className="synthetic-banner"><Icon name="info" size={18} />Sentetik örnek proje — sonuçlar model varsayımlarına dayanır.</p><h3>Veri kaynağı</h3><p>{campus.provenance.source}</p>{campus.pilot&&<><p>{campus.pilot.heating_independence}</p><p>{String(campus.pilot.weather.source)} · {String(campus.pilot.weather.year)} / {String(campus.pilot.weather.timezone)} / {String(campus.pilot.weather.resolution_hours)} saat · {String(campus.pilot.weather.license)}</p></>}<p>{campus.profile_settings.source} Dönem {data.profile_audit.start} → {data.profile_audit.end_exclusive} (hariç); {data.profile_audit.hour_count} saat · {campus.profile_settings.timezone}.</p><h3>Fiyat ve emisyon kayıtları</h3><p>{t("Elektrik")+" "}{n(campus.scenario.electricity_price_try_kwh, 2)} TL/kWh · doğalgaz {n(campus.scenario.heating_price_try_kwh, 2)} TL/kWh.<br />{campus.scenario.price_basis.reference_date} · {campus.scenario.price_basis.source}</p><p>{t("Elektrik")+" "}{n(campus.scenario.electricity_emission_kg_kwh, 3)} · doğalgaz {n(campus.scenario.gas_emission_kg_kwh, 3)} kg CO₂e/kWh.<br />{campus.scenario.emission_basis.reference_date} · {campus.scenario.emission_basis.source}</p><h3>Bina bazlı dönüşüm varsayımları</h3><div className="table-scroll"><table><thead><tr><th>{t("Bina")}</th><th>{t("Kazan verimi")}</th><th>İlgili ısı / azaltım</th><th>SCOP</th><th>{t("Pompa kapasitesi")}</th></tr></thead><tbody>{campus.buildings.map(b => <tr key={b.id}><td>{b.id}</td><td>%{n(b.retrofit.boiler_efficiency * 100)}</td><td>%{n(b.retrofit.insulation_relevant_heat_fraction * 100)} / %{n(b.retrofit.insulation_reduction_fraction * 100)}</td><td>{n(b.retrofit.heat_pump_scop, 2)}</td><td>{n(b.retrofit.heat_pump_capacity_kw_thermal)} kW termal</td></tr>)}</tbody></table></div><h3>Modelin sınırları</h3><ul><li>Isı pompası/kabuk paketleri ısıtma içindir. Pilot kat senaryosunda aydınlatma/program etkileri ayrıca hesaplanır; genel konut ve konfor modeli doğrulanmadı.</li><li>Bağımsız bağlantılar ayrı denetlenir; proje toplamı ortak trafo sınırı değildir.</li><li>SCOP mevsimsel eşdeğer olarak saatlere dağıtılır; sıcaklığa bağlı saatlik COP değildir.</li><li>Pompanın kapsamadığı veya kapasitesini aşan ısı mevcut doğalgaz kazanına gider. Kazan kapasitesi ayrıca kısıtlanmaz.</li><li>Yalıtım yalnız tanımlanan ilgili faydalı ısı payına uygulanır. Isıtma dışı gaz korunur.</li><li>Modellenen profilin sınırı karşılaması ölçülmüş şebeke uygunluğu veya kesin trafo yatırımı önleme iddiası değildir.</li><li>Basit geri ödeme enerji bedeli farkı ve ek bakım içerir; iskonto, ömür, finansman ve fiyat değişimi içermez.</li><li>Yatırım planı fizik ve MILP ile hesaplanır. Sentetik model ve ComStock tahmini ayrı deneysel sağlayıcılardır; saha doğruluğu kanıtı değildir. LLM yalnız hesapları açıklamak içindir; başarılı erişimi ayrıca doğrulanmalıdır.</li></ul>{campus.migration_notes.length > 0 && <details><summary>Kayıt dönüşüm notları</summary><ul>{campus.migration_notes.map(note => <li key={note}>{note}</li>)}</ul></details>}</> : <p>Veri kaynağı bilgisi için önce API bağlantısını kurun.</p>}</Modal>}
  </div>;
}

function Metric({ title, value, unit, note, icon }: { title: string; value: string; unit: string; note: string; icon: 'bolt' | 'building' | 'sliders' | 'grid' }) {
  return <section className="metric-card"><div className="metric-title">{title}<Icon name={icon} size={18} /></div><div className="metric-value">{value}<span>{t(unit)}</span></div><p>{note}</p></section>;
}


