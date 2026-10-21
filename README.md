# Portfolio25-GRID

Bütçe ve elektrik bağlantı sınırları altında bina enerji yatırımlarını değerlendiren karar destek prototipi.

**Canlı demo:** https://buildingportfolio25.vercel.app

**Backend:** https://portfolio25-api.onrender.com

Kendi hesabınızı oluşturabilirsiniz. Dört proje / sekiz bina içeren Kayseri sentetik pilotu her kullanıcı için ayrı oluşturulur. Veriler saha ölçümü değildir; önceki kampüs ve kullanıcı kayıtları otomatik sıfırlanmaz.

## Demo akışı

1. Proje ve bina seçin; tüketim, kat dağılımı ve varsayımları inceleyin.
2. Senaryoda bütçe/hedef ve gerçek bağlantı gruplarını düzenleyin.
3. Mod A ile en yüksek enerji tasarrufunu veya Mod B ile hedefe en düşük yatırımı hesaplayın.
4. Önce/sonra enerji, yoğunluk, net ekonomik tasarruf ve kapasiteyi karşılaştırın; güncel sonucu CSV/JSON indirin.
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
- Render: `COOKIE_SECURE=true`, `FRONTEND_ORIGINS=https://buildingportfolio25.vercel.app`, `DATA_FILE=/var/data/portfolio25/campus.json`. Vercel üretiminde API adresi veya secret ortam değişkeni gerekmez. Yerel Vite proxy için `BACKEND_ORIGIN` kullanılabilir.
- Kalıcı disk varsa mount `/var/data`; kullanıcı/oturum SQLite ve özel proje/sonuç/geçmiş dosyaları `/var/data/portfolio25` altında tutulur. Disk yoksa yeniden başlatma/yayın sonrası bu kayıtlar kaybolabilir. Free web service kalıcı disk desteklemez. Diskin gerçekten bağlanması platformda ayrıca doğrulanmalıdır.

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
