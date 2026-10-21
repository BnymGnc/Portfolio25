# Hesap, oturum ve veri saklama

21 Ekim 2026. Normal API çalışmasında oturum zorunludur. Tek standart kullanıcı türü vardır; otomatik yönetici, sosyal giriş, e-posta doğrulama veya parola sıfırlama sunulmaz.

- Üretim hedefi `STORAGE_BACKEND=postgres` ve Neon pooled `DATABASE_URL`. `portfolio25.users/sessions/attempts` Argon2id parola özeti, oturum özeti/CSRF, sona erme tarihi, tanıtım sürümü ve deneme sınırlarını; `projects` JSONB girdiler/revizyonu, `calculations` son ve tarihsel hesapları tutar. Oturum çerezinin kendisi saklanmaz. Yerel `STORAGE_BACKEND=sqlite` desteği ve `DATA_FILE` üst dizinindeki eski `accounts.sqlite3` korunur.
- Çerez: `portfolio25_session`, HttpOnly, SameSite=Lax; üretimde `COOKIE_SECURE=true`. Kimlik doğrulanmış oturum yedi gün, anonim CSRF oturumu bir saat yaşar. Giriş/kayıt oturumu döndürür; çıkış eski oturumu iptal eder. LocalStorage oturum anahtarı içermez.
- Önce `GET /api/auth/session`; değişiklik isteklerinde izinli `Origin` ve `X-CSRF-Token` zorunlu. Login/register da korunur. FRONTEND_ORIGINS tam adresler listesidir.
- Giriş/kayıt IP ve e-posta özeti başına 15 dakikada 12 denemeyle sınırlıdır. Güvenilmeyen forwarded-IP kullanılmaz. Bir Vercel proxy IP'si birden fazla kullanıcıyı aynı kotaya sokabilir; daha büyük dağıtım öncesinde güvenilen proxy/IP politikası gerekir.
- PostgreSQL'de sahip kimliği oturumdan gelir; proje/hesap sorgularının tamamı `owner_id + project_id` ile sınırlanır. SQLite geliştirmede eski `users/<uid>/` dizini kullanılır. Başka kullanıcıya ait proje kimliği 404 verir; istemciden sahip kimliği alınmaz.
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

Mevcut tek backend worker korunur. Render Free'de `/var/data` diski gerekmez; üretim PostgreSQL bağlantısı olmadan servis kayıtları başarılı göstermez, 503 verir. Neon sağlayıcı yedek/saklama koşulları ayrıca değerlendirilmelidir. Eski SQLite/JSON verisi yalnız açık, özel yedek üzerinden aktarılır; hiçbir eski ortak proje ilk kullanıcıya atanmaz. [Geçiş ve doğrulama](postgres-deployment.md). Açık parola sıfırlama API'si bu sürümün dışındadır. `storage_admin.py reset-password` yalnız erişilen eski yerel SQLite için yönetici aracıdır; PostgreSQL hesabını değiştirmez.
