# Phase 1.2 — Departman, rol, proje, yetki: Implementation Plan

## Bağlam ve tespitler

Phase 1.1 (`phase-1-1`) auth'u kapattı; ADIM 1'in ikinci ve son fazı bu. Kapsam `docs/PHASES.md`'den: `departments` (ağaç), `user_departments`, `projects` (admin CRUD, aktif/pasif, çoklu departman), `allowed_document_ids()`'in SPEC_02 §5 mantığıyla dolması; belge listesi/indirme/`/api/ask` hepsi bu fonksiyondan geçer.

Okunanlar: `docs/PHASES.md`, `docs/DOMAIN_MODEL.md` (tamamı), `docs/SPEC_02_dokuman_metadata_yetki_ux.md` §1-9, `docs/ARCHITECTURE.md` ADR-004/007/020/021, `docs/plans/PHASE_1_1_PLAN.md`; kod: `app/models/{user,document}.py`, `app/models/__init__.py`, `app/models/base.py`, `app/services/authorization.py`, `app/schemas/authorization.py`, `app/repositories/{document_repo,user_repo}.py`, `app/api/{documents,ask,deps,router}.py`, `app/services/{ask,retrieval,document_store,demo_users_seed,admin_seed}.py`, `app/schemas/{document,ask,retrieval}.py`, `app/core/{config,errors}.py`, `app/cli.py`, `backend/entrypoint.sh`, `alembic/versions/{0001,0002}*.py`, `tests/{test_authorization,test_documents,test_ask,test_document_repo,conftest}.py`.

Planı şekillendiren tespitler:

- **T1 — Sözleşme donmuş, mantık `DocumentIdsProvider`'a genişletilerek eklenir.** `allowed_document_ids(user, scope, document_ids_provider) -> set[UUID]` (ADR-004) imzası değişmiyor. Rol/departman mantığı, `Protocol`'e yeni bir metod eklenerek uygulanacak — `AuthorizationScope`'a dokunulmuyor (o yalnızca "narrowing" için var, rol mantığı için değil).
- **T2 — `Document.department` FK almıyor; string/slug olarak kalıyor.** `tests/test_ask.py` (`department="finance"`, `department="legal"`) ve `tests/test_document_repo.py` (`department="finance"`) serbest string değerler kullanıyor, hiçbir `departments` satırına karşılık gelmiyor. Bu testler `admin_user` ile çalışıyor (admin her şeyi görür, departman kontrolüne hiç girmez) — bu yüzden `Document.department`'ı UUID FK'ya çevirmek hem tip kırılması hem de gereksiz risk. Karar: `Document.department: str | None` aynen kalır (FK yok), ama artık **gerçek departman `slug`'ı** taşıması beklenir (örn. `"finans"`, `"enerji_grubu"`); eski İngilizce testler bunu hiç görmez çünkü admin yolundan geçiyorlar. `Document.department`'ın docstring'indeki "which also adds the FK" cümlesi bu fazda **iptal ediliyor** — gerekçe doküman değişikliklerinde not edilecek.
- **T3 — `Document.project_id` FK alıyor (tip zaten uyumlu).** `Document.project_id: UUID | None` zaten var; `projects.id` de UUID. Tek risk: `tests/test_document_repo.py::test_list_document_ids_filters_by_project_id_at_sql_level` rastgele `uuid.uuid4()` kullanıyor, gerçek `Project` satırı olmadan — FK eklenince bu satır patlar. **Bu test güncellenecek** (gerçek `Project` satırı oluşturup onun id'sini kullanacak) — bilinçli, listelenmiş bir değişiklik. (Doğrulandı: mevcut test dosyası tam olarak bu satırı içeriyor.)
- **T4 — İndirme endpoint'i yok.** `app/api/` genelinde `grep -rn "download\|FileResponse\|get_file"` → yalnızca `ask_page.py`'nin statik HTML'i `FileResponse` kullanıyor; `documents.py`'de indirme rotası yok (doğrulandı, ikinci kez grep edildi). `DocumentStore.get_file(document_id, kind: Literal["original","ocr"]) -> Path` arayüzü hazır (`app/services/document_store.py`) ve dosya yoksa `FileNotFoundError` fırlatıyor, ama hiçbir API onu çağırmıyor. Kabul kriteri 1 ("indirme 403") için **yeni, minimal** `GET /api/documents/{id}/download` eklenmesi gerekiyor.
- **T5 — "audit'te retrieved boş" zaten karşılanabilir durumda, `audit_log` beklemeden.** `AskResponse.retrieved_document_ids: list[UUID]` (Phase 0.3'ten beri var) ve `app/services/ask.py`'nin `"ask completed"` log satırı zaten `retrieved_document_ids` alanını `extra`'ya yazıyor (doğrulandı: `app/services/ask.py` `AuthorizationScope`'u kendi kuruyor, `allowed_document_ids`'i çağırıyor, sonucu log'a ve response'a yazıyor — bu fazda `ask.py`'ye dokunulmuyor, yalnızca `allowed_document_ids`'in içi değişiyor). `audit_log` tablosu Phase 3.4'te geliyor (DOMAIN_MODEL §9) — bu fazda "audit" kanıtı bu ikisi (response alanı + structured log) olacak; yeni bir tablo açılmıyor. SORU 2'de teyit isteniyor.
- **T6 — Mevcut 404 deseni ile "indirme 403" arasında gerçek bir tutarsızlık var.** `get_document_status` ve upload'ın `supersedes_document_id` kontrolü, yetkisiz erişimde bilinçli olarak **404** dönüyor (var olan/yok arasındaki farkı gizlemek için). PHASES.md'nin kabul kriteri 1 metni açıkça **403** istiyor indirme için. Plan, spec metnine harfiyen uyup indirme'ye özel 403 uygular — bu mevcut 404 desenine bilinçli bir istisna, SORU 3'te teyit isteniyor.
- **T7 — `subdepartment` yetkilendirme birimi değil.** `Document` modelinde `department` ve `subdepartment` iki ayrı string kolon (DOMAIN_MODEL §1: "Department ──< Document (department, subdepartment)"). SPEC_02 §5 üyeliği yalnızca "departman" seviyesinde tanımlıyor (`user_departments`), alt departman üyeliğinden hiç bahsetmiyor. Karar: **üyelik/yetki her zaman üst-seviye `department` alanı üzerinden çalışır**; `subdepartment` (varsa) salt görüntüleme/filtre alanı, ayrı bir yetki kapısı değil. Bu, `enerji` kullanıcısının "energy/*" tanımını doğal olarak çözüyor: `enerji` yalnızca üst düğüm **"Enerji Grubu"**'na üye olur, 3 alt kart (Geliştirme/EPC-İnşaat/Bakım) otomatik kapsanır çünkü onların belgeleri de `department="enerji_grubu"` taşıyacak (alt kart yalnızca `subdepartment` alanında görünür).
- **T8 — Departman CRUD endpoint'i istenmiyor.** PHASES.md/SPEC_02 §6 yalnızca proje CRUD'unu admin işlemine bağlıyor; departmanlar için CRUD talebi yok. Departmanlar **yalnızca seed** ile oluşturulur (demo_users_seed.py deseniyle aynı). Tek istisna: admin'in proje oluştururken `department_ids` seçebilmesi için salt-okunur `GET /api/departments` eklenecek (aşağıda gerekçeli).
- **T9 — Rol tabanlı endpoint koruması hiç yok, yeni bir dependency gerekiyor.** `app/api/deps.py`'de bugün yalnızca `get_current_user` var; "yalnızca admin" gibi bir kapı yok. Yeni `require_admin` dependency'si `get_current_user`'ı sarıp 403 fırlatacak.
- **T10 — `management` kullanıcısı hiçbir departmana üye edilmiyor.** SPEC_02 §5: "management: tüm departmanlar, normal+restricted+board" — üyelikten bağımsız. `yonetim` demo hesabı `user_departments`'a hiç satır almaz; `allowed_document_ids` rolü admin/management için üyelik sorgusuna hiç bakmıyor zaten (aşağıda §3).
- **T11 — Mevcut `test_authorization.py`'nin 4 testi değişmeden geçer.** `_user()` varsayılan olarak `role=UserRole.admin` üretiyor → admin dalı hâlâ yalnızca `list_document_ids(scope)` çağırıyor, yeni metodu hiç görmüyor. `test_result_is_subset_of_provider_and_scope_is_forwarded` tek `employee` testi: transient (DB'ye hiç yazılmamış) bir `User` nesnesinde SQLAlchemy relationship koleksiyonu varsayılan olarak boş liste döner (`user.departments == []`, sorgu tetiklemeden) → yeni employee dalı "departman yok → boş küme" erken-dönüşüne girer, provider'ın yeni metodunu hiç çağırmaz, `seen_scopes == [scope]` iddiası hâlâ doğru kalır. Yani **bu dosyaya dokunulmadan mevcut 4 test yeşil kalıyor**; yeni testler eklenecek.
- **T12 — Log `extra` key çakışması (Phase 1.1'in T6'sı).** Yeni loglama çağrılarında (`demo_departments_seed.py`, `demo_projects_seed.py`, `require_admin`) `record.__dict__`'in rezerve ettiği isimlerden (`created`, `name`, `message`, ...) kaçınılacak — Phase 1.1'de gerçek bir bug buradan çıkmıştı.

---

## 1. Şema tasarımı — migration `0003_departments_projects.py`

`down_revision = "0002"`. Yeni enum: `project_stage` (`development|construction|operation`).

**`departments`**
| Kolon | Tip | Not |
|---|---|---|
| `id` | `uuid` PK | |
| `name` | `varchar(128)` NOT NULL | Görünen ad (Türkçe), örn. "Enerji Grubu" |
| `slug` | `varchar(64)` UNIQUE NOT NULL, indexed | Makine-okur kimlik, örn. `enerji_grubu` |
| `parent_id` | `uuid` NULL, FK→`departments.id` ON DELETE SET NULL | Ağaç; üst-seviye departmanlarda NULL |
| `created_at`/`updated_at` | timestamptz | `TimestampMixin` |

`is_active` **eklenmiyor** (bkz. Kendi kararlarım) — departman CRUD yok, kullanılmayacak kolon açmıyoruz.

**`user_departments`** (M2M)
| Kolon | Tip |
|---|---|
| `user_id` | `uuid` FK→`users.id` ON DELETE CASCADE, PK'nin parçası |
| `department_id` | `uuid` FK→`departments.id` ON DELETE CASCADE, PK'nin parçası |
| `created_at` | timestamptz, `server_default=now()` |

Composite PK `(user_id, department_id)`; ayrı index `ix_user_departments_department_id`.

**`projects`**
| Kolon | Tip | Not |
|---|---|---|
| `id` | `uuid` PK | |
| `name` | `varchar(255)` NOT NULL | |
| `code` | `varchar(32)` UNIQUE NOT NULL, indexed | `ANK_RES`, `IZM_RES` |
| `stage` | enum `project_stage` NOT NULL, default `development` | |
| `is_active` | `boolean` NOT NULL default `true` | |
| `created_at`/`updated_at` | timestamptz | |

**`project_departments`** (M2M) — `user_departments` ile birebir aynı desen (`project_id`, `department_id` composite PK, CASCADE).

**`documents` ALTER**: `project_id` kolonuna `fk_documents_project_id_projects` eklenir (`ON DELETE SET NULL`). `department` kolonuna **dokunulmaz** (T2).

`downgrade()`: FK'yi düşür → `project_departments` → `projects` (+ enum drop) → `user_departments` → `departments`.

## 2. Modeller

- `app/models/department.py`: `Department(TimestampMixin, Base)` — yukarıdaki kolonlar; parent/children ORM `relationship()` **eklenmiyor** (YAGNI — ağaç UI'ı Phase 3.3'te gerekirse eklenir, şimdi `parent_id` kolonu yeterli).
- `app/models/user_department.py`: `UserDepartment(Base)` — association tablosu, `User.departments`'ın `secondary` hedefi.
- `app/models/project.py`: `ProjectStage(enum.StrEnum)` + `Project(TimestampMixin, Base)`; `departments: Mapped[list["Department"]] = relationship(secondary="project_departments")`; `department_ids` computed property (`[d.id for d in self.departments]`) — `ProjectResponse.model_validate(project)` bunu attribute olarak okuyabilsin diye (mevcut `from_attributes=True` deseniyle tutarlı, ekstra dönüştürme kodu yazmadan).
- `app/models/project_department.py`: `ProjectDepartment(Base)` — `user_department.py` ile birebir aynı desen.
- `app/models/user.py`: `departments: Mapped[list["Department"]] = relationship("Department", secondary="user_departments")` eklenir.
- `app/models/document.py`: `project_id`'nin `mapped_column` tanımına `ForeignKey("projects.id", ondelete="SET NULL")` eklenir; sınıf docstring'i güncellenir ("`department` denormalize slug string olarak kalır, FK yok — bkz. Phase 1.2 planı T2; `project_id` artık FK'lı").
- `app/models/__init__.py`: `Department`, `UserDepartment`, `Project`, `ProjectStage`, `ProjectDepartment` eklenir, `__all__` güncellenir.

## 3. `allowed_document_ids()` gerçek mantığı

`app/services/authorization.py` — Protocol genişler, fonksiyon gövdesi rol dalına ayrılır, **imza değişmez**:

```python
class DocumentIdsProvider(Protocol):
    def list_document_ids(self, scope: AuthorizationScope) -> Iterable[UUID]: ...

    def list_document_ids_for_departments(
        self,
        *,
        department_slugs: Iterable[str] | None,   # None = tüm departmanlar (management)
        confidentiality_levels: Iterable[Confidentiality],
    ) -> Iterable[UUID]: ...


def allowed_document_ids(user, scope, document_ids_provider) -> set[UUID]:
    if not user.is_active:
        return set()
    scoped_ids = set(document_ids_provider.list_document_ids(scope))
    if not scoped_ids:
        return set()
    if user.role == UserRole.admin:
        return scoped_ids
    if user.role == UserRole.management:
        role_ids = set(document_ids_provider.list_document_ids_for_departments(
            department_slugs=None, confidentiality_levels=tuple(Confidentiality)))
        return scoped_ids & role_ids
    department_slugs = [d.slug for d in user.departments]      # employee
    if not department_slugs:
        return set()
    role_ids = set(document_ids_provider.list_document_ids_for_departments(
        department_slugs=department_slugs, confidentiality_levels=(Confidentiality.normal,)))
    return scoped_ids & role_ids
```

`scope` hâlâ yalnızca narrowing (`scoped_ids & role_ids` — kesişim, hiçbir zaman birleşim); "Scope only narrows, never grants" (ADR-004) korunuyor.

`app/repositories/document_repo.py::SqlDocumentIdsProvider` yeni metodu ekler (`Confidentiality` zaten dosyada import edilmiş durumda, yeni import gerekmiyor):
```python
def list_document_ids_for_departments(self, *, department_slugs, confidentiality_levels):
    stmt = select(Document.id).where(Document.confidentiality.in_(list(confidentiality_levels)))
    if department_slugs is not None:
        stmt = stmt.where(Document.department.in_(list(department_slugs)))
    return self._session.scalars(stmt).all()
```
Mevcut `list_document_ids` metoduna dokunulmuyor.

## 4. Repository/schema katmanı (yeni)

- `app/repositories/department_repo.py`: `create(session, *, name, slug, parent_id=None)`, `get_by_slug`, `list_all`, `get_many_by_ids`.
- `app/repositories/project_repo.py`: `create(session, *, name, code, stage, department_ids)`, `get`, `get_by_code`, `list_all`, `update(session, project, *, name=None, stage=None, is_active=None, department_ids=None)`. `department_ids` verildiğinde departmanlar `department_repo.get_many_by_ids` ile çekilip `project.departments`'a atanır (ORM ilişkisi üzerinden — ekstra ham SQL insert yok).
- `app/schemas/department.py`: `DepartmentResponse` (`id, name, slug, parent_id`, `from_attributes=True`).
- `app/schemas/project.py`: `ProjectCreateRequest` (`name, code, stage=development, department_ids: list[UUID]=[]`), `ProjectUpdateRequest` (hepsi opsiyonel: `name, stage, is_active, department_ids`), `ProjectResponse` (`id, name, code, stage, is_active, department_ids`).

## 5. Endpoint'ler

- `app/api/deps.py`'ye `require_admin`: `get_current_user`'ı sarar, `role != admin` ise 403 (`NOT_AUTHORIZED_MESSAGE`, yeni sabit `app/core/errors.py`'ye eklenir: `"Bu işlem için yetkiniz yok."`).
- `app/api/departments.py` (yeni): `GET /api/departments` — `Depends(get_current_user)` (herkes, salt okuma; departman adları gizli değil, admin'in proje formunda `department_ids` seçebilmesi için gerekli — bkz. Kendi kararlarım).
- `app/api/projects.py` (yeni), `prefix="/api/projects"`:
  - `GET ""` — `Depends(get_current_user)` (herkes okuyabilir; SPEC bunu kısıtlamıyor, çalışanların da proje/departman filtresi için proje listesine ihtiyacı var).
  - `POST ""` — `Depends(require_admin)`, 201; `code` çakışırsa 409 (`PROJECT_CODE_EXISTS_MESSAGE`); `department_ids` içinde bilinmeyen id varsa 404 (`DEPARTMENT_NOT_FOUND_MESSAGE`).
  - `PATCH "/{project_id}"` — `Depends(require_admin)`, kısmi güncelleme (aktif/pasif dahil); bilinmeyen `project_id` → 404.
- `router.py`'ye `departments` ve `projects` router'ları eklenir.
- `app/api/documents.py`'ye indirme:
```python
@router.get("/{document_id}/download")
def download_document(session, settings, current_user: Depends(get_current_user), document_id):
    allowed = allowed_document_ids(current_user, AuthorizationScope(), SqlDocumentIdsProvider(session))
    if document_id not in allowed:
        raise HTTPException(403, DOCUMENT_ACCESS_DENIED_MESSAGE)   # T6 — bilinçli 403 istisnası
    document = document_repo.get(session, document_id)
    if document is None:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE)
    try:
        path = LocalFileSystemStore(settings.documents_dir).get_file(document_id, kind="original")
    except FileNotFoundError:
        raise HTTPException(404, DOCUMENT_NOT_FOUND_MESSAGE) from None
    return FileResponse(path, filename=path.name)
```
`app/api/documents.py`'nin mevcut `list_documents`/`get_document_status`'una dokunulmuyor — `list_documents` zaten `allowed_document_ids` üzerinden geçtiği için rol mantığı otomatik devreye girer.

`/api/ask` ve `retrieve()` **hiç değişmiyor** (T5, doğrulandı) — `retrieve()`/`ask.py` zaten `allowed_document_ids`'i çağırıyor; boş küme → boş chunk → `_no_answer()` → `retrieved_document_ids=[]`.

## 6. Demo seed

- `app/services/demo_departments_seed.py` (yeni): 8 satır, üst-seviyeler önce (parent lookup sırası önemli):
```python
_DEPARTMENTS = (
    ("enerji_grubu", "Enerji Grubu", None),
    ("enerji_gelistirme", "Geliştirme", "enerji_grubu"),
    ("enerji_epc_insaat", "EPC-İnşaat", "enerji_grubu"),
    ("enerji_bakim", "Bakım", "enerji_grubu"),
    ("finans", "Finans", None),
    ("hukuk", "Hukuk", None),
    ("mali_isler", "Mali İşler", None),
    ("idari_isler", "İdari İşler", None),
)
def ensure_demo_departments(session, settings) -> list[DemoSeedResult]: ...

_DEMO_USER_DEPARTMENTS = {
    "finans": ("finans", "mali_isler"),
    "hukuk": ("hukuk",),
    "enerji": ("enerji_grubu",),
    # "yonetim": () — management üyelik gerektirmiyor (T10)
}
def ensure_demo_department_memberships(session, settings) -> list[DemoSeedResult]: ...
```
Var-ise-dokunma, `demo_users_seed.py` ile birebir desen.
- `app/services/demo_projects_seed.py` (yeni):
```python
_DEMO_PROJECTS = (
    ("ANK_RES", "Ankara RES", ProjectStage.operation, ("enerji_grubu",)),
    ("IZM_RES", "İzmir RES", ProjectStage.development, ("enerji_grubu",)),
)
def ensure_demo_projects(session, settings) -> list[DemoSeedResult]: ...
```
- `app/cli.py`: `seed-demo-departments` (departman + üyelik, tek komut) ve `seed-demo-projects` alt komutları.
- `entrypoint.sh`: `seed-demo-users`'dan sonra `seed-demo-departments`, ardından `seed-demo-projects` (departmanlar projelerden önce var olmalı).

## 7. Belge upload formu — kapsam dışı (bilinçli)

Upload endpoint'i `department`/`project_id`/`confidentiality` alanlarını **almaya devam etmiyor**. Gerekçe: SPEC_02 §4 "AI metadata önerisi" (departman/proje/gizlilik önerisi + kullanıcı kabul akışı) Phase 3.2'de geliyor; o faza kadar gerçek kullanıcı akışında bu alanları manuel doldurmak zaten spec'in tasarladığı yol değil. Bu fazda testler `Document` satırlarını doğrudan (session.add ile, mevcut `_document()` test yardımcıları gibi) oluşturup `department`/`confidentiality` atar — API'den değil. SORU 5'te teyit isteniyor.

## 8. Kabul kriteri → kanıt

| Kriter (PHASES.md) | Test | Kanıt |
|---|---|---|
| 1. `enerji` → finans belgesi listede yok | `tests/test_documents.py::test_employee_list_excludes_other_department_documents` | `enerji` fixture + `department="finans"` belge → `GET /api/documents` listesinde yok |
| 1. indirme 403 | `tests/test_documents.py::test_employee_download_other_department_document_returns_403` | `GET /{id}/download` → 403 |
| 1. `/api/ask` "bilgi bulamadım" + retrieved boş | `tests/test_ask.py::test_employee_ask_outside_department_returns_no_answer_with_empty_retrieved` | `body["answered"] is False`, `body["retrieved_document_ids"] == []`; `caplog` ile `"ask completed"` kaydının `retrieved_document_ids=[]` taşıdığı doğrulanır (T5 — audit kanıtı) |
| 2. `finans` → legal 403, kendi 200 | `tests/test_documents.py::test_finans_cannot_download_hukuk_document`, `::test_finans_can_download_own_department_document` | 403 / 200 |
| 2. `yonetim` → hepsi 200 | `tests/test_documents.py::test_management_can_download_any_department_document` (+ restricted/board dahil) | 200 |
| 2. restricted/board kuralları | `tests/test_authorization.py::test_employee_never_sees_restricted_or_board_of_own_department`, `::test_management_sees_all_confidentiality_levels` | unit, fake provider ile |
| 3. Admin proje CRUD; employee 403 | `tests/test_projects.py::test_admin_can_create_and_update_project`, `::test_employee_create_project_returns_403`, `::test_duplicate_project_code_returns_409` | 201/200 vs 403/409 |
| 4. Yetki servisi birim testleri | `tests/test_authorization.py` (genişletilmiş, gerçek departman/rol fixture'larıyla) | unit |
| 4. endpoint entegrasyon testleri | `tests/test_documents.py`, `tests/test_ask.py`, `tests/test_projects.py`, `tests/test_document_repo.py` (yeni `list_document_ids_for_departments` testleri) | gerçek DB, gerçek SQL provider |

---

## SORU (Naci cevaplamalı)

1. **Departman taksonomisi/slug'ları ve `finans`/`mali_isler` çift üyeliği.** SPEC_02 §5 "finans: finance + accounting" diyor ama taksonomide (SPEC_02 §8) yalnızca "Finans" ve "Mali İşler" var, ayrı bir "muhasebe" yok. Önerim: `finans` kullanıcısı hem `finans` hem `mali_isler` departmanlarına üye; `enerji` yalnızca üst düğüm `enerji_grubu`'na üye (alt kartlar T7 gereği otomatik kapsanır); slug'lar yukarıdaki §6'daki gibi. Onaylıyor musun, yoksa farklı bir eşleme mi istiyorsun?
2. **"Audit'te retrieved boş" kanıtı.** `audit_log` tablosu Phase 3.4'e kadar yok. Önerim: bu fazda kanıt, zaten var olan `AskResponse.retrieved_document_ids` alanı + `"ask completed"` structured log satırı olsun (T5) — ayrı bir minimal audit tablosu bu faza öne çekilmiyor. Kabul ediyor musun?
3. **İndirme endpoint'inde 403 vs 404.** Mevcut benzer uçlar (`get_document_status`, upload'ın supersedes kontrolü) yetkisiz erişimde bilinçli olarak 404 dönüyor (var olan/yok ayrımını gizlemek için). Kabul kriteri metni açıkça "indirme 403" diyor. Önerim: indirme ucu spec metnine harfiyen uysun (403), mevcut 404 deseninden bilinçli, dokümante edilmiş bir istisna olarak. Onaylıyor musun?
4. **Proje-departman bağlantısı.** Ankara/İzmir RES demo projelerini yalnızca `enerji_grubu`'na mı bağlayayım, yoksa finansman/hukuk gibi başka departmanlar da (salt organizasyonel/filtreleme amaçlı — yetki hâlâ belgenin `department`'ından geliyor, projeden değil) eklenmeli mi?
5. **Upload formuna department/project_id/confidentiality eklenmesi bu fazda mı.** Önerim: hayır, Phase 3.2'nin (AI metadata önerisi) kapsamında kalsın; bu fazda testler belgeleri doğrudan DB'ye yazıyor. Onaylıyor musun?

## Kendi aldığım küçük kararlar

- `Document.department` FK almıyor, string/slug kalıyor (T2); `Document.project_id` FK alıyor (T3).
- `Document.subdepartment` yetkilendirmede kullanılmıyor, salt görüntüleme alanı (T7).
- `departments` tablosuna `is_active` eklenmiyor (CRUD yok, kullanılmayan kolon açılmıyor).
- Departman CRUD endpoint'i yok; yalnızca salt-okunur `GET /api/departments` (admin'in proje formunda departman seçebilmesi için).
- `GET /api/projects` herkese açık (okuma); yalnızca `POST`/`PATCH` `require_admin`.
- Proje kod çakışması → 409; bilinmeyen `department_ids` → 404.
- `yonetim` hiçbir departmana üye edilmiyor (management zaten üyelikten bağımsız her şeyi görüyor).
- `DocumentIdsProvider` protokolüne yeni metod eklendi (`list_document_ids_for_departments`); `AuthorizationScope` değişmedi.
- `tests/test_authorization.py`'nin mevcut 4 testi değiştirilmiyor (T11); yalnızca yeni testler eklenir.
- `tests/test_document_repo.py`'nin `project_id` testi gerçek `Project` satırı kullanacak şekilde güncellenir (FK eklendiği için zorunlu).
- Yeni ortak test yardımcı modülü `tests/department_fixtures.py` (mevcut `tests/t0_fixtures.py`/`tests/fakes.py` deseniyle aynı): `make_department()`, `add_user_to_department()`.
- `tests/conftest.py`'ye `employee_user`/`management_user` fixture'ları (`admin_user`/`inactive_user` ile aynı desen: gerçek DB satırı + `get_current_user` override).

## Doküman değişiklikleri

- `docs/ARCHITECTURE.md`: yeni ADR açılmıyor — ADR-004 zaten "Step 1.2" satırını taşıyor; `DocumentIdsProvider`'a yeni metod eklendiği ve `Document.department`'ın FK almadığı kısa bir not eklenir.
- `docs/DOMAIN_MODEL.md`: §9 zaten doğru (tablolar 1.2 olarak işaretli); değişiklik gerekmiyor.
- `README.md`: proje CRUD `curl` örneği; demo hesap → departman/proje erişim tablosu (`enerji` finansa neden erişemiyor açıklaması).
- `docs/reports/PHASE_1_2_REPORT.md` (şablon `TEMPLATE.md`), `docs/PHASES.md` durum satırı, `git tag phase-1-2`.

## Uygulama sırası

1. Migration `0003_departments_projects.py` (departments, user_departments, projects, project_departments, documents.project_id FK).
2. Modeller: `department.py`, `user_department.py`, `project.py`, `project_department.py`; `user.py`/`document.py`/`__init__.py` güncellemesi.
3. `department_repo.py`, `project_repo.py`; `document_repo.py::SqlDocumentIdsProvider.list_document_ids_for_departments`.
4. `authorization.py` yeniden yazımı + `test_authorization.py` genişletmesi (unit, önce — mantığın izole doğrulanması).
5. `schemas/department.py`, `schemas/project.py`.
6. `deps.py::require_admin`, `core/errors.py` yeni mesajlar; `api/departments.py`, `api/projects.py`; `router.py`.
7. `api/documents.py::download_document`.
8. `demo_departments_seed.py`, `demo_projects_seed.py`; `cli.py` yeni subcommand'lar; `entrypoint.sh`.
9. `tests/department_fixtures.py`; `conftest.py` (`employee_user`/`management_user`); `test_documents.py`, `test_ask.py`, `test_document_repo.py` genişletme; `test_projects.py` (yeni).
10. `make test` yeşil → doküman güncellemeleri → rapor → `docs/PHASES.md` → commit + tag `phase-1-2` + push.

## Kritik dosyalar

- `backend/app/services/authorization.py`
- `backend/app/repositories/document_repo.py`
- `backend/alembic/versions/0003_departments_projects.py`
- `backend/app/models/department.py`
- `backend/app/models/project.py`
- `backend/app/api/projects.py`
- `backend/tests/test_authorization.py`
