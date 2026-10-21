# 2–3 dakikalık yerel demo

Kaynaklar sentetik pilot ve ayrı ComStock simülasyonudur. Özgün kaydı değiştirmek yerine **Proje ve örnek veri yönetimi → Yeni proje oluştur** ile bağımsız ofisin tek bina kopyasını kullanın. Örnek yükleme var olan pilotu sıfırlamaz. Menü başlıkları Proje özeti / Bina detayları / Senaryo girdileri / Optimizasyon sonucu / Model ve veri.

1. **0:00–0:30:** Proje özetinde sentetik uyarı, bütçe ve bağımsız bağlantıyı gösterin. Bina detayında Katlar ve Enerji Dağılımı arasında geçin: aynı toplamın iki kırılımıdır. Elektrik/yakıt/faydalı ısı ayrı.
2. **0:30–1:10:** Müdahale Senaryoları → açık karar durumlarını etkinleştir. Çatı, kabuk, aydınlatma ve HP aday; program hariç olsun. Kaydet. Gerekli lab/konut/otel hizmeti azaltılmaz. Bütçe 2.800.000 TL ile A hesabı çalıştırın. Karar özeti, bütün müdahaleler ve tek sayılan maliyetleri gösterin. Karşılaştırma GRID üstünlüğünü zorlamaz. Zorunlu/uygulanmış davranışı ayrıca denenecekse artık aşağıdaki sayısal örnekle aynı senaryo değildir.
3. **1:10–1:45:** Aynı güncel planın senaryo ekranında “LLM kullanmadan manuel bütçe taslağı” ile daha düşük ikinci bütçe girin; “Kaydetmeden hesapla”. Ana plan ve alternatif yan yana; kayıt ve son hesap değişmez. Sayılar gerçekten farklı çıkmayabilir, bu da geçerli sonuçtur. İkinci planı ana kayda almak için ayrıca uygula gerekir. Kısıtları aşan bütçe/hedef değişikliğinde uygun plan olmayabilir; başarı hikâyesine zorlamayın.
4. **1:45–2:20:** Grafikte kaydırılmış tarihten “Yılın tamamı” seçin,8760/8760 saati; dönem piki/yıllık pik/olay seçimi ve sayısal tabloyu gösterin. Bir girdiyi değiştirin, eski sonuç ve export'un kapanmasını gösterin. Menü değişimindeki Kal/Kaydet/Vazgeç taslak kontrolünü gösterin.
5. **2:20–3:00:** Model ve veri: test MAE ve bağımsız bina split'i; seçili Kayseri projesinde kapsam dışı ML ve ayrı fizik sonucu; ComStock test örneğinde gerçek yıllık inference. LLM'nin gerçek bağlantı denemesi429 aldı; çalışmış gibi açıklama göstermeyin. Erişim varsa kullanıcı Planı açıkla'yı deneyebilir; otomatik demoda yeni ücretli çağrı yok.

Oturumun gerçek görüntüleri/kayıtları `artifacts/improvements/` altındadır. Yerel adres `http://127.0.0.1:5173`; internet yayını değildir. Sunucuları kapatmak gerekirse proje kökünde `powershell -ExecutionPolicy Bypass -File scripts/stop-local.ps1`; normal geliştirme terminallerinde Ctrl+C de kullanılabilir.

## Aynı fizik verisinden gerçekten hesaplanan iki bütçe

`artifacts/improvements/demo_calculations.py` sabit seed pilot ofis girdisini bellek içinde kopyalar; `.env` veya ana kayıt yüklemez/yazmaz. Yalnız yukarıdaki aday politikası eklenir. Mod A ve kapasite sınırları aynıdır; değişen tek senaryo girdisi bütçedir. Sonuçlar hardcode değildir: `demo-scenarios.json` iki tam girdi ve gerçek motor yanıtını içerir.

| Senaryo | Bütçe | Seçilen yeni müdahaleler | Yatırım TL | Tasarruf kWh/yıl | Tasarruf % | Çözücü |
| --- | --- | --- | --- | --- | --- | --- |
| A | 2.800.000 | Kabuk + aydınlatma + ısı pompası | 1.685.500 | 251.728,63 | 52,48 | optimal |
| B | 600.000 | Isı pompası | 572.500 | 199.322,33 | 41,55 | optimal |

B, arayüzde 600.000 TL manuel taslakla kaydetmeden çalıştırılabilir. Bunlar sentetik örneğe ait model sonuçlarıdır; kullanıcı kendi girdilerini değiştirmişse aynı sayılar beklenmez. Her iki uygun plan motorun bina ve bağlantı sınırlarından geçmiştir; maliyet/kapasite farkı üretmek için fizik verileri ayarlanmadı.
