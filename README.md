# Portfolio25-GRID

**Güncel yayın düzeni:** Render **Docker** runtime; depo kökünde `Dockerfile`, Root Directory boş, kalıcı disk `/var/data`. Vercel kökü `frontend`, Vite çıktısı `dist`, tarayıcı API çağrıları aynı origin `/api` üzerinden `https://portfolio25-api.onrender.com/api` hedefine rewrite edilir. Frontend: https://buildingportfolio25.vercel.app. Üretimde `BACKEND_ORIGIN` ortam değişkeni gerekmez. Render'da `COOKIE_SECURE=true`, `FRONTEND_ORIGINS=https://buildingportfolio25.vercel.app` gerekir. [Kesin ekran ayarları ve cookie/CSRF koşulları](docs/deploy-render-vercel.md).

**Canlı doğrulama:** Vercel üzerinden kayıt → proje yükleme → gerçek ofis optimizasyonu → ML inference → çıkış → yeniden giriş akışı 21 Ekim 2026'da geçti. Çıkış sonrası kayıt modunda kalma hatası düzeltildi. Çerez/CSRF, sorgu aktarımı, test sonuçları ve erişilmeyen kontroller [canlı kabul raporunda](docs/live-deployment-report.md).

**21 Ekim teslim güncellemesi:** Gerçek kayıt/giriş/çıkış, kullanıcıya ait dört proje ve sekiz bina, kalıcı tanıtım, kat karar önizlemesi, sentetik ML sağlayıcısı ve Render/Vercel dağıtım dosyaları eklendi. Güncel sınırlar ve kontroller: [teslim raporu](docs/final-delivery.md). Eski bölümler önceki aşamaların kaydıdır; güncel hesap/veri erişimi için aşağıdaki kurallar geçerlidir.

Uygulamayı `http://127.0.0.1:5173/` adresinden açıp **Kayıt olun** seçeneğiyle başlayın. Her hesap kendi sentetik pilotunu alır. Önceki yerel projeler silinmedi; otomatik ilk hesaba atanmaz. Açık ve yedekli aktarım: [hesap ve kayıt rehberi](docs/auth-and-storage.md).

Sunucular kapalıysa VS Code PowerShell'de iki terminal kullanın (çalışan portta ikinci sunucu açmayın):

```powershell
# Terminal 1 — proje kökü
.\.venv\Scripts\python.exe -m pip install -r backend/requirements-lock.txt
.\.venv\Scripts\python.exe backend/run.py
# http://127.0.0.1:8000/api/health
```

```powershell
# Terminal 2 — proje kökünden
cd frontend
npm.cmd ci
npm.cmd run dev
# http://127.0.0.1:5173/
```

Elle başlatılan sunucuları terminalde Ctrl+C durdurur. Bu oturumun arka plan süreçleri için `powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1` yalnız kaydedilmiş PID/başlangıç zamanı eşleşen süreçleri durdurur. `backend/.env` kendi klasöründen yüklenir; gerçek içerik Git'e girmez. Anahtar ekleyince backend'i yeniden başlatın. Eksik anahtar fizik/optimizasyon/ML'yi engellemez.

**Render + Vercel:** Projeye özel servis komutları, ortam değişkenleri, kalıcı disk, kayıt taşıma ve yayın sınırları [yayın rehberinde](docs/deploy-render-vercel.md). 21 Ekim 2026 gerçek LLM kontrolü sağlayıcı HTTP 429 ile başarısız oldu; anahtarın yapılandırılmış olması başarılı bağlantı anlamına gelmez.

**Güncel arayüz — Görev 3:** http://127.0.0.1:5173/ — üst çubukta ayrı **Proje** ve **Bina** alanları vardır. **Tema (Doğa / Gece / Toprak)**, hesap, çıkış, tanıtım ve yardım sağdaki **Hesap ve yardım** menüsündedir. Tek binalı projede bina adı sabit gösterilir. Tema tercihi tarayıcıda korunur. Önceki örnek kampüs ve Kayseri pilotu ayrı kayıtlardır; yeni hesap özel dört projeli pilotla başlar, eski kayıtlar açık aktarım gerektirir. Proje/örnek yönetimi açılır alandadır. Dışa aktarma **Dışa aktar**, teknik bağlam **Uygulama hakkında** bölümündedir. Bina adı ve enerji verileri, senaryoda bütçe/hedef, sonuçta yatırım ve net ekonomik tasarruf öne alınmıştır. [Güncel testler, ekran kanıtları ve ML sınırları](docs/task3-ui-report.md).

Bu adres yerel Vite sunucusudur; internet yayını değildir. Backend aynı 8000 portunda kontrollü yeniden başlatıldı, frontend 5173 korundu. Güncel oturumlu tarayıcı kabul komutu (Selenium kurulu Python): `python -X utf8 scripts/browser_task3.py`; geçici QA hesabı kullanır ve ücretli AI çağrısı yapmaz. Görüntüler/rapor yerelde `artifacts/task3-ui/` altında, Git dışındadır. Önceki hesapsız UI testleri tarihsel aşamaya aittir. [Önceki UI denetimi](docs/ui-fix-report.md).

Sunucular kapalıysa isteğe bağlı tek komut: `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1`. Dolu 8000/5173 portlarında ikinci sunucu açmaz. Durdurmak için yukarıdaki `scripts/stop-local.ps1` komutunu kullanın.

Teknik işler ve enerji yönetimi ekipleri için tek/çok bina enerji yatırım planlama prototipi.

**Sentetik örnek proje — sonuçlar model varsayımlarına dayanır.** Kampüs ve Kayseri pilotu saha ölçümü değildir. Yatırım kararları fizik motoru ve MILP ile hesaplanır. Ayrı deneysel ML ekranı, ABD ComStock harici simülasyonlarında eğitilmiş yıllık tahmin modelini gösterir; Kayseri için kapsam dışıdır.

## Güncel teslim — 20 Ekim 2026

Mevcut uygulama genişletildi; mevcut sekiz JSON girdi/sonuç/yedek dosyası byte düzeyinde korundu. Geçersiz güncelleme artık tam fiziksel ve yanıt şeması doğrulamasından önce diske yazılmaz. Sonuç, grafik, dışa aktarım ve açıklama proje + revizyon + girdi özeti + UUID hesap kimliği + motor sürümüyle eşleşir. Motor değiştiğinde eski sonuç tarihsel kalır, yeniden hesaplama gerekir.

Bina detayında müdahaleler **Uygulanmış / Zorunlu / Aday / Hariç** olarak yönetilebilir. Eski kat seçimleri kullanıcı açıkça yeni karar durumlarına geçene kadar zorunlu sabit yatırım davranışını korur. Aday çatı/kabuk, ışık, uygun program ve ısı pompası kombinasyonları aynı motorla hesaplanır; yeni yatırımlar bir kez sayılır. Uygulanmış durum seçilirse yıllık girdiler uygulama öncesi referans kabul edilir; model uygulanmış müdahaleyi başlangıca taşır, yeniden CAPEX yazmaz. Ölçülmüş mevcut tüketimi bu referansla karıştırmayın.

Taslaklar proje/bina bazında tarayıcıda saklanır; gezinme ve yenilemede Kaydet / Vazgeç / Kal seçenekleri vardır. Sonuçta karar özeti, tüm müdahaleler, üç yöntem karşılaştırması, gerçek çatı U-değeri duyarlılığı, hesap kimliği korumalı yıllık grafik ve sayısal tablo bulunur.

**LLM asistanı:** Sonuçta “Planı açıkla”, binada uygun seçenek açıklaması ve senaryoda onaylı geçici alternatif akışı backend üzerinden çalışacak biçimde uygulandı. Anahtar boşsa fizik/MILP çalışır. Bu teslimde tek kısa gerçek bağlantı denemesi **HTTP 429** aldı; gerçek açıklama başarısı doğrulanmadı. Otomatik testlerde sağlayıcı taklit edildi. Manuel alternatif senaryo ve karşı-olgusal hesap LLM gerektirmez; ana kaydı değiştirmez.

**Model ve veri:** Gerçek ComStock alt kümesinde 739 bağımsız bina / 2.084 müdahale satırıyla eğitim, grup ayrımlı validasyon/test ve yerel inference tamamlandı. Model fizik motorunu değiştirmez; yıllık tahmin kapasite/pik kanıtı olarak kullanılmaz. [Model kartı](docs/model-card.md), [AI mimarisi](docs/ai-architecture.md), [aşama bazlı rapor](docs/improvement-report.md), [güncel API](docs/api-inventory.md), [2–3 dakikalık demo](docs/demo-improvements.md).

Dördüncü aşama tamamlandı: seed=25 ile sekiz bina, yıllık tüketimle tutarlı sentetik profiller ve SciPy MILP motoru korunur. Revizyon/hesap kimliği korumalı başlangıç ve sonuç dışa aktarımları, okunabilir mobil düzen ve API sonuçlarıyla çalışan **Kampüs senaryo modeli** eklendi. Kullanıcı girdileri sıfırlanmadı. Eski QA dosyalarıyla güncel kayıt arasındaki farklar [inceleme raporunda](docs/data-audit.md) açıklanır.

20 Ekim 2026 kapsam genişletmesi: **tek bina ve çok bina projeleri**, ayrı fiziksel bağlantı grupları, üç yöntemli karar karşılaştırması ve sabit plan duyarlılığı eklendi. Mevcut kampüs varsayılan proje olarak korunur. Yeni proje oluştururken seçilen binalar ayrı kayda kopyalanır. Kullanıcı değerleri kaybolmadan v2→v3 dönüşümü yapılır. [Güncel sözleşme](docs/data-contract.md), [doğrulama](docs/verification-projects.md), [gelecek modüller](docs/product-roadmap.md).

Kayseri için **4 ayrı projede 8 binalı sentetik pilot** ve kat/kullanım alanı analizi eklendi. Mevcut proje sessizce değiştirilmez: **Proje ve örnek veri yönetimi → Kayseri sentetik pilotu → Ayrı pilot projelerini yükle ve aç** eylemini kullanın. Bina detayındaki **Katlar / Enerji Dağılımı / Müdahale Senaryoları** görünümleri elektrik ve yakıt kırılımlarını, kaynak/eksikleri ve gerçek API hesaplarını gösterir. Ekli pilot kapsamı güncel motorla yeniden doğrulandı; eski doğrulama betikleri yeni taslak/menü davranışına uyarlandı. Bu yeniden kontrol sırasında yeni LLM çağrısı veya ML eğitimi yapılmadı. Ayrıntılar: [pilot belgesi](docs/pilot-kayseri.md), [son kontrol kayıtları](artifacts/pilot-recheck-20261020-152538/README.md).

Eğitim binası, A blok ve ofis ayrıntılı sentetik zon örnekleridir; diğerleri kaba ana kullanım/ortak alan modelidir. Çatı/aydınlatma ve mevcut ısıtma paketleri hesaplanır. Uygun alanların HVAC programı yalnız açık kabul gerektiren **uzman inceleme senaryosu**dur; laboratuvar/konut/otel hizmeti azaltılmaz. Sıcak su ayrıdır ve her senaryoda korunur. Konfor, gerçek mimari plan veya doğrulanmış Kayseri iklim modeli iddiası yoktur.

Kat senaryosu önizlemesi kayıt değiştirmez. **Kat seçimlerini ve varsayımları kaydet** revizyon artırır; eski sonuç güncel değil olur. Yeni karar durumları etkinleştirildiğinde MILP aday kat müdahalelerini de seçebilir. Çatı ile çatı dahil kabuk paketi birlikte seçilemez. Ana şema 3.0 korunur; isteğe bağlı `spatial` alt modeli 1.0'dır. Kat verisi olmayan eski kayıtlara dağılım uydurulmaz. Yeni hesap önceki sonucu `backend/data/history/<proje>/` altında arşivler.

## Gereksinimler

- Windows / VS Code, PowerShell terminali.
- Node.js `^20.19.0` veya `>=22.12.0` (bu ortamda **22.19.0** ile doğrulandı).
- Python **3.13** (bu ortamda **3.13.7** ile doğrulandı).

Mevcut React + TypeScript + Vite / FastAPI uygulaması genişletildi. Kurulu ve uyumlu SciPy 1.17.1, NumPy 2.4.2 ve tzdata 2025.3 sürümleri incelenip proje sanal ortamına eklendi. Frontend `package-lock.json`, backend `requirements-lock.txt` tekrar kurulumu sabitler.

ML için scikit-learn 1.9.1 ve uyumlu yardımcı bağımlılıklar aynı lock dosyasına eklendi. Fizik kurulumu zaten varsa yalnız ML eklerini `..` içermeyen proje kökünden `.\.venv\Scripts\python.exe -m pip install -r backend\requirements-ml.txt` ile kurabilirsiniz. Mevcut model `backend/ml_assets/comstock-small/` içindedir; açılışta eğitim/indirme yapılmaz. ML bağımlılığı veya artefakt yoksa fizik/MILP çalışır, ML ekranda kullanılamıyor olarak görünür.

Gerçekten çalıştırılan son kontrolleri tekrarlamak için proje kökünde:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
.\.venv\Scripts\python.exe -m pip check
cd frontend
npm.cmd test
npm.cmd run build
cd ..
```

Tarayıcı denetimleri sistem Python + Selenium 4.41.0 + Chrome ile `python artifacts/improvements/browser_core.py` ve ardından `python artifacts/improvements/browser_ai_ml.py` komutlarıyla yapıldı. Bunlar ayrı QA proje kopyaları oluşturur, özgün kayıtları korur ve yeni ücretli AI çağrısı yapmaz; çalışır yerel sunucular gerektirir. ML hazırlık/eğitim kodları `scripts/inspect_comstock.py`, `scripts/prepare_comstock.py`, `scripts/train_energy_model.py` içindedir. Yeniden eğitim bu veri sürümünün test sonucunu gördükten sonra yeni model seçmek için kullanılmamalıdır; yeni deney ayrı holdout/sürüm gerektirir.

## Windows / VS Code kurulumu

VS Code’da bu klasörü açın. Terminal → New Terminal ile proje kökünde PowerShell kullanın. Sanal ortamı aktive etmek gerekmez; execution policy değişikliği gerekmez.

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-lock.txt
if (-not (Test-Path backend\.env)) { Copy-Item backend\.env.example backend\.env }
if (-not (Test-Path frontend\.env)) { Copy-Item frontend\.env.example frontend\.env }
cd frontend
npm.cmd ci
cd ..
```

`.env` dosyaları zaten varsa onları koruyun; `Copy-Item` adımlarını atlayın. `npm.cmd`, PowerShell’in `npm.ps1` kısıtlarına takılmaz.

### Backend ortam dosyası ve isteğe bağlı OpenAI asistanı

Dosya **backend/.env** konumundadır. Mevcut dosya korundu; içeriği incelenmedi veya çıktıya yazdırılmadı. Anahtarsız örnek `backend/.env.example`:

```dotenv
OPENAI_API_KEY=
OPENAI_MODEL=gpt-5.4-mini
```

Gerçek anahtarı yalnız backend/.env içinde kendiniz ekleyin; `VITE_` değişkenine koymayın. **Anahtar veya model eklendikten/değiştirildikten sonra backend'i yeniden başlatın.** Backend kaynak dosyasının konumundan bu dosyayı bulur; başka çalışma dizininden başlatılabilir. Mevcut süreç ortam değişkenlerinin üstüne yazılmaz (`override=False`). Boş API anahtarı uygulamayı veya MILP'yi engellemez. LLM istekleri backend'den OPENAI_MODEL ile yapılır; açıklama ve taslak düğmeleri sağlayıcıya ücretli çağrı yapabilir. Anahtar API/export/frontend/log alanı değildir. Bu teslimde bağlantı 429 ile sınırlı kaldı; birden fazla gerçek deneme yapılmadı.

`.gitignore` gerçek `.env` dosyalarını dışlar, `.env.example` dosyalarına açıkça izin verir. Bu çalışma klasöründe Git deposu bulunmadığından önceden izlenen dosya geçmişi incelenemedi. Gelecekte Git deposuna eklerseniz `.env` dosyasını takip etmeyin; ignore kuralı önceden izlenmiş dosyayı kendiliğinden takipten çıkarmaz.

### Terminal 1 — backend

Proje kökünde:

```powershell
.\.venv\Scripts\python.exe backend\run.py
```

- API: <http://127.0.0.1:8000/api/campus>
- Sağlık kontrolü: <http://127.0.0.1:8000/api/health>
- Etkileşimli veri sözleşmesi: <http://127.0.0.1:8000/docs>

### Terminal 2 — frontend

Proje kökünden ayrı terminal açın:

```powershell
cd frontend
npm.cmd run dev
```

Tarayıcıda **<http://127.0.0.1:5173>** adresini açın. Backend terminali açık kalmalıdır. Dosya yüklemeden sekiz örnek bina görünür.

Alternatif: VS Code’da Terminal → Run Task → **GRID: frontend + backend** iki süreci birlikte açar. Terminallerde `Ctrl+C` ile durdurun.

19 Ekim 2026 teslim kontrolünde iki adres de gerçek HTTP 200 yanıtı verdi; Chrome sekiz binayı API'den yükledi. Teslim sonunda sunucular **arka planda açık bırakıldı**. Aynı portlarda ikinci kez başlatmayın. Çalışan teslim süreçlerini güvenli biçimde durdurmak için proje kökünde:

```powershell
powershell.exe -NoProfile -File scripts\stop-local.ps1
```

Bu komut yalnız `artifacts/runtime/processes.json` içinde kayıtlı PID ve başlama zamanı eşleşen teslim süreçlerini durdurur; veriyi silmez. Daha sonra kendi iki terminalinizde başlattığınız süreçleri `Ctrl+C` ile kapatın. Terminal günlükleri `artifacts/runtime/` altındadır. Açık bırakılan adresler yalnız bu bilgisayara aittir; internette yayın yapılmadı.

## Kullanım

Önce üstteki **Çalışma projesi** seçicisini kullanın. **Yeni proje oluştur** ile kaynak projeden bir veya birden çok sentetik binayı seçin. Varsayılan bağlantı seçimi her bina için bağımsızdır; aynı besleme yalnız gerçekten paylaşılıyorsa ortak bağlantı seçin. Tek bina için aynı düzenleme, hesap, grafik ve export akışı çalışır. Kaynak kampüs kaydı sıfırlanmaz.

Senaryo ekranındaki **Proje, bağlantı grupları ve duyarlılık varsayımları** bölümünde proje adını, grup üyeliklerini, kaynaklarını ve kapasitelerini düzenleyin. Bina başına bağlantı sınırı bina formundadır; bütçe portföy genelindedir. Bağımsız gruplara toplam trafo sınırı uygulanmaz. Her binayı bağımsız bağlantıya ayır düğmesi yalnız taslağı değiştirir; açıkça kaydedin. Hem senaryo hem proje taslağı değiştiyse önce senaryoyu, sonra proje ayarlarını kaydedin. Kaydedilmemiş proje değişiklikleri de eski sonucu geçersiz işaretler.

Bina formundaki **Mevcut sistem ve müdahale uygunluğu** yalnız ısıtmayı kapsar. Uyumsuz paketler gerekçeyle filtrelenir; soğutma tasarrufu eklenmez. Konaklama örneği konut sitesi desteği değildir. Yeni pilot bu alanları sentetik ve bağımsız blok varsayımlarıyla örnekler; gerçek sayaç/konfor/ortak kazan doğrulaması eksiktir.

Hesapla işlemi GRID planıyla birlikte aynı verilerden oran sezgiseli ve elektrik kısıtsız MILP karşılaştırmasını üretir. Her plan için yatırım, tasarruf ve modellenen kapasite ihlalleri gösterilir. Elektrik kısıtsız plan ihlal yapmıyorsa arayüz bunu açıkça söyler; üstünlük zorlanmaz. Ardından seçilen GRID planı sabit tutularak SCOP/maliyet/kabuk duyarlılığı hesaplanır; yeni çatı seçilmişse ayrı çatı hedef U-değeri ekseni de eklenir. Bunlar güven aralığı/olasılık veya yeniden optimize edilmiş plan değildir.

1. Kampüs özetinde mevcut enerji, yoğunluk, varsayımsal işletme maliyeti ve **eşzamanlı** elektrik pikini inceleyin. Ayrı bina pikleri toplanarak kampüs piki üretilmez.
2. Tablodaki kalem simgesiyle binayı düzenleyin. Kampüs senaryo modelinde Önce/Sonra seçin; binaya tıklayınca API'den yatırım, enerji tasarrufu ve bina pik değişimi görünür. Renk anahtarı seçilen paketleri açıklar; gerçek koordinat veya canlı sensör verisi yoktur.
3. Bütçe, hedef ve kapasiteyi değiştirip **Girdileri kaydet** düğmesine basın. Elektrik/ısıtma yakıtı fiyatları genişletilebilir alandadır.
4. Bina düzenleme penceresindeki **Dönüşüm varsayımları** bölümünde kazan verimi, yalıtımın ilgili ısı payı/etkisi, SCOP, pompa kapasitesi ve maliyetleri düzenleyin. Isıtma ve diğer doğalgazı ayrı girin. Senaryodaki fiyat/emisyon varsayımlarının tarih ve kaynaklarını da düzenleyebilirsiniz.
5. **Senaryo girdileri** ekranında mod seçip **Yatırım planını hesapla** düğmesine basın. A: bütçe ve kapasite altında en fazla yıllık enerji tasarrufu; B: hedefe bütçe ve kapasite altında en az yatırımla ulaşma. Bina bağlantı ve ortak besleme sınırları ayrı uygulanır. Süre sınırı 0,01–60 sn.
6. Önce/sonra ve sekiz bina/paket sonucunu inceleyin. Çözümsüzlük ve optimumun kanıtlanmadığı durumlar açık gösterilir. Negatif net tasarruf korunur; geri ödeme yalnız pozitif net tasarrufta hesaplanır.
7. Dışa aktarım türünü seçin: **Başlangıç verisi** hesap/sonuç taşımaz; **Hesaplanmış sonuç** aynı revizyon/hesap kimliğinin paketlerini, çözücüsünü, varsayımlarını, kaynağını ve önce/sonra değerlerini taşır. CSV ve JSON dosya adları kapsamı/revizyonu ayırır. Girdi değişince eski sonuç güncel değil olur; yeniden hesaplanmadan sonuç dışa aktarılamaz. Başka oturum indirme öncesi kaydı veya hesabı değiştirmişse sunucu 409 ile durdurur.

Kaydedilmeyen form değişiklikleri gezinme/yenilemede kaybolabilir. İki sekmede aynı veriyi düzenlerseniz eski revizyon kaydı `409` ile reddedilir; sayfayı yenileyin ve değişikliği tekrar uygulayın.

## Yapılandırma

| Dosya / değişken | Amaç | Varsayılan |
| --- | --- | --- |
| `frontend/.env` → `VITE_API_BASE_URL` | Tarayıcının çağırdığı backend adresi | `http://127.0.0.1:8000` |
| `frontend/.env` → `FRONTEND_HOST` | Vite geliştirme sunucusunun bağlandığı arayüz | `127.0.0.1` |
| `frontend/.env` → `FRONTEND_PORT` | Vite geliştirme portu | `5173` |
| `backend/.env` → `BACKEND_HOST` | Backend dinleme adresi | `127.0.0.1` |
| `backend/.env` → `BACKEND_PORT` | Backend dinleme portu | `8000` |
| `backend/.env` → `FRONTEND_ORIGINS` | Virgülle ayrılmış izinli frontend origin’leri | `http://127.0.0.1:5173,http://localhost:5173` |
| `backend/.env` → `DATA_FILE` | Kalıcı JSON dosyası; göreli ise backend klasörüne göre | `data/campus.json` |

Adres/port değiştirdikten sonra sunucuları yeniden başlatın. `VITE_` değişkenleri üretim derlemesine gömülür; değiştirince tekrar derleyin. Bunlara gizli anahtar koymayın. HTTPS frontend yayımlandığında API de HTTPS olmalıdır. CORS origin’i protokol, alan adı ve varsa port içerir; sonunda `/` içermez.

## Veri saklama

İlk API çağrısında `backend/data/campus.json` oluşturulur. Sonraki başlatmalar düzenlemeleri korur. Eski kayıtta bilinmeyen ısıtma dışı gaz sıfır varsayılır; bu ölçüm değildir. Yeni oluşturulan örnekte diğer gaz, ısıtma gazının %8’i varsayılır. Dönüşüm notları API/UI’da görünür.

Güncel şema **3.0**: v1 kendi yedeğiyle doğrudan v3'e, v2 `campus.v2-backup.json` birebir yedeğiyle v3'e dönüşür; revizyon bir artar, bütün eski değerler korunur. Eski ortak sınır G01 bağlantı grubuna taşınır. Yeni projeler `backend/data/projects/<project-id>.json`, sonuçları `.result.json` içinde saklanır. Eski hesap dosyası silinmez fakat değişen revizyonda güncel plan sayılmaz. Proje silme arayüzü henüz yoktur. Aynı backend çalışma alanında birden çok proje vardır; kullanıcı hesabı/erişim izolasyonu sağlanmaz.

Güncel hesap `backend/data/campus.result.json` içinde revizyonla saklanır. Saatlik diziler depolanmaz; yıllık tüketim ve profil parametrelerinden deterministik üretilir. Dosyalar `.gitignore` kapsamındadır. İlk örneği geri getirmek için backend’i durdurup veri dosyasını başka adla **yedekleyin**; dosya yoksa seed=25 yeniden oluşturulur. Bozuk veri otomatik silinmez.

Tek backend süreci / worker kullanın. Süreç içi kilit ve atomik dosya değişimi bu prototip için uygundur; çok süreçli veya çok kullanıcılı internet yayını için veritabanı gerekir. Bu sürümde kullanıcı hesabı yoktur; aynı backend’e erişen herkes aynı örnek çalışma alanını düzenler.

## Kontroller

Proje kökünde backend testleri:

```powershell
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
.\.venv\Scripts\python.exe -m pip check
```

Frontend tip kontrolü ve üretim derlemesi:

```powershell
cd frontend
npm.cmd run build
```

Testler geçici dosyalar kullanır; çalışma alanı kampüs verisini değiştirmez. API/engine testleri yıllık-saatlik tutarlılığı (normal/artık yıl), elle fizik hesabını, kapasite yedeğini, iki modda tam kombinasyonlarla MILP karşılaştırmasını, negatif ekonomiyi, süre sınırı durumlarını, dönüşümü, kalıcılığı ve dışa aktarımı kontrol eder. Elle örnek: [docs/calculation-example.md](docs/calculation-example.md).

`scripts/browser_delivery.py` güncel Selenium teslim kontrolüdür. İki sunucu açıkken çalıştırılır. Kayıtlı modu aynı revizyonda yeniden hesaplar; canlı girdilere PUT yapmaz, dosya karmasını kontrol eder. CSV/JSON, eski sonuç, harita sayıları, hata durumları ve 390/500/768/1536 px ekranları sınar. Selenium uygulama bağımlılığı değildir. Bu ortamda kurulu Selenium 4.41.0 bulunan global `python` ile çalıştırıldı; sanal ortamda kuracaksanız:

```powershell
.\.venv\Scripts\python.exe -m pip install selenium==4.41.0
.\.venv\Scripts\python.exe scripts\browser_delivery.py
```

Chrome kurulu olmalıdır. İlk tarayıcı testinde Selenium Manager uyumlu sürücüyü indirmek için internet erişimi isteyebilir. Eski `browser_demo.py` / `browser_smoke.py` testleri canlı girdilere geçici PUT yapıp geri yükler ve revizyon artırır; kullanıcı kaydını koruyan teslim kontrolü için yukarıdaki scripti kullanın. Son kontrol kaydı: [docs/verification-stage4.md](docs/verification-stage4.md); önceki aşama kaydı [verification.md](docs/verification.md) içinde korunur.

Güncel tek/çok bina tarayıcı doğrulaması (bu ortamda kurulu global Selenium ile):

```powershell
python scripts\browser_projects.py
```

Yalnız testin oluşturduğu yeni QA proje kopyalarını düzenler; kaynak kampüse PUT yapmaz. Sonunda yalnız kendi dosyalarını son bilinen baytlarıyla eşleşiyorsa arşivleyip kaldırır; eşzamanlı değiştirilmiş dosyayı korur. Görüntü ve kayıtlar `artifacts/stage5/` altındadır. Selenium sanal ortamda kuruluysa aynı komutu `.\.venv\Scripts\python.exe` ile kullanabilirsiniz. Yeni kontrol kaydı: [verification-projects.md](docs/verification-projects.md).

## Daha sonra internet yayını

Bu teslim yerel uygulamadır; yayımlanmış bir bağlantı oluşturulmadı.

1. Backend’i Python 3.13 destekleyen bir sunucuya taşıyın, kilit dosyasından kurun. Kalıcı disk üzerinde `DATA_FILE`, izinli gerçek frontend origin’i ve `BACKEND_HOST=0.0.0.0` ayarlayın. `backend` çalışma dizininde `python -m uvicorn main:app --host 0.0.0.0 --port 8000 --workers 1` çalıştırın; host’un port gereksinimine uyarlayın.
2. Frontend’de `VITE_API_BASE_URL=https://api.example.edu` ayarlayıp `npm.cmd ci` ve `npm.cmd run build` çalıştırın. `frontend/dist` klasörünü statik HTTPS host’ta yayımlayın. Vite geliştirme/preview sunucusu üretim sunucusu değildir.
3. `/api` üzerinden aynı alan adı ters vekili kullanıyorsanız `VITE_API_BASE_URL=/api` **kullanmayın**: uygulama yolları zaten `/api` içerir. Bu durumda `VITE_API_BASE_URL=/` ayarlayın ve proxy’nin `/api/*` yollarını backend’e ilettiğini doğrulayın.
4. Kalıcı dosyanın yeniden dağıtımda korunmasını, HTTPS ve CORS bağlantısını doğrulayın. Çok kullanıcı/worker ihtiyacında veritabanına geçin.

## Sık karşılaşılan sorunlar

- **Backend’e ulaşılamadı:** iki terminali açık tutun; `/api/health` adresini kontrol edin. `VITE_API_BASE_URL` ve CORS origin’ini eşleştirin.
- **Port kullanımda:** `.env` portunu değiştirip frontend API/CORS adreslerini de güncelleyin. Başka uygulamaların süreçlerini kapatmayın.
- **Paket kurulumu ağ hatası:** internet/kurumsal proxy erişimini kontrol edin; `npm.cmd ci` veya pip komutunu tekrar çalıştırın. Uygulama çalışırken internet gerektiren harici font/servis yoktur.
- **422:** alan, tüketim, kapasite ve hedef aralıklarını inceleyin. Bina sayısı ve sentetik kaynak bilgisi bu aşamada sabittir.
- **409:** veriler başka sekmede değişmiştir; yenileyip tekrar düzenleyin.
- **CSV Excel’de tek sütun:** Veri → Metin/CSV’den ile UTF-8 ve virgül ayırıcı seçin.

## Dosyalar ve sonraki işler

```text
frontend/           React + TypeScript + Vite
backend/            FastAPI, örnek üretici, doğrulama ve API testleri
docs/product-spec.md  Kesin kapsam, öneriler, bilinmeyenler
docs/assumptions.md   Veri kaynakları, formüller ve varsayımlar
docs/data-contract.md Endpoint, alan ve birim sözleşmesi
.vscode/tasks.json   İki sunucuyu başlatma görevleri
```

Kalan işler: gerçek veriyle mühendislik doğrulaması; sıcaklığa bağlı COP/kapasite ve ayrıntılı ekonomi. Gerçek veri içe aktarma, çok kullanıcı depolama ve internet yayını uygulanmadı. EV, batarya, IoT, otonom kontrol, hesap, ödeme ve chatbot kapsam dışında.

## Demo ve yeniden üretilebilir teslim

Akış: Kampüs özeti → Bina detayları → Senaryo girdileri → Optimizasyon sonucu. [2–3 dakikalık demo metni](docs/demo-stage4.md) iki gerçek API senaryosunu anlatır: mevcut A planı ve daha sıkı bütçe/kapasiteyle çözümsüz B hesabı. Veriler başarı hikâyesi üretmek için değiştirilmedi.

Bina detayında dört paket API’den hesaplanır. Senaryoda girdileri kaydedebilir veya Kaydet ve hesapla ile birlikte işleyebilirsiniz. Sonuçta yatırım/kalan bütçe, enerji/maliyet farkı ve hedef/çözücü bilgileri bulunur. Sentetik elektrik grafiği yıllık diziden 1/7/30 günlük veya tam yıllık kesit gösterir; tarih, pik haftası ve saat kaydırıcısı kullanılabilir. Tüm kaynaklar Varsayımlar düğmesinden açılır.

Girdiler veya seçilen optimizasyon modu değişince önceki hesap güncel değil olarak işaretlenir. Kaydedilip sayfa yenilense bile eski hesap tarihsel olarak incelenebilir. Yeniden hesaplama olmadan güncel plan diye dışa aktarım yapılamaz. Eski sonuçla güncel bütçe/profil karıştırılmaz.

CSV ile güncelle yalnız uygulamanın dışa aktardığı sentetik şablonu kabul eder. Önizleme sonunda 8 binayı uygula ile mevcut kayıt API’sine gönderilir. Geçersiz CSV, farklı kaynak, eksik bina ve tutarsız ortak değerler reddedilir. Dosyadaki yatırım sonuçları içe alınmaz. Gerçek/ölçülmüş CSV içe aktarımı bu teslimde yoktur.

Frontend veri/grafik durum testleri:

```powershell
cd frontend
npm.cmd test
npm.cmd run build
```

Canlı girdileri değiştirmeden iki senaryoyu geçici depoda yeniden üretmek için:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_delivery_demo.py
```

Script gerçek FastAPI uçlarını TestClient ile geçici DATA_FILE üzerinde çağırır. Çıktılar `artifacts/delivery/scenarios/` altında iki senaryonun inputs/result CSV/JSON dosyaları ve gerçek değerleri içeren manifesttir. Yeniden üretirken mevcut kullanıcı girdilerinin salt okunur kopyası kullanılır; gelecekteki düzenlemeler sayıları değiştirebilir. Tarayıcı görüntüleri `artifacts/delivery/` altında; eski aşama görüntüleri ayrıca korunur.

