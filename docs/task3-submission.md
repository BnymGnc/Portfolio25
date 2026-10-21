# Climathon Görev 3 — form kontrolü ve önerilen metin

Gönderilen form genel olarak mevcut prototiple uyumludur. Aşağıdaki metin kimlik/e-posta alanlarını içermez; bu kişisel bilgiler forma kullanıcı tarafından girilmelidir. Form gönderilmedi.

## Netleştirilen noktalar

- %25 değiştirilebilir hedef; gerçekleşmiş veya garanti tasarruf değildir. Aynı alan/dönemde enerji yoğunluğu azaltımı, toplam nihai enerji azaltımıyla karşılaştırılabilir.
- İlk problem odağı çok binalı kampüslerde yatırım önceliklendirmedir. Hedef kullanıcı teknik işler, enerji ve tesis ekipleri; karar sahibi kurum yönetimidir. Gerçek Task 1 tüketim/yoğunluk baseline'ı henüz sağlanmadı; sekiz sentetik bina bunun yerine sunulmaz.
- Kat/kullanım dağılımı, sentetik bina girdilerinden alan/kullanım/program varsayımlarıyla modellenir; ölçüm veya rastgele yüzdeler değildir.
- 240 bağımsız bina veri kümesinin toplamıdır; tamamı eğitim grubunda değildir. Eğitim/validasyon/test bina bazında ayrıdır. Sekiz demo bina eğitim satırı değildir.
- ML gerçekten inference yapar ama fizik/MILP planını belirlemez. Simülatörü yaklaşık öğrenir; üstünlük ve saha doğruluğu gösterilmedi. Bazı gaz tahminlerinde yüksek hata bulunur.
- Render servis planı ve kalıcı disk bağlantısı yönetim panelinden doğrulanmadı. “Ücretsiz plandayız” diye kesin yazılmamalı. Kalıcı disk yoksa dosya/SQLite değişiklikleri yeniden başlatmada kaybolur; ücretsiz web servisi disk bağlayamaz. [Render free](https://render.com/docs/free), [kalıcı disk](https://render.com/docs/disks).

## Çalışan prototipinin linki

https://buildingportfolio25.vercel.app/

Kendi hesabınızı oluşturup sentetik pilotla deneyebilirsiniz. Şifre paylaşılması gerekmez. İlk açılışta sunucu hazır değilse yüklenme gecikmesi olabilir; bir soğuk başlangıç süresi garantisi verilmez.

## Şu anda gerçekten çalışan temel fonksiyon

Portfolio25-GRID, kampüslerin teknik işler, enerji ve tesis yönetimi ekiplerinin sınırlı enerji dönüşümü bütçesini hangi binalara ve müdahalelere ayıracağını değerlendiren çalışan bir karar destek prototipidir. Kullanıcı tüketimleri, bütçeyi, enerji hedefini ve fiziksel elektrik bağlantı sınırlarını düzenler. Sistem fiziksel enerji hesapları ve matematiksel optimizasyonla yalıtım, ısı pompası ve uygun müdahale kombinasyonlarını değerlendirir; bütçe ve kapasite sınırları altında yatırım planı hesaplar. Aynı bina, alan ve yıllık dönem için başlangıca göre nihai enerji, kWh/m²-yıl, net ekonomik tasarruf ve bağlantı grubu kapasitesi karşılaştırılır. %25 azaltım düzenlenebilir bir senaryo hedefidir; garanti edilmiş veya sahada ölçülmüş sonuç değildir. Tek bina/konut desteği sonraki kapsam genişlemesidir.

Güncel konumlandırma: **bina ısıtmasının elektrifikasyonunu yatırım öncesinde öngörmek**. Gaz kazanından ısı pompasına geçişte elektrik/gaz/karbon ve kapasite etkileri birlikte gösterilir. Canlı cihaz kontrolü yapılmaz. Emisyonlar varsayımsal faktörlerle işletme tüketiminden hesaplanır; bütün bina/inşaat yaşam döngüsü veya karbon optimumu iddia edilmez. [Gerekçe ve kaynaklar](electrification-positioning.md).

## Araçlar, teknolojiler ve seçilme nedeni

Arayüzü React, TypeScript ve Vite; backend’i Python ve FastAPI ile geliştirdim. Fiziksel enerji hesaplarını bütçe ve elektrik kapasitesi kısıtlarıyla birlikte değerlendirmek için SciPy MILP, ayrı yıllık tüketim tahminleri için scikit-learn kullandım. Geliştirme ve hata gidermede VS Code içindeki Codex’ten yararlandım. Frontend Vercel, backend Render üzerinde yayımlanıyor; kod GitHub’da bulunuyor.

Özel enerji denklemleri, bağlantı grupları, kısıtlı optimizasyon ve eğitilmiş model inference’ını aynı uygulamada çalıştırmak için bu yapıyı seçtim. Google AI Studio kullanmadım. Gerçek bina verisi bulunmadığından dört projedeki sekiz pilot bina açıkça etiketlenmiş sentetik girdilerden oluşuyor.

## Çalışan bölümler ve mock/placeholder ayrımı

Proje/bina seçimi, girdileri düzenleme, fiziksel enerji hesabı, uygun müdahale kombinasyonları, bütçe ve bağlantı kapasitesi kısıtlı optimizasyon, yöntem karşılaştırması, sabit plan duyarlılığı, CSV/JSON dışa aktarımı ve eğitilmiş sentetik modelden gerçek inference uygulanmıştır. Kullanıcı kayıt/giriş/çıkışı ve kullanıcıya ait proje ayrımı çalışır. Canlı kontrol kapsamında dört proje/sekiz bina, ofis optimizasyonu ve sentetik ML inference doğrulandı; bütün uç durumlar için üretim garantisi verilmez.

Bina girdileri ve saatlik profiller sentetiktir. Kat/kullanım dağılımları bu girdilerden hesaplanan model paylaştırmalarıdır; gerçek sayaç/sensör ölçümü değildir. Bina görünümü koordinatsız şemadır; canlı dijital ikiz veya otomatik kontrol değildir. Sentetik veri, hesaplanmış sonuç yerine konulan sabit bir demo cevabı değildir; girdiler değişince motor yeniden hesaplar.

ML saha ölçümleriyle doğrulanmadı ve bazı senaryolarda fizik hesabıyla yüksek fark verir. Ayrı ComStock sağlayıcısı ABD simülasyonları içindir; Kayseri’ye uygunluğu iddia edilmez. LLM açıklayıcısının başarılı bağlantısı doğrulanmadığından çalışan çekirdek özellik olarak sunulmuyor. Kalıcı depolama bağlı değilse hesap/proje kayıtları yeniden başlatma veya yayın sonrasında kaybolabilir; mevcut Render disk bağlantısı ayrıca doğrulanmalıdır.

## AI kullanıcı için ne yapıyor?

240 bağımsız sentetik binadan üretilip bina bazında eğitim/validasyon/test kümelerine ayrılan simülasyon verisiyle eğitilmiş model, uygun bina ve müdahale için yıllık dönüşüm sonrası elektrik ve toplam doğalgaz tüketimini tahmin eder. Sekiz demo bina eğitim satırı değildir. Kullanıcı tahmini aynı bina/müdahalenin fizik hesabıyla yan yana inceleyerek farkı ve model sınırlarını görebilir. Eğitim aralığı dışındaki girdilerde tahmin verilmez. Bu işlev simülatöre dayalı deneysel karşılaştırmadır; sahada doğrulanmış tasarruf veya hız üstünlüğü sağlamış sayılmaz.

Yatırım planını ayrı fizik ve matematiksel optimizasyon motoru oluşturur. ML yıllık tahminleri saatlik pik/kapasite uygunluğuna dönüştürülmez; planı belirlemez. LLM başarısı iddia edilmez.

## 2–3 dakikalık gösterim

1. Kendi hesabınızla giriş yapın. “Temsilî kampüs” projesindeki dört binayı gösterin; sentetik etiketini belirtin. Diğer üç projenin dört binası ayrı bütçe ve bağlantılara sahiptir; kampüs hesabına eklenmez.
2. Senaryo girdilerinde varsayılan bütçe/hedef/bağlantıyı gösterip Mod A ile hesaplayın. Önce/sonra enerji yoğunluğu, yatırım, net ekonomik tasarruf ve kapasiteyi açıklayın. Sonuçlar API'den gelir; bu belge sayıları sabitlemez.
3. Bina detaylarında uygun birleşik paketi seçip “ML ve fizik sonucunu karşılaştır” çalıştırın. Yıllık elektrik/toplam gaz, büyük fark uyarısı ve saha doğrulaması sınırını gösterin.
4. Elektrifikasyon kartında elektrik artışı, gaz/karbon farkı ve faydalı ısı ayrımını gösterin. “Karar özeti indir” ile güncel belgeyi alın. Bütçeyi değiştirince eski sonuç indirilemez; yeniden hesaplayın. “%25 hedef; gerçekleşmiş tasarruf değil” diyerek bitirin.

Mevcut uygulamada kısa kapsam/demo açıklaması giriş yardımında ve Uygulama hakkında bölümündedir. Hesap, optimizasyon, ML artefaktı ve kayıt şeması bu değerlendirmede değiştirilmedi. [Canlı kabul kanıtı](live-deployment-report.md), [sentetik model kartı](model-card-synthetic.md), [güncel kampüs değerlendirmesi](product-review.md).

## Önceki form arayüzü güncellemesinin kontrolleri (tarihsel)

Frontend `npm.cmd test`: 15 geçti. `npm.cmd run build`: TypeScript/Vite üretim derlemesi geçti. Backend ve model dosyaları değiştirilmedi; bu görevde yeniden eğitim veya LLM çağrısı yapılmadı.

Gerçek Chrome'da 390/1440 px giriş yardımı, iç içe veri/altyapı açıklamaları, geçici yerel hesapla kayıt/tanıtım ve Hesap ve yardım → Uygulama hakkında erişimi kontrol edildi. Modal Escape ile kapandı; yatay taşma ve yakalanmamış konsol hatası bulunmadı. Özgün JSON kayıtlarının SHA-256 özetleri aynı kaldı; yerel test hesabı temizlendi. Ekranlar `artifacts/form-review/` altında Git dışındadır; mobil giriş yardımı ve mobil/masaüstü hakkında görüntüleri ayrıca açılıp incelendi.
