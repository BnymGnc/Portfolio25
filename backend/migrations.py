from copy import deepcopy

from models import Campus


def migrate_v1(raw: dict) -> Campus:
    """Preserve annual inputs and identity; never reclassify heating as total gas."""
    migrated = deepcopy(raw)
    migrated["schema_version"] = "3.0"
    migrated["optimization_status"] = "ready"
    migrated["revision"] += 1
    migrated["migration_notes"] = [
        "v1→v2: yıllık elektrik, ısıtma yakıtı, bina kimlikleri ve senaryo korundu.",
        "Isıtma yakıtı kWh/yıl alanı ısıtma doğalgazı enerji içeriği olarak yorumlandı.",
        "Isıtma dışı doğalgaz bilinmediğinden 0 varsayıldı; ölçülmüş sıfır değildir, düzenleyin.",
        "Saatlik veri yoktu; sentetik normalize profil eklendi. Eski pik alanı yalnızca tarihsel referanstır.",
        "Bağlantı sınırı, pompa boyutu, verim, SCOP ve maliyetler düzenlenebilir örnek varsayımlarla eklendi.",
        'v1→v3: eski ortak kapasite G01 grubuna taşındı. Gaz kazanı ve uygun sulu dağıtım yalnız sentetik varsayımdır; konut/soğutma dönüşümü yok.',
    ]
    for b in migrated["buildings"]:
        b.setdefault("non_heating_gas_kwh_year", 0)
        b.setdefault("connection_limit_kw", round(max(1, b["peak_electric_kw"] * 1.5,
                                                       b["electricity_kwh_year"] / 8760 * 3), 2))
        b.setdefault("retrofit", {"heat_pump_capacity_kw_thermal": round(b["area_m2"] * 0.045, 2)})
    return Campus.model_validate(migrated)


def migrate_v2(raw: dict) -> Campus:
    migrated=deepcopy(raw)
    migrated['schema_version']='3.0'
    migrated['revision']+=1
    migrated.setdefault('migration_notes',[]).append('v2→v3: kullanıcı girdileri korundu; eski kampüs ortak sınırı G01 bağlantı grubuna taşındı. Gaz kazanı/sulu dağıtım uyumluluğu sentetik varsayımdır; doğrulayın. Eski sonuç tarihsel kaldı; yeniden hesaplayın.')
    return Campus.model_validate(migrated)
