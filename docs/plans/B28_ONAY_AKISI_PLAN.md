# B-28 — İki aşamalı belge onay akışı + §7.2 #7 — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: NOT `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §2 B-28 (çekirdek), §3.3 (iki karar — KAPANDI), §5.2 (akış — "yönetici" = hedef departmanın kendi `department_manager`'ı, KAPANDI 30.09), §5.1 (kural sabit, kişiyi müşteri seçer), §7.2 #7 (açık nokta 2–3); BACKEND_GAPS `b219600` §4.2 (B-12 → B-28), §4.7 (4.7.5 %80 eşiği + "onaylanmamış belge aramada/Balbal'da yok", 4.7.6 kayıt defteri, 4.7.9 açık noktalar), §5.1 (`GET /api/me/agenda` `kind: approval`); `docs/plans/PHASE_3_2_PLAN.md:207-209` SORU 2 ("kabul yetkisi yalnızca admin mi?" → Naci: admin) ve `docs/reports/PHASE_3_2_REPORT.md` §2 (admin-only `apply`/`reject`); B-08 planı/raporu.

Okunanlar (kod): `api/documents.py` (upload `:187-333`, list/download/status, `_get_authorized_document`, `suggest-metadata`/`apply`/`reject` `:425-504`, `PATCH`, `/visibility`), `services/authorization.py`, `schemas/authorization.py` (`AuthorizationScope`), `repositories/document_repo.py` (`create_with_job`, `create_ready`, `list_ids_pending_suggestion`, `SqlDocumentIdsProvider`), `services/{excel_ask,retrieval,ask,metadata_suggestion}.py`, `api/{excel,search,folders}.py`, `models/{document,document_metadata_suggestion,folder}.py` (`FolderGrantEvent` deseni), `services/demo_documents_seed.py`, `core/config.py`, `tests/*` (`Document(` doğrudan kuran 10 dosya, 7 `_document` helper), AI-BalBal `b219600` `api/documents.ts`, `pages/department/UploadTab.tsx`, `components/MetadataSuggestionPanel.tsx` (`isAdmin`), `api/proposed.ts` (`AgendaItem`).

---

## 0. Önce bir düzeltme — `review_status` bugün yok

Naci'nin sorusu "Aşama E'de zaten *onay bekleyen belge görünmez* kuralı vardı (`review_status=approved` koşulu `allowed_document_ids`'e girmişti) — neyin üzerine inşa edilmişti?" varsayımıyla geliyor. **Kodda böyle bir şey yok:** `grep review_status backend/app` → 0 sonuç; `docs/plans/ASAMA_E_PLAN.md` ve `docs/reports/ASAMA_E_REPORT.md`'de de geçmiyor. 30.09.2026'da §3.3/§5.2'de **karar** olarak kaydedildi ("gate'e `review_status = approved` koşulu girer; `SingleDocumentIdsProvider` aynı koşulu taşır; seed'in 74 belgesi `approved` olmalı") ama hiçbir faz onu uygulamadı — Aşama E yalnızca klasörleri yaptı. Bugün bir belge `ingestion_status = ready` olduğu anda `allowed_document_ids` içindedir ve retrieval/arama/Balbal'a girer (ADR-006/021); metadata önerisi görünürlüğü etkilemez.

Dolayısıyla B-28 **sıfırdan** şu temelin üzerine kurulur: ADR-004 tek kapı (12 çağrı noktası, aşağıda T2), Phase 3.2 öneri akışı (`document_metadata_suggestions`, admin-only `apply`/`reject`), B-08 `department_manager` rolü, B-26 klasör `write` kontrolü ve Tansu #6 üyelik kontrolü (upload'ta "departman ⊆ yükleyenin departmanları").

---

## 1. Tespitler

- **T1 — Üç ayrı eksen karıştırılmamalı.** `ingestion_status` (dosya hattı: uploaded→ocr→ready/failed, ocr-worker yazar), `status` (belgenin hukuki yaşam döngüsü: draft/executed/amended/superseded/active), `document_metadata_suggestions.status` (AI önerisi: pending/applied/rejected/failed). B-28 **dördüncü** ekseni ekler: **yayın/onay durumu** `documents.review_status`. Hiçbiri diğerinin yerine kullanılmaz (§5.2: "öneri durumu ≠ belge onay durumu").
- **T2 — Kapının 12 çağrı noktası iki sınıfa ayrılıyor.** *İçerik yolları* — `retrieval.py:71` (→ `/api/ask`), `ask.py:150` (zincir yükleme), `excel_ask.py:221,413` (`/api/excel/ask`, katalog), `search.py:40`, `folders.py:201` (`document_count`) — **yalnızca `approved`** görmeli (§3.3 kararı). *Belgeyle çalışma yolları* — `documents.py` list `:343`, download `:363`, status `:392`, `_get_authorized_document` `:404` (detay, öneri uçları, PATCH), supersedes öncülü `:261`, `/visibility` `:544`, `excel.py:79` (`inspect`) — yükleyenin **kendi bekleyen** belgesini ve onaycının **kuyruğunu** görebilmesi gerekir; aksi halde personel yüklediği belgeyi bir daha göremez, müdür onaylayacağı belgeyi açamaz. Çözüm kapının **içinde** (CLAUDE.md: kapıyı atlayan kod yolu yasak): `AuthorizationScope.include_pending: bool = False`. Varsayılan (`False`) = onaylılar; `True` = onaylılar **+** kullanıcıya ait bekleyenler (T3). İçerik yolları hiçbir şey değiştirmez (varsayılan); belgeyle çalışma yolları `include_pending=True` verir. "Scope yalnızca daraltır" ilkesi korunur: `approved`-only varsayılan daralmanın kendisidir, `include_pending` yalnızca kullanıcının **kendi** bekleyen belgelerini ekler ve sonuç yine ⊆ provider çıktısı.
- **T3 — Bekleyen belgeyi kim görür (kapı kuralı):** `review_status != approved` bir belge yalnızca (a) **yükleyeni** (`uploaded_by_id`), (b) hedef departmanın **`department_manager`'ı** (üyelik, B-08) ve (c) **`admin`** (sistem; destek incelemesi, 4.7.6) tarafından, `include_pending=True` ile görülür. `management` görmez (§5.2: genel ayrıcalık yok; onaycı değil). Provider'a **bir** metot: `list_pending_document_ids(*, uploaded_by_id, manager_department_slugs) -> ids` (Phase 1.2/E deseni; imza sabit).
- **T4 — Kim onaysız yayınlar (KAPANDI, §5.2):** yalnızca **belgenin hedef departmanının kendi `department_manager`'ı** (`department ∈ yükleyenin üyelikleri` **ve** rol `department_manager`) → `approved` anında, olay `auto_approved`. `employee`, `management`, `admin` ve başka departmanın müdürü → iki aşama. B-08 planındaki "yönetici kendi belgesini onaysız ekler" cümlesi **bu dar anlamdadır** ve hâlâ geçerli; `management`/`admin` için **geçerli değil** (soru 4'ün cevabı; §5.2 KAPANDI 30.09, Naci'nin literal örneği). Pratik sonuç: `admin` API'den belge yüklerse de hedef departmanın müdürünü bekler (seed bu yolu kullanmaz, repo'ya doğrudan `approved` yazar).
- **T5 — Durum makinesi (kodda, LLM tetiklemez, P-1/5):**
  ```
  pending_metadata ──submit (yükleyen)──▶ pending_review ──approve (hedef dept müdürü)──▶ approved
        ▲                                     │
        └──────── request_changes (müdür, yorum) ──▶ changes_requested ──submit (yükleyen) ──▶ pending_review
  upload (yükleyen = hedef dept'in kendi müdürü) ──▶ approved  [auto_approved]
  approved ──metadata değişikliği (T9)──▶ pending_review
  ```
  `rejected` terminal durumu **yok** (Tansu'nun akışında "yorumla geri gönderir" var, "reddeder" yok; silme ucu da yok) → SORU 3.
- **T6 — 1. aşama = Phase 3.2'nin `apply`'ının yükleyene devredilmiş ve zorunlu kılınmış hali.** `POST /api/documents/{id}/submit` gövdesi: nihai metadata alanları (bugünkü `MetadataSuggestionApplyRequest` seti) + `confirmed_fields: list[str]`. Sunucu: öneride güveni `< metadata_confirm_threshold` (`Settings`, varsayılan **0.8**, `.env.example`) olan bir alan **öneri değeriyle** kaydediliyorsa ve `confirmed_fields`'ta yoksa → 422 `low_confidence_not_confirmed` (4.7.5: "kural arayüze bırakılmaz"). Yükleyen değeri değiştirdiyse bu açık karardır (olay `field_edited`), onay kutusu gerekmez. Öneri yoksa/`failed` ise (Excel'de hiç yok — T7) submit **elle girilen alanlarla** serbesttir: AI yardımcıdır, son onay insandadır (P-1); öneri **bekleniyorsa** (`ingestion_status=ready`, satır yok, tarama 15 sn) 409 `suggestion_pending` ile kısa bekleme — SORU 5. `submit` öneri satırını `applied` yapar; **Phase 3.2 SORU 2 kararı burada tersine döner:** `apply` artık yayınlama eylemi değil (T10).
- **T7 — Excel aynı akışa girer (plan önerisi, Naci SORU 3 "evet").** Etkisi küçük ve otomatik: `excel_ask.answer_data_question` ve `workbook_document_ids` kapıyı **varsayılan** scope ile çağırıyor → bekleyen workbook katalogdan ve `DATA`/`MIXED` cevabından **kendiliğinden** düşer; `excel.py:79 inspect` yükleyenin kendi bekleyen workbook'unu incelemesi için `include_pending=True` alır. Excel'de AI önerisi yok (sayfa/chunk yok, ADR-006 Phase 4.2) → 1. aşama yükleyenin elle doldurduğu alanları teyididir; %80 kuralı uygulanacak öneri yoktur. Router `DATA` seçer ama tek workbook bekliyorsa → bugünkü `missing_data` yolu (chunk/kaynak yok), yeni uyarı türü yok. **Onaysız workbook'la hesap yapılmaz** cümlesi böylece koda değil kapıya dayanır.
- **T8 — `department_manager` yoksa (§7.2 #7 / §5.2 açık nokta 2).** Plandaki "409 `approver_not_configured` + admin'e bildirim" önerisinin ikinci yarısı **bugün yapılamaz**: `notifications` tablosu/ucu yok (B-02), `GET /api/me/agenda` yok (B-01) — `grep agenda|notification backend/app` → 0. Uygulanabilir kısım ve iki yol:
  - **(a) Upload anında 409 (önerim):** `department` çözüldükten sonra, yükleyen hedef departmanın kendi müdürü **değilse** ve o departmanın aktif bir `department_manager` üyesi **yoksa** → `409 approver_not_configured` (Türkçe: "Bu departman için onaylayıcı tanımlı değil; sistem yöneticinize başvurun."), dosya diske yazılmadan (supersedes kontrolüyle aynı yer). Belge limboda kalmaz; admin'in yapacağı tek şey `PATCH /api/users/{id}` ile rol vermek. Olay: WARNING log + `document_review_events` yazılamaz (belge yok) → log yeterli.
  - **(b) Kabul et, `pending_review`'da beklet, admin kuyruğunda göster:** belge var ama onaycı yok; B-01 gelince `approval` kaleminde admin'e düşer. Bugün admin'in bunu göreceği tek yer `GET /api/documents?review_status=pending_review` (T11) — "bildirim" değil.
  - **Fallback onaycı = admin?** §5.2 KAPANDI bunu kapatıyor ("sistem admin'i değil"); planda **önerilmiyor**, SORU 1'de açıkça soruluyor çünkü demo'da yalnızca `finans`'ın müdürü var (B-08): (a) ile `hukuk`/`enerji_grubu`'na personel yüklemesi 409 alır — doğru davranış ama demo'da görünür. Çözüm demo tarafında: B-18 ile `hukuk_mudur`/`enerji_mudur` eklenir ya da admin PATCH ile atar.
- **T9 — Onaydan sonra değişiklik onayı düşürür (P-1/4, §5.2).** `PATCH /api/documents/{id}` (admin elle düzenleme) ve `apply` bir **`approved`** belgenin metadata'sını değiştirirse → `pending_review` + olay `metadata_changed_after_approval`; **istisna:** aktör hedef departmanın kendi müdürüyse `approved` kalır (onaycının kendisi değiştiriyor). İçerik değişikliği (yeni dosya) zaten yeni belge/versiyondur (supersedes), aynı belgenin dosyası değişmez → yalnızca metadata ekseni. SORU 4.
- **T10 — Mevcut uçların kaderi.** `suggest-metadata`: admin **+ yükleyen (kendi bekleyen belgesi)** tetikleyebilir (arka plan taraması zaten herkes için üretir; değişiklik küçük). `apply`: admin-only **kalır**, ama artık yalnızca metadata yazar ve T9'a tabidir; yayın etkisi yok (dondurulmuş UI'daki admin paneli çalışmaya devam eder). `reject`: değişmez. Yeni: `submit` (1. aşama, yükleyen), `review` (2. aşama, müdür), `GET /api/documents?review_status=…` (kuyruk, T11), `GET /api/admin/documents/{id}/review-events` (kayıt defteri, admin, 4.7.6). PHASES.md'ye not: "Phase 3.2 SORU 2 kararı (yayın = admin `apply`) Tansu #5 iki aşamalı onayla değiştirildi."
- **T11 — Kuyruk ucu B-01 yerine değil, B-01'in kaynağı.** `GET /api/documents` `review_status` filtresi alır ve `include_pending=True` ile çalışır: müdür `?review_status=pending_review` → kendi departmanlarının bekleyenleri; personel `?review_status=pending_metadata,changes_requested` → kendi yüklemeleri. B-01 `agenda` ileride bu sorguyu `kind: approval` olarak sarar. `DocumentListItem`/`DocumentDetailResponse` **`review_status`** alanı kazanır (+ detayda `review_comment`, `reviewed_at`).
- **T12 — Kayıt defteri `document_review_events`** (append-only, `FolderGrantEvent` deseni; `audit_log` değil — ADR-016): `id, document_id (FK CASCADE), created_at, actor_user_id (SET NULL), actor_name, kind, field, before, after, confidence, comment`. `kind ∈ {uploaded, auto_approved, suggested, field_edited, field_confirmed, submitted, approved, changes_requested, resubmitted, metadata_changed_after_approval}`. NOT §2 B-28'deki `document_intake_events` adı bununla **birleşir** (tek tablo, iki ad yok). Okuma: admin-only (4.7.6 "kullanıcı ekranında görünmez"). Rol/üyelik olayları (B-08 SORU 2) **bu tabloya girmez** — ayrı iş.
- **T13 — Versiyon zinciri ve bekleyen belge.** Yükleyen bekleyen belgesinin üstüne yeni versiyon yükleyebilir (öncül `include_pending=True` ile görünür). `/api/ask` zinciri yalnızca onaylılarla kurar (`load_with_chains` her halkada allowed ile kısıtlı, ADR-021) → bekleyen bir tadil "gizli halef" sayılır, eski belge **GÜNCEL** kalır; onay gelince zincir kendiliğinden güncellenir. Davranış değişmez, testle kilitlenir.
- **T14 — Mevcut veri ve testler.** Migration tüm mevcut satırları `approved` yapar (§3.3: "74 belge approved" — bugün 70 + 4 workbook); kolon `NOT NULL DEFAULT 'approved'` ve model varsayılanı `approved` → testlerin 10 dosyadaki doğrudan `Document(...)` kurulumları ve 7 `_document` helper'ı **değişmeden** görünür kalır; `create_with_job`/`create_ready` `review_status` parametresi alır (varsayılan `approved`; seed ve ocr-worker dokunulmaz, yalnızca `upload_document` karar verir). "Bekleyen" yalnızca `/upload` yolundan doğar.
- **T15 — Dondurulmuş AI-BalBal (`b219600`):** personel yükler → belge `pending_metadata`; `UploadTab` `ready` görür, `MetadataSuggestionPanel` **`isAdmin` olmadan** apply düğmesi göstermez → personelin 1. aşamayı yapacağı düğme **yok**; liste `review_status` rozetini bilmiyor (alan fazladan gelir, kırılmaz). Yani akış backend'de tam, UI'da Tansu'nun `submit`/`review` ekranlarını bekler (BACKEND_GAPS canvas `Belge-Yukle.dc.html`). Tansu'ya to-do NOT'a yazılır.
- **T16 — Kapsam dışı (B-28'in geri kalanı, ayrı faz "B-28b"):** `extra_fields JSONB` (personelin eklediği alan), `tag_catalog` sabit etiket listesi, belge türüne göre alan rehberi (P-8), Balbal klasör önerisi, 4.7.9/1 "yazma yetkisi olmayan klasöre yerleştirme onayı". Bu faz **yalnızca onay akışı + kayıt defteri + %80 eşiği**.

---

## 2. Tasarım

### 2.1 Veri modeli (migration `0013_document_review`)

- Enum `document_review_status('pending_metadata','pending_review','changes_requested','approved')`.
- `documents.review_status` NOT NULL DEFAULT `'approved'` (+ index), `documents.review_comment TEXT NULL` (son `request_changes` yorumu), `documents.reviewed_at TIMESTAMPTZ NULL`, `documents.reviewed_by_id uuid NULL FK users SET NULL`, `documents.submitted_at TIMESTAMPTZ NULL`.
- `document_review_events` (T12), index `(document_id, created_at)`.
- Veri adımı: yok (DEFAULT mevcut satırları `approved` yapar). Downgrade: kolonlar + tablo + tip düşer.

### 2.2 Kapı (`authorization.py`, `schemas/authorization.py`, `document_repo.py`)

- `AuthorizationScope.include_pending: bool = False`.
- `DocumentIdsProvider`: mevcut üç metot **yalnızca `approved`** döndürür (`SqlDocumentIdsProvider`'ın üç sorgusuna `review_status = approved` koşulu). Yeni metot `list_pending_document_ids(*, uploaded_by_id: UUID, manager_department_slugs: Iterable[str]) -> Iterable[UUID]`: `review_status != approved AND (uploaded_by_id = :u OR department IN :slugs)`; admin için `manager_department_slugs=None` = tüm bekleyenler.
- `allowed_document_ids`: mevcut hesap aynen (approved kümesi) → `if scope.include_pending:` `pending = provider.list_pending_document_ids(uploaded_by_id=user.id, manager_department_slugs=(üyelik slug'ları if role==department_manager else ()) | None if admin)`; `management` için boş. Sonuç `scoped ∩ (role_ids ∪ pending)`. `scope.department/project_id` daraltması bekleyenlere de uygulanır (tek `list_document_ids(scope)` çağrısı: `include_pending` ise `approved` koşulu kaldırılmış aday küme, aksi halde approved).
- `SingleDocumentIdsProvider`: `review_status`'u bilir; approved değilse yalnızca `include_pending` + (yükleyen | hedef dept müdürü | admin) → `/visibility` bekleyen belge için "kim **görecek**" değil "kim **görüyor**" listesini döner (`review_status` alanı yanıtta).

### 2.3 Upload (`documents.py::upload_document`)

Sıra: mevcut kontroller (tür, departman üyeliği, klasör `write`, supersedes) → **onaycı kontrolü (T8a):** `is_target_manager = role == department_manager and department ∈ department_slugs`; değilse ve `department` dolu ve `user_repo.list_department_managers(session, department)` boşsa → 409 `approver_not_configured` (dosya henüz yazılmadı). `department=None` belgeler (bugün de yalnızca admin görür) → `pending_metadata`, onaycısı yok; T8a onları **engellemez**, admin kuyruğunda kalır (SORU 1'de netleşir). → dosya yazılır → `review_status = approved if is_target_manager else pending_metadata` → olay `uploaded` (+ `auto_approved`).

### 2.4 Uçlar

| Uç | Kim | Ne |
|---|---|---|
| `POST /api/documents/{id}/submit` | yükleyen (`uploaded_by_id == user`) — admin **değil** (P-1: "başkası adına 1. aşama 403") | durum `pending_metadata`/`changes_requested` değilse 409; gövde = nihai alanlar + `confirmed_fields`; %80 kontrolü (T6); alanları yazar (`apply_partial_update`), öneriyi `applied` yapar, olaylar (`field_edited`/`field_confirmed`/`submitted`), `pending_review` (ya da yükleyen hedef dept müdürüyse — rolü sonradan almış olabilir — `approved`) |
| `POST /api/documents/{id}/review` | hedef departmanın `department_manager`'ı (üyelik) | gövde `{decision: approve \| request_changes, comment}`; `pending_review` değilse 409; `request_changes` yorum zorunlu (422); olay + `reviewed_*` |
| `GET /api/documents?review_status=a,b` | herkes (kapı `include_pending=True`) | T11 |
| `GET /api/documents/{id}` / `status` / `download` / `inspect` / öneri uçları | kapı `include_pending=True` | yükleyen/müdür/admin bekleyeni görür |
| `GET /api/admin/documents/{id}/review-events` | `require_admin` | kayıt defteri (4.7.6) |
| `POST …/suggest-metadata` | admin **+ yükleyen** | T10 |
| `POST …/metadata-suggestion/apply`, `PATCH /{id}` | admin (değişmez) | T9 kuralı eklenir |

Hata ayrıntıları makine-okunur (`approver_not_configured`, `low_confidence_not_confirmed`, `suggestion_pending`, `review_state_conflict`) + Türkçe mesaj — AI-BalBal `product_not_enabled` deseniyle aynı.

### 2.5 Ayarlar

`Settings.metadata_confirm_threshold: float = 0.8` (`.env.example`: `METADATA_CONFIRM_THRESHOLD=0.8`, P-8 "eşik bir parametredir").

### 2.6 Seed / demo

Seed belgeleri `approved` (T14). Demo akışı canlı gösterim için: `finans` yükler → `pending_metadata` → `submit` → `finans_mudur` `review approve` → belge aramada görünür. `hukuk`/`enerji_grubu` için müdür yok → T8a 409 (SORU 1).

---

## 3. Dosyalar

`backend/alembic/versions/0013_document_review.py` (yeni) · `models/document.py` (+enum, 5 kolon) · `models/document_review_event.py` (yeni) · `schemas/authorization.py` (`include_pending`) · `services/authorization.py` (+pending dalı, `SingleDocumentIdsProvider`) · `repositories/document_repo.py` (`approved` koşulu ×3, `list_pending_document_ids`, `create_*` parametresi, `list_by_ids` filtre) · `repositories/document_review_repo.py` (yeni: olaylar, durum geçişleri) · `repositories/user_repo.py` (`list_department_managers(department_slug)`) · `services/document_review.py` (yeni: durum makinesi + %80 kontrolü, saf ve testlenebilir) · `api/documents.py` (upload, submit, review, list filtresi, scope'lar, T9/T10) · `api/admin_documents.py` (yeni, review-events) · `api/excel.py` (`inspect` scope) · `schemas/document.py` (+alanlar, `SubmitRequest`, `ReviewRequest`, `ReviewEventResponse`) · `core/config.py` · `infra/.env.example` · testler · docs (ADR-004 concretization + **ADR-024 "Belge yayın durumu ve iki aşamalı onay"**, DOMAIN_MODEL §4/§5/§6, SPEC_02 §4, README, NOT, PHASES.md "Phase 3.2 SORU 2 değişti" notu, rapor).

Dokunulmayanlar: `retrieval.py`, `ask.py`, `excel_ask.py`, `search.py`, `folders.py` kodu (yalnızca kapı varsayılanı etkiler), `ocr-worker`, prompt, eval seti, `metadata_suggestion.py` prompt'u, AI-BalBal.

---

## 4. Kabul kriterleri

| # | Kriter | Test |
|---|---|---|
| O-01 | `employee` upload → `pending_metadata`; liste/arama/`/api/ask`/`/api/excel/ask`'ta **görünmez** (aynı departmanın başka çalışanı, `management`, hatta yükleyen varsayılan scope'ta); yükleyen `GET /api/documents` ve `GET /{id}`'de görür | API testleri (`test_documents`, `test_ask`, `test_search`, `test_excel_api`) |
| O-02 | Hedef departmanın kendi `department_manager`'ı upload → anında `approved`, olay `auto_approved`; başka departmanın müdürü, `management`, `admin` upload → `pending_metadata` | `test_document_review` |
| O-03 | `submit`: yalnızca yükleyen (başkası 403, admin dahil); `pending_metadata`/`changes_requested` dışında 409; alanlar yazılır, öneri `applied`, durum `pending_review`, olaylar yazılır | birim (`services/document_review`) + API |
| O-04 | %80: öneri güveni 0.6 olan alan öneri değeriyle, `confirmed_fields`'ta yokken → 422; `confirmed_fields` ile → 200 + `field_confirmed`; değer değiştirilmişse onay kutusu gerekmez (`field_edited`); eşik `Settings`'ten | birim + API |
| O-05 | `review approve` yalnızca hedef departmanın müdürü (employee/management/admin/başka müdür → 403); `pending_review` dışında 409; sonra belge aramada/Balbal'da/Excel katalogunda görünür | API (`test_ask` ile uçtan uca: onay öncesi "bilgi bulamadım", sonrası cevap) |
| O-06 | `request_changes` yorum zorunlu; durum `changes_requested`, yükleyen yorumu detayda görür, yeniden `submit` → `pending_review` (`resubmitted`) | API |
| O-07 | T8a: müdürü olmayan departmana personel/admin upload → 409 `approver_not_configured`, diskte dosya yok, `documents` satırı yok; hedef departmanın kendi müdürü → 201 `approved` | API + `documents_dir` kontrolü |
| O-08 | Excel: personel workbook yükler → `pending_metadata`; `/api/excel/ask` katalogu onu içermez (deterministik `missing_data`); `inspect` yükleyene açık, başkasına 404; `submit` (öneri olmadan) → `pending_review` → onay → katalogda | `test_excel_api` |
| O-09 | T9: `approved` belgede admin `PATCH` → `pending_review` + olay; hedef dept müdürünün `PATCH`'i → `approved` kalır | API |
| O-10 | Versiyon zinciri: bekleyen tadil → `/api/ask` eski belgeyi GÜNCEL sayar; onaydan sonra tadil GÜNCEL | `test_version_chain`/`test_ask` |
| O-11 | `/visibility`: bekleyen belge için kullanıcı listesi yalnızca yükleyen + hedef dept müdürü + admin; yanıt `review_status` taşır | API |
| O-12 | Kayıt defteri: tam akışta olaylar sırayla (`uploaded, suggested, field_edited, field_confirmed, submitted, approved`), `before/after/confidence` dolu; `GET /api/admin/documents/{id}/review-events` admin-only (employee 403), `audit_log`'a hiçbir satır yazılmaz | API + `audit_log` sayımı |
| O-13 | Migration `0013` boş DB'den head'e ve geri; mevcut satırlar `approved`; `make seed` sonrası **74/74** belge `approved` (`make eval --retrieval-only` 39/39 bunu dolaylı kanıtlar) | `test_migrations` + canlı |
| O-14 | Regresyon: `make test`, `make lint` yeşil; `--retrieval-only` 39/39; `validate-ledger` 0; canlı demo akışı (`finans` upload → `submit` → `finans_mudur` approve → `/api/search` bulur; onay öncesi bulmaz) curl ile, LLM'siz | komut çıktıları |

LLM çağrısı: 0 (öneri üretimi testlerde `FakeLLMClient`; canlı akışta `suggest-metadata` kullanılmaz, elle alanlarla `submit`).

---

## 5. Kendi aldığım küçük kararlar (raporda listelenir)

- `include_pending` scope bayrağı + tek yeni provider metodu (kapı dışına çıkan ikinci yol yok).
- `review_status` DEFAULT `approved` (mevcut veri, seed, testler, ocr-worker dokunulmaz; "bekleyen" yalnızca `/upload`'dan doğar).
- `document_review_events` tek tablo (NOT'taki `document_intake_events` adı buna katlanır); admin-only okuma.
- `submit`/`review` ayrı uçlar; `apply` admin-only kalır ama yayın etkisi yok.
- Makine-okunur `detail` kodları + Türkçe mesaj.
- Durum makinesi `services/document_review.py`'de saf fonksiyonlar (geçiş tablosu), API ince.
- ADR-024 yazılır (yeni mimari karar: yayın durumu kapıya giriyor).

---

## SORU (Naci cevaplamalı)

1. **Müdürü olmayan departman (T8):** **(a)** upload anında `409 approver_not_configured`, dosya yazılmaz (önerim — belge limboda kalmaz, admin'in tek işi rol vermek; "admin'e bildirim" B-02 gelince eklenir, bugün WARNING log) — **(b)** kabul et, `pending_review`'da beklet, admin `?review_status=pending_review` ile görür. İkisinde de **admin fallback onaycı değil** (§5.2 KAPANDI). `department=None` belgeler: 409 **almaz**, admin kuyruğunda kalır — uygun mu? Demo etkisi: `hukuk`/`enerji_grubu`'na personel yüklemesi (a) ile 409 → B-18'de `hukuk_mudur`/`enerji_mudur` eklenmeli (ya da PATCH ile).
2. **`management`/`admin` muafiyeti yok** (T4): API'den yükledikleri belge de hedef departmanın müdürünü bekler. 30.09 kararının aynen uygulanması — teyit.
3. **Terminal `rejected` durumu** gerekli mi? Önerim **hayır** (Tansu'nun akışında yok; `changes_requested` + yeniden `submit`); gerekirse "sil" ucu ayrı iş.
4. **T9 — onaydan sonra metadata değişikliği `pending_review`'a düşürür; istisna hedef dept müdürü.** Admin `apply`/`PATCH` yaptığında da düşsün mü (önerim evet — admin onaycı değil), yoksa admin düzenlemesi `approved`'ı korusun mu?
5. **Öneri henüz yokken `submit`:** öneri bekleniyorsa (`ready`, satır yok) 409 `suggestion_pending` ile kısa bekleme mi (önerim), yoksa önerisiz hemen kabul mi? Excel'de her zaman önerisiz kabul (öneri yok).
6. **Kayıt defteri okuma ucu admin-only** (4.7.6) — hedef dept müdürü de kendi departmanının olaylarını görsün mü? Önerim **şimdilik admin-only**.
7. Faz adı/etiket: etiketsiz düz commit + PHASES.md notu (öncekiler gibi) + **ADR-024** — teyit.

---

## Uygulama sırası

1. Migration `0013` + model + `test_migrations`.
2. Kapı: scope bayrağı, provider koşulu/metodu, `allowed_document_ids` dalı, `SingleDocumentIdsProvider`; `test_authorization` (bekleyen kuralı, `management` görmez, varsayılan scope approved-only).
3. `services/document_review.py` (durum makinesi + %80) + birim testleri.
4. Upload kararı + T8a; `submit`/`review`/liste filtresi/olay ucu; scope'lar; T9/T10; API testleri.
5. Excel yolu (O-08), zincir (O-10), visibility (O-11).
6. `make test`, `make lint`, `--retrieval-only`, `validate-ledger`; canlı O-14 (curl, LLM'siz).
7. Docs: ADR-024 + ADR-004 satırı, DOMAIN_MODEL, SPEC_02 §4, README, PHASES.md (Phase 3.2 SORU 2 notu), NOT (§2 B-28 UYGULANDI, §7.2 #7 KAPANDI, Tansu to-do: `submit`/`review` ekranları, `review_status` rozeti, kuyruk) → rapor → commit → çapraz referans → push → dur.
