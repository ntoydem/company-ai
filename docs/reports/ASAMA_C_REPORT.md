# Aşama C Raporu — departman ağacı (B-20/1–5), ana departman (B-09), unvan + rehber (B-05)

**Tarih:** 01.10.2026  **Model:** Claude Fable 5.1  **Tag:** yok (Naci kararı: düz commit + `docs/PHASES.md` notu)  **Commit:** `<commit>`
**Plan:** `docs/plans/ASAMA_C_PLAN.md` · **ADR:** ADR-003 ve ADR-004 concretization; yeni ADR yok · **Migration:** `0010`

Naci'nin SORU cevapları (hepsi planın önerisi yönünde): (1) `manager_id` yok, B-22'de; (2) demo unvanları; (3) rehberde `management`/`admin` listelenir (`department_slug: null`); (4) `finans` kullanıcısının `display_name`'i "Proje Finans"; (5) ana departman backfill = en eski üyelik, eşitlikte slug; (6) etiketsiz düz commit. C-09 tarayıcı kontrolü Naci elle.

## 1. Kabul kriterleri (plan §6)

| # | Kriter | Durum | Kanıt |
|---|---|---|---|
| C-01 | Snapshot (temiz kurulum): seed → 12 satır, zihin haritasıyla birebir (ad, slug, üst); idempotent | ✅ | `test_department_structure.py::test_seed_tree_matches_mind_map`, `test_departments_endpoint_serves_the_new_names` |
| C-02 | Snapshot (migration yolu): `downgrade 0009` → eski ağaç + `finans`'a iki üyelik → `upgrade head` → aynı 12 satır; `finans` yalnızca `finans`, ana departman `finans`, `display_name` "Proje Finans", unvanlar dolu, `yonetim` ana departmanı `NULL`; boş DB'de `upgrade` sorunsuz (`0010`) | ✅ | `test_migrations.py::test_0010_corrects_an_existing_phase_1_2_tree_and_backfills_users`, `test_downgrade_to_empty_then_upgrade_head` |
| C-03 | `finans` `mali_isler` belgesini göremez (liste yok, indirme 403); yalnızca `finans` üyesi | ✅ | `test_finans_demo_user_is_proje_finans_only_and_cannot_see_mali_isler`; canlı: görünen belge 18 → **15** (14 PDF + 1 workbook; 3 `mali_isler` belgesi düştü) |
| C-04 | `enerji` dört alt birimin (`enerji_uretim_piyasa` dahil) belgelerini görür, `ik` belgesini görmez | ✅ | `test_enerji_sees_all_four_sub_units_including_uretim_piyasa` |
| C-05 | `/login` + `/me`: `primary_department_slug` üyeliklerden biri, `department_slugs[0]` ile aynı; `management` → `null`; `title` döner | ✅ | `test_auth.py::test_me_puts_the_primary_department_first_and_returns_title`, `test_me_management_has_no_primary_department`; canlı `finans` `/me`: `department_slugs ["finans"]`, `primary_department_slug "finans"`, `title "Proje Finans Uzmanı"` |
| C-06 | Admin API: `primary_department_id` üyelikte değil → 422; verilmezse ilk üyelik (slug sırası); üyelik düşerse yeni ilk üyelik; açıkça üye-olmayan → 422; üyelik yoksa `null`; `title` yazılır/okunur | ✅ | `test_users.py::test_create_user_defaults_primary_to_first_membership_and_stores_title`, `test_primary_department_must_be_a_membership`, `test_update_keeps_primary_while_member_and_moves_it_when_dropped` |
| C-07 | `GET /api/directory`: kimliksiz 401; **yalnızca 5 alan** (`extra="forbid"`); `q` ad **veya** unvan (`müş` → Hukuk Müşaviri); `department=` üyeliğe göre; bilinmeyen slug → `[]`; pasif listelenmez; `management` `department_slug: null` ile listelenir | ✅ | `test_directory.py` (4 test); canlı: `?q=hukuk` → 1 kişi, `?department=enerji_grubu` → `enerji`, tüm liste 5 kişi / 5 alan |
| C-08 | `make test`, `make lint`, `--retrieval-only` 36/36 | ✅ | **432 geçti** (418 + 14 yeni), 15 deselected; lint yeşil (ruff/format/mypy 94 dosya); recall@80 **36/36** |
| C-09 | Canlı (`company-ai-dev`) | ✅ backend kısmı | `alembic_version = 0010`; `departments` 12 satır (`finans`="Proje Finans", `enerji_grubu`="Enerji", `enerji_uretim_piyasa`="Üretim/Piyasa" (üst `enerji_grubu`), `ik`="İK", `mali_isler_muhasebe`/`mali_isler_finansal_muhasebe` (üst `mali_isler`) …); `user_departments`: `finans→finans`, `hukuk→hukuk`, `enerji→enerji_grubu` (**`finans→mali_isler` yok**); `users`: 5 hesabın unvanı dolu, `admin`/`yonetim` ana departmanı `NULL`. **Tarayıcı (kart adları, rehber kutusunun kapanması): Naci elle** |

## 2. Yapılanlar

- **Migration `0010_department_structure_and_user_fields`:** 5 ad `UPDATE` (slug'a göre, `EXISTS`-korumalı), 4 `INSERT … WHERE NOT EXISTS` (çocuklar yalnızca üst varsa), `finans→mali_isler` üyelik `DELETE`, `finans` `display_name` düzeltmesi; `users.title`, `users.primary_department_id` (FK, `SET NULL`), backfill (en eski üyelik, eşitlikte slug), demo unvanları (`title IS NULL` iken). Boş DB'de tüm veri adımları no-op. `downgrade` adları/satırları geri alır, silinen üyeliği **geri eklemez**.
- **Seed:** `demo_departments_seed.py` 12 satırlık yeni ağaç, `finans` tek üyelik, temiz kurulumda ana departmanı da atar; `demo_users_seed.py` unvanlar + "Proje Finans"; `admin_seed.py` "Sistem Yöneticisi". "Varsa dokunma" korunur.
- **Model/şema:** `User.title`, `primary_department_id`/`primary_department`, `primary_department_slug`; `department_slugs`/`department_ids` **ana departman başta**; `CurrentUserResponse.{primary_department_slug,title}`; `UserCreate/UpdateRequest.{title,primary_department_id}`, `UserResponse.{title,primary_department_id}`; `schemas/directory.py::DirectoryPerson` (`extra="forbid"`).
- **Repo/API:** `user_repo._resolve_primary` (B-09 kuralı tek yerde), `create/update` yeni alanlar, `search_directory`; `api/users.py` 422 `PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE` (`model_fields_set` ile "verilmedi" ↔ "null verildi" ayrımı); yeni `api/directory.py` (`get_current_user`, `limit` 200).
- **Docs:** README (demo tablosu + unvan, departman ağacı, B-09/B-05, rehber curl), ADR-003/ADR-004 satırları, PHASES.md notu, NOT §1 B-09/B-05 + §2 B-20 UYGULANDI, §4.2 Tansu-tarafı bilgi notları (rehber kutusu, `title`, `UserForm` alanları) ve **B-08 bağımlılık notu** (`ROLE_LABELS`/`ROLE_VALUES`/`UserRole`/`UserForm` eşzamanlı güncellenmeden backend enum'u genişletmez).
- **Dokunulmayanlar:** `allowed_document_ids`/ADR-004 kuralı (yetki birimi üst departman), `documents.department`/`subdepartment`, ledger, 70 belge, projeler, eval seti, `audit_log`, `/api/departments` ucu (veri değişti, şema aynı), B-08 enum, `manager_id`, AI-BalBal, company-ai `frontend/`.

## 3. Değişen dosyalar

`git diff --stat` (uygulama commit'i): kod `alembic/versions/0010_…py` (yeni), `app/models/user.py`, `app/schemas/{auth,user}.py`, `app/schemas/directory.py` (yeni), `app/repositories/user_repo.py`, `app/api/{users,router}.py`, `app/api/directory.py` (yeni), `app/services/{demo_departments_seed,demo_users_seed,admin_seed}.py`; testler `tests/{test_department_structure,test_directory}.py` (yeni), `tests/{test_migrations,test_auth,test_users,test_demo_users_seed}.py`; docs `README.md`, `docs/{ARCHITECTURE,PHASES}.md`, `docs/notes/TANSU_…md`, bu rapor.

## 4. Testler

- Backend: **432 geçti** (14 yeni: 4 ağaç/görünürlük, 4 rehber, 2 `/me`, 3 admin API, 1 migration yolu; + `test_demo_users_seed` unvan testi, `test_migrations` sütun assert'leri), 15 deselected (`live`), 5 dk 05 sn.
- Geçici kırmızı (ilk koşu): migration `INSERT … SELECT :slug … WHERE slug = :slug` — psycopg aynı parametreyi iki tip bağlamında çözemedi (`AmbiguousParameter`); SELECT listesindeki parametreler `CAST(:x AS varchar)` ile sabitlendi. Testler yakaladı (session fixture'ı `upgrade head`'de patladı), üretime hiç gitmedi.
- `make lint` yeşil; `make eval EVAL_ARGS="--retrieval-only"` 36/36 (T3 doğrulandı: `mali_isler` belgesine atıf yapan soru yok).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar

| Karar | Neden | Etkisi |
|---|---|---|
| Migration parametrelerinde açık `CAST(... AS varchar)` | psycopg `AmbiguousParameter` (§4) | Davranış aynı |
| Seed temiz kurulumda ana departmanı da atar (`primary_department_id IS NULL` ve üyelik varsa) | Boş DB'de migration backfill'i no-op; demo `/me` ana departmansız kalmasın | Mevcut ana departmana dokunmaz |
| `department_slugs` ana departman başta, kalanlar slug sırası | Plan T5; dondurulmuş AI-BalBal `[0]`'ı ana departman sayıyor | `department_ids` aynı sıra; `test_users` eski assert'leri geçerli |
| Rehber `q` boşluk kırpılır, `ILIKE %q%`; `limit` 200, sayfalama yok | V0 ölçeği | — |
| `DirectoryPerson` `extra="forbid"` | Sözleşme 5 alan; yanlışlıkla alan sızmasın | — |
| `UserUpdateRequest`'te `primary_department_id: null` açıkça gönderilirse üyeliği olan kullanıcıda **yeniden ilk üyelik** atanır (null kabul edilmez) | Üyeliği olan `employee` ana departmansız kalmaz (BAGLANTI §3.2/4) | Null yalnızca üyeliksizde kalır |
| Canlı DB'de `finans` 15 belge (plan 14 dedi) | Aşama A canlı testinde admin'in `finans`'a yüklediği `Covenant_Report.xlsx` de görünüyor (18 → 15) | Beklenen |

## 6. Açık sorular (Naci cevaplamalı)

- Yok. C-09 tarayıcı kontrolü ve Tansu-tarafı maddeleri (NOT §4.2) Naci/Tansu'da.

## 7. Riskler / sonraki adım için notlar

- Yeni departmanlar (`ik`, `enerji_uretim_piyasa`, `mali_isler_*`) **boş**; AI-BalBal ana sayfada `management` için boş kartlar görünür. B-18 (15 kişilik personel + belgeler) ayrı faz; `enerji_uretim_piyasa`'ya belge ataması da orada.
- B-08 `department_manager`: backend, Tansu `ROLE_LABELS`/`ROLE_VALUES`/`UserRole`/`UserForm`'u hazırlamadan enum'u genişletmez (NOT §4.2 bağımlılık notu). Sıra: B-08 → B-28 iki aşamalı onay.
- AI-BalBal `AdminUser`/`UserForm` `title` ve `primary_department_id`'yi henüz göstermiyor (eklemeli alanlar, kırılma yok).
- `GET /api/users` admin listesi `title`/`primary_department_id` taşıyor; `/api/directory` ise bilinçli olarak dar.

## 8. Doğruladığım üçüncü taraf davranışları

- psycopg 3 (SQLAlchemy `text()` ile): aynı adlı parametre SELECT listesinde ve `WHERE varchar = :p` karşılaştırmasında kullanılınca `AmbiguousParameter: inconsistent types deduced for parameter $2`; `CAST(:p AS varchar)` çözüyor.
- Alembic `downgrade "0009"` → `upgrade "head"` test içinde çalıştı; `gen_random_uuid()` Postgres 16'da yerleşik.
- Pydantic v2 `model_fields_set`: PATCH gövdesinde alan hiç yoksa kümede yok, `null` gönderilirse var — "verilmedi" ↔ "null" ayrımı için kullanıldı.

## 9. Kaynak kullanımı

- Değişiklik yok (migration milisaniyeler); LLM çağrısı yok (retrieval-only eval + canlı kontroller LLM'siz).
