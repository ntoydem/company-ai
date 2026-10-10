# SPEC 05 — Synthetic demo veri ve değerlendirme sistemi

## 1. Klasör
```
seed_data/
  master/       company.yaml, ankara_res.yaml, izmir_res.yaml, fx_rates.yaml   ← truth ledger
  generator/    templates/, generate_documents.py, generate_excel.py, validate_ledger.py, validate_dataset.py, recalc.sh
  documents/    üretilen PDF'ler (git'e girmez, build ile üretilir)
  excel/        üretilen workbook'lar
  evaluation/   questions.json, results/
```

## 2. Üretim sırası — bozulmaz
1. Master folder/domain model → 2. İzmir master document inventory → 3. Ankara master document inventory → 4. Company-level inventory → 5. İzmir master timeline → 6. Ankara master timeline → 7. Kritik belge ilişkileri → 8. `USER_FACT` / `AI_ASSUMPTION` ayrımı ve Naci onayı → 9. Ledger validation → 10. **Ancak bundan sonra** belge dosyaları → 11. Excel dataset → 12. Golden QA dataset.
Master truth model onaylanmadan belge üretilmez.

## 3. Truth ledger YAML şeması (özet)
```yaml
meta: {demo_today: "2026-09-15", currency_note: "..."}
project:
  code: ANK_RES
  name: Ankara RES
  spv: {name: ..., shareholders: [{name:, share_pct:}]}
  stage: operation
  capacity_mw: {initial: {value:, tag: AI_ASSUMPTION}, current: {value:, tag:, source_doc: DOC-ANK-...}}
  turbines: {count:, model_generic:, tag:}
  timeline:            # her olay: {date:, doc: DOC-ID, tag:}
    development_start:
    licence:
    licence_amendment_02:
    financing_signed:
    financial_close:
    construction_start:
    commissioning:
    cod_expected_initial:
    cod_actual:
  finance:
    capex: {value:, currency: EUR, tag:}
    total_debt: {value:, currency: EUR, tag:}
    local_debt: ...
    eca_debt: ...
    interest: {base:, margin_pct:, tag:}
    tenor_years: {initial:, current:, changed_by: DOC-ANK-FIN-006}
    grace_months:
    dscr_covenant: {initial:, current:, changed_by:}
    repayment_profile:
    drawdowns: [{date:, amount:, currency:}]
    outstanding_debt_as_of_demo_today:
    covenant_tests: [{period: Q2_2026, dscr:, result: pass|fail}]
  operations:
    monthly_production: [{month: 2026-06, mwh:, availability_pct:, capacity_factor_pct:}]
    budget_vs_actual: [...]
    incidents: [{date:, type:, doc:}]
documents:            # master document inventory
  - id: DOC-ANK-FIN-001
    department: finance
    subdepartment: null
    folder: finance
    type: Facility Agreement
    name: ...
    document_date:
    effective_date:
    version: EXECUTED
    status: superseded
    parties: [...]
    key_facts: {dscr_covenant: 1.25, tenor_years: 12}   # örnek yapı; değerler ledger onayına tabidir
    supersedes: null
    superseded_by: DOC-ANK-FIN-006
    related: [DOC-ANK-...]
    source_type: digital_pdf | scanned_pdf
    language: en | tr
    tag: USER_FACT | AI_ASSUMPTION
```
İzmir için lisans sonrası tüm alanlar `null`; `ced_status: ongoing`, `permits_completed: [...]`, `pending_steps: [...]`, `latest_event: {...}`.

## 4. Demo veri kuralları
- Gerçek özel şirket, çalışan, banka ilişkisi, sözleşme YOK. Kurgusal jenerik isimler (Adım 5, 09.10.2026 — güncel liste `company.yaml`'ın `name_whitelist`'iyle birebir eşleşir, tek kaynak odur): XYZ Enerji A.Ş. (holding, 7 SPV'nin %100 ortağı), Karatepe RES Enerji Üretim A.Ş., Kızılova RES Enerji Üretim A.Ş., Yeşilova RES Enerji Üretim A.Ş., Boztepe RES Enerji Üretim A.Ş., Güneşalan GES Enerji Üretim A.Ş., Akyar GES Enerji Üretim A.Ş., Demirci RES Enerji Üretim A.Ş. (7 SPV), RST Turbines GmbH, JKL İnşaat A.Ş., MNO Teknik Danışmanlık Ltd., PQR Bank, VWX Export Credit Agency, STU Sigorta, KLM Hukuk Bürosu. GHI Yatırım A.Ş. yalnızca tarihsel referans olarak kalır (Karatepe'nin eski %20 ortağı, bugün tamamen elden çıkarılmış).
- Gerçek kamu kurumu adları süreç bağlamında kullanılabilir; gerçek kişi/imza/belge no/QR/barkod/kimlik verisi kullanılmaz; resmi şablon birebir kopyalanmaz.
- Her belgede: `DEMO / FICTIONAL DOCUMENT FOR DEMONSTRATION PURPOSES ONLY`; sözleşmelerde ayrıca `NOT A REAL CONTRACT`.
- Belge dili: finansman/ECA/EPC belgeleri İngilizce; ÇED, ruhsat, lisans, kurum yazışmaları, board resolution Türkçe.

## 5. Belge tasarımı
Belgeler txt gibi görünmez. Uygun belgelerde: kapak, başlık, proje, tarih, belge no, versiyon, durum, revision history, prepared/reviewed/approved by (kurgusal roller, isim yok), tablolar, sayfa numarası, footer, ek, imza yer tutucuları. Markdown/HTML şablon → WeasyPrint. Görüntü PDF'ler: üretilen PDF → raster (200 dpi) → PDF (ocrmypdf testi için).

## 6. Dağılım (Phase 13, ~70 belge, ≤ 80)
Ankara ≈ 45: Development/lisans 6, Finans 14 (zincir dahil), EPC/Construction 10, Operation 10, Hukuk 3, Mali/İdari 2. İzmir ≈ 15: Development 8, Hukuk 4, Finans 0 (finansman yok!), Mali/İdari 3. Company-level ≈ 10: board/shareholder resolutions, budget, insurance, management report. 8–10 tanesi görüntü PDF.
Adım 0 seti (2 belge, geçici rakamlar) ve Adım 3 seti (15 belge, ledger'dan): PHASES.md'de.

## 7. Controlled changes
Kapasite (Licence → Amendment 02), DSCR + tenor (Facility EXECUTED → Amendment 01), expected COD (Change Order), … Değerler ledger'da; sonraki belgeler yeni değeri kullanır.

## 8. Proje karıştırma testi
Yasak hatalar: Ankara lisans/kapasite/finansman/COD/operasyon bilgisini İzmir'e; İzmir ÇED durumunu Ankara'ya aktarmak. Her proje kendi knowledge scope'una sahiptir.

## 9. Golden evaluation dataset — `evaluation/questions.json`
```json
{
  "id": "ANK-FIN-001",
  "category": "document | temporal | data | mixed | isolation | hallucination | authorization",
  "question": "Ankara RES'in güncel minimum DSCR covenant'ı nedir?",
  "expected_answer": "<ledger>",
  "expected_answer_aliases": ["1,20x", "1.2"],
  "expected_project": "Ankara RES",
  "expected_department": "finance",
  "required_sources": ["Facility Agreement Amendment 01"],
  "forbidden_sources": ["İzmir RES"],
  "ask_as_user": "finans",
  "expect_no_answer": false
}
```
`hallucination` kategorisinde `expect_no_answer: true`. `authorization` kategorisinde `ask_as_user: enerji` ve `expect_no_answer: true`.

Minimum sorular — İzmir: hangi aşamada; ÇED durumu; ÇED tamamlandı mı; yapı ruhsatı var mı; lisans alındı mı; inşaata başlandı mı; hangi adımlar tamamlandı; hangi kritik adımlar bekliyor; en son gelişme.
Ankara: development başlangıcı; lisans tarihi; güncel kapasite; ilk lisans kapasitesi; capacity amendment tarihi; financial close; toplam finansman; local debt; ECA debt; güncel faiz/margin; güncel DSCR covenant; ilk DSCR covenant; güncel Facility Agreement; amendment sayısı; EPC bedeli; güncel EPC sözleşmesi; COD; kaçıncı operating year; son covenant testi; güncel outstanding debt.
Hallucination: "İzmir RES'in COD tarihi nedir?", "Ankara RES'in ikinci EPC yüklenicisi kim?", "Bursa RES'in kapasitesi nedir?".

## 10. Test kategorileri (pytest + eval)
Authentication; Authorization (liste/API/AI üçünde de erişim yok); Project Isolation; Temporal Reasoning; Document Retrieval; Hallucination; Excel (bilinen hesaplar doğru); Citations.

## 11. Domain consistency checks (`validate_dataset.py`)
Chronology (kaba sıra); Finance (loan, interest, tenor, repayment, balance, DSCR tutarlı — Excel ile belge aynı); Technical (kapasite, üretim, türbin sayısı); Legal (amendment ↔ related contracts); Version (güncel belge tek ve doğru); Project Isolation (İzmir'de finansman/COD alanı dolu mu?); Demo Safety (gerçek isim/regex taraması: "A.Ş." önündeki isimler whitelist'te mi).
