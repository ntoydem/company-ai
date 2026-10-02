# B-28 Raporu — İki aşamalı belge onay akışı (`review_status` kapıda) + §7.2 #7

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `<commit>`
**Plan:** `docs/plans/B28_ONAY_AKISI_PLAN.md` · **ADR:** **ADR-024** (yeni) + ADR-004 concretization · **Migration:** `0013_document_review`

Naci'nin SORU cevapları (02.10.2026, hepsi planın önerisiyle): (1a) upload anında 409 `approver_not_configured`, `department=None` 409 almaz; (2) `management`/`admin` muafiyeti yok; (3) `rejected` yok; (4) admin `apply`/`PATCH` de onayı düşürür, istisna yalnızca hedef dept müdürü; (5) öneri bekleniyorsa 409 `suggestion_pending`; (6) kayıt defteri admin-only; (7) etiketsiz commit + PHASES.md + ADR-024. **LLM çağrısı: 0.**

**Düzeltme (plan §0):** `review_status` bu fazdan önce kodda **yoktu** — 30.09'daki karar Aşama E'de uygulanmamıştı. Bu faz onu sıfırdan, ADR-004 kapısı + Phase 3.2 öneri akışı + B-08 + B-26 üzerine kurdu.

## 1. Kabul kriterleri (plan §4)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| O-01 | Personel upload → `pending_metadata`; liste/arama/`/api/ask`/Excel kataloğunda görünmez (aynı departmanın başka çalışanı, `management`, yükleyen için bile varsayılan scope'ta); yükleyen `GET /api/documents` ve `GET /{id}`'de görür | ✅ | `test_document_review::test_employee_upload_is_pending_and_hidden_from_everyone_but_the_handlers` — `/api/ask` LLM'siz "bilgi bulamadım", `/api/search` bulmaz, meslektaş 404, `management` görmez, müdür `?review_status=pending_metadata` kuyruğunda görür, admin görür |
| O-02 | Hedef departmanın kendi müdürü upload → anında `approved` + `auto_approved`; başka dept müdürü/`management`/`admin` → `pending_metadata` | ✅ | `test_only_the_target_departments_manager_publishes_at_once` |
| O-03 | `submit` yalnızca yükleyen (admin dahil başkası 403; göremeyen 404); uygun durum dışında 409 `review_state_conflict`; alanlar yazılır, öneri `applied`, `pending_review`, olaylar | ✅ | `test_submit_is_the_uploaders_act_and_enforces_the_confidence_threshold` |
| O-04 | %80: güveni 0.55 alan öneri değeriyle + `confirmed_fields` yok → 422 `low_confidence_not_confirmed` (`fields: ["counterparty"]`); değeri değiştirilen 0.4'lük alan onay kutusu istemez (`field_edited`); onayla → 200 (`field_confirmed`); eşik `Settings.metadata_confirm_threshold` | ✅ | aynı test; `services/document_review.classify_fields/unconfirmed_low_confidence` saf fonksiyonlar |
| O-05 | `review approve` yalnızca hedef dept müdürü (yükleyen 403, admin 403, meslektaş/management/başka müdür 404); onay öncesi meslektaşın `/api/ask`'ı boş ve LLM çağrısız, onay sonrası chunk retrieval'da ve cevap var | ✅ | `test_only_the_target_departments_manager_reviews_and_approval_publishes` |
| O-06 | `request_changes` yorumsuz 422 `comment_required`; `changes_requested`; yükleyen yorumu detayda görür, `?review_status=changes_requested` listesinde; yeniden `submit` → `pending_review`, olay `resubmitted`, yorum sıfırlanır | ✅ | `test_request_changes_needs_a_comment_and_the_uploader_resubmits` |
| O-07 | Müdürü olmayan departmana upload (admin bile) → 409, diskte dosya ve `documents` satırı yok; `department=None` → 201 `pending_metadata` | ✅ | `test_upload_without_a_configured_approver_is_refused_before_anything_is_stored` |
| O-08 | Excel: personel workbook → `pending_metadata`; `inspect` yükleyene 200 / meslektaşa 404; `/api/excel/ask` kataloğu boş (LLM çağrısız, `excel_files: []`); önerisiz `submit` → `pending_review`; onay → meslektaş `inspect` 200 + listede | ✅ | `test_pending_workbook_stays_out_of_the_excel_catalogue_until_approved` |
| O-09 | Onaylı belgede admin `PATCH` (gerçek değişiklik) → `pending_review` + `metadata_changed_after_approval`; değişmeyen değer onayı düşürmez; `is_target_manager` kuralı | ✅ | `test_editing_an_approved_document_reopens_the_review_unless_the_manager_does_it` |
| O-10 | Bekleyen tadil (supersedes) orijinali gizlemez: meslektaşın `/api/ask`'ı orijinali bulur, tadil listede yok | ✅ | `test_a_pending_amendment_does_not_hide_the_current_document` |
| O-11 | `/visibility` bekleyen belge için yalnızca yükleyen + hedef dept müdürü + admin; `review_status` alanı | ✅ | `test_visibility_of_a_pending_document_lists_only_its_handlers` |
| O-12 | Kayıt defteri sırası `uploaded → submitted → approved` (aktörler doğru); yükleyen/müdür 403; bilinmeyen 404; `audit_log` 0 satır | ✅ | `test_review_events_are_admin_only_and_never_touch_the_audit_log` |
| O-13 | Migration `0013` boş DB'den head'e ve geri; mevcut satırlar `approved`; seed sonrası 74/74 `approved` | ✅ | `test_migrations` (head `0013`, tablo/kolon), canlı §4 |
| O-14 | Regresyon: `make test`, `make lint`, `--retrieval-only` 39/39, `validate-ledger` 0; canlı demo akışı curl ile LLM'siz | ✅ | §4 |

## 2. Yapılanlar

- **Model/migration:** `DocumentReviewStatus` enum + `documents.review_status` (NOT NULL DEFAULT `approved`, index), `review_comment`, `submitted_at`, `reviewed_at`, `reviewed_by_id`; `document_review_events` (`ReviewEventKind` 9 tür; Python-side `created_at` ki aynı istekte yazılan olaylar sıralı okunsun). Veri adımı yok — DEFAULT mevcut 74 belgeyi yayında tutar.
- **Kapı (ADR-004/024):** `AuthorizationScope.include_pending: bool = False`; `SqlDocumentIdsProvider`'ın üç sorgusu `approved` filtreli; yeni tek metot `list_pending_document_ids(uploaded_by_id, manager_department_slugs)`; `allowed_document_ids` üyelik dalına "bekleyenlerim" eklemesi (müdür: departmanlarının bekleyenleri; admin: hepsi; `management`: hiçbiri); `SingleDocumentIdsProvider` aynı kuralı taşır. İmza sabit; retrieval/ask/search/excel_ask/folders **kodu değişmedi**.
- **Upload:** `document_review.initial_status` (hedef dept'in kendi müdürü → `approved`); onaycısız departman → 409 dosya yazılmadan; `uploaded` (+`auto_approved`) olayları; supersedes öncülü `include_pending` ile aranır.
- **Yeni uçlar:** `POST /api/documents/{id}/submit` (1. aşama; `DocumentSubmitRequest` = 9 alan + `confirmed_fields`; `department_required`), `POST /api/documents/{id}/review` (2. aşama; `approve | request_changes` + yorum), `GET /api/documents?review_status=a,b` (kuyruk; liste artık `include_pending`), `GET /api/admin/documents/{id}/review-events` (admin).
- **Mevcut uçlar:** `suggest-metadata` admin **+ yükleyen**; `apply` admin-only kalır ama yayınlamaz, `_apply_metadata_change` ile T9'a tabi; `PATCH` aynı; detay/status/download/`inspect` `include_pending`; `/visibility` bekleyen belge için işleyenleri listeler + `review_status`.
- **Servis:** `services/document_review.py` saf kurallar (`is_target_manager`, `initial_status`, `status_after_submit`, `classify_fields`, `unconfirmed_low_confidence`), `repositories/document_review_repo.py`, `user_repo.list_department_managers`, `Settings.metadata_confirm_threshold` (`.env.example`).
- **Hata sözleşmesi:** `detail = {"code", "message"}` — AI-BalBal `client.ts` `detail.message`'ı okuyor; kodlar ADR-024'te.
- **Testler:** yeni `tests/test_document_review.py` (12 test, O-01..O-12); `department_fixtures.make_department_manager`; `test_migrations` head `0013` + tablo/kolon; mevcut testlerde uyarlama: departmana yükleyen 6 test müdür fixture'ı aldı (artık onaycısız departmana upload 409), `test_suggest_metadata_requires_admin` → "göremeyen çalışan 404" (uç yükleyene açıldı), Excel motor testleri (`test_excel_api` 5, `test_ask_router` 8 yükleme) `_publish` yardımcısıyla workbook'u doğrudan yayınlar (admin yüklemesi artık bekliyor), `test_folders._setup` iki müdür kurar; `FakeProvider` yeni metodu taşır.
- **Docs:** ADR-024 + ADR-004 satırı, DOMAIN_MODEL §3/§4/§5, SPEC_02 §4, README "Belge onay akışı — B-28" bölümü + öneri bölümü notları, PHASES.md (B-28 notu + **Phase 3.2 SORU 2 değişti** notu), NOT (§2 B-28 UYGULANDI + B-28b kalanlar + B-18 notu + **Tansu'ya 3 kalemlik to-do**, §5.2 UYGULANDI, §7.1 satır 3, §7.2 #7 KAPANDI).
- **Dokunulmayanlar:** `retrieval.py`, `ask.py`, `excel_ask.py`, `search.py`, `folders.py`, `ocr-worker`, prompt, eval seti, `metadata_suggestion.py`, seed (`create_*` varsayılan `approved`), AI-BalBal.

## 3. Değişen dosyalar

Kod: `backend/alembic/versions/0013_document_review.py` (yeni), `app/models/{document,__init__}.py`, `app/models/document_review_event.py` (yeni), `app/schemas/{authorization,document}.py`, `app/services/authorization.py`, `app/services/document_review.py` (yeni), `app/repositories/{document_repo,user_repo}.py`, `app/repositories/document_review_repo.py` (yeni), `app/api/{documents,excel,router}.py`, `app/api/admin_documents.py` (yeni), `app/core/config.py`, `infra/.env.example`. Testler: `tests/test_document_review.py` (yeni), `tests/{department_fixtures,test_authorization,test_documents,test_folders,test_excel_api,test_migrations}.py`. Docs: `README.md`, `docs/{ARCHITECTURE,DOMAIN_MODEL,PHASES}.md`, `docs/SPEC_02_…md`, `docs/notes/TANSU_…md`, bu rapor.

## 4. Testler ve canlı doğrulama

- Geliştirme sırasında kırmızılar (hepsi test tarafı ya da beklenen davranış değişikliği): 17 mevcut test onaycısız departmana yükleme (409) ya da admin yüklemesinin beklemesi (katalog boş) yüzünden kırıldı → müdür fixture'ı / `_publish` (ilk tam turda 5 `test_ask_router` kırmızısı aynı sebeple, ikinci turda yeşil); yeni testlerde `management` kullanıcısı commit edilmemişti (FK), olay sırası `set` yüzünden belirsizdi (→ `sorted(provided)` + Python-side `created_at`), Excel dizini yolu container'da farklıydı (→ `test_excel_api.EXCEL_DIR`). Lint: mypy `role_ids` yeniden tanımı, import sırası, E501'ler.
- `make test`: **480 geçti (468 + 12 yeni), 15 deselected, 8 dk 49 sn; ocr-worker 9 geçti**. `make lint`: **0 error(s)** (ruff + format + mypy 106 dosya). `make validate-ledger`: 0 error(s), 0 warning(s). `--retrieval-only`: **recall@80 39/39 (%100), `EVAL_EXIT=0` — bekleyen belge yoktu, kapı filtresi 74 onaylı belgeyi aynen bıraktı**.
- **Canlı O-13/O-14** (`make up` → migration `0013`; curl, LLM yok):

```text
backend logs: Running upgrade 0012 -> 0013 … ; alembic_version = 0013
documents: approved = 74 (70 belge + 4 workbook) — başka durum yok

hukuk (employee, departmanın müdürü yok) upload department=hukuk →
  409 {"detail":{"code":"approver_not_configured","message":"Bu departman için onaylayıcı tanımlı değil; sistem yöneticinize başvurun."}}
finans (employee) upload Covenant_Report.xlsx kopyası, department=finans → 201 (ingestion ready, xlsx)
  finans   GET /api/documents → listede (16); ?review_status=pending_metadata → 1
  yonetim  GET /api/documents → yok (74)            — management genel ayrıcalık taşımaz
  finans_mudur ?review_status=pending_review → 0    — henüz 1. aşama yapılmadı
  admin    ?review_status=pending_metadata → listede (1)
  /api/search?q="B28 Canli Test Finans": finans → False, yonetim → False   — aramaya girmedi
finans POST /review approve → 403 not_the_approver
finans POST /submit {} (Excel, öneri yok) → review_status: pending_review
  finans_mudur ?review_status=pending_review → listede (1); yonetim → yok
yonetim POST /review → 404 (belgeyi göremez)
finans_mudur POST /review request_changes (yorumsuz) → 422 comment_required
finans_mudur POST /review approve → review_status: approved, reviewed_at dolu
  yonetim GET /api/documents → listede (75); /api/search → True       — yayınlandı
admin GET /api/admin/documents/{id}/review-events →
  [('uploaded','Proje Finans'), ('submitted','Proje Finans'), ('approved','Proje Finans Müdürü')]
finans GET …/review-events → 403
Temizlik: canlı test belgesi silindi (documents = 74).
```

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| `submit` için departman zorunlu (422 `department_required`) | departmansız belgenin onaycısı yok → sonsuz `pending_review` oluşmasın; yükleyen `submit` gövdesinde departmanı verebilir | plana ek; Naci'nin "department=None admin kuyruğunda kalır" kararıyla uyumlu (upload kabul, yayın için departman şart) |
| Olaylar için Python-side `created_at` | aynı transaction'da `now()` tüm olaylara aynı değeri verir, defter sırasız okunur | `server_default` yedek olarak kalır |
| `submit` alanları alfabetik işlenir | `model_fields_set` kümesi sırasız → olay sırası deterministik | — |
| `suggest-metadata` yükleyene açıldı | 1. aşama için öneriyi tetikleyebilmeli (arka plan taraması zaten üretir) | eski "admin-only 403" testi "göremeyen 404" oldu |
| `apply` admin-only kaldı, yayınlamaz | Phase 3.2 SORU 2'nin yerini `submit`/`review` aldı; dondurulmuş UI'nın admin paneli kırılmaz | PHASES.md notu |
| Excel `inspect` `include_pending`, `/api/excel/ask` varsayılan scope | yükleyen kendi bekleyen workbook'unu inceler; hesap yalnızca onaylıyla | SORU 3 |
| T9 "müdür istisnası" şimdilik yalnızca saf kuralda | müdürün metadata düzenleme ucu yok (`PATCH`/`apply` admin-only) | B-26 "write = metadata düzenleme değil" kararıyla tutarlı; ileride müdür ucu açılırsa kural hazır |
| Kayıt defterine rol/üyelik olayları girmez | B-08 SORU 2 — ayrı iş | — |
| `uploaded_by_id` NULL belgeler (seed) | yükleyen yok → `submit` edilemez; zaten `approved` | — |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. **Tansu'ya (NOT §2 B-28 to-do):** 1. aşama ekranı (`submit`, 0.8 altı "Onaylıyorum" kutusu, `detail.fields`), müdür kuyruğu + `review` ekranı, `review_status` rozeti/`review_comment`. Dondurulmuş `b219600`'da personelin 1. aşamayı yapacağı düğme yok — akış backend'de tam, UI'da Tansu'yu bekler.

## 7. Riskler / sonraki adım için notlar

- **Demo etkisi (kabul edildi):** `hukuk`/`enerji_grubu`'na personel yüklemesi müdür atanana kadar 409 — B-18'de `hukuk_mudur`/`enerji_mudur`.
- B-28b (ayrı faz): `extra_fields`, `tag_catalog`, tür bazlı alan rehberi, klasör önerisi, 4.7.9/1 yerleştirme onayı.
- B-01 agenda `kind: approval` = `GET /api/documents?review_status=pending_review`'ın sarmalanması; B-02 bildirimleri `changes_requested`/`approved` olaylarından türeyebilir (defter hazır).
- Upload'ta `confidentiality` alanına yükleyen rolüne göre sınır hâlâ yok (B-08 raporu §7) — 2. aşama bunu kısmen kapatır (müdür onaylamadan `board` belge yayına girmez), tam kural B-28b.

## 8. Doğruladığım üçüncü taraf davranışları

- PostgreSQL 16: `ADD COLUMN … NOT NULL DEFAULT 'approved'` enum tipiyle mevcut satırları tek adımda doldurdu; iki yeni enum tipi + tablo downgrade'de temiz düşüyor (`test_migrations`).
- FastAPI: `HTTPException(detail=dict)` JSON gövdede `detail` nesnesi olarak çıkıyor; AI-BalBal `client.ts:39-40` `detail.message`'ı okuyor (frontend koduyla doğrulandı).
- SQLAlchemy: `default=lambda: datetime.now(UTC)` + `server_default=func.now()` birlikte sorunsuz; sıralama `created_at, id`.

## 9. Kaynak kullanımı

- LLM: 0 çağrı (testlerde `FakeLLMClient`; canlı akışta öneri olmadan `submit` kullanılamayacağı için canlı belge Excel ya da öneri satırı elle yazılarak — §4'te belirtildi). Test süresi: 8 dk 49 sn (backend) + 5,8 sn (ocr-worker).
