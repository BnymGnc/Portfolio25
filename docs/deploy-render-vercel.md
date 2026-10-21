# Render + Vercel yayın rehberi

21 Ekim 2026. Depo: https://github.com/BnymGnc/Portfolio25. Bu oturumda Render/Vercel hesap erişimi veya oluşturulmuş servis adresi verilmedi. Ücretli hizmet satın alınmadı; yerel çalışma internet yayını değildir.

## Render

Depoyu **Docker Web Service** olarak bağlayın. `render.yaml` aynı ayarları tanımlar; dosyanın bulunması servisin oluşturulduğu anlamına gelmez. İmaj depo kökündeki Dockerfile ile oluşturulur; test edilmiş mevcut Python 3.13.7 ve kilitli bağımlılıklar kullanılır.

| Alan | Değer |
| --- | --- |
| Language / Runtime | `Docker` |
| Root Directory | **Boş bırakın** — depo kökü |
| Dockerfile Path | `./Dockerfile` |
| Docker Build Context Directory | `.` — depo kökü |
| Docker Command | **Boş bırakın** — Dockerfile CMD kullanılır |
| Çalışma komutu | `python serve.py`; `0.0.0.0`, platform `PORT` değeri ve tek worker |
| Health check | `/api/health` — yalnız yaşam kontrolü |
| Persistent disk | Mount path `/var/data` |
| DATA_FILE | `/var/data/portfolio25/campus.json` |
| COOKIE_SECURE | `true` |
| FRONTEND_ORIGINS | Gerçek tam Vercel üretim adresi |
| OPENAI_MODEL | `gpt-5.4-mini` veya sizin mevcut seçiminiz |
| OPENAI_API_KEY | İsteğe bağlı, yalnız Render secret alanı |
| PORT | Render sağlar; elle tanımlamak gerekmez. İmajın yerel varsayılanı `10000` |

Kayıt kökü **`/var/data/portfolio25`**: `accounts.sqlite3` ve WAL dosyaları kullanıcı/oturumları; `users/<uid>/projects` proje JSON/sonuçlarını; kullanıcı altındaki `history` hesap geçmişini saklar. `/var/data` diski tümünü kapsar. `DATA_FILE`, eski yerel kampüs dosyasının yolunu da tanımlar; yeni hesaplara otomatik atanmaz. Render varsayılan dosya sistemi geçicidir; ücretsiz web servisi kalıcı disk sağlamaz. Disk olmadan bu uygulamayı kalıcı kullanıcı kayıt hizmeti olarak sunmayın. Disk/hizmet fiyatını Render ekranında inceleyin; burada satın alma yapılmadı. [Kalıcı diskler](https://render.com/docs/disks), [ücretsiz hizmet sınırları](https://render.com/docs/free).

## Vercel

Aynı depoyu import edin: Root Directory `frontend`, Framework Preset **Vite**, Build Command `npm run build`, Output Directory `dist`, Install Command `npm ci`, Node 22. `frontend/vercel.json` doğrudan dış-origin rewrite kullanır. Önceki `frontend/api/[...path].js` Node fonksiyonu kaldırıldı; API yollarıyla yarışan ikinci handler yoktur.

Gerçek Render adresi henüz verilmedi. `frontend/vercel.json` içindeki **`https://REPLACE-WITH-REAL-RENDER-URL.invalid` bir yer tutucudur; çalışan servis değildir.** Render servisiniz oluşunca yalnız bu origin kısmını gerçek `https://...onrender.com` ile değiştirin, `/api/:path*` ekini koruyun ve commit/push yapın. Örneğin `/api/auth/session`, Render'da yine `/api/auth/session` olur. Sorgu parametreleri ve istek yöntemi/gövdesi korunmalıdır. Yer tutucu dururken frontend açılabilir ama API/login çalışmaz.

**Vercel üretiminde gerekli ortam değişkeni yoktur.** `BACKEND_ORIGIN` eski Node geçidine aitti ve artık üretimde kullanılmaz; `VITE_API_BASE_URL` boş/silinmiş kalabilir. Üretim kodu yanlışlıkla localhost tanımlanmış olsa bile `/api` kullanır. `BACKEND_ORIGIN` yalnız yerel Vite proxy ayarı olarak korunur. OpenAI anahtarı frontend'e konulmaz.

Tarayıcı Vercel origin'inde `/api` çağırır; rewrite HTTP redirect yapmaz. `credentials: include` ve mevcut CSRF başlığı korunur. Backend cookie ayarı HttpOnly + Secure + SameSite=Lax + Path=/; Domain **tanımlanmaz**, böylece çerez tarayıcının gördüğü Vercel alanına aittir. FRONTEND_ORIGINS tam Vercel HTTPS origin'ini içermelidir. Yanlış Origin/CSRF 403 verir; logout sunucudaki oturumu iptal eder. API yanıtlarında browser ve CDN cache kapalı; ayrıca rewrite cache açıkça devre dışıdır. [Vercel rewrites ve cache](https://vercel.com/docs/routing/rewrites).

Dış-origin rewrite süre sınırı Vercel platformuna bağlıdır; eski Node fonksiyonunun `maxDuration` ayarı artık uygulanmaz. Gerçek yayında uzun MILP çağrılarını ayrıca kontrol edin; UI'daki çözücü süre sınırı kullanılabilir.

Vercel adresi kesinleşince Render FRONTEND_ORIGINS değerini tam HTTPS adresiyle güncelleyip redeploy edin. Preview adresleri otomatik izinli değildir. Cookie akışını farklı siteler arası bağımlı hale getirmemek için tarayıcıyı doğrudan Render API adresine yönlendirmeyin.

## Gerçek yayından sonra kontrol

1. HTTPS kayıt → tanıtım → dört proje/sekiz bina; cookie HttpOnly/Secure/SameSite=Lax ve API no-store.
2. Hesapla, export, manuel alternatif ve ML; LLM erişilemezken diğer işlevler çalışmalı.
3. İkinci hesap ilk kullanıcının proje kimliğine erişememeli.
4. Render yeniden başlatıldıktan sonra kullanıcı, onboarding ve revizyon korunmalı.
5. Logout eski cookie'yi iptal etmeli; yanlış Origin/CSRF 403 dönmeli.

Bu HTTPS kontrolleri gerçek Render/Vercel URL'leri ve servis erişimi sağlanmadığı için burada yapılmış sayılmaz. Yerelde HTTPS origin kullanan oturum/CSRF testleri ve rewrite/cache sözleşmesi doğrulanır; bunlar Vercel'in canlı uçtan uca davranışının yerine geçmez.

## Bu değişiklikte çalıştırılan doğrulama

- Backend: **69 test geçti**, üretim PORT/bind/single-worker ve HTTPS cookie/CSRF testleri dahil. Kalıcı kayıt deposu yeniden açıldığında kullanıcı/tanıtım/proje verisi korunur.
- Frontend: **13 test geçti**; API rewrite yolunu, API'nin SPA fallback'e düşmemesini ve cache başlıklarını sınayan kontroller dahil. TypeScript/Vite üretim derlemesi geçti.
- Linux Docker imajı gerçekten oluşturuldu. İmajda gerçek `.env`, kullanıcı veri dizini ve SQLite bulunmadığı; iki eğitilmiş ML artefaktının bulunduğu kontrol edildi.
- İmaj geçici, ayrı bir host dizini `/var/data` altına bağlanarak rastgele yerel portta çalıştırıldı. Özel `PORT` üzerinden sağlık, Secure/HttpOnly/host-only cookie, Origin/CSRF reddi, dört proje/sekiz bina, gerçek SciPy optimizasyonu ve sentetik ML inference geçti. Eğitim veya LLM çağrısı yapılmadı.
- QA konteyneri kaldırılıp **yeni konteyner** aynı dizinle oluşturuldu: mevcut cookie oturumu, kullanıcı, tanıtım sürümü, projeler ve son hesap korundu; JSON hash'leri değişmedi. Logout sonrasında eski oturum reddedildi. Yalnız bu testin konteynerleri kaldırıldı; diğer Docker servisleri korunur.

Tekrarlamak için depo kökünden (Docker Desktop çalışır durumda):

```powershell
docker build -t portfolio25-api:deploy-check .
python -X utf8 scripts/check_docker_deployment.py
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
cd frontend
npm.cmd test
npm.cmd run build
```

Konteyner testinin host bağlantısı HTTP, gönderdiği frontend Origin HTTPS'tir; gerçek HTTPS cookie davranışı ayrıca TestClient HTTPS origin ile sınanır. Bunlar gerçek Vercel edge rewrite'ını çalıştırmaz. Canlı servis URL'si gelince yukarıdaki dağıtım sonrası kontrol zorunlu kalır. Yerel kanıtlar Git dışında `artifacts/docker-deployment/report.json`, `artifacts/final-delivery/docker-build.txt` ve `deployment-backend-tests.txt` içinde tutulur.

## Modeller ve sırlar

ComStock ve sentetik model artefaktları `backend/ml_assets/` içindedir; sunucu başlangıcında eğitim yapılmaz. `.env`, gerçek kullanıcı kayıtları, SQLite ve özel yedekler Git/Docker dışında tutulur. `backend/.env` kendi klasöründen yüklenir, process ortamını ezmez. Anahtar eklendiğinde backend yeniden başlatılır.

Tek kısa gerçek LLM denemesi kota/kredi hatası verdi. Anahtar yapılandırılmış olması başarılı erişim demek değildir. Hesap sahibi OpenAI kota/faturalama ayarlarını kontrol etmelidir. Anahtar/model değiştirilmedi, kredi satın alınmadı.
