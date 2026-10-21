import { useEffect, useState } from 'react';
import { loadProfiles } from './api';
import { errorMessage, n } from './format';
import { validateProfiles } from './profileData';
import {periodIndices} from './chartSelection';
import type { CampusProfiles, CampusResponse, CalculationResult } from './types';

export default function LoadChart({ data, result }: { data: CampusResponse; result: CalculationResult }) {
  const [profiles, setProfiles] = useState<CampusProfiles | null>(null);
  const [error, setError] = useState('');
  const [retry, setRetry] = useState(0);
  const [start, setStart] = useState(`${data.campus.profile_settings.year}-01-01`);
  const [days, setDays] = useState(7);
  const [hover, setHover] = useState(0);
  const [groupId,setGroupId]=useState('');const [tablePage,setTablePage]=useState(0);const [eventPage,setEventPage]=useState(0);
  useEffect(()=>{setTablePage(0);setEventPage(0);setHover(0)},[groupId,start,days,result.calculation_id]);
  useEffect(() => {
    let alive = true; setProfiles(null); setError('');
    loadProfiles(result.calculation_id).then(p => { const checked = validateProfiles(p, data, result); if (alive) setProfiles(checked); }).catch(e => { if (alive) setError(errorMessage(e)); });
    return () => { alive = false; };
  }, [data.campus.revision, result.mode, result.calculation_id, retry]);
  const year = data.campus.profile_settings.year;
  const group=profiles?.groups?.find(g=>g.id===groupId)??profiles?.groups?.[0];
  const indexes=profiles?periodIndices(profiles.timestamps,start,days):[];
  const before = indexes.map(i => (group?.before_kw??profiles!.before_kw)[i]);
  const after = indexes.map(i => (group?.after_kw??profiles!.after_kw!)[i]);
  const capacity = group?.capacity_kw??profiles?.capacity_kw ?? 0;
  const max = Math.max(capacity, ...before, ...after, 1) * 1.12;
  const annualAfter=group?.after_kw??profiles?.after_kw??[];const annualBefore=group?.before_kw??profiles?.before_kw??[];
  const annualPeak=annualAfter.reduce((best,v,i)=>v>(annualAfter[best]??-1)?i:best,0);
  const violations=profiles?.timestamps.flatMap((_,i)=>annualAfter[i]>capacity+1e-6||annualBefore[i]>capacity+1e-6?[i]:[])??[];
  const width = 1000, height = 300, left = 62, right = 22, top = 25, bottom = 45;
  const x = (i: number) => left + i / Math.max(1, indexes.length - 1) * (width - left - right);
  const y = (v: number) => top + (1 - v / max) * (height - top - bottom);
  const path = (values: number[]) => values.map((v, i) => `${i ? 'L' : 'M'}${x(i).toFixed(2)},${y(v).toFixed(2)}`).join(' ');
  const point = Math.min(hover, Math.max(0, indexes.length - 1));
  const dateLabel = (stamp: string) => new Intl.DateTimeFormat('tr-TR', { timeZone: profiles?.timezone ?? 'Europe/Istanbul', day: '2-digit', month: 'short', hour: '2-digit', minute: '2-digit' }).format(new Date(stamp));
  return <section className="panel chart-panel">
    <div className="section-heading"><div><span className="eyebrow">SAATLİK ELEKTRİK YÜKÜ</span><h2>Bağlantı grubunda önce ve sonra</h2><p className="section-note">Sentetik yıllık profilden seçilen dönem · Europe/Istanbul · 1 saat ortalama kW</p></div><span className="pill amber">Sentetik profil</span></div>
    <div className="chart-controls">{profiles?.groups&&<label>Bağlantı grubu<select aria-label="Bağlantı grubu grafiği" value={group?.id??""} onChange={e=>{setGroupId(e.target.value);setHover(0);}}>{profiles.groups.map(g=><option key={g.id} value={g.id}>{g.name}</option>)}</select></label>}<label>Başlangıç<input aria-label="Grafik başlangıç tarihi" type="date" min={`${year}-01-01`} max={`${year}-12-31`} required value={start} onChange={e => { if (e.target.value && e.target.value >= `${year}-01-01` && e.target.value <= `${year}-12-31`) { setStart(e.target.value); setHover(0); } }} /></label><label>Görüntülenecek dönem<select value={days} onChange={e => { setDays(Number(e.target.value));if(Number(e.target.value)===366)setStart(`${year}-01-01`);setTablePage(0); setHover(0); }}><option value={1}>1 gün</option><option value={7}>7 gün</option><option value={30}>30 gün</option><option value={366}>Yılın tamamı</option></select></label><button className="button secondary" disabled={!profiles||!result.after} onClick={() => { if(!result.after)return;setStart((result.after!.capacity_checks.find(c=>c.kind==="group"&&c.id===group?.id)?.peak_timestamp??result.after!.electric_peak_timestamp).slice(0,10)); setDays(7); setHover(0); }}>Pik haftasını göster</button></div>
    {error ? <div className="error-box" role="alert"><span>{error}</span><button className="button secondary" onClick={() => setRetry(r => r + 1)}>Profili yeniden yükle</button></div> : !profiles ? <div className="loading-state" role="status">Saatlik API profili yükleniyor…</div> : indexes.length === 0 ? <div className="error-box">Bu dönemde saatlik kayıt yok. Başlangıç tarihini değiştirin.</div> : <>
      <p className="evidence-note">Seçili dönem piki (sonra): {n(Math.max(...after))} kW · yıllık pik (sonra): {n(annualAfter[annualPeak])} kW ({dateLabel(profiles.timestamps[annualPeak])}). {violations.length} saatte önce veya sonra sınır aşımı var.</p>
      <label>Pik / aşım saatini seç<select aria-label="Pik ve aşım saati" value="" onChange={e=>{if(e.target.value==='')return;const i=Number(e.target.value);setStart(profiles.timestamps[i].slice(0,10));setDays(1);setHover(Number(profiles.timestamps[i].slice(11,13)));setTablePage(0)}}><option value="">Bir olay seçin</option><option value={annualPeak}>Yıllık sonra piki · {dateLabel(profiles.timestamps[annualPeak])}</option>{violations.slice(eventPage*48,(eventPage+1)*48).map(i=><option key={i} value={i}>{dateLabel(profiles.timestamps[i])} · önce {n(annualBefore[i])} / sonra {n(annualAfter[i])} kW</option>)}</select></label><div className="dialog-actions"><button className="button secondary" disabled={eventPage===0} onClick={()=>setEventPage(p=>p-1)}>Önceki aşım saatleri</button><span>{violations.length} aşım saati · 48 saatlik sayfa {eventPage+1}</span><button className="button secondary" disabled={(eventPage+1)*48>=violations.length} onClick={()=>setEventPage(p=>p+1)}>Sonraki aşım saatleri</button></div>
      <div className="chart-legend"><span><i className="legend-line before" />Önce</span><span><i className="legend-line after" />Sonra</span><span><i className="legend-line capacity" />Bağlantı sınırı: {n(capacity)} kW</span><small>{indexes.length} / {profiles.timestamps.length} saat gösteriliyor</small></div>
      <div className="chart-scroll"><svg className="load-chart" viewBox={`0 0 ${width} ${height}`} role="img" aria-label="Sentetik profilde önce ve sonra grup yükü; aynı eksende kapasite çizgisi" onPointerMove={e => { const rect = e.currentTarget.getBoundingClientRect(); setHover(Math.max(0, Math.min(indexes.length - 1, Math.round(((e.clientX - rect.left) / rect.width * width - left) / (width - left - right) * (indexes.length - 1))))); }}>
        {[0, 1, 2, 3, 4].map(i => { const v = max * i / 4; return <g key={i}><line x1={left} x2={width - right} y1={y(v)} y2={y(v)} stroke="var(--border)" /><text x={left - 12} y={y(v) + 4} textAnchor="end" className="chart-axis">{n(v, 0)}</text></g>; })}
        <text x={left} y={14} className="chart-axis">kW</text>
        <path d={`${path(after)} L${x(after.length - 1)},${y(0)} L${x(0)},${y(0)}Z`} fill="var(--chart-area)" opacity=".65" />
        <path d={path(before)} stroke="var(--chart-before)" strokeDasharray="5 3" strokeWidth="2" fill="none" /><path d={path(after)} stroke="var(--chart-after)" strokeWidth="2.5" fill="none" />
        <line x1={left} x2={width - right} y1={y(capacity)} y2={y(capacity)} stroke="var(--chart-capacity)" strokeWidth="1.5" strokeDasharray="7 5" />
        <line x1={x(point)} x2={x(point)} y1={top} y2={height - bottom} stroke="var(--muted)" strokeDasharray="3 4" />
        <circle cx={x(point)} cy={y(after[point])} r="4" fill="var(--chart-after)" />
        {[0, .25, .5, .75, 1].map(fraction => { const i = Math.round((indexes.length - 1) * fraction); return <text key={fraction} x={x(i)} y={height - 16} textAnchor={fraction === 0 ? 'start' : fraction === 1 ? 'end' : 'middle'} className="chart-axis">{dateLabel(profiles.timestamps[indexes[i]])}</text>; })}
      </svg></div>
      <label className="sr-only" htmlFor="chart-hour">Grafikte saati incele</label><input id="chart-hour" className="hour-slider" type="range" min={0} max={Math.max(0, indexes.length - 1)} value={point} onChange={e => setHover(Number(e.target.value))} />
      <div className="chart-inspector"><strong>{dateLabel(profiles.timestamps[indexes[point]])}</strong><span>Önce <b>{n(before[point])} kW</b></span><span>Sonra <b>{n(after[point])} kW</b></span><span>Bağlantı sınırı <b>{n(capacity)} kW</b></span></div>
      <details className="hourly-table"><summary>Saatlik sayısal tablo · erişilebilir alternatif</summary><div className="table-scroll"><table><caption>Seçili dönem; {indexes.length} saat, sayfa {Math.min(tablePage,Math.floor((indexes.length-1)/24))+1}</caption><thead><tr><th>Zaman</th><th>Önce kW</th><th>Sonra kW</th><th>Sınır kW</th><th>Aşım</th></tr></thead><tbody>{indexes.slice(Math.min(tablePage,Math.floor((indexes.length-1)/24))*24,(Math.min(tablePage,Math.floor((indexes.length-1)/24))+1)*24).map(i=><tr key={i}><td>{dateLabel(profiles.timestamps[i])}</td><td>{n(annualBefore[i])}</td><td>{n(annualAfter[i])}</td><td>{n(capacity)}</td><td>{annualAfter[i]>capacity?'Sonra aşım':annualBefore[i]>capacity?'Önce aşım':'Yok'}</td></tr>)}</tbody></table></div><button className="button secondary" disabled={tablePage<=0} onClick={()=>setTablePage(p=>Math.max(0,p-1))}>Önceki 24 saat</button><button className="button secondary" disabled={(tablePage+1)*24>=indexes.length} onClick={()=>setTablePage(p=>p+1)}>Sonraki 24 saat</button></details>
      <p className="small-note">Bina yükleri aynı zaman damgalarında toplanır. Yıllık kapasite uygunluğu motorun bütün saatlerdeki kontrolüne dayanır; seçilen dönem grafiği bu kontrolün görsel bir kesitidir.</p>
    </>}
  </section>;
}
