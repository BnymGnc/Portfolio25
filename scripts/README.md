# Güncel betikler

- `start-local.ps1`, `restart_backend.ps1`, `stop-local.ps1`: kayıtlı PID/başlangıç zamanını koruyan yerel süreç yönetimi; dolu portta ikinci sunucu başlatılmaz.
- `browser_auth_recovery.py`: metin/HTML 502/503 giriş hatası, alanların korunması ve manuel yeniden bağlanma; geçici yerel QA hesabı temizlenir.
- `browser_task3.py`: güncel oturumlu proje/bina, tema, TR/EN, Ayarlar, taslak, hesap/karbon kartı, karar özeti indirme/eski sonuç reddi ve ML kontrolü. 320–1536 px gerçek Chrome; yerel QA hesabı temizlenir. Selenium Manager ağda takılırsa mevcut uyumlu sürücüyü `SE_CHROMEDRIVER` ortamıyla gösterin; otomatik yeni sürüm kurmak zorunlu değildir.
- `check_live_deployment.py`: Vercel üzerinden gerçek HTTPS kayıt/çıkış/giriş, hesap ve sentetik inference. Ayrı QA hesabı sunucuda kalır; silme API'si yoktur. Parola ve tokenlar kaydedilmez.
- `check_docker_deployment.py`: Linux Docker imajı, bağlama/PORT ve geçici kalıcı kayıt testi.
- `check_llm_connection.py`: isteğe bağlı gerçek LLM bağlantısı; ücretli çağrı yapabilir, standart kontrol akışında çalıştırılmaz.
- `generate_examples.py`, `generate_final_evidence.py`, `audit_delivery_data.py`: örnek/hesap kanıtı ve tutarlılık araçları.
- `import_legacy_project.py`: eski kayıtların açık, yedekli aktarımı; çalıştırmadan önce kullanımını okuyun.
- `inspect_comstock.py`, `prepare_comstock.py`, `train_energy_model.py`, `train_synthetic.py`: model yeniden üretimi; sunucu başlangıcında veya dağıtımda çağrılmaz.

Eski oturumsuz `browser_demo.py`, `browser_smoke.py`, `browser_delivery.py`, `browser_projects.py`, `browser_pilot.py` ve `browser_ui_fix.py` kaldırıldı. Bazıları varsayılan kaydı geçici olarak düzenliyordu ve güncel oturum sözleşmesiyle çalışmıyordu. Yerine güncel oturumlu kontrolleri kullanın. Eski doğrulama belgeleri geçmiş sonuçların kaydıdır; oradaki kaldırılmış komutlar güncel çalışma talimatı sayılmaz.

Son temizlikte eski düğme metinlerini kullanan `browser_final_delivery.py` ve oturum desteği olmadan API çağıran `prepare_delivery_demo.py` / `verify_kayseri_pilot.py` ile eski QA sunucusu kaldırıldı. Byte kopyaları yerelde `artifacts/repository-cleanup/` altında, Git geçmişinde de önceki commit'lerde bulunur. Güncel pilot ve hesap doğrulaması backend testleri ve `browser_task3.py` ile yapılır.

Özel ekran görüntüleri, QA kayıtları ve loglar `artifacts/` altında Git dışındadır. Model artefaktları, backend regresyon testleri ve kayıt dönüşümleri temizlikte korunur.
