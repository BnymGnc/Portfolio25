import {t,tr} from './i18n';
import type {Building, Campus, ProjectSummary} from './types';
import type {PilotStatus} from './spatialTypes';

export default function ContextBar({campus, building, projects, pilot, disabled, onProject, onBuilding}: {
  campus?: Campus; building?: Building; projects: ProjectSummary[]; pilot: PilotStatus|null;
  disabled: boolean;
  onProject: (id:string)=>void; onBuilding: (id:string)=>void;
}) {
  const pilotIds = new Set(pilot?.projects.map(p=>p.id));
  const label = (p:ProjectSummary) => `${p.id==='campus-demo-25'?tr('Previous sample campus','Önceki örnek kampüs'):p.name} · ${p.building_count} ${tr('buildings','bina')}`;
  return <div className="context-bar" aria-label={t("Proje ve bina")}>
    <label className="project-context" htmlFor="project-select">{t("Proje")+" "}<select id="project-select" aria-label={t("Proje seçimi")} value={campus?.id??''} disabled={disabled} onChange={e=>onProject(e.target.value)}>
        {!campus&&<option value="">{t("Proje yükleniyor…")}</option>}
        {projects.some(p=>pilotIds.has(p.id))&&<optgroup label={tr('Kayseri synthetic pilot','Kayseri sentetik pilotu')}>{projects.filter(p=>pilotIds.has(p.id)).map(p=><option key={p.id} value={p.id}>{label(p)}</option>)}</optgroup>}
        {projects.some(p=>!pilotIds.has(p.id))&&<optgroup label={tr('Other projects','Diğer projeler')}>{projects.filter(p=>!pilotIds.has(p.id)).map(p=><option key={p.id} value={p.id}>{label(p)}</option>)}</optgroup>}
      </select>
    </label>
    <div className="building-context">
      {campus?.buildings.length===1
        ? <><span className="context-label">{t("Bina · tek binalı proje")}</span><div className="single-building" title={building?.name}>{building?.name}</div></>
        : <label htmlFor="building-select">{t("Bina")+" "}<select id="building-select" aria-label={t("Bina seçimi")} value={building?.id??''} disabled={disabled||!building} onChange={e=>onBuilding(e.target.value)}>
            {!building&&<option value="">{t("Bina yükleniyor…")}</option>}
            {campus?.buildings.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </label>}
    </div>
  </div>;
}
