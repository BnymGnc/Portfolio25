# Portfolio25-GRID teslim — 21 Ekim 2026

**Yayın düzeni güncellendi:** Render artık kök Dockerfile ile Docker runtime kullanır. Vercel Node proxy kaldırılmış, `/api` doğrudan Render'a rewrite olarak hazırlanmıştır. `.invalid` hedef gerçek Render URL'si gelene kadar yer tutucudur. Aşağıdaki ilk teslimdeki proxy ayrıntılarının yerine [güncel yayın rehberi](deploy-render-vercel.md) geçerlidir.

Yerel uygulama: **http://127.0.0.1:5173/**. Backend yaşam kontrolü: **http://127.0.0.1:8000/api/health**. Mevcut frontend korundu; backend aynı portta kontrollü yeniden başlatıldı. Sunucular teslimde açık bırakılır. İnternet yayını henüz yapılmadı.

GitHub aktarımı doğrulandı: [BnymGnc/Portfolio25](https://github.com/BnymGnc/Portfolio25), `main` dalı. İlk teslim commit'i `0c2b2cb`; gerçek ortam dosyaları ve kullanıcı kayıtları gönderilmedi.

## Uygulananlar ve doğrulama

| Aşama | Gerçek değişiklik | Kontrol / sınır |
| --- | --- | --- |
| 1 — Düzeltmeler | Kat preview isteğine karar durumları; zorunlu/uygulanmış semantiği; boş sayısal taslak korunması; geç yanıt koruması; alternatif uygulamada form/revizyon eşitleme; AI fact referans denetimi; model metadata ve retry; grafik olay sayfalama | Geçersiz fizik güncellemesi dosya/revizyonu değiştirmiyor. Preview ile kayıt sonrası motor yatırımı/enerjisi aynı; uygulanmış çatı CAPEX'i sıfır. Tarayıcı boş girdiyi reddetti, düzeltip kaydetti; manuel alternatif bütçesi ana forma geçti. |
| 2 — Hesap ve sahiplik | Gerçek kayıt/giriş/çıkış, Argon2, SQLite, HttpOnly cookie, Origin/CSRF ve deneme sınırı; kullanıcıya özel proje/geçmiş kökü | İki hesapta farklı dört proje/sekiz bina; diğer kullanıcının snapshot/profil/export/AI/ML/scenario/hesap yollarına 404. Logout cookie iptal; yanlış CSRF/Origin 403; SQLite tekrar açılınca kullanıcı/tanıtım korunur. |
| 3 — Tanıtım | Dört adımlı SVG/CSS tanıtım; geri/ileri/atla/başla, reduced-motion, klavye odağı, yardım üzerinden tekrar | Gerçek tarayıcıda kayıt → tanıtım → pilot ve çıkış/giriş sonrası tekrar gösterilmeme doğrulandı. |
| 4 — ML | ComStock korundu. 240 bağımsız bina/4320 uygun varyantla ikinci model eğitildi; baseline/Ridge/ağaç modelleri; gruplu ayrım, metadata/model artefaktı, inference, fizik/ML farkı | Model seçimi validasyonda; testte elektrik MAE 31.266, gaz MAE 62.370 kWh/yıl. Bina ekranında müdahale değişince gerçek tahmin ve fizik sonucu değişti. İdari pilot cihaz enerjisi aralık dışında; tahmin verilmez. Saha/hız üstünlüğü yok. |
| 5 — LLM | Kota/kredi ile rate limit ayrımı; kota tekrar yok; anahtar yapılandırması, erişim ve son başarı ayrı; kullanıcıya bağlı cache | Tek kısa gerçek deneme **kota/kredi hatası** verdi; başarılı LLM yanıtı yok. Mock testler bozuk referans, sayısal iddia ve 429 davranışını sınadı. Fizik/ML/manuel alternatif çalışır. |
| 6 — Arayüz | Üç tema, açık proje/bina seçimi korundu; auth/tanıtım/ML panelleri temalı; teknik bağlam ayrıntıda; bağımsız panel hata sınırları | Chrome 390/768/1280/1536 px; iki kampüs binası, konut A/B, tek ofis; üç tema ve reload; konsolda yakalanmamış hata yok. Görüntüler açılıp görsel olarak incelendi. |
| 7 — Dağıtım | Render tek worker/kalıcı disk tanımı; Vercel aynı-origin /api geçidi, cookie/CSRF aktarımı ve no-store; modeller dağıtımda, startup eğitimi yok | Proxy testleri geçti. Gerçek Render/Vercel hesap erişimi ve servis adresleri verilmediğinden bulut servisi/HTTPS login doğrulanmadı. Kalıcı disk gerekli; ücretli kaynak satın alınmadı. |

## Çalıştırılan kontroller

- `python -m unittest discover -s backend -v`: 67 test geçti. Enerji dengesi, birleşik paket, sıfır bütçe/imkânsız hedef/aşılmış kapasite, exhaustive optimizasyon kıyası, kayıt atomikliği, proje/hesap/motor bağlamı, geçmiş, geçici senaryo, oturum/sahiplik, ML grup ayrımı/inference/yokluk/OOD kapsanır. Çıktı: `artifacts/final-delivery/backend-tests.txt`.
- Frontend `npm.cmd test`: 13 kontrol geçti; CSV/profile/context ve aynı-origin proxy cookie/CSRF/no-store dahil.
- `npm.cmd run build`: TypeScript ve Vite üretim derlemesi geçti.
- `python -X utf8 scripts/browser_final_delivery.py`: gerçek Chrome, yeni geçici QA hesabı; kullanıcı kayıtları hash ile korunuyor. Başarılı son çalışmada console_errors boş. Rapor ve görüntüler: `artifacts/final-delivery/`.
- `scripts/generate_final_evidence.py`: kullanıcı kaydına yazmadan iki gerçek ofis senaryosu hesaplandı. 2.800.000 TL bütçede 1.307.500 TL yatırım ve 230.681,6 kWh/yıl tasarruf; sıfır bütçede sıfır yatırım/tasarruf. İkincide hedef karşılanmıyor; bu sonuç gizlenmedi.

Önceki ana kampüs/pilot JSON'ları ve hesap geçmişi silinmedi. `.env` içerikleri okunmadı/yazdırılmadı/değiştirilmedi. Git ignore gerçek ortam dosyaları, kullanıcı kökü, SQLite ve özel artifacts kayıtlarını dışlar. Eski kayıtlar ilk hesaba atanmaz; [açık yedekli aktarım](auth-and-storage.md) gerekir.

## Ekran / sağlayıcı haritası

| Ekran | Sağlayıcı ve veri |
| --- | --- |
| Senaryo / sonuç | Fizik + SciPy MILP; aynı saat ekseni, bağlantı grupları, bütçe, hedef |
| Bina / kat müdahaleleri | Aynı fizik evaluator; uygulanmış/zorunlu/aday tam kombinasyonu |
| Bina / ML karşılaştırması; Model ve veri | Gerçek sentetik yıllık model + seçili bina/uygun adayın fizik sonucu, fark ve kapsam |
| Model ve veri / ComStock | Ayrı ABD harici simülasyon modeli ve ayrılmış örnek; Türkiye pilotuna zorlanmaz |
| Planı açıkla / bina seçenekleri | Backend LLM, yalnız hesap fact alanları, varsayımlar ve veri eksikleri; mevcut kredi hatası açık |
| Alternatif senaryo | LLM yalnız taslak önerir veya manuel bütçe girilir; fizik geçici hesaplar; açık uygulamadan önce kayıt değişmez |

## Kalan işler / sınırlar

1. GitHub kod deposu canlı uygulama değildir. Render/Vercel projelerini hesaba bağlayıp gerçek BACKEND_ORIGIN ve FRONTEND_ORIGINS değerlerini tanımlamak, kalıcı diski sağlamak ve HTTPS kabul akışını çalıştırmak gerekir. [Kesin yayın ayarları](deploy-render-vercel.md).
2. OpenAI hesabında kota/kredi düzelmeden LLM açıklaması alınamaz. Anahtar/model değişmedi, ücretli kredi satın alınmadı. Son çağrı durumu process belleğindedir; restart sonrası not_tested olur.
3. SQLite/JSON depolama tek worker/instance içindir. E-posta doğrulama, parola sıfırlama ve çok instance altyapısı yoktur. Proxy IP paylaşımı giriş kotasını kullanıcılar arasında daraltabilir.
4. Sentetik ML kendi fizik motorunun yaklaşımıdır; idari bina ve eğitim dışı girdilerde tahmin yoktur. Zon-kapsamlı ML, sıcak su müdahalesi, konfor/akış modeli veya saha doğruluğu iddiası yoktur.
5. Chrome yerel testleri bütün tarayıcıların veya canlı HTTPS dağıtımın kanıtı değildir. Önceki hesapsız browser scriptleri tarihsel doğrulamalardır; güncel komut browser_final_delivery.py'dir.

[Model kartı ve eğitim komutları](model-card-synthetic.md) · [API envanteri](api-inventory.md) · [Üç dakikalık demo](demo-final.md).
