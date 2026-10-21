# Elle doğrulanan küçük örnek

Bu bir mühendislik referansı değildir. Kolay kontrol için dört aktif saatlik sentetik test ufku kullanılır; üretim profili ayrıca tam 8.760/8.784 saat üzerinden sınanır. Kod: `backend/test_engine.py`, `test_hand_calculation_and_capacity_backup`.

## Girdiler

100 m² bina; elektrik 400 kWh (her saatte 100 kW); ısıtma doğalgazı 1.000 kWh; diğer doğalgaz 100 kWh. Kazan verimi 0,8 → faydalı ısı 800 kWh (her saatte 200 kW).

Yalıtımla ilgili ısı payı 0,5; ilgili payda azaltım 0,4. Pompa kapsamı 0,75; termal kapasite 100 kW; SCOP 4. Elektrik 2 TL/kWh, gaz 1 TL/kWh. Yalıtım 10 TL/m², pompa 20 TL/kW + 100 TL sabit, bakım yatırımın %1’i/yıl.

**Bu parametreler elle kontrole özel olup uygulamanın başlangıç varsayımları değildir.** Başlangıç uygulama değerleri kazan verimi 0,90; yalıtımla ilgili pay 0,90; azaltım 0,30; pompa kapsamı 0,90; SCOP 3,20; elektrik 4,50 TL/kWh ve gaz 1,50 TL/kWh’tır. Örneğin 100 kW pompası, yatırım ve bakım bedelleri de özel test girdileridir. Dört saatlik test ufku tam yıl üretim profili olarak sunulmaz.

| Enerji bileşeni | Önce (kWh) | Sonra (kWh) |
| --- | ---: | ---: |
| Elektrik | 400 | 500 = 400 mevcut + 100 pompa |
| Isıtma doğalgazı | 1.000 | 300 |
| Isıtma dışı doğalgaz | 100 | 100 |
| Toplam doğalgaz | 1.100 | 400 |
| Toplam nihai enerji | 1.500 | 900 |

Isı pompası 400 kWh faydalı ısıyı 100 kWh elektrikle sağlar. Kalan 240 kWh faydalı ısı kazan tarafından 300 kWh gaz tüketilerek sağlanır. Kullanılan iki tarife bütün önce/sonra hesabında sabittir: elektrik 2 TL/kWh, tüm gaz 1 TL/kWh. Dolayısıyla sonraki **enerji bedeli 1.400 TL**, ek bakım 31 TL, toplam işletme bedeli 1.431 TL’dir. Yıllık etiketli çıktı alanları bu küçük testte dört saatlik doğrulama ufkunun toplamını taşır; gerçek yıllık sonuç testi 8.760/8.784 saattir.

## Birleşik paket hesabı

| Adım | Elle beklenen değer |
| --- | --- |
| Başlangıç faydalı ısı | 1.000 × 0,8 = 800 kWh |
| Yalıtımla azaltılan ilgili ısı | 800 × 0,5 × 0,4 = 160 kWh |
| Kalan faydalı ısı | 640 kWh = her saatte 160 kW |
| Pompanın kapsayabileceği ısı | 640 × 0,75 = 480 kWh |
| Kapasiteyle gerçekten sağlanan pompa ısısı | min(120, 100) kW × 4 saat = 400 kWh |
| Kazanda karşılanan ısı | 640 − 400 = 240 kWh |
| Pompa elektriği | 400 / 4 = 100 kWh |
| Kalan ısıtma doğalgazı | 240 / 0,8 = 300 kWh |
| Korunan diğer doğalgaz | 100 kWh |
| Yeni elektrik | 400 + 100 = 500 kWh |
| Nihai enerji önce / sonra | 1.500 / 900 kWh |
| Enerji tasarrufu | 600 kWh (%40) |
| Elektrik piki önce / sonra | 100 / 125 kW |
| Yatırım | 100×10 + 100×20 + 100 = 3.100 TL |
| Ek yıllık bakım | 31 TL |
| Önce maliyet | 400×2 + (1.000+100)×1 = 1.900 TL |
| Sonra maliyet | 500×2 + (300+100)×1 + 31 = 1.431 TL |
| Net ekonomik tasarruf | 469 TL/yıl |
| Basit geri ödeme | 3.100 / 469 ≈ 6,61 yıl |

Motor bu değerlerle eşleşir. Pompa kapasitesini aşan 80 kWh kapsanabilir ısı da diğer kapsanmayan 160 kWh ile birlikte kazana gider; ısı yok edilmez.

İkinci kontrolde kapasite 200 kW yapılır: yalıtım tek başına 200 kWh, pompa tek başına 600 kWh, birleşik paket 680 kWh tasarruf sağlar. **200 + 600 = 800 kWh** birleşik sonuç değildir.

Elektrik fiyatı 10 TL/kWh yapılırsa ilk örneğin net tasarrufu **−331 TL/yıl** olur; motor bu değeri korur ve geri ödeme null döner.

İki bina için tüm 16 kombinasyon bağımsız olarak bütçe, saatlik kapasite, bina bağlantısı ve B hedefi açısından taranır; en yüksek enerji tasarrufu ve en düşük yatırım MILP ile eşleşir. Kaydırılmış iki 100 kW bina pikinde gerçek kampüs piki 100 kW’tır; motor 200 kW diye kısıtlamaz.

## Yeni sentetik kampüs için örnek gerçek motor çalıştırması

Bu örnek yeni üretilen seed=25 kampüstür; diğer gaz 509.904 kWh/yıl içerir. Eski kayıttan dönüşümde bilinmeyen diğer gaz 0 varsayıldığından sonuçlar farklı olabilir.

25.000.000 TL bütçe, 2.200 kW ortak sınır, %25 hedef ve başlangıç model varsayımlarıyla:

- Mod A: yaklaşık 24.892.500 TL yatırım, 4.611.280,52 kWh/yıl (%43,10) tasarruf.
- Mod B: yaklaşık 7.295.000 TL yatırım, 2.791.739,23 kWh/yıl (%26,09) tasarruf. Başlangıç/sonraki eşzamanlı pik yaklaşık 757,60 / 1.167,85 kW.
- Her iki çözümde çözücü durum 0 ve gap=0 gözlendi. Hesaplanmış A yanıtı `sample-calculation.json` içinde.

Bu rakamlar sonuç sabiti olarak kodlanmadı; motor girdilerden hesaplar. Varsayımlar/bütçe/hedef/kapasite değişirse plan değişebilir. Basit geri ödeme yalnız enerji ve ek bakım farkını içerir; iskonto, ömür ve fiyat değişimi yoktur.
