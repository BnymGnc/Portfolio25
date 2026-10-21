import {t} from './i18n';
import type { ReactNode } from 'react';
import type { Building, RetrofitAssumptions, PackageName } from './types';

export type IconName = 'grid' | 'building' | 'sliders' | 'arrow' | 'download' | 'bolt' | 'leaf' | 'close' | 'info' | 'edit' | 'check';
export const retrofitFields: { key: Exclude<keyof RetrofitAssumptions, 'source' | 'reference_date'>; label: string; min: number; max: number }[] = [
  { key: 'boiler_efficiency', label: 'Kazan verimi (0–1)', min: 0.01, max: 1 },
  { key: 'insulation_relevant_heat_fraction', label: 'Yalıtımla ilgili ısı payı (0–1)', min: 0, max: 1 },
  { key: 'insulation_reduction_fraction', label: 'İlgili ısıda yalıtım azaltımı (0–1)', min: 0, max: 1 },
  { key: 'heat_pump_scop', label: 'Mevsimsel SCOP', min: 1, max: 10 },
  { key: 'heat_pump_coverage_fraction', label: 'Pompanın kapsayabildiği ısı payı (0–1)', min: 0, max: 1 },
  { key: 'heat_pump_capacity_kw_thermal', label: 'Pompa ısı kapasitesi (kW termal)', min: 0, max: 1000000 },
  { key: 'insulation_cost_try_m2', label: 'Yalıtım yatırımı (TL/m² brüt alan)', min: 0, max: 100000 },
  { key: 'heat_pump_cost_try_kw', label: 'Pompa yatırımı (TL/kW termal)', min: 0, max: 1000000 },
  { key: 'heat_pump_fixed_cost_try', label: 'Pompa sabit kurulum bedeli (TL)', min: 0, max: 1000000000 },
  { key: 'annual_maintenance_fraction', label: 'Ek yıllık bakım / yatırım (0–1)', min: 0, max: 1 },
];

export function Icon({ name, size = 20 }: { name: IconName; size?: number }) {
  const paths: Record<IconName, ReactNode> = {
    grid: <><rect x="3" y="3" width="7" height="7" rx="1" /><rect x="14" y="3" width="7" height="7" rx="1" /><rect x="3" y="14" width="7" height="7" rx="1" /><rect x="14" y="14" width="7" height="7" rx="1" /></>,
    building: <><path d="M4 21V7l8-4 8 4v14M2 21h20M9 21v-5h6v5M8 8h1m6 0h1M8 12h1m6 0h1" /></>,
    sliders: <><path d="M4 6h16M4 12h16M4 18h16" /><circle cx="8" cy="6" r="2" /><circle cx="16" cy="12" r="2" /><circle cx="10" cy="18" r="2" /></>,
    arrow: <path d="M5 12h14m-6-6 6 6-6 6" />,
    download: <path d="M12 3v12m-4-4 4 4 4-4M4 16v5h16v-5" />,
    bolt: <path d="m13 2-9 12h7l-1 8 10-13h-7l1-7Z" />,
    leaf: <><path d="M20 3C7 2 2 9 6 16c7 5 15-1 14-13ZM4 21 15 10" /></>,
    close: <path d="m6 6 12 12M6 18 18 6" />,
    info: <><circle cx="12" cy="12" r="9" /><path d="M12 11v6m0-10v1" /></>,
    edit: <><path d="m15 4 5 5M4 20l5-1L21 7l-5-5L4 14v6Z" /></>,
    check: <path d="m5 12 4 4L19 6" />,
  };
  return <svg width={size} height={size} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.6" strokeLinecap="round" strokeLinejoin="round" aria-hidden="true">{paths[name]}</svg>;
}

export function CampusMap({ buildings, onSelect, packages, selectedId,extras }: { buildings: Building[]; onSelect: (b: Building) => void; packages?: Partial<Record<string, PackageName>>; selectedId?: string;extras?:Record<string,string[]> }) {
  const positions = buildings.length===8 ? [[60, 48, 75, 42], [174, 38, 54, 36], [272, 50, 72, 42], [382, 46, 52, 38], [74, 149, 66, 46], [184, 146, 82, 44], [307, 148, 56, 48], [404, 142, 66, 57]] : buildings.map((_,i)=>[50+(i%4)*120,40+Math.floor(i/4)*80,75,44]);
  const mapHeight=Math.max(250,Math.ceil(buildings.length/4)*80+65);
  const colors = {none:{fill:'var(--map-none)',text:'var(--map-none-text)',stroke:'var(--border)'},insulation:{fill:'var(--warning-bg)',text:'var(--warning)',stroke:'var(--accent)'},heat_pump:{fill:'var(--info-bg)',text:'var(--info)',stroke:'var(--info)'},combined:{fill:'var(--primary)',text:'var(--on-primary)',stroke:'var(--primary)'}};
  return <div className="campus-map">
    <div className="map-caption"><span className="eyebrow">{t("BİNA YERLEŞİMİ")}</span><span>{t("Şematik gösterim")}</span></div>
    <svg viewBox={`0 0 530 ${mapHeight}`} role="group" aria-label="Şematik senaryo modeli; etkisini incelemek için bir bina seçin">
      <defs><pattern id="dots" width="14" height="14" patternUnits="userSpaceOnUse"><circle cx="1" cy="1" r="0.7" fill="var(--border)" /></pattern></defs>
      <rect width="530" height={mapHeight} fill="url(#dots)" />
      <path d="M10 118h510M155 14v220M287 14v220M386 14v220" stroke="var(--surface)" strokeWidth="15" />
      <path d="M10 118h510" stroke="var(--border)" strokeWidth="1" strokeDasharray="5 6" />
      {[[38, 44], [248, 28], [490, 84], [43, 180], [280, 213], [370, 210], [491, 211], [101, 220]].map(([cx, cy], i) => <g key={i}><circle cx={cx} cy={cy} r="9" fill="var(--surface-soft)" /><circle cx={cx - 2} cy={cy - 3} r="6" fill="var(--border)" /></g>)}
      {positions.map(([x, y, w, h], i) => { const color=colors[packages?.[buildings[i].id] ?? 'none']; return <g key={i} className="map-building" role="button" tabIndex={0} aria-label={`${buildings[i].name} etkisini incele`} onClick={() => onSelect(buildings[i])} onKeyDown={e => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); onSelect(buildings[i]); } }}>
        <title>{buildings[i].name}</title>
        {selectedId === buildings[i].id && <rect x={x-3} y={y-3} width={w+6} height={h+6} rx="6" fill="none" stroke="var(--focus)" strokeWidth="2" />}
        <rect x={x + 4} y={y + 5} width={w} height={h} rx="4" fill="var(--map-shadow)" />
        <rect x={x} y={y} width={w} height={h} rx="4" fill={color.fill} stroke={color.stroke} />
        <path d={`M${x + 9} ${y + 8}h${w - 18}v${h - 16}h-${w - 18}Z`} fill="none" stroke={i === 0 ? 'var(--border)' : 'var(--border)'} />
        <text x={x + w / 2} y={y + h / 2 + 4} textAnchor="middle" fill={color.text} fontSize="11" fontFamily="inherit" fontWeight="600">{buildings[i].id}</text><text x={x+w/2} y={y+h-3} textAnchor="middle" fontSize="9" fill={color.text}>{extras?.[buildings[i].id]?.join(" · ")}</text>
      </g>; })}
      <text x="22" y="242" fill="var(--muted)" fontSize="10">{t("Gerçek konum verisi içermez")}</text>
      <path d="m502 224 0-19m-4 5 4-5 4 5" stroke="var(--muted)" fill="none" /><text x="499" y="239" fontSize="9" fill="var(--muted)">K</text>
    </svg>
    <div className="map-bottom"><span><i className="dot green" />{buildings.length} örnek bina</span><span>{t("Binaları seçerek inceleyin")+" "}<Icon name="arrow" size={14} /></span></div>
  </div>;
}

