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

`sample-campus.json` ve `sample-calculation.json` kişisel kayıt değil, testlerde de kullanılan sentetik sözleşme örnekleridir. Uygulama bunları sabit hesap sonucu olarak okumaz.

Eski sistem/veri incelemeleri ve temizlik günlüğü güncel talimatlarla karışmaması için çalışma ağacından çıkarıldı. [Önceki belge ağacı](https://github.com/BnymGnc/Portfolio25/tree/52a4e6288876c2e017aba31db9a18b143657fd38/docs) geçmişi korur. Yerel kopyalar Git dışındaki `artifacts/ui-review/retired/` içindedir. Çalışan kaynaklar, testler, model artefaktları ve yeniden üretim araçları korunur.
