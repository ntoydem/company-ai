# SPEC 04 — Excel ve veri analiz motoru

## 1. İlke
Excel doküman RAG'ıyla çözülmez. Ayrı bir Excel Analysis modülü vardır (`backend/app/excel/`). Destek: `.xlsx .xlsm .csv`. **XLSM macro çalıştırılmaz.**

## 2. Teknolojiler
- openpyxl — inspection: worksheets, hücreler, formüller, named ranges, hidden sheets, formatlar. `data_only=True` ile cached değerler.
- DuckDB — gerçek hesap: filtre, join, aggregation, grouping, sıralama. Her sheet → tablo (`<file>__<sheet>`), read-only bağlantı, in-memory.
- Polars — karmaşık dönüşümler (gerekirse). Pandas yalnızca zorunluysa.

## 3. LLM matematik yapmaz
Kullanıcı "Ankara RES 2026 Q2 DSCR kaç?" dediğinde: LLM hangi dosya/sheet/kolonların gerektiğini ve hangi predefined fonksiyonun veya SQL'in çalışacağını belirler; hesabı DuckDB/Python yapar; LLM sonucu yorumlar. Final rakam modelden gelmez.

## 4. Güvenlik (karar — V0'da LLM Python yazmaz)
- LLM yalnızca **read-only SELECT** üretir. Whitelist: tek statement, `SELECT` ile başlar, `;` içermez, tablo adları bilinen listeden, `LIMIT` eklenir, `COPY/ATTACH/INSTALL/LOAD/PRAGMA` yasak. DuckDB `enable_external_access=false`.
- Predefined fonksiyonlar: `dscr(period)`, `outstanding_debt(as_of)`, `budget_variance(period, line)`, `capacity_factor(period)`, `production(period)` — parametreleri LLM doldurur, kodu biz yazdık.
- Timeout 10 s, satır limiti, yalnızca `seed_data/excel/` ve upload dizinine erişim. Arbitrary shell/Python yok. Tam sandbox V0 dışı; ileride `CalculationEngine` interface'i arkasına eklenir.

## 5. Kaynak gösterme
Her Excel cevabında dosya + sheet + range: `Financial_Model_2026.xlsx Debt!B21:F21`, `Covenant_Report.xlsx Q2_2026!D14:H14`.

## 6. Formül sınırı
openpyxl hesap motoru değildir. V0'da formül inspect edilir, cached sonuç kullanılır. Cached sonuç yoksa (dosya Excel dışı araçla kaydedilmişse) kullanıcıya "dosyanın Excel'de yeniden hesaplanıp kaydedilmesi gerekiyor" mesajı. Sunucu tarafı recalculation runtime'da yok; synthetic dosyalar için build adımında LibreOffice headless recalc (generator içinde). `CalculationEngine` interface'i (`CachedValueEngine` tek implementasyon) ileride LibreOffice/Graph eklenmesini engellemez.

## 7. Question router
`DOCUMENT_QUERY | DATA_QUERY | MIXED_QUERY | GENERAL_QUERY`.
- "Kredi sözleşmesindeki DSCR covenant nedir?" → DOCUMENT
- "2026 EBITDA variance hangi projede en yüksek?" → DATA
- "Üretim düşüşünün finansal etkisini ve teknik nedenini açıkla." → MIXED
- "DSCR ne demek?" → GENERAL (genel bilgi; şirket verisi kullanılmaz, cevapta bu belirtilir)
Belirsiz sorular ("güncel DSCR kaç?") → MIXED: covenant (belge) ve gerçekleşen (Excel) birlikte, iki kaynak türü.

## 8. Mixed query
Excel (Actual vs Budget) + belge (Maintenance Report, Production Report) → hesaplanan finansal etki + teknik sebep + kaynaklar. V0 implementasyonu basit (iki alt sorgu + birleştirme), mimari bunu destekler.

## 9. Demo workbook'ları (ledger'dan üretilir)
1. `Financial_Model_<year>.xlsx` — Inputs, Debt (schedule, outstanding), DSCR, Cashflow.
2. `Covenant_Report.xlsx` — çeyreklik sheet'ler (`Q1_2026`, `Q2_2026`…), test sonuçları.
3. `Budget_vs_Actual_<year>.xlsx` — aylık kalemler, variance.
4. `Monthly_Production_<year>.xlsx` — üretim, availability, capacity factor, rüzgar.
Named ranges ve en az bir hidden sheet (inspection testi için). Tüm rakamlar ledger ve belgelerle tutarlı.
