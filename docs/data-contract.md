# Veri sözleşmesi v3.0

## Güncel ek sözleşme — motor 4.0.0

20 Ekim 2026: Bu bölüm aşağıdaki tarihsel sabit-kat-seçimi ve LLM-yok açıklamalarının yerini alır. Yürürlükteki alanlar [OpenAPI envanterinde](api-inventory.md), AI sınırları [AI mimarisinde](ai-architecture.md), ML verisi [model kartında](model-card.md) bulunur.

- Girdi şeması 3.0 kalır. `Building.interventions=null` eski davranışı korur: eski `spatial_selection` eylemleri zorunlu yeni yatırım, kabuk/ısı pompası uygunlukla adaydır. Açık liste `{kind:roof|insulation|lighting|schedule|heat_pump,state:applied|mandatory|candidate|excluded}` yeni karar politikasıdır; otomatik dosya dönüşümü yapılmaz. UI açık geçiş sunar. Çatı/kabuk çakışması ve sistem koşulları geçerlidir.
- Uygulanmış eylemler yıllık referans girdilerinden fiziksel başlangıca hesaplanır; yeni CAPEX/bakım/tasarruf tabanı sıfırdır. Zorunlu eylem yeni bütçeye dahildir. Her aday `candidate_id`, tüm `interventions`, `intervention_costs` taşır. Bina başına en çok 32 şablon kombinasyonu; zonlar için sınırsız alt küme üretilmez. `baseline_packages` uygulanmış başlangıcı açık taşır.
- Hesap bağlamı: `project_id`, `input_revision`, SHA-256 `input_hash`, UUID `calculation_id`, `engine_version`, nullable `model_version`. Fizik sonucu ML kullanmadığı için model_version=null. Sadece aynı revizyon yeterli değildir. Motor sürümü, proje veya hash farklıysa eski sonuç güncel değildir. Çözüm süresi kimlik değildir.
- Snapshot, paket/profil, kanıt/duyarlılık, AI ve export bağlamı denetlenir. `expected_calculation_id` farklıysa 409; bina profili yeni politikada tam `candidate_id` kabul eder. Tam yıl 8760/8784 zaman damgasının tümüdür, bina piklerinin toplamı kullanılmaz.
- Yazma, birleşmiş adayın şema/ilişki/fizik ve snapshot response doğrulaması geçtikten sonra olur. Başarısız istekte dosya ve revizyon korunur. Hata biçimi `{detail,error:{code,message,fields:[{field,message}]}}`; anahtar veya ham hassas girdi eklenmez. Sağlık kontrolünde veri/çözücü `not_checked` erişimi hazırlık diye sunmaz.
- CSV ek `interventions_json` ve `context_json` alanlarını taşır; eski CSV gönderilmeyen yeni politikayı silmez. Sonuç export'u aynı UUID/revizyonu şart koşar; başlangıç export'u ayrı kapsamdır. Eski hesap dosyaları tarihsel saklanır, yeni hesapta arşivlenir.
- Seçilen yeni çatı için ayrı `roof` duyarlılık ekseni hedef U değerini değiştirir. Kabuk azaltımını çatı diye adlandırmaz. Sabit plan değerlendirmesidir; yeniden optimizasyon/olasılık değildir.
- AI açıklaması ve senaryo taslağı güncel bağlam taşır; geçici hesap dosya yazmaz. Uygulama yalnız açık onaylı apply endpoint'iyle olur. ML inference ayrı model_context taşır; fizik sonuçları veya saatlik yükler ML ile değiştirilmez.

## Önceki sürümlerin alan açıklamaları

## Kayseri pilotu ve isteğe bağlı kat alt modeli

Ana şema/yazma endpoint'leri korunur. Eski v3 dosyaları yeniden yazılmaz; `Building.spatial=null`, `spatial_selection` boş seçim ve `Campus.pilot=null` varsayılanları geriye uyumludur. Önceki yedekli v1/v2 dönüşümleri sürer. Yeni alt model `spatial.schema_version=1.0`; gerçek ölçüm alma endpoint'i değildir. use_type seçeneklerine Konut/Ofis/Otel eklendi; bunlar sınırlı sentetik örnek kullanım türleridir.

| Yol | İşlev |
| --- | --- |
| GET /api/examples/kayseri | title/dataset ve dört projenin id/name/building_count/budget_try/connection_group_count/loaded alanları; yazmaz |
| POST /api/examples/kayseri/load | Açık yükleme; sabit kimlikli dört ayrı örnek oluşturur, mevcutlarını korur; created/preserved döner. Çakışmada 409. |
| GET /api/buildings/{id}/spatial?project_id=… | available/project_id/input_revision/building_id; varsa spatial/selection/baseline/recommendations/weather/source. Kat verisi olmayan kayıtta available=false, açıklama. |
| POST /api/buildings/{id}/spatial/evaluate?project_id=… | revision, selection, package, isteğe bağlı spatial taslağı. Salt okunur birleşik hesap; revizyon yarışı 409, uygunsuz/geçersiz model 422. |

`spatial`: floors[{id,name,area_m2,zones[]}], systems[{id,name,kind,served_zone_ids,source}], detailed_zones, weather_scenario, yıllık cooling_electricity/common_system_electricity/dhw_gas kWh alanları; çatı U hedefi ve birim yatırım varsayımları/source. Zone'da id/name/use/area_m2/height_m, program gün/kullanım/hizmet saatleri ve doluluk/kritik hizmet katsayıları, cephe/pencere/yön/U değerleri, çatı/zemin teması, hava değişimi, ışık/hedef ışık/cihaz W/m², sistem referansları, dhw_weight, common_area, kind/source/missing_information bulunur. Tam sınırlar spatial_models.py/OpenAPI'dedir.

Her katın zon alanı ve binanın kat alanları eşit olmalı; kimlikler benzersiz ve sistem hizmet referansları tutarlı olmalıdır. Sıcak su gazı non_heating_gas_kwh_year içindedir; eklenmez. Hesaplanmış ışık/cihaz/soğutma/ortak tüketim bina elektriğini aşarsa 422; kalan tüketim silinmez.

`spatial_selection`: roof/lighting/schedule boolean, zone_ids (boşsa tüm uygun alanlar), schedule_review_ack. Çatı bina çatısında bir defadır; zone_ids ışık/program kapsamıdır. Schedule için açık inceleme kabulü ve uygun kritik olmayan alan gerekir. Çatı + insulation/combined çakışır; hariç paket olur veya önizleme 422 verir. Kat seçimlerini kalıcı yapmak için mevcut PUT /api/campus kullanılır.

Dağılım yanıtı: totals (elektrik/yakıt/faydalı ısı), by_floor, by_use, zones; bileşenler heating_electricity/cooling/lighting/devices/unseparated_electricity/heating_fuel/hot_water_fuel/unseparated_fuel/common_systems. SHARED satırı katlara dağıtılmamış ortak ekipmandır; alanı 0, yoğunluğu tanımsızdır. Faydalı ısı nihai enerjiye eklenmez. reconciliation elektrik/yakıt farklarını taşır; tolerans dışı sonuç gösterilmez.

Önerilerde status=calculated/calculated_review_required/review_only; finding, affected kat/zonlar, effect, conditions, missing_information. review_only effect=null; sahte tasarruf yok. Preview önce/sonra PackageResult, elektrik/yakıt ve maliyet farkı, yatırım, bütçe, aynı proje bina/grup capacity_checks, dağılım_before/after ve comfort_modelled=false taşır. Diğer binalar baz durumdadır; önizleme bir portföy çözümü değildir.

Kaydedilmiş kat seçimleri ısıtma paket evrenine sabit taban olarak bir kez katılır. Müdahalesiz baseline ayrıdır. PackageResult ek spatial_investment_try/spatial_interventions alanlarını taşır. Maliyet duyarlılığı kat yatırımlarını da fiyatlar. Kat eylemlerinin kendisi bu sürümde MILP tarafından seçilmez; ısıtma paketleri seçilir.

JSON tüm yapı/kaynağı içerir. CSV ek spatial_model_json/spatial_selection_json ve project_json.pilot taşır; eski CSV eksik yeni alanları silmez. Önceki sonuçlar yeni hesap yazılmadan önce `data/history/<proje>/<sha256>.json` içinde birebir arşivlenir. Arşivler mevcut tek son-hesap API'sine karışmaz; tarihçe tarama arayüzü bu kapsamda yoktur.

Kaynaklar, formüller, pilot dağılımı, gerçek kontroller ve kapsam sınırları [pilot-kayseri.md](pilot-kayseri.md) içindedir.

## Güncel proje sözleşmesi — 20 Ekim 2026

Önceki endpoint adları uyumluluk için korunur. Aşağıdaki v2 alan/aşama kayıtları tarihçedir; bu bölüm sekiz bina ve tek ortak sınır zorunluluğunun yerini alır. Eski örnek JSON belgeleri kendi şema/revizyonlarının tarihsel örnekleridir; güncel kaynak OpenAPI ve modellerdir.

### Proje ve depolama

- `GET /api/projects`: projects satırlarında id, name, building_count, project_type (single_building/multi_building), revision.
- `POST /api/projects`: `{name, building_ids, connection_mode:"independent"|"shared"}`. Seçili kaydın seçilen binalarını bağımsız dosyaya kopyalar; id/name/building_count döner. Tek bina için bir kimlik seçilir. Varsayılan independent; shared aynı fiziksel besleme varsayımıdır. Kaynak değişmez, yeni projede revision=1.
- Mevcut veri/hesap/profil/export endpoint'leri `?project_id=project-<12 küçük hex>` kabul eder. Yoksa `campus-demo-25` kullanılır. Geçersiz kimlik 422; olmayan proje 404. Kimlik dosya yolu olamaz.
- Varsayılan proje mevcut `DATA_FILE`; diğerleri aynı dizinde `projects/<id>.json` ve `<id>.result.json`. Bağımsız kayıtlardır. Proje silme endpoint'i bu aşamada yoktur.
- Kalıcı `schema_version=3.0`; `id` varsayılan veya yeni proje kimliği; `name` düzenlenebilir. `buildings`: 1–50, benzersiz `Bnn`. API bu aşamada mevcut sentetik kaynağın binalarını kopyalar/düzenler; gerçek veri alımı yoktur. Proje türü bina sayısından türetilir.
- v2 dosyası baytları değişmeden `.v2-backup.json` yedeğine alınır; kullanıcı alanları korunarak şema 3.0, revision+1 ile yazılır. Eski ortak sınır G01'e taşınır. v1 kendi yedeğiyle v3'e doğrudan geçer. Eski sonuç dosyası silinmez; eski revizyon güncel sayılamaz. Dönüşüm tekrarlanmaz.

### Bağlantı ve varsayımlar

`connection_groups`: her satır `id:Gnn`, name, building_ids, capacity_kw (>0, ≤10⁷ kW), source. Her bina tam bir gruptadır; boş/tekrarlı/yabancı üyelik reddedilir. Bina connection_limit_kw ayrıca uygulanır. Bütçe bütün proje için ortaktır. Birden fazla bağımsız gruba tek toplam kapasite uygulanmaz.

`scenario.electric_capacity_kw` eski istemciler için korunur. Tek grupta grup kapasitesiyle eşleştirilir; iki taraf birden çelişkili değiştirilirse 422. Çok grupta bu eski alan optimizasyonda/grafikte ortak sınır değildir. Yeni UI çok grupta bu alanı gizler ve ayrı grup kapasitelerini düzenletir.

Bina ekleri: heating_system = gas_boiler/electric_resistance/existing_heat_pump/other; heat_distribution = hydronic_assumed/low_temperature_water/high_temperature_water/none/unknown; insulation_allowed boolean; system_source. Eski kayıtta gas_boiler/hydronic_assumed yalnız sentetik varsayımdır. Uygun olmayan müdahaleler paket evreninden çıkarılır. Paket endpoint'inde `scope=heating_only`, `excluded_packages:[{package,reason}]` ve yalnız uygun packages döner; her zaman dört uygun seçenek beklenmez. Hariç paket profili isteği 422 döner. Soğutma dönüşümü yoktur.

`sensitivity_settings`: reference_date/source; scop, investment, insulation için `{low,high}` çarpanları; 0,1–3 ve low≤1≤high. Temel=1. Varsayılanlar sırasıyla .85/1.15, .8/1.2, .75/1.25. Birlikte değişen birleşik uç senaryo değildir; her seferinde tek parametre değişir.

### Sonuçlar

Baseline/after ek `capacity_checks`: kind=building/group, id/name, peak_kw/peak_timestamp, limit_kw, max_excess_kw, violation_hours. Bütün saatler denetlenir. Çok grupta toplam electric_peak_kw proje talebi tanısıdır; ortak trafo piki değildir. capacity_utilization_pct gruplardaki en yüksek kullanım yüzdesidir.

CalculationResult ekleri:

- project_id, grid_constraints_applied;
- decision_evidence: project_id/input_revision/mode, package_universe, ratio_definition, scope, methods.ratio/without_grid/grid. Yöntemlerde status/message/solver/evaluation. Oran sezgiseli solver=null, optimum kanıtı yok; B hedefi sonradan denetlenir. Elektrik kısıtsız MILP bütçe, uygunluk ve B hedefini korur.
- evaluation: after, investment_try, budget_remaining_try/budget_met, energy_savings_kwh_year/pct, net_savings_try_year, target_met, capacity_met, capacity_violations ve selected_packages. Aday yoksa null; uydurma plan yok.
- sensitivity: fixed_plan=true/reoptimized=false, method/settings ve 9 rows; parameter, level, multiplier, status, evaluation/effective_assumptions. Fiziksel aralık dışı status=invalid_assumptions ve evaluation=null. Uygun GRID planı yoksa rows boş, açık message vardır. İstatistiksel aralık/olasılık değildir.

Tüm karşılaştırmalar bir hesap isteğindeki aynı kayıt ve uygun paketlerden üretilir; sonuçla birlikte kaydedilir ve hesap kimliğine dahildir. GRID çözücü süre sınırı ayrı elektrik kısıtsız çözücü için de uygulanır; toplam API süresi iki çözüm ve duyarlılık hazırlığını kapsar. Büyük veri/çok grup performans garantisi yoktur.

`/api/campus/profiles` proje toplamı before_kw/after_kw yanında `project_id` ve `groups:[{id,name,capacity_kw,before_kw,after_kw}]` döner. Tek grup capacity_kw eski skaler olarak korunur; çok grupta skaler null. UI yalnız seçilen grubun profillerini ve sınırını çizer; grup yıllık integralleri ve toplamları da doğrulanır.

Export kimliği/revizyon koruması sürer; export_metadata.project_id eklenir. Yeni projelerin dosya adlarında proje kimliği vardır. CSV'ye project_json (id/name/gruplar/duyarlılık ayarı), system_assumptions_json, decision_evidence_json, sensitivity_json eklenir. JSON tam sonuçları taşır. CSV yalnız mevcut projenin aynı bina kimliklerini günceller; başka proje kimliği reddedilir; eski şablonda gönderilmeyen yeni alanlar korunur. Yeni proje oluşturmak CSV içe alma değildir.

### Ortam

Backend `.env` konumu kaynak dosyasına göre çözülür; dotenv override=false. Anahtar/model ortam ayarları Pydantic veri modellerinde bulunmaz; API/export/frontend'e eklenmez. Boş anahtar sağlık/optimizasyon için engel değildir. LLM endpoint'i veya çağrısı yoktur.

## Önceki sürüm kararlarının tarihçesi

Çalışan şema: backend/models.py; frontend: frontend/src/types.ts. Makine şeması GET /openapi.json; etkileşimli belge /docs. [sample-campus.json](sample-campus.json) hesaplanmamış örnektir; [sample-calculation.json](sample-calculation.json) motorun ürettiği örnek A planıdır. Motor bu dosyaları sonuç olarak okumaz.

## Endpoint’ler

| Yöntem / yol | Davranış |
| --- | --- |
| GET /api/health | status=ok, version=0.2.0, optimization_status=ready |
| GET /api/campus | campus, baseline, profile_audit, calculation, after, investment_plan |
| PUT /api/campus | revision, buildings, scenario, isteğe bağlı profile_settings; doğrular, birlikte kaydeder, revizyon artırır, GET biçimi döndürür |
| POST /api/calculate | Kayıtlı revizyon üzerinden A/B MILP; CalculationResult döndürür ve kaydeder |
| GET /api/buildings/{id}/profiles?package=none | Zaman damgalı sentetik profil ve paket özeti; kapasite uygunluğu garantisi değil, aritmetik paket değerlendirmesidir |
| GET /api/export/json | GET yanıtının güncel sonuç/kaynak/varsayımlarla UTF-8 JSON çıktısı |
| GET /api/export/csv | BOM UTF-8, virgül ayrılmış 8 bina satırı; varsayımlar ve güncel plan sütunları |

Başarı 200; doğrulama 422; revizyon çakışması/başka hesap sürmesi/hesap sürerken girdi değişmesi 409; bilinmeyen bina/biçim 404. Çözümsüzlük bir çözücü sonucudur, HTTP hatası değildir. Ek alanlar, NaN ve sonsuz sayılar reddedilir. Hesaplama kaydedilmemiş frontend formunu kullanmaz.

## Uyumluluk ve kalıcılık

1.0 dosya doğrulanıp bir kez .v1-backup.json ile yedeklenir; 2.0’a dönüşür, revizyon 1 artar. Önceki tüketimler ve senaryo korunur; ek varsayımlar migration_notes içinde açıklanır. Bilinmeyen ısıtma dışı gaz eski kayıtta sıfır varsayılır. Eski biçimli PUT yeni alanları sıfırlamaz; gönderilmeyen alanlar korunur.

Kampüs DATA_FILE içinde, hesap aynı kökte <stem>.result.json dosyasında atomik değişimle saklanır. Hesap yalnız input_revision == campus.revision ise gösterilir/dışa aktarılır. Eski sonuç fiziksel dosyada kalabilir; güncel sonuç sayılmaz. Hesap sırasında girdi değişirse sonuç kaydedilmez. Tek süreç/worker; aynı anda tek hesap.

## Kampüs girdisi

campus: schema_version=2.0, id=campus-demo-25, name, revision, provenance, buildings, scenario, profile_settings, migration_notes, optimization_status=ready.

### Bina

| Alan | Birim / doğrulama |
| --- | --- |
| id | Sekiz benzersiz B01–B08 |
| name | 1–100 karakter; boş olamaz |
| use_type | Eğitim / Araştırma / İdari / Sosyal / Konaklama |
| area_m2 | (0, 1.000.000] m² |
| year_built | 1800–2100 tamsayı |
| electricity_kwh_year | [0, 10⁹] kWh/yıl elektrik |
| heating_kwh_year | [0, 10⁹] kWh/yıl ısıtma doğalgazı giriş enerjisi |
| non_heating_gas_kwh_year | [0, 10⁹] kWh/yıl diğer doğalgaz |
| peak_electric_kw | Eski referans, [0, 10⁶] kW; hesapta kullanılmaz |
| connection_limit_kw | Bina bağlantı sınırı, (0, 10⁶] kW |
| retrofit | Düzenlenebilir varsayımlar, aşağıda |
| provenance | kind, source, seed; örnek synthetic/25 kaynağı korunur |

Köken sözlüğü measured / external_simulation / synthetic ayrımını destekler; örnek kampüs endpoint’i mevcut sentetik kökeni korur. Gerçek veri alma akışı yoktur.

### retrofit

| Alan | Birim / aralık |
| --- | --- |
| boiler_efficiency | (0, 1] |
| insulation_relevant_heat_fraction | [0, 1] ilgili faydalı ısı payı |
| insulation_reduction_fraction | [0, 1] ilgili ısı azaltımı |
| heat_pump_scop | [1, 10] mevsimsel eşdeğer, saatlik COP değildir |
| heat_pump_coverage_fraction | [0, 1] kapsanabilir ısı payı |
| heat_pump_capacity_kw_thermal | [0, 10⁶] kW termal |
| insulation_cost_try_m2 | [0, 100.000] TL/m² brüt alan |
| heat_pump_cost_try_kw | [0, 10⁶] TL/kW termal |
| heat_pump_fixed_cost_try | [0, 10⁹] TL |
| annual_maintenance_fraction | [0, 1] toplam paket yatırımına ek yıllık bakım oranı |
| reference_date, source | ISO tarih ve 1–500 karakter varsayım kaynağı |

### scenario

| Alan | Birim / aralık |
| --- | --- |
| budget_try | TL, [0, 10¹²], iki modda da sınır |
| savings_target_pct | %, [0, 100], B için zorunlu hedef |
| electric_capacity_kw | Kampüs ortak besleme sınırı, (0, 10⁷] kW |
| electricity_price_try_kwh | [0, 1.000] TL/kWh elektrik |
| heating_price_try_kwh | [0, 1.000] TL/kWh, tüm doğalgaz için |
| price_basis | reference_date, source: fiyat varsayım kaydı |
| electricity_emission_kg_kwh, gas_emission_kg_kwh | [0, 10] kg CO₂e/kWh |
| emission_basis | reference_date, source: emisyon varsayım kaydı |

profile_settings: year (2020–2100), timezone=Europe/Istanbul, seed (0–2³²−1), kind=synthetic, source. Şekiller bu parametrelerden yeniden üretilir; büyük saatlik diziler kampüs dosyasına gömülmez. Profil algoritması v1 kaynak metninde etiketlidir.

## Mevcut ve sonraki özet

baseline ve hesap varsa after aynı dönemi/birimleri kullanır:

| Alan | Tanım |
| --- | --- |
| area_m2 | Kampüs alanı |
| electricity_kwh_year | Elektrik, sonuçta HP elektriği dahil |
| heating_kwh_year, non_heating_gas_kwh_year, total_gas_kwh_year | Isıtma gazı / diğer gaz / toplam gaz |
| total_energy_kwh_year | Elektrik + tüm gaz |
| intensity_kwh_m2_year | Toplam enerji / toplam alan |
| energy_cost_try_year, maintenance_cost_try_year | Enerji bedeli ve ek bakım |
| operating_cost_try_year | Enerji + ek bakım |
| emissions_kg_year | Varsayımsal kg CO₂e/yıl |
| electric_peak_kw, electric_peak_timestamp | Eşzamanlı toplam yük piki ve ISO damgası |
| electric_peak_sum_kw | Kullanımdan kaldırılan diagnostik: ayrı bina pikleri toplamı; UI/kısıt bu alanı kullanmaz |
| capacity_utilization_pct | 100 × eşzamanlı pik / ortak sınır |

profile_audit: kind, source, timezone, start, end_exclusive, interval_hours=1, hour_count, all_consistent. Bina satırları: building_id; annual_electricity_kwh, integrated_electricity_kwh, electricity_error_kwh; annual_useful_heat_kwh, integrated_useful_heat_kwh, heat_error_kwh; electric_peak_kw, connection_limit_kw, consistent. Faydalı ısı = ısıtma gazı × verim. Elektrik/ısı farkı kWh.

## Hesaplama

Örnek POST gövdesi: {"revision": 11, "mode": "B", "time_limit_s": 10}. Revizyon kayıtla eşleşir. Mode A/B; süre 0,01–60 sn, varsayılan A/10 sn. A enerji tasarrufunu en yüksek yapar; B hedefe en az yatırımla ulaşır. Bütçe ve her iki kapasite iki modda zorunludur.

CalculationResult:

- input_revision, mode, status, message.
- solver: name, ham status_code/message; time_limit_s, solve_seconds, hazırlık dahil total_seconds; mip_gap (oran veya null), mip_node_count, objective_bound, objective_unit, optimality_proven.
- A amaç sınırı kWh/yıl tasarruf üst sınırıdır; B sınırı TL yatırım alt sınırıdır. Çözücü amaçları 10⁶ ile ölçeklenir, API fiziksel birime geri çevirir. Süre sınırı yalnız çözücüye uygulanır; hazırlık/JSON dahil değildir.
- baseline, varsa after, selected_packages (uygun planda tam sekiz); investment_try, energy_savings_kwh_year, energy_savings_pct, net_savings_try_year, emissions_savings_kg_year, simple_payback_years, target_met, warnings.
- Başlangıç enerjisi sıfırsa tasarruf yüzdesi null; net tasarruf ≤0 ise geri ödeme null. Negatif tasarruflar korunur.

| status | Yorum |
| --- | --- |
| optimal | Bağımsız uygunluk denetimi geçti; optimum kanıtlandı |
| feasible_limit | Uygun aday var; optimum kanıtlanmadı |
| limit_no_solution | Sınırda aday yok; imkânsızlık kanıtı değil |
| infeasible | Kısıtlar birlikte sağlanamıyor; plan/sonra yok |
| failed | Çözücü veya aday/uygunluk doğrulaması hatası; plan yok |

Paket alanları: building_id/name, package (none/insulation/heat_pump/combined), investment_try; electricity_kwh_year, heating_gas_kwh_year, non_heating_gas_kwh_year; useful_heat_before_kwh_year, useful_heat_after_kwh_year, heat_pump_heat_kwh_year, heat_pump_electricity_kwh_year, backup_boiler_heat_kwh_year, unmet_heat_kwh_year (bu yedek varsayımında 0); energy_savings_kwh_year, net_savings_try_year, maintenance_cost_try_year, electric_peak_kw, connection_limit_kw, simple_payback_years. Tam alanlar OpenAPI ve örnek JSON’da.

Saatlik endpoint: input_revision, building_id, package, kind, source, timezone, interval_hours; aynı uzunluk/sırada timestamps, baseline_electricity_kw, electricity_kw, useful_heat_before_kw, useful_heat_after_kw, heat_pump_heat_kw, backup_boiler_heat_kw ve summary. Diziler 1 saat ortalama kW, damgalar ISO 8601 +03:00, saat dilimi IANA. Yıllık elektrik/yakıt kWh/yıl, yatırım TL, tarifeler TL/kWh.

## Dışa aktarma

Sonuç hesaplanmadıysa calculation, after ve investment_plan null. Çözümsüz/sınırlı-adaysız hesap varsa calculation çözücü durumunu içerir ama after/plan null olur. Güncel revizyonun uygun planı varsa JSON hem girdileri hem sonuçları içerir.

CSV’nin ilk 18 eski sütunu korunur. Ek sütunlar: non_heating_gas_kwh_year, connection_limit_kw, retrofit_assumptions_json, valuation_assumptions_json, profile_settings_json, selected_package, investment_try, after_electricity_kwh_year, after_heating_gas_kwh_year, energy_savings_kwh_year, net_savings_try_year, simple_payback_years, solver_status, solver_gap, optimality_proven. Varsayım JSON hücreleri tarih/kaynak içerir. Sonuç yoksa sayısal plan hücreleri boş ve solver_status=not_calculated. JSON ayrıca tam kampüs özeti ve çözücü detayını taşır.

CSV UTF-8 BOM/virgül, ondalık nokta. Kullanıcı adları =,+,-,@ ile başlıyorsa formül riskini etkisizleştirmek için başına tek tırnak eklenir. Arayüz yalnız gösterimde Türkçe sayı biçimi kullanır.

## Öneriler ve bilinmeyenler

Ölçüm içe aktarma, saatlik COP kaynağı ve çok kullanıcı veritabanı sözleşmesi henüz yoktur. Model sınırları assumptions.md içinde.

## Üçüncü aşama: geriye uyumlu salt okunur ekler

Mevcut v2.0 şema, PUT/POST gövdeleri ve sonuç/export yanıtları değiştirilmedi. Motor ve kayıt dönüşümü aynı kalır. Demo arayüzü için şu GET endpoint’leri eklendi:

| Yol | Yanıt ve amaç |
| --- | --- |
| /api/buildings/{id}/packages | input_revision, building_id, kind=synthetic, packages: motorun aynı bina/profil/tarifeyle hesapladığı dört PackageResult. Girdi veya sonuç kaydetmez. |
| /api/campus/profiles | input_revision, result_input_revision, result_mode, kind, source, timezone, interval_hours, timestamps, before_kw, after_kw, capacity_kw. Tüm binalar aynı saatlerde toplanır; yalnız güncel uygun plan varsa after_kw dizisi bulunur. Sonuç yok/eski/çözümsüz ise after_kw null. |
| /api/calculations/last | current_revision, is_current, calculation. Kaydedilmiş en son hesap revizyonu eski olsa da tarihsel inceleme için döner. Güncel sonuç ve export endpoint’lerine eski hesap eklemez. |

Grafik istemcisi revizyon/mod eşleşmesini, tam yıllık saat sayısını, kesintisiz 1 saat zaman eksenini, sonlu ve negatif olmayan yükleri ve yıllık elektrik integrallerini kontrol eder. Eksik profil sıfırla doldurulmaz; grafik yerine anlaşılır hata ve yeniden yükle gösterilir.

Kaydedilmemiş bina/senaryo, mod değişikliği ve kaydedilmiş yeni revizyon eski sonucu UI’da güncel değil olarak işaretler. Eski sonuçta güncel bütçe veya saatlik grafikle karışık karşılaştırma yapılmaz. Tarihsel kayıt ayrı tutulur; export güncel sonuç sözleşmesini korur.

CSV içe alma API sözleşmesine yeni yazma endpoint’i eklemez: yalnız uygulamanın mevcut sentetik CSV dışa aktarma şablonu tarayıcıda doğrulanır, kullanıcı önizlemeyi uyguladığında mevcut PUT kullanılır. Sekiz benzersiz kimlik, kaynak, ortak senaryo ve sayılar denetlenir. Hesap/sonuç sütunları içe alınmaz; nested varsayımlar API’de de doğrulanır. Geçersiz dosya kayıt değiştirmez.

## Dördüncü aşama: atomik kayıt ve kapsamlı dışa aktarım

Yazma/hesap istekleri ve v2.0 kalıcı veri şeması korunur; eski kayıt dönüşümü gerekmez. Geriye uyumlu ekler:

- `GET /api/campus/snapshot`: mevcut CampusResponse alanları + `calculation_id`. Kilit altında tek kayıt/hesap görüntüsü; frontend bunu kullanır.
- `/api/calculations/last`: ek `calculation_id` alanı.
- Kimlik, CalculationResult JSON'unun SHA-256 özetidir. Aynı revizyon/mod yeniden hesaplandığında süreler de değişebildiğinden yeni kimlik beklenir; bu bir mühendislik güvence sertifikası değildir.
- `/api/export/{json|csv}?scope=inputs&revision=26`: yalnız kaydedilmiş başlangıç girdileri, kaynak/varsayım ve baseline; calculation/after/investment_plan null. Dosya `portfolio25-grid-inputs-r26.*`.
- `?scope=result&revision=26&expected_calculation_id=<snapshot kimliği>`: aynı hesap kimliği/revizyonu zorunlu; farklı kayıt veya aynı revizyonda yeni hesap 409; eksik koruma parametresi 422. Başarılı hesap dosyası `portfolio25-grid-result-r26-A.*`. Çözümsüz hesap da çözücü durumuyla dışa aktarılır; uygun plan yoksa after/plan null.
- Eski istemciler için varsayılan `scope=auto` eski otomatik kapsamı/dosya adını korur. Yeni UI her zaman açık kapsam ve revizyon gönderir; sonuçta ayrıca kimlik gönderir.
- JSON'a `export_metadata`: kind, input_revision, calculation_revision, calculation_id, calculation_mode, exported_at_utc ve peak_definition eklenir.
- CSV'nin eski sütunları korunur; ekler: export_kind, calculation_revision, calculation_id, calculation_mode, exported_at_utc, campus_before_json, campus_after_json, solver_json, selected_package_json, data_provenance_json. Önce/sonra kampüs özetleri ve tam çözücü bilgisi böylece CSV'de de bulunur; paket ve kaynak JSON hücreleri bina bazındadır.

Sunucu dışa aktarım için değişmez anlık görüntüyü kilit altında doğrular; kontrol/indirme arasında yeni kayda geçmez. İstemcide kaydedilmemiş değişiklik her iki kapsamı engeller; yalnız eski hesap bulunması kaydedilmiş yeni başlangıç verisinin açıkça dışa aktarılmasını engellemez. Sonuç kapsamı yeniden hesaplama ister.

