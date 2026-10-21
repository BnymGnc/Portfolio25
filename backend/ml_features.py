"""Features derive only from pre-intervention inputs, never post-retrofit targets."""
def encode(features):
    area=features['area_m2']
    return {'area_m2':area,'year_built':features['year_built'],
        'baseline_electricity_intensity':features['baseline_electricity_kwh_year']/area,
        'baseline_gas_intensity':features['baseline_gas_kwh_year']/area,
        **{k:str(features[k]) for k in ('building_type','climate_zone','hvac_system','upgrade')}}
