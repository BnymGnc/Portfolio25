import type {CalculationResult} from './types';
import {n} from './format';
import {t,tr} from './i18n';

export default function ElectrificationImpact({result,onAssumptions}:{result:CalculationResult;onAssumptions:()=>void}){
 if(!result.after)return null;
 const before=result.baseline,after=result.after;
 const electricity=after.electricity_kwh_year-before.electricity_kwh_year;
 const gas=after.heating_kwh_year+after.non_heating_gas_kwh_year-before.heating_kwh_year-before.non_heating_gas_kwh_year;
 const carbon=after.emissions_kg_year-before.emissions_kg_year;
 const pumpHeat=result.selected_packages.reduce((sum,p)=>sum+p.heat_pump_heat_kwh_year,0);
 const backupHeat=result.selected_packages.reduce((sum,p)=>sum+p.backup_boiler_heat_kwh_year,0);
 const delta=(value:number,divisor=1)=>(value>0?'+':'')+n(value/divisor,1);
 return <section className="panel electrification-impact" aria-label={t('Isıtmanın elektrikleşmesi')}>
  <div className="section-heading"><div><span className="eyebrow">{t('ELEKTRİFİKASYON ETKİSİ')}</span><h2>{t('Gazdan elektriğe geçişin dengesi')}</h2><p className="section-note">{tr('Scenario minus baseline. Higher electricity use does not imply higher total energy or lower carbon automatically.','Senaryo eksi başlangıç. Elektrik artışı, toplam enerji artışı veya otomatik karbon azaltımı anlamına gelmez.')}</p></div></div>
  <dl className="impact-grid"><div><dt>{t('Yıllık elektrik değişimi')}</dt><dd data-metric="electricity" data-value={electricity}>{delta(electricity)} <span>kWh/{tr('year',t("yıl"))}</span></dd></div><div><dt>{t('Yıllık gaz değişimi')}</dt><dd data-metric="gas" data-value={gas}>{delta(gas)} <span>kWh/{tr('year',t("yıl"))}</span></dd></div><div><dt>{t('Modellenen karbon farkı')}</dt><dd data-metric="carbon" data-value={carbon} className={carbon>0?'negative-value':''}>{delta(carbon,1000)} <span>t CO₂e/{tr('year',t("yıl"))}</span></dd></div></dl>
  <div className="impact-heat"><p>{t('Isı pompasının karşıladığı faydalı ısı')}: <strong>{n(pumpHeat,0)} kWh/{tr('year',t("yıl"))}</strong></p><p>{t('Kalan kazan ısısı')}: <strong>{n(backupHeat,0)} kWh/{tr('year',t("yıl"))}</strong></p></div>
  <p className="impact-caveat">{tr('Useful heat is a service output, not an additional final-energy input. Carbon uses the scenario’s electricity/gas factors; lifecycle emissions and embodied materials are not assessed. The optimizer targets energy/cost, not minimum carbon.','Faydalı ısı hizmet çıktısıdır; nihai enerjiye tekrar eklenmez. Karbon, senaryonun elektrik/gaz faktörleriyle hesaplanır; yaşam döngüsü ve malzeme emisyonlarını kapsamaz. Motor enerji/yatırımı optimize eder; en düşük karbonu hedeflemez.')}</p>
  <button className="text-button" onClick={onAssumptions}>{t('Emisyon faktörlerini incele')}</button>
 </section>;
}
