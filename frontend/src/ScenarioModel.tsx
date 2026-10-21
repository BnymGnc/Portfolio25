import {t} from './i18n';
import { useState } from 'react';
import type { CampusResponse, CalculationResult, PackageName } from './types';
import { CampusMap, Icon } from './visuals';
import { money, n, packageNames,planName } from './format';

export default function ScenarioModel({ data, result, onBuilding, selectedId, onSelect }: { data: CampusResponse; result: CalculationResult | null; onBuilding: (id: string) => void; selectedId?:string; onSelect:(id:string)=>void }) {
  const [mode,setMode]=useState<'before'|'after'>('before');
  const selected=selectedId;
  const available=!!result?.after && result.input_revision===data.campus.revision && result.selected_packages.length===data.campus.buildings.length;
  const showingAfter=mode==='after' && available;
  const packages: Partial<Record<string,PackageName>>=showingAfter ? Object.fromEntries(result!.selected_packages.map(p=>[p.building_id,p.package])) : Object.fromEntries((data.baseline_packages??[]).map(p=>[p.building_id,p.package]));
  const building=data.campus.buildings.find(b=>b.id===selected);
  const plan=available ? result?.selected_packages.find(p=>p.building_id===selected) : undefined;
  const baseline=data.baseline_packages?.find(b=>b.building_id===selected);const before=baseline?.electric_peak_kw??data.profile_audit.buildings.find(b=>b.building_id===selected)?.electric_peak_kw;
  return <section className="panel scenario-model">
    <div className="section-heading"><div><span className="eyebrow">{t("ŞEMATİK / SENTETİK ÖRNEK")}</span><h2>{data.campus.id==='campus-demo-25'?t("Kampüs senaryo modeli"):t("Proje senaryo modeli")}</h2><p className="section-note">{t("Gerçek koordinat veya canlı sensör verisi içermez.")}</p></div><div className="model-toggle" role="group" aria-label={t("Senaryo modelinde gösterilen durum")}><button data-mode="before" aria-pressed={!showingAfter} onClick={()=>setMode('before')}>{t("Önce")}</button><button data-mode="after" aria-pressed={showingAfter} disabled={!available} onClick={()=>setMode('after')}>{t("Sonra")}</button></div></div>
    {!available && <p className="small-note model-help">{t("Sonra görünümü için güncel bir yatırım planı hesaplayın. Mevcut durum gösteriliyor.")}</p>}
    <CampusMap buildings={data.campus.buildings} packages={packages} extras={Object.fromEntries(data.campus.buildings.map(b=>[b.id,(showingAfter?result?.selected_packages.find(p=>p.building_id===b.id):data.baseline_packages?.find(p=>p.building_id===b.id))?.interventions?.filter(d=>d.state!=='excluded'&&['roof','lighting','schedule'].includes(d.kind)).map(d=>({roof:'Ç',lighting:'A',schedule:'P'}[d.kind as 'roof'|'lighting'|'schedule']))??[]]))} selectedId={selected ?? undefined} onSelect={b=>onSelect(b.id)} />
    <div className="model-legend"><span>{t("Isıtma renkleri; Ç: çatı / A: aydınlatma / P: program.")}</span>{(['none','insulation','heat_pump','combined'] as const).map(p=><span key={p}><i className={`package-swatch ${p}`} />{t(packageNames[p])}</span>)}</div>
    <p className="small-note model-help">{showingAfter ? `Mod ${result!.mode} · hesap r${result!.input_revision}. Renkler seçilen paketleri gösterir.` : `Mevcut durum · kayıt r${data.campus.revision}. Uygulanmış müdahaleler dahildir; yeni yatırımlar bu görünümde yer almaz.`}</p>
    {building ? <div className="model-building-detail"><div className="model-detail-title"><h3>{building.id} · {building.name}</h3><button className="text-button" onClick={()=>onBuilding(building.id)}>{t("Paketleri karşılaştır")+" "}<Icon name="arrow" size={15} /></button></div>{plan && showingAfter ? <><p>Güncel plandaki paket: <strong>{planName(plan)}</strong></p><dl><div><dt>{t("Yatırım")}</dt><dd data-value={plan.investment_try} data-testid="map-investment">{money(plan.investment_try)}</dd></div><div><dt>{t("Yıllık enerji tasarrufu")}</dt><dd data-value={plan.energy_savings_kwh_year} data-testid="map-savings">{n(plan.energy_savings_kwh_year,0)} kWh</dd></div><div><dt>{t("Bina elektrik piki")}</dt><dd>{n(before)} → {n(plan.electric_peak_kw)} kW</dd></div><div><dt>{t("Pik yük değişimi")}</dt><dd data-value={before == null ? undefined : plan.electric_peak_kw-before} data-testid="map-peak-delta">{before==null ? '—' : `${plan.electric_peak_kw-before>0 ? '+' : ''}${n(plan.electric_peak_kw-before)} kW`}</dd></div></dl><p className="small-note">{t("Bu değerler binanın pikleridir; proje toplam piki aynı saatlerdeki bütün bina yüklerinden ayrıca hesaplanır.")}</p></> : <p className="small-note">Mevcut bina piki {n(before)} kW; bağlantı sınırı {n(building.connection_limit_kw)} kW. Yatırım ve tasarruf için güncel plan gereklidir.</p>}</div> : <div className="model-placeholder">{t("Bir binaya tıklayarak yatırım, enerji tasarrufu ve pik yük değişimini inceleyin.")}</div>}
  </section>;
}
