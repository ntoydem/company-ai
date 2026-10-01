#!/usr/bin/env bash
# Demo veri (Phase 3.1): ledger doğrula -> belgeleri prose'dan render et (LLM yok) ->
# üretilen içeriği doğrula -> kullanıcı/departman/proje seed -> belgeleri yükle -> hepsi
# ready olana kadar bekle. Usage (repo root, `make up` sonrası): bash scripts/seed_demo.sh
set -euo pipefail

cd "$(dirname "$0")/.."
ENV_FILE="${ENV_FILE:-.env}"
COMPOSE="docker compose --project-directory . -f infra/docker-compose.yml --env-file $ENV_FILE"

echo "== truth ledger doğrulanıyor =="
$COMPOSE run --rm -T --no-deps backend python -m seed_data.generator.validate_ledger --summary

echo "== belgeler üretiliyor (committed prose'dan; LLM/ağ gerekmez) =="
$COMPOSE run --rm -T --no-deps backend python -m seed_data.generator.generate_documents

echo "== üretilen içerik doğrulanıyor =="
$COMPOSE run --rm -T --no-deps backend python -m seed_data.generator.validate_documents

echo "== kullanıcılar / departmanlar / projeler =="
$COMPOSE run --rm -T backend python -m app.cli seed-admin
$COMPOSE run --rm -T backend python -m app.cli seed-demo-users
$COMPOSE run --rm -T backend python -m app.cli seed-demo-departments
$COMPOSE run --rm -T backend python -m app.cli seed-demo-folders
$COMPOSE run --rm -T backend python -m app.cli seed-demo-projects

echo "== belgeler yükleniyor =="
$COMPOSE run --rm -T backend python -m app.cli seed-demo-documents

echo "== ocr-worker bekleniyor (70 belge 'ready' olana kadar) =="
$COMPOSE run --rm -T backend python -m app.cli wait-for-documents --timeout 1800

echo "demo veri hazır."
