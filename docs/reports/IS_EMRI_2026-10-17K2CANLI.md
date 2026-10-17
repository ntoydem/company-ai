# İş Emri 2026-10-17K2CANLI — K1 + LEG-004 canlı işlemi (Ç-15/6)

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `dd08085`) · **Ürün 1**

**Dayanak:** Naci 17.10.2026 10:35 açık onay ("canlıya al"). Silme adımı için ikinci açık onay aynı gün oturum içinde ("§5 adım 3'ü çalıştırmana onay veriyorum"). Onay Kanıtı: Tansu, `ftansu/AI-BalBal` `docs/yazismalar/2026-10-17_naciye-bekleyenler-cevabi.md` (PR #61), Ç-15/6. Komut listesi: `docs/reports/IS_EMRI_2026-10-16K2.md` §5, olduğu gibi uygulandı.

**Sonuç:** başarılı. Belge sayısı 113, iki belge yeni tarihlerle yeni UUID'lerle `ready`, LEG-004 → DEV-001 bağı kuruldu, smoke_live **9/9** (ikinci koşu; ilk koşu 8/9, §6).

## 1. Başlangıç

- **TS:** `20261017-0836` (UTC; `date -u +%Y%m%d-%H%M`)
- **Adım 0:** dal `feat/adim5-veri-kutuphanesi`, `dd08085`, `git status --short` yalnız `?? logs/`.
  Manifest: `2025-01-15_IZM_RES_Önlisans_EXECUTED_active.pdf 2025-01-15 2026-08-10_IZM_RES_Legal_Review_Memo_EXECUTED_active.pdf` (beklenen). Yeniden üretim gerekmedi.
  Servisler: backend, ocr-worker, postgres `Up (healthy)`.

## 2. Önce / sonra

**Belgeler**

| | external_ref | id | document_date | effective_date | status |
|---|---|---|---|---|---|
| önce | DOC-IZM-DEV-001 | `4cae7f3e-3c68-4fca-8a6a-f08546cbfd5f` | 2024-01-18 | 2024-01-18 | ready |
| önce | DOC-IZM-LEG-004 | `36aa7c27-c87d-400b-9156-cd62b7ae2606` | 2023-11-01 | – | ready |
| sonra | DOC-IZM-DEV-001 | `a149f710-1b17-4998-a4d6-fc6d23886702` | 2025-01-15 | 2025-01-15 | ready |
| sonra | DOC-IZM-LEG-004 | `391f735e-233b-42af-a3a8-f32a4e6ffcc6` | 2026-08-10 | – | ready |

Önce `storage_path`: `<uuid>/original.pdf` (her ikisi).

**Sayılar**

| | documents | document_chunks | document_pages | audit_log |
|---|---|---|---|---|
| adım 1 (önce) | 113 | 461 | 461 | 1624 |
| adım 3 sonrası (silme teyidi) | 111 | 453 | 453 | – |
| adım 5 (sonra) | **113** | 461 | 461 | – |
| son kontrol | 113 | – | – | 1642 |

Silme teyidinde iki ref için 0 satır, eski UUID'lerin `ingestion_jobs` kaydı 0 (CASCADE).

**FK'siz izler (adım 1):** `|0|84`. Başka belgeden `related_document_ids` bağı yok, supersedes bağı 0, eski iki UUID'yi anan `audit_log.documents_retrieved` satırı **84**. Bu satırlara bilerek dokunulmadı (K2 §5); son kontrolde yine 84.

**Doğrulama (adım 5)**

| Kontrol | Beklenen | Gerçek |
|---|---|---|
| iki belge | yeni UUID; DEV-001 2025-01-15\|2025-01-15\|ready; LEG-004 2026-08-10\|\|ready | ✅ (tablo yukarıda) |
| documents | 113 | 113 |
| LEG-004 `related_document_ids` = [DEV-001] | t | t |
| iki belgede 18.01.2024 / 01.11.2023 parçası | 0\|0, 0\|0 | DEV-001 0\|0, LEG-004 0\|0 |
| tüm DB'de 18.01.2024 parçası | 0 | 0 (önce 2; §5'te "bugün 3" yazıyordu, §6) |
| `make validate-ocr ARGS=--all` | hata yok | exit 0 |
| `/health` | ok | `{"status":"ok","version":"0.1.0","database":"ok"}` |
| smoke_live | 9/9 | 8/9 → yeniden koşu **9/9** (§6) |

`make seed-demo-documents`: `was_created` yalnız DOC-IZM-DEV-001 ve DOC-IZM-LEG-004 için `true`, diğer 111 ref "exists, unchanged". `wait-for-documents: all ready, count 113`.

## 3. Yedek

| Dosya | Boyut | Kontrol |
|---|---|---|
| `data/backups/live_pre_K2_20261017-0836.dump` | 967.520 B | `pg_restore --list` → 20 "TABLE DATA", hata yok |
| `data/backups/live_pre_K2_20261017-0836_docs.tgz` | 740.513 B | `tar -tzvf`: iki klasör, 6 dosya (`original.pdf`, `ocr.pdf`, `text.txt` × 2) |
| `data/backups/live_pre_K2_20261017-0836_docs/` | – | adım 3'te taşınan eski iki klasör |

`data/` gitignore'lu (`.gitignore:7`); commit'e girmedi. İsteğe bağlı restore testi (OPERATIONS.md §2.1) yapılmadı.

## 4. audit_log izi

- Eski iki UUID'yi anan satır: 84 (önce ve sonra aynı, dokunulmadı).
- TS'den sonra eklenen satır: 18 = iki smoke_live koşusu × 9 soru. Geri dönüş yapılsaydı gidecek satırlar bunlardı.

## 5. smoke_live

| Koşu | Saat (UTC) | Sonuç | Ham çıktı |
|---|---|---|---|
| 1 | 09:16–09:17 | **8/9**, exit 1 — (a) ❌ `value '13.600.000' not in Excel part` | `logs/smoke_20261017-0916_*.json` |
| 2 | 10:15 | **9/9**, exit 0 | `logs/smoke_20261017-1015_*.json` |

## 6. Sapmalar ve kendi başına verilen kararlar

1. **Silme ilk denemede çalışmadı.** Claude Code izin denetimi `DELETE` komutunu engelledi; ardından salt okuma SELECT'i de engelledi. Komut çalışmadığı için DB değişmedi. Durdum ve bildirdim. Naci ikinci açık onayı verdi; komut aynen çalıştı (`BEGIN / DELETE 2 / COMMIT`). Yedek ile silme arasında yaklaşık 40 dk geçti. Arada DB'ye yazan bir işlem yapılmadı, yeniden yedek alınmadı.
2. **smoke (a) ilk koşuda düştü.** Belge kısmı 13.600.000 USD'yi doğru kaynakla (Covenant Compliance Report Q2 2026) verdi. Excel kısmı "Erişebildiğiniz Excel dosyalarında bu soruyu cevaplayacak veri bulamadım" dedi (`excel_sources: 0`, request_id `42fb12c16f4b48e896943309115186a6`). 16.10 15:21 koşusunda aynı soru Excel'den 13.600.000 döndürmüştü. Soru Karatepe Excel'iyle ilgili; bu işlemde Excel'e ve Karatepe'ye dokunulmadı. Değerlendirmem: Excel planlayıcı LLM çağrısının tek seferlik sapması. Emir 7 gereği geri almadım ve Naci'ye sordum. Naci seçenek 1'i (bir kez daha koş) seçti; ikinci koşu 9/9.
3. **18.01.2024 sayımı:** §5 "bugün 3" diyordu, adım 1'de tüm DB'de 2 çıktı. DUR koşulu değil; sonuç zaten 0. Bilgi olarak yazıldı.
4. **Kabuk durumu:** Komutlar ayrı Bash çağrılarında çalıştığı için `COMPOSE`, `TS`, `Q`, `DEV`, `LEG` tanımları scratchpad'de tek dosyada tutuldu ve her adımda yüklendi. Komutların kendisi §5 ile aynı.
5. **LLM çağrısı:** Emir "LLM çağrısı yok" diyordu. Tek istisna, emrin istediği `smoke_live.py`: iki koşu, 18 soru. Başka LLM çağrısı yapılmadı. Eval ortamına dokunulmadı.

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1. Okunan: K2 raporu §5; İş Emri 2026-10-17K2CANLI
Ürün etiketi      : Ürün 1 — demo veri düzeltmesinin canlıya alınması (kod/davranış değişmedi)
Ç-15/6 onay kanıtı: Naci 17.10 10:35 "canlıya al" + oturum içi silme onayı; Tansu PR #61
  (ftansu/AI-BalBal docs/yazismalar/2026-10-17_naciye-bekleyenler-cevabi.md). Şartlar:
  yedek (§3, doğrulandı) ✓, geri alma planı (K2 §5 "Geri dönüş", kullanılmadı) ✓,
  smoke_live 9/9 (§5, ikinci koşu) ✓, kapı koşularından önce ✓
Gizli bilgi       : Yok — .env yalnız smoke_live ve CADDY_PORT için okundu, değişmedi; parola yazılmadı
Kapsam dışı değişiklik : Yok — canlı DB'de yalnız DOC-IZM-DEV-001 ve DOC-IZM-LEG-004 silinip
  yeniden yüklendi; data/documents altında iki eski klasör yedeğe taşındı, iki yeni klasör
  oluştu. Kod, prompt, şema, ayar, soru dosyası, eval ortamı dokunulmadı. Git'te yalnız bu rapor
Dur koşulları     : belge sayısı 113 ✓, FK'siz izler |0 ✓, DELETE 2 ✓ — tetiklenmedi.
  smoke 8/9 → emir 7 uygulandı (geri alma yok, Naci'ye soruldu)
Kendi başına verilen kararlar : §6 (4)
```
