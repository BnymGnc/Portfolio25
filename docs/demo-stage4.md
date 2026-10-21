# 2–3 dakikalık teslim demosu

Önce iki sunucu açık olmalı; [README](../README.md) komutlarını kullanın. Demo sentetik kampüse dayanır; resmî tarife veya ölçüm değildir. Buradaki sayılar mevcut r26 girdisinin gerçek API hesabından üretildi. Hazırlama scripti canlı kaydı değiştirmeden geçici DATA_FILE üzerinde çalıştı. Çıktılar: `artifacts/delivery/scenarios/`; tam değerler ve çözücü süreleri `manifest.json` içindedir.

## 0:00–0:35 — veri ve karar sorusu

Kampüs özeti ekranında sentetik etiketi, 8 bina ve 48.900 m² alanı gösterin. Başlangıç enerji 10.188.500 kWh/yıl, yoğunluk 208,35 kWh/m²-yıl, eşzamanlı pik 757,60 kW. Varsayımlar penceresinde elektrik 4,50 ve gaz 1,50 TL/kWh kaynak/tarihini gösterin; değerler düzenlenebilir varsayımlardır. Bina detayında birleşik paketin tekil yüzdeleri toplamadığını açıklayın.

## 0:35–1:30 — Senaryo A

Senaryo girdilerinde 25.000.000 TL, 2.200 kW, %25 hedef ve **Mod A** seçin; **Yatırım planını hesapla** düğmesine basın. Bu değerler mevcut kayıtta zaten bulunur.

Gerçek hesap: optimum kanıtlandı, gap=0; yatırım **24.892.500 TL**, kalan bütçe **107.500 TL**; enerji tasarrufu **4.611.280,52 kWh/yıl (%45,26)**; yoğunluk **208,35 → 114,05 kWh/m²-yıl**; modellenen pik **757,60 → 1.310,49 kW**, sınır 2.200 kW. Elektrik artarken doğalgaz azalır. Ek bakım sonrası net ekonomik tasarruf **2.789.494,93 TL/yıl**. Paketler: B02/B05 ısı pompası; diğer altı bina birleşik paket.

Kampüs senaryo modelini **Sonra** yapın; B01'e tıklayın. 4.815.000 TL yatırım, 1.072.485 kWh/yıl tasarruf ve yaklaşık +115,3 kW bina pik değişimini gösterin. Bunlar API paket hesaplarıdır. Saatlik grafikte pik haftasını seçin; sentetik zaman eksenini ve kapasite çizgisini belirtin. **Hesaplanmış sonuç / JSON** indirin.

## 1:30–2:30 — Senaryo B ve sınırlar

Şimdi demoda bilinçli olarak bütçeyi **8.000.000 TL**, ortak sınırı **1.000 kW**, hedefi **%25**, modu **B** yapın. Girdi değişirken önceki hesabın güncel değil olduğunu ve sonuç indirme düğmelerinin kapanmasını gösterin. Kaydet ve hesapla ile yeni revizyonu oluşturun.

Gerçek sonuç **Çözüm bulunamadı (infeasible)**; yatırım, sonraki enerji ve paketler yoktur. Bu durum için uydurma KPI gösterilmez. Model, bu girdilerin bütün kısıtlarını birlikte sağlayan plan bulamadığını kanıtladı; hangi tek kısıtın tek başına neden olduğu hakkında ayrı analiz yapılmadı. Çözücü ayrıntılarını açın. **Hesaplanmış sonuç / JSON** bu olumsuz çözücü sonucunu da kaydeder. `scenario-b-result.json` içinde after/plan null olması bu kez hesaplanmış çözümsüz durumun açık sonucudur.

Son olarak **Başlangıç verisi** seçeneğinin sonuç taşımayan farklı dosya ürettiğini gösterin. Tarayıcıdaki demo B girdilerini kaydeder; mevcut kullanıcı kaydını korumak istiyorsanız A ve B çıktılarını dosyalardan anlatın. Otomatik hazırlama/teslim doğrulama scriptleri canlı girdileri değiştirmez. İstenirse demo sonrasında önceki A değerlerini kullanıcı açıkça yeniden kaydedebilir; otomatik sıfırlama yapılmaz.

## Yeniden üretme

Proje kökünde:

```powershell
.\.venv\Scripts\python.exe scripts\prepare_delivery_demo.py
```

Script mevcut canlı girdinin salt okunur kopyasını alır; A'da bu girdileri, B'de yukarıdaki üç senaryo değişikliğini kullanır. Bina/fizik/tarife sonuçları zorlanmaz. Kullanıcı girdileri ileride değişirse sayılar da değişir; yeni manifest esas alınır. Her senaryo için ayrı inputs/result CSV ve JSON bulunur. İzole B revizyonu 27 canlı kaydın revizyonu değildir.
