# Portfolio25-GRID iyileştirme teslimi

20 Ekim 2026. Mevcut React/TypeScript/Vite ve FastAPI/SciPy uygulaması genişletildi. İnceleme raporları kaynak kodla karşılaştırıldı; uygulanmış işlevler yeniden yazılmadı. Genel internet yayını yapılmadı.

## 1. Kayıt ve hesap doğruluğu

**Uygulananlar:** `PUT /api/campus` önce birleşmiş adayı Pydantic, kat/sistem ilişkileri, fizik motoru ve snapshot yanıt şemasıyla doğrular; ancak ardından atomik yazma yapılır. Pozitif soğutma enerjisi fakat hizmet verilen uygun zon olmaması alan bilgili 422 üretir. Başarısız istekte dosya/revizyon değişmez. Hatalar ortak code/message/fields biçimindedir.

`calculation_context.py` proje, revizyon, tam girdi SHA-256 özeti, UUID hesap kimliği ve motor sürümünü denetler. Motor sürümü 4.0.0. Son hesap, snapshot, profil, kanıt/duyarlılık, export ve AI bağlamı eşleşir. Çözüm süresi kimlik değildir. Başka proje, değişmiş hash veya motorla eski sonuç güncel sayılmaz; tarihsel dosya silinmez. Fizik ML kullanmadığı için model_version=null; ayrı ML yanıtı kendi model sürümünü taşır.

OpenAPI'de proje query parametresi, typed spatial/profil/kanıt/AI/ML response modelleri ve hata sözleşmeleri bulunur. Sağlık kontrolü erişimi doğrular; veri/çözücü `not_checked` değerini hazırlık başarısı diye göstermez. [26 işlemlik güncel envanter](api-inventory.md).

Senaryo, proje ayarları, bina ve kat düzenleme taslakları proje/bina anahtarlı localStorage ile korunur. Gezinme/yenileme/kapatmada Kaydet/Vazgeç/Kal veya tarayıcı kapanış uyarısı; yeniden açmada taslak kurtarma vardır. Proje değişmişken geç dönen istekler görünümü güncellemez.

**Kontroller:** Geçici veriyle geçersiz soğutma güncellemesi ve dosyanın birebir aynı kalması; proje/hash/motor karışması; yanlış grafik hesap kimliğine 409; eski sonuçtan export koruması. Tarayıcıda kaydet/kal/vazgeç, yenilemede koruma ve reload sonrası taslak kurtarma çalıştırıldı.

**Sınırlar:** Tek süreçli yerel JSON prototipidir; çok kullanıcılı veritabanı/kimlik doğrulama yok. Geçmiş dosyalar tutulur, tarihçe gezgini eklenmedi. localStorage taslakları bu tarayıcı profiline aittir. Yeni proje oluşturma sihirbazı mevcut enerji kayıtlarından ayrı bir formdur; bu form için ayrı taslak kurtarma henüz yoktur.

## 2. Gerçek müdahale seçimi

**Uygulananlar:** Uygulanmış/zorunlu/aday/hariç durumları ve çatı, kabuk, ışık, uygun HVAC programı, ısı pompası kombinasyonları. Uygulanmış eylem fiziksel başlangıca dahil edilir, geçmiş CAPEX tekrar yazılmaz. Zorunlu yeni eylem bütçeden düşer; aday gerçekten seçilebilir/elenebilir. Her bina için en fazla 32 şablon; tek tanımlı zon kapsamı, sınırsız zon alt kümesi yok.

Eski `spatial_selection` anlamı korunur: yeni `interventions` politikası null iken aynı sabit zorunlu yatırım uygulanır. Kullanıcı açıkça durumlara geçer; dosyalar sessizce dönüştürülmez. **Uygulanmış seçeneğinde yıllık girdiler uygulama öncesi referans olarak yorumlanır.** Motor bundan uygulanmış başlangıcı hesaplar; ölçülmüş mevcut tüketim üzerine ikinci kez tasarruf uygulanması anlamına gelmez. UI bu varsayımı açıklar.

Aynı motor tam kombinasyonu yeniden hesaplar. Çatı/kabuk çakışması ve sistem uygunsuzluğu filtrelenir, zorunlu geçersiz eylem 422 olur. Ortak ekipman/çatı bir kez sayılır; sıcak su ve desteklenmeyen tüketimler korunur. Müdahalesiz fiziksel başlangıç yeni zorunlu yatırım içermez; uygulanması gereken yeni yatırımlar adaylarda açık gösterilir. Sonuçta tüm eylemler ve ayrı maliyetler bulunur. Optimizasyon, oran sezgiseli, kısıtsız MILP ve sabit plan duyarlılığı aynı aday evreninden gelir.

Çatı hedef U-değeri düşük/temel/yüksek ekseni eklendi; kabuk azaltım parametresiyle karıştırılmaz. Seçilen yeni çatı varsa görünür. Dinamik konfor sonucu üretilmez; program uzman incelemesi gerektirir ve kritik hizmetler korunur.

**Kontroller:** Küçük ofis örneğindeki bütün uygun kombinasyonlar taranıp A/B MILP hedefleriyle karşılaştırıldı. Aday ışığın ve sıfır yatırımlı başlangıcın varlığı, çatı/kabuk çakışmaması, uygulanmış ışığın sıfır CAPEX'i, zorunlu çatının tek maliyeti, gerçek U duyarlılığı doğrulandı. Eski fiziksel enerji dengesi, sıfır bütçe, imkânsız hedef, başlangıç kapasite aşımı, bina/grup sınırı ve pilot uzlaştırma testleri de geçti.

**Sınırlar:** Sabit HVAC/alan şablonları kullanılır. Gerçek teklif, saha ölçümü ve konfor simülasyonu gereklidir; belirli bir müdahalenin mühendislik uygunluğunu garanti etmez. 50 binada yoğun saatlik MILP performansı bu teslimde benchmark edilmedi.

## 3. Karar odaklı arayüz

**Uygulananlar:** Proje özeti başlığı; açılır proje/örnek yönetimi; mobil içerik önceliği; karar özeti üstte, paket/karşılaştırma/duyarlılık altta. Kat ve kullanım kırılımları ayrı, enerji türü ve pay paydası etiketli. Veri eksikleri/varsayımlar erişilebilir. Haritada çatı/ışık/program işaretleri, gerçek API etkileri ve önce durumunda gelecekteki yatırımın gizlenmesi. Şema koordinatsızdır.

Grafikte Yılın tamamı tüm ekseni seçer; grup/dönem/hesap bağlamı denetlenir. Dönem piki ile yıllık pik ayrı, yıllık pik/aşım saatleri seçilebilir; saatlik sayısal tablo alternatifi ve mobil yatay kaydırma vardır. Soluk yardımcı metinler ve ana hesapla eylemi önceki tasarım diliyle iyileştirildi. Son konsol incelemesinde bina ekranındaki React key çakışması bulundu ve giderildi.

**Kontroller:** Chrome/Selenium ile 390/500/768/1536 px; ana dört ekran + Model ve veri; gezinme, taslak kurtarma, tam yıl ve önce/sonra harita akışı. Ekran görüntüleri ayrıca incelendi. Ayrı test dosyaları tarayıcıdaki SEVERE konsol kayıtlarını başarısızlık sayar.

**Sınırlar:** Gerçek GIS, mimari plan, akış/konfor veya canlı sensör temsili değildir. Grafik çok yıllı karşılaştırma içermez.

## 4. Hesaplara bağlı LLM asistanı

**Uygulananlar ve kullanılan veriler:**

| Ekran | Veri | İşlem |
| --- | --- | --- |
| Optimizasyon sonucu / Planı açıkla | Güncel hesap, seçili yatırımlar, üç yöntem, sabit plan duyarlılığı, kaynak/varsayımlar | Üç bulgu + açılabilir ayrıntı; sayısal kartlar backend fact alanlarından |
| Bina / Seçenekleri açıkla | Motorun uygun tam adayları, yatırım/enerji/pik, veri eksikleri | Uygun seçenekleri açıklama; yeni teknik kesinlik üretme yetkisi yok |
| Senaryo / Alternatif dene | Güncel bağlam ve dört izinli senaryo girdisi | Şemalı taslak → kullanıcıya farklar → geçici fizik hesabı → ayrıca açık uygulama |

Responses API structured output ve tek izinli function calling kullanılır; frontend anahtar almaz. Backend sabit sağlayıcı URL'si ve mevcut ortam yükleyicisini kullanır. Key içeriği incelenmedi/yazdırılmadı; `.env` korunmuştur. Serbest kod/shell/dosya yolu/keyfi endpoint aracı yok. Önbellek bağlam+model+soru+prompt sürümüne bağlı; 12 saniye timeout, en fazla bir sınırlı tekrar, boyut/token ve istek sınırı, yinelenen istek engeli vardır.

Sayısal bulgular izinli source_path/fact_id alanlarına bağlı; metinde yeni rakamlar reddedilir. JSON tek başına doğruluk kanıtı sayılmaz. Nitel LLM yorumunun mutlak doğruluğu garanti edilmez; kritik karar için hesap tablosu esas alınır. RAG/kaynaklı belge cevabı iddiası yok.

“Seçilmemeyi incele” düğmesi müdahaleyi zorunlu tutan gerçek karşı-olgusal çözümü kullanıcı isteğiyle çalıştırır; yatırım/tasarruf/kapasite farkını gösterir, kesin tek neden uydurmaz. Manuel bütçe alternatifi LLM'siz kullanılabilir. Her iki geçici hesap ana girdi ve son hesabı değiştirmez.

**Kontroller:** Sağlayıcı taklit edilerek strict tool alanları, fact eşleştirmesi, yanlış sayı reddi, cache/bağlam, eksik anahtar/hata ve fizik bağımsızlığı; geçici hesapta dosya değişmemesi ve açık apply doğrulandı. Tarayıcıda manuel alternatif ve karşı-olgusal hesap çalıştı. **Tek kısa gerçek bağlantı testi yapıldı; yapılandırılan model gpt-5.4-mini için sağlayıcı HTTP 429 döndürdü. Gerçek açıklama/function-call başarısı doğrulanmadı.** Bu durum kaydı `artifacts/improvements/llm-connection.json`; yeniden ücretli deneme yapılmadı. [Mimari ve resmî dokümantasyon](ai-architecture.md).

**Kalan:** Sağlayıcı erişimi düzeldikten sonra kullanıcının başlatacağı gerçek açıklama ve taslak uçtan uca kontrolü. Sahte AI yanıtı gösterilmez.

## 5. Değerlendirilebilir ML

**Uygulananlar:** Resmî ComStock veri sözlüğü ve upgrade lookup incelendi; ulusal/saatlik indirme yerine 6.862.854 baytlık sıkıştırılmış küçük yıllık alt küme alındı. CO/NY/TX, okul/ofis/otel; baseline, HP Boiler/Gas Backup, LED, Roof. Coğrafi yeniden ağırlıklandırma kopyaları temizlenince 739 bağımsız bina / 2.084 satır. Sekiz demo binası eğitim değildir.

Hedef yıllık dönüşüm sonrası elektrik ve toplam gaz. GroupShuffleSplit ile aynı binanın tüm varyantları birlikte: 443 eğitim, 148 validasyon, 148 test binası. Referans Ridge ve iki gradient boosting konfigürasyonu; model yalnız validasyon MAE ile seçildi, test tuning için tekrar kullanılmadı. Sonuçtan türetilmiş müdahale sonrası özellik yok; baz tüketim girdileri kullanılır. Model/şema/veri sürümü, checksum, split ve metrikler kaydedildi. Gerçek inference endpoint'i ve Model ve veri ekranı vardır.

Seçilen `gradient_boosting_15`, test 419 satırda elektrik MAE **13.543,83**, gaz MAE **13.800,24 kWh/yıl**; referans Ridge 17.970,93 / 32.414,05. Bina türü bazlı sayılar [model kartında](model-card.md). Seçilen modelin her test hedefinde en iyi olduğu iddia edilmez. Veri, bina simülasyonudur; saha doğruluğu veya Türkiye başarısı değildir.

**Kontroller:** Grup ayrımı/metadata/checksum, gerçek model inference, eğitim dışı girdi ve model yokluğu; proje dosyalarının değişmemesi. Tarayıcıda Kayseri girdisine kapsam dışı yanıt + ayrı fizik sonucu ve ayrılmış gerçek ComStock test girdisine yerel tahmin çalıştırıldı.

**Sınırlar:** Türkiye/Kayseri ve konut kapsam dışı; dar ABD ticari bina örneklemi. Saatlik pik/bağlantı/konfor tahmini yok. Fizik motorunu değiştirmez. Fizik motoruna karşı saha doğruluk veya hız faydası ölçülmedi. Lisans/atıf kaynağı kaydedildi; harici yeniden dağıtım koşulları ayrıca incelenmelidir.

## 6. Son doğrulama ve koruma

- Backend: **61 test geçti**, son tam koşu 72,390 sn; `artifacts/improvements/backend-tests-final.log`. Hesap sırasında aynı revizyonda doğrudan dosya değişikliği de son yazma öncesinde hash ile reddedildi. İlk doğrulama komutunda yanlış test dizini kullanıldı; gerçek dizin `backend` ile düzeltilip tamamlandı.
- Frontend: **11 test geçti**; `frontend-tests-final.log`. TypeScript kontrolü + Vite üretim derlemesi geçti; `frontend-build-final.log`.
- `pip check`: bozuk bağımlılık yok. ML bağımlılıkları uyumlu kurulu sürümlerle sabitlendi; mevcut NumPy/SciPy yükseltilmedi.
- Gerçek Chrome akışları: `browser-core-final.log`, `browser-ai-ml.log`; son kontrollerde SEVERE konsol kaydı kabul edilmez. Selenium sistem Python 4.41.0 ile çalıştırıldı; `.venv` içinde Selenium olmadığı için ilk başlatma komutu düzeltilmiştir.
- Özgün **8 JSON dosyası** (kampüs, eski sonuç, yedekler ve dört pilot) önce/sonra SHA-256 ile birebir aynı. Son kayıt: `preservation-final.json`. QA yalnız ayrı oluşturulan proje kopyalarında; son bilinen byte eşitliği denetlenerek arşivlendi/kaldırıldı. Mevcut `.env` okunmadı/değiştirilmedi.
- Frontend `http://127.0.0.1:5173`, backend `http://127.0.0.1:8000/api/health` HTTP 200 ile doğrulandı. Backend aynı portta kontrollü yeniden başlatıldı; frontend süreci korundu. Teslimde sunucular açık bırakıldı, internet yayını değildir.

Yeni hesap UUID'leri nedeniyle eski sonuç motor 4.0.0 altında yeniden hesaplanmalıdır; tarihsel dosyaya müdahale edilmedi. Kesin çalıştırma/durdurma komutları [README](../README.md), iki gerçek bütçe senaryosu [demo akışında](demo-improvements.md).
# 21 Ekim 2026 teslim güncellemesi

Önceki aşamaların ardından kayıt/giriş/sahiplik, tanıtım, kat önizleme tutarlılığı, gerçek sentetik ML eğitimi/inference, LLM kota ayrımı ve Render/Vercel teknik hazırlığı uygulanmıştır. Güncel testler, görsel kanıtlar ve açık sınırlar [final-delivery.md](final-delivery.md) içindedir. Aşağıdaki önceki raporun “hesap yok” veya yayın durumu ifadeleri tarihsel bağlamdadır.

