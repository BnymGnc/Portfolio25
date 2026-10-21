# Güncel API envanteri — 21 Ekim 2026

Bu sürüm önceki sistem incelemesindeki envanterin yerini alır. Kaynak `backend/main.py`, `models.py`, `contracts.py`, `ai_models.py`, `ml_service.py`; makine sözleşmesi `/openapi.json`, arayüz `/docs`. Güncel sözleşme kopyası `artifacts/improvements/openapi-final.json`.

## Ortak kurallar

Bütün proje endpoint’lerinde `project_id` OpenAPI’de vardır. Önce oturum açılır ve `/api/projects` listesinden hesaba ait kimlik seçilir. Middleware proje kimliğini kullanıcıya özel veri kökünde doğrular; başka kullanıcı projesi 404 döner. Eski campus-demo-25 otomatik kullanıcıya atanmaz. Proje kimliği yetki anahtarı değildir. Health/OpenAPI ve oturum başlangıcı dışında uygulama verileri kimlik doğrulama gerektirir. Yazma istekleri ayrıca Origin ve X-CSRF-Token gerektirir.

## Hesap ve ikinci ML sağlayıcısı

| Metot / yol | İşlev |
| --- | --- |
| GET `/api/auth/session` | HttpOnly cookie oturumu + kullanıcı + bellekte tutulacak CSRF; gerekirse anonim CSRF cookie |
| POST `/api/auth/register` | email/password doğrulaması, Argon2, özel dört pilot; kullanıcı/CSRF |
| POST `/api/auth/login` | Oturumu döndürür, mevcut kullanıcı projelerini korur |
| POST `/api/auth/logout` | Mevcut cookie oturumunu sunucuda iptal eder |
| POST `/api/auth/onboarding` | Kullanıcının tanıtım sürümünü kalıcı işaretler |
| GET `/api/ml/synthetic/status` | Model dosyası varlığı, kaynak/split/metrik metaverisi; eğitim başlatmaz |
| POST `/api/ml/synthetic/predict` | `context`, `building_id`, `candidate_id`; uygun motor adayı için yıllık sentetik ML + fizik + fark |

Sentetik tahmin yanıtı güçlü `Prediction` modelidir: kullanıcıya ait `base_context`, bina/adayı, model sürümü, `synthetic_simulation` kaynağı, `available/missing_model/out_of_domain/unavailable`, tahmin, fizik ve fark. Kapasite/optimizasyonda kullanılmaz. ComStock endpoint'leri korunmuştur. Spatial preview isteğine `interventions` eklendi; eksik/null alan eski sabit kayıt davranışını korur, açık karar listesi taslak evaluator'a geçirilir.

Görev 3 güncellemesi: sentetik `Prediction` ayrıca `year` ve `input_features` döndürür. İkincisi inference'a gönderilen sayısal başlangıç özellikleri/müdahale bayraklarıdır; özellik oluşturulamayan durumda null'dır. Fizik gaz referansı `heating_gas_kwh_year + non_heating_gas_kwh_year`, ML gaz hedefi toplam gazdır. Mutlak fark API'de korunur; arayüz göreli farkı aynı referanstan üretir, 1 kWh/yıl altındaki referansta yüzde göstermez. Eğitim/artefakt değişmedi. [Kapsam kontrolü ve büyük fark](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/task3-ui-report.md).

AI status artık configured'dan ayrı `service_reachable`, `last_call_status`, `last_success_at` döndürür. Son çağrı durumu kullanıcı bağlamında process belleğindedir; yeniden başlatınca not_tested olur. 429 quota/kredi ve rate limit ayrılır; kota otomatik tekrar edilmez. Tüm API/hata yanıtları no-store'dur. Detaylı saklama ve aktarım: [hesap rehberi](auth-and-storage.md).

Hata gövdesi `{detail, error:{code,message,fields:[{field,message}]}}`; girdi/anahtar değerleri yansıtılmaz.422 alan/fizik,409 revizyon/bağlam/hesap yarışması,404 kimlik,503 sağlayıcı,429 AI kota; beklenmeyen yanıt sözleşmesi500. Çözümsüz MILP HTTP200 içinde durumdur. Health veri/solver kontrol etmeden ready demez.

Context: proje, revizyon, kanonik input_hash, UUID calculation_id, engine_version4.0.0 ve varsa ayrı model_version. Eski sonuç silinmez, motor/hash uyumsuzluğu güncel sayılmaz. API aynı revizyonda yeni hesabı süre eşitliğiyle değil kimlikle ayırır.

## Endpoint tablosu

| Metot / yol | Amaç / davranış | İstek modeli / ek parametreler | Başarı yanıt modeli | Kayıt değişikliği |
| --- | --- | --- | --- | --- |
| GET `/api/health` | Erişim kontrolü; veri ve çözücü not_checked, hazır iddiası yok. [main.py:160](../backend/main.py#L160) | Gövde yok + ortak project_id | Response | Hayır |
| GET `/api/calculations/current/evidence` | Beklenen hesap kimliğiyle güncel typed karşılaştırma; kayıt değiştirmez. [main.py:165](../backend/main.py#L165) | expected_calculation_id (zorunlu) + ortak project_id | Evidence | Hayır |
| GET `/api/examples/kayseri` | Dört pilot projesinin yüklenme durumunu okur. [main.py:173](../backend/main.py#L173) | Gövde yok + ortak project_id | Response | Hayır |
| POST `/api/examples/kayseri/load` | Açık eylem; eksik pilotları oluşturur, mevcutları korur. [main.py:187](../backend/main.py#L187) | Gövde yok + ortak project_id | Response | Evet; yalnız belirtilen kapsam |
| GET `/api/projects` | Projeleri listeler; ilk varsayılan oluşturma/eski şema dönüşümü dışında okuma. [main.py:208](../backend/main.py#L208) | Gövde yok + ortak project_id | Response | Normalde hayır; ilk oluşturma/dönüşüm istisnası |
| POST `/api/projects` | Kaynak bina kimliklerinden ayrı tek/çok bina kopyası; bağımsız/ortak bağlantı. [main.py:224](../backend/main.py#L224) | ProjectCreate + ortak project_id | Response | Evet; yalnız belirtilen kapsam |
| GET `/api/campus` | Girdi, uygulanmış fiziksel baseline, profil audit ve yalnız geçerli sonuç. [main.py:249](../backend/main.py#L249) | Gövde yok + ortak project_id | Snapshot | Normalde hayır; ilk oluşturma/dönüşüm istisnası |
| PUT `/api/campus` | Revizyon ve tam fiziksel hesaplanabilirlik doğrulanır; başarısızsa dosya değişmez; başarılıysa revizyon+1. [main.py:255](../backend/main.py#L255) | CampusUpdate + ortak project_id | Snapshot | Evet; yalnız belirtilen kapsam |
| GET `/api/campus/snapshot` | GET campus ile aynı atomik bağlam/hesap kimliği görüntüsü. [main.py:306](../backend/main.py#L306) | Gövde yok + ortak project_id | Snapshot | Normalde hayır; ilk oluşturma/dönüşüm istisnası |
| POST `/api/calculate` | A/B; aynı aday evreninde GRID, elektrik kısıtsız karşılaştırma ve sabit plan duyarlılığı; sonucu arşivleyip kaydeder. [main.py:313](../backend/main.py#L313) | CalculationRequest + ortak project_id | Result | Evet; yalnız belirtilen kapsam |
| GET `/api/buildings/{building_id}/spatial` | Kat/kullanım dağılımı, kaynak ve aynı motorun önerileri; eksik veri available=false. [main.py:345](../backend/main.py#L345) | building_id (zorunlu) + ortak project_id | SpatialAnalysis | Hayır |
| POST `/api/buildings/{building_id}/spatial/evaluate` | Revizyonlu kat senaryosu; kayıt değiştirmeyen fizik/kapasite önizlemesi. [main.py:357](../backend/main.py#L357) | SpatialPreviewRequest, building_id (zorunlu) + ortak project_id | SpatialPreview | Hayır |
| GET `/api/buildings/{building_id}/profiles` | Saatlik bina profili; explicit karar durumunda tam candidate_id; beklenen hesap kimliği denetlenebilir. [main.py:372](../backend/main.py#L372) | building_id (zorunlu), package, candidate_id, expected_calculation_id + ortak project_id | BuildingProfiles | Hayır |
| GET `/api/buildings/{building_id}/packages` | Uygun tam aday kombinasyonları; eski kayıtta dört ısıtma/sabit kat uyumluluğu. [main.py:403](../backend/main.py#L403) | building_id (zorunlu) + ortak project_id | BuildingPackages | Hayır |
| GET `/api/calculations/last` | Son dosyayı tarihsel de döndürür; current için proje/revizyon/hash/motor/kimlik birlikte denetlenir. [main.py:420](../backend/main.py#L420) | Gövde yok + ortak project_id | LastResult | Hayır |
| GET `/api/campus/profiles` | Uygulanmış başlangıç ve güncel seçilmiş tam kombinasyonların aynı zaman eksenindeki grup yükleri; beklenen hesap kimliği. [main.py:432](../backend/main.py#L432) | expected_calculation_id + ortak project_id | ProjectProfiles | Hayır |
| GET `/api/export/{file_format}` | inputs/result/legacy auto CSV veya JSON; result revizyon+hesap kimliği gerektirir; bağlam ve kararlar dahil. [main.py:469](../backend/main.py#L469) | file_format (zorunlu), scope, revision, expected_calculation_id + ortak project_id | CSV/JSON indirme eki | Hayır |
| GET `/api/ai/status` | Yalnız yapılandırma boolean/model/prompt; anahtar döndürmez; bağlantı başarısı iddiası değil. [main.py:545](../backend/main.py#L545) | Gövde yok + ortak project_id | AIStatus | Hayır |
| POST `/api/ai/explain` | Bağlamlı plan/bina açıklaması; strict çıktı, izinli fact_id ve sayısal iddia kontrolü; yalnız backend OpenAI. [main.py:550](../backend/main.py#L550) | ExplainRequest + ortak project_id | Explanation | Hayır |
| POST `/api/ai/scenario-draft` | İzinli dört alan için LLM function call taslağı; şema+sınır doğrulaması; kaydetmez/çözmez. [main.py:558](../backend/main.py#L558) | ScenarioDraftRequest + ortak project_id | ScenarioDraft | Hayır |
| POST `/api/scenarios/evaluate` | Derin kopyada geçici A/B fizik/MILP; ana kayıt, sonuç ve geçmiş değişmez. [main.py:566](../backend/main.py#L566) | ScenarioRun + ortak project_id | ScenarioEvaluation | Hayır |
| POST `/api/scenarios/apply` | Açık kullanıcı eylemiyle geçici senaryonun girdilerini PUT doğrulamasından geçirip yeni revizyonla kaydeder; planı kaydetmez. [main.py:578](../backend/main.py#L578) | ScenarioRun + ortak project_id | Snapshot | Evet; yalnız belirtilen kapsam |
| POST `/api/scenarios/counterfactual` | Seçili müdahale zorunlu tutulup yeniden çözülür; geçici, nedensellik iddiası yok. [main.py:586](../backend/main.py#L586) | CounterfactualRequest + ortak project_id | ScenarioEvaluation | Hayır |
| GET `/api/ml/status` | Artefakt/kaynak, train/validation/test sayıları, hedef/tür MAE, domain ve sınırlar. [main.py:608](../backend/main.py#L608) | Gövde yok + ortak project_id | ModelStatus | Hayır |
| POST `/api/ml/predict` | Bağlamlı yıllık ComStock inference; ülke/kategori/aralık/hash; model eksik/kapsam dışı açık durum. [main.py:612](../backend/main.py#L612) | PredictRequest + ortak project_id | Prediction | Hayır |
| POST `/api/ml/project-predict` | Yerel proje için açık kapsam dışı ML ve ayrı gerçek fizik sonucu; sahte yerel tahmin yok. [main.py:620](../backend/main.py#L620) | ProjectPredictRequest + ortak project_id | Prediction | Hayır |

Kod/OpenAPI güncel uygulama işlem sayısı: **26**. Tüm satırlarda auth/yetki yoktur. Spatial, bina/proje profilleri, paket, snapshot/sonuç, evidence/sensitivity ve AI yanıtları güçlü Pydantic response modelleridir. Kaynak/metadata sözlükleri esnek alan olarak açıkça tutulur; uygulama sırları bu alanlara eklenmez.

## İstek modellerinin önemli alanları

- CampusUpdate: revision, buildings, scenario; optional name/profile_settings/connection_groups/sensitivity_settings. Bina alan/zon/sistem ilişkisi ve bütün adayların hesaplanabilirliği diske yazmadan denetlenir.
- Building.interventions: roof/insulation/lighting/schedule/heat_pump; applied/mandatory/candidate/excluded. Null eski spatial_selection sabit davranışını korur; explicit list yeni sınırlı şablon evrenini açar.
- CalculationRequest: revision, modeA/B, time_limit_s0,01–60. Çözücü iki yöntem için ayrı süre sınırı kullanır; toplam HTTP süresi sınırdan uzun olabilir.
- ExplainRequest: context, scopeplan/building, building_id?, question≤1000. ScenarioDraftRequest: context, question.
- ScenarioRun: context, changes1–4, mode, time_limit_s≤15; izinli alanlar bütçe/hedef/elektrik ve gaz bedeli. CounterfactualRequest: context, building_id, intervention.
- PredictRequest: context, country, özellikler; yıllık başlangıç elektrik/gaz, alan/yıl/kullanım/iklim/HVAC/upgrade. Eksik alan422, eğitim dışı veri durum olarak out_of_domain; tahmin null.

## Kalıcılık ve kullanım

Sonuçlar `<stem>.result.json`; önceki raw sonuç history/proje/SHA.json. Girdiler varsayılan campus.json veya projects/proje.json; eski v1/v2 bayt yedeği korunur. Ana schema3.0 ve optional spatial1.0 devam eder. UUID/hash/motor alanları olmayan hesap tarihsel okunur; güncel gösterilmez.

JSON export güçlü bağlam, müdahale durum/maliyetleri, karşılaştırma/duyarlılık ve kaynakları taşır. CSV ek interventions_json/context_json sütunlarını taşır; eski sütunlar korunur. CSV içe alma sonuç sütunlarını uygulamaz; yalnız mevcut sentetik projenin aynı bina/kaynaklarını günceller. Genel JSON import veya kullanıcı yetkisi eklenmedi.

Otomatik FastAPI GET yolları: `/openapi.json`, `/docs`, `/docs/oauth2-redirect`, `/redoc`. OAuth redirect sayfası login uygulandığını göstermez. Swagger/ReDoc CDN varlığına bağlı olabilir; CORS OPTIONS preflight ayrı iş endpoint’i değildir.

LLM mimarisi/gerçek429 testi [ai-architecture.md](ai-architecture.md); model kaynak/metrikleri [model-card.md](model-card.md); aşamalı kontroller [improvement-report.md](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/improvement-report.md).
