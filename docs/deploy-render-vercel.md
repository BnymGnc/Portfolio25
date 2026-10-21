# Render + Vercel yayın rehberi

21 Ekim 2026. Depo: https://github.com/BnymGnc/Portfolio25. Bu oturumda Render/Vercel hesap erişimi veya oluşturulmuş servis adresi verilmedi. Ücretli hizmet satın alınmadı; yerel çalışma internet yayını değildir.

## Render

Depoyu Python Web Service olarak bağlayın. `render.yaml` aynı ayarları tanımlar; dosyanın bulunması servisin oluşturulduğu anlamına gelmez.

| Alan | Değer |
| --- | --- |
| Root Directory | `backend` |
| Python | `3.13.7` |
| Build | `pip install -r requirements-lock.txt` |
| Start | `uvicorn main:app --host 0.0.0.0 --port $PORT --workers 1` |
| Health check | `/api/health` — yalnız yaşam kontrolü |
| Persistent disk | Mount path `/var/data` |
| DATA_FILE | `/var/data/portfolio25/campus.json` |
| COOKIE_SECURE | `true` |
| FRONTEND_ORIGINS | Gerçek tam Vercel üretim adresi |
| OPENAI_MODEL | `gpt-5.4-mini` veya sizin mevcut seçiminiz |
| OPENAI_API_KEY | İsteğe bağlı, yalnız Render secret alanı |

Kayıtlar, kullanıcılar ve oturumlar DATA_FILE üst dizinindeki kalıcı diske yazılır. Render varsayılan dosya sistemi geçicidir; ücretsiz web servisi kalıcı disk sağlamaz. Disk olmadan bu uygulamayı kalıcı kullanıcı kayıt hizmeti olarak sunmayın. Disk/hizmet fiyatını Render ekranında inceleyin; burada satın alma yapılmadı. [Kalıcı diskler](https://render.com/docs/disks), [ücretsiz hizmet sınırları](https://render.com/docs/free).

## Vercel

Aynı depoyu import edin: Root Directory `frontend`, framework Vite, build `npm run build`, output `dist`, Node 22. `frontend/vercel.json` ve `frontend/api/[...path].js` hazırdır.

Sunucu ortam değişkeni `BACKEND_ORIGIN=https://GERCEK-SERVIS.onrender.com` tanımlayın. Adrese `/api` eklemeyin. `VITE_API_BASE_URL` boş/silinmiş olsun; tarayıcı aynı origin `/api/...` kullanır. OpenAI anahtarı frontend'e konulmaz.

Geçit cookie, CSRF ve Origin başlıklarını taşır; yanıtlar `private, no-store` olur. Backend çerezinde Domain olmadığı için HttpOnly/Secure cookie Vercel origin'ine aittir. Keyfî hedef URL kabul edilmez. Proxy 165 saniye, fonksiyon 180 saniyeyle sınırlı; kullandığınız planın süre limitini kontrol edin. [Vercel fonksiyon süresi](https://vercel.com/docs/functions/configuring-functions/duration), [ortam değişkenleri](https://vercel.com/docs/environment-variables).

Vercel adresi kesinleşince Render FRONTEND_ORIGINS değerini tam HTTPS adresiyle güncelleyip redeploy edin. Preview adresleri otomatik izinli değildir. Cookie akışını farklı siteler arası bağımlı hale getirmemek için tarayıcıyı doğrudan Render API adresine yönlendirmeyin.

## Gerçek yayından sonra kontrol

1. HTTPS kayıt → tanıtım → dört proje/sekiz bina; cookie HttpOnly/Secure/SameSite=Lax ve API no-store.
2. Hesapla, export, manuel alternatif ve ML; LLM erişilemezken diğer işlevler çalışmalı.
3. İkinci hesap ilk kullanıcının proje kimliğine erişememeli.
4. Render yeniden başlatıldıktan sonra kullanıcı, onboarding ve revizyon korunmalı.
5. Logout eski cookie'yi iptal etmeli; yanlış Origin/CSRF 403 dönmeli.

Bu HTTPS kontrolleri servis erişimi sağlanmadığı için burada yapılmış sayılmaz. Yerel testler onların yerine geçmez.

## Modeller ve sırlar

ComStock ve sentetik model artefaktları `backend/ml_assets/` içindedir; sunucu başlangıcında eğitim yapılmaz. `.env`, gerçek kullanıcı kayıtları, SQLite ve özel yedekler Git/Docker dışında tutulur. `backend/.env` kendi klasöründen yüklenir, process ortamını ezmez. Anahtar eklendiğinde backend yeniden başlatılır.

Tek kısa gerçek LLM denemesi kota/kredi hatası verdi. Anahtar yapılandırılmış olması başarılı erişim demek değildir. Hesap sahibi OpenAI kota/faturalama ayarlarını kontrol etmelidir. Anahtar/model değiştirilmedi, kredi satın alınmadı.
