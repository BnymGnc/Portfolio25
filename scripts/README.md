# Güncel betikler

- `start-local.ps1`, `restart_backend.ps1`, `stop-local.ps1`: kayıtlı PID/başlangıç zamanını koruyan yerel süreç yönetimi; dolu portta ikinci sunucu başlatılmaz.
- `browser_auth_recovery.py`: metin/HTML 502/503 giriş hatası, alanların korunması ve manuel yeniden bağlanma; geçici yerel QA hesabı temizlenir.
- `browser_task3.py`: güncel oturumlu proje/bina, tema, taslak, hesap, sonuç ve ML tarayıcı kontrolü. Yerel QA hesabı temizlenir.
- `browser_final_delivery.py`: önceki oturumlu teslim kabul kontrolü.
- `check_live_deployment.py`: Vercel üzerinden gerçek HTTPS kayıt/çıkış/giriş, hesap ve sentetik inference. Ayrı QA hesabı sunucuda kalır; silme API'si yoktur. Parola ve tokenlar kaydedilmez.
- `check_docker_deployment.py`: Linux Docker imajı, bağlama/PORT ve geçici kalıcı kayıt testi.
- `check_llm_connection.py`: isteğe bağlı gerçek LLM bağlantısı; ücretli çağrı yapabilir, standart kontrol akışında çalıştırılmaz.
- `generate_examples.py`, `generate_final_evidence.py`, `verify_kayseri_pilot.py`, `audit_delivery_data.py`: örnek/hesap kanıtı ve tutarlılık araçları.
- `import_legacy_project.py`: eski kayıtların açık, yedekli aktarımı; çalıştırmadan önce kullanımını okuyun.
- `inspect_comstock.py`, `prepare_comstock.py`, `train_energy_model.py`, `train_synthetic.py`: model yeniden üretimi; sunucu başlangıcında veya dağıtımda çağrılmaz.
- `run_qa_server.py`, `prepare_delivery_demo.py`: önceki izole QA ortamı yardımcıları; normal kullanıcı verisini sıfırlamak için kullanılmaz.

Eski oturumsuz `browser_demo.py`, `browser_smoke.py`, `browser_delivery.py`, `browser_projects.py`, `browser_pilot.py` ve `browser_ui_fix.py` kaldırıldı. Bazıları varsayılan kaydı geçici olarak düzenliyordu ve güncel oturum sözleşmesiyle çalışmıyordu. Yerine güncel oturumlu kontrolleri kullanın. Eski doğrulama belgeleri geçmiş sonuçların kaydıdır; oradaki kaldırılmış komutlar güncel çalışma talimatı sayılmaz.

Özel ekran görüntüleri, QA kayıtları ve loglar `artifacts/` altında Git dışındadır. Model artefaktları, backend regresyon testleri ve kayıt dönüşümleri temizlikte korunur.
