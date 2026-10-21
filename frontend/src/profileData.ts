import type { CampusProfiles, CampusResponse, CalculationResult } from './types';

export function validateProfiles(p: CampusProfiles, data: CampusResponse, result: CalculationResult) {
  if(result.calculation_id&&(p.calculation_id!==result.calculation_id||p.context?.input_hash!==result.input_hash||p.context?.engine_version!==result.engine_version))throw new Error('Grafik farklı hesap bağlamına ait; yeniden yükleyin.');
  const fail = () => { throw new Error('Saatlik profil eksik veya tutarsız. Grafik gösterilemiyor; veriyi yeniden yükleyin. Yıllık sonuç tablosu ayrıca incelenebilir.'); };
  if((p.project_id&&p.project_id!==data.campus.id)||(result.project_id&&result.project_id!==data.campus.id))fail();
  if (p.input_revision !== data.campus.revision || p.result_input_revision !== result.input_revision || p.result_mode !== result.mode) {
    throw new Error('Grafik ve sonuç aynı kayda ait değil. Girdileri yenileyin ve yeniden hesaplayın.');
  }
  const groups=data.campus.connection_groups;
  const expectedCapacity=groups?groups.length===1?groups[0].capacity_kw:null:data.campus.scenario.electric_capacity_kw;
  if (p.kind !== 'synthetic' || p.timezone !== data.campus.profile_settings.timezone || p.interval_hours !== 1 || p.capacity_kw !== expectedCapacity) fail();
  const length = data.profile_audit.hour_count;
  if (!Array.isArray(p.timestamps) || !Array.isArray(p.before_kw) || !Array.isArray(p.after_kw) || p.timestamps.length !== length || p.before_kw.length !== length || p.after_kw.length !== length) fail();
  const times = p.timestamps.map(t => Date.parse(t));
  if (p.timestamps[0] !== data.profile_audit.start || times.some((t, i) => !Number.isFinite(t) || (i > 0 && t - times[i - 1] !== 3600000))) fail();
  for (const series of [p.before_kw, p.after_kw!]) {
    if (series.some(v => !Number.isFinite(v) || v < 0)) fail();
  }
  const integral = (values: number[]) => values.reduce((sum, v) => sum + v, 0);
  const close = (a: number, b: number) => Math.abs(a - b) <= Math.max(0.001, Math.abs(b) * 1e-8);
  if (!result.after || !close(integral(p.before_kw), result.baseline.electricity_kwh_year) || !close(integral(p.after_kw!), result.after.electricity_kwh_year)) fail();
  if(groups){
    if(!p.groups||p.groups.length!==groups.length||new Set(p.groups.map(g=>g.id)).size!==groups.length)fail();
    for(const g of groups){
      const series=p.groups!.find(x=>x.id===g.id);
      if(!series||series.capacity_kw!==g.capacity_kw||series.before_kw.length!==length||series.after_kw?.length!==length)fail();
      if([...series!.before_kw,...series!.after_kw!].some(v=>!Number.isFinite(v)||v<0))fail();
      const annualBefore=data.baseline_packages?.filter(b=>g.building_ids.includes(b.building_id)).reduce((sum,b)=>sum+b.electricity_kwh_year,0)??data.campus.buildings.filter(b=>g.building_ids.includes(b.id)).reduce((sum,b)=>sum+b.electricity_kwh_year,0);
      const annualAfter=result.selected_packages.filter(b=>g.building_ids.includes(b.building_id)).reduce((sum,b)=>sum+b.electricity_kwh_year,0);
      if(!close(integral(series!.before_kw),annualBefore)||!close(integral(series!.after_kw!),annualAfter))fail();
    }
    for(let i=0;i<length;i++){
      if(!close(p.groups!.reduce((sum,g)=>sum+g.before_kw[i],0),p.before_kw[i])||!close(p.groups!.reduce((sum,g)=>sum+g.after_kw![i],0),p.after_kw![i]))fail();
    }
  }
  return p;
}
