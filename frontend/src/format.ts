import type { CalculationResult, PackageName } from './types';
import {getLanguage} from './preferences.ts';
import {t} from './i18n.ts';

export const n = (value: number | null | undefined, digits = 1) => value == null || !Number.isFinite(value) ? '—' : new Intl.NumberFormat(getLanguage()==='en'?'en-GB':'tr-TR', { maximumFractionDigits: digits }).format(value);
export const money = (value: number | null | undefined) => `${n(value, 0)} TL`;
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'İşlem tamamlanamadı. Tekrar deneyin.';
export const packageNames: Record<PackageName, string> = { none: 'Müdahale yok', insulation: 'Yalıtım', heat_pump: 'Isı pompası', combined: 'Birleşik paket' };
export function solverLabel(result: CalculationResult) {
  if (result.status === 'optimal' && result.solver.optimality_proven) return t('Optimum çözüm bulundu');
  if (result.status === 'feasible_limit') return result.solver.status_code === 1 ? t('Süre sınırında uygun çözüm bulundu') : t('Uygun çözüm bulundu; optimum kanıtlanmadı');
  if (result.status === 'limit_no_solution') return t('Süre sınırında çözüm bulunamadı');
  if (result.status === 'infeasible') return t('Çözüm bulunamadı');
  return t('Hesaplama doğrulanamadı');
}

export const interventionNames:Record<string,string>={roof:'Çatı',insulation:'Kabuk',lighting:'Aydınlatma',schedule:'Program',heat_pump:'Isı pompası'};
export function planName(p:import('./types').PackageResult){
 const decisions=p.interventions?.filter(d=>d.state!=='excluded');
 if(p.interventions?.length)return decisions?.map(d=>t(interventionNames[d.kind])+(d.state==='applied'?(getLanguage()==='en'?' (existing)':' (mevcut)'):'')).join(' + ')||t('Yeni müdahale yok');
 const spatial=(p.spatial_interventions??[]).map(k=>t(interventionNames[k]??k));
 return [p.package==='none'&&spatial.length?'':t(packageNames[p.package]),...spatial].filter(Boolean).join(' + ');
}
