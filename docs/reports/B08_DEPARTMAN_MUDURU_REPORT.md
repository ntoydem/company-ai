# B-08 Raporu — Departman yöneticisi rolü (`department_manager`)

**Tarih:** 02.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `<commit>`
**Plan:** `docs/plans/B08_DEPARTMAN_MUDURU_PLAN.md` · **ADR:** ADR-004 concretization (yeni ADR yok) · **Migration:** `0012_user_role_department_manager`

Naci'nin SORU cevapları (02.10.2026): (1) **(a)** tek demo müdür `finans_mudur` (`department_manager`, üyelik `finans`); (2) rol/üyelik değişikliği kayıt defteri bu fazda **yok**, ayrı küçük iş; (3) müdür `board` **görmez**, kural **sabit** (tablo değil) → NOT §7.2 #1 KAPANDI; (4) etiketsiz düz commit + PHASES.md notu. **LLM çağrısı: 0.**

## 1. Kabul kriterleri (plan §4)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| M-01 | Müdür kendi departmanının `normal` + `restricted` belgelerini görür, `board` görmez | ✅ | `test_authorization::test_department_manager_sees_own_department_normal_and_restricted_but_not_board` — provider çağrısı `(("finans",), (normal, restricted))` |
| M-02 | Başka departmanın hiçbir belgesi (restricted dahil) görünmez | ✅ | aynı test (yalnızca üyelik slug'ları iletilir) + `test_documents::test_department_manager_lists_restricted_but_not_board_in_own_department` (hukuk restricted listede yok) |
| M-03 | Klasör grant'i: grant'li klasörde `normal + restricted`, `board` yok | ✅ | `test_authorization::test_department_manager_folder_grants_use_the_same_two_levels`; `test_folders::test_department_manager_sees_restricted_in_granted_folder_and_own_root_is_write` (SQL yolu: grant'li klasördeki restricted görünür, aynı klasördeki board ve grant'siz kökteki restricted görünmez) |
| M-04 | Üyeliksiz / pasif müdür → ∅; `employee`/`management` değişmedi | ✅ | `test_department_manager_without_membership_or_inactive_sees_nothing`, `test_employee_levels_are_unchanged_by_the_manager_rule`; mevcut 1.2/E testleri yeşil |
| M-05 | SQL yolu: `GET /api/documents` müdüre restricted'ı listeler, aynı departmandaki `employee`'ye listelemez, `board` ikisine de görünmez | ✅ | `test_department_manager_lists_restricted_but_not_board_in_own_department`, `test_employee_in_the_same_department_still_does_not_see_restricted` |
| M-06 | `/visibility` restricted belge için müdürü içerir, employee'yi ve başka departmanın müdürünü içermez; `board` için müdürü içermez | ✅ | `test_visibility_includes_department_manager_for_restricted_document` — `SingleDocumentIdsProvider` **değişmeden** |
| M-07 | Yazma: başka departmana upload 403, kendi departmanına 201; `/api/folders` kendi kökü `write`, grant'li klasör `read`, grant'siz kök listelenmez | ✅ | `test_department_manager_upload_is_bound_to_own_department_like_an_employee`; `test_folders` testi — `documents.py`/`folders.py`'ye **dokunulmadı** |
| M-08 | Canlı (LLM'siz): `finans_mudur` `DOC-ANK-FIN-008`'i listeler/arar, `finans` listelemez/aramaz | ✅ | §4 |
| M-09 | Admin `PATCH /api/users/{id}` ile rolü verir; `primary_department` kuralı korunur | ✅ | `test_users::test_admin_can_assign_department_manager_and_me_reflects_it` |
| M-10 | Migration `0012` boş DB'den head'e ve geri; downgrade müdürleri `employee`'ye düşürür, enum eski üç değere döner | ✅ | `test_migrations::test_0012_adds_department_manager_and_downgrade_demotes_to_employee`; `test_downgrade_to_empty_then_upgrade_head` (head `0012`) |
| M-11 | Regresyon: `make test` yeşil, `make lint` yeşil, `--retrieval-only` 39/39, `validate-ledger` 0 hata | ✅ | §4 |
| Seed | `finans_mudur` oluşturulur, `finans` üyesi, ana departman `finans`, unvan "Proje Finans Müdürü"; restricted görür, board ve Mali İşler görmez | ✅ | `test_department_structure::test_finans_mudur_demo_user_is_a_finans_member_and_sees_restricted`, `test_demo_users_seed` (5 kullanıcı) |

## 2. Yapılanlar

- **`models/user.py`:** `UserRole.department_manager`. **Migration `0012`:** `ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'department_manager'` (veri adımı yok — kimse otomatik müdür olmaz, kişiyi müşteri admin'i seçer, NOT §8.1); downgrade: müdürler `employee`, tip yeniden yaratılır (`RENAME` → `CREATE` → `ALTER COLUMN … USING role::text::user_role` → `DROP`).
- **`services/authorization.py`:** `_MANAGER_CONFIDENTIALITY_LEVELS = (normal, restricted)` + `_membership_confidentiality_levels(role)`; `employee`/`department_manager` **tek dalda** — üyelik ve klasör grant'i çağrıları role göre seviye kümesi alır. `admin`/`management` dalları, imza, `DocumentIdsProvider`, `SqlDocumentIdsProvider`, `SingleDocumentIdsProvider`, `FakeProvider` **değişmedi**.
- **Seed:** `demo_users_seed.py` `finans_mudur` ("Proje Finans Müdürü", ortak `DEMO_USER_PASSWORD`), `demo_departments_seed.py` üyelik `("finans",)`. Entrypoint sırası değişmedi.
- **Testler:** `conftest.department_manager_user` fixture; 4 birim (`test_authorization`), 4 API (`test_documents`), 1 klasör (`test_folders`), 1 kullanıcı (`test_users`), 1 migration veri testi + head `0011→0012` (`test_migrations`), 1 seed/yapı (`test_department_structure`, `_document` helper'ına `confidentiality` parametresi), `test_demo_users_seed` beklenen roller.
- **Docs:** ADR-004 B-08 satırı; DOMAIN_MODEL §4 enum + §5 kural; SPEC_02 §5 rol + demo hesap; README demo tablosu + yetki paragrafı; NOT (§2 B-08 UYGULANDI + Tansu'ya 3 kalemlik to-do, §5.1 satırı, §7.2 #1 KAPANDI, giriş notu); PHASES.md notu.
- **Dokunulmayanlar:** `api/documents.py`, `api/folders.py`, `api/users.py`, `api/deps.py` (`require_admin` kapsamı aynı — müdür yönetim ucu kullanmaz), `repositories/*`, `schemas/*`, retrieval, prompt, eval seti, AI-BalBal.

## 3. Değişen dosyalar

`backend/app/models/user.py`, `backend/alembic/versions/0012_user_role_department_manager.py` (yeni), `backend/app/services/{authorization,demo_users_seed,demo_departments_seed}.py`, `backend/tests/{conftest,test_authorization,test_documents,test_folders,test_users,test_migrations,test_demo_users_seed,test_department_structure}.py`, `README.md`, `docs/{ARCHITECTURE,DOMAIN_MODEL,PHASES}.md`, `docs/SPEC_02_dokuman_metadata_yetki_ux.md`, `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`, bu rapor.

## 4. Testler ve canlı doğrulama

- Hedefli ilk tur: 24 test geçti; tek kırmızı test tarafındaydı (`test_folders` `tests.test_ask._document`'ı kullanıyor, `confidentiality` parametresi yok → belgeye sonradan atandı). Lint: 4 × E501 + 1 format farkı, test dosyalarında, düzeltildi.
- `make test`: **468 geçti (456 + 12 yeni), 15 deselected, 7 dk 24 sn; ocr-worker 9 geçti**. `make lint`: **0 error(s)**. `make validate-ledger`: 0 error(s), 0 warning(s). `--retrieval-only` eval: **recall@80 39/39 (%100), `EVAL_EXIT=0` (`seed_data/evaluation/results/retrieval-only_2026-10-02/recall_083844.md`, git dışı)**.
- **Canlı M-08** (`make up` → migration `0012` + seed; curl, LLM yok):

```text
backend logs: Running upgrade 0011 -> 0012 … demo user created username=finans_mudur … membership created finans_mudur:finans
alembic_version = 0012; users: finans=employee[finans], finans_mudur=department_manager[finans]
DOC-ANK-FIN-008 = "Financial Model 2026" (finans, restricted), id 99509546-…

finans_mudur login: role=department_manager department_slugs=['finans'] title="Proje Finans Müdürü"
finans_mudur: GET /api/documents → 16 belge, DOC-ANK-FIN-008 listede: True; download → 200; /api/search?q=Financial Model 2026 bulur: True
finans       login: role=employee department_slugs=['finans'] title="Proje Finans Uzmanı"
finans:       GET /api/documents → 15 belge, DOC-ANK-FIN-008 listede: False; download → 403; /api/search bulur: False
```

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| Seviye kümesi role göre tuple, `employee` ve müdür tek dal | kopya kod yok; B-26 grant çağrısı da otomatik aynı seviyeleri alır | — |
| Müdürün departmanı = üyelikleri; ayrı "yöneticisi olduğu departman" alanı yok | NOT §5.1 (kuralı değil kişiyi değiştir), `employee` ile simetri; `documents.department` yalnızca üst departman slug'ı (canlı DB'de doğrulandı) | Alt birime üye müdür üst departmanı görmez (employee ile aynı) |
| Enum değeri `department_manager` | BACKEND_GAPS §2.4, NOT ve Tansu'nun `types.ts` birliği için aynı string | — |
| Downgrade tipi yeniden yaratır | PG enum değeri silinemez | `test_migrations` kanıtlıyor |
| `require_admin` değişmedi | müdür yönetim işlemi yapmaz (klasör/grant/kullanıcı admin'de) | — |
| Demo müdür unvanı "Proje Finans Müdürü" (display_name aynı) | P-9 jenerik/kurgusal | — |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. **Tansu'ya (NOT §2 B-08):** `types.ts` birliği, `ROLE_LABELS`/`ROLE_VALUES`, `visibility.ts`/`Home`/`BalbalChat` müdürü üyelik bazlı ele alsın. Dondurulmuş `b219600` kırılmaz: etiket boş görünür, admin formu rolü atayamaz (API ile atanır), kart gizleme müdür için yapılmaz (yetki sunucuda).

## 7. Riskler / sonraki adım için notlar

- B-08 artık §5.2 iki aşamalı onayın (B-28), B-02 "departmana yüklendi" alıcısının ve B-23/2'nin ön koşulunu sağlıyor; sırada NOT §7.2 #7 (§5.2 açık nokta 2–3) + B-28.
- Rol/üyelik değişikliği olay kaydı (`folder_grant_events` deseni) ayrı küçük iş — B-28'den önce.
- Upload'da `confidentiality` alanı için yükleyen rolüne göre sınır yok (bir `employee` `board` seçebilir → kendisine görünmez, fail-safe). Bu B-08 öncesi de böyleydi; B-28 onay akışında ele alınmalı, not düşüldü.

## 8. Doğruladığım üçüncü taraf davranışları

- PostgreSQL 16: `ALTER TYPE … ADD VALUE IF NOT EXISTS` Alembic'in tek transaction'ı içinde çalıştı (değer aynı transaction'da kullanılmadığı için); enum değeri silinemediği için downgrade'de tip yeniden kuruldu, `role::text::user_role` dönüşümü sorunsuz (`test_migrations`).
- SQLAlchemy `Enum(..., values_callable=...)` yeni Python üyesini ek ayar gerektirmeden eşledi; Pydantic v2 `UserRole` şemaları (`UserCreateRequest`, `UserUpdateRequest`, `UserResponse`, `/me`) yeni değeri otomatik kabul etti/döndürdü.

## 9. Kaynak kullanımı

- LLM: 0 çağrı. Test süresi: 7 dk 24 sn (backend) + 5,6 sn (ocr-worker). RAM değişmedi.
