from typing import Literal
from pydantic import Field
from models import Model
from contracts import Context,Result
from spatial_models import InterventionDecision


class ExplainRequest(Model):
    context:Context
    scope:Literal['plan','building']='plan'
    building_id:str|None=None
    question:str=Field(default='Bu hesaplanan seçenekleri ve sınırlarını açıkla.',min_length=1,max_length=1000)


class Fact(Model):
    id:str
    label:str
    value:float|str|bool
    unit:str
    source_path:str


class Finding(Model):
    fact_id:str
    text:str=Field(min_length=1,max_length=500)


class Explanation(Model):
    scope:Literal['plan','building']
    building_id:str|None=None
    context:Context
    status:Literal['available']='available'
    model:str
    prompt_version:str
    cached:bool=False
    findings:list[Finding]=Field(min_length=3,max_length=3)
    details:list[Finding]=Field(max_length=6)
    facts:list[Fact]
    limitations:list[str]


class ScenarioChange(Model):
    field:Literal['budget_try','savings_target_pct','electricity_price_try_kwh','heating_price_try_kwh','intervention']
    value:float|Literal['candidate','mandatory','excluded']
    building_id:str|None=None
    intervention:Literal['roof','insulation','lighting','schedule','heat_pump']|None=None


class ScenarioDraftRequest(Model):
    context:Context
    question:str=Field(min_length=1,max_length=1000)


class ScenarioDraft(Model):
    clarification:str|None=Field(default=None,max_length=500)
    context:Context
    model:str
    prompt_version:str
    changes:list[ScenarioChange]=Field(max_length=20)
    explanation:str
    cached:bool=False


class ScenarioRun(Model):
    context:Context
    changes:list[ScenarioChange]=Field(min_length=1,max_length=20)
    mode:Literal['A','B']='A'
    time_limit_s:float=Field(default=5,ge=.01,le=15)


class ScenarioEvaluation(Model):
    forced_intervention:InterventionDecision|None=None
    building_id:str|None=None
    base_context:Context
    transient:Literal[True]=True
    persisted:Literal[False]=False
    changes:list[ScenarioChange]
    baseline_plan:Result|None
    alternative:Result


class CounterfactualRequest(Model):
    context:Context
    building_id:str
    intervention:Literal['roof','insulation','lighting','schedule','heat_pump']


class AIStatus(Model):
    last_call_status:Literal['not_tested','success','quota_exhausted','rate_limited','provider_error','unreachable']='not_tested'
    last_success_at:float|None=None
    service_reachable:bool|None=None
    configured:bool
    provider:Literal['OpenAI']='OpenAI'
    model:str
    prompt_version:str
    explanation_available:bool
    rag:Literal[False]=False
