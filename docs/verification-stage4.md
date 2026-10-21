# Dördüncü aşama teslim doğrulaması — 19 Ekim 2026

## Tamamlanan değişiklikler

Mevcut React/FastAPI motoru, veri şeması, düzenleme ve JSON kalıcılığı korundu. Hesap fiziği veya optimizasyon amacı başarı öyküsü üretmek için değiştirilmedi. Dışa aktarımlar açık inputs/result kapsamıyla, revizyon ve hesap kimliği denetimiyle üretildi. Aynı revizyonda farklı hesap oluşması da 409 ile korunur. Eski QA CSV/JSON, başlangıç dosyası ve güncel sonuç ayrımı [data-audit.md](data-audit.md) içinde kanıtlarıyla açıklandı.

Okunabilir yardımcı metinler, görünür ana hesaplama eylemi ve mobil üst menü eklendi. Önce/sonra **Kampüs senaryo modeli** API'deki seçilen paketleri renklendirir; tıklanan binada gerçek yatırım, enerji tasarrufu ve bireysel pik farkını gösterir. Şematik/sentetik etiket ve renk anahtarı görünür. Güncel hesap yoksa Sonra görünümü kullanılmaz.

## Gerçek çalıştırma

Windows PowerShell, Python 3.13.7 / Node 22.19.0. Mevcut bağımlılıklar kullanıldı; uygulama için yeni paket gerekmedi.

- Backend `.venv\Scripts\python.exe backend\run.py` ile başlatıldı. Log: `Uvicorn running on http://127.0.0.1:8000`; uygulama başlangıcı başarılı. API değişikliğinden sonra bir kez yeniden başlatıldı.
- Frontend kurulu Vite CLI ile frontend çalışma dizininde başlatıldı; eşdeğer kullanıcı komutu `npm.cmd run dev`. Log: `VITE v8.3.4 ready`, adres `http://127.0.0.1:5173/`.
- `/api/health` gerçek HTTP 200: status=ok, version=0.2.0, optimization_status=ready. Frontend HTML HTTP 200. Chrome gerçek API'den sekiz kayıtlı binayı yükledi.
- İki ana sunucu teslim sonunda **açık bırakıldı**. Süreçler/başlama zamanları `artifacts/runtime/processes.json`, günlükler aynı dizindedir. `scripts/stop-local.ps1` yalnız bu PID/başlama zamanı eşleşmelerini kapatır; teslim sırasında durdurma scripti çalıştırılmadı. İki terminalde kendi başlattığınız sunucuları Ctrl+C ile durdurun.

Ayrı portta ek QA sunucusu başlatma denemesi otomatik onay incelemesince engellendi. Bu süreç çalıştırılmış sayılmadı; yerine geçici dosyalı FastAPI TestClient ve canlı girdilere PUT yapmayan tarayıcı kontrolü kullanıldı. Selenium sanal ortamda bulunmadığından ilk tarayıcı komutu ModuleNotFoundError verdi; mevcut global Python'daki kurulu Selenium 4.41.0 ile komut düzeltildi ve gerçek Chrome kontrolleri geçti. Uygulamanın çalışması Selenium gerektirmez.

## Gerçekten çalıştırılan kontroller

| Kontrol | Sonuç |
| --- | --- |
| `.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v` | **34 test geçti**, 38,460 sn |
| `.venv\Scripts\python.exe -m pip check` | No broken requirements found |
| `npm.cmd test` (frontend) | **6 test geçti** |
| `npm.cmd run build` (frontend) | TypeScript kontrolü ve Vite üretim derlemesi geçti |
| `python scripts\browser_delivery.py` | Gerçek Chrome / canlı yerel frontend + backend, kayıtlı girdiler değişmeden geçti |
| `.venv\Scripts\python.exe scripts\prepare_delivery_demo.py` | İki gerçek API hesabı ve 8 kapsam/biçim çıktısı geçici DATA_FILE ile üretildi |
| `python scripts\audit_delivery_data.py` | Eski/güncel dosyalar salt okunur incelendi; SHA ve alanlar kaydedildi |

Backend test kapsamı:

- Elle örnek: 1.000 kWh ısıtma gazı × 0,8 = 800 kWh faydalı ısı. Birleşik pakette 640 kWh kalan ısının 400'ü pompa/240'ı kazan; 100 kWh HP elektriği, 300 kWh ısıtma gazı, 100 kWh diğer gaz. Toplam enerji 1.500 → 900 kWh; net maliyet tasarrufu 469 TL. Örneğe özel varsayımlar [calculation-example.md](calculation-example.md) içinde başlangıç varsayımlarından ayrıdır.
- Birleşik paket tekil tasarrufların toplamı değildir; yalıtım yalnız ilgili faydalı ısıya uygulanır. Diğer gaz ve kapasiteyi aşan/kapsanmayan ısı korunur. Negatif ekonomik tasarruf gizlenmez.
- Tam yıl/artık yılda saatlik elektrik ve ısı integralleri yıllık değerlere eşit; sabit seed yeniden üretilebilir. Kaydırılmış pikler ve alanla ağırlıklı yoğunluk doğrulanır.
- Küçük iki binada tüm **16** kombinasyon bağımsız taranır; A'nın en yüksek tasarrufu ve B'nin en düşük yatırımı MILP ile eşleşir. B bütçesi de uygulanır.
- Gerçek sekiz bina × dört paket ısı dengesi; A/B planlarında her **8.760 saatte** ortak sınır ve her binanın bağlantı sınırı kontrol edilir.
- Sıfır bütçe A'da sıfır yatırım/müdahale yok; %100 B hedefi karşılanamaz; başlangıçta 50 kW ortak sınır aşılmışsa iki modda da uygun plan yoktur. Ayrı bina sınırı ve ortak sınır ayrı testlerdir.
- Süre sınırındaki uygun aday, adaysız sınır ve geçersiz aday kontrollü çözücü testleriyle ayrılır. Gerçek kampüste süre sınırında uygun çözüm gözlendiği iddia edilmez.
- Geçici dosyalarda kalıcılık/dönüşüm, eski revizyon, hesap sürerken değişiklik, açık kapsamlı CSV/JSON, aynı revizyonda A→B hesap yarışı testleri geçti. Canlı kullanıcı girdisine yazılmaz.

Chrome kontrolü:

- API bağlantısı, 8 bina, hesap POST revizyonu, görüntülenen sonuç ve dört açık kapsam/biçim indirmenin kimlik eşleşmesi.
- Kaydedilmemiş bütçe değişikliği sonucu güncel değil yapar ve indirmeyi kapatır; yenileme kayıtlı değerleri PUT yapmadan geri getirir.
- Dört ekran **390, 500, 768, 1536 px** emülasyonda belge düzeyinde yatay taşma olmadan açılır. Mobil içerik sol kenarı 0; menü kalıcı yan sütunla daraltmaz. Geniş tablolar kendi içinde kayar.
- Haritada Sonra, bina seçimi ve yatırım/tasarruf/pik farkı ham sayıları API ile birebir karşılaştırıldı.
- Geçersiz CSV reddedildi; yeni sonuç CSV'si önizlendi ve kaydetmeden vazgeçildi.
- Gerçek profil yanıtından tarayıcıda bir saat çıkarılarak eksik profil hatası üretildi; sıfır doldurulmadı. Yeniden yükle gerçek profili getirdi.
- API istekleri tarayıcıda geçici engellendi; açık hata/yeniden dene çalıştı. Beklenen engelleme hataları dışında ciddi konsol hatası yok.
- `artifacts/delivery/desktop.png`, `results.png`, `mobile.png`, `campus-scenario-model.png` alındı. Masaüstü kampüs modeli ve mobil sonuç görüntüleri görsel olarak incelendi.

Canlı girdi r26 dosyası teslim başındaki kopyayla **bayt bayt aynı**, SHA-256 `cad01997adba241386007c42dbbd5bcd7edd67662bbcba5795f468d1e2a23974`. Canlı A hesabı aynı girdilerle tekrar hesaplandı; sonuç dosyasındaki süre/hesap kimliği bu nedenle yenilendi. Eski paylaşılan artifacts/portfolio25-grid.csv ve .json korunur.

## Demo hesapları

Tam girdiler, paketler ve sayılar `artifacts/delivery/scenarios/manifest.json` ve kapsamlı dışa aktarımlardadır. [2–3 dakikalık akış](demo-stage4.md).

| Senaryo | Mod / bütçe / ortak sınır / hedef | Gerçek sonuç |
| --- | --- | --- |
| A | A / 25 milyon TL / 2.200 kW / %25 | optimal, gap=0; 24.892.500 TL yatırım; 4.611.280,52 kWh/yıl (%45,26) tasarruf; 1.310,49 kW sonraki eşzamanlı pik |
| B | B / 8 milyon TL / 1.000 kW / %25 | infeasible, status_code=2; plan/sonra yok; yatırım ve tasarruf uydurulmadı |

## Kalan sınırlar

İnternet yayını yapılmadı; adresler yalnız yerelde çalışır. Gerçek ölçüm/iklim/elektrik mühendisliği kapasite doğrulaması, sıcaklığa bağlı saatlik COP, gerçek veri içe aktarımı ve çok kullanıcı veritabanı yok. TestClient'ta mevcut Starlette/httpx deprecation uyarısı sürer; test hatası değildir. CSV yalnız uygulamanın sentetik şablonunu günceller. Sentetik kapasite uygunluğu gerçek trafo yatırımı önleme garantisi olarak sunulmaz.
