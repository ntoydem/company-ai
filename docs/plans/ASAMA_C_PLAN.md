# Aşama C — Departman/kullanıcı düzeltmeleri (B-20/1–5, B-09, B-05) — Uygulama Planı

**Tarih:** 01.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` (NOT) §1 B-09/B-05, §2 B-20 (1–5)/B-08, §5.1 (Platform Yetkilendirmesi), "Sonraki aday: B-09/B-13/B-17/B-05" paragrafı; BACKEND_GAPS (dondurulmuş `b219600`) §2.1 (B-20), §2.2 (B-09), §2.3 (unvan/yönetici), §6.1 (B-05); BAGLANTI_YOL_HARITASI §3 (Adım 2: hedef yapı, slug kararı, yapılacaklar, kabul testleri). B-08 bu fazın **dışında** (§4 yalnızca bağımlılık notu).

Okunanlar: `backend/app/services/{demo_departments_seed,demo_users_seed,demo_projects_seed}.py`, `models/{user,user_department,department}.py`, `repositories/{user_repo,department_repo}.py`, `api/{users,departments,auth}.py`, `schemas/{user,department,auth}.py`, `alembic/versions/0001`, `0003`; `seed_data/master/company.yaml`, `seed_data/generator/ledger_schema.py:39,49`, `seed_data/documents/manifest.json` (70 belgenin departman dağılımı), `seed_data/evaluation/questions.json` (`ask_as_user`/`expected_department`/`required_sources`), `scripts/seed_demo.sh`, README demo hesap tablosu, `tests/{test_users,test_documents,test_demo_documents_seed,test_migrations}.py`; AI-BalBal `b219600`: `Home.tsx:33`, `BalbalChat.tsx:32`, `UserMenu.tsx:18,27,62`, `lib/format.ts:45-49,86`, `api/proposed.ts` (`useDirectory`, `DirectoryPerson`), `SearchPanel.tsx:20`, `TeamChat.tsx:21`, `TeamNewChat.tsx`.

---

## 1. Tespitler

- **T1 — Slug'lar değişmez, yalnızca adlar ve dört yeni satır.** BAGLANTI §3.1'in kararı doğru ve zorunlu: 70 demo belgenin `department`'ı `enerji_grubu` 34 / `finans` 14 / `idari_isler` 12 / `hukuk` 7 / `mali_isler` 3, `subdepartment`'ı `enerji_gelistirme` 14 / `enerji_epc_insaat` 10 / `enerji_bakim` 10 (slug olarak); `ledger_schema.py` slug listesini doğruluyor; eval `expected_department` slug; proje seed'i (`demo_projects_seed.py:21-24`) departmanları slug ile bağlıyor; AI-BalBal URL'leri `/departman/<slug>`. **Ledger (`company.yaml`) ad değil slug taşır → ledger ve belgelere dokunulmaz.** Değişen: 5 ad, 4 yeni departman (`ik`, `enerji_uretim_piyasa`, `mali_isler_muhasebe`, `mali_isler_finansal_muhasebe`), 1 üyelik silme.
- **T2 — Seed "varsa dokunma", bu yüzden mevcut DB'ye ad değişikliği seed'le gelmez.** `ensure_demo_departments` var olan satırı hiç güncellemez (`demo_departments_seed.py:49`). Ama **temiz kurulumda migration seed'den önce koşar** (entrypoint: `alembic upgrade head` → seed'ler) — tablo o anda **boş**, dolayısıyla migration'daki `UPDATE`/`DELETE` no-op olur, çocuk departman `INSERT`'leri üst satırı bulamaz. Sonuç: **ikisi de gerekli ve ikisi de koşulsuz güvenli yazılmalı**: migration tüm adımlarını `WHERE EXISTS` / `INSERT … SELECT … WHERE NOT EXISTS` ile korur (var olan DB'yi düzeltir, boş DB'de hiçbir şey yapmaz); seed yeni ağacı kurar (temiz kurulum). Kabul testi iki yolun aynı snapshot'ı verdiğini kanıtlar (§5 C-01/C-02).
- **T3 — `finans` üyelik düzeltmesi eval'i etkilemez.** `questions.json`'da `mali_isler` belgesine `required_sources`/`forbidden_sources` ile atıf yapan **hiçbir soru yok**; `ask_as_user: finans` 20 soru hepsi `finans` belgelerine. `finans` kullanıcısı 3 `mali_isler` belgesini görmez olur (P-5), `yonetim` görmeye devam eder. `--retrieval-only` yine 36/36 beklenir; koşulur.
- **T4 — Mevcut testler eski ağacı pin'lemiyor.** `tests/test_documents.py:314` `mali_isler` departmanını kendi oluşturuyor (`make_department`), demo seed'ine bağlı değil; `test_demo_documents_seed.py:34` `ensure_demo_departments`'ı çağırıyor ama ad/üyelik assert'i yok. README demo tablosu (`:100-103`) `finans | finans, mali_isler` diyor — güncellenir.
- **T5 — AI-BalBal `department_slugs[0]`'ı ana departman sayıyor** (`Home.tsx:33`, `BalbalChat.tsx:32`, `UserMenu.tsx:18,27,62`). B-09 alanı gelene kadar bu kalır. **Uyumluluk hilesi:** `User.department_slugs` property'si **ana departmanı başa** koyarsa dondurulmuş sürüm hiçbir değişiklik olmadan doğru departmanı açar; `primary_department_slug` alanı da ayrıca döner (BAGLANTI §3.2/4'ün adı birebir).
- **T6 — `GET /api/directory` sözleşmesi frontend'de hazır.** `proposed.ts:433-452`: `DirectoryPerson {id, display_name, title, department_slug, department_name}`, `GET /api/directory?q=&department=`; `SearchPanel.tsx:20` (kişi araması), `TeamChat.tsx:21`, `TeamNewChat.tsx` çağırıyor → uç gelince "Kişi araması için şirket rehberi (backend) bekleniyor" kutusu **kendiliğinden kapanır** (alan adları birebir tutulursa). `title` dışında yeni veri gerekmez; `users.title` bugün yok.
- **T7 — `users.manager_id` (BACKEND_GAPS §2.3) Ürün 2 (B-22) için.** NOT §1 B-05 "aynı migration'da eklenebilir, kullanımı B-22'ye kalır" diyor; CLAUDE.md "ileride lazım olur diye ekleme" yasağı → öneri **eklenmesin** (SORU 1).
- **T8 — B-08 enum genişlemesi AI-BalBal'ı kırar, bu yüzden C'de yok.** `format.ts:45-49` `ROLE_LABELS: Record<UserRole,string>` ve `:86` `ROLE_VALUES` üç rolü biliyor; backend `user_role` enum'una `department_manager` eklenirse `/api/users` satırında etiket boş kalır, `UserForm` seçeneği olmaz. B-08 ayrı faz; §4'te Tansu'ya bağımlılık notu.
- **T9 — Yetki birimi üst departman kalır.** Alt birimler (`enerji_*`, yeni `mali_isler_*`) `departments` satırı olur ama `allowed_document_ids` üyeliğe bakar; belgelerin `department`'ı üst slug'dır, `subdepartment` görüntü/filtre alanı (PHASE_1_2_PLAN T7, ADR-004). Bu fazda bu kural **değişmez**; `enerji` kullanıcısı dört alt birimin belgesini görür (BAGLANTI §3.3/5).

---

## 2. Tasarım

### 2.1 B-20 (1–5): departman ağacı

Hedef (BAGLANTI §3.1, zihin haritası birebir; `GET /api/departments` `ORDER BY name`):

| slug (sabit) | name (yeni) | parent |
|---|---|---|
| `finans` | **Proje Finans** (eski "Finans") | — |
| `mali_isler` | Mali İşler | — |
| `mali_isler_muhasebe` **(yeni)** | Muhasebe | `mali_isler` |
| `mali_isler_finansal_muhasebe` **(yeni)** | Finansal Muhasebe | `mali_isler` |
| `hukuk` | Hukuk | — |
| `idari_isler` | İdari İşler | — |
| `ik` **(yeni)** | İK | — |
| `enerji_grubu` | **Enerji** (eski "Enerji Grubu") | — |
| `enerji_gelistirme` | **Proje Geliştirme** (eski "Geliştirme") | `enerji_grubu` |
| `enerji_bakim` | **O&M (İşletme ve Bakım)** (eski "Bakım") | `enerji_grubu` |
| `enerji_epc_insaat` | **EPC (İnşaat)** (eski "EPC-İnşaat") | `enerji_grubu` |
| `enerji_uretim_piyasa` **(yeni)** | Üretim/Piyasa | `enerji_grubu` |

- **Migration `0010_department_structure_and_user_fields`** (tek migration, §2.2/§2.3 sütunlarıyla birlikte):
  1. `UPDATE departments SET name=… WHERE slug=… AND name<>…` (5 satır; boş DB'de no-op).
  2. `INSERT INTO departments (id, name, slug, parent_id) SELECT gen_random_uuid(), 'İK', 'ik', NULL WHERE NOT EXISTS (SELECT 1 FROM departments WHERE slug='ik')`; çocuklar için `parent_id = (SELECT id FROM departments WHERE slug='enerji_grubu')` ve **üst yoksa INSERT atlanır** (`WHERE EXISTS (üst)`).
  3. `DELETE FROM user_departments WHERE user_id = (SELECT id FROM users WHERE username='finans') AND department_id = (SELECT id FROM departments WHERE slug='mali_isler')` (P-5; satır yoksa no-op).
  4. (SORU 4 evetse) `UPDATE users SET display_name='Proje Finans' WHERE username='finans' AND display_name='Finans'`.
  5. `downgrade`: adları geri çevirir, dört yeni satırı siler (`user_departments`/`project_departments` cascade), silinen üyeliği **geri eklemez** (veri kaybı yok — üyelik kasıtlı kaldırıldı; downgrade testi bunu bilir).
- **`demo_departments_seed.py`**: `_DEPARTMENTS` yeni ağaç; `_DEMO_USER_DEPARTMENTS["finans"] = ("finans",)`; docstring. "Varsa dokunma" davranışı **korunur** (seed hâlâ idempotent ve pasif; düzeltme migration'ın işi).
- **`demo_users_seed.py`**: `display_name` "Finans" → "Proje Finans" (SORU 4), `title` (§2.3).
- README demo hesap tablosu, `docs/ARCHITECTURE.md` ADR-004 Phase 1.2 satırına concretization ("ağaç 01.10.2026'da genişledi; hâlâ seed/migration = platform işi, NOT §5.1").

### 2.2 B-09: ana departman

- `users.primary_department_id uuid NULL REFERENCES departments(id) ON DELETE SET NULL` (migration `0010`). Backfill: `UPDATE users u SET primary_department_id = (SELECT ud.department_id FROM user_departments ud JOIN departments d ON d.id=ud.department_id WHERE ud.user_id=u.id ORDER BY ud.created_at, d.slug LIMIT 1) WHERE u.primary_department_id IS NULL` — **en eski üyelik**, eşitlikte slug sırası (deterministik). Üyelik düzeltmesi (§2.1/3) **önce** koşar, böylece `finans`'ın ana departmanı `finans` olur (demo'da zaten tek üyelik kalıyor).
- Kural (BAGLANTI §3.2/4): ana departman üyeliklerden biri olmalı; `management`/`admin` için `NULL` olabilir; üyeliği olan `employee` için `NULL` bırakılmaz (otomatik ilk üyelik).
- `models/user.py`: `primary_department_id`, `primary_department` relationship; `primary_department_slug` property; **`department_slugs` ana departmanı başa alır** (T5), `department_ids` aynı sıra.
- `schemas/auth.py::CurrentUserResponse.primary_department_slug: str | None` (`/login` + `/me`, `from_user`'a eklenir).
- `schemas/user.py`: `UserCreateRequest.primary_department_id: UUID | None`, `UserUpdateRequest.primary_department_id`, `UserResponse.primary_department_id`. `api/users.py` + `user_repo`: verilen `primary_department_id` üyeliklerde değilse **422** (`PRIMARY_DEPARTMENT_NOT_A_MEMBERSHIP_MESSAGE`); verilmezse: mevcut ana departman üyeliklerde kalıyorsa korunur, kalmıyorsa (veya hiç yoksa) ilk üyelik; üyelik yoksa `NULL`. Mantık tek yerde `user_repo.set_memberships(...)` benzeri yardımcıda.

### 2.3 B-05: unvan ve rehber

- `users.title varchar(128) NULL` (migration `0010`). `manager_id` **eklenmez** (SORU 1).
- `UserCreateRequest/UserUpdateRequest.title: str | None`, `UserResponse.title`, `CurrentUserResponse.title` (UserMenu için).
- Demo unvanları (`demo_users_seed.py`, kurgusal/jenerik, P-9; seed yalnızca **yeni** kullanıcıya yazar — mevcut demo kullanıcılarına migration `UPDATE users SET title=… WHERE username=… AND title IS NULL` ile verilir, SORU 2): `yonetim` "Genel Müdür Yardımcısı", `finans` "Proje Finans Uzmanı", `hukuk` "Hukuk Müşaviri", `enerji` "Enerji Grubu Uzmanı", `admin` "Sistem Yöneticisi".
- **`GET /api/directory?q=&department=`** (`api/directory.py`, `schemas/directory.py::DirectoryPerson`): `get_current_user` (her kimlikli kullanıcı, admin değil). Dönüş yalnızca `{id, display_name, title, department_slug, department_name}` — `department_*` = **ana departman** (yoksa `null`); `username`, `role`, `is_active`, `password_hash` **dönmez** (BACKEND_GAPS §6.1). `q`: `display_name` **veya** `title` üzerinde `ILIKE %q%` (boş = hepsi); `department`: o slug'a **üye** olanlar (ana departman değil üyelik — "Finans'ta kim var" sorusunun cevabı; bilinmeyen slug → boş liste, 404 değil). Yalnızca `is_active = true`. `management`/`admin` de listelenir (`department_*` `null`; sohbete eklenebilir kişiler, SORU 3). Sıra `display_name`. Sayfalama yok (V0, onlarca kullanıcı); `limit` sabit 200.
- `user_repo.search_directory(session, q, department_slug)`.

### 2.4 Dokunulmayanlar

`allowed_document_ids` ve ADR-004 kuralları (üst departman = yetki birimi), `documents.department`/`subdepartment` değerleri, ledger, 70 belge, projeler, eval seti, `audit_log`, `/api/departments` ucu (ad değişikliği veriden gelir), AI-BalBal, company-ai `frontend/`, B-08 enum.

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `alembic/versions/0010_department_structure_and_user_fields.py` | §2.1 veri düzeltmeleri (korumalı), `users.primary_department_id`, `users.title`, backfill, demo unvanları |
| `app/services/demo_departments_seed.py`, `demo_users_seed.py` | yeni ağaç, `finans` tek üyelik, unvan/display_name |
| `app/models/user.py` | `primary_department_id`, `title`, `primary_department_slug`, `department_slugs` sırası |
| `app/schemas/{auth,user}.py`, `schemas/directory.py` (yeni) | alanlar; `DirectoryPerson` |
| `app/repositories/user_repo.py` | `create/update` yeni alanlar + ana departman kuralı; `search_directory` |
| `app/api/users.py`, `api/directory.py` (yeni), `api/router.py` | 422 kuralı; `GET /api/directory` |
| `tests/{test_migrations,test_users,test_auth,test_authorization,test_demo_documents_seed}.py`, `tests/test_directory.py` (yeni), `tests/test_department_structure.py` (yeni, snapshot) | §5 |
| `README.md` (demo hesap tablosu, `/me` alanları, `/api/directory`), `docs/ARCHITECTURE.md` (ADR-003: `primary_department_slug`/`title` `/me`'de; ADR-004: ağaç + "yetki birimi üst departman" korunuyor), `docs/PHASES.md` notu, NOT (§1 B-09/B-05, §2 B-20 UYGULANDI; §4.1/§4.2 satırları; B-08 bağımlılık notu), `docs/reports/ASAMA_C_REPORT.md` | docs |

Yeni uç: `GET /api/directory`. Değişen uçlar (eklemeli): `GET/POST/PATCH /api/users`, `POST /api/auth/login`, `GET /api/auth/me`. `GET /api/departments`: şema aynı, **veri** değişir.

---

## 4. B-08'in AI-BalBal tarafı — bağımlılık notu (bu planın işi değil)

`department_manager` rolü (B-08) C'de **eklenmiyor** (T8). Eklendiği fazda Tansu tarafında zorunlu:
- `lib/format.ts:45-49` `ROLE_LABELS` + `:86` `ROLE_VALUES`'a `department_manager: "Departman Yöneticisi"`; `types.ts:3` `UserRole` birliğine değer; `UserForm` rol seçicisi. Aksi halde `/api/users` satırında rol etiketi boş, form seçeneği yok.
- Sıra bağımlılığı: B-08 → B-28 iki aşamalı onay (NOT §5.2 "B-08, B-28'den önce gelir").
C'nin kendi Tansu-tarafı maddeleri (bilgi, NOT §4.2'ye yazılır): `department_slugs[0]` → `primary_department_slug` (üç dosya; T5 sayesinde zorunlu değil), `UserMenu`'de `title`, `/api/directory` kutusunun kendiliğinden kapanmasının teyidi, yeni departman kartlarının (İK, Üretim/Piyasa, Mali İşler alt birimleri) adlarını API'den aldığının teyidi.

---

## 5. Demo verisi etkisi — yeniden seed gerekmez

- 70 belge: `department`/`subdepartment` slug'ları aynı → dokunulmaz, `make reset-demo`/`make seed` gerekmez. `make seed` idempotent kalır (yeni departmanlar seed'den de gelir, varsa dokunmaz).
- Projeler: `enerji_grubu`/`finans`/`hukuk` slug bağları aynı.
- Kullanıcılar: 5 hesap aynı; `finans` 3 `mali_isler` belgesini artık görmez (P-5, T3), `yonetim`/`admin` görür. Audit log etkilenmez.
- Yeni departmanlar **boş** (İK, Üretim/Piyasa, Muhasebe, Finansal Muhasebe'ye belge yok): AI-BalBal ana sayfada `management` için boş kartlar görünür; B-18 (15 kişilik personel + belgeler) ayrı faz. `enerji_uretim_piyasa` alt birimine belge atanması da B-18'de.
- Dev VM: `make up` → migration adları/satırları/üyeliği düzeltir; **downtime yok**, oturumlar korunur.

---

## 6. Kabul kriterleri ve kanıt

| # | Kriter | Test / komut |
|---|---|---|
| C-01 | **Snapshot (temiz kurulum):** test DB'de `ensure_demo_departments` → `GET /api/departments` §2.1 tablosuyla birebir (ad, slug, parent slug), 12 satır | `test_department_structure.py::test_seed_tree_matches_mind_map` |
| C-02 | **Snapshot (migration yolu):** `downgrade 0009` → eski ağaç + `finans`'a `finans`+`mali_isler` üyeliği elle eklenir → `upgrade head` → aynı 12 satır, `finans` yalnızca `finans` üyesi, `primary_department_id = finans`, unvanlar dolu; boş DB'de `upgrade` hata vermez (`test_downgrade_to_empty_then_upgrade_head` revizyon `0010`) | `test_migrations.py` |
| C-03 | `finans` kullanıcısı `mali_isler` belgesini **göremez**: liste yok, indirme 403, `/api/ask` retrieval'a girmez (`retrieved_document_ids` boş); `yonetim` görür | `test_authorization.py` + `test_ask.py` (demo seed'li fixture) |
| C-04 | `enerji` dört alt birimin (`enerji_uretim_piyasa` dahil) `department="enerji_grubu"` belgelerini görür | `test_authorization.py` |
| C-05 | `/login` ve `/me`: `primary_department_slug` üyeliklerden biri; `department_slugs[0] == primary_department_slug`; `management`/`admin` → `null`; `title` döner | `test_auth.py` |
| C-06 | Admin API: `primary_department_id` üyelikte değil → 422; verilmezse ilk üyelik; `department_ids` daraltılıp ana departman düşerse yeni ilk üyelik; `title` yazılır/okunur | `test_users.py` |
| C-07 | `GET /api/directory`: kimliksiz 401; `employee` 200; alanlar **yalnızca** 5 (şema `extra` yok, `password_hash`/`role`/`username` yok); `q` ad ve unvanda arar (`"müş"` → Hukuk Müşaviri); `department=finans` üyeleri; bilinmeyen slug → `[]`; pasif kullanıcı listelenmez; `management` `department_slug: null` ile listelenir | `test_directory.py` |
| C-08 | `make test`, `make lint` yeşil; `make eval EVAL_ARGS="--retrieval-only"` 36/36 (T3) | komutlar |
| C-09 | Canlı (`company-ai-dev`, LLM yok): `make up` sonrası `GET /api/departments` adları ("Proje Finans", "Enerji", "Üretim/Piyasa", "İK", "Muhasebe"…); `finans` ile `/me` → `department_slugs: ["finans"]`, `primary_department_slug: "finans"`, `title`; `GET /api/documents` olarak `finans` → 14 belge (öncesi 17); `GET /api/directory?q=hukuk` → 1 kişi, 5 alan; `GET /api/directory?department=enerji_grubu` → `enerji`; `psql`: `user_departments` `finans`→`mali_isler` satırı yok | komut çıktıları rapora; AI-BalBal tarayıcı kontrolü (kart adları, kişi araması kutusunun kapanması) **Naci elle** |

---

## 7. SORU (Naci cevaplamalı)

1. **`users.manager_id` şimdi mi?** BACKEND_GAPS §2.3 ve NOT B-05 "aynı migration'da eklenebilir" diyor; kullanımı B-22 (Ürün 2). Öneri: **hayır**, B-22'de gelir (CLAUDE.md "ileride lazım olur" yasağı).
2. **Demo unvanları** (kurgusal/jenerik): `yonetim` "Genel Müdür Yardımcısı", `finans` "Proje Finans Uzmanı", `hukuk` "Hukuk Müşaviri", `enerji` "Enerji Grubu Uzmanı", `admin` "Sistem Yöneticisi" — uygun mu? Mevcut hesaplara migration ile (`title IS NULL` iken) verilmesi kabul mü?
3. **Rehberde `management`/`admin`:** listelensin (öneri; `department_slug: null`) mi, yoksa yalnızca departman üyeleri mi?
4. **`finans` kullanıcısının `display_name`'i** "Finans" → "Proje Finans" (öneri: evet, departman adıyla tutarlı; kullanıcı adı `finans` aynı kalır)?
5. **Ana departman backfill kuralı:** en eski üyelik, eşitlikte slug sırası (öneri) — uygun mu? (Demo'da tek üyelik kalıyor, kural yalnızca ileride çok üyelikli kullanıcılar için.)
6. **Faz birimi:** etiketsiz düz commit + PHASES.md notu (A/B ile aynı) — uygun mu?

---

## 8. Kendi aldığım küçük kararlar

- Tek migration (`0010`): departman veri düzeltmeleri + iki kullanıcı sütunu + backfill; hepsi `EXISTS`-korumalı, boş DB'de no-op (T2).
- Seed "varsa dokunma" olarak kalır; düzeltme sorumluluğu migration'da (iki yol aynı snapshot'ı verir, C-01/C-02).
- `department_slugs` ana departmanı başa alır (T5) — dondurulmuş AI-BalBal değişiklik gerektirmez.
- Rehber `department` süzgeci **üyelik** üzerinden, `department_*` alanı **ana departman**; pasifler dışarıda; `limit` 200, sayfalama yok.
- `downgrade` silinen üyeliği geri eklemez (kasıtlı düzeltme, veri kaybı değil).
- B-08 enum'u, `manager_id`, B-18 personel listesi, `SourceCard.project_code/name` **bu fazda yok**.
