# Phase 5.3 — Backup / restore: Implementation Plan

## Bağlam ve tespitler

Phase 5.2 (`phase-5-2`) kapandı. `docs/PHASES.md`'deki kapsam: `backup.sh` (Postgres dump, `documents/`,
`excel/`, app-data, config) → `$DATA_ROOT/backups/` günlük, 14 gün; haftalık `BACKUP_SECONDARY_PATH`
(spindown'dan önce); `restore.sh`; README prosedürü. Kabul kriteri: backup → `make down` → volume sil →
restore → aynı belgeler/kullanıcılar; eval skoru aynı. Aynı kapsam `docs/SPEC_06_operasyon_guvenlik_kalite.md`
§5'te ("Phase 15" — eski numaralandırma, bugünkü 5.3'e karşılık geliyor) tekrarlanıyor: ".env (şifrelenmiş
veya ayrı, README'de belirtilir)" ve "haftalık `BACKUP_SECONDARY_PATH` kopyası; cron saati HDD
spindown'dan önce" ifadeleri buradan.

Okunanlar: `docs/PHASES.md` (5.3 bağlamı), `docs/SPEC_06_operasyon_guvenlik_kalite.md` §4/§5/§6 (tamamı);
kod: `infra/docker-compose.yml` (tüm servisler), `infra/postgres/init/01_init.sql`, `Makefile` (`dirs`,
`backup`/`restore` stub'ları, `psql`, `migrate`), `scripts/reset_demo.sh`, `scripts/wait_for_services.sh`,
`infra/.env.example`, `backend/app/core/config.py` (`documents_dir`/`excel_dir`/`app_state_dir` özellikleri),
canlı dev VM'de `$DATA_ROOT` altındaki gerçek dizin boyutları (`du -sh`).

Planı şekillendiren tespitler:

- **T1 — `$DATA_ROOT/app-data/models` gerçekte 2,2 GB ve yedeğe girmemeli.** Canlı dev VM'de ölçtüm:
  `app-data/models` (bge-m3 embedding ağırlıkları, `EMBEDDINGS_ENABLED=true` denemesinden kalma önbellek) 2,2 GB,
  `app-data/caddy` birkaç KB, `documents/` 81 MB, `postgres/` (container-owned, ölçülemedi ama tipik olarak
  yüzlerce MB), `excel/` 4 KB (boş). SPEC_06 §4 "app-data" tek kalem olarak yazıyor ama `models/` HuggingFace'ten
  yeniden indirilebilir bir önbellek — kurumsal veri değil. **Öneri: `app-data/models/` günlük yedeğe dahil
  edilmesin** (boyutu her gün gereksiz yere 14× büyütür); `app-data/caddy` (önemsiz boyutlu) dahil edilsin.
  `EMBEDDINGS_ENABLED=true` olan bir kurulumda bu önbellek `make up-full` ilk açılışta zaten kendini yeniden
  indirir (SORU 1).
- **T2 — `$DATA_ROOT/excel/` şu an fiilen boş ve kullanılmıyor.** `backend/app/core/config.py::excel_dir` yalnızca
  `app/main.py`'de `mkdir` ediliyor (satır 102); Excel workbook upload'ları da (Phase 4.2) diğer her belge gibi
  `documents_dir` altına yazılıyor (`documents.py::upload_document`, `LocalFileSystemStore(settings.documents_dir)`).
  Spec'in ismen saydığı bu dizin bugün 0 bayt veri taşıyor — yine de spec'e sadık kalınarak yedek script'i bu
  dizini de kapsar (boşsa maliyeti sıfır, ileride kullanılırsa hazır olur); `seed_data/excel/` (git'e commit'li
  ham workbook şablonları) ve `seed_data/documents/` (gitignore'lu, `make prose`/generator build çıktısı, `make
  seed` ile yeniden üretilebilir) bu kapsamın **dışında** — onlar zaten git'te veya yeniden üretilebilir, yedek
  konusu değil.
- **T3 — pg_dump/pg_restore konteyner içinden, stdin/stdout pipe'ıyla; `docker-compose.yml`'a dokunmadan.**
  `postgres` servisi `$DATA_ROOT/backups`'ı hiç mount etmiyor. `make psql`'in zaten kullandığı
  `$(COMPOSE) exec postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB"'` deseni gibi,
  `docker compose exec -T postgres pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" > backups/DATE/postgres.dump`
  (host'a stdout redirect) ve geri yüklemede `... exec -T postgres pg_restore --clean --if-exists -U ... -d ... <
  postgres.dump` (host'tan stdin) yeterli — yeni bir volume mount'a gerek yok. `-Fc` (custom format): sıkıştırılmış,
  `pg_restore`'un `--clean`/paralel restore/seçmeli tablo gibi esnekliklerini destekler; düz SQL dump'tan daha az
  kırılgan.
- **T4 — `vector` extension'ı restore'dan ÖNCE, init script zaten hallediyor.** `infra/postgres/init/01_init.sql`
  yalnızca **boş** bir `$DATA_ROOT/postgres` üzerinde ilk açılışta çalışır ve `CREATE EXTENSION IF NOT EXISTS
  vector` + `company_ai_test` DB'sini kurar. Kabul kriterinin akışı ("volume sil → restore") bunu doğal olarak
  tetikler: volume silinip `postgres` servisi yeniden ayağa kalkınca init script kendini tekrar çalıştırır,
  extension restore'dan önce hazır olur — `restore.sh`'ın kendisi extension kurmakla uğraşmaz, yalnızca
  `postgres`'in sağlıklı (healthy) olmasını bekler, sonra `pg_restore` çalıştırır.
- **T5 — `.env` yedeğe ayrı bir dosya olarak girer, şifrelenmemiş ama izole ve `chmod 600`.** SPEC_06 §5'in
  ifadesi "şifrelenmiş VEYA ayrı" — ikisi arasında seçim var. Ortamda `gpg`/`age` kurulu olduğu doğrulanmadı
  (CLAUDE.md kural 4: olmayan bir CLI'ye bağımlı kod üretme); `openssl` hemen hemen her Linux dağıtımında var ama
  bu da doğrulanmamış bir varsayım olur. **Öneri: script `.env`'i şifrelemesin**, bunun yerine `postgres.dump`/
  `*.tar.gz` demetinden **ayrı**, kendi dosyasına (`backups/DATE/env.backup`, `chmod 600`) kopyalasın; README bu
  dosyanın sırlar içerdiğini ve ikincil/uzak konuma taşınmadan önce operatörün kendi anahtarıyla (ör. `age`/`gpg`,
  hangisi VM'de kuruluysa) şifrelemesi gerektiğini açıkça yazsın (SORU 2 — Naci otomatik şifrelemeyi tercih
  ederse hangi araç kurulu, netleşince eklenir).
- **T6 — Haftalık ikincil kopya: script yalnızca "senkronize et" komutunu sağlar, zamanlama Naci'nin cron'u.**
  Kullanıcının kendi talimatı da bunu söylüyor. `BACKUP_SECONDARY_PATH` zaten `.env.example`'da var (boş
  varsayılan). Öneri: `scripts/backup.sh --sync-secondary` bayrağı (veya ayrı `scripts/sync_secondary_backup.sh`
  — küçük teknik detay, uygulama sırasında netleşir), `BACKUP_SECONDARY_PATH` boşsa no-op + uyarı; doluysa `rsync
  -a --delete` (mevcut değilse `cp -r` fallback) ile **en son N günün** yedeğini oraya kopyalar — 8 TB HDD'nin
  yerel bir ikinci disk mi, ağ üzerinden bağlı bir NAS mı, yoksa uzak bir host mu olduğu netleşmeden gerçek
  mekanizma (`rsync -a /path` vs `rsync -a -e ssh user@host:/path`) tam belirlenemez (SORU 3).
- **T7 — Rotasyon dizin adına göre, mtime'a göre değil.** `backups/YYYY-MM-DD/` adları zaten sıralanabilir ISO
  tarih; `find ... -mtime` yerine dizin adını `date -d "14 days ago" +%F` ile metinsel karşılaştırmak, bir
  dosyanın `touch`lanması/kopyalanması gibi yan etkilerden etkilenmez — daha güvenilir.
- **T8 — `restore.sh` `.env`'e asla otomatik dokunmaz.** Geri yüklenen ortamın `.env`'i (DB şifresi, JWT secret,
  LLM anahtarı) mevcut/canlı `.env`'den kasıtlı olarak farklı olabilir (ör. farklı bir host'a restore). Script
  yedekteki `env.backup`'ın yolunu ekrana yazar ve **elle** karşılaştırıp taşımayı operatöre bırakır — sessizce
  üzerine yazmaz.
- **T9 — `make backup`/`make restore` stub'ları zaten Makefile'da (`Phase 5.3` yorumuyla `exit 1` dönüyorlar) —
  bu faz onları gerçek script çağrılarına bağlar.** Bu, kullanıcının listesinde ayrı bir madde değil ama
  stub'ların kendi yorumu bu fazı işaret ediyor; atlanırsa "admin her işlemi `make` üzerinden yapar" beklentisiyle
  tutarsız kalır.
- **T10 — Kabul kriterinin "eval skoru aynı mı" adımı LLM kotasına maliyetli; kapsamı daraltmayı öneriyorum.**
  Bu hafta zaten bir günlük Gemini kotası (500 istek/gün/model) tükenmişti (Phase 5.1). Restore'un kanıtlaması
  gereken şey **veri bütünlüğü** (Postgres + dosyalar aynen geri geldi mi), model cevap kalitesi değil — o zaten
  Phase 5.1/5.1b'nin konusu. Öneri: kabul testi `make test` (şema/CRUD bütünlüğü) + `make eval EVAL_ARGS="--retrieval-only"`
  (LLM'siz, yalnızca `document_chunks`'ın restore'dan sağ çıktığını kanıtlar, sıfır ek istek) ile yapılsın; tam
  `make eval` (LLM'li) **isteğe bağlı, ayrı bir onay** gerektirsin (SORU 4).

---

## 1. `scripts/backup.sh`

Konvansiyon `reset_demo.sh`/`wait_for_services.sh` ile birebir: `#!/usr/bin/env bash`, `set -euo pipefail`,
`cd "$(dirname "$0")/.."`, `ENV_FILE`/`COMPOSE`/`DATA_ROOT` değişkenleri Makefile'daki gibi `.env`'den okunur.

Akış:
1. `DATE="$(date +%F)"`, hedef `"$DATA_ROOT/backups/$DATE"` — `mkdir -p`.
2. `docker compose exec -T postgres pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB" > "$TARGET/postgres.dump"`
   (T3). Postgres ayakta değilse açık bir hata mesajıyla dur (`make up` öner).
3. `tar czf "$TARGET/documents.tar.gz" -C "$DATA_ROOT" documents`
4. `tar czf "$TARGET/excel.tar.gz" -C "$DATA_ROOT" excel` (T2 — boşsa da alınır, tutarlılık için)
5. `tar czf "$TARGET/app-data.tar.gz" -C "$DATA_ROOT" app-data --exclude='app-data/models'` (T1)
6. `cp "$ENV_FILE" "$TARGET/env.backup" && chmod 600 "$TARGET/env.backup"` (T5)
7. Rotasyon (T7): `backups/` altında `YYYY-MM-DD` deseniyle eşleşen dizinleri adına göre sırala, 14 günden eski
   olanları sil.
8. Özet yazdır: toplam boyut (`du -sh "$TARGET"`), hangi dosyalar oluştu.
9. `--sync-secondary` bayrağı verilirse (T6), adım 10'a geç; verilmezse burada biter.
10. `BACKUP_SECONDARY_PATH` boşsa uyarı verip no-op; doluysa `rsync -a --delete "$DATA_ROOT/backups/" "$BACKUP_SECONDARY_PATH/"`
    (`rsync` yoksa `cp -r` fallback + uyarı).

Çıkış kodu: herhangi bir adım başarısız olursa `set -e` zaten durdurur; `pg_dump` başarısız olursa yarım kalan
`$TARGET` silinir (temiz başarısızlık, bir sonraki koşuda karışıklık olmasın).

## 2. `scripts/restore.sh`

```
bash scripts/restore.sh 2026-09-26          # backups/2026-09-26/'dan geri yükle
bash scripts/restore.sh /yol/env-disi/yedek # ya da tam bir yol
bash scripts/restore.sh 2026-09-26 --yes    # onay istemeden (otomasyon için)
```

Akış:
1. Argüman kontrolü: tarih mi tam yol mu, dizin var mı, içinde `postgres.dump`/`documents.tar.gz` var mı — yoksa
   açık hata.
2. **Yıkıcı adım uyarısı** (`reset_demo.sh`'daki `--yes` deseniyle birebir): "Bu işlem MEVCUT tüm belgeleri,
   kullanıcıları ve verileri SİLECEK ve `<tarih>` yedeğiyle DEĞİŞTİRECEK. `$DATA_ROOT/postgres`,
   `$DATA_ROOT/documents`, `$DATA_ROOT/excel`, `$DATA_ROOT/app-data` kaybolacak. Devam? [y/N]" — `--yes` ile
   atlanır.
3. `$(COMPOSE) down` (tüm servisleri durdur, T9'un `make restore` çağırdığı script bunu kendisi yapar —
   kullanıcı ayrıca `make down` çalıştırmak zorunda kalmaz).
4. `rm -rf "$DATA_ROOT"/{postgres,documents,excel,app-data}/*` (app-data'nın `models/` alt dizini de dahil silinir
   — restore sonrası `EMBEDDINGS_ENABLED=true` ile ilk açılışta kendini yeniden indirir, T1).
5. `tar xzf .../documents.tar.gz -C "$DATA_ROOT"`, aynısı `excel.tar.gz`/`app-data.tar.gz` için.
6. `$(COMPOSE) up -d postgres` + sağlıklı olmasını bekle (T4 — init script kendiliğinden `vector`
   extension'ı kurar).
7. `docker compose exec -T postgres pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB" <
   postgres.dump`
8. `$(COMPOSE) up -d --build` (tüm servisler; `make up`'ın yaptığının aynısı, backend/ocr-worker/caddy image'ları
   yeniden inşa edilsin ki kod da güncel olsun — Phase 5.4'ün "temiz kurulum" senaryosuyla tutarlı).
9. `bash scripts/wait_for_services.sh 120`
10. Özet: geri yüklenen tarih, `env.backup`'ın yolu ve "elle karşılaştırıp gerekirse `.env`'e taşıyın" notu (T8
    — otomatik üzerine yazma yok).

## 3. Makefile

```makefile
backup: dirs ## yedek al: postgres dump + documents/excel/app-data + .env (ayrı dosya); make backup ARGS="--sync-secondary"
	bash scripts/backup.sh $(ARGS)

restore: dirs ## yedekten geri yükle (YIKICI): make restore ARGS="2026-09-26"
	@test -n "$(ARGS)" || { echo "ARGS=<tarih|yol> gerekli, örn: make restore ARGS=2026-09-26"; exit 1; }
	bash scripts/restore.sh $(ARGS)
```
Mevcut `exit 1` stub'larının yerini alır (T9); `dirs` ön koşulu zaten `backups/` dizinini garanti ediyor.

## 4. README — "Backup / restore (Phase 5.3)" bölümü

- `make backup` / `make backup ARGS="--sync-secondary"` örnekleri, ne yedeklendiği (Postgres, documents, excel,
  app-data **models hariç**), ne yedeklenmediği (`.env` ayrı dosyada, şifrelenmemiş — operatör kendi anahtarıyla
  şifrelemeli) net yazılır.
- `make restore ARGS="<tarih>"` örneği + **YIKICI OLDUĞU** açıkça belirtilir, `--yes` bayrağının anlamı.
- Haftalık ikincil kopya: `BACKUP_SECONDARY_PATH` ayarlanınca `--sync-secondary` çalıştıran bir cron satırı
  örneği (spindown saatinden önce — gerçek saat Naci'nin donanımına özel, örnek olarak yazılır, kurulum
  yapılmaz).
- "Bilinen sınırlar" bölümüne bir satır: `.env` yedeği şifrelenmemiş, ayrı dosya olarak tutulur — SORU 2'nin
  kararına göre netleşir.

---

## Kabul kriterleri → kanıt

| # | Kriter (PHASES.md) | Nasıl kanıtlanacak |
|---|---|---|
| 1 | canlı olarak yedek al | `make backup` çalıştırılır, `backups/<bugün>/` içeriği listelenir (dosya boyutları) |
| 2 | `make down` | script'in kendisi zaten `compose down` yapıyor (T9); ek olarak elle `make down` da denenip idempotent olduğu gösterilir |
| 3 | volume sil | `rm -rf "$DATA_ROOT"/{postgres,documents,excel,app-data}` elle çalıştırılır (restore.sh'ın adım 4'ünün gerçek bir "sil" senaryosunu simüle ettiği kanıtlanır) |
| 4 | restore → aynı belgeler/kullanıcılar | `make restore ARGS="<tarih>"`; sonra `curl /api/documents`/`/api/users` sayıları yedek-öncesiyle karşılaştırılır |
| 5 | eval skoru aynı | T10 önerisi: `make test` (tam yeşil) + `make eval EVAL_ARGS="--retrieval-only"` (restore öncesi/sonrası aynı recall) — tam LLM eval'i yalnızca SORU 4'ün cevabı "evet" ise |

---

## SORU (Naci cevaplamalı)

1. **`app-data/models/` (embedding önbelleği, ~2,2 GB) günlük yedeğe dahil edilmesin mi?** Önerim: hayır — HuggingFace'ten yeniden inen bir önbellek, kurumsal veri değil; dahil edilirse her gün gereksiz 2+ GB kopyalanır/saklanır. `EMBEDDINGS_ENABLED=false` olduğu sürece zaten hiç yok sayılabilir.
2. **`.env` yedeği nasıl korunsun?** Önerim (T5): şifrelenmemiş ama izole bir dosya (`env.backup`, `chmod 600`), README'de "ikincil/uzak konuma taşımadan önce kendi anahtarınızla şifreleyin" notuyla. Alternatif: script'in belirli bir aracı (örn. `openssl enc -aes-256-cbc -pbkdf2`, VM'de neredeyse kesin kurulu) kullanarak otomatik şifrelemesini ister misin — onaylarsan önce VM'de gerçekten kurulu olduğunu doğrularım.
3. **İkincil kopya (8 TB HDD) hangi mekanizmayla erişilecek?** Yerel ikinci bir disk mi (basit `cp`/`rsync` yeterli), ağ paylaşımı/NAS (mount noktası nedir) mı, yoksa SSH ile erişilen ayrı bir host mu? Cevaba göre `--sync-secondary`'nin gerçek komutu netleşir (T6).
4. **Kabul testi tam bir `make eval` (LLM'li) içersin mi, yoksa `--retrieval-only` + `make test` yeterli mi?** Önerim (T10): ikincisi — restore'un kanıtlaması gereken veri bütünlüğü, model kalitesi değil; ayrıca bu hafta zaten bir günlük kota tükenmişti. Naci tam eval'i de görmek isterse ekstra bir istek turu (kaç soru × kaç LLM çağrısı) göze alınmalı.

---

## Kendi aldığım küçük kararlar (raporda da listelenecek)

- `pg_dump -Fc` (custom format) + `pg_restore --clean --if-exists` — düz SQL dump yerine (T3).
- Rotasyon dizin adına göre (ISO tarih string karşılaştırması), `mtime`'a göre değil (T7).
- `restore.sh` kendi içinde `compose down`/`up` çağırır — kullanıcı ayrıca `make down` çalıştırmak zorunda değil, ama kabul kriterinin lafzına uyması için elle de gösterilecek (kanıt tablosu #2).
- `seed_data/documents/` (build çıktısı) ve `seed_data/excel/` (git'e commit'li) yedek kapsamı dışında — zaten git'te veya yeniden üretilebilir (T2).
- `.env` restore'da asla otomatik üzerine yazılmaz (T8) — sessiz secret kaybı/karışıklığı riski.
- Makefile `backup`/`restore` stub'ları gerçek script çağrılarına bağlanır (T9).

## Uygulama sırası

1. `scripts/backup.sh` (dump + tar + rotasyon + `.env` kopyası, `--sync-secondary` bayrağı SORU 3 netleşince).
2. `scripts/restore.sh` (onay istemi, `compose down`, silme, açma, `pg_restore`, `compose up`, `wait_for_services`).
3. `Makefile` `backup`/`restore` hedeflerini bağla.
4. Dev VM'de gerçek bir `make backup` → içerik/boyut doğrulaması.
5. Kabul testi: `make backup` → `make down` → volume'ları elle sil → `make restore ARGS=<tarih>` → `make test` +
   `make eval EVAL_ARGS="--retrieval-only"` (SORU 4 "hayır" ise) karşılaştırması → belge/kullanıcı sayıları
   kontrolü.
6. README "Backup / restore (Phase 5.3)" bölümü + "Bilinen sınırlar" satırı.
7. `docs/SPEC_06`'ya dokunma gerekmiyor (zaten doğru tarif ediyor) — rapor + `docs/PHASES.md` durum → commit +
   tag `phase-5-3` + push.

## Kritik dosyalar

- `scripts/backup.sh`, `scripts/restore.sh` (yeni)
- `Makefile` (`backup`/`restore` hedefleri)
- `README.md` (yeni bölüm)
- `infra/.env.example` (`BACKUP_SECONDARY_PATH` yorumu SORU 3'e göre güncellenebilir)
