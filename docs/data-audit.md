# Kayıt ve dışa aktarım incelemesi — 19 Ekim 2026

Kullanıcı girdileri değiştirilmedi. İnceleme başlangıcındaki kopyalar `artifacts/delivery/before/` altında, makine raporu `artifacts/delivery/data-audit.json` içindedir. Eski CSV/JSON dosyaları kanıt olarak korundu.

| Kayıt | Şema / revizyon | Bütçe / ortak sınır | İlk bina | Hesap |
| --- | --- | --- | --- | --- |
| artifacts/portfolio25-grid.json ve .csv | 1.0 / 3 | 30.000.000 TL / 50 kW | QA Ornek Bina | optimization_status=not_implemented; after/plan null |
| backend/data/campus.json | 2.0 / 26 | 25.000.000 TL / 2.200 kW | Mühendislik Fakültesi | Ayrı .result.json içinde aynı revizyonlu A hesabı |
| docs/sample-campus.json | 2.0 / 1 | 25.000.000 TL / 2.200 kW | Mühendislik Fakültesi | Hesaplanmamış yeni seed=25 örneği |

Dolayısıyla paylaşılan dosyalarla güncel ekran aynı kayıt revizyonuna ait değildir. Eski dosyanın şema/ready olmayan motor alanı, hesapların henüz bulunmadığı bir aşamadan kaldığını gösteriyor. “QA Ornek Bina” test verisine işaret eder; dosyayı hangi işlem veya kişinin ürettiği bağımsız olarak kanıtlanamadı. Kullanıcı adı veya senaryosu bu nedenle otomatik düzeltilmedi. Eski çıktıda null sonuç beklenir; güncel motorun hesaplanmış plan dışa aktarımıyla karıştırılmamalıdır.

Eski JSON SHA-256: `bf7b9f073d39c6ec64e09e2ef6ef03bda3bca2ba81d70a5d52750fcd86d8001e`.
Korunan güncel girdi SHA-256: `cad01997adba241386007c42dbbd5bcd7edd67662bbcba5795f468d1e2a23974`.

## Piklerin anlamı

- Eski `electric_peak_sum_kw=1860.1`: eski bina referans piklerinin toplamı; eşzamanlılık bilgisi yoktur.
- Güncel sentetik yıllık profilde ayrı bina pikleri toplamı: **841,3413 kW**, yalnız diagnostik alan.
- Güncel eşzamanlı kampüs piki: **757,5995 kW**, `max_t(sum_b(load[b,t]))`; ekran ve ortak kısıt bunu kullanır.

Bu üç sayı farklı tanımlara aittir. Eski referans `peak_electric_kw` girdileri korundu; optimizasyonda kullanılmaz. Yeni profiller yıllık elektrik tüketimlerine normalize edilir. Ölçülmüş kapasite uygunluğu iddiası yoktur.

Yeni oluşturulan örneğin diğer gazı ısıtma gazının %8'idir. Mevcut eski kayıttan dönüştürülmüş kampüste bilinmeyen diğer gaz 0 varsayılmıştır; bu kayıt değiştirilmedi. Böylece yeni örnek belgesindeki %43,10 ile mevcut kayıt A hesabındaki %45,26 tasarrufun paydaları farklıdır; mutlak tasarruf 4.611.280,52 kWh/yıl aynıdır.

## Giderilen risk

Eski dışa aktarım dosya adı başlangıç girdisiyle hesaplanmış sonucu ayırmıyordu. Ayrıca istemcide kontrol ve indirme arasındaki başka bir kaydetme/hesaplama aynı dosyaya farklı içerik getirebilirdi. Yeni arayüz açıkça kapsam seçtirir; sunucu aynı kilit altında revizyon ve hesap özeti kimliğini doğrular. Uyumsuzlukta 409 döner. Aynı revizyonda başka modla yeniden hesaplama da reddedilir. JSON ve CSV kaynak, varsayım, paket, çözücü ve önce/sonra bilgilerini taşır. Ayrıntı: [data-contract.md](data-contract.md).
