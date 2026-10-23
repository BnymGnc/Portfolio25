# Kendi bina akışı kabul kaydı — 23 Ekim 2026

## Çalıştırılan kontroller

- Geniş backend koşusu: 106 test, hata yok; o koşuda ayrı PostgreSQL gerektiren 7 test atlandı. Sonraki gerçek PostgreSQL koşusunda güncel 8 test hatasız tamamlandı; yeni intake/proje/teklif/sonuç yeniden bağlantı ve tekrarlı migration sonrasında korundu. Eski kayıt aktarımı/sahiplik, yanlış parola/çıkış ve kesinti sırasında 503/no-fallback de sınandı.
- Son hedefli kontroller: 11 intake/hesap testi, 5 AI testi (sağlayıcı taklidi), 7 depolama testi geçti. Basit CSV satır hatası, aylık eksik veri, kaynaklı m³ dönüşümü, desteklenmeyen yakıt, daire ortak kabuk kapsamı, gerçek teklifin enerji/maliyet/geri ödemeye etkisi, grup piki ve kullanıcılar arası erişim kontrol edildi.
- Frontend: 24 test ve üretim derlemesi geçti. GET koleksiyonları ile aynı URL'deki POST kayıt nesnesinin ayrımı için regresyon testi eklendi.
- `scripts/browser_own_building.py`: gerçek yerel backend, izole QA hesabı, eksik taslak kaydı, kaydedilmiş taslağı tekrar açma, gerçek bina projesi, öneri kartları, plan ve geçici müdahale hesabı. 390/1440 px'de veri girişi, tüketim, teklifler, seçenek kartları ve sonuç görüntüleri incelendi. Ölçülmüş saha verisi kullanılmadı; test girdileri açık QA örneğidir. AI çağrısı yapılmadı. Kanıtlar Git dışında `artifacts/own-building-ui/` altında.

## Canlı ilk kabul — 2dfee6e

Vercel'de yeni JS derlemesi ve Render `/api/health` PostgreSQL/şema hazır durumu kontrol edildi. İki ayrı QA hesabıyla:

- Kayıt ve aynı dört proje/sekiz pilot bina oluşturuldu.
- Eksik kendi-bina taslağında null değerler saklandı ve diğer hesaba görünmedi.
- Kendi doğalgaz/sulu bina projesi pilot kopyalamadan oluşturuldu; kat verisi uydurulmadı; optimizasyon sonuç üretti. Başka hesap proje erişimi 404 döndü.
- Teklif 100.000 → 120.000 TL değişince revizyon ve yatırım değişti; eski hesap güncel sayılmadı.
- Manuel zorunlu müdahale alternatifi ana kaydı değiştirmedi; adlandırılmış senaryo saklandı.
- **Bir gerçek LLM isteği 503 / quota_exhausted ile reddedildi.** Anahtarın varlığı başarılı AI işlevi olarak kabul edilmedi; harici kota/kredi sorunu devam ederken manuel fizik/optimizasyon kullanılabilir. Başka gerçek AI denemesi veya model eğitimi yapılmadı.

Gerçek saha tüketimi, tasarruf gerçekleşmesi veya kesin kapasite uygunluğu iddia edilmez. UI kontrolü yerel gerçek tarayıcıyla, canlı kabul ise aynı-origin HTTPS API üzerinden yapıldı. QA kimlikleri, parolalar, çerezler, bağlantı adresleri veya özel belgeler bu rapora yazılmadı. Eski hesabın Neon'a kurtarma aktarımı bu kontrolden bağımsızdır ve çalıştırılmadı.

## Yeniden deploy kontrol yöntemi

Canlı QA bilgileri yalnız kontrol sürecinin belleğinde tutulur. Yeni `boot_id` sonrası parolayla tekrar giriş, aynı intake, teklif, proje/revizyon, hesap ve adlandırılmış senaryo karşılaştırılır. Son makine raporu Git dışında `artifacts/product-live/report.json` dosyasındadır; süreç değişimi görülmeden kalıcılık başarılı sayılmaz.
