# Görev 3 — kullanılabilirlik teslimi, 21 Ekim 2026

Mevcut React/FastAPI uygulaması düzenlendi; hesap motoru, modeller, kullanıcı kayıtları ve Render Docker / Vercel rewrite düzeni korundu. Bu görevde model eğitimi ve ücretli LLM çağrısı yapılmadı. Yerel uygulama `http://127.0.0.1:5173/`; bu bir internet yayını değildir.

## Somut düzeltmeler

- Giriş/kayıt kartı 432 px, masaüstünde 32 px ve mobilde 24 px iç boşlukla düzenlendi. Parola kuralı yalnız kayıtta; göster/gizle, autocomplete, Enter, yüklenme ve hata durumları gerçek kimlik doğrulamaya bağlı. Submit öncesi CSRF oturumu yenilenir. Tema küçük kontrol; uygulanmayan hesap özellikleri yardım metninde.
- Üst çubukta Proje ve Bina seçimi kaldı. Sağdaki **Hesap ve yardım** açılır menüsünde tema, hesap, çıkış, tanıtım, veriyi yenileme ve varsayımlar bulunur. Proje/örnek yükleme ayrı açılır alanda. Başarılı API satırı, tekrarlanan adım şeridi ve büyük sentetik uyarı kaldırıldı; kısa sentetik rozet ve ilgili kaynak açıklamaları korundu.
- Bina adı ana başlık; proje/tür/alan ve düzenleme eylemi yanında. Önce enerji değerleri, sonra Katlar / Enerji Dağılımı / Müdahaleler. Kat ve kullanım tabloları aynı toplamın farklı kırılımları olarak etiketlidir; geniş tablolar kendi içinde kayar.
- Senaryoda bütçe ve hedef önce; anlaşılır A/B modu ve tek ana hesap eylemi. Bağlantılar, tarifeler ve uzman varsayımları açılır ayrıntılarda. Hesaplanan proje ve bina sayısı belirtilir.
- Sonuçta önce seçilen plan/yatırım, enerji tasarrufu, yoğunluk ve **ek bakım sonrası yıllık net ekonomik tasarruf** gösterilir. Enerji bedeli farkı ayrı açıklanır. Kapasite, grafik ve bina planı devam eder; çözücü süresi/gap ayrıntıda. Optimum ve çözümsüz etiketleri API durumundan gelir; kanıtlanmamış sonuç optimum sayılmaz.
- Bildirimler proje/revizyon/hesap kimliğine bağlı. Yeni başarılı hesap kayıt bildirimini temizler. Eski sonuç ve dışa aktarım koruması sürer; mobilde sonuç üstüne yerleşen sabit bildirim yoktur.
- Tanıtım sırasında henüz yüklenmemiş uygulama yerine genel marka arka planı bulunur. Native dialog odağı, Escape, geri/ileri/atla ve azaltılmış hareket desteği korunur. Tanıtımı tekrar açma taslak korumasından geçer.
- Üç tema ve sayısal Türkçe gösterim korunur. Eski CSS çakışmaları kontrollü yerleşimle çözüldü; sayfa taşması `overflow:hidden` ile gizlenmedi.

## ML kapsamı kontrolü

Mevcut `synthetic-annual-1.1` artefaktı değişmedi. 240 bağımsız sentetik bina / 4.320 müdahale satırıyla önceki eğitimden gelen gerçek inference kullanılır. Eğitim tekrarlanmadı. ComStock sağlayıcısı da korundu. ML yatırım seçmez; fizik ve MILP kararın kaynağıdır. Yıllık ML tahmini elektrik kapasitesi kanıtı değildir.

Bağımsız ofisin 2025 birleşik kabuk + ısı pompası adayı için kontrol:

| Alan | Gerçek hesap/tahmin, kWh/yıl |
| --- | ---: |
| Fizik: kalan ısıtma gazı | 22.688,4 |
| Fizik: sıcak su/diğer gaz | 25.200,0 |
| Fizik: toplam gaz | 47.888,4 |
| ML: toplam gaz | 118.155,1 |
| ML − fizik | +70.266,7 |
| Fizik toplam gazına göre fark | +%146,7 |

Aynı bina, yıl, kWh/yıl birimi, toplam gaz hedefi ve müdahale bayrakları karşılaştırıldı. Özelliklerin başlangıç tüketimlerinden geldiği ve çıktı sırasının kayıtlı eğitim hedefleriyle eşleştiği test edildi. Bu örnekte kapsam/özellik eşleme hatası bulunmadı; büyük fark deneysel modelin sınırlamasıdır. Tahminler ve örnek veri değiştirilmedi.

API yanıtına `year` ve gerçek `input_features` eklendi; arayüzde açılır kapsam/özellik tablosu, fizik gaz ayrımı, mutlak ve göreli fark bulunur. Fizik referansı 1 kWh/yıl altında ise yüzde gösterilmez. %50 üzerindeki fark dikkat uyarısıdır; istatistiksel güven sınırı değildir. LLM açıklamaları ikincil açılır paneldedir. Bu görevde gerçek LLM başarısı doğrulanmadı; önceki kota/kredi hatası nedeniyle çalışıyor iddiası yapılmaz.

## Çalıştırılan doğrulama

| Kontrol | Sonuç |
| --- | --- |
| `cd frontend; npm.cmd test` | 15 geçti; mevcut veri/deployment kontrolleri ve yeni bildirim bağlamı/ML farkı kontrolleri |
| `cd frontend; npm.cmd run build` | TypeScript + Vite üretim derlemesi geçti |
| `.\.venv\Scripts\python.exe -m unittest discover -s backend -p test_prediction_scope.py -v` | 1 geçti; toplam gaz/yıl/özellik ve gerçek artefakt çıktı eşlemesi |
| Aynı komut, `-p test_final_integrity.py` | 3 geçti; preview/kayıt paritesi, hariç müdahale ve ML ayrımı/inference/yokluk |
| Aynı komut, `-p test_ml.py` | 1 geçti; mevcut ComStock davranışı |
| `python -X utf8 scripts/browser_task3.py` | Gerçek Chrome akışı geçti; yakalanmamış konsol hatası yok |

Tarayıcı yeni geçici QA hesabıyla kayıt/giriş/çıkış, tanıtım/tekrar/Escape, kampüste iki bina, konut A/B, tek ofis, üç tema ve yenilemede tercih, taslakla gezinme/yenilemede Kal, kurtarılabilir paket API hatası/tekrar dene, kaydet→gerçek MILP→eski uyarının temizlenmesi, değişen müdahaleyle gerçek ML ve imkânsız hedef durumunu çalıştırdı. Özgün JSON girdi/sonuç dosyalarının SHA-256 özetleri değişmedi. Geçici hesabın kendi kayıtları temizlendi; özel QA kopyaları Git dışındadır.

İlk anlamlı sayı veya senaryo girdisinin sayfa üstünden uzaklığı; kart kenarı yerine gerçek veri öğesi ölçüldü:

| Görünüm | 390 px | 768 px | 1440 px |
| --- | ---: | ---: | ---: |
| Özet | 438,2 | 343,4 | 277,5 |
| Bina | 432,2 | 335,4 | 269,5 |
| Senaryo | 442,7 | 344,9 | 284,0 |
| Sonuç | 419,2 | 374,4 | 308,5 |

Hedef masaüstünde 350 px, diğer iki genişlikte 450 px; üç genişlikte sayfa genelinde yatay taşma kontrolü geçti. Grafik/tablo kendi kaydırma alanına sahiptir.

41 ekran görüntüsü ve makine raporu yerelde `artifacts/task3-ui/` altındadır. Giriş masaüstü/mobil, mobil özet, masaüstü senaryo/sonuç/ML, mobil kat/sonuç/grafik, 768 px kullanım dağılımı ve Gece teması görüntüleri ayrıca açılıp görsel olarak incelendi. Klasör özel QA verisi içerebildiği için Git'e alınmaz; yeniden üretim betiği depodadır.

## Kalan sınırlar ve yayın

Saha doğruluğu, konfor simülasyonu ve ML üstünlüğü kanıtlanmadı. Gerçek LLM bağlantısı bu görevde denenmedi. Render ve Vercel servis URL'leri verilmediği için HTTPS üzerindeki canlı kabul testi yapılmadı. `frontend/vercel.json` içindeki `.invalid` adres yer tutucudur; gerçek Render URL'si olmadan üretim API bağlantısı çalışmaz. [Yayın ayarları](deploy-render-vercel.md) geçerlidir.

Yerel sunucular görev sonunda açık bırakılır. Kapalıysa `powershell -ExecutionPolicy Bypass -File scripts/start-local.ps1` boş 8000/5173 portlarında başlatır; dolu portta ikinci sunucu açmaz. `scripts/stop-local.ps1` yalnız kayıtlı PID ve başlangıç zamanı eşleşen süreçleri durdurur. Elle başlatılan terminalde Ctrl+C kullanılabilir. Gerçek `.env` okunmadı, değiştirilmedi ve Git'e eklenmedi.
