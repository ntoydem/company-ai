# B-08 — Departman yöneticisi rolü (`department_manager`) — Uygulama Planı

**Tarih:** 02.10.2026 · **Durum:** Naci onayı bekliyor, uygulamaya geçilmedi · **Kod yazılmadı.**

Kaynak: BACKEND_GAPS (dondurulmuş `b219600`) §2.4 (B-08 önerilen karar: "`department_manager` rolü; kendi departman(lar)ı, `normal` + `restricted`"), §2.6.1/6 (klasör yetkisi gizlilik düzeyini aşmaz — "B-08 gelince müdür grant'li klasörde de `restricted` görür"); NOT `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §2 B-08, §5.1 (B-08 satırı: sabit kural, tablo değil), §5.2 (ikinci onaycı = hedef departmanın kendi `department_manager`'ı — **KAPANDI 30.09.2026, Naci**), §7.2 #1 (açık: müdür `board` görür mü; kural sabit mi tablo mu), §8.1 (departman yapısı müşteri yönetir — rolü kişiye **müşteri admin'i** verir).

Okunanlar: `backend/app/services/authorization.py` (gate + `SingleDocumentIdsProvider`), `repositories/document_repo.py::SqlDocumentIdsProvider`, `models/{user,department,document}.py`, `api/{documents,folders,users,deps}.py`, `schemas/user.py`, `alembic/versions/0001_init_users.py` (`user_role` enum'u `CREATE TYPE` ile), `0011_folders.py` (korumalı veri adımı deseni), `services/demo_{users,departments}_seed.py`, `tests/{test_authorization,test_users,test_migrations,conftest}.py`, AI-BalBal `b219600` `api/types.ts:3` (`UserRole` birliği), `lib/format.ts:48,86` (`ROLE_LABELS`/`ROLE_VALUES`), `lib/visibility.ts:8`, `docs/ARCHITECTURE.md` ADR-004, `docs/DOMAIN_MODEL.md` §4–5, `docs/SPEC_02 §5`, canlı DB (`documents` departman × gizlilik dağılımı).

---

## 1. Tespitler

- **T1 — Kural değişikliği tek yerde ve küçük.** `allowed_document_ids`'in `employee` dalı bugün `_EMPLOYEE_CONFIDENTIALITY_LEVELS = (normal,)` ile çalışıyor; üyelik ∪ klasör grant'leri aynı seviye kümesini alıyor. `department_manager` **aynı dal**, yalnızca seviye kümesi `(normal, restricted)`. Yeni provider metodu, yeni imza, yeni tablo **yok** (ADR-004 imzası sabit). `SingleDocumentIdsProvider` seviye kümesini parametre olarak aldığı için "bu belgeyi kim görebilir" (`/visibility`) **değişiklik olmadan** doğru çalışır.
- **T2 — Yetki birimi üst departman, bugün de öyle.** Canlı DB: `documents.department` yalnızca üst departman slug'ı (`enerji_grubu 36 normal`, `finans 15 normal + 1 restricted`, `hukuk 7`, `idari_isler 7 normal + 5 board`, `mali_isler 3`); alt birim `documents.subdepartment`'ta, yetki girdisi değil (ADR-004 Aşama C). Müdürün departmanları = **üyelikleri** (`user_departments`), `employee` ile aynı — alt birim üyeliği olan bir müdür üst departmanın belgelerini **görmez**, bugünkü `employee` davranışıyla simetrik. Ayrı bir "müdürü olduğu departman" alanı/tablosu açılmaz (§5.1: kuralı müşteri değil, kişiyi değiştirir).
- **T3 — Yazma tarafı kendiliğinden doğru.** `documents.py::upload_document`'taki üç kontrol (`department ∈ department_slugs` güvenlik yaması, klasör `write` kontrolü, `role not in (management, admin)` muafiyeti) ve `folders.py::list_user_folders`'ın `admin/management → write` dalı müdürü **`employee` gibi** ele alır — §5.2'nin "management/admin genel onaysız-yükleme ayrıcalığı taşımaz, müdür kendi departmanına yükler" kuralıyla tutarlı. Bu yüzden bu dosyalara dokunulmaz; yalnızca davranış **testle kilitlenir** (M-05).
- **T4 — Postgres enum genişletme.** `user_role` `CREATE TYPE … AS ENUM` ile açılmış (0001). `ALTER TYPE user_role ADD VALUE 'department_manager'` PG 12+'da transaction içinde çalışır; yeni değer **aynı transaction'da kullanılamaz** — migration değeri kullanmaz, sorun yok (Alembic `env.py` tüm upgrade'i tek transaction'da koşuyor; `test_migrations.py` bunu kanıtlar). **Downgrade** enum'dan değer silemez: `UPDATE users SET role='employee' WHERE role='department_manager'` → tipi yeniden yarat (rename eski, create yeni, `ALTER COLUMN … TYPE … USING role::text::user_role`, drop eski). `test_downgrade_to_empty_then_upgrade_head` bu yolu da çalıştırır.
- **T5 — Rolü kim verir: zaten var olan uç.** `PATCH /api/users/{id}` (`require_admin`) `role` alıyor; `UserRole` enum'u genişleyince Pydantic/`UserResponse` yeni değeri otomatik kabul eder/döndürür. Lockout koruması (`admin` kendini düşüremez) değişmez. `primary_department_id` kuralı ("üyeliklerden biri olmalı") müdüre de uygulanır; müdürün **en az bir üyeliği olmalı** — yoksa `employee` gibi hiçbir şey görmez (bugünkü fail-safe).
- **T6 — Dondurulmuş AI-BalBal'ın durumu (kırılma yok, bilgi).** `types.ts:3` `UserRole = "admin" | "management" | "employee"`; `ROLE_LABELS[department_manager]` → `undefined` (boş etiket), `UserForm` `ROLE_VALUES` yeni rolü **listelemez** (admin bu rolü dondurulmuş UI'dan veremez; `/api/users` + curl ile verir — README'de örnek var). `visibility.ts:8` ve `Home.tsx:33` `role !== "employee"`'yi "her şeyi görür" sayar → müdür için departman kartları gizlenmez; **kolaylık katmanı**, yetki sunucuda (ADR-004). Tansu'ya 3 kalemlik to-do: birliğe ekle, etiket "Departman Yöneticisi", `visibility.ts`/`Home`/`BalbalChat`'te müdürü `employee` gibi (üyelik bazlı) ele al.
- **T7 — Demo verisinde tek `restricted` belge:** `DOC-ANK-FIN-008` (`finans`). Kabul kriteri canlıda yalnızca bir `finans` müdürüyle gösterilebilir (M-08); `board` belgeler `idari_isler`'de (5) — "müdür `board` görmez" kuralı için canlı negatif test `idari_isler` müdürü ister, birim testle kanıtlanır. Demo kullanıcı eklenip eklenmeyeceği → **SORU 1**.
- **T8 — Rol değişikliği kayıt defteri.** NOT §5.1: "yetki değişiklikleri … denetim kaydına yazılarak (`folder_grant_events` deseni, roller için de aynı)". Bugün `PATCH /api/users` hiçbir olay yazmıyor (rol, aktiflik, üyelik). Bu B-08'in değil, **kullanıcı yönetiminin** eksiği; bu fazda eklenmesi fazı büyütür → **SORU 2**.
- **T9 — Eval/retrieval etkilenmez.** `retrieve()` allowed id kümesini alır; `questions.json` `ask_as_user` değerleri (`enerji`, `finans`, `hukuk`, `yonetim`, `admin`) değişmez. Retrieval-only eval regresyon olarak koşar, LLM çağrısı gerekmez.

---

## 2. Tasarım

### 2.1 Model ve migration (`0012_user_role_department_manager`)

- `UserRole` (`models/user.py`): `department_manager = "department_manager"` eklenir (sıra: `admin, management, department_manager, employee` — yalnızca okunabilirlik; DB enum'unda sıra önemsiz).
- Migration `0012`: `upgrade`: `ALTER TYPE user_role ADD VALUE IF NOT EXISTS 'department_manager'`. `downgrade`: T4'teki yeniden-yaratma. Veri adımı yok (hiç kimse otomatik müdür yapılmaz — kişiyi müşteri admin'i seçer, §8.1).
- Yeni tablo/kolon **yok**. `users.manager_id` **yine eklenmiyor** (B-22'ye ait, Aşama C kararı korunur).

### 2.2 Yetki kuralı (`authorization.py`)

```python
_MANAGER_CONFIDENTIALITY_LEVELS = (Confidentiality.normal, Confidentiality.restricted)

def _membership_confidentiality_levels(role: UserRole) -> tuple[Confidentiality, ...]:
    return _MANAGER_CONFIDENTIALITY_LEVELS if role == UserRole.department_manager else _EMPLOYEE_CONFIDENTIALITY_LEVELS
```

- `allowed_document_ids`: `admin` ve `management` dalları aynen; üçüncü dal (`employee` **ve** `department_manager`) üyelik slug'larıyla `list_document_ids_for_departments(...)` ∪ `list_document_ids_for_folder_grants(...)` çağırır, **ikisine de** role göre seviye kümesini verir. Böylece müdür grant'li klasörde de `restricted` görür (BACKEND_GAPS 2.6.1/6), `board` hiçbir yoldan görmez (SORU'suz varsayılan: NOT §7.2 #1, ADR-004 muhafazakâr okuma — bkz. §5 kararlar).
- Docstring'e B-08 paragrafı; modül başındaki kural özeti güncellenir.
- `SqlDocumentIdsProvider`, `SingleDocumentIdsProvider`, `FakeProvider`: **değişmez** (seviye kümesi zaten parametre).

### 2.3 API

- Yeni uç **yok**. `POST/PATCH /api/users` yeni rol değerini kabul eder (enum genişlemesiyle otomatik); `GET /api/auth/me`, `/api/users`, `/api/directory`, `/visibility` yeni rolü döndürür.
- Türkçe hata mesajı değişmez. `require_admin` değişmez (müdür **yönetim işlemi yapamaz**; klasör/grant/kullanıcı uçları admin'de kalır).

### 2.4 Seed (SORU 1'e bağlı)

- **Önerilen (a):** `demo_users_seed.py`'ye bir kullanıcı: `("finans_mudur", "Proje Finans Müdürü", UserRole.department_manager, "Proje Finans Müdürü")`, üyelik `("finans",)`; `_DEMO_USER_DEPARTMENTS` ve `department_fixtures.py` güncellenir; `DEMO_USER_PASSWORD` ortak. Tek restricted demo belge `finans`'ta olduğundan canlı kabul kriterini (M-08) gösterir; SPEC_02 §5 demo hesap listesine satır eklenir (P-9: unvan kurgusal/jenerik).
- (b) Seed'e dokunmadan yalnızca test + `PATCH /api/users` ile canlı doğrulama.

---

## 3. Dosyalar

| Dosya | Değişiklik |
|---|---|
| `backend/app/models/user.py` | `UserRole.department_manager` |
| `backend/alembic/versions/0012_user_role_department_manager.py` | **yeni** — enum değeri + geri alınabilir downgrade |
| `backend/app/services/authorization.py` | seviye kümesi role göre; üyelik dalı iki rolü kapsar; docstring |
| `backend/app/services/demo_users_seed.py`, `demo_departments_seed.py` | (SORU 1a) `finans_mudur` + üyelik |
| `backend/tests/test_authorization.py` | M-01..M-04 birim testleri |
| `backend/tests/test_documents.py` (veya yeni `test_department_manager.py`) | M-05..M-07 API testleri (liste, visibility, upload 403) |
| `backend/tests/test_users.py` | M-09 rol atama |
| `backend/tests/test_migrations.py` | M-10 (`0012` upgrade/downgrade, mevcut iki test zaten koşar) |
| `backend/tests/test_demo_users_seed.py`, `department_fixtures.py` | (SORU 1a) |
| `docs/ARCHITECTURE.md` | ADR-004 concretization satırı (B-08) |
| `docs/DOMAIN_MODEL.md` §4 (`user_role` değerleri), §5 (kural satırı) · `docs/SPEC_02 §5` (rol + demo hesap) · `README.md` (rol tablosu, demo hesap) | güncelleme |
| `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` | §2 B-08 **UYGULANDI**, §5.1 tablo satırı, §7.2 #1 **KAPANDI** (varsayılanlarla), Tansu to-do (T6) |
| `docs/PHASES.md` | "B-08 (02.10.2026, `<commit>`)" notu · `docs/reports/B08_DEPARTMAN_MUDURU_REPORT.md` |

Dokunulmayanlar: `api/documents.py`, `api/folders.py`, `api/users.py`, `repositories/*`, `schemas/*`, `authorization.py` imzası, `FakeProvider`, retrieval, prompt, eval seti, AI-BalBal.

---

## 4. Kabul kriterleri ve testler

| # | Kriter | Test |
|---|---|---|
| M-01 | Müdür, üye olduğu departmanın `normal` **ve** `restricted` belgelerini görür; `board` görmez | `test_authorization`: FakeProvider `seen_department_calls` → `(slugs, (normal, restricted))`; `board` id'si sonuçta yok |
| M-02 | Müdür başka departmanın hiçbir belgesini görmez (restricted dahil) | provider çağrısı yalnızca kendi slug'larıyla; sonuç ⊆ provider çıktısı |
| M-03 | Klasör grant'i: müdür grant'li klasörde `normal + restricted` görür, `board` görmez | `seen_folder_calls` → `(slugs, (normal, restricted))` |
| M-04 | Üyeliği olmayan / pasif müdür → ∅; `employee` ve `management` davranışı **değişmez** | mevcut testler yeşil + iki yeni negatif |
| M-05 | SQL yolu: `GET /api/documents` müdür için restricted belgeyi listeler, `employee` aynı departmanda listelemez; `board` belge ikisine de görünmez | `test_documents`: 3 belge (normal/restricted/board, `finans`) + müdür/employee istemci |
| M-06 | `GET /api/documents/{id}/visibility` restricted belge için müdürü **içerir**, employee'yi içermez | `SingleDocumentIdsProvider` değişmeden |
| M-07 | Yazma tarafı: müdür **başka** departmana upload → 403 `DEPARTMENT_NOT_ALLOWED_MESSAGE`; kendi departmanına → 201; `/api/folders`'ta kendi kökü `write`, grant'siz başka kök listelenmez | T3 kilidi |
| M-08 | Canlı (LLM'siz): `finans_mudur` (ya da PATCH ile müdür yapılmış kullanıcı) `GET /api/documents` → `DOC-ANK-FIN-008` listede; `finans` (employee) → listede yok; `GET /api/search?q=` aynı belgeyi müdüre bulur, employee'ye bulmaz | curl, raporda çıktı |
| M-09 | Admin `PATCH /api/users/{id}` ile `role=department_manager` verir; `/me` yeni rolü döndürür; `primary_department` kuralı korunur | `test_users` |
| M-10 | Migration `0012` boş DB'den head'e ve geri çalışır; downgrade müdürleri `employee`'ye düşürür | `test_migrations` (mevcut iki test + bir veri testi) |
| M-11 | Regresyon: `make test` yeşil, `make lint` yeşil, `make eval EVAL_ARGS="--retrieval-only"` 39/39, `make validate-ledger` 0 hata | komut çıktıları |

LLM çağrısı: **0** (canlı kriter liste + `/api/search` ile).

---

## 5. Kendi aldığım küçük kararlar (raporda da listelenecek)

- Seviye kümesi role göre seçilen bir tuple; `employee`/`department_manager` **tek dalda** (kopya kod yok).
- Enum değeri adı `department_manager` (BACKEND_GAPS §2.4 ve NOT'taki tüm referanslarla aynı; Tansu'nun `types.ts` birliğine aynı string girer).
- Downgrade enum'u yeniden yaratır (değer silinemez); `ADD VALUE IF NOT EXISTS` ile upgrade idempotent.
- Müdürün departmanı = üyelikleri; ayrı "yöneticisi olduğu departman" alanı yok (T2, §5.1).
- `require_admin` kapsamı değişmez; müdür yönetim ucu kullanmaz.
- Rapor + PHASES.md notu; **faz etiketi yok** (son turlarla aynı — SORU 4 teyit).

---

## SORU (Naci cevaplamalı)

1. **Demo müdür kullanıcısı eklensin mi?** Önerim **(a)**: tek kullanıcı `finans_mudur` (`department_manager`, üyelik `finans`, unvan "Proje Finans Müdürü", ortak `DEMO_USER_PASSWORD`) — tek restricted demo belge `finans`'ta, kabul kriteri canlıda gösterilir ve Tansu'nun demo senaryosu (BACKEND_GAPS §9/6 "ikinci onay: departman yöneticisi") için hesap hazır olur. (b): seed'e dokunma, yalnızca test + PATCH ile doğrula. (a) SPEC_02 §5 demo hesap listesini genişletir — ürün kararı.
2. **Rol/üyelik değişikliği kayıt defteri (`user_role_events` benzeri) bu fazda mı?** Önerim **hayır**: B-08 yalnızca kuralı ekler; `PATCH /api/users`'ın olay kaydı (rol, aktiflik, üyelik — `folder_grant_events` deseni) B-28/§5.2 onay fazından **önce** ayrı küçük bir iş olarak planlanır (NOT §5.1'e not düşülür). Evet dersen bu plana `user_events` tablosu + `GET /api/admin/users/audit` eklenir (~+1 migration, +1 uç, +4 test).
3. **İki varsayılan teyidi (NOT §7.2 #1):** müdür `board` **görmez**; kural **sabit** (tablo değil). Onaylıyorsan #1 bu fazla KAPANDI işaretlenir.
4. **Etiketsiz düz commit + PHASES.md notu** (Aşama A–E ve Ürün 1 turuyla aynı) — teyit.

---

## Uygulama sırası

1. `UserRole` + migration `0012` (+ `test_migrations` veri testi) → `make test -k migrations`.
2. `authorization.py` kural + `test_authorization` (M-01..M-04).
3. API testleri (M-05..M-07, M-09) — kod değişikliği beklenmez; kırmızı çıkarsa **neden** raporlanır, sessizce yama yapılmaz.
4. (SORU 1a) seed + fixture + `test_demo_users_seed`.
5. `make test`, `make lint`, retrieval-only eval, `validate-ledger`.
6. Canlı M-08 (`make up` sonrası `alembic upgrade` + seed; curl).
7. Docs (ADR-004, DOMAIN_MODEL, SPEC_02 §5, README, NOT, PHASES.md) → rapor → commit → hash çapraz referansı → push → dur.
