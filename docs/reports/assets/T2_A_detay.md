# T2 — A: TEST_PRJ pasife alma — ön kontrol, kod değişikliği, canlı uygulama

## Ön kontrol (salt okunur, canlıya dokunmadan önce)

```
TEST_PRJ row: code='TEST_PRJ' name='Test Project' is_active=True
  id=af57bf0b-532d-4f4c-a272-8633ee60ab8a created_at=2026-09-23 08:12:10.045502+00:00
documents with project_id=af57bf0b-532d-4f4c-a272-8633ee60ab8a: 0
```

Karar kapısı geçti: bağlı belge **0** → UPDATE adımına devam edildi (belgeye hiç dokunulmadı, çünkü hiç yok).

## Kod değişikliği — `is_active` filtresi

`projects.is_active` kolonu migration 0003'ten beri var; şema/migration değişikliği yok, yalnız sorgu filtresi. Üç fonksiyona `Project.is_active.is_(True)` eklendi (mevcut emsal: `tag_repo.py`, `user_repo.py`, `guide_repo.py`):

| Fonksiyon | Dosya | Rol | Değişti mi |
|---|---|---|---|
| `named_project_codes` | `app/services/assist.py` | Soruda adı geçen projeyi tespit eder — iş emrinin "proje adı eşleştirme" maddesi | ✅ |
| `unknown_project_names` | `app/services/project_narrowing.py` | "Bilinen proje kelimeleri" kümesini kurar; bir mention'ın "olmayan proje" sayılıp sayılmayacağına karar verir | ✅ |
| `visible_project_names` | `app/services/project_narrowing.py` | "Hangi projeyi kastediyorsunuz: X mi, Y mi?" listesini kurar | ✅ |
| `narrow_allowed` | `app/services/project_narrowing.py` | Girdi kodları zaten yukarıdaki filtreli `named_project_codes`'tan geldiği için gereksiz savunma kodu eklenmedi | ❌ (bilinçli) |
| `project_words` | `app/services/assist.py` | Eşleşmeyen terim listesinden proje kelimelerini hariç tutar (ayrı amaç: terminoloji, isimlendirme değil) | ❌ (kapsam dışı, iş emrinin iki maddesine girmiyor) |
| `project_repo.search` | `app/repositories/project_repo.py` | Admin'e özel; satırdaki yorum bilinçli olarak pasif projeleri de gösteriyor diyor | ❌ (DOKUNULMADI, emir gereği) |
| `group_available`, `_project_names`, `disambiguate_question` | `app/services/assist.py` | Girdileri zaten yetkili/adlı aday kümeden geliyor (TEST_PRJ'nin hiç belgesi yok, bu yüzden bu kümelere hiç girmiyor) | ❌ (kapsam dışı) |

Alt dize eşleşmesi, harf duyarsızlığı, ASCII katlama, RES/GES eki mantığına dokunulmadı (T3'e bırakıldı).

## Birim test

`backend/tests/test_project_narrowing.py::test_inactive_project_is_never_named_known_or_visible` — is_active=False bir proje ekleyip: (1) tam adı soruda geçse bile `named_project_codes` boş döner, (2) "covenant testi" / "performans testi" cümleleri onu adlandırmaz, (3) `unknown_project_names` etkilenmez, (4) `visible_project_names` onu listelemez (bir belgesi `allowed` kümesinde olsa bile). 788'lik yeşil koşuya dahil.

## Canlı veri değişikliği

- **Yedek:** `data/backups/live_pre_T2_20261016-0848.dump`, **945.952 bayt**, sha256 `f574de844e93e64128b52bad031a7c66352d5f9bea1f8a7ab2faebfd5f670772` (pg_dump -Fc, UPDATE'ten önce).
- **UPDATE:** `docker exec -i company-ai-backend-1 python -` ile ORM session üzerinden `UPDATE projects SET is_active=false WHERE code='TEST_PRJ'`; `result.rowcount == 1` doğrulandı, ancak sonra commit edildi. Çıktı: `OK: rowcount=1, committed`. Satır silinmedi.
- **Doğrulama:** `code='TEST_PRJ' name='Test Project' is_active=False`.
- **`make restart-backend`:** 08:50:00.059 → 08:50:12.215 UTC, **≈ 12 s** kesinti; backend log'unda `Running upgrade` satırı yok (migration tetiklenmedi, schema zaten head).
- **`scripts/smoke_live.py`:** **9/9**, exit 0 (bkz. `logs/t2_smoke_after.log`).

## 45 satırlık alias vektörü (`scripts/t1/b5_alias_vectors.py`) — önce/sonra

Önce (15.10.2026, commit `09cb870`'teki `results/t1/b5_alias_vectors.json`): **36/45 ✅**. Sonra (16.10.2026, TEST_PRJ pasif + filtre canlıda): **35/45 ✅**.

**Tek değişen satır:**
| Soru | Önce | Sonra |
|---|---|---|
| "Test Project belgeleri nerede?" | ok=True, named=['TEST_PRJ'] | ok=False, named=[] |

Bu satırın kendi beklentisi (`expected_named={"TEST_PRJ"}`) TEST_PRJ'nin aktif-ve-adlandırılabilir olduğu döneme ait; pasife alma kararıyla artık geçersiz (script güncellenmedi — emir "36/45'in kalanını düzeltmeye çalışma" dediği için script'in kendisi de bu iş emrinin kapsamı dışında bırakıldı). Diğer 44 satırın hiçbiri değişmedi (RES/GES-eki, ASCII, büyük/küçük harf sorunları aynen duruyor, T3'e bırakıldı).

**Hedeflenen 4 soru doğrudan `named_project_codes` ile canlıda teyit edildi** (bunlar b5'in 45 satırında değil, eval'in 99 sorusunda — ayrı doğrulama):

| Soru ID | Soru | Önce (T1 raporu) | Sonra |
|---|---|---|---|
| ANK-FIN-010 | "Karatepe RES'in son covenant testi sonucu nedir?" | `{ANK_RES, TEST_PRJ}` → eksen `none` | `{ANK_RES}` → eksen `named` |
| ANK-AUT-003 | "Karatepe RES'in son covenant testi sonucu nedir?" | `{ANK_RES, TEST_PRJ}` → eksen `none` | `{ANK_RES}` → eksen `named` |
| ANK-EPC-005 | "Karatepe RES performans testi raporuna göre teyit edilen kapasite kaç MW'tır?" | `{ANK_RES, TEST_PRJ}` → eksen `none` | `{ANK_RES}` → eksen `named` |
| GEN-GEN-003 | "Bir kredi sözleşmesinde covenant testi ne işe yarar?" | `{TEST_PRJ}` → aday küme 10 grup belgesine iniyor | `{}` (adsız) → eksen dağılıma göre karar verir, eski davranış geri geldi |

Dört soru da beklendiği gibi düzeldi; b5'in 45 satırında bunların dışında başka bir satır değişmedi.

## Geri dönüş

Gerekmedi — `smoke_live.py` ilk denemede 9/9 verdi. Gerekseydi: `UPDATE projects SET is_active=true WHERE code='TEST_PRJ'` → `git checkout <önceki HEAD> -- backend/` → `make restart-backend` → smoke; veri hasarı şüphesinde `data/backups/live_pre_T2_20261016-0848.dump`'tan `pg_restore` (önce `restore_test_X` provası, OPERATIONS.md §2.1).

## Eval ortamı

Eval DB'de `TEST_PRJ` hiç yoktu (seed_data'da da yok); artık canlı ve eval aktif proje kümesi eşit: **6 aktif proje**.
