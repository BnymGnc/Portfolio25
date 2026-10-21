"""One context contract for results, charts, previews, exports and assistants."""
import hashlib
import json
from uuid import uuid4

ENGINE_VERSION = '4.0.0'


def input_hash(campus):
    return hashlib.sha256(json.dumps(campus.model_dump(mode='json'),sort_keys=True,
        separators=(',',':'),ensure_ascii=False).encode()).hexdigest()


def stale_reason(campus,result):
    if result is None:return 'Hesap bulunmuyor.'
    if result.project_id!=campus.id:return 'Hesap başka bir projeye ait.'
    if result.input_revision!=campus.revision:return 'Girdi revizyonu değişti; yeniden hesaplayın.'
    if result.engine_version!=ENGINE_VERSION:return 'Hesap motoru sürümü değişti; yeniden hesaplayın.'
    if result.input_hash!=input_hash(campus):return 'Girdi özeti değişti; yeniden hesaplayın.'
    if not result.calculation_id:return 'Eski hesap kimlik sözleşmesi; yeniden hesaplayın.'
    return None


def stamp(campus,result):
    result.project_id=campus.id;result.input_revision=campus.revision
    result.input_hash=input_hash(campus);result.engine_version=ENGINE_VERSION
    result.calculation_id=uuid4().hex
    for report in (result.decision_evidence,result.sensitivity):
        if report is not None:report['context']=context(campus,result)
    return result


def context(campus,result=None):
    return dict(project_id=campus.id,input_revision=campus.revision,input_hash=input_hash(campus),
        engine_version=ENGINE_VERSION,calculation_id=result.calculation_id if result else None,model_version=None)
