# Kayseri sentetik pilotu

**Kayseri için hazırlanmış sentetik pilot senaryo — saha ölçümü değildir.**

Veri seti `kayseri-synthetic-v1`, ana seed **25**. Gerçek kurum/işletme, sayaç, mimari plan veya hava dosyası kullanılmadı. Pilot üretiminde LLM veya ML kullanılmadı. Sonuçlar tanımlı varsayımlar altında aritmetik senaryolardır; gerçekleşmiş tasarruf veya konfor kanıtı değildir.

## Ekli pilot kapsamının yeniden doğrulanması — 20 Ekim 2026

Kapsam güncel kaynakta zaten uygulandığından uygulama veya pilot baştan oluşturulmadı. Mevcut kampüs, dört pilot ve kullanıcı kayıtları korundu. Bu oturumda LLM API çağrısı ve ML eğitimi **yapılmadı**; önceki ayrı AI/ML özellikleri de silinmedi. Saatlik enerji, müdahale, karşılaştırma ve duyarlılık kontrolleri fizik/MILP motorunda yürütüldü.

Doğrulama betikleri güncel arayüze uyarlandı: açılır proje yönetimi, yenilemede Kal/Vazgeç koruması, değişken kayıt revizyonu ve kayıtlı birim maliyetler kullanılır. Artık `--output-dir` ile önceki rapor/görüntüler ezilmeden ayrı kanıt klasörü seçilebilir. Çalıştırılan komutlar ve kayıtlar [yeniden doğrulama klasöründe](../artifacts/pilot-recheck-20261020-152538/README.md).

**Gerçek sonuçlar:** 61 backend testi (73,860 sn), 11 frontend testi, TypeScript/Vite üretim derlemesi geçti. Geçici veri üzerinde API ile 4 projede A/B hesabı, 8 binada dağılım/öneriler ve birleşik önizleme üretildi. Chrome'da dört proje geçişi, kat/kullanım yakıt toplamı, API ile birebir birleşik önizleme, taslak korunması, eski sonucun/export'un engellenmesi ve yalnız QA kopyasında kayıt→portföy hesabı çalıştırıldı. Üç kat görünümü 390/500/768/1536 px'de taşma yapmadı; SEVERE konsol hatası yok. Özgün sekiz JSON dosyasının önce/sonra SHA-256 değerleri aynı; ortam dosyaları incelenmedi/değiştirilmedi. Çalışan 5173/8000 sunucuları kullanıldı; ikinci sunucu başlatılmadı.

| Müdahale | Gerçekten hesaplanan kapsam | Yalnız inceleme adayı / korunacak tüketim |
| --- | --- | --- |
| Çatı/kabuk yalıtımı | Sekiz sentetik binada uygun ayrı senaryolar; çatı/kabuk birlikte seçilmez | Sistem/çatı uygunluğu sağlanmayan girdiler için etki verilmez |
| Aydınlatma | Sekiz binanın uygun alanlarında alan, W/m² ve kullanım programı üzerinden | Yalnız yüksek tüketim payı verimsizlik gerekçesi sayılmaz |
| Isı pompası | Sekiz binada SCOP, termal kapasite ve kazan yedeğiyle; elektrik artışı da raporlanır | Sıcak su müdahalesi eklenmez; uyumsuz sistemde hesaplanmış öneri verilmez |
| HVAC programı | Eğitim, kütüphane, idari bina ve ofiste **uzman incelemesi gereken hesaplanmış senaryo** | Laboratuvar, A/B konut blokları ve otelde yalnız inceleme adayı; tasarruf rakamı yok |
| Sıcak su / konfor | Sıcak su enerji dengesi içinde ayrı gösterilip korunur | Sıcak su tasarrufu, iç sıcaklık/konfor garantisi veya hava akışı sonucu hesaplanmaz |

Kat/zon ve ortak sistem toplamları elektrik, yakıt ve faydalı ısı için ayrı uzlaşır; iki kırılım toplanmaz, HP ısısı nihai enerjiye ikinci kez eklenmez. Yükleme ve kaydetme testleri kullanıcı dosyaları yerine geçici veri/ayrı QA proje kopyalarında yürütüldü. Canlı pilotta yalnız salt okunur inceleme, kayıt yazmayan önizleme ve mevcut kayıtları koruyan açık örnek yükleme eylemi kullanıldı.

**Güncel motor notu:** Aşağıdaki sayısal pilot teslimi ve sabit kat seçimi açıklamaları önceki sürümün tarihsel kaydıdır. Motor 4.0.0 eski seçimleri zorunlu yatırım olarak korur; açık kullanıcı geçişiyle uygulanmış/zorunlu/aday müdahaleler MILP'ye girer. Yeni çatı hedef U duyarlılığı ayrıdır. Pilot dosyaları yeniden üretilmedi. Ayrı ComStock ML modeli ABD kapsamlıdır ve bu pilot için tahmin vermez; LLM açıklayıcı pilot sayıları üretmez. [Güncel teslim](https://github.com/BnymGnc/Portfolio25/blob/c41071b/docs/improvement-report.md), [varsayımlar](assumptions.md), [model kartı](model-card.md).

## Yükleme ve koruma

Arayüzde **Proje ve örnek veri yönetimi → Kayseri sentetik pilotu → Ayrı pilot projelerini yükle ve aç** açık eylemi dört ayrı proje ekler. Önizleme GET'i kayıt oluşturmaz. Mevcut kampüs/projeler değiştirilmez. Tekrar yükleme mevcut pilot girdilerini ve hesaplarını sıfırlamaz; yalnız eksik pilot projeleri oluşturur. Sabit proje kimlikleri veri seti/rol adının SHA-256 özetinden türetilir. Başka kayıtla kimlik çakışırsa 409 döner, üzerine yazılmaz.

Varsayılan kampüs ayrıca korunur; toplam proje listesinde önceki projeler ile dört pilot birlikte görünür. Pilotun kendi dağılımı **4 proje / 8 bina**dır; önceki kampüsün sekiz binası bu pilotun parçası değildir. Dört projenin bütçeleri veya yükleri ortak bir kısıta toplanmaz.

## Dağılım

| Proje | Bina | Brüt alan | Kat | Zon ayrıntısı |
| --- | --- | ---: | ---: | --- |
| Temsilî kampüs | B01 Eğitim binası | 4.800 m² | 4 | Derslik, bilgisayar ve ortak alan; ayrıntılı örnek |
| Temsilî kampüs | B02 Kütüphane | 3.600 m² | 3 | Ana kullanım + ortak alan; kaba model |
| Temsilî kampüs | B03 Araştırma laboratuvarı | 2.400 m² | 2 | Ana kullanım + ortak alan; korunacak sürekli hizmet |
| Temsilî kampüs | B04 İdari bina | 1.800 m² | 3 | Ana kullanım + ortak alan; kaba model |
| Temsilî konut sitesi | B05 A blok | 3.000 m² | 5 | Yaşam, yatak ve ortak alan; ayrıntılı örnek |
| Temsilî konut sitesi | B06 B blok | 3.300 m² | 5 | Ana kullanım + ortak alan; kaba model |
| Bağımsız ofis | B07 Bağımsız ofis | 2.100 m² | 3 | Açık ofis, toplantı ve ortak alan; ayrıntılı örnek |
| Küçük otel | B08 Küçük otel | 2.800 m² | 4 | Ana kullanım + ortak alan; kaba model |

| Proje | Ortak yenileme bütçesi | Elektrik bağlantıları |
| --- | ---: | --- |
| Temsilî kampüs | 12.000.000 TL | Tek sentetik ortak grup 1.100 kW; dört bina sınırı ayrıca uygulanır |
| Temsilî konut sitesi | 7.000.000 TL | A blok 420 kW, B blok 462 kW; birbirinden bağımsız |
| Bağımsız ofis | 2.800.000 TL | Tek bağımsız bağlantı 294 kW |
| Küçük otel | 4.000.000 TL | Tek bağımsız bağlantı 392 kW |

Kampüs bina sınırları sırasıyla **672, 504, 336, 252 kW**. Bunlar saha bağlantı anlaşması değildir; brüt alan × 0,14 kW/m² sentetik varsayımıdır. Konut bloklarının **kazanları bağımsızdır**; ortak kazan/ısı merkezi veya maliyeti modellenmedi. Her binanın tek merkezî ısıtma, soğutma ve ayrı sıcak su sistemi birden fazla kata hizmet verir; kat başına yeni cihaz sayılmaz.

## Kullanım ve geometri varsayımları

- Eğitim/idari/ofis: hafta içi 08–18 kullanım, 06–22 HVAC hizmeti. Kütüphane: haftanın yedi günü 08–22 kullanım, 06–24 hizmet.
- Laboratuvar: yedi gün 24 saat, kritik hizmet; havalandırma azaltılmaz. Konut ve otel: yedi gün 24 saat hizmet gereksinimi korunur. Bu üç türde otomatik program azaltımı önerilmez.
- Eğitim ve laboratuvar kat yüksekliği 3,5 m, diğerleri 3 m. Eş alanlı katlar, yaklaşık kare taban çevresi ve alana göre dağıtılmış cephe kabul edilir. Pencere oranı ortak alanlarda %15, ofiste %32, diğer ana alanlarda %25. Pilot üreticisi sentetik K/G/D yönlerini döndürür; şema B yönüne de izin verir. Gerçek yerleşim değildir.
- Ayrıntılı eğitim katları %55 derslik/%25 bilgisayar/%20 dolaşım; A blok %55 yaşam/%25 yatak/%20 ortak alan; ofis %60 açık ofis/%20 toplantı/%20 ortak alan. Bunlar **alan girdileri**, rastgele enerji yüzdeleri değildir. Diğer binalarda %82 ana/%18 ortak alan yalnız kaba geometri varsayımıdır.
- Ana alan aydınlatması 9 W/m² (ofis 10), ortak alan 5; hedefler 4,5 ve 3 W/m². Cihaz yükü laboratuvarda 35, ofiste 12, diğer ana alanlarda 7, ortak alanda 1 W/m². Kullanım katsayıları konut/otel/laboratuvar için farklıdır; tam değerler API/JSON'da saklıdır. Doluluk kişi/100m² olarak saklanır; insan ısı kazancı veya konfor sıcaklığı ayrıca simüle edilmez.
- Duvar U değeri bina seed'iyle 0,9–1,4 arasında üretilir; pencere 2,5, çatı 1,25, zemin 0,7 W/m²K. Hava değişimi laboratuvarda 2, diğerlerinde 0,5/saat varsayımıdır. Hiçbiri ölçüm değildir.

## Hava ve zaman ekseni

2025-01-01 00:00+03:00 → 2026-01-01 00:00+03:00 hariç, **8.760 bir saatlik aralık**, Europe/Istanbul. Bütün pilot binaları aynı ekseni ve `kayseri-synthetic-v1` eğrisini kullanır:

`T = 10 + 15*cos(2π*(yılın_günü−200)/365,25) + 5*sin(2π*(saat−8)/24)`

Bu eğri **Kayseri ölçümü, meteorolojik normali veya doğrulanmış yerel iklim modeli değildir**; yalnız Kayseri için hazırlanmış demo senaryosudur. Isıtma ağırlığı max(18−T,0), soğutma ağırlığı max(T−22,0). 18/22 eşikleri hesap varsayımıdır; sağlanmış iç sıcaklık değildir. Kaynak proje içi sentetik formüldür; harici hava dosyası indirilmedi ve harici hava veri lisansı kullanılmadı. Kaynak/yıl/çözünürlük/lisans açıklaması proje `pilot.weather` alanında saklanır.

## Enerji paylaştırması ve uzlaştırma

Kat ve kullanım amacı aynı toplamın iki görünümüdür; **birbirine eklenmez**. Her zon yalnız bir kata aittir. Alan toplamları bina alanıyla doğrulanır; tüm sistem hizmet alanları mevcut zonlara referans verir.

- Aydınlatma/cihaz elektriği = alan × kurulu W/m² × gerçek takvimde kullanım saatleri × kullanım katsayısı / 1.000. Bu varsayımsal bileşenler bina toplamını aşarsa hata verilir; toplam zorla küçültülmez.
- Faydalı ısı toplamı mevcut modelde ısıtma gazı × kazan verimidir. Zon ağırlığı duvar/pencere/çatı/zemin için U×alan ve havalandırma için **varsayımsal** 0,33×hava değişimi×hacim ile kurulur. Sentetik derece-saat ve hizmet programına göre dağıtılır, başlangıçtaki yıllık faydalı ısıya normalize edilir.
- Hizmet dışında 0,45 göreli ısı ağırlığı kabul edilir; termal kütle veya sıcaklık dinamiği değildir. Dolayısıyla program değişince konfor korundu sonucu üretilemez.
- Soğutma yıllık elektriği açık sentetik girdidir: alan başına laboratuvar 28, otel 25, ofis 18, konut 8, diğerleri 14 kWh/yıl. Zon dağılımı alan/pencere, göreli yön etkisi ve sentetik soğutma derece-saatleriyle yapılır; cihaz verimi/konfor simülasyonu değildir.
- Ortak sistem elektriği ayrı satırdır; katlara/zonlara tekrar eklenmez. Ortak dolaşım alanları ayrıca zon olarak vardır. Ayrıştırılamayan elektrik kalanı alanla paylaştırılır ve açık etiketlenir; sessizce silinmez.
- Sıcak su gazı konutta 55, otelde 85 kWh/m²-yıl varsayımıyla tanımlanmıştır; mevcut ısıtma dışı gazın **alt bileşenidir**, ek enerji değildir. Diğer binalarda da küçük ayrı sıcak su girdisi vardır. Sıcak su/diğer gaz her müdahalede korunur.
- Sonraki HP elektriği zonlara sağlanan ısı oranında dağıtılır. Faydalı ısı raporlanır fakat nihai elektrik+yakıt toplamına tekrar eklenmez. Başlangıç ve sonrasında zon/kat/kullanım toplamları bina değerine 10⁻⁵ kWh toleransla uzlaşmazsa sonuç gösterilmez.

Kat yoğunluğu seçilen elektrik veya yakıt / kat alanıdır. Ortak sistem satırında alan olmadığı için yoğunluk boş gösterilir; kampüs/bina yoğunluğuna yeni bir alan veya enerji eklenmez. Kaynağı belirsiz artığı “verimsiz” alan diye yorumlayan kural yoktur.

## Hesaplanan müdahaleler

| Müdahale | Hesap ve maliyet | Uygunluk / sınır |
| --- | --- | --- |
| Çatı yalıtımı | Çatı temaslı yüzey U değeri hedef 0,35'e düşer; yalnız ısıtma ağırlığı yeniden hesaplanır. Çatı alanı × 650 TL/m², bina çatısında bir kez. | Uygun gaz kazanı/yalıtım ve iyileştirilebilen çatı gerekir; soğutma kazancı eklenmez. |
| Aydınlatma | Seçili uygun zonlarda hedef W/m² ile saatlik elektrik yeniden hesaplanır; alan × 180 TL/m². | Kurulu güç hedefin üstünde olmalı; alan ve kullanım saatleri değerlendirilir, tüketim payı tek başına verimsizlik değildir. |
| HVAC programı | Kullanım + gerekli hazırlık payını koruyan daha dar hizmet penceresinde ısı/soğutma ağırlıkları yeniden hesaplanır. Kontrol yatırımı bina başına 45.000 TL, zon başına değil. | Eğitim/kütüphane/idari/ofiste hesaplanmış **uzman inceleme senaryosu**. Açık inceleme kabulü gerekir. Laboratuvar/konut/otel kritik hizmetinde yalnız inceleme adayı; tasarruf rakamı/aktif seçim yok. |
| Kabuk/ısı pompası | Mevcut η, ilgili ısı payı, SCOP, termal kapasite ve kazan yedeği motoru korunur. | Yalnız uyumlu gaz kazanı/sulu dağıtım; elektrik kapasitesi tüm gerçek gruplarda denetlenir. |

Çatı ve çatı dahil kabuk/birleşik paket **çakıştığı için birlikte seçilemez**. Çatı + aydınlatma + program + HP gibi uygun birleşimler baştan hesaplanır; tekil tasarruf yüzdeleri toplanmaz. Merkezî HP ve program kontrolü kat başına fiyatlanmaz. Aydınlatmanın iç ısı kazançlarına etkisi ve çatı kaynaklı soğutma etkisi bu sürümde modellenmez.

Her öneri bulgu, etkilenen kat/zon, koşullar/eksikler, yıllık elektrik/yakıt etkisi, yatırım, enerji bedeli/net işletme farkı ve pik/kapasite etkisi taşır. Bunlar `spatial_service` tarafından hesaplanır; LLM metni değildir. Negatif elektrik veya ekonomik tasarruf korunur.

## Portföye yansıma ve eski sonuçlar

Önizleme salt okunurdur; diğer proje binaları müdahalesiz baz durumdayken kapasiteyi değerlendirir, portföy optimizasyonu yerine geçmez. Isıtma paketi önizleme seçimidir. **Kat seçimlerini ve varsayımları kaydet** yalnız bina kat girdisini kaydeder ve revizyon artırır; eski yatırım/kat sonucu güncel sayılmaz. Ardından portföy hesabı ısıtma paketini yeniden seçer.

Kaydedilmiş kat seçimleri her bina için **sabit taban**dır; MILP bu aşamada kat eylemlerini seçmez. Her ısıtma paketinde taban tüketim/maliyet bir kez yer alır. Müdahalesiz fiziksel baz ayrı korunur. Oran sezgiseli sabit taban yatırımını önce bütçeden düşürür, ek paketleri ek kWh/ek TL ile sıralar. Üç yöntem aynı eylem/paket evrenini kullanır. Duyarlılıkta maliyet çarpanı kat yatırımlarını da yeniden fiyatlar; paketler sabit kalır. Mevcut yalıtım duyarlılık ekseni kabuk paketinin ilgili ısı azaltımına aittir; çatı hedef U değeri ayrı kat varsayımıdır.

Eski kayıtlar isteğe bağlı spatial alanı olmadan çalışır; kat verisi uydurulmaz. v3 ana şema korunmuştur, `spatial.schema_version=1.0` isteğe bağlı alt modeldir; mevcut v3 kayıtlarına otomatik yazma/dönüşüm yapılmaz. Önceki v1/v2 yedekli dönüşümleri korunur. Yeni hesap önceki sonuç dosyasını SHA-256 adlandırılmış `data/history/<project-id>/` arşivine birebir koyar; eski sonuç sessizce kaybolmaz. CSV/JSON spatial modeli/seçimleri taşır, eski CSV gönderilmeyen yeni alanları silmez.

## Gerçek doğrulama ve örnek hesap

Önce önceki kapsamın **42 backend / 8 frontend testi ve üretim derlemesi** tekrar çalıştırıldı. Son kodda **52 backend / 9 frontend testi**, üretim derlemesi ve Chrome pilot akışı geçti. Yeni 10 backend testi alan/enerji dengesi, iki görünümün aynı toplamı vermesi, ortak sistemler, sıcak su, çakışan yatırımlar, korunacak hizmet, tek sayılan portföy maliyeti, salt okunur önizleme, revizyon ve tarihçe korumasını içerir.

`scripts/verify_kayseri_pilot.py` geçici DATA_FILE üzerinde gerçek API ile dört projede A/B, sekiz binada dağılım/öneri ve birleşik senaryo hesapladı. Sonuçları `artifacts/pilot/reports/` içinde; canlı kullanıcı kayıtlarına yazmaz.

**Örnek:** bağımsız ofiste çatı + aydınlatma + uzman inceleme programı + HP birlikte yeniden hesaplandığında yatırım **1.450.500 TL**, elektrik tüketimi **35.604,64 kWh/yıl artış**, ısıtma yakıtı **287.424,27 kWh/yıl azalış**, ek bakım sonrası net fark **249.158,02 TL/yıl** bulundu. Mevcut tarifeler elektrik 4,50 / gaz 1,50 TL/kWh sentetik varsayımdır. Sıcak su korunur; konfor doğrulanmadı. Bunlar koda sabitlenmiş çıktılar değildir.

| Proje | A yatırım / tasarruf | B yatırım / tasarruf |
| --- | --- | --- |
| Temsilî kampüs | 7.645.000 TL / 1.496.758,33 kWh/yıl | 2.325.000 TL / 948.047,86 kWh/yıl |
| Temsilî konut sitesi | 3.822.500 TL / 724.331,28 kWh/yıl | 1.617.500 TL / 631.280,60 kWh/yıl |
| Bağımsız ofis | 1.307.500 TL / 230.681,59 kWh/yıl | 572.500 TL / 199.322,33 kWh/yıl |
| Küçük otel | 1.710.000 TL / 338.748,64 kWh/yıl | 730.000 TL / 295.233,75 kWh/yıl |

Bu A/B tablo **henüz kat seçimi kaydedilmemiş** pilot girişlerinin ısıtma paketi optimizasyonudur; yukarıdaki birleşik ofis önizlemesiyle aynı senaryo değildir. %25 hedef, her projenin kendi bütçesi/sınırları kullanıldı. Bu çalıştırmalarda optimum kanıtlandı; sonuçlar veri değiştirilerek zorlanmadı. GRID üstünlüğü sonucuna zorlamak için kapasite/demand ayarlanmadı; üç yöntemin gerçek farkları API çıktısında gösterilir.

Chrome'da açık yükleme, dört projede geçiş, yakıt/elektrik kırılımı, API ile birebir birleşik önizleme, değişen varsayımda eski sonucu engelleme, ayrı QA kopyasında kaydet/portföye bir kez yansıtma, karşılaştırma/duyarlılık, 390/500/768/1536 px kontrolleri geçti. QA kopyaları yalnız son bilinen baytları eşleşirse arşivlenip kaldırıldı. Tüm önceden var olan JSON girdileri/sonuçları/yedekleri bayt bayt korundu. Görüntüler `artifacts/pilot/` altında incelendi.

Yeniden çalıştırma:

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v
.\.venv\Scripts\python.exe scripts\verify_kayseri_pilot.py
python scripts\browser_pilot.py
```

Son komut mevcut iki sunucuyu ve bu ortamda kurulu Selenium/Chrome'u kullanır; ikinci sunucu açmaz. Gerçek `.env` bu görevde okunmadı/yazdırılmadı veya değiştirilmedi. Backend kaynak değişikliğini almak için mevcut backend yeniden başlatıldı; frontend süreci korundu. Sunucular teslimde açık kalır. İnternete yayın yapılmadı.

## Yalnız inceleme adayları / sınırlar

Laboratuvar, konut ve otel programı azaltımı; sıcak su müdahalesi; uyumsuz sistemde çatı/HP; kat verisi olmayan eski bina; ortak blok kazanı ve dağıtım ağı; dinamik konfor ve hava akışı için doğrulanmış etki yoktur. Uygunluk sağlanmazsa öneri rakam üretmez veya API açık hata verir. Gerçek sayaçlar, hava/plan dosyaları, emisyon/tarife kaynakları, sistem performansı, iç sıcaklık ve yatırım teklifleriyle mühendislik doğrulaması gerekir. Genel konut sitesi desteği veya canlı dijital ikiz iddiası yoktur.
