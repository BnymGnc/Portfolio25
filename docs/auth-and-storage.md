# Hesap, oturum ve veri saklama

21 Ekim 2026. Normal API çalışmasında oturum zorunludur. Tek standart kullanıcı türü vardır; otomatik yönetici, sosyal giriş, e-posta doğrulama veya parola sıfırlama sunulmaz.

- `DATA_FILE` üst dizinindeki `accounts.sqlite3`: Argon2id parola özeti, oturum özeti/CSRF, sona erme tarihi, tanıtım sürümü ve giriş deneme sınırları. Oturum çerezinin kendisi veritabanında saklanmaz.
- Çerez: `portfolio25_session`, HttpOnly, SameSite=Lax; üretimde `COOKIE_SECURE=true`. Kimlik doğrulanmış oturum yedi gün, anonim CSRF oturumu bir saat yaşar. Giriş/kayıt oturumu döndürür; çıkış eski oturumu iptal eder. LocalStorage oturum anahtarı içermez.
- Önce `GET /api/auth/session`; değişiklik isteklerinde izinli `Origin` ve `X-CSRF-Token` zorunlu. Login/register da korunur. FRONTEND_ORIGINS tam adresler listesidir.
- Giriş/kayıt IP ve e-posta özeti başına 15 dakikada 12 denemeyle sınırlıdır. Güvenilmeyen forwarded-IP kullanılmaz. Bir Vercel proxy IP'si birden fazla kullanıcıyı aynı kotaya sokabilir; daha büyük dağıtım öncesinde güvenilen proxy/IP politikası gerekir.
- Projeler ve hesap geçmişi `users/<sunucunun ürettiği kullanıcı kimliği>/` altında saklanır. Başka kullanıcıya ait proje kimliği 404 verir; istemciden sahip kimliği alınmaz.
- Her hesaba dört projenin ayrı kimlikli kopyası oluşturulur. Mevcut kopyaların üzerine yazılmaz. Eski kampüs ve pilotlar özgün yerde korunur, ilk hesaba atanmaz.
- Taslak anahtarları kullanıcı/proje/bina bağlamındadır. Tarayıcı taslakları şifreli kasa değildir; ortak bilgisayarda ayrı tarayıcı profili kullanın.

## Eski projenin açık aktarımı

Hedef hesabı arayüzden oluşturduktan sonra proje kökünden:

```powershell
.\.venv\Scripts\python.exe scripts/import_legacy_project.py --source backend/data/campus.json --email kullanici@example.com
.\.venv\Scripts\python.exe scripts/import_legacy_project.py --source backend/data/campus.json --email kullanici@example.com --apply
```

İlk komut yalnız doğrular. İkincisi yeni kimlikle özel kopya oluşturur; özgün dosyayı değiştirmez. Girdi yedeği ve varsa eski sonuç `import-backups/` altında korunur. Eski sonuç güncel hesap sayılmaz. Tekrar aktarım mevcut projeyi ezmez. Araç güncel Campus şemasını kabul eder; v1/v2 önce mevcut yedekli dönüşümden geçmelidir.

## Operasyon sınırı

JSON ve SQLite için tek backend worker/instance kullanın. Render'da `/var/data` kalıcı diski gerekir. Tam yedek SQLite ve kullanıcı proje dizinlerini kapsar. Canlı SQLite'ı WAL dosyalarından bağımsız kopyalamayın; SQLite backup API kullanın veya sunucu dururken yedekleyin. Çok instance ve parola kurtarma bu sürümün dışındadır.
