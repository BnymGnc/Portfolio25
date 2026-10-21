# Sentetik yıllık enerji model kartı

Model: `synthetic-annual-1.1` · özellik şeması `spatial-inputs-1.0` · üretici `independent-spatial-1.1` · seed `25027`.

**Sentetik simülasyon verisiyle eğitilmiştir; saha doğruluğu kanıtı değildir.** Fizik/MILP motorunu değiştirmez. Saatlik pik, elektrik bağlantısı veya konfor tahmini değildir.

240 bağımsız bina; 3000 eğitim, 648 validasyon ve 672 test varyantı. Bina grupları 70/15/15 oranıyla ayrıldı; aynı binanın bütün müdahaleleri aynı gruptadır. Grup kimlikleri metadata.json içindedir.

Alan 700–6500 m², kat sayısı 2–6, altı kullanım türü; ısıtma yoğunluğu 85–240 kWh/m²-yıl tabanı, sıcak su 2–100 kWh/m²-yıl. Kazan verimi 0,70–0,96, SCOP 2,2–4,6, pompa termal kapasitesi alan × 0,025–0,09 kW/m²; pompa kapsamı sabit 0,9. Kabuk ilgili payı 0,5–1 ve azaltım 0,12–0,48. Çatı hedef U 0,18–0,55 W/m²K. Başlangıç U, ışık/cihaz gücü ve kullanım programları ayrıca bağımsız değiştirilir. Tam üretici aralıkları scripts/train_synthetic.py içindedir. Eğitimde örnek sekiz bina satır olarak kullanılmaz; ortak sentetik geometri/kullanım şablonu üreticisi kullanılır.

Yalnız uygun tüm-bina kombinasyonları mevcut interventions.candidates fizik evaluator’ından etiketlenir. Çatı/kabuk çakışması ve kritik hizmet azaltımı elenir. Sıcak su korunur. Girdiler başlangıç verileri ve müdahale bayraklarıdır; sonuç tüketimi, tasarruf veya hedeflerden türetilmiş özellik yoktur. Aydınlatma azaltım özelliği kurulu/hedef W/m² ve kullanım programından çıkar; sonuç etiketinden alınmaz.

Mean referansı, standardize Ridge, ExtraTrees ve RandomForest karşılaştırıldı. StandardScaler yalnız eğitimde fit edilir. Sabit, küçük model evreninden seçim validasyon MAE’sinin eğitim hedef ortalamalarına göre normalize edilmiş ortalamasıyla yapılır. Seçim dondurulduktan sonra test bir defa raporlanır; testle hiperparametre seçilmez.

Seçilen model: **extra_trees**. Test hataları kWh/yıl:

| Model | Elektrik MAE | Gaz MAE | Elektrik RMSE | Gaz RMSE | Elektrik R² | Gaz R² |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| mean | 186,532.26 | 259,362.86 | 262,187.63 | 338,095.70 | -0.01 | -0.01 |
| linear | 29,620.14 | 84,921.90 | 41,571.01 | 119,062.80 | 0.97 | 0.87 |
| extra_trees | 31,265.70 | 62,369.73 | 44,558.52 | 95,618.13 | 0.97 | 0.92 |
| random_forest | 41,349.52 | 83,230.53 | 60,056.20 | 120,534.79 | 0.95 | 0.87 |

## Seçilen modelin kullanım türüne göre test MAE’si

| Tür | Satır | Elektrik | Gaz |
| --- | ---: | ---: | ---: |
| Araştırma | 60 | 20,870.53 | 52,971.94 |
| Eğitim | 120 | 33,054.33 | 61,731.45 |
| Konut | 60 | 25,268.87 | 51,030.84 |
| Ofis | 192 | 22,832.06 | 46,810.58 |
| Otel | 72 | 67,469.59 | 140,719.71 |
| İdari | 168 | 29,964.88 | 54,434.92 |

## Sınırlar ve yeniden üretim

Bu model fizik simülatörünü yaklaşık öğrenir. Tablodaki R² gerçek saha kalibrasyonu değildir. Üretimde fizik sonucu zaten hesaplandığından bu entegrasyon hız üstünlüğü sağlamaz; deneysel kıyaslama sağlar.

İlk küçük deneme 24 bağımsız binayla yapıldı. İlk büyük üreticide zon başına bağımsız hava değişimi çekmek bina ortalamasını yapay biçimde dar aralıkta topladı; ofis 0,5 hava değişimi/saat eğitim aralığı dışında kaldı. 1.1 sürümü hava değişimini bina düzeyinde çeker. Önceki model yerel artifacts/training-v1-archive içinde tutuldu; nihai üretim yeni seed ve yeni grup ayrımıyla yeniden yapıldı. İlk test metrikleri son model seçimi için kullanılmadı.

Nihai modelin kapsam denetimi korunur: idari pilot binasının cihaz yıllık enerjisi öğrenilen aralık dışında; tahmin verilmez. Diğer yedi pilotun temel girdileri aralık içindedir. Zon seçili müdahaleler, farklı yıl/sistem, farklı pompa kapsamı ve eğitim özellik sınırını aşan girdiler reddedilir. Model dosyası yoksa veya SHA256 uyuşmazsa tahmin uydurulmaz. Aralık içinde olmak dağılım benzerliğinin veya doğruluğun garantisi değildir.

```powershell
.\.venv\Scripts\python.exe scripts/train_synthetic.py --buildings 24 --seed 25027 --output artifacts/training-smoke-final
.\.venv\Scripts\python.exe scripts/train_synthetic.py --buildings 240 --seed 25027
```

Sunucu başlangıcında eğitim yoktur. Model, özellik listesi, sınırlar, gruplar, hedef/tür/müdahale başına metrikler ve özetler backend/ml_assets/synthetic-annual altındadır. Güvenilen yerel joblib dosyası hash kontrolünden sonra yüklenir; dosya yolu istemciden alınmaz. ComStock modeli ayrı tutulur.
