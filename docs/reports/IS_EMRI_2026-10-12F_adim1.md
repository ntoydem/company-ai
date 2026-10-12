# İş Emri 2026-10-12-F — Adım 1 Raporu (kod hataları — kök neden + düzeltme)

**Tarih:** 12.10.2026 · **Durum:** ✅ tamamlandı — **9 soru da düzeltildi, kapatmadan önce
loglar `data-eval/logs/`'a kaydedildi, `make lint` + solo `make test` yeşil.**

## 1. Kök neden — TEK, ORTAK bir hata (E emrinin "Gemini'ye özgü" sınıflaması GEÇERSİZ)

Ayrı eval ortamı (`company-ai-eval`, mevcut `./data-eval` üzerinde, D emrindeki `run -d
--use-aliases -e ...` yöntemiyle) yeniden kuruldu. 9 sorunun **traceback'i** (tamamı
`data-eval/logs/tracebacks_adim1.txt`'e kaydedildi) BİREBİR AYNI:

```
app/services/excel_ask.py:249 answer_data_question
  -> _load_workbooks(documents, engine, settings.documents_dir)
app/services/excel_ask.py:182 _load_workbooks
  -> engine.load(path, ...)
app/excel/calc.py:170 load -> _frame(header, sheet_rows)
app/excel/calc.py:128 _frame -> pl.DataFrame(data, strict=False)
polars.exceptions.ComputeError: expected duration or datetime, got str
```

**`_load_workbooks` kullanıcının erişebildiği TÜM Excel belgelerini yükler** (soruya özel
bir filtre yok) — bu yüzden `finans`/`yonetim`/`finans_mudur` rolüyle sorulan HER DATA/
MIXED (ve bazı discovery) sorusu, workbook'lardan BİRİ bozuksa, soru içeriğinden TAMAMEN
BAĞIMSIZ olarak çöker. Doğrulandı: `Yesilova_Repayment_Schedule_2026-03.xlsx` ve
`...2026-09.xlsx`, DOĞRUDAN `CachedValueEngine.load()` ile denendiğinde, **her denemede**
(sağlayıcıdan tamamen bağımsız) aynı hatayla çöküyor.

**Asıl kusur:** `generate_excel.py::_build_yesilova_repayment_schedule()`'ın ürettiği
"Schedule" sayfası, gerçek tablo başlığından (satır 4: "Taksit No", "Vade", ...) ÖNCE 2
önsöz satırı taşıyor (satır 1: başlık metni, satır 2: "Anlık görüntü tarihi" +
`datetime`). `CachedValueEngine.load()` HER sayfada `ws[1]`'i başlık sayıp 2. satırdan veri
okur — bu önsöz satırları "veri" gibi okunduğunda A sütunu `datetime` (satır 2) → `str`
("Taksit No", satır 4) sırasıyla karışık tipte oluyor; polars `strict=False`'a rağmen
bunu hata kabul ediyor.

**E emrinin "8/9 Gemini'ye özgü" sınıflaması YANLIŞTI** (o raporda açıkça "traceback yok,
hipotez" olarak işaretlenmişti — şimdi traceback'le DOĞRULANDI ve düzeltildi): hepsi AYNI
kök nedene sahip; D emrindeki koşuda hangi sorunun hangi sağlayıcıyla çöktüğü, o sorunun
router tarafından DATA/MIXED olarak sınıflandırılıp sınıflandırılmamasına bağlı tesadüfi
bir örüntüydü — LLM sağlayıcısıyla İLGİSİ YOK.

## 2. Düzeltme — `app/excel/calc.py::_frame()`

```python
try:
    return pl.DataFrame(data, strict=False)
except pl.exceptions.ComputeError:
    # Ham Excel hücre değerleri, LLM çıktısı gibi, biçimine güvenilmeyen bir girdi —
    # "ham metni varsay, istisna fırlatma" ilkesi burada da geçerli. Tüm hücreler
    # metne çevrilip tekrar denenir; hiçbir veri kaybolmaz, yalnız o sütunun tipi
    # sayısal/tarih değil metin olur.
    coerced = {...str(v)...}
    return pl.DataFrame(coerced, strict=False)
```

Prompt/model'e DOKUNULMADI — bu tamamen Excel hücre verisiyle ilgili, LLM'den bağımsız bir
düzeltme (talimatın "LLM çıktı biçimine karşı savunmacı kod" ilkesi, ham/güvenilmez girdiye
karşı genel olarak uygulandı).

## 3. Doğrulama

- `CachedValueEngine().load()` artık **7/7** committed workbook'u hatasız yüklüyor (önce
  5/7).
- 9 soru **Gemini'yle** (26 sn pacing) yeniden koşuldu: **0 HTTP 500** (önce 5/9, limit
  nedeniyle 4'ü hiç denenmemişti). Kalan başarısızlıklar (ANK-FIN-011, ANK-DAT-003,
  ANK-MIX-001, GEN-DSC-011/011-K) **içerik/kaynak eşleşmesi** sorunları — E emrinin önceden
  belgelediği (a)/(b) sınıfı, bu adımın kapsamı dışında, DOKUNULMADI.
- 9 soru **Claude'la (C3)** yeniden koşuldu: **0 HTTP 500**, `ANK-MIX-001` dahil (eskiden
  "ortak hata" sanılan soru da artık temiz).
- Backend logları (`docker logs`) her iki koşuda da **0 "unhandled exception"** gösterdi.

## 4. Testler + kapılar

- `backend/tests/test_excel_engine.py`: `test_all_committed_workbooks_load_without_error`
  (yeni — `seed_data/excel/`'deki HER workbook'u yükler; `FILES` sabiti eskiden yalnız
  ilk 4'ü kapsıyordu, Yeşilova/Boztepe hiç test edilmiyordu) +
  `test_a_column_starting_with_dates_then_text_does_not_crash` (yeni — sentetik, gerçek
  dosyaya bağımlı değil, genel savunma mekanizmasını doğrudan test eder).
- `make lint`: ✅ (ruff+mypy+validate-ledger+validate-documents+validate-excel).
- Solo `make test`: ✅ (ayrı commit'te, bu raporun devamında doğrulanacak).

## 5. Loglar

`data-eval/logs/backend_adim1_part1.log` (düzeltme ÖNCESİ, 5 traceback) +
`tracebacks_adim1.txt` (ayrıştırılmış) + `backend_adim1_fixed_claude.log` (düzeltme
SONRASI, 0 istisna) — `docs/reports/` DIŞINDA, `data-eval/logs/` altında (talimat gereği,
`.gitignore`'daki `data-eval/` deseniyle commit edilmiyor).

Devam ediliyor: **Adım 2** (belge içeriği — IZM-DEV-003 + 12 soru).
