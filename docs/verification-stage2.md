# İkinci aşama doğrulama kaydı — 19 Ekim 2026

## Ortam ve çalıştırılan komutlar

Windows/PowerShell, Node 22.19.0, Python 3.13.7; mevcut React 19.3.1, TypeScript 7.0.2, Vite 8.3.4 ve FastAPI 0.141.1 korundu. Kurulu SciPy 1.17.1 / NumPy 2.4.2 metadata’sı incelendi; SciPy’nin NumPy gereksinimi >=1.26.4,<2.7 ile uyumlu. Bu sürümler ve Windows IANA saat dilimi için tzdata 2025.3 sanal ortama kuruldu. requirements-lock.txt güncellendi.

- .venv/Scripts/python.exe -m unittest discover -s backend -p "test_*.py" -v: **26 test geçti**.
- frontend içinde npm.cmd run build: TypeScript kontrolü ve Vite üretim derlemesi başarılı.
- .venv/Scripts/python.exe -m pip check: uyumsuz bağımlılık yok.
- .venv/Scripts/python.exe scripts/generate_examples.py: 8.760 saatlik tutarlı örnek kampüs ve gerçek motor A planı yeniden üretildi.
- python scripts/browser_smoke.py: Chrome/Selenium üzerinden frontend/backend iş akışı geçti.

## Fizik ve optimizasyon kanıtları

| Kontrol | Sonuç |
| --- | --- |
| 2025/2024 saatlik eksen | 8.760 / 8.784 saat; ISO +03:00, Europe/Istanbul |
| Elektrik ve faydalı ısı integrali | Yıllık toplamlarla tutarlı; ilk 8 bina elektrik farkı en fazla yaklaşık 5,82×10⁻¹¹ kWh |
| Seed tekrarı | Aynı seed/parametreyle diziler aynı; başka seed şekli değiştiriyor |
| Küçük elle örnek | Q=800, yalıtım sonrası 640, HP 400, gaz kazanı 240, HP elektrik 100, kalan gaz 300 kWh; motorla eşleşti |
| Pompa kapasite aşımı | Açık gaz yedeğine aktarılıyor; ısı korunumu doğrulandı |
| Birleşik paket | Ayrı hesap: örnekte 680 kWh; tekil 200+600 toplamı uygulanmıyor |
| Negatif ekonomi | −331 TL/yıl korunuyor; geri ödeme null |
| Müdahale yok | Tam sıfır enerji/net tasarruf; sahte sıfır yıllık geri ödeme yok |
| Eşzamanlı pik | İki farklı saatte 100 kW bina piki → kampüs 100 kW; 200 kW değil |
| Enerji yoğunluğu | Toplam enerji / toplam alan; bina ortalamaları kullanılmıyor |
| Küçük MILP A/B | İki bina × dört paket = 16 kombinasyonun bağımsız taramasıyla aynı amaç değeri |
| Bütçeli B hedefi | Sıfır bütçeyle pozitif hedef çözümsüz; hedef/bütçe birlikte uygulanıyor |
| Ayrı kapasite sınırları | Bina bağlantısı ve ortak besleme ayrı zorunlu |
| Süre/gap/kanıt durumu | Kontrollü çözücü testinde süre sınırı adayları optimum etiketlenmiyor; aday yoksa imkânsızlık iddiası yok |
| Hatalı aday | Kesirli/uygunsuz aday bağımsız doğrulamada reddediliyor |
| Gerçek MILP tekrarı | Aynı girdilerle aynı plan; hardcoded seçim yok |
| Sıfır başlangıç enerjisi | Yüzde/geri ödeme null; bölme hatası yok |

Elle hesap ve örnek kampüs sonuçları: calculation-example.md. Örnek JSON motor tarafından scripts/generate_examples.py ile üretilir; çalışma zamanı bu dosyaları okumaz.

## Korunan işlevler ve tarayıcı doğrulaması

- Kalıcı bina düzenleme ve yenileme sonrası veri korunması geçti.
- Bütçe/kapasite kaydı ve aşım uyarısı geçti.
- İmkânsız kapasitede Hesapla uygun plan olmadığını gösterdi; sahte sonuç tablosu oluşmadı.
- A ve B modunda sekiz bina/paket ve gerçek önce/sonra sonuçları gösterildi; B hedefi sağlandı.
- Kaydedilmemiş senaryo Hesapla’yı devre dışı bıraktı; kayıttan sonra eski sonuç kaldırıldı.
- CSV/JSON indirmelerinde güncel hesap ve optimum kanıtı doğrulandı.
- Envanter araması, API kesintisi/açık hata/tekrar dene ve konsol kontrolü geçti.
- 390/768 px görünümlerde belge yatay taşması yok; geniş sonuç tabloları kendi alanında kaydırılır.
- 1.0 kayıt yedeklendi; bina ad/alan/yıl/tüketimleri ile senaryo bütçe/kapasitesi korundu. Dönüşüm tekrar uygulanmıyor; eski PUT yeni varsayımları sıfırlamıyor.
- Hesap sırasında girdi değiştirme testi eski sonucu kaydetmeden 409 döndürdü.
- QA girdileri geri yüklendi; revizyon yükseldi. Üretim dosyasında hesaplanmış sonuç ayrı result.json içinde revizyona bağlanır.

## Sınırlar

Gerçek ölçüm/iklim/bağlantı verisiyle doğrulama veya internete dağıtım yapılmadı. SCOP saatlere sabit mevsimsel eşdeğer olarak dağıtılıyor; saatlik sıcaklık COP modeli değil. Kazan yedeği ayrıca kapasite kısıtına sahip değil. Detaylı ekonomi ve çok worker/çok kullanıcı desteği yok. Görsel tasarım kapsamlı yenilenmedi.

Starlette test istemcisi httpx entegrasyonu için gelecekte kaldırma uyarısı veriyor. Testler geçiyor; bu uyarı çalışan API’nin sonucu değildir. Gerçek süre sınırının tam hangi milisaniyede devreye gireceği makineye bağlıdır; sınır durumu mantığı kontrollü çözücü yanıtlarıyla ayrıca test edildi.
