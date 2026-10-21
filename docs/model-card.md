# Model kartı — ComStock yıllık enerji tahmini

21 Ekim Görev 3 notu: mevcut ComStock ve sentetik model artefaktları yeniden eğitilmedi. Sentetik ofis karşılaştırmasındaki toplam gaz farkı (fizik 47.888,4; ML 118.155,1 kWh/yıl, +%146,7) aynı yıl/hedef/özellik kapsamıyla doğrulandı; hata gizlenmedi. [İnceleme ve sınırlar](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/task3-ui-report.md#ml-kapsamı-kontrolü). Aşağıdaki ComStock metrikleri değişmedi.

20 Ekim 2026. Bu dosya gerçekten eğitilmiş modelin metadata ve metriklerinden üretilmiştir. Model sekiz demo binasını öğrenmedi. **Deneysel harici simülasyon tahmini; saha doğruluğu veya Türkiye uygunluğu kanıtı değildir.**

## Kimlik ve görev

- Model sürümü `comstock-annual-1.0`, özellik şeması `annual-inputs-1.0`, scikit-learn 1.9.1.
- Validasyonla seçilen model: `gradient_boosting_15`. Artefakt `backend/ml_assets/comstock-small/model.joblib`; SHA-256 `adacb5d5e4415cfcd85c28fb515b9e74b5a0ed31354296b71c34f52fd1895afe`.
- Hedefler: müdahale sonrası yıllık elektrik (satın alınan elektrik, seçili müdahalelerde PV yok) ve toplam doğalgaz, kWh/yıl. Gaz ısıtma+sıcak su+diğer toplamıdır; saatlik yük veya konfor hedefi yok.
- Kod: `scripts/prepare_comstock.py`, `scripts/train_energy_model.py`, `backend/ml_features.py`, `backend/ml_service.py`. Eğitim API içinde yapılmaz; inference ana fizik motorunu değiştirmez.

## Gerçek veri kaynağı ve kapsam

[ComStock 2025 Release 3 / AMY2018](https://natlabrockies.github.io/ComStock.github.io/docs/data.html) küçük yıllık alt kümesi: CO/NY/TX ilk üç ilçe klasörü; okul, ofis ve otel türleri. Ülke ABD; Kayseri ölçümü değildir. Başlangıç, upgrade16 (HP Boiler, Gas Backup),43 (LED Lighting),49 (Roof Insulation). Upgrade sözlüğü gerçekten indirildi; GRID paketleriyle birebir aynı sayılmadı.
Sıkıştırılmış indirilen dosya toplamı 6,862,854 bayt; limit8MB, ulusal/saatlik bulk dosya yok. Ham eşleşme 3910 satır; coğrafi yeniden ağırlıklandırmayla tekrarlanan bldg_id/upgrade çiftlerinden 1826 tekrar kaldırıldı. Çelişen çift 0; nihai 2084 satır / 739 bina grubu. Sayısal eşitlik denetiminde0,001 kWh yuvarlama yalnız kopya tespiti içindir; eğitim değerleri kırpılmadı.
Veri dosyası `data.jsonl`, kaynak/dosya özetleri `source.json`, özellikler/split/metrik/örnek `metadata.json`. Dosya adları `.csv.gz` olsa da içlerinde tar arşivi olabildiği okuma sırasında doğrulandı; arşiv disk üzerinde açılmadan CSV üyesi okunur.
Alan ft²×0,09290304→m²; gaz weighted TBtu×293071070,1722222/weight→kWh. Temel ve müdahale aynı bldg_id üzerinden eşleşir. Hedefe ait weighted gaz yalnız hedef dönüşümünde kullanılır. Girdi gazı baz satırdan gelir.
Atıf/lisans kaydı: [ComStock attribution/disclaimer](https://natlabrockies.github.io/ComStock.github.io/docs/citation.html). NLR/DOE ComStock veri kaynağı kaydedildi. S3 viewer yazılımının Apache lisansı veri lisansı diye sunulmadı; harici dağıtım koşullarının ayrıca doğrulanması gerekir. [2025 Release 2 isim karışıklığı](https://natlabrockies.github.io/ComStock.github.io/docs/resources/explanations/2025_release_2_packages_known_issue.html) incelendi; eğitim Release3 ve kendi lookup kimlikleriyle yapıldı. California sıcak su eksikliği bildirimine sahip veriler bu alt kümede yok.

## Özellikler, sızıntı ve split

Alan, yapım yılı, başlangıç elektrik/gaz yoğunlukları (yalnız baz girdilerden), bina türü, as-simulated iklim sınıfı, baz HVAC sistemi ve upgrade kimliği. Dönüşüm sonrası enerji, gerçekleşmiş tasarruf, maliyet sonucu, hedef veya split kimliği özellik değildir. Yıllık hedefler alanla bölünerek regresyon öğrenilir; inference çıktısı alanla çarpılıp kWh/yıl olur. DictVectorizer sadece eğitimde fit edilir.
GroupShuffleSplit sabit seed25/26: eğitim 443 bina / 1248 satır; validasyon 148 bina / 417 satır; test 148 bina / 419 satır. Aynı binanın bütün müdahale varyantları aynı grupta; üç küme kesişmiyor. Geçerli bina türü/geometri/iklim aralıkları yalnız eğitimden çıkarılır.
Referans Ridge(alpha10); gradient boosting için iki önceden tanımlı HistGradientBoostingRegressor konfigürasyonu. İki hedef MultiOutputRegressor ile; erken durdurma kapalıdır (iç rastgele satır bölmesiyle grup sızıntısı yaratılmaz). Aday seçimi validasyon elektrik+gaz MAE toplamıyla; **test seçme/tuning için kullanılmadı**, model seçildikten sonra raporlandı. Testi gördükten sonra yeniden eğitim/tuning yapılmadı.

## Gerçek test sonuçları

| Model | Test satırı | Elektrik MAE kWh/yıl | Gaz MAE kWh/yıl |
| --- | --- | --- | --- |
| ridge_reference | 419 | 17.970,93 | 32.414,05 |
| gradient_boosting_15 (seçildi) | 419 | 13.543,83 | 13.800,24 |
| gradient_boosting_31 | 419 | 12.716,76 | 14.183,48 |

Her model için bina türü bazında test:

| Model | Bina türü | Satır | Elektrik MAE | Gaz MAE |
| --- | --- | --- | --- | --- |
| ridge_reference | LargeHotel | 41 | 28.398,07 | 65.455,80 |
| ridge_reference | MediumOffice | 37 | 23.372,29 | 47.022,99 |
| ridge_reference | PrimarySchool | 27 | 15.464,28 | 13.479,51 |
| ridge_reference | SecondarySchool | 77 | 46.104,93 | 96.129,73 |
| ridge_reference | SmallHotel | 37 | 22.364,01 | 4.440,52 |
| ridge_reference | SmallOffice | 200 | 3.528,20 | 6.138,57 |
| gradient_boosting_15 | LargeHotel | 41 | 14.761,40 | 32.755,47 |
| gradient_boosting_15 | MediumOffice | 37 | 13.807,46 | 6.387,37 |
| gradient_boosting_15 | PrimarySchool | 27 | 24.216,75 | 6.336,70 |
| gradient_boosting_15 | SecondarySchool | 77 | 33.860,19 | 44.634,22 |
| gradient_boosting_15 | SmallHotel | 37 | 13.534,25 | 3.613,89 |
| gradient_boosting_15 | SmallOffice | 200 | 3.984,59 | 2.306,76 |
| gradient_boosting_31 | LargeHotel | 41 | 14.052,01 | 34.644,66 |
| gradient_boosting_31 | MediumOffice | 37 | 13.196,14 | 7.316,53 |
| gradient_boosting_31 | PrimarySchool | 27 | 27.364,66 | 5.827,38 |
| gradient_boosting_31 | SecondarySchool | 77 | 30.179,43 | 45.508,93 |
| gradient_boosting_31 | SmallHotel | 37 | 11.077,60 | 3.895,87 |
| gradient_boosting_31 | SmallOffice | 200 | 3.957,00 | 2.230,30 |

Seçilen konfigürasyon her test hedefinde en iyi diye etiketlenmez. Örneğin başka konfigürasyonun elektrik MAE’si daha düşük olsa da seçim validasyonla sabitlenmiştir. MAE mutlak kWh hatasıdır, gerçekleşme olasılığı/güven aralığı değildir. Alt türlerde örnek sayısı küçük olabilir. Bu örneklemde referansla kıyas görülebilir; fizik motoruna karşı saha doğruluğu veya hız üstünlüğü ölçülmedi. Batch inference/eğitim süreleri metadata/timing içindedir; HTTP uçtan uca süreyle karıştırılmaz.

## Inference ve kullanım sınırı

`GET /api/ml/status`, `POST /api/ml/predict`, `POST /api/ml/project-predict`; Model ve veri ekranı. Model checksum ile doğrulanır; yalnız sabit yerel artefakt yüklenir, kullanıcı dosya yolu vermez. Eksik dosya/bağımlılıkta tahmin yok; fizik/MILP sürer. Eğitim dışı ülke/kategori/sayısal aralık reddedilir, sessiz ekstrapolasyon yapılmaz. Negatif çıktı sıfıra sınırlandırılırsa bayrakla açıklanır; test metrikleri ham tahminlerden hesaplandı.
Kayseri projeleri için ML tahmini **kapsam dışı**; fizik sonucu ayrı gösterilir. ComStock’tan ayrılmış gerçek test örneğinde yerel inference çalıştırıldı; bu örneğin bilinen hedefleri inference girdisine gönderilmez. GRID ve ComStock müdahaleleri eşleşmediğinden örneğe uydurma fizik sonucu eklenmez. Yıllık tahmin saatlik pik/kapasiteye dönüştürülmez; ana yatırım planı tamamen fizik sağlayıcısındadır.

Temel sınırlar: dar ilçe/tür/iklim örneklemi, coğrafi bağımsız holdout olmaması, harici simülasyon gerçeği, kısmi müdahale kapsamı. Daha geniş Türk bina verisine veya konutlara taşınabilirlik test edilmedi. Dinamik konfor/RC model/ML otonom kontrol yoktur.

Kaynak kütüphane belgeleri: [HistGradientBoostingRegressor](https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.HistGradientBoostingRegressor.html), [GroupShuffleSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.GroupShuffleSplit.html).
# 21 Ekim 2026 güncellemesi

Bu dosyadaki ComStock modeli korunmuştur. Ayrı sentetik simülasyon modeli, eğitim grupları, hedef/tür/müdahale metrikleri ve kapsam sınırları [model-card-synthetic.md](model-card-synthetic.md) içindedir. İki sağlayıcı birbirine karıştırılmaz; hiçbiri fizik/MILP kapasite kararını değiştirmez.

