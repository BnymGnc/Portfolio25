"""Read committed model metadata and calculate demo scenarios without user records."""
import json,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'backend'))
from pilot_kayseri import create_pilot
from engine import calculate
from models import CalculationRequest

def main():
    path=ROOT/'backend/ml_assets/synthetic-annual/metadata.json';m=json.loads(path.read_text(encoding='utf-8'))
    # Correct the version tag to match the building-level infiltration generator;
    # training outputs, split, metrics, model bytes and hashes are unchanged.
    if m['model_version']=='synthetic-annual-1.1' and m['seed']==25027:
        m['generator_version']='independent-spatial-1.1';path.write_text(json.dumps(m,ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# Sentetik yıllık enerji model kartı','',f"Model: `{m['model_version']}` · özellik şeması `{m['feature_schema']}` · üretici `{m['generator_version']}` · seed `{m['seed']}`.",'',
        '**Sentetik simülasyon verisiyle eğitilmiştir; saha doğruluğu kanıtı değildir.** Fizik/MILP motorunu değiştirmez. Saatlik pik, elektrik bağlantısı veya konfor tahmini değildir.','',
        f"{m['building_count']} bağımsız bina; {m['training_rows']} eğitim, {m['validation_rows']} validasyon ve {m['test_rows']} test varyantı. Bina grupları 70/15/15 oranıyla ayrıldı; aynı binanın bütün müdahaleleri aynı gruptadır. Grup kimlikleri metadata.json içindedir.",'',
        'Alan 700–6500 m², kat sayısı 2–6, altı kullanım türü; ısıtma yoğunluğu 85–240 kWh/m²-yıl tabanı, sıcak su 2–100 kWh/m²-yıl. Kazan verimi 0,70–0,96, SCOP 2,2–4,6, pompa termal kapasitesi alan × 0,025–0,09 kW/m²; pompa kapsamı sabit 0,9. Kabuk ilgili payı 0,5–1 ve azaltım 0,12–0,48. Çatı hedef U 0,18–0,55 W/m²K. Başlangıç U, ışık/cihaz gücü ve kullanım programları ayrıca bağımsız değiştirilir. Tam üretici aralıkları scripts/train_synthetic.py içindedir. Eğitimde örnek sekiz bina satır olarak kullanılmaz; ortak sentetik geometri/kullanım şablonu üreticisi kullanılır.','',
        'Yalnız uygun tüm-bina kombinasyonları mevcut interventions.candidates fizik evaluator’ından etiketlenir. Çatı/kabuk çakışması ve kritik hizmet azaltımı elenir. Sıcak su korunur. Girdiler başlangıç verileri ve müdahale bayraklarıdır; sonuç tüketimi, tasarruf veya hedeflerden türetilmiş özellik yoktur. Aydınlatma azaltım özelliği kurulu/hedef W/m² ve kullanım programından çıkar; sonuç etiketinden alınmaz.','',
        'Mean referansı, standardize Ridge, ExtraTrees ve RandomForest karşılaştırıldı. StandardScaler yalnız eğitimde fit edilir. Sabit, küçük model evreninden seçim validasyon MAE’sinin eğitim hedef ortalamalarına göre normalize edilmiş ortalamasıyla yapılır. Seçim dondurulduktan sonra test bir defa raporlanır; testle hiperparametre seçilmez.','',
        f"Seçilen model: **{m['selected_model']}**. Test hataları kWh/yıl:",'',
        '| Model | Elektrik MAE | Gaz MAE | Elektrik RMSE | Gaz RMSE | Elektrik R² | Gaz R² |','| --- | ---: | ---: | ---: | ---: | ---: | ---: |']
    for name,data in m['test'].items():
        v=data['overall'];lines.append('| '+name+' | '+' | '.join(f'{a:,.2f}' for a in v['mae']+v['rmse']+v['r2'])+' |')
    lines+=['','## Seçilen modelin kullanım türüne göre test MAE’si','','| Tür | Satır | Elektrik | Gaz |','| --- | ---: | ---: | ---: |']
    for name,data in m['test'][m['selected_model']]['by_use'].items():lines.append(f"| {name} | {data['rows']} | {data['mae'][0]:,.2f} | {data['mae'][1]:,.2f} |")
    lines+=['','## Sınırlar ve yeniden üretim','',
        'Bu model fizik simülatörünü yaklaşık öğrenir. Tablodaki R² gerçek saha kalibrasyonu değildir. Üretimde fizik sonucu zaten hesaplandığından bu entegrasyon hız üstünlüğü sağlamaz; deneysel kıyaslama sağlar.','',
        'İlk küçük deneme 24 bağımsız binayla yapıldı. İlk büyük üreticide zon başına bağımsız hava değişimi çekmek bina ortalamasını yapay biçimde dar aralıkta topladı; ofis 0,5 hava değişimi/saat eğitim aralığı dışında kaldı. 1.1 sürümü hava değişimini bina düzeyinde çeker. Önceki model yerel artifacts/training-v1-archive içinde tutuldu; nihai üretim yeni seed ve yeni grup ayrımıyla yeniden yapıldı. İlk test metrikleri son model seçimi için kullanılmadı.','',
        'Nihai modelin kapsam denetimi korunur: idari pilot binasının cihaz yıllık enerjisi öğrenilen aralık dışında; tahmin verilmez. Diğer yedi pilotun temel girdileri aralık içindedir. Zon seçili müdahaleler, farklı yıl/sistem, farklı pompa kapsamı ve eğitim özellik sınırını aşan girdiler reddedilir. Model dosyası yoksa veya SHA256 uyuşmazsa tahmin uydurulmaz. Aralık içinde olmak dağılım benzerliğinin veya doğruluğun garantisi değildir.','',
        '```powershell','.\\.venv\\Scripts\\python.exe scripts/train_synthetic.py --buildings 24 --seed 25027 --output artifacts/training-smoke-final',
        '.\\.venv\\Scripts\\python.exe scripts/train_synthetic.py --buildings 240 --seed 25027','```','',
        'Sunucu başlangıcında eğitim yoktur. Model, özellik listesi, sınırlar, gruplar, hedef/tür/müdahale başına metrikler ve özetler backend/ml_assets/synthetic-annual altındadır. Güvenilen yerel joblib dosyası hash kontrolünden sonra yüklenir; dosya yolu istemciden alınmaz. ComStock modeli ayrı tutulur.']
    (ROOT/'docs/model-card-synthetic.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
    out=ROOT/'artifacts/final-delivery';out.mkdir(exist_ok=True,parents=True)
    scenarios=[]
    for budget in (2_800_000,0):
        campus=create_pilot()[2];campus.scenario.budget_try=budget
        result=calculate(campus,CalculationRequest(revision=1,mode='A',time_limit_s=5))
        (out/f'demo-budget-{budget}.json').write_text(result.model_dump_json(indent=2),encoding='utf-8')
        scenarios.append((budget,result))
    demo=['# Üç dakikalık gerçek demo akışı','','0:00–0:30 — Kayıt/giriş; ilk tanıtımı gösterin. Dört proje ve sekiz binanın sentetik olduğunu belirtin. Eski yerel projeler korunur.','',
        '0:30–1:00 — Kampüste iki bina, konut sitesinde A/B blok, ardından bağımsız ofis. Bina/kat dağılımı ile varsayımları gösterin.','',
        '1:00–2:00 — Bağımsız ofiste aşağıdaki iki bütçeyi sırayla kaydedip Mod A hesaplayın. Sonuçlar aynı sentetik ofisin mevcut evaluator’ından hesaplandı; başarı hikâyesi için girdi değiştirilmedi.','',
        '| Bütçe TL | Durum | Yatırım TL | Tasarruf kWh/yıl | Tasarruf % | Hedef | Kapasite |','| ---: | --- | ---: | ---: | ---: | --- | --- |']
    for budget,r in scenarios:demo.append(f"| {budget:,.0f} | {r.status} | {r.investment_try:,.0f} | {r.energy_savings_kwh_year:,.1f} | {r.energy_savings_pct:.2f} | {'karşılandı' if r.target_met else 'karşılanmadı'} | {'modellenen sınırlar içinde' if r.after and not any(c.violation_hours for c in r.after.capacity_checks) else 'uygun plan yok/aşım'} |")
    demo+=['','2:00–3:00 — Bina ekranında iki ML paketini karşılaştırın; fizik/ML farkını ve sentetik model sınırını gösterin. LLM kredi kotası nedeniyle yanıt alınamıyorsa bunu açıkça söyleyin; manuel alternatif ve hesaplama çalışır. Sonucu dışa aktarın. Girdi değiştirip eski sonucun güncel sayılmadığını gösterin.','',
           'Bu demo kaydı gerçek kullanıcı projesini değiştirmez; scripts/generate_final_evidence.py bellek içi örnekleri hesaplar. JSON kanıtları artifacts/final-delivery/demo-budget-*.json içindedir.']
    (ROOT/'docs/demo-final.md').write_text('\n'.join(demo)+'\n',encoding='utf-8')
    print('Model card and two calculated demo scenarios written.')
if __name__=='__main__':main()
