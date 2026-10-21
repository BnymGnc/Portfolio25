import { useEffect, useRef, useState, type FormEvent } from 'react';
import type { Building, Campus, Scenario } from './types';
import { Icon, retrofitFields } from './visuals';
import { errorMessage as message } from './format';
import {useDraft,storeDraft,readDraft,clearDraft} from './drafts';

export function BuildingEditor({ building, onClose, onSave, onDirtyChange }: { onDirtyChange: (dirty: boolean) => void; building: Building; onClose: () => void; onSave: (b: Building) => Promise<void> }) {
  const dialog = useRef<HTMLDialogElement>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState('');
  useEffect(() => { dialog.current?.showModal();const saved=readDraft<Record<string,string>>('editor:'+building.id,{});
    const form=dialog.current?.querySelector('form');if(form)for(const [key,value] of Object.entries(saved)){
      const el=form.elements.namedItem(key);if(el instanceof HTMLInputElement||el instanceof HTMLSelectElement){if(el instanceof HTMLInputElement&&el.type==='checkbox')el.checked=value==='on';else el.value=value;}}
    if(Object.keys(saved).length)onDirtyChange(true);
  }, []);
  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    const values = new FormData(event.currentTarget);
    setSaving(true); setError('');
    try {
      await onSave({ ...building, name: String(values.get('name')).trim(), use_type: values.get('use_type') as Building['use_type'],
        ...Object.fromEntries(['area_m2', 'year_built', 'electricity_kwh_year', 'heating_kwh_year', 'non_heating_gas_kwh_year', 'peak_electric_kw', 'connection_limit_kw'].map(key => [key, Number(values.get(key))])),
        heating_system:values.get('heating_system') as Building['heating_system'],heat_distribution:values.get('heat_distribution') as Building['heat_distribution'],
        insulation_allowed:values.get('insulation_allowed')==='on',system_source:String(values.get('system_source')),
        retrofit: { ...building.retrofit, ...Object.fromEntries(retrofitFields.map(f => [f.key, Number(values.get(`retrofit.${f.key}`))])),
          reference_date: String(values.get('retrofit.reference_date')), source: String(values.get('retrofit.source')) } });
      clearDraft('editor:'+building.id);onClose();
    } catch (e) { setError(message(e)); }
    finally { setSaving(false); }
  }
  const fields: { key: keyof Building; label: string; min: number; max: number; step?: string }[] = [
    { key: 'area_m2', label: 'Brüt alan (m²)', min: 0.01, max: 1000000, step: 'any' },
    { key: 'year_built', label: 'Yapım yılı', min: 1800, max: 2100 },
    { key: 'electricity_kwh_year', label: 'Yıllık elektrik (kWh/yıl)', min: 0, max: 1000000000, step: 'any' },
    { key: 'heating_kwh_year', label: 'Isıtma doğalgazı (kWh/yıl)', min: 0, max: 1000000000, step: 'any' },
    { key: 'non_heating_gas_kwh_year', label: 'Isıtma dışı doğalgaz (kWh/yıl)', min: 0, max: 1000000000, step: 'any' },
    { key: 'connection_limit_kw', label: 'Bina bağlantı sınırı (kW)', min: 0.01, max: 1000000, step: 'any' },
    { key: 'peak_electric_kw', label: 'Eski referans pik (hesapta kullanılmaz, kW)', min: 0, max: 1000000, step: 'any' },
  ];
  return <dialog ref={dialog} onCancel={e => { if (saving) e.preventDefault(); else onClose(); }} aria-labelledby="editor-title">
    <form onSubmit={submit} onChange={e => {onDirtyChange(true);const f=e.currentTarget;const values=Object.fromEntries(new FormData(f).entries()) as Record<string,string>;values.insulation_allowed=(f.elements.namedItem('insulation_allowed') as HTMLInputElement).checked?'on':'off';storeDraft('editor:'+building.id,values)}}>
      <div className="dialog-top"><div><span className="eyebrow">BİNA ENVANTERİ / {building.id}</span><h2 id="editor-title">Bina bilgilerini düzenle</h2></div><button type="button" className="icon-button" aria-label="Pencereyi kapat" onClick={onClose} disabled={saving}><Icon name="close" /></button></div>
      <p className="small-note">Bu kayıtta yapılan değişiklikler sentetik örnek veri olarak saklanır.</p>
      <label>Bina adı<input name="name" required maxLength={100} pattern=".*\S.*" defaultValue={building.name} autoFocus /></label>
      <div className="form-grid"><label>Kullanım türü<select name="use_type" defaultValue={building.use_type}>{['Eğitim', 'Araştırma', 'İdari', 'Sosyal', 'Konaklama','Konut','Ofis','Otel'].map(use => <option key={use}>{use}</option>)}</select></label>
        {fields.map(field => <label key={field.key}>{field.label}<input type="number" name={field.key} required min={field.min} max={field.max} step={field.step || '1'} defaultValue={building[field.key] as number} /></label>)}
      </div>
      <details className="system-fields"><summary>Mevcut sistem ve müdahale uygunluğu · yalnız ısıtma</summary><label>Mevcut ısıtma sistemi<select name="heating_system" defaultValue={building.heating_system}><option value="gas_boiler">Doğalgaz kazanı</option><option value="electric_resistance">Elektrik dirençli ısıtma · dönüşüm modeli yok</option><option value="existing_heat_pump">Mevcut ısı pompası · dönüşüm modeli yok</option><option value="other">Diğer · dönüşüm modeli yok</option></select></label><label>Isı dağıtımı<select name="heat_distribution" defaultValue={building.heat_distribution}><option value="hydronic_assumed">Uygun sulu dağıtım · sentetik varsayım</option><option value="low_temperature_water">Düşük sıcaklıklı sulu dağıtım</option><option value="high_temperature_water">Yüksek sıcaklıklı dağıtım · uyarlama modeli eksik</option><option value="none">Dağıtım yok</option><option value="unknown">Bilinmiyor</option></select></label><label className="project-checkbox"><input type="checkbox" name="insulation_allowed" defaultChecked={building.insulation_allowed}/>Yalıtım müdahalesi uygun</label><label>Sistem varsayım kaynağı<input name="system_source" required maxLength={500} defaultValue={building.system_source}/></label><p className="small-note">Uyumsuz paketler filtrelenir. Isıtma modeli gaz kazanı girişinden türetilir; diğer sistemlerdeki elektrik ısıtması ayrıştırılmaz. Soğutma cihazı dönüşümü yok; pilotta sıcak su ayrı tüketim olarak korunur.</p></details>
      <details className="retrofit-fields"><summary>Dönüşüm varsayımları — sentetik, düzenlenebilir</summary>
        <p className="small-note">Doğalgaz kWh enerji içeriğidir. Yalıtım yalnızca ilgili faydalı ısı payını azaltır. Pompanın karşılamadığı ısı mevcut kazanla karşılanır.</p>
        <div className="form-grid">{retrofitFields.map(f => <label key={f.key}>{f.label}<input type="number" required name={`retrofit.${f.key}`} min={f.min} max={f.max} step="any" defaultValue={building.retrofit[f.key]} /></label>)}</div>
        <label>Varsayım tarihi<input type="date" name="retrofit.reference_date" required defaultValue={building.retrofit.reference_date} /></label>
        <label>Varsayım kaynağı<input name="retrofit.source" required maxLength={500} defaultValue={building.retrofit.source} /></label>
      </details>
      {error && <p role="alert" className="error-box">{error}</p>}
      <div className="dialog-actions"><button type="button" className="button secondary" disabled={saving} onClick={onClose}>Vazgeç</button><button className="button primary" disabled={saving}>{saving ? 'Kaydediliyor…' : 'Değişiklikleri kaydet'}<Icon name="check" size={17} /></button></div>
    </form>
  </dialog>;
}

export function ScenarioForm({ campus, disabled, onSave, onDirtyChange, onDraftChange }: { campus: Campus; disabled: boolean; onSave: (s: Scenario) => Promise<void>; onDirtyChange: (dirty: boolean) => void; onDraftChange: (scenario: Scenario) => void }) {
  const [draft, setDraft] = useDraft<Scenario>('scenario',campus.scenario);
  const [error, setError] = useState('');
  const dirty = JSON.stringify(draft) !== JSON.stringify(campus.scenario);
  const previousScenario=useRef(campus.scenario);
  useEffect(()=>{const previous=previousScenario.current;setDraft(value=>JSON.stringify(value)===JSON.stringify(previous)?campus.scenario:value);previousScenario.current=campus.scenario;},[campus.scenario]);
  useEffect(() => { onDirtyChange(dirty); }, [dirty, onDirtyChange]);
  useEffect(() => { onDraftChange(draft); }, [draft, onDraftChange]);
  useEffect(() => () => onDirtyChange(false), [onDirtyChange]);
  // A building save preserves this draft. A successful scenario save makes it clean.
  async function submit(event: FormEvent) {
    event.preventDefault(); setError('');
    try { await onSave(draft); } catch (e) { setError(message(e)); }
  }
  function field(key: Exclude<keyof Scenario, 'price_basis' | 'emission_basis'>, label: string, unit: string, min: number, max: number, step = 'any') {
    return <label>{label}<div className="input-unit"><input type="number" required min={min} max={max} step={step} value={Number.isNaN(draft[key]) ? '' : draft[key]} onChange={e => setDraft({ ...draft, [key]: e.target.value === '' ? NaN : Number(e.target.value) })} name={key} /><span>{unit}</span></div></label>;
  }
  return <section className="panel scenario-panel" id="scenario"><div className="panel-heading"><div><span className="eyebrow">SENARYO GİRDİLERİ</span><h2>Planlama çerçevesi</h2></div><span className="square-icon"><Icon name="sliders" /></span></div>
    <p className="section-note">Yatırım sınırlarını belirleyin ve hesaplamadan önce girdileri kaydedin.</p>
    <form onSubmit={submit}>
      {field('budget_try', 'Toplam yatırım bütçesi', '₺', 0, 1000000000000)}
      <div className="form-grid">{field('savings_target_pct', 'Tasarruf hedefi', '%', 0, 100)}{campus.connection_groups.length===1&&field('electric_capacity_kw', 'Tek bağlantı grubunun kapasitesi', 'kW', 0.01, 10000000)}</div>
      {campus.connection_groups.length>1&&<p className="small-note">{campus.connection_groups.length} bağımsız bağlantı grubu var. Kapasiteleri üstteki proje bölümünden düzenleyin; proje geneline ortak trafo sınırı uygulanmaz.</p>}
      <details><summary>Fiyat ve emisyon varsayımları</summary><div className="form-grid">{field('electricity_price_try_kwh', 'Elektrik birim bedeli', '₺/kWh', 0, 1000)}{field('heating_price_try_kwh', 'Doğalgaz birim bedeli', '₺/kWh', 0, 1000)}{field('electricity_emission_kg_kwh', 'Elektrik emisyonu', 'kg/kWh', 0, 10)}{field('gas_emission_kg_kwh', 'Doğalgaz emisyonu', 'kg/kWh', 0, 10)}</div>
        {(['price_basis', 'emission_basis'] as const).map(key => <div key={key} className="reference-fields"><label>{key === 'price_basis' ? 'Fiyat' : 'Emisyon'} varsayım tarihi<input type="date" required value={draft[key].reference_date} onChange={e => setDraft({ ...draft, [key]: { ...draft[key], reference_date: e.target.value } })} /></label><label>Kaynak<input required maxLength={500} value={draft[key].source} onChange={e => setDraft({ ...draft, [key]: { ...draft[key], source: e.target.value } })} /></label></div>)}
        <p className="small-note">Örnek sabit değerler; resmî güncel tarife veya emisyon faktörü değildir. Birim: kg CO₂e/kWh.</p></details>
      {error && <p className="error-box" role="alert">{error}</p>}
      <button className="button primary full" disabled={disabled || !dirty}>{disabled ? 'Kaydediliyor…' : dirty ? 'Girdileri kaydet' : 'Girdiler kayıtlı'}<Icon name={dirty ? 'arrow' : 'check'} size={17} /></button>
      <p className="form-footnote">{dirty ? 'Kaydedilmemiş değişiklikler var.' : 'Backend’de kayıtlı senaryo · TRY / kW'}</p>
    </form>
  </section>;
}

