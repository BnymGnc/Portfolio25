# Güncel belge dizini

| İhtiyaç | Belge |
| --- | --- |
| Kampüs odağı, Climathon ölçütleri ve öneriler | [Ürün değerlendirmesi](product-review.md) |
| Isıtma elektrifikasyonu, karbon ve uygulanabilirlik gerekçesi | [Ürün konumlandırması](electrification-positioning.md) |
| Teslim için gözden geçirilecek kısa içerik | [PDR taslağı](pdr-draft.md) |
| Görev 3 formuna uygun anlatım ve kısa gösterim | [Teslim metni](task3-submission.md) |
| Render/Vercel, Origin reddi ve ortam | [Yayın rehberi](deploy-render-vercel.md) |
| Render Free + Neon, migration ve eski hesapta 401 | [PostgreSQL geçişi](postgres-deployment.md) |
| Gerçek HTTPS kabul kontrolü ve sınırlar | [Canlı rapor](live-deployment-report.md) |
| API / veri / fizik varsayımları | [API](api-inventory.md), [veri sözleşmesi](data-contract.md), [varsayımlar](assumptions.md), [elle hesap](calculation-example.md) |
| Proje/kayıt sahipliği ve eski dosyaların aktarımı | [Hesap ve saklama](auth-and-storage.md) |
| Sentetik pilot | [Kayseri pilotu](pilot-kayseri.md) |
| Modelin ne öğrendiği ve hata metrikleri | [Sentetik model](model-card-synthetic.md), [ComStock modeli](model-card.md) |
| Mevcut LLM akışlarının sınırları | [AI mimarisi](ai-architecture.md) |
| Kapsam ve sonraki araştırma | [Ürün kapsamı](product-spec.md), [yol haritası](product-roadmap.md) |
| Temizlik, korunanlar ve Git dışı yerel arşiv | [Temizlik kaydı](repository-cleanup.md) |

`system-audit.md` önceki kaynak incelemesi, `data-audit.md` eski dışa aktarım tutarsızlığı incelemesidir; güncel hata listesi değildir. İkisi hesap doğruluğunun nedenleri için korundu. `sample-campus.json` ve `sample-calculation.json` kişisel kayıt değil, yeniden üretilebilir belgelenmiş sentetik örneklerdir; uygulama bunları hardcoded sonuç olarak okumaz.

Tekrarlanan aşama raporları ve eski demo metinleri Git çalışma ağacından çıkarıldı. Yerel byte kopyaları `artifacts/repository-cleanup/` altında Git dışındadır. Önceki [c41071b belge ağacı](https://github.com/BnymGnc/Portfolio25/tree/c41071b/docs) da geçmişi korur. Kaldırılan raporlara kalan bağlantılar bu sabit Git commit'ine yönelir; yeni çalıştırma talimatı olarak kullanılmamalıdır.
