# İş Emri 2026-10-17P1K_CANLI — Madde 1 (P1, ADR-035) canlıya alma (Ç-15/6)

**Tarih:** 17.10.2026 · **Dal:** `feat/adim5-veri-kutuphanesi` (HEAD `beac784`) · **Ürün 1**

**Dayanak:** Naci 17.10.2026 açık onayı (Ç-15/6). Kapsam:
- kod commit'i `6c4f38b` ve rapor `beac784`;
- yalnız backend yeniden başlatması;
- veri, şema ve ayar değişikliği yok.

Komutlar: `docs/reports/IS_EMRI_2026-10-17P1K.md` §8, aynen uygulandı.

**Sonuç:** başarılı.
- Smoke **9/9** ilk koşuda geçti; yeniden koşu gerekmedi.
- Smoke (f) beklenen dört projeyi sordu.
- İki kontrol sorusu beklendiği gibi cevaplandı.
- Geri alma gerekmedi.

## 1. Başlangıç (adım 1–2)

| | |
|---|---|
| Dal / HEAD | `feat/adim5-veri-kutuphanesi`, `beac784` (üstünde `6c4f38b`). `git status --short` yalnız `?? logs/`. `origin` ile eşit |
| Canlı backend, önce | imaj `company-ai-backend` `sha256:9ac73489e7d3…` (oluşturma 11.10.2026 11:10Z), **StartedAt 2026-10-16T15:21:21Z**, healthy. Kod `./backend` bind-mount'tan; uvicorn `--reload` olmadan çalışıyor, yani P1K kodu bu süreçte henüz yüklü değildi |
| Canlı DB, önce (yalnız SELECT, 11:21:56Z) | `company_ai`: documents **113**, document_chunks 461, audit_log **1653**, alembic **0016** |

D1'den sonra audit_log 1649'du. Aradaki 4 satır bu emir dışındaki kullanımlardan geliyor; dokunulmadı.

## 2. Yeniden başlatma (adım 3)

```
make restart-backend        # 11:22:01 → 11:22:13 UTC (12 s)
hazır: http://localhost:8080/health -> {"status":"ok","version":"0.1.0","database":"ok"}
```

- **Sonra:** aynı imaj (`sha256:9ac73489e7d3…`, `--build` yok), **StartedAt 2026-10-17T11:22:02Z**.
- `Running upgrade` satırı 0; migrasyon 0016'da kaldı. ERROR satırı 0.
- `.env` değişmedi.

## 3. smoke_live (adım 4)

`python3 scripts/smoke_live.py`, ilk koşu (11:22–11:23 UTC), exit 0:

| # | user | http | type | answered | s | sonuç |
|---|---|---|---|---|---|---|
| a | finans | 200 | MIXED_QUERY | True | 19.4 | ✅ |
| b | finans_mudur | 200 | DOCUMENT_QUERY | True | 6.8 | ✅ |
| c | admin | 200 | DOCUMENT_QUERY | True | 3.8 | ✅ |
| d | enerji | 200 | DOCUMENT_QUERY | False | 1.0 | ✅ |
| e | finans | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |
| f | yonetim | 200 | DOCUMENT_QUERY | False | 0.1 | ✅ |
| g | finans | 200 | MIXED_QUERY | True | 17.3 | ✅ |
| h | finans | 200 | DOCUMENT_QUERY | True | 3.4 | ✅ |
| i | enerji | 200 | DOCUMENT_QUERY | False | 0.0 | ✅ |

**9/9 geçti.** Ham çıktı `logs/smoke_20261017-1122_*.json` (`logs/` izlenmiyor).

**Smoke (f)** (yonetim, "Sözleşmenin vadesi ne zaman doluyor?"):

> Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Kızılova RES, Yeşilova RES)?

- Beklenenle **birebir aynı**. Önce 6 proje soruluyordu (Akyar GES ve Demirci RES dahil), şimdi 4.
- `answered=false`, `model` null, tokens 0.

## 4. Kontrol soruları (adım 5)

Yöntem: `smoke_live.py`'nin kendisi, `--spec` ile iki soruluk geçici bir dosya (scratchpad, repoya girmedi):
- aynı kullanıcılar ve aynı `/api/auth/login` → `/api/ask` yolu;
- parolalar `.env`'den, yazdırılmadan.

Beklentiler spec'e `contains` ve `response_excludes` olarak yazıldı. Sonuç **2/2**, exit 0. Ham çıktı `logs/smoke_20261017-1123_{j,k}.json`.

| Soru (kullanıcı) | Cevap (tam metin) | Beklenen | Sonuç |
|---|---|---|---|
| "Sigorta ne zaman bitiyor?" (enerji) | **Hangi proje için sormak istiyorsunuz (Karatepe RES)?** | yalnız Karatepe RES | ✅. Önceki kod "(Karatepe RES, Kızılova RES)" soruyordu (N1, GEN-DSC-003) |
| "Güncel DSCR kaç?" (finans) | **Hangi proje için sormak istiyorsunuz (Boztepe RES, Karatepe RES, Yeşilova RES)?** | Boztepe, Karatepe, Yeşilova; Kızılova yok | ✅. Önceki kod Kızılova'yı da listeliyordu (N1, ANK-MIX-001) |

İkisinde de `answered=false`, `model` null, tokens 0/0, kaynak yok. LLM çağrısı yapılmadı.

## 5. audit_log

| | audit_log | documents |
|---|---|---|
| Önce (11:21:56Z) | 1653 | 113 |
| Sonra | **1664** (+11) | 113 |

- **+11 satır:** smoke 9 + kontrol 2; hepsi `error` NULL.
- Model alanı: 6 satırda `claude-haiku-5-5` (a, b, c, d, g, h); 5 satırda NULL (e, f, i ve iki kontrol sorusu, yani kod yolları).
- Backend logunda 11:22'den sonra WARNING/ERROR 0.

## 6. Geri alma (gerekmedi; yazılı)

Yalnız kod geri alınır. Veri, migrasyon ve `.env` değişmedi.

```bash
cd ~/company-ai
git revert --no-edit 6c4f38b               # ya da: git checkout 7e2e148 -- backend/app scripts/measure_stage2.py
make restart-backend                       # ~12 s
curl -fsS http://localhost:8080/health
python3 scripts/smoke_live.py              # 9/9; (f) yeniden 6 proje sorar
```

## [ANAYASA KONTROLÜ]
```
Anayasa versiyonu : v2.1 (+ ADT-4). Okunan: Çekirdek (Ç-15/6, Ç-16); P1K raporu §8
Ürün etiketi      : Ürün 1 — T-11 (netleştirme sorusunun seçenekleri)
Ç-15/6 onay kanıtı: Naci 17.10.2026 açık canlıya alma onayı (6c4f38b + beac784; yalnız backend
  yeniden başlatması). Şartlar: geri alma planı (§6) ✓, smoke 9/9 ✓ (ilk koşu), migrasyon yok ✓
Gizli bilgi / yeni bağımlılık : Yok — .env okunup değiştirilmedi (parolalar smoke_live içinde,
  yazdırılmadı); yeni paket yok; imaj yeniden kurulmadı
Kapsam dışı değişiklik : Yok — canlıda yalnız backend container'ı yeniden yaratıldı. DB'ye yazan tek
  şey smoke + kontrol sorularının kendi 11 audit satırı. Kod, şema, ayar, veri, eval ortamı
  dokunulmadı. Git'te yalnız bu rapor (smoke ham çıktıları logs/ altında, izlenmiyor)
Dur koşulları     : tetiklenmedi — /health ok, smoke 9/9 ilk koşuda, iki kontrol beklenen metinle
Kendi başına verilen kararlar :
  1. Kontrol soruları smoke_live.py --spec ile soruldu (aynı kullanıcı/giriş yöntemi); spec dosyası
     scratchpad'de, repoya girmedi
  2. Kontrol beklentileri spec'e contains/response_excludes olarak yazıldı; cevap metinleri ayrıca
     ham JSON'dan okunup bu rapora aynen kondu
```
