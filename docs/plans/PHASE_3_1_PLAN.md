# Phase 3.1 — 15 demo belge + seed/reset: Implementation Plan

## Bağlam ve tespitler

ADIM 3'ün ilk fazı. Kapsam (`docs/PHASES.md` 3.1): `seed_data/generator/` şablonlar + WeasyPrint; 15 belge (Ankara 10, İzmir 4, company 1); dil karışık (finans/EPC EN, mevzuat/board TR); rakam/tarih/isim yalnızca ledger'dan, prose LLM ile batch (`AI_ASSUMPTION`); `scripts/seed_demo.sh` (kullanıcılar + projeler + belgeler + metadata) ve `scripts/reset_demo.sh`; Adım 0'ın geçici 2 belgesi kaldırılır. Kabul: `make seed` → 15 belge `ready`, metadata doğru, zincir bağlı, "güncel" belge tek; belgeler gerçekçi görünür; gerçek isim yok (validator); `make reset-demo` + `make seed` tekrar çalışır.

Ön koşul sağlandı: ledger onayı commit'i (`142d132`, 23.09.2026) — 269/269 `USER_FACT` (SPEC_05 §2 madde 8–10).

Okunanlar: `docs/PHASES.md` (3.1, 3.2, 5.1, 5.4), `SPEC_05` §1–§8/§11, `SPEC_03` §2–§10, `SPEC_02` §1–§4/§11, `DOMAIN_MODEL` §3/§6/§7, ADR-003/004/005/006/012/013/021, `docs/reports/PHASE_2_1_REPORT.md` §7/§10.8; kod: `seed_data/t0/{generate.py,upload.sh,templates/document.html}`, `seed_data/generator/{ledger_schema,validate_ledger}.py`, `seed_data/master/*.yaml`, `app/api/documents.py`, `app/repositories/document_repo.py`, `app/models/document.py`, `app/services/{document_store,version_chain,*_seed}.py`, `app/cli.py`, `ocr-worker/worker/{main,pipeline,ocr}.py`, `tests/{t0_fixtures,test_ask,test_search_query,live/test_t0_live}.py`, `Makefile`, `scripts/`, `infra/docker-compose.yml`, `backend/Dockerfile`, `.gitignore`.

Planı şekillendiren tespitler:

- **T1 — Ledger onaylı ve değişmez; 3.1 onu olduğu gibi uygular.** Keşifte "belirsiz" görünen birkaç nokta ledger'da zaten kararlaştırılmış: lisans tadili (`DOC-ANK-DEV-002`) lisansı `supersedes` etmez, `related` ile bağlıdır (tadil lisansı yürürlükten kaldırmaz; ikisi de güncel); `DOC-ANK-EPC-001` `status: amended` (Change Order 5.1'de); `DOC-ANK-FIN-001`/`FIN-007` `effective_date: null` (`version_chain` `document_date`'e düşer; DRAFT `status: draft` olduğu için güncel sayılmaz). Bunlar SORU değil.
- **T2 — Zincirde 3.1'de üretilmeyen halkalar var.** `FIN-004.supersedes = FIN-003` ama V01/V02 5.1'de (SORU 5 cevabı). DB'de zincir *seed edilen* belgeler arasında kurulur: seeder `supersedes`'i, seed edilmiş ilk ataya ulaşana kadar yürür (DRAFT → EXECUTED → AMD01 → AMD02, doğrusal, tek "güncel"). 5.1'de V01/V02 gelince zincir tam hale gelir; seeder aynı algoritmayla yeniden bağlar (varsa dokunmaz kuralı yalnızca satırı korur, zincir bağlantısı idempotent olarak yeniden hesaplanır — bkz. §4.3).
- **T3 — Upload API seed için yetersiz; seed doğrudan DB yazar.** `POST /api/documents/upload` `department/subdepartment/project_id/confidentiality/tags/related` almıyor, `version` int. Seed `app.cli seed-demo-documents` ile `DocumentStore.store()` + `create_with_job()` (genişletilmiş) üzerinden yazar, `ingestion_jobs` kuyruğuna girer, ocr-worker `ready`'ye taşır. API'yi 3.2/3.3 kapsamı öne çekmeden değiştirmiyoruz.
- **T4 — İdempotency için belgede ledger kimliği yok.** `documents` tablosunda dış kimlik kolonu yok; başlık eşleştirmesi kırılgan, `tags` kötüye kullanım. Yeni kolon `external_ref` (migration `0004`) — `DOC-ANK-FIN-004` gibi; seed "varsa dokunma" anahtarı, Phase 4.1 runner'ın `required_sources` eşleştirmesi için de temiz kimlik (SORU 3).
- **T5 — ADR-013 sınırı: backend generator'ı import etmez; generator da `app.*` import etmez (2.1 konvansiyonu).** Köprü: generator `seed_data/documents/manifest.json` + PDF'leri üretir; `app.cli seed-demo-documents` yalnızca manifest'i okur. `./seed_data:/app/seed_data` mount'u sayesinde container içinden erişilebilir; klasör gitignore'da.
- **T6 — Prose'un `make seed` sırasında LLM'den üretilmesi prod'u (5.4: `git clone` → `make up` → `make seed`) API anahtarına ve ağa bağımlı kılar, üstelik tekrarlanamaz.** Karar önerisi: prose **bir kez** üretilir (`make prose`), `seed_data/generator/prose/<DOC-ID>.yaml` olarak **commit edilir** (`tag: AI_ASSUMPTION`); `generate_documents.py` deterministiktir ve LLM çağırmaz (SORU 1).
- **T7 — Rakam sızıntısına karşı yapısal önlem.** LLM'e facts değil **placeholder** verilir (`{{capex}}`, `{{cod_actual}}`, `{{spv_name}}`…); prose içinde rakam/tarih/isim yazması yasaktır ve `validate_documents.py` bunu denetler (prose'da 3+ haneli sayı, para birimi, `A.Ş./Ltd./Bank/…` kalıbı → hata). Değerler şablon aşamasında ledger'dan biçimlenerek (`1.250.000 EUR`, `15.03.2025`, `1,20x`) yerleştirilir. "Rakam/tarih/isim yalnızca ledger'dan" kuralı böylece kod tarafından garanti edilir, LLM disiplinine bırakılmaz.
- **T8 — T0 şablonu iyi bir çekirdek, ama tek-tip.** `templates/document.html`: A4, DejaVu, DEMO filigranı, footer sayfa no, kapak + meta; ama `lang="en"`, banner "AGREEMENT", tablo/liste/imza bloğu/revizyon geçmişi yok. Bölüm-başına-sayfa-kırımı (deterministik sayfa numaraları) korunur; üstüne blok kütüphanesi ve üç aile şablonu gelir (§2).
- **T9 — T0'a bağlı testler taşınmalı.** `tests/t0_fixtures.py`, `test_ask.py::test_sources_come_from_citations_with_page_and_chain`, `test_search_query.py` (3 test), `tests/live/test_t0_live.py` T0 PDF'lerine ve T0 rakamlarına (1,25x/1,20x, sayfa 6/3) bağlı. Ledger'dan üretilen EXECUTED/AMD01'e taşınır; beklenen değerler ledger YAML'ından ve sayfa numaraları manifest `page_map`'inden okunur — testlerde rakam tekrarı yok.
- **T10 — ocr-worker sıralı çalışır; 4 taranmış belge OCR süresini belirler.** Dijital PDF birkaç saniye, taranmış sayfa başına Tesseract (tur+eng). 15 belge (~70 sayfa, ~10'u taranmış) için `seed_demo.sh` "tümü `ready`" beklemesi 10 dk bütçeli.
- **T11 — `data/documents/` altında 129 yetim klasör var.** `reset_demo.sh` hem DB satırlarını hem dosyaları temizlemeli; yalnızca `documents/*` kapsamı (SORU 2).
- **T12 — Hukuk departmanının 15 belgede belgesi yok.** 5.1'e kadar `hukuk` kullanıcısı yalnızca "bilgi bulamadım" alır; kabul kriteri etkilenmez, raporda not (SORU 5).

---

## 1. Üretim hattı — `seed_data/generator/`

```
seed_data/generator/
  ledger_schema.py, validate_ledger.py        (2.1, değişmez)
  facts.py            ledger → belge başına biçimlenmiş facts sözlüğü (placeholder adı → metin)
  generate_prose.py   LLM batch (bir kez): DOC-ID başına prose YAML   [make prose]
  generate_documents.py  prose + facts + şablon → PDF + manifest.json (deterministik)  [make seed içinde]
  validate_documents.py  prose ve üretilen PDF'lerin denetimi (§5)
  templates/          base.html, agreement.html, letter.html, report.html, blocks/*.html, styles.css
  prose/              <DOC-ID>.yaml (commit edilir, tag: AI_ASSUMPTION)
seed_data/documents/  (gitignore) <YYYY-MM-DD_PROJECT_DOCUMENT_VERSION_STATUS>.pdf, *.digital.pdf, manifest.json
```

### 1.1 `facts.py` — ledger'dan placeholder sözlüğü
Her belge için `key_facts` + belge tipine göre sabit ek alanlar (ör. Facility: `spv_name, borrower, lenders, capex, total_debt, local_debt, eca_debt, interest_base, margin_pct, tenor_initial, grace_months, dscr_initial, repayment_profile, financing_signed, financial_close`; AMD01: `dscr_current, tenor_current, effective_date`; Licence: `capacity_initial, licence_date`; COD cert: `cod_actual, capacity_current, epc_contractor`; Covenant report: son 4 çeyrek `covenant_tests`, `outstanding_debt`; Üretim raporu: son 12 ay `monthly_production`; İzmir: `target_capacity, ced_status, permits_completed, pending_steps, latest_event`). Biçimleme tek yerde: EUR `50.400.000 EUR`, TR tarih `15.03.2025`, EN tarih `15 March 2025`, oran `1,20x`/`1.20x` (dile göre), yüzde `%3,25`/`3.25%`. Manifest'e `facts_used` yazılır (test/validator için).

### 1.2 `generate_prose.py` — LLM batch (SORU 1)
- `openai` SDK doğrudan (`LLM_BASE_URL/LLM_API_KEY`, model `PROSE_MODEL` env → varsayılan `LLM_MODEL_ANSWER`); `app.services.llm` **import edilmez** (T5 konvansiyonu). Ücretsiz katman: çağrılar 13 sn aralıklı, 503/429'da 65 sn bekle-yeniden dene (T0 canlı testleriyle aynı disiplin).
- Belge başına **tek** çağrı: sistem promptu (rol: sözleşme/rapor/resmi yazı yazarı; dil `language`; DEMO belge; **rakam, tarih, para tutarı, şirket/kişi adı YAZMA**, yalnızca verilen placeholder'ları kullan; başlıklar ve bölüm sırası verilir) → JSON: `{sections: [{heading, paragraphs[], table?: {columns, rows (placeholder'lı)}}], revision_history[], signature_roles[]}`. Çıktı `prose/<DOC-ID>.yaml`'a `{doc_id, model, generated_at, tag: AI_ASSUMPTION, sections: …}` olarak yazılır.
- `--only DOC-ID` ve `--force` ile tek belge yeniden üretilir; mevcut dosya varsa atlanır (idempotent). Çıktı `validate_documents.py --prose` ile denetlenir (§5); hata varsa dosya `*.rejected.yaml` olarak bırakılır, commit'e girmez.
- Sayfa hedefleri (prompt'a verilir): Facility EXECUTED 10–12 bölüm (≈12 sayfa), DRAFT aynı iskelet + "DRAFT — subject to negotiation" kutuları (≈10), AMD01/AMD02 4–5, EPC 8–10, COD sertifikası 2, Covenant Report 3–4, Üretim Raporu 3, Lisans 2–3, Lisans Tadili 2, Önlisans 2, Arazi raporu 3, ÇED yazısı 2, Teknik rapor 5–6, Board Resolution 2. Toplam ≈ 70 sayfa.

### 1.3 `generate_documents.py` — deterministik render
- Girdi: ledger (validator temiz olmalı — önce çalıştırılır), `prose/*.yaml`, `facts.py`. Her `generate_in_phase: "3.1"` belge için şablon ailesi seçilir (`type` → `agreement | letter | report`), placeholder'lar facts ile değiştirilir (bilinmeyen placeholder → hata), Jinja2 (autoescape) + WeasyPrint → `seed_data/documents/<SPEC_02 §3 adı>.pdf`.
- `source_type: scanned_pdf` olanlar: dijital PDF `*.digital.pdf` olarak saklanır, seed edilen dosya rasterize kopyadır: PyMuPDF 200 dpi → JPEG (q=80) → PDF, sayfa başına ±0,4° rastgele (tohumlu, deterministik) döndürme — worker'ın `--deskew/--rotate-pages`'ini gerçekçi test eder; metin katmanı yok → OCR zorunlu.
- Bölüm-başına-sayfa-kırımı korunur; render sonrası PyMuPDF ile `page_map` çıkarılır (`{section_heading: page_number}` + her `facts_used` anahtarının ilk geçtiği sayfa) ve manifest'e yazılır.
- `manifest.json`: belge başına `{external_ref, file, digital_file?, title, document_type, department, subdepartment, project_code, counterparty, document_date, effective_date, status, confidentiality, language, version_label, chain_position, supersedes_ref, related_refs, tags, page_count, page_map, facts_used, sha256}` + `{generated_at, ledger_sha256, demo_today}`.
- Dosya adı SPEC_02 §3: `YYYY-MM-DD_PROJECT_DOCUMENT_VERSION_STATUS.pdf` (`2021-09-30_ANK_RES_Facility_Agreement_EXECUTED_superseded.pdf`); sistemde `original.pdf` olarak saklanır (ADR-005: dosya adı metadata kaynağı değildir).

## 2. Şablonlar — `templates/`
- `base.html` + `styles.css`: A4, DejaVu Serif/Sans, DEMO filigranı, footer `sayfa X / Y` (TR) / `page X of Y` (EN), `lang` değişkeni; banner **her belgede** literal `DEMO / FICTIONAL DOCUMENT FOR DEMONSTRATION PURPOSES ONLY` (SPEC_05 §4) + TR belgelerde altına "Kurgusal demo belgesi"; `agreement` ailesinde ek `NOT A REAL CONTRACT`.
- `blocks/`: `cover` (başlık, proje, belge no = `external_ref`, versiyon, durum, tarih, taraflar), `meta_table`, `revision_history` (zincir üyeleri için: DRAFT/V01/V02/EXECUTED/AMD01/AMD02 satırları — 3.1'de dosyası olmayanlar da satırda görünür, "belge arşivde yok" ibaresiyle değil, normal satır olarak; içerik ledger'dan), `section` (h2 + paragraflar), `clauses` (numaralı madde), `table`, `signature_block` (kurgusal roller: "Borrower — Authorized Signatory", "Hazırlayan / Kontrol / Onay", isim yok), `annex`, `letterhead` (TR resmi yazı: sayı/konu/tarih satırı, gerçek kurum şablonu kopyalanmaz, kurum adı yalnızca hitap satırında).
- Aileler: `agreement.html` (Facility ×4, EPC), `letter.html` (Üretim Lisansı, Lisans Tadili, Önlisans, ÇED Durum Yazısı, Board Resolution), `report.html` (Covenant Report, Üretim Raporu, Teknik Rapor, Arazi Edinim Raporu).
- T0 şablonu (`seed_data/t0/templates/`) yeni `base.html`'in kaynağıdır; T0 klasörü sonra silinir (§6).

## 3. Migration `0004_documents_external_ref` (SORU 3)
`documents.external_ref VARCHAR(64) NULL`, unique index `ix_documents_external_ref`. Model: `Document.external_ref: Mapped[str | None]`. `DocumentListItem`'a eklenir (okuma). Upload API'de kabul edilmez (yalnızca seed yazar).

## 4. Seed — `app.cli seed-demo-documents` + `scripts/seed_demo.sh`

### 4.1 `document_repo.create_with_job` genişletmesi
Yeni keyword-only opsiyonel parametreler: `department, subdepartment, project_id, confidentiality, source, tags, related_document_ids, external_ref, expiration_date`. Upload endpoint'i çağrısı değişmez (varsayılanlar bugünkü davranış). Böylece 3.2'nin öneri-kabul akışı da aynı fonksiyonu kullanabilir.

### 4.2 `app/services/demo_documents_seed.py::ensure_demo_documents(session, settings, manifest_path) -> list[DemoSeedResult]`
Diğer `ensure_*` ile aynı desen. Her manifest kaydı için: `external_ref` varsa **dokunma** (satır, dosya, zincir korunur; `created=False`); yoksa `LocalFileSystemStore.store(uuid4, "original.pdf", open(file))` → `create_with_job(...)` ile:
- `title` = ledger `name.value`; `document_type` = ledger `type`; `department/subdepartment` = ledger slug'ları; `project_id` = `projects.code` ile bulunur (`CO` → `null`); `confidentiality`, `document_date`, `effective_date`, `status` = ledger; `counterparty` = `parties` içinde proje SPV'si/holding olmayan ilk taraf, yoksa SPV adı; `tags` = `[project_code|COMPANY, version_label]`; `source = web`; `version` = zincir konumu (DRAFT=1 … AMD02=6), zincir dışı 1; `revision = 0`; `related_document_ids` = `related_refs` → mevcut satır id'leri (henüz seed edilmemişse ikinci geçişte doldurulur); `uploaded_by_id` = admin; `external_ref` = ledger ID.
- Belge satırları `ingestion_status=uploaded` + `ingestion_jobs(queued)`; `ready` ocr-worker'dan gelir.

### 4.3 Zincir bağlama (T2) — ikinci geçiş
Tüm kayıtlar yazıldıktan sonra, ledger `facility_chain` sırasıyla: her belge için `supersedes_ref` zinciri yürünür, seed edilmiş ilk ata bulunur → `supersedes_document_id` / `superseded_by_document_id` ayarlanır (`mark_superseded`). İdempotent: mevcut bağ aynıysa dokunulmaz, farklıysa (5.1'de V01/V02 gelince) güncellenir — bu, "varsa dokunma" kuralının tek bilinçli istisnasıdır (zincir türetilmiş veridir, ledger'ın kendisi değil) ve raporda yazılır. Sonuç: DRAFT→EXECUTED→AMD01→AMD02 doğrusal; `status` ledger'dan geldiği için `version_chain.evaluate` tam olarak AMD02'yi `is_current` sayar.

### 4.4 `app.cli wait-for-documents --timeout 600`
`external_ref IS NOT NULL` satırlarını yoklar; hepsi `ready` → 0; biri `failed` → 1 + hata; zaman aşımı → 1.

### 4.5 `scripts/seed_demo.sh` (bash, LF)
```
make validate-ledger  (0 hata şart)
compose run backend python -m seed_data.generator.generate_documents      # prose commit'ten, LLM yok
compose run backend python -m seed_data.generator.validate_documents      # §5, 0 hata şart
compose run backend python -m app.cli seed-admin && seed-demo-users && seed-demo-departments && seed-demo-projects
compose run backend python -m app.cli seed-demo-documents --manifest seed_data/documents/manifest.json
compose run backend python -m app.cli wait-for-documents --timeout 600
özet: N belge ready / M zaten vardı
```
`make seed` = bu script. `make up` önkoşul (script `/health` bekler, `wait_for_services.sh`).

### 4.6 `scripts/reset_demo.sh` (SORU 2)
`--yes` yoksa onay ister (`DATA_ROOT` ve DB adını gösterir). Kapsam: `TRUNCATE documents CASCADE` (pages, chunks, jobs cascade) + `${DATA_ROOT}/documents/*` silinir (yetimler dahil, T11). Kullanıcılar/departmanlar/projeler **korunur** (ADR-003: seed var olanı değiştirmez; onlar zaten idempotent). `make reset-demo` = `bash scripts/reset_demo.sh --yes`. Ardından `make seed` sıfırdan çalışır (kabul kriteri).

## 5. `validate_documents.py` — üretilen içeriğin denetimi (5.1 `validate_dataset.py`'nin 3.1 alt kümesi)
| # | Kontrol | Seviye |
|---|---|---|
| P1 | `prose/*.yaml`: 3+ haneli sayı, `EUR/USD/TRY/€/$`, `A.Ş./Ltd./Bank/Sigorta/GmbH` kalıbı, bilinen placeholder dışı `{{…}}` → hata (T7) | ERROR |
| P2 | Prose'da yalnızca facts sözlüğündeki placeholder'lar; her belge için **zorunlu** placeholder seti (`key_facts` anahtarları) en az bir kez kullanılmış | ERROR |
| G1 | Üretilen dijital PDF metni: banner sayfa 1'de; `agreement` ailesinde `NOT A REAL CONTRACT` | ERROR |
| G2 | İsim taraması: `validate_ledger`'daki `_NAME_PATTERN` + `company.name_whitelist` (paylaşılan fonksiyon) | ERROR |
| G3 | İzolasyon: Ankara belgelerinde "İzmir"/"IZM_RES" yok, İzmir belgelerinde "Ankara"/"ANK_RES" yok (SPEC_05 §8); hiçbirinde "Bursa" | ERROR |
| G4 | `facts_used` içindeki her biçimlenmiş değer PDF metninde geçiyor ve `page_map`'teki sayfada | ERROR |
| G5 | PDF metnindeki 3+ haneli sayılar ∖ (facts değerleri ∪ tarihler ∪ yıllar ∪ sayfa no ∪ madde no) → listelenir | WARNING |
| G6 | `manifest.json` ↔ ledger envanteri: 15 kayıt, alanlar birebir; taranmışlar için `digital_file` var | ERROR |
Makefile: `validate-documents` hedefi; `make seed` içinde zorunlu; `make lint`'e **eklenmez** (üretilen dosyalar gitignore'da, lint çalışma ağacından bağımsız kalmalı) — prose denetimi (P1–P2) ise lint'e eklenir (`--prose-only`, prose commit'te olduğu için).

## 6. T0'ın kaldırılması ve test taşıması (T9)
- Silinir: `seed_data/t0/` (generate.py, templates, upload.sh, *.pdf), `tests/t0_fixtures.py`, `tests/live/test_t0_live.py`. `Dockerfile`/`pyproject` yorumlarındaki `t0` referansları güncellenir.
- Yeni `tests/ledger_fixtures.py`: `ensure_generated_documents()` (manifest yoksa `generate_documents.main()`'i importlib ile çalıştırır — prose commit'te olduğu için LLM'siz), `load_ledger_documents(session, refs=[...])` (manifest + PDF metni PyMuPDF ile sayfa/chunk olarak DB'ye, `ingestion_status=ready`, ledger metadata'sıyla), `ledger_value(path)` (YAML'dan `ledger:` yolu çözer — testlerde rakam tekrarı yok), `page_of(ref, fact_key)` (manifest `page_map`).
- Taşınan testler: `test_ask.py::test_sources_come_from_citations_with_page_and_chain` (EXECUTED/AMD01, sayfa no `page_of`, değerler `ledger_value`), `test_search_query.py` (3 test), `tests/live/test_ledger_live.py` (questions.json'daki `ANK-FIN-006`, `ANK-FIN-007`, `GEN-HAL-001` — 0.3'ün 3 kriteri, ledger değerleriyle; SORU 4).
- Yeni testler: `tests/test_demo_documents_seed.py` (aşağıda), `tests/test_validate_documents.py` (P1–P2 sentetik prose ile, G2–G3 sentetik PDF metniyle), migration testi `0004`.

## 7. Kabul kriteri → kanıt
| Kriter (PHASES.md) | Test / komut | Kanıt |
|---|---|---|
| `make seed` → 15 belge `ready` | canlı: `make reset-demo && make seed` çıktısı (`wait-for-documents` 15/15 ready, süre) + rapor; test: `test_demo_documents_seed.py::test_seed_creates_15_documents_and_queues_jobs` (test DB'de 15 satır, 15 `queued` job; `ready` ocr-worker'ın işi, `ocr-worker/tests/test_pipeline.py` ile zaten kanıtlı) | `make seed` özeti |
| metadata doğru | `::test_seeded_metadata_matches_ledger` — her satırın `department/subdepartment/project_id/confidentiality/status/dates/counterparty/external_ref/tags` ledger envanteriyle karşılaştırılır (YAML'dan okunur) | |
| zincir bağlı, "güncel" belge tek | `::test_facility_chain_is_linear_and_single_current` — `evaluate_version_chains` ile 4 halka, `is_current` yalnızca AMD02, `is_initial` DRAFT; `::test_licence_amendment_is_related_not_superseding` | |
| belgeler gerçekçi görünür | rapora 3 örnek sayfa-1 küçük resmi (`docs/reports/assets/phase_3_1/*.png`, ≤100 KB) + Naci görsel inceleme (SORU 6); `make seed` sonrası `GET /api/documents/{id}/download` ile açılır | |
| gerçek isim yok (validator) | `make validate-documents` 0 hata (G2) + `test_validate_documents.py::test_name_outside_whitelist_is_error`; `make lint` prose denetimi | |
| `make reset-demo` + `make seed` tekrar çalışır | canlı iki kez (rapor); `::test_seed_is_idempotent` (ikinci çağrı `created=0`, satır sayısı sabit, zincir aynı) | |
| Adım 0 belgeleri kaldırıldı | `git ls-files seed_data/t0` boş; `make test` yeşil (taşınan testlerle) | |

---

## SORU (Naci cevaplamalı)

1. **Prose'un yeri.** Önerim: prose **bir kez** LLM ile üretilir (`make prose`, 15 çağrı, ~5 dk), `seed_data/generator/prose/*.yaml` olarak `AI_ASSUMPTION` etiketiyle **commit edilir**; `make seed` LLM çağırmaz (prod klonu anahtar/ağ gerektirmez, çıktı tekrarlanabilir, prose'u sen de gözden geçirebilirsin). Alternatif: her `make seed`'de yeniden üretmek. Onaylıyor musun? Model: `gemini-3.5-flash` (kalite) mi, `.env`'deki `-lite` mı?
2. **Reset kapsamı.** Önerim: yalnızca belgeler (DB `documents` cascade + `${DATA_ROOT}/documents/*`); kullanıcılar/departmanlar/projeler korunur (zaten idempotent seed). `--yes` olmadan onay sorar. Kabul mü?
3. **`documents.external_ref` kolonu (migration 0004).** Seed idempotency'si ve 4.1 runner'ın belge eşleştirmesi için ledger ID'sini saklar; upload API'de görünmez. Alternatif: `tags`'e `ledger:DOC-…` yazmak (kirli). Onaylıyor musun?
4. **Canlı testler.** Önerim: `tests/live/test_t0_live.py` → `test_ledger_live.py` (aynı 3 kriter, questions.json'daki 3 soru, değerler ledger'dan). Alternatif: canlı testi 4.1 eval runner'a bırakıp 3.1'de tamamen kaldırmak. Hangisi?
5. **Hukuk'un belgesi yok.** 15 belge içinde `hukuk` departmanına ait belge yok (PHASES listesi böyle); `hukuk` kullanıcısı 5.1'e kadar her soruya "bilgi bulamadım" alır. Kabul mü, yoksa Arazi Edinim Raporu'nun departmanı `hukuk` mu olsun (ledger değişikliği → yeniden onay)?
6. **Görsel kanıt.** Rapora 3 sayfa-1 küçük resmi (PNG, ≤100 KB × 3) commit edilsin mi, yoksa yalnızca `make seed` sonrası senin açıp bakman yeterli mi?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)
- Ledger değişmez; lisans tadili `related` ile bağlı (supersede etmez), EPC `amended`, DRAFT `effective_date: null` (T1).
- Zincir seed edilmiş halkalar arasında kurulur; 5.1'de idempotent yeniden bağlanır (T2, §4.3).
- Seed doğrudan DB (`app.cli seed-demo-documents` + manifest); upload API değişmez (T3, T5).
- Placeholder tabanlı prose; rakam/tarih/isim yalnızca `facts.py`'den; `validate_documents.py` P1–P2 (T7).
- Şablon aileleri `agreement/letter/report` + blok kütüphanesi; bölüm-başına-sayfa-kırımı ve `page_map` (T8).
- Taranmış kopya: PyMuPDF 200 dpi JPEG q80 + ±0,4° tohumlu döndürme; yalnızca taranmış kopya seed edilir, dijital `*.digital.pdf` denetim için saklanır.
- `version` int = zincir konumu; `tags = [proje|COMPANY, versiyon etiketi]`; `source = web`; `counterparty` = SPV/holding olmayan ilk taraf; company belgesinde `project_id = null`.
- Banner her belgede literal EN metin + TR alt satır; `NOT A REAL CONTRACT` yalnızca `agreement` ailesinde.
- `validate-documents` `make seed`'de zorunlu, `make lint`'te yalnızca prose denetimi.
- Sayfa hedefleri §1.2 (toplam ≈ 70 sayfa); OCR bütçesi 10 dk.

## Doküman değişiklikleri
- `docs/ARCHITECTURE.md`: ADR-013'e 3.1 notu (placeholder-prose, commit edilen prose, manifest köprüsü, `external_ref`); ADR-006'ya seed'in kuyruğu kullandığı notu. Yeni ADR yok.
- `README.md`: "Demo veri (Phase 3.1)" — `make prose` (bir kez, anahtar gerekir), `make seed`, `make reset-demo`, `make validate-documents`; T0 bölümleri kaldırılır; "Soru sorma" örneği ledger belgesine güncellenir.
- `infra/.env.example`: `PROSE_MODEL` (opsiyonel, yorumlu).
- `docs/PHASES.md` durum satırı; `docs/reports/PHASE_3_1_REPORT.md`; `git tag phase-3-1`.

## Uygulama sırası
1. Migration `0004` + model/şema (`external_ref`); `create_with_job` genişletmesi + testleri.
2. `facts.py` + `templates/` (base, bloklar, 3 aile) + `generate_documents.py` — önce prose'suz iskelet render (yer tutucu paragraflarla) ile şablon/`page_map`/manifest doğrulanır.
3. `generate_prose.py` + `validate_documents.py --prose`; `make prose` (15 çağrı); reddedilenler düzeltilip yeniden; `prose/*.yaml` commit.
4. `generate_documents.py` gerçek prose ile; `validate_documents.py` G1–G6; `make validate-documents` 0 hata.
5. `demo_documents_seed.py`, `cli.py` (`seed-demo-documents`, `wait-for-documents`), `scripts/seed_demo.sh`, `scripts/reset_demo.sh`, Makefile (`seed`, `reset-demo`, `prose`, `validate-documents`).
6. T0 kaldırma; `ledger_fixtures.py`; taşınan testler; yeni testler.
7. Canlı: `make reset-demo && make seed` ×2, `wait-for-documents` süresi, örnek küçük resimler; `make test` + `make lint` yeşil → docs → rapor → PHASES → commit + tag `phase-3-1` + push.

## Kritik dosyalar
- `seed_data/generator/{facts,generate_prose,generate_documents,validate_documents}.py`, `seed_data/generator/templates/`, `seed_data/generator/prose/`
- `backend/alembic/versions/0004_documents_external_ref.py`, `backend/app/repositories/document_repo.py`, `backend/app/services/demo_documents_seed.py`, `backend/app/cli.py`
- `scripts/seed_demo.sh`, `scripts/reset_demo.sh`, `Makefile`
- `backend/tests/{ledger_fixtures,test_demo_documents_seed,test_validate_documents}.py`, taşınan `test_ask.py`/`test_search_query.py`/`tests/live/`
