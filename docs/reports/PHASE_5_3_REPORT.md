# Phase 5.3 Raporu — Backup / restore

**Tarih:** 26.09.2026  **Model:** Sonnet 5  **Tag:** phase-5-3  **Commit:** (bu rapor commit'iyle aynı)

## 1. Kabul kriterleri
| # | Kriter (PHASES.md'den) | Durum | Kanıt |
|---|---|---|---|
| 1 | canlı olarak yedek al | ✅ | `make backup` — dev VM'de gerçek çalıştırıldı, `data/backups/2026-09-26/` (postgres.dump 340K, documents.tar.gz 81M, excel.tar.gz 4K, app-data.tar.gz 4K, env.backup 2,9K) |
| 2 | `make down` | ✅ | `restore.sh` kendi içinde `compose down` çağırıyor (script çıktısında görülüyor); ayrıca `--sync-secondary` ve rotasyon ayrı ayrı test edildi |
| 3 | volume sil | ✅ | `restore.sh`'ın kendisi bunu yapıyor: `documents/`/`excel/` host'tan, `postgres/`/`app-data/` kısa ömürlü bir `--user root` konteynerinden silinir (bkz. §5, T-yeni) |
| 4 | restore → aynı belgeler/kullanıcılar | ✅ | Restore öncesi `documents=74 users=5 projects=3`, restore sonrası **birebir aynı** (`curl /api/documents`, `/api/users`, `/api/projects`) |
| 5 | eval skoru aynı | ✅ | `make eval EVAL_ARGS="--retrieval-only"`: restore öncesi ve sonrası ikisi de **recall@80: 36/36 (%100.0)** — birebir aynı (SORU 4 kararı gereği tam LLM eval'i çalıştırılmadı, kotadan bağımsız kalındı) |

**Genel sonuç:** Kabul kriterinin tamamı gerçek, yıkıcı bir döngüyle (canlı dev VM'de `make backup` →
`make restore` → doğrulama) kanıtlandı — simülasyon veya kuru-koşu değil.

## 2. Yapılanlar
- **`scripts/backup.sh`** (yeni): `pg_dump -Fc` (çalışan `postgres` servisine `exec` ile, stdin/stdout —
  `docker-compose.yml`'a hiç dokunmadan), `documents.tar.gz`/`excel.tar.gz` (host'tan doğrudan), `app-data.tar.gz`
  (`app-data/models` hariç, kısa ömürlü bir `--user root` konteynerinden — bkz. §5), `env.backup` (`chmod 600`,
  şifrelenmemiş), 14 gün rotasyon (dizin adına göre, `mtime`'a değil), `--sync-secondary` bayrağı
  (`BACKUP_SECONDARY_PATH`'e `rsync -a --delete`, yoksa `cp -a` fallback).
- **`scripts/restore.sh`** (yeni): argüman = tarih veya tam yol; onay istemi (`--yes` ile atlanır);
  `compose down` → `documents`/`excel` host'tan, `postgres`/`app-data` root konteynerinden silinir → dosyalar
  geri yüklenir → `postgres` tek başına başlatılır (init script `vector` extension'ını yeniden kurar) →
  `pg_isready` ile beklenir → `pg_restore --clean --if-exists` → tüm servisler `--build` ile ayağa kaldırılır →
  `wait_for_services.sh`. `.env` hiçbir zaman otomatik değiştirilmez; yedeğin `env.backup`'ının yolu yazdırılır.
- **`Makefile`**: `backup`/`restore` stub'ları (`"Henüz uygulanmadı"; exit 1`) gerçek script çağrılarına
  bağlandı; `restore` hedefi `ARGS` boşsa açık bir hata verir.
- **`infra/.env.example`**: `BACKUP_SECONDARY_PATH` yorumu netleştirildi (yerel 8 TB disk, `--sync-secondary`).
- **`README.md`**: yeni "Backup / restore (Phase 5.3)" bölümü + "Bilinen sınırlar"a `.env` şifrelemesi notu +
  "Make hedefleri" tablosundaki eski "henüz uygulanmadı" satırı güncellendi.
- **Yol boyunca bulunan ve düzeltilen bir mypy hatası (Phase 5.2'den kalma):** `authorization.py`'deki
  `SingleDocumentIdsProvider.list_document_ids_for_departments`, `self._document.department` (`str | None`)
  ile `Iterable[str]` arasında tip-güvenli olmayan bir `in` karşılaştırması yapıyordu; `make lint` bunu Phase
  5.2'de neden yakalamadığı belirsiz (muhtemelen mypy'nin artımlı önbelleği), ama bu fazda tam `make lint`
  koşusunda ortaya çıktı ve `department is None` dalını açıkça ayırarak düzeltildi — çalışma zamanı davranışı
  değişmedi (testler değişmeden yeşil), yalnızca tip daraltması netleşti.

## 3. Değişen dosyalar
`git diff --stat` (bu rapor commit'iyle): `scripts/backup.sh` (yeni, ~75 satır), `scripts/restore.sh` (yeni,
~65 satır), `Makefile` (+4/-2), `infra/.env.example` (+3), `README.md` (+~35, yeni bölüm + iki küçük düzeltme),
`backend/app/services/authorization.py` (+3/-1, mypy düzeltmesi), `docs/PHASES.md` (durum + Phase 5.3 notu).
Migration yok.

## 4. Testler
- `make test`: 383 backend + 9 ocr-worker, tamamı yeşil — hem restore öncesi hem **restore sonrası** ayrı ayrı
  çalıştırıldı (restore'un DB şemasını/verisini bozmadığının kanıtı).
- `make lint`: backend (`ruff`/`mypy`), ocr-worker (`ruff`), frontend (`eslint`/`tsc`), prompt-doküman eşitliği,
  ledger/document/excel validasyonları — tamamı yeşil (mypy düzeltmesinden sonra).
- Script'ler için ayrı bir birim test dosyası açılmadı (bash, pytest kapsamı dışı) — doğrulama gerçek çalıştırma
  ile yapıldı (§1, §6).

## 5. Spec'ten sapmalar / kendi aldığım küçük kararlar
| Karar | Neden | Etkisi |
|---|---|---|
| Postgres verisi ve `app-data/`, host'tan değil kısa ömürlü bir `--user root` konteynerinden silinip arşivleniyor | **Planda öngörülmemiş, uygulama sırasında ölçülen gerçek bir engel:** host kullanıcısı (uid 1000) `data/postgres`'i (uid 999, mod 700) ve `data/app-data/caddy`'yi (Caddy container'ı root çalışıyor) okuyamıyor/silemiyor bile — `ls`/`tar`/`rm` "Permission denied" veriyor | Script'ler ilk denemede gerçek dev VM'de başarısız oldu, kanıtla düzeltildi (§6); nihai tasarım hâlâ `docker-compose.yml`'a dokunmuyor (yalnızca `docker compose run -v ek-mount`) |
| `app-data/caddy` yedeğe dahil (yalnızca `models/` hariç) | Root-konteyner çözümüyle artık okunabiliyor; boyutu önemsiz (birkaç KB) — plandaki T1 yalnızca `models/`i hariç tutmayı öneriyordu, `caddy/`yi hariç tutmak için ek bir gerekçe yok | Plan'a sadık: yalnızca gerçekten büyük/yeniden-üretilebilir önbellek dışarıda |
| Phase 5.2'nin mypy hatası bu fazda bulunup düzeltildi | `make lint` bu fazda ilk kez restore-sonrası tam koşuldu ve hatayı gösterdi; "kırmızı test varken ilerleme" kuralı | Scope dışı görünen ama CLAUDE.md'nin gerektirdiği bir düzeltme; ayrı, minimal bir değişiklik (yalnızca tip daraltması) |
| Kabul testi tam bir yıkıcı döngüyle (simülasyon değil) canlı dev VM'de çalıştırıldı | SORU'larda netleşen kapsamla (retrieval-only + make test) risk kabul edilebilir düzeye indi; gerçek kanıt sahte/kuru-koşu kanıttan daha güvenilir | Dev VM'in gerçek verisi bir kez silinip aynı yedekten geri yüklendi — veri kaybı olmadı (kanıtlandı), ama bu türden testler gelecekte de dikkatli yapılmalı |

## 6. Açık sorular (Naci cevaplamalı)
- Yok — SORU 1-4'ün hepsi plan onayında cevaplandı ve uygulandı.

## 7. Riskler / sonraki phase için notlar
- `--sync-secondary` yalnızca sahte bir yerel yol (`/tmp/...`) ile test edildi (gerçek 8 TB disk henüz takılı/
  bağlı değil) — gerçek donanım hazır olduğunda `BACKUP_SECONDARY_PATH`'i o yola ayarlayıp bir kez elle
  doğrulamak (`make backup ARGS="--sync-secondary"`) faydalı olur.
- Cron zamanlaması (haftalık, spindown'dan önce) bilinçli olarak bu fazın dışında bırakıldı — Naci'nin kendi
  sunucusuna özel bir `crontab` satırı gerekiyor, README'de örnek var ama kurulum yok.
- `env.backup` şifrelenmemiş duruyor (SORU 2 kararı) — operatör disiplinine bağlı bir risk, README'de ve
  "Bilinen sınırlar"da açıkça işaretlendi.
- Restore, tüm servisleri `--build` ile yeniden ayağa kaldırıyor (Phase 5.4'ün "temiz kurulum" senaryosuyla
  tutarlı olsun diye) — bu, restore'u `--build` yapmayan bir varyanttan birkaç on saniye daha yavaş yapar;
  V0 ölçeğinde önemsiz.

## 8. Doğruladığım üçüncü taraf davranışları
- **`docker compose run --rm --user root --entrypoint sh <servis> -c '...'`, servisin kendi `volumes:`
  tanımına ek olarak `-v` ile verilen ad-hoc mount'ları da kabul ediyor** ve `--user root`, bind mount'un host
  tarafındaki dosya sahipliğinden bağımsız olarak (root DAC kontrolünü atlar) okuma/yazma/silme yapabiliyor —
  bu, host kullanıcısının erişemediği container-sahipli verilere (Postgres PGDATA, Caddy state) erişmenin
  `docker-compose.yml`'a dokunmadan tek yolu olduğu canlı olarak doğrulandı.
- **`infra/postgres/init/01_init.sql`, yalnızca PGDATA tamamen boşken (ilk açılış) çalışıyor** — restore
  akışında volume silindikten sonra `postgres` yeniden başlatıldığında `CREATE EXTENSION IF NOT EXISTS vector`
  kendiliğinden tekrar çalıştı, `restore.sh`'ın ayrıca extension kurmasına gerek kalmadı (canlı doğrulandı:
  `pg_restore` hatasız tamamlandı, `document_chunks.embedding` sütunu sorunsuz geri geldi).
- **`pg_dump -Fc` / `pg_restore --clean --if-exists`, pgvector extension'ı ve tüm `document_chunks`/`documents`/
  `users`/`audit_log` şemasını sorunsuz taşıdı** — restore sonrası `make test`'in 383/383 yeşil kalması ve
  belge/kullanıcı sayılarının birebir eşleşmesi bunun kanıtı.

## 9. Kaynak kullanımı
- LLM çağrısı yok (`--retrieval-only` kullanıldı, SORU 4).
- Docker: backend/ocr-worker/caddy image'ları restore sırasında `--build` ile yeniden inşa edildi (~1-2 dk,
  çoğunlukla cache'ten); toplam restore süresi (silme + geri yükleme + tüm servisler sağlıklı oluncaya kadar)
  ~2-3 dk.
- Disk: bugünkü yedek `data/backups/2026-09-26/` ~81 MB (documents.tar.gz baskın kalem); `app-data/models`
  hariç tutulmasaydı +2,2 GB olurdu.
