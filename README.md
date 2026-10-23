# Portfolio25-GRID

Kampüslerde hangi binaya hangi müdahalenin yapılacağını, yatırım bütçesi ve elektrik bağlantı sınırları altında değerlendiren enerji karar destek prototipi. Isıtma elektrifikasyonu bu kararın önemli bir bileşenidir. İlk kullanım odağı kampüs yatırımlarını önceliklendirmektir; canlı cihaz kontrolü yapmaz.

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

## Sentetik veriler nereden geliyor?

**“Kayseri için hazırlanmış sentetik pilot senaryo — saha ölçümü değildir.”** Gerçek kurum veya işletme verisi kullanılmaz. [Pilot üreticisi](backend/pilot_kayseri.py) `kayseri-synthetic-v1` veri setini sabit seed 25 ile oluşturur; bina özelliklerindeki kontrollü çeşitlilik bina indeksine bağlıdır. Aynı kod, seed ve varsayımlar aynı örneği yeniden üretir. Kullanıcının sonradan yaptığı düzenlemeler ayrı kayıtlardır.

| Bağımsız proje | Binalar | Başlangıç bütçesi | Elektrik bağlantısı |
|---|---|---:|---|
| Temsilî kampüs | Eğitim, kütüphane, araştırma laboratuvarı, idari bina | 12.000.000 TL | Sentetik ortak 1.100 kW sınır + her binanın kendi sınırı |
| Temsilî konut sitesi | A blok, B blok | 7.000.000 TL | İki bağımsız bağlantı; bağımsız ısıtma sistemleri |
| Bağımsız ofis | Bir ofis binası | 2.800.000 TL | Kendi bağlantısı |
| Küçük otel | Bir otel binası | 4.000.000 TL | Kendi bağlantısı |

Bunlar değiştirilebilir demo girdileridir, yatırım teklifi veya şebeke kapasitesi ölçümü değildir. Dört projenin bütçeleri ve bağlantıları birleştirilmez. Önceki sekiz binalı örnek kampüs ayrı veri setidir; yeni pilot mevcut kullanıcı kayıtlarının üzerine sessizce yazılmaz.

- Alanlar, kat sayıları, kullanım programları, aydınlatma/cihaz güçleri ve ısıtma yoğunlukları kullanım türüne göre tanımlanır. Laboratuvar, konut ve otelin hizmet gereksinimleri ofisle aynı kabul edilmez.
- Saatlik zaman ekseni 2025, `Europe/Istanbul`, 1 saattir (8.760 saat). Hava senaryosu proje içinde üretilmiştir; doğrulanmış Kayseri hava ölçümü veya yerel kalibrasyon yoktur. Harici hava dosyası kullanılmaz.
- [Profil motoru](backend/profiles.py) saatlik yükleri yıllık enerjiyle uzlaştırır. Bir saatlik kW değerlerinin toplamı yıllık kWh ile tutarlıdır. Profil sentetiktir; modellenen kapasite uygunluğu saha uygunluğu kanıtı değildir.
- Kat ve kullanım amacı görünümleri aynı bina enerjisinin iki farklı kırılımıdır; birbirine eklenmez. Alan, kullanım süresi ve yük varsayımlarıyla paylaştırılır; ortak alanlar da hesaba katılır. Ayrıntılı termal simülasyon değildir.
- Isıtma gazı ve ısıtma dışı gaz ayrıdır. Otelin sıcak su tüketimi ayrıca temsil edilir; desteklenmeyen sıcak su müdahalesinden tasarruf üretilmez.
- Örnek tarifeler elektrik için 4,5 TL/kWh, gaz için 1,5 TL/kWh'dir. Güncel resmî tarife değildir. Tarife, emisyon, maliyet ve performans varsayımları kaynak/tarih bilgileriyle değerlendirilmelidir.
- Girdi kaynakları ölçülmüş, kullanıcı tahmini, varsayılan, sentetik veya belirtilmemiş olabilir. Bir kaynak etiketi doğrulama sertifikası değildir; bilinmeyen veri ölçülmüş sayılmaz.

Gerçek kampüs pilotu için yıllık faturalar, alanlar, ısıtma sistemi ve kazan verimi, bağlantı belgeleri, mümkünse saatlik elektrik yükü ve yatırım teklifleri gerekir. **Gerçek ölçülmüş baseline henüz yoktur.** %25 azaltım değiştirilebilir hedeftir; elde edilmiş saha başarısı veya garanti değildir. [Ayrıntılı pilot varsayımları](docs/pilot-kayseri.md).

## Hesap nasıl yapılıyor?

1. Faydalı ısı ihtiyacı = ısıtma gazı × kazan verimi. Yalıtım yalnız ilgili ısı ihtiyacına uygulanır.
2. Isı pompasının karşıladığı faydalı ısı / SCOP, yıllık pompa elektriğini verir. Kapsanmayan veya cihaz kapasitesini aşan talebin kazan tüketimi ve ısıtma dışı gaz korunur. Birleşik müdahaleler yeniden hesaplanır; tekil tasarruf yüzdeleri toplanmaz.
3. Nihai enerji = yıllık elektrik + gaz enerjisi. Faydalı ısı bu toplama tekrar eklenmez. Enerji yoğunluğu = aynı dönem için toplam nihai enerji / toplam alan (kWh/m²-yıl); bina yüzdelerinin basit ortalaması değildir.
4. Bağlantı grubu piki, aynı zaman damgasındaki bina yükleri toplanıp en yüksek değer alınarak bulunur. Ayrı bina piklerinin toplamı kullanılmaz. Bina bağlantı sınırları da ayrıca uygulanır.
5. Her bina için uygun müdahale kombinasyonlarından bir paket seçilir. Mod A bütçe ve kapasite altında tasarrufu artırır; Mod B aynı sınırlar altında hedefe en düşük yatırımla ulaşır. Çözümsüz, süre sınırında uygun ve kanıtlanmış optimum sonuçlar ayrılır.

Uygulanmış müdahale başlangıç durumudur ve yeni yatırım sayılmaz; zorunlu müdahale yeni plana dahil edilir; aday müdahale seçilebilir veya elenebilir. Çatı/aydınlatma/program/ısı pompası kombinasyonları sistem uygunluğuna tabidir. Ortak ekipman maliyeti zon başına çoğaltılmaz. HVAC programı senaryosu, sıcaklık dinamiği modellenmediği için konfor garantisi vermez.

Oran yöntemi, kapasite kısıtları kaldırılmış optimizasyon ve GRID planı aynı veri/paket evreni ve fizik motoruyla karşılaştırılır. Kısıtsız plan kapasiteyi aşmıyorsa bu da gösterilir. “Bu müdahale seçilseydi?” ayrı hesap yapar, ana kaydı değiştirmez ve tek kesin seçim nedeni iddia etmez. Duyarlılık aynı planı düşük/temel/yüksek varsayımlarla değerlendirir; istatistiksel güven aralığı değildir.

Ekonomik tasarruf önce/sonra enerji maliyeti farkıdır; negatif değer gizlenmez. Basit geri ödeme yalnız yıllık net tasarruf pozitifse hesaplanır; finansman, iskonto, vergi ve tam yaşam döngüsü analizi değildir. [Elle doğrulanan örnek](docs/calculation-example.md) · [Varsayımlar](docs/assumptions.md).

## AI, ML ve optimizasyonun farklı rolleri

| Bileşen | Gerçek görevi | Sınırı |
|---|---|---|
| Fizik + SciPy MILP | Enerji/maliyet hesabı, bütçe ve elektrik sınırlarında paket seçimi | Eğitilmiş AI modeli değildir; sonuç girdilere bağlıdır |
| LLM asistanı | Motor sonuçlarını açıklar; kullanıcının isteğini incelenebilir alternatif senaryo taslağına dönüştürür | Sayısal kartlar motordan gelir; taslak kullanıcı çalıştırmadan hesaplanmaz, açık uygulama olmadan ana proje değişmez |
| Deneysel sentetik ML | Yıllık dönüşüm sonrası elektrik ve toplam gazı tahmin eder, fizikle karşılaştırılır | Kendi simülatörünü yaklaşık öğrenir; saha doğruluğu kanıtı değildir |
| ComStock sağlayıcısı | Ayrı ABD bina simülasyonu alt kümesinden tahmin | Türkiye/Kayseri ölçümü değildir; sentetik pilotla aynı veri seti değildir |

Sentetik ML eğitim veri seti **sekiz demo binası değil, 240 bağımsız sentetik binadır**: 168 eğitim, 36 validasyon, 36 test. Aynı binanın müdahale varyantları aynı grupta tutulur. Hedefler kWh/yıl elektrik ve **toplam** gazdır; gaz hedefi yalnız ısıtma gazı değildir. Artefaktlar, özellik şeması, veri kaynağı ve hata metrikleri model kartlarında kayıtlıdır. Bütün hedeflerde referans modelden üstünlük iddia edilmez. Üretimde yeniden eğitim yapılmaz; ML, MILP adaylarını veya saatlik kapasite uygunluğunu belirlemez.

LLM çağrısı yalnız backend üzerinden yapılır; anahtar frontend'e gönderilmez. Model/sağlayıcı erişilemiyorsa fizik ve optimizasyon çalışmaya devam eder; sahte AI yanıtı gösterilmez. Hesap, profil, açıklama ve dışa aktarım proje/revizyon/hesap/motor bağlamıyla ilişkilidir. Girdi değişince eski sonuç güncel sayılmaz. Adlandırılmış senaryolar bağımsız anlık görüntüdür; açılması ana projeyi değiştirmez.

[AI mimarisi](docs/ai-architecture.md) · [Sentetik model kartı](docs/model-card-synthetic.md) · [ComStock model kartı](docs/model-card.md) · [Teknik değerlendirme](docs/final-decision-review.md).

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
- Render: Docker runtime, kök `Dockerfile`, Root Directory boş, platform `PORT`, `0.0.0.0`, tek worker. `/api/health` kimlik doğrulaması gerektirmez; PostgreSQL bağlantısı ve şema durumunu denetler, erişilemezse 503 döndürür. Fizik verisi ve optimizasyon çözücüsü için `not_checked` bildirir; tam uçtan uca kabul testi değildir.
- Vercel: Root Directory `frontend`, Framework Vite, build `npm run build`, çıktı `dist`. Tarayıcı aynı origin `/api` kullanır; rewrite `https://portfolio25-api.onrender.com/api/:path*` hedefine gider. SPA API yollarını dışlar.
- Hedef yayın: **Render Free + Neon Free PostgreSQL**, Vercel frontend. Render: `STORAGE_BACKEND=postgres`, yalnız backend'de gizli `DATABASE_URL`, `COOKIE_SECURE=true`, `FRONTEND_ORIGINS=https://buildingportfolio25.vercel.app`. Neon pooled adresinin TLS parametrelerini koruyun. Ücretli instance veya `/var/data` diski gerekmez. Yerel geliştirmede `STORAGE_BACKEND=sqlite`, `DATA_FILE=data/campus.json` kullanılabilir.
- PostgreSQL modunda hesaplar, oturumlar, özel proje belgeleri/revizyonları ve hesap geçmişi PostgreSQL'dedir. Bağlantı kesilince SQLite/JSON'a geri dönülmez; istek 503 verir. Migration sürümlü ve tekrar çalıştırılabilirdir, kayıt sıfırlamaz. [Neon geçiş ve kabul adımları](docs/postgres-deployment.md).
- **Tarihsel kabul kaydı — güncel erişilebilirlik garantisi değildir:** 22 Ekim 2026 tarihinde Render/Vercel üzerinden PostgreSQL ve backend commit `2962183` doğrulandı. Gerçek tarayıcıda kayıt/giriş/çıkış, proje/revizyon, optimizasyon, sentetik ML ve sonuç dışa aktarımı çalıştı. Kontrollü yeniden yayın sonrası farklı süreçte aynı QA hesabı, düzenlenmiş proje/revizyon ve hesap sonucu korundu; parolayla tekrar giriş başarılı. [Canlı rapor](docs/live-deployment-report.md). Önceki kullanıcı hesabının 401 nedeni veya kurtarıldığı doğrulanmadı; yeni depolama geçmişte kaybolmuş kaydı kendiliğinden getirmez.

[Yayın rehberi](docs/deploy-render-vercel.md) · [Canlı kabul raporu](docs/live-deployment-report.md) · [Hesap/kayıt ve eski veriyi aktarma](docs/auth-and-storage.md)

## Hesap ve AI sınırları

Yatırım planı fizik ve SciPy MILP ile hesaplanır. Sentetik model yıllık elektrik/toplam gaz tahmini sağlar; optimizasyonu veya saatlik kapasiteyi belirlemez. ComStock sağlayıcısı ayrı ABD simülasyon verisine dayanır. İki model de saha doğruluğu veya hız üstünlüğü kanıtı değildir. Büyük ML/fizik farkları gizlenmez. LLM açıklaması isteğe bağlıdır. Önceki belgelenmiş gerçek denemede kota/kredi hatası görülmüştür; bu tarihsel bulgu güncel sağlayıcı durumunu kanıtlamaz. Anahtarın bulunması başarılı AI erişimi anlamına gelmez; hizmet hatası kullanıcıya gösterilir.

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

Bina sayfasında kat/kullanım, yatırım seçenekleri ve ML/fizik karşılaştırması ayrı sekmelerdir; sekme değişimi taslağı silmez. Özet ekranında plan oluşturma/sonuca gitme ve AI ile alternatif hazırlama eylemleri, ardından seçilebilir bina kartları bulunur. Ayrıntılı tablo, göstergeler ve koordinatsız şema gerektiğinde açılır. Senaryoda hesapla eylemi başlıktadır; mobilde alt menünün hemen üstünde sabit kalır. Sonuçta yatırım kararı ve seçilen paketler öndedir; karşılaştırma/duyarlılık ve çözücü kanıtı açılır bölümlerdedir. [Ürün gerekçesi](docs/electrification-positioning.md) · [PDR taslağı](docs/pdr-draft.md); özgün Task 1 veya ölçülmüş baseline yerine geçmez.

Git yalnız kaynak kodu, lock dosyalarını, dağıtım/migration dosyalarını, testleri, gerekli model artefaktlarını ve güncel belgeleri içerir. `.env`, kullanıcı/oturum/proje kayıtları, özel yedekler, yerel QA görüntüleri, loglar, `node_modules` ve `dist` dışlanır. Eski tek seferlik raporlar Git geçmişinde ve yerelde Git dışı arşivde korunur; model dosyaları çalışan çıkarım için gereklidir.

Final karar araçları: sonuçlarda yöntem karşılaştırması ve LLM gerektirmeyen “Bu müdahale seçilseydi?” hesabı. Sayfa altındaki adlandırılmış senaryolar bağımsız kayıt/inceleme sağlar; açmak ana projeyi değiştirmez. PostgreSQL migration 002 başlangıçta uygulanır; kayıtları sıfırlamaz. Motor 4.1.0 eski hesapları tarihsel kabul eder. [Final teknik değerlendirme](docs/final-decision-review.md).

## SSL, giriş ve sunucu hatalarını ayırma

- `ERR_SSL_PROTOCOL_ERROR`: HTTPS bağlantısı kurulamadığından uygulama henüz yüklenemeyebilir. Render'ın uyanmasını beklemek veya parola değiştirmek bu hatanın teşhisi değildir. Gizli pencere ve farklı ağ (telefonda Wi-Fi kapalı mobil internet) ile sabit üretim adresini deneyin. Vercel proje ayarlarında Domains bölümünde bu adresin doğru projeye/üretim dağıtımına bağlı olduğunu kontrol edin. TLS doğrulamasını veya CSRF korumasını kapatmayın.
- `403 İstek kaynağı izinli değil`: Sunucuya ulaşıldı fakat Origin izinli değil. Eski `frontend-...vercel.app` dağıtımı yerine yukarıdaki sabit üretim adresini kullanın; tüm Vercel alan adlarına genel izin vermeyin.
- `401 E-posta veya parola geçersiz`: Kimlik doğrulama reddidir; tek başına kaydın silindiğini kanıtlamaz.
- `502/503` veya zaman aşımı: Proxy, servis uyanması veya depolama erişimi ayrıca incelenmelidir. `/api/health` başarılı olması giriş/optimizasyon/LLM'nin tamamının çalıştığını kanıtlamaz.

**22 Ekim 2026 son bağlantı kontrolü:** Bu çalışma ortamında frontend TLS hatası yeniden üretildi; `vercel.com` HTTPS yanıtı verdi. Render sağlık kontrolü 200 ve PostgreSQL bağlantısı/şema doğrulaması döndürdü (backend `e378f18`). İlk backend isteği 20 saniyede zaman aşımına uğradı, sonraki deneme başarılı oldu. Frontend'in ağ/alan adı düzeyindeki kesin SSL nedeni ve farklı ağdan erişimi henüz doğrulanmadı; önceki kabul raporları güncel erişim garantisi değildir.

[Vercel resmî bağlantı teşhisi](https://vercel.com/kb/guide/troubleshooting-connectivity-issues).

### Güncel AI kullanıcı akışı

Bina ekranındaki **Seçenekleri AI ile incele** uygun müdahaleleri ve veri eksiklerini açıklamak içindir. Sonuç ekranındaki **Planı AI ile incele**, güncel hesaba bağlı soruları yanıtlar; henüz hesap yoksa plan oluşturmaya yönlendirir. **Alternatif dene** içinde kullanıcı değişikliği tarif eder, hazırlanan değerleri inceler, ayrı hesabı çalıştırır ve isterse girdileri uygular. Aynı ekranda bütçe/hedef/tarife elle de değiştirilebilir; bu seçenek AI yanıtı değildir. Taslak hazırlandığında giriş bölümü kapanır, değişiklik ve karşılaştırma öne geçer. Eski sonuçlar girdi değişince güncel sayılmaz.

Anahtar, son çağrı ve sağlayıcı test durumu kullanıcı çalışma alanında gösterilmez. AI kota, bağlantı ve yanıt doğrulama hataları kısa mesajlarla belirtilir; ham sağlayıcı/proxy yanıtları gösterilmez. Bu düzenleme sağlayıcı erişiminin çalıştığını kanıtlamaz. Yerel kabulde AI yanıtı/hatası taklit edilmiş, alternatifin fizik hesabı gerçek backend ile çalıştırılmıştır; ücretli LLM çağrısı yapılmamıştır.
