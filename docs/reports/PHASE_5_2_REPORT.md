# Phase 5.2 Raporu — Admin panel

**Tarih:** 26.09.2026  **Model:** Sonnet 5  **Tag:** phase-5-2  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den) | Durum | Kanıt |
|---|---|---|---|
| 1 | admin her işlemi UI'dan yapabilir | ✅ | `/yonetim/kullanicilar` (kullanıcı ekle/rol/aktiflik/departman), `/yonetim/denetim-kaydi` (filtreli liste + detay); belge detayında "kim görebilir" kartı + manuel metadata formu; proje CRUD zaten Phase 3.3'ten UI'da vardı |
| 2 | employee admin endpoint'lerinde 403 | ✅ | `test_employee_create_user_returns_403`, `test_employee_list_users_returns_403`, `test_edit_metadata_requires_admin`, `test_visibility_requires_admin` (+ mevcut `test_list_requires_admin`/`test_detail_requires_admin` audit log'da) |
| 3 | audit'te gizli veri yok | ✅ | Değişmedi — Phase 5.2 audit log'un backend'ine dokunmadı, yalnızca mevcut `GET /api/audit-log` uçlarını tüketen bir UI ekledi |

**Genel sonuç:** Kapsamdaki 6 kalemden 2'si (proje CRUD, audit log backend) zaten tamamdı; kalan 4'ü
(kullanıcı yönetimi, departman üyelik ataması, manuel metadata düzenleme, "kim görebilir") bu fazda
eklendi, audit log'un yalnızca admin UI'ı eklendi (backend Phase 3.4'ten değişmeden).

## 2. Yapılanlar
- **`POST/GET /api/users`, `PATCH /api/users/{id}`** (yeni `app/api/users.py`, `app/schemas/user.py`): kullanıcı
  oluşturma (username/password/display_name/role/department_ids), listeleme, rol/aktiflik/departman düzenleme.
  `password_hash` hiçbir response şemasında yok; `username` oluşturma sonrası immutable (PATCH şemasında hiç
  yok). Admin kendi hesabının rolünü `admin` dışına düşüremez veya `is_active=false` yapamaz (409) — V0'da
  şifre kurtarma akışı olmadığından, aksi halde tüm admin endpoint'lerine erişimin kaybolabileceği bir
  kilitlenmeyi önler (T6).
- **`PATCH /api/documents/{id}`** (manuel metadata düzenleme): Phase 3.2'nin AI-öneri-kabul akışıyla aynı 9 alan
  (`department, subdepartment, project_code, document_type, counterparty, document_date, status,
  confidentiality, tags`) + `title`/`effective_date`/`expiration_date` (12 alan toplam — SORU 1'in "11 alan"
  ifadesi bir sayım hatasıydı, alan listesinin kendisi netti ve öyle uygulandı). Versiyon zinciri alanları
  (`supersedes_document_id` vb.) şemada hiç yok — ADR-012'nin zincir bütünlüğü kontrollerini (upload/apply
  akışındaki "predecessor görünür mü / zaten superseded mi" kontrolleri) bypass etmesin diye. Öneri akışıyla
  paylaşılan bir `_resolve_metadata_updates()` yardımcı fonksiyonu (`department`/`project_code` çözümleme
  mantığı tekrarlanmadı, T4/T5 deseni).
- **`GET /api/documents/{id}/visibility`** ("bu belgeyi kim görebilir"): `app/services/authorization.py`'ye
  eklenen `SingleDocumentIdsProvider`, `DocumentIdsProvider` protokolünü tek bir belgeye sararak
  `allowed_document_ids()`'i tersinden çalıştırır (sistemdeki her kullanıcı için tek tek çağrılır) — ikinci bir
  yetki kural motoru yazılmadı (ADR-004, T2). V0 ölçeğinde (birkaç düzine kullanıcı) performans önemsiz.
- **`department_repo.all_exist()`** — `projects.py`'nin özel `_check_department_ids`'i artık bu paylaşılan
  fonksiyonu çağırıyor, `users.py` da aynısını kullanıyor (T4, kopyala-yapıştır önlendi; `projects.py`'nin
  davranışı/mesajı değişmedi, mevcut testler etkilenmedi).
- **Frontend:** `/yonetim/kullanicilar` (`AdminUsersPage` + `UserForm`, `ProjectsTab`/`ProjectForm` deseninin
  birebir eşdeğeri), `/yonetim/denetim-kaydi` (`AdminAuditLogPage`: filtre formu — departman/proje/soru
  türü/tarih aralığı/yalnızca-hatalı — + sayfalanmış tablo + satır tıklayınca tam detay). `RequireAdmin` guard'ı
  (`DepartmentPage`'in bilinmeyen-slug davranışıyla tutarlı: sessiz `Navigate to="/"`, ayrı bir 403 sayfası
  yok). `Layout`'a yalnızca admin'e görünen "Yönetim" linki. Belge detay paneline (`DocumentDetailPanel`) admin
  için iki yeni bölüm: `DocumentVisibilityCard` (salt-okunur kullanıcı listesi) ve
  `DocumentMetadataEditForm` (diff tabanlı — yalnızca değiştirilen alanlar `PATCH`'e gönderilir).

## 3. Değişen dosyalar
`git diff --stat` (bu rapor commit'iyle, önceki commit'e göre): 30 dosya, +1718/-32. Backend: `api/users.py`
(yeni), `schemas/user.py` (yeni), `api/documents.py` (+108, iki yeni endpoint + paylaşılan yardımcı),
`services/authorization.py` (+29, `SingleDocumentIdsProvider`), `repositories/user_repo.py` (+32),
`repositories/department_repo.py` (+9), `models/user.py` (+6), `api/projects.py` (-3, refactor). Testler:
`tests/test_users.py` (yeni, 12 test), `tests/test_documents.py` (+177, 13 yeni test). Frontend: 2 yeni sayfa,
4 yeni bileşen, 2 yeni API client dosyası, `types.ts`/`strings.ts`/`format.ts` ekleri, `router.tsx`/`Layout.tsx`
güncellemeleri. Migration yok (hiçbir yeni tablo/kolon).

## 4. Testler
- Backend: 383 test, tamamı yeşil (`make test`, ~210 sn) — 25 yeni test (`test_users.py` 12, `test_documents.py`
  13 ek) dahil. ocr-worker: 9 test, değişmedi.
- `make lint` (backend `ruff check`/`ruff format --check`/`mypy`, ocr-worker `ruff`, frontend `eslint`/`tsc`,
  prompt-doküman eşitliği, ledger/document/excel validasyonları): tamamı yeşil.
- Frontend'de ayrı bir UI test dosyası açılmadı (CLAUDE.md: Playwright/UI testleri V0 dışı, mevcut
  `ProjectForm`/`ProjectsTab` da testsiz) — `tsc`/`eslint` yeterli kabul edildi.
- **Manuel doğrulama (tarayıcı yerine curl + gerçek dev veritabanı):** bu ortamda bir tarayıcı aracı
  bulunmadığından uçtan uca UI tıklama testi yapılamadı — bunun yerine gerçek dev backend'i yeniden
  build/restart edilip gerçek seed verisiyle canlı curl testleri koşuldu: admin girişi → `/api/users` liste +
  oluşturma (201, `password`/`password_hash` response'ta yok) → gerçek bir seed belgesinin
  `/visibility`'si (admin + `yonetim` (management) + `enerji` departmanındaki `enerji` kullanıcısı listede,
  `finans`/`hukuk` kullanıcıları listede değil — beklenen departman/rol kuralına birebir uyuyor) →
  `PATCH /api/documents/{id}` ile `tags` güncellemesi (200, değişiklik yansıdı). Test sırasında oluşturulan
  geçici kullanıcı ve değiştirilen `tags` alanı test sonunda geri alındı/silindi (dev seed verisi kirletilmedi).
  Frontend bundle'ı da `make build-frontend` ile derlendi (vite build hatasız, 118 modül) ve Caddy üzerinden
  200 ile serviste doğrulandı; sayfaların gerçek tarayıcıda tıklanarak denenmesi yapılmadı — bu, raporun
  açıkça belirttiği bir sınırlamadır.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Manuel metadata düzenlemede 12 alan (9 + title/effective_date/expiration_date) uygulandı, plandaki "11 alan" sayımı değil | SORU 1'in alan listesi ("9 AI-önerisi + title/effective_date/expiration_date") açık ve net; "(11 alan)" ibaresi aritmetik hata (9+3=12) — listeye sadık kalındı, sayıya değil | Kapsam SORU 1'in niyetine tam uyuyor; sayı etiketindeki yazım hatası önemsiz |
| `department_repo.all_exist()` paylaşılan fonksiyon, `projects.py`'nin mevcut mesaj/404 davranışı korunarak | Kopyala-yapıştır önleme (T4) mevcut testleri bozmadan | `test_projects.py` değişmeden yeşil kaldı |
| "Kim görebilir" ikinci bir yetki motoru yazmadı, `SingleDocumentIdsProvider` ile mevcut `allowed_document_ids`'i tersinden kullandı | ADR-004: tek gate kuralı | Yeni bir yerde üç seviyeli (admin/management/employee) kural tekrarlanmadı |
| Frontend manuel test tarayıcıda değil curl + gerçek dev DB ile yapıldı | Bu ortamda tarayıcı aracı yok | Backend entegrasyonu ve derleme doğrulandı; UI'nin görsel/etkileşimsel doğruluğu doğrulanmadı — Naci ilk fırsatta tarayıcıda gözden geçirmeli |

## 6. Açık sorular (Naci cevaplamalı)
- Yok — SORU 1-4'ün hepsi plan onayında cevaplandı ve uygulandı.

## 7. Riskler / sonraki phase için notlar
- Frontend admin sayfaları tarayıcıda henüz elle denenmedi (bkz. §4) — Phase 5.3/5.4'e geçmeden önce veya ilk
  kullanımda Naci'nin bir kez gözden geçirmesi önerilir (özellikle `AdminAuditLogPage`'in tarih filtreleri ve
  `UserForm`'un kendi-hesabını-düzenleme dalı).
- `GET /api/documents/{id}/visibility`, sistemdeki her kullanıcı için `allowed_document_ids()`'i ayrı ayrı
  çağırıyor (V0 ölçeğinde önemsiz — birkaç düzine kullanıcı); kullanıcı sayısı büyürse (yüzlerce) bu N+1
  desenin SQL tabanlı bir sorguya çevrilmesi gerekebilir — şimdilik YAGNI.
- Departman ağacının kendisi (isim/parent) hâlâ seed-only; bu bilinçli bir kapsam dışı bırakma (Phase 1.2
  kararı, SORU 4'te yeniden onaylandı), gelecekte gerçek bir ihtiyaç çıkarsa ayrı bir faz gerekir.

## 8. Doğruladığım üçüncü taraf davranışları
- Yok — bu faz yalnızca mevcut FastAPI/SQLAlchemy/React/TanStack Query desenlerini genişletti, yeni bir
  üçüncü taraf API/kütüphane davranışına dayanmadı.

## 9. Kaynak kullanımı
- LLM çağrısı yok (bu faz LLM'e dokunmadı).
- Docker build: backend image yeniden build edildi (kod değişikliği), frontend `vite build` ~0,9 sn (118
  modül, 301 KB JS gzip 93 KB) → caddy imajına gömüldü.
- Disk: yeni dosyalar küçük (toplam ~40 KB kaynak kodu).
