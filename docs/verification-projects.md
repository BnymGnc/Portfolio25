# Proje kapsamı doğrulaması — 20 Ekim 2026

## Uygulananlar

- Mevcut React/FastAPI uygulaması genişletildi; fizik formülleri, MILP amaçları, düzenleme, revizyon koruması ve CSV/JSON korundu. Yeni uygulama bağımlılığı gerekmedi.
- Tek/çok bina projeleri ve ayrı JSON kayıtları; varsayılan kampüs korunur. Her bina tam bir bağlantı grubunda; proje bütçesi ortak, bağımsız beslemelerin saatlik sınırları ayrı.
- Üç gerçek karar hesabı: tanımlı oran sezgiseli, bina/grup elektrik sınırları kaldırılmış MILP, GRID MILP. Aynı uygun paket evreni ve fizik motoruyla bütçe, tasarruf, hedef ve kapasite ihlalleri gösterilir.
- Seçilen GRID planında tek değişkenli SCOP/yatırım/yalıtım düşük-temel-yüksek taraması; 9 satır, yeniden optimizasyon/olasılık iddiası yok.
- Isıtma sistemi/dağıtım ve yalıtım uygunluğu filtreleri; hariç paket gerekçeleri. Soğutma ve konut sitesi dönüşümü destekleniyor diye sunulmaz.
- Gelecek ML/kat-zon modülleri yalnız [product-roadmap.md](product-roadmap.md) gereksinim belgesidir; eğitim, simülasyon entegrasyonu, LLM veya canlı kontrol geliştirilmedi.

## Ortam ve gizlilik

Backend/.env başlangıçta yoktu; boş OPENAI_API_KEY ve kullanıcının istediği OPENAI_MODEL=gpt-5.4-mini ile oluşturuldu. Gerçek anahtar okunmadı/yazdırılmadı; varsa mevcut dosyayı açmadan koruyan oluşturma kullanıldı. `config.load_backend_env` kaynak konumunu kullanır ve override=False uygular. Testte farklı çalışma dizini ve sahte ortam değerleriyle süreç değişkenlerinin korunması doğrulandı. Boş anahtarla sağlık ve gerçek optimizasyon çalıştı. OpenAI istemcisi veya ücretli çağrı yok; alanlar uygulama veri modellerine/API'ye/frontend'e eklenmedi.

Git ignore kuralları ayrı geçici Git deposunda gerçek `git check-ignore --no-index` ile sınandı: backend/.env ve frontend/.env dışlanıyor; iki .env.example dahil edilebiliyor. Yeni proje JSON dizini de ignore kapsamına alındı. Çalışma klasörünün kendisi Git deposu olmadığından önceden takip edilmiş dosya geçmişi kontrol edilemedi.

## Kayıt dönüşümü ve koruma kanıtı

Başlangıç kopyaları `artifacts/stage5/before/` altında. Canlı v2 r26 kampüs v3 r27 oldu. id/name/scenario/profile_settings/provenance ve bütün eski bina alanlarının her biri eski değerle karşılaştırıldı: değişiklik yok. `backend/data/campus.v2-backup.json` başlangıç dosyasıyla bayt bayt aynı. Yalnız yeni alanlar ve dönüşüm notu eklendi; önceki r26 sonuç dosyası ilk aşamada tarihsel kaldı, güncel r27 A hesabı gerçek motorla yeniden üretildi.

Tekrarlanan tarayıcı testlerinde r27 girdi dosyası bayt bayt korundu. TestClient testleri geçici DATA_FILE kullanır. Yeni proje Chrome testi yalnız kendi oluşturduğu QA projelerine PUT yaptı; kaynak kampüse yazmadı. QA dosyaları testin son bilinen baytlarıyla eşleşirse artifacts/stage5 altında arşivlenerek çalışma alanından kaldırıldı. Başka süreç değiştirmiş olsaydı silinmeyecekti. Canlı proje listesinde yalnız kullanıcının varsayılan kampüsü kaldı; QA isimleri ekranda bırakılmadı.

## Çalıştırılan kontroller

| Kontrol | Gerçek sonuç |
| --- | --- |
| `.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v` | **42 test geçti**, 59,234 sn; kayıt artifacts/stage5-backend-tests.log |
| `npm.cmd test` (frontend) | **8 test geçti** |
| `npm.cmd run build` (frontend) | TypeScript + Vite üretim derlemesi geçti |
| `.venv\Scripts\python.exe -m pip check` | No broken requirements found |
| `python scripts\browser_delivery.py` | Mevcut kampüs akışı, aynı revizyon/kimlik export, eski sonuç, harita, CSV/profil/API hatası ve 390/500/768/1536 px geçti |
| `python scripts\browser_projects.py` | Tek bina ve iki bağımsız bina: oluşturma, düzenleme, kalıcılık, A hesabı, karşılaştırma, 9 duyarlılık satırı, grup grafiği, proje kimlikli export, eski sonuç, yeniden yükleme ve dört genişlik geçti |

Backend testleri tek/çok binada **A ve B** modlarını, proje izolasyonunu, tam v2 yedeğini/tekrarlanmayan dönüşümü, v1 uyumluluğunu, eski istemcinin gönderilmeyen alanları korumasını, grup üyeliklerini, eski skaler kapasitenin çok grupta yok sayılmasını, uygun olmayan paketlerin gerçekten seçilememesini doğruladı. İki binanın tüm kombinasyonları elektrik kısıtsız A/B sonuçlarıyla da karşılaştırıldı. Önceki GRID tam kombinasyon, enerji dengesi, eşzamanlı pik, negatif ekonomi, sıfır bütçe, imkânsız hedef ve başlangıç aşımı testleri de geçti.

Duyarlılık testleri temel satırın GRID sonucu ile eşitliğini, her satırda aynı paketlerin kalmasını, maliyetin çarpanla yeniden fiyatlanmasını, SCOP etkisini ve fiziksel aralık dışının kırpılmadan reddini kontrol etti. Sezgisel bütçe ve sonradan kapasite denetimi sınandı. Geniş sınırda kısıtsız planın ihlal yapmadığı, kontrollü dar sınır örneğinde gerçek ihlallerinin raporlandığı test edildi; bu kontrollü test gerçek kampüs üstünlüğü olarak sunulmadı.

Tarayıcı ilk denemede yeni duyarlılık alanında 0.8 yazısını 08'e dönüştüren kontrollü sayı alanı hatası yakaladı. Ham giriş metni korunarak düzeltildi; tek/iki bina akışı tekrar geçti. Beklenmeyen ciddi Chrome konsol hatası yok. Karşılaştırma, duyarlılık ve mobil proje ayarlarının görüntüleri `artifacts/stage5/` altındadır; görüntüler ayrıca incelendi.

## Gerçek mevcut kampüs karşılaştırması

25 milyon TL bütçe, 2.200 kW tek ortak grup; kullanıcı girdileri değişmedi:

| Yöntem | Yatırım (TL) | Enerji tasarrufu (kWh/yıl) | Kapasite |
| --- | ---: | ---: | --- |
| Oran sezgiseli | 11.802.500 | 3.954.949,85 | İhlal yok |
| Elektrik kısıtsız MILP | 24.892.500 | 4.611.280,52 | İhlal yok |
| GRID MILP | 24.892.500 | 4.611.280,52 | İhlal yok |

Kısıtsız ve GRID MILP bu girdilerde aynı amaç değerini verdi; ikisi optimum kanıtlı, gap=0. Kapasite ihlali açısından GRID üstünlüğü çıkmadı; ekranda bu açık belirtilir. Oran yöntemi daha az bütçe kullanır ve daha az toplam enerji tasarrufu sağlar; bu başka bir optimum iddiası değildir. Tam güncel CSV/JSON: `artifacts/stage5/current-project-result.*`; CSV 1.090.867 bayt ve 2 MiB içe alma sınırının altındadır. Zaman/çözücü kimliği tekrar hesaplamada değişebilir.

## Çalışma durumu ve sınırlar

Kullanıcı mevcut sunucuların çalıştığını belirtmişti; bu oturumun ilk gerçek bağlantı/port kontrolünde ikisi de kapalıydı. Boş portlarda yalnız bir backend ve bir frontend başlatıldı; gerekli backend kaynak değişikliği için bir kez yeniden başlatıldı. 8000/5173 HTTP 200, sağlık ok. Teslimde açık bırakıldı; aktif PID/başlama zamanları artifacts/runtime/processes.json içinde, README'deki stop-local.ps1 bunları güvenli kapatır. İkinci QA sunucusu başlatılmadı.

Yerel çalışma internet yayını değildir. Gerçek bina, elektrik anlaşması, iklim, ölçüm veya konut/soğutma doğrulaması yoktur. UI mevcut sentetik binalardan proje kopyalar; yeni gerçek veri alımı ve proje silme arayüzü yoktur. 1–50 bina şema sınırıdır; büyük projeler için performans doğrulaması yapılmadı. CSV içe alma 2 MiB ile sınırlıdır. Çok kullanıcı/yetki ve çok worker depolaması yok. Mevcut TestClient Starlette/httpx deprecation uyarısı sürer; test hatası değildir. LLM/ML/zon modülleri henüz çalışmaz; etkin özellik olarak gösterilmez.
