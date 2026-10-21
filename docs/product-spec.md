# Portfolio25-GRID ürün kapsamı — proje genişletmesi

## Güncel teslim — 20 Ekim 2026

Kayıt doğrulama, hesap bağlamı, korunan taslaklar, uygulanmış/zorunlu/aday müdahale kombinasyonları ve karar odaklı ekranlar uygulanmıştır. Üç asistan akışı backend'e bağlandı; gerçek sağlayıcı bağlantısı 429 ile sınırlıdır. Ayrı ComStock yıllık tahmin modeli eğitildi ve inference ekranı eklendi; ana fizik/MILP motorunun yerine geçmez, Kayseri kapsam dışıdır. Mevcut kayıtlar ve sentetik pilot korunur. [Yapılanlar, kontroller ve sınırlamalar](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/improvement-report.md).

Aşağıdaki aşama kayıtları tarihçedir; ML/LLM yok ve kat eylemleri sabittir ifadeleri bu güncellemeyle değişmiştir. Gerçek iklim/konfor, saha doğrulaması, kullanıcı hesabı, otonom kontrol ve genel internet yayını eklenmedi.

## Kayseri pilotu — uygulanan ek kapsam

Önceki proje/grup/karşılaştırma/duyarlılık kapsamı doğrulandı ve korundu. Ayrı yükleme eylemiyle dört projede sekiz bina; isteğe bağlı bina→kat→kullanım alanı modeli, uzlaştırılmış elektrik/yakıt/faydalı ısı dağılımı ve yeniden hesaplanan müdahale senaryoları eklendi. Eski kayıtlar sessizce değiştirilmez. Genel konut sitesi, dinamik konfor veya termal simülasyon doğrulaması yerine sınırlı, bağımsız blok kazanlı sentetik örnek sağlanır. ML/LLM yoktur. Güncel kapsam ve sınırlar [pilot-kayseri.md](pilot-kayseri.md) içinde; aşağıdaki önceki kararlar tarihçedir.

## Güncel kapsam — 20 Ekim 2026

Kampüs tek zorunlu kullanım değildir. Proje 1–50 sentetik bina içerir; mevcut sekiz binalı kampüs varsayılan örnektir. UI seçilen mevcut binaları ayrı tek/çok bina projesine kopyalar; kaynak proje değiştirilmez. Her proje ayrı JSON ve sonuç dosyasıyla saklanır. Gerçek veri ve konut sitesi desteği yoktur.

Bütçe proje portföyünün tamamına aittir. Elektrik sınırları her bina ve tam bir fiziksel bağlantı grubunun saatlik toplamı üzerinden uygulanır. Bağımsız bağlantılara toplam trafo sınırı konmaz. Yeni projeler varsayılan olarak bağımsız bağlantılıdır; ortak bağlantı açıkça seçilir.

Üç yöntem aynı uygun paket evrenini kullanır: tanımlı kWh/yıl/TL oran sezgiseli, elektrik sınırları kaldırılmış MILP, GRID MILP. SCOP/maliyet/yalıtım için tek değişkenli düşük/temel/yüksek koşullarda seçilmiş plan sabit değerlendirilir. Üstünlük ve olasılık iddiası yoktur. Uyumsuz ısıtma sistemleri gerekçeyle filtrelenir. Soğutma dönüşümü modellenmez.

v2→v3 yedekli dönüşüm eski değerleri korur; revizyon bir artar, eski hesap tarihsel kalır. Backend ortam dosyası çalışma dizininden bağımsız ve mevcut süreç değişkenleri ezilmeden yüklenir. OPENAI alanları yalnız hazırlıktır; LLM entegrasyonu/çağrısı yoktur. Gelecek modüller [product-roadmap.md](product-roadmap.md) içinde öneridir.

Aşağıdaki önceki aşama kararlarında geçen sekiz bina/tek kampüs zorunluluğunun yerini bu proje/grup kuralları alır.

Ana soru: Tek bina veya çok bina projesi sınırlı bütçesini hangi yalıtım ve ısı pompası paketlerine ayırırsa bina ve fiziksel bağlantı grubu sınırlarını aşmadan en iyi enerji tasarrufunu sağlar?

Hedef kullanıcı üniversitenin teknik işler ve enerji yönetimi ekibi. Gerçek bina/AGÜ verisi yoktur; eğitilmiş AI iddiası bulunmaz.

## Kesinleşmiş ve uygulanan kapsam

İlk aşamanın React/TypeScript/Vite + FastAPI teknolojileri, seed=25 ile 8 bina, bina düzenleme, kalıcı JSON, senaryo, revizyon denetimi ve CSV/JSON korunur.

İkinci aşama:

- Yedekli 1.0 → 2.0 dönüşüm; eski kayıt/istemci yeni alanları kaybetmez.
- Isıtma ve diğer doğalgaz ayrımı; ayrı bina bağlantı ve kampüs ortak besleme sınırları.
- Düzenlenebilir kazan verimi, ilgili ısı payı, yalıtım azaltımı, SCOP, pompa kapasitesi/kapsama payı ve yatırım/bakım varsayımları.
- Fiyat/emisyon için ayrı düzenlenebilir tarih ve kaynak.
- Yıllık enerjiye normalize sentetik saatlik elektrik ve faydalı ısı; tutarlılık audit’i ve zaman damgalı profil API’si.
- Dört paket için ayrı fizik hesabı; pompanın karşılamadığı ısıda açık doğalgaz kazan yedeği.
- Paket profilleri üzerinden SciPy MILP; her binaya tam bir paket.
- Mod A: bütçe ve her iki kapasite sınırı altında en yüksek yıllık nihai enerji tasarrufu.
- Mod B: hedefe bütçe ve kapasite sınırları altında en düşük yatırımla ulaşma; açık çözümsüzlük bildirimi.
- Eşzamanlı saatlik kampüs piki; ayrı bina piklerinin toplamı kapasite kararı değildir.
- Çözücü durum/süre/gap/amaç sınırı ve bağımsız uygunluk kontrolü; kanıtlanmayan sonuç optimum değildir.
- Enerji, yoğunluk, maliyet, emisyon, yatırım, elektrik piki ve basit geri ödeme; negatif ekonomik tasarruf korunur.
- Mevcut arayüzde sade Hesapla formu, önce/sonra ve bina/paket tabloları. Ayrıntılı görsel tasarım yapılmaz.
- Sonucun revizyonla kalıcı kaydı, girdi değişince geçersizleşmesi, güncel planın CSV/JSON çıktısı.
- Elle hesap, tam kombinasyonlarla MILP kontrolü ve tarayıcı entegrasyon testleri.

## Öneriler — henüz uygulanmadı

Gerçek saatlik elektrik ve iklimle doğrulama; saatlik COP/kapasite, kazan sınırı ve yardımcı elektrik; yatırım teklifleri ve detaylı ekonomi; gerçek veri içe aktarma; çok kullanıcı veritabanı; sonraki aşamada ayrıntılı görsel tasarım.

## Henüz bilinmeyenler

Gerçek tüketimler, gaz payı, bağlantı anlaşmaları, SCOP/COP, ısı kaybı, maliyet/etki, gerçek tarife/emisyon kaynakları ve yayın sağlayıcısı bilinmiyor. Yerine kullanılanlar açık sentetik varsayımlardır; mühendislik uygunluk belgesi değildir.

Hesap, ödeme, EV, batarya, IoT, otonom kontrol ve chatbot kapsam dışında. Bu aşamada internet yayını yapılmaz; yerel çalıştırma ve sonraki yayın yapılandırması korunur.

## Üçüncü aşama — kullanılabilir demo arayüzü

Yukarıdaki ikinci aşama motoru ve v2.0 veri sözleşmesi korunarak uygulandı:

- Türkçe dört ekran: kampüs özeti/envanter, bina detayları/paket karşılaştırması, senaryo girdileri, optimizasyon sonucu.
- Gerçek API sonuçlarından yatırım/kalan bütçe, yıllık kWh ve yüzde tasarruf, önce/sonra yoğunluk, enerji bedeli farkı, ek bakım sonrası net fark, hedef ve çözücü durumu.
- Tam yıllık sentetik profilin 1/7/30 gün veya yıl kesiti; aynı eksende önce/sonra kampüs elektrik yükleri ve kapasite; pik haftası ve saat inceleme kontrolü.
- Paket katkısı ve alternatif farkları hesaplanmış yatırım/enerji/pik değerlerinden açıklanır; tekil bina seçimi için kanıtlanmamış küresel nedensellik iddiası yoktur.
- Eski sonuç, kaydedilmemiş değişiklik ve yenileme sonrası dahil, güncel değil diye işaretlenir; güncel sonuç diye dışa aktarılmaz.
- Optimum, süre sınırında uygun aday, süre sınırında aday yok, çözümsüzlük ve hata durumları ayrılır.
- Kolay erişilen varsayım/kaynak penceresi; örnek verinin sentetik olduğu sürekli görünür.
- Kendi sentetik CSV şablonunu doğrulayıp önizleyerek güncelleme; API/profil/CSV/çözümsüzlük için anlaşılır hata ve kurtarma.

Önceki bölümde gelecek iş olarak geçen ayrıntılı demo tasarımı bu aşamada yapılmıştır. Gerçek veri içe aktarma, gerçek şebeke uygunluk onayı ve saatlik sıcaklık/COP modeli hâlâ kapsam dışıdır. Yerel uygulama olarak doğrulanır; internet yayını yapılmaz.
