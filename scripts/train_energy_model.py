"""Train a bounded ComStock annual surrogate; building-group holdout, no demo data."""
import os
os.environ.setdefault('OMP_NUM_THREADS','2')
import copy,hashlib,json,time,sys
from pathlib import Path
from datetime import datetime,timezone
import numpy as np
from sklearn.feature_extraction import DictVectorizer
from sklearn.pipeline import make_pipeline
from sklearn.linear_model import Ridge
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.multioutput import MultiOutputRegressor
from sklearn.model_selection import GroupShuffleSplit
from sklearn.metrics import mean_absolute_error
import sklearn,joblib

ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from ml_features import encode
OUT=ROOT/'backend/ml_assets/comstock-small'
rows=[json.loads(line) for line in (OUT/'data.jsonl').read_text(encoding='utf-8').splitlines()]
# Geographic reweighting repeats identical simulated bldg_id/upgrade pairs.
unique={};conflicts=set()
def normalized(r):return json.dumps({'f':{k:round(v,3) if isinstance(v,float) else v for k,v in r['features'].items()},'y':[round(v,3) for v in r['targets']]},sort_keys=True)
for row in rows:
 key=(row['building_id'],row['features']['upgrade'])
 if key in unique and normalized(unique[key])!=normalized(row):conflicts.add(key)
 else:unique.setdefault(key,row)
clean=[r for k,r in unique.items() if k not in conflicts]
groups=np.array([r['building_id'] for r in clean]);x=[encode(r['features']) for r in clean]
areas=np.array([r['features']['area_m2'] for r in clean]);y=np.array([r['targets'] for r in clean]);intensity=y/areas[:,None]
trainval,test=next(GroupShuffleSplit(n_splits=1,test_size=.2,random_state=25).split(x,y,groups))
smalltrain,val=next(GroupShuffleSplit(n_splits=1,test_size=.25,random_state=26).split(trainval,y[trainval],groups[trainval]))
train=trainval[smalltrain];val=trainval[val]
splits={name:sorted(set(groups[idx])) for name,idx in [('train',train),('validation',val),('test',test)]}
assert not set(splits['train'])&set(splits['validation']) and not set(splits['train'])&set(splits['test']) and not set(splits['validation'])&set(splits['test'])
def matrix(indices):return [x[i] for i in indices]
models={'ridge_reference':make_pipeline(DictVectorizer(sparse=False),Ridge(alpha=10)),
    'gradient_boosting_15':make_pipeline(DictVectorizer(sparse=False),MultiOutputRegressor(HistGradientBoostingRegressor(max_leaf_nodes=15,max_iter=120,learning_rate=.1,early_stopping=False,random_state=25))),
    'gradient_boosting_31':make_pipeline(DictVectorizer(sparse=False),MultiOutputRegressor(HistGradientBoostingRegressor(max_leaf_nodes=31,max_iter=160,learning_rate=.08,early_stopping=False,random_state=25)))}
validation={};timing={}
for name,model in models.items():
 started=time.perf_counter();model.fit(matrix(train),intensity[train]);timing[name]={'training_seconds':time.perf_counter()-started}
 predicted=model.predict(matrix(val))*areas[val,None]
 validation[name]={'mae_electricity_kwh_year':float(mean_absolute_error(y[val,0],predicted[:,0])),'mae_gas_kwh_year':float(mean_absolute_error(y[val,1],predicted[:,1]))}
selected=min(validation,key=lambda name:sum(validation[name].values()))
# Test is evaluated only now, after model selection; never used to tune parameters.
test_metrics={}
for name,model in models.items():
 started=time.perf_counter();pred=model.predict(matrix(test))*areas[test,None];timing[name]['batch_inference_seconds']=time.perf_counter()-started
 def metrics(indices):return {'rows':len(indices),'mae_electricity_kwh_year':float(mean_absolute_error(y[test[indices],0],pred[indices,0])),'mae_gas_kwh_year':float(mean_absolute_error(y[test[indices],1],pred[indices,1]))}
 test_metrics[name]={'overall':metrics(np.arange(len(test))),'by_building_type':{kind:metrics(np.array([j for j,i in enumerate(test) if clean[i]['features']['building_type']==kind])) for kind in sorted({clean[i]['features']['building_type'] for i in test})}}
model=models[selected];joblib.dump(model,OUT/'model.joblib')
numeric=['area_m2','year_built','baseline_electricity_kwh_year','baseline_gas_kwh_year']
categories=['building_type','climate_zone','hvac_system','upgrade']
domain={'country':'US','numeric':{k:{'min':min(clean[i]['features'][k] for i in train),'max':max(clean[i]['features'][k] for i in train)} for k in numeric},'categorical':{k:sorted({clean[i]['features'][k] for i in train}) for k in categories}}
source=json.loads((OUT/'source.json').read_text(encoding='utf-8'));source['attribution']='ComStock dataset developed by NLR with funding from U.S. DOE. Research simulation data; no field accuracy guarantee.'
source['license_source']='https://natlabrockies.github.io/ComStock.github.io/docs/citation.html'
source['license_note']='Dataset attribution/disclaimer source recorded; S3 viewer software Apache license is not asserted as the dataset license. Verify redistribution terms before external publication.'
(OUT/'source.json').write_text(json.dumps(source,ensure_ascii=False,indent=2),encoding='utf-8')
metadata={'model_version':'comstock-annual-1.0','feature_schema':'annual-inputs-1.0','trained_at_utc':datetime.now(timezone.utc).isoformat(),
    'sklearn_version':sklearn.__version__,'selected_model':selected,'source':source,'training_rows':len(train),'validation_rows':len(val),'test_rows':len(test),
    'clean_rows':len(clean),'duplicate_pairs_removed':len(rows)-len(unique),'conflicting_pairs_removed':len(conflicts),'building_groups':len(set(groups)),
    'split_groups':splits,'validation_metrics':validation,'test_metrics':test_metrics,'timing':timing,'domain':domain,
    'features':['area_m2','year_built','baseline_electricity_intensity','baseline_gas_intensity',*categories],
    'targets':['electricity_kwh_year','gas_kwh_year'],'model_sha256':hashlib.sha256((OUT/'model.joblib').read_bytes()).hexdigest(),
    'training_data_sha256':hashlib.sha256((OUT/'data.jsonl').read_bytes()).hexdigest(),
    'example':{'features':clean[int(test[0])]['features'],'country':'US','observed_simulation_targets':clean[int(test[0])]['targets']},
    'limitations':['ABD ticari bina simülasyonlarından sınırlı ilçe alt kümesi; Kayseri/Türkiye coğrafyası kapsam dışı.',
        'Mevcut GRID müdahale tanımlarıyla ComStock upgrade tanımları birebir eşdeğer değildir.',
        'Yalnız yıllık elektrik ve toplam gaz; saatlik pik/kapasite veya konfor için kullanılamaz.',
        'Optimizasyon yalnız fizik motorunu kullanır; ML plan seçmez.',
        'Alt küme nüfusu temsil eden ağırlıklı istatistik örneği değildir; dar örnek kapsamı.',
        'Bina grubuyla split varyant sızıntısını önler; bağımsız coğrafi/iklim holdout doğrulaması değildir.']}
(OUT/'metadata.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'groups':len(set(groups)),'rows':len(clean),'selected':selected,'validation':validation,'test':{k:v['overall'] for k,v in test_metrics.items()}},ensure_ascii=True))
