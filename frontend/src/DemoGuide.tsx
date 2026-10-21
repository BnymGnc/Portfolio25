export default function DemoGuide() {
  return <section className="demo-guide" aria-label="Prototip kapsamı ve demo rehberi">
    <h3>Demoyu deneyin</h3>
    <ol>
      <li>Proje ve bina seçin; senaryoda bütçe, hedef ve bağlantı sınırlarını inceleyin.</li>
      <li>Yatırım planını hesaplayın. Önce/sonra enerji, net maliyet ve kapasiteyi karşılaştırıp güncel sonucu dışa aktarın.</li>
      <li>Bina detaylarında “ML ve fizik sonucunu karşılaştır” ile uygun müdahaleye ait gerçek model tahminini deneyin. Kapsam dışındaki girdiye tahmin verilmez.</li>
    </ol>
    <details><summary>AI ve hesaplama sınırları</summary>
      <p>Yatırım planını fizik ve SciPy MILP belirler. Deneysel ML yalnız yıllık elektrik/toplam gazı tahmin eder; planı veya pik yükü belirlemez. Sentetik model saha doğruluğu kanıtı değildir; kapsam dışındaki girdiye tahmin verilmez. ComStock ayrı bir ABD simülasyon sağlayıcısıdır.</p>
      <p>LLM isteğe bağlı açıklama içindir; başarılı bağlantısı doğrulanmış bir özellik olarak sunulmaz. LLM hatası hesaplamayı engellemez.</p>
    </details>
    <details><summary>Veri ve kayıt sınırları</summary>
      <p>Binalar ve saatlik profiller sentetiktir; kat/kullanım dağılımı bu girdilerden modellenir. Saha ölçümü, canlı sensör veya ayrıntılı termal simülasyon değildir. Bina görünümü koordinatsız şemadır.</p>
      <p>%25 azaltım, değiştirilebilir bir senaryo hedefidir; garanti değildir. Aynı dönem ve alan için nihai enerji / toplam alan referansı kullanılır. ML sentetik simülatörü yaklaşık öğrenir; saha doğruluğu veya fizik motoruna üstünlüğü kanıtlanmadı. Bazı tahminlerde büyük fark oluşabilir.</p>
      <p>Bu arayüz barındırma planını veya kalıcı disk bağlantısını doğrulamaz. Kalıcı depolama bağlı değilse yeniden başlatma/yayın sonrasında hesap ve proje kayıtları kaybolabilir. Önemli girdi ve sonuçları dışa aktarın; bu dosyalar kullanıcı hesabının tam yedeği değildir.</p>
    </details>
  </section>;
}
