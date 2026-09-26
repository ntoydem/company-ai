#!/usr/bin/env bash
# Daily backup (Phase 5.3, SPEC_06 §5): Postgres dump (pg_dump -Fc, via the running
# `postgres` service — no docker-compose.yml volume change needed) + documents/, excel/,
# app-data/ (embedding-model cache excluded — see below) + a separate, permission-locked
# copy of .env. Writes to $DATA_ROOT/backups/YYYY-MM-DD/, keeps 14 days.
#
# Usage: bash scripts/backup.sh [--sync-secondary]
#   --sync-secondary  also mirror backups/ to BACKUP_SECONDARY_PATH (a local second disk,
#                      SORU 3 docs/plans/PHASE_5_3_PLAN.md) — run this from your own cron,
#                      timed before the disk spins down; this script does not install one.
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file $ENV_FILE"
DATA_ROOT="$(grep -E '^DATA_ROOT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"')"
DATA_ROOT="${DATA_ROOT:-./data}"
BACKUP_SECONDARY_PATH="$(grep -E '^BACKUP_SECONDARY_PATH=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"')"

DATE="$(date +%F)"
TARGET="$DATA_ROOT/backups/$DATE"
mkdir -p "$TARGET"

# A backup that dies partway through must not leave a half-written directory behind for
# tomorrow's rotation logic (or a worried operator) to trip over.
trap '[[ -f "$TARGET/.complete" ]] || rm -rf "$TARGET"' EXIT

echo "== Postgres dump alınıyor =="
# `sh -c` + the container's own POSTGRES_USER/POSTGRES_DB env vars — same trick `make psql`
# uses — so this script never has to parse credentials out of .env itself.
$COMPOSE exec -T postgres sh -c 'pg_dump -Fc -U "$POSTGRES_USER" -d "$POSTGRES_DB"' \
  > "$TARGET/postgres.dump"

echo "== documents/ ve excel/ arşivleniyor =="
tar czf "$TARGET/documents.tar.gz" -C "$DATA_ROOT" documents
tar czf "$TARGET/excel.tar.gz" -C "$DATA_ROOT" excel

echo "== app-data/ arşivleniyor (embedding model önbelleği hariç) =="
# app-data/models: bge-m3 ağırlıkları, HuggingFace'ten yeniden inebilir, kurumsal veri
# değil — her gün gereksiz yere GB'larca veri kopyalamamak için dışarıda bırakılıyor
# (docs/plans/PHASE_5_3_PLAN.md T1, SORU 1). app-data/ ayrıca Caddy'nin kendi container'ı
# içinde root olarak yazdığı state dosyaları içerir (`app-data/caddy/caddy/...`, host
# kullanıcısı okuyamaz) — bu yüzden host'ta düz `tar` yerine, aynı volume'u `--user root`
# ile bağlayan kısa ömürlü bir konteynerden arşivleniyor (postgres image'ı zaten yerelde
# mevcut ve Debian tabanlı — tar dahil).
ABS_DATA_ROOT="$(cd "$DATA_ROOT" && pwd)"
ABS_TARGET="$(cd "$TARGET" && pwd)"
$COMPOSE run --rm --user root --entrypoint sh \
  -v "$ABS_DATA_ROOT/app-data:/app-data:ro" -v "$ABS_TARGET:/backup" \
  postgres -c 'tar --exclude="app-data/models" -czf /backup/app-data.tar.gz -C / app-data'

echo "== .env ayrı, izinle kilitli bir kopya olarak saklanıyor =="
# Şifrelenmiş değil (SORU 2): ikincil/uzak bir konuma taşımadan önce kendi anahtarınızla
# şifrelemeniz önerilir, örn. `gpg --symmetric --cipher-algo AES256 env.backup` — bkz. README.
cp "$ENV_FILE" "$TARGET/env.backup"
chmod 600 "$TARGET/env.backup"

echo "== 14 günden eski yedekler siliniyor =="
CUTOFF="$(date -d '14 days ago' +%F)"
for dir in "$DATA_ROOT"/backups/*/; do
  [[ -d "$dir" ]] || continue
  name="$(basename "$dir")"
  [[ "$name" =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] || continue
  if [[ "$name" < "$CUTOFF" ]]; then
    echo "  siliniyor: $name"
    rm -rf "$dir"
  fi
done

touch "$TARGET/.complete"
echo "== yedek tamamlandı: $TARGET =="
du -sh "$TARGET"/*

if [[ "${1:-}" == "--sync-secondary" ]]; then
  echo "== ikincil kopyaya (yerel disk) senkronize ediliyor =="
  if [[ -z "$BACKUP_SECONDARY_PATH" ]]; then
    echo "BACKUP_SECONDARY_PATH ayarlı değil (.env) — senkronizasyon atlandı." >&2
  else
    mkdir -p "$BACKUP_SECONDARY_PATH"
    if command -v rsync >/dev/null 2>&1; then
      rsync -a --delete "$DATA_ROOT/backups/" "$BACKUP_SECONDARY_PATH/"
    else
      echo "rsync bulunamadı, 'cp -a' ile kopyalanıyor (eski yedekleri silmez)." >&2
      cp -a "$DATA_ROOT/backups/." "$BACKUP_SECONDARY_PATH/"
    fi
    echo "ikincil kopya güncel: $BACKUP_SECONDARY_PATH"
  fi
fi
