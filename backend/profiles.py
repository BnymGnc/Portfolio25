from dataclasses import dataclass
from datetime import datetime, timedelta
from functools import lru_cache
from zoneinfo import ZoneInfo

import numpy as np

from models import Building, Campus, ProfileAudit, ProfileAuditRow, ProfileSettings


@dataclass
class AnnualProfiles:
    timestamps: tuple[str, ...]
    electricity_kw: np.ndarray
    useful_heat_kw: np.ndarray


@lru_cache(maxsize=16)
def time_axis(year: int, timezone: str) -> tuple[datetime, ...]:
    start = datetime(year, 1, 1, tzinfo=ZoneInfo(timezone))
    end = datetime(year + 1, 1, 1, tzinfo=ZoneInfo(timezone))
    return tuple(start + timedelta(hours=i) for i in range(int((end - start).total_seconds() / 3600)))


def normalize(weights: np.ndarray, annual_kwh: float) -> np.ndarray:
    # Each element is average kW for a one-hour interval. No display rounding here.
    return weights * (annual_kwh / float(weights.sum()))


def generate_profiles(building: Building, settings: ProfileSettings) -> AnnualProfiles:
    if building.spatial:
        from spatial_energy import profile_inputs
        return profile_inputs(building,settings)
    axis = time_axis(settings.year, settings.timezone)
    hour = np.array([t.hour for t in axis])
    day = np.array([t.timetuple().tm_yday for t in axis])
    weekday = np.array([t.weekday() < 5 for t in axis])
    rng = np.random.default_rng(np.random.SeedSequence([settings.seed, int(building.id[1:])]))
    phase = rng.uniform(-1.5, 1.5)
    occupied = np.exp(-0.5 * ((hour - (13 + phase)) / 4) ** 2)
    if building.use_type == "Konaklama":
        occupied = 0.55 + 0.65 * np.exp(-0.5 * ((hour - 20) / 3) ** 2)
    if building.use_type == "Araştırma":
        occupied = 0.7 + occupied * 0.5
    electricity_shape = (0.3 + occupied) * np.where(weekday, 1.0, 0.72) * rng.uniform(0.94, 1.06, len(axis))
    # Common synthetic seasonal pattern, not meteorological observations.
    winter = np.maximum(0, np.cos(2 * np.pi * (day - 20) / 365.25)) ** 1.3
    heat_shape = winter * (0.65 + 0.35 * occupied) * (1.05 + 0.15 * np.cos(2 * np.pi * (hour - 6) / 24))
    useful_heat = building.heating_kwh_year * building.retrofit.boiler_efficiency
    return AnnualProfiles(tuple(t.isoformat() for t in axis),
                          normalize(electricity_shape, building.electricity_kwh_year),
                          normalize(heat_shape, useful_heat))


def audit_profiles(campus: Campus, profiles: list[AnnualProfiles]) -> ProfileAudit:
    rows = []
    for b, p in zip(campus.buildings, profiles, strict=True):
        expected_heat = b.heating_kwh_year * b.retrofit.boiler_efficiency
        electricity = float(p.electricity_kw.sum())
        heat = float(p.useful_heat_kw.sum())
        rows.append(ProfileAuditRow(
            building_id=b.id, annual_electricity_kwh=b.electricity_kwh_year,
            integrated_electricity_kwh=electricity, electricity_error_kwh=electricity - b.electricity_kwh_year,
            annual_useful_heat_kwh=expected_heat, integrated_useful_heat_kwh=heat,
            heat_error_kwh=heat - expected_heat, electric_peak_kw=float(p.electricity_kw.max()),
            connection_limit_kw=b.connection_limit_kw,
            consistent=bool(np.isclose(electricity, b.electricity_kwh_year, rtol=1e-10, atol=1e-6)
                            and np.isclose(heat, expected_heat, rtol=1e-10, atol=1e-6)),
        ))
    axis = time_axis(campus.profile_settings.year, campus.profile_settings.timezone)
    return ProfileAudit(source=campus.profile_settings.source, timezone=campus.profile_settings.timezone,
                        start=axis[0].isoformat(), end_exclusive=(axis[-1] + timedelta(hours=1)).isoformat(),
                        hour_count=len(axis), all_consistent=all(r.consistent for r in rows), buildings=rows)
