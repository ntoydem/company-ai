# Aşama E Raporu — Klasörler ve departman erişim yetkileri (B-26, ADR-023)

**Tarih:** 01.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu + ADR-023)  **Commit:** `<commit>`
**Plan:** `docs/plans/ASAMA_E_PLAN.md` · **ADR:** ADR-023 (yeni), ADR-004 concretization · **Migration:** `0011`

Naci'nin SORU cevapları (hepsi planın önerisi yönünde): (1) yalnızca kök klasörler, zengin demo ağacı B-18'e; (2) `PATCH`/`DELETE /api/admin/folders/{id}` yazıldı; (3) `write` yetkisi metadata düzenlemeyi kapsamıyor (B-28); (4) `GET /api/folders` `document_count` = kullanıcının görebildiği sayı; (5) etiketsiz düz commit + ADR-023. Naci'nin özel vurgusu: **E-03 (anında kaybolma) ve E-05 (gizlilik aşılmıyor)** — ikisi de hem testle hem canlı doğrulandı (§1, §4).

## 1. Kabul kriterleri (plan §5, BACKEND_GAPS §2.6.5)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| E-01 | Proje Finans'a Hukuk klasöründe **görme** → `finans` çalışanı belgeyi **listede**, **aramada** (`/api/search`), **Balbal retrieval'ında** (`retrieved_document_ids`, prompt'ta başlık) görür ve **indirir** (200); o klasöre yükleme 403 | ✅ | `test_folders.py::test_read_grant_shows_documents_everywhere_and_revocation_hides_them_at_once`; canlı: liste ✓, indirme 200, arama ✓, `/api/folders` `('Proje Sözleşmeleri (test)', 'read', 1)`, yükleme 403 |
| E-02 | **Değiştirme** → yükleme 201, `department` = klasör sahibi (`hukuk`), `folder_id` = klasör; `supersedes_document_id` ile yeni versiyon 201 | ✅ | `test_write_grant_allows_upload_and_new_version_with_department_derived_from_folder`; canlı: admin `folder_id` ile yükleme → `department: hukuk`, `folder_id` eşit |
| **E-03** | **Yetki kaldırılınca anında kaybolma:** `PUT` `none` sonrası **aynı istek dizisinde** liste boş, indirme 403, arama boş, `/api/ask` retrieval boş ve LLM **çağrılmıyor** (sıfır chunk), `/visibility`'den düşüyor | ✅ | aynı test (`len(fake_llm.requests)` değişmedi, `retrieved_document_ids == []`); canlı: revoke sonrası liste ✗, indirme 403, arama ✗, visibility'de `finans` yok — cache yok, gate her istekte hesaplanıyor |
| E-04 | Miras: üst `read` → alt klasör belgesi görünür (`inherited: true`); alt `write` → alta yükleme 201, üste 403; alt tanım `none` → üstün `read`'i geri gelir | ✅ | `test_inheritance_and_child_override`; `test_folder_access.py` (saf kural: en yakın tanım, 3 seviye miras, kardeş dal etkilenmez) |
| **E-05** | **Gizlilik aşılmaz:** yetkili klasördeki `restricted` belge `employee`'ye **`write` yetkisiyle bile** görünmez (liste ✗, indirme 403, `/visibility`'de yok), `management` görür; `document_count` 3 değil 2 | ✅ | `test_folder_grant_never_exceeds_confidentiality_and_applies_to_every_project`; `test_authorization.py` `FakeProvider` seviye kontrolü (`_EMPLOYEE_CONFIDENTIALITY_LEVELS` grant dalına da uygulanıyor) |
| E-06 | Aynı yetki iki projenin belgesine aynı uygulanır (ANK_RES + IZM_RES tek grant'le görünür) | ✅ | aynı test |
| E-07 | Her **etkin** değişiklik bir `folder_grant_events` satırı (`before/after` etkin değer, `actor_name`); değişmeyen `PUT` olay üretmez; sahibine yetki 422; audit yeniden eskiye | ✅ | `test_every_effective_change_is_one_audit_event` (4 olay: none→read, read→write, write→read, read→none); canlı: `Yönetici … finans none -> read`, `read -> none` |
| E-08 | Admin olmayan → `/api/admin/folders*` 403; `GET /api/folders` kullanıcıya göre (sahip `write`, grant etkin seviye) | ✅ | `test_admin_endpoints_require_admin_and_user_view_is_scoped` |
| E-09 | `/visibility` klasör yetkisiyle tutarlı (grant → listede, revoke → değil) | ✅ | E-01 testi + canlı |
| E-10 | Sözleşme `proposed.ts` §10 ile birebir (`AdminFolder`, `FolderGrant`, `UserFolder`, `FolderAuditEntry` anahtar kümeleri) | ✅ | anahtar-küme assert'leri (E-07/E-08 testleri) |
| E-11 | Çocuk sahibi ≠ üst → 422; aynı üstte aynı ad → 409; bilinmeyen departman 404; kendi altına taşıma 422; dolu klasör silme 409 (alt klasör **veya** belge), boş → 204, bilinmeyen 404 | ✅ | `test_tree_rules_owner_match_duplicate_name_move_and_delete`; canlı: belgeli klasör silme 409, boşaltılınca 204 |
| E-12 | Migration `0011`: eski verili DB'de üst departman başına kök (alt departmana yok), belgeler köke, departmansız belge `NULL`; boş DB no-op; downgrade | ✅ | `test_migrations.py::test_0011_creates_root_folders_and_moves_existing_documents`, `test_downgrade_to_empty_then_upgrade_head` (`0011`); canlı dev DB: 6 kök (Enerji 36, Proje Finans 16, Hukuk 7, İdari İşler 12, İK 0, Mali İşler 3), **74/74 belge klasörde** |
| E-13 | `folder_id`'siz upload → departmanın kökü; `department` + `folder_id` çelişkisi 422; ikisi de yoksa `folder_id NULL` | ✅ | E-02 testi |
| E-14 | `make test`, `make lint`, `--retrieval-only` 36/36 | ✅ | **449 geçti** (438 + 11 yeni), 15 deselected; lint çıkış 0; recall@80 **36/36** |
| E-15 | Canlı backend senaryosu | ✅ (backend) | §4; tarayıcı (AdminFoldersPage/DocumentsTab/UploadTab'ın kendiliğinden açılması) **Naci elle** |

## 2. Yapılanlar

- **Model/migration `0011`:** `folders` (üst RESTRICT, sahibi RESTRICT, seviye başına benzersiz ad — kök için sentinel COALESCE index), `folder_grants` (PK `(folder_id, department_id)`, `folder_access` enum), `folder_grant_events` (aktör/klasör/departman adları kopyalı, `before/after` etkin değer), `documents.folder_id` (SET NULL). Veri adımı korumalı: üst departman başına kök, belgeler köke.
- **Saf kural (`services/folder_access.py::FolderAccessMap`):** en yakın tanım, sahibi grant değil, `write ⊇ read`, alt ağaç/okunabilir küme/grantee kümesi — tüm ağaç bellekte (düzinelerce satır), SQL'siz, birim testli; gate provider'ı, admin API, kullanıcı görünümü ve upload kontrolü aynı sınıfı kullanır.
- **Tek kapı:** `DocumentIdsProvider.list_document_ids_for_folder_grants`; `allowed_document_ids` `employee` dalı `üyelik ∪ grant` (aynı `normal` seviyesi, aynı `scoped_ids` kesişimi); `management`/`admin` değişmedi; `SingleDocumentIdsProvider(document, folder_grantee_slugs)`. `FakeProvider` (testler) aynı metodu aldı.
- **API (`api/folders.py`):** `GET/POST/PATCH/DELETE /api/admin/folders[/{id}]`, `PUT …/{id}/grants`, `GET …/audit?limit=`, `GET /api/folders`. `api/documents.py`: upload `folder_id` (sahibi/`write`/management-admin; `department` sunucuda türetilir, çelişki 422; `folder_id` yoksa departman kökü), `DocumentListItem.folder_id`, `/visibility` grantee'leri.
- **Seed/CLI:** `demo_folders_seed.ensure_demo_root_folders`, `seed-demo-folders` (entrypoint, `seed_demo.sh`, `make seed-demo-folders`), demo belgeler departmanının köküne.
- **Docs:** ADR-023 + ADR-004 satırı, README "Klasörler ve departman erişim yetkileri", PHASES.md notu, NOT (§2 B-26 UYGULANDI, §4.2 yükleme satırı, §4.4 `folder_id` notu; §8.1 Tansu'nun klasör cevabı önceki commit'te).
- **Dokunulmayanlar:** ADR-004 imzası, `management`/`admin` kuralları, gizlilik düzeyleri, `documents.department` sütunu, `PATCH /api/documents/{id}` yetkisi (admin, B-28), `audit_log`, AI-BalBal, company-ai `frontend/`, B-18 demo ağacı, `GET /api/admin/access-matrix` (yazılmadı, UI türetiyor).

## 3. Değişen dosyalar

Uygulama commit'i: 27 dosya (+~1.650 / −10 satır). Yeni: `alembic/versions/0011_folders.py`, `app/models/folder.py`, `app/services/folder_access.py`, `app/repositories/folder_repo.py`, `app/schemas/folder.py`, `app/api/folders.py`, `app/services/demo_folders_seed.py`, `tests/test_folder_access.py`, `tests/test_folders.py`, bu rapor. Değişen: `app/models/{document,__init__}.py`, `app/services/{authorization,demo_documents_seed}.py`, `app/repositories/document_repo.py`, `app/schemas/document.py`, `app/api/{documents,router}.py`, `app/cli.py`, `entrypoint.sh`, `scripts/seed_demo.sh`, `Makefile`, `tests/{test_authorization,test_migrations}.py`, `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`.

## 4. Testler ve canlı doğrulama

- Backend: **449 geçti** (11 yeni: 3 saf kural, 7 uçtan uca senaryo, 1 migration yolu), 15 deselected (`live`), 7 dk 05 sn. `make lint` yeşil (ruff/format/mypy 102 dosya). `--retrieval-only` 36/36 (seed belgeleri köklerde; retrieval değişmedi).
- Geçici kırmızı: E-05 testi `management_user` fixture'ını kullanıyordu — fixture `get_current_user`'ı management'a çevirdiği için admin uçları 403 dönüyordu; yönetim kullanıcısı testin içinde elle oluşturuldu. Kod değişikliği yok.
- **Canlı (`company-ai-dev`, LLM'siz):** `alembic_version 0011`; 6 kök klasör, 74/74 belge klasörde. Admin: Hukuk kökü altına "Proje Sözleşmeleri (test)" → 201; `folder_id` ile belge yükleme → `department: hukuk` türetildi. `finans`: grant öncesi liste ✗ / indirme 403 / arama ✗ / `/api/folders` yalnızca kendi kökü; `read` grant → liste ✓, indirme 200, arama ✓, `/api/folders` `('Proje Sözleşmeleri (test)', 'read', 1)`, yükleme 403, `/visibility`'de ✓; **revoke → bir sonraki istekte** liste ✗, indirme 403, arama ✗, `/visibility` ✗ (E-03). Audit: iki olay (`none -> read`, `read -> none`, aktör "Yönetici"). Belgeli klasör silme 409; test belgesi/klasörü temizlendi (6 kök kaldı). Balbal retrieval canlıda denenmedi — test belgesi metinsiz sahte PDF (chunk yok); E-01 testi fake LLM ile retrieval'ı kanıtlıyor.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| Miras çözümü Python'da (`FolderAccessMap`), recursive CTE yok | Ağaç düzinelerce satır; kural tek yerde, saf, birim testli; SQL'e yalnızca klasör id listesi gider | Her istekte iki küçük SELECT (`folders`, `folder_grants`) |
| `before/after` **etkin** değerler | Denetim okuyan kişi gerçek erişim değişimini görür (miras dahil) | Değişmeyen `PUT` olay üretmez |
| Kök için benzersizlik `COALESCE(parent_id, sentinel)` index'i | Postgres'te `NULL`'lar benzersizlikte eşleşmez | Aynı adda iki kök yok |
| Sahibi departmana grant 422 | Sahibi zaten `write`; çift kaynak olmasın | Frontend zaten sahibini listede göstermiyor |
| `management`/`admin` her klasöre yazar | Okuma tarafıyla simetrik (güvenlik yaması muafiyeti) | — |
| `GET /api/admin/folders` `document_count` = klasörün kendisi; `GET /api/folders` = kullanıcının gördüğü | Plan SORU 4 | — |
| Canlı Balbal retrieval denenmedi | Test belgesi metinsiz; gerçek LLM harcaması gereksiz, test kanıtı var | — |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. Tansu tarafı: `AdminFoldersPage`/`DocumentsTab`/`UploadTab` dondurulmuş sürümde kendiliğinden açılmalı (alan adları birebir); tarayıcı teyidi E-15.

## 7. Riskler / sonraki adım için notlar

- Zengin demo ağacı ve çapraz yetki örnekleri (BACKEND_GAPS §2.6.4) **B-18'de**; bugün her kök tek klasör, `İK` boş.
- `write` yetkisi metadata düzenlemeyi kapsamıyor (admin-only); B-28 (B-08 sonrası) düzenleme/onay yetkisini yeniden tanımlayacak.
- `documents.department` ile `folder.owner` çift kaynak: upload sunucuda türetiyor; `PATCH /api/documents/{id}` `department` değiştirirse klasörle çelişebilir — admin-only ve nadir; B-28'de "departman = klasörden" kuralı PATCH'e de uygulanmalı (not).
- `folder_grant_events` retention yok (hacim küçük).

## 8. Doğruladığım üçüncü taraf davranışları

- Postgres 16: `CREATE UNIQUE INDEX … (COALESCE(parent_id, '…'::uuid), name)` ifade index'i kök adlarını benzersiz kılıyor; `ON DELETE RESTRICT` üst/sahibi silmeyi engelliyor (API zaten 409 veriyor).
- SQLAlchemy 2.x: `relationship("FolderGrant", cascade="all, delete-orphan", passive_deletes=True)` + `session.expire(folder, ["grants"])` ile `PUT` sonrası etkin harita doğru; Pydantic `model_fields_set` ile `PATCH`'te `parent_id: null` ("köke taşı") ile "gönderilmedi" ayrıldı.
- FastAPI dependency sırası: `require_admin` → 403 before body validation yok; test E-08'de 403 beklendiği gibi.

## 9. Kaynak kullanımı

- Migration milisaniyeler; her yetkili istekte iki küçük ek SELECT; LLM çağrısı yok (canlı doğrulama LLM'siz, eval retrieval-only).
