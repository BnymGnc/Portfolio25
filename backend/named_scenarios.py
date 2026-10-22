"""Immutable named snapshots on the existing PostgreSQL / local project store."""
from datetime import datetime, timezone
import json
from uuid import uuid4
from fastapi import HTTPException
from pydantic import Field
from models import Model, Campus, CalculationResult
from contracts import Context
from calculation_context import context, input_hash
from auth import user_context
from psycopg.types.json import Jsonb

class SaveNamed(Model):
    name: str = Field(min_length=1,max_length=80,pattern=r'\S')
    context: Context

class Named(Model):
    id: str
    name: str
    created_at: str
    context: Context
    inputs: Campus
    calculation: CalculationResult | None

class NamedSummary(Model):
    id: str
    name: str
    created_at: str
    context: Context

def install(app, main):
    def documents():
        campus=main.read_campus() # ownership checked even when list is empty
        store=main.get_store()
        if store:
            with store.connection() as db:
                rows=db.execute('SELECT document FROM portfolio25.named_scenarios WHERE owner_id=%s AND project_id=%s ORDER BY created_at DESC',(user_context.get(),campus.id)).fetchall()
                return [r['document'] for r in rows]
        directory=main.data_root()/'named_scenarios'/campus.id
        return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(directory.glob('*.json'),reverse=True)]

    @app.get('/api/scenarios/saved',response_model=list[NamedSummary])
    def list_named():
        return [{k:v[k] for k in ('id','name','created_at','context')} for v in documents()]

    @app.get('/api/scenarios/saved/{scenario_id}',response_model=Named)
    def get_named(scenario_id:str):
        value=next((v for v in documents() if v['id']==scenario_id),None)
        if not value:raise HTTPException(404,'Senaryo bulunamadı.')
        return value

    @app.post('/api/scenarios/saved',response_model=Named)
    def save_named(request:SaveNamed):
        with main.lock:
            campus,result,current=main.require_context(request.context,False)
            value=Named(id=uuid4().hex,name=request.name.strip(),created_at=datetime.now(timezone.utc).isoformat(),context=current,inputs=campus,calculation=result)
            raw=value.model_dump(mode='json');store=main.get_store()
            if store:
                with store.connection() as db:
                    row=db.execute('SELECT document,latest_calculation_id FROM portfolio25.projects WHERE owner_id=%s AND project_id=%s FOR UPDATE',(user_context.get(),campus.id)).fetchone()
                    if not row or input_hash(Campus.model_validate(row['document']))!=current['input_hash']:
                        raise HTTPException(409,'Girdiler değişti; senaryo kaydedilmedi.')
                    if result and row['latest_calculation_id']!=result.calculation_id:
                        raise HTTPException(409,'Hesap değişti; senaryo kaydedilmedi.')
                    count=db.execute('SELECT count(*) AS n FROM portfolio25.named_scenarios WHERE owner_id=%s AND project_id=%s',(user_context.get(),campus.id)).fetchone()['n']
                    if count>=50:raise HTTPException(422,'Proje başına en fazla 50 adlandırılmış senaryo saklanabilir.')
                    db.execute('INSERT INTO portfolio25.named_scenarios(owner_id,project_id,scenario_id,document) VALUES(%s,%s,%s,%s)',(user_context.get(),campus.id,value.id,Jsonb(raw)))
            else:
                directory=main.data_root()/'named_scenarios'/campus.id
                directory.mkdir(parents=True,exist_ok=True)
                if len(list(directory.glob('*.json')))>=50:raise HTTPException(422,'Proje başına en fazla 50 adlandırılmış senaryo saklanabilir.')
                temp=directory/(value.id+'.tmp');temp.write_text(json.dumps(raw,ensure_ascii=False),encoding='utf-8');temp.replace(directory/(value.id+'.json'))
            return value
