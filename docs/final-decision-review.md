# Final karar desteği — 22 Ekim 2026

## Uygulanan kapsam

Üç yöntemin ortak fizik/aday evreni korundu. Tablo nihai enerji, yoğunluk, net ekonomik tasarruf ve bağlantı gruplarının eşzamanlı pik/limitlerini gösterir. Oran yöntemi B modunda hedefe ulaşınca durur; minimum yatırım garantisi değildir. Kapasitesiz plan sınırı aşmadığında GRID üstünlüğü iddia edilmez.

Sonuçtaki “Bu müdahale seçilseydi?” mevcut zorunlu müdahale endpoint'ini kullanır; LLM çağırmaz, ana planı değiştirmez. Fark tek seçim nedeni değildir; eşdeğer optimumlar olabilir. Çözümsüzlük tek başına hangi kısıtın belirleyici olduğunu kanıtlamaz.

Kaynak etiketleri geriye uyumludur. Bina genel kökeni ölçülmüş olsa bile alan bazında kaynak yoksa belirtilmemiş gösterilir. Sentetik kökenli örneklerde sentetik etiketi kullanılır. Etiket belge doğrulaması değildir. CSV sistem metadata'sı alan kaynaklarını taşır. Kaynak listesi bina ve senaryo düzenleyicilerine yönlendirir. Gerçek ölçülmüş kampüs baseline'ı henüz yoktur; %25 değiştirilebilir hedeftir.

Adlandırılmış senaryolar mevcut PostgreSQL deposunda sahip/proje anahtarıyla bağımsız girdiler, bağlam ve varsa güncel hesap olarak saklanır. Migration 002 tekrar çalıştırılabilir; kayıtları sıfırlamaz. Yerel geliştirme aynı kullanıcı veri kökünde JSON kullanır. Görüntüleme ana projeyi değiştirmez. 50 kayıt/proje sınırı vardır; silme ve ana projeye uygulama bu sürümde yoktur. Farklı girdi/motor karşılaştırması yöntem üstünlüğü kanıtı değildir.

Motor 4.1.0 nedeniyle önceki hesaplar tarihsel kalır; güncel hesap yeniden üretilmelidir.

## ML teknik incelemesi — eğitim yapılmadı

Sentetik model `synthetic-annual-1.1`, özellik şeması `spatial-inputs-1.0`. Hedef sırası elektrik ve toplam gaz; ikisi de kWh/yıl. Toplam gaz ısıtma ve sıcak su/diğer gazı içerir. Müdahale bayrakları fizik adayından gelir. Çıktı indeksleri ve toplam gaz kapsamı test_prediction_scope.py ile doğrulandı.

240 bağımsız bina: 168 eğitim, 36 validasyon, 36 test; kimlikler ayrık, varyantlar aynı bina grubunda. Test 672 satırdır. Mevcut metadata'daki Extra Trees MAE: elektrik 31.266, gaz 62.370 kWh/yıl. Lineer referans: elektrik 29.620, gaz 84.922. Seçilen model elektrikte lineer referanstan daha iyi değildir; test yeni model seçmek için kullanılmadı.

Tür bazında elektrik/gaz MAE (kWh/yıl): araştırma 20.871/52.972; eğitim 33.054/61.731; konut 25.269/51.031; ofis 22.832/46.811; otel 67.470/140.720; idari 29.965/54.435. Bunlar sentetik simülatörü yaklaşık öğrenme hatalarıdır, saha doğruluğu değildir. Model MILP adaylarını elemez veya saatlik kapasite belirlemez. Hız üstünlüğü ölçülmedi.

## Yayın ve kaynak hatası

Giriş adresi https://buildingportfolio25.vercel.app. Eski `frontend-...vercel.app` dağıtımı ayrı origin ve eski JavaScript içerir; main push o sabit dağıtımın dosyalarını değiştirmez. Backend kaynak hatası doğru adresi açıklar; CSRF/Origin koruması kaldırılmadı. SSL/TLS bağlantı hatası HTTP 403'ten ayrıdır ve yanlış parola kanıtı değildir.

## Kontroller

Gerçek PostgreSQL 16.15 üzerinde 7 test geçti: auth, sahiplik, revizyon, export/ML, migration, kesinti ve yeni senaryonun başka kullanıcıya kapalı/değişmez olması ile yeni bağlantı havuzunda korunması. Yerel JSON ve karşı-olgusal testler, kaynak şeması testleri ve mevcut yöntemlerin kombinasyon doğrulamaları geçti. Canlı yeniden deploy kalıcılığı ayrı kabul kontrolüdür; yerel PostgreSQL testi bunun yerine sunulmaz.


### Canlı kabul durumu
9b7f6b0 Render sürümünde doğrudan HTTPS backend kontrolü: PostgreSQL health, geçici QA kayıt/giriş, dört proje/sekiz bina, optimizasyon, değişmez senaryo kaydı ve ana kaydı değiştirmeyen zorunlu alternatif geçti. Gerçek kullanıcı kayıtları düzenlenmedi. Tarayıcı, curl ve Python ile Vercel sabit adresine bu ağdan TLS/SSL hatası alındı; Vercel üzerinden uçtan uca giriş başarılı sayılmadı. Eski dağıtım Origin'i backend tarafından reddediliyor; sabit üretim Origin'i kaynak kontrolünü geçiyor. Yeni backend hata metni doğru üretim adresini açıkça gösteriyor.

Yerel Chrome kabul akışı yeni senaryo kaydı/incelemesi, karşı-olgusal hesap, daha sonraki ana proje düzenlemelerinden sonra senaryo değişmezliği, eski sonuç/export koruması, ML çıkarımı ve giriş/çıkışı doğruladı. 390/1440 px yeni kontrollerin görüntüleri görsel olarak incelendi; 320–1536 px ana akış taşma kontrolleri geçti. 22 frontend testi ve üretim derlemesi geçti. Yeniden deploy sonrası canlı kalıcılık kontrolü ayrıca yürütülmektedir; sonucunu canlı kabul raporundan kontrol edin.
