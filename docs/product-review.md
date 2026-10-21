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
