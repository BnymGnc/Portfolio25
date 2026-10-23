"""Portable decision evidence from one guarded snapshot. No LLM, external assets or scripts."""
from html import escape

from models import CampusResponse


def number(value, digits=1):
    if value is None:
        return '—'
    return f'{value:,.{digits}f}'.replace(',', '_').replace('.', ',').replace('_', '.')


def solver_label(result):
    if result.status == 'optimal' and result.solver.optimality_proven:
        return 'Optimum çözüm bulundu'
    if result.status == 'feasible_limit' and result.solver.status_code != 1:
        return 'Uygun çözüm bulundu; optimum kanıtlanmadı'
    return {'feasible_limit': 'Süre sınırında uygun çözüm bulundu',
            'limit_no_solution': 'Süre sınırında çözüm bulunamadı',
            'infeasible': 'Çözüm bulunamadı', 'failed': 'Hesap tamamlanamadı'}.get(result.status, 'Optimalite kanıtlanmadı')


INTERVENTIONS = {'roof': 'Çatı yalıtımı', 'insulation': 'Kabuk yalıtımı', 'lighting': 'Aydınlatma',
                 'schedule': 'HVAC çalışma programı', 'heat_pump': 'Isı pompası'}
PACKAGES = {'none': 'Yeni ısıtma müdahalesi yok', 'insulation': 'Kabuk yalıtımı',
            'heat_pump': 'Isı pompası', 'combined': 'Kabuk + ısı pompası'}
STATES = {'applied': 'uygulanmış', 'mandatory': 'zorunlu', 'candidate': 'adaydan seçildi', 'excluded': 'dışarıda'}


def package_label(package):
    if package.interventions:
        return '; '.join(f'{INTERVENTIONS.get(d.kind, d.kind)} ({STATES[d.state]})'
                         for d in package.interventions if d.state != 'excluded') or 'Yeni müdahale yok'
    names = [] if package.package == 'none' and package.spatial_interventions else [PACKAGES[package.package]]
    names.extend(INTERVENTIONS.get(k, k) for k in package.spatial_interventions)
    return '; '.join(names)


def render_brief(snapshot: CampusResponse, metadata: dict) -> str:
    campus, result = snapshot.campus, snapshot.calculation
    if result is None:
        raise ValueError('Karar özeti güncel hesap gerektirir.')
    before, after = result.baseline, result.after
    esc = lambda value: escape(str(value), quote=True)
    source_notice = ('Sentetik örnek proje — sonuçlar model varsayımlarına dayanır. Saha ölçümü değildir.'
                     if campus.provenance.kind == 'synthetic' else
                     'Bina girdilerinin veri türü: ' + {'measured': 'ölçülmüş', 'external_simulation': 'harici simülasyon','user_estimate':'kullanıcı girişi; alan kaynakları ayrıca kayıtlı','unspecified':'belirtilmemiş'}.get(campus.provenance.kind,'belirtilmemiş') + '. Saatlik profil sentetiktir; dönüşüm varsayımları ayrıca doğrulanmalıdır.')
    rows = ''
    indicators = [('Toplam nihai enerji', before.total_energy_kwh_year, after.total_energy_kwh_year if after else None, 'kWh/yıl'),
                  ('Enerji yoğunluğu', before.intensity_kwh_m2_year, after.intensity_kwh_m2_year if after else None, 'kWh/m²-yıl'),
                  ('Elektrik', before.electricity_kwh_year, after.electricity_kwh_year if after else None, 'kWh/yıl'),
                  ('Toplam doğalgaz', before.heating_kwh_year + before.non_heating_gas_kwh_year,
                   after.heating_kwh_year + after.non_heating_gas_kwh_year if after else None, 'kWh/yıl'),
                  ('İşletme maliyeti', before.operating_cost_try_year, after.operating_cost_try_year if after else None, 'TL/yıl')]
    indicators.append(('Modellenen işletme emisyonu', before.emissions_kg_year,
                       after.emissions_kg_year if after else None, 'kg CO₂e/yıl'))
    for label, initial, final, unit in indicators:
        rows += f'<tr><th scope="row">{label}</th><td>{number(initial)}</td><td>{number(final)}</td><td>{unit}</td></tr>'
    plans = ''.join(f'<tr><th scope="row">{esc(p.building_name)}</th><td>{esc(package_label(p))}</td>'
                    f'<td>{number(p.investment_try, 0)} TL</td><td>{number(p.energy_savings_kwh_year)} kWh/yıl</td></tr>'
                    for p in result.selected_packages)
    # All building and physical group checks are retained, never the sum of building peaks.
    checks = ''.join(f'<tr><th scope="row">{esc(c.name)}</th><td>{"Bina" if c.kind == "building" else "Bağlantı grubu"}</td>'
                     f'<td>{number(c.peak_kw)} / {number(c.limit_kw)} kW</td><td>{c.violation_hours} saat</td></tr>'
                     for c in (after or before).capacity_checks)
    methods = ''
    if result.decision_evidence:
        for key, name in [('ratio', 'Tasarruf / yatırım oranı'), ('without_grid', 'Elektrik kısıtları olmadan'), ('grid', 'GRID kısıtlarıyla')]:
            method = result.decision_evidence['methods'][key]
            v = method.get('evaluation')
            if v:
                methods += f'<tr><th scope="row">{name}</th><td>{number(v["investment_try"], 0)} TL</td><td>{number(v["energy_savings_kwh_year"])} kWh/yıl</td><td>{"İhlal yok" if v["capacity_met"] else "Kapasite ihlali var"}</td></tr>'
            else:
                methods += f'<tr><th scope="row">{name}</th><td colspan="3">Plan yok · {esc(method["status"])}</td></tr>'
    limits = ''.join(f'<li>{esc(w)}</li>' for w in result.warnings)
    assumptions = ''.join(f'<tr><th scope="row">{esc(b.name)}</th><td>{number(b.retrofit.boiler_efficiency * 100)}%</td>'
                          f'<td>{number(b.retrofit.insulation_relevant_heat_fraction * 100)}% / {number(b.retrofit.insulation_reduction_fraction * 100)}%</td>'
                          f'<td>{number(b.retrofit.heat_pump_scop, 2)}</td><td>{esc(b.retrofit.reference_date)} · {esc(b.retrofit.source)}</td></tr>' for b in campus.buildings)
    finding = (f'<p><strong>{number(result.investment_try, 0)} TL yatırım</strong> · kalan bütçe {number(campus.scenario.budget_try - result.investment_try, 0)} TL.</p>'
               f'<p>Yıllık nihai enerji farkı {number(result.energy_savings_kwh_year)} kWh (%{number(result.energy_savings_pct, 2)}); '
               f'ek bakım sonrası net ekonomik tasarruf {number(result.net_savings_try_year, 0)} TL/yıl.</p>'
               f'<p>Hedef %{number(campus.scenario.savings_target_pct)}: {"karşılanıyor" if result.target_met else "karşılanmıyor"}. '
               f'Modellenen kapasite: {"sınırlar içinde" if not any(c.violation_hours for c in after.capacity_checks) else "ihlal var"}.</p>') if after else '<p>Bu hesap için uygulanabilir yatırım planı bulunmadı; sonraki durum veya tasarruf üretilmedi.</p>'
    return f'''<!doctype html><html lang="tr"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta http-equiv="Content-Security-Policy" content="default-src 'none'; style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'">
<title>{esc(campus.name)} · Portfolio25-GRID karar özeti</title><style>
*{{box-sizing:border-box}}body{{font:15px/1.65 system-ui,sans-serif;color:#172b24;background:#f4f7f5;margin:0}}main{{max-width:960px;margin:auto;background:white;padding:36px}}h1{{font-size:28px;line-height:1.25}}h2{{font-size:20px;margin-top:32px}}p,li,td,th{{overflow-wrap:anywhere}}.label{{color:#17634b;font-weight:700}}.notice{{padding:16px;border-left:4px solid #9a681b;background:#faf0d9}}.table-scroll{{overflow:auto}}table{{border-collapse:collapse;width:100%;font-size:13px}}td,th{{text-align:left;padding:10px;border-bottom:1px solid #d8e2dc;vertical-align:top}}thead{{background:#eaf1ed}}code{{word-break:break-all}}footer{{margin-top:32px;font-size:12px;color:#52665c}}@media(max-width:600px){{main{{padding:20px}}table{{min-width:600px}}}}@media print{{body{{background:white}}main{{padding:0;max-width:none}}.table-scroll{{overflow:visible}}table{{min-width:0;font-size:10px}}thead{{display:table-header-group}}tr{{break-inside:avoid}}h2{{break-after:avoid}}}}
</style></head><body><main><p class="label">Portfolio25-GRID · Karar özeti</p><h1>{esc(campus.name)}</h1>
<p class="notice">{esc(source_notice)} Sonuçlar gerçekleşmiş tasarruf değildir. Hedef bir senaryo girdisidir; garanti değildir.</p>
<p>{len(campus.buildings)} bina · {number(before.area_m2, 0)} m² · {campus.profile_settings.year} · {esc(campus.profile_settings.timezone)} · Mod {result.mode}</p>
<h2>Yatırım kararı</h2><p>{esc(solver_label(result))}</p>{finding}<p>{esc(result.message)}</p>
<h2>Aynı bina, alan ve yıllık dönem için etki</h2><p>Nihai enerji = elektrik + yakıt enerjisi. Enerji yoğunluğu = toplam nihai enerji / toplam alan; bina yüzdelerinin ortalaması değildir.</p>
<div class="table-scroll"><table><thead><tr><th>Gösterge</th><th>Başlangıç</th><th>Senaryo</th><th>Birim</th></tr></thead><tbody>{rows}</tbody></table></div>
<h2>Seçilen müdahaleler</h2><div class="table-scroll"><table><thead><tr><th>Bina</th><th>Müdahale / karar durumu</th><th>Yatırım</th><th>Tasarruf</th></tr></thead><tbody>{plans or '<tr><td colspan="4">Plan bulunmadı.</td></tr>'}</tbody></table></div>
<h2>Elektrik bağlantı denetimi</h2><p>Eşzamanlı saatler değerlendirilir. Bina pikleri toplanarak ortak pik üretilmez; bağımsız gruplara ortak trafo sınırı uygulanmaz. {"Senaryo" if after else "Başlangıç"} profili:</p>
<div class="table-scroll"><table><thead><tr><th>Bağlantı</th><th>Tür</th><th>Pik / sınır</th><th>Aşım</th></tr></thead><tbody>{checks}</tbody></table></div>
<h2>Aynı aday evrenindeki yöntemler</h2><div class="table-scroll"><table><thead><tr><th>Yöntem</th><th>Yatırım</th><th>Tasarruf</th><th>Fiziksel denetim</th></tr></thead><tbody>{methods or '<tr><td colspan="4">Karşılaştırma hesaplanmadı.</td></tr>'}</tbody></table></div><p>GRID'siz plan da sınırı karşılayabilir; bu tablo üstünlük garantisi değildir. Oran yöntemi optimum iddia etmez.</p>
<h2>Varsayımlar ve doğrulama ihtiyacı</h2><p>Elektrik {number(campus.scenario.electricity_price_try_kwh, 2)} TL/kWh · doğalgaz {number(campus.scenario.heating_price_try_kwh, 2)} TL/kWh. {esc(campus.scenario.price_basis.reference_date)} · {esc(campus.scenario.price_basis.source)}</p>
<div class="table-scroll"><table><thead><tr><th>Bina</th><th>Kazan verimi</th><th>İlgili ısı / azaltım</th><th>SCOP</th><th>Tarih / kaynak</th></tr></thead><tbody>{assumptions}</tbody></table></div>
<p>Kaynak: {esc(campus.provenance.source)} · profil: {esc(campus.profile_settings.source)}</p><p>Fizik ve MILP planı belirler. ML yıllık tüketim için deneysel karşılaştırmadır; bu rapor ML veya LLM tahminiyle karar üretmez. Gerçek Task 1 tüketim baseline'ı henüz sağlanmadı. Gerçek pilot için fatura, ısıtma ayrımı, ekipman ve bağlantı belgeleriyle doğrulama gerekir.</p>
<p>Basit geri ödeme: {number(result.simple_payback_years)} yıl. Yalnız pozitif yıllık net tasarrufta hesaplanır; iskonto, ömür, finansman ve fiyat değişimini içermez. Duyarlılıklar olasılık veya güven aralığı değildir; ayrıntılar sonuç JSON/CSV'sindedir.</p><ul>{limits}</ul>
<footer><p>Bu dosyayı tarayıcıda açıp Yazdır → PDF olarak kaydet ile paylaşabilirsiniz. Hesap anının kopyasıdır; sonraki girdi değişiklikleri bu dosyayı güncellemez.</p><p>Proje <code>{esc(campus.id)}</code> · revizyon {campus.revision} · hesap <code>{esc(result.calculation_id)}</code> · motor {esc(result.engine_version)} · girdi özeti <code>{esc(result.input_hash)}</code> · oluşturma {esc(metadata['exported_at_utc'])}</p></footer></main></body></html>'''
