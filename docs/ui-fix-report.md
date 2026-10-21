# Arayüz doğrulama ve düzeltme raporu

20 Ekim 2026. Bu görev mevcut uygulamanın görünürlük, gezinme, tema ve yerleşim düzeltmesidir. Yeni ML eğitimi, LLM çağrısı, hesap/rol sistemi veya internet yayını yapılmadı.

## Sorunun kaynağı ve açılacak adres

**http://127.0.0.1:5173/** — kullanıcı arayüzü. **http://127.0.0.1:8000/docs** — API sözleşmesi.

Port 5173'teki Node/Vite süreci **7476**, `Portfolio25-GRID/frontend` klasöründe; port 8000'deki Python süreci **24636**, proje kökünde `.venv/Scripts/python.exe backend/run.py` ile çalışıyor. İşlem çalışma dizinleri `psutil` ile, portlar işletim sisteminden, bağlantı tarayıcıdan kontrol edildi. Yeni sunucu açılmadı ve bu süreçler durdurulmadı.

Frontend `/@vite/client` ve güncel `/src/App.tsx` sunuyor; `frontend/dist` sunulmuyor. Dönen kaynakta yeni `ContextBar` var, eski `v0.3` etiketi yok. Kaynak HTTP başlıkları ve süreç kanıtı [browser-report.json](../artifacts/ui-fix/browser-report.json) içinde. Service worker kaydı kaynakta bulunmadı. Burada yanlış klasör, eski üretim sunucusu veya eski cache kanıtı yoktu; kullanıcının başka bir tarayıcı sekmesinin URL'si doğrudan okunmadı.

Asıl nedenler:

- Üç temalı özellik kaynakta **yoktu**; yalnız görünürlüğü eksik değildi.
- Proje seçimi kapalı “Proje ve örnek veri yönetimi” panelindeydi. Bina listesi yalnız detay ekranında bulunuyordu.
- `v0.3 · kullanıcı hesabı içermez` doğrudan güncel App kaynak dosyasında duran eski arayüz metniydi.
- Renkler CSS/SVG içine dağılmıştı. Önceki mobil kurallar ve işlem alanları üst bölümde gereksiz yer kaplıyordu.

Paket sürümü `0.3.0` değiştirilmedi. Özellik doğruluğu paket numarasından çıkarılmadı; çalışan kaynak, hesap ve tarayıcı kanıtları esas alındı.

## Kod / görünürlük / çalıştırma denetimi

Tarihsel `system-audit.md` güncel hata listesi olarak alınmadı. Güncel `main.py`, `exports.py`, `engine.py`, API istemcisi ve UI kaynakları incelendi; düzeltilmiş çekirdek yeniden yazılmadı.

| Beklenen özellik | Kodda mevcut | Arayüzde görünür | Çalıştırılarak doğrulanan / sınır |
| --- | --- | --- | --- |
| Eski örnek kampüs + dört projeli sekiz binalı Kayseri pilotu | Evet, korunuyor | Üstte etiketli proje seçimi | Önceki kampüs 8; pilot 4/2/1/1. Eski kampüs, kampüs, konut A/B ve ofis açıldı |
| Ayrı bina seçimi | Bu görevde üst çubuğa bağlandı | Proje alanının yanında “Bina”; mobilde ikinci satır | Kampüste eğitim/kütüphane ve konutta A/B başlıkları, kat verisi ve paketleri değişti |
| Tek bina | Evet | Sabit bina adı + “tek binalı proje” | Ofis, hesap ve sonuç geçici ofis kopyasında çalıştırıldı |
| Pilot yükleme | Evet, korunuyor | Yönetim alanında; eksikse açıklama ve yükleme alanını açma eylemi | Eksik durum yanıtı tarayıcıda taklit edilerek görünür yükleme düğmesine ulaşıldı. Bu görevde özgün projeler yeniden yüklenmedi |
| Doğa / Gece / Toprak | **Bu görevde eklendi** | Üst çubukta adı yazan “Tema” | Üç tema, yenileme sonrası tercih, gerçek hesap grafiği, form, tablo, müdahaleler ve modal kontrolü |
| Kullanıcı hesabı | Yok | “Uygulama hakkında” içinde açıkça belirtiliyor | Ana ekranda yalnız “Sentetik demo”; hesap varmış gibi bir giriş düğmesi yok |
| Taslak koruması | Evet, geçişlerle korundu | Kaydet / Vazgeç / Kal | Proje/bina değiştirme, yenileme ve tarayıcı yeniden yüklemede sınandı; kaydetme yalnız QA kaydında |
| Geç yanıt / sonuç güncelliği | Evet; yenileme sırası koruması tamamlandı | Yanlış bağlamdaki yanıt gösterilmez, eski sonuç işaretlenir | Eski bina isteği geciktirildi; yeni bina başlığı ve kat toplamı doğrulandı. Kayıt sonrası sonuç export kapalı |
| Kalıcı JSON ve hesap dışa aktarımı | Evet | “Dışa aktar” → başlangıç / sonuç → CSV / JSON | Tarayıcıdan gerçek JSON indirildi; proje ve calculation_id API snapshot'ı ile eşleşti. Mevcut CSV sözleşme testleri geçti |
| Katlar / kullanım dağılımı / müdahaleler | Evet | Bina detayında ayrı sekmeler | Elektrik toplamı API ile karşılaştırıldı; üç sekme temalar ve ekran genişliklerinde açıldı |
| Fizik, A/B, bağlantı grupları, karşılaştırma ve duyarlılık | Evet, değiştirilmedi | Senaryo / sonuç | 61 backend testi; geçici ofiste gerçek UI hesabı ve karşılaştırma/duyarlılık görünümü |
| Plan ve bina LLM açıklaması | Evet, önceki aşama | Sonuç ve bina ekranlarında korunuyor | Bu görevde ücretli çağrı yok. Sağlayıcı taklitli testler geçti; önceki tek gerçek deneme HTTP 429 idi, başarılı gerçek açıklama iddiası yok |
| Alternatif senaryo | Evet | Senaryo ekranında korunuyor | Kayıt değiştirmeyen hesap / açık uygulama testleri geçti. Bu görevde yeni AI çağrısı yapılmadı |
| Deneysel ComStock ML | Evet, önceki aşama | Model ve veri ekranı | Mevcut inference/grup ayrımı/model yokluğu testleri geçti; yeni eğitim yapılmadı. Türkiye girdileri kapsam dışı |
| Yeni tam ekran enerji gezgini / bağımsız zon detay sayfası | Kısmi: mevcut kat ve kullanım görünümleri | Mevcut sekmeler | Son ek dosyadaki bütün yeni drill-down kapsamı bu UI düzeltme görevinin parçası yapılmadı |
| Paylaşılabilir internet demo, Docker, ziyaretçi oturumu/izolasyonu | Tamamlanmış yayın yok | Yayımlanmış gibi gösterilmez | Yerel iki servis doğrulandı. İnternet yayını ve yeni oturum sistemi bu görevde eklenmedi |
| GIS / canlı dijital ikiz / otomatik klima yerleşimi | Yok | Şematik model olarak etiketli | Bu özellikler varmış gibi sunulmaz |

## Düzen ve davranış

- Masaüstü üst çubuk: **Proje → Bina → Tema**. Üçü de kapalı menü aramadan görünür. Mobilde proje tam satır, bina ve tema alt satırdır.
- Proje değişince eski detay bileşenleri kaldırılır, önceki hesap temizlenir ve ilgili snapshot yüklenir. Proje/yenileme sırası değişmişse geç başarı, hata veya loading yanıtı uygulanmaz.
- Harita ve bina seçicisi aynı seçili bina bilgisini kullanır. Grafik bileşeni hesap UUID'siyle anahtarlanır; çözücü süresi kimlik olarak kullanılmaz.
- Kaynak, veri sözleşmesi, motor ve hesap kimlikleri “Uygulama hakkında”/varsayım ayrıntılarındadır.
- CSS paletleri kullanıcı tarafından verilen renklerden oluşturuldu. Uyarı/başarı/hata renkleri, harita paket anahtarı ve grafik çizgileri de temaya bağlıdır. “Önce” kesikli, “sonra” düz, kapasite ayrı kesikli çizgiyle ayırt edilir.
- Mobilde yan menü içerik genişliğini daraltmaz. Gereksiz adım şeridi ve tekrar eden açıklamalar kaldırıldı; üstteki etiketli menü ekranlara erişimi korur. Export seçenekleri gerçek işlevlerini koruyan açılır alanda toplandı.
- Geniş tablolar ve saatlik grafik kendi içinde kayar. KPI rakamları/birimler satırlanabilir; formlar dar genişlikte tek sütuna geçer.

## Doğrulama ve kanıtlar

- `npm.cmd --prefix frontend test`: 11 geçti.
- `npm.cmd --prefix frontend run build`: TypeScript ve Vite üretim derlemesi geçti.
- `.\.venv\Scripts\python.exe -m unittest discover -s backend -p "test_*.py" -v`: 61 geçti (86,045 sn). Girdi doğrulama/yazma atomikliği, bağlam, birleşik paket, optimizasyon, ML ve AI hata izolasyonu dahil.
- `python -X utf8 scripts/browser_ui_fix.py`: gerçek Chrome/Selenium; 390, **500 ek kontrol**, 768, 1280, 1536 px. Son çalışma sonucu ve tek tek kontroller [browser-report.json](../artifacts/ui-fix/browser-report.json) içinde.
- Gerçek hesap ve kaydetme yalnız yeni QA proje kopyasında yapılır. Bu testin oluşturduğu kayıtlar, içerikleri son okuma ile aynıysa `qa-archive/` altına alınarak aktif veri alanından kaldırılır. Özgün dosyalar byte düzeyinde karşılaştırılır; hash listesi rapordadır.
- Üç temada ortak metin/etkin düğme/menü/etiketlerin hesaplanmış kontrastı en az 4,5:1 kontrol edilir. Bu tam WCAG sertifikası veya bütün ekran okuyucularla test değildir.
- [Görüntü dizini ve görsel inceleme](../artifacts/ui-fix/README.md). Ekran görüntüleri ayrıca açılarak incelendi; yalnız DOM taşması ya da build sonucuna dayanılmadı.

## Sınırlar

Yerel URL başka bilgisayarlara yayımlanmış demo değildir. Chrome masaüstü ve viewport emülasyonu kullanıldı; fiziksel Android/iOS cihaz ve Safari testi yapılmadı. Asistanın gerçek sağlayıcı başarısı bu görevde yeniden sınanmadı. Çalışan backend, kayıtlar ve `.env` değiştirilmedi. İstenen UI kapsamı dışında yeni modül eklenmedi.
