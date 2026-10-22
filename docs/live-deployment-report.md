# Canlı PostgreSQL kabulü — 22 Ekim 2026

Frontend: https://buildingportfolio25.vercel.app · Backend: https://portfolio25-api.onrender.com.

**Sonuç: canlı ana akış ve kontrollü yeniden yayın sonrası kalıcılık geçti.** Gerçek Chrome kontrolü 22 Ekim 2026 **12:26:10–12:28:46 Türkiye saati** arasında tamamlandı. Backend commit'i doğrudan Render ve Vercel `/api/health` yanıtında `29621834b1dc523e9d38e3b1552b84a2c243ef9b`; `storage.status=postgresql`. Üretim frontend asset'i `/assets/index-COwvB1eI.js` beklentisi doğrulanmadan QA kaydı başlatılmadı.

| Kontrol | Gerçek sonuç |
| --- | --- |
| PostgreSQL ve şema | Her iki origin'de sağlık JSON 200; şema kontrolü geçti. Fizik/çözücü hazır durumu yalnız health'ten çıkarılmadı. |
| Kayıt, giriş ve çıkış | Ayrı geçici QA hesabıyla gerçek form; aynı kullanıcı/projeler tekrar açıldı. Logout eski çerezi 401 ile reddetti. |
| Cookie / CSRF / Origin | Secure + HttpOnly + SameSite=Lax + Path=/ ve Vercel host-only cookie; yanlış CSRF ve Origin 403. |
| Özel pilot | Dört proje / sekiz bina; doğru project_id ile ofis hesabı. |
| Optimizasyon | Gerçek API/MILP sonucu arayüzde; proje/revizyon/hesap kimliği aynı. |
| Saatlik grafik | Aynı hesap kimliğiyle 8.760 zaman damgası ve önce/sonra profil. |
| Sonuç dışa aktarımı | Güncel JSON ve HTML karar özeti aynı hesap kimliği; attachment/no-store. |
| ML/fizik | Gerçek sentetik model inference `available`, model `synthetic-annual-1.1`; fizik bağlamı eşleşti. |
| API yönlendirmesi | Gözlemlenen tarayıcı API isteklerinin tamamı Vercel aynı origin `/api`; SPA fallback API hatasını HTML'e çevirmedi. |
| Girdi değişikliği | Yalnız QA projesinin revizyonu arttırıldı; eski sonuç güncel değil olarak işaretlendi. Yeniden hesaplamayla farklı güncel hesap kimliği üretildi. |
| Gerçek yeniden yayın | Kullanıcı aynı commit'i Render'da yeniden yayımladı. Süreç boot kimliği `454bc10e…` → `80427a38…` değişti. |
| Yayın sonrası kalıcılık | Aynı oturum/kullanıcı, düzenlenmiş proje belgesi/revizyonu, son hesap kimliği ve JSON dışa aktarımı korundu. Yeni süreçte parolayla tekrar giriş ve sonuç ekranı geçti. |
| Tarayıcı hataları | Yakalanmamış JavaScript hatası: 0. Sonuç ekranları görsel olarak incelendi. |

Sentetik ofis QA hesabı **1.307.500 TL yatırım**, **230.681,6 kWh/yıl nihai enerji tasarrufu**, **154.119,8 TL/yıl net ekonomik tasarruf** üretti; motor `4.0.0`. Bu saha tasarrufu veya ML doğruluk kanıtı değildir. İkinci hesap da aynı fiziksel girdilerle yeniden üretildi; başarı öyküsü için veri değiştirilmedi.

Kanıtlar Git dışında `artifacts/live-deployment/report.json`, `live-result.png`, `postgres-after-redeploy.png`. Rapor `completed=true`, `redeploy_persistence.completed=true`, `different_boot=true`, `fresh_password_login=true` içerir. Parola, session cookie değeri, CSRF ve DATABASE_URL yalnız süreç/servis ortamında kaldı; rapor veya Git'e yazılmadı. Test sonunda QA oturumu kapatıldı. Hesap silme API'si olmadığı için bu ayrı QA hesabı ve sentetik projeleri sunucuda kaldı; diğer kullanıcı kayıtlarına dokunulmadı.

Eski kullanıcının 401 nedenini bu kabul testi belirlemez. Yanlış parola ile bulunamayan hesabın aynı cevabı vermesi korunur. Asıl eski SQLite/JSON kayıtlarının aktarıldığı veya kurtarıldığı iddia edilmez; aktarım aracı yalnız açık yedekle çalışır. Canlı PostgreSQL kasıtlı durdurulmadı: kesinti/fallback reddi ve toparlanma yalnız ayrı yerel gerçek PostgreSQL testinde doğrulandı. Ücretli LLM çağrısı, ML eğitimi, yeni özellik veya ücretli kaynak yok. Neon paneli ve gizli DSN okunmadığından plan/branch/role seçimi panel kanıtı olarak sunulmaz.

## Önceki kabul kaydı — 21 Ekim 2026

Aşağıdaki bulgular önceki SQLite tabanlı yayına aittir; 22 Ekim PostgreSQL kalıcılık kanıtı yukarıdadır.

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
