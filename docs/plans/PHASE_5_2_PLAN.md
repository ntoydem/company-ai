# Phase 5.2 — Admin panel: Implementation Plan

## Bağlam ve tespitler

Phase 5.1b (`phase-5-1b`) kapandı; ADIM 5'in ikinci fazı başlıyor. `docs/PHASES.md`'deki kapsam: **kullanıcı ekle/disable/rol, departman izinleri, proje CRUD, metadata düzenleme, "bu belgeyi kim görebilir", audit log (filtre)**; kabul kriterleri: admin her işlemi UI'dan yapabilir, employee admin endpoint'lerinde 403 alır, audit'te gizli veri sızmaz. Aynı kapsam `docs/SPEC_06_operasyon_guvenlik_kalite.md` §2'de birebir tekrarlanıyor ("Phase 14" olarak anılmış — eski faz numaralandırması, bugünkü 5.2'ye karşılık geliyor).

Okunanlar: `docs/PHASES.md` (5.1/5.1b/5.2 bağlamı), `docs/SPEC_02_dokuman_metadata_yetki_ux.md` (tamamı), `docs/SPEC_06_operasyon_guvenlik_kalite.md` §1/§2 (tamamı), `docs/ARCHITECTURE.md` ADR-003/004/016, `docs/DOMAIN_MODEL.md` §3-5; kod: `app/models/user.py`, `app/models/project.py`, `app/models/document.py`, `app/api/{auth,projects,departments,documents,audit_log,deps}.py`, `app/services/authorization.py`, `app/repositories/{user,project,department,document}_repo.py`, `app/schemas/{auth,project,document}.py`, `frontend/src/**` (router, auth, api client, sayfalar, `ProjectForm`/`ProjectsTab`, `DocumentDetailPanel`, `MetadataSuggestionPanel`, `Layout`, `visibility.ts`).

Planı şekillendiren tespitler — **her kapsam kalemi için mevcut durum**:

| # | Kapsam kalemi | Durum |
|---|---|---|
| 1 | Kullanıcı ekle/disable/rol | **Hiç yok.** `user_repo.py`'de yalnızca `get_by_username`/`get_by_id`/`create` var; `list_all`/`update` yok. Hiçbir `/api/users*` endpoint'i yok (`router.py`'de kayıtlı değil). Frontend'de hiçbir admin/kullanıcı-yönetimi sayfası yok. |
| 2 | Departman izinleri | **Hiç yok** (kullanıcı-departman ataması anlamında). `user_departments` tablosu ve `User.departments` ilişkisi var (Phase 1.2) ama yalnızca seed script'i (`demo_departments_seed.py`) doldurabiliyor; hiçbir endpoint bir kullanıcının departman üyeliğini okuyup değiştiremiyor. Departman **CRUD**'u (ağaç düzenleme) T7/ADR-004 Phase 1.2 notuyla bilinçli olarak V0 dışı bırakılmış (`departments.py`: "No CRUD: departments are seed-only in V0") — bu karar bu fazda **yeniden açılmıyor**; "departman izinleri" burada yalnızca kullanıcı↔departman üyeliği atamasını kapsıyor (SORU 4). |
| 3 | Proje CRUD | **Tamamen bitmiş** (Phase 1.2 backend, Phase 3.3 frontend). `POST/PATCH /api/projects` `require_admin` ile korunuyor, `ProjectForm`/`ProjectsTab` admin'e create/edit UI'ı zaten sunuyor (departman sekmesi altında). Bu fazda **ek iş gerekmiyor** — mevcut UI zaten "admin her işlemi UI'dan yapar" kriterini karşılıyor. |
| 4 | Metadata düzenleme | **Kısmen.** AI öneri kabul/düzenle/reddet akışı var (`POST .../suggest-metadata`, `.../metadata-suggestion/apply`, `.../reject`, hepsi `require_admin`) ama **yalnızca bir öneri satırı varsa çalışıyor** (`SUGGESTION_NOT_FOUND_MESSAGE`). Öneri hiç üretilmemiş/reddedilmiş bir belgede admin'in metadata'yı elle düzeltecek hiçbir yolu yok. `document_repo.apply_partial_update` zaten var ve alan-bazlı kısmi güncellemeyi destekliyor (öneri-apply akışı bunu kullanıyor) — genel bir `PATCH /api/documents/{id}` bu fonksiyonu doğrudan çağırabilir, yeni bir depolama mantığı gerekmez. |
| 5 | "Bu belgeyi kim görebilir" | **Hiç yok.** Ne bir endpoint ne de bir UI parçası var. `allowed_document_ids(user, scope, provider) -> set[UUID]` (ADR-004) yönü **kullanıcı → belgeler**; burada tersi (**belge → kullanıcılar**) gerekiyor. |
| 6 | Audit log (filtre) | **Backend tamamen bitmiş** (Phase 3.4/4.3): `GET /api/audit-log` zaten `user_id/department/project_id/query_type/from_ts/to_ts/has_error` filtreleri + `limit/offset` sayfalama ile çalışıyor, `require_admin`, `answer`/`sources` liste görünümünde yok (yalnızca detay endpoint'inde) — ADR-016 bunu doğruluyor: *"the UI on top is Phase 5.2"*. **Yalnızca frontend eksik.** |

**T1 — `require_admin` zaten var ve tam olgun.** `app/api/deps.py:38`, `projects.py`/`documents.py`/`audit_log.py` üçü de kullanıyor. Yeni endpoint'ler aynı dependency'yi tekrar kullanır, yeni bir yetki mekanizması icat edilmiyor.

**T2 — "Belge → kullanıcılar" sorgusu, `allowed_document_ids`'i yeniden yazmadan, onu tersinden besleyerek çözülebilir.** `DocumentIdsProvider` protokolü (ADR-004) iki metotlu bir arayüz; `SqlDocumentIdsProvider` (kullanıcı → tüm belgeler) yerine tek bir belgeyi saran bir `SingleDocumentIdsProvider(document)` yazıp, sistemdeki her aktif kullanıcı için `allowed_document_ids(user, AuthorizationScope(), SingleDocumentIdsProvider(document))` çağırmak, üç seviyeli yetki mantığını (admin/management/employee) **tekrarlamadan** yeniden kullanır — CLAUDE.md'nin "Authorization tek fonksiyondan geçer" kuralına en sadık çözüm budur; ayrı bir "kim görebilir" kural motoru yazmak riskli bir kopya olurdu.

**T3 — `User.departments` ilişkisi `Project.departments` ile birebir aynı desende (`secondary="user_departments"` / `secondary="project_departments"`).** `project_repo.update()`'un `department_ids` senkronizasyonu (`project.departments = department_repo.get_many_by_ids(...)`) satır satır `user_repo`'ya taşınabilir; yeni bir ilişki yönetim deseni icat edilmiyor.

**T4 — Departman id doğrulaması (`_check_department_ids`) şu an yalnızca `projects.py`'de private bir fonksiyon.** Kullanıcı oluşturma/güncellemede de aynı doğrulama gerekiyor; kopyala-yapıştır yerine bu `department_repo.py`'ye taşınıp iki router'dan da çağrılacak (CLAUDE.md: "kopyala-yapıştır istenmeyen").

**T5 — Manuel metadata düzenleme, versiyon zincirine dokunmamalı.** `MetadataSuggestionApplyRequest`'in kapsadığı 9 alan (department, subdepartment, project_code, document_type, counterparty, document_date, status, confidentiality, tags) zaten "AI'nin tahmin edebileceği, zincir bütünlüğünü bozmayan" alanlar olarak seçilmiş. `supersedes_document_id`/`superseded_by_document_id`/`version`/`related_document_ids` upload sırasında `mark_superseded` ile birlikte, sıkı bir "predecessor görünür mü / zaten superseded mi" kontrolüyle yazılıyor (`documents.py:142-156`); bunları elle-düzenleme endpoint'ine açmak bu kontrolleri bypass eder ve zinciri bozabilir (ADR-012 "old ≠ wrong" modelinin dayandığı temel). **Öneri: manuel düzenleme aynı 9 alan + `title` + `effective_date` + `expiration_date`'i kapsasın, zincir alanlarını kapsamasın** (SORU 1).

**T6 — Kendi kendini kilitleme riski.** Admin, kendi hesabının `role`'ünü düşürür veya `is_active=false` yaparsa ve sistemde başka aktif admin yoksa, kimse admin endpoint'lerine erişemez hale gelir (V0'da şifre sıfırlama/kurtarma akışı yok). **Öneri: `PATCH /api/users/{id}` kendi hesabı için `role != admin` veya `is_active=false` içeren bir güncellemeyi 409 ile reddetsin** (SORU 3).

**T7 — Şifre değişikliği kapsamda değil (spec'te yok).** SPEC_06 §2 ve PHASES.md kapsam metni yalnızca "kullanıcı ekle/disable/rol" diyor; şifre sıfırlama hiçbir yerde geçmiyor. **Öneri: bu fazda dahil edilmesin** — bir sonraki ihtiyaç doğduğunda ayrı, dar bir ek olarak yapılsın (SORU 2, ama varsayılan hayır).

**T8 — Migration gerekmiyor.** Hiçbir yeni tablo/kolon yok; `user_departments`, `departments`, `projects`, `documents`, `audit_log` zaten var ve yeterli. `User` modeline yalnızca `Project.department_ids` ile simetrik, DB'siz bir `@property department_ids` eklenir (mevcut `department_slugs` property'sinin yanına).

---

## 1. Backend — Kullanıcı yönetimi (kapsam 1+2)

### `app/repositories/user_repo.py` — ekleme
```python
def list_all(session: Session) -> list[User]:
    return list(session.scalars(select(User).order_by(User.username)).all())

def update(
    session: Session, user: User, *,
    display_name: str | None = None,
    role: UserRole | None = None,
    is_active: bool | None = None,
    password_hash: str | None = None,
    department_ids: Iterable[uuid.UUID] | None = None,
) -> User:
    ...  # project_repo.update ile birebir aynı desen (T3)
```

### `app/repositories/department_repo.py` — ekleme (T4)
```python
def assert_all_exist(session: Session, ids: Iterable[uuid.UUID]) -> None:
    """404 semantics yok burada — çağıran router kendi mesajıyla fırlatır; bu yalnızca
    'kaç tanesi bulundu' bilgisini döner."""
```
(Ya da doğrudan `get_many_by_ids` üzerine ince bir `HTTPException` sarmalayıcısı — uygulama sırasında netleşecek küçük bir teknik detay, raporda listelenecek.)

### `app/models/user.py` — ekleme
```python
@property
def department_ids(self) -> list[uuid.UUID]:
    """`ProjectResponse.department_ids` ile simetrik — admin formunun departman
    checkbox'larını önceden işaretlemesi için (Project.department_ids, project.py:38)."""
    return [department.id for department in self.departments]
```

### `app/schemas/user.py` (yeni)
```python
class UserCreateRequest(BaseModel):
    username: str
    password: str
    display_name: str
    role: UserRole = UserRole.employee
    department_ids: list[uuid.UUID] = Field(default_factory=list)

class UserUpdateRequest(BaseModel):
    display_name: str | None = None
    role: UserRole | None = None
    is_active: bool | None = None
    department_ids: list[uuid.UUID] | None = None

class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: uuid.UUID
    username: str
    display_name: str
    role: UserRole
    is_active: bool
    department_ids: list[uuid.UUID]
    department_slugs: list[str]
```
`password_hash` şemada yok (`CurrentUserResponse` ile aynı disiplin — sızamaz). `username` `UserUpdateRequest`'te **yok** — `ProjectForm`'daki `code` gibi oluşturma sonrası immutable (kimlik alanı).

### `app/api/users.py` (yeni), `prefix="/api/users"`, hepsi `require_admin`
| Endpoint | Davranış |
|---|---|
| `GET ""` | Tüm kullanıcılar (aktif + pasif), `list_all` |
| `POST ""` | 201; username unique değilse 409 (`USERNAME_EXISTS_MESSAGE`, login'deki enumeration-koruması mesajından **farklı** — burada admin zaten kimin var olduğunu bilme yetkisine sahip, gizlemeye gerek yok); `department_ids` doğrulanır (404 `DEPARTMENT_NOT_FOUND_MESSAGE`, `projects.py`'deki mesajla aynı metin) |
| `PATCH "/{user_id}"` | 404 yoksa; **T6**: `user_id == current_user.id` ve (`role is not None and role != admin` veya `is_active is False`) → 409 `CANNOT_DEMOTE_OR_DISABLE_SELF_MESSAGE`; `department_ids` verilmişse doğrulanır |

`router.py`'ye `router.include_router(users.router)` eklenir.

## 2. Backend — Metadata düzenleme (kapsam 4)

`app/schemas/document.py`'ye `DocumentMetadataEditRequest` (T5'teki 11 alan, hepsi `Optional`, `model_fields_set` ile "yalnızca verilenler yazılır" — `apply_metadata_suggestion`'ın zaten kullandığı desenin birebir aynısı). `documents.py`'ye:

```python
@router.patch("/{document_id}", response_model=DocumentDetailResponse)
def edit_document_metadata(
    document_id: uuid.UUID, body: DocumentMetadataEditRequest,
    current_user: Annotated[User, Depends(require_admin)], ...
) -> DocumentDetailResponse:
    """Öneri akışından bağımsız, doğrudan admin düzenlemesi. Aynı department/project_code
    doğrulaması `apply_metadata_suggestion` ile paylaşılır (ikisi de aynı helper'ı çağırır,
    T4 deseni)."""
```
`_get_authorized_document` ile aynı 404 (belge admin'e de görünmüyorsa — olmaz ama tutarlılık için) kontrolünden geçer, sonra `document_repo.apply_partial_update`.

## 3. Backend — "Bu belgeyi kim görebilir" (kapsam 5, T2)

`app/services/authorization.py`'ye (mevcut dosyanın içine, yeni servis dosyası açmadan — ADR-004'ün "tek gate" ruhuna uygun, bu da aynı dosyanın bir parçası):
```python
class SingleDocumentIdsProvider:
    """`DocumentIdsProvider` protokolünü tek bir belgeye sararak `allowed_document_ids`'i
    'belge → kullanıcılar' yönünde tersine kullanmayı sağlar (T2) — kural motoru
    tekrarlanmaz, yalnızca girdi kümesi değişir."""
    def __init__(self, document: Document) -> None: ...
    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]: ...
    def list_document_ids_for_departments(self, *, department_slugs, confidentiality_levels) -> Iterable[UUID]: ...
```

`app/api/documents.py`'ye:
```python
@router.get("/{document_id}/visibility", response_model=DocumentVisibilityResponse)
def get_document_visibility(
    document_id: uuid.UUID, current_user: Annotated[User, Depends(require_admin)], ...
) -> DocumentVisibilityResponse:
    document = _get_authorized_document(session, current_user, document_id)  # admin zaten her şeyi görür
    provider = SingleDocumentIdsProvider(document)
    visible_users = [
        u for u in user_repo.list_all(session)
        if document.id in allowed_document_ids(u, AuthorizationScope(), provider)
    ]
    return DocumentVisibilityResponse(
        document_id=document.id, department=document.department,
        confidentiality=document.confidentiality,
        users=[VisibilityUser.model_validate(u) for u in visible_users],
    )
```
V0 ölçeğinde (birkaç düzine kullanıcı) her kullanıcı için tek belgelik bir küme hesaplamak önemsiz maliyetli — ayrı bir SQL sorgusu optimizasyonu gerekmez.

## 4. Frontend — Admin Panel

### Route + guard
`router.tsx`'e `/admin` altında iki alt rota (`/admin/kullanicilar`, `/admin/denetim-kaydi`); `Layout.tsx`'teki nav'a `user.role === "admin"` ise bir "Yönetim" linki. Guard: mevcut `RequireAuth`'un yanına, `visibility.ts`'teki `canSeeDepartment` desenine benzer saf bir fonksiyon (`isAdmin(user)`) + admin olmayan biri `/admin/*`'e giderse `Navigate to="/"` (var olan `DepartmentPage`'in "yanlış slug" davranışıyla tutarlı — yeni bir 403 sayfası icat edilmiyor, sessiz yönlendirme).

### `AdminUsersPage`
`ProjectsTab`/`ProjectForm` çiftinin birebir eşdeğeri: tablo (kullanıcı adı, ad, rol, aktif/pasif rozet, departmanlar) + "Yeni kullanıcı" formu (username, şifre, ad, rol select, departman checkbox'ları — `ProjectForm`'daki chip deseni) + her satırda "Düzenle" (rol/aktiflik/departman) — **şifre alanı yalnızca oluşturmada**, düzenlemede yok (T7).

### `AdminAuditLogPage`
Filtre formu (departman select, proje select, `query_type` select, tarih aralığı, `has_error` checkbox) + sayfalanmış tablo (`DocumentTable`'daki `table-wrap`/`table` deseniyle aynı CSS) + satır tıklayınca detay paneli (`DocumentDetailPanel`'deki kart/kapat deseniyle aynı: soru, cevap, kaynaklar, model, token, maliyet, hata).

### `DocumentDetailPanel` genişletmesi
- **Kim görebilir:** yalnızca `isAdmin` iken görünen küçük bir kart (`GET .../visibility`), kullanıcı listesini rol etiketiyle gösterir (`ROLE_LABELS`, zaten `Layout.tsx`'te kullanılıyor).
- **Metadata düzenle:** `MetadataSuggestionPanel`'in yanına (öneri yoksa/reddedilmişse de her zaman görünen) ayrı bir küçük form — aynı alan render fonksiyonlarının (select'ler, departman/proje dropdown'ları) `MetadataSuggestionPanel.tsx`'ten çıkarılıp paylaşılan bir yardımcıya taşınması gerekebilir (kopyala-yapıştır'dan kaçınmak için, T5) — uygulama sırasında netleşecek küçük bir dosya-bölme kararı.

`frontend/src/api/users.ts` (yeni, `projects.ts` deseniyle birebir), `frontend/src/api/audit-log.ts` (yeni), `frontend/src/api/documents.ts`'e `useVisibility`/`editMetadata` eklemeleri, `frontend/src/api/types.ts`'e ilgili tipler, `lib/strings.ts`'e `S.admin.*` bloğu, `lib/format.ts`'e gerekirse yeni etiket sabitleri.

## 5. Testler

| Kabul kriteri | Test dosyası/örnek |
|---|---|
| Admin kullanıcı oluşturur/düzenler, employee 403 | `test_users.py`: create/patch 201/200, employee → 403, tekrar username → 409, bilinmeyen departman id → 404 |
| Admin kendi rolünü/aktifliğini düşüremez | `test_users.py::test_admin_cannot_demote_or_disable_self` |
| Departman ataması `/api/auth/me`'ye yansır | `test_users.py` + mevcut `test_auth.py`'ye bir satır (yeni atanan departman `department_slugs`'ta görünür) |
| Metadata manuel düzenlenir, employee 403, versiyon alanları endpoint'te yok | `test_documents.py` (yoksa oluşturulur) veya mevcut belge testine ekleme |
| "Kim görebilir" — employee finans belgesini görmüyorsa listede yok | `test_documents.py::test_visibility_excludes_employee_without_department_access` (authorization testlerinin department/confidentiality fikstürlerini yeniden kullanır) |
| Audit log filtreleri (zaten yeşil, regresyon yok) | mevcut `test_audit_log.py` değişmeden geçmeli |
| Employee admin endpoint'lerinde 403 (genel) | her yeni router için en az bir 403 testi (CLAUDE.md: "her endpoint için en az bir test") |

Frontend: mevcut proje testsiz-UI kültürüne uyarak (CLAUDE.md: Playwright/UI testleri V0 dışı) yeni sayfalar için ayrı bir test dosyası açılmaz; `tsc`/`eslint` (`make lint`) yeşil olması yeterli — mevcut desenle tutarlı (`ProjectForm`/`ProjectsTab`'ın da UI testi yok).

## 6. Doküman güncellemeleri
- `docs/ARCHITECTURE.md` ADR-004'e bir **Phase 5.2 concretization** paragrafı: `SingleDocumentIdsProvider` ile "kim görebilir" tersine kullanımı (T2).
- ADR-016'ya **Phase 5.2 concretization**: audit log admin UI'ı artık var, filtre alanları frontend'de birebir backend'deki `list_filtered` parametreleriyle eşleşiyor.
- `README.md`: "Giriş" bölümünün yanına kısa bir "Yönetim paneli (Phase 5.2)" paragrafı (hangi rol neyi yapabilir).
- `docs/SPEC_06_operasyon_guvenlik_kalite.md` değişmez (zaten §2 bu fazı doğru tarif ediyor).

---

## SORU (Naci cevaplamalı)

1. **Manuel metadata düzenleme hangi alanları kapsasın?** Önerim (T5): AI öneri akışının kapsadığı 9 alan + `title` + `effective_date` + `expiration_date` (11 alan); `version`/`supersedes_document_id`/`superseded_by_document_id`/`related_document_ids` **dışarıda** (zincir bütünlüğü, ADR-012). Onaylıyor musun, yoksa zincir alanlarından biri (örn. yalnızca `effective_date`'i düzeltmek yerine yanlış girilmiş bir `supersedes` bağını da düzeltebilmek) senin için önemli mi?
2. **Şifre sıfırlama admin panelinde olsun mu?** Spec'te yok (T7); önerim **hayır**, bu fazda dahil edilmesin (kapsamı "kullanıcı ekle/disable/rol" ile sınırlı tutalım). Katılıyor musun, yoksa şimdiden eklensin mi?
3. **Admin kendi hesabını düşüremesin/disable edemesin kuralı (T6) onaylı mı?** Yoksa bu bir ürün kısıtlaması değil, "dikkatli ol" seviyesinde mi kalsın (yani serbest bırakılsın)?
4. **"Departman izinleri" = yalnızca kullanıcı↔departman üyeliği ataması, departman ağacının kendisi (isim/parent) hâlâ seed-only mi?** Phase 1.2'nin bu kararını (ADR-004 concretization, `departments.py` yorumu) bu fazda yeniden açmıyorum — onaylıyor musun?

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- Yeni servis dosyası açılmıyor: "kim görebilir" mantığı `app/services/authorization.py`'nin içinde (tek gate ruhu).
- `department_repo`'ya `_check_department_ids` benzeri bir doğrulama taşınıyor, `projects.py` da ona geçiyor (kopyala-yapıştır önleme, T4) — `projects.py`'nin küçük bir refactor'ü, davranışı değişmiyor (mevcut testler kırılmamalı).
- `username` oluşturma sonrası immutable (`code` deseniyle simetrik).
- `PATCH /api/users/{id}` username'i asla kabul etmiyor (şema seviyesinde yok, ayrıca kontrol gerekmiyor).
- Yeni migration yok (T8).
- Audit log listesi ve detayının frontend'i, mevcut backend endpoint'lerini **hiç değiştirmeden** tüketiyor.

## Uygulama sırası

1. `department_repo.py` doğrulama yardımcı fonksiyonu + `projects.py`'nin ona geçmesi (mevcut testler yeşil kalmalı).
2. `user_repo.list_all/update`, `User.department_ids` property.
3. `app/schemas/user.py`, `app/api/users.py`, `router.py` kaydı, `test_users.py`.
4. `app/schemas/document.py::DocumentMetadataEditRequest`, `documents.py::edit_document_metadata`, testi.
5. `SingleDocumentIdsProvider`, `documents.py::get_document_visibility`, `app/schemas/document.py::DocumentVisibilityResponse`, testi.
6. `make test`/`make lint` yeşil — backend tarafı burada kapanır.
7. Frontend: `api/users.ts`, `api/audit-log.ts`, `api/types.ts`/`lib/strings.ts`/`lib/format.ts` ekleri.
8. `AdminUsersPage`, `AdminAuditLogPage`, `router.tsx`/`Layout.tsx` admin nav + guard.
9. `DocumentDetailPanel`'e "kim görebilir" + "metadata düzenle" bölümleri.
10. `make lint` (frontend `tsc`+`eslint`) yeşil; manuel tarayıcı testi (admin + employee ile).
11. ARCHITECTURE.md/README güncellemeleri → rapor → `docs/PHASES.md` → commit + tag `phase-5-2` + push.

## Kritik dosyalar

- `backend/app/repositories/user_repo.py`, `backend/app/repositories/department_repo.py`
- `backend/app/api/users.py`, `backend/app/schemas/user.py`
- `backend/app/api/documents.py`, `backend/app/schemas/document.py`, `backend/app/services/authorization.py`
- `backend/tests/test_users.py`, `backend/tests/test_documents.py`
- `frontend/src/pages/admin/AdminUsersPage.tsx`, `frontend/src/pages/admin/AdminAuditLogPage.tsx`
- `frontend/src/api/users.ts`, `frontend/src/api/audit-log.ts`
- `frontend/src/components/DocumentDetailPanel.tsx`, `frontend/src/router.tsx`, `frontend/src/components/Layout.tsx`
