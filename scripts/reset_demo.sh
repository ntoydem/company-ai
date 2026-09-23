#!/usr/bin/env bash
# Demo belgelerini sıfırla (Phase 3.1, SORU 2 cevabı): yalnızca `documents` tablosu (+
# page/chunk/job cascade) ve $DATA_ROOT/documents dosyaları silinir. Kullanıcılar,
# departmanlar ve projeler KORUNUR (zaten idempotent seed ediliyor). Onay ister, tersi
# için --yes ver: bash scripts/reset_demo.sh --yes
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file $ENV_FILE"
DATA_ROOT="$(grep -E '^DATA_ROOT=' "$ENV_FILE" 2>/dev/null | cut -d= -f2- | tr -d '"')"
DATA_ROOT="${DATA_ROOT:-./data}"

if [[ "${1:-}" != "--yes" ]]; then
  read -r -p "'$DATA_ROOT/documents' ve documents tablosu silinecek (kullanıcı/departman/proje korunur). Devam? [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]] || { echo "iptal edildi."; exit 1; }
fi

echo "== documents tablosu temizleniyor =="
$COMPOSE exec -T postgres sh -c 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "TRUNCATE documents CASCADE;"'

echo "== '$DATA_ROOT/documents' altındaki dosyalar siliniyor =="
rm -rf "${DATA_ROOT:?}/documents"/*

echo "demo belgeler sıfırlandı. 'make seed' ile yeniden oluştur."
