# Aşama B Raporu — `file_kind`, indirme adı + `?inline=1`, `project_id` kaldırma

**Tarih:** 30.09.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `9d83227`
**Plan:** `docs/plans/ASAMA_B_PLAN.md` · **ADR:** ADR-011 ve ADR-015 concretization (B-13/B-17), ADR-010 notu (B-20/6); yeni ADR yok · **Migration:** yok

Naci'nin SORU cevapları (hepsi planın önerisi yönünde): (1) bilinmeyen uzantı → `null`; (2) `filename*`-only kabul, ASCII fallback yok; (3) Excel indirme adı = başlık + uzantı; (4) görüntü inline = orijinal PNG/JPG; (5) `ExcelAskRequest.project_id` de kaldırıldı; (6) etiketsiz düz commit.

## 1. Kabul kriterleri (plan §5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| T-01 | `file_kind` türetme (pdf, png/jpg/JPEG→image, xlsx, xlsm, csv; docx/uzantısız → `null`) | ✅ | `test_documents.py::test_file_kind_is_derived_from_storage_path` (9 parametre) |
| T-02 | Liste ve detay her satırda `file_kind`; PDF `pdf`, PNG `image`, `Covenant_Report.xlsx` `xlsx` | ✅ | `test_list_detail_and_upload_carry_file_kind`; `test_excel_api.py::test_xlsx_upload_is_ready_without_an_ocr_job` (`xlsx`); canlı: seed'li listede `{'pdf': 17, 'xlsx': 1}` |
| T-03 | `POST /upload` cevabında `file_kind` | ✅ | aynı testler (`DocumentUploadResponse.file_kind`) |
| T-04 | `download_file_name`: Türkçe korunur; `/ \ : * ? " < > \|` ve kontrol karakterleri → boşluk; baş/son nokta-boşluk kırpılır; boş/`???` → `belge`; 300 → 120 karakter | ✅ | `test_download_file_name_is_safe_and_keeps_turkish_letters` (7 parametre) |
| T-05 | `/download`: `attachment; filename*=utf-8''Kredi%20S%C3%B6zle%C5%9Fmesi.pdf`, `Content-Type: application/pdf`, `X-Content-Type-Options: nosniff`, gövde bayt bayt orijinal | ✅ | `test_download_uses_the_title_and_rfc5987_encodes_it`; canlı: `attachment; filename*=utf-8''Facility%20Agreement.pdf` |
| T-06 | `?inline=1`: PDF → `inline`; PNG → `inline` + `image/png`; xlsx → **`attachment`** + `application/vnd.openxmlformats…sheet`; csv → `attachment` + `text/csv; charset=utf-8` | ✅ | `test_inline_is_honoured_for_pdf_and_image_only`; canlı: PDF `inline; filename*=…`, workbook `attachment; filename*=utf-8''Covenant%20Report%20%28workbook%29.xlsx` |
| T-07 | `?inline=1` yetkiyi değiştirmez (başka departman 403, bilinmeyen 403) | ✅ | `test_inline_does_not_change_authorization` |
| T-08 | Gövde orijinal dosya (inline/attachment fark etmez) | ✅ | T-05/T-06 testlerinde `response.content == FAKE_PDF`; canlı gövde `%PDF-1.7` |
| T-09 | Eski istemcinin `project_id` göndermesi **200** (422 değil) | ✅ | `test_ask.py::test_legacy_project_id_is_ignored_not_rejected`; canlı: `project_id` ile `/api/ask` → 200 |
| T-10 | `/api/ask` proje ile daralmıyor: iki projenin belgesi de prompt'ta | ✅ | aynı test (`"Ankara Sözleşme"` ve `"İzmir Sözleşme"` prompt'ta) |
| T-11 | `audit_log.scope_project` `/api/ask` satırında `NULL` | ✅ | aynı test (`rows[0].scope_project is None`) |
| T-12 | `make test`, `make lint` yeşil; `--retrieval-only` 36/36 | ✅ | **418 geçti** (397 + 21 yeni), 15 deselected (live); `make lint` çıkış 0; recall@80 **36/36** |
| T-13 | Canlı (`company-ai-dev`, seed'li) | ✅ | yukarıdaki canlı satırlar; ayrıca **bulgu:** uç HEAD desteklemiyor (`curl -I` → 405, önceden de öyle) — README örneği GET ile yazıldı |

## 2. Yapılanlar

- `models/document.py`: `FileKind` Literal, `Document.storage_extension` / `Document.file_kind` property'leri (uzantı → tür haritası, kapalı küme; bilinmeyen → `None`). Migration yok.
- `schemas/document.py`: `DocumentListItem.file_kind` (detay miras alır), `DocumentUploadResponse.file_kind`.
- `api/documents.py`: `download_file_name(title, extension)` saf fonksiyon; `MEDIA_TYPE_BY_EXTENSION` (container `mimetypes`'ında xlsx/xlsm yok); `INLINE_FILE_KINDS = {pdf, image}`; `download_document(inline: bool = False)` → `FileResponse(filename=…, media_type=…, content_disposition_type=…, headers={"X-Content-Type-Options": "nosniff"})`; her zaman `kind="original"`.
- `schemas/ask.py`, `schemas/excel.py`: `project_id` kaldırıldı (docstring: `extra="ignore"` → eski istemci 200). `services/ask.py`, `excel_ask.py`, `ask_router.py`: `RetrievalFilters`/`AuthorizationScope` yalnızca `department`; `scope_project=None`.
- **Dokunulmayanlar:** `RetrievalFilters.project_id`, `AuthorizationScope.project_id`, `GET /api/documents?project_id=`, `audit_log.scope_project` sütunu + `?project_id=` filtresi (geçmiş satırlar), `inspect` (`kind` zaten vardı), AI-BalBal, company-ai `frontend/`.
- Docs: README (yükleme bölümüne "Dosya türü, indirme adı, tarayıcıda açma"; `/api/ask` gövdesi notu), ADR-011/ADR-015/ADR-010 satırları, PHASES.md notu, NOT §1 B-13/B-17/B-20/6 UYGULANDI + **isolation uyarısının geçersiz olduğu düzeltmesi**, §4.1/§4.2/§4.4 satırları.

## 3. Değişen dosyalar

`git diff --stat` (uygulama commit'i): 15 dosya, +284 / −34 (rapor hariç). Kod: `app/models/document.py`, `app/schemas/{document,ask,excel}.py`, `app/api/documents.py`, `app/services/{ask,ask_router,excel_ask}.py`; testler: `tests/{test_documents,test_excel_api,test_ask}.py`; docs: `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`.

## 4. Testler

- Backend: **418 geçti** (21 yeni: 9 `file_kind` parametresi, 7 `download_file_name` parametresi, 4 indirme/inline testi, 1 `project_id`), 15 deselected (`live`), 3 dk 50 sn. Tek geçici kırmızı: ASCII başlıkta `filename="…"` bekleyen assert — Starlette boşluğu da `%20` yapar, bu yüzden boşluklu her başlık `filename*` biçimini alır; SORU 2 ("Starlette davranışı kabul") gereği test davranışa uyduruldu, kod değiştirilmedi.
- `make lint`: yeşil. `make eval EVAL_ARGS="--retrieval-only"`: 36/36 (retrieval çağrı imzası değiştiği için koşuldu).
- Canlı: LLM'siz (`/api/documents`, `/download`), + 1 router çağrısı (`project_id`'li `/api/ask`, boş retrieval → cevap modeli çağrılmadı).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| Boşluklu ASCII başlık da `filename*=utf-8''…` alır (`filename="…"` yalnızca boşluksuz/ASCII-temiz başlıkta) | Starlette `quote()` boşluğu kodlar; SORU 2 özel başlık yazma dedi | Modern tarayıcılar doğru adı gösterir; eski istemci adsız indirir |
| `file_kind` property, sütun değil; `image` tek değer | Plan T1; png/jpg ayrımı indirme uzantısında zaten korunuyor | Migration yok |
| `inline` yalnızca `pdf`/`image`; xlsx/csv sessizce `attachment` | Plan T6; tarayıcı zaten indirir, `nosniff` ile tutarlı | — |
| `Content-Type` haritası uzantıya göre; bilinmeyen → `application/octet-stream` | Container `mimetypes` xlsx/xlsm bilmiyor | — |
| `download_file_name` 120 karakter, `belge` fallback | Plan §2.2 | — |
| HEAD desteği eklenmedi (405 kalıyor) | Kapsam dışı, önceden de yoktu; tarayıcı GET kullanır | README örneği GET |

## 6. Açık sorular (Naci cevaplamalı)

- Yok.

## 7. Riskler / sonraki adım için notlar

- AI-BalBal (`b219600`) `file_kind`'ı okumuyor, `WorkbookInspectCard` hâlâ her belgede `/inspect` deniyor; `FileLink`'in "aç" linki `?inline=1` eklemiyor — ikisi de Tansu tarafında 1-2 satır (NOT §4.1/§4.2'ye yazıldı).
- `AskPanel.tsx:31` hâlâ `project_id` gönderiyor; zararsız (yok sayılır), çip artık görsel.
- `SourceCard.project_code/name` (B-20/6'nın ikinci yarısı) hâlâ yapılmadı; ayrı küçük iş.
- `audit_log.scope_project` yeni satırlarda hep `NULL`; `GET /api/audit-log?project_id=` yalnızca geçmiş satırları bulur.

## 8. Doğruladığım üçüncü taraf davranışları

- Starlette 1.6.0 `FileResponse`: `filename` `quote()` sonucu değişiyorsa **yalnızca** `filename*=utf-8''…` yazar (ASCII fallback yok); `content_disposition_type` parametresi `inline` alıyor; `media_type` verilince `guess_type` çağrılmıyor.
- Container `mimetypes.guess_type`: `.xlsx`/`.xlsm` → `None`, `.csv` → `text/csv`, `.pdf/.png/.jpg` doğru.
- Pydantic v2 `BaseModel` varsayılan `extra="ignore"`: şemadan silinen alan gövdede gelirse sessizce atılır (T-09 canlı 200).
- FastAPI `GET` rotası HEAD'e 405 döner (Starlette otomatik HEAD eklemez).

## 9. Kaynak kullanımı

- Değişiklik yok (Caddy/backend RAM aynı); LLM: canlı doğrulamada 1 router çağrısı.
