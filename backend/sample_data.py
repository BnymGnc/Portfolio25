import random

from models import Baseline, Building, Campus, Provenance, RetrofitAssumptions, Scenario


def create_sample_campus() -> Campus:
    rng = random.Random(25)
    descriptions = [
        ("Mühendislik Fakültesi", "Eğitim", 8200, 1998),
        ("Merkez Kütüphane", "Eğitim", 5400, 2008),
        ("Araştırma Laboratuvarı", "Araştırma", 4600, 2012),
        ("Rektörlük", "İdari", 3200, 1995),
        ("Öğrenci Yaşam Merkezi", "Sosyal", 6100, 2015),
        ("Fen Fakültesi", "Eğitim", 7200, 2002),
        ("Spor Merkezi", "Sosyal", 4800, 2010),
        ("Öğrenci Yurdu", "Konaklama", 9400, 2005),
    ]
    provenance = Provenance(kind="synthetic", seed=25, source="Sabit seed=25 ile üretilmiş örnek; gerçek bir üniversiteyi temsil etmez.")
    buildings = [
        Building(
            id=f"B{index:02d}", name=name, use_type=use, area_m2=area,
            year_built=year, electricity_kwh_year=area * rng.randint(45, 110),
            heating_kwh_year=area * rng.randint(80, 180),
            peak_electric_kw=round(area * rng.uniform(0.022, 0.045), 1),
            provenance=provenance.model_copy(deep=True),
        )
        for index, (name, use, area, year) in enumerate(descriptions, 1)
    ]
    for building in buildings:
        building.non_heating_gas_kwh_year = round(building.heating_kwh_year * 0.08, 2)
        building.connection_limit_kw = round(max(building.peak_electric_kw * 1.5,
                                                building.electricity_kwh_year / 8760 * 3, 1), 2)
        building.retrofit = RetrofitAssumptions(heat_pump_capacity_kw_thermal=round(building.area_m2 * 0.045, 2))
    return Campus(
        revision=1, buildings=buildings, provenance=provenance,
        scenario=Scenario(budget_try=25_000_000, savings_target_pct=25,
                          electric_capacity_kw=2200, electricity_price_try_kwh=4.5,
                          heating_price_try_kwh=1.5),
    )


def calculate_baseline(campus: Campus) -> Baseline:
    from engine import calculate_package, summarize
    from profiles import generate_profiles
    return summarize(campus.buildings, [calculate_package(b, generate_profiles(b, campus.profile_settings),
                                                         campus.scenario, "none",apply_spatial=False) for b in campus.buildings], campus.scenario, campus.connection_groups)
