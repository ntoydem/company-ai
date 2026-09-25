# Phase 4.2 Raporu — Excel motoru

**Tarih:** 25.09.2026  **Model:** Fable 5.1  **Tag:** phase-4-2  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt |
|---|---|---|---|
| 1 | cached değerler dolu (`data_only` boş hücre yok) | ✅ | `validate_excel.py` W1 (`make lint`): 4 dosya, 0 hata; `test_excel_engine.py::test_generated_workbooks_have_no_uncached_formula_and_a_hidden_meta_sheet` |
| 2 | "Ankara RES 2026 Q2 DSCR kaç?" → DuckDB + `Covenant_Report.xlsx Q2_2026!D14` tarzı kaynak | ✅ | Canlı (gerçek Gemini, `finans` kullanıcısı): plan `{"kind":"function","name":"dscr","params":{"period":"Q2_2026"}}`, cevap "Ankara RES 2026 Q2 DSCR 1,37x olarak gerçekleşmiştir.", kaynak **`Covenant_Report.xlsx Q2_2026!D14`**; `test_excel_api.py::test_ask_dscr_uses_the_predefined_function_and_cites_the_cell` (sahte LLM), `tests/live/...::test_excel_dscr_question_is_planned_computed_and_cited` (`make test-llm`) |
| 3 | `DROP/;/COPY/çoklu statement` reddedilir | ✅ | `test_sql_guard.py`: 24 kötü niyetli/ bilinmeyen sorgu parametrize (DROP, `;`, yorum, `read_csv('/etc/passwd')`, ATTACH, INSTALL/LOAD, PRAGMA, COPY, `duckdb_settings()`, WITH…INSERT, `SELECT INTO`, SET, bilinmeyen tablo, EXPLAIN, glob) — hepsi `SqlRejectedError`; `test_excel_engine.py::test_sql_guard_and_external_access_are_both_enforced`; canlı uçta `test_excel_api.py::test_ask_rejects_dangerous_sql_from_the_model` (model `SELECT 1; DROP …` üretirse Türkçe ret, ikinci LLM çağrısı yok) |
| 4 | `.xlsm` macro çalışmaz | ✅ | `test_no_execution_paths.py` (statik: `app/excel/`, `excel_ask.py`, `api/excel.py` içinde `subprocess/os.system/soffice/keep_vba=True/exec/eval/importlib` yok; DuckDB `enable_external_access=false`) + `test_excel_api.py::test_xlsm_is_flagged_never_executed` (VBA projeli dosya: `has_macros=true`, inspect/sorgu çalışır, hiçbir kod yolu VBA'yı yüklemez — openpyxl `keep_vba` verilmez) |
| 5 | audit'te excel kaynakları | ✅ | `test_excel_api.py::test_ask_dscr…`: `audit_log.query_type=DATA_QUERY`, `excel_files_used=["Covenant_Report.xlsx"]`, `sources[0].label="Covenant_Report.xlsx Q2_2026!D14"` |

## 2. Yapılanlar
- **Ledger (SORU 1):** `ankara_res.yaml` finance'e `base_rate_pct_by_year` (2021-2035, 15 satır), `repayment_schedule`
  (23 yarıyıllık anapara satırı, 2024-06-30 … 2035-06-30, toplam 50,4M), `cfads_by_quarter` (11 çeyrek) —
  hepsi `AI_ASSUMPTION` (269 `USER_FACT` / 95 `AI_ASSUMPTION`). `debt_math.py` (validator + üretici + motorun ortak
  aritmetiği), `validate_ledger.py` F9 (DEMO_TODAY bakiyesi = 44.100.000), F10 (CFADS/servis = covenant DSCR ±0,01),
  F11 (taksit toplamı = çekilen, son taksit tenor içinde). Şema: `source_type += xlsx`, `generate_in_phase += "4.2"`,
  4 workbook envanter satırı (`DOC-ANK-FIN-008/009`, `DOC-ANK-OPS-002/003`).
- **Workbook'lar:** `generate_excel.py` (openpyxl, yalnızca formül; named range'ler kontrat; gizli `_meta`),
  `recalc.sh` + `infra/libreoffice/Dockerfile` (`tools` profili, app kullanıcısıyla), `validate_excel.py` W1-W5,
  `make excel` / `make validate-excel` (lint'in parçası). 4 dosya + `manifest.json` **commit'li** (SORU 2),
  `.gitignore` güncellendi.
- **Backend `app/excel/`:** `inspect.py`, `sql_guard.py`, `calc.py` (`CalculationEngine` + `CachedValueEngine`),
  `functions.py` (5 predefined), `periods.py` (TR/EN dönem yazımları). `services/excel_ask.py` (yetki → katalog →
  plan LLM JSON → motor → yorum LLM → rakam garantisi → audit), `api/excel.py` (`POST /api/excel/ask`,
  `GET /api/excel/{id}/inspect`; SORU 3), `schemas/excel.py`. Ayarlar `EXCEL_QUERY_TIMEOUT_S`, `EXCEL_ROW_LIMIT`.
- **Upload/ingestion:** xlsx/xlsm zip içeriğinden (`xl/workbook.xml`, `xl/vbaProject.bin`), csv ad+UTF-8+ayraç ile
  algılanır (SORU 4: csv yalnızca SQL yolu); Excel ailesi OCR job'suz `ready`, chunk yok; migration `0008`
  (`documents.has_macros`, `documents.file_name` — atıf için orijinal ad, `storage_path` hep `original.<ext>`);
  `ocr-worker` savunma dalı; `seed-demo-documents` workbook manifest'ini de yükler.
- Bağımlılıklar: `openpyxl`, `duckdb`, `polars`, `pyarrow` (Polars→DuckDB köprüsü), dev `types-openpyxl`.
- Dokümanlar: ADR-006/011/016 notları, DOMAIN_MODEL, README "Excel analizi", `docs/prompts/EXCEL_PROMPTS.md`
  (`make prompt-doc` + lint eşitlik kontrolü, ANSWER_SYSTEM_PROMPT deseni), `.env.example`.

## 3. LibreOffice recalc — gerçekleşen (plan §2 risk tablosuna karşı)
| Plan riski | Gerçekleşen |
|---|---|
| Headless ilk çalıştırma profili | `-env:UserInstallation=file:///tmp/lo_profile --norestore`; sorunsuz. Yalnızca "javaldx" uyarısı (Java yok, Calc'a gerekmiyor) |
| Round-trip'te named range / hidden sheet kaybı | **Korundu** — W2/W3 0 hata (15+22+33+39 named range, 4 gizli `_meta`) |
| Locale / formül uyumu | `VLOOKUP/INDEX/MATCH/SUMIF/AVERAGEIF/COUNTIF/ROUND/IF/YEAR` hepsi hesaplandı; W4 ledger tutarlılığı 0 hata |
| Süre / imaj | 4 dosya **3,2 sn**; imaj `debian:bookworm-slim` + `libreoffice-calc-nogui` = 641 MB, yalnızca dev; backend imajı büyümedi |
| Dosya sahipliği | İlk koşuda root'a düştü → compose'da `user: ${APP_UID}:${APP_GID}` + `HOME=/tmp`; düzeltildi |
| Prod'da LO yok | Workbook'lar commit'li; `make seed` LO gerektirmez, `validate_excel` commit'li dosyayı doğrular |

## 4. Canlı doğrulama (gerçek Gemini, `make up` + `make seed` sonrası)
| Kullanıcı | Soru | Plan | Cevap | Kaynak |
|---|---|---|---|---|
| `finans` | Ankara RES 2026 Q2 DSCR kaç? | `dscr(Q2_2026)` | "Ankara RES 2026 Q2 DSCR 1,37x olarak gerçekleşmiştir." | `Covenant_Report.xlsx Q2_2026!D14` |
| `enerji` | Ankara RES 2026 yılında toplam kaç MWh üretti? | `production(2026)` | "… toplam 108.858 MWh elektrik üretmiştir." | `Monthly_Production_2026.xlsx KPI!B5` |
| `enerji` | Ankara RES 2026 Q2 DSCR kaç? | `dscr(Q2_2026)` (katalogda Covenant workbook yok — finans) | "Erişebildiğiniz Excel dosyalarında … bulamadım." | — (ADR-004: yetki önce) |

Plan promptu 1.462 token (katalog: tablolar, sütunlar, named range'ler, fonksiyon imzaları). Rakam garantisi
canlıda tetiklenmedi (model rakamı aynen yazdı); sahte-LLM testi ("yaklaşık 1,4x") şablona düşüşü kanıtlıyor.

## 5. Testler
- Backend: 337 geçti, 7 atlandı (canlı LLM), 0 kırmızı (3 dk); yeni: `test_sql_guard.py` (29), `test_periods.py` (8), `test_excel_engine.py` (11),
  `test_excel_api.py` (11), `test_no_execution_paths.py` (2), `test_migrations.py` (0008). ocr-worker 9.
- `make lint`: ruff+mypy (strict, `types-openpyxl` ile), eslint+tsc, ledger F1-F11, prose, **`validate_excel` W1-W5**,
  iki prompt dokümanı eşitliği — temiz.
- `make test-llm ARGS="-k excel"`: 1 geçti — gerçek Gemini planı `dscr(Q2_2026)`, cevap "Ankara RES 2026 Q2 DSCR 1,37x olarak gerçekleşmiştir.", kaynak `Covenant_Report.xlsx Q2_2026!D14`.

## 6. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `documents.file_name` kolonu (planda yoktu) | Atıf dosya adı ister (`Covenant_Report.xlsx …`), depolama hep `original.<ext>`; ilk testler `original.xlsx Q2_2026!D14` üretti | Migration 0008'e eklendi; upload orijinal adı (basename, uzantı normalize) yazar |
| Budget vs Actual yalnızca `Summary` (SORU 1e) | Aylık kalem uydurmamak | `budget_variance(period, line)`'da `line` yok sayılır |
| Rüzgar sütunu yok (SORU 1d) | Ledger'da yok | Production sheet: MWh, availability, CF |
| SQL kaynak range'i: `_row` seçilmemişse tablonun tüm veri aralığı | Satır bazlı atıf için sonuçta `_row` gerekir; yoksa kullanılan sheet'in aralığı dürüst cevap | `SELECT SUM(...)` → `Production!A2:D35`; `SELECT _row, …` → tam satır aralığı |
| `pyarrow` bağımlılığı | DuckDB, Polars frame'ini Arrow üzerinden okuyor; onsuz `register` patlıyor | +~40 MB imaj |
| Yorum LLM'i başlık/etiket eklemez, kaynak kartı ayrı döner | Rakam garantisini basit tutmak | UI 4.3'te kartı gösterir |

## 7. Açık sorular (Naci cevaplamalı)
- Yok. Dört SORU plan onayında cevaplandı ve uygulandı.

## 8. Riskler / sonraki phase için notlar
- **Phase 4.3 (router/MIXED):** `/api/ask`'ın DATA/MIXED dallanması `services/excel_ask.py::answer_data_question`'ı
  aynen çağırabilir; `ExcelSourceCard` ile belge `SourceCard` birlikte döndürülmeli; frontend Sor ekranı Excel kartını
  öğrenmeli.
- Plan LLM'i katalog büyüdükçe (Phase 5.1, daha çok workbook) token yiyecek (bugün ~1,5k); sütun listesi 40 ile
  sınırlı, gerekirse katalog özeti kısaltılır.
- `outstanding_debt(as_of=tarih)` Debt sheet'inde `end_date`/`closing_eur` sütun adlarına bağlı (üretici kontratı);
  kullanıcı yüklemesi farklı başlıklarla gelirse yalnızca named range'li/SQL yolu çalışır.
- Eval soru seti v2'ye (Phase 5.1) `data` kategorisi eklenmeli; `eval_lib` Excel kaynak kartını (`file/sheet/range`)
  puanlamayı öğrenmeli.

## 9. Doğruladığım üçüncü taraf davranışları
- LibreOffice 7.x (Debian bookworm `libreoffice-calc-nogui`) `--headless --convert-to xlsx`: openpyxl'in yazdığı,
  cached değeri olmayan formülleri yüklerken hesaplayıp değerle birlikte kaydediyor; `definedNames` ve
  `sheet_state=hidden` korunuyor (canlı, 4 dosya).
- DuckDB `duckdb.connect(config={"enable_external_access": False})` + `conn.interrupt()` başka thread'den →
  `duckdb.InterruptException` (canlı timeout testi 0,2 sn'de kesti). Polars `DataFrame` `register` için `pyarrow`
  zorunlu.
- openpyxl `load_workbook(data_only=True)`: LO'nun yazdığı cached değerler okunuyor; `defined_names` dict API (3.1).

## 10. Kaynak kullanımı
- LLM: canlı doğrulama 3 soru × 2 çağrı + canlı test 2 çağrı ≈ 8; testler sahte LLM.
- `libreoffice` imajı 641 MB (yalnızca dev); backend imajına +openpyxl/duckdb/polars/pyarrow (~90 MB).
