export default function DemoGuide() {
  return <section className="demo-guide" aria-label="Prototip kapsamı ve demo rehberi">
    <h3>Demoyu iki dakikada deneyin</h3>
    <ol>
      <li>Hesap oluşturun; size ait dört projeli, sekiz binalı sentetik pilot açılır.</li>
      <li>Proje ve bina seçin. Senaryo girdilerinde bütçeyi, hedefi ve bağlantı sınırlarını inceleyin; yatırım planını hesaplayın.</li>
      <li>Sonuçta aynı yıllık başlangıca göre enerji, kWh/m²-yıl, net ekonomik tasarruf ve kapasiteyi karşılaştırın. Güncel sonucu CSV/JSON olarak dışa aktarabilirsiniz.</li>
      <li>Bina detaylarında “ML ve fizik sonucunu karşılaştır” ile uygun müdahaleye ait gerçek model tahminini deneyin. Kapsam dışındaki girdiye tahmin verilmez.</li>
    </ol>
    <h3>Fizik, optimizasyon ve AI ne yapıyor?</h3>
    <dl>
      <dt>Fizik ve SciPy MILP</dt><dd>Enerjiyi hesaplar; bütçe ve elektrik bağlantı sınırlarına göre yatırım planını seçer. Eğitilmiş ML değildir.</dd>
      <dt>Deneysel ML</dt><dd>Sentetik simülasyonla eğitilmiş model, bina ve müdahaleden yıllık elektrik/toplam gaz tüketimini tahmin eder. Fizik sonucuyla kıyaslanır; yatırım planını veya saatlik pik hesabını belirlemez. Ayrı ComStock modeli ABD simülasyonları içindir.</dd>
      <dt>İsteğe bağlı LLM</dt><dd>Hesapları açıklamak için hazırlanmıştır. Başarılı erişimi doğrulanmış bir çekirdek özellik olarak sunulmaz; hata vermesi fizik ve ML hesabını engellemez.</dd>
    </dl>
    <details><summary>Veri, hedef ve kayıt sınırları</summary>
      <p>Binalar ve saatlik profiller sentetiktir; kat/kullanım dağılımı bu girdilerden modellenir. Saha ölçümü, canlı sensör veya ayrıntılı termal simülasyon değildir. Bina görünümü koordinatsız şemadır.</p>
      <p>%25 azaltım, değiştirilebilir bir senaryo hedefidir; garanti değildir. Aynı dönem ve alan için nihai enerji / toplam alan referansı kullanılır. ML sentetik simülatörü yaklaşık öğrenir; saha doğruluğu veya fizik motoruna üstünlüğü kanıtlanmadı. Bazı tahminlerde büyük fark oluşabilir.</p>
      <p>Bu arayüz barındırma planını veya kalıcı disk bağlantısını doğrulamaz. Kalıcı depolama bağlı değilse yeniden başlatma/yayın sonrasında hesap ve proje kayıtları kaybolabilir. Önemli girdi ve sonuçları dışa aktarın; bu dosyalar kullanıcı hesabının tam yedeği değildir.</p>
    </details>
    <details><summary>Geliştirme altyapısı</summary><p>React · TypeScript · Vite / Python · FastAPI / SciPy MILP / scikit-learn. Frontend Vercel, backend Render üzerinde yayımlanır. Özel enerji denklemleri ve bağlantı kısıtlı optimizasyon bu ayrımı gerektirir. Geliştirme ve hata gidermede VS Code içindeki Codex kullanıldı; AI Studio kullanıldığı iddia edilmez.</p></details>
  </section>;
}
