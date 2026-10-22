import {sourceFields,sourceKind,sourceLabels} from './sources';
import {t,tr} from './i18n';
import type {CampusResponse} from './types';
import {Icon} from './visuals';
import {n} from './format';

export default function ProjectReadiness({data,onAssumptions,onBuilding,onScenario}:{data:CampusResponse;onBuilding:(id:string)=>void;onScenario:()=>void;onAssumptions:()=>void}){
 const {campus,profile_audit:audit,baseline}=data;
 const violations=baseline.capacity_checks.filter(c=>c.violation_hours>0);
 const unsupported=campus.buildings.filter(b=>b.heating_system!=='gas_boiler'||!['hydronic_assumed','low_temperature_water'].includes(b.heat_distribution));
 return <section className="panel readiness-card" aria-label={t("Veri ve doğrulama durumu")}>
  <span className="eyebrow">{t("HESABIN DAYANAĞI")}</span><h2>{t("Veri ve doğrulama")}</h2>
  <ul className="readiness-list">
   <li><Icon name={audit.all_consistent?'check':'info'} size={18}/><div><strong>{audit.all_consistent?t("Yıllık enerji ve saatlik profil tutarlı"):t("Saatlik profilin kontrol edilmesi gerekiyor")}</strong><p>{n(audit.hour_count,0)} {tr("hours","saat")} · {campus.profile_settings.year} · {audit.timezone}</p></div></li>
   <li className={violations.length?'readiness-warning':''}><Icon name={violations.length?'info':'check'} size={18}/><div><strong>{violations.length?`${violations.length} başlangıç bağlantı sınırı aşılıyor`:t("Başlangıç profili bağlantı sınırları içinde")}</strong><p>{campus.connection_groups.length} {tr("physical groups; building limits are checked separately. The profile is synthetic.","fiziksel grup; bina sınırları ayrıca denetlenir. Profil sentetiktir.")}</p></div></li>
  </ul>
  {unsupported.length>0&&<p className="readiness-warning">{unsupported.length} binada ısı pompası dönüşümüne uygun sistem varsayımı yok. Uygun olmayan seçenekler motor tarafından filtrelenir.</p>}
  <details className="readiness-next"><summary>Öncelikli girdilerin kaynakları</summary><p>Sayısal zorunlu alanlar kayıt sırasında doğrulanır. Kaynak doğrulaması ve saatlik ölçümler pilot hazırlığı içindir; sentetik denemeyi engellemez. Gerçek kampüs baseline'ı henüz bulunmuyor.</p><div className="table-scroll"><table><thead><tr><th>Bina</th>{sourceFields.map(([k,v])=><th key={k}>{v}</th>)}<th>Düzenle</th></tr></thead><tbody>{campus.buildings.map(b=><tr key={b.id}><td>{b.name}</td>{sourceFields.map(([k])=><td key={k}>{sourceLabels[sourceKind(b,k)]}</td>)}<td><button className="text-button" onClick={()=>onBuilding(b.id)}>Girdileri düzenle</button></td></tr>)}</tbody></table></div><p>Tarife: {sourceLabels[campus.scenario.price_basis.kind??'unspecified']} · {campus.scenario.price_basis.source}</p><button className="text-button" onClick={onScenario}>Tarifeleri ve bağlantı gruplarını düzenle</button></details>
  <details className="readiness-next"><summary>{t("Gerçek pilot için hangi veriler gerekli?")}</summary><ul><li>{t("Aynı yılın elektrik/gaz faturaları ve doğrulanmış brüt alan.")}</li><li>{t("Isıtma ile sıcak su/diğer gazın ayrımı; kazan ve dağıtım sistemi.")}</li><li>{t("Bağlantı grupları, sözleşme sınırları ve eşzamanlı saatlik sayaç kayıtları.")}</li><li>{t("Yalıtım, SCOP ve maliyetler için teknik inceleme/teklif.")}</li></ul></details>
  <button className="text-button" onClick={onAssumptions}>{t("Kaynak ve varsayımları incele")+" "}<Icon name="arrow" size={15}/></button>
 </section>;
}
