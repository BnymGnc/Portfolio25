# Depo ve arayüz temizliği

Bu temizlik çalışan ürünü yeniden yazmaz; hesap motoru, modeller, kullanıcı kayıtları ve ortam dosyalarını korur.

## Git çalışma ağacından çıkarılanlar

- 12 tekrarlanan/tarihsel belge: dört eski verification raporu; üç demo metni; eski UI raporları, ilk teslim/iyileştirme ve önceki giriş temizliği raporu. Güncel belge dizini bunların yerini gösterir. Kalan tarihsel referanslar sabit önceki Git commit'ine bağlanır.
- 4 eski betik: `browser_final_delivery.py`, `prepare_delivery_demo.py`, `run_qa_server.py`, `verify_kayseri_pilot.py`. Biri eski düğme metnini kullanır; API betikleri güncel oturum akışını kullanmaz. Güncel oturumlu tarayıcı ve backend regresyon testleri korundu.
- `.vscode/settings.json` yalnız Git takibinden çıkarıldı; kullanıcının bilgisayarındaki dosya silinmedi. Ortak çalıştırma görevleri `.vscode/tasks.json` depoda kaldı.

16 belge/betik silinmeden önce byte kopyası alındı ve SHA-256 kontrolü yapıldı. Yerel arşiv/manifest `artifacts/repository-cleanup/` altındadır. Bu arşiv Git'e/Docker'a girmez. Git geçmişi force push veya yeniden yazımla değiştirilmedi.

Önceki temizlikte kaldırılan altı oturumsuz tarayıcı betiği ve kullanılmayan CSS geri getirilmedi. Güncel komutlar [betik rehberinde](../scripts/README.md).

## Korunanlar

Python/React kaynakları, regresyon testleri, lock dosyaları, iki model artefaktı, model metadata/kaynakları ve ComStock yeniden üretim verisi korundu. Büyük `model.joblib` çalışan ML inference için gereklidir; “gereksiz dosya” sayılmaz. Veri sözleşmesi, fizik varsayımları, örnek hesaplar, kayıt dönüşümleri ve sistem incelemesi korundu.

Gerçek `.env` okunmadı veya değiştirilmedi. Kullanıcı JSON/SQLite, geçmiş, özel yedek ve QA dosyaları Git dışında kalır. Yerel kullanıcı kayıtlarına temizlik amacıyla silme işlemi yapılmadı. Geçmişteki gerçek sırlar için Git geçmişi taraması bu çalışma değildir; çalışma ağacında izlenen dosyalar sır/özel veri yolu açısından denetlenir.

## Girişteki düzeltme

Dağıtıma özel Vercel adresinde üretim formu gösterilmez; sabit üretim adresine açık bağlantı sunulur. Origin reddi ile yanlış CSRF birbirinden ayrılır. Üretim dışındaki bütün Vercel domain'lerine backend izni açılmaz. Eski değişmez preview URL'si bu yeni kodu geriye dönük almaz; kullanıcı doğru üretim adresini açmalıdır. [Ayrıntı](deploy-render-vercel.md).

Geliştirme aracı ve teknik kapsam anlatımı ana karar akışına yeniden eklenmedi. Çalışan kat, karşılaştırma, duyarlılık, ML, kayıt ve dışa aktarım özellikleri kaldırılmadı. LLM başarısı iddia edilmez; yeni ücretli çağrı veya model eğitimi yapılmadı.

## Bu çalışmada gerçekten yürütülen kontroller

- `npm.cmd test`: 19 test geçti; yanlış Origin ile CSRF hatası ayrımı ve Vercel adres politikası dahil.
- `npm.cmd run build`: TypeScript ve Vite üretim derlemesi geçti.
- `python scripts/browser_auth_recovery.py`: gerçek Chrome'da metin/HTML 502/503, elle yeniden bağlanma, 403 sonrası doğru üretim bağlantısı ve girdilerin korunması geçti. Son açık denemede yerel kayıt/pilot yükleme çalıştı.
- `python scripts/browser_task3.py`: 390/768/1440 px; proje/bina, kampüs/iki blok/ofis, üç tema/yenileme, katlar, taslak koruma, optimizasyon, ML/fizik, imkânsız hedef, çıkış/giriş geçti. Yakalanmamış konsol hatası yok. Her iki betikte özgün JSON özetleri aynı; yalnız geçici QA hesabı temizlendi.
- Derlenmiş uygulama, yerel test sunucusunda simüle edilen Vercel hostname'iyle Chrome'da açıldı: form/API isteği yerine üretim bağlantısı, 390/1440 px taşmasız görünüm doğrulandı. Bu gerçek preview dağıtımını güncellemez. Test sunucusu/cert yalnız bu kontrol içindi ve kapatıldı.
- Mobil preview bağlantısı, 403 hata görünümü ve sonuç ekranı görüntüleri ayrıca açılıp görsel olarak incelendi. Yerel kanıtlar `artifacts/auth-recovery/` ve `artifacts/task3-ui/` altındadır.
- 16 arşiv kopyasının SHA-256 kontrolü geçti; mevcut Markdown yerel bağlantılarında kırık hedef kalmadı. Git aday dosyalarında gerçek ortam/kullanıcı/QA/yedek yolu veya yaygın anahtar kalıbı bulunmadı. Bu bütün Git geçmişine yönelik sır taraması değildir. `.env` örneklerine izin verilirken gerçek `.env` ve kullanıcı kayıtları ignore edilir.
- Sentetik kampüs Mod A hesabı yeniden yürütüldü; aynı fizik/aday evrenindeki üç yöntemin gerçek çıktıları [ürün değerlendirmesinde](product-review.md). Backend/motor/model dosyaları değiştirilmedi; bu görevde tüm backend regresyonları yeniden çalıştırılmadı.

Tarayıcı ilk denemesinde `.venv` içinde Selenium bulunmadı; sistem Python'daki kurulu Selenium 4.41.0 kullanılarak yukarıdaki kontroller tamamlandı. Yeni bağımlılık kurulmadı. Yerel test başarısı yeni commit'in üretimde yayımlandığını göstermez; üretim varlık kimliği ayrıca kontrol edilmelidir.
