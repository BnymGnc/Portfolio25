"""Consistent, revision-guarded exports; legacy auto scope stays compatible."""
import hashlib
from datetime import datetime, timezone

from fastapi import HTTPException

from models import CampusResponse, CalculationResult
from calculation_context import stale_reason


def calculation_id(result: CalculationResult | None) -> str | None:
    if not result:return None
    return result.calculation_id or hashlib.sha256(result.model_dump_json().encode('utf-8')).hexdigest()


def guarded_export(snapshot: CampusResponse, scope: str, revision: int | None, expected_calculation_id: str | None):
    if revision is not None and snapshot.campus.revision != revision:
        raise HTTPException(409, 'Dışa aktarım durduruldu: kayıt revizyonu değişti. Ekranı yenileyin.')
    if scope == 'result':
        if revision is None or not expected_calculation_id:
            raise HTTPException(422, 'Sonuç dışa aktarımı kayıt revizyonu ve hesap kimliği gerektirir.')
        if not snapshot.calculation or snapshot.calculation.input_revision != revision:
            raise HTTPException(409, 'Bu revizyon için güncel hesap yok. Yeniden hesaplayın.')
        if stale_reason(snapshot.campus, snapshot.calculation):
            raise HTTPException(409, 'Dışa aktarım durduruldu: hesap proje, girdi veya motor bağlamıyla eşleşmiyor.')
        if calculation_id(snapshot.calculation) != expected_calculation_id:
            raise HTTPException(409, 'Hesap aynı revizyonda yeniden üretildi veya mod değişti. Ekranı yenileyin.')
    if scope == 'inputs':
        snapshot = snapshot.model_copy(update={'calculation':None, 'after':None, 'investment_plan':None})
    metadata = {
        'project_id': snapshot.campus.id,
        'context': snapshot.context,
        'kind': scope, 'input_revision': snapshot.campus.revision,
        'calculation_revision': snapshot.calculation.input_revision if snapshot.calculation else None,
        'calculation_id': calculation_id(snapshot.calculation),
        'calculation_mode': snapshot.calculation.mode if snapshot.calculation else None,
        'exported_at_utc': datetime.now(timezone.utc).isoformat(),
        'peak_definition': 'electric_peak_kw = max_t sum_b load[b,t]; electric_peak_sum_kw is diagnostic only',
    }
    return snapshot, metadata
