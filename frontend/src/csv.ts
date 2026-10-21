import type { Building, Campus, Scenario } from './types';

export function parseCSV(text: string): string[][] {
  const rows: string[][] = [];
  let row: string[] = [], cell = '', quoted = false, closed = false;
  const pushCell = () => { row.push(cell); cell = ''; closed = false; };
  const pushRow = () => { pushCell(); if (row.some(v => v.trim())) rows.push(row); row = []; };
  const source = text.replace(/^\uFEFF/, '');
  for (let i = 0; i < source.length; i++) {
    const c = source[i];
    if (quoted) {
      if (c === '"') { if (source[i + 1] === '"') { cell += '"'; i++; } else { quoted = false; closed = true; } }
      else cell += c;
    } else if (c === ',') pushCell();
    else if (c === '\n' || c === '\r') { if (c === '\r' && source[i + 1] === '\n') i++; pushRow(); }
    else if (c === '"' && !cell && !closed) quoted = true;
    else if (closed) { if (c !== ' ' && c !== '\t') throw new Error('CSV geçersiz: kapanan tırnaktan sonra beklenmeyen karakter var.'); }
    else { if (c === '"') throw new Error('CSV geçersiz: alan içindeki tırnaklar çift tırnakla kaçırılmalıdır.'); cell += c; }
  }
  if (quoted) throw new Error('CSV geçersiz: kapatılmamış tırnak var.');
  if (cell || row.length) pushRow();
  return rows;
}

export function campusFromCSV(text: string, current: Campus): Campus {
  const [headers, ...rows] = parseCSV(text);
  const required = ['id', 'name', 'use_type', 'area_m2', 'year_built', 'electricity_kwh_year', 'heating_kwh_year', 'peak_electric_kw', 'data_kind', 'source', 'seed', 'budget_try', 'savings_target_pct', 'electric_capacity_kw', 'electricity_price_try_kwh', 'heating_price_try_kwh'];
  if (!headers || required.some(key => !headers.includes(key))) throw new Error('CSV şablonu geçersiz. Uygulamanın CSV dışa aktarımını kullanın; virgül ayracı ve zorunlu sütunları koruyun.');
  if (new Set(headers).size !== headers.length) throw new Error('CSV geçersiz: yinelenen sütun adı var.');
  if (rows.length !== current.buildings.length) throw new Error(`CSV bu projenin ${current.buildings.length} binasını içermeli. Hiçbir değişiklik uygulanmadı.`);
  const records = rows.map((r, i) => { if (r.length !== headers.length) throw new Error(`CSV ${i + 2}. satırında sütun sayısı uyuşmuyor.`); return Object.fromEntries(headers.map((h, j) => [h, r[j]])); });
  if (new Set(records.map(r => r.id)).size !== current.buildings.length || records.some(r => !current.buildings.some(b => b.id === r.id))) throw new Error('CSV bina kimlikleri mevcut proje ile aynı ve benzersiz olmalı.');
  function numeric(row: Record<string, string>, field: string, min: number, max: number, fallback?: number) {
    if (row[field] === undefined && fallback !== undefined) return fallback;
    const raw = row[field]?.trim();
    if (!raw || !/^[+-]?(?:\d+\.?\d*|\.\d+)(?:[eE][+-]?\d+)?$/.test(raw)) throw new Error(`${row.id}: ${field} için noktalı ondalık biçiminde sayı bekleniyor.`);
    const value = Number(raw);
    if (!Number.isFinite(value) || value < min || value > max) throw new Error(`${row.id}: ${field} değeri ${min}–${max} aralığında olmalı.`);
    return value;
  }
  function metadata(row: Record<string, string>, key: string) {
    if (!row[key]) return {};
    try { const parsed = JSON.parse(row[key]); if (!parsed || typeof parsed !== 'object' || Array.isArray(parsed)) throw new Error(); return parsed; }
    catch { throw new Error(`${row.id}: ${key} geçerli bir JSON nesnesi değil.`); }
  }
  const scenarioFor = (r: Record<string, string>): Scenario => ({ ...current.scenario, ...metadata(r, 'valuation_assumptions_json'),
    budget_try: numeric(r, 'budget_try', 0, 1e12), savings_target_pct: numeric(r, 'savings_target_pct', 0, 100),
    electric_capacity_kw: numeric(r, 'electric_capacity_kw', Number.MIN_VALUE, 1e7),
    electricity_price_try_kwh: numeric(r, 'electricity_price_try_kwh', 0, 1000), heating_price_try_kwh: numeric(r, 'heating_price_try_kwh', 0, 1000) });
  const scenario = scenarioFor(records[0]);
  const profile = { ...current.profile_settings, ...metadata(records[0], 'profile_settings_json') };
  const project=metadata(records[0],'project_json');
  if(project.id&&project.id!==current.id)throw new Error('CSV başka bir projeye ait; önce ilgili projeyi seçin.');
  if (records.some(r => JSON.stringify(scenarioFor(r)) !== JSON.stringify(scenario) || JSON.stringify({ ...current.profile_settings, ...metadata(r, 'profile_settings_json') }) !== JSON.stringify(profile)||JSON.stringify(metadata(r,'project_json'))!==JSON.stringify(project))) throw new Error('CSV ortak senaryo/profil/proje değerleri bütün satırlarda aynı olmalı.');
  const buildings: Building[] = records.map(r => {
    const b = current.buildings.find(b => b.id === r.id)!;
    if (r.data_kind !== 'synthetic' || Number(r.seed) !== b.provenance.seed || r.source !== b.provenance.source) throw new Error(`${r.id}: bu içe aktarım yalnız mevcut sentetik örnek kaynağını kabul eder. Ölçülmüş veri içe aktarımı desteklenmiyor.`);
    const name = r.name.startsWith("'") && /^[=+\-@]/.test(r.name.slice(1).trimStart()) ? r.name.slice(1) : r.name;
    if (!name.trim() || name.length > 100) throw new Error(`${r.id}: bina adı 1–100 karakter olmalı.`);
    if (!['Eğitim', 'Araştırma', 'İdari', 'Sosyal', 'Konaklama','Konut','Ofis','Otel'].includes(r.use_type)) throw new Error(`${r.id}: kullanım türü tanınmadı.`);
    const year = numeric(r, 'year_built', 1800, 2100);
    if (!Number.isInteger(year)) throw new Error(`${r.id}: yapım yılı tamsayı olmalı.`);
    return { ...b, ...metadata(r,'system_assumptions_json'), interventions:r.interventions_json?JSON.parse(r.interventions_json):b.interventions,spatial:r.spatial_model_json?metadata(r,'spatial_model_json'):b.spatial,
      spatial_selection:r.spatial_selection_json?metadata(r,'spatial_selection_json'):b.spatial_selection, name, use_type: r.use_type as Building['use_type'], year_built: year,
      area_m2: numeric(r, 'area_m2', Number.MIN_VALUE, 1e6), electricity_kwh_year: numeric(r, 'electricity_kwh_year', 0, 1e9),
      heating_kwh_year: numeric(r, 'heating_kwh_year', 0, 1e9), peak_electric_kw: numeric(r, 'peak_electric_kw', 0, 1e6),
      non_heating_gas_kwh_year: numeric(r, 'non_heating_gas_kwh_year', 0, 1e9, b.non_heating_gas_kwh_year),
      connection_limit_kw: numeric(r, 'connection_limit_kw', Number.MIN_VALUE, 1e6, b.connection_limit_kw),
      retrofit: { ...b.retrofit, ...metadata(r, 'retrofit_assumptions_json') } };
  });
  // Server validates nested bounds/dates as well; no mutation until explicit Apply.
  return { ...current, name:project.name??current.name,connection_groups:project.connection_groups??current.connection_groups,
    sensitivity_settings:project.sensitivity_settings??current.sensitivity_settings,buildings, scenario, profile_settings: profile };
}
