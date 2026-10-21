"""Heating-only engineering scope; eligibility is independent of electrical limits."""
from models import Building, PackageName


def exclusion_reason(building: Building, package: PackageName) -> str | None:
    if package == 'none':
        return None
    if building.spatial_selection.roof and package in ('insulation','combined'):
        return 'Çatı müdahalesi aktif; aynı çatıya ait yatırımı tekrar içeren kabuk paketi birlikte seçilemez.'
    if building.heating_system != 'gas_boiler':
        return 'Motor yalnız mevcut doğalgaz kazanının faydalı ısı dönüşümünü modeller. Bu sistem için ısı ayrıştırması ve yedek model eksik.'
    if package in ('insulation', 'combined') and not building.insulation_allowed:
        return 'Yalıtım müdahalesi mevcut bina için uygun değil olarak işaretlendi.'
    if package in ('heat_pump', 'combined'):
        if building.heat_distribution not in ('hydronic_assumed', 'low_temperature_water'):
            return 'Uygun düşük sıcaklıklı sulu dağıtım doğrulanmadı. Yüksek sıcaklık, bilinmeyen veya olmayan dağıtım için pompa paketi filtrelendi.'
        if building.retrofit.heat_pump_capacity_kw_thermal <= 0 or building.retrofit.heat_pump_coverage_fraction <= 0:
            return 'Pozitif pompa kapasitesi ve kapsama payı gerekir.'
    return None
