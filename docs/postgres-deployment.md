# Render Free + Neon PostgreSQL geçişi

22 Ekim 2026. Ücretli instance/disk kararı iptal edildi. Mevcut frontend Vercel'de, backend Render Free Docker'da kalır. Kullanıcı bağlantıyı yalnız Render'a eklediğini bildirdikten sonra normal push yapıldı. Backend `2962183` sürümünde PostgreSQL bağlantısı ve gerçek tarayıcı/kontrollü yeniden yayın kabulü geçti. Gizli bağlantı okunmadı veya istenmedi. [Güncel canlı rapor](live-deployment-report.md).

## 401 için doğrulanabilenler

`POST /api/auth/login` yanlış parola ve bulunamayan kullanıcı için aynı 401'i verir. Bu, hesap varlığını herkese açıklamamak için korunur. Kullanıcının eski hesabına ait sunucu kaydı incelenmedi; hesabın silindiği kesinleştirilmedi. Önceki canlı kabulde ayrı QA hesabıyla kayıt/çıkış/tekrar giriş geçti; bu eski hesabın hâlâ varlığını kanıtlamaz. `HEAD /` veya `GET /` 401 korumalı backend kök yoludur; `/api/health` ayrıdır. Render panelindeki “Build not found” yazısının giriş hatasıyla ilişkisi kanıtlanmadı.

Eski üretim SQLite ve JSON kullanıyordu. Render Free dosyaları yeniden yayın/yeniden başlatma/uyku sırasında korumaz; bu olası kayıt kaybı nedenidir, eski hesap için tek başına kanıt değildir. [Render Free](https://render.com/docs/free#local-files-lost-on-redeploy).

## Render'a girilecek ayarlar

Kullanıcının hazırladığı Neon bağlantısında şu seçimler kullanılacak: **Branch `production` → Compute `Primary` (yazılabilir) → Database `neondb` → Role `neondb_owner` → Connection pooling açık**. Bunlar kullanıcı tarafından bildirilen ayarlardır; Neon paneline veya gizli bağlantıya erişilerek doğrulanmış değildir. Yeni bir veritabanı/branch oluşturmanız gerekmez. Uygulama tabloları bu veritabanının `portfolio25` şemasında oluşturulur; Neon veritabanı rolü uygulama kullanıcı hesabı değildir.

Connect ekranından yalnız `postgresql://` ile başlayan **bağlantı metnini** kopyalayın; `psql` komutunu, çevreleyen tırnakları veya `DATABASE_URL=` önekini Render Value alanına eklemeyin. Pooled adresin hostname kısmında `-pooler` bulunur. URL'yi elle yeniden kurmayın; TLS parametrelerini ve parola kodlamasını koruyun. `PGHOST`, `PGUSER`, `PGPASSWORD`, `PGDATABASE` veya `NEON_API_KEY` ayrıca gerekli değildir.

| Alan | Değer |
| --- | --- |
| Instance | **Free** |
| Runtime | **Docker** |
| Root Directory | Boş — depo kökü |
| Dockerfile Path / Context | `./Dockerfile` / `.` |
| Docker Command | Boş; `python serve.py` |
| Health Check Path | `/api/health` |
| Disk | **Yok** |
| `STORAGE_BACKEND` | `postgres` |
| `DATABASE_URL` | Neon Connect ekranındaki **pooled** PostgreSQL bağlantısı, yalnız secret alanı |
| `COOKIE_SECURE` | `true` |
| `FRONTEND_ORIGINS` | `https://buildingportfolio25.vercel.app` |
| `PORT` | Render sağlar; elle değişiklik gerekmez |
| `OPENAI_API_KEY` / `OPENAI_MODEL` | Mevcut değerleri koruyun; bu görevde çağrı yapılmaz |

`DATA_FILE`, `PERSISTENT_DATA_DIR`, `REQUIRE_PERSISTENT_STORAGE` üretim için gerekli değildir. Yeni Docker varsayılanı PostgreSQL'dir; Render'da açıkça SQLite seçimi de reddedilir. Vercel'e `DATABASE_URL`, parola veya API anahtarı konmaz. Vercel root `frontend`, framework Vite, `npm run build`, çıktı `dist`, mevcut `/api` rewrite aynen korunur.

Neon hesabını kullanıcı açar. Connect → Connection pooling → bağlantıyı yalnız Render secret alanına kopyalayın. `sslmode=require` / daha güçlü doğrulama ve varsa `channel_binding=require` parametrelerini silmeyin. Kod uzak bağlantılarda TLS kapatılmasını reddeder; test veritabanı yalnız loopback üzerinde TLS'siz olabilir. DSN yeniden üretilmez; sorgu parametreleri sürücüye korunarak geçer. [Neon bağlantıları](https://neon.com/docs/connect/connect-from-any-app), [pooling](https://neon.com/docs/connect/connection-pooling).

## Yayın ve migration sırası

1. Render → Settings → **Auto-Deploy kapalı**. Mevcut üretimi yeniden başlatmadan bağlantı hazırlayın. Free dosyalar hâlâ erişilebiliyorsa özel hesap/proje yedeği alın; tek CSV hesap/oturum/geçmiş yedeği değildir. Free Shell erişimi kısıtlıdır; erişilmeyen verinin yedeğini aldığımız iddia edilmez.
2. Hazır Neon projesinde yukarıdaki `production / Primary / neondb / neondb_owner` seçimlerinden pooled bağlantıyı alın. Pooled bağlantıyı Render `DATABASE_URL` secret alanına **Save only** ile ekleyin; `STORAGE_BACKEND=postgres`, cookie ve origin ayarlarını doğrulayın. **Save and deploy / Save, rebuild, and deploy seçmeyin**: eski kod henüz PostgreSQL sürümü değildir. Bağlantıyı sohbete göndermeyin. Save only seçeneği mevcut servisi değiştirmeden bir sonraki deploy için ortamı saklar. [Render ortam seçenekleri](https://render.com/docs/configure-environment-variables).
3. Yalnız ortam hazır olduğunu bildirdikten sonra normal main push yapılır. Auto-Deploy kapalı tutuluyorsa Render'da **Manual Deploy → Deploy latest commit** seçilir; eski build'i yalnız restart etmek yeni kodu yüklemez. Alternatif olarak ortam hazır olduktan sonra Auto-Deploy **On Commit** seçilip normal push ile yayın tetiklenebilir. `serve.py`, `db_migrations/001_initial.sql` dosyasını transaction ve advisory lock altında uygular. Render Free için ayrı Build/Pre-deploy migration komutu gerekmez. Sürüm/checksum `portfolio25.schema_migrations` içinde tutulur. Yeniden başlatma yalnız eksik migration'ları uygular; tablo/proje temizlemez. Eksik URL/bağlantıda sunucu 503 durumuyla yanıt verir; SQLite'ı seçmez.
4. İsteğe bağlı eski kayıt aktarımı için aşağıdaki açık yedek/aktarım araçlarını kullanın. İlk yeni hesaba eski ortak kampüsü atama yoktur. Eski hesapların devam etmesi için asıl SQLite kullanıcıları/hash'leri aktarılmalıdır; yalnız eski proje CSV'sinden hesap geri kazanılamaz.
5. Hem Render hem Vercel `/api/health`: `status=ok`, `storage.status=postgresql` beklenir. Bu bağlantı/şema denetimidir; hesap varlığını ve çözücü hazır durumunu göstermez. Veritabanı kesintisinde health 503/degraded, hesap/proje API'si `503 database_unavailable` döner; yanlış parola 401 ayrı kalır.
6. Geçici QA hesabıyla kayıt, düzenleme, revizyon, hesaplama, dışa aktarım yapın. Backend'i kontrollü yeniden deploy edin. Aynı hesaba giriş, aynı proje/revizyon/son hesap kimliğini doğrulayın. Özgün kullanıcı girdilerini değiştirmeyin. Bu üretim kontrolü bağlantı hazır olmadan tamamlandı sayılmaz.

Startup yerine yönetici migration'ı gerektiğinde process ortamındaki bağlantıyla, backend klasöründen `python postgres_store.py` çalıştırılır. `.env` içeriği okunup yazdırılmaz; bu CLI otomatik `.env` yüklemez. Render Free'de ayrı pre-deploy/job/shell olmayabileceği için Docker başlangıcı migration'ı zaten güvenle uygular. İlk normal yayında Neon SQL Editor'e elle tablo oluşturma veya `DROP/TRUNCATE` komutu girmeyin. Neon pooled bağlantısında session ayarı gerektirmeyen transaction-local kilit/timeout ve tamamen nitelikli tablo adları kullanılır; prepared statements kapalıdır.

## Kalıcı kapsam ve bağlantı politikası

- `users`: mevcut Argon2 hash'i, kullanıcı kimliği, e-posta ve tanıtım sürümü.
- `sessions` / `attempts`: hash'lenmiş oturum kimliği, CSRF, expiry ve giriş deneme sınırları. HttpOnly/Secure/SameSite=Lax/host-only çerez ve logout iptali değişmez.
- `projects`: sahip + proje kimliği, revizyon, tüm bina/zon/varsayım/girdi belgesi JSONB, son hesap işaretçisi. Kaydetme `WHERE owner_id/project_id/revision` koşuluyla transaction içinde; yarışan eski revizyon 409.
- `calculations`: güncel ve önceki kalıcı ana hesaplar JSONB. Kaydetme proje satırını kilitler ve proje/revizyon/girdi özeti/motor bağlamını tekrar doğrular. Girdi değişince son hesap silinmez, tarihsel kalır. Geçici alternatif hesap ana kaydı değiştirmez.
- Statik örnekler ve ML artefaktları dosyada kalır; eğitim başlatılmaz. AI önbelleği/geçici açıklama durumu zaten process belleğiydi; kalıcı kullanıcı kaydı gibi sunulmaz.
- Psycopg 3 + küçük havuz: en az 0 / en çok 3 bağlantı (kod üst sınırı 4), en çok 16 bekleyen, bağlantı 8 sn / havuz bekleme 12 sn, boşa çıkan bağlantı 60 sn. Her checkout bağlantı kontrolü yapar. İstek yazmaları otomatik tekrar edilmez; belirsiz commit sonucu kullanıcıya açıkça söylenir. Sürücü hatası/DSN/hash/cookie loglanmaz.

## Erişilen eski SQLite/JSON için kontrollü aktarım

Kaynağı değiştirmeden, uygulama yazmaları durdurulmuş bakım aralığında **bir** özel yedek oluşturun (depo kökü, Windows):

```powershell
.\.venv\Scripts\python.exe backend/storage_admin.py backup --data-dir backend/data --output artifacts/private-migration.portfolio25-backup.zip
```

Araç SQLite backup API kullanır; JSON tutarlılığı için bakım aralığı gerekir. `.env` veya loglar yedeğe girmez. Yedek kullanıcı hash'leri/özel veriler içerir; Git veya açık web dizinine koymayın. Aracı tekrar çalıştırmak aynı yedeği ezmez.

`DATABASE_URL` yalnız güvenli process ortamında ve `STORAGE_BACKEND=postgres` olarak ayarlanmış yönetici terminalinde:

```powershell
.\.venv\Scripts\python.exe backend/import_postgres.py --archive artifacts/private-migration.portfolio25-backup.zip
.\.venv\Scripts\python.exe backend/import_postgres.py --archive artifacts/private-migration.portfolio25-backup.zip --apply
```

İlk komut yalnız kaynak doğrular; ikinci tüm hedef aktarımını tek transaction'da yapar. Aynı arşivin tekrar uygulanması `already_imported`, çoğaltma yoktur. Hash'ler yeniden üretilmez; mevcut oturumlar/CSRF kimliği korunur. Kullanıcıya ait `users/<uid>/campus.json`, `projects/`, sonuç/geçmiş belgeleri sahipliğiyle aktarılır. Paylaşılan kökteki eski kampüs/projeler yedekte kalır, hiçbir hesaba otomatik atanmaz. Eski şema örnekleri bellekte mevcut dönüşümlerden geçer; kaynak dosyalar değişmez. Hedefte farklı kullanıcı/hash veya farklı/yeni proje girdisi varsa tüm aktarım geri alınır; kullanıcı verisi ezilmez.

Kaybolmuş kaydı yedek olmadan geri getirdiğimizi iddia etmiyoruz. `scripts/import_legacy_project.py` eski yerel SQLite için korunmuştur; PostgreSQL üretim geçişinde bu tam yedek aracını kullanın.

## Yerel geçiş kontrollerinde doğrulananlar

Ek Docker kabulü `scripts/test_postgres.py --docker-api portfolio25-api:postgres-check` ile gerçek `serve.py`/CMD ve özel PORT üzerinden çalışır. Boş PostgreSQL'de ilk migration, Secure cookie/CSRF akışı, dört proje/sekiz bina, düzenleme/hesap/dışa aktarım ve API konteynerini silip yeniden oluşturduktan sonra aynı hesap/revizyon/sonuç doğrulanır; kullanıcı veri volume'ü veya SQLite/JSON kaynağı yoktur. Bu kontrol canlı Neon TLS testi değildir.

`/api/health` ayrıca yalnız geçerli Git SHA'sı olan `release_commit` ve her API sürecinde değişen rastgele `boot_id` döndürür. Böylece eski sürüm veya hiç yeniden başlamamış süreç başarılı redeploy sayılmaz. Host adı, bağlantı metni, kullanıcı veya ortam dökümü verilmez. `scripts/check_live_deployment.py --expected-backend-commit SHA --wait-for-redeploy` gerçek Chrome kabulünden sonra QA bilgilerini yalnız bellekte tutup farklı boot gözlenince aynı kullanıcı, düzenlenmiş proje/revizyon, son hesap/dışa aktarım ve yeni parola girişini tekrar sınar. Bu bekleme sırasında kontrollü Render deploy gerekir.

- Gerçek PostgreSQL **16.15** (Docker, `postgres:16-alpine`): altı kabul testi geçti. Kayıt/doğru-yanlış parola, Secure cookie/CSRF/logout/revocation, iki hesap sahiplik reddi, gerçek düzenleme/revizyon yarışı, optimizasyon/JSON/CSV/ML çıkarımı, yeni uygulama havuzunda aynı hesap/sonuç, idempotent migration/pilot, eski hash ve oturum aktarımı, aktarım çakışmasında tüm rollback ve gerçek veritabanı stop/start sonrasında aynı havuzun toparlanması.
- Mevcut backend keşfinde **88 test, 82 başarılı + PostgreSQL için açıkça atlanan 6**. Atlanan altı test yukarıdaki ayrı gerçek veritabanı komutunda geçti; SQLite başarısı PostgreSQL kanıtı olarak sayılmadı.
- Frontend **22 test** ve TypeScript/Vite üretim derlemesi geçti. Üretim ön yüzün hâlâ doğrulanmış `f010e8e` asset'ini sunduğu HTTP+SHA256 ile kontrol edildi; yeni kod henüz push edilmedi.
- Paralel tam regresyon/Docker derlemesi sırasında test makinesinde boş RAM 154 MB düzeyine indi; iki kısa QA bağlantı zaman aşımı görüldü. Normal test bağlantı sınırı üretime yakınlaştırıldı, PostgreSQL testi bağımsız tekrar çalıştırıldı ve geçti. Bu, bir yük/kapasite testi veya Neon gecikme garantisi değildir.
- İlk kesinti testinde Docker'ın rastgele yayın portunu stop/start ile değiştirdiği ayrıldı. QA sabit uygun portla çalıştırılınca gerçek aynı adrese yeniden bağlanma doğrulandı; üretim kodunda hatayı gizleyen fallback eklenmedi.
- Gerçek `.env`, kullanıcı kayıtları ve model artefaktları değiştirilmedi; eğitim/ücretli LLM çağrısı yok. Kaynak kullanıcı kayıtlarında toplu aktarım veya tam yedek çalıştırılmadı; aktarım testleri yalnız geçici örnek kayıtlarla yapıldı.

**22 Ekim canlı kabulü:** Kullanıcının bildirdiği Neon ortamına gerçek backend bağlantısı, şema ve `29621834b1dc523e9d38e3b1552b84a2c243ef9b` commit'i hem Render hem Vercel sağlık yanıtından doğrulandı. Gerçek Chrome'da kayıt/çıkış/giriş, dört özel proje/sekiz bina, optimizasyon, 8.760 saatlik profil, sentetik ML ve sonuç dışa aktarımı geçti. QA projesi revizyonu artırılıp önceki sonuç tarihsel işaretlendi ve yeniden hesaplandı. Kullanıcının başlattığı ikinci Render yayını farklı `boot_id` üretti; aynı QA hesabı/oturumu, proje belgesi/revizyonu ve hesap/dışa aktarım kimliği korundu. Yeni süreçte parolayla tekrar giriş başarılı. Yakalanmamış tarayıcı hatası yok; LLM çağrısı veya model eğitimi yapılmadı. Eski kullanıcı hesabının 401 nedeni veya asıl kayıtların aktarılmış olduğu hâlâ doğrulanmadı.

## Doğrulama komutları ve bekleyen canlı kabul

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s backend -v
.\.venv\Scripts\python.exe -X utf8 scripts/test_postgres.py
cd frontend
npm.cmd test
npm.cmd run build
```

İlk komuttaki PostgreSQL testleri `TEST_DATABASE_URL` yokken açıkça skip edilir; SQLite başarısı PostgreSQL kanıtı sayılmaz. İkinci komut Docker'daki mevcut `postgres:16-alpine` imajıyla rastgele localhost portunda ayrı QA veritabanı çalıştırır. Mevcut konteynerlere dokunmaz. Kaynak kayıtları/gerçek `.env` okunmaz, geçici parolalar yazdırılmaz; sonunda yalnız kendi QA konteyneri/volume silinir. Yerel rapor `artifacts/postgres-acceptance/report.json`, 22 Ekim gerçek HTTPS/yeniden yayın raporu `artifacts/live-deployment/report.json` içinde Git dışındadır. Canlı veritabanı kesintisi kasıtlı oluşturulmadı; kesinti ve aynı havuzda toparlanma kontrolü yalnız ayrı yerel PostgreSQL'de yapıldı.
