import type {Building, Campus, ProjectSummary} from './types';
import type {PilotStatus} from './spatialTypes';

export default function ContextBar({campus, building, projects, pilot, disabled, onProject, onBuilding}: {
  campus?: Campus; building?: Building; projects: ProjectSummary[]; pilot: PilotStatus|null;
  disabled: boolean;
  onProject: (id:string)=>void; onBuilding: (id:string)=>void;
}) {
  const pilotIds = new Set(pilot?.projects.map(p=>p.id));
  const label = (p:ProjectSummary) => `${p.id==='campus-demo-25'?'Önceki örnek kampüs':pilotIds.has(p.id)?`Kayseri pilotu · ${p.name}`:p.name} · ${p.building_count} bina`;
  return <div className="context-bar" aria-label="Proje ve bina">
    <label className="project-context" htmlFor="project-select">Proje
      <select id="project-select" aria-label="Proje seçimi" value={campus?.id??''} disabled={disabled} onChange={e=>onProject(e.target.value)}>
        {!campus&&<option value="">Proje yükleniyor…</option>}
        {projects.map(p=><option key={p.id} value={p.id}>{label(p)}</option>)}
      </select>
    </label>
    <div className="building-context">
      {campus?.buildings.length===1
        ? <><span className="context-label">Bina · tek binalı proje</span><div className="single-building" title={building?.name}>{building?.name}</div></>
        : <label htmlFor="building-select">Bina
          <select id="building-select" aria-label="Bina seçimi" value={building?.id??''} disabled={disabled||!building} onChange={e=>onBuilding(e.target.value)}>
            {!building&&<option value="">Bina yükleniyor…</option>}
            {campus?.buildings.map(b=><option key={b.id} value={b.id}>{b.name}</option>)}
          </select>
        </label>}
    </div>
  </div>;
}
