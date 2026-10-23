# Kullanıcının kendi binası: veri → seçenek → plan

23 Ekim 2026. Birincil kullanıcı enerji danışmanı ve teknik/tesis yönetimi ekibidir. Bina/portföy sahibi yatırım kararını verir. Ev sahibinin teknik katsayıları bilmesi beklenmez.

## Veri kaydı

`building_intakes` sürümlü, kullanıcıya özel taslak entity'sidir; mevcut projeler ve hesap geçmişi aynı tablolarında kalır. Migration 003 tabloyu ekler, hiçbir kullanıcı/proje sıfırlamaz. Taslak ve yayın sırasında revizyon/proje bağlantısı sunucuda denetlenir. PostgreSQL'de proje oluşturma ile taslağın projeye bağlanması aynı transaction içindedir. Başka kullanıcının taslağı okunamaz/değiştirilemez. Yayınlanan taslak kaynak anlık görüntüdür; sonraki düzenlemeler proje ekranında yapılır.

Eksik alanlar `null`, kaynak belirtilmemişse `unspecified` kalır. Eksik taslak hesap sonucu içermez. Aynı `kayseri-synthetic-v1` pilotu yeni hesaplarda aynen korunur; kullanıcıya göre yalnız proje kimlikleri farklıdır. Kendi bina girişi pilot kopyalamaz, kat/zon üretmez ve bina kaynağını sentetik etiketlemez.

Yıllık giriş tam takvim yılına aittir. Aylık girişin 12 ayı tamamlanmadan yıllık değer kullanılmaz. Elektrik kWh, alan m², bağlantı kW'dır. Gaz m³ ancak kullanıcı kaynaklı kWh/m³ dönüşümü girerse enerjiye çevrilir. Toplam gazın ısıtma payı ve ayrım kaynağı ayrıca saklanır; ayrıştırılan ısıtma/diğer gaz kullanıcı tahmini olarak etiketlenir, toplam fatura ölçümü ile karıştırılmaz. Yapım yılı ve eski referans pik bilinmiyorsa `null` kalır; model piki bunlardan türetilmez.

Saatlik ölçüm yükleme bu sürümün yeni bina akışına dahil değildir. Kullanıcı yıllık tüketimden normalize edilen model profilini açıkça kabul eder. Bina/grup kapasite kontrolleri bu profile bağlı senaryodur; ölçülmüş bağlantı uygunluğu değildir. Bağımsız binalar ayrı bağlantılarla başlar; gerçek ortak bağlantı varsa proje ayarlarında düzenlenir. Farklı yıllar aynı hesapta karıştırılmaz.

## Hesaplanabilirlik

- Doğalgaz kazanı: yıllık elektrik/gaz, ısıtma payı, alan, yıl, kaynaklı uzman varsayımları, bütçe/tarifeler ve bağlantı bilgisi tamamlandığında proje oluşturulabilir.
- Kabuk iyileştirmesi: tüm bina kapsamında teklif ve tanımlanmış ısı etkisiyle hesaplanır. Tek daireye tüm cephe/çatı yatırımı sunulmaz.
- Isı pompası: düşük sıcaklıklı sulu dağıtım, uygun hizmet kapsamı, teklif ve performans/kapasite varsayımları gerekir. Yüksek sıcaklıklı radyatör veya bilinmeyen dağıtım teknik inceleme gerektirir; kabuk seçeneğini otomatik engellemez.
- Elektrik dirençli, mevcut ısı pompası, kömür, LPG, bölgesel ısıtma ve diğer kaynaklar: taslak saklanır, bu yeni akışta sayısal ısı dönüşümü desteklenmez. Gaz kazanı gibi hesaplanmaz.
- Çatı, aydınlatma, program: mevcut pilot/kat modelinde destek korunur. Yeni kullanıcı binasında geometri/kat/zon/program olmadığı için bunlar veri/inceleme gerektirir; yapay kat oluşturulmaz. Program için korunan hizmet/uzman onayı kuralları sürer.

`GET /api/buildings/{id}/catalog` katalog kimliği/sürüm, uygunluk, sonraki adım, parametre, çakışma ve maliyet dayanağını döndürür. Ön yüzde uygunluk kararı tekrar yazılmaz. Katalog bir yapı malzemesi veya kesin cihaz kapasitesi tavsiyesi değildir.

## Maliyet

Demo fiyatları sentetik varsayımdır. Kendi bina akışında toplam tutarlı kullanıcı teklifi veya kaynaklı referans maliyet; kapsam, tarih, TRY, KDV/işçilik dahil bilgileriyle kaydedilir. Bilinmeyen dahil bilgileri null kalır. Toplam kat alanı çatı/cephe alanı yerine kullanılmaz. Teklif tutarı fizik motorunun yatırımına, yıllık bakım/net tasarrufuna, geri ödemeye ve MILP bütçesine gerçekten girer. Değişiklik eski hesabı güncel olmaktan çıkarır. Yatırım duyarlılığı teklif tutarlarını da çarpar. Uygulanmış yatırımların yeni CAPEX'i sıfırdır; birleşik müdahale yeniden hesaplanır.

## AI ve manuel yol

Mevcut Responses API tek izinli taslak aracıyla bütçe/hedef/tarife ve bina bazında `candidate / mandatory / excluded` müdahale kararı önerebilir. `applied` oluşturamaz veya mevcut uygulanmış durumu değiştiremez. Bina kimliği, katalog uygunluğu, çakışma, alan sınırı ve hesap bağlamı sunucuda denetlenir. Çok binalı belirsiz müdahale sorusunda bina adı/kodu istenir. Ana proje, kullanıcı değişikliği inceleyip uygula demeden değişmez. Geçici hesap fizik/MILP ile yapılır; LLM hesap motoru yerine geçmez.

Sayısal kartlar backend alanlarından gelir. Açıklama yanıtındaki sayısal iddialar reddedilir; doğrulanmış `fact_id` kartına bağlanır. Kapsam/birim etiketleri bu faktın motor kaydındandır. Soru/hesap değişince eski yanıt gösterilmez. Kota/erişim hatası gizlenmez. AI kapalıyken aynı geçici değerlendirme manuel müdahale seçimiyle kullanılabilir; AI yanıtı diye sunulmaz. Bu sürümde doğal dil taslağı güncel ana plan hesabından sonra kullanılabilir; eksik ilk bina verisini sohbetle tamamlama uygulanmadı.

[Resmî function calling sözleşmesi](https://developers.openai.com/api/docs/guides/function-calling): strict şemada tüm özellikler required, opsiyoneller nullable, additionalProperties false. Yeni serbest kod/SQL/ağ aracı veya vektör deposu yok. Deneysel ML, kullanıcı bina önerisi/kapasite kararı için kullanılmaz ve artefakt yeniden eğitilmez.

## Akış ve sınırlar

Binalarım → Kendi binamı ekle → üç adımlı kayıt → eksikleri tamamla/kaydet → Yatırım seçeneklerini aç → Planım → hesapla → Karşılaştır. Basit CSV şablonu/önizleme/satır hataları bu giriştedir; eski sentetik CSV yolu ayrı korunur. Kaydedilmiş senaryolar proje/alan/yıl/motor karşılaştırılabilirliğini denetler. Teknik model ekranı Yardım altındadır.

Kayıt sonrası asıl proje girdi düzenleyicisi uzman kapsamındadır. Kullanıcı teklifi eklemek mühendislik uygunluğunu kanıtlamaz. Yeni kullanıcı binası için ayrıntılı kat editörü, ölçülmüş saatlik sayaç içe aktarımı ve elektrik dirençli ısıtma dönüşümü bu teslimde yoktur. Gerçek saha baseline'ı veya gerçekleşmiş tasarruf iddiası yoktur.
