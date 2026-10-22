# Portfolio25-GRID — Climathon için değerlendirme ve öneriler

Bu belge kullanıcının aktardığı Görev 1–4 ölçütleri, mevcut kaynak kodu, model metadata'sı ve motorla yeniden hesaplanan sentetik örnek üzerinden hazırlanmıştır. Jüri puanı veya saha doğrulaması değildir. Bu görev yeni model, ücretli LLM çağrısı veya ML'yi optimizasyona bağlama içermez.

## Önerdiğim ana hikâye

**Kampüslerde yatırım önceliklendirme problemi → çalışan fizik/optimizasyon prototipi → sentetik senaryolarda karşılaştırma → gerçek bina verisiyle pilot doğrulama.**

Ana kullanıcı kampüsün teknik işler, enerji ve tesis yönetimi ekibi; yatırım kararını veren kurum yönetimidir. Ofis, otel ve konut desteği kapsam genişlemesidir; final hikâyesini dört ayrı müşteri segmentine bölmeyin. Arayüzde bu projeler çalışmaya devam eder, fakat ilk gösterim kampüs üzerinden olmalı.

Kök neden için sınanabilir hipotez: bina müdahaleleri, ortak yatırım bütçesi ve elektrik bağlantı etkileri birlikte değerlendirilmediğinde yatırım öncelikleri eksik bilgiyle seçilebilir. Bu hipotezin kampüs görüşmesiyle doğrulandığı henüz gösterilmedi; “bütün üniversiteler böyle yapıyor” denmemeli.

Task 1 belgesi veya ölçülmüş yıllık tüketim/yoğunluk baseline'ı sunulmadı. Sayısal Task 1 başlangıcı eksiktir; aşağıdaki sentetik referans bunun yerine geçirilmez. %25 hedef olarak kalır; ölçülmüş başarı veya garanti değildir.

## Bugünkü güçlü ve zayıf taraflar

| Climathon beklentisi | Bugünkü kanıt | Eksik / öneri |
| --- | --- | --- |
| Çekirdek işlev | Gerçek fizik hesabı, iki modlu MILP, bütçe ve bağlantı sınırları, önce/sonra, dışa aktarım | Son commit'in üretime çıktığını ve jüri adresinde girişin çalıştığını doğrulayın |
| AI ürün içinde gerçek iş yapar | Kaydedilmiş modelden bina/müdahale bazlı yıllık elektrik/toplam gaz inference'ı ve fizik kıyası | AI'ın kararı hızlandırdığı veya iyileştirdiği gösterilmedi; bunu açık sınırlama olarak söyleyin |
| Baseline'a bağlı somut etki | Aynı binalar/alan/yılda sentetik önce/sonra hesaplanır | Gerçek kampüs tüketimi ve gerçekleşmiş tasarruf yok |
| Alternatiflerden ayrışma | Aynı aday evreninde oran yöntemi, GRID'siz ve GRID'li optimizasyon | GRID her örnekte daha iyi değildir; aşağıdaki örnekte GRID'siz plan da sınırlar içinde |
| Jüri tek başına deneyebilir | Sabit URL, kendi hesabı, sentetik pilot, kısa rehber | Ücretsiz sunucunun uyanması ve kalıcı depolama durumu kritik; kısa gerçek ekran kaydı yedek kanıt olsun |
| Tutarlı final hikâyesi | Kampüs problemiyle çalışan motor örtüşür | İlk kullanıcı ve problem kanıtını yazılı doğrulayın; yeni modüllerle hikâyeyi dağıtmayın |

En önemli eleştirim: ML'nin teknik olarak çalışması, kullanıcıya ek değer sağladığının kanıtı değildir. Bugün fizik sonucu zaten hesaplanır; kendi simülatörünü yaklaşık öğrenmiş model için daha hızlı/daha doğru karar iddiası yapılmamalı. Bunu çözmek için final öncesi ML çıktısını zorla yatırım seçimine sokmayın. Sonraki çalışmada bağımsız veri, referans model ve hata/süre karşılaştırmasıyla hangi işte yararlı olduğuna karar verin.

## Somut, fakat yalnız sentetik demo referansı

Sabit seed'li **Temsilî kampüs**, 4 bina, toplam **12.600 m²**, **2025**, **12.000.000 TL** bütçe, Mod A; motor `4.0.0`. Kullanıcı kaydı okunmadan/değiştirilmeden `create_pilot()[0]` üzerinden hesaplandı. Kayseri hava senaryosu sentetiktir.

| Gösterge | Başlangıç | Seçilen senaryo |
| --- | ---: | ---: |
| Yıllık nihai elektrik + toplam gaz | 3.526.744,3 kWh | 2.029.985,9 kWh |
| Enerji yoğunluğu | 279,90 kWh/m²-yıl | 161,11 kWh/m²-yıl |
| Yıllık elektrik | 1.369.144,3 kWh | 1.741.774,1 kWh |
| Yıllık toplam gaz | 2.157.600,0 kWh | 288.211,8 kWh |
| Eşzamanlı elektrik piki | 529,29 kW | 529,29 kW |

Hesaplanan yatırım **7.645.000 TL**, yıllık nihai enerji azaltımı **1.496.758,3 kWh / %42,44**, ek bakım sonrası yıllık net ekonomik fark **1.012.572,9 TL**. Mevcut senaryo tarifeleri/maliyet varsayımları geçerlidir; resmî güncel fiyat veya teklif değildir. Bina limitleri ve kampüs bağlantısının **1.100 kW** sınırı modellenen profilde aşılmadı. Diğer üç projenin bütçeleri/bağlantıları buna eklenmedi.

Elektrik tüketimi artarken gaz ve toplam nihai enerji azalır. Pik aynı kalır; “elektrik tüketimi/piki düştü” ya da “trafo yatırımı kesin önlendi” sonucu çıkarılamaz. Hesapta azaltım %25'ten büyük çıktı diye hedef veya veriler başarı hikâyesine göre değiştirilmedi. Bu **gerçek kampüste %42,44 tasarruf sağlandı** demek değildir.

Üç yöntem aynı fizik motoru ve aday evreninde:

| Yöntem | Yatırım | Yıllık nihai enerji tasarrufu | Kapasite |
| --- | ---: | ---: | --- |
| Enerji tasarrufu / yatırım oranıyla sıralama | 3.235.000 TL | 1.290.324,9 kWh / %36,59 | Modellenen sınırlar içinde |
| Elektrik kapasitesiz optimizasyon | 7.645.000 TL | 1.496.758,3 kWh / %42,44 | Sonradan fizik denetiminde sınırlar içinde |
| GRID kısıtlı optimizasyon | 7.645.000 TL | 1.496.758,3 kWh / %42,44 | Modellenen sınırlar içinde |

Bu örnekte GRID'siz plan ihlal üretmedi ve GRID ile aynı çıktı. GRID üstünlüğü iddia etmeyin; sağlanan değer açık kapasite kontrolü ve karşılaştırmadır. Oran yöntemi daha düşük yatırımla daha az tasarruf sağladı; bütün ölçütlerde tek kazanan yok. Ham hesap kanıtı yerelde `artifacts/repository-cleanup/campus-review-evidence.json` içindedir, kullanıcı verisi değildir.

## PDR'da karşılaştırılacak en yakın alternatifler

| Alternatif | Yapılabilecek dürüst karşılaştırma |
| --- | --- |
| Mevcut manuel/Excel önceliklendirme | Bir enerji yöneticisinden gerçekten kullandığı yöntemi isteyin; varsayım olarak oran yöntemiyle kontrollü kıyas sunulabilir |
| RETScreen Expert | Resmî tanıtım benchmark, fizibilite, performans ve portföy analizi içerdiğini belirtir; “alternatiflerde portföy yok” denemez. Aynı veriyle karşılaştırmalı test yapılmadı. [NRCan](https://natural-resources.canada.ca/science-data/science-research/research-centres/retscreen-innovation-lab) |
| EnergyPlus | Bina enerji tüketimini modelleyen ayrıntılı simülasyon motorudur; mevcut statik paylaştırmayı onunla eşdeğer sunmayın. Portföy karar katmanı ayrı bir işlevdir. [DOE](https://www.energy.gov/cmei/buildings/articles/energyplus), [EnergyPlus](https://energyplus.net/) |

Savunulabilir ayrışma önerisi: “Kampüsün aynı bütçe ve bağlantı grupları altında hangi müdahalelerin birlikte seçilebildiğini açıklanabilir, sınırları görünür bir prototipte karşılaştırıyorum.” Bu bir ürün konumlandırmasıdır; dünyada ilk veya rakiplerden ölçülmüş üstünlük iddiası değildir.

## Öncelik önerilerim

1. **Tek doğru jüri adresi ve kalıcılık.** Dağıtıma özel URL yerine `https://buildingportfolio25.vercel.app` paylaşın. Son main commit'i Vercel'de üretime alın. Kalıcı disk/veritabanı gerçekten bağlı mı kontrol edin. Free servis dosyaları yeniden başlatma/yayın/uyku sonrasında kaybedebilir; [Render](https://render.com/docs/free). Bu görev ücretli kaynak satın almadı veya platform ayarı değiştirmedi.
2. **İki dakikalık gerçek kampüs demosu.** 0–20 sn problem/kullanıcı; 20–70 sn kampüsü ve bütçeyi açıp gerçekten hesapla; 70–95 sn önce/sonra ile kapasite ve baseline; 95–110 sn ML/fizik kıyası ve hata; 110–120 sn sentetik sınır ve gerçek pilot adımı. Sadece ekran görüntülerinden video yapmayın. LLM ve ComStock ayrıntılarını ana demoya yığmayın.
3. **Bir gerçek kampüs ekibiyle problem doğrulaması.** Mevcut karar süreci, kimlerin onayladığı, veri erişimi ve ödemeye istek belirsiz. Üç kısa görüşme planı önerilir; yapılmış gibi yazılmamalı. Sonraki adım için tek kampüste az sayıda binanın yıllık fatura, alan, ısıtma ayrımı ve bağlantı belgesi yeterli başlangıç olur. Kişisel/kurumsal bilgiyi depoya koymayın.
4. **ML'nin faydasını bağımsız sınayın.** Gerçek veya bağımsız harici simülasyon verisinde yıllık elektrik/gaz hatasını ve inference süresini basit referansla karşılaştırın. Eğitim bina gruplarını ayırmayı sürdürün. Yarar yoksa ML'nin deneysel sınırını koruyun; optimizasyonu “eğitilmiş AI” diye tanıtmayın. Şimdilik yeni eğitim yapılmadı.
5. **Etkiyi doğrulayacak pilot tasarımı.** Aynı alan/yıl, sayaç kapsamı ve hizmet düzeyini sabitleyin. Sonraki gerçek pilotta hava/kullanım değişimini ve net bakım maliyetini kaydedin. Gerçekleşmiş tasarruf için uygulama sonrası ölçüm gerekir. SCOP ve yatırım duyarlılıkları olasılık/güven aralığı değildir.

Bu aşamada yeni kullanıcı rolleri, ödeme, IoT, 3D, otomatik klima yerleşimi ve daha fazla proje türü önermiyorum. Kat/zon, duyarlılık ve karşılaştırma çalışan ayrıntı olarak kalsın; çekirdek demo yatırım kararıdır. Yeni özellik, sahaya ilişkin kanıt eksikliğini çözmez.

## Dört kriter için gerçekçi öz değerlendirme önerisi

Aşağıdaki puanlar tartışma taslağıdır; objektif ölçüm veya jüri sonucu değildir.

| Kriter | Öneri | Gerekçe / sınır |
| --- | ---: | --- |
| Greener | 3/5 | Enerji/emisyon azaltım potansiyeli modelleniyor; gerçekleşmiş saha etkisi yok. Enerji ve emisyon ayrı değerlendirilmelidir |
| Circular | 1/5 | Atık akışı, ekipman yeniden kullanımı ve gömülü karbon hesabı henüz yok; yalnız yalıtım önermek döngüsellik kanıtı değildir |
| Financeable | 2/5 | Model yatırım/net maliyet farkı sunuyor; müşteri ödemeye isteği, gerçek teklifler ve finansman modeli doğrulanmadı |
| Socially Impactful | 2/5 | Kurum kaynaklarının verimli kullanımı olası dolaylı fayda; konfor, eşit erişim veya ölçülmüş sosyal etki gösterilmedi |

SDG eşleşmesi için ana öneri enerji verimliliği hedefi **7.3**, ikincil ilişki **13** iklim eylemidir. Uygulamanın kWh/m²-yıl metriği, resmî ulusal **7.3.1** birincil enerji/GSYİH göstergesiyle aynı değildir. [BM Goal 7](https://sdgs.un.org/goals/goal7), [BM Goal 13](https://sdgs.un.org/goals/goal13). Siemens için enerji verimliliği/elektrifikasyon alanıyla ilişki bir öneridir; resmî ortaklık veya onay yoktur. Task 1'deki COP31/Siemens eşleştirme metni verilmediğinden kesin eşleşme teyit edilmedi.

## Form ve final paketi

Görev 2 PDR: problem/kullanıcı, neden mevcut yöntem yetmiyor, çözüm akışı, dürüst benchmark, prototip sınırı, sentetik etki ve bilinmeyenler tek sayfaya sığmalı. Görev 3: çalışan link, özel fizik/MILP gerekçesiyle React/FastAPI stack'i, gerçek inference ve açık mock/veri ayrımı. Google AI Studio/Gemini kullanılmadı; kullanılan Codex ve scikit-learn doğru yazılmalı.

Görev 4 için eksikler: özgün Task 1 belgesinin final hâli, tek sayfalık final PDR PDF, iki dakikalık gerçek çalışan demo videosu ve bu videonun paylaşılabilir bağlantısı. Bunların teslim edildiği iddia edilmez. Bu görev yalnız değerlendirme/temizlik ve girişte doğru adres yönlendirmesi yaptı; video, gerçek saha ölçümü veya uygulanmış yatırım üretmedi.

## 21 Ekim — önerilerin uygulamaya aktarılması

Takip geliştirmesinin hedefi, teknik kapsamı büyütmeden kararın anlaşılmasını ve hesap kanıtının paylaşılmasını kolaylaştırmaktır.

| Alan | Kaynakta görülen durum | Uygulanan değişiklik |
| --- | --- | --- |
| Ürün hikâyesi | Kampüs problemi detaylar arasında kaybolabiliyor | Giriş yardımında hedef kullanıcı/soru net; PDR taslağı kampüse odaklı |
| Üst çubuk | Tema hesap menüsündeydi | Etiketli tema seçimi proje/bina seçicilerinin yanında; dar ekranda hesap menüsü kısa etiketle yer kazanır |
| Veri hazırlığı | “Örnek yüklendi” teknik bir durum mesajıydı | API profil tutarlılığı, başlangıç bağlantı ihlalleri ve uygun sistem varsayımı eksikleri gösterilir. Gerçek pilot veri listesi açılabilir; saha doğrulaması iddia edilmez |
| Bina | Kat/paket/ML bölümleri için uzun kaydırma | Bölüm bağlantıları; dışarıda bırakılan müdahale seçilmiş gibi adlandırılmaz; eski kat seçimleri paket başlığında korunur |
| Sonuç | Uzun bina/paket cümlesi kararı okumayı zorlaştırıyor | Kısa karar, aynı alan/yıl kapsamı, KPI ve teknik kanıt sırası; negatif enerji farkı artış olarak yazılır; elektrik artışı/toplam enerji azaltımı ayrılır |
| AI | ComStock ilk görünümde Kayseri için tahmin vermeyebilir | Seçili binanın sentetik ML/fizik karşılaştırması önde; ABD kapsamlı model ayrı açılır ayrıntı, açılmadan sorgulanmaz. Inference korunur; yeni eğitim/LLM çağrısı yok |
| Paylaşım | CSV/JSON yönetim/jüri için uzun | Güncel hesaptan yazdırılabilir HTML karar özeti: yatırım, enerji, bağlantılar, karşılaştırma, kaynaklar ve hesap kimliği. Tarayıcıdan PDF kaydedilebilir; dosya hesabın anlık kopyasıdır |
| Backend | Ana API `read_result` ile bağlamı korur; export yardımcısı yalnız revizyon/ID denetler | Export yardımcısı da proje, girdi özeti ve motoru denetler. HTML yalnız `scope=result`, revizyon ve hesap ID ile indirilir. Kullanıcı metni HTML olarak çalıştırılmaz |

Fizik denklemleri, aday evreni ve optimizasyon hedefi değiştirilmedi. %25 hedef/veriler başarı iddiasına göre ayarlanmadı. Aynı sentetik kampüs hesabı tekrar yürütülünce yukarıdaki sayılar korundu.

### Sonraki geliştirmeler — her açıdan öncelik sırası

| Öncelik / açı | Öneri ve gerekçe | Kabul kanıtı |
| --- | --- | --- |
| 1 · Operasyon | Kalıcı Render diski ve özel yedekten geri dönüş. JSON/SQLite tek process prototip için uygundur; yeniden başlatmada kayıp teslimi zedeler | Ayrı test verisi deploy sonrası korunur. Panel erişimi olmadan gerçek disk bağlantısı doğrulanmaz |
| 1 · Fikir | Kampüsün karar süreci, kimin neyi onayladığı ve mevcut Excel/etüt yaklaşımıyla görüşme | Görüşme notu ve izinli fatura/alan/bağlantı örneği; yapılmış gibi sunulmaz |
| 1 · Sunum | İki dakikalık gerçek kayıt: kampüs → bütçe → hesap → etki → ML farkı → karar özeti | İzleyici aynı akışı deneyebilir; yalnız ekran görüntüsü dizisi video sayılmaz |
| 2 · Fizik / mantık | Gerçek tarifeler, tasarım sıcaklığında COP/pompa kapasitesi, kazan kapasitesi ve hizmet koşulları | Aynı dönem/alan için ölçümle enerji dengesi ve pik saat denetimi. Mevsimsel SCOP saatlik saha performansı değildir |
| 2 · AI | Bağımsız veride referansa göre hata/süre ve kullanıcı faydası | Ayrılmış bina grupları, bilinen kapsam ve görünür hata. Fayda kanıtı olmadan ML plan seçimine bağlanmaz |
| 2 · Arayüz | Bir teknik işler kullanıcısıyla görev testi: bütçeyi değiştir, limiti bul, yatırımları karşılaştır, belge indir | Tamamlama süresi ve takıldığı yerler; Chrome otomasyonu kullanıcı araştırması değildir |
| 3 · Backend ölçeği | PostgreSQL kalıcı saklama uygulanmıştır. Artan talepte hesap kuyruğu ve iptal yönetimi; mevcut global kilidin meşgulken 409 davranışının ölçülmesi | İzolasyon, iptal/süre sınırı ve kayıt dönüşümü; talep yokken büyük yeniden yazım yapılmaz |
| 3 · Hesap desteği | Gerçek müşteriden önce e-posta doğrulama, parola sıfırlama ve veri saklama/silme politikası | Yetkisiz erişim ve kurtarma testleri; bugünkü demo desteklediğini iddia etmez |

Görsel kontrollerde [W3C reflow](https://www.w3.org/WAI/WCAG22/Understanding/reflow.html) ve [etkileşim hedefi](https://www.w3.org/WAI/WCAG22/Understanding/target-size-minimum) rehberleri referans alındı. Tam WCAG uygunluğu iddia edilmez.

### Son yönlendirme: elektrifikasyon odağı ve uygulama ayarları

Kullanıcının son yönlendirmesiyle ana fikir “bina ısıtmasının elektrifikasyon etkisini yatırım öncesinde öngörmek” olarak netleştirildi; kampüs ilk uygulama alanı kalır. Bu bir canlı kontrol modülü değildir. Binaların/inşaatın toplam karbonu ile yalnız ısıtma emisyonu birbirine eşitlenmez. Isı pompası her koşulda karbon azaltıyor denmez. [Fiziksel gerekçe, kaynaklar ve yarışma anlatımı](electrification-positioning.md).

Proje/bina seçimi içerikteki çalışma alanındadır. Proje/pilot yönetimi sayfanın altındadır. Ayarlar, görünüm/dil, hareket tercihi, senaryo ayarlarına geçiş ve kaynak erişimi sağlar. Tema ve dil girişte de oturum içinde de yalnız Ayarlar penceresinden seçilir; formun/karar alanının önüne geçmez.

TR/EN ana arayüz sözlüğü yerel kod içindedir. Dil değişimi sayı/tarih gösterimini değiştirir, para birimini veya hesap girdisini dönüştürmez. Kullanıcı proje/bina adları, kaynak metinleri, backend'in özgün anlatımları ve bazı ileri teknik ayrıntılar Türkçe kalabilir; tam belge/API çevirisi iddia edilmez. HTML karar özeti Türkçedir. Bu sınır Ayarlar'da açıkça yazılıdır. Çeviri DOM metni değiştirmez, ağ/LLM çağrısı yapmaz; kanonik API enum değerleri ve taslak anahtarları çevrilmez.

Sonuçtaki elektrifikasyon kartı yalnız API sonucu kullanır: yıllık elektrik/gaz değişimi, varsayımsal karbon farkı, ısı pompası faydalı ısısı ve kalan kazan ısısı. Faydalı ısı nihai enerjiye ikinci kez eklenmez. Enerji/yatırım optimumu karbon optimumu diye etiketlenmez. İndirilebilir karar özeti, mevcut CSV/JSON ve eski sonuç koruması devam eder.

### Yürütülen yerel kabul — 21 Ekim 2026

- Backend `python -m unittest discover -s backend`: **76 test geçti**. Yeni HTML özetin gerçek değer/kayıt tutarlılığı, kimlik/sürüm/özet koruması, XSS kaçışı, oturum gereksinimi ve çözümsüz sonuç testleri dahil. LLM otomatik testleri harici sağlayıcıyı taklit eder; eğitim yapılmaz.
- Frontend `npm.cmd test`: **21 test geçti**. Dil/hareket tercihi, sayı formatı, özel adların korunması ve müdahale başlıkları dahil. TypeScript/Vite üretim derlemesi geçti.
- Gerçek yerel Chrome'da **320, 390, 500, 768, 1280, 1536 px**: giriş, proje özeti, bina/katlar, senaryo, sonuç ve model ekranlarında sayfa taşması kontrolü. Geniş tablolar/grafik kendi alanında kayar. İlk anlamlı veri konumu kontrolü gevşetilmeden gereksiz üst boşluklar azaltıldı. Üç tema ve yenilemede korunması çalıştı.
- Ayarlar/TR/EN: açık senaryo taslağı dil değişiminde korunur; dil/hareket tercihi yenilemede kalır; proje/girdi/hesap bağlamı aynıdır. İngilizce bina formu `Education` gösterirken API enum değeri `Eğitim` kalır. Kat sayısal taslağının anahtarları da çevrilmez.
- Elektrifikasyon kartının üç farkı API değerleriyle bire bir karşılaştırıldı. HTML karar özeti gerçekten indirildi, tarayıcıda açıldı ve hesap kimliğiyle eşleşti. Girdi değişince indirme görünmez; eski bağlam GET isteği 409, yeniden hesap sonrasında güncel sonuç.
- ML gerçek inference ve paket değişimine bağlı değişen çıktı, büyük fark uyarısı; imkânsız hedef, kaydedilmemiş taslakta Kal, tekrar giriş ve tanıtım tekrarlamama geçti. Paket yüklemesinde ML düğmesinin erken etkinleşmesi düzeltildi; geçerli aday listesi hazır olmadan çalışmaz.
- Tarayıcıda yakalanmamış hata yok; özgün JSON SHA-256 özetleri aynı. Geçici yerel hesap dışında kullanıcı kaydı düzenlenmedi; QA hesapları temizlendi. Ortam dosyası, model artefaktları ve kayıt şeması değişmedi. Özel kanıtlar `artifacts/task3-ui/` altında Git dışındadır. Türkçe/İngilizce masaüstü, mobil, Ayarlar ve elektrikleşme görüntüleri ayrıca açılıp görsel olarak incelendi.
- PDR taslağı tek sayfalık PDF'ye çevrildi ve sayfa sayısı kontrol edildi; içerik `docs/pdr-draft.md`, yerel paylaşılabilir PDF `artifacts/presentation/portfolio25-pdr-taslak.pdf`. Özgün Task 1 belgesinin veya bir saha ölçümünün yerine geçmez.

Yerel geliştirme sunucusu eski CSS sunarken kimliği/portu doğrulanarak yeniden başlatıldı. Uzun QA turunda yerel backend sağlık isteği zaman aşımına uğradı; kayıt silinmeden aynı portta kontrollü yeniden başlatıldı ve son tur tamamlandı. Kalıcı altyapı/üretim yük testi yapıldığı iddia edilmez. TestClient için Starlette/httpx deprecation uyarısı var; test hatası değildir, bağımlılık yükseltme bu kapsama alınmadı. Canlı yayın kontrolü yerel kabulden ayrı raporlanır.

### Arayüz incelemesi ve sonraki adımlar — 22 Ekim 2026

Girişteki ayrı tema/dil kontrolleri Ayarlar'a toplandı. Proje adı ve marka tekrarları azaltıldı; başlık, bağlam seçimi, veri ve eylem sırası netleştirildi. Mobil menü altta durur. Bina kat/kullanım, yatırım ve ML görünümleri gerçek sekmelerdir; açık taslaklar sekme değişiminde korunur. Envanter haritadan önce, seçilen yatırımlar ayrıntılı teknik kanıttan önce gelir. Kritik hata, eskimiş sonuç ve kapasite uyarıları gizlenmez.

Bu düzenleme yeni bir fizik/AI yeteneği değildir. Motor, veri modeli, oturum güvenliği ve PostgreSQL saklama yolu değiştirilmedi. Eski tek teslim raporları ve bunları yazan betikler Git dışı yerel arşive taşındı; temel belgeler, testler ve çalışan model artefaktları korundu.

Önerilen öncelikler:

1. **Bir kampüste problemi doğrulayın.** Teknik işler ekibiyle son yatırım kararının nasıl alındığını inceleyin. Aynı yılın faturaları, alanı, ısıtma/sıcak su ayrımı ve fiziksel bağlantı grupları olmadan sentetik azaltımı kurum başarısı diye sunmayın. %25 hedef olarak kalır.
2. **Elektrifikasyonu üç ayrı göstergeyle değerlendirin.** Nihai enerji, işletme maliyeti ve kaynak/tarihli emisyon farklı sonuçlardır. Enerji optimumu karbon/maliyet optimumu sayılmaz. Sonraki hedef seçimi genişlemesi bu ayrımı korumalı, bütçe/kapasiteyle küçük örnekte doğrulanmalıdır.
3. **Teklif ve saha performansını duyarlılığa bağlayın.** SCOP, soğuk saatlerde kapasite ve kazan sınırları için uzman verisi, yatırım için teklif aralığı gerekir. Bugünkü mevsimsel yaklaşım saatlik COP veya konfor güvencesi değildir. Ekipman ömrü ve iskonto sonraki ekonomik değerlendirmede ele alınabilir; basit geri ödeme bunları içermez.
4. **AI'ın ek faydasını ölçün.** Mevcut ML yıllık tüketim kıyasıdır. Bağımsız veride hata, kapsam dışı oranı, süre ve kullanıcıya katkı ölçülmeden plan seçimine bağlanmamalı. LLM hesaplanmış sayıları açıklayabilir; motorun yerine geçmez. Bu çalışmada eğitim veya ücretli LLM çağrısı yoktur.
5. **Jüri demosunu tek kararda tutun.** Kampüs → bir binanın seçenekleri → bütçe/bağlantı sınırı → yatırım planı → önce/sonra ve karar özeti. Diğer proje türleri destek kanıtıdır. İki dakikalık gerçek ekran kaydı hazırlayın; ana akışı yeni modüllerle büyütmeyin.

Bunlar uygulanmış özellik veya saha başarısı değildir. Sonraki kabul ölçütü daha fazla ekran değil, teknik işler kullanıcısının yardımsız doğru yatırım çıktısını alabilmesi ve verinin sınırını anlayabilmesidir.

Son düzenlemede gerçekten çalıştırılan yerel kontroller: frontend 22 test ve TypeScript/Vite üretim derlemesi; backend oturum/CSRF/sahiplik için 3 regresyon; gerçek Chrome'da 320/390/500/768/1280/1536 px ana ekranlar, üç tema, TR/EN, kat taslağında sekme ve navigasyon koruması, iki kampüs binası/iki konut bloğu/tek ofis, gerçek optimizasyon, eski hesap reddi ve yeniden hesaplama, HTML indirme, gerçek ML/fizik kıyası, imkânsız hedef, çıkış/giriş. Metin/HTML 502/503 ve Origin 403 kurtarma denemesi ayrıca geçti. Yatay sayfa taşması ve yakalanmamış JavaScript hatası görülmedi; seçili görüntüler ayrıca görsel olarak incelendi. Backend'in özgün kullanıcı verisi yerine `artifacts/ui-review/qa-data` içinde ayrı yerel test deposu kullanıldı. Kanıtlar Git dışındaki `artifacts/ui-review/acceptance/` altındadır. Bu kontroller tam WCAG veya saha doğruluğu belgesi değildir; önceki PostgreSQL yeniden deploy kontrolü ayrı canlı raporda korunur.


### Çalışma alanı menüsü (22 Ekim)
Hesap, Ayarlar ve Yardım masaüstünde sol menünün altında ayrı girişlerdir. Mobilde üstteki Menü aynı araçları açar; alt navigasyon karar akışına ayrılmıştır. Hesap oturum işlemlerini, Ayarlar görünüm/dil tercihlerini, Yardım demo rehberi ve kaynak açıklamalarını içerir. Masaüstündeki tekrarlı üst başlık kaldırıldı. Veri yenileme yardım içinden taslak korumasıyla çalışır.

Önerilen ürün sırası: (1) gerçek kampüs girdilerinin tamamlanma durumunu görünür tutmak; (2) yatırım kararında enerji, net maliyet ve bağlantı uygunluğunu ayrı değerlendirmek; (3) saha pilotunda fatura ve eşzamanlı yük ölçümüyle varsayımları doğrulamak. Karbon azaltımı için tarihli elektrik/yakıt faktörleri ve aynı kapsam şarttır; elektrikleşme tek başına emisyon azalması garantisi değildir. Fazlara bölünmüş yatırım ve fiyat belirsizliği sonraki karar ihtiyaçlarıdır; henüz hesaplanmış özellik gibi sunulmaz.

Doğrulama: 22 frontend testi ve üretim derlemesi geçti. Geçici yerel QA hesabıyla Chrome kabul akışı tamamlandı: 320/390/500/768/1280/1536 px, tema/dil, bina/proje geçişi, taslak koruması, optimizasyon, gerçek ML karşılaştırması, eski sonuç/dışa aktarım, çıkış ve tekrar giriş. Ekran görüntüleri görsel olarak incelendi; özgün yerel kayıt özetleri değişmedi. Ücretli AI çağrısı yapılmadı.


### Eylem ve AI odaklı çalışma alanı
Proje özeti önce plan oluştur/aç eylemini gösterir. Binalar seçilebilir yatırım kartlarıdır; geniş veri tablosu ve başlangıç metrikleri isteğe bağlı açılır. Sayfa eylemlerindeki AI asistanı, bina seçenekleri veya güncel plan açıklamasını açar. Hesap sonrası “AI ile alternatif dene” mevcut yapılandırılmış senaryo taslağı endpoint'ini kullanır: öneriyi incele → kaydetmeden hesapla → açıkça uygula. Yeni hesap motoru veya model eklenmedi. Soru değişince önceki AI senaryo taslağı kullanılamaz.

390/1440 px gerçek Chrome kontrolünde karttan bina yatırımlarına geçiş, AI görev pencereleri ve taslak → gerçek geçici hesap akışı doğrulandı. Ücretli LLM çağrısı yapılmadı; yalnız taslak sağlayıcı yanıtı testte taklit edildi, alternatif fizik hesabı gerçek backend üzerinde çalıştı ve ana snapshot aynı kaldı. AI bağlantısı erişilemezse sahte yanıt üretilmez.
