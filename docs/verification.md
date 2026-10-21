# Üçüncü aşama doğrulama kaydı — 19 Ekim 2026

## Sonuç

Mevcut hesaplama motoru ve v2.0 yazma/sonuç/export sözleşmesi korunarak dört ekranlı Türkçe demo tamamlandı. Yeni bağımlılık gerekmedi. Önceki motor doğrulama kaydı verification-stage2.md içinde korunur.

## Elle hesap kontrolü

calculation-example.md ve motor testi karşılaştırıldı. Başlangıç 400 kWh elektrik + 1.000 kWh ısıtma gazı + 100 kWh diğer gaz = 1.500 kWh. Örneğe özel verim 0,8, ilgili ısı payı 0,5, yalıtım azaltımı 0,4, SCOP 4; kapsam 0,75 ve termal kapasite 100 kW. Pompa 400 kWh ısıyı 100 kWh elektrikle sağlar; kazan 240 kWh ısı için 300 kWh gaz kullanır. Sonra 500 kWh elektrik + 300 kWh ısıtma gazı + 100 kWh diğer gaz = 900 kWh.

Elektrik 2 TL/kWh, gaz 1 TL/kWh; enerji bedeli 1.900 → 1.400 TL, ek bakım 31 TL, net tasarruf 469 TL. Hesap tutarlıydı; motor değiştirilmedi. Örnek parametrelerinin uygulama başlangıç varsayımlarından farklı olduğu ve dört saatlik ufkun tam yıl olmadığı belgeye açıkça eklendi. İlgili fizik testleri yeniden geçti.

## Otomatik kontroller

| Kontrol | Sonuç |
| --- | --- |
| Backend unittest tüm testler | 29 test geçti; önceki 26 motor/kayıt testi dahil |
| Yeni salt okunur paket endpoint’i | Dört paket mevcut motor hesabıyla aynı; revizyon değiştirmiyor |
| Kampüs profil endpoint’i | Yıllık integral ve eşzamanlı pik gerçek sonuçla eşleşiyor |
| Tarihsel sonuç | Eski revizyon açıkça eski; mevcut GET/export/profil after alanlarına taşınmıyor |
| Frontend npm.cmd test | 6 test geçti: CSV alıntı/BOM/çok satır, bozuk veri/kaynak, profil bütünlüğü ve çözücü etiketleri |
| npm.cmd run build | TypeScript ve Vite üretim derlemesi geçti |
| pip check | Bağımlılık uyumsuzluğu yok |

## Chrome üzerinden temel akış

Gerçek yerel frontend ve FastAPI ile scripts/browser_demo.py çalıştırıldı:

- API’den 8 bina; sentetik kaynak ve kampüs özeti.
- Bina düzenleme ve yenileme sonrası kalıcılık; 4 gerçek paket karşılaştırması.
- Girdi kaydı + A hesabı; gerçek yatırım, 8 paket ve önce/sonra değerleri.
- 1 günlük grafik kesiti 24 saat; pik haftası doğru zaman damgasına gidiyor.
- Kaydedilmemiş değişiklik, kaydedilmiş yeni revizyon ve sayfa yenileme sonrasında eski sonuç güncel değil olarak işaretleniyor; dışa aktarma kapalı. Backend JSON export’unda eski calculation null.
- B modunda hedef sağlandı; CSV/JSON dosyaları gerçek güncel planla indirildi.
- Geçersiz CSV kaydı değiştirmedi; geçerli çıktı önizlendi, vazgeçildi ve yeniden seçilerek 8 binayı uygula ile kaydedildi. Revizyon arttı; eski sonuç geçersizleşti.
- Kontrollü profil hatası: gerçek API yanıtından bir saat çıkarıldı. Sıfır doldurmak yerine açık profil hatası gösterildi. Profili yeniden yükle gerçek grafiği geri getirdi.
- B modunda sıfır bütçe/%100 hedef çözümsüz; KPI/plan uydurulmadı.
- Varsayımlar penceresi gerçek kayıt kaynak/tarih/parametrelerini gösterdi.
- Dört ekran 390/768 px emülasyonda belge düzeyinde yatay taşma olmadan açıldı; geniş tablolar kendi alanında kaydırılıyor.
- API kesintisi açık hata verdi; tekrar dene toparlandı. Beklenmeyen tarayıcı konsol hatası yok.

Süre sınırında uygun aday ve kanıtlanmayan optimum etiketleri frontend birim testinde ve önceki motorun kontrollü çözücü testinde sınandı. Bu küçük kampüste gerçek çözücü uygun örnekleri hızlıca optimuma ulaştırdığı için tarayıcıda gerçek süre aşımı gözlendiği iddia edilmez.

QA girdileri finally içinde geri yüklendi; önceki hesap aynı modda tekrar üretildi. Revizyon yükseldi, kullanıcı bina/senaryo değerleri korundu. Son ekran görüntüleri geri yüklenen gerçek girdilerden salt okunur olarak alındı: artifacts/stage3-overview.png, stage3-results.png, stage3-chart.png, stage3-mobile.png. Ekranlar görsel olarak incelendi.

## Sınırlar

İnternete yayın yapılmadı. Gerçek ölçüm/iklim/şebeke doğrulaması veya sıcaklığa bağlı saatlik COP modeli yok. CSV yalnız mevcut sentetik şablonu günceller; ölçülmüş veri içe aktarmaz. Kaynak/varsayım sınırları UI’da erişilebilir. Starlette test istemcisinin mevcut httpx deprecation uyarısı devam eder; testler geçti.
