# Phase 1.2 Raporu — Departman, rol, proje, yetki

**Tarih:** 23.09.2026  **Model:** Claude Sonnet 5  **Tag:** phase-1-2  **Commit:** `git rev-list -n1 phase-1-2`

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den kelimesi kelimesine) | Durum | Kanıt (test adı / komut / çıktı) |
|---|---|---|---|
| 1 | `enerji` → finans belgesi listede yok, indirme 403, `/api/ask` ile "bilgi bulamadım", audit'te retrieved boş | ✅ | `test_documents.py::test_employee_list_excludes_other_department_documents`, `::test_employee_download_other_department_document_returns_403`, `test_ask.py::test_employee_ask_outside_department_returns_no_answer_with_empty_retrieved` (+ canlı doğrulama, §"Canlı doğrulama") |
| 2 | `finans` → legal 403, kendi 200; `yonetim` → hepsi 200; `restricted`/`board` kuralları test edilmiş | ✅ | `test_documents.py::test_finans_cannot_download_hukuk_document`, `::test_finans_can_download_own_department_document`, `::test_management_can_download_any_department_and_confidentiality_level`, `::test_employee_cannot_download_restricted_document_of_own_department`; unit: `test_authorization.py::test_management_sees_all_departments_and_confidentiality_levels`, `::test_employee_sees_only_own_department_normal_documents` |
| 3 | Admin proje CRUD; employee 403 | ✅ | `test_projects.py::test_admin_can_create_and_update_project`, `::test_employee_create_project_returns_403`, `::test_duplicate_project_code_returns_409`, `::test_create_project_with_unknown_department_id_returns_404` |
| 4 | Yetki servisi birim testleri + endpoint entegrasyon testleri | ✅ | `test_authorization.py` (6 yeni unit test, fake provider); `test_documents.py`/`test_ask.py`/`test_projects.py`/`test_document_repo.py` (gerçek DB, gerçek `SqlDocumentIdsProvider`) |

## 2. Yapılanlar
- `departments` (ağaç, `parent_id` self-FK), `user_departments`, `projects`, `project_departments` tabloları (migration `0003`); `documents.project_id`'ye FK eklendi, `documents.department` bilinçli olarak FK almadı (bkz. §5).
- `allowed_document_ids()` gerçek mantıkla dolduruldu: `admin` = scope içindeki her şey; `management` = tüm departman + tüm gizlilik seviyesi (üyelikten bağımsız); `employee` = üye olduğu departman(lar)ın yalnızca `normal` belgeleri. `DocumentIdsProvider` protokolüne tek yeni metod (`list_document_ids_for_departments`) eklendi; `allowed_document_ids`'in 3 parametreli imzası (ADR-004) değişmedi.
- `GET /api/documents/{id}/download` (yeni) — yetkisiz erişimde `403` (mevcut `get_document_status`'un 404 desenine bilinçli, dokümante edilmiş bir istisna).
- `GET /api/departments` (salt okunur, seed-only — CRUD yok) ve admin-only proje CRUD: `GET/POST /api/projects`, `PATCH /api/projects/{id}` (`require_admin` dependency, yeni).
- Demo departmanları (`enerji_grubu` + 3 alt departman, `finans`, `hukuk`, `mali_isler`, `idari_isler`) ve demo kullanıcı üyelikleri (`finans`→finans+mali_isler, `hukuk`→hukuk, `enerji`→enerji_grubu; `yonetim` üyeliksiz) idempotent seed edildi. Demo projeler Ankara RES / İzmir RES, `enerji_grubu`+`finans`+`hukuk`'a bağlı (SORU 4 cevabı).
- `seed_data/t0/upload.sh`'a dokunulmadı (admin olarak çalışıyor, department set etmiyor — kırılmadı).

## 3. Değişen dosyalar
`git diff --stat` (36 dosya): 1273 satır eklendi, 45 satır çıkarıldı. Yeni: `app/models/{department,project,project_department,user_department}.py`, `app/repositories/{department_repo,project_repo}.py`, `app/schemas/{department,project}.py`, `app/api/{departments,projects}.py`, `app/services/{demo_departments_seed,demo_projects_seed}.py`, `alembic/versions/0003_departments_projects.py`, `tests/{department_fixtures,test_projects}.py`. Değişen: `app/services/authorization.py`, `app/repositories/document_repo.py`, `app/models/{user,document,__init__}.py`, `app/api/{deps,documents,router}.py`, `app/core/errors.py`, `app/cli.py`, `entrypoint.sh`, `tests/{conftest,test_authorization,test_document_repo,test_documents,test_ask,test_migrations}.py`, `README.md`, `Makefile`, `docs/{ARCHITECTURE,PHASES}.md`.

## 4. Testler
- Backend: **128 geçti**, 3 atlandı (`live_llm`), 5 uyarı (JWT test secret uzunluğu — Phase 1.1'den kalma, zararsız). ~53 sn.
- `assert-pipeline-schema`: geçti. ocr-worker: **9 geçti**.
- `make lint` (ruff check + format --check + mypy, backend/ocr-worker): temiz. `docs/prompts/ANSWER_SYSTEM_PROMPT.md` eşitliği: güncel (bu faz dokunmadı).
- Migration: `0002 -> 0003` uygulandı ve geri alındı (`test_migrations.py`, güncellenmiş revizyon beklentisiyle); `alembic upgrade head` idempotent.

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| `documents.department` FK almıyor, string/slug kalıyor | Mevcut testler/veriler serbest İngilizce string kullanıyor (`"finance"`, `"legal"`); admin bu alanı hiç filtrelemiyor, kırılma riski yok | Yanlış yazılmış slug güvenli yönde başarısız olur (belge admin dışında görünmez) — Phase 3.2 notu eklendi (docs/PHASES.md) |
| `documents.project_id` FK alıyor | Tip zaten uyumlu (UUID); tek etkilenen test güncellendi | `test_document_repo.py`'nin proje testi artık gerçek `Project` satırı kullanıyor |
| Departman CRUD yok, yalnızca seed + salt-okunur `GET /api/departments` | Spec yalnızca proje CRUD'unu istiyor | Departman ekleme/değiştirme yalnızca migration/seed ile |
| İndirme ucunda 403 (diğer uçlardaki 404 deseninden bilinçli istisna) | Kabul kriteri metni "indirme 403" diyor | Dokümante edildi (ADR-004 notu, kod yorumu) |
| `yonetim` hiçbir departmana üye edilmiyor | management zaten üyelikten bağımsız her şeyi görüyor | Seed daha basit |
| Upload formu bu fazda değişmedi (department/project_id/confidentiality hâlâ API'den ayarlanamıyor) | Phase 3.2'nin (AI metadata önerisi) kapsamı | Testler `Document` satırlarını doğrudan DB'ye yazıyor |

**SORU cevapları (Naci, uygulamadan önce):** 1) `finans`→finans+mali_isler, `enerji`→yalnızca enerji_grubu — uygulandı. 2) Audit kanıtı `AskResponse.retrieved_document_ids` + `"ask completed"` log'u — uygulandı, `audit_log` tablosu öne çekilmedi. 3) İndirme 403, mevcut 404 desenine bilinçli istisna — uygulandı ve dokümante edildi. 4) Ankara/İzmir RES → `enerji_grubu` + `finans` + `hukuk` (genişletildi; `mali_isler`/`idari_isler` hariç, şirket geneli) — uygulandı. 5) Upload formu değişmiyor — uygulandı.

## 6. Açık sorular (Naci cevaplamalı)
Yok.

## 7. Riskler / sonraki phase için notlar
- **Güvenli yöndeki hata modu (Naci'nin notu):** `documents.department` FK olmadığı için yanlış yazılmış/bilinmeyen bir slug, belgeyi sessizce yalnızca admin'e görünür bırakır (hiçbir employee/management departman eşleşmesi bulamaz) — hata verilmez, belge kaybolmuş gibi görünür. Phase 3.2'nin upload/öneri akışı `department` değerini `GET /api/departments`'ın döndürdüğü bilinen slug listesine karşı doğrulamalı; bu not `docs/PHASES.md`'nin Phase 3.2 girdisine eklendi.
- `subdepartment` alanı yetkilendirmede kullanılmıyor (yalnızca görüntüleme/filtre) — bir departmanın alt kartları her zaman üst düğümün `department` slug'ını paylaşmalı; aksi halde o alt kart belgeleri kimseye görünmez olur (yine güvenli yönde, ama şaşırtıcı olabilir).
- Departman ağacı yalnızca `parent_id` kolonuyla var; hiyerarşik sorgu/ORM relationship (parent/children) eklenmedi (YAGNI) — Phase 3.3'ün departman kartlı ana sayfası bunu ihtiyaç duyarsa eklenecek.
- Proje-departman bağlantısı organizasyonel/filtreleme amaçlıdır; retrieval/`/api/ask` hâlâ yalnızca `Document.department`'a bakıyor, `project_id`'nin department'larına değil (ADR-004 ile tutarlı, bilinçli).

## 8. Doğruladığım üçüncü taraf davranışları
- SQLAlchemy 2.0: transient (DB'ye hiç eklenmemiş) bir `User` nesnesinde `relationship()` koleksiyonu (`user.departments`) ilk erişimde sorgu tetiklemeden boş liste döner — `tests/test_authorization.py`'nin mevcut 4 testi bu sayede hiç değişmeden yeşil kaldı (planın T11 tespiti, uygulamada doğrulandı).
- `session.expire(user, ["departments"])`: bir ilişkiyi ham `session.add(AssociationRow(...))` ile (ORM koleksiyonu üzerinden değil) değiştirdikten sonra, aynı obje üzerinde ilişkinin bir sonraki erişimde taze yüklenmesini garantiliyor — `tests/department_fixtures.py::add_user_to_department`'ta kullanıldı.

## 9. Kaynak kullanımı
- Bu fazda LLM çağrısı yok (yetki katmanı). Container'lar sağlıklı kaldı (`docker compose ps` → `healthy`); canlı doğrulama sırasında admin/enerji/yonetim hesaplarıyla gerçek login + proje + belge indirme akışları çalıştırıldı.

## Canlı doğrulama
```
# enerji, finans belgesini listede göremiyor, indiremiyor, /api/ask ile öğrenemiyor:
curl http://localhost:8000/api/documents -b enerji_cookies.txt        # finans belgesi yok
curl -w '%{http_code}' http://localhost:8000/api/documents/<finans-id>/download -b enerji_cookies.txt   # 403
curl -X POST http://localhost:8000/api/ask -b enerji_cookies.txt -d '{"question":"Finans belgesinde ne yazıyor?"}'
# {"answered":false,"answer":"Mevcut şirket kaynaklarında ... yeterli bilgi bulamadım.","retrieved_document_ids":[]}

# admin aynı belgeyi indirebiliyor:
curl -w '%{http_code}' http://localhost:8000/api/documents/<finans-id>/download -b admin_cookies.txt    # 200

# enerji proje oluşturamıyor, admin oluşturabiliyor:
curl -w '%{http_code}' -X POST http://localhost:8000/api/projects -b enerji_cookies.txt -d '{"name":"X","code":"X"}'  # 403
curl -w '%{http_code}' -X POST http://localhost:8000/api/projects -b admin_cookies.txt -d '{"name":"Test","code":"TEST_PRJ"}'  # 201
```
