import {t} from './i18n';
export default function DemoGuide() {
  return <section className="demo-guide" aria-label="Prototip kapsamı ve demo rehberi">
    <h3>{t("Demoyu deneyin")}</h3>
    <p>{t("Kampüsün teknik işler ve enerji ekibi için soru: sınırlı bütçe hangi binalara ayrılmalı? Kurum yönetiminin kararını desteklemek için bütçe, enerji ve elektrik bağlantıları birlikte hesaplanır.")}</p>
    <ol>
      <li>“Temsilî kampüs” projesini seçin; binaları, bütçeyi, hedefi ve bağlantı sınırlarını inceleyin. Ofis/konut/otel ayrı projelerdir.</li>
      <li>{t("Yatırım planını hesaplayın. Önce/sonra enerji, net maliyet ve kapasiteyi karşılaştırın. “Karar özeti indir” ile paylaşılabilir hesap belgesini alın.")}</li>
      <li>{t("Bina detaylarında “ML ve fizik sonucunu karşılaştır” ile uygun müdahaleye ait gerçek model tahminini deneyin. Kapsam dışındaki girdiye tahmin verilmez.")}</li>
    </ol>
    <details><summary>{t("AI ve hesaplama sınırları")}</summary>
      <p>{t("Yatırım planını fizik ve SciPy MILP belirler. Deneysel ML yalnız yıllık elektrik/toplam gazı tahmin eder; planı veya pik yükü belirlemez. Sentetik model saha doğruluğu kanıtı değildir; kapsam dışındaki girdiye tahmin verilmez. ComStock ayrı bir ABD simülasyon sağlayıcısıdır.")}</p>
      <p>{t("LLM isteğe bağlı açıklama içindir; başarılı bağlantısı doğrulanmış bir özellik olarak sunulmaz. LLM hatası hesaplamayı engellemez.")}</p>
    </details>
    <details><summary>{t("Veri ve kayıt sınırları")}</summary>
      <p>{t("Binalar ve saatlik profiller sentetiktir; kat/kullanım dağılımı bu girdilerden modellenir. Saha ölçümü, canlı sensör veya ayrıntılı termal simülasyon değildir. Bina görünümü koordinatsız şemadır.")}</p>
      <p>%25 azaltım, değiştirilebilir bir senaryo hedefidir; garanti değildir. Aynı dönem ve alan için nihai enerji / toplam alan referansı kullanılır. ML sentetik simülatörü yaklaşık öğrenir; saha doğruluğu veya fizik motoruna üstünlüğü kanıtlanmadı. Bazı tahminlerde büyük fark oluşabilir.</p>
      <p>Bu arayüz barındırma planını veya kalıcı disk bağlantısını doğrulamaz. Kalıcı depolama bağlı değilse yeniden başlatma/yayın sonrasında hesap ve proje kayıtları kaybolabilir. Önemli girdi ve sonuçları dışa aktarın; bu dosyalar kullanıcı hesabının tam yedeği değildir.</p>
    </details>
  </section>;
}
