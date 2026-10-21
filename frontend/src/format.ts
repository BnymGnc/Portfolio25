import type { CalculationResult, PackageName } from './types';

export const n = (value: number | null | undefined, digits = 1) => value == null || !Number.isFinite(value) ? '—' : new Intl.NumberFormat('tr-TR', { maximumFractionDigits: digits }).format(value);
export const money = (value: number | null | undefined) => `${n(value, 0)} TL`;
export const errorMessage = (error: unknown) => error instanceof Error ? error.message : 'İşlem tamamlanamadı. Tekrar deneyin.';
export const packageNames: Record<PackageName, string> = { none: 'Müdahale yok', insulation: 'Yalıtım', heat_pump: 'Isı pompası', combined: 'Birleşik paket' };
export function solverLabel(result: CalculationResult) {
  if (result.status === 'optimal' && result.solver.optimality_proven) return 'Optimum çözüm bulundu';
  if (result.status === 'feasible_limit') return result.solver.status_code === 1 ? 'Süre sınırında uygun çözüm bulundu' : 'Uygun çözüm bulundu; optimum kanıtlanmadı';
  if (result.status === 'limit_no_solution') return 'Süre sınırında çözüm bulunamadı';
  if (result.status === 'infeasible') return 'Çözüm bulunamadı';
  return 'Hesaplama doğrulanamadı';
}

export function planName(p:import('./types').PackageResult){const names:Record<string,string>={roof:'Çatı',insulation:'Kabuk',lighting:'Aydınlatma',schedule:'Program',heat_pump:'Isı pompası'};return p.interventions?.length?p.interventions.map(d=>names[d.kind]+(d.state==='applied'?' (mevcut)':'')).join(' + '):packageNames[p.package];}
