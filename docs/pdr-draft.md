# Portfolio25-GRID — PDR taslağı

**Kapsam:** Bina ısıtmasının elektrifikasyonu için yatırım öncesi karar desteği; ilk uygulama kampüslerde önceliklendirme. Özgün Task 1 ve ölçülmüş baseline eksik; problem hipotezi doğrulanmalı. Form gönderilmedi.

**Problem ve kullanıcı.** Gazla ısıtmayı ısı pompalarıyla elektrikleştirmek, gaz ihtiyacını azaltırken elektrik yükünü artırabilir; karbon etkisi SCOP ve emisyon faktörlerine bağlıdır. Kampüs teknik işler/enerji/tesis ekipleri hangi binadan başlanacağını belirler; yönetim yatırım kararını verir. Hipotez: bütçe, enerji ve bağlantıları ayrı ele almak eksik önceliklendirmeye yol açabilir. Kampüs görüşmesiyle doğrulanmalıdır.

**Çözüm.** Kullanıcı tüketim, alan, bütçe, hedef ve bağlantı gruplarını düzenler. Fizik motoru uygun müdahale kombinasyonlarını hesaplar. SciPy MILP bütçe ve saatlik bina/grup sınırları altında en yüksek enerji tasarrufunu veya hedefe en düşük yatırımı arar. Önce/sonra, yöntem karşılaştırması, duyarlılık ve güncel hesap için karar özeti/CSV/JSON sunulur. Değişen girdi eski sonucu geçersiz kılar.

**AI ve teknoloji.** React/TypeScript/Vite, Python/FastAPI, SciPy ve scikit-learn; Vercel/Render. 240 bağımsız sentetik binanın bina grupları ayrılmış simülasyon verisiyle eğitilmiş ML modeli yıllık elektrik/toplam gaz tahminini fizik hesabıyla karşılaştırır; yatırım veya pik kararını vermez. Bazı tahminlerde büyük hata vardır; kullanıcıya ek fayda/saha doğruluğu kanıtlanmadı. LLM isteğe bağlı açıklayıcıdır; başarı iddiası yok. Özel enerji/optimizasyon mantığı nedeniyle AI Studio yerine kod kullanıldı.

**Alternatif ve ayrışma.** Manuel/Excel oran sıralaması kontrollü referanstır. RETScreen portföy/fizibilite, EnergyPlus ayrıntılı bina simülasyonu sunar; aynı veriyle ürün kıyası yapılmadı. Öneri: kampüsün birlikte seçebileceği yatırımları açık bütçe/bağlantı sınırları ve hesap kanıtıyla göstermek; ilk/üstün olduğu iddia edilmez.

**Yalnız sentetik etki.** 2025, dört kampüs binası, aynı 12.600 m²: 3.526.744 → 2.029.986 kWh/yıl; 279,90 → 161,11 kWh/m²-yıl (%42,44 azaltım). Yatırım 7.645.000 TL; varsayımsal tarifeler ve ek bakım sonrası net tasarruf 1.012.573 TL/yıl. Modellenen sınırlar aşılmadı. GRID'siz plan aynı sonucu verdi; üstünlük gösterilmedi. Elektrik artarken gaz/toplam enerji azalır. %25 hedeftir; gerçekleşmiş tasarruf veya garanti değildir. Diğer dört bina ayrı üç projededir; hesaba eklenmez.

**Sonraki kanıt.** Çalışan hesap ve dışa aktarım prototipi mevcut. Sıradaki adım kampüs görüşmesi, alan/fatura/ısıtma ayrımı/bağlantı verisi ve kontrollü pilot doğrulaması. Kalıcı depolama panelden teyit edilmeli. Konfor, ayrıntılı termal simülasyon ve gerçekleşmiş tasarruf doğrulanmadı.

**Sınır.** Canlı cihaz kontrolü yapılmaz. Yatırım planı yıllık enerji/yatırımı optimize eder; karbon optimumu iddia edilmez. İşletme emisyonu, binanın tüm yaşam döngüsü değildir. [Gerekçe ve resmî kaynaklar](electrification-positioning.md).

**Öz değerlendirme taslağı:** Greener 3/5 (potansiyel); Circular 1/5 (atık/yeniden kullanım hesabı yok); Financeable 2/5 (teklif/ödemeye istek doğrulanmadı); Socially Impactful 2/5 (ölçülmüş sosyal etki yok). SDG 7.3 ana, 13 ikincil öneri. Puanlar jüri sonucu değildir.

**Demo:** https://buildingportfolio25.vercel.app · [Kanıt ve alternatif kaynakları](product-review.md) · [Model kartı](model-card-synthetic.md).
