# Üç dakikalık gerçek demo akışı

0:00–0:30 — Kayıt/giriş; ilk tanıtımı gösterin. Dört proje ve sekiz binanın sentetik olduğunu belirtin. Eski yerel projeler korunur.

0:30–1:00 — Kampüste iki bina, konut sitesinde A/B blok, ardından bağımsız ofis. Bina/kat dağılımı ile varsayımları gösterin.

1:00–2:00 — Bağımsız ofiste aşağıdaki iki bütçeyi sırayla kaydedip Mod A hesaplayın. Sonuçlar aynı sentetik ofisin mevcut evaluator’ından hesaplandı; başarı hikâyesi için girdi değiştirilmedi.

| Bütçe TL | Durum | Yatırım TL | Tasarruf kWh/yıl | Tasarruf % | Hedef | Kapasite |
| ---: | --- | ---: | ---: | ---: | --- | --- |
| 2,800,000 | optimal | 1,307,500 | 230,681.6 | 48.09 | karşılandı | modellenen sınırlar içinde |
| 0 | optimal | 0 | 0.0 | 0.00 | karşılanmadı | modellenen sınırlar içinde |

2:00–3:00 — Bina ekranında iki ML paketini karşılaştırın; fizik/ML farkını ve sentetik model sınırını gösterin. LLM kredi kotası nedeniyle yanıt alınamıyorsa bunu açıkça söyleyin; manuel alternatif ve hesaplama çalışır. Sonucu dışa aktarın. Girdi değiştirip eski sonucun güncel sayılmadığını gösterin.

Bu demo kaydı gerçek kullanıcı projesini değiştirmez; scripts/generate_final_evidence.py bellek içi örnekleri hesaplar. JSON kanıtları artifacts/final-delivery/demo-budget-*.json içindedir.
