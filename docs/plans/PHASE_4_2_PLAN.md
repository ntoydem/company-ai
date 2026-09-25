# Phase 4.2 — Excel motoru: Implementation Plan

## Bağlam ve tespitler

Adım 4'ün eval kısmı kapandı (3.2c, eşikler geçildi). Phase 4.2, SPEC_04'ün tamamını getiriyor: ledger'dan dört
workbook, build-time LibreOffice recalc, openpyxl inspection, DuckDB read-only hesap, `CalculationEngine`,
dosya+sheet+range kaynak, `.xlsm` macro garantisi. Router (DATA/MIXED ayrımı) **4.3** — bu fazda `/api/ask`'e
dokunulmuyor (T6).

Okunanlar: `docs/PHASES.md` (4.2), `docs/SPEC_04_excel_motoru.md` (tamamı), ADR-009/010/011/013/019/021,
`seed_data/master/{ankara_res,fx_rates}.yaml` (finance/operations bölümleri), `ledger_schema.py::Document`,
`backend/app/api/documents.py` (upload/MIME), `ocr-worker/worker/pipeline.py`, `infra/docker-compose.yml` (tools
profili), `backend/pyproject.toml`, `seed_data/generator/{generate_documents,validate_documents}.py` deseni.

### T1 — Ledger, workbook'ların çoğunu besliyor ama Financial Model için üç girdi eksik
Ledger'da olan: drawdowns (4 çekiş, toplam 50,4M), tenor (12→14), grace 24 ay, marj %3,25, taban "EURIBOR 6M"
(**sayı yok**), `outstanding_debt_as_of_demo_today` 44,1M, 11 çeyreklik `covenant_tests` (DSCR + pass/fail),
11 çeyreklik `budget_vs_actual` (TRY, tek kalem), 34 aylık `monthly_production` (MWh, availability, CF),
`fx_rates`. **Olmayan:** (a) taban faiz oranı sayısı (faiz hesabı için), (b) dönemlik CFADS/EBITDA (DSCR =
CFADS ÷ borç servisi — covenant_tests yalnızca sonucu veriyor), (c) geri ödeme takvimi (44,1M'e ulaşan anapara
satırları), (d) aylık rüzgar hızı ("rüzgar" sütunu), (e) aylık bütçe kalemleri ("aylık kalemler"). ADR-013:
workbook'taki her rakam ledger'dan gelir → bunlar ledger'a `AI_ASSUMPTION` olarak **eklenmeli**, validator
tutarlılığı zorlamalı (outstanding = 44,1M; hesaplanan DSCR = covenant_tests.dscr ±0,01). Kapsam ve yöntem
**SORU 1**.

### T2 — openpyxl formül yazar ama hesaplamaz; cached değer LibreOffice'ten gelmeli
openpyxl ile yazılan `=SUM(...)` hücresinin `data_only=True` değeri `None`'dır (kütüphane hesap motoru değil).
SPEC_04 §6 çözümü: build adımında LibreOffice headless `--convert-to xlsx` (dosyayı yükler, cached değeri olmayan
formülleri hesaplar, kaydeder). Gerçekçi değerlendirme §2'de.

### T3 — Workbook'lar da birer `Document` — ledger envanterine girmeli, yetki aynı kapıdan
DOMAIN_MODEL: "Workbooks are Documents with `document_type` in the Excel family". `documents[]` şeması
`source_type: digital_pdf|scanned_pdf`, `generate_in_phase: 3.1|5.1|never` — ikisi de genişler (`xlsx`,
`"4.2"`). Dört workbook envanter satırı (`DOC-ANK-FIN-008` Financial Model, `DOC-ANK-FIN-009` Covenant Report
workbook, `DOC-ANK-OPS-002` Budget vs Actual, `DOC-ANK-OPS-003` Monthly Production; departman finans/enerji_grubu,
proje ANK_RES). `allowed_document_ids` değişmiyor — Excel sorgusu da AUTHORIZATION → allowed → hesap → LLM sırasını
izler; `enerji` kullanıcısı Financial Model'i **göremez** (finans).

### T4 — Upload/ingestion: xlsx bir zip; OCR hattına girmemeli
`_MAGIC_BYTES` yalnızca pdf/png/jpg; `PK\x03\x04` → zip → `xl/workbook.xml` varsa xlsx, ayrıca `xl/vbaProject.bin`
varsa **xlsm**; csv'nin imzası yok (uzantı + UTF-8 çözülebilir + `csv.Sniffer`). ocr-worker `original_path.suffix`
ile dallanıyor — xlsx'i `ocrmypdf`'e verirse patlar. Karar (kendi kararım, §5): Excel ailesi upload'da **job
oluşturmadan** `ready` olur, `page_count` = sheet sayısı, **chunk/page yazılmaz** (SPEC_04 §1 "Excel doküman
RAG'ıyla çözülmez" — sheet metnini FTS'e sokmak Excel'i belge cevabına sızdırır). Sheet'ler sorgu anında DuckDB'ye
yüklenir (DOMAIN_MODEL).

### T5 — `audit_log.excel_files_used` Phase 3.4'ten beri boş bekliyor
Excel cevabında dosya adları buraya, `sources` JSONB'sine de dosya/sheet/range kartları yazılır — şema değişikliği yok.

### T6 — Router yok; Phase 4.2'nin kabul sorusu bir giriş noktası ister
"Ankara RES 2026 Q2 DSCR kaç?" → DuckDB + `Covenant_Report.xlsx Q2_2026!D14` — bunu tetikleyecek bir uç gerekiyor.
`/api/ask` DOCUMENT-only kalır (4.3 router'ı ekler); bu fazda ayrı `POST /api/excel/ask` (**SORU 3**).

### T7 — Bağımlılıklar
`duckdb`, `openpyxl`, `polars` `pyproject.toml`'da yok; üçü de runtime bağımlılığı olur (`app/excel/`). LibreOffice
**runtime bağımlılığı değil** (T2) — yalnızca build/generator.

---

## 1. Dört workbook — `seed_data/generator/generate_excel.py` (openpyxl)

Tümü `seed_data/excel/`, rakamlar yalnızca `facts.py::load_raws()` üzerinden ledger'dan; formüller Excel
formülü olarak yazılır (cached değer §2'de). Her workbook'ta bir **hidden** `_meta` sheet'i (üretim tarihi, ledger
`schema_version`, `DEMO_TODAY`, "DEMO — synthetic" ibaresi) — SPEC_04 §9'un "en az bir hidden sheet"i ve
inspection testinin hedefi. Named range'ler predefined fonksiyonların adres kaynağı (§6).

| Workbook | Sheet'ler | İçerik / formüller | Named range'ler |
|---|---|---|---|
| `Financial_Model_2026.xlsx` | `Inputs` (capex, equity, total/local/ECA debt, marj, taban oran(lar), tenor, grace, drawdown'lar, FX), `Debt` (yarıyıllık satırlar: tarih, açılış bakiye, çekiş, anapara, faiz `=bakiye*(taban+marj)/2`, kapanış bakiye `=açılış+çekiş-anapara`), `DSCR` (çeyreklik: CFADS, borç servisi `=anapara+faiz`, DSCR `=CFADS/servis`, covenant eşiği (1,25→1,20 yürürlük tarihine göre `=IF(...)`), sonuç `=IF(DSCR>=eşik,"pass","fail")`), `Cashflow` (çeyreklik: CFADS − servis = equity'ye nakit, kümülatif), `_meta` (hidden) | `Outstanding_DemoToday` (Debt!kapanış bakiye, DEMO_TODAY'e en yakın satır), `DSCR_<period>` (DSCR!satır), `Inputs_TotalDebt`, `Inputs_Margin` |
| `Covenant_Report.xlsx` | `Summary` (tüm çeyrekler: DSCR, eşik, sonuç — Financial Model ile aynı değerler, ledger `covenant_tests`), çeyrek başına sheet `Q4_2023`…`Q2_2026` (test detayı: CFADS, borç servisi, DSCR `=CFADS/servis`, eşik, sonuç, outstanding), `_meta` | `DSCR_Q2_2026` → `Q2_2026!D14` (kabul kriterinin adresi), her çeyrek için aynı desen; `Outstanding_Q2_2026` |
| `Budget_vs_Actual_2026.xlsx` | `Summary` (çeyrek: bütçe, gerçekleşen, variance `=actual-budget`, `%` `=variance/budget`), `Q1_2026`, `Q2_2026` (aylık kalemler — **SORU 1e**), `_meta` | `Variance_<period>` |
| `Monthly_Production_2026.xlsx` | `Production` (34 ay: MWh, availability %, CF %, rüzgar — **SORU 1d**; yıllık toplam `=SUM`), `KPI` (yıllık: toplam MWh `=SUMIF`, ortalama availability `=AVERAGEIF`, CF `=…`), `_meta` | `Production_<YYYY_MM>`, `MWh_Total_2026` |

Üretim tek komut: `make excel` (`generate_excel.py` → `recalc.sh` → `validate_excel.py`), `make seed`'in içine
belgelerden sonra girer (SPEC_05 §2 sırası: 10 belge → 11 Excel). Workbook'ların `documents` tablosuna yüklenmesi
`app/cli.py seed-demo-documents`'ın mevcut manifest deseniyle (`manifest.json`'a 4 satır, `source_type: xlsx`,
upload yolu `original.xlsx`, OCR job yok — T4).

## 2. Build-time recalc — `seed_data/generator/recalc.sh` ve gerçekçi değerlendirme

**Komut:** `soffice --headless --norestore --convert-to xlsx --outdir <tmp> <in.xlsx>` → çıktı dosyası girdinin
üzerine yazılır. LibreOffice, cached değeri olmayan formül hücrelerini yüklerken hesaplar ve xlsx'e **değerle
birlikte** yazar (openpyxl'in yazdığı dosyada hiçbir formülün cached değeri yoktur, bu yüzden "Never recalculate
on load" ayarı bile bu hücreleri hesaplamak zorunda kalır; yine de `--convert-to` öncesi profil ayarı
`RecalcMode=always` ile garanti altına alınır — implementasyonda resmi LO yapılandırma anahtarı doğrulanacak).

**Nereye kurulacak (kendi kararım):** backend imajına **değil** (LibreOffice Calc + bağımlılıkları ~450-700 MB,
runtime'da hiç kullanılmıyor, ADR-011 "runtime recalculation yok"). `docker-compose.yml`'e `profiles: ["tools"]`
altında `libreoffice` servisi (mevcut `frontend` tooling deseni; imaj: `debian:bookworm-slim` + `libreoffice-calc-nogui`
+ `fonts-dejavu`, ya da hazır `linuxserver/libreoffice`), `./seed_data:/seed_data` mount; `recalc.sh` bunu
`docker compose --profile tools run --rm libreoffice` ile çağırır. Backend imajı büyümez.

**Sürprizler ve önlemleri (dürüst liste):**
| Risk | Olasılık | Önlem |
|---|---|---|
| Headless ilk çalıştırmada profil oluşturma takılır / `HOME` yazılamaz | Sık | `-env:UserInstallation=file:///tmp/lo_profile` + `--norestore`; script'te 120 s timeout |
| Round-trip'te openpyxl artefaktları değişir (stil, sütun genişliği) — **named range'ler ve hidden bayrağı korunur mu?** | Orta | `validate_excel.py` W2/W3: recalc sonrası `defined_names` ve `sheet_state == "hidden"` aynen var mı; yoksa faz **durur**, çözüm (LO'nun kendi `.ods`→xlsx yolu ya da post-fix) o zaman kararlaştırılır |
| Yerel ayar: ondalık/tarih biçimi (TR locale) formülleri bozmaz ama görüntü biçimleri değişebilir | Düşük | `LANG=C.UTF-8`; biçim önemsiz, değer önemli |
| Formül LO'da desteklenmiyor / farklı hesaplıyor (`IFS`, dinamik dizi) | Düşük | Yalnızca `SUM/SUMIF/AVERAGEIF/IF/INDEX/MATCH/ROUND` — LO ile Excel'de birebir |
| Prod klonunda LibreOffice yok (Phase 5.4: yalnızca README) | **Kesin** | **SORU 2:** recalc'lı workbook'lar git'e commit edilsin (prose gibi), `make seed` LO gerektirmesin |
| LO çıktısında `data_only` değeri `None` kalan hücre | Orta | `validate_excel.py` W1: **her** formül hücresinin cached değeri dolu; kabul kriteri 1 tam bu |

**Doğrulama:** `validate_excel.py` (W1 cached değerler dolu; W2 named range'ler; W3 hidden `_meta`; W4 ledger
tutarlılığı — `Outstanding_DemoToday` = 44.100.000, her `DSCR_<q>` = `covenant_tests[q].dscr` ±0,01, Budget
Summary = ledger, Production toplamları = ledger; W5 dosya adları/sheet adları listeyle aynı). `make lint`'e girer
(`--prose-only` gibi hızlı mod: commit'li dosyalar üzerinde).

## 3. Inspection katmanı — `app/excel/inspect.py` (openpyxl, `data_only=True`)

`inspect_workbook(path) -> WorkbookInfo{file, sheets:[{name, hidden, dims, header_row, columns}], named_ranges:
[{name, sheet, range}], has_macros: bool, formula_cells_without_cache: int}`. İki yükleme: `data_only=True`
(değerler) + `data_only=False` (formül var mı / cache eksik mi). `read_only=True` ile büyük dosyalarda bellek
sınırı; `keep_vba=False` (varsayılan — §7). Uç: `GET /api/excel/{document_id}/inspect` (yetkili kullanıcı;
`allowed_document_ids`), LLM'in gördüğü katalog da buradan (§4). Dosya kaynağı: `DocumentStore.get_file(id,
"original")`.

## 4. Hesap motoru — `app/excel/engine.py` + `app/excel/sql_guard.py` + `app/excel/functions.py`

**Yükleme:** her sheet → DuckDB tablosu `<file_stem>__<sheet>` (openpyxl değerleri → Polars DataFrame → `conn.register`),
ilk satır başlık, ek `_row` sütunu (Excel satır numarası — kaynak range için, §6). Bağlantı: `duckdb.connect(":memory:",
config={"enable_external_access": False, "threads": 2})`, sorgu `read_only` anlamında yalnızca `SELECT` (whitelist);
`conn.interrupt()` ile 10 s zaman aşımı (ayrı thread), sonuç satır sınırı `LIMIT 200` (yoksa eklenir, varsa küçültülür).

**SQL whitelist (`sql_guard.py`, saf fonksiyon, birim testli):**
1. `strip()` sonra tek statement: `;` **hiçbir yerde** yok (string literal içinde bile — basit ve güvenli).
2. `SELECT` (veya `WITH … SELECT`) ile başlar (case-insensitive); `--`/`/*` yorum yok.
3. Yasak kelimeler token bazında (tırnak dışı): `INSERT UPDATE DELETE DROP CREATE ALTER ATTACH DETACH INSTALL LOAD
   PRAGMA COPY EXPORT IMPORT CALL SET RESET EXECUTE PREPARE VACUUM CHECKPOINT` + fonksiyon adları `read_csv
   read_parquet read_json read_text read_blob glob httpfs sniff_csv` + `duckdb_` öneki (sistem tabloları).
4. Tablo adları: `FROM`/`JOIN` sonrası tanımlayıcılar bilinen tablo listesinde olmalı (regex + DuckDB
   `EXPLAIN` — bilinmeyen tablo zaten hata verir, ama açık liste kontrolü önce).
5. `LIMIT` yoksa `LIMIT 200` eklenir; varsa `min(n, 200)`.
Reddedilen sorgu kullanıcıya Türkçe sabit mesaj ("Bu veri sorgusu güvenlik kuralına takıldı."), detay loga.

**Predefined fonksiyonlar (`functions.py`, parametreleri LLM doldurur, kod bizim):**
`dscr(period)`, `outstanding_debt(as_of)`, `budget_variance(period, line=None)`, `capacity_factor(period)`,
`production(period)` — her biri named range / `_row` üzerinden hücreyi okur (DuckDB'den değil, doğrudan
`data_only` değerden; toplam/ortalama gerekiyorsa DuckDB) ve `CalcResult{value, unit, source: SourceRange}` döner.
Period normalizasyonu ("2026 Q2", "Q2_2026", "2026-06", "2026") tek yerde (`periods.py`), birim testli.

**LLM'in rolü (SPEC_04 §3):** iki çağrı. (1) **plan** — `LLM_MODEL_CLASSIFY`, `json_object` (Phase 3.2 deseni):
girdi = soru + katalog (kullanıcının görebildiği workbook'lar: sheet'ler, sütunlar, named range'ler, fonksiyon
imzaları); çıktı `{"kind":"function","name":"dscr","params":{"period":"Q2_2026"}}` **veya**
`{"kind":"sql","sql":"SELECT …"}` **veya** `{"kind":"none","reason":…}`. (2) **yorum** — `LLM_MODEL_ANSWER`:
girdi = soru + `CalcResult` (değer, birim, kaynak); çıktı Türkçe tek-iki cümle. **Garanti:** son cümledeki rakam
motorun ürettiği `value`'nun biçimlendirilmiş hali metinde aynen yoksa cevap **şablona** düşer ("Ankara RES
Q2 2026 DSCR: 1,37x [Covenant_Report.xlsx Q2_2026!D14]") — LLM rakamı değiştiremez (ADR-011 "final rakam
modelden gelmez", ölçülebilir).

**Güvenlik testlerinin tasarımı (`tests/test_sql_guard.py`, `tests/test_excel_engine.py`):** parametrize edilmiş
kötü niyetli liste, her biri **reddedilmeli** ve DuckDB'ye hiç ulaşmamalı: `DROP TABLE x`, `SELECT 1; DROP TABLE x`,
`SELECT * FROM t; --`, `SELECT * FROM read_csv('/etc/passwd')`, `ATTACH '/data/x.db'`, `INSTALL httpfs`, `LOAD httpfs`,
`PRAGMA database_list`, `COPY t TO '/tmp/x'`, `SELECT * FROM duckdb_settings()`, `WITH x AS (SELECT 1) INSERT INTO …`,
`SELECT * FROM unknown_table`, `select * from t /* ; */`, çoklu boşluk/karışık büyük-küçük harf varyantları,
`SELECT * FROM t` (LIMIT eklenmiş mi), `SELECT * FROM t LIMIT 100000` (200'e indirilmiş mi). Motor seviyesinde:
`enable_external_access=false` iken `read_csv` doğrudan çağrılsa bile DuckDB hata verir (ikinci savunma hattı,
ayrı test); 10 s'de `SELECT` sonsuz döngü (`generate_series(1e12)`) kesiliyor mu; satır sınırı.

## 5. `CalculationEngine` interface — `app/excel/calc.py`

```python
class CalculationEngine(Protocol):
    def load(self, path: Path) -> LoadedWorkbook: ...           # tablolar + named range'ler + değerler
    def run_sql(self, wb: LoadedWorkbook, sql: str) -> QueryResult: ...
    def run_function(self, wb: LoadedWorkbook, name: str, params: dict[str, Any]) -> CalcResult: ...
class CachedValueEngine: ...  # tek implementasyon: openpyxl data_only + DuckDB
```
Cached değer eksikse (`formula_cells_without_cache > 0` ve sorgu o hücreye dokunuyorsa) `NeedsRecalculationError`
→ kullanıcıya SPEC_04 §6'nın cümlesi ("dosyanın Excel'de yeniden hesaplanıp kaydedilmesi gerekiyor"), 422.
Servis katmanı (`app/services/excel_ask.py`) motoru `Protocol` üzerinden kullanır; testler sahte motorla.

## 6. Kaynak gösterimi

`SourceRange{file: "Covenant_Report.xlsx", sheet: "Q2_2026", range: "D14"|"B21:F21", document_id}` →
metin `Covenant_Report.xlsx Q2_2026!D14` (SPEC_04 §5 biçimi birebir). Fonksiyonlar: named range adresi
(`DSCR_Q2_2026` → `Q2_2026!D14`). SQL: sonuç satırlarının `_row` min/max'ı + kullanılan sütunların harf aralığı →
`Production!B14:D25`. Yanıt şeması `ExcelAskResponse{answer, answered, value, unit, sources:[ExcelSourceCard],
plan_kind, sql|function, model, tokens_in, tokens_out}`; `SourceCard` (belge) ile **ayrı** tip — 4.3'te
`/api/ask` iki tipi birlikte döndürür. Audit: `excel_files_used=[file]`, `sources=[card…]`.

## 7. `.xlsm` macro garantisi (statik + dinamik)

- openpyxl VBA'yı **asla çalıştırmaz**; `load_workbook(keep_vba=False)` (varsayılan) `vbaProject.bin`'i okumaz bile.
  DuckDB/Polars yalnızca hücre değerlerini görür. `app/` içinde `subprocess`, `soffice`, `os.system`, `exec/eval`
  **yok** — `tests/test_no_execution_paths.py` `app/excel/` ve `app/services/excel_ask.py` kaynağını tarar (statik).
- Upload: `xl/vbaProject.bin` varsa `has_macros=true` metadata'ya (inspection'da görünür), dosya olduğu gibi
  saklanır, motor aynı yoldan (değer okuma) çalışır. Test: gerçek bir `.xlsm` fixture (küçük, macro'lu, macro'su
  bir dosya yazmaya çalışır) → inspect + sorgu çalışır, dosya sisteminde macro'nun yazacağı iz **yok**, log'da
  "macro çalıştırılmadı" değil — hiç böyle bir kod yolu yok, test bunu kanıtlar.
- LibreOffice yalnızca generator'da, yalnızca bizim `.xlsx`'lerimizde; upload edilen dosyalar LO'ya hiç gitmez.

## 8. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Kanıt |
|---|---|
| cached değerler dolu (`data_only` boş hücre yok) | `validate_excel.py` W1 (`make lint`); `tests/test_excel_inspect.py::test_generated_workbooks_have_no_uncached_formula` (4 dosya × tüm formül hücreleri) |
| "Ankara RES 2026 Q2 DSCR kaç?" → DuckDB + `Covenant_Report.xlsx Q2_2026!D14` tarzı kaynak | `tests/test_excel_ask.py` (sahte LLM planı `dscr(Q2_2026)` → değer 1,37 = ledger, kaynak `Covenant_Report.xlsx Q2_2026!D14`); canlı: `make test-llm` içinde gerçek Gemini planı ile aynı soru; ayrıca SQL yolu için "2026'da toplam üretim kaç MWh?" (`SUM` DuckDB'de, kaynak `Production!B…`) |
| `DROP/;/COPY/çoklu statement` reddedilir | `tests/test_sql_guard.py` parametrize liste (§4) + motor seviyesi `enable_external_access` testi |
| `.xlsm` macro çalışmaz | §7'nin iki testi (statik tarama + xlsm fixture) |
| audit'te excel kaynakları | `tests/test_excel_ask.py::test_audit_row_has_excel_files_and_sources` (`excel_files_used`, `sources`) |
| (yetki) `enerji` Financial Model'i sorgulayamaz | `tests/test_excel_ask.py::test_excel_query_respects_allowed_document_ids` — katalogda görünmez, doğrudan `document_id` ile 403/"bilgi yok" |

---

## SORU (Naci cevaplamalı)

1. **Ledger eksikleri (T1) nasıl kapatılsın?** Önerim, her biri `AI_ASSUMPTION` olarak `ankara_res.yaml`'a:
   (a) `finance.interest.base_rate_pct_by_year` (2021-2026, 6 sayı, EURIBOR 6M yıllık ortalama kurgusu);
   (b) `finance.repayment_schedule` yarıyıllık satırlar (tarih, anapara) — grace 24 ay + sculpted profil, toplamı
   2026-09-15'e kadar 6,3M olacak şekilde (44,1M'e tutarlı; validator zorlar); (c) `finance.cfads_by_quarter`
   (Q4_2023…Q2_2026, EUR) — `cfads / (anapara+faiz)` = `covenant_tests.dscr` ±0,01 olacak şekilde türetilmiş
   (validator zorlar); (d) rüzgar: `monthly_production[].wind_speed_ms` **eklenmesin**, Production sheet'inde
   rüzgar sütunu **olmasın** (SPEC "rüzgar" diyor ama ledger'da yok; uydurmaktansa atlıyorum); (e) aylık bütçe
   kalemleri: çeyreklik tek kalem yerine 4 kalem (O&M, sigorta, arazi kirası, G&A) × ay — 11 çeyrek × 4 kalem ×
   3 ay = 132 sayı, hepsi `AI_ASSUMPTION`, çeyrek toplamı ledger `budget/actual`'a eşit (validator). (e) çok
   "yaratıcılık" ise alternatif: çeyreklik tek kalem kalsın, `Budget_vs_Actual` yalnızca `Summary` içersin. Hangisi?
   Onaylanan eklemeler Phase 2.1 akışıyla (taslak `AI_ASSUMPTION` → gözden geçir → `USER_FACT`) girer; bu faz
   onları `AI_ASSUMPTION` olarak bırakır.
2. **Recalc'lı workbook'lar git'e commit edilsin mi?** `.gitignore` bugün `seed_data/excel/`'i dışlıyor (SPEC_05 §1
   "üretilen"). Ama prod klonunda LibreOffice olmayacak (Phase 5.4: yalnızca `git clone` + `make up` + `make seed`).
   Önerim: 4 dosya (toplam < 500 KB) **commit edilir** (prose deseni: üretim dev'de bir kez, `make excel`; `make
   seed` LO gerektirmez, validator commit'li dosyayı doğrular). Alternatif: prod'da da `tools` profiliyle LO
   çekmek (~700 MB imaj, kurulum süresi).
3. **Giriş noktası:** bu fazda `POST /api/excel/ask` (yalnızca DATA; `/api/ask` DOCUMENT-only kalır, 4.3 router
   ikisini birleştirir) + `GET /api/excel/{document_id}/inspect`. Frontend'e bu fazda **dokunulmaz** (Sor ekranı
   4.3'te Excel kaynak kartını öğrenir). Onaylıyor musun, yoksa `/api/ask`'e şimdiden basit bir "Excel mi?"
   anahtar kelime dallanması mı istiyorsun (önermiyorum — router'ın işi, iki kez yazılır)?
4. **Upload'da `.csv`:** SPEC destekliyor ama demo'da csv yok. Önerim: upload kabul edilir (tek sheet gibi
   yüklenir, `csv.Sniffer` ile ayraç), predefined fonksiyonlar csv'ye bağlanmaz (named range yok), yalnızca SQL.
   Yeterli mi, yoksa csv bu fazda tamamen dışarıda mı kalsın?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Excel ailesi upload'da OCR job'suz `ready`; chunk/page yazılmaz (T4) — Excel FTS'e girmez.
- xlsx/xlsm ayrımı zip içeriğinden (`xl/vbaProject.bin`), uzantı beyanına güvenilmez; `has_macros` belge
  metadata'sında (`documents`'a küçük bir kolon, migration `0008`) — inspection'da ve listede görünür.
- LibreOffice ayrı `tools` profili container'ında; backend imajına girmez.
- İki LLM çağrısı (plan `json_object` + yorum), rakam garantisi şablona düşme ile (§4).
- SQL guard saf fonksiyon + DuckDB `enable_external_access=false` çift savunma; `LIMIT 200`; 10 s `interrupt()`.
- `_row` sütunu ile SQL kaynak range'i; fonksiyonlar named range'den.
- Period normalizasyonu tek modül; Türkçe "2026 2. çeyrek" → `Q2_2026`.
- Dört workbook `documents` envanterine `DOC-…-00x` id'leriyle girer; şema `source_type` += `xlsx`,
  `generate_in_phase` += `"4.2"`.
- Polars yalnızca sheet→DataFrame köprüsü; pandas yok.

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: ADR-011'e "Phase 4.2 concretization" (LO tools container, plan/yorum çağrıları, rakam
  garantisi, `_row` kaynak, csv kararı); ADR-006'ya Excel'in OCR hattını atladığı notu; ADR-016'ya
  `excel_files_used` artık dolu.
- `docs/DOMAIN_MODEL.md`: Excel workbook satırı somutlaşır (`has_macros`, 4 demo workbook).
- `docs/SPEC_04` değişmez (spec). `docs/prompts/EXCEL_PLAN_PROMPT.md` (plan promptu kopyası, `make prompt-doc`
  deseni).
- `README.md`: "Excel analizi (Phase 4.2)" — `make excel`, `/api/excel/ask` `curl`, güvenlik sınırları, csv/xlsm notu.
- `infra/.env.example`: `EXCEL_QUERY_TIMEOUT_S=10`, `EXCEL_ROW_LIMIT=200`.
- `docs/reports/PHASE_4_2_REPORT.md`, `docs/PHASES.md`, `git tag phase-4-2`.

## Uygulama sırası

1. SORU 1'e göre ledger eklemeleri (`AI_ASSUMPTION`) + `validate_ledger.py` yeni kurallar (F9 outstanding, F10
   DSCR tutarlılığı) + şema (`source_type`, `generate_in_phase`, workbook envanteri).
2. `generate_excel.py` (4 workbook, named range, hidden `_meta`) + `libreoffice` tools servisi + `recalc.sh` +
   `validate_excel.py` (W1-W5) + `make excel`; LO round-trip riskleri burada ölçülür (§2 tablosu → rapora).
3. `pyproject`: duckdb/openpyxl/polars; `app/excel/{inspect,calc,engine,sql_guard,functions,periods}.py` + birim
   testleri (güvenlik listesi dahil).
4. Upload: xlsx/xlsm/csv algılama, `has_macros` (migration 0008), OCR'suz `ready`; ocr-worker'a savunma (Excel
   uzantısı görürse job'ı `failed` değil `done` işaretler — normalde hiç job gelmez).
5. `app/services/excel_ask.py` (yetki → katalog → plan LLM → motor → yorum LLM → rakam garantisi → audit) +
   `POST /api/excel/ask`, `GET /api/excel/{id}/inspect` + testler (sahte LLM/motor).
6. `seed-demo-documents` workbook'ları yükler; `make seed` uçtan uca; canlı `make test-llm` Excel testleri.
7. Dokümanlar → rapor → PHASES.md → commit + tag `phase-4-2` + push.

## Kritik dosyalar

- `seed_data/generator/{generate_excel.py,recalc.sh,validate_excel.py}`, `seed_data/master/ankara_res.yaml`
- `backend/app/excel/{inspect,calc,engine,sql_guard,functions,periods}.py`, `backend/app/services/excel_ask.py`,
  `backend/app/api/excel.py`, `backend/app/api/documents.py` (upload), `backend/alembic/versions/0008_*`
- `infra/docker-compose.yml` (`libreoffice` tools), `Makefile` (`excel`), `backend/pyproject.toml`
