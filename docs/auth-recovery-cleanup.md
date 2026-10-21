# Giriş hatası ve sadeleştirme

## Sorun ve düzeltme

Giriş istemcisi, HTTP durumunu ve içerik türünü kontrol etmeden `response.json()` çağırıyordu. Vercel/Render metin veya HTML hata sayfası döndürdüğünde kullanıcı ham `Unexpected token 'A'` ayrıştırma hatasını görüyordu. İnceleme sırasında canlı health/session istekleri JSON 200 döndü; aralıklı platform hatasının tek nedeninin uyku modu olduğu iddia edilmez.

İstemci artık içerik türünü, JSON nesnesini ve oturum alanlarını denetler. Proxy sayfası veya ayrıştırıcı hatası kullanıcıya yansıtılmaz. Hatalar Türkçe ve durum koduyla sunulur. Ana uygulamadaki JSON istekleri de aynı denetimden geçer; CSV/JSON indirmeleri kendi mevcut yolunu kullanır.

Giriş/kayıt ve ilk bağlantı ekranlarında ücretsiz demo sunucusunun uyuyabileceği ve uyanmanın yaklaşık bir dakika, bazen daha uzun sürebileceği açıklanır. Bu süre garanti değildir. [Render'ın resmî açıklaması](https://render.com/docs/free#spinning-down-on-idle).

Oturum başlangıcı için bekleme sınırı 65 saniye, yazma istekleri için 45 saniyedir. **Bağlantıyı yeniden dene** yalnız GET oturum kontrolü yapar; e-posta/parola alanlarını silmez. Kayıt/giriş gibi yazma istekleri otomatik tekrarlanmaz. Kesilen isteğin sonucu belirsizse bu açıkça belirtilir. Çerez ve CSRF akışı korunmuştur; secret değerleri frontend'e eklenmez.

Bu değişiklik sunucunun gerçek 502/503 veya DNS sorununun giderildiği anlamına gelmez. Yanıt tekrar JSON olarak erişilebilir olduğunda kullanıcı formu yeniden doldurmadan devam edebilir.

## Kaldırılanlar

- Güncel oturum sözleşmesiyle çalışmayan altı eski tarayıcı betiği: `browser_demo`, `browser_smoke`, `browser_delivery`, `browser_projects`, `browser_pilot`, `browser_ui_fix`. Bunların bir bölümü varsayılan kayıt üzerinde geçici değişiklik yapıyordu. Güncel oturumlu testler korundu; `browser_auth_recovery.py` eklendi.
- Kullanılmayan 49 CSS seçicisi: eski adım şeridi/toast, eski üst çubuk ve kaldırılan sidebar tanıtım/footer parçaları. Aktif bileşen stilleri korunur.
- Sidebar'daki tekrar eden tanıtım kartı/alt marka, yardım alanındaki geliştirme aracı metinleri ve üç kullanılmayan import.
- README'deki tekrar eden aşama anlatıları ve eski çalıştırma komutları. Güncel kurulum/yayın/test rehberi ve geçmiş belgelerin bağlantıları kaldı; `scripts/README.md` güncel betikleri açıklar.

Kullanılmayan import/parametreler artık TypeScript derlemesinde hata verir. Hesap motoru, modeller, kayıt şeması/dönüşümleri, backend regresyon testleri, kullanıcı kayıtları, `.env`, yayın rewrite/cookie ayarları değiştirilmedi. Geçmiş doğrulama belgeleri tarihsel kayıt olarak korunur; kaldırılan komutları güncel talimat saymayın.

## Doğrulama

- `cd frontend; npm.cmd test`: 18 geçti. Yeni kontroller metin/HTML 502, yanlış 200 HTML, bozuk JSON, eksik oturum alanı, manuel tekrar, çerez/CSRF taşıma ve yazma isteğinin otomatik yinelenmemesini sınar.
- `npm.cmd run build`: TypeScript ve Vite geçti; kullanılmayan değişken denetimi dahil.
- `python -X utf8 scripts/browser_auth_recovery.py`: gerçek Chrome'da ilk GET'e metin 502, kayıt POST'una HTML 503 verilerek hata yeniden üretildi. Güvenli mesaj, uyanma açıklaması, 390/1440 px, alanların korunması, yalnız bir kayıt isteği ve açık ikinci gönderimle başarılı özel pilot yüklemesi doğrulandı. Yakalanmamış konsol hatası yok; özgün JSON hash'leri aynı. Yerel QA hesabı temizlendi.
- `python -X utf8 scripts/browser_task3.py`: 390/768/1440 px; kayıt/tanıtım, proje/bina, üç tema/yenileme, taslak, gerçek MILP, değişen müdahaleyle gerçek ML, imkânsız hedef, çıkış/giriş geçti. Son rapor `completed=true`, konsol hatası yok, özgün kayıt hash'leri aynı. Bu testin özel QA hesabı da temizlendi.

Ekranlar ve rapor Git dışında `artifacts/auth-recovery/` altındadır. Hata ekranları ve sadeleştirilmiş özet açılıp görsel olarak incelendi. Geniş kullanıcı akışı kontrolünün kanıtı `artifacts/task3-ui/browser-report.json` içinde tutulur. LLM çağrısı ve ML eğitimi yapılmadı.
