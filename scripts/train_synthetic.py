"""Explicit offline training. Never reads saved projects, secrets, or the eight demo instances."""
import argparse,sys,time,json,hashlib
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'backend'))
import numpy as np
from pilot_kayseri import make_building
from models import Building,Scenario,ProfileSettings
from spatial_models import InterventionDecision
from spatial_energy import known_electricity,zones
from profiles import generate_profiles
from interventions import candidates
from synthetic_ml import features,NAMES,KINDS,USES,VERSION,FEATURE_VERSION,ASSET_DIR

def generate(count,seed):
    rng=np.random.default_rng(seed);rows=[];groups=[];types=[];actions=[];targets=[]
    for i in range(count):
        use=USES[i%len(USES)];area=float(rng.uniform(700,6500));floors=int(rng.integers(2,7))
        b=make_building(i%8+1,'Independent synthetic building',use,area,floors,float(rng.uniform(85,240)),float(rng.uniform(2,100)),True)
        b.year_built=int(rng.integers(1970,2021))
        b.retrofit.boiler_efficiency=float(rng.uniform(.70,.96));b.retrofit.heat_pump_scop=float(rng.uniform(2.2,4.6))
        b.retrofit.heat_pump_capacity_kw_thermal=area*float(rng.uniform(.025,.09))
        b.retrofit.insulation_reduction_fraction=float(rng.uniform(.12,.48));b.retrofit.insulation_relevant_heat_fraction=float(rng.uniform(.5,1))
        # Draw infiltration at building level: independent draws per small zone
        # concentrate the area-weighted feature near the mean and lose low/high buildings.
        building_air_changes=float(rng.uniform(.3,2.5))
        for _,z in zones(b):
            z.wall_u_w_m2k=float(rng.uniform(.5,2));z.window_u_w_m2k=float(rng.uniform(1.6,4));z.roof_u_w_m2k=float(rng.uniform(.7,2.2))
            z.air_changes_hour=building_air_changes;z.lighting_w_m2=float(rng.uniform(5,15));z.target_lighting_w_m2=float(rng.uniform(2,4.8));z.device_w_m2=float(rng.uniform(3,40))
            z.program.lighting_use_fraction=float(rng.uniform(.15,.9));z.program.device_use_fraction=float(rng.uniform(.25,.85))
            if not z.program.critical_service:
                z.program.occupied_start=int(rng.integers(7,10));z.program.occupied_end=int(rng.integers(17,22));z.program.service_start=max(0,z.program.occupied_start-int(rng.integers(1,4)));z.program.service_end=min(24,z.program.occupied_end+int(rng.integers(1,4)))
        b.spatial.roof_target_u_w_m2k=float(rng.uniform(.18,.55));b.spatial.cooling_electricity_kwh_year=area*float(rng.uniform(5,35));b.spatial.common_system_electricity_kwh_year=area*float(rng.uniform(3,14))
        b.electricity_kwh_year=known_electricity(b,2025)+area*float(rng.uniform(3,25))
        b.spatial_selection.schedule_review_ack=True
        b.interventions=[InterventionDecision(kind=k,state='excluded' if k=='schedule' and use in ('Araştırma','Konut','Otel') else 'candidate') for k in KINDS]
        b=Building.model_validate(b.model_dump());p=generate_profiles(b,ProfileSettings())
        for candidate in candidates(b,p,Scenario(budget_try=1e9,savings_target_pct=25,electric_capacity_kw=1e5,electricity_price_try_kwh=4.5,heating_price_try_kwh=1.5)):
            report=candidate.report;action={d.kind for d in report.interventions}
            rows.append(features(b,action,2025));targets.append([report.electricity_kwh_year,report.heating_gas_kwh_year+report.non_heating_gas_kwh_year]);groups.append(i);types.append(use);actions.append(report.candidate_id)
        if (i+1)%20==0:print(f'Generated {i+1}/{count} independent buildings, {len(rows)} variants',flush=True)
    return np.array(rows),np.array(targets),np.array(groups),np.array(types),np.array(actions)

def metrics(y,p):
    from sklearn.metrics import mean_absolute_error,mean_squared_error,r2_score
    return {'rows':len(y),'mae':mean_absolute_error(y,p,multioutput='raw_values').tolist(),'rmse':np.sqrt(mean_squared_error(y,p,multioutput='raw_values')).tolist(),'r2':r2_score(y,p,multioutput='raw_values').tolist() if len(y)>1 else None}

def train(count,seed,destination):
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import ExtraTreesRegressor,RandomForestRegressor
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from threadpoolctl import threadpool_limits
    import sklearn,joblib
    started=time.perf_counter();x,y,g,types,actions=generate(count,seed)
    order=np.random.default_rng(seed+1).permutation(count);train_ids=order[:int(count*.7)];val_ids=order[int(count*.7):int(count*.85)];test_ids=order[int(count*.85):]
    train=np.isin(g,train_ids);val=np.isin(g,val_ids);test=np.isin(g,test_ids)
    models={'mean':DummyRegressor(),'linear':make_pipeline(StandardScaler(),Ridge(alpha=10)),'extra_trees':ExtraTreesRegressor(n_estimators=100,min_samples_leaf=2,random_state=seed,n_jobs=2),'random_forest':RandomForestRegressor(n_estimators=80,min_samples_leaf=3,random_state=seed,n_jobs=2)}
    validation={};timing={}
    with threadpool_limits(limits=2):
        for name,model in models.items():
            t=time.perf_counter();model.fit(x[train],y[train]);timing[name]=time.perf_counter()-t;validation[name]=metrics(y[val],model.predict(x[val]));print(name,'validation MAE',validation[name]['mae'],flush=True)
        scale=np.maximum(y[train].mean(axis=0),1);selected=min(models,key=lambda n:float(np.mean(np.array(validation[n]['mae'])/scale)))
        # Selection is now frozen; held-out test is evaluated once per model for reporting only.
        tests={}
        for name,model in models.items():
            pred=model.predict(x[test]);tests[name]={'overall':metrics(y[test],pred),'by_use':{u:metrics(y[test][types[test]==u],pred[types[test]==u]) for u in sorted(set(types[test]))},'by_action':{a:metrics(y[test][actions[test]==a],pred[actions[test]==a]) for a in sorted(set(actions[test]))}}
    destination.mkdir(parents=True,exist_ok=True);joblib.dump(models[selected],destination/'model.joblib')
    meta={'model_version':VERSION,'feature_schema':FEATURE_VERSION,'generator_version':'independent-spatial-1.1','seed':seed,'building_count':count,'source_kind':'synthetic_simulation','weather':'kayseri-synthetic-v1 / 2025 / Europe/Istanbul; not measured','selected_model':selected,'sklearn_version':sklearn.__version__,'features':NAMES,'targets':['electricity_kwh_year','gas_kwh_year'],'training_rows':int(train.sum()),'validation_rows':int(val.sum()),'test_rows':int(test.sum()),'groups':{'train':train_ids.tolist(),'validation':val_ids.tolist(),'test':test_ids.tolist()},'feature_bounds':np.stack([x[train].min(axis=0),x[train].max(axis=0)],axis=1).tolist(),'validation':validation,'test':tests,'fit_seconds':timing,'total_seconds':time.perf_counter()-started,'dataset_sha256':hashlib.sha256(x.tobytes()+y.tobytes()+g.tobytes()).hexdigest(),'model_sha256':hashlib.sha256((destination/'model.joblib').read_bytes()).hexdigest(),'limitations':['Synthetic simulator approximation, not field validation.','Only whole-building intervention templates; zonal scopes are out of domain.','No hourly, peak, comfort or capacity inference.','Validation selected model; held-out building groups used once for final reporting.']}
    (destination/'metadata.json').write_text(json.dumps(meta,ensure_ascii=False,indent=2),encoding='utf-8');print('Saved',selected,'to',destination,flush=True)

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--buildings',type=int,default=240);p.add_argument('--seed',type=int,default=25027);p.add_argument('--output',type=Path,default=ASSET_DIR);args=p.parse_args()
    if args.buildings<24:raise SystemExit('At least 24 independent buildings required.')
    train(args.buildings,args.seed,args.output)
