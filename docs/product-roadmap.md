# Ürün yol haritası — 20 Ekim 2026

Güncelleme: [Kayseri sentetik pilotunda](pilot-kayseri.md) sınırlı kat/zon paylaştırması ve müdahale önizlemesi uygulanmıştır. Ardından ComStock küçük yıllık alt kümesinde gerçek eğitim/inference ve backend LLM akışları eklendi: [model kartı](model-card.md), [AI mimarisi](ai-architecture.md), [teslim raporu](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/improvement-report.md). Aşağıdaki modül önerileri önceki gereksinim kaydıdır; yıllık ML ve statik kat paylaştırmasının dar ilk sürümü artık vardır. Ayrıntılı termal ağ, saatlik ML, dinamik konfor ve Türkiye saha doğrulaması gelecek iştir. Pilot mimari plan, hava akışı veya dijital ikiz uygulaması değildir.

LLM için tek gerçek bağlantı denemesi HTTP 429 aldı; uygulanan açıklayıcı akışları taklit sağlayıcıyla doğrulandı. Otomatik klima konumlandırması veya canlı dijital ikiz geliştirilmedi; bunlar için etkin düğme yoktur.

## Şimdi uygulanan temel

Tek/çok bina projesi, proje bütçesi, ayrı bağlantı grupları, ısıtma müdahalesi uygunluğu, üç yöntemle karar karşılaştırması ve sabit plan duyarlılığı vardır. Veri sentetiktir; ölçülmüş uygunluk veya kesin tasarruf garantisi değildir. Mevcut kampüs varsayılan örnektir. Bağımsız bağlantılara tek ortak trafo kısıtı uygulanmaz.

## Modül 1 — ML enerji/paket etkisi tahmini (ilk gereksinimler; yıllık alt kapsam uygulandı)

Amaç: bina ve müdahale özelliklerinden yıllık nihai enerji veya saatlik ısı/yük profili tahmini; mevcut fizik motoruna alternatif bir sağlayıcı olarak bağımsız değerlendirme. Eğitim ve test yapılmadan “eğitilmiş AI” veya “doğrulanmış tasarruf” denmez.

ComStock ABD ticari bina stokunun yıllık ve zaman serili son kullanım simülasyon sonuçlarını yayımlar; bina/model özellikleri ve veri sözlükleri erişim kaynaklarında bulunur. Bu kampüsün veya Türkiye binalarının ölçümü değildir. Alan ve müdahale kimlikleri seçilen sürümün sözlüğünden alınmalıdır. [Resmî veri setleri](https://comstock.nlr.gov/page/datasets), [resmî veri yapısı rehberi](https://natlabrockies.github.io/ComStock.github.io/docs/data.html).

Alternatif: kaynağı **synthetic** olarak saklanan kontrollü simülasyon örnekleri. Harici ComStock simülasyonu **external_simulation**, varsa ayrı ölçüm kaynağı **measured** etiketlenir. Mevcut aritmetik motor çıktılarından eğitim yalnız bu motorun yaklaşık kopyasını üretir; bağımsız fiziksel doğrulama değildir.

Gerekli veri sözleşmesi:

- dataset/release/model_id, motor/sürüm, iklim ve hava dosyası/yılı, kaynak URL/lisans/erişim tarihi ve dosya karması;
- bina kullanımı, alan/birim sistemi, geometri/kabuk özellikleri, HVAC/dağıtım sistemi, doluluk ve işletim çizelgeleri;
- baz/müdahale kimliği ve uygulanabilirliği, yakıt ve son kullanım bazında yıllık ve saatlik enerji;
- zaman dilimi/aralık, damganın başlangıç/son tanımı, örnek ağırlığı; maliyet için ayrı kaynaklı teklifler.

ft²→m² ve yakıt enerjisi dönüşümleri açık kaydedilir. Alt saatlik kWh saatlik kWh'ye toplanır; kW süreyle ağırlıklandırılır. Isıtma, sıcak su, soğutma ve diğer gaz ayrıştırılır; zaman ve enerji audit'i zorunludur. Baz yük şekli otomatik olarak tasarruf şekli kabul edilmez; resmî EULP rehberi tasarruf için ayrı şekilleri işaret eder. [Resmî son kullanım profilleri rehberi](https://www.nlr.gov/buildings/end-use-load-profiles).

Doğrulama kapısı: aynı baz binanın müdahale kopyaları eğitim/test arasında bölünmez. Bina ve iklim gruplu test; basit referansla MAE/RMSE, yıllık enerji, pik ve enerji dengesi karşılaştırması; kapsama alanı dışında tahmin reddi/uyarı; model kartı, sürüm ve tekrarlanabilir seed gerekir. ABD simülasyon testleri Türkiye'de gerçekleşmiş tasarruf kanıtı sayılmaz. Kabul eşikleri veri incelendikten sonra belirlenecek; henüz bilinmiyor.

Entegrasyon önerisi: `profiles.generate_profiles` / `engine.calculate_package` yerine gizli model koymak yerine, sürümlü bir `PackageProfileProvider` aynı eksende `PackageProfile` ve model/dataset kaynağı üretir. `prepare` audit'i, uygunluk filtresi ve MILP korunur. `CalculationResult` sağlayıcı/model/dataset kimliğini taşır. Mevcut deterministik sağlayıcı geri dönüş olur. Eğitim API isteği içinde çalışmaz. Bu arayüz henüz kodlanmadı.

## Modül 2 — kat/zon enerji ve konfor senaryosu (statik enerji uygulandı; dinamik konfor gelecek iş)

Amaç: kullanıcının tanımladığı kat/zonların kabuk, kullanım ve HVAC senaryolarını enerji, kapasite ve konforla karşılaştırmak. Canlı bina ikizi değildir.

Gerekli veri: proje/bina/kat/zon kimlikleri ve ilişkileri; alan/hacim/yönlenme, yüzeyler, pencere alanı, U-değerleri, güneş kazançları, komşuluklar ve ısıl kütle; iklim dosyası/zaman ekseni; doluluk/aydınlatma/cihaz, sızıntı ve havalandırma çizelgeleri; ısıtma/soğutma set değerleri, işletim saatleri, sistem ve dağıtım kayıpları; termal/elektrik kapasite ve sıcaklığa bağlı performans. Konfor için hava/operatif sıcaklık, gerekiyorsa nem, hava hızı, giyim/metabolizma varsayımları gerekir. Eksik geometrinin yerine gerçekmiş gibi koordinat üretilmez.

İlk model önerisi kaynaklı dış simülasyon veya etiketli indirgenmiş termal ağdır. Zon ısıtma/soğutma ihtiyacı, karşılanan/karşılanmayan yük, elektrik, sıcaklık ve tanımlı konfor bandı dışındaki saatler raporlanır. Konfor eşikleri kaynak/tarihli yapılandırılır; bağımsız inceleme olmadan standart uygunluğu iddia edilmez. Zon alan/enerji toplamları bina sınırıyla, eşzamanlı yükleri bina ve bağlantı gruplarıyla tutarlı olmalıdır. Isıtma ve soğutma kapasiteleri ayrı kısıtlardır.

Entegrasyon önerisi: Building altında sürümlü kat/zon alt modeli; zon sağlayıcısından bina paket profili; mevcut yıllık/saatlik audit ve bina→grup kapasite denetimi. Bina detayındaki senaryo/konfor sekmesi ancak veri ve hesap endpoint'leri çalıştıktan sonra açılır. Export model, kaynak, varsayımlar ve karşılanmayan yükü taşır. Bu görevde kat/zon ekranı/endpoint'i eklenmedi.

## Konut sitesi için açık eksikler

Mevcut Konaklama örneği öğrenci yurdudur; konut sitesi desteği değildir. Daire/ortak alan ve sayaç/bağlantı sınırları, bireysel/merkezî sistemler, kullanım ve sıcak su profilleri, sıcak su/hijyen ve boyler yedeği, eşzamanlılık, zon konforu ve ısıtma/soğutma cihazları bilinmeden başlık değiştirmek yeterli değildir. Bu veriler ve doğrulama eklenene kadar konut sitesi destekleniyor diye sunulmaz.

## Bilinmeyenler

Veri seti sürümü/lisans koşulları, eğitim hedefi/örnek büyüklüğü, model ailesi, kalite eşikleri, yerel iklim eşlemesi, zon motoru, gerçek veri erişimi ve yayın altyapısı henüz kararlaştırılmadı. İndirme/eğitim veya ücretli hizmet başlatılmadı.
