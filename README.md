# Portfolio25-GRID

Binaların ısıtmasını elektrikleştirmeden önce enerji, karbon, yatırım bütçesi ve elektrik bağlantı etkilerini birlikte değerlendiren karar destek prototipi. İlk kullanım odağı kampüs yatırımlarını önceliklendirmektir; canlı cihaz kontrolü yapmaz.

**Canlı demo:** https://buildingportfolio25.vercel.app

**Backend:** https://portfolio25-api.onrender.com

**Giriş adresi:** Jüri ve kullanıcılarla yukarıdaki sabit demo adresini paylaşın. `frontend-...vercel.app` dağıtım adresleri ayrı Origin'dir; backend bunlara otomatik izin vermez. Yeni arayüz bu adreslerde form yerine üretim bağlantısını gösterir. Önceden yayımlanmış eski dağıtım sayfaları push ile güncellenmez. [Giriş/yayın açıklaması](docs/deploy-render-vercel.md).

Kendi hesabınızı oluşturabilirsiniz. Dört proje / sekiz bina içeren Kayseri sentetik pilotu her kullanıcı için ayrı oluşturulur. Veriler saha ölçümü değildir; önceki kampüs ve kullanıcı kayıtları otomatik sıfırlanmaz.

**Ürün odağı:** Kampüslerin teknik işler, enerji ve tesis ekipleri için yatırım önceliklendirme; kurum yönetimi yatırım kararı verir. Tek bina, ofis ve konut desteği ikincil kapsamdır. Gerçek Task 1 baseline'ı henüz sağlanmadı; pilot başlangıcı yalnız sentetik demo referansıdır.

## Demo akışı

1. Proje ve bina seçin; tüketim, kat dağılımı ve varsayımları inceleyin.
2. Senaryoda bütçe/hedef ve gerçek bağlantı gruplarını düzenleyin.
3. Mod A ile en yüksek enerji tasarrufunu veya Mod B ile hedefe en düşük yatırımı hesaplayın.
4. Önce/sonra enerji, yoğunluk, net ekonomik tasarruf ve kapasiteyi karşılaştırın. “Karar özeti indir” güncel hesaptan HTML üretir; tarayıcıda açıp PDF yazdırabilirsiniz. CSV/JSON ayrıntıları korunur.
5. Bina detaylarında deneysel ML tahminini fizik hesabıyla karşılaştırın.

**Ücretsiz sunucu:** Kullanılmadığında uyuyabilir. İlk bağlantı yaklaşık bir dakika, bazen daha uzun sürebilir. Girişte bağlantı hatası olursa **Bağlantıyı yeniden dene** ile oturumu kontrol edin; alanlarınız korunur. Başarısız kayıt/giriş isteği otomatik yinelenmez. Arayüzdeki bu iyileştirme platform kaynaklı 502/503 hatasını ortadan kaldırmaz.

## Yerel kurulum — Windows / VS Code PowerShell

Mevcut sanal ortamı ve `.env` dosyasını koruyun. İlk kurulum için Python 3.13, Node.js 22.12+ gerekir; kilitli bağımlılıklar kullanılır.

```powershell
# Proje kökü; .venv yoksa ilk kez oluşturun
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
cd frontend
npm.cmd ci
```

İki terminalde, çalışan portlarda ikinci sunucu açmadan:

```powershell
# Terminal 1 — proje kökü
.\.venv\Scripts\python.exe backend/run.py
# http://127.0.0.1:8000/api/health
```

```powershell
# Terminal 2 — frontend klasörü
npm.cmd run dev
# http://127.0.0.1:5173/
```

Alternatif: kökten `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1`. Dolu 8000/5173 portlarında ikinci sunucu başlatmaz. Elle başlatılan sunucuyu Ctrl+C; kayıtlı arka plan süreçlerini `scripts/stop-local.ps1` durdurur.

## Ortam ve yayın

- Backend kendi `backend/.env` dosyasını çalışma dizininden bağımsız yükler; process ortamını ezmez. Gerçek anahtarı frontend'e veya Git'e koymayın. Değişiklikten sonra backend'i yeniden başlatın. `OPENAI_API_KEY` isteğe bağlı; eksikliği fizik/MILP/ML'yi engellemez.
- Render: Docker runtime, kök `Dockerfile`, Root Directory boş, platform `PORT`, `0.0.0.0`, tek worker. `/api/health` kimlik doğrulamasız yaşam kontrolüdür; veri/çözücü hazır olduğunu iddia etmez.
- Vercel: Root Directory `frontend`, Framework Vite, build `npm run build`, çıktı `dist`. Tarayıcı aynı origin `/api` kullanır; rewrite `https://portfolio25-api.onrender.com/api/:path*` hedefine gider. SPA API yollarını dışlar.
- Hedef yayın: **Render Free + Neon Free PostgreSQL**, Vercel frontend. Render: `STORAGE_BACKEND=postgres`, yalnız backend'de gizli `DATABASE_URL`, `COOKIE_SECURE=true`, `FRONTEND_ORIGINS=https://buildingportfolio25.vercel.app`. Neon pooled adresinin TLS parametrelerini koruyun. Ücretli instance veya `/var/data` diski gerekmez. Yerel geliştirmede `STORAGE_BACKEND=sqlite`, `DATA_FILE=data/campus.json` kullanılabilir.
- PostgreSQL modunda hesaplar, oturumlar, özel proje belgeleri/revizyonları ve hesap geçmişi PostgreSQL'dedir. Bağlantı kesilince SQLite/JSON'a geri dönülmez; istek 503 verir. Migration sürümlü ve tekrar çalıştırılabilirdir, kayıt sıfırlamaz. [Neon geçiş ve kabul adımları](docs/postgres-deployment.md).
- **22 Ekim 2026 canlı kabulü geçti:** Render/Vercel üzerinden PostgreSQL ve backend commit `2962183` doğrulandı. Gerçek tarayıcıda kayıt/giriş/çıkış, proje/revizyon, optimizasyon, sentetik ML ve sonuç dışa aktarımı çalıştı. Kontrollü yeniden yayın sonrası farklı süreçte aynı QA hesabı, düzenlenmiş proje/revizyon ve hesap sonucu korundu; parolayla tekrar giriş başarılı. [Canlı rapor](docs/live-deployment-report.md). Önceki kullanıcı hesabının 401 nedeni veya kurtarıldığı doğrulanmadı; yeni depolama geçmişte kaybolmuş kaydı kendiliğinden getirmez.

[Yayın rehberi](docs/deploy-render-vercel.md) · [Canlı kabul raporu](docs/live-deployment-report.md) · [Hesap/kayıt ve eski veriyi aktarma](docs/auth-and-storage.md)

## Hesap ve AI sınırları

Yatırım planı fizik ve SciPy MILP ile hesaplanır. Sentetik model yıllık elektrik/toplam gaz tahmini sağlar; optimizasyonu veya saatlik kapasiteyi belirlemez. ComStock sağlayıcısı ayrı ABD simülasyon verisine dayanır. İki model de saha doğruluğu veya hız üstünlüğü kanıtı değildir. Büyük ML/fizik farkları gizlenmez. LLM açıklaması isteğe bağlıdır; son gerçek deneme kota/kredi hatası verdi, başarılı erişim iddia edilmez.

%25 azaltım değiştirilebilir hedef, garanti değildir. Kat dağılımı model paylaştırması, bina görünümü koordinatsız şemadır; canlı sensör veya dijital ikiz değildir. Eksik fiziksel veri ve kapsam dışı müdahaleler görünür tutulur. Girdi değişince eski sonuç güncel olarak dışa aktarılamaz.

## Kontroller

```powershell
# Proje kökü; testler geçici veride çalışır
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
python -X utf8 scripts/browser_auth_recovery.py
python -X utf8 scripts/browser_task3.py
cd frontend
npm.cmd test
npm.cmd run build
```

Tarayıcı kontrolleri Selenium/Chrome gerektirir. `scripts/check_live_deployment.py` gerçek HTTPS uçtan uca kontrolüdür; ayrı bir QA hesabı oluşturur. Hiçbiri model eğitimi veya ücretli LLM çağrısı başlatmaz. [Betik rehberi](scripts/README.md). Oturum desteğinden önceki altı eski tarayıcı betiği kaldırıldı; eski doğrulama belgelerindeki komutlar tarihsel kayıttır.

[API](docs/api-inventory.md) · [Veri sözleşmesi](docs/data-contract.md) · [Varsayımlar](docs/assumptions.md) · [Pilot](docs/pilot-kayseri.md) · [Sentetik model](docs/model-card-synthetic.md) · [ComStock](docs/model-card.md) · [Form yanıtları / kısa demo](docs/task3-submission.md)

[Belge dizini](docs/README.md) · [Climathon değerlendirmesi ve öneriler](docs/product-review.md)

Proje ve bina seçimi sayfa başlığının altındadır. Tema, TR/EN ve hareket tercihleri tek **Ayarlar** penceresindedir: giriş kartının alt sağında, oturum açıkken sol menünün altında; mobilde üstteki Menü düğmesinde. Tercihler tarayıcıda saklanır ve taslakları/proje verisini değiştirmez. Mobil ana menü altta sabittir. Kullanıcı adları ve özgün API kaynak/teknik açıklamaları çevrilmeden korunur; karar özeti bu sürümde Türkçedir.

Bina sayfasında kat/kullanım, yatırım seçenekleri ve ML/fizik karşılaştırması ayrı sekmelerdir; sekme değişimi taslağı silmez. Özet ekranında bina tablosu öndedir; koordinatsız şema isteğe bağlı açılır. Senaryoda hesapla eylemi başlıktadır; mobilde alt menünün hemen üstünde sabit kalır. Sonuçta yatırım kararı ve seçilen paketler öndedir; karşılaştırma/duyarlılık ve çözücü kanıtı açılır bölümlerdedir. [Ürün gerekçesi](docs/electrification-positioning.md) · [PDR taslağı](docs/pdr-draft.md); özgün Task 1 veya ölçülmüş baseline yerine geçmez.

Git yalnız kaynak kodu, lock dosyalarını, dağıtım/migration dosyalarını, testleri, gerekli model artefaktlarını ve güncel belgeleri içerir. `.env`, kullanıcı/oturum/proje kayıtları, özel yedekler, yerel QA görüntüleri, loglar, `node_modules` ve `dist` dışlanır. Eski tek seferlik raporlar Git geçmişinde ve yerelde Git dışı arşivde korunur; model dosyaları çalışan çıkarım için gereklidir.

Final karar araçları: sonuçlarda yöntem karşılaştırması ve LLM gerektirmeyen “Bu müdahale seçilseydi?” hesabı. Sayfa altındaki adlandırılmış senaryolar bağımsız kayıt/inceleme sağlar; açmak ana projeyi değiştirmez. PostgreSQL migration 002 başlangıçta uygulanır; kayıtları sıfırlamaz. Motor 4.1.0 eski hesapları tarihsel kabul eder. [Final teknik değerlendirme](docs/final-decision-review.md).
