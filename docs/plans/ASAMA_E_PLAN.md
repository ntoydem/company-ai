# Aşama E — Klasörler ve departman erişim yetkileri (B-26) — Uygulama Planı

**Tarih:** 01.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: BACKEND_GAPS (dondurulmuş `b219600`) §2.6 (B-26: kurallar 2.6.1, uçlar 2.6.2, veri modeli 2.6.3, kabul 2.6.5); AI-BalBal `b219600` `api/proposed.ts` §10 (`FolderGrant`, `AdminFolder`, `UserFolder`, `FolderAuditEntry`, uçlar), `pages/admin/AdminFoldersPage.tsx`, `pages/department/{DocumentsTab,UploadTab}.tsx`, `lib/folders.ts`, `types.ts:68` (`DocumentListItem.folder_id?`); NOT §2 B-26 (4 "değişmesi gereken" madde; 3. madde güvenlik yamasıyla kapandı), §5.1, §8.1 (Tansu 01.10.2026: klasör ağacını **müşteri admin'i** kurar). Tasarım ilkesi (Naci): klasör ağacı admin ekranından kurulur, `folder_grant_events` `audit_log`'dan ayrı, **`allowed_document_ids` tek yetki kapısı kalır** — B-26 ikinci bir motor açmaz, mevcut fonksiyona entegre olur.

Okunanlar: `backend/app/services/authorization.py` (gate + `SingleDocumentIdsProvider`), `repositories/document_repo.py::SqlDocumentIdsProvider`, `api/documents.py` (upload, list, `/visibility`), `models/{document,department}.py`, `tests/test_authorization.py::FakeProvider`, Phase 1.2/5.2 planları; `docs/ARCHITECTURE.md` ADR-004/ADR-016.

---

## 1. Tespitler

- **T1 — Frontend sözleşmesi hazır ve dar.** `proposed.ts` §10: `GET /api/admin/folders` → `AdminFolder{id, name, parent_id, owner_department_slug, grants[{department_slug, access: read|write, inherited}], document_count}`; `POST /api/admin/folders {name, parent_id, owner_department_slug}`; `PUT /api/admin/folders/{id}/grants {grants:[{department_slug, access: none|read|write}]}` (yalnızca **bu klasörde tanımlı** yetkiler gönderilir, `none` = tanımı kaldır → miras geçerli; `AdminFoldersPage.tsx:218-222`); `GET /api/admin/folders/audit` → `FolderAuditEntry{id, created_at, actor_name, folder_id, folder_name, department_slug, before, after}`; `GET /api/folders` → `UserFolder{id, name, parent_id, owner_department_slug, access: read|write, document_count}`. BACKEND_GAPS §2.6.2'deki `PATCH`/`DELETE`/`access-matrix` uçlarını frontend **çağırmıyor** (matrisi istemci kuruyor, `:155-174`). Alan adları birebir korunursa `AdminFoldersPage`, `DocumentsTab` klasör görünümü ve `UploadTab` klasör seçimi **kendiliğinden** devreye girer (`DocumentsTab.tsx:28-31`: `useMyFolders` dolu gelince klasör moduna geçer).
- **T2 — `UploadTab` zaten `folder_id` gönderiyor ve `department`'ı klasörün sahibinden türetiyor** (`:80-83`); backend bugün alanı yok sayıyor (FastAPI bilinmeyen form alanını atar). `DocumentsTab` belgeyi `folder_id` ile alt ağaca süzüyor (`:101-106`, `types.ts:68` `folder_id?: string | null`) → `DocumentListItem.folder_id` şart.
- **T3 — Çocuk klasörün sahibi üstünden gelir.** `AdminFoldersPage.tsx:355`: `owner_department_slug: parent?.owner_department_slug ?? owner` — frontend çocuk için sahibi üstten alıyor; backend de bunu **kural** yapar (alt klasör sahibi = üstün sahibi; aksi 422). Böylece "belgenin departmanı = klasörün sahibi" (2.6.1/3) ağaçta tutarlı kalır.
- **T4 — Miras modeli (2.6.1/5) frontend'in beklediği biçimde:** bir departmanın bir klasördeki etkin yetkisi = **kendisinde ya da en yakın üstünde tanımlı** yetki; hiçbirinde yoksa `none`. Alt klasörde tanım üsttekini **değiştirir** (read↔write); "üstte var, altta yok" diye bir geri alma yok (`PUT`'ta `none` = tanımı sil = mirasa dön). Görünürlük için `read ⊆ write`.
- **T5 — Gate'e entegrasyon, imza sabit.** `allowed_document_ids(user, scope, provider)` değişmez (ADR-004). `DocumentIdsProvider`'a Phase 1.2'deki gibi **bir** metot eklenir: `list_document_ids_for_folder_grants(department_slugs, confidentiality_levels)` → o departmanlara (doğrudan ya da miras) yetki verilmiş klasörlerin alt ağacındaki, gizlilik düzeyi uygun belgeler. `employee` dalı: `üyelik_belgeleri ∪ klasör_grant_belgeleri`, ikisi de `scoped_ids` ile kesilir. `management`/`admin` dalları **değişmez** (zaten her şeyi görür, 2.6.1/6). Gizlilik: aynı `_EMPLOYEE_CONFIDENTIALITY_LEVELS` (`normal`) — klasör yetkisi gizliliği aşmaz (2.6.1/6). Yetki kaldırılınca anında geçerli: gate her istekte hesaplanır, cache yok (2.6.1/9).
- **T6 — `SingleDocumentIdsProvider` ("kim görebilir") aynı kuralı taşımalı** (2.6.1/7, 2.6.5/9). Tek belge için klasör sorusu "bu belgenin klasörüne/üstlerine hangi departmanlar yetkili?"dir → provider'a `folder_grantee_slugs: frozenset[str]` verilir (API katmanı `folder_repo.effective_grantee_slugs(document.folder_id)` ile hesaplar). İkinci motor yok.
- **T7 — Yazma tarafı:** `POST /api/documents/upload` `folder_id` alır. `write` = sahibi departman üyeliği **veya** en yakın tanımlı yetki `write`; `management`/`admin` her klasöre yazar (okuma tarafıyla simetrik, Aşama güvenlik yamasıyla aynı muafiyet). `department` **sunucuda** klasörün sahibinden türetilir (istemcinin gönderdiği `department` klasörle çelişirse 422). `folder_id` verilmezse: `department` verilmişse o departmanın **kök** klasörü atanır (eski istemciler, eval seed'i), ikisi de yoksa `folder_id = NULL` (bugünkü gibi; `employee`'ye görünmez, fail-safe). Metadata düzenleme (`PATCH /api/documents/{id}`) Phase 5.2'de `require_admin`; "değiştirme" yetkisinin düzenlemeyi de kapsaması (2.6.1/4) B-28 onay akışıyla birlikte ele alınır — bu fazda **değişmez** (SORU 3).
- **T8 — Denetim, ayrı tablo.** Yetki değişikliği `audit_log`'a yazılmaz (ADR-016 soru-cevap kaydı); `folder_grant_events(id, actor_user_id, folder_id, department_id, before, after, created_at)`; `GET /api/admin/folders/audit` oradan okur, `actor_name`/`folder_name`/`department_slug` join ile. Silinmeyen tablo (retention yok; hacim küçük).
- **T9 — Mevcut veri.** 70 belge + 4 workbook `department` slug'ıyla duruyor, `folder_id` yok. Migration her **üst** departman için bir kök klasör açar (ad = departman adı; `ik` dahil, boş) ve her belgeyi `department`'ının kök klasörüne taşır; `department IS NULL` belgeler `folder_id = NULL`. BACKEND_GAPS §2.6.4'ün demo ağacı (Hukuk → Proje Sözleşmeleri…, çapraz yetki örnekleri) **B-18'in işi**; bu fazda yalnızca kök klasörler + testlerde sentetik ağaç (SORU 1). `enerji_grubu` belgelerinin `subdepartment`'ı alt klasöre eşlenmez (B-18'e bırakılır).
- **T10 — Anayasa/§5.1 uyumu.** Tansu (01.10.2026): klasörleri müşteri admin'i tayin eder → Personel Yetkilendirmesi; departman CRUD sorusundan bağımsız (NOT §8.1 notu). Bu yüzden klasör uçları `require_admin` (müşterinin sistem yöneticisi), departman uçları yok.

---

## 2. Tasarım

### 2.1 Veri modeli (migration `0011_folders`)

- `folders(id uuid PK, name varchar(128), parent_id uuid NULL FK folders ON DELETE RESTRICT, owner_department_id uuid FK departments ON DELETE RESTRICT, created_at, updated_at)`; `UNIQUE(parent_id, name)` (kök düzeyinde `COALESCE(parent_id, '000…')` ile unique index); CHECK yok — "çocuk sahibi = üst sahibi" uygulamada (T3).
- `folder_grants(folder_id FK ON DELETE CASCADE, department_id FK ON DELETE CASCADE, access folder_access ENUM('read','write'), created_at; PK (folder_id, department_id))`.
- `folder_grant_events(id uuid PK, actor_user_id FK users SET NULL, folder_id FK folders ON DELETE SET NULL, folder_name varchar(128) (silinse de kalsın), department_id FK departments SET NULL, department_slug varchar(64), before folder_access_or_none, after folder_access_or_none, created_at)` — `before`/`after` `varchar(5)` (`none|read|write`).
- `documents.folder_id uuid NULL FK folders ON DELETE SET NULL` (+ index).
- **Veri adımı (korumalı, boş DB'de no-op):** her `parent_id IS NULL` departman için `folders(name = departments.name, owner = o departman)` kök (yoksa); `UPDATE documents SET folder_id = kök(department)` (`folder_id IS NULL AND department IS NOT NULL`). `downgrade`: sütun + tablolar gider (kökler dahil); belgeler `department` ile kalır, veri kaybı yok.
- Seed: `demo_folders_seed.py` — temiz kurulumda aynı kök klasörleri açar ("varsa dokunma"), `demo_documents_seed.py` belgeyi departmanının köküne koyar (migration yolu ile aynı sonuç; test C-02 deseni).

### 2.2 Yetki kuralı (`authorization.py`, `document_repo.py`)

- `DocumentIdsProvider.list_document_ids_for_folder_grants(*, department_slugs, confidentiality_levels) -> Iterable[UUID]`.
- `SqlDocumentIdsProvider`: `WITH RECURSIVE` — başlangıç: `folder_grants` satırları `department_id ∈ slugs`; genişleme: alt klasörler, **bir alt klasörde aynı departman için kendi tanımı varsa** o dal o tanımla devam eder (T4; görünürlük için read/write fark etmez → özetle "yetkili klasörlerin alt ağacı"); sonuç `documents.folder_id ∈ ağaç AND confidentiality ∈ levels`.
- `allowed_document_ids` `employee` dalı: `role_ids = departments(üyelik) ∪ folder_grants(üyelik departmanları)`; `scoped_ids & role_ids`. İki `FakeProvider` metodu da `test_authorization.py`'de taklit edilir.
- `SingleDocumentIdsProvider(document, folder_grantee_slugs=frozenset())`: yeni metot `department_slugs ∩ folder_grantee_slugs` boş değilse ve gizlilik uygunsa belge id'si. `/visibility` ucu `folder_repo.effective_grantee_slugs(document.folder_id)` ile doldurur.
- **Yazma yetkisi** `folder_repo.effective_access(folder, department_slugs) -> none|read|write|owner` (en yakın tanım; sahibi → `owner`); upload: `management/admin` ya da `owner`/`write` → izin, aksi 403 `FOLDER_WRITE_DENIED_MESSAGE`.

### 2.3 Uçlar

| Uç | Kim | Davranış |
|---|---|---|
| `GET /api/admin/folders` | admin | Tüm klasörler; her klasörde `grants` = **etkin** yetkiler (kendi tanımı `inherited:false`, üstten gelen `inherited:true`, sahibi listede yok), `document_count` = klasördeki (alt ağaç değil) belge sayısı |
| `POST /api/admin/folders` | admin | `{name, parent_id, owner_department_slug}`; `parent_id` varsa sahibi üstünkiyle aynı olmalı (422), bilinmeyen slug 404, aynı üstte aynı ad 409 |
| `PATCH /api/admin/folders/{id}` | admin | `{name?, parent_id?}` — ad değiştir/taşı; taşıma sahibi değiştiremez (422), kendi altına taşınamaz (422) **(SORU 2)** |
| `DELETE /api/admin/folders/{id}` | admin | Yalnızca boş (belge ve alt klasör yok) → 204; doluysa 409 **(SORU 2)** |
| `PUT /api/admin/folders/{id}/grants` | admin | `{grants:[{department_slug, access: none\|read\|write}]}` **bu klasördeki** tanımları topluca yazar: `none` → tanım silinir; sahibi departman gönderilirse 422; her fark `folder_grant_events`'e (before = eski **etkin** değer, after = yeni etkin değer) |
| `GET /api/admin/folders/audit?limit=` | admin | `folder_grant_events` yeniden eskiye, `limit` ≤ 500 |
| `GET /api/folders` | her kullanıcı | Kullanıcının görebildiği klasörler: sahibi olduğu departmanların klasörleri (`access: write`), yetki verilmiş klasörler ve alt ağaçları (`access` = etkin yetki); `management`/`admin` → hepsi `write`; `document_count` = **kullanıcının görebildiği** belge sayısı (allowed ∩ klasör) |
| `POST /api/documents/upload` | — | `folder_id` (opsiyonel form alanı) — T7 |
| `GET /api/documents`, `/{id}` | — | `folder_id` alanı (`DocumentListItem`) |
| `GET /api/documents/{id}/visibility` | admin | klasör yetkilerini yansıtır (T6) |

`GET /api/admin/access-matrix` **yazılmaz** (frontend matrisi `AdminFolder.grants`'tan kuruyor).

### 2.4 Dokunulmayanlar

ADR-004 imzası; `management`/`admin` kuralları; gizlilik düzeyleri; `documents.department` (klasörden türetilir ama sütun kalır — retrieval filtresi, eval, Aşama C düzeltmeleri ona bağlı); `PATCH /api/documents/{id}` yetkisi (admin, SORU 3); `audit_log`; AI-BalBal; company-ai `frontend/`; B-18 demo klasör ağacı.

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `alembic/versions/0011_folders.py` | §2.1 tablolar + `documents.folder_id` + kök klasör/backfill |
| `app/models/{folder,folder_grant,folder_grant_event}.py` (yeni), `models/document.py` (`folder_id`, `folder`), `models/__init__.py` | model |
| `app/repositories/folder_repo.py` (yeni): `create/get/list_all/update/delete`, `set_grants` (fark + event), `effective_access`, `effective_grantee_slugs`, `visible_folders_for(user, allowed_ids)`, `document_counts`; `document_repo.py` (`list_document_ids_for_folder_grants`, `root_folder_for(department)`) | repo |
| `app/services/authorization.py` (protokol metodu, `employee` birleşimi, `SingleDocumentIdsProvider` parametresi), `services/demo_folders_seed.py` (yeni), `demo_documents_seed.py` | servis |
| `app/schemas/folder.py` (yeni: `FolderGrantResponse`, `AdminFolderResponse`, `FolderCreateRequest`, `FolderUpdateRequest`, `FolderGrantsUpdateRequest`, `FolderAuditEntryResponse`, `UserFolderResponse`), `schemas/document.py` (`folder_id`) | şema |
| `app/api/folders.py` (yeni: `/api/admin/folders*`, `/api/folders`), `api/documents.py` (upload `folder_id`, visibility grantee'leri), `api/router.py`, `app/cli.py` (`seed-demo-folders`), `scripts/seed_demo.sh`, `Makefile` | API/CLI |
| `tests/test_folders.py` (yeni), `tests/{test_authorization,test_documents,test_document_repo,test_migrations,test_ask}.py` | §5 |
| `docs/ARCHITECTURE.md` (**ADR-023 — Folders and department access grants** + ADR-004 concretization), README ("Klasörler ve erişim yetkileri"), `docs/PHASES.md` notu, NOT (§2 B-26 UYGULANDI, §4.2 klasör satırları, §4.4 "folder_id yok sayılır" notu düzelir), `docs/reports/ASAMA_E_REPORT.md` | docs |

---

## 4. Uygulama sırası

1. Modeller + migration `0011` + `folder_repo` temel CRUD → `test_migrations` (köklerin açılması, belgelerin taşınması, downgrade).
2. Gate: protokol metodu + SQL (recursive CTE) + `employee` birleşimi + `SingleDocumentIdsProvider` → `test_authorization` (fake), `test_document_repo` (SQL: miras, alt klasörde farklı tanım, gizlilik).
3. `/api/admin/folders*` + `set_grants` + events + `/audit` → `test_folders.py`.
4. `GET /api/folders`, `DocumentListItem.folder_id`, upload `folder_id` (write kontrolü, department türetme, kök fallback) → `test_documents`, `test_folders`.
5. `/visibility` grantee'leri; `/api/ask` retrieval'da grant'li belgenin görünmesi → `test_ask`.
6. Seed (`demo_folders_seed`, belge → kök) + `make seed` yolu; `make test`, `make lint`, `--retrieval-only` 36/36.
7. Canlı: admin ile klasör oluştur, Proje Finans'a Hukuk klasöründe `read`, `finans` kullanıcısıyla liste/indirme/`/api/ask`; yetkiyi kaldır → kaybolur; `/visibility`; audit listesi.
8. ADR-023 + docs → rapor → düz commit + PHASES.md notu + push (SORU 5).

---

## 5. Kabul kriterleri ve kanıt (BACKEND_GAPS §2.6.5 ile eşlenmiş)

| # | Kriter (§2.6.5) | Test / komut |
|---|---|---|
| E-01 | (1) Proje Finans'a Hukuk klasörüne **görme** → `finans` çalışanı belgeyi **listede**, **aramada** (`/api/search`), **Balbal'da** (`/api/ask` retrieval, `retrieved_document_ids`) görür, **açar/indirir** (200); yükleme (`folder_id` o klasör) **403**, metadata düzenleme admin-only (zaten 403) | `test_folders.py::test_read_grant_makes_documents_visible_everywhere`, `test_ask.py` |
| E-02 | (2) **Değiştirme** → yükleme 201, belgenin `department` = klasör sahibi (`hukuk`), `folder_id` = klasör; `supersedes_document_id` ile yeni versiyon 201 | `test_folders.py` |
| E-03 | (3) Yetki kaldırılınca (`PUT` ile `none`) aynı kullanıcıya liste boş, indirme 403, `/api/ask` retrieval boş, `/api/search` boş — **aynı istek dizisinde, cache yok** | `test_folders.py::test_revoking_grant_hides_documents_immediately` |
| E-04 | (4) Miras: üst klasöre `read` → alt klasördeki belge görünür; alt klasörde `write` tanımı → yükleme alt klasöre 201, üst klasöre 403; `PUT` `none` ile alt tanım silinince üstün `read`'i geri gelir | `test_document_repo.py` (CTE) + `test_folders.py` |
| E-05 | (5) Klasör yetkisi gizliliği aşmaz: yetkili klasördeki `restricted` belge `employee`'ye görünmez, `management`'a görünür | `test_authorization.py` (fake), `test_folders.py` |
| E-06 | (6) Aynı yetki iki projenin belgesine aynı uygulanır: klasörde ANK_RES ve IZM_RES belgeleri, grant tek, ikisi de görünür | `test_folders.py` |
| E-07 | (7) Her `PUT` farkı `folder_grant_events`'e `before/after` (etkin değerler) + `actor_name`; değişmeyen satır olay üretmez; `GET /api/admin/folders/audit` yeniden eskiye | `test_folders.py` |
| E-08 | (8) Admin olmayan → `/api/admin/folders*` **403**; `GET /api/folders` her kullanıcıya 200 ve yalnızca görebildiği klasörler (`access` doğru, `document_count` görebildiği belge sayısı) | `test_folders.py` |
| E-09 | (9) `/visibility`: grant verilen departmanın `employee`'si listeye girer, kaldırılınca çıkar | `test_documents.py` |
| E-10 | Sözleşme birebir: `AdminFolder`/`UserFolder`/`FolderAuditEntry`/`FolderGrant` alan adları `proposed.ts` §10 ile aynı (snapshot assert); `DocumentListItem.folder_id` | `test_folders.py` |
| E-11 | Çocuk klasörün sahibi üstünden farklı → 422; aynı üstte aynı ad → 409; `DELETE` dolu → 409, boş → 204; kendi altına taşıma 422 | `test_folders.py` |
| E-12 | Migration `0011`: eski verili DB'de her üst departman için kök klasör, belgeler köke taşındı, `department IS NULL` belge `folder_id NULL`; boş DB'de no-op; downgrade | `test_migrations.py` |
| E-13 | `folder_id`'siz upload (eski istemci/eval seed): `department` verilmişse kök klasöre düşer; `department`+`folder_id` çelişirse 422 | `test_documents.py` |
| E-14 | `make test`, `make lint`, `--retrieval-only` 36/36 (seed belgeleri köklerde, retrieval değişmedi) | komutlar |
| E-15 | Canlı (`company-ai-dev`): §4/7 senaryosu curl ile; AI-BalBal tarayıcı: `AdminFoldersPage` ve `DocumentsTab` klasör görünümü **kendiliğinden** açılır (`useAdminFolders`/`useMyFolders` 200), `PendingNotice` kutuları kapanır — Naci elle | rapora |

---

## 6. SORU (Naci cevaplamalı)

1. **Demo klasör ağacı:** bu fazda yalnızca **kök klasörler** (departman başına bir) + testlerde sentetik ağaç (öneri; §2.6.4'ün Hukuk/Proje Finans/Enerji alt klasörleri ve çapraz yetki örnekleri B-18'e kalır) — mı, yoksa §2.6.4 örnek ağacı ve iki çapraz yetki şimdi seed'e girsin mi? İkincisi belge→klasör eşlemesi için ledger'a `folder` alanı ister (ledger `folder:` alanı zaten var: `corporate` gibi — kullanılabilir).
2. **`PATCH`/`DELETE /api/admin/folders/{id}`:** frontend çağırmıyor; BACKEND_GAPS listeliyor. Öneri: ikisini de yaz (küçük; ad değiştirme/boş klasör silme olmadan admin ekranı eksik kalır).
3. **"Değiştirme" yetkisi metadata düzenlemeyi kapsasın mı?** `PATCH /api/documents/{id}` Phase 5.2'de admin-only. Öneri: **bu fazda değil** — B-28 onay akışı (B-08 sonrası) düzenleme yetkisini yeniden tanımlayacak; şimdi açmak iki kez değiştirmek olur.
4. **`GET /api/folders` `document_count`:** kullanıcının görebildiği belge sayısı (öneri) mi, klasördeki toplam mı?
5. **Faz birimi:** etiketsiz düz commit + PHASES.md notu + **yeni ADR-023** (veri modeli + kural; BACKEND_GAPS §2.6.3 "kısa bir ADR" istiyor) — uygun mu?

---

## 7. Kendi aldığım küçük kararlar

- Çocuk klasörün sahibi = üstün sahibi (T3); `owner_department` yalnızca kökte seçilir.
- Miras: en yakın tanım geçerli; `PUT`'ta `none` = tanımı sil (frontend sözleşmesi); açık "none override" yok.
- `before`/`after` etkin değerler (miras dahil) — denetim okuyan kişi gerçek erişim değişikliğini görür.
- `management`/`admin` her klasöre yazar (okuma tarafıyla simetrik); `employee` için sahibi üyeliği = `write`.
- `GET /api/admin/folders` `document_count` = klasörün kendi belgeleri (alt ağaç değil); `GET /api/folders` kullanıcıya göre.
- `folder_grant_events` için retention yok.
- `GET /api/admin/access-matrix` yazılmaz.
- `documents.department` korunur ve klasör sahibinden türetilir; çelişki 422.
