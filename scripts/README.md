# Güncel betikler

- `test_postgres.py`: Docker'da gerçek, ayrı PostgreSQL 16 QA veritabanında oturum/CSRF, sahiplik, revizyon yarışı, kalıcı hesap/dışa aktarım/ML, eski veri aktarımı, tekrarlı migration ve gerçek stop/start kesintisi. Üretim Neon testi yerine geçmez. `.\.venv\Scripts\python.exe -X utf8 scripts/test_postgres.py`. `--docker-api portfolio25-api:postgres-check` eklenirse gerçek uygulama imajının CMD/PORT/migration/configuration yolu ve yeni konteyner sonrası hesap/proje/revizyon/hesap sonucu da doğrulanır; önce bu imajı güncel Dockerfile ile oluşturun. Geçici loopback HTTP kontrolü canlı HTTPS cookie/Neon TLS testi değildir.
- `backend/storage_admin.py`: yalnız eski yerel SQLite için açık özel yedek ve yönetici işlemleri; gerçek `.env` okumaz. `backend/import_postgres.py` aynı özel yedeği kontrollü/idempotent PostgreSQL aktarımında kullanır. [Geçiş sırası](../docs/postgres-deployment.md).
- `check_docker_deployment.py` eski SQLite geliştirme yolunu açık `STORAGE_BACKEND=sqlite` ile sınar; bu test PostgreSQL doğrulaması değildir. Üretim Docker varsayılanı PostgreSQL'dir.

- `start-local.ps1`, `restart_backend.ps1`, `stop-local.ps1`: kayıtlı PID/başlangıç zamanını koruyan yerel süreç yönetimi; dolu portta ikinci sunucu başlatılmaz.
- `browser_auth_recovery.py`: metin/HTML 502/503 giriş hatası, alanların korunması ve manuel yeniden bağlanma; geçici yerel QA hesabı temizlenir. `--data-dir` yerel QA sunucusunun veri dizinini seçer.
- `browser_task3.py`: güncel oturumlu proje/bina, Ayarlar üzerinden tema/TR/EN, bina sekmeleri, taslak, hesap/karbon kartı, karar özeti indirme/eski sonuç reddi ve ML kontrolü. 320–1536 px gerçek Chrome; yerel QA hesabı temizlenir. `--data-dir` sunucunun `DATA_FILE` üst diziniyle aynı olmalıdır; ayrı QA deposu önerilir. Yalnız seçili kabul görüntüleri saklanır. Selenium Manager ağda takılırsa mevcut uyumlu sürücüyü `SE_CHROMEDRIVER` ortamıyla gösterin.
- `check_live_deployment.py`: Vercel üzerinden gerçek HTTPS kayıt/çıkış/giriş, hesap ve sentetik inference. Ayrı QA hesabı sunucuda kalır; silme API'si yoktur. Parola ve tokenlar kaydedilmez.
- `check_docker_deployment.py`: Linux Docker imajı, bağlama/PORT ve geçici kalıcı kayıt testi.
- `check_llm_connection.py`: isteğe bağlı gerçek LLM bağlantısı; ücretli çağrı yapabilir, standart kontrol akışında çalıştırılmaz.
- `generate_examples.py`: belgelenmiş sentetik sözleşme örneklerini üretir. Güncel kullanıcı verisini okumaz.
- `import_legacy_project.py`: eski kayıtların açık, yedekli aktarımı; çalıştırmadan önce kullanımını okuyun.
- `inspect_comstock.py`, `prepare_comstock.py`, `train_energy_model.py`, `train_synthetic.py`: model yeniden üretimi; sunucu başlangıcında veya dağıtımda çağrılmaz.

Eski oturumsuz tarayıcı betikleri ve tek teslim için yazılmış rapor üreticileri çıkarıldı. Güncel pilot ve hesap doğrulaması backend testleri ve oturumlu tarayıcı kontrolleriyle yapılır. Eski araçlar Git geçmişinde, son çıkarılanların yerel kopyaları `artifacts/ui-review/retired/` altında bulunur.

Özel ekran görüntüleri, QA kayıtları ve loglar `artifacts/` altında Git dışındadır. Model artefaktları, backend regresyon testleri ve kayıt dönüşümleri temizlikte korunur.
