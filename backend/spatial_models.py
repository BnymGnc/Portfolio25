"""Optional, versioned spatial assumptions. No architectural/comfort simulation claim."""
from pydantic import BaseModel, ConfigDict, Field, model_validator
from typing import Literal


class SpatialBase(BaseModel):
    model_config=ConfigDict(extra='forbid',allow_inf_nan=False)


class UseProgram(SpatialBase):
    days: list[int] = Field(default_factory=lambda:[0,1,2,3,4],min_length=1,max_length=7)
    occupied_start: int = Field(default=8,ge=0,le=23)
    occupied_end: int = Field(default=18,ge=1,le=24)
    service_start: int = Field(default=6,ge=0,le=23)
    service_end: int = Field(default=22,ge=1,le=24)
    required_margin_hours: int = Field(default=1,ge=0,le=4)
    lighting_use_fraction: float = Field(default=.8,ge=0,le=1)
    device_use_fraction: float = Field(default=.65,ge=0,le=1)
    people_per_100m2: float = Field(default=5,ge=0,le=200)
    schedule_change_allowed: bool = True
    critical_service: bool = False

    @model_validator(mode='after')
    def valid_program(self):
        if len(set(self.days))!=len(self.days) or any(d<0 or d>6 for d in self.days):
            raise ValueError('Kullanım günleri benzersiz 0–6 olmalı.')
        if not 0<=self.service_start<=self.occupied_start<self.occupied_end<=self.service_end<=24:
            raise ValueError('Hizmet programı gerekli kullanım saatlerini kapsamalı.')
        return self


class Zone(SpatialBase):
    id: str = Field(pattern=r'^Z[0-9]{3}$')
    name: str = Field(min_length=1,max_length=100)
    use: str = Field(min_length=1,max_length=80)
    area_m2: float = Field(gt=0,le=1_000_000)
    height_m: float = Field(default=3,gt=0,le=15)
    program: UseProgram = Field(default_factory=UseProgram)
    facade_m2: float = Field(ge=0,le=1_000_000)
    window_m2: float = Field(ge=0,le=1_000_000)
    orientation: Literal['K','G','D','B'] = 'G'
    roof_contact: bool = False
    ground_contact: bool = False
    wall_u_w_m2k: float = Field(default=1.1,gt=0,le=10)
    window_u_w_m2k: float = Field(default=2.5,gt=0,le=10)
    roof_u_w_m2k: float = Field(default=1.2,gt=0,le=10)
    ground_u_w_m2k: float = Field(default=.7,gt=0,le=10)
    air_changes_hour: float = Field(default=.5,ge=0,le=20)
    lighting_w_m2: float = Field(default=9,ge=0,le=100)
    target_lighting_w_m2: float = Field(default=4.5,ge=0,le=100)
    device_w_m2: float = Field(default=8,ge=0,le=500)
    lighting_upgrade_allowed: bool = True
    heating_system_id: str
    cooling_system_id: str | None = None
    dhw_weight: float = Field(default=0,ge=0,le=1_000_000)
    common_area: bool = False
    kind: Literal['synthetic'] = 'synthetic'
    source: str = 'Sentetik geometri ve kullanım varsayımı; saha ölçümü yok.'
    missing_information: list[str] = Field(default_factory=lambda:['Gerçek plan ve pencere yönleri doğrulanmadı.','Zon ölçümü ve konfor sıcaklığı yok.'])

    @model_validator(mode='after')
    def window_geometry(self):
        if self.window_m2>self.facade_m2:raise ValueError('Pencere alanı cephe alanını aşamaz.')
        return self


class Floor(SpatialBase):
    id: str = Field(pattern=r'^F[0-9]{2}$')
    name: str
    area_m2: float = Field(gt=0,le=1_000_000)
    zones: list[Zone] = Field(min_length=1,max_length=30)

    @model_validator(mode='after')
    def floor_balance(self):
        if abs(sum(z.area_m2 for z in self.zones)-self.area_m2)>1e-6:
            raise ValueError('Zon alanları kat alanıyla uzlaşmalı; ortak alanı ayrıca temsil edin.')
        return self


class SharedSystem(SpatialBase):
    id: str
    name: str
    kind: Literal['heating','cooling','domestic_hot_water']
    served_zone_ids: list[str] = Field(min_length=1)
    source: str = 'Sentetik ortak ekipman; birden çok kata hizmet verir. Kat başına yeni cihaz sayılmaz.'


class SpatialModel(SpatialBase):
    schema_version: Literal['1.0'] = '1.0'
    floors: list[Floor] = Field(min_length=1,max_length=20)
    systems: list[SharedSystem] = Field(min_length=1,max_length=20)
    detailed_zones: bool = False
    weather_scenario: Literal['kayseri-synthetic-v1'] = 'kayseri-synthetic-v1'
    cooling_electricity_kwh_year: float = Field(default=0,ge=0,le=1e9)
    common_system_electricity_kwh_year: float = Field(default=0,ge=0,le=1e9)
    dhw_gas_kwh_year: float = Field(default=0,ge=0,le=1e9)
    roof_target_u_w_m2k: float = Field(default=.35,gt=0,le=10)
    roof_cost_try_m2: float = Field(default=650,ge=0,le=100_000)
    lighting_cost_try_m2: float = Field(default=180,ge=0,le=100_000)
    schedule_control_cost_try: float = Field(default=45_000,ge=0,le=1e9)
    source: str = 'Açıklanabilir sentetik paylaştırma v1; termal/konfor simülasyonu değildir.'

    @model_validator(mode='after')
    def relationships(self):
        ids=[z.id for f in self.floors for z in f.zones]
        systems={s.id:s for s in self.systems}
        if len(set(f.id for f in self.floors))!=len(self.floors) or len(ids)!=len(set(ids)) or len(systems)!=len(self.systems):
            raise ValueError('Kat, zon ve sistem kimlikleri bina içinde benzersiz olmalı.')
        for s in self.systems:
            if len(set(s.served_zone_ids))!=len(s.served_zone_ids) or not set(s.served_zone_ids)<=set(ids):raise ValueError('Ortak sistem hizmet alanları tutarsız.')
        for f in self.floors:
            for z in f.zones:
                for key,kind in [(z.heating_system_id,'heating'),(z.cooling_system_id,'cooling')]:
                    if key is not None and (key not in systems or systems[key].kind!=kind or z.id not in systems[key].served_zone_ids):
                        raise ValueError('Zon ile merkezî sistemin hizmet verdiği alanlar eşleşmiyor.')
        return self


class SpatialSelection(SpatialBase):
    roof: bool = False
    lighting: bool = False
    schedule: bool = False
    zone_ids: list[str] = Field(default_factory=list)
    schedule_review_ack: bool = False


class InterventionDecision(SpatialBase):
    kind:Literal['roof','insulation','lighting','schedule','heat_pump']
    state:Literal['applied','mandatory','candidate','excluded']='candidate'


class SpatialPreviewRequest(SpatialBase):
    revision: int = Field(ge=1)
    selection: SpatialSelection = Field(default_factory=SpatialSelection)
    package: Literal['none','insulation','heat_pump','combined'] = 'none'
    spatial: SpatialModel | None = None
    interventions: list[InterventionDecision] | None = None
