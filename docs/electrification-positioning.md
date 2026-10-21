# Portfolio25-GRID — elektrifikasyon kararının uygulanabilirliği

## Ana fikir

**“Binaların ısıtmasını elektrikleştirmeden önce; hangi bina, hangi müdahale, hangi bütçe ve hangi elektrik bağlantısı?”**

Ürün, enerji yöneticisinin gaz kazanından ısı pompasına geçiş ve yalıtım kararlarını aynı fiziksel modelle karşılaştırmasına yardım eder. İlk müşteri odağı kampüs teknik işler/enerji/tesis ekibi, karar sahibi kurum yönetimidir. Tek bina, konut ve otel desteklenen örnek kapsamdır. Bütün ekonominin elektrifikasyonunu veya canlı şebekeyi yönettiğimiz iddia edilmez.

“Kontrol” bugün **yatırım öncesi sınır ve senaryo kontrolü** anlamındadır. Sayaç bağlantısı, otomatik cihaz kontrolü, canlı durum veya gerçekleşmiş tüketim tahmini yoktur. Saatlik yükler sentetik, mevsimsel performans eşdeğerdir. ML yalnız yıllık tüketim karşılaştırması sunar.

## Problem gerekçesi ve kaynak kapsamı

IEA, binalardaki ısıtma elektrifikasyonunda ısı pompalarının rolünü vurgular; bu dönüşüm elektrik talebini de etkiler. Bu genel eğilim, kampüs bağlantılarının incelenmesi için gerekçedir; belirli bir kampüste ölçülmüş sorun kanıtı değildir. [IEA, Electrification, 22 Eylül 2026](https://www.iea.org/reports/electrification).

Isıtma/sıcak su ihtiyacı bina enerji kullanımında önemli olabilir. IEA 2025'te **gelişmiş ekonomilerde konutlar** için bu iki kullanımın yaklaşık %70 payını verir. Bu sayı Türkiye'deki kampüs, laboratuvar, otel veya tüm binalar için genellenmez. Isıtma, aydınlatma, cihaz, soğutma ve sıcak su ayrı tutulmalıdır. [IEA, Energy Efficiency 2025 — Buildings](https://www.iea.org/reports/energy-efficiency-2025/buildings).

UNEP'in 2025–2026 raporu **bina ve inşaat sektörünü**, malzeme etkileri dahil geniş bir kapsamda ele alır; yaklaşık %37 küresel CO₂ payını “yalnız ısınma emisyonu” diye sunmak yanlış olur. Portfolio25'in bugünkü emisyon hesabı elektrik/gaz işletme tüketimi ve kullanıcı faktörleriyle sınırlıdır; gömülü karbon veya bütün yaşam döngüsü hesabı değildir. [UNEP, 2026 ana bulguları](https://wedocs.unep.org/items/8fbf878c-7136-4864-8d88-ee929f591c76).

## Neden yalnız “daha fazla elektrik” değil?

Bir ısı pompasına verilen elektrik ile ürettiği faydalı ısı aynı enerji hesabına iki kez eklenmez. Aynı faydalı ısıyı daha az nihai enerjiyle sağlamak mümkündür. Ancak yıllık elektrik artabilir, kış yükü büyüyebilir ve karbon sonucu elektrik üretiminin emisyon faktörüne bağlıdır. Fiziksel kapasite uygunluğu bütün zaman damgalarında bina ve gerçek bağlantı grubu için ayrı kontrol edilir.

Yalıtım olmadan aynı faydalı ısı Q'nun yalnız kazan/pompa alternatifini kıyaslayan basit eşik:

`pompa emisyonu = Q / SCOP × elektrik_faktörü`

`kazan emisyonu = Q / kazan_verimi × gaz_faktörü`

Bu dar karşılaştırmada pompanın işletme emisyonu daha düşük olması için `elektrik_faktörü / SCOP < gaz_faktörü / kazan_verimi` gerekir. Yardımcı yük, farklı bakım, yalıtım, kapsama ve saatlik sıcaklık etkileri bu eşikte yoktur; tam proje sonucu motorla yeniden hesaplanır. Bu bir emisyon faktörü tavsiyesi veya her koşulda düşük karbon garantisi değildir.

## Bugün gösterilebilen kanıt

Mevcut dört binalı sentetik kampüste aynı 2025 ve 12.600 m² için Mod A sonucu:

| Gösterge | Başlangıç | Plan |
| --- | ---: | ---: |
| Elektrik | 1.369.144,3 | 1.741.774,1 kWh/yıl |
| Toplam gaz | 2.157.600,0 | 288.211,8 kWh/yıl |
| Toplam nihai enerji | 3.526.744,3 | 2.029.985,9 kWh/yıl |
| Yoğunluk | 279,90 | 161,11 kWh/m²-yıl |
| Modellenen işletme emisyonu | 979,18 | 754,35 t CO₂e/yıl |

Elektrik yaklaşık **372.629,9 kWh/yıl artıyor**, gaz **1.869.388,2 kWh/yıl azalıyor**; varsayımsal faktörlerle karbon farkı **−224,83 t CO₂e/yıl**. Yatırım **7.645.000 TL**, yıllık net ekonomik tasarruf **1.012.572,9 TL**. Modellenen sınırlarda ihlal yok. GRID'siz plan da aynı çıktı; veriler üstünlük göstermek için değiştirilmedi.

Bu değerler saha başarısı değildir. Motor enerji/yatırımı optimize eder; **en düşük karbon** planını bulduğunu iddia etmez. %25 azaltım hedeftir. Gerçek Task 1 baseline'ı eksiktir. Ürün elektrik/gaz/karbon kartını ve bağlantı kontrolünü yan yana gösterir; son karar teknik inceleme gerektirir.

## Yarışmada savunulabilir fark ve sonraki iş

1. **Farklı karar boyutlarını birleştirme:** Sadece ekipman önerisi yerine bütçe, enerji, yıllık ekonomik etki ve gerçek bağlantı gruplarını aynı aday evreninde karşılaştırmak. RETScreen gibi alternatiflerde portföy analizi vardır; ilk/benzersiz olduğumuz söylenmez.
2. **Hizmet gereksinimi:** Laboratuvar havalandırması, konut/otel sürekliliği ve sıcak su korunur. Konfor dinamiği yoksa “konfor korundu” denmez. Sonraki fizik doğrulamasında tasarım günü COP, dağıtım sıcaklığı ve kazan kapasitesi öncelikli.
3. **Gerçek veriyle dar pilot:** Bir kampüs, az sayıda bina; aynı alan/yıl faturası, ısıtma ayrımı, alan, bağlantı belgesi ve eşzamanlı yük. Önce mevcut durum uzlaştırılır, sonra yatırım senaryosu değerlendirilir. Kurulum sonrası ölçüm olmadan gerçekleşmiş tasarruf iddia edilmez.
4. **AI değerini ölçme:** Modelden gerçek inference mevcut, ancak kendi simülatörünü öğrenmek saha doğruluğunu kanıtlamaz. Bağımsız veri ve referansla hata/süre, ardından teknik işler kullanıcısının karar görevindeki fayda ölçülmeli. AI görüntüsü için fizik veya kapasiteyi ML ile sessizce değiştirmek uygun değil.
5. **Karbon amaçlı planlama sonraki seçenek:** Kullanıcı karbonu önceliklendirirse ayrı, açık amaç/kısıt gerekir. Güncel iki mod korunur; yıllık enerji optimumu karbon optimumu diye etiketlenmez. Saatlik faktör ve eklenen elektrik talebinin etkisi için veri/kapsam ayrıca tanımlanmalı.
6. **Uygulanabilir işletim:** Kalıcı disk/veritabanı, özel yedek, gerçek teklif, teknik kullanıcı görüşmesi ve iki dakikalık çalışan kayıt; daha fazla proje türü veya 3D eklemekten önce gelmeli.

## İki dakikalık anlatım

- 0–20 sn: “Isıtmayı elektrikleştiriyoruz; hangi binadan başlayacağımızı bütçe ve bağlantı kapasitesiyle birlikte seçmeliyiz.” Hedef kullanıcı/karar sahibi.
- 20–65 sn: Kampüsü seç, varsayımsal bütçeyi göster, gerçekten hesapla; hangi müdahalelerin seçildiğini aç.
- 65–90 sn: Elektrik artışı, gaz/karbon farkı, enerji yoğunluğu ve bağlantı kontrolü. Aynı yıl/alan ve sentetik sınır.
- 90–110 sn: Bir bina/müdahalede gerçek ML/fizik karşılaştırması; hata ve deneysel kapsamı göster.
- 110–120 sn: Karar özetini indir. Sonraki kanıt: gerçek kampüs verisi ve uygulama sonrası ölçüm. AI/ML başarısı veya saha tasarrufu garantisi verme.
