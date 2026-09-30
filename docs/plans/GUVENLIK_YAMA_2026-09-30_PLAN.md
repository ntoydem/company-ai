# Güvenlik yaması — Yüklemede departman yetkisi: Implementation Plan

## Bağlam

`docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §2 (B-26 notu) ve §3.3'te tespit edilen, Tansu'nun 30.09.2026
cevap #6'sında "öncelikli giderilmeli" dediği gerçek bir yetki boşluğu: `POST /api/documents/upload`,
`department` alanını yalnızca **bilinen bir slug mu** diye doğruluyor (`app/api/documents.py:176-177`), yükleyenin
o departmana **üye olup olmadığını** hiç sormuyor. Bugün `enerji` üyeliğine sahip bir çalışan
`department=finans` ile yükleme yapabilir; belge Finans'ın `allowed_document_ids` kümesine girer ve o
departmanın Balbal cevaplarına/aramasına kaynak olur (ADR-004, ADR-021 — okuma tarafı korunuyor, yazma tarafı
korunmuyor). Bu, kural 1'in (SECURITY) "yetkisiz içerik LLM'e bile girmez" ilkesini yazma yoluyla delen tek
gerçek açık.

Bu, Balbal entegrasyonundan (B-serisi) bağımsız, küçük ve kendi başına kapatılabilir bir düzeltme.

Okunanlar: `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §0 (Tansu #5/#6), §2 (B-26/3), §3.3, §5.2; kod:
`backend/app/api/documents.py` (tam), `backend/app/models/user.py` (`department_slugs`/`department_ids`
property'leri), `backend/app/services/authorization.py` (`allowed_document_ids`, employee/management/admin
kuralları), `backend/tests/test_documents.py` (tüm upload testleri + fixture kullanımları), `backend/tests/
department_fixtures.py`, `backend/tests/conftest.py` (`admin_user`/`employee_user`/`management_user`).

## Tespitler

- **T1 — Bugün `POST /api/documents/upload`'da rol bazlı hiçbir kısıt yok.** Endpoint yalnızca
  `Depends(get_current_user)` alıyor (`documents.py:152`); `employee`, `management`, `admin` aynı şekilde
  çağırabiliyor. Kısıtlanacak olan rol değil, **hangi `department` değerinin kabul edildiği**.
- **T2 — `User.department_slugs`/`departments` zaten var, yeni bir sorgu gerekmiyor.** `models/user.py`'deki
  `department_slugs` property'si (`[d.slug for d in self.departments]`) tam ihtiyaç duyulan bilgiyi veriyor;
  `user_departments` tablosundan ekstra bir repo çağrısı gerekmez.
- **T3 — Kural yalnızca `employee` için anlamlı; `management`/`admin` zaten her departmanı görür.**
  `authorization.py`'nin kendi kuralı: `management` = tüm departmanlar/tüm gizlilik, `admin` = her şey. Bu
  iki rolü yükleme tarafında da kısıtlamak, okuma tarafındaki yetkiyle tutarsız ve gereksiz olurdu — Tansu'nun
  cevabı da yalnızca "üye olmadığı departman" örneğini (enerji çalışanının finans'a yüklemesi) veriyor,
  yönetim kadrosunu değil. **Kural: `current_user.role not in (management, admin)` ise `department`,
  `current_user.department_slugs` içinde olmalı.**
- **T4 — `department=None` (belirtilmemiş) davranışı değişmemeli.** Bugün `department` opsiyonel
  (`Form()` varsayılanı `None`); boş bırakılan bir yükleme zaten yalnızca admin'e görünür kalıyor (employee
  filtre kuralı `Document.department.in_(department_slugs)`'a göre `None` hiçbir slug'a eşleşmez,
  `management`'ın filtresi de yalnızca gizlilik seviyesine bakar ama department eksik olsa da satırı
  döndürür — yani "hiç departman yok" fail-safe bir durumdur, güvenlik açığı değildir). Yeni kural yalnızca
  **belirtilmiş ve yükleyenin üyesi olmadığı** bir `department` değerine uygulanır; `None` etkilenmez. Bu,
  SORU 1'in önerilen cevabıdır.
- **T5 — Kontrolün sırası: önce "slug var mı" (422), sonra "yükleyen üye mi" (403).** Mevcut
  `UNKNOWN_DEPARTMENT_MESSAGE` (422) kontrolü (`documents.py:176-177`) korunur; yeni kontrol onun **hemen
  ardından**, `project_id`/versiyon zinciri kontrollerinden **önce** eklenir — dosya diske yazılmadan (henüz
  `store.store(...)` çağrılmamış, `documents.py:196` civarı) reddedilmesi gerekir, mevcut kod zaten bu sırayı
  (önce doğrulama, sonra depolama) izliyor.
- **T6 — Hiçbir mevcut test kırılmaz.** `test_documents.py`'deki **tüm** upload testleri (`_upload(...)`
  çağıran her test) `admin_user` fixture'ını kullanıyor (`grep` ile doğrulandı: 12 upload testinin hepsi
  `admin_user`); admin yeni kuralı bypass ettiği için hiçbiri etkilenmez. `employee_user`/`management_user`
  fixture'ları bugün yalnızca metadata-suggestion, list/get/download testlerinde kullanılıyor — hiçbiri
  `/upload`'ı çağırmıyor. Bu, plan maddesinin 2. sorusunu (mevcut testleri bozar mı) olumsuz yanıtlıyor:
  **bozmaz**, çünkü bugüne kadar employee/management ile gerçek bir upload testi hiç yazılmamış.
- **T7 — İki aşamalı onay kararıyla (Tansu #5, `TANSU_GERI_BILDIRIM` §5.2) çelişmiyor, onun ön koşulunu
  kapatıyor.** İki aşamalı onay, **hangi belgenin yayınlanacağını** (bir `review_status`/`documents.
  published` benzeri alan, bugün kodda **hiç yok** — B-28 ile birlikte gelecek) kontrol edecek; bu yama ise
  **hangi departmana yüklenebileceğini** kontrol ediyor — ayrı katmanlar. `TANSU_GERI_BILDIRIM.md` §3.3 ve
  §5.2 zaten bunu ayrı ayrı işaretlemişti ("ikinci onay yanlış departmana yüklenmiş belgeyi durdurur; ama
  yönetici onaysız yayınlar, dolayısıyla departman kontrolü **ayrıca** şarttır, onay akışı onun yerine
  geçmez"). Bu yama olmadan iki aşamalı onay da açığı kapatmazdı: bir çalışan `department=finans` yazıp kendi
  onayını verse bile (1. aşama), belge yanlış departmanda kalırdı — onay *akışı* departmanı değil, *içeriği*
  doğruluyor. Sonuç: **çelişki yok**, iki düzeltme birbirini tamamlıyor ve bağımsız sırayla yapılabilir; bu
  yama B-28'i beklemeden şimdi uygulanabilir.
- **T8 — Mesaj ve kod:** mevcut `UNKNOWN_DEPARTMENT_MESSAGE` (422, "Bilinmeyen departman.") ile aynı ailede,
  ayrı bir sabit: `DEPARTMENT_NOT_ALLOWED_MESSAGE = "Bu departmana belge yükleme yetkiniz yok."`, **403**
  (yetki var ama bu kaynağa değil — `download_document`'ın zaten kullandığı 403 deseniyle tutarlı,
  `documents.py:238-240`'taki "existence hiding yerine 403" kararı burada da geçerli: departman adı zaten
  `GET /api/departments` ile herkese açık, gizlenecek bir şey yok).

## Değişiklik (uygulama aşamasında, şimdi yazılmayacak)

`app/api/documents.py::upload_document`, mevcut departman doğrulama bloğunun hemen altına:

```python
if department is not None and department_repo.get_by_slug(session, department) is None:
    raise HTTPException(422, UNKNOWN_DEPARTMENT_MESSAGE)
if (
    department is not None
    and current_user.role not in (UserRole.management, UserRole.admin)
    and department not in current_user.department_slugs
):
    raise HTTPException(403, DEPARTMENT_NOT_ALLOWED_MESSAGE)
```

`UserRole` zaten `app.models.user`'dan içe aktarılıyor mu kontrol edilecek (bugün yalnızca `User` içe
aktarılmış, `UserRole` eklenmesi gerekecek — küçük bir import satırı).

## Testler (uygulama aşamasında eklenecek)

| Senaryo | Beklenen | Fixture |
|---|---|---|
| Enerji çalışanı `department=finans` ile yükler | **403**, `DEPARTMENT_NOT_ALLOWED_MESSAGE` | `employee_user` + `add_user_to_department(..., "enerji_grubu")` |
| Enerji çalışanı `department=enerji_grubu` (kendi üyeliği) ile yükler | 201 | aynısı |
| Çok üyelikli çalışan (`finans`+`mali_isler`) ikinci üyeliğine yükler | 201 | `employee_user` + iki `add_user_to_department` |
| `department` belirtilmez (`None`) | 201, mevcut davranış değişmez | `employee_user`, üyeliksiz de olabilir |
| `management` herhangi bir departmana yükler (üyeliği olmasa bile) | 201 | `management_user`, üyelik eklenmez |
| `admin` herhangi bir departmana yükler | 201 (zaten mevcut testler kanıtlıyor) | `admin_user` (regresyon, değişmez) |
| Bilinmeyen slug + yetkisiz departman aynı anda | 422 önce döner (T5 sırası) | `employee_user`, `department="hayali_departman"` |

Mevcut `test_upload_with_department_project_and_confidentiality` ve `test_upload_unknown_department_returns_422`
(ikisi de `admin_user`) değişmeden yeşil kalmalı — regresyon kanıtı olarak ayrıca çalıştırılacak.

## Doküman güncellemeleri (uygulama aşamasında)

- `docs/ARCHITECTURE.md` ADR-004'e kısa bir concretization satırı: yükleme artık `department`'ı yalnızca
  slug geçerliliği için değil, yükleyenin üyeliği için de doğruluyor (management/admin muaf).
- `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`: §7.1'e bu maddenin kapandığı not düşülür ("Tansu #6 —
  KAPANDI, bkz. `phase-...` / rapor").
- Bu küçük düzeltme için ayrı bir Phase numarası açılmayacak (Naci'nin onayına bağlı — SORU 3); rapor
  gerekiyorsa `docs/reports/` altında kısa bir not, `docs/PHASES.md`'ye ayrı bir satır değil.

## SORU (Naci cevaplamalı)

1. **`department=None` (belirtilmemiş) employee için serbest kalsın mı?** Önerim (T4): evet — bugünkü
   davranış zaten fail-safe (yalnızca admin görür), kısıtlamak gereksiz bir kısıtlama olur.
2. **Mesaj/kod onaylı mı?** Önerim (T8): 403 + `"Bu departmana belge yükleme yetkiniz yok."` — `download`
   ucundaki 403 deseniyle tutarlı, departman adı zaten herkese açık olduğu için "varlığı gizleme" endişesi yok.
3. **Bu yama bir phase sayılsın mı (tag/rapor) yoksa doğrudan `main`'e küçük bir commit mi?** Önerim: küçük,
   bağımsız bir commit + `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md`'ye tek satır güncelleme; ayrı bir
   `phase-x-y` etiketi açmaya gerek yok, çünkü PHASES.md'nin phase birimlerinden biri değil (Naci'nin doğrudan
   talebiyle açılan bağımsız bir güvenlik yaması).

## Uygulama sırası (onaydan sonra)

1. `app/api/documents.py`: `UserRole` import, `DEPARTMENT_NOT_ALLOWED_MESSAGE` sabiti, kontrol satırı.
2. `tests/test_documents.py`: yukarıdaki 7 senaryo.
3. `make test` (hedefli: `-k test_upload`) + tam `make test` + `make lint`.
4. `docs/ARCHITECTURE.md` ADR-004 concretization, `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` §7.1 notu.
5. Commit + push (SORU 3'ün cevabına göre tag'li ya da tagsız).

## Kritik dosyalar

- `backend/app/api/documents.py` (satır ~176 civarı)
- `backend/tests/test_documents.py`
- `docs/ARCHITECTURE.md` (ADR-004)
- `docs/notes/TANSU_GERI_BILDIRIM_2026-09-30.md` (§7.1)
