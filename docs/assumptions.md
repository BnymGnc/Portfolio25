# Veri ve model varsayımları — proje genişletmesi

## Güncel varsayımlar — motor 4.0.0

20 Ekim 2026: Aşağıdaki önceki aşama notlarında “eğitilmiş AI yok” ve “sabit kat seçimi” ifadeleri tarihsel kapsamı anlatır. Güncel farklar:

- Kampüs/Kayseri verisi hâlâ sentetik; fizik ve MILP ana karar sağlayıcısıdır. Ayrı ComStock modeli **external_simulation** kaynağında eğitildi; saha doğruluğu veya Kayseri uygunluğu kanıtı değildir. Türkiye girdisine kapsam dışı yanıt verir. [Model kartı](model-card.md).
- Eski kat seçimleri zorunlu yatırım olarak korunur. Açık müdahale politikası isteğe bağlıdır: uygulanmış başlangıç, zorunlu yeni yatırım, optimizasyon adayı veya hariç. Uygulanmış seçimi için yıllık girdiler uygulama öncesi referanstır; motor fiziksel başlangıcı dönüştürür ve eski yatırımı yeniden saymaz. Ölçülmüş güncel tüketim varsayımı değildir.
- En çok beş müdahalenin uygun kombinasyonları aynı fizik motorunda yeniden hesaplanır. Tek zon kapsam şablonu kullanılır; zon başına sınırsız kombinasyon aranmaz. Ortak çatı/ekipman bir kez maliyetlenir. Sıcak su korunur; program uygunluğu ve uzman inceleme kabulü zorunludur. Konfor dinamiği modellenmez.
- Seçilmiş yeni çatı varsa hedef U ×0,8/1/1,2 (düzenlenebilir) ayrı duyarlılıktır; daha düşük U daha iyi kabuk performansıdır. SCOP/maliyet/kabuk eksenleriyle tek tek, sabit plan üzerinde değerlendirilir. Güven aralığı değildir.
- LLM açıklayıcı sayıları üretmez; backend hesap alanlarına bağlı sayısal kartları açıklar. Tek gerçek bağlantı testi HTTP 429 ile başarısız oldu; açıklayıcı gerçek sağlayıcı başarısı doğrulanmadı. Fizik hesabı bundan bağımsızdır. [AI mimarisi](ai-architecture.md).

Önceki formüller, kaynak/konfor sınırları geçerlidir; yeni politika ve bağlam için [veri sözleşmesine](data-contract.md) bakın.

## Kayseri kat/kullanım alanı pilotu

İsteğe bağlı spatial v1; yıllık toplamları kabuk/kullanım ağırlıklarıyla uzlaştıran açıklanabilir paylaştırmadır. Doğrulanmış hava/konfor simülasyonu yoktur. Çatı/aydınlatma ve uygun alan program etkileri yeniden hesaplanır; sıcak su korunur. Kritik laboratuvar/konut/otel programı azaltılmaz. Kat seçimleri portföye bir kez girer; eski fiziksel baz değişmez. Tam formüller, varsayımlar ve eksikler [pilot-kayseri.md](pilot-kayseri.md) içinde; aşağıdaki eski sınırlamaların yalnız bu dar sentetik pilot kapsamında genişletildiği dikkate alınmalıdır.

## Güncel ekler — 20 Ekim 2026

- Bütçe proje düzeyindedir. Her bina tam bir bağlantı grubuna atanır; yalnız o grubun yükleri aynı saatlerde toplanır ve grup sınırına karşılaştırılır. Bağımsız grupların toplam piki ortak trafo uygunluğu değildir. Proje toplamı tanısal olarak korunur; kapasite kullanım yüzdesi grupların en yükseğidir. Grafik ayrı grup seçtirir.
- v2 kampüsünün ortak sınırı G01'e kopyalanır. Kullanıcı değerleri korunur; dosya birebir `.v2-backup.json` yedeğiyle v3'e, revizyon +1 ile dönüşür. Eski hesap tarihsel kalır. v1 kendi yedeğiyle doğrudan v3'e dönüşür; önceki gaz varsayımları korunur.
- Gaz kazanı ve uygun sulu dağıtım **sentetik varsayımdır**; bina formunda sistem/dağıtım/kaynak ve yalıtım uygunluğu düzenlenir. Elektrikli, mevcut pompalı veya diğer sistemlerde bu gaz dönüşüm motorunun müdahaleleri filtrelenir. Yüksek sıcaklık/bilinmeyen/olmayan dağıtım pompa ve birleşik paketi engeller. Soğutma ve sıcak su tasarrufu eklenmez; mevcut elektrik/diğer gaz korunur. Konaklama konut sitesi doğrulaması değildir.
- Oran sezgiseli: pozitif yıllık nihai kWh tasarrufu / ilk TL yatırım; azalan sıra; ücretsiz pozitif tasarruf önce, eşitlikte bina kimliği/paket adı. Bina başına ilk bütçeye sığan aday, yükseltme yok; kapasite kullanılmaz. B hedefi sonradan raporlanır; optimum veya hedefe erişim garantisi değildir.
- Elektrik kısıtsız MILP bina ve grup elektrik sınırlarını kaldırır; bütçe, uygunluk ve mod B hedefi kalır. Üç plan aynı fizik motoruyla tüm gerçek sınırlar karşısında sonradan denetlenir. İhlal çıkmaması geçerli sonuçtur; üstünlük uydurulmaz.
- Sabit GRID planı için 9 satır: SCOP ×0,85/1/1,15; üç ilk yatırım maliyeti ×0,8/1/1,2; ilgili ısıdaki yalıtım azaltımı ×0,75/1/1,25. Düşük/yüksek çarpan ve kaynak/tarih düzenlenebilir; temel 1 sabittir. Her seferinde yalnız bir parametre değişir. Paketler, pompa boyutu, kazan verimi, ilgili ısı payı ve tarifeler sabittir. Maliyetle oransal bakım da değişir. Yüksek maliyet daha iyi sonuç değildir. Yeniden optimizasyon, güven aralığı ve olasılık yoktur. Geçersiz fiziksel aralıkta satır kırpılmaz; hesaplanmadı gösterilir. Bütçe/hedef/kapasite aşılması açık raporlanır.

Aşağıdaki formüller korunur; önceki tek ortak kampüs sınırı güncel sürümde her bağlantı grubuna ayrı uygulanır. Gelecek kapsam [product-roadmap.md](product-roadmap.md) içinde öneridir.

## Kesinleşmiş davranış ve kaynaklar

Gerçek bina veya AGÜ verisi, ölçülmüş saatlik veri ve eğitilmiş AI modeli yoktur. Sonuçlar aritmetik paket modeli ve SciPy/HiGHS MILP çözümünden gelir. Bina ve profil kökeni synthetic olarak saklanır. Düzenlemek bir kaydı ölçüme dönüştürmez.

İlk aşamadaki kayıtlar incelendi: **saatlik profil yoktu**. Yıllık elektrik, yıllık ısıtma yakıtı ve zaman damgasız referans pikler vardı. Referans pikler peak_electric_kw alanında korunur; kapasite hesabında kullanılmaz.

### Kayıt dönüşümü

- Şema 1.0 önce doğrulanır; orijinal içerik campus.v1-backup.json dosyasına bir kez yedeklenir. Mevcut yedek ezilmez. 2.0 atomik dosya değişimiyle yazılır, revizyon bir artar; dönüşüm tekrarlanmaz.
- Bina kimlik/ad/alan/yıl/tüketimleri ve senaryo korunur. heating_kwh_year önceki sözleşmedeki ısıtma yakıtı giriş enerjisidir; yeni modelde ısıtma doğalgazının enerji içeriği olarak yorumlanır. Toplam gaz veya faydalı ısı değildir.
- Eski kayıtta ısıtma dışı gaz bilinmediği için 0 varsayılır. Bu ölçülmüş sıfır değildir; bina formundan düzenlenmelidir. migration_notes bu kararı saklar.
- Eski biçimli PUT gönderilmeyen yeni alanları sıfırlamaz; yalnızca gönderilen alanlar birleştirilir.
- Girdi değişince revizyon artar ve eski sonuç gösterilmez/dışa aktarılmaz. Hesap sırasında girdi değişirse sonuç 409 ile reddedilir.
- Tek backend süreci/worker desteklenir. Çok süreç için veritabanı gerekir.

### Tekrarlanabilir örnek

random.Random(25) ve ilk aşamanın 8 bina sabitleri/çekiliş sırası korunur. Elektrik 45–110 kWh/m²·yıl, ısıtma doğalgazı 80–180 kWh/m²·yıl sentetik aralıklarından gelir; mühendislik referansı değildir.

Yeni oluşturulan örnekte ısıtma dışı gaz, ısıtma gazının %8’i varsayılır (toplam gazın yaklaşık %7,41’i). Dönüştürülen eski kayda ek tüketim icat edilmez: bilinmeyen diğer gaz 0’dır. Bu nedenle yeni örnek ile dönüştürülmüş kaydın toplamları farklı olabilir.

## Düzenlenebilir varsayımlar

Bina formunda parametrelerin tamamı, kaynak metni ve ISO tarih düzenlenebilir. Oranlar 0–1 kesirleridir.

| Parametre | Başlangıç varsayımı |
| --- | --- |
| Kazan verimi η | 0,90 |
| Yalıtımla ilgili faydalı ısı payı f | 0,90 |
| İlgili ısıdaki yalıtım azaltımı r | 0,30 |
| Mevsimsel SCOP | 3,20 |
| Pompanın kapsayabildiği ısı payı c | 0,90 |
| Pompa kapasitesi P | Brüt alan × 0,045 kW termal/m² |
| Yalıtım yatırımı | 350 TL/m² brüt alan |
| Pompa kapasite bedeli | 5.000 TL/kW termal |
| Pompa sabit kurulum bedeli | 100.000 TL |
| Ek yıllık bakım | Toplam paket yatırımının %1,5’i/yıl |
| Bina bağlantı sınırı | max(1 kW, eski referans pik × 1,5, yıllık elektrik / 8.760 × 3) |

Bağlantı sınırı ve pompa boyutu ilk eklemede atanır. Alan/yıllık tüketim düzenlenince sessizce yeniden boyutlandırılmaz; ayrı düzenlenir. Bu sınır gerçek bağlantı anlaşması değildir. Mevcut kazan ısı talebini karşılayabilen ve bu modelde ayrıca kapasite sınırı olmayan yedek sistem kabul edilir; yeni kazan yatırımı eklenmez.

Başlangıç fiyatları elektrik 4,5 TL/kWh, tüm doğalgaz 1,5 TL/kWh. Emisyon faktörleri elektrik 0,4 kg CO₂e/kWh, doğalgaz 0,2 kg CO₂e/kWh. Fiyat ve emisyon için ayrı düzenlenebilir kaynak/tarih alanları vardır. 19 Ekim 2026 başlangıç tarihi bir varsayım kayıt tarihidir; resmî tarife geçerlilik tarihi değildir. Bu değerler güncel resmî faktör veya fiyat teklifi olarak sunulmaz.

## Saatlik profiller

- Varsayılan dönem: 2025-01-01 00:00+03:00 → 2026-01-01 00:00+03:00 (hariç); Europe/Istanbul; 1 saat; 8.760 satır. Artık yılda 8.784 satır. Profil yılı ve seed API’de yapılandırılabilir; UI dönem/kaynağı gösterir.
- Satır ortalama kW; integral Σ(kW × 1 saat). ISO zaman damgası aralık başlangıcıdır. Bütün binalar aynı ekseni kullanır.
- NumPy SeedSequence [profil seed, bina sayısal kimliği] ile sabit yük şekli kurulur. Gün içi kullanım, hafta sonu, bina kullanımı ve ortak sentetik mevsimsellik vardır. Gerçek hava veya kullanım ölçümü değildir.
- Elektrik şekli yıllık elektriğe; ısı şekli yıllık ısıtma gazı × kazan verimine normalize edilir. Hesap dizileri yuvarlanmaz. Audit toleransı atol=10⁻⁶ kWh, rtol=10⁻¹⁰. Kontrol geçmezse optimizasyon durur.
- Isı şekli sentetik kış eğrisidir; yazın sıfır olabilir. Sıcak su ayrıca bu şekle eklenmez. Diğer gaz müdahaleden etkilenmez.
- Kampüs piki max_t Σ_b yük[b,t]. Bina uygunluğu max_t yük[b,t] ≤ bina bağlantı sınırı. Ayrı bina piklerinin toplamı kampüs kısıtı değildir.
- kW aktif güçtür; kVA, güç faktörü, faz dengesizliği, gerilim düşümü yoktur. Sonuç ölçülmüş kapasite uygunluğu değildir.

## Paket formülleri

Her bina için none, insulation, heat_pump, combined ayrı hesaplanır.

1. Faydalı ısı Q = ısıtma doğalgazı × η.
2. Yalıtımla ilgili ısı f × Q; yalıtımlı pakette Q_yeni = Q × (1 − f × r). Başka gaz ve elektriğe yalıtım tasarrufu uygulanmaz.
3. Pompalı pakette Q_HP[t] = min(c × Q_yeni[t], P × 1 saat).
4. E_HP[t] = Q_HP[t] / SCOP.
5. Kazan yedeği Q_kazan[t] = Q_yeni[t] − Q_HP[t]; kalan ısıtma gazı ΣQ_kazan / η.
6. Elektrik = mevcut elektrik + pompa elektriği. Isıtma dışı gaz korunur. Pompanın kapasitesini aşan ve kapsamadığı ısı yok edilmez; gaz kazanında karşılanır. Bu yedek varsayımında karşılanmamış ısı sıfırdır.

SCOP mevsimsel eşdeğerdir. Saatlere aynı eşdeğer oranla dağıtılır, sıcaklığa bağlı saatlik COP tahmini değildir. ΣQ_HP / ΣE_HP = SCOP korunur. Özellikle pik elektrik tahmini bu varsayıma bağlıdır. Defrost, yardımcı direnç, dağıtım pompası ve sıcaklıkla değişen termal kapasite ayrıca modellenmez. Birleşik paket bu adımların yeniden hesabıdır; tekil tasarruf yüzdeleri toplanmaz. Girilen pompa boyutu paketler arasında sabittir.

## Enerji, ekonomi ve emisyon

Nihai enerji = elektrik + ısıtma gazı + diğer gaz. Kampüs yoğunluğu aynı dönemin toplam nihai enerjisi / toplam alan; bina yüzdelerinin ortalaması değildir.

Net yıllık ekonomik tasarruf = önceki enerji maliyeti − sonraki enerji maliyeti − ek bakım. Negatif değer korunur. Bakım toplam seçilen paket yatırımına oranlanır; none için sıfır ek bakım vardır. Bilinmeyen mevcut ortak bakımın değişmediği varsayılır.

Basit geri ödeme yalnız net tasarruf >0 ise yatırım / net tasarruf; aksi halde null. İskonto, finansman, vergi, ömür, yenileme, sabit/talep bedelleri, fiyat değişimi ve karbon geliri içermez. Emisyon = elektrik × elektrik faktörü + tüm gaz × gaz faktörü. Gömülü yatırım emisyonu yoktur. Emisyon raporlanır, optimizasyon amacı değildir.

## Optimizasyon

Bina/paket başına bir ikili değişken; bina başına toplamı tam 1. Uygun olmayan bina paketinin üst sınırı 0. Kampüs için bütün saatler kısıttır. Bütçe her iki modda zorunludur.

- A: toplam yıllık nihai enerji tasarrufunu en yüksek yapar; hedef bilgi amaçlıdır.
- B: en az hedef × başlangıç kampüs enerjisi tasarrufu sağlayan en düşük yatırımı bulur; bütçe ve her iki kapasite sınırı geçerlidir.
- SciPy milp / HiGHS, mip_rel_gap=0; süre sınırı 0,01–60 sn. Durum, süre, gap ve amaç sınırı döner.
- Aday plan tamsayılık/tek seçim, bütçe, bina/kampüs kapasitesi ve B hedefi için bağımsız olarak denetlenir. Fiziksel kontrol toleransı bütçede 0,01 TL, yükte 10⁻⁶ kW, hedefte 0,001 kWh.
- Optimum yalnız çözücü durum 0 ve sıfır sayısal gap ile etiketlenir. Sınırda uygun aday optimum diye sunulmaz. Süre sınırında aday bulunamaması imkânsızlığı kanıtlamaz.
- Aynı girdiler ve bağımlılıklar tekrar üretilebilir sonuç verir; sonuç/bina seçimleri hardcode değildir. Eşdeğer optimumlarda farklı çözücü sürümleri eşdeğer farklı paket seçebilir.

## Öneriler ve henüz bilinmeyenler

Gerçek sayaç, ısıtma dışı gaz payı, iklim, saatlik yükler, kazan kapasitesi/verimi, COP eğrileri, elektrik anlaşmaları ve yatırım teklifleri bilinmiyor. Sonraki mühendislik doğrulamasında varsayımlar kaynaklı verilerle değiştirilmelidir. Gerçek veri içe aktarma, saatlik COP modeli, ayrıntılı ekonomi, çok kullanıcı depolama ve ayrıntılı görsel tasarım bu teslimde yoktur.
