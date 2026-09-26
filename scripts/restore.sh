#!/usr/bin/env bash
# Restore from a backup.sh backup (Phase 5.3, SPEC_06 §5). DESTRUCTIVE: replaces the
# current Postgres data, documents/, excel/ and app-data/ with the backup's contents.
# Asks for confirmation unless --yes is given.
#
# Usage: bash scripts/restore.sh <YYYY-MM-DD|path> [--yes]
#   bash scripts/restore.sh 2026-09-26
#   bash scripts/restore.sh /mnt/8tb/backups/2026-09-26 --yes
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file $ENV_FILE"
DATA_ROOT="$(grep -E '^DATA_ROOT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"')"
DATA_ROOT="${DATA_ROOT:-./data}"
CADDY_PORT="$(grep -E '^CADDY_PORT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2-)"
CADDY_PORT="${CADDY_PORT:-8080}"

ARG="${1:?Kullanım: bash scripts/restore.sh <YYYY-MM-DD|yol> [--yes]}"
if [[ -d "$ARG" ]]; then
  BACKUP_DIR="$ARG"
else
  BACKUP_DIR="$DATA_ROOT/backups/$ARG"
fi

for f in postgres.dump documents.tar.gz excel.tar.gz app-data.tar.gz; do
  [[ -f "$BACKUP_DIR/$f" ]] || {
    echo "Geçersiz yedek: '$BACKUP_DIR/$f' yok." >&2
    exit 1
  }
done

if [[ "${2:-}" != "--yes" ]]; then
  echo "UYARI: bu işlem mevcut TÜM belgeleri, kullanıcıları ve verileri SİLECEK ve"
  echo "'$BACKUP_DIR' yedeğiyle DEĞİŞTİRECEK: \$DATA_ROOT/{postgres,documents,excel,app-data}."
  read -r -p "Devam edilsin mi? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || {
    echo "iptal edildi."
    exit 1
  }
fi

echo "== servisler durduruluyor =="
$COMPOSE down

echo "== documents/, excel/ siliniyor =="
mkdir -p "$DATA_ROOT"/{documents,excel,app-data}
rm -rf "${DATA_ROOT:?}"/documents/* "${DATA_ROOT:?}"/excel/*

ABS_DATA_ROOT="$(cd "$DATA_ROOT" && pwd)"
ABS_BACKUP_DIR="$(cd "$BACKUP_DIR" && pwd)"

echo "== postgres verisi ve app-data/ siliniyor (root container ile — host kullanıcısı bu verilere yazamaz) =="
# app-data/ Caddy'nin container-içi root olarak yazdığı state dosyalarını içerebilir
# (bkz. backup.sh) — hem postgres verisi hem app-data aynı sebeple root'tan silinir.
$COMPOSE run --rm --user root --entrypoint sh postgres -c 'rm -rf /var/lib/postgresql/data/*'
$COMPOSE run --rm --user root --entrypoint sh -v "$ABS_DATA_ROOT/app-data:/app-data" postgres \
  -c 'rm -rf /app-data/*'

echo "== documents/, excel/ geri yükleniyor =="
tar xzf "$BACKUP_DIR/documents.tar.gz" -C "$DATA_ROOT"
tar xzf "$BACKUP_DIR/excel.tar.gz" -C "$DATA_ROOT"

echo "== app-data/ geri yükleniyor (root container ile) =="
$COMPOSE run --rm --user root --entrypoint sh \
  -v "$ABS_DATA_ROOT/app-data:/app-data" -v "$ABS_BACKUP_DIR:/backup:ro" \
  postgres -c 'tar xzf /backup/app-data.tar.gz -C /'

echo "== postgres başlatılıyor (init script'i 'vector' extension'ını yeniden kurar) =="
$COMPOSE up -d postgres
for _ in $(seq 1 60); do
  if $COMPOSE exec -T postgres sh -c 'pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB"' >/dev/null 2>&1; then
    break
  fi
  sleep 1
done

echo "== postgres dump geri yükleniyor =="
$COMPOSE exec -T postgres sh -c 'pg_restore --clean --if-exists -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  < "$BACKUP_DIR/postgres.dump"

echo "== tüm servisler ayağa kaldırılıyor =="
$COMPOSE up -d --build
CADDY_PORT="$CADDY_PORT" bash scripts/wait_for_services.sh 120

echo "== geri yükleme tamamlandı: $BACKUP_DIR =="
echo "Not: '.env' otomatik değiştirilmedi (T8, docs/plans/PHASE_5_3_PLAN.md). Yedeğin kendi"
echo ".env kopyası burada, gerekirse elle karşılaştırıp taşıyın: $BACKUP_DIR/env.backup"
