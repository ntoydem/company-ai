# Aşama B — `file_kind`, indirme adı + `?inline=1`, `AskRequest.project_id` kaldırma — Uygulama Planı

**Tarih:** 30.09.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` (NOT) §1 B-13, B-17, B-20/6; BACKEND_GAPS §4.1, §4.3, §3.3 (dondurulmuş v7.9). Üçü de "ADR gerekmez, küçük şema eklemesi" sınıfında (NOT §1 son paragraf).

Okunanlar: NOT §1/§4.1/§4.2/§4.4; `backend/app/api/documents.py` (`_detect_extension`, `_safe_file_name`, `upload_document`, `download_document`, `get_document`), `schemas/document.py`, `schemas/ask.py`, `schemas/excel.py` (`WorkbookInspectResponse`), `services/{ask,ask_router,excel_ask,retrieval,document_store,demo_documents_seed}.py`, `models/document.py`, `repositories/document_repo.py`, `tests/test_documents.py` (indirme testleri, `_document`/`_upload` yardımcıları), Starlette `FileResponse` kaynağı (container: **starlette 1.6.0**), container `mimetypes` tablosu; AI-BalBal `b219600`: `FileLink.tsx`, `DocumentDetailPanel.tsx:80-84`, `WorkbookInspectCard.tsx`, `api/documents.ts:99`, `api/types.ts`, `components/AskPanel.tsx:31`, `components/balbal/BalbalChat.tsx:47`.

---

## 1. Tespitler

- **T1 — Dosya türü zaten diskte ve satırda kodlu, migration gerekmez.** Her yükleme `_detect_extension` (magic bytes: `%PDF-`→`pdf`, PNG→`png`, JPEG→`jpg`; zip + `xl/workbook.xml`→`xlsx`/`xlsm`; `.csv` + UTF-8 + ayraç→`csv`) ile sınıflanır ve `storage_path = <uuid>/original.<ext>` yazılır (`documents.py:169,209-210`, `document_store.py:29`). Demo seed de `original.pdf`/`original.xlsx` yazar (`demo_documents_seed.py:59`). Dolayısıyla `file_kind`, `storage_path` uzantısından **türetilir**; olası uzantı kümesi kapalıdır: `pdf | png | jpg | xlsx | xlsm | csv`.
- **T2 — `inspect` cevabında tür zaten var.** `WorkbookInspectResponse.kind: str  # xlsx | xlsm | csv` (`schemas/excel.py:69`, `inspect.py:97,133`). `WorkbookInspectCard.tsx:7`'nin sorunu inspect'in tür dönmemesi değil, **listede** tür olmadığı için her belgede körlemesine `/inspect` çağırıp Excel olmayanlarda 422 almasıdır. Çözüm liste/detayda `file_kind`; inspect'e yeni alan gerekmez.
- **T3 — İndirme adı `original.<ext>`.** `download_document` (`documents.py:304`) `FileResponse(path, filename=path.name)`; `path` = `get_file(kind="original")`. Başlık (`documents.title`, serbest metin, Türkçe karakterli) dosya adına girmiyor.
- **T4 — Starlette 1.6.0 `FileResponse` RFC 5987'yi kendisi yapıyor.** Kaynak: `filename` ASCII'ye `quote()` ile değişmeden çevriliyorsa `filename="…"`, aksi halde **yalnızca** `filename*=utf-8''<percent-encoded>` yazar; `content_disposition_type` parametresi (`"attachment"` varsayılan) `"inline"` alabilir. Türkçe karakter için ek kod gerekmez; ama `filename*`-only başlık eski istemcilerde adsız iner (modern tarayıcılar sorunsuz — plan bu davranışı kabul eder, ASCII fallback eklemez; **SORU 2**).
- **T5 — MIME tahmini container'da eksik.** `mimetypes.guess_type`: `pdf/png/jpg/csv` doğru, **`xlsx`/`xlsm` → `None`** → Starlette `application/octet-stream` yazar. Tarayıcıda indirme için zararsız, ama `inline` ve doğru `Content-Type` için açık bir `MEDIA_TYPE_BY_KIND` haritası şart.
- **T6 — `?inline=1` güvenlik sınırı.** Aynı origin'den kullanıcı yüklemesi PDF/PNG/JPG'yi `inline` sunmak: tarayıcı PDF görüntüleyicisi ve `img` render'ı sandbox'lıdır; SVG/HTML kabul edilmediği için (`_MAGIC_BYTES`) script yürütme yüzeyi yok. Yine de `X-Content-Type-Options: nosniff` eklenir ve `Content-Type` **her zaman** bizim haritamızdan gelir (tarayıcı sniff etmez). `xlsx/xlsm/csv` için `inline` anlamsız; istense de `attachment`'a düşürülür (tarayıcı zaten indirir; CSV'yi `text/csv inline` göstermek yerine tutarlılık).
- **T7 — `AskRequest.project_id` bugün nerede:** `schemas/ask.py:30` (opsiyonel), `ask_router.py:139,152` (alt isteklere geçirilir), `:232,271` (`audit_log.scope_project`), `ask.py:139,147` (`RetrievalFilters`/`AuthorizationScope` daraltması), `excel_ask.py:220,394` (aynı, `ExcelAskRequest.project_id`). **Kullanan istemciler:** AI-BalBal `BalbalChat.tsx:47` göndermiyor; **`AskPanel.tsx:31` (departman "Balbal'a Sor" sekmesi) hâlâ gönderiyor** (`project_id: projectId ?? undefined`, `types.ts:211`); company-ai `frontend/` emekli; `ask_page.py` (geliştirici sayfası) göndermiyor; **eval (`questions.json`, `run_eval.py`) hiç göndermiyor** — NOT §1 B-20/6'daki "filtre kaldırılınca isolation eval'i zorlanır" uyarısı bu yüzden **geçersiz**: `isolation %75` zaten filtresiz ölçüldü, kaldırma eval'i değiştirmez. Testlerde `/api/ask`'a `project_id` gönderen yok.
- **T8 — Kaldırma geriye dönük uyumlu.** `AskRequest` `ConfigDict(frozen=True)`, `extra` varsayılan `ignore` → alan şemadan çıkınca eski istemcinin gönderdiği `project_id` **sessizce yok sayılır, 422 olmaz**. `AskPanel` çalışmaya devam eder, yalnızca proje daraltması kalkar (B-20/6'nın istediği tam bu). `RetrievalFilters.project_id`, `AuthorizationScope.project_id` ve `GET /api/documents?project_id=` **kalır** (ADR-004 imzası donmuş; liste süzme başka bir özellik). `audit_log.scope_project` sütunu kalır, `/api/ask` için artık hep `NULL`.

---

## 2. Tasarım

### 2.1 `file_kind` (B-13)

- `models/document.py`: `FileKind = Literal["pdf", "image", "xlsx", "xlsm", "csv"]` ve `Document.file_kind` **property** (`storage_path`'in son uzantısı: `png`/`jpg`/`jpeg` → `"image"`, diğerleri aynen). Bilinmeyen uzantı (teorik; yükleme yolu kapalı küme) → `ValueError` **değil**, `"pdf"`'e de düşmez: property `FileKind | None` döner, şema `file_kind: FileKind | None`. Sessiz yanlış tür yerine açık `null` (SORU 1).
- `schemas/document.py::DocumentListItem.file_kind` (`from_attributes` property'yi okur) → `DocumentDetailResponse` miras alır; `GET /api/documents`, `GET /api/documents/{id}`, `POST …/metadata-suggestion/apply` (liste şeması) ve `PATCH` (detay) otomatik taşır. `DocumentUploadResponse`'a da eklenir (yükleme anında bilinir; `UploadTab` durum kartı için ucuz).
- `inspect`: değişmez (T2). `document_repo.EXCEL_SUFFIXES` ile `has_workbook`-tarzı ikinci bir türetme **yazılmaz**; `file_kind in ("xlsx","xlsm","csv")` yeter.
- Migration: **yok** (T1).

### 2.2 İndirme adı (B-17)

- `documents.py`: `download_file_name(title: str, kind: FileKind, ext: str) -> str` saf fonksiyon (test edilebilir):
  1. `title.strip()`; kontrol karakterleri (`\x00-\x1f\x7f`) ve dosya-sistemi/başlık-güvensiz `/ \ : * ? " < > |` → boşluk; ardışık boşluklar tek; baş/son nokta ve boşluk kırpılır (Windows).
  2. Boş kalırsa `belge`.
  3. Uzunluk: 120 karakter (UTF-8 percent-encoded hâli başlık sınırlarına sığsın), sonra `.{ext}`.
  4. Türkçe karakterler **korunur**; encoding Starlette'e bırakılır (T4).
- Uzantı `storage_path`'ten (`pdf | png | jpg | xlsx | xlsm | csv`), `file_kind`'dan değil (`image` uzantı değildir).
- Excel için `documents.file_name` (orijinal yükleme adı, ör. `Covenant_Report.xlsx`) kullanılmaz; B-17 "başlık + uzantı" diyor ve kaynak kartı zaten `file_name`'i gösteriyor — tutarlılık için başlık (SORU 3).

### 2.3 `?inline=1` (B-17)

- `download_document(..., inline: bool = False)` (FastAPI query; `1/true/yes` → `True`).
- `MEDIA_TYPE_BY_KIND = {pdf: application/pdf, image(png): image/png, image(jpg): image/jpeg, xlsx: application/vnd.openxmlformats-officedocument.spreadsheetml.sheet, xlsm: application/vnd.ms-excel.sheet.macroEnabled.12, csv: text/csv; charset=utf-8}` — uzantıya göre; `guess_type`'a güvenilmez (T5).
- `disposition = "inline" if inline and kind in ("pdf", "image") else "attachment"` (T6); `FileResponse(path, filename=download_file_name(...), media_type=..., content_disposition_type=disposition, headers={"X-Content-Type-Options": "nosniff"})`.
- Yetki/404/403 davranışı değişmez (`allowed_document_ids` önce, `403` istisnası korunur — `PHASE_1_2_PLAN` T6).
- Her zaman **orijinal** dosya sunulur (`kind="original"`); görüntü yüklemesinin OCR'lı `ocr.pdf`'i inline'da sunulmaz (SORU 4).

### 2.4 `AskRequest.project_id` kaldırma (B-20/6)

- `schemas/ask.py::AskRequest`: alan silinir; docstring "extra ignored → eski istemci 422 almaz" (T8).
- `ask_router.py`: alt isteklerde `project_id=` geçişleri ve `scope_project=request.project_id` → `scope_project=None`; `ask.py` `RetrievalFilters(department=…)`, `AuthorizationScope(department=…)`. `ExcelAskRequest.project_id`: **SORU 5** (öneri: aynı gerekçeyle kaldır; `document_ids` daraltması kalır).
- `ask_page.py` (geliştirici sayfası): proje alanı yok, değişmez.
- `RetrievalFilters`/`AuthorizationScope.project_id`, `GET /api/documents?project_id=`: **dokunulmaz** (T8).
- Not: NOT §1 B-20/6'nın `SourceCard.project_code/name` kısmı bu fazın **dışında** (Aşama A SORU 4'te de dışarıda bırakıldı; ayrı küçük iş).

### 2.5 Dokunulmayanlar

Backend yetki modeli, retrieval, router, `audit_log` şeması (sütun kalır), AI-BalBal, company-ai `frontend/`, Caddyfile, migration'lar.

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `app/models/document.py` | `FileKind`, `Document.file_kind` property |
| `app/schemas/document.py` | `DocumentListItem.file_kind`, `DocumentUploadResponse.file_kind` |
| `app/api/documents.py` | `download_file_name()`, `MEDIA_TYPE_BY_EXT`, `download_document(inline)` |
| `app/schemas/ask.py`, `app/services/{ask,ask_router}.py` | `project_id` kaldırma; (SORU 5 evetse) `schemas/excel.py`, `services/excel_ask.py` |
| `tests/test_documents.py`, `tests/test_ask.py`, `tests/test_ask_router.py`, (`tests/test_excel_api.py`) | §5 |
| `README.md` (belge yükleme/indirme + `/api/ask` bölümleri), `docs/ARCHITECTURE.md` (ADR-011/ADR-015 concretization: `file_kind` türetme, inline sınırı; ADR-010/020 notu: `/api/ask` proje daraltması kaldırıldı), `docs/PHASES.md` notu, NOT §1 B-13/B-17/B-20/6 + §4.1/§4.2 → UYGULANDI, `docs/reports/ASAMA_B_REPORT.md` | docs |

Yeni uç yok; değişen uçlar: `GET /api/documents`, `GET /api/documents/{id}`, `POST /api/documents/upload` (eklemeli), `GET /api/documents/{id}/download` (`?inline=1`, ad, `Content-Type`), `POST /api/ask` (alan kaldırma, uyumlu).

---

## 4. Uygulama sırası

1. `FileKind` + property + şema alanları + testler (T-01..T-03).
2. `download_file_name` saf fonksiyon + birim testleri (T-04); `download_document` (T-05..T-08).
3. `project_id` kaldırma + testler (T-09..T-11).
4. `make test`, `make lint`; canlı: seed'li dev VM'de `curl -I` ile başlık kontrolü (§5).
5. Docs → rapor → düz commit + PHASES.md notu (Aşama A ile aynı kural) → push.

---

## 5. Kabul kriterleri ve kanıt

| # | Kriter | Test / komut |
|---|---|---|
| T-01 | `file_kind` türetme: `original.pdf→pdf`, `png/jpg→image`, `xlsx/xlsm/csv` aynen; bilinmeyen uzantı → `null` | `test_documents.py::test_file_kind_derived_from_storage_path` (parametrize, `Document` nesnesi üzerinde) |
| T-02 | `GET /api/documents` ve `/{id}` her satırda `file_kind`; PDF yüklemesi `pdf`, PNG `image`, `Covenant_Report.xlsx` `xlsx`, `.xlsm` `xlsm`, CSV `csv` | mevcut yükleme testlerine assert; `test_excel_api.py` yükleme testlerine `file_kind` |
| T-03 | `POST /upload` cevabında `file_kind` | `test_upload_*` assert |
| T-04 | `download_file_name`: `"Ankara RES Kredi Sözleşmesi"` → `Ankara RES Kredi Sözleşmesi.pdf`; `"a/b:c*d?e\"f<g>h\|i"` → `a b c d e f g h i.pdf`; `"  ..gizli.. "` → `gizli.pdf`; `""`/`"???"` → `belge.pdf`; 300 karakter → 120 + uzantı; kontrol karakteri düşer | `test_documents.py` parametrize |
| T-05 | `/download`: `Content-Disposition: attachment; filename*=utf-8''Ankara%20RES%20Kredi%20S%C3%B6zle%C5%9Fmesi.pdf`; ASCII başlıkta `filename="Facility Agreement.pdf"`; `Content-Type: application/pdf`; `X-Content-Type-Options: nosniff` | `test_documents.py` (`_document` fixture'ı Türkçe başlıkla) |
| T-06 | `?inline=1` PDF → `inline; filename*=…`; PNG → `inline`, `image/png`; `xlsx` `?inline=1` → **`attachment`** + `application/vnd.openxmlformats…sheet`; `csv` → `text/csv` | aynı dosya |
| T-07 | `?inline=1` yetki davranışını değiştirmez: başka departman → 403, bilinmeyen → 403 (mevcut testler + `inline=1` varyantı) | mevcut 403 testleri parametrize |
| T-08 | Gövde bayt bayt orijinal dosya (inline/attachment fark etmez) | `response.content == FAKE_PDF` |
| T-09 | `POST /api/ask` gövdesinde `project_id` gönderen eski istemci **200** alır (422 değil); cevap aynı | `test_ask.py::test_legacy_project_id_is_ignored` |
| T-10 | `/api/ask` retrieval'ı artık proje ile daralmıyor: iki projeye ait iki belge, `project_id` gönderilse de ikisi de aday (prompt'ta ikisi de) | `test_ask.py` (`_document` + `project_id`) |
| T-11 | `audit_log.scope_project` `/api/ask` satırlarında `NULL`; `scope_department` çalışmaya devam | `test_ask_router.py` |
| T-12 | `make test`, `make lint` yeşil; `make eval EVAL_ARGS="--retrieval-only"` 36/36 (retrieval'a dokunulmadı, ama `RetrievalFilters` çağrısı değiştiği için koşulur) | komutlar |
| T-13 | Canlı (`company-ai-dev`, seed'li, LLM yok): `curl -sI -b c.txt :8080/api/documents/<DOC-ANK-FIN-004 id>/download` → `Content-Disposition` başlıkta belge adı; `…?inline=1` → `inline`; `GET /api/documents` ilk 3 satırda `file_kind`; AI-BalBal `FileLink`'in `target=_blank` linki (`DocumentDetailPanel.tsx:80`) `?inline=1` **eklemiyor** — tarayıcıda hâlâ indirir; inline'ı Tansu `downloadUrl(id) + "?inline=1"` ile bağlar (bilgi) | komut çıktısı rapora |

---

## 6. SORU (Naci cevaplamalı)

1. **Bilinmeyen uzantıda `file_kind`:** `null` (öneri; yükleme yolu bu durumu üretemez, yalnızca elle bozulmuş satır) — mı, yoksa `pdf` varsayımı mı?
2. **`filename*`-only başlık (T4):** Starlette'in davranışı kabul (modern tarayıcılar, AI-BalBal'ın hedefi) — mı, yoksa ASCII fallback (`filename="Ankara RES Kredi Sozlesmesi.pdf"; filename*=…`) için özel başlık mı yazılsın? Öneri: kabul, özel kod yok.
3. **Excel indirme adı:** başlık + uzantı (B-17 birebir, öneri) — mı, yoksa `documents.file_name` (orijinal ad) mı?
4. **Görüntü yüklemesinde `?inline=1`:** orijinal PNG/JPG (öneri) — mı, yoksa OCR'lı `ocr.pdf` (metin katmanlı, aranabilir) mi? İkincisi "indir = orijinal, aç = ocr.pdf" ayrımı yaratır; B-17 bunu istemiyor.
5. **`ExcelAskRequest.project_id` de kaldırılsın mı?** Öneri: evet, aynı B-20/6 gerekçesi; `document_ids` daraltması kalır. AI-BalBal `/api/excel/ask`'ı çağırmıyor.
6. **Faz birimi:** etiketsiz düz commit + PHASES.md notu (Aşama A/deploy ile aynı) — uygun mu?

---

## 7. Kendi aldığım küçük kararlar

- `file_kind` bir **property**, sütun değil (T1); `image` tek değer (png/jpg ayrımı gerekmiyor; uzantı indirme adında korunur).
- `inspect` cevabına `file_kind` **eklenmez** (`kind` zaten var, T2).
- `inline` yalnızca `pdf`/`image` (T6); diğerleri sessizce `attachment`.
- `Content-Type` haritası uzantıya göre, `guess_type` kullanılmaz (T5).
- Dosya adı sınırı 120 karakter; boş → `belge`.
- `audit_log.scope_project` sütunu ve `GET /api/audit-log?project_id=` filtresi kalır (geçmiş satırlar için).
- `RetrievalFilters.project_id` kalır — `GET /api/documents?project_id=` ve retrieval birim testleri (`test_retrieval.py`) dokunulmadan geçer.
