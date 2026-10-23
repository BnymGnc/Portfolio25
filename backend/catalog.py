"""Small versioned action catalogue, derived from the same eligibility and cost inputs."""
from typing import Literal
from models import Model,Building,CostQuote
from eligibility import exclusion_reason
from interventions import KINDS,policy
from intakes import CATALOG_VERSION
from pydantic import Field

class CatalogItem(Model):
    id:Literal['roof','insulation','heat_pump','lighting','schedule']
    label:str
    status:Literal['calculable','data_required','technical_review','unsupported']
    reason:str
    next_step:str
    scope:str
    conflicts:list[str]
    parameters:dict
    cost:dict
    source:str
    version:str=CATALOG_VERSION

LABELS={'roof':'Çatı yalıtımı','insulation':'Kabuk yalıtımı','heat_pump':'Isı pompası','lighting':'Aydınlatma iyileştirmesi','schedule':'HVAC çalışma programı'}
def catalogue(b):
    result=[]
    for kind in KINDS:
        reason='';status='calculable'
        if kind in ('insulation','heat_pump'):
            reason=exclusion_reason(b,kind) or ''
            if reason:status='data_required' if 'maliyet' in reason.lower() else 'technical_review' if 'dağıtım' in reason.lower() or 'daire' in reason.lower() else 'unsupported'
        else:
            if not b.spatial:status='data_required';reason='Kat/zon ve ilgili geometri, aydınlatma veya hizmet programı verisi gerekli.'
            else:
                try:
                    from spatial_energy import validate_selection
                    from spatial_models import SpatialSelection
                    copy=b.model_copy(deep=True);copy.spatial_selection=SpatialSelection(**{kind:True},schedule_review_ack=b.spatial_selection.schedule_review_ack)
                    validate_selection(copy,copy.spatial_selection,'none')
                except ValueError as e:status='technical_review';reason=str(e)
        quote=b.cost_quotes.get(kind)
        if b.provenance.kind!='synthetic' and not quote:status='data_required';reason=reason or 'Kapsamı belirtilmiş teklif veya kaynaklı referans maliyet gerekli.'
        result.append(CatalogItem(id=kind,label=LABELS[kind],status=status,reason=reason or 'Mevcut fizik motoru ve veri kapsamı içinde değerlendirilebilir.',next_step='Eksik bilgiyi veya teknik incelemeyi tamamlayın.' if status!='calculable' else 'Bina seçeneklerini karşılaştırın; portföy uygunluğunu ayrıca hesaplayın.',
            scope='Bina/ortak ekipman' if kind in ('roof','insulation','heat_pump') else 'Tanımlı hizmet alanları',conflicts=['insulation'] if kind=='roof' else ['roof'] if kind=='insulation' else [],
            parameters=b.retrofit.model_dump(mode='json') if kind in ('insulation','heat_pump') else b.spatial.model_dump(mode='json') if b.spatial else {},
            cost=quote.model_dump(mode='json') if quote else {'kind':'synthetic' if b.provenance.kind=='synthetic' else 'unspecified','source':b.retrofit.source,'reference_date':str(b.retrofit.reference_date),'currency':'TRY','scope':'Motor varsayımı; piyasa teklifi değildir.','vat_included':None,'labor_included':None},source='Mevcut motor uygunluk kuralları; saha incelemesi yerine geçmez.'))
    return result
