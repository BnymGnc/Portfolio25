import {t} from './i18n';
import PanelBoundary from './PanelBoundary';
import {planName} from './format';
import { useEffect, useState } from 'react';
import { loadPackages } from './api';
import { errorMessage, money, n, packageNames } from './format';
import type { Building, BuildingPackages, CalculationResult } from './types';
import SpatialDetail from './SpatialDetail';
import SyntheticPrediction from './SyntheticPrediction';
import type {CalculationContext} from './types';

export default function BuildingDetail({ context,disabled=false,building, revision, result, onEdit,onSpatialSave,onSpatialDirty,initialTab='floors' }: {
  context?:CalculationContext;disabled?:boolean;building: Building; revision: number; result: CalculationResult | null;
  onEdit: () => void;
  onSpatialSave:(b:Building)=>Promise<void>;onSpatialDirty:(dirty:boolean)=>void;
  initialTab?:'floors'|'packages'|'ml';
}) {
  const [data, setData] = useState<BuildingPackages | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [tab,setTab]=useState(initialTab);
  useEffect(()=>{setTab(initialTab)},[building.id,initialTab]);
  useEffect(() => {
    let alive = true; setData(null); setError('');
    loadPackages(building.id).then(value => {
      if (value.input_revision !== revision || value.building_id !== building.id || !value.packages.length) throw new Error('Paketler güncel bina kaydıyla eşleşmiyor. Veriyi yenileyin.');
      if (alive) setData(value);
    }).catch(e => { if (alive) setError(errorMessage(e)); });
    return () => { alive = false; };
  }, [building.id, revision, retry]);
  const selected = result?.selected_packages.find(p => p.building_id === building.id);
  const highestSaving = data?.packages.reduce((best, p) => p.energy_savings_kwh_year > best.energy_savings_kwh_year ? p : best);
  const overLimit = data?.packages.filter(p => p.electric_peak_kw > building.connection_limit_kw + 1e-6);
  return <div className="building-layout">
    <div className="detail-content">
      <div className="mini-metrics"><div><span>{t("Elektrik")}</span><strong>{n(building.electricity_kwh_year, 0)} <small>{t("kWh/yıl")}</small></strong></div><div><span>{t("Isıtma doğalgazı")}</span><strong>{n(building.heating_kwh_year, 0)} <small>{t("kWh/yıl")}</small></strong></div><div><span>{t("Diğer doğalgaz")}</span><strong>{n(building.non_heating_gas_kwh_year, 0)} <small>{t("kWh/yıl")}</small></strong></div><div><span>{t("Bina bağlantı sınırı")}</span><strong>{n(building.connection_limit_kw)} <small>kW</small></strong></div></div>
      <nav className="detail-sections" aria-label={t('Bina detay bölümleri')}>{([{id:'floors',label:'Katlar ve kullanım'},{id:'packages',label:'Yatırım seçenekleri'},{id:'ml',label:'ML / fizik karşılaştırması'}] as const).map(item=><button key={item.id} id={'detail-tab-'+item.id} aria-pressed={tab===item.id} aria-controls={'detail-view-'+item.id} className={tab===item.id?'active':''} onClick={()=>setTab(item.id)}>{t(item.label)}</button>)}</nav>
      <div id="detail-view-floors" hidden={tab!=='floors'}><SpatialDetail key={'spatial:'+building.id} building={building} revision={revision} onSave={onSpatialSave} onDirty={onSpatialDirty}/></div><div id="detail-view-packages" hidden={tab!=='packages'}><section id="building-packages" className="panel package-panel"><div className="section-heading"><div><span className="eyebrow">{t("HESAPLANMIŞ ALTERNATİFLER")}</span><h2>{t("Uygun paketlerin bina üzerindeki etkisi")}</h2><p className="section-note">{t("Aynı kayıt ve tarifelerle API’de hesaplanır. Her satır tam bir müdahale kombinasyonudur. Bina sınırını karşılaması, projenin ortak bütçe ve bağlantılarına da uygun olduğu anlamına gelmez.")}</p></div></div>
        {error ? <div className="error-box" role="alert">{error}<button className="button secondary" onClick={() => setRetry(v => v + 1)}>{t("Tekrar dene")}</button></div> : !data ? <div className="loading-state" role="status">{t("Paketler hesaplanıyor…")}</div> : <div className="table-scroll"><table className="package-table"><thead><tr><th>{t("Paket")}</th><th>{t("Yatırım")}</th><th>{t("Enerji tasarrufu")}</th><th>{t("Net tasarruf")}</th><th>{t("Elektrik piki")}</th><th>{t("Bina bağlantısı")}</th><th>{t("Geri ödeme")}</th></tr></thead><tbody>{data.packages.map(p => <tr key={p.candidate_id??p.package} className={(selected?.candidate_id??selected?.package) === (p.candidate_id??p.package) ? 'selected-row' : ''}><td><strong>{planName(p)}</strong>{(selected?.candidate_id??selected?.package) === (p.candidate_id??p.package) && <small className="selected-note">{t("Güncel planda seçildi")}</small>}</td><td>{money(p.investment_try)}</td><td>{n(p.energy_savings_kwh_year, 0)}<small>{t("kWh/yıl")}</small></td><td className={p.net_savings_try_year < 0 ? 'negative-value' : ''}>{money(p.net_savings_try_year)}<small>{t("/ yıl")}</small></td><td>{n(p.electric_peak_kw)} kW</td><td><span className={`pill ${p.electric_peak_kw <= building.connection_limit_kw + 1e-6 ? 'green' : 'red'}`}>{p.electric_peak_kw <= building.connection_limit_kw + 1e-6 ? t("Sınır içinde") : t("Sınırı aşıyor")}</span></td><td>{p.simple_payback_years === null ? '—' : `${n(p.simple_payback_years)} yıl`}</td></tr>)}</tbody></table></div>}
      {data?.excluded_packages.length? <div className="exclusion-list"><h3>{t("Uygun olmadığı için filtrelenen paketler")}</h3>{data.excluded_packages.map(p=><p key={p.package}><strong>{packageNames[p.package]}:</strong> {p.reason}</p>)}<p>{building.interventions==null?'Eski kat seçimleri zorunlu sabit yatırım olarak korunur.':'Tam müdahale kombinasyonları karar durumlarına göre hesaplanır.'}{" "+t("Soğutma cihazı dönüşümü modellenmez.")}</p></div>:null}</section>
      {selected && <section className="panel contribution-panel"><span className="eyebrow">SEÇİLEN PAKETİN HESAPLANMIŞ KATKISI</span><h3>{planName(selected)}</h3><p>{money(selected.investment_try)} yatırım karşılığında yıllık {n(selected.energy_savings_kwh_year, 0)} kWh nihai enerji tasarrufu ve {money(selected.net_savings_try_year)} net ekonomik fark hesaplanıyor. Bina piki {n(selected.electric_peak_kw)} kW; bağlantı sınırı {n(selected.connection_limit_kw)} kW.</p>{highestSaving && <p className="small-note">Bina alternatifleri içinde en yüksek hesaplanan enerji tasarrufu: {planName(highestSaving)}, {n(highestSaving.energy_savings_kwh_year, 0)} kWh/yıl; {money(highestSaving.investment_try)} yatırım; {n(highestSaving.electric_peak_kw)} kW pik. {(highestSaving.candidate_id??highestSaving.package) !== (selected.candidate_id??selected.package) && `Seçilen pakete göre ${money(highestSaving.investment_try - selected.investment_try)} yatırım ve ${n(highestSaving.energy_savings_kwh_year - selected.energy_savings_kwh_year, 0)} kWh/yıl tasarruf farkı var.`}</p>}{overLimit && overLimit.length > 0 && <p className="small-note">Bina bağlantı sınırını aşan seçenekler: {overLimit.map(p => `${planName(p)} (${n(p.electric_peak_kw)} kW)`).join(', ')}. Bu seçenekler bu bağlantı sınırı altında seçilemez.</p>}<p className="small-note">{result?.mode === 'A' ? 'Mod A projenin toplam enerji tasarrufunu en yüksek yapar.' : 'Mod B projenin hedefini en düşük toplam yatırımla karşılar.'} Paketler ortak bütçe ve saatlik kapasite altında birlikte seçilir; bu tablo alternatiflerin sayısal etkilerini açıklar.</p></section>}
      </div>
      <div id="detail-view-ml" hidden={tab!=='ml'}><PanelBoundary><SyntheticPrediction context={context} buildingId={building.id} disabled={disabled}/></PanelBoundary></div>
      <details className="panel building-assumptions"><summary>{t("Bu binada kullanılan varsayımlar ve kaynak")}</summary><div className="assumption-values"><span>{t("Kazan verimi")+" "}<b>{n(building.retrofit.boiler_efficiency * 100)}%</b></span><span>{t("Yalıtımla ilgili ısı")+" "}<b>{n(building.retrofit.insulation_relevant_heat_fraction * 100)}%</b></span><span>{t("İlgili payda azaltım")+" "}<b>{n(building.retrofit.insulation_reduction_fraction * 100)}%</b></span><span>{t("Mevsimsel SCOP")+" "}<b>{n(building.retrofit.heat_pump_scop, 2)}</b></span><span>{t("Pompa kapasitesi")+" "}<b>{n(building.retrofit.heat_pump_capacity_kw_thermal)} kW termal</b></span><span>{t("Pompa kapsamı")+" "}<b>{n(building.retrofit.heat_pump_coverage_fraction * 100)}%</b></span></div><p className="small-note">{building.retrofit.reference_date} · {building.retrofit.source}</p><button className="button secondary" onClick={onEdit}>{t("Varsayımları düzenle")}</button></details>
    </div>
  </div>;
}
