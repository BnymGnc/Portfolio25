# Canlı Render / Vercel doğrulaması — 21 Ekim 2026

Frontend: https://buildingportfolio25.vercel.app

Backend: https://portfolio25-api.onrender.com

## Değişiklik ve bulunan hatalar

`frontend/vercel.json` artık `/api/:path*` isteklerini **`https://portfolio25-api.onrender.com/api/:path*`** hedefine iletir. `/api` öneki korunur; SPA fallback API yollarını dışlar. Üretim API tabanı boş string olarak kaldı: tarayıcı doğrudan Render'a gitmez. Kişisel/API yanıtlarında tarayıcı ve CDN cache kapalıdır. Resmî [Vercel rewrite sözleşmesi](https://vercel.com/docs/routing/rewrites) kontrol edildi.

Başlangıçta Render health 200 iken Vercel health 502 `DNS_HOSTNAME_NOT_FOUND` döndü. Yer tutucu kaldırılıp `a5067dd` commit'i normal push ile gönderilince Vercel health JSON 200 oldu. `.env.production.example` içindeki origin gerçek Vercel adresiyle güncellendi; gerçek `.env` ve platform secret değerleri okunmadı/değiştirilmedi.

İlk canlı akış ayrıca kayıt sonrası çıkışta formun kayıt modunda kaldığını ortaya çıkardı. Bu, tekrar girişin yanlışlıkla register isteği göndermesine yol açıyordu. `cd76041` düzeltmesi çıkıştan sonra modu açıkça giriş yapar. Yeni üretim JS artefaktı `/assets/index-BVP41zSQ.js` canlı HTML'de görülmeden son tarayıcı kontrolüne başlanmadı.

## Gerçek HTTPS kontrolleri

Son tam akış **14:17:52–14:18:41 UTC** (17:17–17:18 Türkiye saati), gerçek headless Chrome ve yeni, ayrı QA hesabıyla tamamlandı. Son akışta GET tekrarına ihtiyaç olmadı; yakalanmamış tarayıcı hatası yoktu.

| Kontrol | Gerçek sonuç |
| --- | --- |
| Render `/api/health` | Kimlik doğrulama olmadan JSON 200 |
| Vercel `/api/health` | JSON 200, `Cache-Control: private, no-store`; backend sürümü 0.4.0 |
| API / SPA ayrımı | Bilinmeyen `/api/...` JSON hata; `/scenario` HTML uygulaması |
| Kayıt ve tanıtım | Gerçek tarayıcı formu ve atlama işlemi başarılı |
| Çerez | Secure=true, HttpOnly=true, SameSite=Lax, Path=/, host-only `buildingportfolio25.vercel.app` |
| Origin / CSRF | Mevcut izinli Vercel origin'iyle yazma başarılı; yanlış Origin veya CSRF 403 |
| Projeler | Hesaba özel dört proje / toplam sekiz bina yüklendi |
| Sorgu aktarımı | Office `project_id` ve profil `expected_calculation_id` doğru bağlama ulaştı |
| Optimizasyon | Gerçek UI üzerinden ofis hesabı; optimal, revizyon ve hesap kimliği eşleşiyor |
| Saatlik veri | Aynı hesap için önce/sonra 8.760 saatlik profil alındı |
| ML | Dağıtılan `synthetic-annual-1.1` artefaktından gerçek yıllık inference, available; fizik bağlamı eşleşiyor |
| Tarayıcı origin'i | Gözlemlenen API isteklerinin tamamı Vercel origin'inde `/api` yoluyla; doğrudan Render isteği yok |
| Çıkış | Eski oturum çereziyle `/api/projects` 401 |
| Yeniden giriş | Aynı kullanıcı, proje, son hesap ve tamamlanmış tanıtım geri yüklendi; sonrasında test oturumu kapatıldı |

Sağlık endpoint'i `data_status=not_checked` / `optimization_status=not_checked` döndürmeye devam eder; yalnız yaşam kontrolüdür. Proje/çözücü/ML işlevleri yukarıdaki ayrı isteklerle doğrulandı. Platform paneline erişilmediği için ortam değişkenlerinin içeriği okunmadı; `COOKIE_SECURE=true` ile beklenen etkin çerez davranışı ve mevcut `FRONTEND_ORIGINS` izin davranışı canlı istekte gözlendi.

Ofis QA hesabının gerçek sonucu: **1.307.500 TL yatırım**, **230.681,6 kWh/yıl enerji tasarrufu**, **154.119,8 TL/yıl net ekonomik tasarruf**, motor `4.0.0`. ML birleşik pakette elektrik **239.288,9**, toplam gaz **118.155,1 kWh/yıl** tahmin etti. Bu, ML'nin doğruluğu veya planı belirlediği anlamına gelmez; önceki rapordaki büyük gaz farkı model sınırlaması olarak geçerlidir.

Aradaki ikinci tarayıcı denemesi, hesap sonucu ekranda görünmesine rağmen sonraki snapshot isteğini doğrulayamadı. O denemede yanıt durumunun ayrıntısı kaydedilmediğinden kök neden kesinleşmedi; başarılı sayılmadı. Betik artık başarısız okuma durumunu kaydeder ve yalnız GET için bir kez sınırlı tekrar yapabilir; kayıt/hesap gibi yazma istekleri otomatik yinelenmez. Son tam akış bu tekrar mekanizmasına ihtiyaç duymadan geçti. Bu kısa kabul kontrolü yük/dayanıklılık garantisi değildir.

## Yerel kontroller ve tekrar üretim

- `cd frontend; npm.cmd test`: **15 geçti**; gerçek upstream origin, `/api` yolunun korunması, SPA ayrımı ve cache kuralları dahil.
- `npm.cmd run build`: TypeScript/Vite geçti; çıkış/giriş düzeltmesinden sonra yeniden derlendi.
- `.\.venv\Scripts\python.exe -m unittest discover -s backend -p test_deployment.py -v`: **2 geçti**; gerçek Vercel origin'li HTTPS cookie/CSRF ve PORT/single-worker kontrolleri, geçici veri kökünde.
- `python -X utf8 scripts/check_live_deployment.py --expected-asset /assets/index-BVP41zSQ.js`: son canlı akış geçti. Selenium ve Chrome gerekir. İleride frontend kodu değişirse `--expected-asset` güncellenmeli veya seçenek kaldırılmalıdır.

Yerel kanıtlar Git dışında `artifacts/live-deployment/report.json`, `live-result.png`, `last-state.png`; ilk başarısız denemeler ayrı dosyalarda korunur. Canlı sonuç ekranı açılıp görsel olarak incelendi. Parola, session cookie değeri ve CSRF anahtarı rapora/loga/Git'e yazılmaz.

## Sınırlar ve kayıt koruması

Bu görevde üç ayrı geçici QA hesabı oluşturuldu. Hesap silme endpoint'i olmadığından bu hesapların sentetik projeleri sunucuda kaldı; gerçek kullanıcı hesaplarına veya projelerine dokunulmadı. Test kimlik bilgileri yalnız süreç belleğindeydi. Oturum sonrasında sunucu yeniden başlatma/kalıcı disk deneyi yapılmadı; disk bağlama ve plan durumu platform panelinden ayrıca kontrol edilmelidir. Yeni LLM çağrısı, model eğitimi veya ücretli kaynak satın alma yapılmadı. ComStock sağlayıcısı bu canlı kontrolde ayrıca çalıştırılmadı; gerçek inference kontrolü sentetik sağlayıcı içindir.
