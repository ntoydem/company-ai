# Operasyon — geri alma ve yedekten geri yükleme

Bu dosya canlı ortamda (tek VM, Docker Compose, `~/company-ai`) **geri alma** adımlarını toplar.
Günlük yedek/geri yükleme komutları README "Backup / restore (Phase 5.3)" bölümünde; burada
yalnızca *bir sürüm ya da migration'ı geri alma* ve *yalnız-Postgres* dump'tan dönme anlatılır.
Her komut repo kökünden, `COMPOSE` kısaltması Makefile'dakiyle aynıdır:

```bash
cd ~/company-ai
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file .env"
```

İki sabit gerçek, her adımın sırasını belirler:

1. **Backend her açılışta `alembic upgrade head` çalıştırır** (`backend/entrypoint.sh`). Şemayı
   geri alıp kodu eski haline getirmezsen ilk restart migration'ı yeniden uygular. Bind mount
   olduğu için *çalışma ağacı = canlı kod*; "kodu geri al" demek `git checkout` demektir.
2. **`alembic downgrade` için geri alınacak migration dosyası diskte durmalıdır.** Önce indir,
   sonra kodu eski commit'e çek — tersi sırada alembic `0016` script'ini bulamaz.

## 1. Migration 0016 → 0015 geri alma (`documents.project_scope`, ADR-031)

`0016_document_project_scope.py` `downgrade()` fonksiyonu vardır: CHECK kısıtını, `project_scope`
sütununu ve `project_scope` enum tipini siler; satırlara dokunmaz. **15.10.2026'da geçici
veritabanında denendi** (`restore_test_a2l3`, canlı dump'tan): `0015 → 0016 → 0015` turu temiz,
sütun/enum/CHECK 0, `documents` 113 (İş Emri 2026-10-15A2L3 raporu §2).

```bash
# 0) (isteğe bağlı ama önerilir) geri alma öncesi dump
$COMPOSE exec -T postgres sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > data/backups/live_pre_rollback_$(date -u +%Y%m%d-%H%M).dump

# 1) yazan servisleri durdur (postgres ve caddy açık kalır)
$COMPOSE stop backend ocr-worker

# 2) şemayı indir — kod hâlâ 0016'yı içeren commit'te
$COMPOSE run --rm -T --no-deps backend alembic downgrade 0015

# 3) doğrula: 0015, sütun yok, enum yok, CHECK yok, belge sayısı aynı
$COMPOSE exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "
  select (select version_num from alembic_version),
         (select count(*) from information_schema.columns
            where table_name=\x27documents\x27 and column_name=\x27project_scope\x27),
         (select count(*) from pg_type where typname=\x27project_scope\x27),
         (select count(*) from pg_constraint
            where conname=\x27ck_documents_project_scope_matches_project_id\x27),
         (select count(*) from documents)"'
# beklenen: 0015|0|0|0|<belge sayısı>

# 4) kodu 0016 öncesi commit'e çek (A2 öncesi: 28265c9). Dal ismi ve çalışma ağacı temiz olsun.
git status --short            # temiz değilse önce git stash -u
git checkout --detach 28265c9  # bütün ağaç; 0016 dosyası ve project_narrowing.py diskten gider
ls backend/alembic/versions | tail -1   # 0015_... görünmeli

# 5) yeniden başlat ve doğrula
make restart-backend
$COMPOSE up -d ocr-worker
$COMPOSE logs backend --since 2m | grep -c "Running upgrade"   # 0 olmalı
python3 scripts/smoke_live.py   # 9/9 ve exit 0
```

Geri dönmek (ileri almak) için: `git checkout feat/adim5-veri-kutuphanesi && make restart-backend`
— entrypoint `0016`'yı yeniden uygular (≈ 12 s kesinti), `checkfirst` sayesinde yetim enum sorun
çıkarmaz.

**`downgrade()` çalışmazsa** (ileride bir migration'ın geri alma fonksiyonu yoksa ya da hata
verirse): §2'deki yalnız-Postgres geri yüklemeyi kullan; dump migration öncesi alınmış olmalıdır
(`alembic_version` dump'la birlikte gelir).

## 2. Yalnız-Postgres dump'tan geri yükleme (`data/backups/live_pre_*.dump`)

Canlıya alma öncesi alınan dump'lar yalnız veritabanını içerir (`pg_dump -Fc`); belge dosyaları
(`$DATA_ROOT/documents`) diskte olduğu gibi kalır. Tam yedekten (postgres + documents + excel +
app-data) dönmek için `make restore ARGS=...` kullanılır (README) — o yol *bütün* veriyi siler.

```bash
# 1) yazan servisleri durdur
$COMPOSE stop backend ocr-worker

# 2) dump'ı canlı veritabanının ÜZERİNE yaz (--clean: nesneleri düşürür, dump'takini kurar;
#    alembic_version da dump'taki değere döner)
$COMPOSE exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < data/backups/live_pre_A2L_20261015-1501.dump

# 3) kodu dump'ın şema sürümüne uyan commit'e çek (§1 adım 4), sonra §1 adım 5
```

Dump'tan sonra yüklenmiş belgeler varsa satırları gider, dosyaları `documents/<uuid>/` altında
öksüz kalır; dump'tan sonraki `audit_log` satırları da gider (A2L2 duman satırları gibi) — ham
JSON'lar `logs/` altında durur. Geri yüklemeden önce şu farkı yazıp rapora koy:

```bash
$COMPOSE exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "
  select count(*) from audit_log where timestamp > \x27<dump zamanı UTC>\x27"'
```

### 2.1 Canlıya dokunmadan prova (önerilen ilk adım)

Her dump'ı önce **ayrı, geçici bir veritabanında** aç; satır sayılarını canlıyla karşılaştır; sil.
15.10.2026 provası: 906.744 B dump, `pg_restore` 0,74 s, canlıyla belge/parça/proje kimlikleri
bire bir, fark yalnız dump sonrası 9 audit satırı.

```bash
$COMPOSE exec -T postgres sh -c 'createdb -U "$POSTGRES_USER" restore_test_X'
$COMPOSE exec -T postgres sh -c 'pg_restore -U "$POSTGRES_USER" -d restore_test_X --no-owner --exit-on-error' \
  < data/backups/<dump>
$COMPOSE exec -T postgres sh -c 'for db in restore_test_X "$POSTGRES_DB"; do
  echo "$db: $(psql -U "$POSTGRES_USER" -d "$db" -Atc "
    select (select version_num from alembic_version),(select count(*) from documents),
           (select count(*) from document_chunks),(select count(*) from audit_log),
           (select count(*) from projects),(select count(*) from users)")"; done'
# geçici veritabanında downgrade provası (isteğe bağlı): TEST_DATABASE_URL'nin adını değiştirerek
$COMPOSE run --rm -T --no-deps backend sh -c \
  'export DATABASE_URL="$(echo "$TEST_DATABASE_URL" | sed s/company_ai_test/restore_test_X/)"; alembic upgrade head && alembic downgrade 0015 && alembic current'
$COMPOSE exec -T postgres sh -c 'dropdb -U "$POSTGRES_USER" restore_test_X; psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -Atc "select datname from pg_database"'
```

## 3. Her geri almadan sonra doğrulama listesi

| Kontrol | Komut / beklenen |
|---|---|
| Şema sürümü | `alembic_version.version_num` beklenen değer; backend logunda `Running upgrade` **yok** |
| Satır sayıları | `documents`, `document_chunks`, `audit_log`, `projects`, `users` — geri alma öncesi sayılarla karşılaştır, farkı rapora yaz |
| Servisler | `$COMPOSE ps` → backend ve ocr-worker `healthy`; `curl -fsS http://localhost:$CADDY_PORT/health` |
| Davranış | `python3 scripts/smoke_live.py` → 9/9, exit 0 (`seed_data/evaluation/smoke.json`) |
| Ayarlar | `.env` değişmedi (`diff .env data/backups/<gün>/env.backup`) |
| Kesinti | restart öncesi/sonrası ilk 502 ve ilk 200 zaman damgaları; rapora yaz |
